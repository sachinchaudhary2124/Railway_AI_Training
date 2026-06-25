from pathlib import Path
from PIL import Image
import pandas as pd

# -------------------------------------------------
# Dataset Path
# -------------------------------------------------

DATASET_PATH = Path("dataset/raw")

# -------------------------------------------------
# Supported Image Formats
# -------------------------------------------------

IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]

# -------------------------------------------------
# Store Results
# -------------------------------------------------

records = []

print("\nScanning Dataset...\n")

# -------------------------------------------------
# Scan Every Class Folder
# -------------------------------------------------

for class_folder in DATASET_PATH.iterdir():

    if not class_folder.is_dir():
        continue

    class_name = class_folder.name

    for image_path in class_folder.iterdir():

        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        try:

            with Image.open(image_path) as img:

                width, height = img.size

                records.append({
                    "Class": class_name,
                    "Image": image_path.name,
                    "Format": img.format,
                    "Width": width,
                    "Height": height,
                    "Status": "OK"
                })

        except Exception:

            records.append({
                "Class": class_name,
                "Image": image_path.name,
                "Format": "Unknown",
                "Width": 0,
                "Height": 0,
                "Status": "Corrupted"
            })

# -------------------------------------------------
# Create DataFrame
# -------------------------------------------------

df = pd.DataFrame(records)

print(df.head())

print("\n-----------------------------------")
print("Dataset Summary")
print("-----------------------------------\n")

print(df.groupby("Class").size())

print("\n-----------------------------------")
print("Image Formats")
print("-----------------------------------\n")

print(df["Format"].value_counts())

print("\n-----------------------------------")
print("Corrupted Images")
print("-----------------------------------\n")

print(df[df["Status"] == "Corrupted"])

# -------------------------------------------------
# Save Report
# -------------------------------------------------

output_path = Path("reports") / "dataset_audit.csv"

df.to_csv(output_path, index=False)

print(f"\nAudit report saved to:\n{output_path}")