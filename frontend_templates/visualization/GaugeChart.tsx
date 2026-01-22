import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * GAUGE CHART
 * Semi-circle gauge for KPIs.
 */

interface GaugeChartProps {
  value: number; // 0 to 100
  label?: string;
  size?: number;
  color?: string;
  className?: string;
}

export const GaugeChart = ({
  value,
  label,
  size = 200,
  color = "var(--color-primary)",
  className
}: GaugeChartProps) => {
  const radius = size / 2.5;
  const circumference = Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  return (
    <div className={cn("relative flex flex-col items-center", className)}>
      <svg 
        width={size} 
        height={size / 1.5} 
        className="overflow-visible"
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={size / 12}
          strokeDasharray={circumference}
          strokeLinecap="round"
          className="text-white/5"
          style={{
            transformOrigin: "center",
            transform: "rotate(180deg)",
          }}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={size / 12}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
          style={{
            transformOrigin: "center",
            transform: "rotate(180deg)",
            filter: `drop-shadow(0 0 8px ${color}44)`
          }}
        />
      </svg>
      
      <div className="absolute top-[45%] flex flex-col items-center">
        <span className="text-3xl font-bold tracking-tighter">{value}%</span>
        {label && <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{label}</span>}
      </div>
    </div>
  );
};
