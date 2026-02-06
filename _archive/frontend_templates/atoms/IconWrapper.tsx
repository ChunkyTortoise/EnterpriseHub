import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * ICON WRAPPER
 * Ensures consistent scaling, alignment, and 
 * color injection for Lucide or other icon sets.
 */

interface IconWrapperProps extends React.HTMLAttributes<HTMLDivElement> {
  icon: React.ElementType;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  glow?: boolean;
}

export const IconWrapper = ({
  icon: Icon,
  size = 'md',
  glow = false,
  className,
  ...props
}: IconWrapperProps) => {
  const sizes = {
    xs: "h-3 w-3",
    sm: "h-4 w-4",
    md: "h-5 w-5",
    lg: "h-6 w-6",
    xl: "h-8 w-8",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center justify-center transition-all",
        glow && "drop-shadow-[0_0_8px_rgba(var(--color-primary-rgb),0.4)]",
        className
      )}
      {...props}
    >
      <Icon className={cn(sizes[size])} />
    </div>
  );
};
