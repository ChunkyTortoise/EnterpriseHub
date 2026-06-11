import type { ChatEvent, ExtractedData, HandoffEvent, Telemetry, TimedEvent, Trace } from './demoEngine';

interface BotTurn {
  kind: 'bot';
  id: string;
  bot: 'lead' | 'buyer' | 'seller';
  title: string;
  text: string;
  telemetry: Telemetry;
}

interface UserTurn {
  kind: 'user';
  id: string;
  title: string;
  text: string;
}

interface HandoffStep {
  kind: 'handoff';
  data: HandoffEvent;
}

interface ContextStep {
  kind: 'context';
  data: ExtractedData;
}

type Step = BotTurn | UserTurn | HandoffStep | ContextStep;

/** Deterministic per-chunk jitter so replay timing looks organic without Math.random (keeps replays identical across runs). */
function jitter(seed: number): number {
  return 28 + ((seed * 37) % 41);
}

function tokenize(messageId: string, text: string): TimedEvent[] {
  const words = text.split(' ');
  const events: TimedEvent[] = [];
  let chunk: string[] = [];
  words.forEach((word, index) => {
    chunk.push(word);
    if (chunk.length === 3 || index === words.length - 1) {
      events.push({
        delay: jitter(index + messageId.length),
        event: { type: 'token', messageId, text: chunk.join(' ') + (index === words.length - 1 ? '' : ' ') },
      });
      chunk = [];
    }
  });
  return events;
}

function buildEvents(steps: Step[]): TimedEvent[] {
  const events: TimedEvent[] = [];
  for (const step of steps) {
    if (step.kind === 'user') {
      events.push({
        delay: 350,
        event: { type: 'message_start', messageId: step.id, role: 'user', title: step.title },
      });
      events.push({ delay: 120, event: { type: 'token', messageId: step.id, text: step.text } });
    } else if (step.kind === 'bot') {
      events.push({
        delay: 600,
        event: { type: 'message_start', messageId: step.id, role: 'bot', bot: step.bot, title: step.title },
      });
      events.push(...tokenize(step.id, step.text));
      events.push({ delay: 180, event: { type: 'telemetry', messageId: step.id, data: step.telemetry } });
    } else if (step.kind === 'handoff') {
      events.push({ delay: 700, event: { type: 'handoff', data: step.data } });
    } else {
      events.push({ delay: 250, event: { type: 'extracted_data', data: step.data } });
    }
  }
  events.push({ delay: 400, event: { type: 'done' } as ChatEvent });
  return events;
}

/**
 * Scripted from real Jorge bot behavior: seller qualification mirrors the golden
 * dataset seller flow (motivation -> timeline -> condition) and the handoff payload
 * mirrors JorgeHandoffService confidence scoring (0.7 threshold).
 */
const sellerHandoff: Trace = {
  id: 'seller-handoff',
  trigger: {
    label: 'Qualify new seller lead',
    keywords: ['seller', 'sell', 'qualify', 'maria', 'cma'],
  },
  events: buildEvents([
    {
      kind: 'user',
      id: 's-u1',
      title: 'Inbound SMS — Maria Gonzalez',
      text: "I'm thinking about selling my house in Etiwanda, not sure where to start.",
    },
    {
      kind: 'bot',
      id: 's-b1',
      bot: 'lead',
      title: 'Lead Intake Bot',
      text: "Happy to help, Maria. What's prompting the move — and if you sold, would you stay in the Inland Empire or relocate?",
      telemetry: {
        cacheTier: 'MISS',
        cacheLatencyMs: 2,
        model: 'claude-haiku-4-5',
        tokensIn: 412,
        tokensOut: 38,
        costUsd: 0.00071,
        latencyMs: 842,
      },
    },
    {
      kind: 'user',
      id: 's-u2',
      title: 'Inbound SMS — Maria Gonzalez',
      text: "We're relocating to Texas for my husband's job. Honestly we need to sell fast, ideally before the school year.",
    },
    {
      kind: 'handoff',
      data: {
        from: 'lead',
        to: 'seller',
        confidence: 0.91,
        threshold: 0.7,
        reason: 'Seller intent signals: relocation motive + explicit urgency + owned property in service area',
        context: ['Motivation: job relocation (TX)', 'Timeline: <45 days', 'Property: Etiwanda, owner-occupied'],
      },
    },
    {
      kind: 'context',
      data: {
        leadName: 'Maria Gonzalez',
        items: [
          { label: 'Maria Gonzalez — Seller Lead', variant: 'success' },
          { label: 'Intent confidence: 91%', variant: 'primary' },
          { label: 'Timeline: under 45 days', variant: 'warning' },
          { label: 'Etiwanda · owner-occupied', variant: 'neutral' },
          { label: 'Motivation: TX relocation', variant: 'neutral' },
        ],
        nextActions: [
          'Run CMA for the Etiwanda property.',
          'Lead with the 30-45 day listing plan.',
          'Flag school-year deadline in follow-ups.',
        ],
      },
    },
    {
      kind: 'bot',
      id: 's-b2',
      bot: 'seller',
      title: 'Seller Bot (post-handoff)',
      text: 'A 30-45 day close is realistic in Etiwanda right now — homes there are averaging 18 days on market. Quick question so I can price this right: any repairs or updates the house needs before listing?',
      telemetry: {
        cacheTier: 'L2',
        cacheLatencyMs: 11,
        model: 'claude-haiku-4-5',
        tokensIn: 689,
        tokensOut: 54,
        costUsd: 0.00094,
        latencyMs: 1067,
      },
    },
    {
      kind: 'user',
      id: 's-u3',
      title: 'Inbound SMS — Maria Gonzalez',
      text: 'Just cosmetic stuff, new paint and maybe carpet in the bedrooms.',
    },
    {
      kind: 'bot',
      id: 's-b3',
      bot: 'seller',
      title: 'Seller Bot',
      text: "Paint and carpet are the two highest-ROI refreshes — worth doing. I'm preparing a CMA with three pricing scenarios for your place now. Want it by text or email?",
      telemetry: {
        cacheTier: 'L1',
        cacheLatencyMs: 3,
        model: 'claude-haiku-4-5',
        tokensIn: 0,
        tokensOut: 0,
        costUsd: 0,
        latencyMs: 6,
      },
    },
  ]),
};

const buyerMatch: Trace = {
  id: 'buyer-match',
  trigger: {
    label: 'Match buyer to listings',
    keywords: ['buyer', 'match', 'david', 'portal', 'listings', 'showing'],
  },
  events: buildEvents([
    {
      kind: 'user',
      id: 'b-u1',
      title: 'Inbound SMS — David Chen',
      text: "We're pre-approved for $750K and want to be in the Etiwanda school district. Hoping to move within 30 days.",
    },
    {
      kind: 'bot',
      id: 'b-b1',
      bot: 'buyer',
      title: 'Buyer Bot',
      text: "That's a strong position, David — pre-approval plus a 30-day window puts you ahead of most offers. Two quick filters: minimum bedrooms, and do you want move-in ready or are light projects okay?",
      telemetry: {
        cacheTier: 'MISS',
        cacheLatencyMs: 1,
        model: 'claude-haiku-4-5',
        tokensIn: 437,
        tokensOut: 47,
        costUsd: 0.00079,
        latencyMs: 911,
      },
    },
    {
      kind: 'user',
      id: 'b-u2',
      title: 'Inbound SMS — David Chen',
      text: '4 beds minimum, move-in ready. Garage for two cars.',
    },
    {
      kind: 'context',
      data: {
        leadName: 'David Chen',
        items: [
          { label: 'David Chen — Buyer Lead', variant: 'success' },
          { label: 'Pre-approved: $750K', variant: 'primary' },
          { label: 'Urgency: 30 days', variant: 'warning' },
          { label: '4BR+ · move-in ready · 2-car garage', variant: 'neutral' },
          { label: 'Area: Etiwanda school district', variant: 'neutral' },
        ],
        nextActions: [
          'Send portal link with 3 matched listings.',
          'Hold Saturday morning for showings.',
          'Confirm lender letter is dated this month.',
        ],
      },
    },
    {
      kind: 'bot',
      id: 'b-b2',
      bot: 'buyer',
      title: 'Buyer Bot — Property Match',
      text: '3 active listings match: 1248 Cypress Ridge Ln ($769K, 4BR/3BA), 4417 Alta Crest Dr ($849K, 5BR/3BA — slightly over budget but 41 days on market, negotiable), and 7753 Etiwanda Ave ($629K, 3BR — under count, included for the lot size). Sending your swipe portal link now; anything you pass on teaches the matcher why.',
      telemetry: {
        cacheTier: 'L3',
        cacheLatencyMs: 24,
        model: 'claude-haiku-4-5',
        tokensIn: 1283,
        tokensOut: 96,
        costUsd: 0.00177,
        latencyMs: 1490,
      },
    },
    {
      kind: 'bot',
      id: 'b-b3',
      bot: 'buyer',
      title: 'Portal Link Sent',
      text: 'Portal link delivered to David. He liked 2 of 3 within four minutes — high-intent signal fired, and Saturday 10 AM showing request queued for your approval.',
      telemetry: {
        cacheTier: 'L1',
        cacheLatencyMs: 4,
        model: 'claude-haiku-4-5',
        tokensIn: 0,
        tokensOut: 0,
        costUsd: 0,
        latencyMs: 9,
      },
    },
  ]),
};

export const demoTraces: Trace[] = [sellerHandoff, buyerMatch];

export const samplePrompts = demoTraces.map((trace) => trace.trigger.label);
