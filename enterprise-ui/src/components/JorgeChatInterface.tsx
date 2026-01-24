// Jorge Real Estate Bot Chat Interface
// Professional chat UI for LangGraph bot conversations

'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Phone, Mail, Calendar, TrendingUp, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useChatStore } from '@/store/useChatStore'
import { useActiveConversation, useBotTyping, useRealtimeStatus } from '@/lib/providers'
import { format } from 'date-fns'

interface ChatMessage {
  content: string
  role: 'user' | 'bot'
  timestamp: string
  botId: string
}

interface MessageBubbleProps {
  message: ChatMessage
  isTyping?: boolean
}

function MessageBubble({ message, isTyping = false }: MessageBubbleProps) {
  const isBot = message.role === 'bot'
  
  return (
    <div className={`flex gap-3 ${isBot ? 'flex-row' : 'flex-row-reverse'} mb-4`}>
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
        isBot 
          ? 'bg-blue-500 text-white' 
          : 'bg-gray-500 text-white'
      }`}>
        {isBot ? <Bot size={16} /> : <User size={16} />}
      </div>
      
      <div className={`flex-1 max-w-[80%] ${isBot ? '' : 'flex justify-end'}`}>
        <div className={`rounded-lg px-4 py-2 ${
          isBot 
            ? 'bg-blue-50 text-blue-900 border border-blue-200' 
            : 'bg-gray-100 text-gray-900 border border-gray-200'
        }`}>
          <div className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
            {isTyping && (
              <span className="inline-flex ml-1">
                <span className="animate-pulse">●</span>
                <span className="animate-pulse delay-100">●</span>
                <span className="animate-pulse delay-200">●</span>
              </span>
            )}
          </div>
          <div className={`text-xs mt-1 ${
            isBot ? 'text-blue-600' : 'text-gray-600'
          }`}>
            {format(new Date(message.timestamp), 'h:mm a')}
          </div>
        </div>
      </div>
    </div>
  )
}

function BotStatusIndicator({ botId }: { botId: string }) {
  const botStatuses = useChatStore((state) => state.botStatuses)
  const isTyping = useBotTyping(botId)
  const isConnected = useRealtimeStatus()
  
  const status = botStatuses[botId]
  
  if (!status) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <div className="w-2 h-2 rounded-full bg-gray-400" />
        Connecting...
      </div>
    )
  }
  
  const statusColor = status.status === 'online' ? 'green' : 'gray'
  const statusText = isTyping ? 'Typing...' : status.status
  
  return (
    <div className="flex items-center gap-2 text-sm">
      <div className={`w-2 h-2 rounded-full bg-${statusColor}-500 ${
        status.status === 'online' ? 'animate-pulse' : ''
      }`} />
      <span className="text-gray-700">{statusText}</span>
      {!isConnected && (
        <AlertTriangle size={14} className="text-amber-500" /* title="Connection unstable" */ />
      )}
      {status.responseTimeMs && (
        <span className="text-xs text-gray-500">
          ({status.responseTimeMs}ms avg)
        </span>
      )}
    </div>
  )
}

function QuickActions({ onActionSelect }: { onActionSelect: (action: string) => void }) {
  const actions = [
    { icon: <Phone size={14} />, label: "Schedule Call", action: "I'd like to schedule a call" },
    { icon: <Mail size={14} />, label: "Send Info", action: "Please send me more information" },
    { icon: <Calendar size={14} />, label: "Book Showing", action: "I want to schedule a property showing" },
    { icon: <TrendingUp size={14} />, label: "Market Analysis", action: "Can you provide a market analysis?" },
  ]
  
  return (
    <div className="flex flex-wrap gap-2 p-3 bg-gray-50 rounded-lg">
      <span className="text-xs font-medium text-gray-600 w-full mb-1">Quick Actions:</span>
      {actions.map((action, index) => (
        <Button
          key={index}
          variant="outline"
          size="sm"
          onClick={() => onActionSelect(action.action)}
          className="flex items-center gap-2 text-xs h-8"
        >
          {action.icon}
          {action.label}
        </Button>
      ))}
    </div>
  )
}

interface JorgeChatInterfaceProps {
  botId: string
  botName: string
  conversationId?: string
  className?: string
}

export function JorgeChatInterface({ 
  botId, 
  botName, 
  conversationId,
  className = '' 
}: JorgeChatInterfaceProps) {
  const [messageInput, setMessageInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  
  const sendMessage = useChatStore((state) => state.sendMessage)
  const setActiveConversation = useChatStore((state) => state.setActiveConversation)
  const activeConversation = useActiveConversation()
  const isTyping = useBotTyping(botId)
  
  // Set active conversation on mount
  useEffect(() => {
    if (conversationId) {
      setActiveConversation(conversationId)
    }
  }, [conversationId, setActiveConversation])
  
  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activeConversation?.messages, isTyping])
  
  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus()
  }, [])
  
  const handleSendMessage = () => {
    if (!messageInput.trim()) return
    
    sendMessage(botId, messageInput.trim())
    setMessageInput('')
  }
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }
  
  const handleQuickAction = (action: string) => {
    setMessageInput(action)
    // Auto-send quick actions
    setTimeout(() => {
      sendMessage(botId, action)
      setMessageInput('')
    }, 100)
  }
  
  return (
    <Card className={`flex flex-col h-[600px] ${className}`}>
      <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-indigo-50">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Bot className="w-5 h-5 text-blue-600" />
              {botName}
            </CardTitle>
            <BotStatusIndicator botId={botId} />
          </div>
          
          <div className="flex gap-2">
            <Badge variant="outline" className="bg-white">
              Jorge's AI
            </Badge>
            <Badge variant="outline" className="bg-green-50 text-green-700">
              Real Estate Pro
            </Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col p-0">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {!activeConversation?.messages?.length ? (
            <div className="text-center text-gray-500 mt-8">
              <Bot className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <h3 className="font-semibold mb-2">Start a conversation with {botName}</h3>
              <p className="text-sm mb-4">
                I'm here to help with real estate questions, property searches, and lead qualification.
              </p>
              <QuickActions onActionSelect={handleQuickAction} />
            </div>
          ) : (
            <>
              {activeConversation.messages.map((message, index) => (
                <MessageBubble
                  key={index}
                  message={message}
                />
              ))}
              
              {isTyping && (
                <MessageBubble
                  message={{
                    content: '',
                    role: 'bot',
                    timestamp: new Date().toISOString(),
                    botId
                  }}
                  isTyping={true}
                />
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
              placeholder="Type your message..."
              className="flex-1"
              disabled={isTyping}
            />
            <Button 
              onClick={handleSendMessage}
              disabled={!messageInput.trim() || isTyping}
              size="sm"
              className="px-4"
            >
              <Send size={16} />
            </Button>
          </div>
          
          {activeConversation?.messages?.length === 0 && (
            <div className="mt-3">
              <QuickActions onActionSelect={handleQuickAction} />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export default JorgeChatInterface