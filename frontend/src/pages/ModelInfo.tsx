import React, { useState, useEffect } from "react";
import { 
  FiAward, 
  FiActivity, 
  FiLayers, 
  FiAlertTriangle,
  FiBox
} from "react-icons/fi";
import apiService from "../services/api";
import type { ModelInfoResponse } from "../types";

export const ModelInfo: React.FC = () => {
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchModelInfo = async () => {
      try {
        setError(null);
        const data = await apiService.getModelInfo();
        setModelInfo(data);
      } catch (err) {
        setError("Failed to fetch model specification details from backend service.");
      } finally {
        setLoading(false);
      }
    };
    fetchModelInfo();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 bg-background p-8 flex flex-col justify-center items-center text-gray-400">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-accent-blue mb-4"></div>
        <p className="text-sm font-medium tracking-wide">Syncing Model Weights Specs...</p>
      </div>
    );
  }

  // Format accuracy metrics from backend metadata only.
  const accuracy = modelInfo ? modelInfo.accuracy * 100 : null;
  const precision = modelInfo ? modelInfo.precision * 100 : null;
  const recall = modelInfo ? modelInfo.recall * 100 : null;
  const f1 = modelInfo ? modelInfo.f1 * 100 : null;

  return (
    <div className="flex-1 bg-background p-8 space-y-8 overflow-y-auto max-h-[calc(100vh-64px)] font-sans">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white m-0">
          Model Specifications
        </h1>
        <p className="text-xs text-gray-400 font-medium">
          Detailed metrics, class labels, image sizes, and parameters profile for the active deep learning model.
        </p>
      </div>

      {/* Error notification */}
      {error && (
        <div className="bg-accent-red/10 border border-accent-red/30 rounded-lg p-3 flex items-start space-x-3 text-accent-red text-xs">
          <FiAlertTriangle className="shrink-0 text-sm mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Model Spec Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Card 1: Core details */}
        <div className="glass-panel p-6 space-y-4 md:col-span-2">
          <div className="flex items-center space-x-2 border-b border-gray-800 pb-2">
            <FiAward className="text-accent-cyan text-lg" />
            <span className="text-xs font-bold text-gray-500 uppercase tracking-widest block">
              Neural Network Architecture
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4 text-xs font-mono">
            <div className="space-y-1 bg-gray-950 p-3 rounded-lg border border-gray-800">
              <span className="text-gray-500 uppercase tracking-wider block">Model Type</span>
              <span className="text-gray-200 font-bold text-sm">{modelInfo?.model_name || "Unavailable"}</span>
            </div>
            <div className="space-y-1 bg-gray-950 p-3 rounded-lg border border-gray-800">
              <span className="text-gray-500 uppercase tracking-wider block">Training Session End</span>
              <span className="text-gray-200 font-bold">{modelInfo?.training_date || "2026-06-25 15:48:09"}</span>
            </div>
            <div className="space-y-1 bg-gray-950 p-3 rounded-lg border border-gray-800">
              <span className="text-gray-500 uppercase tracking-wider block">Input Resolution</span>
              <span className="text-gray-200 font-bold">{modelInfo?.image_size || "N/A"}</span>
            </div>
            <div className="space-y-1 bg-gray-950 p-3 rounded-lg border border-gray-800">
              <span className="text-gray-500 uppercase tracking-wider block">Model Size on Disk</span>
              <span className="text-gray-200 font-bold">{modelInfo ? `${modelInfo.model_size_mb} MB` : "N/A"}</span>
            </div>
          </div>
        </div>

        {/* Card 2: Diagnostics latency */}
        <div className="glass-panel p-6 flex flex-col justify-between space-y-4">
          <div className="space-y-4">
            <div className="flex items-center space-x-2 border-b border-gray-800 pb-2">
              <FiActivity className="text-accent-blue text-lg" />
              <span className="text-xs font-bold text-gray-500 uppercase tracking-widest block">
                Speed Metrics
              </span>
            </div>
            <div className="text-center bg-gray-950 p-5 rounded-xl border border-gray-800/80">
              <span className="text-[10px] text-gray-500 uppercase font-bold tracking-wider block mb-1">
                Average Inference Speed
              </span>
              <span className="text-3xl font-extrabold text-accent-cyan tracking-tight font-mono">
                {modelInfo ? `${modelInfo.prediction_speed_ms.toFixed(1)} ms` : "N/A"}
              </span>
            </div>
          </div>
          <span className="text-[9px] text-gray-500 font-semibold tracking-wider text-center block uppercase">
            Includes image scaling & transforms
          </span>
        </div>

        {/* Card 3: Performance metrics */}
        <div className="glass-panel p-6 space-y-4 md:col-span-3">
          <div className="flex items-center space-x-2 border-b border-gray-800 pb-2">
            <FiLayers className="text-accent-emerald text-lg" />
            <span className="text-xs font-bold text-gray-500 uppercase tracking-widest block">
              Validation Diagnostics Accuracy
            </span>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 text-center">
            <div className="bg-gray-950 p-4 rounded-xl border border-gray-800/60 space-y-1">
              <span className="text-[10px] text-gray-500 uppercase font-bold tracking-wider block">Accuracy</span>
              <span className="text-2xl font-extrabold text-white font-mono">{accuracy !== null ? `${accuracy.toFixed(2)}%` : "N/A"}</span>
            </div>
            <div className="bg-gray-950 p-4 rounded-xl border border-gray-800/60 space-y-1">
              <span className="text-[10px] text-gray-500 uppercase font-bold tracking-wider block">Precision</span>
              <span className="text-2xl font-extrabold text-white font-mono">{precision !== null ? `${precision.toFixed(2)}%` : "N/A"}</span>
            </div>
            <div className="bg-gray-950 p-4 rounded-xl border border-gray-800/60 space-y-1">
              <span className="text-[10px] text-gray-500 uppercase font-bold tracking-wider block">Recall</span>
              <span className="text-2xl font-extrabold text-white font-mono">{recall !== null ? `${recall.toFixed(2)}%` : "N/A"}</span>
            </div>
            <div className="bg-gray-950 p-4 rounded-xl border border-gray-800/60 space-y-1">
              <span className="text-[10px] text-gray-500 uppercase font-bold tracking-wider block">F1 Score</span>
              <span className="text-2xl font-extrabold text-white font-mono">{f1 !== null ? `${f1.toFixed(2)}%` : "N/A"}</span>
            </div>
          </div>
        </div>

        {/* Card 4: Classes target mapping */}
        <div className="glass-panel p-6 space-y-4 md:col-span-3">
          <div className="flex items-center space-x-2 border-b border-gray-800 pb-2">
            <FiBox className="text-yellow-500 text-lg" />
            <span className="text-xs font-bold text-gray-500 uppercase tracking-widest block">
              Recognized Classification Targets
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {modelInfo?.classes.map((cls) => (
              <div 
                key={cls}
                className="bg-gray-950 py-3 px-4 rounded-xl border border-gray-800 hover:border-gray-700 transition-colors duration-200 text-center font-bold text-xs uppercase tracking-wider text-gray-300"
              >
                {cls.replace("_", " ")}
              </div>
            )) || ["broken_rail", "crack", "normal", "surface_wear"].map((cls) => (
              <div 
                key={cls}
                className="bg-gray-950 py-3 px-4 rounded-xl border border-gray-800 text-center font-bold text-xs uppercase tracking-wider text-gray-400"
              >
                {cls.replace("_", " ")}
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};
export default ModelInfo;
