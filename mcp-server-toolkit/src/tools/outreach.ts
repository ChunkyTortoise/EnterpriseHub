/**
 * Tool: generate_outreach_sequence
 *
 * Generates a personalized cold outreach email sequence (1-5 emails).
 * Returns JSON array: [{ subject, body, send_delay_days }]
 * Model: claude-sonnet-4-6 (quality matters for outreach)
 * Price: $0.50/sequence
 */

import { callLLM } from "../utils/anthropic.js";

interface OutreachArgs {
  company_name: string;
  contact_name: string;
  contact_role?: string;
  company_pain_point: string;
  your_service: string;
  sequence_length?: number;
  tone?: "formal" | "conversational" | "direct";
  your_name?: string;
  social_proof?: string;
}

const SYSTEM_PROMPT = `You are a B2B cold outreach specialist who writes email sequences with above-average reply rates.

Your emails:
- Are short (under 150 words for Email 1, under 200 for follow-ups)
- Open with a specific observation about the company — never a generic opener
- Focus on one problem per email
- Have a clear, low-friction CTA (not "schedule a call" for Email 1 — ask a question instead)
- Feel human — no buzzwords, no "I hope this email finds you well"

Sequence structure:
- Email 1: Problem-aware opener + specific value prop + single question CTA
- Email 2: Different angle or social proof + different CTA
- Email 3: "Last follow-up" / soft breakup — keep door open
- Email 4 (if requested): Case study or result reference
- Email 5 (if requested): Industry insight + re-engage

Output format: Valid JSON array. Each element:
{
  "sequence_number": 1,
  "subject": "...",
  "body": "...",
  "send_delay_days": 0
}

send_delay_days: Email 1 = 0, Email 2 = 3-4, Email 3 = 5-7, Email 4 = 10-14, Email 5 = 21

Return ONLY the JSON array, no markdown code blocks, no explanation.`;

export async function generateOutreachSequence(args: OutreachArgs): Promise<string> {
  const seqLength = args.sequence_length ?? 3;
  const senderName = args.your_name ?? "Cayman";

  const userMessage = `
Company: ${args.company_name}
Contact: ${args.contact_name}${args.contact_role ? `, ${args.contact_role}` : ""}
Pain Point: ${args.company_pain_point}
Your Service: ${args.your_service}
${args.social_proof ? `Social Proof: ${args.social_proof}` : ""}
Sender Name: ${senderName}
Sequence Length: ${seqLength} emails
Tone: ${args.tone ?? "conversational"}

Write a ${seqLength}-email cold outreach sequence.`.trim();

  const rawJson = await callLLM({
    systemPrompt: SYSTEM_PROMPT,
    userMessage,
    useQualityModel: true, // sonnet — quality matters for outreach
    maxTokens: 3000,
  });

  // Validate it's parseable JSON before returning
  try {
    JSON.parse(rawJson);
  } catch {
    // Attempt to extract JSON array from response
    const match = rawJson.match(/\[[\s\S]*\]/);
    if (match) {
      JSON.parse(match[0]); // will throw if still invalid
      return match[0];
    }
    throw new Error("LLM returned invalid JSON for outreach sequence");
  }

  return rawJson;
}
