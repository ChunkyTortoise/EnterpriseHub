'use client'

import * as React from 'react'
import { useRouter } from 'next/navigation'
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from 'cmdk'
import {
  Settings,
  Bot,
  Zap,
  TrendingUp,
  Target,
  Activity,
  Brain,
  BarChart3
} from 'lucide-react'

export function CommandMenu() {
  const [open, setOpen] = React.useState(false)
  const router = useRouter()

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
      }
    }

    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  const runCommand = React.useCallback((command: () => void) => {
    setOpen(false)
    command()
  }, [])

  return (
    <>
      <div 
        onClick={() => setOpen(true)}
        className="fixed bottom-8 right-8 z-50 flex items-center gap-2 px-3 py-2 bg-jorge-dark/80 backdrop-blur-md border border-white/10 rounded-xl cursor-pointer hover:bg-white/5 transition-all group shadow-2xl"
      >
        <div className="flex items-center gap-1.5">
          <kbd className="pointer-events-none h-5 select-none items-center gap-1 rounded border border-white/20 bg-white/5 px-1.5 font-mono text-[10px] font-medium text-gray-400 opacity-100 flex">
            <span className="text-xs">⌘</span>K
          </kbd>
          <span className="text-[10px] font-bold jorge-code text-gray-400 group-hover:text-blue-400 transition-colors uppercase tracking-widest">Command</span>
        </div>
      </div>

      <CommandDialog open={open} onOpenChange={setOpen}>
        <div className="jorge-command-wrapper overflow-hidden bg-[#0f0f0f] border border-white/10 shadow-2xl rounded-2xl">
          <CommandInput 
            placeholder="Type a command or search..." 
            className="w-full bg-transparent p-4 text-white outline-none border-b border-white/5 font-medium placeholder:text-gray-600"
          />
          <CommandList className="max-h-[400px] overflow-y-auto p-2 scrollbar-thin">
            <CommandEmpty className="p-4 text-sm text-gray-500 text-center">No results found.</CommandEmpty>
            
            <CommandGroup heading="Platform" className="px-2 py-3">
              <div className="text-[10px] text-gray-500 font-mono uppercase tracking-[0.2em] mb-2 px-2">Navigation</div>
              <CommandItem 
                onSelect={() => runCommand(() => router.push('/jorge'))}
                className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer aria-selected:bg-white/10 transition-colors"
              >
                <div className="p-1.5 bg-blue-500/10 rounded-md text-blue-400">
                  <Bot size={16} />
                </div>
                <span className="text-sm font-medium text-gray-300">Jorge Dashboard</span>
                <span className="text-[10px] text-gray-600 font-mono">G D</span>
              </CommandItem>
              
              <CommandItem
                onSelect={() => runCommand(() => router.push('/executive-dashboard'))}
                className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer aria-selected:bg-white/10 transition-colors"
              >
                <div className="p-1.5 bg-purple-500/10 rounded-md text-purple-400">
                  <TrendingUp size={16} />
                </div>
                <span className="text-sm font-medium text-gray-300">Executive Overview</span>
                <span className="text-[10px] text-gray-600 font-mono">G E</span>
              </CommandItem>

              <CommandItem
                onSelect={() => runCommand(() => router.push('/intelligence'))}
                className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer aria-selected:bg-white/10 transition-colors"
              >
                <div className="p-1.5 bg-blue-500/10 rounded-md text-blue-400">
                  <Brain size={16} />
                </div>
                <span className="text-sm font-medium text-gray-300">Business Intelligence</span>
                <span className="text-[10px] text-gray-600 font-mono bg-amber-500/10 text-amber-400 px-1.5 rounded">PHASE 7</span>
              </CommandItem>

              <CommandItem
                onSelect={() => runCommand(() => router.push('/bi-dashboard'))}
                className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer aria-selected:bg-white/10 transition-colors"
              >
                <div className="p-1.5 bg-emerald-500/10 rounded-md text-emerald-400">
                  <BarChart3 size={16} />
                </div>
                <span className="text-sm font-medium text-gray-300">Advanced BI Dashboard</span>
                <span className="text-[10px] text-gray-600 font-mono bg-emerald-500/10 text-emerald-400 px-1.5 rounded">NEW</span>
              </CommandItem>
            </CommandGroup>

            <CommandSeparator className="h-px bg-white/5 my-2" />

            <CommandGroup heading="Lead Intelligence" className="px-2 py-3">
              <div className="text-[10px] text-gray-500 font-mono uppercase tracking-[0.2em] mb-2 px-2">Analytics</div>
              <CommandItem className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer aria-selected:bg-white/10 transition-colors">
                <div className="p-1.5 bg-jorge-glow/10 rounded-md text-jorge-glow">
                  <Target size={16} />
                </div>
                <span className="text-sm font-medium text-gray-300">Lead Heatmap</span>
              </CommandItem>
              <CommandItem className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer aria-selected:bg-white/10 transition-colors">
                <div className="p-1.5 bg-jorge-gold/10 rounded-md text-jorge-gold">
                  <Zap size={16} />
                </div>
                <span className="text-sm font-medium text-gray-300">Run SHAP Analysis</span>
              </CommandItem>
            </CommandGroup>

            <CommandSeparator className="h-px bg-white/5 my-2" />

            <CommandGroup heading="Settings" className="px-2 py-3">
              <div className="text-[10px] text-gray-500 font-mono uppercase tracking-[0.2em] mb-2 px-2">System</div>
              <CommandItem className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer aria-selected:bg-white/10 transition-colors">
                <div className="p-1.5 bg-gray-500/10 rounded-md text-gray-400">
                  <Settings size={16} />
                </div>
                <span className="text-sm font-medium text-gray-300">Platform Settings</span>
              </CommandItem>
              <CommandItem className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer aria-selected:bg-white/10 transition-colors">
                <div className="p-1.5 bg-green-500/10 rounded-md text-green-400">
                  <Activity size={16} />
                </div>
                <span className="text-sm font-medium text-gray-300">System Health</span>
              </CommandItem>
            </CommandGroup>
          </CommandList>
        </div>
      </CommandDialog>

      <style jsx global>{`
        .jorge-command-wrapper [cmdk-group-heading] {
          display: none;
        }
      `}</style>
    </>
  )
}
