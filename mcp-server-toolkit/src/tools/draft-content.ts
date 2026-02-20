/**
 * Tool: draft_content
 *
 * Repurposes a topic into multiple content formats simultaneously.
 * Returns JSON object: { linkedin, twitter, devto, newsletter, reddit, youtube-script }
 * Model: claude-haiku (volume tool — cost matters)
 * Price: $0.10/format
 */

import { callLLM } from "../utils/anthropic.js";

type ContentFormat =
  | "linkedin"
  | "twitter"
  | "devto"
  | "newsletter"
  | "reddit"
  | "youtube-script";

interface DraftContentArgs {
  topic: string;
  source_content?: string;
  formats?: ContentFormat[];
  tone?: "technical" | "conversational" | "educational" | "thought-leader";
  target_audience?: string;
  call_to_action?: string;
}

const ALL_FORMATS: ContentFormat[] = [
  "linkedin",
  "twitter",
  "devto",
  "newsletter",
  "reddit",
  "youtube-script",
];

const FORMAT_INSTRUCTIONS: Record<ContentFormat, string> = {
  linkedin:
    "150-300 word post. Hook in line 1 (no 'I' opener). 3-5 short paragraphs. End with question or CTA. 3-5 hashtags at bottom.",
  twitter:
    "Thread of 5-7 tweets. Tweet 1 = hook (max 280 chars). Each tweet standalone. Number them 1/7, 2/7 etc. End with follow CTA.",
  devto:
    "Full article in markdown, 800-1200 words. Frontmatter: title, tags (4 max). Include code examples where relevant. Technical depth.",
  newsletter:
    "Email body, 400-600 words. Subject line at top. Conversational tone. One main insight. Clear CTA at bottom.",
  reddit:
    "Reddit post for r/MachineLearning or r/Python (choose the better fit). Title + body. Informative, not promotional. Community tone.",
  "youtube-script":
    "5-7 minute video script with [TIMESTAMP] markers every 60-90 seconds. Hook (30s), Main Content (4-5min), CTA (30s). Conversational spoken language.",
};

const SYSTEM_PROMPT = `You are a content strategist and writer who specializes in repurposing technical topics across multiple platforms.

You will receive a topic and list of requested formats. For each format, write platform-optimized content following the specific instructions provided.

Output format: Valid JSON object where each key is a format name and the value is the content string.
Return ONLY the JSON object, no markdown code blocks, no explanation outside the JSON.

Example:
{
  "linkedin": "...",
  "twitter": "..."
}`;

export async function draftContent(args: DraftContentArgs): Promise<string> {
  const requestedFormats = args.formats ?? ALL_FORMATS;

  const formatInstructions = requestedFormats
    .map((f) => `${f}: ${FORMAT_INSTRUCTIONS[f]}`)
    .join("\n");

  const userMessage = `
Topic: ${args.topic}
${args.source_content ? `\nSource Content to Repurpose:\n${args.source_content}` : ""}
Tone: ${args.tone ?? "educational"}
${args.target_audience ? `Target Audience: ${args.target_audience}` : ""}
${args.call_to_action ? `CTA to include: ${args.call_to_action}` : ""}

Generate content for these formats:
${formatInstructions}`.trim();

  const rawJson = await callLLM({
    systemPrompt: SYSTEM_PROMPT,
    userMessage,
    useQualityModel: false, // haiku — volume tool
    maxTokens: 4096,
  });

  // Validate JSON
  try {
    JSON.parse(rawJson);
  } catch {
    const match = rawJson.match(/\{[\s\S]*\}/);
    if (match) {
      JSON.parse(match[0]);
      return match[0];
    }
    throw new Error("LLM returned invalid JSON for draft content");
  }

  return rawJson;
}
