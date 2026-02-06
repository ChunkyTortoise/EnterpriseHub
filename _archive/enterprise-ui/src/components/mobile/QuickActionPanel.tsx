'use client';

import { motion } from "framer-motion";
import Link from "next/link";
import { HeroIcon } from "@/types/ui";

interface QuickAction {
  id: string;
  name: string;
  icon: HeroIcon;
  color: string;
  href?: string;
  action?: () => void;
  haptic?: boolean;
}

interface QuickActionPanelProps {
  actions: QuickAction[];
}

export function QuickActionPanel({ actions }: QuickActionPanelProps) {
  const handleAction = (action: QuickAction) => {
    if (action.haptic && 'vibrate' in navigator) {
      navigator.vibrate(50); // Light haptic feedback
    }

    if (action.action) {
      action.action();
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="jorge-heading text-lg">Quick Actions</h2>
        <div className="flex items-center gap-1">
          <div className="w-1 h-1 bg-jorge-electric rounded-full" />
          <div className="w-1 h-1 bg-jorge-glow rounded-full animate-pulse" />
          <div className="w-1 h-1 bg-jorge-gold rounded-full" />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {actions.map((action, index) => {
          const Icon = action.icon;

          const content = (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{
                delay: index * 0.1,
                type: "spring",
                stiffness: 300,
                damping: 20
              }}
              whileTap={{ scale: 0.95 }}
              className={`
                jorge-card jorge-card-hover jorge-touch-target jorge-haptic
                flex flex-col items-center justify-center gap-3 py-6
                border-l-2 border-${action.color}/50
                hover:border-${action.color}
                group cursor-pointer
                relative overflow-hidden
              `}
              onClick={() => handleAction(action)}
            >
              {/* Background gradient effect */}
              <div className={`
                absolute inset-0 bg-gradient-to-br from-${action.color}/5 to-transparent
                opacity-0 group-hover:opacity-100 transition-opacity duration-300
              `} />

              {/* Icon container */}
              <div className={`
                relative p-3 rounded-xl bg-${action.color}/10
                group-hover:bg-${action.color}/20 transition-colors duration-200
              `}>
                <Icon className={`w-6 h-6 text-${action.color}`} />

                {/* Glow effect */}
                <motion.div
                  animate={{
                    scale: [1, 1.2, 1],
                    opacity: [0, 0.6, 0]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: index * 0.3
                  }}
                  className={`
                    absolute inset-0 bg-${action.color}/20 rounded-xl blur-md -z-10
                  `}
                />
              </div>

              {/* Label */}
              <span className="jorge-code text-sm text-white font-medium text-center">
                {action.name}
              </span>

              {/* Active indicator */}
              <motion.div
                className={`
                  absolute top-2 right-2 w-2 h-2 bg-${action.color} rounded-full
                  opacity-0 group-hover:opacity-100
                `}
                layoutId={`quick-action-${action.id}`}
              />

              {/* Ripple effect on tap */}
              <motion.div
                className="absolute inset-0 bg-white/10 rounded-xl"
                initial={{ scale: 0, opacity: 1 }}
                whileTap={{
                  scale: 2,
                  opacity: 0,
                  transition: { duration: 0.3 }
                }}
              />
            </motion.div>
          );

          return action.href ? (
            <Link key={action.id} href={action.href}>
              {content}
            </Link>
          ) : (
            <div key={action.id}>
              {content}
            </div>
          );
        })}
      </div>

      {/* Usage tip for new users */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5 }}
        className="text-center text-xs text-gray-500 jorge-code"
      >
        Tap for haptic feedback • Hold for shortcuts
      </motion.div>
    </div>
  );
}