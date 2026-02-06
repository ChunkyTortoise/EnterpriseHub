'use client';

import { motion } from "framer-motion";
import { useState } from "react";
import {
  BellIcon,
  HomeIcon,
  MapPinIcon,
  CurrencyDollarIcon,
  CalendarIcon,
  HeartIcon,
  ShareIcon,
  EyeIcon,
} from "@heroicons/react/24/outline";

interface PropertyAlert {
  id: string;
  address: string;
  price: number;
  type: string;
  bedrooms: number;
  bathrooms: number;
  sqft: number;
  daysOnMarket: number;
  matchScore: number;
  leadName: string;
  alertType: 'new_listing' | 'price_drop' | 'back_on_market' | 'hot_property';
  timestamp: string;
  imageUrl?: string;
}

const propertyAlerts: PropertyAlert[] = [
  {
    id: 'prop-001',
    address: '1425 Brickell Avenue #45B',
    price: 875000,
    type: 'Luxury Condo',
    bedrooms: 2,
    bathrooms: 2,
    sqft: 1450,
    daysOnMarket: 1,
    matchScore: 94,
    leadName: 'Sarah Mitchell',
    alertType: 'new_listing',
    timestamp: '8 min ago',
  },
  {
    id: 'prop-002',
    address: '3401 Coral Way',
    price: 1150000,
    type: 'Single Family',
    bedrooms: 4,
    bathrooms: 3,
    sqft: 2800,
    daysOnMarket: 12,
    matchScore: 88,
    leadName: 'Marcus Rodriguez',
    alertType: 'price_drop',
    timestamp: '25 min ago',
  },
  {
    id: 'prop-003',
    address: '2100 Park Avenue #301',
    price: 685000,
    type: 'Investment Condo',
    bedrooms: 1,
    bathrooms: 1,
    sqft: 850,
    daysOnMarket: 3,
    matchScore: 76,
    leadName: 'Jennifer Chen',
    alertType: 'hot_property',
    timestamp: '1 hr ago',
  },
];

export function PropertyAlertsWidget() {
  const [selectedAlert, setSelectedAlert] = useState<string | null>(null);

  const getAlertTypeConfig = (type: string) => {
    switch (type) {
      case 'new_listing':
        return {
          icon: HomeIcon,
          label: 'NEW LISTING',
          color: 'jorge-glow',
          bgColor: 'bg-jorge-glow/20',
        };
      case 'price_drop':
        return {
          icon: CurrencyDollarIcon,
          label: 'PRICE DROP',
          color: 'jorge-gold',
          bgColor: 'bg-jorge-gold/20',
        };
      case 'back_on_market':
        return {
          icon: CalendarIcon,
          label: 'BACK ON MARKET',
          color: 'jorge-electric',
          bgColor: 'bg-jorge-electric/20',
        };
      case 'hot_property':
        return {
          icon: BellIcon,
          label: 'HOT PROPERTY',
          color: 'orange-400',
          bgColor: 'bg-orange-500/20',
        };
      default:
        return {
          icon: BellIcon,
          label: 'ALERT',
          color: 'gray-400',
          bgColor: 'bg-gray-500/20',
        };
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-jorge-gold';
    if (score >= 75) return 'text-jorge-glow';
    if (score >= 60) return 'text-jorge-electric';
    return 'text-gray-400';
  };

  const handleShare = (property: PropertyAlert) => {
    if ('vibrate' in navigator) {
      navigator.vibrate(50);
    }

    if (navigator.share) {
      navigator.share({
        title: `Property Match for ${property.leadName}`,
        text: `Check out this ${property.type} at ${property.address} - $${property.price.toLocaleString()}`,
        url: window.location.href,
      });
    } else {
      // Fallback - copy to clipboard
      const text = `Property Match: ${property.address} - $${property.price.toLocaleString()} - ${property.matchScore}% match for ${property.leadName}`;
      navigator.clipboard.writeText(text);
    }
  };

  const handleView = (property: PropertyAlert) => {
    if ('vibrate' in navigator) {
      navigator.vibrate(50);
    }
    // Navigate to property details or open property viewer
    console.log('Viewing property:', property.id);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BellIcon className="w-5 h-5 text-jorge-electric" />
          <h2 className="jorge-heading text-lg">Property Alerts</h2>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 bg-jorge-electric rounded-full jorge-glow-pulse" />
          <span className="text-xs jorge-code text-jorge-electric">
            {propertyAlerts.length} NEW
          </span>
        </div>
      </div>

      <div className="space-y-3">
        {propertyAlerts.map((alert, index) => {
          const alertConfig = getAlertTypeConfig(alert.alertType);
          const AlertIcon = alertConfig.icon;

          return (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`
                jorge-card jorge-card-hover
                ${selectedAlert === alert.id ? 'border-jorge-electric ring-1 ring-jorge-electric/30' : ''}
                cursor-pointer relative overflow-hidden
              `}
              onClick={() => setSelectedAlert(selectedAlert === alert.id ? null : alert.id)}
            >
              {/* Alert type badge */}
              <div className={`
                absolute top-3 right-3 flex items-center gap-1 px-2 py-1 rounded-lg
                ${alertConfig.bgColor}
              `}>
                <AlertIcon className={`w-3 h-3 text-${alertConfig.color}`} />
                <span className={`text-xs jorge-code text-${alertConfig.color} font-semibold`}>
                  {alertConfig.label}
                </span>
              </div>

              {/* Property header */}
              <div className="pr-20 mb-3">
                <h3 className="jorge-code text-sm font-medium text-white mb-1">
                  {alert.address}
                </h3>
                <div className="flex items-center gap-2">
                  <span className="property-value text-lg">
                    ${(alert.price / 1000).toFixed(0)}K
                  </span>
                  <span className="text-xs text-gray-400">•</span>
                  <span className="text-xs text-gray-400">{alert.type}</span>
                </div>
              </div>

              {/* Property stats */}
              <div className="grid grid-cols-4 gap-2 mb-3">
                <div className="text-center">
                  <div className="text-sm text-white font-semibold">{alert.bedrooms}</div>
                  <div className="text-xs text-gray-400">Beds</div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-white font-semibold">{alert.bathrooms}</div>
                  <div className="text-xs text-gray-400">Baths</div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-white font-semibold">
                    {(alert.sqft / 1000).toFixed(1)}K
                  </div>
                  <div className="text-xs text-gray-400">SqFt</div>
                </div>
                <div className="text-center">
                  <div className={`text-sm font-semibold ${getScoreColor(alert.matchScore)}`}>
                    {alert.matchScore}%
                  </div>
                  <div className="text-xs text-gray-400">Match</div>
                </div>
              </div>

              {/* Lead match info */}
              <div className="flex items-center justify-between mb-3 p-2 bg-white/5 rounded-lg">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 bg-jorge-gradient rounded-full flex items-center justify-center">
                    <span className="text-white text-xs font-semibold">
                      {alert.leadName.split(' ').map(n => n[0]).join('')}
                    </span>
                  </div>
                  <div>
                    <span className="text-xs font-medium text-white">{alert.leadName}</span>
                    <div className="text-xs text-gray-400">{alert.timestamp}</div>
                  </div>
                </div>
                <div className="text-xs jorge-code text-jorge-glow">
                  {alert.daysOnMarket} DAYS ON MARKET
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex gap-2">
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleView(alert);
                  }}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-jorge-electric/20 text-jorge-electric rounded-lg jorge-haptic"
                >
                  <EyeIcon className="w-4 h-4" />
                  <span className="text-xs font-semibold">VIEW</span>
                </motion.button>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleShare(alert);
                  }}
                  className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-jorge-glow/20 text-jorge-glow rounded-lg jorge-haptic"
                >
                  <ShareIcon className="w-4 h-4" />
                  <span className="text-xs font-semibold">SHARE</span>
                </motion.button>
              </div>

              {/* Expanded details */}
              {selectedAlert === alert.id && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-3 pt-3 border-t border-white/10 space-y-2"
                >
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <span className="text-xs text-gray-400">Days on Market</span>
                      <div className="text-sm text-white font-semibold">
                        {alert.daysOnMarket} days
                      </div>
                    </div>
                    <div>
                      <span className="text-xs text-gray-400">Price per SqFt</span>
                      <div className="text-sm text-white font-semibold">
                        ${Math.round(alert.price / alert.sqft)}
                      </div>
                    </div>
                  </div>

                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    className="w-full mt-3 px-3 py-2 bg-jorge-gold/20 text-jorge-gold text-xs font-semibold rounded-lg jorge-haptic"
                  >
                    SCHEDULE SHOWING
                  </motion.button>
                </motion.div>
              )}

              {/* Match score indicator */}
              <motion.div
                animate={{
                  scale: alert.matchScore >= 90 ? [1, 1.1, 1] : 1,
                  opacity: alert.matchScore >= 90 ? [0.7, 1, 0.7] : 1
                }}
                transition={{
                  duration: 2,
                  repeat: alert.matchScore >= 90 ? Infinity : 0,
                  ease: "easeInOut"
                }}
                className={`
                  absolute bottom-2 right-2 w-2 h-2 rounded-full
                  ${alert.matchScore >= 90 ? 'bg-jorge-gold' :
                    alert.matchScore >= 75 ? 'bg-jorge-glow' : 'bg-jorge-electric'}
                `}
              />
            </motion.div>
          );
        })}
      </div>

      {/* Summary */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="jorge-card text-center space-y-2"
      >
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="property-value text-lg">
              {propertyAlerts.length}
            </div>
            <div className="text-xs text-gray-400">New Alerts</div>
          </div>
          <div>
            <div className="property-value text-lg">
              {Math.round(propertyAlerts.reduce((sum, alert) => sum + alert.matchScore, 0) / propertyAlerts.length)}%
            </div>
            <div className="text-xs text-gray-400">Avg Match</div>
          </div>
          <div>
            <div className="property-value text-lg">
              ${(propertyAlerts.reduce((sum, alert) => sum + alert.price, 0) / 1000000).toFixed(1)}M
            </div>
            <div className="text-xs text-gray-400">Total Value</div>
          </div>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          AI-powered property matching • Real-time alerts • Smart notifications
        </p>
      </motion.div>
    </div>
  );
}