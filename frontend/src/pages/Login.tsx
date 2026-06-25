import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FiUser, FiLock, FiAlertTriangle, FiCpu } from "react-icons/fi";
import { motion } from "framer-motion";
import { useAuth } from "../contexts/AuthContext";

export const Login: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState<string>("admin");
  const [password, setPassword] = useState<string>("");
  const [rememberMe, setRememberMe] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(username, password);
      navigate("/");
    } catch (err: any) {
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Network connection failure. Server is offline.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col md:flex-row select-none">
      {/* 1. Left Side: AI Railway Artwork HUD */}
      <div className="flex-1 bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 relative overflow-hidden hidden md:flex flex-col justify-between p-12 border-r border-gray-800/80">
        {/* Animated grid lines background */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f29371a_1px,transparent_1px),linear-gradient(to_bottom,#1f29371a_1px,transparent_1px)] bg-[size:32px_32px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]"></div>

        {/* Brand header */}
        <div className="flex items-center space-x-3 relative z-10">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-accent-blue to-accent-cyan flex items-center justify-center shadow-lg shadow-accent-blue/30">
            <FiCpu className="text-white text-xl animate-pulse" />
          </div>
          <div>
            <span className="font-extrabold text-xl tracking-wider text-white">
              RAILVISION <span className="text-accent-cyan font-extrabold text-sm">AI</span>
            </span>
          </div>
        </div>

        {/* Abstract HUD scanning animation */}
        <div className="relative flex items-center justify-center flex-1">
          <div className="absolute h-96 w-96 rounded-full border border-gray-800/40 flex items-center justify-center">
            <div className="absolute h-72 w-72 rounded-full border border-gray-800/60 flex items-center justify-center">
              <div className="absolute h-48 w-48 rounded-full border border-accent-cyan/15 flex items-center justify-center animate-ping"></div>
              <div className="absolute h-40 w-40 rounded-full border border-accent-blue/20 flex items-center justify-center">
                <div className="absolute h-2 w-2 rounded-full bg-accent-cyan animate-pulse"></div>
              </div>
            </div>
            
            {/* Spinning Radar sweeping */}
            <div className="absolute inset-0 rounded-full border-t border-accent-blue/40 animate-spin [animation-duration:12s]"></div>
            <div className="absolute inset-4 rounded-full border-b border-accent-cyan/30 animate-spin [animation-duration:8s] [animation-direction:reverse]"></div>
          </div>

          {/* AI Track Vector Overlay graphics */}
          <svg className="w-80 h-40 text-accent-blue/40 relative" viewBox="0 0 300 150">
            {/* Rails */}
            <line x1="10" y1="120" x2="290" y2="120" stroke="currentColor" strokeWidth="3" />
            <line x1="10" y1="130" x2="290" y2="130" stroke="currentColor" strokeWidth="3" />
            
            {/* Ties */}
            {Array.from({ length: 15 }).map((_, i) => (
              <line
                key={i}
                x1={20 + i * 18}
                y1="115"
                x2={20 + i * 18}
                y2="135"
                stroke="currentColor"
                strokeWidth="2"
              />
            ))}

            {/* AI inspection boxes */}
            <rect x="75" y="105" width="40" height="40" fill="none" stroke="#06b6d4" strokeWidth="1.5" className="animate-pulse" />
            <line x1="95" y1="60" x2="95" y2="105" stroke="#06b6d4" strokeWidth="1" strokeDasharray="3 3" />
            <text x="75" y="50" fill="#06b6d4" fontSize="10" fontWeight="bold" fontFamily="sans-serif" letterSpacing="1">
              [CRACK DETECT]
            </text>

            <rect x="180" y="105" width="40" height="40" fill="none" stroke="#10b981" strokeWidth="1.5" />
            <line x1="200" y1="75" x2="200" y2="105" stroke="#10b981" strokeWidth="1" strokeDasharray="3 3" />
            <text x="185" y="68" fill="#10b981" fontSize="10" fontWeight="bold" fontFamily="sans-serif" letterSpacing="1">
              [NORMAL]
            </text>
          </svg>
        </div>

        {/* Left Side footer */}
        <div className="relative z-10">
          <h2 className="text-xl font-bold text-white tracking-wide">
            Automated Defect Explainer & Diagnostics
          </h2>
          <p className="text-xs text-gray-500 max-w-sm mt-2 leading-relaxed">
            Real-time classification and local activations segmentations deployed on track assets. Secured with enterprise cryptography credentials mapping.
          </p>
        </div>
      </div>

      {/* 2. Right Side: Login Panel */}
      <div className="w-full md:w-[480px] bg-background flex flex-col justify-center px-8 sm:px-16 py-12">
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-8"
        >
          {/* Form Header */}
          <div className="space-y-2">
            <h1 className="text-3xl font-extrabold text-white tracking-tight leading-none my-0">
              Sign In
            </h1>
            <p className="text-sm text-gray-400 font-medium">
              AI Railway Track Inspection Command Centre
            </p>
          </div>

          {/* Form validation alerts */}
          {error && (
            <div className="bg-accent-red/10 border border-accent-red/30 rounded-lg p-3 flex items-start space-x-3 text-accent-red text-xs">
              <FiAlertTriangle className="shrink-0 text-sm mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Login form fields */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gray-400 uppercase tracking-widest">
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                  <FiUser />
                </div>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="input-field pl-9"
                  placeholder="Enter admin username"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gray-400 uppercase tracking-widest">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                  <FiLock />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field pl-9"
                  placeholder="Enter account password"
                />
              </div>
            </div>

            {/* Remember me option */}
            <div className="flex items-center justify-between text-xs font-medium">
              <label className="flex items-center space-x-2 text-gray-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="h-4 w-4 bg-gray-900 border-gray-800 text-accent-blue rounded focus:ring-0 cursor-pointer"
                />
                <span>Remember this terminal</span>
              </label>
            </div>

            {/* Action buttons */}
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-2.5 flex items-center justify-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white"></div>
                  <span>Authenticating...</span>
                </>
              ) : (
                <span>Establish Connection</span>
              )}
            </button>
          </form>

          {/* Demo account hints info */}
          <div className="bg-gray-950 rounded-lg p-3 border border-gray-800 text-[10px] text-gray-500 space-y-1 font-mono">
            <p className="font-bold text-gray-400">DEMO OPERATOR METRICS CAPABILITIES</p>
            <p>Username: <span className="text-gray-300">admin</span></p>
            <p>Password: <span className="text-gray-300">configured on backend</span></p>
          </div>
        </motion.div>
      </div>
    </div>
  );
};
export default Login;
