import torch
import torch.nn as nn

class BaselineCNN(nn.Module):
    """
    Baseline CNN Model designed for Railway Track defect detection.
    Features:
    - 4 Convolutional blocks (Conv -> BatchNorm -> ReLU -> MaxPool -> Dropout)
    - Global Average Pooling (GAP) to reduce parameter count and prevent overfitting
    - Multi-layer Perceptron classification head
    """
    def __init__(self, num_classes=4):
        super(BaselineCNN, self).__init__()
        
        self.conv1 = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout(0.25)
        )
        
        self.conv2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout(0.25)
        )
        
        self.conv3 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout(0.25)
        )
        
        # Keep conv4 separate so we can easily hook the last conv layer for Grad-CAM
        self.conv4_layer = nn.Conv2d(128, 256, kernel_size=3, padding=1)
        self.conv4_rest = nn.Sequential(
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Dropout(0.25)
        )
        
        self.gap = nn.AdaptiveAvgPool2d((1, 1))
        
        self.classifier = nn.Sequential(
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes)
        )
        
    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        
        # Keep track of last conv layer pass
        x = self.conv4_layer(x)
        x = self.conv4_rest(x)
        
        x = self.gap(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x
        
    def get_last_conv_layer(self):
        """Exposes the last conv layer for Grad-CAM hooks."""
        return self.conv4_layer

def get_resnet18_model(num_classes=4):
    """
    Loads pre-trained ResNet18 model and replaces the classification head.
    Supports backward compatible loading of ImageNet weights.
    """
    try:
        from torchvision.models import resnet18, ResNet18_Weights
        model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
    except (ImportError, NameError):
        from torchvision.models import resnet18
        model = resnet18(pretrained=True)
        
    # Replace final classification head
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)
    return model

def freeze_backbone(model):
    """Freezes all layers except the classification head (fc)."""
    for name, param in model.named_parameters():
        if "fc" not in name:
            param.requires_grad = False
        else:
            param.requires_grad = True

def unfreeze_last_layers(model):
    """Unfreezes the last block (layer4) and classification head (fc) for fine-tuning."""
    for name, param in model.named_parameters():
        if "layer4" in name or "fc" in name:
            param.requires_grad = True
        else:
            param.requires_grad = False
            
if __name__ == "__main__":
    # Smoke tests
    cnn = BaselineCNN()
    x = torch.randn(2, 3, 224, 224)
    out = cnn(x)
    print("Baseline CNN output shape:", out.shape)
    
    resnet = get_resnet18_model()
    out = resnet(x)
    print("ResNet18 output shape:", out.shape)
