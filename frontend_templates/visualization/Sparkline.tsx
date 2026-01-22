import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * ELITE SPARKLINE
 * Lightweight SVG sparkline for dashboards.
 * Supports dynamic color based on trend.
 */

interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  strokeWidth?: number;
  className?: string;
  animated?: boolean;
}

export const Sparkline = ({
  data,
  width = 120,
  height = 40,
  color = "currentColor",
  strokeWidth = 2,
  className,
  animated = true
}: SparklineProps) => {
  if (!data || data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min;
  
  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((val - min) / (range || 1)) * height;
    return `${x},${y}`;
  }).join(" ");

  const pathData = `M ${points}`;

  return (
    <svg 
      width={width} 
      height={height} 
      className={cn("overflow-visible", className)}
    >
      <defs>
        <linearGradient id="sparkline-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.2" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      
      {/* Area under the line */}
      <path
        d={`${pathData} L ${width},${height} L 0,${height} Z`}
        fill="url(#sparkline-grad)"
        className={animated ? "animate-in fade-in duration-1000" : ""}
      />

      {/* The line itself */}
      <path
        d={pathData}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={cn(
          "transition-all duration-500",
          animated && "sparkline-path"
        )}
        style={{
          // @ts-ignore
          "--path-length": "200px" // Approximate
        }}
      />
      
      <style>{`
        .sparkline-path {
          stroke-dasharray: 500;
          stroke-dashoffset: 500;
          animation: draw 2s ease-out forwards;
        }
        @keyframes draw {
          to { stroke-dashoffset: 0; }
        }
      `}</style>
    </svg>
  );
};
