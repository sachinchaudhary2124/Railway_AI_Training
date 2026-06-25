import React from "react";
import { useNavigate } from "react-router-dom";
import { FiAlertTriangle, FiHome } from "react-icons/fi";
import { motion } from "framer-motion";

export const NotFound: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center p-8 select-none">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="glass-panel max-w-md w-full p-8 text-center space-y-6 border-gray-800"
      >
        <div className="mx-auto h-14 w-14 rounded-full bg-yellow-500/10 border border-yellow-500/20 flex items-center justify-center text-yellow-400">
          <FiAlertTriangle className="text-3xl" />
        </div>

        <div className="space-y-2">
          <h1 className="text-4xl font-extrabold text-white font-mono tracking-widest leading-none my-0">
            404
          </h1>
          <h2 className="text-lg font-bold text-gray-200 tracking-wide m-0">
            Module Not Found
          </h2>
          <p className="text-xs text-gray-500 leading-relaxed max-w-xs mx-auto">
            The control module path you requested does not exist or has been relocated to another diagnostic section.
          </p>
        </div>

        <button
          onClick={() => navigate("/")}
          className="btn-primary w-full py-2.5 flex items-center justify-center space-x-2 text-xs font-bold uppercase tracking-widest"
        >
          <FiHome />
          <span>Return to Central Console</span>
        </button>
      </motion.div>
    </div>
  );
};
export default NotFound;
