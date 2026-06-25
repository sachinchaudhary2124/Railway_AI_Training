import React, { useState } from "react";
import { 
  FiTrash2, 
  FiInfo, 
  FiSliders, 
  FiCheckCircle, 
  FiAlertTriangle
} from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";
import apiService from "../services/api";

export const Settings: React.FC = () => {
  const [showWipeModal, setShowWipeModal] = useState<boolean>(false);
  const [wiping, setWiping] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [themeMode, setThemeMode] = useState<"dark" | "blue-dark">("dark");

  const handleWipeDatabase = async () => {
    setWiping(true);
    setSuccessMessage(null);
    setErrorMessage(null);
    try {
      const res = await apiService.clearHistory();
      setSuccessMessage(res.message);
      setShowWipeModal(false);
    } catch (err) {
      setErrorMessage("Failed to reset prediction history database.");
    } finally {
      setWiping(false);
    }
  };

  return (
    <div className="flex-1 bg-background p-8 space-y-8 overflow-y-auto max-h-[calc(100vh-64px)] font-sans">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white m-0">
          System Settings
        </h1>
        <p className="text-xs text-gray-400 font-medium">
          Manage local databases, styling custom theme selections, and review project spec sheets.
        </p>
      </div>

      {/* Operation notifications */}
      {successMessage && (
        <div className="bg-accent-emerald/10 border border-accent-emerald/30 rounded-lg p-3.5 flex items-start space-x-3 text-accent-emerald text-xs">
          <FiCheckCircle className="shrink-0 text-sm mt-0.5" />
          <span>{successMessage}</span>
        </div>
      )}
      
      {errorMessage && (
        <div className="bg-accent-red/10 border border-accent-red/30 rounded-lg p-3.5 flex items-start space-x-3 text-accent-red text-xs">
          <FiAlertTriangle className="shrink-0 text-sm mt-0.5" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Settings Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        
        {/* Left Column: Actions and Configurations */}
        <div className="space-y-6">
          {/* Section: Themes */}
          <div className="glass-panel p-6 space-y-4">
            <div className="flex items-center space-x-2 border-b border-gray-800 pb-2">
              <FiSliders className="text-accent-cyan text-lg" />
              <span className="text-xs font-bold text-gray-500 uppercase tracking-widest block">
                Visual Customization
              </span>
            </div>

            <div className="space-y-3">
              <label className="text-xs font-bold text-gray-400 uppercase tracking-wider block">
                Color Profile Theme
              </label>
              
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => setThemeMode("dark")}
                  className={`py-3 px-4 rounded-xl border text-xs font-bold uppercase tracking-wider transition-all duration-200 ${
                    themeMode === "dark"
                      ? "bg-accent-blue/10 border-accent-blue text-accent-blue"
                      : "bg-gray-950 border-gray-800 text-gray-400 hover:border-gray-700 hover:text-gray-300"
                  }`}
                >
                  Deep Coal Dark
                </button>
                <button
                  onClick={() => setThemeMode("blue-dark")}
                  className={`py-3 px-4 rounded-xl border text-xs font-bold uppercase tracking-wider transition-all duration-200 ${
                    themeMode === "blue-dark"
                      ? "bg-accent-cyan/10 border-accent-cyan text-accent-cyan"
                      : "bg-gray-950 border-gray-800 text-gray-400 hover:border-gray-700 hover:text-gray-300"
                  }`}
                >
                  Tactical Navy
                </button>
              </div>
            </div>
          </div>

          {/* Section: Database actions */}
          <div className="glass-panel p-6 space-y-4">
            <div className="flex items-center space-x-2 border-b border-gray-800 pb-2">
              <FiTrash2 className="text-accent-red text-lg" />
              <span className="text-xs font-bold text-gray-500 uppercase tracking-widest block">
                Log Database Operations
              </span>
            </div>

            <div className="space-y-4">
              <p className="text-xs text-gray-400 leading-relaxed">
                Clearing history removes all recorded diagnostics logs from <code className="bg-gray-950 px-1 rounded border border-gray-800 font-mono text-[10px]">prediction_history.json</code> and deletes generated Grad-CAM overlays to save local disk capacity.
              </p>
              
              <button
                onClick={() => setShowWipeModal(true)}
                className="btn-danger w-full py-2 flex items-center justify-center space-x-2 text-xs uppercase font-bold tracking-widest"
              >
                <FiTrash2 />
                <span>Reset Database Logs</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Spec sheet / about details */}
        <div className="glass-panel p-6 space-y-6">
          <div className="flex items-center space-x-2 border-b border-gray-800 pb-2">
            <FiInfo className="text-accent-blue text-lg" />
            <span className="text-xs font-bold text-gray-500 uppercase tracking-widest block">
              Software Specifications Catalog
            </span>
          </div>

          <div className="space-y-4 text-xs">
            <div className="space-y-2 leading-relaxed text-gray-400">
              <p>
                <strong>RailVision AI Track Inspector</strong> is an enterprise AI Command Centre interface designed for high-resolution visual diagnostics of track assets, utilizing deep convolutional features extraction and activation explanation grids overlays.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 font-mono text-[11px] bg-gray-950 p-4 rounded-xl border border-gray-800">
              <div className="space-y-0.5">
                <span className="text-gray-500 uppercase text-[9px] tracking-wider block">Dashboard Version</span>
                <span className="text-gray-300 font-bold">1.0.0 Stable</span>
              </div>
              <div className="space-y-0.5">
                <span className="text-gray-500 uppercase text-[9px] tracking-wider block">API Core</span>
                <span className="text-gray-300 font-bold">FastAPI 0.138+</span>
              </div>
              <div className="space-y-0.5 pt-2 border-t border-gray-800">
                <span className="text-gray-500 uppercase text-[9px] tracking-wider block">Model Architecture</span>
                <span className="text-gray-300 font-bold">Backend Metadata</span>
              </div>
              <div className="space-y-0.5 pt-2 border-t border-gray-800">
                <span className="text-gray-500 uppercase text-[9px] tracking-wider block">Visual Layer</span>
                <span className="text-gray-300 font-bold">Tailwind v3 + Motion</span>
              </div>
            </div>

            <div className="text-center text-[10px] text-gray-600 font-semibold uppercase tracking-wider pt-2">
              Copyright © 2026 Indian Railways Operations
            </div>
          </div>
        </div>

      </div>

      {/* Database Reset confirmation modal */}
      <AnimatePresence>
        {showWipeModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-panel w-full max-w-sm border-accent-red/30 p-6 space-y-6"
            >
              <div className="flex items-center space-x-3 text-accent-red">
                <div className="h-10 w-10 rounded-full bg-accent-red/10 border border-accent-red/20 flex items-center justify-center">
                  <FiAlertTriangle className="text-xl" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-sm m-0">Reset Logs Database?</h3>
                  <p className="text-[10px] text-gray-500">This action cannot be undone.</p>
                </div>
              </div>

              <p className="text-xs text-gray-400 leading-relaxed">
                You are about to delete all historical prediction records and remove their corresponding Grad-CAM overlay images from the backend storage.
              </p>

              <div className="flex space-x-3">
                <button
                  onClick={() => setShowWipeModal(false)}
                  disabled={wiping}
                  className="btn-secondary flex-1 py-2 text-xs"
                >
                  Cancel
                </button>
                <button
                  onClick={handleWipeDatabase}
                  disabled={wiping}
                  className="btn-danger flex-1 py-2 text-xs flex items-center justify-center space-x-1"
                >
                  {wiping ? (
                    <>
                      <div className="animate-spin rounded-full h-3.5 w-3.5 border-t-2 border-b-2 border-white"></div>
                      <span>Resetting...</span>
                    </>
                  ) : (
                    <span>Confirm Reset</span>
                  )}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
export default Settings;
