from pydantic import BaseModel, Field
from typing import List, Optional

# --- Authentication Schemas ---
class LoginRequest(BaseModel):
    username: str = Field(..., description="The admin username", example="admin")
    password: str = Field(..., description="The admin password", example="password")

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="The generated JWT access token")
    token_type: str = Field("bearer", description="The token type prefix")

# --- Health & Info Schemas ---
class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall server status", example="healthy")
    model_loaded: bool = Field(..., description="True if the PyTorch model loaded successfully", example=True)
    device: str = Field(..., description="Inference device (cuda or cpu)", example="cuda")
    pytorch_version: str = Field(..., description="Installed PyTorch version", example="2.5.1+cu121")
    gpu_available: bool = Field(..., description="Is PyTorch GPU (CUDA) available", example=True)

class ModelInfoResponse(BaseModel):
    model_name: str = Field(..., description="Underlying architecture name", example="ResNet18")
    training_date: str = Field(..., description="Date/Time when training completed", example="2026-06-25 15:48:09")
    classes: List[str] = Field(..., description="The labels that the model is trained to predict")
    accuracy: float = Field(..., description="Overall accuracy of the model on the test dataset", example=0.7778)
    precision: float = Field(..., description="Weighted precision metric", example=0.8381)
    recall: float = Field(..., description="Weighted recall metric", example=0.7778)
    f1: float = Field(..., description="Weighted F1-score metric", example=0.7814)
    image_size: str = Field(..., description="Resolution model expects (width x height)", example="224x224")
    model_size_mb: float = Field(..., description="Size of model parameters weight file on disk in Megabytes", example=106.79)
    prediction_speed_ms: float = Field(..., description="Average inference latency in milliseconds per image", example=17.29)

# --- Prediction API Schemas ---
class PredictionItem(BaseModel):
    class_name: str = Field(..., description="Name of predicted class label", example="crack")
    confidence: float = Field(..., description="Probability of predicted class (0.0 to 1.0)", example=0.8543)

class PredictionResponse(BaseModel):
    prediction_id: str = Field(..., description="Unique UUID for this prediction", example="4d693bfb-1175-4c9f-8be3-ee83359d95f8")
    timestamp: str = Field(..., description="ISO 8601 formatted time of prediction", example="2026-06-25T16:18:00.123456")
    predicted_class: str = Field(..., description="Class name with the highest confidence", example="crack")
    confidence: float = Field(..., description="Confidence score for the winning class (0.0 to 1.0)", example=0.8543)
    top_3_predictions: List[PredictionItem] = Field(..., description="Details of the top 3 class predictions sorted by confidence")
    inference_time_ms: float = Field(..., description="Time taken to preprocess and run model prediction in milliseconds", example=15.6)
    gradcam_path: str = Field(..., description="Local system path to generated Grad-CAM heatmap overlay", example="backend/outputs/gradcam/gradcam_4d693bfb.jpg")
    gradcam_url: str = Field(..., description="Endpoint URL to fetch/embed the Grad-CAM heatmap overlay image", example="/static/gradcam/gradcam_4d693bfb.jpg")
    risk_score: int = Field(..., ge=0, le=100, description="Operational repair priority score derived from defect class and confidence")
    severity: str = Field(..., description="Operational severity bucket", example="critical")
    recommended_action: str = Field(..., description="Maintenance action recommended for the detected class and confidence")
    location_status: str = Field("not_provided", description="Geospatial metadata status for this inspection")

# --- History Schemas ---
class HistoryItem(BaseModel):
    prediction_id: str = Field(..., description="UUID identifying this prediction")
    timestamp: str = Field(..., description="Timestamp of inference")
    predicted_class: str = Field(..., description="Winning defect label")
    confidence: float = Field(..., description="Winning confidence")
    original_filename: str = Field(..., description="Uploaded original filename")
    gradcam_path: str = Field(..., description="Local path to Grad-CAM heatmap")
    gradcam_url: str = Field(..., description="Static URL to Grad-CAM heatmap")
    inference_time_ms: float = Field(..., description="Latency of inference in milliseconds")
    risk_score: int = Field(0, ge=0, le=100, description="Operational repair priority score")
    severity: str = Field("unknown", description="Operational severity bucket")
    recommended_action: str = Field("", description="Maintenance action recommended for the prediction")
    location_status: str = Field("not_provided", description="Geospatial metadata status")

class HistoryListResponse(BaseModel):
    history: List[HistoryItem] = Field(..., description="Array of prediction logs")
    total_count: int = Field(..., description="Total count of items in history")

class MessageResponse(BaseModel):
    message: str = Field(..., description="Operational status message response", example="Success")

# --- Reports Schemas ---
class ReportItem(BaseModel):
    name: str = Field(..., description="Human-readable title of report")
    filename: str = Field(..., description="Filename of report under the reports folder")
    type: str = Field(..., description="File format type (e.g. markdown, csv, image)")
    url: str = Field(..., description="Dynamic download link for client app")
