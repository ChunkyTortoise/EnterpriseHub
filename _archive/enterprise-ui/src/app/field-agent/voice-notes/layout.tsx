'use client';

import { motion } from "framer-motion";
import { VoicePermissionsProvider } from "@/components/mobile/voice/VoicePermissionsProvider";
import { VoiceProcessingIndicator } from "@/components/mobile/voice/VoiceProcessingIndicator";

interface VoiceNotesLayoutProps {
  children: React.ReactNode;
}

export default function VoiceNotesLayout({ children }: VoiceNotesLayoutProps) {
  return (
    <VoicePermissionsProvider>
      <div className="relative space-y-6">
        {/* Voice Processing Indicator */}
        <VoiceProcessingIndicator />

        {/* Voice Notes Content */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          {children}
        </motion.div>

        {/* Background Audio Visualization */}
        <div className="fixed inset-0 pointer-events-none z-0">
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/20" />

          {/* Subtle audio wave pattern */}
          <div className="absolute bottom-0 left-0 right-0 h-32 opacity-5">
            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(0,163,255,0.3)_0%,transparent_70%)]" />
            <div className="absolute inset-0 bg-[linear-gradient(90deg,transparent_0%,rgba(0,163,255,0.1)_50%,transparent_100%)] animate-pulse" />
          </div>
        </div>
      </div>
    </VoicePermissionsProvider>
  );
}