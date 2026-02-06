import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import * as React from "react";

/**
 * ELITE TABS
 * Modern tab system with sliding indicator.
 */

interface Tab {
  id: string;
  label: string;
  icon?: React.ReactNode;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (id: string) => void;
  className?: string;
}

export const Tabs = ({ tabs, activeTab, onChange, className }: TabsProps) => {
  return (
    <div className={cn("relative flex items-center gap-1 p-1 bg-white/5 backdrop-blur-sm rounded-xl border border-white/5", className)}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={cn(
            "relative z-10 flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors",
            activeTab === tab.id ? "text-primary-foreground" : "text-muted-foreground hover:text-foreground"
          )}
        >
          {tab.icon}
          {tab.label}
          
          {activeTab === tab.id && (
            <motion.div
              layoutId="active-tab"
              className="absolute inset-0 bg-primary rounded-lg -z-10 shadow-lg shadow-primary/20"
              transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
            />
          )}
        </button>
      ))}
    </div>
  );
};
