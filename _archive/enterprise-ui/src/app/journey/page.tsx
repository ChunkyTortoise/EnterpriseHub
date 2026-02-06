'use client'

import { CustomerJourneyOrchestrator } from '@/components/journey-orchestrator/CustomerJourneyOrchestrator'

export default function JourneyPage() {
  return (
    <div className="min-h-screen bg-[#0f0f0f] p-6">
      <CustomerJourneyOrchestrator />
    </div>
  )
}