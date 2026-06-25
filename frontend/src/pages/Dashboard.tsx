import React, { useState, useEffect } from "react";
import { 
  FiActivity, 
  FiCpu, 
  FiFileText, 
  FiTrendingUp, 
  FiAward, 
  FiDatabase 
} from "react-icons/fi";
import { motion } from "framer-motion";
import apiService from "../services/api";
import { StatCard } from "../components/StatCard";
import type { HealthResponse, ModelInfoResponse, HistoryListResponse } from "../types";

export const Dashboard: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [modelInfo, setModelInfo] = useState<ModelInfoResponse | null>(null);
  const [history, setHistory] = useState<HistoryListResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [apiError, setApiError] = useState<boolean>(false);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setApiError(false);
        const [healthRes, modelRes, historyRes] = await Promise.all([
          apiService.getHealth(),
          apiService.getModelInfo(),
          apiService.getHistory(),
        ]);
        setHealth(healthRes);
        setModelInfo(modelRes);
        setHistory(historyRes);
      } catch (err) {
        setApiError(true);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
    // Poll data every 15s to keep dashboard fresh
    const interval = setInterval(fetchDashboardData, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex-1 bg-background p-8 flex flex-col justify-center items-center text-gray-400">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-accent-blue mb-4"></div>
        <p className="text-sm font-medium tracking-wide">Syncing Telemetry Metrics...</p>
      </div>
    );
  }

  // Calculate dynamic stats
  const predictionsCount = history?.total_count ?? 0;
  
  const averageConfidence = history && history.history.length > 0
    ? (history.history.reduce((sum, item) => sum + item.confidence, 0) / history.history.length) * 100
    : 0;

  const testAccuracy = modelInfo ? modelInfo.accuracy * 100 : null;
  const isOnline = !apiError && health?.status === "healthy";

  return (
    <div className="flex-1 bg-background p-8 space-y-8 overflow-y-auto max-h-[calc(100vh-64px)]">
      {/* 1. Header welcome */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-2 sm:space-y-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white m-0">
            System Operations Dashboard
          </h1>
          <p className="text-xs text-gray-400 font-medium">
            Live telemetry, defect metrics overview, and inspection statistics.
          </p>
        </div>

        <div className="text-[10px] text-gray-500 uppercase tracking-widest font-mono bg-gray-950 px-3 py-1.5 rounded border border-gray-800 self-start sm:self-center">
          Terminal ID: IR-NDLS-01
        </div>
      </div>

      {/* 2. Error Banner */}
      {apiError && (
        <div className="bg-accent-red/10 border border-accent-red/30 rounded-xl p-4 flex items-center justify-between text-accent-red text-xs">
          <div>
            <span className="font-bold block uppercase tracking-wider mb-1">Inference API Link Fault</span>
            <span>Could not establish data link with backend service. Retrying query automatically...</span>
          </div>
          <div className="animate-pulse h-2.5 w-2.5 rounded-full bg-accent-red"></div>
        </div>
      )}

      {/* 3. Metrics Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <StatCard
          title="System Link Status"
          value={isOnline ? "ONLINE" : "OFFLINE"}
          icon={<FiActivity className="text-lg" />}
          color={isOnline ? "emerald" : "red"}
          subtitle={isOnline ? `Ping latency: Stable` : "Service unreachable"}
        />

        <StatCard
          title="Inference Core"
          value={health?.model_loaded ? "ACTIVE" : "INACTIVE"}
          icon={<FiCpu className="text-lg" />}
          color={health?.model_loaded ? "blue" : "yellow"}
          subtitle={isOnline ? `Device: ${health?.device.toUpperCase()}` : "Device offline"}
        />

        <StatCard
          title="Trained Model"
          value={modelInfo?.model_name || "Unavailable"}
          icon={<FiAward className="text-lg" />}
          color="cyan"
          subtitle={testAccuracy !== null ? `Best Test Accuracy: ${testAccuracy.toFixed(2)}%` : "Model metadata unavailable"}
        />

        <StatCard
          title="Predictions Logged"
          value={predictionsCount}
          icon={<FiDatabase className="text-lg" />}
          color="blue"
          subtitle="Logs stored in local JSON database"
        />

        <StatCard
          title="Average Confidence"
          value={predictionsCount > 0 ? `${averageConfidence.toFixed(1)}%` : "N/A"}
          icon={<FiTrendingUp className="text-lg" />}
          color={averageConfidence > 80 ? "emerald" : averageConfidence > 60 ? "yellow" : "cyan"}
          subtitle={predictionsCount > 0 ? `Calculated from ${predictionsCount} logs` : "No predictions analyzed yet"}
        />

        <StatCard
          title="Telemetry Data"
          value={modelInfo?.image_size || "N/A"}
          icon={<FiFileText className="text-lg" />}
          color="cyan"
          subtitle={modelInfo?.image_size ? `Image size: ${modelInfo.image_size}` : "Awaiting model metadata"}
        />
      </div>

      {/* 4. Telemetry overview panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Core telemetry specs */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="glass-panel p-6 space-y-4"
        >
          <span className="text-xs font-bold text-gray-500 uppercase tracking-widest block border-b border-gray-800 pb-2">
            Inference System Telemetry
          </span>
          <div className="grid grid-cols-2 gap-4 text-xs font-mono">
            <div className="space-y-1 bg-gray-950 p-2.5 rounded border border-gray-800">
              <span className="text-gray-500 uppercase tracking-wider block">PyTorch Version</span>
              <span className="text-gray-300 font-bold">{health?.pytorch_version || "N/A"}</span>
            </div>
            <div className="space-y-1 bg-gray-950 p-2.5 rounded border border-gray-800">
              <span className="text-gray-500 uppercase tracking-wider block">GPU Available</span>
              <span className={`font-bold ${health?.gpu_available ? "text-accent-emerald" : "text-gray-400"}`}>
                {health?.gpu_available ? "YES (CUDA Active)" : "NO (CPU Fallback)"}
              </span>
            </div>
            <div className="space-y-1 bg-gray-950 p-2.5 rounded border border-gray-800">
              <span className="text-gray-500 uppercase tracking-wider block">Model Size</span>
              <span className="text-gray-300 font-bold">
                {modelInfo ? `${modelInfo.model_size_mb} MB` : "N/A"}
              </span>
            </div>
            <div className="space-y-1 bg-gray-950 p-2.5 rounded border border-gray-800">
              <span className="text-gray-500 uppercase tracking-wider block">Prediction Latency</span>
              <span className="text-gray-300 font-bold">
                {modelInfo ? `${modelInfo.prediction_speed_ms} ms` : "N/A"}
              </span>
            </div>
          </div>
        </motion.div>

        {/* Operational guide */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="glass-panel p-6 flex flex-col justify-between space-y-4"
        >
          <div className="space-y-3">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-widest block border-b border-gray-800 pb-2">
              Command Centre Operator Guide
            </span>
            <ul className="text-xs text-gray-400 space-y-2 list-disc pl-4 leading-relaxed">
              <li>
                Navigate to <strong className="text-gray-200">Track Inspection</strong> to trigger predictions on railway sleeper and rail image uploads.
              </li>
              <li>
                Verify <strong className="text-accent-cyan">Grad-CAM Overlay</strong> maps to review features selected by the deep network for anomalies detection.
              </li>
              <li>
                View complete history records and wipe logs database in the <strong className="text-gray-200">Inference History</strong> module.
              </li>
              <li>
                Download compiled performance metrics and classification documents inside <strong className="text-gray-200">Inspection Reports</strong>.
              </li>
            </ul>
          </div>
          <div className="text-[10px] text-gray-600 bg-gray-950/40 p-2 rounded text-center border border-gray-800/40 font-semibold tracking-wider uppercase mt-4">
            Security Classification: Operational Asset Diagnostics
          </div>
        </motion.div>
      </div>
    </div>
  );
};
export default Dashboard;
