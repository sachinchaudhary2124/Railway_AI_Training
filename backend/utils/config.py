from pathlib import Path
import os

# Base workspace directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Backend base directory
BACKEND_DIR = BASE_DIR / "backend"

# Model paths
MODEL_PATH = BASE_DIR / "models" / "best_model.pth"
METADATA_PATH = BASE_DIR / "models" / "model_metadata.json"

# Output directories
OUTPUT_DIR = BACKEND_DIR / "outputs"
GRADCAM_OUTPUT_DIR = OUTPUT_DIR / "gradcam"
LOG_DIR = BACKEND_DIR / "logs"

# Ensure all directories exist
for folder in [OUTPUT_DIR, GRADCAM_OUTPUT_DIR, LOG_DIR]:
    folder.mkdir(parents=True, exist_ok=True)

# Prediction history file
HISTORY_PATH = BACKEND_DIR / "prediction_history.json"

# JWT Authentication Config
JWT_SECRET = os.getenv("JWT_SECRET", "railway_inspection_secure_secret_key_987654321")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # 2 Hours

# Demo Account Credentials. Override these in production through environment variables.
DEMO_USER = os.getenv("RAILWAY_DEMO_USER", "admin")
DEMO_PASSWORD = os.getenv("RAILWAY_DEMO_PASSWORD", "password")

# CORS configuration for browser clients.
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
CORS_ALLOWED_ORIGIN_REGEX = os.getenv("CORS_ALLOWED_ORIGIN_REGEX", r"https://.*\.onrender\.com")
EAGER_LOAD_MODEL = os.getenv("EAGER_LOAD_MODEL", "false").lower() == "true"

# Rate Limiting (Token Bucket)
RATE_LIMIT_BURST = 15  # Max request burst
RATE_LIMIT_REFILL_RATE = 1.0  # Refills 1 token per second (60/min)

# Image pre-processing constants matching model training parameters
TARGET_SIZE = (224, 224)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Dataset Class mapping (must match model training outputs)
CLASS_NAMES = ["broken_rail", "crack", "normal", "surface_wear"]
NUM_CLASSES = len(CLASS_NAMES)
