import torch
import torch.nn.functional as F
import numpy as np
import matplotlib
# Use non-interactive backend for matplotlib in headless scripts
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

class GradCAM:
    """
    Grad-CAM (Gradient-weighted Class Activation Mapping) for PyTorch models.
    Supports registering hooks on target layers to compute activation maps.
    """
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # Register hooks
        self.forward_hook = self.target_layer.register_forward_hook(self.save_activation)
        # Register backward hook, supporting both new and old PyTorch versions
        if hasattr(self.target_layer, "register_full_backward_hook"):
            self.backward_hook = self.target_layer.register_full_backward_hook(self.save_gradient)
        else:
            self.backward_hook = self.target_layer.register_backward_hook(self.save_gradient)
            
    def save_activation(self, module, input, output):
        self.activations = output.detach()
        
    def save_gradient(self, module, grad_input, grad_output):
        # grad_output is a tuple where first element contains the gradients
        self.gradients = grad_output[0].detach()
        
    def generate_heatmap(self, input_tensor, class_idx=None):
        """
        Generates a 2D float32 heatmap in range [0, 1] for the target class.
        If class_idx is None, computes heatmap for the highest scoring class.
        """
        self.model.eval()
        output = self.model(input_tensor)
        
        if class_idx is None:
            class_idx = output.argmax(dim=1).item()
            
        self.model.zero_grad()
        loss = output[0, class_idx]
        loss.backward()
        
        if self.gradients is None or self.activations is None:
            raise RuntimeError("Gradients or Activations were not captured! Check if hooks are registered correctly.")
            
        # Shape of gradients: [1, C, H, W]
        # Shape of activations: [1, C, H, W]
        gradients = self.gradients[0]
        activations = self.activations[0]
        
        # Global average pool the gradients to get channel weights
        weights = gradients.mean(dim=(1, 2), keepdim=True)  # [C, 1, 1]
        
        # Weighted combination of activations
        grad_cam = (weights * activations).sum(dim=0)  # [H, W]
        
        # Apply ReLU (we only care about features that positively contribute to the class score)
        grad_cam = torch.clamp(grad_cam, min=0)
        
        # Normalize between 0 and 1
        if grad_cam.max() > 0:
            grad_cam = grad_cam / grad_cam.max()
            
        return grad_cam.cpu().numpy(), class_idx
        
    def remove_hooks(self):
        """Removes the hooks from the target layer to avoid memory leaks."""
        self.forward_hook.remove()
        self.backward_hook.remove()

def overlay_heatmap(original_image, heatmap, alpha=0.5):
    """
    Overlays a Grad-CAM heatmap on the original Pillow Image.
    Returns:
    - Pillow Image with the blended overlay.
    """
    # Resize heatmap to match original image size
    heatmap_resized = Image.fromarray((heatmap * 255).astype(np.uint8)).resize(original_image.size, Image.Resampling.BILINEAR)
    heatmap_arr = np.array(heatmap_resized) / 255.0
    
    # Get colormap (fallback to legacy API if matplotlib.colormaps is not present)
    if hasattr(matplotlib, "colormaps"):
        colormap = matplotlib.colormaps.get_cmap('jet')
    else:
        import matplotlib.cm as cm
        colormap = cm.get_cmap('jet')
        
    # Colorize heatmap (maps single values to RGBA, we take RGB)
    heatmap_colored = colormap(heatmap_arr)[:, :, :3]
    
    # Convert original image to floating point [0, 1] numpy array
    img_arr = np.array(original_image.convert("RGB"), dtype=np.float32) / 255.0
    
    # Blend images
    blended = alpha * heatmap_colored + (1 - alpha) * img_arr
    blended = np.clip(blended * 255, 0, 255).astype(np.uint8)
    
    return Image.fromarray(blended)
