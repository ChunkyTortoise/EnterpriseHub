'use client';

import { useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  ArrowLeftIcon,
  MapPinIcon,
  Bars3Icon,
} from "@heroicons/react/24/outline";

import { PropertyMap } from "@/components/mobile/location/PropertyMap";
import { NearbyPropertiesWidget } from "@/components/mobile/location/NearbyPropertiesWidget";
import { MarketInsightCard } from "@/components/mobile/location/MarketInsightCard";

export default function PropertyMapPage() {
  const router = useRouter();
  const [showSidebar, setShowSidebar] = useState(false);
  const [selectedProperty, setSelectedProperty] = useState<string | null>(null);

  const handlePropertySelect = (propertyId: string) => {
    setSelectedProperty(propertyId);
    console.log('Selected property:', propertyId);
  };

  const handleNavigateToProperty = (propertyId: string) => {
    console.log('Navigate to property:', propertyId);
  };

  const handleCreateAlert = (propertyId: string) => {
    console.log('Create alert for property:', propertyId);
    // Show success feedback
    if ('vibrate' in navigator) {
      navigator.vibrate([100, 50, 100]);
    }
  };

  return (
    <div className="min-h-screen bg-jorge-dark text-white flex flex-col">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between p-4 bg-jorge-dark/95 backdrop-blur border-b border-white/10"
      >
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-2 bg-white/10 rounded-lg jorge-haptic"
          >
            <ArrowLeftIcon className="w-5 h-5" />
          </button>
          <div>
            <h1 className="jorge-display text-lg">PROPERTY MAP</h1>
            <p className="text-xs text-gray-400">GPS-Enabled Property Intelligence</p>
          </div>
        </div>

        <button
          onClick={() => setShowSidebar(!showSidebar)}
          className={`p-2 rounded-lg jorge-haptic ${
            showSidebar ? 'bg-jorge-electric/20 text-jorge-electric' : 'bg-white/10 text-gray-400'
          }`}
        >
          <Bars3Icon className="w-5 h-5" />
        </button>
      </motion.header>

      {/* Main Content */}
      <div className="flex-1 flex relative">
        {/* Map */}
        <div className="flex-1">
          <PropertyMap
            showControls={true}
            onPropertySelect={handlePropertySelect}
            onLocationChange={(location) => console.log('Location changed:', location)}
          />
        </div>

        {/* Sidebar */}
        {showSidebar && (
          <motion.div
            initial={{ x: '100%', opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: '100%', opacity: 0 }}
            className="absolute right-0 top-0 bottom-0 w-80 bg-jorge-dark/95 backdrop-blur border-l border-white/10 overflow-y-auto z-30"
          >
            <div className="p-4 space-y-6">
              {/* Nearby Properties */}
              <div>
                <h2 className="jorge-heading text-lg mb-4 flex items-center gap-2">
                  <MapPinIcon className="w-5 h-5 text-jorge-electric" />
                  Nearby Properties
                </h2>
                <NearbyPropertiesWidget
                  maxProperties={8}
                  showFilters={true}
                  onPropertySelect={handlePropertySelect}
                  onNavigateToProperty={handleNavigateToProperty}
                  onCreateAlert={handleCreateAlert}
                />
              </div>

              {/* Market Insights */}
              <div>
                <MarketInsightCard
                  showDetailed={false}
                  onViewFullReport={() => {
                    router.push('/field-agent/location/market-report');
                  }}
                  onNeighborhoodClick={(neighborhood) => {
                    console.log('Clicked neighborhood:', neighborhood);
                  }}
                />
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Mobile Bottom Sheet for Properties (when sidebar is closed) */}
      {!showSidebar && selectedProperty && (
        <motion.div
          initial={{ y: '100%' }}
          animate={{ y: 0 }}
          className="absolute bottom-0 left-0 right-0 bg-jorge-dark/95 backdrop-blur border-t border-white/10 max-h-96 overflow-y-auto z-20"
        >
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="jorge-heading text-base">Property Details</h3>
              <button
                onClick={() => setSelectedProperty(null)}
                className="text-gray-400 hover:text-white"
              >
                ×
              </button>
            </div>

            <div className="text-sm text-gray-300">
              Property ID: {selectedProperty}
            </div>

            {/* This would show detailed property information */}
            <div className="mt-4 space-y-3">
              <div className="jorge-card">
                <p className="text-sm text-gray-300">
                  Detailed property information would be displayed here, including photos,
                  pricing, features, and available actions.
                </p>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <button className="py-2 bg-jorge-electric/20 text-jorge-electric text-xs font-semibold rounded jorge-haptic">
                  Navigate
                </button>
                <button className="py-2 bg-jorge-glow/20 text-jorge-glow text-xs font-semibold rounded jorge-haptic">
                  Call Lead
                </button>
                <button className="py-2 bg-jorge-gold/20 text-jorge-gold text-xs font-semibold rounded jorge-haptic">
                  Create Alert
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Overlay to close sidebar on mobile */}
      {showSidebar && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={() => setShowSidebar(false)}
        />
      )}
    </div>
  );
}