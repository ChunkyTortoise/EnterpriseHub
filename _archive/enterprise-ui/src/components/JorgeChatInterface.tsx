// Jorge Real Estate Bot Chat Interface
// Professional chat UI for LangGraph bot conversations

'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, Phone, Mail, Calendar, TrendingUp, AlertTriangle, Sparkles, BarChart3, ChevronRight, CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useChatStore } from '@/store/useChatStore'
import { useActiveConversation, useBotTyping, useRealtimeStatus } from '@/lib/providers'
import { format } from 'date-fns'
import { cn } from '@/lib/utils'

import { ShapExplainability } from './analytics/ShapExplainability'

interface ChatMessage {
  content: string
  role: 'user' | 'bot'
  timestamp: string
  botId: string
  type?: 'text' | 'chart' | 'lead_action' | 'property' | 'shap_explainability'
  metadata?: any
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-3 py-2 bg-[#1a1a1a] border border-white/5 rounded-2xl w-fit">
      <motion.div
        animate={{ opacity: [0.4, 1, 0.4] }}
        transition={{ duration: 1.5, repeat: Infinity, times: [0, 0.5, 1] }}
        className="w-1.5 h-1.5 bg-blue-500 rounded-full"
      />
      <motion.div
        animate={{ opacity: [0.4, 1, 0.4] }}
        transition={{ duration: 1.5, repeat: Infinity, times: [0, 0.5, 1], delay: 0.2 }}
        className="w-1.5 h-1.5 bg-blue-500 rounded-full"
      />
      <motion.div
        animate={{ opacity: [0.4, 1, 0.4] }}
        transition={{ duration: 1.5, repeat: Infinity, times: [0, 0.5, 1], delay: 0.4 }}
        className="w-1.5 h-1.5 bg-blue-500 rounded-full"
      />
    </div>
  )
}

function GenerativeContent({ type, metadata }: { type: string, metadata?: any }) {
  if (type === 'shap_explainability') {
    return (
      <div className="mt-3">
        <ShapExplainability 
          baseScore={metadata?.baseScore || 50} 
          finalScore={metadata?.finalScore || 85}
          features={metadata?.features}
        />
      </div>
    )
  }

  if (type === 'chart') {
    return (
      <div className="mt-3 p-4 bg-black/40 border border-white/10 rounded-xl overflow-hidden">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-jorge-glow" />
            <span className="text-xs font-semibold text-white uppercase tracking-wider">Market Analysis</span>
          </div>
          <Badge className="bg-jorge-glow/10 text-jorge-glow border-none text-[10px]">Real-time</Badge>
        </div>
        <div className="h-32 flex items-end gap-1 px-2">
          {[40, 70, 45, 90, 65, 80, 50, 85].map((h, i) => (
            <motion.div
              key={i}
              initial={{ height: 0 }}
              animate={{ height: `${h}%` }}
              transition={{ delay: i * 0.1, duration: 0.5 }}
              className="flex-1 bg-gradient-to-t from-blue-600 to-jorge-glow rounded-t-sm"
            />
          ))}
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2">
          <div className="p-2 bg-white/5 rounded-lg">
            <div className="text-[10px] text-gray-500 uppercase font-mono">Growth</div>
            <div className="text-sm font-bold text-white">+12.4%</div>
          </div>
          <div className="p-2 bg-white/5 rounded-lg">
            <div className="text-[10px] text-gray-500 uppercase font-mono">Confidence</div>
            <div className="text-sm font-bold text-white">94%</div>
          </div>
        </div>
      </div>
    )
  }

  if (type === 'lead_action') {
    return (
      <div className="mt-3 space-y-2">
        <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="w-4 h-4 text-blue-400" />
            <span className="text-xs font-bold text-blue-100 uppercase">Recommended Action</span>
          </div>
          <p className="text-xs text-blue-200/80 mb-3">{metadata?.reason || "Jorge suggests escalating this lead based on psychological commitment scores."}</p>
          <Button className="w-full bg-blue-600 hover:bg-blue-500 text-white h-8 text-xs jorge-haptic">
            Execute Escalation
            <ChevronRight className="w-3 h-3 ml-1" />
          </Button>
        </div>
      </div>
    )
  }

  return null
}

interface MessageBubbleProps {
  message: ChatMessage
  isTyping?: boolean
}

function MessageBubble({ message, isTyping = false }: MessageBubbleProps) {
  const isBot = message.role === 'bot'
  
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={cn(
        "flex gap-3 mb-6",
        isBot ? "flex-row" : "flex-row-reverse"
      )}
    >
      <div className={cn(
        "flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center border transition-all duration-300",
        isBot 
          ? "bg-blue-500/10 border-blue-500/30 text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.1)]" 
          : "bg-white/5 border-white/10 text-gray-400"
      )}>
        {isBot ? <Bot size={16} /> : <User size={16} />}
      </div>
      
      <div className={cn(
        "flex-1 max-w-[85%] sm:max-w-[75%]",
        isBot ? "" : "flex flex-col items-end"
      )}>
        <div className={cn(
          "relative rounded-2xl px-4 py-3 shadow-sm transition-all duration-300",
          isBot 
            ? "bg-[#1a1a1a] text-gray-200 border border-white/5 rounded-tl-none" 
            : "bg-blue-600 text-white border border-blue-500/30 rounded-tr-none"
        )}>
          {isBot && (
            <div className="absolute -top-5 left-0 flex items-center gap-1.5">
              <span className="text-[10px] font-bold tracking-widest text-blue-500 uppercase font-mono">Agent</span>
              <Sparkles className="w-2.5 h-2.5 text-blue-500" />
            </div>
          )}
          
          <div className="text-sm leading-relaxed whitespace-pre-wrap font-medium">
            {message.content}
          </div>

          {isBot && message.type && (
            <GenerativeContent type={message.type} metadata={message.metadata} />
          )}

          <div className={cn(
            "text-[9px] mt-2 font-mono uppercase tracking-tighter opacity-40",
            isBot ? "text-gray-400" : "text-blue-100"
          )}>
            {format(new Date(message.timestamp), 'HH:mm:ss')} • {isBot ? 'Verified AI' : 'User'}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function BotStatusIndicator({ botId }: { botId: string }) {
  const botStatuses = useChatStore((state) => state.botStatuses)
  const isTyping = useBotTyping(botId)
  const isConnected = useRealtimeStatus()
  
  const status = botStatuses[botId]
  
  if (!status) {
    return (
      <div className="flex items-center gap-2 jorge-label px-2 py-1 rounded-full bg-white/5 border border-white/10">
        <div className="w-1.5 h-1.5 rounded-full bg-gray-600 animate-pulse" />
        Synchronizing...
      </div>
    )
  }
  
  const statusColor = status.status === 'online' ? 'bg-jorge-glow' : 'bg-gray-600'
  const statusText = isTyping ? 'Synthesizing...' : status.status.toUpperCase()
  
  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2 bg-white/5 px-2.5 py-1 rounded-full border border-white/10 group cursor-default">
        <div className={cn(
          "w-1.5 h-1.5 rounded-full shadow-[0_0_8px_rgba(0,240,255,0.5)] transition-all duration-500",
          status.status === 'online' ? 'bg-jorge-glow animate-pulse' : 'bg-gray-600'
        )} />
        <span className="jorge-label text-gray-300 group-hover:text-jorge-glow transition-colors">{statusText}</span>
      </div>
      
      {status.responseTimeMs && (
        <div className="jorge-code text-jorge-glow/60 hidden sm:block tracking-[0.2em]">
          {status.responseTimeMs}MS
        </div>
      )}
      
      {!isConnected && (
        <Badge variant="outline" className="h-5 text-[9px] bg-red-500/10 text-red-400 border-red-500/20 px-1.5 animate-pulse">
          UNSTABLE
        </Badge>
      )}
    </div>
  )
}

function QuickActions({ onActionSelect }: { onActionSelect: (action: string) => void }) {
  const actions = [
    { icon: <Phone size={14} />, label: "Call", action: "I'd like to schedule a call" },
    { icon: <Mail size={14} />, label: "Info", action: "Please send me more information" },
    { icon: <Calendar size={14} />, label: "Showing", action: "I want to schedule a property showing" },
    { icon: <TrendingUp size={14} />, label: "Market", action: "Can you provide a market analysis?" },
  ]
  
  return (
    <div className="flex flex-wrap gap-2 py-4">
      {actions.map((action, index) => (
        <motion.div
          key={index}
          whileHover={{ scale: 1.05, translateY: -2 }}
          whileTap={{ scale: 0.95 }}
        >
          <Button
            variant="outline"
            size="sm"
            onClick={() => onActionSelect(action.action)}
            className="bg-white/5 border-white/10 hover:bg-white/10 text-gray-300 jorge-label h-8 px-4 rounded-full flex items-center gap-2 group transition-all"
          >
            <span className="text-jorge-glow opacity-60 group-hover:opacity-100 group-hover:scale-110 transition-all">{action.icon}</span>
            {action.label}
          </Button>
        </motion.div>
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
    <Card className={cn(
      "flex flex-col h-[700px] border-white/10 bg-jorge-dark/40 backdrop-blur-xl overflow-hidden shadow-2xl relative",
      className
    )}>
      {/* Dynamic Background Element */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-blue-500/50 to-transparent" />
      
      <CardHeader className="border-b border-white/5 bg-white/[0.02] py-4 px-6">
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-1">
            <CardTitle className="flex items-center gap-3 text-white text-lg font-bold tracking-tight">
              <div className="p-1.5 bg-blue-500/10 rounded-md border border-blue-500/20">
                <Bot className="w-5 h-5 text-blue-500" />
              </div>
              {botName}
            </CardTitle>
            <BotStatusIndicator botId={botId} />
          </div>
          
          <div className="flex gap-2">
            <Badge variant="outline" className="bg-white/5 border-white/10 text-gray-400 font-mono text-[9px] uppercase tracking-widest px-2">
              JORGE V4.0
            </Badge>
            <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20 font-mono text-[9px] uppercase tracking-widest px-2">
              SECURE
            </Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col p-0 overflow-hidden relative">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
          {!activeConversation?.messages?.length ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-sm mx-auto animate-in fade-in zoom-in duration-500">
              <div className="relative mb-6">
                <div className="absolute inset-0 bg-blue-500/20 blur-2xl rounded-full" />
                <div className="relative w-16 h-16 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center shadow-2xl">
                  <Sparkles className="w-8 h-8 text-blue-500" />
                </div>
              </div>
              <h3 className="text-white font-bold text-xl mb-2 tracking-tight">Jorge Concierge Active</h3>
              <p className="text-gray-400 text-sm leading-relaxed mb-8">
                Ready to handle qualification, market analysis, and strategic property matching. How can I assist?
              </p>
              <div className="w-full">
                <QuickActions onActionSelect={handleQuickAction} />
              </div>
            </div>
          ) : (
            <>
              <AnimatePresence initial={false}>
                {activeConversation.messages.map((message, index) => (
                  <MessageBubble
                    key={index}
                    message={message}
                  />
                ))}
                
                {isTyping && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    className="flex gap-3 mb-6"
                  >
                    <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 flex items-center justify-center">
                      <Bot size={16} />
                    </div>
                    <TypingIndicator />
                  </motion.div>
                )}
              </AnimatePresence>
              
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
        
        {/* Input Area */}
        <div className="p-4 bg-white/[0.02] border-t border-white/5">
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500/30 to-purple-500/30 rounded-xl blur opacity-0 group-focus-within:opacity-100 transition duration-500" />
            <div className="relative flex items-center gap-2 bg-[#0f0f0f] border border-white/10 rounded-xl p-1.5 focus-within:border-blue-500/50 transition-all">
              <Input
                ref={inputRef}
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Message Jorge AI..."
                className="flex-1 bg-transparent border-none text-white focus-visible:ring-0 placeholder:text-gray-600 h-10"
                disabled={isTyping}
              />
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button 
                  onClick={handleSendMessage}
                  disabled={!messageInput.trim() || isTyping}
                  size="icon"
                  className="h-9 w-9 bg-blue-600 hover:bg-blue-500 text-white rounded-lg shadow-[0_0_15px_rgba(37,99,235,0.4)] transition-all"
                >
                  <Send size={16} />
                </Button>
              </motion.div>
            </div>
          </div>
          
          <div className="flex items-center justify-between mt-3 px-1">
            <p className="text-[10px] text-gray-500 jorge-code">
              Cmd + Enter to send • Verified AI Response
            </p>
            <div className="flex items-center gap-1.5">
              <div className="w-1 h-1 rounded-full bg-blue-500" />
              <span className="text-[10px] text-blue-500/60 font-mono tracking-widest uppercase">Encryption Active</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default JorgeChatInterface