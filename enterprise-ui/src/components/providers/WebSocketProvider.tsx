/**
 * WebSocket Provider - Real-time Connection Management
 *
 * Provides WebSocket context and connection management for Jorge's Real Estate Platform
 * Handles connection state, reconnection, and global event distribution
 */

'use client'

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { socketManager } from '@/lib/socket'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Wifi, WifiOff, Loader2, AlertTriangle } from 'lucide-react'

interface WebSocketContextType {
  connected: boolean
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'error'
  reconnect: () => Promise<void>
  disconnect: () => void
  lastActivity: string | null
}

const WebSocketContext = createContext<WebSocketContextType | null>(null)

export const useWebSocket = () => {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider')
  }
  return context
}

interface WebSocketProviderProps {
  children: ReactNode
  autoConnect?: boolean
  showConnectionStatus?: boolean
  fallbackToPolling?: boolean
}

export default function WebSocketProvider({
  children,
  autoConnect = true,
  showConnectionStatus = true,
  fallbackToPolling = true
}: WebSocketProviderProps) {
  const [connected, setConnected] = useState(false)
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected')
  const [lastActivity, setLastActivity] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  const [showError, setShowError] = useState(false)

  const maxReconnectAttempts = 5

  // Monitor connection state
  useEffect(() => {
    const interval = setInterval(() => {
      const isConnected = socketManager.connected
      const state = socketManager.connectionState

      setConnected(isConnected)
      setConnectionState(state)

      if (isConnected) {
        setError(null)
        setShowError(false)
        setReconnectAttempts(0)
        setLastActivity(new Date().toISOString())
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect && connectionState === 'disconnected') {
      connect()
    }
  }, [autoConnect])

  const connect = async () => {
    try {
      setError(null)
      setConnectionState('connecting')
      await socketManager.connect()
      setConnected(true)
      setConnectionState('connected')
      setLastActivity(new Date().toISOString())
    } catch (err: any) {
      setError(err.message)
      setConnectionState('error')
      setConnected(false)
      setShowError(true)

      // Auto-reconnect with exponential backoff
      if (reconnectAttempts < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
        setTimeout(() => {
          setReconnectAttempts(prev => prev + 1)
          connect()
        }, delay)
      }
    }
  }

  const disconnect = () => {
    socketManager.disconnect()
    setConnected(false)
    setConnectionState('disconnected')
    setLastActivity(null)
    setError(null)
    setShowError(false)
    setReconnectAttempts(0)
  }

  const reconnect = async () => {
    disconnect()
    await new Promise(resolve => setTimeout(resolve, 500)) // Brief pause
    await connect()
  }

  const contextValue: WebSocketContextType = {
    connected,
    connectionState,
    reconnect,
    disconnect,
    lastActivity
  }

  const getConnectionBadge = () => {
    switch (connectionState) {
      case 'connected':
        return (
          <Badge variant="secondary" className="bg-green-100 text-green-800">
            <Wifi className="w-3 h-3 mr-1" />
            Real-time Connected
          </Badge>
        )
      case 'connecting':
        return (
          <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
            Connecting...
          </Badge>
        )
      case 'error':
        return (
          <Badge variant="destructive">
            <AlertTriangle className="w-3 h-3 mr-1" />
            Connection Error
          </Badge>
        )
      default:
        return (
          <Badge variant="outline">
            <WifiOff className="w-3 h-3 mr-1" />
            Offline
          </Badge>
        )
    }
  }

  return (
    <WebSocketContext.Provider value={contextValue}>
      {showConnectionStatus && (
        <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
          {getConnectionBadge()}

          {showError && error && (
            <Alert className="w-80 bg-red-50 border-red-200">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-sm text-red-800">
                <div className="mb-2">WebSocket connection failed: {error}</div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={reconnect}
                    disabled={connectionState === 'connecting'}
                  >
                    {connectionState === 'connecting' ? (
                      <>
                        <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                        Reconnecting...
                      </>
                    ) : (
                      'Retry Connection'
                    )}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setShowError(false)}
                  >
                    Dismiss
                  </Button>
                </div>
                {reconnectAttempts > 0 && (
                  <div className="text-xs text-red-600 mt-1">
                    Attempt {reconnectAttempts}/{maxReconnectAttempts}
                    {reconnectAttempts >= maxReconnectAttempts && fallbackToPolling && (
                      <span className="block mt-1">
                        Falling back to polling mode for updates
                      </span>
                    )}
                  </div>
                )}
              </AlertDescription>
            </Alert>
          )}

          {connectionState === 'connected' && lastActivity && (
            <div className="text-xs text-gray-500 text-right">
              Last update: {new Date(lastActivity).toLocaleTimeString()}
            </div>
          )}
        </div>
      )}

      {/* Connection status for development */}
      {process.env.NODE_ENV === 'development' && (
        <div className="fixed bottom-4 left-4 z-50 text-xs text-gray-500 bg-white p-2 rounded shadow">
          <div>WebSocket: {connectionState}</div>
          <div>Reconnects: {reconnectAttempts}</div>
          {lastActivity && (
            <div>Last Activity: {new Date(lastActivity).toLocaleTimeString()}</div>
          )}
        </div>
      )}

      {children}
    </WebSocketContext.Provider>
  )
}