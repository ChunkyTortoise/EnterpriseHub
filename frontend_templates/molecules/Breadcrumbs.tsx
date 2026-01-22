import { ChevronRight, Home } from "lucide-react";
import { cn } from "@/lib/utils";
import * as React from "react";

/**
 * ELITE BREADCRUMBS
 * Responsive navigation utility.
 */

interface BreadcrumbItem {
  label: string;
  href?: string;
}

export const Breadcrumbs = ({ 
  items, 
  className 
}: { 
  items: BreadcrumbItem[]; 
  className?: string;
}) => {
  return (
    <nav className={cn("flex items-center gap-2 overflow-x-auto no-scrollbar py-2", className)}>
      <a href="/" className="text-muted-foreground hover:text-foreground transition-colors p-1">
        <Home className="h-4 w-4" />
      </a>
      
      {items.map((item, i) => (
        <React.Fragment key={i}>
          <ChevronRight className="h-4 w-4 text-muted-foreground/40 shrink-0" />
          <a
            href={item.href}
            className={cn(
              "text-sm font-medium transition-colors whitespace-nowrap",
              i === items.length - 1 
                ? "text-foreground cursor-default" 
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {item.label}
          </a>
        </React.Fragment>
      ))}
    </nav>
  );
};
