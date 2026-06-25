from pathlib import Path

# -------------------------------------------------
# Directory Paths
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "dataset/raw"
CLEANED_DIR = BASE_DIR / "dataset/cleaned"
PROCESSED_DIR = BASE_DIR / "dataset/processed"
SPLITS_DIR = BASE_DIR / "dataset/splits"
REPORTS_DIR = BASE_DIR / "reports"
MODELS_DIR = BASE_DIR / "models"

# Ensure dirs list
DIRECTORIES = [CLEANED_DIR, PROCESSED_DIR, SPLITS_DIR, REPORTS_DIR, MODELS_DIR]

# -------------------------------------------------
# Image Standardisation Settings
# -------------------------------------------------
TARGET_SIZE = (224, 224)
TARGET_MODE = "RGB"
TARGET_FORMAT = "JPEG"
TARGET_EXTENSION = ".jpg"
PADDING_COLOR = (0, 0, 0)  # Black border

# -------------------------------------------------
# Quality Check Settings
# -------------------------------------------------
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
MIN_IMAGE_DIMENSION = 64  # Flag images with width or height below this
BLANK_IMAGE_STD_THRESHOLD = 5.0  # Flat color check

# -------------------------------------------------
# Dataset Splitting Settings
# -------------------------------------------------
SPLIT_RATIOS = {
    "train": 0.8,
    "val": 0.1,
    "test": 0.1
}
RANDOM_SEED = 42

# -------------------------------------------------
# Class Balancing Settings
# -------------------------------------------------
TARGET_IMAGES_PER_CLASS = 250

# -------------------------------------------------
# Pipeline Decisions
# -------------------------------------------------
# True will remove images found in multiple classes due to label contradiction.
REMOVE_CROSS_CLASS_DUPLICATES = True

# -------------------------------------------------
# Deep Learning Training Settings
# -------------------------------------------------
BATCH_SIZE = 32
LR_CNN = 1e-3
LR_RESNET_HEAD = 1e-3
LR_RESNET_FINETUNE = 1e-4
MAX_EPOCHS = 30
PATIENCE = 7
WEIGHT_DECAY = 1e-4

# Normalization constants (ImageNet defaults)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Dataset Classes
NUM_CLASSES = 4
CLASS_NAMES = ["broken_rail", "crack", "normal", "surface_wear"]
