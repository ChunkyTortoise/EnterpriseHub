/**
 * Shared Anthropic client and LLM call helper.
 */

import Anthropic from "@anthropic-ai/sdk";

// Default models — can be overridden via env vars
const DEFAULT_MODEL = process.env.MCP_DEFAULT_MODEL ?? "claude-haiku-4-5-20251001";
const QUALITY_MODEL = process.env.MCP_QUALITY_MODEL ?? "claude-sonnet-4-6";
const MAX_TOKENS = parseInt(process.env.MCP_MAX_TOKENS ?? "2048", 10);

let _client: Anthropic | null = null;

function getClient(): Anthropic {
  if (!_client) {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    if (!apiKey) {
      throw new Error("ANTHROPIC_API_KEY environment variable not set");
    }
    _client = new Anthropic({ apiKey });
  }
  return _client;
}

export interface LLMCallOptions {
  systemPrompt: string;
  userMessage: string;
  useQualityModel?: boolean;   // true = claude-sonnet-4-6, false = claude-haiku
  maxTokens?: number;
}

/**
 * Call Anthropic API and return the text response.
 */
export async function callLLM(options: LLMCallOptions): Promise<string> {
  const client = getClient();
  const model = options.useQualityModel ? QUALITY_MODEL : DEFAULT_MODEL;

  const response = await client.messages.create({
    model,
    max_tokens: options.maxTokens ?? MAX_TOKENS,
    system: options.systemPrompt,
    messages: [{ role: "user", content: options.userMessage }],
  });

  const textBlock = response.content.find((b) => b.type === "text");
  if (!textBlock || textBlock.type !== "text") {
    throw new Error("LLM returned no text content");
  }

  return textBlock.text;
}

export { DEFAULT_MODEL, QUALITY_MODEL };
