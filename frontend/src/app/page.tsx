'use client';

import { Building2, FlaskConical, Layers, Network } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { SectionHeader } from '../components/ui/SectionHeader';
import { StatPill } from '../components/ui/StatPill';
import { TopNav } from '../components/ui/TopNav';
import { ChatStream } from '../components/console/ChatStream';
import type { ChatMessage } from '../components/console/StreamingMessage';
import type { ExtractedData } from '../lib/demoEngine';
import { useBackendStatus, type BackendStatus } from '../lib/useBackendStatus';
import styles from './page.module.css';

const seededMessages: ChatMessage[] = [
  {
    id: 'm1',
    role: 'bot',
    title: 'Morning Market Briefing',
    text: 'Rancho Cucamonga median price up 2.3% to $749K this week. Avg days on market dropped to 18 — tightest inventory since Q3 2024. Alta Loma and Etiwanda leading demand.',
    time: '7:02 AM',
    streaming: false,
  },
  {
    id: 'm2',
    role: 'bot',
    title: 'Pipeline Summary',
    text: '12 active leads tracked today. Total pipeline value: $2.1M. 4 listings pending showing, 2 offers in review. Pick a scenario below to watch the bots work.',
    time: '8:16 AM',
    streaming: false,
  },
];

const defaultContext: ExtractedData = {
  leadName: 'No active lead',
  items: [{ label: 'Run a scenario to populate live signals', variant: 'neutral' }],
  nextActions: ['Start with "Qualify new seller lead" to see a bot handoff.'],
};

const statusPill: Record<BackendStatus, { label: string; variant: 'neutral' | 'warning' | 'success' }> = {
  replay: { label: 'Replay Mode', variant: 'neutral' },
  warming: { label: 'Warming Backend…', variant: 'warning' },
  live: { label: 'Live Backend', variant: 'success' },
};

export default function Dashboard() {
  const status = useBackendStatus();
  const [context, setContext] = useState<ExtractedData>(defaultContext);
  const pill = statusPill[status];

  return (
    <div>
      <TopNav
        left={
          <div className={styles.topNavBrand}>
            <div className={styles.logoBadge}>
              <Building2 size={18} />
            </div>
            <div>
              <h1 className={styles.brandTitle}>Lyrio Operator Console</h1>
              <p className={styles.brandSubtitle}>Real Estate AI Command Center</p>
            </div>
          </div>
        }
        right={
          <div className={styles.topNavStats}>
            <StatPill label="Active Leads" value="12" />
            <StatPill label="Pipeline" value="$2.1M" />
            <Badge variant={pill.variant}>{pill.label}</Badge>
            <Link href="/mesh">
              <Button variant="ghost" icon={<Network size={16} />}>
                Agent Mesh
              </Button>
            </Link>
            <Link href="/quality">
              <Button variant="ghost" icon={<FlaskConical size={16} />}>
                Evals
              </Button>
            </Link>
            <Link href="/portal">
              <Button variant="ghost" icon={<Layers size={16} />}>
                Buyer Portal
              </Button>
            </Link>
          </div>
        }
      />

      <main className={styles.shell}>
        <div className={styles.layout}>
          <Card variant="surface" className={styles.panel}>
            <SectionHeader title="Workspaces" subtitle="Your active projects" />
            <div className={styles.workspaceList}>
              {['Lead Pipeline', 'Market Intel', 'Follow-ups', 'Listings'].map((item, index) => (
                <button
                  key={item}
                  className={`${styles.workspaceItem} ${index === 0 ? styles.workspaceItemActive : ''}`.trim()}
                >
                  {item}
                </button>
              ))}
            </div>
          </Card>

          <section className={styles.streamSection}>
            <Card variant="elevated" className={styles.streamPanel}>
              <SectionHeader
                title="Agent Stream"
                subtitle="Prioritized interactions for Jorge"
                action={<Badge variant="primary">Lead → Buyer → Seller</Badge>}
              />
              <ChatStream status={status} initialMessages={seededMessages} onContext={setContext} />
            </Card>
          </section>

          <Card variant="surface" className={styles.contextPanel}>
            <SectionHeader title="Lead Context" subtitle="Extracted live from the conversation" />
            <div className={styles.contextBadges}>
              {context.items.map((item) => (
                <Badge key={item.label} variant={item.variant}>
                  {item.label}
                </Badge>
              ))}
            </div>
            <Card variant="surface" className={styles.contextCard}>
              <p className={styles.contextTitle}>Suggested next actions</p>
              <ul className={styles.contextList}>
                {context.nextActions.map((action) => (
                  <li key={action}>{action}</li>
                ))}
              </ul>
            </Card>
            <Button variant="secondary">Open full lead dossier</Button>
            <Button variant="primary">Approve draft outreach</Button>
          </Card>
        </div>

        <Card variant="surface" className={styles.howItWorks}>
          <SectionHeader title="How this demo works" subtitle="Honest engineering notes" />
          <p className={styles.howItWorksText}>
            This console boots in <strong>Replay Mode</strong>: recorded bot sessions stream back with their real
            timing, handoff decisions, and cache/cost telemetry, so the demo is never broken by a cold backend. In the
            background it pings a FastAPI service on Render&apos;s free tier (cold start ≈50s); when the backend wakes,
            the pill flips to <strong>Live Backend</strong> and messages stream over SSE with genuine Redis cache hits.
            Architecture: Next.js 15 on Vercel → FastAPI + Redis on Render → Claude (Haiku, rate-limited).{' '}
            <a
              className={styles.howItWorksLink}
              href="https://github.com/ChunkyTortoise/EnterpriseHub"
              target="_blank"
              rel="noreferrer"
            >
              Read the source on GitHub
            </a>
            .
          </p>
        </Card>
      </main>
    </div>
  );
}
