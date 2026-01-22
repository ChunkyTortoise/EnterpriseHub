import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * FLOATING INPUT v2026
 * Features: Semantic labels, glassmorphism, 
 * and ultra-responsive states.
 */

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, label, error, icon, ...props }, ref) => {
    const [focused, setFocused] = React.useState(false);
    const hasValue = props.value || props.defaultValue;

    return (
      <div className="group relative flex w-full flex-col gap-1.5">
        <div 
          className={cn(
            "relative flex items-center rounded-xl border bg-background/50 transition-all duration-200 backdrop-blur-sm",
            focused ? "border-primary ring-2 ring-primary/20" : "border-input hover:border-accent-foreground/30",
            error ? "border-destructive ring-destructive/20" : "",
            className
          )}
        >
          {icon && (
            <div className="pl-3 text-muted-foreground group-focus-within:text-primary transition-colors">
              {icon}
            </div>
          )}
          
          <input
            type={type}
            className={cn(
              "flex h-12 w-full rounded-xl bg-transparent px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground/50 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50",
              icon ? "pl-2" : ""
            )}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            ref={ref}
            {...props}
          />

          {label && (
            <label
              className={cn(
                "absolute left-3 transition-all duration-200 pointer-events-none",
                (focused || hasValue) 
                  ? "-top-2.5 left-2 bg-background px-1.5 text-xs font-medium text-primary" 
                  : "top-3.5 text-sm text-muted-foreground",
                icon && !(focused || hasValue) ? "left-9" : ""
              )}
            >
              {label}
            </label>
          )}
        </div>
        
        {error && (
          <p className="text-[11px] font-medium text-destructive px-1 animate-in fade-in slide-in-from-top-1">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
