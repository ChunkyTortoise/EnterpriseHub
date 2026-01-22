import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * ACTIVITY HEATMAP
 * Github-style contribution grid for visualizing activity.
 */

interface ActivityHeatmapProps {
  data: { date: string; value: number }[];
  months?: number;
  className?: string;
}

export const ActivityHeatmap = ({ 
  data, 
  months = 6, 
  className 
}: ActivityHeatmapProps) => {
  // Simple Mock Generation for visualization
  const days = months * 30;
  const grid = Array.from({ length: days }).map((_, i) => ({
    level: Math.floor(Math.random() * 5), // 0 to 4
  }));

  const levelColors = [
    "bg-white/5",
    "bg-emerald-500/20",
    "bg-emerald-500/40",
    "bg-emerald-500/70",
    "bg-emerald-500",
  ];

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <div className="grid grid-flow-col grid-rows-7 gap-1.5">
        {grid.map((day, i) => (
          <div
            key={i}
            className={cn(
              "h-3 w-3 rounded-sm transition-all hover:ring-2 hover:ring-white/20 cursor-pointer",
              levelColors[day.level]
            )}
            title={`Level: ${day.level}`}
          />
        ))}
      </div>
      <div className="flex items-center gap-2 text-[10px] text-muted-foreground self-end mt-1">
        <span>Less</span>
        {levelColors.map((color, i) => (
          <div key={i} className={cn("h-2.5 w-2.5 rounded-sm", color)} />
        ))}
        <span>More</span>
      </div>
    </div>
  );
};
