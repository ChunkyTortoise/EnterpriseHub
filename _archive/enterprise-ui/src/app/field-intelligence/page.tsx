'use client';

import { FieldAgentIntelligenceDashboard } from '@/components/mobile/FieldAgentIntelligenceDashboard';

export default function FieldIntelligencePage() {
  return (
    <div className="min-h-screen bg-[#0f0f0f] p-2 md:p-6">
      <div className="max-w-[400px] md:max-w-[1200px] mx-auto">
        <FieldAgentIntelligenceDashboard
          agentId="jorge-field-agent"
          location={{ lat: 30.2672, lng: -97.7431 }} // Austin, TX
          maxRadius={25}
        />
      </div>
    </div>
  );
}