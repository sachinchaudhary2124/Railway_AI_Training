import torch
import time
import sys
import os
from pathlib import Path
from scripts.config import MODELS_DIR, REPORTS_DIR, MAX_EPOCHS, PATIENCE
from scripts.models import BaselineCNN, get_resnet18_model
from scripts.train import TrainManager, set_seeds
from scripts.evaluate import evaluate_all
from scripts.compare import compare_models

def generate_training_report(cnn_train_time, resnet_train_time, cnn_checkpoint, resnet_checkpoint):
    """Compiles reports/training_report.md summarizing the training performance."""
    report_path = REPORTS_DIR / "training_report.md"
    
    cnn_best_val_acc = cnn_checkpoint.get("val_acc", 0.0) if cnn_checkpoint else 0.0
    cnn_best_epoch = cnn_checkpoint.get("epoch", 0) if cnn_checkpoint else 0
    cnn_best_val_loss = cnn_checkpoint.get("val_loss", 0.0) if cnn_checkpoint else 0.0
    
    resnet_best_val_acc = resnet_checkpoint.get("val_acc", 0.0) if resnet_checkpoint else 0.0
    resnet_best_epoch = resnet_checkpoint.get("epoch", 0) if resnet_checkpoint else 0
    resnet_best_val_loss = resnet_checkpoint.get("val_loss", 0.0) if resnet_checkpoint else 0.0
    
    report_content = f"""# Railway Track Inspection - Model Training Report

This report summarizes the training progression, learning dynamics, and hyperparameters for both the Baseline CNN and Transfer Learning ResNet18 models.

---

## 1. Hyperparameters & Settings

- **Maximum Epochs**: {MAX_EPOCHS}
- **Early Stopping Patience**: {PATIENCE} epochs (monitored on Validation Loss)
- **Automatic Mixed Precision (AMP)**: Enabled (if GPU is available)
- **Out-of-Memory (OOM) Handler**: Configured (recovers from VRAM limits by falling back from batch size 32 to 16)
- **Random Seed**: 42 (all initializations, dataloader shuffles, and split splits are deterministic)
- **Optimiser**: AdamW with weight decay `1e-4`
- **Learning Rate Scheduler**: `ReduceLROnPlateau` (decays LR by 0.5 if Validation Loss plateaus for 3 epochs)

---

## 2. Baseline CNN Model Training

The custom CNN was trained from scratch. 
- **Trainable Parameters**: 446,180
- **Total Training Time**: {cnn_train_time:.1f} seconds
- **Best Validation Accuracy**: {cnn_best_val_acc*100:.2f}% (Epoch {cnn_best_epoch})
- **Best Validation Loss**: {cnn_best_val_loss:.4f}

---

## 3. Transfer Learning ResNet18 Model Training

ResNet18 was trained using pre-trained ImageNet weights in two phases:
1. **Phase 1: Head Warmup (3 epochs)**: Backbone frozen, only the custom classification head was trained (learning rate `1e-3`).
2. **Phase 2: Fine-Tuning (remaining epochs)**: Residual block `layer4` and the classification head unfrozen (learning rate `1e-4`).

- **Trainable Parameters (Phase 2)**: 8,393,860
- **Total Training Time**: {resnet_train_time:.1f} seconds
- **Best Validation Accuracy**: {resnet_best_val_acc*100:.2f}% (Epoch {resnet_best_epoch})
- **Best Validation Loss**: {resnet_best_val_loss:.4f}

---

## 4. Learning Progression Curves

### Accuracy Dynamics
The training and validation accuracy progression for both models is compared below:
![Accuracy Curve](accuracy_curve.png)

### Loss Dynamics
The training and validation cross-entropy loss progression is shown below:
![Loss Curve](loss_curve.png)

---
*Report generated automatically on {time.strftime("%Y-%m-%d")} by MLOps Deep Learning orchestrator.*
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"--> Training report saved to: {report_path}")

def main():
    print("==================================================")
    print("RUNNING RAILWAY DEEP LEARNING TRAINING PIPELINE")
    print("==================================================")
    
    # 0. Set random seeds
    set_seeds()
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Executing training on device: {device}")
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Train Baseline CNN
    print("\n[Step 1/4] Training Baseline CNN Model...")
    cnn_model = BaselineCNN()
    cnn_trainer = TrainManager(cnn_model, "BaselineCNN", device)
    
    cnn_start = time.time()
    cnn_trainer.train()
    cnn_train_time = time.time() - cnn_start
    print(f"Finished training CNN. Elapsed: {cnn_train_time:.1f} seconds")
    
    # Inject training time into CNN checkpoint
    cnn_path = MODELS_DIR / "cnn_model.pth"
    cnn_checkpoint = None
    if cnn_path.exists():
        cnn_checkpoint = torch.load(cnn_path)
        cnn_checkpoint["training_time_sec"] = cnn_train_time
        torch.save(cnn_checkpoint, cnn_path)
        print("--> Updated CNN checkpoint with training time.")
        
    # 2. Train Transfer Learning ResNet18
    print("\n[Step 2/4] Training Transfer Learning ResNet18 Model...")
    resnet_model = get_resnet18_model()
    resnet_trainer = TrainManager(resnet_model, "ResNet18", device)
    
    resnet_start = time.time()
    resnet_trainer.train()
    resnet_train_time = time.time() - resnet_start
    print(f"Finished training ResNet18. Elapsed: {resnet_train_time:.1f} seconds")
    
    # Inject training time into ResNet18 checkpoint
    resnet_path = MODELS_DIR / "resnet18_best.pth"
    resnet_checkpoint = None
    if resnet_path.exists():
        resnet_checkpoint = torch.load(resnet_path)
        resnet_checkpoint["training_time_sec"] = resnet_train_time
        torch.save(resnet_checkpoint, resnet_path)
        print("--> Updated ResNet18 checkpoint with training time.")
        
    # 3. Evaluate Models on Test Set
    print("\n[Step 3/4] Running Model Evaluations on Test Set...")
    evaluate_all()
    
    # 4. Compare Models and Select Best
    print("\n[Step 4/4] Running Model Comparison...")
    compare_models()
    
    # 5. Compile reports/training_report.md
    # Reload checkpoints to get latest updates
    if cnn_path.exists():
        cnn_checkpoint = torch.load(cnn_path)
    if resnet_path.exists():
        resnet_checkpoint = torch.load(resnet_path)
        
    generate_training_report(cnn_train_time, resnet_train_time, cnn_checkpoint, resnet_checkpoint)
    
    print("\n==================================================")
    print("DEEP LEARNING TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    main()
