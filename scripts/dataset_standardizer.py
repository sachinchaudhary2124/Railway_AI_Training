from pathlib import Path
from PIL import Image
from scripts.config import CLEANED_DIR, PROCESSED_DIR, TARGET_SIZE, TARGET_MODE, TARGET_FORMAT, PADDING_COLOR
from scripts.utils import setup_directories, load_image, save_image

def standardize_image_aspect_ratio(img, target_size=TARGET_SIZE, background_color=PADDING_COLOR):
    """
    Standardises a Pillow Image:
    - Converts mode to RGB (handles RGBA, grayscale, etc.)
    - Resizes keeping aspect ratio using LANCZOS
    - Pads with background color to fill target_size exactly
    """
    # 1. Convert to RGB
    if img.mode != TARGET_MODE:
        img = img.convert(TARGET_MODE)
        
    # 2. Compute aspect ratio resizing
    # copy image to avoid modifying original in-place
    img_copy = img.copy()
    img_copy.thumbnail(target_size, Image.Resampling.LANCZOS)
    
    # 3. Create background image and paste resized image in the center
    standardized = Image.new(TARGET_MODE, target_size, background_color)
    x = (target_size[0] - img_copy.width) // 2
    y = (target_size[1] - img_copy.height) // 2
    standardized.paste(img_copy, (x, y))
    
    return standardized

def standardize_dataset():
    """
    Reads images from CLEANED_DIR, standardises them (RGB, 224x224, aspect ratio, padded),
    and saves them in PROCESSED_DIR as JPEG.
    """
    print("\n[Step 3] Standardising Images...")
    
    setup_directories([PROCESSED_DIR], clear=True)
    count = 0
    
    for class_folder in CLEANED_DIR.iterdir():
        if not class_folder.is_dir():
            continue
            
        class_name = class_folder.name
        dest_class_dir = PROCESSED_DIR / class_name
        dest_class_dir.mkdir(parents=True, exist_ok=True)
        
        for image_path in class_folder.iterdir():
            if not image_path.is_file():
                continue
                
            try:
                # Load image
                img = load_image(image_path)
                
                # Standardise
                std_img = standardize_image_aspect_ratio(img)
                
                # Save as JPEG with target extension
                dest_path = dest_class_dir / f"{image_path.stem}.jpg"
                save_image(std_img, dest_path, format=TARGET_FORMAT)
                count += 1
                
            except Exception as e:
                print(f"Error standardising image {image_path.name}: {str(e)}")
                
    print(f"Standardisation completed. Processed {count} images saved to:\n{PROCESSED_DIR}")
