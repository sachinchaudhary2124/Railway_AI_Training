import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless mode for matplotlib
import matplotlib.pyplot as plt
from PIL import Image
import torch
import torch.nn as nn
from backend.utils.config import GRADCAM_OUTPUT_DIR
from backend.utils.logger import logger

class GradCAM:
    """
    Hooks onto target layer and extracts gradients & activation feature maps for CAM overlays.
    """
    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # Register hooks
        self.forward_hook = self.target_layer.register_forward_hook(self.save_activation)
        if hasattr(self.target_layer, "register_full_backward_hook"):
            self.backward_hook = self.target_layer.register_full_backward_hook(self.save_gradient)
        else:
            self.backward_hook = self.target_layer.register_backward_hook(self.save_gradient)
            
    def save_activation(self, module, input, output):
        self.activations = output.detach()
        
    def save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()
        
    def generate_heatmap(self, input_tensor: torch.Tensor, class_idx: int) -> np.ndarray:
        """
        Calculates gradients with respect to target class, generates and normalizes heatmap.
        """
        # Ensure gradients are enabled for the backward pass
        with torch.enable_grad():
            # Get model device dynamically
            device = next(self.model.parameters()).device
            # Move tensor to target device, clone and enable gradients
            input_tensor = input_tensor.to(device).clone().detach().requires_grad_(True)
            self.model.zero_grad()
            
            # Forward pass
            output = self.model(input_tensor)
            
            # Loss is class score
            loss = output[0, class_idx]
            loss.backward()
            
            if self.gradients is None or self.activations is None:
                raise RuntimeError(
                    "Grad-CAM failed to capture activations/gradients. "
                    "Confirm hook registrations and ensure gradient tracking is active."
                )
                
            gradients = self.gradients[0]
            activations = self.activations[0]
            
            # Global Average Pooling of gradients (weights)
            weights = gradients.mean(dim=(1, 2), keepdim=True)
            
            # Weighted sum of feature maps
            grad_cam = (weights * activations).sum(dim=0)
            
            # ReLU to keep only positive contributions
            grad_cam = torch.clamp(grad_cam, min=0)
            
            # Normalize to [0, 1] range
            grad_cam_max = grad_cam.max()
            if grad_cam_max > 0:
                grad_cam = grad_cam / grad_cam_max
                
            return grad_cam.cpu().numpy()
            
    def remove_hooks(self):
        """Cleans up target hooks to prevent memory leaks in PyTorch runtime."""
        self.forward_hook.remove()
        self.backward_hook.remove()

def overlay_heatmap(original_image: Image.Image, heatmap: np.ndarray, alpha: float = 0.5) -> Image.Image:
    """
    Blends the 2D heatmap colormap (Jet) onto the original image.
    """
    # Resize heatmap to match original image dimensions
    heatmap_resized = Image.fromarray((heatmap * 255).astype(np.uint8)).resize(original_image.size, Image.Resampling.BILINEAR)
    heatmap_arr = np.array(heatmap_resized) / 255.0
    
    # Load colormap
    try:
        colormap = matplotlib.colormaps.get_cmap('jet')
    except AttributeError:
        # Fallback to legacy matplotlib
        import matplotlib.cm as cm
        colormap = cm.get_cmap('jet')
        
    # RGB heatmap values
    heatmap_colored = colormap(heatmap_arr)[:, :, :3]
    
    # Get original image float RGB values
    img_arr = np.array(original_image.convert("RGB"), dtype=np.float32) / 255.0
    
    # Perform standard alpha blending
    blended = alpha * heatmap_colored + (1.0 - alpha) * img_arr
    blended = np.clip(blended * 255.0, 0.0, 255.0).astype(np.uint8)
    
    return Image.fromarray(blended)

class GradCAMService:
    """
    Coordinates hook generation, heatmap processing, image overlaying, and saving overlay images.
    """
    @staticmethod
    def generate_and_save(model: nn.Module, input_tensor: torch.Tensor, original_image: Image.Image, class_idx: int, prediction_id: str) -> str:
        """
        Performs the complete Grad-CAM pipeline, saving the output.
        Returns the local file path to the saved heatmap overlay.
        """
        # Find target layer (last conv layer of final ResNet block)
        target_layer = None
        
        # ResNet18 structure: model.layer4 is the final block, we hook the last conv layer
        if hasattr(model, "layer4"):
            target_layer = model.layer4[-1].conv2
        # BaselineCNN layout (for fallback / compatibility testing)
        elif hasattr(model, "conv4_layer"):
            target_layer = model.conv4_layer
            
        if target_layer is None:
            # Fallback to look for a conv layer dynamically
            for name, module in reversed(list(model.named_modules())):
                if isinstance(module, nn.Conv2d):
                    target_layer = module
                    logger.warning(f"Grad-CAM dynamically bound to conv layer: {name}")
                    break
                    
        if target_layer is None:
            raise RuntimeError("Could not find a valid Conv2d layer in the model for Grad-CAM.")
            
        # Hook and generate
        cam = GradCAM(model, target_layer)
        try:
            heatmap = cam.generate_heatmap(input_tensor, class_idx)
            overlay = overlay_heatmap(original_image, heatmap, alpha=0.45)
            
            # Save to disk
            filename = f"gradcam_{prediction_id}.jpg"
            save_path = GRADCAM_OUTPUT_DIR / filename
            overlay.save(save_path, "JPEG", quality=90)
            
            logger.info(f"Generated Grad-CAM for prediction {prediction_id} -> {save_path}")
            return f"backend/outputs/gradcam/{filename}"
        except Exception as e:
            logger.error(f"Grad-CAM generation error for prediction {prediction_id}: {str(e)}")
            raise e
        finally:
            # Always clean hooks to prevent memory leaks
            cam.remove_hooks()
