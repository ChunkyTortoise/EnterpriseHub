import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import * as React from "react";

/**
 * ELITE BUTTON v2026
 * Features: Framer Motion scaling, Tailwind 4 theme variables, 
 * Glassmorphism variants, and high-precision focus states.
 */

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'glass' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, ...props }, ref) => {
    const variants = {
      primary: "bg-primary text-primary-foreground shadow-[0_0_20px_rgba(var(--color-primary-rgb),0.3)] hover:shadow-[0_0_30px_rgba(var(--color-primary-rgb),0.5)]",
      secondary: "bg-secondary text-secondary-foreground border border-border/50 backdrop-blur-sm",
      glass: "bg-white/10 border border-white/20 backdrop-blur-md text-white hover:bg-white/20",
      ghost: "hover:bg-accent hover:text-accent-foreground",
      danger: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
    };

    const sizes = {
      sm: "h-9 px-3 text-xs rounded-lg",
      md: "h-11 px-6 text-sm font-medium rounded-xl",
      lg: "h-14 px-8 text-base font-semibold rounded-2xl",
      icon: "h-11 w-11 flex items-center justify-center rounded-xl",
    };

    return (
      <motion.button
        ref={ref}
        whileHover={{ scale: 1.015, translateY: -1 }}
        whileTap={{ scale: 0.985 }}
        className={cn(
          "relative inline-flex items-center justify-center overflow-hidden transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {isLoading ? (
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
            <span>Loading...</span>
          </div>
        ) : children}
        
        {/* Subtle Shine Effect */}
        <div className="absolute inset-0 pointer-events-none bg-gradient-to-tr from-white/0 via-white/10 to-white/0 opacity-0 hover:opacity-100 transition-opacity duration-500 translate-x-[-100%] hover:translate-x-[100%] transform ease-in-out" />
      </motion.button>
    );
  }
);

Button.displayName = "Button";
