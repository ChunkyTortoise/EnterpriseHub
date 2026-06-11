export type BotId = 'lead' | 'buyer' | 'seller';

export interface Telemetry {
  cacheTier: 'L1' | 'L2' | 'L3' | 'MISS';
  cacheLatencyMs: number;
  model: string;
  tokensIn: number;
  tokensOut: number;
  costUsd: number;
  latencyMs: number;
}

export interface HandoffEvent {
  from: BotId;
  to: BotId;
  confidence: number;
  threshold: number;
  reason: string;
  context: string[];
}

export interface LeadContextItem {
  label: string;
  variant: 'primary' | 'success' | 'warning' | 'neutral';
}

export interface ExtractedData {
  leadName: string;
  items: LeadContextItem[];
  nextActions: string[];
}

export type ChatEvent =
  | { type: 'message_start'; messageId: string; role: 'bot' | 'user'; bot?: BotId; title: string }
  | { type: 'token'; messageId: string; text: string }
  | { type: 'telemetry'; messageId: string; data: Telemetry }
  | { type: 'handoff'; data: HandoffEvent }
  | { type: 'extracted_data'; data: ExtractedData }
  | { type: 'done' }
  | { type: 'error'; message: string };

export interface TimedEvent {
  delay: number;
  event: ChatEvent;
}

export interface Trace {
  id: string;
  trigger: { label: string; keywords: string[] };
  events: TimedEvent[];
}

export type EventHandler = (event: ChatEvent) => void;

export interface ChatEventSource {
  start(userInput: string, onEvent: EventHandler): void;
  cancel(): void;
}

/** Plays canned traces client-side with their recorded timing. Default source so the demo works with no backend at all. */
export class ReplaySource implements ChatEventSource {
  private timers: ReturnType<typeof setTimeout>[] = [];

  constructor(private traces: Trace[]) {}

  matchTrace(userInput: string): Trace {
    const normalized = userInput.toLowerCase();
    const match = this.traces.find((trace) =>
      trace.trigger.keywords.some((keyword) => normalized.includes(keyword)),
    );
    return match ?? this.traces[0];
  }

  start(userInput: string, onEvent: EventHandler): void {
    this.cancel();
    const trace = this.matchTrace(userInput);
    let elapsed = 0;
    for (const timed of trace.events) {
      elapsed += timed.delay;
      this.timers.push(setTimeout(() => onEvent(timed.event), elapsed));
    }
  }

  cancel(): void {
    this.timers.forEach(clearTimeout);
    this.timers = [];
  }
}

/** Streams real server-sent events from the demo API once the backend is warm. */
export class SseSource implements ChatEventSource {
  private controller: AbortController | null = null;

  constructor(private endpoint: string = '/api/demo/chat/stream') {}

  start(userInput: string, onEvent: EventHandler): void {
    this.cancel();
    this.controller = new AbortController();
    void this.stream(userInput, onEvent, this.controller.signal);
  }

  private async stream(userInput: string, onEvent: EventHandler, signal: AbortSignal): Promise<void> {
    try {
      const response = await fetch(this.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userInput }),
        signal,
      });
      if (!response.ok || !response.body) {
        onEvent({ type: 'error', message: `Stream unavailable (HTTP ${response.status})` });
        return;
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const frames = buffer.split('\n\n');
        buffer = frames.pop() ?? '';
        for (const frame of frames) {
          const dataLine = frame.split('\n').find((line) => line.startsWith('data: '));
          if (!dataLine) continue;
          try {
            onEvent(JSON.parse(dataLine.slice(6)) as ChatEvent);
          } catch {
            // Skip malformed frames; the stream stays usable.
          }
        }
      }
    } catch (error) {
      if (!signal.aborted) {
        onEvent({ type: 'error', message: error instanceof Error ? error.message : 'Stream failed' });
      }
    }
  }

  cancel(): void {
    this.controller?.abort();
    this.controller = null;
  }
}
