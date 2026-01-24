// Jorge Real Estate AI Platform Main Page
// Professional interface for Jorge's bot ecosystem

import { JorgeCommandCenter } from '@/components/JorgeCommandCenter'

export default function JorgePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        <JorgeCommandCenter />
      </div>
    </div>
  )
}

export const metadata = {
  title: 'Jorge Command Center | Real Estate AI Platform',
  description: 'Professional dashboard for managing Jorge\'s enterprise-grade real estate bot ecosystem',
}