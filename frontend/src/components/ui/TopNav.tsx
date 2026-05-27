import type { ReactNode } from 'react';
import styles from './ui.module.css';

export function TopNav({ left, right }: { left: ReactNode; right?: ReactNode }) {
  return (
    <nav className={styles.topNav} aria-label="Primary">
      <div className={styles.topNavSlot}>{left}</div>
      {right ? <div className={`${styles.topNavSlot} ${styles.topNavRight}`}>{right}</div> : null}
    </nav>
  );
}
