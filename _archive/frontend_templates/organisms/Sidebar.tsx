import { motion } from "framer-motion";
import { 
  LayoutDashboard, 
  Users, 
  BarChart3, 
  Settings, 
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Database,
  Layers
} from "lucide-react";
import { cn } from "@/lib/utils";
import * as React from "react";

/**
 * ELITE SIDEBAR
 * Collapsible, glassmorphism, nested navigation support.
 */

export const Sidebar = () => {
  const [collapsed, setCollapsed] = React.useState(false);

  const menuItems = [
    { icon: <LayoutDashboard />, label: "Overview", active: true },
    { icon: <Users />, label: "Leads" },
    { icon: <BarChart3 />, label: "Analytics" },
    { icon: <Database />, label: "Intelligence" },
    { icon: <Layers />, label: "Integrations" },
    { icon: <Settings />, label: "Settings" },
  ];

  return (
    <motion.aside
      animate={{ width: collapsed ? 80 : 280 }}
      className="relative h-screen bg-background/50 backdrop-blur-3xl border-r border-white/5 flex flex-col transition-all duration-300 overflow-hidden"
    >
      {/* Sidebar Header */}
      <div className="p-6 flex items-center gap-3">
        <div className="h-10 w-10 shrink-0 bg-primary rounded-xl flex items-center justify-center shadow-lg shadow-primary/20">
          <Layers className="text-white h-6 w-6" />
        </div>
        {!collapsed && (
          <motion.span 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-xl font-black tracking-tighter"
          >
            HUB<span className="text-primary">OS</span>
          </motion.span>
        )}
      </div>

      {/* Toggle Button */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-3 top-20 h-6 w-6 bg-primary text-white rounded-full flex items-center justify-center shadow-xl border-2 border-background z-50 hover:scale-110 transition-transform"
      >
        {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 flex flex-col gap-2">
        {menuItems.map((item, i) => (
          <button
            key={i}
            className={cn(
              "group relative flex items-center gap-4 px-4 py-3 rounded-xl transition-all",
              item.active 
                ? "bg-primary text-primary-foreground shadow-lg shadow-primary/10" 
                : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
            )}
          >
            <div className={cn("shrink-0", item.active ? "text-white" : "group-hover:text-primary transition-colors")}>
              {React.cloneElement(item.icon as React.ReactElement, { size: 22 })}
            </div>
            
            {!collapsed && (
              <motion.span 
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="font-medium"
              >
                {item.label}
              </motion.span>
            )}

            {/* Tooltip for collapsed mode */}
            {collapsed && (
              <div className="absolute left-full ml-4 px-3 py-1 bg-foreground text-background text-xs rounded opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
                {item.label}
              </div>
            )}
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 mt-auto">
        <div className={cn(
          "flex items-center gap-3 p-3 bg-white/5 rounded-2xl border border-white/5",
          collapsed ? "justify-center" : ""
        )}>
          <HelpCircle className="h-5 w-5 text-muted-foreground" />
          {!collapsed && (
            <div className="flex flex-col">
              <span className="text-sm font-medium">Support</span>
              <span className="text-[10px] text-muted-foreground uppercase tracking-widest">Enterprise Elite</span>
            </div>
          )}
        </div>
      </div>
    </motion.aside>
  );
};
