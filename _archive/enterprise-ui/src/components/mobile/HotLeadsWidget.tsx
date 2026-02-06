'use client';

import { motion } from "framer-motion";
import { useState } from "react";
import {
  FireIcon,
  PhoneIcon,
  ChatBubbleLeftEllipsisIcon,
  ClockIcon,
  MapPinIcon,
  CurrencyDollarIcon,
  ChevronRightIcon,
} from "@heroicons/react/24/outline";

interface HotLead {
  id: string;
  name: string;
  phone: string;
  location: string;
  score: number;
  lastContact: string;
  propertyType: string;
  budget: number;
  urgency: 'hot' | 'warm' | 'lukewarm';
  notes: string;
  avatar?: string;
}

const hotLeadsData: HotLead[] = [
  {
    id: 'lead-001',
    name: 'Sarah Mitchell',
    phone: '+1 (555) 123-4567',
    location: 'Downtown Miami',
    score: 87,
    lastContact: '5 min ago',
    propertyType: 'Luxury Condo',
    budget: 850000,
    urgency: 'hot',
    notes: 'Ready to view properties this weekend. Pre-approved financing.',
  },
  {
    id: 'lead-002',
    name: 'Marcus Rodriguez',
    phone: '+1 (555) 987-6543',
    location: 'Coral Gables',
    score: 92,
    lastContact: '12 min ago',
    propertyType: 'Single Family',
    budget: 1200000,
    urgency: 'hot',
    notes: 'Referred by Jorge. Looking for quick close. Cash buyer.',
  },
  {
    id: 'lead-003',
    name: 'Jennifer Chen',
    phone: '+1 (555) 456-7890',
    location: 'Brickell',
    score: 74,
    lastContact: '1 hr ago',
    propertyType: 'Investment',
    budget: 650000,
    urgency: 'warm',
    notes: 'First-time investor. Needs guidance on rental properties.',
  },
];

export function HotLeadsWidget() {
  const [selectedLead, setSelectedLead] = useState<string | null>(null);

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'hot':
        return 'text-orange-400';
      case 'warm':
        return 'text-yellow-400';
      case 'lukewarm':
        return 'text-blue-400';
      default:
        return 'text-gray-400';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-jorge-gold';
    if (score >= 60) return 'text-jorge-glow';
    return 'text-gray-400';
  };

  const handleCall = (phone: string) => {
    if ('vibrate' in navigator) {
      navigator.vibrate(100);
    }
    window.location.href = `tel:${phone}`;
  };

  const handleMessage = (phone: string) => {
    if ('vibrate' in navigator) {
      navigator.vibrate(50);
    }
    window.location.href = `sms:${phone}`;
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FireIcon className="w-5 h-5 text-orange-400" />
          <h2 className="jorge-heading text-lg">Hot Leads</h2>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 bg-orange-400 rounded-full jorge-glow-pulse" />
          <span className="text-xs jorge-code text-orange-400">
            {hotLeadsData.filter(lead => lead.urgency === 'hot').length} HOT
          </span>
        </div>
      </div>

      <div className="space-y-3">
        {hotLeadsData.map((lead, index) => (
          <motion.div
            key={lead.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`
              jorge-card jorge-card-hover
              ${selectedLead === lead.id ? 'border-jorge-electric ring-1 ring-jorge-electric/30' : ''}
              cursor-pointer relative overflow-hidden
            `}
            onClick={() => setSelectedLead(selectedLead === lead.id ? null : lead.id)}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-start gap-3 flex-1">
                {/* Avatar */}
                <div className="w-10 h-10 bg-jorge-gradient rounded-full flex items-center justify-center">
                  <span className="text-white font-semibold text-sm">
                    {lead.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                  </span>
                </div>

                {/* Lead info */}
                <div className="flex-1 min-w-0">
                  <h3 className="jorge-code text-sm font-medium text-white truncate">
                    {lead.name}
                  </h3>
                  <div className="flex items-center gap-2 mt-1">
                    <div className={`w-2 h-2 rounded-full ${getUrgencyColor(lead.urgency)} jorge-glow-pulse`} />
                    <span className={`text-xs jorge-code ${getUrgencyColor(lead.urgency)}`}>
                      {lead.urgency.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-500">•</span>
                    <span className={`text-xs jorge-code font-bold ${getScoreColor(lead.score)}`}>
                      {lead.score}/100
                    </span>
                  </div>
                  <div className="flex items-center gap-1 mt-1">
                    <MapPinIcon className="w-3 h-3 text-gray-400" />
                    <span className="text-xs text-gray-400 truncate">{lead.location}</span>
                  </div>
                </div>
              </div>

              {/* Chevron */}
              <ChevronRightIcon
                className={`
                  w-4 h-4 text-gray-400 transition-transform duration-200
                  ${selectedLead === lead.id ? 'rotate-90' : ''}
                `}
              />
            </div>

            {/* Quick stats */}
            <div className="grid grid-cols-3 gap-2 mb-3">
              <div className="text-center">
                <div className="property-value text-sm">
                  ${(lead.budget / 1000).toFixed(0)}K
                </div>
                <div className="text-xs text-gray-400">Budget</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-white font-semibold">
                  {lead.propertyType.split(' ')[0]}
                </div>
                <div className="text-xs text-gray-400">Property</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-jorge-glow font-semibold">
                  {lead.lastContact}
                </div>
                <div className="text-xs text-gray-400">Contact</div>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex gap-2">
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={(e) => {
                  e.stopPropagation();
                  handleCall(lead.phone);
                }}
                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-jorge-electric/20 text-jorge-electric rounded-lg jorge-haptic"
              >
                <PhoneIcon className="w-4 h-4" />
                <span className="text-xs font-semibold">CALL</span>
              </motion.button>
              <motion.button
                whileTap={{ scale: 0.95 }}
                onClick={(e) => {
                  e.stopPropagation();
                  handleMessage(lead.phone);
                }}
                className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-jorge-glow/20 text-jorge-glow rounded-lg jorge-haptic"
              >
                <ChatBubbleLeftEllipsisIcon className="w-4 h-4" />
                <span className="text-xs font-semibold">TEXT</span>
              </motion.button>
            </div>

            {/* Expanded details */}
            {selectedLead === lead.id && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-3 pt-3 border-t border-white/10 space-y-2"
              >
                <div className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-400">Phone</span>
                    <span className="text-xs jorge-code text-white">{lead.phone}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-400">Property Type</span>
                    <span className="text-xs text-white">{lead.propertyType}</span>
                  </div>
                </div>

                <div className="mt-2">
                  <span className="text-xs text-gray-400">Notes:</span>
                  <p className="text-xs text-gray-300 mt-1">{lead.notes}</p>
                </div>

                <motion.button
                  whileTap={{ scale: 0.95 }}
                  className="w-full mt-3 px-3 py-2 bg-jorge-gold/20 text-jorge-gold text-xs font-semibold rounded-lg jorge-haptic"
                >
                  VIEW FULL PROFILE
                </motion.button>
              </motion.div>
            )}

            {/* Temperature indicator */}
            <motion.div
              animate={{
                scale: lead.urgency === 'hot' ? [1, 1.2, 1] : 1,
                opacity: lead.urgency === 'hot' ? [0.7, 1, 0.7] : 1
              }}
              transition={{
                duration: 2,
                repeat: lead.urgency === 'hot' ? Infinity : 0,
                ease: "easeInOut"
              }}
              className={`
                absolute top-2 right-2 w-2 h-2 rounded-full
                ${lead.urgency === 'hot' ? 'bg-orange-400' :
                  lead.urgency === 'warm' ? 'bg-yellow-400' : 'bg-blue-400'}
              `}
            />
          </motion.div>
        ))}
      </div>

      {/* Summary stats */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="jorge-card text-center space-y-2"
      >
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="property-value text-lg">
              {hotLeadsData.filter(lead => lead.urgency === 'hot').length}
            </div>
            <div className="text-xs text-gray-400">Hot Leads</div>
          </div>
          <div>
            <div className="property-value text-lg">
              ${(hotLeadsData.reduce((sum, lead) => sum + lead.budget, 0) / 1000000).toFixed(1)}M
            </div>
            <div className="text-xs text-gray-400">Total Value</div>
          </div>
          <div>
            <div className="property-value text-lg">
              {Math.round(hotLeadsData.reduce((sum, lead) => sum + lead.score, 0) / hotLeadsData.length)}
            </div>
            <div className="text-xs text-gray-400">Avg Score</div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}