import React, { useState, useEffect } from "react";
import { 
  FiSearch, 
  FiFilter, 
  FiEye, 
  FiTrash2, 
  FiX, 
  FiAlertTriangle,
  FiDatabase
} from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";
import apiService from "../services/api";
import type { HistoryItem } from "../types";

export const History: React.FC = () => {
  const [historyList, setHistoryList] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [classFilter, setClassFilter] = useState<string>("all");
  const [sortField, setSortField] = useState<"timestamp" | "confidence" | "inference_time_ms">("timestamp");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null);
  const [showWipeModal, setShowWipeModal] = useState<boolean>(false);
  const [wiping, setWiping] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // 1. Fetch History on mount
  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await apiService.getHistory();
      setHistoryList(res.history);
    } catch (err) {
      setError("Failed to load prediction history database.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  // 2. Clear all history
  const handleWipeHistory = async () => {
    setWiping(true);
    try {
      await apiService.clearHistory();
      setHistoryList([]);
      setShowWipeModal(false);
    } catch (err) {
      setError("Failed to clear prediction logs database.");
    } finally {
      setWiping(false);
    }
  };

  // 3. Search, Filter, and Sort logic
  const filteredList = historyList
    .filter((item) => {
      // Search matches filename
      const matchSearch = item.original_filename.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          item.predicted_class.toLowerCase().includes(searchQuery.toLowerCase());
      
      // Class filter matches
      const matchFilter = classFilter === "all" || item.predicted_class === classFilter;
      
      return matchSearch && matchFilter;
    })
    .sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];

      if (sortField === "timestamp") {
        return sortOrder === "desc"
          ? new Date(valB).getTime() - new Date(valA).getTime()
          : new Date(valA).getTime() - new Date(valB).getTime();
      } else {
        return sortOrder === "desc"
          ? (valB as number) - (valA as number)
          : (valA as number) - (valB as number);
      }
    });

  const toggleSort = (field: "timestamp" | "confidence" | "inference_time_ms") => {
    if (sortField === field) {
      setSortOrder(sortOrder === "desc" ? "asc" : "desc");
    } else {
      setSortField(field);
      setSortOrder("desc");
    }
  };

  return (
    <div className="flex-1 bg-background p-8 space-y-8 overflow-y-auto max-h-[calc(100vh-64px)] font-sans">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white m-0">
            Prediction History Logs
          </h1>
          <p className="text-xs text-gray-400 font-medium">
            Search, filter, and review historical diagnostic scan logs.
          </p>
        </div>

        {historyList.length > 0 && (
          <button
            onClick={() => setShowWipeModal(true)}
            className="btn-danger text-xs uppercase font-bold tracking-widest flex items-center space-x-2 py-2"
          >
            <FiTrash2 />
            <span>Wipe Database</span>
          </button>
        )}
      </div>

      {/* Database sync status or errors */}
      {error && (
        <div className="bg-accent-red/10 border border-accent-red/30 rounded-lg p-3 flex items-start space-x-3 text-accent-red text-xs">
          <FiAlertTriangle className="shrink-0 text-sm mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Table filters panel */}
      <div className="glass-panel p-4 flex flex-col md:flex-row gap-4 items-center justify-between">
        {/* Search */}
        <div className="relative w-full md:w-80">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
            <FiSearch />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-field pl-9 text-xs"
            placeholder="Search by filename..."
          />
        </div>

        {/* Filter Dropdown */}
        <div className="flex items-center space-x-3 w-full md:w-auto">
          <div className="flex items-center space-x-1.5 text-gray-500 text-xs font-bold uppercase">
            <FiFilter />
            <span>Filter:</span>
          </div>
          <select
            value={classFilter}
            onChange={(e) => setClassFilter(e.target.value)}
            className="bg-gray-900 border border-gray-800 rounded-lg text-xs text-gray-300 px-3 py-2 focus:outline-none focus:border-accent-blue cursor-pointer"
          >
            <option value="all">ALL CLASSES</option>
            <option value="broken_rail">BROKEN RAIL</option>
            <option value="crack">CRACK</option>
            <option value="normal">NORMAL</option>
            <option value="surface_wear">SURFACE WEAR</option>
          </select>
        </div>
      </div>

      {/* Main logs table */}
      <div className="glass-panel overflow-hidden border border-gray-800">
        {loading ? (
          <div className="py-20 text-center text-gray-400">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-accent-blue mx-auto mb-4"></div>
            <p className="text-xs font-semibold tracking-wide uppercase">Reading database records...</p>
          </div>
        ) : filteredList.length === 0 ? (
          <div className="py-20 text-center text-gray-500 space-y-3">
            <FiDatabase className="text-4xl text-gray-700 mx-auto" />
            <p className="text-sm font-semibold">No diagnostic records found</p>
            <p className="text-xs text-gray-600">
              Run a track scan in the inspection module to generate logs.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-gray-800 bg-gray-950/60 uppercase font-bold text-gray-500 tracking-wider">
                  <th 
                    className="p-4 cursor-pointer hover:text-white transition-colors duration-150 select-none"
                    onClick={() => toggleSort("timestamp")}
                  >
                    Time {sortField === "timestamp" && (sortOrder === "desc" ? "↓" : "↑")}
                  </th>
                  <th className="p-4">Filename</th>
                  <th className="p-4">Prediction Class</th>
                  <th 
                    className="p-4 cursor-pointer hover:text-white transition-colors duration-150 select-none"
                    onClick={() => toggleSort("confidence")}
                  >
                    Confidence {sortField === "confidence" && (sortOrder === "desc" ? "↓" : "↑")}
                  </th>
                  <th 
                    className="p-4 cursor-pointer hover:text-white transition-colors duration-150 select-none"
                    onClick={() => toggleSort("inference_time_ms")}
                  >
                    Latency {sortField === "inference_time_ms" && (sortOrder === "desc" ? "↓" : "↑")}
                  </th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800 bg-card/20">
                {filteredList.map((item, i) => (
                  <tr key={i} className="hover:bg-gray-800/20 transition-colors duration-150 text-gray-300">
                    <td className="p-4 font-mono text-[11px] text-gray-400">
                      {new Date(item.timestamp).toLocaleString("en-IN", { hour12: false })}
                    </td>
                    <td className="p-4 font-medium truncate max-w-[180px]" title={item.original_filename}>
                      {item.original_filename}
                    </td>
                    <td className="p-4">
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                        item.predicted_class === "normal"
                          ? "bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/20"
                          : "bg-accent-red/10 text-accent-red border border-accent-red/20"
                      }`}>
                        {item.predicted_class.replace("_", " ")}
                      </span>
                    </td>
                    <td className="p-4 font-mono font-bold">
                      {(item.confidence * 100).toFixed(1)}%
                    </td>
                    <td className="p-4 font-mono text-gray-400">
                      {item.inference_time_ms.toFixed(1)} ms
                    </td>
                    <td className="p-4 text-right">
                      <button
                        onClick={() => setSelectedItem(item)}
                        className="bg-gray-800 hover:bg-accent-blue/15 hover:text-accent-blue text-gray-300 p-2 rounded-lg border border-gray-700 transition-colors duration-150"
                        title="View diagnostic heatmap details"
                      >
                        <FiEye />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Detail Overlay modal */}
      <AnimatePresence>
        {selectedItem && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="glass-panel w-full max-w-2xl overflow-hidden"
            >
              {/* Modal header */}
              <div className="flex items-center justify-between border-b border-gray-800 p-5 bg-gray-950/60">
                <div>
                  <h3 className="font-bold text-white text-sm m-0">
                    Diagnostic Log Details
                  </h3>
                  <p className="text-[10px] text-gray-500 font-mono mt-0.5">ID: {selectedItem.prediction_id}</p>
                </div>
                <button
                  onClick={() => setSelectedItem(null)}
                  className="text-gray-400 hover:text-white p-1 rounded-full hover:bg-gray-800"
                >
                  <FiX className="text-lg" />
                </button>
              </div>

              {/* Modal body */}
              <div className="p-6 space-y-6 max-h-[calc(80vh-100px)] overflow-y-auto">
                <div className="grid grid-cols-2 gap-4 text-xs font-mono bg-gray-950 p-4 rounded-xl border border-gray-800">
                  <div className="space-y-1">
                    <span className="text-gray-500 uppercase tracking-wider block">Filename</span>
                    <span className="text-gray-200 font-bold truncate block">{selectedItem.original_filename}</span>
                  </div>
                  <div className="space-y-1">
                    <span className="text-gray-500 uppercase tracking-wider block">Diagnostics Result</span>
                    <span className={`font-bold ${
                      selectedItem.predicted_class === "normal" ? "text-accent-emerald" : "text-accent-red"
                    }`}>
                      {selectedItem.predicted_class.toUpperCase().replace("_", " ")} ({(selectedItem.confidence * 100).toFixed(1)}%)
                    </span>
                  </div>
                  <div className="space-y-1 pt-2 border-t border-gray-800">
                    <span className="text-gray-500 uppercase tracking-wider block">Scan Timestamp</span>
                    <span className="text-gray-300 font-semibold">{new Date(selectedItem.timestamp).toLocaleString()}</span>
                  </div>
                  <div className="space-y-1 pt-2 border-t border-gray-800">
                    <span className="text-gray-500 uppercase tracking-wider block">Execution Latency</span>
                    <span className="text-gray-300 font-semibold">{selectedItem.inference_time_ms.toFixed(2)} ms</span>
                  </div>
                </div>

                <div className="space-y-3 bg-gray-950 p-4 rounded-xl border border-gray-800">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                      Repair Priority
                    </span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full border uppercase font-bold tracking-wider ${
                      selectedItem.severity === "critical"
                        ? "bg-accent-red/10 text-accent-red border-accent-red/30"
                        : selectedItem.severity === "high"
                        ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/30"
                        : selectedItem.severity === "nominal"
                        ? "bg-accent-emerald/10 text-accent-emerald border-accent-emerald/30"
                        : "bg-accent-blue/10 text-accent-blue border-accent-blue/30"
                    }`}>
                      {selectedItem.severity}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-gray-500 uppercase tracking-wider">Risk Score</span>
                    <span className="text-gray-300 font-bold">{selectedItem.risk_score}/100</span>
                  </div>
                  <p className="text-xs text-gray-400 leading-relaxed">{selectedItem.recommended_action}</p>
                  <p className="text-[10px] text-gray-600 uppercase tracking-wider font-semibold">
                    Geospatial metadata: {selectedItem.location_status.replace("_", " ")}
                  </p>
                </div>

                <div className="space-y-3">
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block border-b border-gray-800 pb-1.5">
                    Grad-CAM Activation Segmentation
                  </span>
                  
                  {/* Serves the pre-compiled Grad-CAM overlay image directly */}
                  <div className="relative aspect-square w-full rounded-xl overflow-hidden border border-gray-800 bg-gray-950">
                    <img
                      src={selectedItem.gradcam_url}
                      alt="Grad-CAM Activation overlay file"
                      className="h-full w-full object-cover"
                    />
                    <div className="absolute bottom-3 left-3 bg-gray-900/80 border border-gray-800 px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-widest text-gray-300">
                      Heatmap overlay output
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Database reset Wipe Confirmation Modal */}
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
                  <h3 className="font-bold text-white text-sm m-0">Wipe Logs Database?</h3>
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
                  onClick={handleWipeHistory}
                  disabled={wiping}
                  className="btn-danger flex-1 py-2 text-xs flex items-center justify-center space-x-1"
                >
                  {wiping ? (
                    <>
                      <div className="animate-spin rounded-full h-3.5 w-3.5 border-t-2 border-b-2 border-white"></div>
                      <span>Wiping...</span>
                    </>
                  ) : (
                    <span>Confirm Wipe</span>
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
export default History;
