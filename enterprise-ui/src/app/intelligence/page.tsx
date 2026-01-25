'use client'

import { PropertyIntelligenceDashboard } from '@/components/property-intelligence/PropertyIntelligenceDashboard'

export default function IntelligencePage() {
  return (
    <div className="min-h-screen bg-[#0f0f0f] p-6">
      <PropertyIntelligenceDashboard propertyId="demo-property" />
    </div>
  )
}