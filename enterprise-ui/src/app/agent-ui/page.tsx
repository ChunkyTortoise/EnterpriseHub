"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Card,
  Title,
  Text,
  Flex,
  Button,
  ProgressBar,
  Badge,
  Grid,
  Col,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent
} from "@tremor/react";
import {
  Terminal,
  Code,
  Play,
  CheckCircle2,
  AlertCircle,
  Cpu,
  Layers,
  Eye,
  Copy,
  Sparkles,
  MessageSquare,
  ShieldCheck,
  Zap
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface UIEvent {
  event: string;
  content?: string;
  name?: string;
  code?: string;
  jsx?: string;
  agent?: string;
  data?: any;
  issues?: string[];
  fix?: string;
  status?: string;
  features?: any;
  audio_data?: string;
}

export default function AgentUIPage() {
  const [objective, setObjective] = useState("Executive Dashboard with KPI cards and revenue charts");
  const [isGenerating, setIsGenerating] = useState(false);
  const [useVoice, setVoiceMode] = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState("Hey Claude, build me a high-converting dashboard for my Austin market leads with revenue trends.");
  const [events, setEvents] = useState<UIEvent[]>([]);
  const [components, setComponents] = useState<{name: string, status: string, code?: string, features?: any, feedback?: number}[]>([]);
  const [finalJsx, setFinalJsx] = useState("");
  const [qaStatus, setQaStatus] = useState<"idle" | "capturing" | "verifying" | "passed" | "failed">("idle");
  const [activeTab, setActiveTab] = useState("code");
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [events]);

  const playAudio = (base64Data: string) => {
    if (!base64Data) return;
    
    const audioBlob = b64toBlob(base64Data, "audio/mpeg");
    const audioUrl = URL.createObjectURL(audioBlob);
    
    if (audioRef.current) {
      audioRef.current.src = audioUrl;
      audioRef.current.play();
      setIsPlayingAudio(true);
    }
  };

  const b64toBlob = (b64Data: string, contentType = "", sliceSize = 512) => {
    const byteCharacters = atob(b64Data);
    const byteArrays = [];
    for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
      const slice = byteCharacters.slice(offset, offset + sliceSize);
      const byteNumbers = new Array(slice.length);
      for (let i = 0; i < slice.length; i++) {
        byteNumbers[i] = slice.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      byteArrays.push(byteArray);
    }
    return new Blob(byteArrays, { type: contentType });
  };

  const startGeneration = () => {
    if (!objective.trim() && !useVoice) return;

    // Reset state
    setEvents([]);
    setComponents([]);
    setFinalJsx("");
    setIsGenerating(true);
    setQaStatus("idle");
    setIsPlayingAudio(false);

    const queryParams = new URLSearchParams({
      location_id: "ghl_demo_user"
    });

    if (useVoice) {
      queryParams.append("voice_transcript", voiceTranscript);
    } else {
      queryParams.append("objective", objective);
    }

    const url = `http://localhost:8000/api/agent-ui/stream-ui-generation?${queryParams.toString()}`;

    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.addEventListener("thinking", (e) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, { event: "thinking", content: data.content }]);
    });

    es.addEventListener("critic_feedback", (e) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, { event: "critic", agent: data.agent, content: data.content }]);
    });

    es.addEventListener("engineer_response", (e) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, { event: "engineer", agent: data.agent, content: data.content }]);
    });

    es.addEventListener("architecture_ready", (e) => {
      const data = JSON.parse(e.data);
      const initialComponents = data.data.components.map((c: any) => ({
        name: c.name,
        status: "pending"
      }));
      setComponents(initialComponents);
      setEvents(prev => [...prev, { event: "system", content: "Architecture finalized. Multi-agent swarm deployed." }]);
    });

    es.addEventListener("generating_component", (e) => {
      const data = JSON.parse(e.data);
      setComponents(prev => prev.map(c => 
        c.name === data.name ? { ...c, status: "generating" } : c
      ));
    });

    es.addEventListener("component_ready", (e) => {
      const data = JSON.parse(e.data);
      setComponents(prev => prev.map(c => 
        c.name === data.name ? { ...c, status: "ready", code: data.code } : c
      ));
      // Update preview incrementally
      setFinalJsx(prev => prev + "\n\n" + data.code);
    });

    es.addEventListener("assembly_complete", (e) => {
      const data = JSON.parse(e.data);
      setFinalJsx(data.jsx);
      setEvents(prev => [...prev, { event: "system", content: "Component assembly complete." }]);
    });

    es.addEventListener("visual_qa_check", (e) => {
      const data = JSON.parse(e.data);
      setQaStatus(data.status === "capturing_with_grid" ? "capturing" : "verifying");
    });

    es.addEventListener("visual_feedback", (e) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, { 
        event: "warning", 
        content: `Visual QA found issues: ${data.issues.join(", ")}. Triggering fix: ${data.fix}` 
      }]);
    });

    es.addEventListener("simulation_result", (e) => {
      const data = JSON.parse(e.data);
      setComponents(prev => prev.map(c => 
        c.name === data.name ? { ...c, features: data.features } : c
      ));
      setEvents(prev => [...prev, { 
        event: "simulation", 
        content: `Behavioral ML Prediction for ${data.name}: ${Math.round(data.score * 100)}% conversion. Tips: ${data.tips.join(", ")}` 
      }]);
    });

    es.addEventListener("voice_briefing", (e) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, { event: "system", content: "AI Voice Briefing ready. Playing audio..." }]);
      if (data.audio_data) {
        playAudio(data.audio_data);
      }
    });

    es.addEventListener("final_ui_ready", (e) => {
      const data = JSON.parse(e.data);
      setFinalJsx(data.jsx);
      setQaStatus("passed");
      setIsGenerating(false);
      setEvents(prev => [...prev, { event: "success", content: "Ultimate UI generation successful! Debate closed." }]);
      es.close();
    });

    es.onerror = (err) => {
      console.error("SSE Error:", err);
      setIsGenerating(false);
      es.close();
    };
  };

  const handleFeedback = async (name: string, rating: number) => {
    const comp = components.find(c => c.name === name);
    if (!comp || !comp.features) return;

    try {
      await fetch("http://localhost:8000/api/agent-ui/record-feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          component_id: name,
          user_id: "ghl_demo_user",
          location_id: "ghl_demo_user",
          rating: rating,
          features: comp.features
        })
      });
      
      setComponents(prev => prev.map(c => 
        c.name === name ? { ...c, feedback: rating } : c
      ));
    } catch (err) {
      console.error("Feedback error:", err);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(finalJsx);
    alert("JSX copied to clipboard!");
  };

  return (
    <main className="p-8 bg-slate-950 min-h-screen text-slate-200 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Audio Element for Briefings */}
        <audio 
          ref={audioRef} 
          onEnded={() => setIsPlayingAudio(false)} 
          className="hidden" 
        />
        
        {/* Header */}
        <Flex justifyContent="between" alignItems="center">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-600 rounded-lg">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <Title className="text-3xl font-bold text-white tracking-tight">
                Ultimate UI Swarm Cockpit
              </Title>
            </div>
            <Text className="text-slate-400 mt-1">Multi-agent design debates with real-time visual grounding.</Text>
          </div>
          <div className="flex items-center gap-4">
            {isPlayingAudio && (
              <Badge className="bg-purple-500/10 text-purple-400 border-purple-500/20 px-3 py-1 flex items-center gap-2">
                <div className="flex gap-0.5 items-end h-3">
                  <div className="w-0.5 bg-purple-400 animate-[bounce_1s_infinite]" />
                  <div className="w-0.5 bg-purple-400 animate-[bounce_1.2s_infinite]" />
                  <div className="w-0.5 bg-purple-400 animate-[bounce_0.8s_infinite]" />
                </div>
                Voice Briefing Active
              </Badge>
            )}
            <Badge className="bg-blue-500/10 text-blue-400 border-blue-500/20 px-3 py-1">
              Multi-Agent Debate Active
            </Badge>
            <Badge className="bg-green-500/10 text-green-400 border-green-500/20 px-3 py-1">
              Live Sandbox Sync
            </Badge>
          </div>
        </Flex>

        <Grid numItemsLg={3} className="gap-8">
          {/* Left Column: Control & Status */}
          <Col numItemsLg={1} className="space-y-6">
            <Card className="bg-slate-900 border-slate-800">
              <Flex justifyContent="between" alignItems="center" className="mb-4">
                <Title className="text-slate-100 flex items-center gap-2">
                  <Zap className="h-4 w-4 text-blue-400" />
                  Swarm Control
                </Title>
                <div className="flex items-center gap-2 bg-slate-950 p-1 rounded-lg border border-slate-800">
                  <Button 
                    size="xs" 
                    variant={!useVoice ? "primary" : "light"}
                    onClick={() => setVoiceMode(false)}
                    className="text-[10px] px-2 py-1"
                  >
                    Text
                  </Button>
                  <Button 
                    size="xs" 
                    variant={useVoice ? "primary" : "light"}
                    onClick={() => setVoiceMode(true)}
                    className="text-[10px] px-2 py-1"
                  >
                    Voice
                  </Button>
                </div>
              </Flex>
              
              {!useVoice ? (
                <textarea
                  value={objective}
                  onChange={(e) => setObjective(e.target.value)}
                  disabled={isGenerating}
                  className="w-full h-32 bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-all resize-none"
                  placeholder="Describe the UI you want to build..."
                />
              ) : (
                <div className="space-y-3">
                  <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/20 flex items-center gap-3">
                    <div className="animate-pulse bg-blue-500 h-2 w-2 rounded-full" />
                    <Text className="text-[10px] text-blue-400 font-mono uppercase tracking-tighter">Mock Voice Metadata Active</Text>
                  </div>
                  <textarea
                    value={voiceTranscript}
                    onChange={(e) => setVoiceTranscript(e.target.value)}
                    disabled={isGenerating}
                    className="w-full h-32 bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm focus:ring-2 focus:ring-blue-500 outline-none transition-all resize-none italic"
                    placeholder="Simulate a voice command..."
                  />
                </div>
              )}

              <Button 
                className="w-full mt-4 bg-blue-600 hover:bg-blue-700 py-6 text-lg font-bold rounded-xl shadow-lg shadow-blue-900/20"
                onClick={startGeneration}
                disabled={isGenerating}
                icon={isGenerating ? Cpu : useVoice ? Sparkles : Play}
              >
                {isGenerating ? "Swarm Executing..." : useVoice ? "Trigger Voice-to-UI" : "Ignite Swarm"}
              </Button>
            </Card>

            <Card className="bg-slate-900 border-slate-800">
              <Title className="text-slate-100 mb-4 flex items-center gap-2">
                <Layers className="h-4 w-4 text-blue-400" />
                Component Stack
              </Title>
              <div className="space-y-3">
                {components.length > 0 ? (
                  components.map((comp, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-slate-950 border border-slate-800">
                      <div className="flex items-center gap-3">
                        <Code className="h-4 w-4 text-slate-500" />
                        <Text className="text-sm font-medium">{comp.name}</Text>
                      </div>
                      {comp.status === "ready" ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : comp.status === "generating" ? (
                        <div className="h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <div className="h-2 w-2 rounded-full bg-slate-700" />
                      )}
                    </div>
                  ))
                ) : (
                  <div className="h-24 flex items-center justify-center border border-dashed border-slate-800 rounded-lg">
                    <Text className="text-xs text-slate-600 italic">Waiting for architecture...</Text>
                  </div>
                )}
              </div>
            </Card>

            <Card className="bg-slate-900 border-slate-800">
              <Title className="text-slate-100 mb-4 flex items-center gap-2">
                <Eye className="h-4 w-4 text-blue-400" />
                Visual QA Loop
              </Title>
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-full ${qaStatus === 'passed' ? 'bg-green-500/10' : 'bg-slate-800'}`}>
                  <Eye className={`h-6 w-6 ${qaStatus === 'passed' ? 'text-green-500' : 'text-slate-500'}`} />
                </div>
                <div className="flex-1">
                  <Text className="text-sm font-bold">Status: {qaStatus.toUpperCase()}</Text>
                  <ProgressBar 
                    value={qaStatus === 'passed' ? 100 : isGenerating ? 45 : 0} 
                    color={qaStatus === 'passed' ? 'green' : 'blue'} 
                    className="mt-2" 
                  />
                </div>
              </div>
              {qaStatus === 'capturing' && (
                <div className="mt-4 p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
                  <Text className="text-xs text-blue-400 animate-pulse font-mono text-center">
                    [SYSTEM] Rendering preview with 12x12 visual grid...
                  </Text>
                </div>
              )}
            </Card>
          </Col>

          {/* Right Column: Thought Stream & Sandbox */}
          <Col numItemsLg={2} className="space-y-6">
            <Card className="bg-slate-900 border-slate-800 h-[350px] flex flex-col p-0 overflow-hidden shadow-2xl">
              <div className="p-4 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
                <Flex justifyContent="start" alignItems="center" className="gap-2">
                  <Terminal className="h-4 w-4 text-blue-400" />
                  <Text className="text-sm font-bold text-slate-300 tracking-widest uppercase">Agent Debate Stream</Text>
                </Flex>
                <div className="flex gap-2 items-center">
                   <Text className="text-[10px] text-slate-500 font-bold uppercase">Multi-Agent Protocol v2.0</Text>
                   <div className="h-2 w-2 rounded-full bg-blue-500 animate-pulse shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
                </div>
              </div>
              <div 
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-6 space-y-4 font-mono text-sm"
              >
                <AnimatePresence>
                  {events.map((ev, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className={`flex gap-3 ${ 
                        ev.event === 'critic' ? 'text-amber-400 bg-amber-400/5 p-2 rounded border-l-2 border-amber-500' : 
                        ev.event === 'engineer' ? 'text-blue-400 bg-blue-400/5 p-2 rounded border-l-2 border-blue-500' : 
                        ev.event === 'simulation' ? 'text-emerald-400 bg-emerald-400/5 p-2 rounded border-l-2 border-emerald-500 italic' :
                        ev.event === 'warning' ? 'text-rose-400 bg-rose-400/5 p-2 rounded border-l-2 border-rose-500' :
                        ev.event === 'success' ? 'text-green-400 font-bold' : 'text-slate-400'
                      }`}
                    >
                      <span className="text-slate-600 flex-shrink-0">[{new Date().toLocaleTimeString([], {hour12: false})}]</span>
                      <span className="flex-1">
                        {ev.event === 'thinking' && <span className="text-blue-400 mr-2">💭</span>}
                        {ev.event === 'system' && <span className="text-slate-500 mr-2">⚙️</span>}
                        {ev.event === 'critic' && <span className="font-bold mr-2">⚖️ {ev.agent}:</span>}
                        {ev.event === 'engineer' && <span className="font-bold mr-2">🛠️ {ev.agent}:</span>}
                        {ev.event === 'simulation' && <span className="font-bold mr-2">📈 SIM:</span>}
                        {ev.event === 'warning' && <span className="font-bold mr-2">⚠️ QA:</span>}
                        {ev.content}
                      </span>
                    </motion.div>
                  ))}
                </AnimatePresence>
                {isGenerating && (
                  <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex items-center gap-2 text-blue-400 italic pl-2"
                  >
                    <div className="flex gap-1">
                      <div className="h-1 w-1 bg-blue-400 rounded-full animate-bounce" />
                      <div className="h-1 w-1 bg-blue-400 rounded-full animate-bounce [animation-delay:0.2s]" />
                      <div className="h-1 w-1 bg-blue-400 rounded-full animate-bounce [animation-delay:0.4s]" />
                    </div>
                    <span>Swarm is debating...</span>
                  </motion.div>
                )}
              </div>
            </Card>

            <Card className="bg-slate-900 border-slate-800 flex-1 min-h-[450px] flex flex-col p-0 overflow-hidden shadow-2xl">
              <Tabs defaultValue="preview" className="h-full flex flex-col">
                <div className="p-4 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between">
                  <TabsList className="bg-slate-950 border border-slate-800">
                    <TabsTrigger value="preview" className="text-xs">Live Sandbox</TabsTrigger>
                    <TabsTrigger value="code" className="text-xs">JSX Code</TabsTrigger>
                  </TabsList>
                  <Button 
                    size="xs" 
                    variant="outline" 
                    className="border-slate-700 hover:bg-slate-800 text-slate-400"
                    onClick={copyToClipboard}
                    disabled={!finalJsx}
                    icon={Copy}
                  >
                    Copy JSX
                  </Button>
                </div>
                
                <TabsContent value="code" className="flex-1 bg-slate-950 p-6 overflow-auto custom-scrollbar m-0">
                  {finalJsx ? (
                    <pre className="text-xs font-mono text-blue-300 leading-relaxed">
                      <code>{finalJsx}</code>
                    </pre>
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-slate-700">
                      <Code className="h-12 w-12 mb-4 opacity-20" />
                      <Text className="italic opacity-50">Code will appear here during assembly.</Text>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="preview" className="flex-1 bg-white dark:bg-slate-950 p-0 m-0 relative overflow-hidden">
                  {finalJsx ? (
                    <div className="h-full w-full flex flex-col">
                      <div className="p-4 bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                        <Flex justifyContent="start" className="gap-2">
                           <Eye className="h-3 w-3 text-slate-400" />
                           <Text className="text-[10px] font-bold text-slate-500 uppercase">Interactive Preview Sandbox</Text>
                        </Flex>
                        <Badge className="bg-blue-500/10 text-blue-500 text-[10px]">Auto-Reloading</Badge>
                      </div>
                      <div className="flex-1 p-8 flex items-center justify-center">
                        {/* Simulation of rendered components with motion */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-2xl">
                          {components.filter(c => c.status === 'ready').map((comp, idx) => (
                            <motion.div
                              key={comp.name}
                              initial={{ opacity: 0, scale: 0.9, y: 20 }}
                              animate={{ opacity: 1, scale: 1, y: 0 }}
                              transition={{ duration: 0.5, delay: idx * 0.1 }}
                              className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl shadow-slate-200/50 dark:shadow-none"
                            >
                              <Flex justifyContent="between">
                                <Title className="text-sm font-bold text-slate-900 dark:text-white">{comp.name}</Title>
                                <Sparkles className="h-4 w-4 text-blue-500" />
                              </Flex>
                              <div className="mt-4 h-24 bg-slate-50 dark:bg-slate-950 rounded-lg flex items-center justify-center border border-dashed border-slate-200 dark:border-slate-800">
                                <Text className="text-[10px] text-slate-400 font-mono">Rendered: {comp.name}.tsx</Text>
                              </div>
                              <Flex className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
                                <div className="h-2 w-12 bg-blue-100 dark:bg-blue-900/30 rounded" />
                                <div className="h-2 w-8 bg-slate-100 dark:border-slate-800 rounded ml-2" />
                                <Flex justifyContent="end" className="gap-2 ml-auto">
                                  <Button 
                                    size="xs" 
                                    variant={comp.feedback === 1 ? "primary" : "outline"} 
                                    className="rounded-full p-1"
                                    onClick={() => handleFeedback(comp.name, 1)}
                                  >
                                    👍
                                  </Button>
                                  <Button 
                                    size="xs" 
                                    variant={comp.feedback === -1 ? "secondary" : "outline"} 
                                    className="rounded-full p-1"
                                    onClick={() => handleFeedback(comp.name, -1)}
                                  >
                                    👎
                                  </Button>
                                </Flex>
                              </Flex>
                            </motion.div>
                          ))}
                          {components.filter(c => c.status === 'ready').length === 0 && (
                             <div className="col-span-2 text-center py-20">
                                <Cpu className="h-12 w-12 text-slate-200 mx-auto mb-4 animate-pulse" />
                                <Text className="text-slate-400 italic">Waiting for agents to finalize components...</Text>
                             </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center bg-slate-50 dark:bg-slate-950 text-slate-300 dark:text-slate-800">
                      <Layers className="h-16 w-12 mb-4 opacity-20" />
                      <Text className="italic opacity-50">The swarm must initialize to generate the preview.</Text>
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            </Card>
          </Col>
        </Grid>
      </div>
      
      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #1e293b;
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #334155;
        }
      `}</style>
    </main>
  );
}