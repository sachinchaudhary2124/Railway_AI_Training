import io
from PIL import Image, UnidentifiedImageError
import numpy as np
import torch
from fastapi import HTTPException, status
from backend.utils.config import TARGET_SIZE, IMAGENET_MEAN, IMAGENET_STD

# Enforce a 5MB image size limit
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

class ImageService:
    """
    Handles validation, sanitization, and PyTorch pre-processing for uploaded images.
    """
    @staticmethod
    def validate_image(file_bytes: bytes, filename: str, content_type: str) -> Image.Image:
        """
        Validates the upload bytes:
        - Rejects empty uploads
        - Rejects oversized files (>5MB)
        - Rejects unsupported extensions or MIME types
        - Rejects corrupted files that PIL cannot open
        """
        # 1. Reject empty files
        if not file_bytes or len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )

        # 2. Reject oversized files
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Uploaded file exceeds the maximum allowed size of 5MB. Got: {len(file_bytes) / (1024 * 1024):.2f}MB"
            )

        # 3. Validate content type and file extension
        ext = filename.lower()[filename.rfind("."):] if "." in filename else ""
        if ext not in SUPPORTED_EXTENSIONS or not content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Supported extensions are: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

        # 4. Attempt opening and verifying the image structure
        try:
            image = Image.open(io.BytesIO(file_bytes))
            image.verify()  # Verifies the file header integrity
            # Need to re-open after verify() because verify() resets file pointer / closes file
            image = Image.open(io.BytesIO(file_bytes))
            # Load pixel data to trigger full load (check for internal corruption)
            image.load()
            return image
        except (UnidentifiedImageError, IOError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is corrupted or is not a valid image structure."
            )

    @staticmethod
    def preprocess(image: Image.Image) -> torch.Tensor:
        """
        Standardizes the PIL image:
        - Converts color scheme to RGB
        - Resizes to (224, 224) using LANCZOS
        - Normalizes pixel values using ImageNet mean/std
        - Outputs a batched torch Tensor [1, 3, 224, 224]
        """
        # Convert to RGB if format differs (e.g. grayscale, RGBA)
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        # Resize to Target Shape
        image = image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
        
        # Scale to [0, 1] range
        arr = np.array(image, dtype=np.float32) / 255.0
        
        # Normalize
        mean = np.array(IMAGENET_MEAN, dtype=np.float32)
        std = np.array(IMAGENET_STD, dtype=np.float32)
        arr_normalized = (arr - mean) / std
        
        # Transpose from HWC to CHW
        arr_transposed = np.transpose(arr_normalized, (2, 0, 1))
        
        # Convert to tensor and add batch dimension
        tensor = torch.from_numpy(arr_transposed).unsqueeze(0)
        return tensor
