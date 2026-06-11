'use client';

import { Send, WandSparkles } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { IconInput } from '../ui/IconInput';
import {
  ReplaySource,
  SseSource,
  type ChatEvent,
  type ChatEventSource,
  type ExtractedData,
  type HandoffEvent,
} from '../../lib/demoEngine';
import { demoTraces, samplePrompts } from '../../lib/traces';
import type { BackendStatus } from '../../lib/useBackendStatus';
import { HandoffCard } from './HandoffCard';
import { StreamingMessage, type ChatMessage } from './StreamingMessage';
import styles from './console.module.css';

type StreamItem =
  | { kind: 'message'; message: ChatMessage }
  | { kind: 'handoff'; id: string; data: HandoffEvent };

function now(): string {
  return new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

export function ChatStream({
  status,
  initialMessages,
  onContext,
}: {
  status: BackendStatus;
  initialMessages: ChatMessage[];
  onContext: (data: ExtractedData) => void;
}) {
  const [items, setItems] = useState<StreamItem[]>(
    initialMessages.map((message) => ({ kind: 'message', message })),
  );
  const [prompt, setPrompt] = useState('');
  const [busy, setBusy] = useState(false);
  const bodyRef = useRef<HTMLDivElement>(null);
  const sourceRef = useRef<ChatEventSource | null>(null);
  const handoffCounter = useRef(0);
  const lastInput = useRef('');

  const replaySource = useMemo(() => new ReplaySource(demoTraces), []);
  const sseSource = useMemo(() => new SseSource(), []);

  useEffect(() => () => sourceRef.current?.cancel(), []);

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight });
  }, [items]);

  function applyEvent(event: ChatEvent) {
    if (event.type === 'message_start') {
      setItems((prev) => [
        ...prev,
        {
          kind: 'message',
          message: {
            id: event.messageId,
            role: event.role,
            title: event.title,
            text: '',
            time: now(),
            streaming: true,
          },
        },
      ]);
    } else if (event.type === 'token') {
      setItems((prev) =>
        prev.map((item) =>
          item.kind === 'message' && item.message.id === event.messageId
            ? { ...item, message: { ...item.message, text: item.message.text + event.text } }
            : item,
        ),
      );
    } else if (event.type === 'telemetry') {
      setItems((prev) =>
        prev.map((item) =>
          item.kind === 'message' && item.message.id === event.messageId
            ? { ...item, message: { ...item.message, streaming: false, telemetry: event.data } }
            : item,
        ),
      );
    } else if (event.type === 'handoff') {
      handoffCounter.current += 1;
      setItems((prev) => [...prev, { kind: 'handoff', id: `handoff-${handoffCounter.current}`, data: event.data }]);
    } else if (event.type === 'extracted_data') {
      onContext(event.data);
    } else if (event.type === 'done') {
      setBusy(false);
      setItems((prev) =>
        prev.map((item) =>
          item.kind === 'message' ? { ...item, message: { ...item.message, streaming: false } } : item,
        ),
      );
    } else if (event.type === 'error') {
      // Live stream failed mid-flight: replay the same input so the demo never dead-ends.
      sourceRef.current?.cancel();
      sourceRef.current = replaySource;
      replaySource.start(lastInput.current, applyEvent);
    }
  }

  function send(input: string) {
    const trimmed = input.trim();
    if (!trimmed || busy) return;
    lastInput.current = trimmed;
    setPrompt('');
    setBusy(true);
    const source = status === 'live' ? sseSource : replaySource;
    sourceRef.current = source;
    source.start(trimmed, applyEvent);
  }

  return (
    <>
      <div className={styles.streamBody} ref={bodyRef}>
        {items.map((item) =>
          item.kind === 'message' ? (
            <StreamingMessage key={item.message.id} message={item.message} />
          ) : (
            <HandoffCard key={item.id} data={item.data} />
          ),
        )}
      </div>

      <footer className={styles.composer}>
        <p className={styles.composerHint}>
          {status === 'live'
            ? 'Live mode: streaming from the FastAPI backend.'
            : 'Replay mode: recorded sessions with real timing. Try a sample scenario:'}
        </p>
        <div className={styles.quickActionRow}>
          {samplePrompts.map((label) => (
            <button
              key={label}
              type="button"
              className={styles.quickActionBadge}
              onClick={() => send(label)}
              disabled={busy}
            >
              <Badge variant="neutral">{label}</Badge>
            </button>
          ))}
        </div>
        <form
          className={styles.commandRow}
          onSubmit={(event) => {
            event.preventDefault();
            send(prompt);
          }}
        >
          <IconInput
            leadingIcon={<WandSparkles size={16} />}
            placeholder="Instruct the agent swarm..."
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            aria-label="Agent command input"
          />
          <Button type="submit" icon={<Send size={16} />} aria-label="Send command" disabled={busy}>
            Send
          </Button>
        </form>
      </footer>
    </>
  );
}
