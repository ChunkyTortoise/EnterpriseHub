// Jorge Real Estate AI Platform Main Page
// Professional interface for Jorge's bot ecosystem

import { JorgeCommandCenter } from '@/components/JorgeCommandCenter'
import { BackgroundBeams } from '@/components/effects/BackgroundBeams'

export default function JorgePage() {
  return (
    <div className="min-h-screen bg-jorge-dark relative overflow-hidden">
      {/* Elite Background Effects */}
      <BackgroundBeams className="opacity-50" />
      
      {/* Dashboard Content */}
      <div className="container mx-auto px-4 py-8 max-w-7xl relative z-10">
        <JorgeCommandCenter />
      </div>
    </div>
  )
}

export const metadata = {
  title: 'Jorge Command Center | Real Estate AI Platform',
  description: 'Professional dashboard for managing Jorge\'s enterprise-grade real estate bot ecosystem',
}

