import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
import torchvision.transforms as transforms
import time
import os
import copy
from pathlib import Path
from scripts.config import (
    SPLITS_DIR, MODELS_DIR, BATCH_SIZE, LR_CNN, LR_RESNET_HEAD, LR_RESNET_FINETUNE,
    MAX_EPOCHS, PATIENCE, WEIGHT_DECAY, IMAGENET_MEAN, IMAGENET_STD, RANDOM_SEED
)
from scripts.models import freeze_backbone, unfreeze_last_layers

# Set random seeds for reproducibility
def set_seeds(seed=RANDOM_SEED):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Ensure deterministic behavior
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def get_dataloaders(batch_size):
    """
    Creates DataLoaders for train and val splits.
    Applies standard ImageNet normalizations.
    """
    train_dir = SPLITS_DIR / "train"
    val_dir = SPLITS_DIR / "val"
    
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])
    
    train_dataset = ImageFolder(train_dir, transform=transform)
    val_dataset = ImageFolder(val_dir, transform=transform)
    
    # We set pin_memory=True for faster GPU transfer
    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True,
        num_workers=0, pin_memory=True
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False,
        num_workers=0, pin_memory=True
    )
    
    return train_loader, val_loader

class TrainManager:
    """
    Manages the training cycle, early stopping, AMP, and OOM fallbacks.
    """
    def __init__(self, model, model_name, device):
        self.model = model.to(device)
        self.model_name = model_name
        self.device = device
        self.best_val_acc = 0.0
        self.best_epoch = 0
        self.history = {
            "train_loss": [], "train_acc": [],
            "val_loss": [], "val_acc": [], "lr": []
        }
        
    def train(self, start_epoch=1, max_epochs=MAX_EPOCHS, patience=PATIENCE):
        # We start with the configured BATCH_SIZE
        current_batch_size = BATCH_SIZE
        
        # Instantiate optimizer, scheduler, criterion, and scaler
        criterion = nn.CrossEntropyLoss()
        
        # Adjust hyperparams depending on architecture
        if self.model_name == "BaselineCNN":
            optimizer = optim.AdamW(self.model.parameters(), lr=LR_CNN, weight_decay=WEIGHT_DECAY)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)
            use_amp = torch.cuda.is_available()
            scaler = torch.cuda.amp.GradScaler() if use_amp else None
            
            # Standard single training loop
            self._train_loop(
                max_epochs, patience, criterion, optimizer, scheduler, scaler, use_amp, current_batch_size
            )
            
        else:  # ResNet18
            # Two-phase fine-tuning
            # Phase 1: Warmup classification head for 3 epochs with frozen backbone
            print("\n--- ResNet18 Phase 1: Head Warmup (Frozen Backbone) ---")
            freeze_backbone(self.model)
            optimizer = optim.AdamW(filter(lambda p: p.requires_grad, self.model.parameters()), lr=LR_RESNET_HEAD, weight_decay=WEIGHT_DECAY)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)
            use_amp = torch.cuda.is_available()
            scaler = torch.cuda.amp.GradScaler() if use_amp else None
            
            warmup_epochs = 3
            self._train_loop(
                warmup_epochs, patience, criterion, optimizer, scheduler, scaler, use_amp, current_batch_size, is_warmup=True
            )
            
            # Phase 2: Fine-tune backbone last layers
            print("\n--- ResNet18 Phase 2: Fine-Tuning Last Layers (Unfrozen layer4 + fc) ---")
            unfreeze_last_layers(self.model)
            optimizer = optim.AdamW(filter(lambda p: p.requires_grad, self.model.parameters()), lr=LR_RESNET_FINETUNE, weight_decay=WEIGHT_DECAY)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)
            # Retain history and best performance, resume training
            self._train_loop(
                max_epochs - warmup_epochs, patience, criterion, optimizer, scheduler, scaler, use_amp, current_batch_size, offset_epoch=warmup_epochs
            )
            
    def _train_loop(self, epochs, patience, criterion, optimizer, scheduler, scaler, use_amp, batch_size, is_warmup=False, offset_epoch=0):
        # Create directories for models
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        
        train_loader, val_loader = get_dataloaders(batch_size)
        
        epochs_no_improve = 0
        best_val_loss = float('inf')
        
        for epoch in range(1 + offset_epoch, epochs + 1 + offset_epoch):
            epoch_start_time = time.time()
            
            # Loop with OOM protection
            try:
                train_loss, train_acc = self._run_train_epoch(
                    train_loader, criterion, optimizer, scaler, use_amp
                )
            except RuntimeError as e:
                # Catch CUDA Out Of Memory
                if "out of memory" in str(e).lower() and batch_size == 32:
                    print("\n[OOM CRITICAL] CUDA Out of Memory. Re-allocating VRAM and reducing batch size to 16...")
                    torch.cuda.empty_cache()
                    batch_size = 16
                    train_loader, val_loader = get_dataloaders(batch_size)
                    # Retry this epoch
                    train_loss, train_acc = self._run_train_epoch(
                        train_loader, criterion, optimizer, scaler, use_amp
                    )
                else:
                    raise e
                    
            val_loss, val_acc = self._run_val_epoch(val_loader, criterion)
            
            epoch_time = time.time() - epoch_start_time
            current_lr = optimizer.param_groups[0]['lr']
            
            # Update learning rate scheduler
            scheduler.step(val_loss)
            
            # Log results
            self.history["train_loss"].append(train_loss)
            self.history["train_acc"].append(train_acc)
            self.history["val_loss"].append(val_loss)
            self.history["val_acc"].append(val_acc)
            self.history["lr"].append(current_lr)
            
            print(f"Epoch {epoch:02d}/{epochs + offset_epoch:02d} | "
                  f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc*100:.2f}% | "
                  f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc*100:.2f}% | "
                  f"LR: {current_lr:.6f} | Time: {epoch_time:.1f}s")
            
            # Save best model based on Validation Accuracy
            if val_acc > self.best_val_acc:
                self.best_val_acc = val_acc
                self.best_epoch = epoch
                # Save best state dict
                checkpoint = {
                    "epoch": epoch,
                    "model_state_dict": self.model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_acc": val_acc,
                    "val_loss": val_loss,
                    "history": self.history
                }
                save_filename = "cnn_model.pth" if self.model_name == "BaselineCNN" else "resnet18_best.pth"
                torch.save(checkpoint, MODELS_DIR / save_filename)
                print(f"--> Saved best model checkpoint ({save_filename}) with Val Acc: {val_acc*100:.2f}%")
                
            # Early Stopping check (only outside warmup phase)
            if not is_warmup:
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    epochs_no_improve = 0
                else:
                    epochs_no_improve += 1
                    
                if epochs_no_improve >= patience:
                    print(f"--> Early stopping triggered after {patience} epochs without validation loss improvement.")
                    break

    def _run_train_epoch(self, dataloader, criterion, optimizer, scaler, use_amp):
        self.model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for inputs, targets in dataloader:
            inputs, targets = inputs.to(self.device), targets.to(self.device)
            optimizer.zero_grad()
            
            if use_amp:
                # Automatic Mixed Precision forward pass
                with torch.cuda.amp.autocast():
                    outputs = self.model(inputs)
                    loss = criterion(outputs, targets)
                
                # Scaled backward pass
                scaler.scale(loss).backward()
                # Unscale gradients before clipping
                scaler.unscale_(optimizer)
                nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                # Scaler optimizer step
                scaler.step(optimizer)
                scaler.update()
            else:
                outputs = self.model(inputs)
                loss = criterion(outputs, targets)
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                
            running_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()
            
        epoch_loss = running_loss / total
        epoch_acc = correct / total
        return epoch_loss, epoch_acc

    def _run_val_epoch(self, dataloader, criterion):
        self.model.eval()
        running_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for inputs, targets in dataloader:
                inputs, targets = inputs.to(self.device), targets.to(self.device)
                outputs = self.model(inputs)
                loss = criterion(outputs, targets)
                
                running_loss += loss.item() * inputs.size(0)
                _, predicted = outputs.max(1)
                total += targets.size(0)
                correct += predicted.eq(targets).sum().item()
                
        val_loss = running_loss / total
        val_acc = correct / total
        return val_loss, val_acc
