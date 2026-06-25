import React from "react";
import { motion } from "framer-motion";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: "blue" | "cyan" | "emerald" | "red" | "yellow";
  subtitle?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  color,
  subtitle,
}) => {
  // Theme color maps
  const colorMap = {
    blue: {
      border: "border-accent-blue/30 hover:border-accent-blue/60",
      text: "text-accent-blue",
      glow: "hover:shadow-accent-blue/10",
      iconBg: "bg-accent-blue/10 text-accent-blue",
    },
    cyan: {
      border: "border-accent-cyan/30 hover:border-accent-cyan/60",
      text: "text-accent-cyan",
      glow: "hover:shadow-accent-cyan/10",
      iconBg: "bg-accent-cyan/10 text-accent-cyan",
    },
    emerald: {
      border: "border-accent-emerald/30 hover:border-accent-emerald/60",
      text: "text-accent-emerald",
      glow: "hover:shadow-accent-emerald/10",
      iconBg: "bg-accent-emerald/10 text-accent-emerald",
    },
    red: {
      border: "border-accent-red/30 hover:border-accent-red/60",
      text: "text-accent-red",
      glow: "hover:shadow-accent-red/10",
      iconBg: "bg-accent-red/10 text-accent-red",
    },
    yellow: {
      border: "border-yellow-500/30 hover:border-yellow-500/60",
      text: "text-yellow-400",
      glow: "hover:shadow-yellow-500/10",
      iconBg: "bg-yellow-500/10 text-yellow-400",
    },
  };

  const currentTheme = colorMap[color];

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -3 }}
      transition={{ duration: 0.3 }}
      className={`glass-panel border p-5 flex items-start justify-between transition-all duration-300 shadow-md ${currentTheme.border} ${currentTheme.glow}`}
    >
      <div className="space-y-2">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-widest block">
          {title}
        </span>
        <h3 className="text-3xl font-extrabold text-white tracking-tight leading-none">
          {value}
        </h3>
        {subtitle && (
          <span className="text-[10px] text-gray-400 tracking-wide block font-medium">
            {subtitle}
          </span>
        )}
      </div>

      <div className={`h-11 w-11 rounded-xl flex items-center justify-center ${currentTheme.iconBg} border border-white/5`}>
        {icon}
      </div>
    </motion.div>
  );
};
export default StatCard;
