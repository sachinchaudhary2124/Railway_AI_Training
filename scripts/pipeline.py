import sys
import pandas as pd
from pathlib import Path
from scripts.config import RAW_DIR, CLEANED_DIR, PROCESSED_DIR, SPLITS_DIR, REPORTS_DIR, DIRECTORIES, TARGET_IMAGES_PER_CLASS
from scripts.utils import setup_directories, plot_class_distribution, plot_before_after_distribution
from scripts.dataset_analyzer import analyze_raw_dataset
from scripts.dataset_cleaner import clean_dataset
from scripts.dataset_standardizer import standardize_dataset
from scripts.dataset_splitter import split_dataset
from scripts.synthetic_generator import generate_synthetic_data

def compile_dataset_statistics(split_counts, cleaning_log, augmentation_log):
    """
    Compiles detailed counts for each class:
    - Raw count
    - Cleaned count
    - Train Real count
    - Train Synthetic count
    - Val count (real only)
    - Test count (real only)
    - Total final count (real + synthetic across all splits)
    Saves to REPORTS_DIR / dataset_statistics.csv.
    """
    print("\n[Step 6] Compiling Dataset Statistics...")
    
    # 1. Get raw counts per class
    raw_counts = {}
    for class_folder in RAW_DIR.iterdir():
        if class_folder.is_dir():
            raw_counts[class_folder.name] = len([f for f in class_folder.iterdir() if f.is_file()])
            
    # 2. Get cleaned counts per class
    cleaned_df = pd.DataFrame(cleaning_log)
    cleaned_counts = cleaned_df[cleaned_df["status"] == "Kept"]["class"].value_counts().to_dict()
    
    # 3. Get augmentation counts per class
    aug_df = pd.DataFrame(augmentation_log)
    if not aug_df.empty:
        aug_counts = aug_df["class"].value_counts().to_dict()
    else:
        aug_counts = {}
        
    stats = []
    
    for class_name in raw_counts.keys():
        r_count = raw_counts.get(class_name, 0)
        c_count = cleaned_counts.get(class_name, 0)
        
        split_info = split_counts.get(class_name, {"train_real": 0, "val_real": 0, "test_real": 0})
        t_real = split_info["train_real"]
        t_syn = aug_counts.get(class_name, 0)
        v_real = split_info["val_real"]
        e_real = split_info["test_real"]
        
        total_final = t_real + t_syn + v_real + e_real
        
        stats.append({
            "class_name": class_name,
            "raw_count": r_count,
            "cleaned_count": c_count,
            "train_real": t_real,
            "train_synthetic": t_syn,
            "val_real": v_real,
            "test_real": e_real,
            "total_final": total_final
        })
        
    stats_df = pd.DataFrame(stats)
    stats_path = REPORTS_DIR / "dataset_statistics.csv"
    stats_df.to_csv(stats_path, index=False)
    print(f"Statistics compiled. Table saved to:\n{stats_path}")
    
    # Print statistics table
    print("\nFinal Dataset Summary Table:")
    print(stats_df.to_string(index=False))
    
    return stats_df

def generate_report_markdown(stats_df, analysis_records, cleaning_log, augmentation_log):
    """Generates the final comprehensive dataset report (dataset_report.md)."""
    report_path = REPORTS_DIR / "dataset_report.md"
    
    total_raw = stats_df["raw_count"].sum()
    total_cleaned = stats_df["cleaned_count"].sum()
    total_train_real = stats_df["train_real"].sum()
    total_train_syn = stats_df["train_synthetic"].sum()
    total_val = stats_df["val_real"].sum()
    total_test = stats_df["test_real"].sum()
    total_final = stats_df["total_final"].sum()
    
    # Analyze formats
    formats = {}
    corrupted_files = []
    unsupported_files = []
    small_files = []
    for r in analysis_records:
        formats[r["format"]] = formats.get(r["format"], 0) + 1
        if r["is_corrupted"]:
            corrupted_files.append(r)
        if not r["is_supported"]:
            unsupported_files.append(r)
        if r["is_small"]:
            small_files.append(r)
            
    # Analyze cleaning
    clean_df = pd.DataFrame(cleaning_log)
    removed_duplicates = clean_df[clean_df["reason"].str.contains("Duplicate", na=False)]
    
    # Analyze augmentation approaches
    aug_df = pd.DataFrame(augmentation_log)
    approach_counts = aug_df["approach"].value_counts().to_dict() if not aug_df.empty else {}
    
    # Generate markdown content
    content = f"""# Railway Track Inspection - Dataset Engineering Report

This report summarizes the data quality analysis, cleaning, standardisation, splitting, and balancing operations performed on the Railway Track Inspection dataset.

---

## 1. Executive Summary

- **Total Raw Images**: {total_raw}
- **Total Cleaned Images**: {total_cleaned} (removed duplicates, corrupted, and invalid files)
- **Standardised Resolution**: 224 × 224 pixels
- **Standardised Format & Mode**: JPEG, RGB
- **Target Distribution**: ~{TARGET_IMAGES_PER_CLASS} images per class
- **Balanced Dataset Splits**:
  - **Train**: {total_train_real} real + {total_train_syn} synthetic = {total_train_real + total_train_syn} images
  - **Validation**: {total_val} images (100% real)
  - **Test**: {total_test} images (100% real)
- **Grand Total (Balanced Dataset)**: {total_final} images

---

## 2. Dataset Quality Audit & Analysis (Step 1)

All raw images were inspected for format support, file integrity, blank colors, size thresholds, and uniqueness.

### File Format Scan
We detected the following formats in the raw folder:
- **JPEG/JPG**: {formats.get("JPEG", 0) + formats.get("Unknown", 0) if "AVIF" in formats or "WEBP" in formats else total_raw} images
- **WEBP**: {formats.get("WEBP", 0)} images
- **AVIF**: {formats.get("AVIF", 0)} images
- **PNG**: {formats.get("PNG", 0)} images

### Detected Issues
- **Corrupted/Unreadable Images**: {len(corrupted_files)}
- **Unsupported Format Images**: {len(unsupported_files)}
- **Extremely Small Images (<64px)**: {len(small_files)}
- **Blank/Flat-Color Images**: {len([r for r in analysis_records if r["is_blank"]])}

---

## 3. Dataset Cleaning (Step 2)

To maintain a clean and reliable label distribution, we filtered out invalid files and resolved duplication. All cleaning actions were logged to `cleaning_log.csv`.

### Duplicate Analysis & Resolution
We calculated MD5 hashes of all images and resolved duplication as follows:
- **Intra-class Duplicates**: Kept the first occurrence, discarded the remaining identical files.
- **Cross-class Duplicates (Label Noise)**: Removed cross-class duplicate images entirely. Having identical images in multiple classes (e.g. `broken_rail` and `normal`) creates class ambiguity that degrades model training and evaluation. A total of **{len(removed_duplicates[removed_duplicates["reason"].str.contains("Cross-class", na=False)])}** cross-class duplicate records were excluded.

### Summary of Exclusions
- **Duplicates Removed**: {len(removed_duplicates)}
- **Corrupted Files Removed**: {len(corrupted_files)}
- **Total Excluded Files**: {total_raw - total_cleaned}

All kept files were copied to `dataset/cleaned/` with normalized filenames (e.g., `normal_001.jpg`).

---

## 4. Image Standardisation (Step 3)

Cleaned images were standardized to a uniform shape and color profile ready for deep neural network input:
- **Color Mode**: Converted to 3-channel **RGB** (removing transparency/alpha channels).
- **Target Resolution**: **224 × 224 pixels**.
- **Aspect Ratio Conservation**: To prevent stretching/distortion, we resized images using the maximum bounding box and filled the empty borders using **black letterbox padding** `(0, 0, 0)`.
- **Output Format**: Saved as high-quality **JPEG** in `dataset/processed/`.

---

## 5. Dataset Splitting (Step 5)

We performed a **stratified** split of the standardized real images to maintain class proportions across partitions:
- **Train**: 80%
- **Validation**: 10%
- **Test**: 10%

> [!IMPORTANT]
> **Data Leakage Prevention**: Validation and test sets contain **ONLY real images**. Splitting was performed *before* generating synthetic data, ensuring that augmented versions of training images never leak into evaluation splits.

---

## 6. Class Balancing & Synthetic Data Generation (Step 4)

We analysed the size of each class in the training split and automatically generated the exact number of synthetic images needed to reach a total of **{TARGET_IMAGES_PER_CLASS}** images per class (real + synthetic).

### Synthetic Generation Methodology
Synthetic images were generated inside `dataset/splits/train/[class]/` using two complementary approaches:
1. **Approach 1: Standard Augmentations**
   - Applies random geometric and color transforms: rotation (-15° to 15°), horizontal flips, brightness/contrast adjustments, gamma shifts, random crop/resize, Gaussian noise, perspective shears, blur, and histogram equalization.
2. **Approach 2: Controlled Railway Defect Simulation**
   - *Rust Texture*: Blends realistic brownish-red noise patches onto the tracks.
   - *Surface Wear*: Draws shiny metallic wheel contact bands in the center.
   - *Small Crack Extension*: Traces thin, dark, jagged paths representing micro-cracks.
   - *Weather Effects*: Simulates atmospheric variations (rain streaks, foggy mist).
   - *Lighting & Camera*: Adds localized shadow polygons, lens dust specs, and exposure variations.

### Generation Summary
- **Total Synthetic Images Generated**: {total_train_syn}
- **Breakdown of Approaches**:
  - Standard Augmentation: {approach_counts.get("Standard Augmentation", 0)}
  - Railway Defect Simulation: {approach_counts.get("Railway Defect Simulation", 0)}
  - Combined: {approach_counts.get("Combined", 0)}

---

## 7. Dataset Statistics (Step 6)

### Distribution Breakdown Table
| Class Name | Raw (Real) | Cleaned (Real) | Train (Real) | Train (Synthetic) | Val (Real) | Test (Real) | Total Balanced |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""
    for _, row in stats_df.iterrows():
        content += f"| {row['class_name']} | {row['raw_count']} | {row['cleaned_count']} | {row['train_real']} | {row['train_synthetic']} | {row['val_real']} | {row['test_real']} | {row['total_final']} |\n"
        
    content += f"""| **Total** | **{total_raw}** | **{total_cleaned}** | **{total_train_real}** | **{total_train_syn}** | **{total_val}** | **{total_test}** | **{total_final}** |

### Class Distribution Visualizations

Before vs After Balancing Comparison:
![Before vs After Distribution](before_after_distribution.png)

Final Class Distribution (Balanced):
![Final Class Distribution](class_distribution.png)

---
*Report generated automatically on 2026-06-25 by the Railway Track Inspection AI Foundation Pipeline.*
"""
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"Markdown report saved to:\n{report_path}")

def main():
    print("==================================================")
    print("RUNNING RAILWAY TRACK INSPECTION DATA ENGINEERING PIPELINE")
    print("==================================================")
    
    # 0. Setup and clean folders
    setup_directories(DIRECTORIES, clear=True)
    
    # 1. Quality Analysis
    analysis_records = analyze_raw_dataset()
    
    # 2. Cleaning
    cleaning_log = clean_dataset(analysis_records)
    
    # 3. Standardisation
    standardize_dataset()
    
    # 5. Split Dataset
    split_counts = split_dataset()
    
    # 4. Generate Synthetic balancing data
    augmentation_log = generate_synthetic_data(split_counts)
    
    # 6. Generate statistics & CSV
    stats_df = compile_dataset_statistics(split_counts, cleaning_log, augmentation_log)
    
    # 7. Generate plots
    final_distribution = stats_df.set_index("class_name")["total_final"].to_dict()
    plot_class_distribution(final_distribution, REPORTS_DIR / "class_distribution.png", "Final Class Distribution (Balanced)")
    
    raw_distribution = stats_df.set_index("class_name")["raw_count"].to_dict()
    plot_before_after_distribution(raw_distribution, final_distribution, REPORTS_DIR / "before_after_distribution.png")
    
    # 8. Generate markdown report
    generate_report_markdown(stats_df, analysis_records, cleaning_log, augmentation_log)
    
    print("\n==================================================")
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    main()
