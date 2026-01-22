import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * DASHBOARD GRID
 * Uses CSS Container Queries for true modular responsiveness.
 */

interface DashboardGridProps extends React.HTMLAttributes<HTMLDivElement> {
  columns?: 1 | 2 | 3 | 4 | 6;
  gap?: 'sm' | 'md' | 'lg';
}

export const DashboardGrid = ({
  className,
  columns = 3,
  gap = 'md',
  children,
  ...props
}: DashboardGridProps) => {
  const columnMap = {
    1: "grid-cols-1",
    2: "grid-cols-1 md:grid-cols-2",
    3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
    6: "grid-cols-2 md:grid-cols-3 lg:grid-cols-6",
  };

  const gapMap = {
    sm: "gap-2",
    md: "gap-4 lg:gap-6",
    lg: "gap-8 lg:gap-12",
  };

  return (
    <div
      className={cn(
        "grid w-full @container",
        columnMap[columns],
        gapMap[gap],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export const GridItem = ({ 
  className, 
  span = 1,
  children 
}: { 
  className?: string; 
  span?: 1 | 2 | 3 | 4; 
  children: React.ReactNode 
}) => {
  const spanMap = {
    1: "col-span-1",
    2: "col-span-1 md:col-span-2",
    3: "col-span-1 md:col-span-3",
    4: "col-span-1 md:col-span-4",
  };

  return (
    <div className={cn(spanMap[span], className)}>
      {children}
    </div>
  );
};
