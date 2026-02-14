'use client'

import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Map as MapIcon, Filter, Layers, Navigation, Info, Search, Target } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface HeatPoint {
  id: string
  x: number
  y: number
  intensity: number // 0 to 1
  label: string
  type: 'hot' | 'warm' | 'cold'
}

export function HeatmapOfOpportunity() {
  const [points, setPoints] = useState<HeatPoint[]>([
    { id: '1', x: 250, y: 150, intensity: 0.9, label: 'Downtown Rancho Cucamonga', type: 'hot' },
    { id: '2', x: 320, y: 220, intensity: 0.7, label: 'East Rancho Cucamonga', type: 'hot' },
    { id: '3', x: 180, y: 180, intensity: 0.5, label: 'Zilker', type: 'warm' },
    { id: '4', x: 400, y: 100, intensity: 0.4, label: 'Mueller', type: 'warm' },
    { id: '5', x: 100, y: 300, intensity: 0.8, label: 'South Lamar', type: 'hot' },
    { id: '6', x: 450, y: 350, intensity: 0.3, label: 'Del Valle', type: 'cold' },
    { id: '7', x: 50, y: 50, intensity: 0.2, label: 'West Lake Hills', type: 'cold' },
  ])

  return (
    <div className="relative w-full aspect-square md:aspect-video bg-[#050505] rounded-2xl border border-white/10 overflow-hidden group">
      {/* Map Background (Stylized SVG) */}
      <svg 
        viewBox="0 0 600 400" 
        className="w-full h-full opacity-30 group-hover:opacity-40 transition-opacity duration-700"
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Stylized Grid */}
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="0.5" strokeOpacity="0.05"/>
          </pattern>
        </defs>
        <rect width="600" height="400" fill="url(#grid)" />
        
        {/* Stylized Roads / Boundaries (Abstracted Rancho Cucamonga-like) */}
        <path d="M0 200 Q 150 180 300 200 T 600 200" stroke="white" strokeWidth="1" strokeOpacity="0.1" />
        <path d="M300 0 L 300 400" stroke="white" strokeWidth="1" strokeOpacity="0.1" />
        <path d="M100 0 Q 120 200 100 400" stroke="white" strokeWidth="0.5" strokeOpacity="0.1" />
        <path d="M500 0 Q 480 200 500 400" stroke="white" strokeWidth="0.5" strokeOpacity="0.1" />
        
        {/* River (Colorado River / Lady Bird Lake) */}
        <path 
          d="M0 250 Q 150 230 300 250 T 600 250" 
          stroke="#0052FF" 
          strokeWidth="4" 
          strokeOpacity="0.2" 
          fill="none" 
        />
      </svg>

      {/* Heat Points Layer */}
      <div className="absolute inset-0 pointer-events-none">
        {points.map((point) => (
          <div 
            key={point.id}
            className="absolute -translate-x-1/2 -translate-y-1/2 pointer-events-auto cursor-pointer group/point"
            style={{ left: `${(point.x / 600) * 100}%`, top: `${(point.y / 400) * 100}%` }}
          >
            {/* Heat Pulse */}
            <motion.div
              animate={{ 
                scale: [1, 1.5, 1],
                opacity: [0.2, 0.5, 0.2]
              }}
              transition={{ 
                duration: 3 / point.intensity, 
                repeat: Infinity,
                ease: "easeInOut"
              }}
              className={cn(
                "absolute -inset-8 rounded-full blur-xl",
                point.type === 'hot' ? 'bg-red-500' : point.type === 'warm' ? 'bg-yellow-500' : 'bg-blue-500'
              )}
            />
            
            {/* Center Point */}
            <div className={cn(
              "relative w-2 h-2 rounded-full border border-white/20",
              point.type === 'hot' ? 'bg-red-400' : point.type === 'warm' ? 'bg-yellow-400' : 'bg-blue-400'
            )} />

            {/* Label (Visible on Hover or for Hot Leads) */}
            <div className={cn(
              "absolute top-4 left-1/2 -translate-x-1/2 opacity-0 group-hover/point:opacity-100 transition-opacity duration-300 pointer-events-none",
              point.intensity > 0.8 && "opacity-60"
            )}>
              <div className="bg-black/80 backdrop-blur-md border border-white/10 px-2 py-1 rounded text-[9px] font-bold text-white whitespace-nowrap jorge-code uppercase tracking-widest">
                {point.label}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Map Controls (Glassmorphism) */}
      <div className="absolute top-4 left-4 flex flex-col gap-2">
        <div className="p-1 bg-black/40 backdrop-blur-xl border border-white/10 rounded-xl flex flex-col gap-1">
          <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 hover:text-white hover:bg-white/5">
            <Layers className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 hover:text-white hover:bg-white/5">
            <Filter className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-blue-400 hover:bg-white/5">
            <Navigation className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="absolute top-4 right-4">
        <div className="px-3 py-1.5 bg-jorge-dark/80 backdrop-blur-xl border border-white/10 rounded-full flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-jorge-glow animate-pulse" />
          <span className="text-[10px] font-bold jorge-code text-gray-300 uppercase tracking-widest">Rancho Cucamonga Market Intelligence</span>
        </div>
      </div>

      {/* Legend / Stats Overlay */}
      <div className="absolute bottom-4 left-4 right-4 flex items-end justify-between pointer-events-none">
        <div className="bg-black/60 backdrop-blur-md border border-white/10 p-3 rounded-xl pointer-events-auto">
          <div className="text-[10px] text-gray-500 font-mono uppercase tracking-widest mb-2">Live Demand Matrix</div>
          <div className="flex gap-4">
            <div className="flex flex-col">
              <span className="text-xl font-black text-white leading-none">84</span>
              <span className="text-[9px] text-red-500 font-bold uppercase mt-1">Hot Leads</span>
            </div>
            <div className="w-px bg-white/10" />
            <div className="flex flex-col">
              <span className="text-xl font-black text-white leading-none">12.4%</span>
              <span className="text-[9px] text-jorge-glow font-bold uppercase mt-1">MoM Growth</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 pointer-events-auto">
          <Button className="bg-jorge-electric hover:bg-blue-600 text-white h-9 px-4 rounded-xl shadow-lg shadow-blue-500/20 jorge-haptic">
            <Search className="w-4 h-4 mr-2" />
            Zoom to Hot Zone
          </Button>
        </div>
      </div>

      {/* Scanline Effect */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.03] bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] bg-[length:100%_2px,3px_100%]" />
    </div>
  )
}
