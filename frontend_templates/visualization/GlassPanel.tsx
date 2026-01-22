import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * GLASS PANEL
 * A versatile reusable container for high-end UIs.
 * Uses CSS variables for consistent glass intensity.
 */

interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  intensity?: 'low' | 'medium' | 'high';
  border?: boolean;
}

export const GlassPanel = ({
  className,
  intensity = 'medium',
  border = true,
  children,
  ...props
}: GlassPanelProps) => {
  const intensities = {
    low: "bg-white/5 backdrop-blur-md",
    medium: "bg-white/10 backdrop-blur-xl",
    high: "bg-white/20 backdrop-blur-2xl",
  };

  return (
    <div
      className={cn(
        "rounded-2xl transition-all duration-500",
        intensities[intensity],
        border && "border border-white/10",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};
