"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { TrendingUp, ShieldCheck, Zap, Activity, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-slate-50 text-slate-900 overflow-x-hidden">
      <header className="px-4 lg:px-6 h-16 flex items-center border-b bg-white/80 backdrop-blur-md sticky top-0 z-50">
        <Link className="flex items-center justify-center" href="#">
          <Zap className="h-6 w-6 text-blue-600" />
          <span className="ml-2 text-xl font-bold tracking-tight">Lyrio EnterpriseHub</span>
        </Link>
        <nav className="ml-auto flex gap-4 sm:gap-8">
          <Link className="text-sm font-semibold hover:text-blue-600 transition-colors" href="/jorge">
            Jorge Command Center
          </Link>
          <Link className="text-sm font-semibold hover:text-blue-600 transition-colors" href="/dashboard">
            Intelligence Hub
          </Link>
          <Link className="text-sm font-semibold hover:text-blue-600 transition-colors" href="#">
            Agent Specs
          </Link>
        </nav>
      </header>
      <main className="flex-1">
        <section className="w-full py-24 md:py-32 lg:py-48 relative overflow-hidden bg-white">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(59,130,246,0.05),transparent_70%)]" />
          <div className="container px-4 md:px-6 mx-auto relative z-10">
            <div className="flex flex-col items-center space-y-8 text-center">
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="space-y-4"
              >
                <div className="inline-flex items-center rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-sm font-medium text-blue-600 mb-4">
                  <span className="mr-2">✨</span> Phase 3: Elite Agentic Swarms Live
                </div>
                <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl/none bg-clip-text text-transparent bg-gradient-to-r from-slate-900 via-blue-900 to-slate-900">
                  Real Estate Intelligence,<br />Fully Autonomous.
                </h1>
                <p className="mx-auto max-w-[800px] text-slate-500 md:text-xl lg:text-2xl leading-relaxed">
                  Enterprise-grade agentic workflows for the modern brokerage. Swarm intelligence, predictive matching, and autonomous negotiation at scale.
                </p>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.3, duration: 0.5 }}
                className="flex flex-col sm:flex-row gap-4"
              >
                <Button asChild size="lg" className="h-14 px-8 text-lg bg-blue-600 hover:bg-blue-700 shadow-xl shadow-blue-500/20 group">
                  <Link href="/jorge" className="flex items-center">
                    Enter Jorge Command Center
                    <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                  </Link>
                </Button>
                <Button variant="outline" size="lg" className="h-14 px-8 text-lg border-slate-200">
                  View Swarm Documentation
                </Button>
              </motion.div>
            </div>
          </div>
        </section>
        
        <section className="w-full py-24 bg-slate-50">
          <div className="container px-4 md:px-6 mx-auto">
            <div className="grid gap-12 sm:grid-cols-2 lg:grid-cols-3">
              {[
                {
                  icon: <Activity className="h-12 w-12 text-blue-600" />,
                  title: "Swarm Intelligence",
                  desc: "Orchestrate 5+ specialized agents coordinating across SMS, Email, and Voice to close deals 24/7."
                },
                {
                  icon: <TrendingUp className="h-12 w-12 text-blue-600" />,
                  title: "Predictive Analytics",
                  desc: "Claude-powered lead scoring and market trend prediction with 92% accuracy on conversion signals."
                },
                {
                  icon: <ShieldCheck className="h-12 w-12 text-blue-600" />,
                  title: "Enterprise Governance",
                  desc: "Complete observability, policy-based guardrails, and secure multi-tenant isolation for large teams."
                }
              ].map((feature, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.1 }}
                  className="flex flex-col items-start space-y-4 border border-slate-200 p-8 rounded-2xl bg-white shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="p-3 rounded-xl bg-blue-50">{feature.icon}</div>
                  <h2 className="text-2xl font-bold">{feature.title}</h2>
                  <p className="text-slate-500 leading-relaxed">{feature.desc}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <section className="w-full py-24 bg-blue-600 text-white overflow-hidden">
          <div className="container px-4 md:px-6 mx-auto flex flex-col items-center text-center space-y-8">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl md:text-5xl">Ready to deploy the swarm?</h2>
            <p className="max-w-[600px] text-blue-100 md:text-xl">
              Integrate with GoHighLevel in minutes and start converting cold leads into hot appointments autonomously.
            </p>
            <Button size="lg" className="bg-white text-blue-600 hover:bg-blue-50 h-14 px-10 text-lg font-bold">
              Get Started with Lyrio
            </Button>
          </div>
        </section>
      </main>
      <footer className="flex flex-col gap-2 sm:flex-row py-8 w-full shrink-0 items-center px-4 md:px-6 border-t bg-white text-slate-500">
        <p className="text-sm">© 2026 Lyrio AI. All rights reserved.</p>
        <nav className="sm:ml-auto flex gap-4 sm:gap-8">
          <Link className="text-sm hover:text-blue-600 transition-colors" href="#">
            Terms
          </Link>
          <Link className="text-sm hover:text-blue-600 transition-colors" href="#">
            Privacy
          </Link>
          <Link className="text-sm hover:text-blue-600 transition-colors" href="#">
            Security
          </Link>
        </nav>
      </footer>
    </div>
  );
}
