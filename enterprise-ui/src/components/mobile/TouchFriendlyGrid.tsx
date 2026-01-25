// Jorge's Real Estate AI Platform - Touch-Friendly Grid Component
// Mobile-optimized grid with large touch targets and haptic feedback

'use client'

import React, { useCallback, ReactNode } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

interface TouchFriendlyGridProps {
  children: ReactNode
  className?: string
  columns?: 2 | 3 | 4
  gap?: 'sm' | 'md' | 'lg'
  minTouchTarget?: number // Minimum touch target size in pixels (recommended: 44px)
}

export function TouchFriendlyGrid({
  children,
  className,
  columns = 2,
  gap = 'md',
  minTouchTarget = 44
}: TouchFriendlyGridProps) {

  // Haptic feedback for supported devices
  const triggerHapticFeedback = useCallback((type: 'light' | 'medium' | 'heavy' = 'light') => {
    if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
      // Simple vibration pattern based on feedback type
      switch (type) {
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

  const gapClasses = {
    sm: 'gap-2',
    md: 'gap-4',
    lg: 'gap-6'
  }

  const columnClasses = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        'grid w-full',
        columnClasses[columns],
        gapClasses[gap],
        className
      )}
      style={{
        // Ensure minimum touch target size
        '--min-touch-target': `${minTouchTarget}px`
      } as React.CSSProperties}
    >
      {React.Children.map(children, (child, index) => {
        if (!React.isValidElement(child)) return child

        // Enhance child elements with touch feedback
        return React.cloneElement(child, {
          ...child.props,
          onTouchStart: (e: TouchEvent) => {
            // Trigger light haptic feedback on touch start
            triggerHapticFeedback('light')

            // Call original onTouchStart if it exists
            if (child.props.onTouchStart) {
              child.props.onTouchStart(e)
            }
          },
          onMouseDown: (e: MouseEvent) => {
            // Trigger feedback for mouse events too (desktop testing)
            triggerHapticFeedback('light')

            // Call original onMouseDown if it exists
            if (child.props.onMouseDown) {
              child.props.onMouseDown(e)
            }
          },
          style: {
            ...child.props.style,
            // Ensure minimum touch target size
            minHeight: `${minTouchTarget}px`,
            minWidth: `${minTouchTarget}px`,
            // Improve touch responsiveness
            touchAction: 'manipulation',
            // Prevent text selection on mobile
            WebkitUserSelect: 'none',
            userSelect: 'none',
            // Prevent callout menus on iOS
            WebkitTouchCallout: 'none',
            // Prevent highlighting
            WebkitTapHighlightColor: 'transparent'
          }
        })
      })}
    </motion.div>
  )
}

// Touch-optimized button component for use within the grid
interface TouchButtonProps {
  children: ReactNode
  onClick?: () => void
  disabled?: boolean
  variant?: 'primary' | 'secondary' | 'accent' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  className?: string
  icon?: ReactNode
  hapticFeedback?: 'light' | 'medium' | 'heavy'
}

export function TouchButton({
  children,
  onClick,
  disabled = false,
  variant = 'primary',
  size = 'md',
  className,
  icon,
  hapticFeedback = 'light'
}: TouchButtonProps) {

  const triggerHaptic = useCallback(() => {
    if (disabled) return

    if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
      switch (hapticFeedback) {
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
  }, [disabled, hapticFeedback])

  const variantClasses = {
    primary: 'bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white border-blue-400',
    secondary: 'bg-gray-700 hover:bg-gray-600 active:bg-gray-800 text-gray-200 border-gray-600',
    accent: 'bg-green-500 hover:bg-green-600 active:bg-green-700 text-white border-green-400',
    danger: 'bg-red-500 hover:bg-red-600 active:bg-red-700 text-white border-red-400'
  }

  const sizeClasses = {
    sm: 'h-12 px-3 text-sm',
    md: 'h-16 px-4 text-base',
    lg: 'h-20 px-6 text-lg'
  }

  const handleClick = useCallback(() => {
    if (disabled) return

    triggerHaptic()
    onClick?.()
  }, [disabled, triggerHaptic, onClick])

  return (
    <motion.button
      whileHover={disabled ? {} : { scale: 1.02 }}
      whileTap={disabled ? {} : { scale: 0.98 }}
      onClick={handleClick}
      disabled={disabled}
      className={cn(
        // Base styles
        'relative overflow-hidden rounded-xl border transition-all duration-200',
        'flex items-center justify-center gap-2 font-medium',
        'focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-900',

        // Touch optimizations
        'touch-manipulation select-none',
        'active:duration-75', // Faster transition on tap

        // Size classes
        sizeClasses[size],

        // Variant classes
        disabled
          ? 'bg-gray-800 text-gray-500 border-gray-700 cursor-not-allowed'
          : variantClasses[variant],

        className
      )}
    >
      {/* Background gradient effect */}
      {!disabled && (
        <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0 opacity-0 transition-opacity active:opacity-100" />
      )}

      {/* Content */}
      <div className="relative flex items-center justify-center gap-2">
        {icon && (
          <span className="flex-shrink-0">
            {icon}
          </span>
        )}
        <span className="truncate">
          {children}
        </span>
      </div>

      {/* Loading indicator placeholder */}
      <div className="absolute inset-0 flex items-center justify-center bg-inherit opacity-0 transition-opacity">
        <div className="w-5 h-5 border-2 border-current border-r-transparent rounded-full animate-spin" />
      </div>
    </motion.button>
  )
}

// Quick action card component optimized for touch
interface QuickActionCardProps {
  icon: ReactNode
  title: string
  subtitle?: string
  onClick?: () => void
  disabled?: boolean
  className?: string
  badge?: string | number
  isActive?: boolean
}

export function QuickActionCard({
  icon,
  title,
  subtitle,
  onClick,
  disabled = false,
  className,
  badge,
  isActive = false
}: QuickActionCardProps) {

  const triggerHaptic = useCallback(() => {
    if (disabled) return

    if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
      navigator.vibrate(15) // Medium feedback for cards
    }
  }, [disabled])

  return (
    <motion.button
      whileHover={disabled ? {} : { scale: 1.02, y: -2 }}
      whileTap={disabled ? {} : { scale: 0.98 }}
      onClick={() => {
        if (disabled) return
        triggerHaptic()
        onClick?.()
      }}
      disabled={disabled}
      className={cn(
        // Base styles
        'relative overflow-hidden rounded-xl p-4 min-h-[88px]',
        'flex flex-col items-center justify-center gap-2',
        'transition-all duration-200 border',
        'touch-manipulation select-none',

        // Background and border
        isActive
          ? 'bg-blue-500/20 border-blue-400/50 shadow-lg shadow-blue-500/25'
          : 'bg-gray-800/80 border-gray-700',

        // States
        disabled
          ? 'opacity-50 cursor-not-allowed'
          : 'hover:border-gray-600 active:bg-gray-700/80',

        className
      )}
    >
      {/* Badge */}
      {badge && (
        <div className="absolute -top-1 -right-1 w-6 h-6 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
          {badge}
        </div>
      )}

      {/* Icon */}
      <div className={cn(
        'p-2 rounded-lg transition-colors',
        isActive ? 'text-blue-400 bg-blue-500/20' : 'text-gray-400',
        disabled ? 'text-gray-600' : 'group-hover:text-gray-300'
      )}>
        {icon}
      </div>

      {/* Text content */}
      <div className="text-center space-y-0.5">
        <div className={cn(
          'text-sm font-medium transition-colors',
          isActive ? 'text-blue-400' : 'text-white',
          disabled && 'text-gray-500'
        )}>
          {title}
        </div>
        {subtitle && (
          <div className="text-xs text-gray-400">
            {subtitle}
          </div>
        )}
      </div>

      {/* Active indicator */}
      {isActive && (
        <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-blue-400 rounded-full" />
      )}

      {/* Ripple effect on tap */}
      <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/10 to-white/0 opacity-0 transition-opacity active:opacity-100" />
    </motion.button>
  )
}