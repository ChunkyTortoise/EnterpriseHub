import type { Telemetry } from '../../lib/demoEngine';
import styles from './console.module.css';

function formatCost(costUsd: number): string {
  if (costUsd === 0) return '$0 (cached)';
  return `$${costUsd.toFixed(5)}`;
}

export function TelemetryChips({ data }: { data: Telemetry }) {
  const isHit = data.cacheTier !== 'MISS';
  const cacheClass = isHit ? styles.telemetryChipHit : styles.telemetryChipMiss;
  return (
    <div className={styles.telemetryRow} aria-label="Response telemetry">
      <span className={`${styles.telemetryChip} ${cacheClass}`}>
        {isHit ? `cache ${data.cacheTier} HIT ${data.cacheLatencyMs}ms` : 'cache MISS → Claude'}
      </span>
      {!isHit || data.tokensOut > 0 ? (
        <>
          <span className={styles.telemetryChip}>{data.model}</span>
          <span className={styles.telemetryChip}>
            {data.tokensIn}→{data.tokensOut} tok
          </span>
        </>
      ) : null}
      <span className={styles.telemetryChip}>{formatCost(data.costUsd)}</span>
      <span className={styles.telemetryChip}>{data.latencyMs}ms</span>
    </div>
  );
}
