import type { InputHTMLAttributes, ReactNode } from 'react';
import styles from './ui.module.css';

export interface IconInputProps extends InputHTMLAttributes<HTMLInputElement> {
  leadingIcon?: ReactNode;
}

export function IconInput({ className = '', leadingIcon, ...props }: IconInputProps) {
  return (
    <label className={`${styles.inputWrap} ${className}`.trim()}>
      {leadingIcon}
      <input className={styles.input} {...props} />
    </label>
  );
}
