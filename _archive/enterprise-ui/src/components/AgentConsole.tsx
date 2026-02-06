"use client";

import React, { useState, useRef, useEffect } from "react";
import { Card, Title, Text, Flex, Button } from "@tremor/react";
import { Terminal, Send, Zap, Shield, Cpu, Terminal as TerminalIcon } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Message {
  id: string;
  sender: "user" | "swarm" | "system";
  text: string;
  timestamp: Date;
}

export function AgentConsole() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      sender: "system",
      text: "Elite Agentic Swarm Console Initialized. Ready for commands.",
      timestamp: new Date(),
    },
  ]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchThoughts = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/agent-sync/state');
        const data = await response.json();
        
        if (data.recent_thoughts) {
          const formattedThoughts: Message[] = data.recent_thoughts.map((t: any, idx: number) => ({
            id: `thought-${idx}`,
            sender: t.agent.toLowerCase().includes('bot') ? 'swarm' : 'system',
            text: `[${t.agent}] ${t.task}`,
            timestamp: new Date(t.timestamp)
          }));
          
          setMessages(prev => {
            // Only update if we have new thoughts
            const lastPrev = prev.filter(m => m.sender !== 'user').length > 0 ? prev.filter(m => m.sender !== 'user')[0].id : '';
            const lastNew = formattedThoughts.length > 0 ? formattedThoughts[0].id : '';
            
            if (lastNew !== lastPrev) {
              // Merge user messages with new system thoughts
              const userMsgs = prev.filter(m => m.sender === 'user');
              return [...userMsgs, ...formattedThoughts].sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());
            }
            return prev;
          });
        }
      } catch (err) {
        console.error("Sync Error:", err);
      }
    };

    const interval = setInterval(fetchThoughts, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    // Call the API to record the thought/command
    try {
      await fetch(`http://localhost:8000/api/agent-sync/thought?agent_id=User&thought=${encodeURIComponent(input)}&status=Success`, { method: 'POST' });
      
      // Simulate swarm response
      setTimeout(() => {
        const swarmMsg: Message = {
          id: (Date.now() + 1).toString(),
          sender: "swarm",
          text: `Acknowledge: "${input}". Reconfiguring swarm parameters and deploying sub-agents to execute.`,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, swarmMsg]);
      }, 1000);
    } catch (err) {
      console.error("Failed to send command to swarm:", err);
    }
  };

  return (
    <Card className="h-[600px] flex flex-col p-0 overflow-hidden border-slate-800 bg-slate-950 text-slate-300 shadow-2xl">
      <div className="p-4 border-b border-slate-800 bg-slate-900 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TerminalIcon className="h-5 w-5 text-blue-400" />
          <Title className="text-slate-100 text-lg">Swarm Command Console</Title>
        </div>
        <div className="flex gap-2">
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <Text className="text-xs text-slate-500 uppercase tracking-widest font-bold">Encrypted Link Active</Text>
        </div>
      </div>

      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 space-y-4 font-mono text-sm scrollbar-thin scrollbar-thumb-slate-800"
      >
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className={`flex flex-col ${
                msg.sender === "user" ? "items-end" : "items-start"
              }`}
            >
              <div className={`max-w-[80%] rounded-lg p-3 ${
                msg.sender === "user" 
                  ? "bg-blue-600 text-white" 
                  : msg.sender === "system"
                  ? "bg-slate-800 text-blue-400 border border-blue-900/50"
                  : "bg-slate-900 text-slate-300 border border-slate-800"
              }`}>
                <div className="flex items-center gap-2 mb-1">
                  {msg.sender === "swarm" && <Zap className="h-3 w-3 text-amber-400" />}
                  {msg.sender === "system" && <Shield className="h-3 w-3 text-blue-400" />}
                  {msg.sender === "user" && <Cpu className="h-3 w-3 text-blue-200" />}
                  <span className="text-[10px] uppercase font-bold opacity-50">
                    {msg.sender} • {msg.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                <p className="leading-relaxed">{msg.text}</p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      <div className="p-4 border-t border-slate-800 bg-slate-900">
        <div className="relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Execute swarm command..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg py-3 px-4 pr-12 text-slate-100 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all placeholder:text-slate-600"
          />
          <button
            onClick={handleSend}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-blue-500 hover:text-blue-400 transition-colors"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
        <div className="mt-3 flex gap-4">
          <button className="text-[10px] uppercase font-bold text-slate-500 hover:text-blue-400 transition-colors">/status</button>
          <button className="text-[10px] uppercase font-bold text-slate-500 hover:text-blue-400 transition-colors">/reboot-all</button>
          <button className="text-[10px] uppercase font-bold text-slate-500 hover:text-blue-400 transition-colors">/logs</button>
          <button className="text-[10px] uppercase font-bold text-slate-500 hover:text-blue-400 transition-colors">/flush-cache</button>
        </div>
      </div>
    </Card>
  );
}
