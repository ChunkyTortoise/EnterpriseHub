'use client'

import { RealtimeProvider } from '@/lib/providers/RealtimeProvider'

interface ProvidersProps {
  children: React.ReactNode
}

export function Providers({ children }: ProvidersProps) {
  return (
    <RealtimeProvider
      autoConnect={true}
      maxReconnectAttempts={10}
      reconnectInterval={5000}
      maxEvents={1000}
    >
      {children}
    </RealtimeProvider>
  )
}