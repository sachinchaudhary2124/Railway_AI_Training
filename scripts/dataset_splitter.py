import random
import shutil
from pathlib import Path
from scripts.config import PROCESSED_DIR, SPLITS_DIR, SPLIT_RATIOS, RANDOM_SEED
from scripts.utils import setup_directories

def split_dataset():
    """
    Splits the standardized real images in PROCESSED_DIR into train, val, and test splits.
    Applies a stratified approach (per-class split).
    Moves images to:
    - dataset/splits/train/[class_name]/
    - dataset/splits/val/[class_name]/
    - dataset/splits/test/[class_name]/
    Val and Test contain only real images.
    Returns a dict containing the counts per class and split.
    """
    print("\n[Step 5] Splitting Dataset (Stratified)...")
    
    # Setup directories for train, val, test
    setup_directories([SPLITS_DIR], clear=True)
    for split in ["train", "val", "test"]:
        for class_folder in PROCESSED_DIR.iterdir():
            if class_folder.is_dir():
                (SPLITS_DIR / split / class_folder.name).mkdir(parents=True, exist_ok=True)
                
    # Track split details
    split_counts = {}
    
    # Set seed for reproducibility
    random.seed(RANDOM_SEED)
    
    for class_folder in PROCESSED_DIR.iterdir():
        if not class_folder.is_dir():
            continue
            
        class_name = class_folder.name
        
        # Get list of images and sort for deterministic sorting
        images = sorted([f for f in class_folder.iterdir() if f.is_file()])
        
        # Shuffle
        random.shuffle(images)
        
        n = len(images)
        n_train = int(n * SPLIT_RATIOS["train"])
        n_val = int(n * SPLIT_RATIOS["val"])
        n_test = n - n_train - n_val
        
        train_images = images[:n_train]
        val_images = images[n_train:n_train + n_val]
        test_images = images[n_train + n_val:]
        
        # Copy files to splits
        for img in train_images:
            shutil.copy2(img, SPLITS_DIR / "train" / class_name / img.name)
        for img in val_images:
            shutil.copy2(img, SPLITS_DIR / "val" / class_name / img.name)
        for img in test_images:
            shutil.copy2(img, SPLITS_DIR / "test" / class_name / img.name)
            
        split_counts[class_name] = {
            "total_real": n,
            "train_real": len(train_images),
            "val_real": len(val_images),
            "test_real": len(test_images)
        }
        
        print(f"Class '{class_name}': total real={n} | train={len(train_images)}, val={len(val_images)}, test={len(test_images)}")
        
    print(f"Dataset splitting completed. Files copied to splits under:\n{SPLITS_DIR}")
    return split_counts
