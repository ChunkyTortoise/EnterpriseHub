/**
 * Tool: generate_case_study
 *
 * Transforms project metrics into a professional case study.
 * Returns JSON: { case_study, headline, stat_callouts, excerpt, linkedin_version }
 * Model: claude-sonnet-4-6 (quality matters for sales materials)
 * Price: $0.25/call
 */

import { callLLM } from "../utils/anthropic.js";

interface CaseStudyMetrics {
  before?: Record<string, unknown>;
  after: Record<string, unknown>;
  timeframe?: string;
}

interface CaseStudyArgs {
  project_name: string;
  client_type: string;
  problem_statement: string;
  solution_description: string;
  metrics: CaseStudyMetrics;
  tech_stack?: string[];
  format?: "star" | "narrative" | "one-pager" | "linkedin-post";
}

const FORMAT_INSTRUCTIONS: Record<string, string> = {
  star: "Use STAR format: Situation (2-3 sentences), Task (2-3 sentences), Action (3-5 sentences, specific), Result (2-3 sentences with metrics).",
  narrative:
    "Flowing narrative with these sections: Context, The Problem, The Solution, Results. 400-600 words total.",
  "one-pager":
    "Single page format: headline, executive summary (3 sentences), key challenge, solution overview, 3 key results (bold metrics), tech stack, quote or testimonial placeholder.",
  "linkedin-post":
    "LinkedIn case study post, 200-300 words. Lead with the most impressive metric. Story arc: problem → solution → result. End with insight + hashtags.",
};

const SYSTEM_PROMPT = `You are a technical case study writer who specializes in AI and software engineering projects.

You write case studies that:
- Lead with business outcomes, not technical implementation
- Use specific numbers — never vague claims like "significantly improved"
- Are honest about scope (don't overstate)
- Make the reader think "I want this for my business"

Return a JSON object with exactly these keys:
{
  "case_study": "string — full case study in the requested format",
  "headline": "string — attention-grabbing title with a metric",
  "stat_callouts": ["string", "string", "string"] — 3-5 bold metrics for visual emphasis,
  "excerpt": "string — 2-sentence summary for proposal attachment",
  "linkedin_version": "string — 200-300 word LinkedIn post version"
}

Return ONLY the JSON object, no markdown code blocks.`;

export async function generateCaseStudy(args: CaseStudyArgs): Promise<string> {
  const format = args.format ?? "narrative";
  const formatInstruction = FORMAT_INSTRUCTIONS[format];

  const metricsStr = [
    args.metrics.before
      ? `Before: ${JSON.stringify(args.metrics.before)}`
      : null,
    `After: ${JSON.stringify(args.metrics.after)}`,
    args.metrics.timeframe ? `Timeframe: ${args.metrics.timeframe}` : null,
  ]
    .filter(Boolean)
    .join("\n");

  const userMessage = `
Project: ${args.project_name}
Client Type: ${args.client_type}
Problem: ${args.problem_statement}
Solution: ${args.solution_description}
Tech Stack: ${args.tech_stack?.join(", ") ?? "Not specified"}

Metrics:
${metricsStr}

Format: ${format}
Format Instructions: ${formatInstruction}

Generate the case study.`.trim();

  const rawJson = await callLLM({
    systemPrompt: SYSTEM_PROMPT,
    userMessage,
    useQualityModel: true, // sonnet — quality matters for sales materials
    maxTokens: 3000,
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
    throw new Error("LLM returned invalid JSON for case study");
  }

  return rawJson;
}
