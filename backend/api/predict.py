import uuid
from datetime import datetime, timezone
import torch
from fastapi import APIRouter, File, UploadFile, Depends, BackgroundTasks, Request
from backend.api.auth import get_current_user
from backend.services.model_service import model_service
from backend.services.image_service import ImageService
from backend.services.gradcam_service import GradCAMService
from backend.utils.config import CLASS_NAMES
from backend.utils.schemas import PredictionResponse, PredictionItem
from backend.utils.logger import logger
from backend.api.history import append_history_item

router = APIRouter(prefix="/predict", tags=["Prediction"])

def build_repair_priority(predicted_class: str, confidence: float) -> dict:
    """Maps model output to maintenance-oriented prioritization without inventing location data."""
    class_weights = {
        "broken_rail": 95,
        "crack": 82,
        "surface_wear": 58,
        "normal": 8,
    }
    base_score = class_weights.get(predicted_class, 50)
    risk_score = int(round(base_score * confidence))

    if predicted_class == "normal":
        severity = "nominal"
        action = "No defect detected. Continue routine monitoring."
    elif risk_score >= 80:
        severity = "critical"
        action = "Dispatch inspection crew immediately and restrict operations on the affected section."
    elif risk_score >= 55:
        severity = "high"
        action = "Schedule priority maintenance validation and monitor adjacent track segments."
    else:
        severity = "medium"
        action = "Create a maintenance ticket for manual review during the next inspection window."

    return {
        "risk_score": max(0, min(100, risk_score)),
        "severity": severity,
        "recommended_action": action,
        "location_status": "not_provided",
    }

@router.post("", response_model=PredictionResponse)
async def predict_track_image(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Uploaded track image file (.jpg, .jpeg, .png, .webp)"),
    current_user: str = Depends(get_current_user)
):
    """
    Uploads an image, validates it, performs classification, generates a Grad-CAM heatmap,
    and logs the prediction into local history.
    """
    # 1. Read file raw bytes
    file_bytes = await file.read()
    
    # 2. Validate and load PIL Image
    pil_img = ImageService.validate_image(file_bytes, file.filename, file.content_type)
    
    # 3. Preprocess image into torch tensor
    tensor = ImageService.preprocess(pil_img)
    
    # 4. Perform Inference
    logits, latency_ms = model_service.run_inference(tensor)
    
    # 5. Extract probabilities using Softmax
    probs = torch.softmax(logits, dim=1).squeeze(0)
    
    # 6. Extract predictions
    top_prob_vals, top_indices = torch.topk(probs, k=min(3, len(CLASS_NAMES)))
    
    # Top predictions list
    top_3_predictions = []
    for val, idx in zip(top_prob_vals.tolist(), top_indices.tolist()):
        top_3_predictions.append(
            PredictionItem(class_name=CLASS_NAMES[idx], confidence=val)
        )
        
    predicted_idx = top_indices[0].item()
    predicted_class = CLASS_NAMES[predicted_idx]
    confidence = top_prob_vals[0].item()
    priority = build_repair_priority(predicted_class, confidence)
    
    # 7. Generate Prediction UUID and Timestamp
    prediction_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # 8. Generate and save Grad-CAM
    gradcam_relative_path = GradCAMService.generate_and_save(
        model=model_service.model,
        input_tensor=tensor,
        original_image=pil_img,
        class_idx=predicted_idx,
        prediction_id=prediction_id
    )
    
    # 9. Formulate dynamic server-relative URL for loading the static Grad-CAM overlay image
    base_url = str(request.base_url).rstrip("/")
    gradcam_url = f"{base_url}/{gradcam_relative_path}"
    
    # 10. Queue local JSON file writing as a background task to keep API latency low
    history_item = {
        "prediction_id": prediction_id,
        "timestamp": timestamp,
        "predicted_class": predicted_class,
        "confidence": confidence,
        "original_filename": file.filename,
        "gradcam_path": gradcam_relative_path,
        "gradcam_url": gradcam_url,
        "inference_time_ms": latency_ms,
        **priority,
    }
    background_tasks.add_task(append_history_item, history_item)
    
    # 11. Log predictions info
    logger.info(
        f"Prediction complete. ID: {prediction_id} | Class: {predicted_class} | "
        f"Conf: {confidence*100:.2f}% | Latency: {latency_ms:.2f}ms"
    )
    
    # Return structured prediction data
    return PredictionResponse(
        prediction_id=prediction_id,
        timestamp=timestamp,
        predicted_class=predicted_class,
        confidence=confidence,
        top_3_predictions=top_3_predictions,
        inference_time_ms=latency_ms,
        gradcam_path=gradcam_relative_path,
        gradcam_url=gradcam_url,
        **priority,
    )
