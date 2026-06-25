import os
import json
import torch
from fastapi import APIRouter
from backend.utils.config import METADATA_PATH, MODEL_PATH, CLASS_NAMES
from backend.utils.schemas import HealthResponse, ModelInfoResponse
from backend.services.model_service import model_service
from backend.utils.logger import logger

router = APIRouter(tags=["System Info & Health"])

@router.get("/")
async def root():
    """
    Root endpoint showing standard system welcome details.
    """
    return {
        "project": "Railway AI Track Inspection System",
        "role": "FastAPI Inference Backend Service",
        "version": "1.0.0",
        "documentation": "/docs"
    }

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Inference server health status endpoint.
    """
    gpu_available = torch.cuda.is_available()
    device_name = str(model_service.device) if hasattr(model_service, "device") else ("cuda" if gpu_available else "cpu")
    
    return HealthResponse(
        status="healthy",
        model_loaded=getattr(model_service, "_initialized", False),
        device=device_name,
        pytorch_version=torch.__version__,
        gpu_available=gpu_available
    )

@router.get("/model/info", response_model=ModelInfoResponse)
async def get_model_info():
    """
    Retrieves model specifications, architectural details, and evaluation metrics.
    """
    # 1. Default fallback parameters
    model_name = "ResNet18"
    training_date = "2026-06-25 15:48:09"
    accuracy = 0.7778
    precision = 0.8381
    recall = 0.7778
    f1 = 0.7814
    image_size = "224x224"
    prediction_speed = 17.29

    # 2. Try loading from model_metadata.json
    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
                model_name = meta.get("model_name", model_name)
                training_date = meta.get("training_date", training_date)
                image_size = meta.get("image_size", image_size)
                
                metrics = meta.get("metrics", {})
                accuracy = metrics.get("test_accuracy", accuracy)
                precision = metrics.get("test_precision", precision)
                recall = metrics.get("test_recall", recall)
                f1 = metrics.get("test_f1", f1)
                prediction_speed = metrics.get("inference_time_ms_per_image", prediction_speed)
        except Exception as e:
            logger.warning(f"Failed to read model metadata JSON: {str(e)}. Using standard fallbacks.")

    # 3. Calculate model file size in Megabytes dynamically
    model_size_mb = 0.0
    if MODEL_PATH.exists():
        try:
            model_size_mb = os.path.getsize(MODEL_PATH) / (1024 * 1024)
        except Exception as e:
            logger.warning(f"Could not read model weight file size: {str(e)}")

    return ModelInfoResponse(
        model_name=model_name,
        training_date=training_date,
        classes=CLASS_NAMES,
        accuracy=round(accuracy, 4),
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        image_size=image_size,
        model_size_mb=round(model_size_mb, 2),
        prediction_speed_ms=round(prediction_speed, 2)
    )
