import time
import threading
import torch
import torch.nn as nn
from typing import Tuple
from backend.utils.config import MODEL_PATH, CLASS_NAMES
from backend.utils.logger import logger

def get_resnet18_model(num_classes: int = 4) -> nn.Module:
    """
    Instantiates ResNet18 model and replaces the classification head to match 4 classes.
    """
    try:
        from torchvision.models import resnet18
        model = resnet18(weights=None)
    except (ImportError, NameError):
        from torchvision.models import resnet18
        model = resnet18(pretrained=False)
        
    # Replace classification head
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)
    return model

class ModelService:
    """
    Singleton service that manages model lifecycle, inference, and GPU allocation.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ModelService, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
            cls._instance._lock = threading.Lock()
        return cls._instance

    def initialize(self):
        """Loads and warms up the model. Safe to call multiple times, loads only once."""
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            logger.info("Initializing Model Service...")
        
            # 1. Setup Inference Device
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Target inference device detected: {self.device}")

            # 2. Check model file existence
            if not MODEL_PATH.exists():
                raise FileNotFoundError(
                    f"Model checkpoint weight file not found at: {MODEL_PATH}. "
                    "Please run training or place best_model.pth inside the models/ directory."
                )

            # 3. Instantiate model architecture
            logger.info("Instantiating ResNet18 neural network structure...")
            self.model = get_resnet18_model(num_classes=len(CLASS_NAMES))

            # 4. Load weights checkpoint
            logger.info(f"Loading checkpoint weights from: {MODEL_PATH}")
            try:
                checkpoint = torch.load(MODEL_PATH, map_location=self.device)
                # Check if checkpoint is dict with state_dict or direct state_dict
                if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                    self.model.load_state_dict(checkpoint["model_state_dict"])
                    logger.info(f"Successfully loaded model weights from checkpoint (Val Acc: {checkpoint.get('val_acc', 0.0)*100:.2f}%)")
                else:
                    self.model.load_state_dict(checkpoint)
                    logger.info("Successfully loaded model state dict directly")
            except Exception as e:
                logger.error(f"Error loading model checkpoint: {str(e)}")
                raise e

            # 5. Move model to device and set to eval mode
            self.model.to(self.device)
            self.model.eval()

            # 6. Model Warmup
            logger.info("Running dummy inference warmup...")
            try:
                start_time = time.time()
                dummy_input = torch.zeros(1, 3, 224, 224).to(self.device)
                with torch.no_grad():
                    _ = self.model(dummy_input)
                warmup_time = (time.time() - start_time) * 1000
                logger.info(f"Model warmed up successfully in {warmup_time:.2f}ms.")
            except Exception as e:
                logger.warning(f"Failed to complete model warmup: {str(e)}")

            self._initialized = True
            logger.info("Model Service fully initialized.")

    def run_inference(self, tensor: torch.Tensor) -> Tuple[torch.Tensor, float]:
        """
        Runs model inference on a preprocessed input image tensor.
        Returns the output logits tensor and the execution time in ms.
        """
        if not self._initialized:
            self.initialize()

        tensor = tensor.to(self.device)
        start_time = time.time()
        
        with torch.no_grad():
            outputs = self.model(tensor)
            
        latency_ms = (time.time() - start_time) * 1000
        return outputs, latency_ms

# Shared instance for routes/endpoints
model_service = ModelService()
