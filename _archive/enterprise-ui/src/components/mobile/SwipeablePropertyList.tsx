// Jorge's Real Estate AI Platform - Swipeable Property List
// Touch-optimized property browsing with swipe gestures

'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import { motion, PanInfo, AnimatePresence } from 'framer-motion'
import { MapPin, Bed, Bath, Square, Calendar, TrendingUp, Heart, Share, Camera } from 'lucide-react'
import { cn } from '@/lib/utils'

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
  description?: string
  listingAgent?: {
    name: string
    phone: string
  }
  marketInsights?: {
    pricePerSqft: number
    daysOnMarket: number
    priceHistory: Array<{ date: string; price: number }>
  }
}

interface SwipeablePropertyListProps {
  properties: Property[]
  currentLocation?: {
    lat: number
    lng: number
  }
  className?: string
  onPropertySelect?: (property: Property) => void
  onPropertyLike?: (propertyId: string) => void
  onPropertyShare?: (property: Property) => void
  onAnalyzeProperty?: (property: Property) => void
}

interface SwipeState {
  currentIndex: number
  direction: 'left' | 'right' | null
  isDragging: boolean
  dragOffset: number
}

export function SwipeablePropertyList({
  properties,
  currentLocation,
  className,
  onPropertySelect,
  onPropertyLike,
  onPropertyShare,
  onAnalyzeProperty
}: SwipeablePropertyListProps) {
  const [state, setState] = useState<SwipeState>({
    currentIndex: 0,
    direction: null,
    isDragging: false,
    dragOffset: 0
  })

  const [likedProperties, setLikedProperties] = useState<Set<string>>(new Set())
  const containerRef = useRef<HTMLDivElement>(null)

  const swipeThreshold = 100 // Minimum distance for a swipe
  const swipeVelocityThreshold = 500 // Minimum velocity for a quick swipe

  const currentProperty = properties[state.currentIndex]
  const hasNext = state.currentIndex < properties.length - 1
  const hasPrevious = state.currentIndex > 0

  // Haptic feedback
  const triggerHaptic = useCallback((intensity: 'light' | 'medium' | 'heavy' = 'light') => {
    if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
      switch (intensity) {
        case 'light':
          navigator.vibrate(10)
          break
        case 'medium':
          navigator.vibrate(25)
          break
        case 'heavy':
          navigator.vibrate(50)
          break
      }
    }
  }, [])

  // Handle swipe gestures
  const handleDragEnd = useCallback((event: any, info: PanInfo) => {
    const { offset, velocity } = info
    const swipeDistance = Math.abs(offset.x)
    const swipeVelocity = Math.abs(velocity.x)

    setState(prev => ({ ...prev, isDragging: false, dragOffset: 0 }))

    // Determine if this is a valid swipe
    if (swipeDistance > swipeThreshold || swipeVelocity > swipeVelocityThreshold) {
      const direction = offset.x > 0 ? 'right' : 'left'

      if (direction === 'right' && hasPrevious) {
        // Swipe right - previous property
        setState(prev => ({
          ...prev,
          currentIndex: prev.currentIndex - 1,
          direction: 'right'
        }))
        triggerHaptic('medium')
      } else if (direction === 'left' && hasNext) {
        // Swipe left - next property
        setState(prev => ({
          ...prev,
          currentIndex: prev.currentIndex + 1,
          direction: 'left'
        }))
        triggerHaptic('medium')
      } else {
        // Invalid swipe - provide feedback
        triggerHaptic('light')
      }
    }
  }, [hasNext, hasPrevious, swipeThreshold, swipeVelocityThreshold, triggerHaptic])

  const handleDrag = useCallback((event: any, info: PanInfo) => {
    setState(prev => ({
      ...prev,
      isDragging: true,
      dragOffset: info.offset.x
    }))
  }, [])

  // Navigate to specific property
  const goToProperty = useCallback((index: number) => {
    if (index >= 0 && index < properties.length) {
      setState(prev => ({
        ...prev,
        currentIndex: index,
        direction: index > prev.currentIndex ? 'left' : 'right'
      }))
      triggerHaptic('light')
    }
  }, [properties.length, triggerHaptic])

  // Property actions
  const handleLike = useCallback((propertyId: string) => {
    setLikedProperties(prev => {
      const newSet = new Set(prev)
      if (newSet.has(propertyId)) {
        newSet.delete(propertyId)
      } else {
        newSet.add(propertyId)
      }
      return newSet
    })
    triggerHaptic('light')
    onPropertyLike?.(propertyId)
  }, [onPropertyLike, triggerHaptic])

  const formatPrice = useCallback((price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(price)
  }, [])

  const formatDistance = useCallback((distance?: number) => {
    if (!distance) return null
    return `${distance.toFixed(1)} mi away`
  }, [])

  const getTemperatureColor = useCallback((temperature: number) => {
    if (temperature >= 75) return 'text-red-400 bg-red-500/20'
    if (temperature >= 50) return 'text-orange-400 bg-orange-500/20'
    if (temperature >= 25) return 'text-yellow-400 bg-yellow-500/20'
    return 'text-blue-400 bg-blue-500/20'
  }, [])

  const getTemperatureLabel = useCallback((temperature: number) => {
    if (temperature >= 75) return 'Hot'
    if (temperature >= 50) return 'Warm'
    if (temperature >= 25) return 'Cool'
    return 'Cold'
  }, [])

  if (!currentProperty) {
    return (
      <div className={cn('text-center text-gray-400 py-12', className)}>
        <MapPin className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>No properties available in this area</p>
      </div>
    )
  }

  return (
    <div ref={containerRef} className={cn('relative', className)}>
      {/* Property Counter */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Nearby Properties</h3>
        <div className="text-sm text-gray-400">
          {state.currentIndex + 1} of {properties.length}
        </div>
      </div>

      {/* Main Property Card */}
      <motion.div
        className="relative h-96 rounded-xl overflow-hidden"
        drag="x"
        dragConstraints={{ left: -50, right: 50 }}
        dragElastic={0.2}
        onDrag={handleDrag}
        onDragEnd={handleDragEnd}
        animate={{
          x: state.dragOffset,
          rotateZ: state.dragOffset * 0.1 // Subtle rotation while dragging
        }}
        transition={{
          type: state.isDragging ? 'spring' : 'spring',
          stiffness: 500,
          damping: 50
        }}
      >
        {/* Property Image */}
        <div className="relative h-full w-full">
          {currentProperty.images.length > 0 ? (
            <img
              src={currentProperty.images[0]}
              alt={currentProperty.address}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-gray-800 flex items-center justify-center">
              <Camera className="w-12 h-12 text-gray-600" />
            </div>
          )}

          {/* Gradient Overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />

          {/* Temperature Badge */}
          <div className={cn(
            'absolute top-4 right-4 px-3 py-1 rounded-full text-xs font-medium',
            getTemperatureColor(currentProperty.temperature)
          )}>
            {getTemperatureLabel(currentProperty.temperature)} {currentProperty.temperature}%
          </div>

          {/* ML Score Badge */}
          {currentProperty.mlScore && (
            <div className="absolute top-4 left-4 px-3 py-1 rounded-full bg-purple-500/20 text-purple-400 text-xs font-medium">
              AI Score: {Math.round(currentProperty.mlScore * 100)}%
            </div>
          )}

          {/* Property Details Overlay */}
          <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
            {/* Price */}
            <div className="flex justify-between items-start mb-2">
              <h4 className="text-2xl font-bold">
                {formatPrice(currentProperty.price)}
              </h4>
              {currentProperty.marketInsights && (
                <div className="text-right">
                  <div className="text-sm text-gray-300">
                    ${currentProperty.marketInsights.pricePerSqft}/sqft
                  </div>
                  <div className="text-xs text-gray-400">
                    {currentProperty.marketInsights.daysOnMarket} days
                  </div>
                </div>
              )}
            </div>

            {/* Address */}
            <div className="flex items-center gap-2 mb-3">
              <MapPin className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-gray-300">
                {currentProperty.address}
              </span>
              {currentProperty.distance && (
                <span className="text-xs text-gray-400">
                  • {formatDistance(currentProperty.distance)}
                </span>
              )}
            </div>

            {/* Property Stats */}
            <div className="flex items-center gap-4 mb-4">
              <div className="flex items-center gap-1">
                <Bed className="w-4 h-4 text-gray-400" />
                <span className="text-sm">{currentProperty.bedrooms}</span>
              </div>
              <div className="flex items-center gap-1">
                <Bath className="w-4 h-4 text-gray-400" />
                <span className="text-sm">{currentProperty.bathrooms}</span>
              </div>
              <div className="flex items-center gap-1">
                <Square className="w-4 h-4 text-gray-400" />
                <span className="text-sm">{currentProperty.sqft.toLocaleString()}</span>
              </div>
              <div className="flex items-center gap-1">
                <Calendar className="w-4 h-4 text-gray-400" />
                <span className="text-sm">
                  {new Date(currentProperty.listingDate).toLocaleDateString()}
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-between items-center">
              <button
                onClick={() => handleLike(currentProperty.id)}
                className={cn(
                  'p-3 rounded-full transition-colors',
                  likedProperties.has(currentProperty.id)
                    ? 'bg-red-500 text-white'
                    : 'bg-white/20 text-white hover:bg-white/30'
                )}
              >
                <Heart className={cn(
                  'w-5 h-5',
                  likedProperties.has(currentProperty.id) && 'fill-current'
                )} />
              </button>

              <button
                onClick={() => onAnalyzeProperty?.(currentProperty)}
                className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-full text-sm font-medium transition-colors"
              >
                Analyze Property
              </button>

              <button
                onClick={() => onPropertyShare?.(currentProperty)}
                className="p-3 rounded-full bg-white/20 text-white hover:bg-white/30 transition-colors"
              >
                <Share className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Swipe Direction Indicators */}
          <AnimatePresence>
            {state.isDragging && (
              <>
                {state.dragOffset > 20 && hasPrevious && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-green-500/80 text-white p-3 rounded-full"
                  >
                    <TrendingUp className="w-6 h-6 rotate-180" />
                  </motion.div>
                )}

                {state.dragOffset < -20 && hasNext && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-blue-500/80 text-white p-3 rounded-full"
                  >
                    <TrendingUp className="w-6 h-6" />
                  </motion.div>
                )}
              </>
            )}
          </AnimatePresence>
        </div>
      </motion.div>

      {/* Property Navigation Dots */}
      {properties.length > 1 && (
        <div className="flex justify-center gap-2 mt-4">
          {properties.map((_, index) => (
            <button
              key={index}
              onClick={() => goToProperty(index)}
              className={cn(
                'w-2 h-2 rounded-full transition-colors',
                index === state.currentIndex
                  ? 'bg-blue-400'
                  : 'bg-gray-600 hover:bg-gray-500'
              )}
            />
          ))}
        </div>
      )}

      {/* Navigation Controls */}
      {properties.length > 1 && (
        <div className="absolute top-1/2 transform -translate-y-1/2 left-0 right-0 flex justify-between px-2 pointer-events-none">
          <button
            onClick={() => goToProperty(state.currentIndex - 1)}
            disabled={!hasPrevious}
            className={cn(
              'p-3 rounded-full bg-black/50 text-white backdrop-blur-sm pointer-events-auto transition-opacity',
              hasPrevious ? 'opacity-75 hover:opacity-100' : 'opacity-25 cursor-not-allowed'
            )}
          >
            <TrendingUp className="w-5 h-5 rotate-180" />
          </button>

          <button
            onClick={() => goToProperty(state.currentIndex + 1)}
            disabled={!hasNext}
            className={cn(
              'p-3 rounded-full bg-black/50 text-white backdrop-blur-sm pointer-events-auto transition-opacity',
              hasNext ? 'opacity-75 hover:opacity-100' : 'opacity-25 cursor-not-allowed'
            )}
          >
            <TrendingUp className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Swipe Hint */}
      {!state.isDragging && state.currentIndex === 0 && properties.length > 1 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1 }}
          className="text-center mt-2 text-xs text-gray-500"
        >
          Swipe left/right to browse properties
        </motion.div>
      )}
    </div>
  )
}