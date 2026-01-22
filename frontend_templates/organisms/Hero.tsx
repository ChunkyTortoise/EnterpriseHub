import { motion } from "framer-motion";
import { ArrowRight, Play } from "lucide-react";
import { Button } from "../atoms/Button";
import * as React from "react";

/**
 * ELITE HERO SECTION
 * Modern layout with animated typography and 
 * glassmorphism background elements.
 */

export const Hero = () => {
  return (
    <div className="relative min-h-[80vh] flex items-center justify-center overflow-hidden py-20 px-6">
      {/* Background Decor */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-full pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-primary/20 blur-[120px] rounded-full animate-pulse" />
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-secondary/20 blur-[150px] rounded-full" />
      </div>

      <div className="max-w-5xl mx-auto text-center relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm font-medium text-primary mb-8">
            <span className="flex h-2 w-2 rounded-full bg-primary animate-ping" />
            New: v4.0 Platform Economy Active
          </span>
          
          <h1 className="text-6xl md:text-8xl font-black tracking-tighter mb-8 leading-[0.9]">
            TRANSFORM YOUR <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary via-blue-400 to-secondary">
              REAL ESTATE
            </span>
          </h1>
          
          <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto mb-12 leading-relaxed">
            Autonomous AI agents, predictive lead intelligence, and 
            seamless GHL integration in one elite command center.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <Button size="lg" className="group h-16 px-10 text-lg rounded-2xl">
              Get Started Now
              <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Button>
            
            <button className="flex items-center gap-3 font-semibold hover:text-primary transition-colors py-4">
              <div className="h-12 w-12 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
                <Play className="h-5 w-5 fill-current" />
              </div>
              Watch Demo
            </button>
          </div>
        </motion.div>

        {/* Floating Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-24">
          {[
            { label: "Active Nodes", val: "1.2k" },
            { label: "Total Volume", val: "$4.5B" },
            { label: "Efficiency", val: "99.9%" },
            { label: "Users", val: "50k+" },
          ].map((stat) => (
            <div key={stat.label} className="flex flex-col">
              <span className="text-3xl font-bold tracking-tight">{stat.val}</span>
              <span className="text-xs text-muted-foreground uppercase tracking-widest">{stat.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
