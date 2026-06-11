import { ArrowLeft, Database, Gauge, Network } from 'lucide-react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { SectionHeader } from '../../components/ui/SectionHeader';
import { StatPill } from '../../components/ui/StatPill';
import { TopNav } from '../../components/ui/TopNav';
import { cacheTiers, meshAgents, meshTotals } from '../../lib/data/meshSnapshot';
import styles from './page.module.css';

export const metadata: Metadata = {
  title: 'Agent Mesh | Lyrio',
  description: 'Agent mesh roster, cache tiers, and cost governance telemetry',
};

export default function MeshPage() {
  return (
    <div>
      <TopNav
        left={
          <div className={styles.brand}>
            <div className={styles.logoBadge}>
              <Network size={18} />
            </div>
            <div>
              <h1 className={styles.brandTitle}>Agent Mesh &amp; Telemetry</h1>
              <p className={styles.brandSubtitle}>Coordinator roster, cache tiers, cost governance</p>
            </div>
          </div>
        }
        right={
          <div className={styles.navRight}>
            <StatPill label="Hourly budget" value={`$${meshTotals.budgetPerHour}`} />
            <StatPill label="Spend this hour" value={`$${meshTotals.spendThisHour.toFixed(2)}`} />
            <Link href="/">
              <Button variant="ghost" icon={<ArrowLeft size={16} />}>
                Console
              </Button>
            </Link>
          </div>
        }
      />

      <main className={styles.shell}>
        <Card variant="surface" className={styles.section}>
          <SectionHeader
            title="Agent roster"
            subtitle="Mirrors mesh_agent_registry.py — capability-routed, cost-governed"
            action={<Badge variant="primary">{meshAgents.length} agents</Badge>}
          />
          <div className={styles.agentGrid}>
            {meshAgents.map((agent) => (
              <Card key={agent.name} variant="surface" className={styles.agentCard}>
                <div className={styles.agentHeader}>
                  <strong>{agent.name}</strong>
                  <Badge variant={agent.status === 'active' ? 'success' : 'neutral'}>{agent.status}</Badge>
                </div>
                <div className={styles.capabilityRow}>
                  {agent.capabilities.map((capability) => (
                    <Badge key={capability} variant="neutral">
                      {capability}
                    </Badge>
                  ))}
                </div>
                <div className={styles.agentStats}>
                  <span>{agent.tasksToday} tasks today</span>
                  <span>{agent.avgLatencyMs}ms avg</span>
                  <span>${agent.costToday.toFixed(2)} cost</span>
                </div>
              </Card>
            ))}
          </div>
        </Card>

        <div className={styles.twoColumn}>
          <Card variant="surface" className={styles.section}>
            <SectionHeader
              title="3-tier response cache"
              subtitle="claude_orchestrator.py — exact, normalized, semantic"
              action={<Database size={16} color="var(--lyr-color-text-muted)" />}
            />
            <div className={styles.cacheList}>
              {cacheTiers.map((tier) => (
                <div key={tier.tier} className={styles.cacheRow}>
                  <div className={styles.cacheLabel}>
                    <strong>{tier.tier}</strong>
                    <span>{tier.description}</span>
                  </div>
                  <div className={styles.cacheBarTrack}>
                    <div className={styles.cacheBarFill} style={{ width: `${tier.hitRate * 100}%` }} />
                  </div>
                  <div className={styles.cacheMeta}>
                    <span>{Math.round(tier.hitRate * 100)}% hit</span>
                    <span>{tier.avgLatencyMs}ms</span>
                    <Badge variant={tier.measured ? 'success' : 'warning'}>
                      {tier.measured ? 'measured' : 'modeled'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
            <p className={styles.footnote}>
              L1 hit rate measured live (seed 42, benchmarks/results/cache_live_2026-05-27.json). L2/L3 are modeled
              targets — labeled to keep the numbers honest.
            </p>
          </Card>

          <Card variant="surface" className={styles.section}>
            <SectionHeader
              title="Cost governance"
              subtitle="agent_mesh_coordinator.py — budget gates and shutdown"
              action={<Gauge size={16} color="var(--lyr-color-text-muted)" />}
            />
            <div className={styles.governanceList}>
              <div className={styles.governanceRow}>
                <span>Hourly budget gate</span>
                <Badge variant="primary">${meshTotals.budgetPerHour}/hr</Badge>
              </div>
              <div className={styles.governanceRow}>
                <span>Emergency shutdown</span>
                <Badge variant="warning">${meshTotals.emergencyShutdownAt}/hr</Badge>
              </div>
              <div className={styles.governanceRow}>
                <span>Tokens saved by cache today</span>
                <Badge variant="success">{meshTotals.tokensSavedToday.toLocaleString()}</Badge>
              </div>
            </div>
            <p className={styles.footnote}>
              Every task is admitted through a budget check before routing; the coordinator records per-agent cost and
              shuts the mesh down at the hard ceiling. Audit trail in docs/adr/0004 and 0011.
            </p>
          </Card>
        </div>
      </main>
    </div>
  );
}
