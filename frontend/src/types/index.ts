export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  device: string;
  pytorch_version: string;
  gpu_available: boolean;
}

export interface ModelInfoResponse {
  model_name: string;
  training_date: string;
  classes: string[];
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  image_size: string;
  model_size_mb: number;
  prediction_speed_ms: number;
}

export interface PredictionItem {
  class_name: string;
  confidence: number;
}

export interface PredictionResponse {
  prediction_id: string;
  timestamp: string;
  predicted_class: string;
  confidence: number;
  top_3_predictions: PredictionItem[];
  inference_time_ms: number;
  gradcam_path: string;
  gradcam_url: string;
  risk_score: number;
  severity: string;
  recommended_action: string;
  location_status: string;
}

export interface HistoryItem {
  prediction_id: string;
  timestamp: string;
  predicted_class: string;
  confidence: number;
  original_filename: string;
  gradcam_path: string;
  gradcam_url: string;
  inference_time_ms: number;
  risk_score: number;
  severity: string;
  recommended_action: string;
  location_status: string;
}

export interface HistoryListResponse {
  history: HistoryItem[];
  total_count: number;
}

export interface ReportItem {
  name: string;
  filename: string;
  type: string;
  url: string;
}

export interface User {
  username: string;
}
