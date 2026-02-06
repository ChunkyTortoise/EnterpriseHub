import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import * as React from "react";

/**
 * ELITE CARD
 * Aesthetic: Layered depth, border glow on hover, 
 * glassmorphism background.
 */

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hoverEffect?: boolean;
  glass?: boolean;
}

export const Card = ({ 
  className, 
  hoverEffect = true, 
  glass = true, 
  children, 
  ...props 
}: CardProps) => {
  return (
    <motion.div
      whileHover={hoverEffect ? { y: -4, scale: 1.01 } : {}}
      className={cn(
        "relative overflow-hidden rounded-3xl border border-border/50 bg-card p-6 shadow-sm transition-all",
        glass && "bg-white/5 backdrop-blur-xl border-white/10",
        hoverEffect && "hover:border-primary/30 hover:shadow-2xl hover:shadow-primary/10",
        className
      )}
      {...props}
    >
      {/* Decorative Glow Background */}
      <div className="absolute -right-20 -top-20 h-40 w-40 rounded-full bg-primary/5 blur-[80px] pointer-events-none" />
      <div className="absolute -left-20 -bottom-20 h-40 w-40 rounded-full bg-secondary/5 blur-[80px] pointer-events-none" />
      
      <div className="relative z-10">
        {children}
      </div>
    </motion.div>
  );
};

export const CardHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex flex-col space-y-1.5 mb-4", className)} {...props} />
);

export const CardTitle = ({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
  <h3 className={cn("text-xl font-bold leading-none tracking-tight text-foreground/90", className)} {...props} />
);

export const CardDescription = ({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
  <p className={cn("text-sm text-muted-foreground/70", className)} {...props} />
);

export const CardContent = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("pt-0", className)} {...props} />
);

export const CardFooter = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("flex items-center pt-4 border-t border-border/20 mt-4", className)} {...props} />
);
