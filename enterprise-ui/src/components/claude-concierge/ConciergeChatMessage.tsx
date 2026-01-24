/**
 * Individual message component with metadata display
 * Shows reasoning, suggested actions, and handoff recommendations
 */

'use client'

import { Sparkles, User, Lightbulb, ArrowRight, Bot, Clock, Zap } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useConciergeStore } from '@/store/useConciergeStore'
import type { ConciergeMessage } from '@/store/useConciergeStore'
import { format } from 'date-fns'
import { cn } from '@/lib/utils'

interface Props {
  message: ConciergeMessage
}

export function ConciergeChatMessage({ message }: Props) {
  const acceptHandoff = useConciergeStore((state) => state.acceptHandoff)
  const executeAction = useConciergeStore((state) => state.executeAction)

  const isUser = message.role === 'user'
  const hasMetadata = Boolean(message.metadata)

  const handleAcceptHandoff = async () => {
    if (message.metadata?.handoffRecommendation) {
      try {
        await acceptHandoff(message.metadata.handoffRecommendation)
      } catch (error) {
        console.error('Failed to accept handoff:', error)
      }
    }
  }

  const handleExecuteAction = async (actionIndex: number) => {
    if (message.metadata?.suggestedActions?.[actionIndex]) {
      try {
        await executeAction(message.metadata.suggestedActions[actionIndex])
      } catch (error) {
        console.error('Failed to execute action:', error)
      }
    }
  }

  return (
    <div className={cn(
      "flex gap-3 max-w-[90%]",
      isUser ? "flex-row-reverse self-end" : "flex-row self-start"
    )}>
      {/* Avatar */}
      <div className={cn(
        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
        isUser
          ? "bg-gray-500 text-white"
          : "bg-gradient-to-r from-purple-600 to-blue-600 text-white"
      )}>
        {isUser ? <User size={16} /> : <Sparkles size={16} />}
      </div>

      {/* Message Content */}
      <div className={cn(
        "flex flex-col gap-2",
        isUser ? "items-end" : "items-start"
      )}>
        {/* Main Message */}
        <div className={cn(
          "rounded-lg px-4 py-2 max-w-sm break-words",
          isUser
            ? "bg-gray-100 text-gray-900"
            : "bg-purple-50 text-purple-900 border border-purple-200"
        )}>
          <div className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
          </div>

          {/* Processing time indicator */}
          {message.metadata?.processingTime && !isUser && (
            <div className="flex items-center gap-1 mt-2 text-xs text-purple-600">
              <Clock size={10} />
              <span>{message.metadata.processingTime}ms</span>
            </div>
          )}

          {/* Timestamp */}
          <div className={cn(
            "text-xs mt-1",
            isUser ? "text-gray-600" : "text-purple-600"
          )}>
            {format(new Date(message.timestamp), 'h:mm a')}
          </div>
        </div>

        {/* Reasoning Section */}
        {message.metadata?.reasoning && !isUser && (
          <Card className="p-3 bg-purple-25 border-purple-100 max-w-sm">
            <div className="flex items-start gap-2">
              <Lightbulb size={14} className="text-purple-600 mt-0.5 flex-shrink-0" />
              <div>
                <div className="text-xs font-semibold text-purple-700 mb-1">
                  My Reasoning:
                </div>
                <div className="text-xs text-purple-600 leading-relaxed">
                  {message.metadata.reasoning}
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Suggested Actions */}
        {message.metadata?.suggestedActions && message.metadata.suggestedActions.length > 0 && !isUser && (
          <Card className="p-3 bg-blue-25 border-blue-100 max-w-sm">
            <div className="text-xs font-semibold text-blue-700 mb-2">
              Suggested Actions:
            </div>
            <div className="space-y-2">
              {message.metadata.suggestedActions.map((action, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => handleExecuteAction(index)}
                  className={cn(
                    "w-full justify-start text-xs h-auto py-2 px-3",
                    "hover:bg-blue-50 hover:border-blue-300"
                  )}
                >
                  <ArrowRight size={12} className="mr-2 flex-shrink-0" />
                  <div className="text-left min-w-0 flex-1">
                    <div className="font-semibold truncate">
                      {action.label}
                    </div>
                    <div className="text-gray-600 text-xs leading-tight">
                      {action.description}
                    </div>
                  </div>
                  {action.priority === 'high' && (
                    <Badge variant="destructive" className="ml-2 text-xs py-0 px-1">
                      High
                    </Badge>
                  )}
                </Button>
              ))}
            </div>
          </Card>
        )}

        {/* Bot Handoff Recommendation */}
        {message.metadata?.handoffRecommendation && !isUser && (
          <Card className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 border-green-200 max-w-sm">
            <div className="flex items-start gap-2 mb-3">
              <Bot size={16} className="text-green-700 mt-0.5 flex-shrink-0" />
              <div>
                <div className="text-sm font-semibold text-green-900 mb-1">
                  Recommended Bot Transfer
                </div>
                <div className="text-sm text-green-800 mb-2">
                  {getBotDisplayName(message.metadata.handoffRecommendation.targetBot)}
                </div>
              </div>
            </div>

            <div className="text-xs text-green-700 mb-3 leading-relaxed">
              {message.metadata.handoffRecommendation.reasoning}
            </div>

            <div className="flex items-center justify-between mb-3">
              <Badge
                variant="outline"
                className={cn(
                  "text-xs",
                  getConfidenceBadgeStyle(message.metadata.handoffRecommendation.confidence)
                )}
              >
                {Math.round(message.metadata.handoffRecommendation.confidence * 100)}% confidence
              </Badge>

              {message.metadata.handoffRecommendation.confidence > 0.8 && (
                <Badge className="bg-green-600 text-white text-xs">
                  Highly Recommended
                </Badge>
              )}
            </div>

            <Button
              size="sm"
              onClick={handleAcceptHandoff}
              className={cn(
                "w-full h-8 text-xs font-medium",
                "bg-green-600 hover:bg-green-700 text-white",
                "flex items-center justify-center gap-2"
              )}
            >
              <Zap size={14} />
              Start {getBotDisplayName(message.metadata.handoffRecommendation.targetBot)} Conversation
            </Button>

            {/* Context Transfer Preview */}
            {Object.keys(message.metadata.handoffRecommendation.contextToTransfer || {}).length > 0 && (
              <div className="mt-2 p-2 bg-green-100 rounded text-xs">
                <div className="font-medium text-green-800 mb-1">Context to transfer:</div>
                <div className="text-green-700">
                  {Object.keys(message.metadata.handoffRecommendation.contextToTransfer).join(', ')}
                </div>
              </div>
            )}
          </Card>
        )}
      </div>
    </div>
  )
}

function getBotDisplayName(botId: string): string {
  switch (botId) {
    case 'jorge-seller-bot':
      return 'Jorge Seller Bot'
    case 'lead-bot':
      return 'Lead Bot'
    case 'intent-decoder':
      return 'Intent Decoder'
    default:
      return botId
  }
}

function getConfidenceBadgeStyle(confidence: number): string {
  if (confidence >= 0.9) {
    return "bg-green-50 text-green-700 border-green-200"
  } else if (confidence >= 0.7) {
    return "bg-yellow-50 text-yellow-700 border-yellow-200"
  } else {
    return "bg-red-50 text-red-700 border-red-200"
  }
}