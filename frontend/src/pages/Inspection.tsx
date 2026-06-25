import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  FiUploadCloud, 
  FiAlertTriangle, 
  FiCheckCircle,
  FiZap,
  FiRotateCcw,
  FiHelpCircle
} from "react-icons/fi";
import apiService from "../services/api";
import CompareSlider from "../components/CompareSlider";
import type { PredictionResponse } from "../types";

export const Inspection: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);

  // 1. File validation check
  const validateAndSetFile = (file: File) => {
    setError(null);
    const validExtensions = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
    
    if (!validExtensions.includes(file.type)) {
      setError("Unsupported file format. Please upload PNG, JPEG, or WEBP.");
      return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
      setError("File exceeds the maximum 5MB size limit.");
      return;
    }
    
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setPrediction(null);
  };

  // 2. Custom drag event handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  // 3. Trigger API analysis
  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setAnalyzing(true);
    setError(null);
    try {
      const response = await apiService.predictImage(selectedFile);
      setPrediction(response);
    } catch (err: any) {
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Inference failed. Check if backend API is online.");
      }
    } finally {
      setAnalyzing(false);
    }
  };

  // 4. Reset states
  const handleReset = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setPrediction(null);
    setError(null);
  };

  return (
    <div className="flex-1 bg-background p-8 space-y-8 overflow-y-auto max-h-[calc(100vh-64px)]">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white m-0">
          Track Inspection Scanner
        </h1>
        <p className="text-xs text-gray-400 font-medium">
          Upload track section images to perform automated classification and anomaly activation overlays.
        </p>
      </div>

      {/* Main Workspace Layout split into upload-action and preview-results */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 items-start">
        
        {/* Left Column: Upload Panels & Controls */}
        <div className="space-y-6">
          <div className="glass-panel p-6 space-y-6">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-widest block border-b border-gray-800 pb-2">
              Diagnostics Input Panel
            </span>

            {/* Error notifications */}
            {error && (
              <div className="bg-accent-red/10 border border-accent-red/30 rounded-lg p-3.5 flex items-start space-x-3 text-accent-red text-xs">
                <FiAlertTriangle className="shrink-0 text-sm mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {/* File Drag and Drop zone */}
            {!selectedFile ? (
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={`relative border-2 border-dashed rounded-xl h-64 flex flex-col items-center justify-center p-6 transition-all duration-200 select-none ${
                  isDragOver
                    ? "border-accent-blue bg-accent-blue/5 shadow-inner"
                    : "border-gray-800 hover:border-gray-700 bg-gray-950/40"
                }`}
              >
                <input
                  type="file"
                  id="track-file"
                  accept="image/png, image/jpeg, image/jpg, image/webp"
                  onChange={handleFileSelect}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                
                <div className="text-center space-y-4 pointer-events-none">
                  <div className="mx-auto h-12 w-12 rounded-xl bg-gray-900 border border-gray-800 flex items-center justify-center text-gray-400">
                    <FiUploadCloud className="text-2xl" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-200">
                      Drag & Drop Image Here
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      or click to browse local folders
                    </p>
                  </div>
                  <div className="text-[10px] text-gray-600 font-medium uppercase tracking-widest">
                    PNG, JPEG, WEBP | MAX SIZE 5MB
                  </div>
                </div>
              </div>
            ) : (
              /* Image Pre-analysis Preview */
              <div className="space-y-4">
                <div className="relative aspect-video w-full rounded-xl overflow-hidden border border-gray-800 bg-gray-950">
                  <img
                    src={previewUrl!}
                    alt="Preview Upload"
                    className="h-full w-full object-cover"
                  />
                  <div className="absolute top-3 left-3 bg-gray-900/80 border border-gray-800 px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-widest text-gray-300">
                    Raw Preview
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-gray-400 font-mono bg-gray-950 p-2.5 rounded border border-gray-800">
                  <span className="truncate max-w-[200px]">{selectedFile.name}</span>
                  <span>{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</span>
                </div>

                {/* Operation controls */}
                <div className="flex items-center space-x-4">
                  <button
                    onClick={handleReset}
                    disabled={analyzing}
                    className="btn-secondary flex-1 py-2 flex items-center justify-center space-x-2"
                  >
                    <FiRotateCcw />
                    <span>Clear File</span>
                  </button>
                  
                  {!prediction && (
                    <button
                      onClick={handleAnalyze}
                      disabled={analyzing}
                      className="btn-primary flex-1 py-2 flex items-center justify-center space-x-2"
                    >
                      <FiZap className="animate-pulse" />
                      <span>Trigger Diagnostic</span>
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* AI Loader overlay */}
          <AnimatePresence>
            {analyzing && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="glass-panel p-6 flex flex-col items-center justify-center space-y-4 overflow-hidden border-accent-blue/30"
              >
                <div className="h-10 w-10 border-t-2 border-b-2 border-accent-cyan rounded-full animate-spin"></div>
                <div className="text-center space-y-1.5">
                  <p className="text-sm font-bold tracking-wide text-white">AI Inference Diagnostic Running...</p>
                  <p className="text-xs text-gray-500 font-mono uppercase tracking-widest">
                    Extracting features & calculating backprop activation maps
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Right Column: Diagnostic Results Dashboard */}
        <AnimatePresence>
          {prediction && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="space-y-6"
            >
              <div className="glass-panel p-6 space-y-6">
                <span className="text-xs font-bold text-gray-500 uppercase tracking-widest block border-b border-gray-800 pb-2">
                  Diagnostic Scan Results
                </span>

                {/* Main Predicted class card */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-950 p-4 rounded-xl border border-gray-800/80 flex flex-col justify-between">
                    <span className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">
                      Defect Classification
                    </span>
                    <div className="mt-2">
                      <span className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                        prediction.predicted_class === "normal"
                          ? "bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/20"
                          : "bg-accent-red/10 text-accent-red border border-accent-red/20"
                      }`}>
                        {prediction.predicted_class === "normal" ? (
                          <>
                            <FiCheckCircle />
                            <span>Normal</span>
                          </>
                        ) : (
                          <>
                            <FiAlertTriangle />
                            <span>{prediction.predicted_class.replace("_", " ")}</span>
                          </>
                        )}
                      </span>
                    </div>
                  </div>

                  <div className="bg-gray-950 p-4 rounded-xl border border-gray-800/80 flex flex-col justify-between">
                    <span className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">
                      Model Confidence
                    </span>
                    <div className="mt-2">
                      <span className="text-2xl font-extrabold text-white tracking-tight">
                        {(prediction.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Sub metrics stats */}
                <div className="grid grid-cols-2 gap-4 text-xs font-mono bg-gray-950/60 p-4 rounded-xl border border-gray-800/40">
                  <div className="space-y-1">
                    <span className="text-gray-500 uppercase tracking-wider block">Inference Latency</span>
                    <span className="text-gray-300 font-bold">{prediction.inference_time_ms.toFixed(2)} ms</span>
                  </div>
                  <div className="space-y-1">
                    <span className="text-gray-500 uppercase tracking-wider block">Scan Timestamp</span>
                    <span className="text-gray-300 font-bold">
                      {new Date(prediction.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="space-y-1 col-span-2 pt-2 border-t border-gray-800">
                    <span className="text-gray-500 uppercase tracking-wider block">Prediction ID</span>
                    <span className="text-[10px] text-gray-400 select-all">{prediction.prediction_id}</span>
                  </div>
                </div>

                {/* Repair priority computed by backend from prediction class and confidence */}
                <div className="bg-gray-950/60 p-4 rounded-xl border border-gray-800/40 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Automated Repair Priority
                    </span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full border uppercase font-bold tracking-wider ${
                      prediction.severity === "critical"
                        ? "bg-accent-red/10 text-accent-red border-accent-red/30"
                        : prediction.severity === "high"
                        ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/30"
                        : prediction.severity === "nominal"
                        ? "bg-accent-emerald/10 text-accent-emerald border-accent-emerald/30"
                        : "bg-accent-blue/10 text-accent-blue border-accent-blue/30"
                    }`}>
                      {prediction.severity}
                    </span>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs font-mono mb-1">
                      <span className="text-gray-500 uppercase tracking-wider">Risk Score</span>
                      <span className="text-gray-300 font-bold">{prediction.risk_score}/100</span>
                    </div>
                    <div className="h-2 w-full bg-gray-900 rounded-full overflow-hidden border border-gray-800">
                      <div
                        className={`h-full ${prediction.predicted_class === "normal" ? "bg-accent-emerald" : "bg-accent-red"}`}
                        style={{ width: `${prediction.risk_score}%` }}
                      />
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 leading-relaxed">
                    {prediction.recommended_action}
                  </p>
                  <p className="text-[10px] text-gray-600 uppercase tracking-wider font-semibold">
                    Geospatial metadata: {prediction.location_status.replace("_", " ")}
                  </p>
                </div>

                {/* Top 3 predictions bars list */}
                <div className="space-y-3.5">
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block">
                    Softmax Probabilities Distribution
                  </span>
                  
                  <div className="space-y-2">
                    {prediction.top_3_predictions.map((pred, i) => (
                      <div key={i} className="space-y-1">
                        <div className="flex justify-between text-xs font-mono">
                          <span className="capitalize text-gray-300">
                            {pred.class_name.replace("_", " ")}
                          </span>
                          <span className="text-gray-400">{(pred.confidence * 100).toFixed(2)}%</span>
                        </div>
                        <div className="h-2 w-full bg-gray-900 rounded-full overflow-hidden border border-gray-800">
                          <div 
                            className={`h-full rounded-full ${
                              pred.class_name === "normal"
                                ? "bg-accent-emerald"
                                : pred.confidence > 0.8
                                ? "bg-accent-red"
                                : "bg-accent-blue"
                            }`}
                            style={{ width: `${pred.confidence * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Grad-CAM Compare Slider panel */}
              <div className="glass-panel p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-gray-800 pb-2">
                  <span className="text-xs font-bold text-gray-500 uppercase tracking-widest block">
                    Grad-CAM Activation Segmentation
                  </span>
                  <div className="flex items-center space-x-1.5 text-[10px] text-gray-500 font-semibold uppercase tracking-wider">
                    <FiHelpCircle className="text-accent-cyan" />
                    <span>Explain map</span>
                  </div>
                </div>

                {/* Compare Slider display */}
                <CompareSlider
                  originalUrl={previewUrl!}
                  overlayUrl={prediction.gradcam_url}
                  aspectRatioClassName="aspect-square w-full"
                />

                <p className="text-[11px] text-gray-400 leading-relaxed font-medium bg-gray-950 p-3 rounded-lg border border-gray-800">
                  <strong className="text-accent-cyan">Explainability Note:</strong> The heatmap highlights the specific region used by the neural network weights to reach the classification score above. Red areas represent highest feature alignment.
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};
export default Inspection;
