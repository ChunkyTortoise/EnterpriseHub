import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import * as React from "react";

/**
 * ELITE TOOLTIP
 * Ultra-lightweight CSS/Framer motion tooltip.
 */

interface TooltipProps {
  content: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export const Tooltip = ({ content, children, position = 'top' }: TooltipProps) => {
  const [show, setShow] = React.useState(false);

  const positions = {
    top: "-top-2 left-1/2 -translate-x-1/2 -translate-y-full mb-2",
    bottom: "-bottom-2 left-1/2 -translate-x-1/2 translate-y-full mt-2",
    left: "top-1/2 -left-2 -translate-x-full -translate-y-1/2 mr-2",
    right: "top-1/2 -right-2 translate-x-full -translate-y-1/2 ml-2",
  };

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      <AnimatePresence>
        {show && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className={cn(
              "absolute z-[200] px-3 py-1.5 bg-foreground text-background text-[11px] font-bold rounded-lg shadow-xl whitespace-nowrap pointer-events-none",
              positions[position]
            )}
          >
            {content}
            {/* Arrow */}
            <div className={cn(
              "absolute h-2 w-2 bg-foreground rotate-45",
              position === 'top' && "bottom-[-4px] left-1/2 -translate-x-1/2",
              position === 'bottom' && "top-[-4px] left-1/2 -translate-x-1/2",
              position === 'left' && "right-[-4px] top-1/2 -translate-y-1/2",
              position === 'right' && "left-[-4px] top-1/2 -translate-y-1/2",
            )} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
