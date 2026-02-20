/**
 * Tool: generate_proposal
 *
 * Generates a 300-500 word freelance proposal from a job description.
 * Model: claude-haiku (fast, cost-effective)
 * Price: $0.25/call
 */

import { callLLM } from "../utils/anthropic.js";

interface ProposalArgs {
  job_title: string;
  job_description: string;
  budget?: string;
  client_background?: string;
  your_skills?: string[];
  tone?: "technical" | "conversational" | "direct";
}

const SYSTEM_PROMPT = `You are an expert freelance proposal writer who specializes in AI/ML engineering, automation, and software development projects.

Write compelling, personalized proposals that:
1. Open with the client's specific problem (not a generic intro)
2. Demonstrate understanding of their requirements
3. Show relevant experience with concrete examples
4. Provide a clear, confident next step

Default skills to highlight (unless overridden): Claude/Anthropic API, multi-agent systems, RAG pipelines, Python, FastAPI, GoHighLevel/CRM automation, Streamlit dashboards, production AI deployment.

Tone guidelines:
- conversational: warm, direct, human — no corporate-speak
- technical: precise, show technical depth, use correct terminology
- direct: brief, confident, no fluff — lead with value

Always end with a specific call to action (reply, call, quick question).

Length: 300-500 words. No headers or bullet points — flowing paragraphs only.`;

export async function generateProposal(args: ProposalArgs): Promise<string> {
  const skillsList =
    args.your_skills?.join(", ") ??
    "Claude API, multi-agent systems, RAG pipelines, Python, FastAPI, GHL automation";

  const userMessage = `
Job Title: ${args.job_title}

Job Description:
${args.job_description}

${args.budget ? `Budget: ${args.budget}` : ""}
${args.client_background ? `Client Background: ${args.client_background}` : ""}

Skills to Highlight: ${skillsList}
Tone: ${args.tone ?? "conversational"}

Write a proposal for this job.`.trim();

  return callLLM({
    systemPrompt: SYSTEM_PROMPT,
    userMessage,
    useQualityModel: false, // haiku — fast and cost-effective for proposals
  });
}
