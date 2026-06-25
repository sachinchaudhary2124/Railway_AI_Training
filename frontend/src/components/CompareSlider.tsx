import React, { useState } from "react";
import { FiChevronsLeft, FiChevronsRight } from "react-icons/fi";

interface CompareSliderProps {
  originalUrl: string;
  overlayUrl: string;
  aspectRatioClassName?: string;
}

export const CompareSlider: React.FC<CompareSliderProps> = ({
  originalUrl,
  overlayUrl,
  aspectRatioClassName = "aspect-square",
}) => {
  const [sliderPosition, setSliderPosition] = useState<number>(50);

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSliderPosition(Number(e.target.value));
  };

  return (
    <div className={`relative w-full overflow-hidden rounded-xl border border-gray-800 bg-gray-950 ${aspectRatioClassName} select-none group`}>
      {/* 1. Base Image - Original Image */}
      <img
        src={originalUrl}
        alt="Original Uploaded Track"
        className="absolute inset-0 h-full w-full object-cover"
        draggable={false}
      />

      {/* 2. Overlaid Image - Grad-CAM Overlay with Clip Path */}
      <div
        className="absolute inset-0 h-full w-full"
        style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
      >
        <img
          src={overlayUrl}
          alt="Grad-CAM Hotspot Activation"
          className="absolute inset-0 h-full w-full object-cover"
          draggable={false}
        />
      </div>

      {/* 3. Slider Line Divider */}
      <div
        className="absolute inset-y-0 w-0.5 bg-accent-cyan shadow-[0_0_10px_rgba(6,182,212,0.8)] pointer-events-none"
        style={{ left: `${sliderPosition}%` }}
      >
        {/* Center Drag Handle Indicator */}
        <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 h-8 w-8 rounded-full bg-gray-900 border border-accent-cyan flex items-center justify-center text-accent-cyan shadow-md shadow-accent-cyan/30 group-hover:scale-110 transition-transform duration-150">
          <div className="flex items-center space-x-0.5 text-xs">
            <FiChevronsLeft />
            <FiChevronsRight />
          </div>
        </div>
      </div>

      {/* 4. Sliding controller input layer */}
      <input
        type="range"
        min="0"
        max="100"
        value={sliderPosition}
        onChange={handleSliderChange}
        className="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-20"
      />

      {/* 5. Floating Labels */}
      <div className="absolute bottom-3 left-3 bg-gray-900/80 px-2.5 py-1 rounded text-[10px] uppercase font-bold tracking-widest text-white border border-gray-800 backdrop-blur-sm pointer-events-none z-10">
        Heatmap overlay
      </div>
      <div className="absolute bottom-3 right-3 bg-gray-900/80 px-2.5 py-1 rounded text-[10px] uppercase font-bold tracking-widest text-white border border-gray-800 backdrop-blur-sm pointer-events-none z-10">
        Original raw
      </div>
    </div>
  );
};
export default CompareSlider;
