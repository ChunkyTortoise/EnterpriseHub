import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import * as React from "react";

/**
 * ELITE TOGGLE
 * High-performance animated switch.
 */

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  size?: 'sm' | 'md';
}

export const Toggle = ({ 
  checked, 
  onChange, 
  disabled, 
  size = 'md' 
}: ToggleProps) => {
  const sizes = {
    sm: { width: "w-8", height: "h-4.5", dot: "h-3.5 w-3.5" },
    md: { width: "w-11", height: "h-6", dot: "h-5 w-5" },
  };

  return (
    <button
      onClick={() => !disabled && onChange(!checked)}
      className={cn(
        "relative rounded-full transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-primary/20",
        sizes[size].width,
        sizes[size].height,
        checked ? "bg-primary" : "bg-white/10 border border-white/5",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <motion.div
        animate={{ x: checked ? (size === 'md' ? 22 : 16) : 2 }}
        className={cn(
          "absolute top-0.5 rounded-full bg-white shadow-lg",
          sizes[size].dot
        )}
      />
    </button>
  );
};
