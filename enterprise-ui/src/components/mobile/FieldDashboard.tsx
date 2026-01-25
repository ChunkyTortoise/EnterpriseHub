// Jorge's Real Estate AI Platform - Field Operations Dashboard
// Mobile-first interface for real estate field work

'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { Camera, Mic, Users, MapPin, Calendar, Zap, Phone, MessageSquare } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'
import { useVoiceRecognition } from '@/hooks/useVoiceRecognition'
import { useNetwork } from '@/hooks/useNetwork'
import { useOfflineData } from '@/hooks/useOfflineData'
import { TouchFriendlyGrid } from './TouchFriendlyGrid'
import { SwipeablePropertyList } from './SwipeablePropertyList'
import { FloatingVoiceButton } from './FloatingVoiceButton'
import { QuickActions } from './QuickActions'
import { TodaySchedule } from './TodaySchedule'
import { HotLeadsAlert } from './HotLeadsAlert'
import { ConnectionStatus } from './ConnectionStatus'

interface FieldDashboardProps {
  className?: string
  leadId?: string
  propertyId?: string
  fromNotification?: string
}

interface DashboardState {
  activeSection: 'home' | 'schedule' | 'leads' | 'properties' | 'voice'
  todayStats: {
    appointments: number
    hotLeads: number
    propertiesViewed: number
    conversions: number
  }
  currentLocation?: {
    lat: number
    lng: number
    address?: string
  }
  nearbyProperties: Property[]
  urgentTasks: Task[]
}

interface Property {
  id: string
  address: string
  price: number
  bedrooms: number
  bathrooms: number
  sqft: number
  listingDate: string
  temperature: number
  distance?: number
  images: string[]
  mlScore?: number
}

interface Task {
  id: string
  type: 'follow_up' | 'showing' | 'call' | 'analysis'
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  dueTime?: string
  leadName?: string
  propertyAddress?: string
}

export function FieldDashboard({ className, leadId, propertyId, fromNotification }: FieldDashboardProps) {
  const [state, setState] = useState<DashboardState>({
    activeSection: 'home',
    todayStats: {
      appointments: 0,
      hotLeads: 0,
      propertiesViewed: 0,
      conversions: 0
    },
    nearbyProperties: [],
    urgentTasks: []
  })

  const [showVoiceInterface, setShowVoiceInterface] = useState(false)
  const [quickActionMode, setQuickActionMode] = useState(false)

  const { isOnline, connectionQuality, canHandlePropertyPhotos } = useNetwork()
  const { isListening, transcript, startListening, stopListening, isSupported } = useVoiceRecognition()
  const { storeData, getAllData, syncQueuedActions } = useOfflineData({
    storeName: 'field-operations',
    autoSync: true
  })

  // Initialize dashboard data
  useEffect(() => {
    loadDashboardData()
    getCurrentLocation()

    // Handle notification-based navigation
    if (fromNotification) {
      handleNotificationNavigation(fromNotification, leadId, propertyId)
    }
  }, [fromNotification, leadId, propertyId])

  // Voice command handling
  useEffect(() => {
    const handleVoiceCommand = (event: CustomEvent) => {
      const { command, transcript } = event.detail
      processVoiceCommand(command, transcript)
    }

    window.addEventListener('jorgeVoiceCommand', handleVoiceCommand as EventListener)
    return () => window.removeEventListener('jorgeVoiceCommand', handleVoiceCommand as EventListener)
  }, [])

  const loadDashboardData = useCallback(async () => {
    try {
      // Load today's stats
      const statsResponse = await fetch('/api/backend/analytics/today-stats')
      if (statsResponse.ok) {
        const stats = await statsResponse.json()
        setState(prev => ({ ...prev, todayStats: stats }))
      }

      // Load urgent tasks
      const tasksResponse = await fetch('/api/backend/tasks/urgent')
      if (tasksResponse.ok) {
        const tasks = await tasksResponse.json()
        setState(prev => ({ ...prev, urgentTasks: tasks }))
      }

      // Try to sync offline data if online
      if (isOnline) {
        await syncQueuedActions()
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error)

      // Load from offline cache
      const offlineData = await getAllData()
      if (offlineData.success && offlineData.data.length > 0) {
        console.log('Loading data from offline cache')
        // Process offline data...
      }
    }
  }, [isOnline, syncQueuedActions, getAllData])

  const getCurrentLocation = useCallback(() => {
    if (!navigator.geolocation) return

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude: lat, longitude: lng } = position.coords

        setState(prev => ({
          ...prev,
          currentLocation: { lat, lng }
        }))

        // Load nearby properties
        try {
          const response = await fetch(`/api/backend/properties/nearby?lat=${lat}&lng=${lng}&radius=5`)
          if (response.ok) {
            const properties = await response.json()
            setState(prev => ({ ...prev, nearbyProperties: properties }))
          }
        } catch (error) {
          console.error('Failed to load nearby properties:', error)
        }
      },
      (error) => {
        console.warn('Location access denied:', error)
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 5 * 60 * 1000 // 5 minutes
      }
    )
  }, [])

  const processVoiceCommand = useCallback((command: string, transcript: string) => {
    console.log('Processing voice command:', command, transcript)

    switch (command) {
      case 'ANALYZE_PROPERTY':
        setActiveSection('properties')
        // Trigger camera for property analysis
        break

      case 'FIND_COMPARABLES':
        if (propertyId) {
          // Navigate to property comps
        }
        break

      case 'CAPTURE_LEAD':
        setActiveSection('leads')
        // Open lead capture form
        break

      case 'JORGE_BOT':
        setShowVoiceInterface(true)
        // Start Jorge Seller Bot conversation
        break

      case 'HOT_LEADS':
        setActiveSection('leads')
        // Filter to hot leads only
        break

      case 'TODAY_SCHEDULE':
        setActiveSection('schedule')
        break

      default:
        console.log('Unknown voice command:', command)
    }
  }, [propertyId])

  const handleNotificationNavigation = useCallback((notificationType: string, leadId?: string, propertyId?: string) => {
    switch (notificationType) {
      case 'hot_lead':
        if (leadId) {
          setState(prev => ({ ...prev, activeSection: 'leads' }))
          // Navigate to specific lead
        }
        break

      case 'property_match':
        if (propertyId) {
          setState(prev => ({ ...prev, activeSection: 'properties' }))
          // Navigate to specific property
        }
        break

      case 'bot_escalation':
        setShowVoiceInterface(true)
        break
    }
  }, [])

  const setActiveSection = useCallback((section: DashboardState['activeSection']) => {
    setState(prev => ({ ...prev, activeSection: section }))
  }, [])

  const quickActions = [
    {
      icon: <Camera className="w-6 h-6" />,
      label: 'Property Scan',
      action: 'scan',
      description: 'Photo analysis',
      enabled: canHandlePropertyPhotos
    },
    {
      icon: <Mic className="w-6 h-6" />,
      label: 'Voice Note',
      action: 'voice',
      description: 'Quick recording',
      enabled: isSupported
    },
    {
      icon: <Users className="w-6 h-6" />,
      label: 'New Lead',
      action: 'lead',
      description: 'Capture prospect',
      enabled: true
    },
    {
      icon: <MessageSquare className="w-6 h-6" />,
      label: 'Jorge Bot',
      action: 'bot',
      description: 'AI consultation',
      enabled: true
    }
  ]

  return (
    <div className={cn('min-h-screen bg-gray-950 text-white overflow-hidden', className)}>
      {/* Connection Status Bar */}
      <ConnectionStatus
        isOnline={isOnline}
        quality={connectionQuality.quality}
        className="fixed top-0 left-0 right-0 z-50"
      />

      {/* Main Content */}
      <div className="pt-8 pb-20 px-4">
        {/* Header with Stats */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <div className="text-center mb-4">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
              Jorge Field Agent
            </h1>
            <p className="text-gray-400 text-sm">
              {state.currentLocation ? '📍 Location Active' : '📍 Location Unavailable'}
            </p>
          </div>

          {/* Today's Stats Grid */}
          <div className="grid grid-cols-4 gap-2 bg-gray-900/50 rounded-xl p-4 backdrop-blur-sm border border-gray-800">
            <div className="text-center">
              <div className="text-xl font-bold text-blue-400">{state.todayStats.appointments}</div>
              <div className="text-xs text-gray-400">Meetings</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-orange-400">{state.todayStats.hotLeads}</div>
              <div className="text-xs text-gray-400">Hot Leads</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-green-400">{state.todayStats.propertiesViewed}</div>
              <div className="text-xs text-gray-400">Properties</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-purple-400">{state.todayStats.conversions}</div>
              <div className="text-xs text-gray-400">Closed</div>
            </div>
          </div>
        </motion.div>

        {/* Hot Leads Alert */}
        {state.todayStats.hotLeads > 0 && (
          <HotLeadsAlert
            count={state.todayStats.hotLeads}
            onViewLeads={() => setActiveSection('leads')}
            className="mb-6"
          />
        )}

        {/* Quick Actions Grid */}
        <TouchFriendlyGrid className="mb-6">
          {quickActions.map((action, index) => (
            <motion.button
              key={action.action}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              disabled={!action.enabled}
              className={cn(
                'group relative overflow-hidden rounded-xl p-4 h-24',
                'bg-gradient-to-br from-gray-800/80 to-gray-900/80',
                'border border-gray-700 backdrop-blur-sm',
                'active:scale-95 transition-all duration-200',
                action.enabled
                  ? 'hover:border-blue-500/50 hover:shadow-lg hover:shadow-blue-500/25'
                  : 'opacity-50 cursor-not-allowed'
              )}
              onClick={() => action.enabled && processVoiceCommand(action.action.toUpperCase(), '')}
            >
              <div className="flex flex-col items-center justify-center h-full space-y-1">
                <div className={cn(
                  'p-2 rounded-lg transition-colors',
                  action.enabled ? 'text-blue-400 group-active:text-blue-300' : 'text-gray-500'
                )}>
                  {action.icon}
                </div>
                <div className="text-center">
                  <div className="text-sm font-medium">{action.label}</div>
                  <div className="text-xs text-gray-400">{action.description}</div>
                </div>
              </div>

              {/* Ripple effect */}
              {action.enabled && (
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 via-blue-500/10 to-blue-500/0 opacity-0 group-active:opacity-100 transition-opacity" />
              )}
            </motion.button>
          ))}
        </TouchFriendlyGrid>

        {/* Section Content */}
        <AnimatePresence mode="wait">
          {state.activeSection === 'schedule' && (
            <motion.div
              key="schedule"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <TodaySchedule className="mb-6" />
            </motion.div>
          )}

          {state.activeSection === 'properties' && (
            <motion.div
              key="properties"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <SwipeablePropertyList
                properties={state.nearbyProperties}
                currentLocation={state.currentLocation}
                className="mb-6"
              />
            </motion.div>
          )}

          {state.activeSection === 'leads' && (
            <motion.div
              key="leads"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-4"
            >
              <h3 className="text-lg font-semibold">Today's Priority Leads</h3>
              {/* Lead cards would go here */}
              <div className="text-center text-gray-400 py-8">
                Lead management interface coming soon
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Urgent Tasks */}
        {state.urgentTasks.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-500/10 border border-red-500/30 rounded-xl p-4"
          >
            <div className="flex items-center gap-2 mb-3">
              <Zap className="w-5 h-5 text-red-400" />
              <h3 className="font-semibold text-red-400">Urgent Tasks</h3>
            </div>
            <div className="space-y-2">
              {state.urgentTasks.slice(0, 3).map((task) => (
                <div key={task.id} className="flex justify-between items-center">
                  <div>
                    <div className="text-sm font-medium">{task.title}</div>
                    <div className="text-xs text-gray-400">{task.dueTime}</div>
                  </div>
                  <button className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded">
                    Act
                  </button>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-gray-900/95 backdrop-blur-sm border-t border-gray-800 px-4 py-2">
        <div className="flex justify-around items-center max-w-sm mx-auto">
          {[
            { key: 'home', icon: <MapPin />, label: 'Field' },
            { key: 'schedule', icon: <Calendar />, label: 'Schedule' },
            { key: 'properties', icon: <Camera />, label: 'Properties' },
            { key: 'leads', icon: <Users />, label: 'Leads' }
          ].map((item) => (
            <button
              key={item.key}
              onClick={() => setActiveSection(item.key as any)}
              className={cn(
                'flex flex-col items-center space-y-1 p-2 rounded-lg transition-colors',
                state.activeSection === item.key
                  ? 'text-blue-400 bg-blue-500/20'
                  : 'text-gray-400 hover:text-gray-300'
              )}
            >
              <div className="w-5 h-5">{item.icon}</div>
              <span className="text-xs">{item.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Floating Voice Button */}
      <FloatingVoiceButton
        isListening={isListening}
        onToggle={isListening ? stopListening : startListening}
        transcript={transcript}
        className="fixed bottom-20 right-4"
      />

      {/* Voice Interface Overlay */}
      <AnimatePresence>
        {showVoiceInterface && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center"
            onClick={() => setShowVoiceInterface(false)}
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              className="bg-gray-900 rounded-2xl p-6 m-4 max-w-sm w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <h3 className="text-lg font-semibold text-center mb-4">Jorge Voice Assistant</h3>
              <div className="text-center text-gray-400 mb-6">
                {isListening ? 'Listening...' : 'Tap to speak with Jorge AI'}
              </div>
              <div className="flex justify-center gap-4">
                <button
                  onClick={isListening ? stopListening : startListening}
                  className={cn(
                    'w-16 h-16 rounded-full flex items-center justify-center',
                    isListening
                      ? 'bg-red-500 text-white'
                      : 'bg-blue-500 text-white'
                  )}
                >
                  <Mic className="w-8 h-8" />
                </button>
              </div>
              {transcript && (
                <div className="mt-4 p-3 bg-gray-800 rounded-lg text-sm">
                  {transcript}
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}