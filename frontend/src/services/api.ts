import axios from "axios";
import type { 
  HealthResponse, 
  ModelInfoResponse, 
  PredictionResponse, 
  HistoryListResponse, 
  HistoryItem,
  ReportItem 
} from "../types";

export const apiService = {
  /**
   * Queries FastAPI server check.
   */
  async getHealth(): Promise<HealthResponse> {
    const response = await axios.get<HealthResponse>("/health");
    return response.data;
  },

  /**
   * Queries model info.
   */
  async getModelInfo(): Promise<ModelInfoResponse> {
    const response = await axios.get<ModelInfoResponse>("/model/info");
    return response.data;
  },

  /**
   * Performs defect prediction.
   * Uploads image via multipart form-data.
   */
  async predictImage(file: File): Promise<PredictionResponse> {
    const formData = new FormData();
    formData.append("file", file);
    
    const response = await axios.post<PredictionResponse>("/predict", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  /**
   * Fetches all prediction history.
   */
  async getHistory(): Promise<HistoryListResponse> {
    const response = await axios.get<HistoryListResponse>("/history");
    return response.data;
  },

  /**
   * Fetches a specific prediction detail.
   */
  async getHistoryItem(predictionId: string): Promise<HistoryItem> {
    const response = await axios.get<HistoryItem>(`/history/${predictionId}`);
    return response.data;
  },

  /**
   * Clears prediction logs history database.
   */
  async clearHistory(): Promise<{ message: string }> {
    const response = await axios.delete<{ message: string }>("/history");
    return response.data;
  },

  /**
   * Lists available reports.
   */
  async getReports(): Promise<ReportItem[]> {
    const response = await axios.get<ReportItem[]>("/reports");
    return response.data;
  },

  /**
   * Programmatically downloads a protected report file.
   * Uses Blob responses to attach Axios authentication headers safely.
   */
  async downloadReport(filename: string): Promise<void> {
    const response = await axios.get(`/reports/${filename}`, {
      responseType: "blob",
    });
    
    const blob = new Blob([response.data], { type: (response.headers["content-type"] as string) || "application/octet-stream" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    
    // Cleanup
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }
};
export default apiService;
