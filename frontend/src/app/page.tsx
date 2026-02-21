'use client';

import { useMemo, useState } from 'react';
import {
  AlertTriangle,
  Bot,
  Building2,
  Loader2,
  Send,
  Sparkles,
  User,
  WandSparkles,
} from 'lucide-react';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { IconInput } from '../components/ui/IconInput';
import { InlineAlert } from '../components/ui/InlineAlert';
import { SectionHeader } from '../components/ui/SectionHeader';
import { StatPill } from '../components/ui/StatPill';
import { TopNav } from '../components/ui/TopNav';
import styles from './page.module.css';

type ViewState = 'active' | 'loading' | 'error' | 'empty';

const seededMessages = [
  {
    id: 'm1',
    role: 'bot' as const,
    title: 'Signal Snapshot',
    text: "Rancho Cucamonga inventory is tightening in 3BR segments. Lead #402 has 87% seller-intent probability.",
    time: '2:14 PM',
  },
  {
    id: 'm2',
    role: 'user' as const,
    title: 'Operator Instruction',
    text: 'Prioritize high-equity owners with permit activity in the last 60 days.',
    time: '2:15 PM',
  },
  {
    id: 'm3',
    role: 'bot' as const,
    title: 'Action Drafted',
    text: 'Drafted outreach for 12 high-confidence leads. Ready to send to Jorge for approval.',
    time: '2:16 PM',
  },
];

const quickActions = ['Generate pitch', 'Qualify lead', 'Draft SMS follow-up', 'Re-score lead cluster'];

export default function Dashboard() {
  const [viewState, setViewState] = useState<ViewState>('active');
  const [prompt, setPrompt] = useState('');

  const messages = useMemo(() => (viewState === 'empty' ? [] : seededMessages), [viewState]);

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
              <p className={styles.brandSubtitle}>Premium War Room</p>
            </div>
          </div>
        }
        right={
          <div className={styles.topNavStats}>
            <StatPill label="AI Health" value="97%" />
            <StatPill label="Queue" value="12 leads" />
            <Badge variant="success">Live Agent Sync</Badge>
          </div>
        }
      />

      <main className={styles.shell}>
        <div className={styles.layout}>
          <Card variant="surface" className={styles.panel}>
            <SectionHeader title="Workspaces" subtitle="Active operating lanes" />
            <div className={styles.workspaceList}>
              {['War Room', 'Market Intelligence', 'Follow-up Studio', 'Compliance'].map((item, index) => (
                <button
                  key={item}
                  className={`${styles.workspaceItem} ${index === 0 ? styles.workspaceItemActive : ''}`.trim()}
                >
                  {item}
                </button>
              ))}
            </div>

            <div className={styles.statePicker}>
              <p className={styles.statePickerLabel}>Screen State Demo</p>
              <div className={styles.statePickerActions}>
                <Button variant="ghost" onClick={() => setViewState('active')}>Active</Button>
                <Button variant="ghost" onClick={() => setViewState('loading')}>Loading</Button>
                <Button variant="ghost" onClick={() => setViewState('error')}>Error</Button>
                <Button variant="ghost" onClick={() => setViewState('empty')}>Empty</Button>
              </div>
            </div>
          </Card>

          <section className={styles.streamSection}>
            <Card variant="elevated" className={styles.streamPanel}>
              <SectionHeader
                title="Agent Stream"
                subtitle="Prioritized interactions for Jorge"
                action={<Badge variant="primary">Session 04</Badge>}
              />

              <div className={styles.streamBody}>
                {viewState === 'loading' ? (
                  <InlineAlert
                    title="Loading stream"
                    body="Pulling latest lead intelligence and outbound drafts."
                    icon={<Loader2 size={16} />}
                  />
                ) : null}

                {viewState === 'error' ? (
                  <InlineAlert
                    variant="error"
                    title="Sync failed"
                    body="Lead scoring service timed out. Retry or continue with cached results."
                    icon={<AlertTriangle size={16} />}
                  />
                ) : null}

                {messages.length === 0 && viewState !== 'loading' && viewState !== 'error' ? (
                  <InlineAlert
                    variant="warning"
                    title="No active items"
                    body="New lead events will populate here when the next workflow triggers."
                    icon={<Sparkles size={16} />}
                  />
                ) : null}

                {messages.map((message) => {
                  const isBot = message.role === 'bot';
                  return (
                    <Card
                      key={message.id}
                      variant="surface"
                      className={`${styles.messageCard} ${isBot ? styles.messageCardBot : ''}`.trim()}
                    >
                      <div className={styles.messageHeader}>
                        <div className={styles.messageTitleWrap}>
                          {isBot ? <Bot size={16} color="var(--lyr-color-primary)" /> : <User size={16} color="var(--lyr-color-text-muted)" />}
                          <strong className={styles.messageTitle}>{message.title}</strong>
                        </div>
                        <span className={styles.messageTime}>{message.time}</span>
                      </div>
                      <p className={styles.messageText}>{message.text}</p>
                    </Card>
                  );
                })}
              </div>

              <footer className={styles.composer}>
                <div className={styles.quickActionRow}>
                  {quickActions.map((label) => (
                    <Badge key={label} variant="neutral" className={styles.quickActionBadge}>
                      {label}
                    </Badge>
                  ))}
                </div>
                <div className={styles.commandRow}>
                  <IconInput
                    leadingIcon={<WandSparkles size={16} />}
                    placeholder="Instruct the agent swarm..."
                    value={prompt}
                    onChange={(event) => setPrompt(event.target.value)}
                    aria-label="Agent command input"
                  />
                  <Button icon={<Send size={16} />} aria-label="Send command">
                    Send
                  </Button>
                </div>
              </footer>
            </Card>
          </section>

          <Card variant="surface" className={styles.contextPanel}>
            <SectionHeader title="Lead Context" subtitle="Live qualification signals" />
            <div className={styles.contextBadges}>
              <Badge variant="success">Lead #402 • High Equity</Badge>
              <Badge variant="primary">Intent Score 87%</Badge>
              <Badge variant="warning">Permit Activity: 18 days ago</Badge>
            </div>
            <Card variant="surface" className={styles.contextCard}>
              <p className={styles.contextTitle}>Suggested next actions</p>
              <ul className={styles.contextList}>
                <li>Send valuation teaser with permit insight.</li>
                <li>Queue follow-up call in 90 minutes.</li>
                <li>Trigger comparative market snapshot.</li>
              </ul>
            </Card>
            <Button variant="secondary">Open full lead dossier</Button>
            <Button variant="primary">Approve draft outreach</Button>
          </Card>
        </div>
      </main>
    </div>
  );
}
