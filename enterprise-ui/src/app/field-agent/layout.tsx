'use client';

import { motion } from "framer-motion";
import { Suspense } from "react";
import { MobileNavigation } from "@/components/mobile/MobileNavigation";
import { OfflineIndicator } from "@/components/mobile/OfflineIndicator";
import { PWAInstallPrompt } from "@/components/mobile/PWAInstallPrompt";

interface FieldAgentLayoutProps {
  children: React.ReactNode;
}

export default function FieldAgentLayout({ children }: FieldAgentLayoutProps) {
  return (
    <div className="relative min-h-screen bg-jorge-gradient-dark overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,82,255,0.1)_0%,transparent_50%)] transform-gpu" />
        <div className="absolute top-0 left-0 w-full h-full bg-[linear-gradient(90deg,transparent_0%,rgba(0,163,255,0.05)_50%,transparent_100%)] animate-pulse" />
      </div>

      {/* Main Content Container */}
      <div className="relative z-10 flex flex-col min-h-screen safe-top safe-bottom">
        {/* Status Bar */}
        <div className="flex items-center justify-between px-4 py-2 bg-black/20 backdrop-blur-sm border-b border-white/5">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-jorge-electric jorge-glow-pulse" />
            <span className="text-xs jorge-code text-jorge-electric">
              JORGE AI ACTIVE
            </span>
          </div>

          <OfflineIndicator />
        </div>

        {/* Main Content Area */}
        <main className="flex-1 px-4 py-6 overflow-y-auto">
          <Suspense fallback={<LoadingSkeleton />}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
              className="space-y-6"
            >
              {children}
            </motion.div>
          </Suspense>
        </main>

        {/* Mobile Navigation */}
        <MobileNavigation />
      </div>

      {/* PWA Install Prompt */}
      <PWAInstallPrompt />

      {/* Emergency Contact Overlay */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        className="fixed bottom-24 right-4 z-50"
      >
        <button className="w-12 h-12 rounded-full bg-jorge-gradient shadow-lg jorge-haptic">
          <span className="text-white text-xl">🆘</span>
        </button>
      </motion.div>
    </div>
  );
}

// Loading skeleton for field agent interface
function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div className="h-8 w-48 bg-white/10 rounded-lg" />
        <div className="h-8 w-16 bg-white/10 rounded-lg" />
      </div>

      {/* Bot cards skeleton */}
      <div className="grid grid-cols-2 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-24 bg-white/5 rounded-xl border border-white/10"
          />
        ))}
      </div>

      {/* Quick actions skeleton */}
      <div className="space-y-3">
        <div className="h-4 w-24 bg-white/10 rounded" />
        <div className="flex gap-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 flex-1 bg-white/5 rounded-lg" />
          ))}
        </div>
      </div>

      {/* Properties skeleton */}
      <div className="space-y-3">
        <div className="h-4 w-32 bg-white/10 rounded" />
        {[1, 2].map((i) => (
          <div
            key={i}
            className="h-20 bg-white/5 rounded-xl border border-white/10"
          />
        ))}
      </div>
    </div>
  );
}