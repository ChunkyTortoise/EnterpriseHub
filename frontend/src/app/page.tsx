'use client';

import { useState } from 'react';
import {
  Bot,
  Building2,
  Layers,
  Send,
  User,
  WandSparkles,
} from 'lucide-react';
import Link from 'next/link';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { IconInput } from '../components/ui/IconInput';
import { SectionHeader } from '../components/ui/SectionHeader';
import { StatPill } from '../components/ui/StatPill';
import { TopNav } from '../components/ui/TopNav';
import styles from './page.module.css';

const seededMessages = [
  {
    id: 'm1',
    role: 'bot' as const,
    title: 'Morning Market Briefing',
    text: 'Rancho Cucamonga median price up 2.3% to $749K this week. Avg days on market dropped to 18 — tightest inventory since Q3 2024. Alta Loma and Etiwanda leading demand.',
    time: '7:02 AM',
  },
  {
    id: 'm2',
    role: 'bot' as const,
    title: 'Hot Lead Alert',
    text: 'Maria Gonzalez (Baseline Rd) flagged at 87% seller intent. Recent permit activity 18 days ago, 4BR/3BA, est. equity $280K. Recommend immediate CMA outreach.',
    time: '7:15 AM',
  },
  {
    id: 'm3',
    role: 'user' as const,
    title: 'Operator Instruction',
    text: 'Send Maria the CMA teaser. Prioritize Alta Loma permit owners in the 60-day window.',
    time: '7:18 AM',
  },
  {
    id: 'm4',
    role: 'bot' as const,
    title: 'Actions Completed',
    text: 'CMA teaser sent to Maria Gonzalez via SMS. Identified 9 additional Alta Loma permit owners — outreach queued for your approval.',
    time: '7:19 AM',
  },
  {
    id: 'm5',
    role: 'bot' as const,
    title: 'Buyer Match Found',
    text: 'David Chen — $750K pre-approval, Etiwanda school district preference, 30-day urgency. Matched to 3 active listings. Portal link ready to send.',
    time: '9:41 AM',
  },
  {
    id: 'm6',
    role: 'user' as const,
    title: 'Operator Instruction',
    text: 'Send David the portal link and schedule a showing for Saturday.',
    time: '9:44 AM',
  },
  {
    id: 'm7',
    role: 'bot' as const,
    title: 'Follow-up Reminder',
    text: '3 warm leads have not responded in 72+ hours. Auto-drafted re-engagement SMS ready — review and approve to send.',
    time: '11:30 AM',
  },
  {
    id: 'm8',
    role: 'bot' as const,
    title: 'Pipeline Summary',
    text: '12 active leads tracked today. Total pipeline value: $2.1M. 4 listings pending showing, 2 offers in review. Everything on track.',
    time: '2:16 PM',
  },
];

const quickActions = ['Draft CMA report', 'Qualify new lead', 'Send follow-up SMS', 'Schedule showing'];

export default function Dashboard() {
  const [prompt, setPrompt] = useState('');

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
            <StatPill label="AI Health" value="99.2%" />
            <StatPill label="Active Leads" value="12" />
            <StatPill label="Pipeline" value="$2.1M" />
            <Badge variant="success">All Bots Online</Badge>
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
                action={<Badge variant="primary">Session 04</Badge>}
              />

              <div className={styles.streamBody}>
                {seededMessages.map((message) => {
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
              <Badge variant="success">Maria Gonzalez — Seller Lead</Badge>
              <Badge variant="primary">Intent Score: 87%</Badge>
              <Badge variant="warning">Permit Activity: 18 days ago</Badge>
              <Badge variant="neutral">4BR/3BA · 2,650 sqft</Badge>
              <Badge variant="neutral">Est. Equity: $280K</Badge>
            </div>
            <Card variant="surface" className={styles.contextCard}>
              <p className={styles.contextTitle}>Suggested next actions</p>
              <ul className={styles.contextList}>
                <li>Send CMA teaser with permit insight.</li>
                <li>Highlight neighborhood appreciation trend.</li>
                <li>Schedule follow-up call within 90 minutes.</li>
                <li>Queue market snapshot for comparison.</li>
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
