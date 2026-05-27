import type { ButtonHTMLAttributes, ReactNode } from 'react';
import styles from './ui.module.css';

type ButtonVariant = 'primary' | 'secondary' | 'ghost';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  icon?: ReactNode;
  variant?: ButtonVariant;
}

const variantClass: Record<ButtonVariant, string> = {
  primary: styles.buttonPrimary,
  secondary: styles.buttonSecondary,
  ghost: styles.buttonGhost,
};

export function Button({ children, className = '', icon, type = 'button', variant = 'primary', ...props }: ButtonProps) {
  return (
    <button className={`${styles.button} ${variantClass[variant]} ${className}`.trim()} type={type} {...props}>
      {icon}
      {children}
    </button>
  );
}
