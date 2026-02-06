import { cn } from "@/lib/utils";
import * as React from "react";

/**
 * ELITE SKELETON
 * High-precision placeholder for loading states.
 */

export const Skeleton = ({ 
  className, 
  variant = 'default' 
}: { 
  className?: string; 
  variant?: 'default' | 'circular' | 'shimmer'; 
}) => {
  return (
    <div
      className={cn(
        "bg-white/5 animate-pulse",
        variant === 'circular' ? "rounded-full" : "rounded-xl",
        className
      )}
    >
      {variant === 'shimmer' && (
        <div className="h-full w-full bg-gradient-to-r from-transparent via-white/5 to-transparent shimmer-effect" />
      )}
    </div>
  );
};
