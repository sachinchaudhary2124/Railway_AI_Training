import numpy as np
from pathlib import Path
from PIL import Image
from scripts.config import RAW_DIR, SUPPORTED_EXTENSIONS, MIN_IMAGE_DIMENSION, BLANK_IMAGE_STD_THRESHOLD
from scripts.utils import calculate_file_hash, load_image

def analyze_raw_dataset():
    """
    Scans RAW_DIR and runs tests for:
    - Supported extensions
    - File corruption / readability
    - Image dimensions & aspect ratio
    - Extremely small images
    - Blank images (monochromatic/low variance)
    - Duplicates (hash-based, intra-class and cross-class)
    """
    records = []
    hash_groups = {}  # hash -> list of file dicts

    print("\n[Step 1] Analyzing Dataset Quality...")

    # Traverse RAW_DIR
    for class_folder in RAW_DIR.iterdir():
        if not class_folder.is_dir():
            continue
        
        class_name = class_folder.name
        
        for file_path in class_folder.iterdir():
            if not file_path.is_file():
                continue
                
            suffix = file_path.suffix.lower()
            file_size_bytes = file_path.stat().st_size
            
            # Record basic info
            file_info = {
                "original_path": file_path,
                "filename": file_path.name,
                "class": class_name,
                "suffix": suffix,
                "size_bytes": file_size_bytes,
                "hash": None,
                "width": 0,
                "height": 0,
                "aspect_ratio": 0.0,
                "format": "Unknown",
                "is_supported": suffix in SUPPORTED_EXTENSIONS,
                "is_corrupted": False,
                "is_small": False,
                "is_blank": False,
                "analysis_notes": []
            }
            
            # Check supported format
            if not file_info["is_supported"]:
                file_info["analysis_notes"].append("Unsupported file format")
            
            # Calculate hash (even if unsupported suffix, to check duplicate files)
            try:
                file_hash = calculate_file_hash(file_path)
                file_info["hash"] = file_hash
                hash_groups.setdefault(file_hash, []).append(file_info)
            except Exception as e:
                file_info["is_corrupted"] = True
                file_info["analysis_notes"].append(f"Failed to read file hash: {str(e)}")
                records.append(file_info)
                continue
                
            # If supported, try to load and test properties
            if file_info["is_supported"]:
                try:
                    with Image.open(file_path) as img:
                        # Test if pixel data can be loaded
                        img.verify() 
                        
                    # Re-open to read size and data (verify() closes/invalidates the file object)
                    with Image.open(file_path) as img:
                        width, height = img.size
                        file_info["width"] = width
                        file_info["height"] = height
                        file_info["aspect_ratio"] = round(width / height, 3) if height > 0 else 0.0
                        file_info["format"] = img.format
                        
                        # Check if extremely small
                        if min(width, height) < MIN_IMAGE_DIMENSION:
                            file_info["is_small"] = True
                            file_info["analysis_notes"].append(f"Extremely small dimension: {width}x{height}")
                            
                        # Check if blank (flat color check using std dev)
                        img_arr = np.array(img.convert("L"))
                        pixel_std = np.std(img_arr)
                        if pixel_std < BLANK_IMAGE_STD_THRESHOLD:
                            file_info["is_blank"] = True
                            file_info["analysis_notes"].append(f"Blank/flat color image (std={pixel_std:.2f})")
                            
                except Exception as e:
                    file_info["is_corrupted"] = True
                    file_info["analysis_notes"].append(f"Failed to open/verify image: {str(e)}")
            
            records.append(file_info)

    # Duplicate resolution logic
    # We will tag duplicate statuses
    for file_hash, group in hash_groups.items():
        if len(group) > 1:
            # We have duplicate files
            classes_in_group = {item["class"] for item in group}
            is_cross_class = len(classes_in_group) > 1
            
            # Mark all but the first item in the group as duplicates
            first_item = group[0]
            first_item_path = f"{first_item['class']}/{first_item['filename']}"
            
            for index, duplicate_item in enumerate(group):
                if index == 0:
                    if is_cross_class:
                        duplicate_item["analysis_notes"].append(f"Cross-class duplicate source (matches {len(group)-1} other files)")
                    else:
                        duplicate_item["analysis_notes"].append(f"Intra-class duplicate source (matches {len(group)-1} other files)")
                else:
                    duplicate_item["is_duplicate"] = True
                    duplicate_item["duplicate_of"] = first_item["original_path"]
                    if is_cross_class:
                        duplicate_item["analysis_notes"].append(f"Cross-class duplicate of {first_item_path}")
                    else:
                        duplicate_item["analysis_notes"].append(f"Intra-class duplicate of {first_item_path}")
        else:
            # Single file
            group[0]["is_duplicate"] = False
            group[0]["duplicate_of"] = None

    print(f"Quality Analysis Completed. Total scanned: {len(records)}")
    return records
