'use client';

export const dynamic = 'force-dynamic';

import { useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  ArrowLeftIcon,
  MapIcon,
} from "@heroicons/react/24/outline";

import { GeofenceManager } from "@/components/mobile/location/GeofenceManager";
import { MobileNavigation } from "@/components/mobile/MobileNavigation";

export default function GeofenceManagerPage() {
  const router = useRouter();

  const handleCreateGeofence = () => {
    // Navigate to map with create mode
    router.push('/field-agent/location/map?mode=create_geofence');
  };

  const handleEditGeofence = (geofenceId: string) => {
    // Navigate to edit geofence (could be a modal or separate page)
    router.push(`/field-agent/location/geofences/edit/${geofenceId}`);
  };

  return (
    <div className="min-h-screen bg-jorge-gradient-dark text-white">
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
            <h1 className="jorge-display text-lg">GEOFENCE MANAGER</h1>
            <p className="text-xs text-gray-400">Property Alert Zones</p>
          </div>
        </div>

        <div className="flex items-center gap-1 text-xs jorge-code text-jorge-electric">
          <MapIcon className="w-4 h-4" />
          <span>ACTIVE</span>
        </div>
      </motion.header>

      {/* Content */}
      <div className="container mx-auto px-4 py-6 pb-24">
        <GeofenceManager
          onCreateGeofence={handleCreateGeofence}
          onEditGeofence={handleEditGeofence}
        />
      </div>

      <MobileNavigation />
    </div>
  );
}