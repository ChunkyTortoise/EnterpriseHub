/**
 * Proactive Suggestions Panel
 * Displays context-aware suggestions based on platform activity
 */

'use client'

import {
  TrendingUp,
  Users,
  ArrowRight,
  X,
  Lightbulb,
  Zap,
  Target,
  Clock,
  CheckCircle
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useConciergeStore } from '@/store/useConciergeStore'
import type { ProactiveSuggestionState } from '@/store/useConciergeStore'
import { cn } from '@/lib/utils'

interface Props {
  suggestions: ProactiveSuggestionState[]
}

export function ProactiveSuggestionsPanel({ suggestions }: Props) {
  const acceptSuggestion = useConciergeStore((state) => state.acceptSuggestion)
  const dismissSuggestion = useConciergeStore((state) => state.dismissSuggestion)

  if (suggestions.length === 0) return null

  const handleAcceptSuggestion = async (suggestion: ProactiveSuggestionState) => {
    try {
      await acceptSuggestion(suggestion)
    } catch (error) {
      console.error('Failed to accept suggestion:', error)
    }
  }

  const handleDismissSuggestion = (suggestionId: string) => {
    dismissSuggestion(suggestionId)
  }

  return (
    <div className="border-b bg-gradient-to-r from-orange-25 to-yellow-25">
      <div className="p-3">
        <div className="flex items-center gap-2 mb-3">
          <Lightbulb className="w-4 h-4 text-orange-600" />
          <span className="text-sm font-semibold text-orange-800">
            Smart Suggestions
          </span>
          <Badge variant="secondary" className="text-xs">
            {suggestions.length}
          </Badge>
        </div>

        <div className="space-y-2">
          {suggestions.slice(0, 3).map((suggestion) => ( // Show max 3 suggestions
            <ProactiveSuggestionCard
              key={suggestion.id}
              suggestion={suggestion}
              onAccept={() => handleAcceptSuggestion(suggestion)}
              onDismiss={() => handleDismissSuggestion(suggestion.id)}
            />
          ))}
        </div>

        {suggestions.length > 3 && (
          <div className="text-xs text-orange-600 mt-2 text-center">
            +{suggestions.length - 3} more suggestions available
          </div>
        )}
      </div>
    </div>
  )
}

interface SuggestionCardProps {
  suggestion: ProactiveSuggestionState
  onAccept: () => void
  onDismiss: () => void
}

function ProactiveSuggestionCard({ suggestion, onAccept, onDismiss }: SuggestionCardProps) {
  const getSuggestionIcon = (type: string) => {
    switch (type) {
      case 'workflow':
        return <Target className="w-4 h-4" />
      case 'feature':
        return <Zap className="w-4 h-4" />
      case 'best_practice':
        return <CheckCircle className="w-4 h-4" />
      case 'opportunity':
        return <TrendingUp className="w-4 h-4" />
      default:
        return <Lightbulb className="w-4 h-4" />
    }
  }

  const getSuggestionTypeColor = (type: string) => {
    switch (type) {
      case 'workflow':
        return 'text-blue-600'
      case 'feature':
        return 'text-purple-600'
      case 'best_practice':
        return 'text-green-600'
      case 'opportunity':
        return 'text-orange-600'
      default:
        return 'text-gray-600'
    }
  }

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'high':
        return (
          <Badge variant="destructive" className="text-xs py-0 px-1">
            High Priority
          </Badge>
        )
      case 'medium':
        return (
          <Badge variant="default" className="text-xs py-0 px-1 bg-orange-500">
            Medium
          </Badge>
        )
      case 'low':
        return (
          <Badge variant="outline" className="text-xs py-0 px-1">
            Low
          </Badge>
        )
      default:
        return null
    }
  }

  return (
    <Card className={cn(
      "p-3 transition-all duration-200 hover:shadow-md",
      suggestion.priority === 'high'
        ? "border-l-4 border-l-red-400 bg-red-50/50"
        : suggestion.priority === 'medium'
        ? "border-l-4 border-l-orange-400 bg-orange-50/50"
        : "border-l-4 border-l-blue-400 bg-blue-50/50"
    )}>
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-start gap-2 flex-1 min-w-0">
          <div className={cn("mt-0.5 flex-shrink-0", getSuggestionTypeColor(suggestion.type))}>
            {getSuggestionIcon(suggestion.type)}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="text-sm font-semibold text-gray-900 truncate">
                {suggestion.title}
              </h4>
              {getPriorityBadge(suggestion.priority)}
            </div>

            <p className="text-xs text-gray-600 leading-relaxed">
              {suggestion.description}
            </p>
          </div>
        </div>

        {/* Dismiss button */}
        <button
          onClick={onDismiss}
          className="flex-shrink-0 p-1 hover:bg-gray-100 rounded transition-colors"
          title="Dismiss suggestion"
        >
          <X size={12} className="text-gray-500" />
        </button>
      </div>

      {/* Action button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <Clock size={10} />
          <span className="capitalize">{suggestion.type.replace('_', ' ')}</span>
        </div>

        <Button
          size="sm"
          onClick={onAccept}
          className={cn(
            "h-7 text-xs px-3 flex items-center gap-1.5",
            suggestion.priority === 'high'
              ? "bg-red-600 hover:bg-red-700 text-white"
              : suggestion.priority === 'medium'
              ? "bg-orange-600 hover:bg-orange-700 text-white"
              : "bg-blue-600 hover:bg-blue-700 text-white"
          )}
        >
          <span>{suggestion.action.label}</span>
          <ArrowRight size={12} />
        </Button>
      </div>

      {/* Expiration indicator */}
      {suggestion.expiresAt && (
        <div className="mt-2 text-xs text-gray-500 flex items-center gap-1">
          <Clock size={10} />
          <span>
            Expires {new Date(suggestion.expiresAt).toLocaleTimeString()}
          </span>
        </div>
      )}
    </Card>
  )
}

export default ProactiveSuggestionsPanel