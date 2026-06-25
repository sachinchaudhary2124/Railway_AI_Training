import React, { useState, useEffect } from "react";
import { FiPower, FiClock, FiActivity, FiUser, FiCpu } from "react-icons/fi";
import { useAuth } from "../contexts/AuthContext";
import apiService from "../services/api";

export const Navbar: React.FC = () => {
  const { logout, user } = useAuth();
  const [time, setTime] = useState<string>("");
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [device, setDevice] = useState<string>("CPU");

  // 1. Clock effect
  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString("en-IN", { hour12: false }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // 2. Poll API Health status dynamically every 10s
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await apiService.getHealth();
        setIsOnline(health.status === "healthy");
        setDevice(health.device.toUpperCase());
      } catch (err) {
        setIsOnline(false);
      }
    };
    checkHealth();
    const healthInterval = setInterval(checkHealth, 10000);
    return () => clearInterval(healthInterval);
  }, []);

  return (
    <nav className="h-16 border-b border-gray-800 bg-gray-900/60 backdrop-blur-md sticky top-0 z-50 flex items-center justify-between px-6">
      {/* Brand logo details */}
      <div className="flex items-center space-x-3">
        <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-accent-blue to-accent-cyan flex items-center justify-center shadow-md shadow-accent-blue/20">
          <FiCpu className="text-white text-lg animate-pulse" />
        </div>
        <div>
          <span className="font-bold text-lg tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-white via-gray-200 to-gray-400">
            RAILVISION <span className="text-accent-cyan font-extrabold text-sm">AI</span>
          </span>
          <span className="hidden md:inline-block text-[10px] text-gray-500 uppercase tracking-widest ml-2 border-l border-gray-800 pl-2">
            Track Inspector v1.0
          </span>
        </div>
      </div>

      {/* Top Navbar details */}
      <div className="flex items-center space-x-6 text-sm font-medium">
        {/* API Health indicator */}
        <div className="flex items-center space-x-2 bg-gray-950 px-3 py-1.5 rounded-full border border-gray-800">
          <FiActivity className={`${isOnline ? "text-accent-emerald animate-pulse" : "text-accent-red"} text-md`} />
          <span className={`text-xs uppercase tracking-wider ${isOnline ? "text-accent-emerald" : "text-accent-red"}`}>
            {isOnline ? "System Online" : "System Offline"}
          </span>
          {isOnline && (
            <span className="text-[10px] text-gray-500 bg-gray-900 px-1.5 py-0.5 rounded border border-gray-800">
              {device}
            </span>
          )}
        </div>

        {/* Live Clock ticking */}
        <div className="hidden sm:flex items-center space-x-2 text-gray-400">
          <FiClock className="text-accent-cyan" />
          <span className="font-mono text-xs tracking-widest bg-gray-950 px-3 py-1.5 rounded-full border border-gray-800">
            {time || "00:00:00"}
          </span>
        </div>

        {/* User login state card */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 border-r border-gray-800 pr-4">
            <div className="h-7 w-7 rounded-full bg-gray-800 flex items-center justify-center border border-gray-700">
              <FiUser className="text-gray-300 text-sm" />
            </div>
            <span className="text-gray-300 text-xs tracking-wider capitalize hidden md:inline">
              {user?.username || "Operator"}
            </span>
          </div>

          {/* Logout operation */}
          <button
            onClick={logout}
            className="flex items-center space-x-1.5 text-xs uppercase tracking-wider text-gray-400 hover:text-accent-red transition-colors duration-200"
            title="Log Out Command Center"
          >
            <FiPower className="text-sm" />
            <span className="hidden sm:inline">Log Out</span>
          </button>
        </div>
      </div>
    </nav>
  );
};
export default Navbar;
