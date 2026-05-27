import styles from './ui.module.css';

export function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.statPill}>
      <span className={styles.statLabel}>{label}</span>
      <strong className={styles.statValue}>{value}</strong>
    </div>
  );
}
