'use client';

import { motion } from "framer-motion";
import { useState } from "react";
import Link from "next/link";
import {
  UserIcon,
  HomeIcon,
  ChatBubbleLeftRightIcon,
  ChartBarIcon,
  FireIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";

interface BotStatus {
  id: string;
  name: string;
  type: 'seller' | 'buyer' | 'lead' | 'analytics';
  status: 'active' | 'idle' | 'processing' | 'error';
  activeChats: number;
  lastActivity: string;
  performance: {
    todayLeads: number;
    conversionRate: number;
    avgResponseTime: number;
  };
  temperature: 'hot' | 'warm' | 'cold';
}

const botData: BotStatus[] = [
  {
    id: 'jorge-seller',
    name: 'Jorge Seller Bot',
    type: 'seller',
    status: 'active',
    activeChats: 12,
    lastActivity: '2 min ago',
    performance: {
      todayLeads: 8,
      conversionRate: 67,
      avgResponseTime: 1.2,
    },
    temperature: 'hot',
  },
  {
    id: 'lead-nurture',
    name: 'Lead Nurture Bot',
    type: 'lead',
    status: 'processing',
    activeChats: 23,
    lastActivity: 'Just now',
    performance: {
      todayLeads: 15,
      conversionRate: 43,
      avgResponseTime: 2.1,
    },
    temperature: 'warm',
  },
  {
    id: 'buyer-assistant',
    name: 'Buyer Assistant',
    type: 'buyer',
    status: 'idle',
    activeChats: 5,
    lastActivity: '12 min ago',
    performance: {
      todayLeads: 4,
      conversionRate: 38,
      avgResponseTime: 3.5,
    },
    temperature: 'warm',
  },
  {
    id: 'analytics-engine',
    name: 'ML Analytics',
    type: 'analytics',
    status: 'active',
    activeChats: 0,
    lastActivity: 'Real-time',
    performance: {
      todayLeads: 0,
      conversionRate: 95, // Accuracy rate
      avgResponseTime: 0.04,
    },
    temperature: 'hot',
  },
];

export function BotStatusCards() {
  const [selectedBot, setSelectedBot] = useState<string | null>(null);

  const getBotIcon = (type: string) => {
    switch (type) {
      case 'seller':
        return HomeIcon;
      case 'buyer':
        return UserIcon;
      case 'lead':
        return ChatBubbleLeftRightIcon;
      case 'analytics':
        return ChartBarIcon;
      default:
        return ChatBubbleLeftRightIcon;
    }
  };

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'active':
        return {
          color: 'jorge-glow',
          bgColor: 'bg-jorge-glow/20',
          icon: CheckCircleIcon,
          text: 'ACTIVE',
        };
      case 'processing':
        return {
          color: 'jorge-electric',
          bgColor: 'bg-jorge-electric/20',
          icon: ClockIcon,
          text: 'PROCESSING',
        };
      case 'idle':
        return {
          color: 'gray-400',
          bgColor: 'bg-gray-500/20',
          icon: ClockIcon,
          text: 'IDLE',
        };
      case 'error':
        return {
          color: 'red-400',
          bgColor: 'bg-red-500/20',
          icon: ExclamationTriangleIcon,
          text: 'ERROR',
        };
      default:
        return {
          color: 'gray-400',
          bgColor: 'bg-gray-500/20',
          icon: ClockIcon,
          text: 'UNKNOWN',
        };
    }
  };

  const getTemperatureColor = (temp: string) => {
    switch (temp) {
      case 'hot':
        return 'text-orange-400';
      case 'warm':
        return 'text-yellow-400';
      case 'cold':
        return 'text-blue-400';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="jorge-heading text-lg">Jorge's Bot Ecosystem</h2>
        <div className="flex items-center gap-1">
          <FireIcon className="w-4 h-4 text-orange-400" />
          <span className="text-xs jorge-code text-gray-400">LIVE</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {botData.map((bot, index) => {
          const BotIcon = getBotIcon(bot.type);
          const statusConfig = getStatusConfig(bot.status);
          const StatusIcon = statusConfig.icon;

          return (
            <motion.div
              key={bot.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileTap={{ scale: 0.98 }}
              className={`
                jorge-card jorge-card-hover jorge-haptic cursor-pointer
                ${selectedBot === bot.id ? 'border-jorge-electric ring-1 ring-jorge-electric/30' : ''}
                relative overflow-hidden group
              `}
              onClick={() => setSelectedBot(selectedBot === bot.id ? null : bot.id)}
            >
              {/* Background pattern */}
              <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className={`p-2 rounded-lg ${statusConfig.bgColor}`}>
                    <BotIcon className={`w-4 h-4 text-${statusConfig.color}`} />
                  </div>
                  <div>
                    <h3 className="jorge-code text-sm font-medium text-white truncate">
                      {bot.name}
                    </h3>
                    <div className="flex items-center gap-1">
                      <StatusIcon className={`w-3 h-3 text-${statusConfig.color}`} />
                      <span className={`text-xs jorge-code text-${statusConfig.color}`}>
                        {statusConfig.text}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Temperature indicator */}
                <div className={`w-2 h-2 rounded-full ${getTemperatureColor(bot.temperature)} jorge-glow-pulse`} />
              </div>

              {/* Stats */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">Active Chats</span>
                  <span className="property-value text-sm">{bot.activeChats}</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">Today Leads</span>
                  <span className="property-value text-sm">{bot.performance.todayLeads}</span>
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-400">
                    {bot.type === 'analytics' ? 'Accuracy' : 'Conversion'}
                  </span>
                  <span className="text-sm text-jorge-glow font-semibold">
                    {bot.performance.conversionRate}%
                  </span>
                </div>
              </div>

              {/* Last activity */}
              <div className="mt-3 pt-3 border-t border-white/10">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">Last Activity</span>
                  <span className="text-xs jorge-code text-gray-400">
                    {bot.lastActivity}
                  </span>
                </div>
              </div>

              {/* Expanded details */}
              {selectedBot === bot.id && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-3 pt-3 border-t border-white/10 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-400">Response Time</span>
                    <span className="text-xs jorge-code text-white">
                      {bot.performance.avgResponseTime}s
                    </span>
                  </div>

                  <Link
                    href={`/field-agent/conversations/${bot.id}`}
                    className="w-full mt-2 px-3 py-2 bg-jorge-electric/20 text-jorge-electric text-xs font-semibold rounded-lg text-center block jorge-haptic"
                  >
                    VIEW CONVERSATIONS
                  </Link>
                </motion.div>
              )}

              {/* Activity pulse for active bots */}
              {bot.status === 'active' && (
                <motion.div
                  animate={{
                    scale: [1, 1.1, 1],
                    opacity: [0.7, 1, 0.7]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                  className="absolute top-2 right-2 w-2 h-2 bg-jorge-glow rounded-full"
                />
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Overall status */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="jorge-card text-center space-y-2"
      >
        <div className="flex items-center justify-center gap-2">
          <CheckCircleIcon className="w-4 h-4 text-jorge-glow" />
          <span className="jorge-code text-sm text-jorge-glow">
            ALL BOTS OPERATIONAL
          </span>
        </div>
        <p className="text-xs text-gray-400">
          {botData.reduce((sum, bot) => sum + bot.activeChats, 0)} active conversations •
          {botData.reduce((sum, bot) => sum + bot.performance.todayLeads, 0)} leads today •
          Real-time sync enabled
        </p>
      </motion.div>
    </div>
  );
}