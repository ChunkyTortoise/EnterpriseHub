import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import * as React from "react";

/**
 * PULSE INDICATOR
 * Status indicator with a radiating pulse effect.
 */

interface PulseIndicatorProps {
  status?: 'success' | 'warning' | 'error' | 'info';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const PulseIndicator = ({
  status = 'success',
  size = 'md',
  className
}: PulseIndicatorProps) => {
  const colors = {
    success: "bg-emerald-500",
    warning: "bg-amber-500",
    error: "bg-rose-500",
    info: "bg-sky-500",
  };

  const sizes = {
    sm: "h-2 w-2",
    md: "h-3 w-3",
    lg: "h-4 w-4",
  };

  return (
    <div className={cn("relative flex items-center justify-center", sizes[size], className)}>
      <motion.div
        animate={{ scale: [1, 2, 1], opacity: [0.5, 0, 0.5] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        className={cn("absolute inset-0 rounded-full", colors[status])}
      />
      <div className={cn("relative z-10 rounded-full shadow-lg", sizes[size], colors[status])} />
    </div>
  );
};
