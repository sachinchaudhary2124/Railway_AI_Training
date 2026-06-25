import os
import shutil
import hashlib
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

def setup_directories(directories, clear=True):
    """Creates directories, option to clear existing directories."""
    for directory in directories:
        directory_path = Path(directory)
        if clear and directory_path.exists():
            # Never delete RAW_DIR
            if "dataset/raw" not in str(directory_path.as_posix()):
                shutil.rmtree(directory_path)
        directory_path.mkdir(parents=True, exist_ok=True)

def calculate_file_hash(filepath):
    """Calculates MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def load_image(filepath):
    """Safely loads an image in RGB mode."""
    with Image.open(filepath) as img:
        img.load()  # Read full data into memory
        return img

def save_image(image, filepath, format="JPEG", quality=95):
    """Safely saves an image to the path, creating parents if needed."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    image.save(filepath, format=format, quality=quality)

def plot_class_distribution(counts, filepath, title="Class Distribution"):
    """Plots final class distribution and saves it."""
    plt.figure(figsize=(8, 5))
    classes = list(counts.keys())
    values = list(counts.values())
    
    # Premium styling
    colors = ['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78']
    plt.bar(classes, values, color=colors, edgecolor='grey', width=0.6)
    
    plt.title(title, fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Classes', fontsize=12, labelpad=10)
    plt.ylabel('Image Count', fontsize=12, labelpad=10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add counts above bars
    for i, v in enumerate(values):
        plt.text(i, v + 5, str(v), ha='center', fontweight='bold', color='black')
        
    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()

def plot_before_after_distribution(before, after, filepath):
    """Plots before vs after balancing distributions side-by-side."""
    classes = sorted(list(before.keys()))
    before_vals = [before[c] for c in classes]
    after_vals = [after[c] for c in classes]
    
    x = np.arange(len(classes))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Elegant colors
    rects1 = ax.bar(x - width/2, before_vals, width, label='Before Balancing (Real)', color='#3498db')
    rects2 = ax.bar(x + width/2, after_vals, width, label='After Balancing (Real + Synthetic)', color='#2ecc71')
    
    ax.set_ylabel('Image Count', fontsize=12)
    ax.set_title('Class Distribution: Before vs After Balancing', fontsize=14, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(classes, fontsize=11)
    ax.legend(frameon=True, facecolor='white', edgecolor='none', fontsize=11)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    
    # Add values on top of bars
    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontweight='bold')
            
    autolabel(rects1)
    autolabel(rects2)
    
    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()
