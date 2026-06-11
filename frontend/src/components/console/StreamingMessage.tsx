import { Bot, User } from 'lucide-react';
import { Card } from '../ui/Card';
import type { Telemetry } from '../../lib/demoEngine';
import { TelemetryChips } from './TelemetryChips';
import styles from './console.module.css';

export interface ChatMessage {
  id: string;
  role: 'bot' | 'user';
  title: string;
  text: string;
  time: string;
  streaming: boolean;
  telemetry?: Telemetry;
}

export function StreamingMessage({ message }: { message: ChatMessage }) {
  const isBot = message.role === 'bot';
  return (
    <Card variant="surface" className={`${styles.messageCard} ${isBot ? styles.messageCardBot : ''}`.trim()}>
      <div className={styles.messageHeader}>
        <div className={styles.messageTitleWrap}>
          {isBot ? (
            <Bot size={16} color="var(--lyr-color-primary)" />
          ) : (
            <User size={16} color="var(--lyr-color-text-muted)" />
          )}
          <strong className={styles.messageTitle}>{message.title}</strong>
        </div>
        <span className={styles.messageTime}>{message.time}</span>
      </div>
      <p className={styles.messageText}>
        {message.text}
        {message.streaming ? <span className={styles.cursor} aria-hidden="true" /> : null}
      </p>
      {message.telemetry ? <TelemetryChips data={message.telemetry} /> : null}
    </Card>
  );
}
