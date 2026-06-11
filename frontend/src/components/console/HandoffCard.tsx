import { ArrowRight, GitBranch } from 'lucide-react';
import { Badge } from '../ui/Badge';
import type { HandoffEvent } from '../../lib/demoEngine';
import styles from './console.module.css';

const botLabels: Record<HandoffEvent['from'], string> = {
  lead: 'Lead Intake Bot',
  buyer: 'Buyer Bot',
  seller: 'Seller Bot',
};

export function HandoffCard({ data }: { data: HandoffEvent }) {
  const confidencePct = Math.round(data.confidence * 100);
  const thresholdPct = Math.round(data.threshold * 100);
  return (
    <div className={styles.handoffCard} role="status" aria-label="Bot handoff">
      <div className={styles.handoffHeader}>
        <GitBranch size={15} />
        Bot Handoff — confidence {confidencePct}% (threshold {thresholdPct}%)
      </div>
      <div className={styles.handoffArrow}>
        <span>{botLabels[data.from]}</span>
        <ArrowRight size={14} color="var(--lyr-color-primary)" />
        <span>{botLabels[data.to]}</span>
      </div>
      <div className={styles.confidenceTrack}>
        <div className={styles.confidenceFill} style={{ width: `${confidencePct}%` }} />
        <div className={styles.confidenceThreshold} style={{ left: `${thresholdPct}%` }} />
      </div>
      <div className={styles.confidenceLabels}>
        <span>0%</span>
        <span>threshold {thresholdPct}%</span>
        <span>100%</span>
      </div>
      <p className={styles.handoffReason}>{data.reason}</p>
      <div className={styles.handoffContext}>
        {data.context.map((item) => (
          <Badge key={item} variant="neutral">
            {item}
          </Badge>
        ))}
      </div>
    </div>
  );
}
