import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, 
    balanced_accuracy_score, confusion_matrix, classification_report
)
import time
import os
import random
import shutil
from pathlib import Path
from scripts.config import (
    SPLITS_DIR, REPORTS_DIR, MODELS_DIR, CLASS_NAMES, IMAGENET_MEAN, IMAGENET_STD, TARGET_SIZE
)
from scripts.models import BaselineCNN, get_resnet18_model
from scripts.gradcam import GradCAM, overlay_heatmap

# Setup directories for galleries
BASE_DIR = Path(__file__).resolve().parent.parent
GRADCAM_DIR = BASE_DIR / "gradcam"
PREDICTION_DIR = BASE_DIR / "prediction_gallery"
MISCLASSIFIED_DIR = BASE_DIR / "misclassified_gallery"
CORRECT_DIR = BASE_DIR / "correct_predictions"

GALLERY_DIRS = [GRADCAM_DIR, PREDICTION_DIR, MISCLASSIFIED_DIR, CORRECT_DIR]

def setup_gallery_dirs():
    for d in GALLERY_DIRS:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

def load_test_dataset():
    """Loads raw test dataset files and labels."""
    test_dir = SPLITS_DIR / "test"
    image_paths = []
    labels = []
    
    for class_idx, class_name in enumerate(CLASS_NAMES):
        class_folder = test_dir / class_name
        if class_folder.exists():
            for f in class_folder.iterdir():
                if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".avif"]:
                    image_paths.append(f)
                    labels.append(class_idx)
                    
    return image_paths, np.array(labels)

def preprocess_image(pil_img):
    """Preprocesses a single PIL image into a torch tensor."""
    # Convert to RGB if not already
    if pil_img.mode != "RGB":
        pil_img = pil_img.convert("RGB")
    # Resize to target
    pil_img = pil_img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
    # Convert to numpy array and normalize
    arr = np.array(pil_img, dtype=np.float32) / 255.0
    mean = np.array(IMAGENET_MEAN, dtype=np.float32)
    std = np.array(IMAGENET_STD, dtype=np.float32)
    arr_normalized = (arr - mean) / std
    # Transpose to [C, H, W]
    arr_transposed = np.transpose(arr_normalized, (2, 0, 1))
    # Convert to tensor and add batch dimension
    tensor = torch.from_numpy(arr_transposed).unsqueeze(0)
    return tensor

def evaluate_model(model, image_paths, true_labels, device):
    """
    Evaluates a model on the test dataset.
    Measures accuracy, precision, recall, f1, balanced accuracy, latency, and confidence.
    """
    model.eval()
    predictions = []
    confidences = []
    latencies = []
    
    with torch.no_grad():
        for path in image_paths:
            img = Image.open(path)
            tensor = preprocess_image(img).to(device)
            
            start_time = time.time()
            outputs = model(tensor)
            latency = (time.time() - start_time) * 1000  # in ms
            latencies.append(latency)
            
            probs = torch.softmax(outputs, dim=1)
            conf, pred = torch.max(probs, 1)
            
            predictions.append(pred.item())
            confidences.append(conf.item())
            
    predictions = np.array(predictions)
    confidences = np.array(confidences)
    
    # Calculate metrics
    acc = accuracy_score(true_labels, predictions)
    balanced_acc = balanced_accuracy_score(true_labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(true_labels, predictions, average='weighted', zero_division=0)
    
    avg_latency = np.mean(latencies)
    avg_conf = np.mean(confidences)
    
    # Confusion matrix
    cm = confusion_matrix(true_labels, predictions, labels=list(range(len(CLASS_NAMES))))
    
    # Classification Report
    cr = classification_report(true_labels, predictions, target_names=CLASS_NAMES, zero_division=0)
    
    # Per-class accuracy
    per_class_acc = {}
    for idx, name in enumerate(CLASS_NAMES):
        class_mask = (true_labels == idx)
        if np.sum(class_mask) > 0:
            class_acc = np.mean(predictions[class_mask] == idx)
        else:
            class_acc = 0.0
        per_class_acc[name] = class_acc
        
    return {
        "accuracy": acc,
        "balanced_accuracy": balanced_acc,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "avg_latency_ms": avg_latency,
        "avg_confidence": avg_conf,
        "confusion_matrix": cm,
        "classification_report": cr,
        "per_class_accuracy": per_class_acc,
        "predictions": predictions,
        "confidences": confidences
    }

def plot_joint_curves(cnn_hist, resnet_hist):
    """Plots joint learning curves for CNN vs ResNet18."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Accuracy Curve
    plt.figure(figsize=(10, 5))
    if cnn_hist:
        plt.plot(cnn_hist["train_acc"], label="CNN Train Acc", color="#1f77b4", linestyle="--")
        plt.plot(cnn_hist["val_acc"], label="CNN Val Acc", color="#ff7f0e", linestyle="--")
    if resnet_hist:
        plt.plot(resnet_hist["train_acc"], label="ResNet18 Train Acc", color="#2ca02c", linestyle="-")
        plt.plot(resnet_hist["val_acc"], label="ResNet18 Val Acc", color="#d62728", linestyle="-")
        
    plt.title("Training and Validation Accuracy Curves", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Epochs", fontsize=12)
    plt.ylabel("Accuracy", fontsize=12)
    plt.legend(frameon=True)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "accuracy_curve.png", dpi=300)
    plt.close()
    
    # Loss Curve
    plt.figure(figsize=(10, 5))
    if cnn_hist:
        plt.plot(cnn_hist["train_loss"], label="CNN Train Loss", color="#1f77b4", linestyle="--")
        plt.plot(cnn_hist["val_loss"], label="CNN Val Loss", color="#ff7f0e", linestyle="--")
    if resnet_hist:
        plt.plot(resnet_hist["train_loss"], label="ResNet18 Train Loss", color="#2ca02c", linestyle="-")
        plt.plot(resnet_hist["val_loss"], label="ResNet18 Val Loss", color="#d62728", linestyle="-")
        
    plt.title("Training and Validation Loss Curves", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Epochs", fontsize=12)
    plt.ylabel("Cross-Entropy Loss", fontsize=12)
    plt.legend(frameon=True)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "loss_curve.png", dpi=300)
    plt.close()

def plot_side_by_side_cm(cnn_cm, resnet_cm):
    """Plots confusion matrices for both models side-by-side."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    def draw_cm(ax, cm, title):
        im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
        ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        
        ax.set(xticks=np.arange(cm.shape[1]),
               yticks=np.arange(cm.shape[0]),
               xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES,
               title=title,
               ylabel='True label',
               xlabel='Predicted label')
        
        # Rotate class names
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        # Text annotations
        fmt = 'd'
        thresh = cm.max() / 2.
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(j, i, format(cm[i, j], fmt),
                        ha="center", va="center",
                        color="white" if cm[i, j] > thresh else "black",
                        fontweight='bold')
                
    if cnn_cm is not None:
        draw_cm(axes[0], cnn_cm, "CNN Confusion Matrix")
    if resnet_cm is not None:
        draw_cm(axes[1], resnet_cm, "ResNet18 Confusion Matrix")
        
    plt.suptitle("Model Evaluation on Test Dataset", fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "confusion_matrix.png", dpi=300)
    plt.close()

def plot_per_class_bar(cnn_per_class, resnet_per_class):
    """Plots side-by-side per-class accuracies."""
    classes = CLASS_NAMES
    x = np.arange(len(classes))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    rects1 = ax.bar(x - width/2, [cnn_per_class.get(c, 0)*100 for c in classes], width, label='CNN', color='#3498db')
    rects2 = ax.bar(x + width/2, [resnet_per_class.get(c, 0)*100 for c in classes], width, label='ResNet18', color='#2ecc71')
    
    ax.set_ylabel('Accuracy (%)', fontsize=12)
    ax.set_title('Per-Class Accuracy: CNN vs ResNet18', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(classes)
    ax.set_ylim(0, 105)
    ax.legend(frameon=True)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height:.1f}%',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontweight='bold', fontsize=9)
            
    autolabel(rects1)
    autolabel(rects2)
    
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "per_class_accuracy.png", dpi=300)
    plt.close()

def plot_confidence_distribution(cnn_conf, resnet_conf):
    """Plots histogram of prediction confidence scores."""
    plt.figure(figsize=(10, 5))
    
    plt.hist(cnn_conf * 100, bins=15, alpha=0.5, label='CNN Confidences', color='#1f77b4', edgecolor='black')
    plt.hist(resnet_conf * 100, bins=15, alpha=0.5, label='ResNet18 Confidences', color='#2ca02c', edgecolor='black')
    
    plt.title("Prediction Confidence Score Distribution", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Confidence Score (%)", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.legend(frameon=True)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "confidence_distribution.png", dpi=300)
    plt.close()

def create_prediction_galleries(model, model_name, image_paths, true_labels, predictions, confidences, target_conv_layer, device):
    """
    Populates correct_predictions/, misclassified_gallery/, and gradcam/ directories.
    Applies Grad-CAM overlay heatmap to selected images.
    """
    setup_gallery_dirs()
    
    gradcam_tool = GradCAM(model, target_conv_layer)
    
    for i, path in enumerate(image_paths):
        img = Image.open(path)
        actual_class = CLASS_NAMES[true_labels[i]]
        pred_class = CLASS_NAMES[predictions[i]]
        conf = confidences[i]
        
        is_correct = (predictions[i] == true_labels[i])
        
        # Formulate a nice visual container using Matplotlib
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.imshow(img)
        ax.axis('off')
        
        title_color = "green" if is_correct else "red"
        border_color = "#2ecc71" if is_correct else "#e74c3c"
        
        # Add a border around plot
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color(border_color)
            spine.set_linewidth(5)
            
        plt.title(f"Model: {model_name}\n"
                  f"Actual: {actual_class.upper()} | Predicted: {pred_class.upper()}\n"
                  f"Confidence: {conf*100:.2f}%", 
                  fontsize=12, fontweight='bold', color=title_color)
        
        plt.tight_layout()
        
        # Save to correct/incorrect folders
        filename = f"{model_name}_{actual_class}_{i:03d}.jpg"
        if is_correct:
            plt.savefig(CORRECT_DIR / filename, dpi=200)
        else:
            plt.savefig(MISCLASSIFIED_DIR / filename, dpi=200)
        plt.close()
        
        # Generate Grad-CAM overlays (generate for all samples, save under gradcam/)
        try:
            tensor = preprocess_image(img).to(device)
            # generate heatmap for the predicted class
            heatmap, _ = gradcam_tool.generate_heatmap(tensor, class_idx=predictions[i])
            overlay = overlay_heatmap(img, heatmap, alpha=0.45)
            
            # Save side-by-side Grad-CAM overlay
            fig, axes = plt.subplots(1, 2, figsize=(10, 5))
            axes[0].imshow(img)
            axes[0].set_title(f"Original Image ({actual_class})", fontsize=11, fontweight='bold')
            axes[0].axis('off')
            
            axes[1].imshow(overlay)
            axes[1].set_title(f"Grad-CAM Heatmap (Pred: {pred_class})", fontsize=11, fontweight='bold')
            axes[1].axis('off')
            
            plt.suptitle(f"Defect Explainer - {model_name}\n"
                         f"Status: {'CORRECT' if is_correct else 'INCORRECT'} | Conf: {conf*100:.2f}%", 
                         fontsize=13, fontweight='bold', y=0.98)
            plt.tight_layout()
            plt.savefig(GRADCAM_DIR / f"gradcam_{filename}", dpi=200)
            plt.close()
            
        except Exception as e:
            print(f"Failed to generate Grad-CAM for {path.name}: {str(e)}")
            plt.close()
            
    # Clean up hooks
    gradcam_tool.remove_hooks()

def run_unseen_testing(model, model_name, image_paths, true_labels, target_conv_layer, device):
    """
    Selects 10 random unseen images from the test set.
    Generates side-by-side original image + Grad-CAM heatmap overlays.
    Saves in prediction_gallery/.
    """
    random.seed(42)
    indices = list(range(len(image_paths)))
    # Sample up to 10
    sample_indices = random.sample(indices, min(10, len(indices)))
    
    gradcam_tool = GradCAM(model, target_conv_layer)
    
    print(f"\n[Unseen Image Testing] Running 10-image testing with {model_name}...")
    
    for rank, idx in enumerate(sample_indices):
        path = image_paths[idx]
        img = Image.open(path)
        actual_idx = true_labels[idx]
        actual_class = CLASS_NAMES[actual_idx]
        
        # Inference
        tensor = preprocess_image(img).to(device)
        model.eval()
        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1)
            conf, pred = torch.max(probs, 1)
            pred_idx = pred.item()
            pred_class = CLASS_NAMES[pred_idx]
            
        is_correct = (pred_idx == actual_idx)
        status = "CORRECT" if is_correct else "INCORRECT"
        
        # Generate Grad-CAM heatmap
        # Do not use no_grad block for Grad-CAM forward/backward calculation
        heatmap, _ = gradcam_tool.generate_heatmap(tensor, class_idx=pred_idx)
        overlay = overlay_heatmap(img, heatmap, alpha=0.45)
        
        # Save side-by-side explanation
        fig, axes = plt.subplots(1, 2, figsize=(10, 5))
        axes[0].imshow(img)
        axes[0].set_title(f"Original ({actual_class})", fontsize=12, fontweight='bold')
        axes[0].axis('off')
        
        axes[1].imshow(overlay)
        axes[1].set_title(f"Grad-CAM overlay (Pred: {pred_class})", fontsize=12, fontweight='bold')
        axes[1].axis('off')
        
        title_color = "green" if is_correct else "red"
        plt.suptitle(f"Unseen Test Image #{rank+1} | Model: {model_name}\n"
                     f"Actual: {actual_class.upper()} | Predicted: {pred_class.upper()} | "
                     f"Confidence: {conf.item()*100:.2f}% | {status}", 
                     fontsize=13, fontweight='bold', color=title_color, y=0.98)
        
        plt.tight_layout()
        filename = f"unseen_{rank+1:02d}_{actual_class}_to_{pred_class}.jpg"
        plt.savefig(PREDICTION_DIR / filename, dpi=200)
        plt.close()
        
    gradcam_tool.remove_hooks()
    print(f"Unseen image testing completed. Results saved to:\n{PREDICTION_DIR}")

def evaluate_all():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n[Step 6] Running Test Set Evaluation on device: {device}...")
    
    # 1. Load test dataset files and labels
    image_paths, true_labels = load_test_dataset()
    if len(image_paths) == 0:
        print("CRITICAL ERROR: No test images found! Run dataset pipeline first.")
        return
        
    # 2. Instantiate and load CNN
    cnn_model = BaselineCNN()
    cnn_path = MODELS_DIR / "cnn_model.pth"
    if cnn_path.exists():
        cnn_checkpoint = torch.load(cnn_path, map_location=device)
        cnn_model.load_state_dict(cnn_checkpoint["model_state_dict"])
        cnn_hist = cnn_checkpoint.get("history", None)
        print("Loaded best CNN checkpoint from:", cnn_path)
    else:
        print("WARNING: cnn_model.pth not found! Skipping CNN evaluation.")
        cnn_checkpoint = None
        cnn_hist = None
        
    # 3. Instantiate and load ResNet18
    resnet_model = get_resnet18_model()
    resnet_path = MODELS_DIR / "resnet18_best.pth"
    if resnet_path.exists():
        resnet_checkpoint = torch.load(resnet_path, map_location=device)
        resnet_model.load_state_dict(resnet_checkpoint["model_state_dict"])
        resnet_hist = resnet_checkpoint.get("history", None)
        print("Loaded best ResNet18 checkpoint from:", resnet_path)
    else:
        print("WARNING: resnet18_best.pth not found! Skipping ResNet18 evaluation.")
        resnet_checkpoint = None
        resnet_hist = None
        
    # 4. Evaluate models
    cnn_metrics = None
    resnet_metrics = None
    
    if cnn_checkpoint:
        cnn_metrics = evaluate_model(cnn_model.to(device), image_paths, true_labels, device)
        print(f"\nBaseline CNN Test Accuracy: {cnn_metrics['accuracy']*100:.2f}% | "
              f"Balanced Accuracy: {cnn_metrics['balanced_accuracy']*100:.2f}%")
              
    if resnet_checkpoint:
        resnet_metrics = evaluate_model(resnet_model.to(device), image_paths, true_labels, device)
        print(f"ResNet18 Test Accuracy: {resnet_metrics['accuracy']*100:.2f}% | "
              f"Balanced Accuracy: {resnet_metrics['balanced_accuracy']*100:.2f}%")
              
    # 5. Save comparison plots and metrics
    plot_joint_curves(cnn_hist, resnet_hist)
    
    cnn_cm = cnn_metrics["confusion_matrix"] if cnn_metrics else None
    resnet_cm = resnet_metrics["confusion_matrix"] if resnet_metrics else None
    plot_side_by_side_cm(cnn_cm, resnet_cm)
    
    cnn_per_class = cnn_metrics["per_class_accuracy"] if cnn_metrics else {}
    resnet_per_class = resnet_metrics["per_class_accuracy"] if resnet_metrics else {}
    plot_per_class_bar(cnn_per_class, resnet_per_class)
    
    cnn_conf = cnn_metrics["confidences"] if cnn_metrics else np.array([])
    resnet_conf = resnet_metrics["confidences"] if resnet_metrics else np.array([])
    plot_confidence_distribution(cnn_conf, resnet_conf)
    
    # 6. Save text reports & CSV
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    metrics_list = []
    if cnn_metrics:
        metrics_list.append({
            "model": "CNN",
            "accuracy": cnn_metrics["accuracy"],
            "balanced_accuracy": cnn_metrics["balanced_accuracy"],
            "precision": cnn_metrics["precision"],
            "recall": cnn_metrics["recall"],
            "f1_score": cnn_metrics["f1_score"],
            "avg_latency_ms": cnn_metrics["avg_latency_ms"],
            "avg_confidence": cnn_metrics["avg_confidence"]
        })
    if resnet_metrics:
        metrics_list.append({
            "model": "ResNet18",
            "accuracy": resnet_metrics["accuracy"],
            "balanced_accuracy": resnet_metrics["balanced_accuracy"],
            "precision": resnet_metrics["precision"],
            "recall": resnet_metrics["recall"],
            "f1_score": resnet_metrics["f1_score"],
            "avg_latency_ms": resnet_metrics["avg_latency_ms"],
            "avg_confidence": resnet_metrics["avg_confidence"]
        })
        
    metrics_df = pd.DataFrame(metrics_list)
    metrics_df.to_csv(REPORTS_DIR / "evaluation_metrics.csv", index=False)
    
    with open(REPORTS_DIR / "classification_report.txt", "w") as f:
        if cnn_metrics:
            f.write("==================================================\n")
            f.write("BASELINE CNN CLASSIFICATION REPORT\n")
            f.write("==================================================\n")
            f.write(cnn_metrics["classification_report"])
            f.write("\n\n")
        if resnet_metrics:
            f.write("==================================================\n")
            f.write("RESNET18 CLASSIFICATION REPORT\n")
            f.write("==================================================\n")
            f.write(resnet_metrics["classification_report"])
            
    print(f"\nClassification reports and metrics CSV saved in:\n{REPORTS_DIR}")
    
    # 7. Decide best model to generate galleries and unseen testing
    # We will use the model with the highest validation accuracy
    cnn_val_acc = cnn_checkpoint["val_acc"] if cnn_checkpoint else 0.0
    resnet_val_acc = resnet_checkpoint["val_acc"] if resnet_checkpoint else 0.0
    
    if resnet_val_acc >= cnn_val_acc and resnet_checkpoint:
        best_model = resnet_model
        best_name = "ResNet18"
        best_metrics = resnet_metrics
        # last conv block of resnet18 is resnet18.layer4[-1].conv2
        target_layer = resnet_model.layer4[-1].conv2
    elif cnn_checkpoint:
        best_model = cnn_model
        best_name = "BaselineCNN"
        best_metrics = cnn_metrics
        target_layer = cnn_model.get_last_conv_layer()
    else:
        print("CRITICAL ERROR: No models loaded for testing.")
        return
        
    print(f"\nSelected {best_name} (Val Acc: {max(cnn_val_acc, resnet_val_acc)*100:.2f}%) to populate galleries.")
    
    # Run gallery generation and unseen testing
    create_prediction_galleries(
        best_model, best_name, image_paths, true_labels, 
        best_metrics["predictions"], best_metrics["confidences"], 
        target_layer, device
    )
    
    run_unseen_testing(
        best_model, best_name, image_paths, true_labels, 
        target_layer, device
    )
    
if __name__ == "__main__":
    evaluate_all()
