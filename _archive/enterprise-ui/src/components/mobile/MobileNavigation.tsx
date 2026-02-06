'use client';

import { motion } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  HomeIcon,
  QrCodeIcon,
  MicrophoneIcon,
  PresentationChartBarIcon,
  ChatBubbleLeftRightIcon,
} from "@heroicons/react/24/outline";
import {
  HomeIcon as HomeIconSolid,
  QrCodeIcon as QrCodeIconSolid,
  MicrophoneIcon as MicrophoneIconSolid,
  PresentationChartBarIcon as PresentationChartBarIconSolid,
  ChatBubbleLeftRightIcon as ChatBubbleLeftRightIconSolid,
} from "@heroicons/react/24/solid";

const navigationItems = [
  {
    name: "Dashboard",
    href: "/field-agent",
    icon: HomeIcon,
    activeIcon: HomeIconSolid,
    color: "jorge-electric",
  },
  {
    name: "Scanner",
    href: "/field-agent/scanner",
    icon: QrCodeIcon,
    activeIcon: QrCodeIconSolid,
    color: "jorge-gold",
  },
  {
    name: "Voice",
    href: "/field-agent/voice-notes",
    icon: MicrophoneIcon,
    activeIcon: MicrophoneIconSolid,
    color: "jorge-glow",
  },
  {
    name: "Bots",
    href: "/field-agent/conversations",
    icon: ChatBubbleLeftRightIcon,
    activeIcon: ChatBubbleLeftRightIconSolid,
    color: "jorge-steel",
  },
  {
    name: "Present",
    href: "/presentation",
    icon: PresentationChartBarIcon,
    activeIcon: PresentationChartBarIconSolid,
    color: "jorge-gold",
  },
];

export function MobileNavigation() {
  const pathname = usePathname();

  return (
    <motion.nav
      initial={{ y: 100 }}
      animate={{ y: 0 }}
      className="fixed bottom-0 left-0 right-0 z-40 safe-bottom"
    >
      {/* Gradient backdrop */}
      <div className="absolute inset-0 bg-gradient-to-t from-black via-black/90 to-transparent backdrop-blur-xl" />

      {/* Navigation container */}
      <div className="relative px-4 py-2">
        <div className="jorge-glass rounded-2xl p-3">
          <div className="flex items-center justify-around">
            {navigationItems.map((item) => {
              const isActive = pathname === item.href ||
                (item.href !== "/field-agent" && pathname.startsWith(item.href));

              const Icon = isActive ? item.activeIcon : item.icon;

              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className="relative flex flex-col items-center jorge-touch-target jorge-haptic"
                >
                  {/* Active indicator */}
                  {isActive && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute -top-1 w-8 h-1 bg-jorge-electric rounded-full"
                      initial={false}
                      transition={{
                        type: "spring",
                        stiffness: 500,
                        damping: 30
                      }}
                    />
                  )}

                  {/* Icon container */}
                  <div className={`
                    relative p-2 rounded-xl transition-all duration-200
                    ${isActive
                      ? 'bg-jorge-electric/20 scale-110'
                      : 'hover:bg-white/5 scale-100'
                    }
                  `}>
                    <Icon
                      className={`
                        w-6 h-6 transition-all duration-200
                        ${isActive
                          ? 'text-jorge-electric'
                          : 'text-gray-400'
                        }
                      `}
                    />

                    {/* Glow effect for active state */}
                    {isActive && (
                      <motion.div
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="absolute inset-0 bg-jorge-electric/20 rounded-xl blur-sm -z-10"
                      />
                    )}
                  </div>

                  {/* Label */}
                  <span className={`
                    text-xs jorge-code mt-1 transition-all duration-200
                    ${isActive
                      ? 'text-jorge-electric font-semibold'
                      : 'text-gray-500'
                    }
                  `}>
                    {item.name}
                  </span>

                  {/* Haptic feedback ripple */}
                  <motion.div
                    className="absolute inset-0 bg-white/10 rounded-xl"
                    initial={{ scale: 1, opacity: 0 }}
                    whileTap={{ scale: 1.2, opacity: 1 }}
                    animate={{ scale: 1, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  />
                </Link>
              );
            })}
          </div>

          {/* Notification badges */}
          <div className="absolute -top-1 -right-1">
            <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
          </div>
        </div>
      </div>
    </motion.nav>
  );
}