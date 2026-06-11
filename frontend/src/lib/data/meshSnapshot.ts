/**
 * Canned mesh snapshot for replay mode. Agent roster mirrors
 * ghl_real_estate_ai/services/mesh_agent_registry.py; cache numbers come from
 * benchmarks/results/cache_live_2026-05-27.json (L1 measured live, L2/L3 modeled).
 */

export interface MeshAgentSnapshot {
  name: string;
  capabilities: string[];
  status: 'active' | 'idle';
  tasksToday: number;
  avgLatencyMs: number;
  costToday: number;
}

export const meshAgents: MeshAgentSnapshot[] = [
  {
    name: 'Jorge Seller Bot',
    capabilities: ['lead_qualification', 'conversation_analysis'],
    status: 'active',
    tasksToday: 34,
    avgLatencyMs: 1067,
    costToday: 0.41,
  },
  {
    name: 'Lead Lifecycle Bot',
    capabilities: ['followup_automation', 'voice_interaction'],
    status: 'active',
    tasksToday: 58,
    avgLatencyMs: 423,
    costToday: 0.22,
  },
  {
    name: 'Intent Decoder',
    capabilities: ['conversation_analysis'],
    status: 'active',
    tasksToday: 92,
    avgLatencyMs: 187,
    costToday: 0.17,
  },
  {
    name: 'Conversation Intelligence Service',
    capabilities: ['conversation_analysis', 'market_intelligence'],
    status: 'idle',
    tasksToday: 21,
    avgLatencyMs: 512,
    costToday: 0.09,
  },
  {
    name: 'Enhanced Property Matcher',
    capabilities: ['property_matching', 'market_intelligence'],
    status: 'active',
    tasksToday: 17,
    avgLatencyMs: 1490,
    costToday: 0.13,
  },
  {
    name: 'Ghost Followup Engine',
    capabilities: ['followup_automation'],
    status: 'idle',
    tasksToday: 44,
    avgLatencyMs: 95,
    costToday: 0.04,
  },
  {
    name: 'ML Analytics Engine',
    capabilities: ['conversation_analysis', 'market_intelligence'],
    status: 'idle',
    tasksToday: 12,
    avgLatencyMs: 233,
    costToday: 0.02,
  },
];

export interface CacheTierSnapshot {
  tier: 'L1' | 'L2' | 'L3';
  description: string;
  hitRate: number;
  avgLatencyMs: number;
  measured: boolean;
}

export const cacheTiers: CacheTierSnapshot[] = [
  { tier: 'L1', description: 'In-memory exact match', hitRate: 0.908, avgLatencyMs: 3, measured: true },
  { tier: 'L2', description: 'Redis normalized prompt', hitRate: 0.62, avgLatencyMs: 12, measured: false },
  { tier: 'L3', description: 'Redis semantic similarity', hitRate: 0.31, avgLatencyMs: 26, measured: false },
];

export const meshTotals = {
  budgetPerHour: 50,
  spendThisHour: 1.08,
  emergencyShutdownAt: 100,
  tokensSavedToday: 84_312,
};
