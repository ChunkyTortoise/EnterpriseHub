'use client';

import { useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { LocationDashboard } from "@/components/mobile/location/LocationDashboard";
import { MobileNavigation } from "@/components/mobile/MobileNavigation";

export default function LocationServicesPage() {
  const router = useRouter();

  const handleNavigateToMap = () => {
    router.push('/field-agent/location/map');
  };

  const handleNavigateToGeofences = () => {
    router.push('/field-agent/location/geofences');
  };

  const handleNavigateToSettings = () => {
    router.push('/field-agent/location/settings');
  };

  return (
    <div className="min-h-screen bg-jorge-gradient-dark text-white">
      <div className="container mx-auto px-4 py-6 pb-24">
        <LocationDashboard
          onNavigateToMap={handleNavigateToMap}
          onNavigateToGeofences={handleNavigateToGeofences}
          onNavigateToSettings={handleNavigateToSettings}
        />
      </div>

      <MobileNavigation />
    </div>
  );
}