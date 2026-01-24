/**
 * Main Claude Concierge UI Component
 * Floating sidebar with collapsible interface
 *
 * Integration Points:
 * - JorgeChatInterface.tsx:139-286 (chat UI patterns)
 * - JorgeCommandCenter.tsx:206-372 (dashboard integration)
 */

'use client'

import { useState, useRef, useEffect } from 'react'
import { MessageSquare, X, Sparkles, ChevronDown, ChevronUp, Settings, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { useConciergeStore } from '@/store/useConciergeStore'
import { ConciergeChatMessage } from './ConciergeChatMessage'
import { ProactiveSuggestionsPanel } from './ProactiveSuggestionsPanel'
import { cn } from '@/lib/utils'

export function ClaudeConcierge() {
  const [messageInput, setMessageInput] = useState('')
  const [showSettings, setShowSettings] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Store state
  const isVisible = useConciergeStore((state) => state.isVisible)
  const isExpanded = useConciergeStore((state) => state.isExpanded)
  const isTyping = useConciergeStore((state) => state.isTyping)
  const isInitialized = useConciergeStore((state) => state.isInitialized)
  const initializationError = useConciergeStore((state) => state.initializationError)
  const suggestionsEnabled = useConciergeStore((state) => state.suggestionsEnabled)

  const activeConversation = useConciergeStore((state) => {
    const id = state.activeConversationId
    return id ? state.conversations[id] : null
  })

  const activeSuggestions = useConciergeStore((state) =>
    state.proactiveSuggestions.filter(s => !s.dismissed && !s.acceptedAt)
  )

  // Store actions
  const toggleVisibility = useConciergeStore((state) => state.toggleVisibility)
  const setExpanded = useConciergeStore((state) => state.setExpanded)
  const sendMessage = useConciergeStore((state) => state.sendMessage)
  const initializeConcierge = useConciergeStore((state) => state.initializeConcierge)
  const toggleSuggestions = useConciergeStore((state) => state.toggleSuggestions)
  const getPerformanceMetrics = useConciergeStore((state) => state.getPerformanceMetrics)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activeConversation?.messages])

  // Focus input when expanded
  useEffect(() => {
    if (isVisible && isExpanded && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isVisible, isExpanded])

  // Initialize on mount if needed
  useEffect(() => {
    if (!isInitialized && !initializationError) {
      initializeConcierge()
    }
  }, [isInitialized, initializationError, initializeConcierge])

  const handleSendMessage = async () => {
    if (!messageInput.trim() || isTyping) return

    const message = messageInput.trim()
    setMessageInput('')

    try {
      await sendMessage(message)
    } catch (error) {
      console.error('Failed to send message:', error)
      // Error is already handled in the store, just restore input
      setMessageInput(message)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const performanceMetrics = getPerformanceMetrics()

  // Floating button when collapsed
  if (!isVisible) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <button
          onClick={toggleVisibility}
          className={cn(
            "relative w-16 h-16 rounded-full shadow-lg transition-all duration-300 flex items-center justify-center group",
            isInitialized
              ? "bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
              : "bg-gray-400 cursor-not-allowed"
          )}
          disabled={!isInitialized}
          title={isInitialized ? "Open Claude Concierge" : "Initializing..."}
        >
          <Sparkles className={cn(
            "w-7 h-7 text-white transition-transform",
            isInitialized && "group-hover:scale-110"
          )} />

          {/* Status indicators */}
          <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full animate-pulse" />

          {activeSuggestions.length > 0 && (
            <div className="absolute -top-2 -left-2 w-6 h-6 bg-orange-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xs font-bold">{activeSuggestions.length}</span>
            </div>
          )}
        </button>
      </div>
    )
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 w-96 flex flex-col bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-gradient-to-r from-purple-50 to-blue-50 border-b">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 bg-gradient-to-r from-purple-600 to-blue-600 rounded-full flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div className={cn(
              "absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-white",
              isInitialized ? "bg-green-500" : "bg-orange-500"
            )} />
          </div>

          <div>
            <h3 className="font-semibold text-sm text-gray-900">Claude Concierge</h3>
            <p className="text-xs text-gray-600">
              {isInitialized ? 'Your AI Platform Guide' : 'Initializing...'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Performance indicator */}
          {performanceMetrics.avgResponseTime > 0 && (
            <Badge variant="outline" className="text-xs">
              {Math.round(performanceMetrics.avgResponseTime)}ms
            </Badge>
          )}

          {/* Settings button */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-1 hover:bg-white/50 rounded transition-colors"
            title="Settings"
          >
            <Settings size={14} />
          </button>

          {/* Expand/collapse button */}
          <button
            onClick={() => setExpanded(!isExpanded)}
            className="p-1 hover:bg-white/50 rounded transition-colors"
            title={isExpanded ? "Minimize" : "Expand"}
          >
            {isExpanded ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
          </button>

          {/* Close button */}
          <button
            onClick={toggleVisibility}
            className="p-1 hover:bg-white/50 rounded transition-colors"
            title="Close"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && isExpanded && (
        <div className="p-3 bg-gray-50 border-b text-sm space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-gray-700">Proactive Suggestions</span>
            <button
              onClick={() => toggleSuggestions(!suggestionsEnabled)}
              className={cn(
                "w-10 h-6 rounded-full transition-colors relative",
                suggestionsEnabled ? "bg-blue-500" : "bg-gray-300"
              )}
            >
              <div className={cn(
                "w-4 h-4 bg-white rounded-full absolute top-1 transition-transform",
                suggestionsEnabled ? "translate-x-5" : "translate-x-1"
              )} />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
            <div>Conversations: {performanceMetrics.conversationsCount}</div>
            <div>Interactions: {performanceMetrics.totalInteractions}</div>
            <div>Avg Response: {performanceMetrics.avgResponseTime}ms</div>
            <div>Error Rate: {Math.round(performanceMetrics.errorRate * 100)}%</div>
          </div>
        </div>
      )}

      {isExpanded && (
        <>
          {/* Error Display */}
          {initializationError && (
            <div className="p-3 bg-red-50 border-b border-red-200 text-sm">
              <div className="text-red-800 font-medium">Initialization Error</div>
              <div className="text-red-600 text-xs">{initializationError}</div>
              <Button
                size="sm"
                variant="outline"
                className="mt-2 text-xs h-6"
                onClick={initializeConcierge}
              >
                Retry
              </Button>
            </div>
          )}

          {/* Proactive Suggestions */}
          {activeSuggestions.length > 0 && (
            <ProactiveSuggestionsPanel suggestions={activeSuggestions} />
          )}

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 max-h-[400px] min-h-[300px]">
            {!activeConversation?.messages.length ? (
              <div className="text-center text-gray-500 mt-8">
                <div className="w-16 h-16 bg-gradient-to-r from-purple-100 to-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Sparkles className="w-8 h-8 text-purple-500" />
                </div>
                <h4 className="font-semibold mb-2 text-gray-700">Welcome to Claude Concierge!</h4>
                <p className="text-sm mb-4 text-gray-600">
                  I'm your AI guide for Jorge's platform. I can help you navigate, suggest actions, and coordinate with our specialized bots.
                </p>

                {isInitialized ? (
                  <div className="space-y-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => sendMessage("What can you help me with?")}
                      className="w-full text-xs h-8"
                    >
                      What can you help me with?
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => sendMessage("Show me Jorge Seller Bot capabilities")}
                      className="w-full text-xs h-8"
                    >
                      Tell me about Jorge Seller Bot
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => sendMessage("How do I qualify a new lead?")}
                      className="w-full text-xs h-8"
                    >
                      How do I qualify leads?
                    </Button>
                  </div>
                ) : (
                  <div className="flex items-center justify-center gap-2 text-orange-600">
                    <Zap className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Initializing AI services...</span>
                  </div>
                )}
              </div>
            ) : (
              <>
                {activeConversation.messages.map((message, index) => (
                  <ConciergeChatMessage key={`${message.timestamp}-${index}`} message={message} />
                ))}

                {isTyping && (
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" />
                      <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce delay-100" />
                      <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce delay-200" />
                    </div>
                    <span>Claude is thinking...</span>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Input Area */}
          <div className="border-t p-4">
            <div className="flex gap-2">
              <Input
                ref={inputRef}
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={isInitialized ? "Ask me anything..." : "Initializing..."}
                className="flex-1 text-sm"
                disabled={!isInitialized || isTyping}
                maxLength={500}
              />
              <Button
                onClick={handleSendMessage}
                disabled={!messageInput.trim() || !isInitialized || isTyping}
                size="sm"
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 px-3"
              >
                {isTyping ? (
                  <Zap className="w-4 h-4 animate-pulse" />
                ) : (
                  <MessageSquare className="w-4 h-4" />
                )}
              </Button>
            </div>

            {messageInput.length > 0 && (
              <div className="text-xs text-gray-500 mt-1">
                {messageInput.length}/500 characters
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}

export default ClaudeConcierge