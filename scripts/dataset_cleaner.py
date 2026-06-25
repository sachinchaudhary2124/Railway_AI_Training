import pandas as pd
import shutil
from pathlib import Path
from scripts.config import RAW_DIR, CLEANED_DIR, REMOVE_CROSS_CLASS_DUPLICATES, REPORTS_DIR
from scripts.utils import setup_directories

def clean_dataset(analysis_records):
    """
    Cleans the raw dataset and saves results in CLEANED_DIR.
    Decides for each image:
    - Keep (renamed normalized filename)
    - Remove/Exclude (due to corruption, unsupported format, intra-class duplicate, or cross-class duplicate)
    Creates cleaning_log.csv in REPORTS_DIR.
    """
    print("\n[Step 2] Cleaning Dataset...")
    
    # Reset cleaned directory structure
    setup_directories([CLEANED_DIR], clear=True)
    
    cleaning_log = []
    
    # Identify cross-class duplicate hashes
    cross_class_hashes = set()
    hash_to_classes = {}
    for record in analysis_records:
        h = record["hash"]
        if h:
            hash_to_classes.setdefault(h, set()).add(record["class"])
            
    for h, classes in hash_to_classes.items():
        if len(classes) > 1:
            cross_class_hashes.add(h)
            
    # Track index per class for normalized renaming
    class_indices = {}
    
    # Sort analysis records to ensure deterministic file ordering
    sorted_records = sorted(analysis_records, key=lambda x: (x["class"], x["filename"]))
    
    for record in sorted_records:
        orig_path = record["original_path"]
        class_name = record["class"]
        suffix = record["suffix"]
        h = record["hash"]
        
        status = "Removed"
        reason = "OK"
        new_path = ""
        
        # 1. Check for corruption
        if record["is_corrupted"]:
            reason = "Corrupted/Unreadable image"
        # 2. Check for unsupported format
        elif not record["is_supported"]:
            reason = "Unsupported file format"
        # 3. Check for cross-class duplicate conflict
        elif h in cross_class_hashes:
            if REMOVE_CROSS_CLASS_DUPLICATES:
                reason = f"Cross-class duplicate conflict (found in classes: {sorted(list(hash_to_classes[h]))})"
            else:
                # If not removing, resolve by keeping only the first one found (by alphabetical class order)
                # We can determine if this is the first class alphabetically in the group
                sorted_classes = sorted(list(hash_to_classes[h]))
                primary_class = sorted_classes[0]
                if class_name == primary_class:
                    # Treat as potential keep (subject to intra-class duplicates)
                    pass
                else:
                    reason = f"Cross-class duplicate resolved in favor of class '{primary_class}'"
        
        # 4. Check for intra-class duplicate
        # If the hash has been seen and this specific record is flagged as a duplicate
        if reason == "OK" and record.get("is_duplicate", False):
            dup_of = record.get("duplicate_of")
            dup_of_name = f"{dup_of.parent.name}/{dup_of.name}" if dup_of else "unknown"
            reason = f"Intra-class duplicate of {dup_of_name}"
            
        # 5. If everything is OK, copy and rename
        if reason == "OK":
            status = "Kept"
            class_indices[class_name] = class_indices.get(class_name, 0) + 1
            idx = class_indices[class_name]
            
            # Format filename as normal_001.jpg
            normalized_filename = f"{class_name}_{idx:03d}{suffix}"
            dest_dir = CLEANED_DIR / class_name
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / normalized_filename
            
            # Copy file
            shutil.copy2(orig_path, dest_path)
            new_path = str(dest_path.relative_to(CLEANED_DIR.parent.parent))
            
        cleaning_log.append({
            "original_path": str(orig_path.relative_to(RAW_DIR.parent.parent)),
            "class": class_name,
            "status": status,
            "reason": reason,
            "new_path": new_path
        })
        
    # Write cleaning log to CSV
    log_df = pd.DataFrame(cleaning_log)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = REPORTS_DIR / "cleaning_log.csv"
    log_df.to_csv(log_path, index=False)
    
    # Print status counts
    print(log_df["status"].value_counts())
    print(f"Cleaning completed. Log saved to:\n{log_path}")
    
    return cleaning_log
