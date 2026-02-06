'use client';

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { XMarkIcon, ArrowDownTrayIcon } from "@heroicons/react/24/outline";

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
}

export function PWAInstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);
  const [isInstalling, setIsInstalling] = useState(false);

  useEffect(() => {
    // Check if app is already installed
    const checkInstalled = () => {
      // Check if running in standalone mode (installed PWA)
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
      // Check for iOS home screen app
      const isIOS = (window.navigator as any).standalone === true;
      // Check for Android TWA or installed PWA
      const isAndroidInstalled = document.referrer.includes('android-app://');

      setIsInstalled(isStandalone || isIOS || isAndroidInstalled);
    };

    checkInstalled();

    // Listen for beforeinstallprompt event
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      const promptEvent = e as BeforeInstallPromptEvent;
      setDeferredPrompt(promptEvent);

      // Show prompt after a delay (not immediately on page load)
      setTimeout(() => {
        if (!isInstalled) {
          setShowPrompt(true);
        }
      }, 10000); // 10 second delay
    };

    // Listen for app installed event
    const handleAppInstalled = () => {
      setIsInstalled(true);
      setShowPrompt(false);
      setDeferredPrompt(null);

      // Show success message
      console.log('Jorge AI app installed successfully!');
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, [isInstalled]);

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    setIsInstalling(true);

    try {
      // Show the install prompt
      await deferredPrompt.prompt();

      // Wait for the user to respond
      const { outcome } = await deferredPrompt.userChoice;

      if (outcome === 'accepted') {
        console.log('User accepted the install prompt');
        setIsInstalled(true);
      } else {
        console.log('User dismissed the install prompt');
      }

      setDeferredPrompt(null);
      setShowPrompt(false);
    } catch (error) {
      console.error('Error during PWA installation:', error);
    } finally {
      setIsInstalling(false);
    }
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    // Don't show again for this session
    sessionStorage.setItem('pwa-prompt-dismissed', 'true');
  };

  // Don't show if already installed or user dismissed in this session
  if (isInstalled || sessionStorage.getItem('pwa-prompt-dismissed')) {
    return null;
  }

  return (
    <AnimatePresence>
      {showPrompt && deferredPrompt && (
        <motion.div
          initial={{ opacity: 0, y: 100 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 100 }}
          className="fixed bottom-20 left-4 right-4 z-50"
        >
          <div className="jorge-glass rounded-2xl p-4 border border-jorge-electric/30">
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-jorge-gradient rounded-xl flex items-center justify-center">
                  <ArrowDownTrayIcon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="jorge-heading text-sm text-white">
                    Install Jorge AI
                  </h3>
                  <p className="text-xs text-gray-400 jorge-code">
                    Get faster access with offline features
                  </p>
                </div>
              </div>

              <button
                onClick={handleDismiss}
                className="p-1 text-gray-400 hover:text-white transition-colors jorge-haptic"
              >
                <XMarkIcon className="w-4 h-4" />
              </button>
            </div>

            {/* Benefits */}
            <div className="space-y-2 mb-4">
              <div className="flex items-center gap-2 text-xs text-gray-300">
                <div className="w-1 h-1 bg-jorge-electric rounded-full" />
                <span>Instant access from home screen</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-300">
                <div className="w-1 h-1 bg-jorge-electric rounded-full" />
                <span>Offline bot conversations</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-300">
                <div className="w-1 h-1 bg-jorge-electric rounded-full" />
                <span>Push notifications for hot leads</span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={handleDismiss}
                className="flex-1 px-3 py-2 text-sm text-gray-400 hover:text-white transition-colors jorge-haptic"
              >
                Not now
              </button>
              <button
                onClick={handleInstall}
                disabled={isInstalling}
                className={`
                  flex-1 px-3 py-2 text-sm font-semibold rounded-lg transition-all jorge-haptic
                  ${isInstalling
                    ? 'bg-gray-600 text-gray-300 cursor-not-allowed'
                    : 'bg-jorge-gradient text-white hover:shadow-lg'
                  }
                `}
              >
                {isInstalling ? (
                  <div className="flex items-center justify-center gap-2">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="w-3 h-3 border border-white border-t-transparent rounded-full"
                    />
                    Installing...
                  </div>
                ) : (
                  'Install App'
                )}
              </button>
            </div>

            {/* Visual enhancement */}
            <motion.div
              animate={{
                scale: [1, 1.05, 1],
                opacity: [0.5, 0.8, 0.5]
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut"
              }}
              className="absolute -top-2 -right-2 w-4 h-4 bg-jorge-electric rounded-full blur-sm"
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}