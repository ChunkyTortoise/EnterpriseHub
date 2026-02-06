import { motion } from "framer-motion";
import { Menu, X, Command, Bell, User } from "lucide-react";
import { cn } from "@/lib/utils";
import * as React from "react";

/**
 * ELITE NAVIGATION
 * Sticky, blurred backdrop, responsive menu, 
 * and active state indicator.
 */

export const Navigation = () => {
  const [isOpen, setIsOpen] = React.useState(false);
  const [scrolled, setScrolled] = React.useState(false);

  React.useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { label: "Dashboard", href: "#" },
    { label: "Analytics", href: "#" },
    { label: "Inventory", href: "#" },
    { label: "Settings", href: "#" },
  ];

  return (
    <nav
      className={cn(
        "fixed top-0 left-0 right-0 z-[100] transition-all duration-300 px-6",
        scrolled ? "py-3 bg-background/80 backdrop-blur-xl border-b border-white/5 shadow-xl" : "py-6 bg-transparent"
      )}
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-8">
          {/* Logo */}
          <div className="flex items-center gap-2 group cursor-pointer">
            <div className="h-10 w-10 bg-primary rounded-xl flex items-center justify-center shadow-lg shadow-primary/20 group-hover:scale-110 transition-transform">
              <Command className="text-primary-foreground h-6 w-6" />
            </div>
            <span className="text-xl font-bold tracking-tight">EnterpriseHub</span>
          </div>

          {/* Desktop Links */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/5 rounded-lg transition-all"
              >
                {link.label}
              </a>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="hidden md:flex items-center gap-4">
          <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-white/5 rounded-full relative transition-all">
            <Bell className="h-5 w-5" />
            <span className="absolute top-2 right-2 h-2 w-2 bg-primary rounded-full" />
          </button>
          
          <div className="h-8 w-[1px] bg-white/10 mx-2" />
          
          <button className="flex items-center gap-3 px-1.5 py-1.5 bg-white/5 rounded-full border border-white/10 hover:border-white/20 transition-all">
            <div className="h-8 w-8 bg-gradient-to-tr from-primary to-secondary rounded-full flex items-center justify-center">
              <User className="h-4 w-4 text-white" />
            </div>
            <span className="text-sm font-medium pr-3">Admin</span>
          </button>
        </div>

        {/* Mobile Toggle */}
        <button
          className="md:hidden p-2 text-foreground"
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? <X /> : <Menu />}
        </button>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden mt-4 overflow-hidden bg-background/95 backdrop-blur-2xl rounded-2xl border border-white/10"
          >
            <div className="p-4 flex flex-col gap-2">
              {navLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  className="px-4 py-3 text-lg font-medium border-b border-white/5 last:border-0"
                >
                  {link.label}
                </a>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
};
