import type { HTMLAttributes } from 'react';
import styles from './ui.module.css';

type BadgeVariant = 'primary' | 'success' | 'warning' | 'neutral';

const variantClass: Record<BadgeVariant, string> = {
  primary: styles.badgePrimary,
  success: styles.badgeSuccess,
  warning: styles.badgeWarning,
  neutral: styles.badgeNeutral,
};

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

export function Badge({ children, className = '', variant = 'neutral', ...props }: BadgeProps) {
  return (
    <span className={`${styles.badge} ${variantClass[variant]} ${className}`.trim()} {...props}>
      {children}
    </span>
  );
}
