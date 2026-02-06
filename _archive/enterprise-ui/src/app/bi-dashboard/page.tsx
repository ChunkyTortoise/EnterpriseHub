'use client';

import { BusinessIntelligenceDashboard } from '@/components/BusinessIntelligenceDashboard';

export default function BusinessIntelligencePage() {
  return (
    <div className="min-h-screen bg-[#0f0f0f] p-6">
      <div className="max-w-[1600px] mx-auto">
        <BusinessIntelligenceDashboard
          locationId="jorge-platform"
          autoRefresh={true}
          showRealTimeAlerts={true}
        />
      </div>
    </div>
  );
}