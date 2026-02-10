"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  TrendingUp, ShieldCheck, Zap, Activity, ArrowRight, Bot, Crown,
  Brain, Users, Target, Eye, Route, Building, Star, CheckCircle2,
  Sparkles, Globe, BarChart3, MessageSquare
} from "lucide-react";
import { motion } from "framer-motion";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-[#0f0f0f] text-white overflow-x-hidden">
      <header className="px-4 lg:px-6 h-16 flex items-center border-b border-white/10 bg-black/40 backdrop-blur-md sticky top-0 z-50">
        <Link className="flex items-center justify-center" href="#">
          <div className="p-2 bg-blue-600/10 rounded-lg border border-blue-500/20">
            <Crown className="h-6 w-6 text-blue-500" />
          </div>
          <span className="ml-2 text-xl font-bold tracking-tight text-white">Jorge's AI Empire</span>
        </Link>
        <nav className="ml-auto flex gap-4 sm:gap-8">
          <Link className="text-sm font-semibold hover:text-blue-400 transition-colors text-gray-300" href="/agents">
            Agent Ecosystem
          </Link>
          <Link className="text-sm font-semibold hover:text-purple-400 transition-colors text-gray-300" href="/concierge">
            Claude Concierge
          </Link>
          <Link className="text-sm font-semibold hover:text-green-400 transition-colors text-gray-300" href="/intelligence">
            Property Intelligence
          </Link>
          <Link className="text-sm font-semibold hover:text-yellow-400 transition-colors text-gray-300" href="/journey">
            Customer Journeys
          </Link>
          <Link className="text-sm font-semibold hover:text-blue-300 transition-colors text-gray-300" href="/proof-metrics">
            Proof & Metrics
          </Link>
        </nav>
      </header>
      <main className="flex-1">
        {/* Hero Section */}
        <section className="w-full py-24 md:py-32 lg:py-48 relative overflow-hidden bg-gradient-to-b from-[#0f0f0f] to-[#1a1a1a]">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_40%,rgba(59,130,246,0.1),transparent_70%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,rgba(168,85,247,0.1),transparent_70%)]" />
          <div className="container px-4 md:px-6 mx-auto relative z-10">
            <div className="flex flex-col items-center space-y-8 text-center">
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="space-y-6"
              >
                <div className="inline-flex items-center rounded-full border border-green-500/20 bg-green-500/10 px-4 py-2 text-sm font-medium text-green-400 mb-6">
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  Track 1 & 2 Complete: 43+ Agent Ecosystem Live
                </div>
                <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl/none bg-clip-text text-transparent bg-gradient-to-r from-white via-blue-400 to-purple-400">
                  Jorge's AI Empire<br />
                  <span className="text-blue-400">43+ Specialized Agents</span>
                </h1>
                <p className="mx-auto max-w-[900px] text-gray-400 md:text-xl lg:text-2xl leading-relaxed">
                  The most sophisticated real estate AI ecosystem ever built. Omnipresent Claude Concierge,
                  investment-grade property intelligence, and seamless multi-agent coordination.
                </p>
              </motion.div>

              {/* Agent Stats */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3, duration: 0.6 }}
                className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full max-w-4xl"
              >
                {[
                  { label: "Total Agents", value: "43+", icon: <Bot className="w-6 h-6" />, color: "text-blue-400" },
                  { label: "Intelligence Levels", value: "4", icon: <Brain className="w-6 h-6" />, color: "text-purple-400" },
                  { label: "Coordination Types", value: "Real-time", icon: <Activity className="w-6 h-6" />, color: "text-green-400" },
                  { label: "Platform Coverage", value: "100%", icon: <Eye className="w-6 h-6" />, color: "text-yellow-400" }
                ].map((stat, index) => (
                  <Card key={index} className="bg-white/5 border-white/10">
                    <CardContent className="p-4 text-center">
                      <div className={`flex justify-center mb-2 ${stat.color}`}>
                        {stat.icon}
                      </div>
                      <div className="text-2xl font-bold text-white">{stat.value}</div>
                      <div className="text-xs text-gray-400">{stat.label}</div>
                    </CardContent>
                  </Card>
                ))}
              </motion.div>

              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.5, duration: 0.5 }}
                className="flex flex-col sm:flex-row gap-4"
              >
                <Button asChild size="lg" className="h-14 px-8 text-lg bg-blue-600 hover:bg-blue-700 shadow-xl shadow-blue-500/20 group">
                  <Link href="/agents" className="flex items-center">
                    <Bot className="mr-2 w-5 h-5" />
                    Explore Agent Ecosystem
                    <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                  </Link>
                </Button>
                <Button asChild variant="outline" size="lg" className="h-14 px-8 text-lg border-white/20 text-white hover:bg-white/10">
                  <Link href="/concierge" className="flex items-center">
                    <Sparkles className="mr-2 w-5 h-5" />
                    Launch Claude Concierge
                  </Link>
                </Button>
              </motion.div>
            </div>
          </div>
        </section>

        {/* Advanced Agent Showcase */}
        <section className="w-full py-24 bg-[#1a1a1a]">
          <div className="container px-4 md:px-6 mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                Advanced Intelligence Agents
              </h2>
              <p className="text-gray-400 text-lg max-w-3xl mx-auto">
                Enterprise-grade AI agents with specialized intelligence levels and seamless coordination
              </p>
            </div>

            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
              {[
                {
                  icon: <Sparkles className="h-12 w-12 text-purple-500" />,
                  title: "Claude Concierge",
                  subtitle: "Omnipresent AI Guide",
                  desc: "Platform-wide intelligence with complete 43+ agent awareness and proactive assistance",
                  color: "purple",
                  link: "/concierge"
                },
                {
                  icon: <Building className="h-12 w-12 text-green-500" />,
                  title: "Property Intelligence",
                  subtitle: "Investment-Grade Analysis",
                  desc: "Institutional-level property analysis with 4-tier intelligence and ROI optimization",
                  color: "green",
                  link: "/intelligence"
                },
                {
                  icon: <Route className="h-12 w-12 text-blue-500" />,
                  title: "Journey Orchestrator",
                  subtitle: "Experience Coordinator",
                  desc: "End-to-end customer journey management with smart agent handoffs and analytics",
                  color: "blue",
                  link: "/journey"
                },
                {
                  icon: <Crown className="h-12 w-12 text-yellow-500" />,
                  title: "Enhanced Jorge",
                  subtitle: "Adaptive Qualification",
                  desc: "Real-time question adaptation with FRS/PCS scoring and confrontational methodology",
                  color: "yellow",
                  link: "/jorge"
                }
              ].map((agent, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.1 }}
                  className="group cursor-pointer"
                >
                  <Link href={agent.link}>
                    <Card className="h-full bg-white/5 border-white/10 hover:border-white/20 transition-all group-hover:scale-105">
                      <CardHeader className="text-center">
                        <div className={`p-4 rounded-2xl bg-${agent.color}-500/10 border border-${agent.color}-500/20 mx-auto w-fit mb-4 group-hover:shadow-[0_0_20px_rgba(168,85,247,0.3)] transition-all`}>
                          {agent.icon}
                        </div>
                        <CardTitle className="text-xl font-bold text-white">{agent.title}</CardTitle>
                        <p className={`text-sm text-${agent.color}-400 font-semibold`}>{agent.subtitle}</p>
                      </CardHeader>
                      <CardContent className="text-center">
                        <p className="text-gray-400 leading-relaxed">{agent.desc}</p>
                        <Button
                          variant="outline"
                          size="sm"
                          className="mt-4 border-white/20 text-white hover:bg-white/10 group-hover:scale-110 transition-all"
                        >
                          Explore <ArrowRight className="w-3 h-3 ml-2" />
                        </Button>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Agent Ecosystem Stats */}
        <section className="w-full py-24 bg-gradient-to-r from-blue-500/10 to-purple-500/10">
          <div className="container px-4 md:px-6 mx-auto">
            <div className="grid gap-8 md:grid-cols-3">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                className="text-center"
              >
                <div className="text-4xl font-bold text-white mb-2">95%</div>
                <div className="text-blue-400 font-semibold mb-2">Test Coverage</div>
                <div className="text-gray-400 text-sm">Comprehensive testing across all agent interactions</div>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.1 }}
                className="text-center"
              >
                <div className="text-4xl font-bold text-white mb-2">&lt;30s</div>
                <div className="text-green-400 font-semibold mb-2">Analysis Time</div>
                <div className="text-gray-400 text-sm">Investment-grade property analysis response time</div>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.2 }}
                className="text-center"
              >
                <div className="text-4xl font-bold text-white mb-2">Real-time</div>
                <div className="text-purple-400 font-semibold mb-2">Coordination</div>
                <div className="text-gray-400 text-sm">Multi-agent handoffs and experience orchestration</div>
              </motion.div>
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="w-full py-24 bg-gradient-to-r from-blue-600 to-purple-600 text-white overflow-hidden relative">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.1),transparent_70%)]" />
          <div className="container px-4 md:px-6 mx-auto flex flex-col items-center text-center space-y-8 relative z-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="space-y-6"
            >
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">
                Jorge's AI Empire is Live
              </h2>
              <p className="max-w-[700px] text-blue-100 md:text-xl">
                43+ specialized agents with omnipresent Claude Concierge, investment-grade property intelligence,
                and seamless customer journey orchestration. Ready for enterprise deployment.
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-4xl">
              <Card className="bg-white/10 border-white/20">
                <CardContent className="p-6 text-center">
                  <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">Track 1 Complete</h3>
                  <p className="text-blue-100 text-sm">Enhanced bot intelligence with real-time adaptation</p>
                </CardContent>
              </Card>
              <Card className="bg-white/10 border-white/20">
                <CardContent className="p-6 text-center">
                  <CheckCircle2 className="w-12 h-12 text-green-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">Track 2 Complete</h3>
                  <p className="text-blue-100 text-sm">Claude Concierge omnipresent intelligence</p>
                </CardContent>
              </Card>
              <Card className="bg-white/10 border-white/20">
                <CardContent className="p-6 text-center">
                  <Star className="w-12 h-12 text-yellow-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-white mb-2">Enterprise Ready</h3>
                  <p className="text-blue-100 text-sm">Production deployment with comprehensive testing</p>
                </CardContent>
              </Card>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <Button asChild size="lg" className="bg-white text-blue-600 hover:bg-blue-50 h-14 px-10 text-lg font-bold group">
                <Link href="/agents" className="flex items-center">
                  <Crown className="mr-2 w-5 h-5" />
                  Enter Jorge's Empire
                  <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="border-white/30 text-white hover:bg-white/10 h-14 px-10 text-lg">
                <Link href="/concierge" className="flex items-center">
                  <Sparkles className="mr-2 w-5 h-5" />
                  Launch Concierge
                </Link>
              </Button>
            </div>
          </div>
        </section>
      </main>
      <footer className="flex flex-col gap-2 sm:flex-row py-8 w-full shrink-0 items-center px-4 md:px-6 border-t border-white/10 bg-black/40 text-gray-400">
        <div className="flex items-center gap-2">
          <Crown className="w-4 h-4 text-blue-500" />
          <p className="text-sm">© 2026 Jorge's AI Empire. All rights reserved.</p>
        </div>
        <nav className="sm:ml-auto flex gap-4 sm:gap-8">
          <Link className="text-sm hover:text-blue-400 transition-colors" href="#">
            Agent Documentation
          </Link>
          <Link className="text-sm hover:text-purple-400 transition-colors" href="#">
            API Reference
          </Link>
          <Link className="text-sm hover:text-green-400 transition-colors" href="#">
            Enterprise Support
          </Link>
        </nav>
      </footer>
    </div>
  );
}
