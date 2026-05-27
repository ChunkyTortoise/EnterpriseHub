import type { HTMLAttributes } from 'react';
import styles from './ui.module.css';

type CardVariant = 'surface' | 'elevated';

const variantClass: Record<CardVariant, string> = {
  surface: styles.cardSurface,
  elevated: styles.cardElevated,
};

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
}

export function Card({ children, className = '', variant = 'surface', ...props }: CardProps) {
  return (
    <div className={`${styles.card} ${variantClass[variant]} ${className}`.trim()} {...props}>
      {children}
    </div>
  );
}
