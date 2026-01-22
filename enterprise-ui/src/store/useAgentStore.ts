
import { create } from 'zustand';

interface BlackboardEntry {
  timestamp: string;
  agent: string;
  key: string;
  value: any;
}

interface AgentState {
  history: BlackboardEntry[];
  thinking: string;
  currentDeltas: Record<string, any>;
  isGenerating: boolean;
  addEntry: (entry: BlackboardEntry) => void;
  setThinking: (thought: string) => void;
  startStreaming: () => void;
}

export const useAgentStore = create<AgentState>((set, get) => ({
  history: [],
  thinking: '',
  currentDeltas: {},
  isGenerating: false,

  addEntry: (entry) => {
    set((state) => ({
      history: [...state.history, entry],
      // If the key is a UI component, update deltas
      currentDeltas: entry.key.startsWith('ui_component_') 
        ? { ...state.currentDeltas, [entry.key]: entry.value }
        : state.currentDeltas,
      // Update thinking if it's a thought key
      thinking: entry.key === 'agent_thought' ? entry.value : state.thinking
    }));
  },

  setThinking: (thought) => set({ thinking: thought }),

  startStreaming: () => {
    set({ isGenerating: true });
    
    const eventSource = new EventSource('/api/agent-ui/stream-ui-updates');
    
    eventSource.onmessage = (event) => {
      const entry = JSON.parse(event.data);
      get().addEntry(entry);
    };

    eventSource.onerror = (err) => {
      console.error('SSE connection failed:', err);
      eventSource.close();
      set({ isGenerating: false });
    };

    return () => eventSource.close();
  }
}));
