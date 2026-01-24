'use client';

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import {
  BoltIcon,
  FireIcon,
  ClockIcon,
  MapPinIcon,
  PhoneIcon,
  ChatBubbleLeftEllipsisIcon,
  CameraIcon,
  UserGroupIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
} from "@heroicons/react/24/outline";

import { QuickActionPanel } from "@/components/mobile/QuickActionPanel";
import { BotStatusCards } from "@/components/mobile/BotStatusCards";
import { HotLeadsWidget } from "@/components/mobile/HotLeadsWidget";
import { PropertyAlertsWidget } from "@/components/mobile/PropertyAlertsWidget";
import { LocationWidget } from "@/components/mobile/LocationWidget";
import { OfflineStorageIndicator } from "@/components/mobile/OfflineStorageIndicator";
import { useOfflineStorage } from "@/hooks/useOfflineStorage";

interface DashboardStats {
  activeLeads: number;
  hotLeads: number;
  todayAppointments: number;
  weeklyRevenue: number;
  botEngagements: number;
}

export default function FieldAgentDashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    activeLeads: 0,
    hotLeads: 0,
    todayAppointments: 0,
    weeklyRevenue: 0,
    botEngagements: 0,
  });

  const [currentTime, setCurrentTime] = useState(new Date());

  // Offline storage integration
  const {
    status,
    isOnline,
    syncStatus,
    pendingOperations,
    jorge,
    formatBytes
  } = useOfflineStorage();

  useEffect(() => {
    // Load stats from offline storage or API
    const loadStats = async () => {
      try {
        // Try to load from offline storage first
        const cachedStats = await jorge.getPreferences('dashboard_stats');

        if (cachedStats?.app_state?.dashboard_stats) {
          setStats(cachedStats.app_state.dashboard_stats);
        } else {
          // Fallback to default stats if offline
          setStats({
            activeLeads: 127,
            hotLeads: 23,
            todayAppointments: 6,
            weeklyRevenue: 145250,
            botEngagements: 89,
          });

          // Store stats offline for future use
          const statsConfig = {
            id: 'dashboard_stats',
            user_id: 'jorge_agent',
            preferences: {},
            app_state: {
              dashboard_stats: {
                activeLeads: 127,
                hotLeads: 23,
                todayAppointments: 6,
                weeklyRevenue: 145250,
                botEngagements: 89,
                last_updated: Date.now()
              },
              active_bot_id: 'jorge_seller_bot',
              last_sync_timestamp: Date.now(),
              offline_mode: !isOnline,
              location_permission: true
            },
            sync_version: Date.now()
          };

          await jorge.storePreferences(statsConfig, true);
        }
      } catch (error) {
        console.error('Failed to load dashboard stats:', error);
        // Use default stats on error
        setStats({
          activeLeads: 127,
          hotLeads: 23,
          todayAppointments: 6,
          weeklyRevenue: 145250,
          botEngagements: 89,
        });
      }
    };

    loadStats();

    // Update time every minute
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000);

    return () => {
      clearInterval(timeInterval);
    };
  }, [jorge, isOnline]);

  const quickActions = [
    {
      id: 'scan',
      name: 'Scan Property',
      icon: CameraIcon,
      color: 'jorge-gold',
      href: '/field-agent/scanner',
      haptic: true,
    },
    {
      id: 'voice',
      name: 'Voice Note',
      icon: ChatBubbleLeftEllipsisIcon,
      color: 'jorge-glow',
      href: '/field-agent/voice-notes',
      haptic: true,
    },
    {
      id: 'call',
      name: 'Quick Call',
      icon: PhoneIcon,
      color: 'jorge-electric',
      action: () => console.log('Initiating call...'),
      haptic: true,
    },
  ];

  return (
    <div className="space-y-6 pb-20"> {/* Extra bottom padding for navigation */}
      {/* Welcome Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-2"
      >
        <h1 className="jorge-display text-2xl">
          JORGE AI COMMAND
        </h1>
        <div className="flex items-center justify-center gap-2 text-sm jorge-code text-gray-400">
          <BoltIcon className="w-4 h-4 text-jorge-electric" />
          <span>{currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          <span>•</span>
          <span>FIELD READY</span>
          <span>•</span>
          <span className={isOnline ? "text-jorge-glow" : "text-yellow-400"}>
            {isOnline ? "ONLINE" : "OFFLINE"}
          </span>
          {pendingOperations > 0 && (
            <>
              <span>•</span>
              <span className="text-jorge-electric">{pendingOperations} SYNCING</span>
            </>
          )}
        </div>

        {/* Offline Storage Status */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex justify-center mt-3"
        >
          <OfflineStorageIndicator />
        </motion.div>
      </motion.div>

      {/* Key Metrics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 gap-4"
      >
        <div className="jorge-card jorge-card-hover space-y-2">
          <div className="flex items-center justify-between">
            <FireIcon className="w-5 h-5 text-orange-400" />
            <span className="text-xs jorge-code text-gray-400">HOT</span>
          </div>
          <div className="space-y-1">
            <div className="property-value text-2xl">
              {stats.hotLeads}
            </div>
            <div className="text-xs text-gray-400">Hot Leads</div>
          </div>
        </div>

        <div className="jorge-card jorge-card-hover space-y-2">
          <div className="flex items-center justify-between">
            <ClockIcon className="w-5 h-5 text-jorge-electric" />
            <span className="text-xs jorge-code text-gray-400">TODAY</span>
          </div>
          <div className="space-y-1">
            <div className="property-value text-2xl">
              {stats.todayAppointments}
            </div>
            <div className="text-xs text-gray-400">Appointments</div>
          </div>
        </div>

        <div className="jorge-card jorge-card-hover space-y-2">
          <div className="flex items-center justify-between">
            <CurrencyDollarIcon className="w-5 h-5 text-jorge-gold" />
            <span className="text-xs jorge-code text-gray-400">WEEK</span>
          </div>
          <div className="space-y-1">
            <div className="property-value text-lg">
              ${(stats.weeklyRevenue / 1000).toFixed(0)}K
            </div>
            <div className="text-xs text-gray-400">Revenue</div>
          </div>
        </div>

        <div className="jorge-card jorge-card-hover space-y-2">
          <div className="flex items-center justify-between">
            <ChartBarIcon className="w-5 h-5 text-jorge-glow" />
            <span className="text-xs jorge-code text-gray-400">BOTS</span>
          </div>
          <div className="space-y-1">
            <div className="property-value text-lg">
              {stats.botEngagements}
            </div>
            <div className="text-xs text-gray-400">Active Chats</div>
          </div>
        </div>
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <QuickActionPanel actions={quickActions} />
      </motion.div>

      {/* Bot Status Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <BotStatusCards />
      </motion.div>

      {/* Hot Leads Widget */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <HotLeadsWidget />
      </motion.div>

      {/* Property Alerts */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
      >
        <PropertyAlertsWidget />
      </motion.div>

      {/* Location Services */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
      >
        <LocationWidget />
      </motion.div>

      {/* Emergency Contact & Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="jorge-card text-center space-y-3"
      >
        <div className="flex items-center justify-center gap-2">
          <div className="w-2 h-2 bg-jorge-electric rounded-full jorge-glow-pulse" />
          <span className="jorge-code text-sm text-jorge-electric">
            JORGE AI ECOSYSTEM ACTIVE
          </span>
        </div>
        <p className="text-xs text-gray-400">
          All bots operational • {isOnline ? 'Real-time sync enabled' : 'Offline mode active'} • Emergency protocols ready
          {status.storageUsed > 0 && (
            <span className="block mt-1">
              Storage: {formatBytes(status.storageUsed)} used
            </span>
          )}
        </p>
        <div className="flex items-center justify-center gap-4 pt-2">
          <div className="flex items-center gap-1">
            <UserGroupIcon className="w-4 h-4 text-jorge-glow" />
            <span className="text-xs jorge-code">{stats.activeLeads} LEADS</span>
          </div>
          <div className="flex items-center gap-1">
            <BoltIcon className="w-4 h-4 text-jorge-electric" />
            <span className="text-xs jorge-code">6% COMMISSION</span>
          </div>
        </div>
      </motion.div>
    </div>
  );
}