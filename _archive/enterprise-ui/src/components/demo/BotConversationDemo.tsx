// Jorge's Bot Conversation Demo Component
// Real-time bot interaction simulation for professional presentations

'use client';

import { useState, useEffect, useRef } from 'react';
import {
  MessageSquare,
  Bot,
  User,
  Mic,
  MicOff,
  Send,
  MoreVertical,
  Volume2,
  Brain,
  Target,
  TrendingUp,
  Clock,
  Zap
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarContent, AvatarFallback } from '@/components/ui/avatar';
import { motion, AnimatePresence } from 'framer-motion';
import type { DemoScenario, ConversationStep } from '@/lib/demo/ScenarioEngine';
import type { ConversationState } from '@/lib/demo/ConversationSimulator';

interface BotConversationDemoProps {
  scenario: DemoScenario;
  conversationState: ConversationState;
  currentStep: ConversationStep | null;
  isTyping: boolean;
  onUserInput: (input: string) => void;
  isFullScreen?: boolean;
}

interface Message {
  id: string;
  speaker: string;
  content: string;
  timestamp: Date;
  type: 'bot' | 'user' | 'system';
  botType?: string;
  confidence?: number;
  reasoning?: string;
  tone?: string;
}

export function BotConversationDemo({
  scenario,
  conversationState,
  currentStep,
  isTyping,
  onUserInput,
  isFullScreen = false
}: BotConversationDemoProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [userInput, setUserInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize with welcome message
  useEffect(() => {
    const welcomeMessage: Message = {
      id: 'welcome',
      speaker: 'Jorge AI',
      content: `Welcome to Jorge's AI demonstration. I'm going to show you how my confrontational qualification methodology identifies serious ${scenario.category.includes('seller') ? 'sellers' : 'buyers'} in minutes, not days.`,
      timestamp: new Date(),
      type: 'bot',
      botType: 'jorge_seller',
      confidence: 0.98,
      tone: 'confrontational'
    };
    setMessages([welcomeMessage]);
  }, [scenario]);

  // Add messages from conversation steps
  useEffect(() => {
    if (!currentStep) return;

    const newMessage: Message = {
      id: currentStep.id,
      speaker: currentStep.content.speaker,
      content: currentStep.content.message,
      timestamp: new Date(),
      type: currentStep.content.speaker.toLowerCase().includes('ai') ? 'bot' : 'user',
      botType: currentStep.botType,
      confidence: currentStep.content.confidence,
      reasoning: currentStep.content.reasoning,
      tone: currentStep.content.tone
    };

    setMessages(prev => [...prev, newMessage]);
  }, [currentStep]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSendMessage = () => {
    if (!userInput.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      speaker: 'Client',
      content: userInput,
      timestamp: new Date(),
      type: 'user'
    };

    setMessages(prev => [...prev, userMessage]);
    onUserInput(userInput);
    setUserInput('');

    // Simulate Jorge's response after a delay
    setTimeout(() => {
      const jorgeResponse: Message = {
        id: (Date.now() + 1).toString(),
        speaker: 'Jorge AI',
        content: generateJorgeResponse(userInput),
        timestamp: new Date(),
        type: 'bot',
        botType: 'jorge_seller',
        confidence: 0.92,
        tone: 'confrontational'
      };
      setMessages(prev => [...prev, jorgeResponse]);
    }, 1500);
  };

  const generateJorgeResponse = (input: string): string => {
    const responses = [
      "I appreciate the honesty. Now let's talk about what it's really going to take to sell your property.",
      "That's exactly what I needed to hear. You're ready to work with a professional who gets results.",
      "Perfect. Most agents would waste your time with pleasantries. I get straight to business.",
      "Good. I don't work with tire kickers, so I'm glad you're serious about selling.",
      "That tells me everything I need to know. Let's get your property SOLD."
    ];
    return responses[Math.floor(Math.random() * responses.length)];
  };

  const getBotTypeIcon = (botType?: string) => {
    switch (botType) {
      case 'jorge_seller': return Target;
      case 'lead_nurture': return MessageSquare;
      case 'analytics': return TrendingUp;
      case 'buyer_assistant': return User;
      default: return Bot;
    }
  };

  const getBotTypeColor = (botType?: string) => {
    switch (botType) {
      case 'jorge_seller': return 'text-red-400';
      case 'lead_nurture': return 'text-blue-400';
      case 'analytics': return 'text-green-400';
      case 'buyer_assistant': return 'text-purple-400';
      default: return 'text-gray-400';
    }
  };

  const getToneColor = (tone?: string) => {
    switch (tone) {
      case 'confrontational': return 'bg-red-500/10 text-red-300 border-red-500/30';
      case 'supportive': return 'bg-blue-500/10 text-blue-300 border-blue-500/30';
      case 'analytical': return 'bg-green-500/10 text-green-300 border-green-500/30';
      case 'urgent': return 'bg-yellow-500/10 text-yellow-300 border-yellow-500/30';
      default: return 'bg-gray-500/10 text-gray-300 border-gray-500/30';
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const renderMessage = (message: Message) => {
    const isBot = message.type === 'bot';
    const BotIcon = getBotTypeIcon(message.botType);

    return (
      <motion.div
        key={message.id}
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.3 }}
        className={`flex gap-3 ${isBot ? 'justify-start' : 'justify-end'} mb-4`}
      >
        {isBot && (
          <Avatar className="w-10 h-10 border-2 border-blue-500/30">
            <AvatarContent className="bg-blue-600 text-white">
              <BotIcon className="w-5 h-5" />
            </AvatarContent>
            <AvatarFallback>AI</AvatarFallback>
          </Avatar>
        )}

        <div className={`max-w-[80%] ${isBot ? 'mr-12' : 'ml-12'}`}>
          <div
            className={`rounded-2xl px-4 py-3 ${
              isBot
                ? 'bg-white/5 border border-white/10'
                : 'bg-blue-600 text-white'
            }`}
          >
            {/* Message Header */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className={`font-medium text-sm ${isBot ? 'text-white' : 'text-blue-100'}`}>
                  {message.speaker}
                </span>
                {isBot && message.tone && (
                  <Badge variant="outline" className={`text-xs ${getToneColor(message.tone)}`}>
                    {message.tone}
                  </Badge>
                )}
              </div>
              <span className={`text-xs ${isBot ? 'text-gray-400' : 'text-blue-200'}`}>
                {formatTime(message.timestamp)}
              </span>
            </div>

            {/* Message Content */}
            <p className={`text-sm leading-relaxed ${isBot ? 'text-gray-300' : 'text-white'}`}>
              {message.content}
            </p>

            {/* Bot Metadata */}
            {isBot && showDetails && (message.confidence || message.reasoning) && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                transition={{ duration: 0.2 }}
                className="mt-3 pt-3 border-t border-white/10"
              >
                {message.confidence && (
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="w-3 h-3 text-blue-400" />
                    <span className="text-xs text-gray-400">Confidence:</span>
                    <span className="text-xs text-blue-400 font-medium">
                      {Math.round(message.confidence * 100)}%
                    </span>
                  </div>
                )}
                {message.reasoning && (
                  <p className="text-xs text-gray-400 leading-relaxed">
                    <span className="font-medium">Reasoning:</span> {message.reasoning}
                  </p>
                )}
              </motion.div>
            )}
          </div>
        </div>

        {!isBot && (
          <Avatar className="w-10 h-10 border-2 border-gray-500/30">
            <AvatarContent className="bg-gray-600 text-white">
              <User className="w-5 h-5" />
            </AvatarContent>
            <AvatarFallback>CL</AvatarFallback>
          </Avatar>
        )}
      </motion.div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-black/20">
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/10 bg-black/40 backdrop-blur-md">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-blue-400" />
              <h3 className="font-semibold text-white">Live Bot Conversation</h3>
            </div>
            <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/30">
              <div className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></div>
              Live Demo
            </Badge>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowDetails(!showDetails)}
              className="text-white hover:bg-white/10"
            >
              <Brain className="w-4 h-4 mr-2" />
              {showDetails ? 'Hide' : 'Show'} AI Details
            </Button>
          </div>
        </div>

        {/* Scenario Context */}
        <div className="mt-2 text-sm text-gray-400">
          <span className="capitalize">{scenario.category.replace('_', ' ')}</span> •
          <span className="ml-1">{scenario.name}</span>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {messages.map(renderMessage)}
        </AnimatePresence>

        {/* Typing Indicator */}
        <AnimatePresence>
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="flex gap-3 justify-start"
            >
              <Avatar className="w-10 h-10 border-2 border-blue-500/30">
                <AvatarContent className="bg-blue-600 text-white">
                  <Bot className="w-5 h-5" />
                </AvatarContent>
              </Avatar>
              <div className="bg-white/5 border border-white/10 rounded-2xl px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                  <span className="text-sm text-gray-400">Jorge AI is typing...</span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-white/10 bg-black/40 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Input
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Type your response as the client..."
              className="bg-white/5 border-white/20 text-white placeholder-gray-400 pr-12"
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsListening(!isListening)}
              className={`absolute right-2 top-1/2 transform -translate-y-1/2 ${
                isListening ? 'text-red-400' : 'text-gray-400'
              } hover:bg-white/10`}
            >
              {isListening ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
            </Button>
          </div>

          <Button
            onClick={handleSendMessage}
            disabled={!userInput.trim()}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>

        {/* Quick Responses */}
        <div className="mt-3 flex flex-wrap gap-2">
          {[
            "I'm just testing the market",
            "What's your commission?",
            "I need to think about it",
            "How quickly can you sell?"
          ].map((response, index) => (
            <Button
              key={index}
              variant="outline"
              size="sm"
              onClick={() => setUserInput(response)}
              className="text-xs border-white/20 text-gray-300 hover:bg-white/10"
            >
              "{response}"
            </Button>
          ))}
        </div>

        {/* Demo Instruction */}
        <div className="mt-3 text-xs text-gray-400 text-center">
          {isFullScreen
            ? "Use quick responses above or type your own client responses to see Jorge's confrontational methodology in action"
            : "Interact as a potential client to demonstrate Jorge's qualification process"
          }
        </div>
      </div>
    </div>
  );
}

export default BotConversationDemo;