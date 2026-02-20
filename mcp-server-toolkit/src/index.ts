/**
 * mcp-server-toolkit — Skills MCP Server
 *
 * Exposes 4 AI-powered productivity tools as MCP tools:
 *   - generate_proposal
 *   - generate_outreach_sequence
 *   - draft_content
 *   - generate_case_study
 *
 * Transport: stdio (works with Claude Desktop and MCP clients)
 *
 * Usage:
 *   ANTHROPIC_API_KEY=sk-ant-... node dist/index.js
 *   npx mcp-server-toolkit
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { generateProposal } from "./tools/proposal.js";
import { generateOutreachSequence } from "./tools/outreach.js";
import { draftContent } from "./tools/draft-content.js";
import { generateCaseStudy } from "./tools/case-study.js";

const server = new McpServer({
  name: "mcp-server-toolkit",
  version: "1.0.0",
});

// -------------------------------------------------------------------------
// Tool: generate_proposal
// -------------------------------------------------------------------------

server.tool(
  "generate_proposal",
  "Generate a tailored freelance or agency proposal from a job description. Returns a 300-500 word proposal ready to paste into Upwork or Fiverr.",
  {
    job_title: z.string().describe("Job posting title"),
    job_description: z
      .string()
      .min(100)
      .describe("Full job description text (minimum 100 characters)"),
    budget: z
      .string()
      .optional()
      .describe("Budget from posting, e.g. '$5,000' or '$75/hr'"),
    client_background: z
      .string()
      .optional()
      .describe("Any known context about the client or company"),
    your_skills: z
      .array(z.string())
      .optional()
      .describe("Skills to highlight — overrides defaults if provided"),
    tone: z
      .enum(["technical", "conversational", "direct"])
      .default("conversational")
      .describe("Tone for the proposal"),
  },
  async (args) => {
    try {
      const result = await generateProposal(args);
      return { content: [{ type: "text", text: result }] };
    } catch (err) {
      return {
        isError: true,
        content: [{ type: "text", text: `Error: ${(err as Error).message}` }],
      };
    }
  }
);

// -------------------------------------------------------------------------
// Tool: generate_outreach_sequence
// -------------------------------------------------------------------------

server.tool(
  "generate_outreach_sequence",
  "Create a personalized cold outreach email sequence (1-5 emails). Returns JSON array of { subject, body, send_delay_days }.",
  {
    company_name: z.string().describe("Target company name"),
    contact_name: z.string().describe("Target contact's name"),
    contact_role: z
      .string()
      .optional()
      .describe("Contact role/title, e.g. 'VP of Sales'"),
    company_pain_point: z
      .string()
      .describe("Researched or inferred pain point for this company"),
    your_service: z
      .string()
      .describe("What you offer — 1-2 sentences"),
    sequence_length: z
      .number()
      .int()
      .min(1)
      .max(5)
      .default(3)
      .describe("Number of emails in the sequence"),
    tone: z
      .enum(["formal", "conversational", "direct"])
      .default("conversational"),
    your_name: z.string().optional().describe("Your name for email sign-off"),
    social_proof: z
      .string()
      .optional()
      .describe("One stat or result to include, e.g. '89% cost reduction'"),
  },
  async (args) => {
    try {
      const result = await generateOutreachSequence(args);
      return { content: [{ type: "text", text: result }] };
    } catch (err) {
      return {
        isError: true,
        content: [{ type: "text", text: `Error: ${(err as Error).message}` }],
      };
    }
  }
);

// -------------------------------------------------------------------------
// Tool: draft_content
// -------------------------------------------------------------------------

server.tool(
  "draft_content",
  "Repurpose a topic or article into multiple content formats simultaneously. Supported formats: linkedin, twitter, devto, newsletter, reddit, youtube-script.",
  {
    topic: z
      .string()
      .min(10)
      .describe("Core topic, article title, or source content to repurpose"),
    source_content: z
      .string()
      .optional()
      .describe("Existing article or post to repurpose (optional)"),
    formats: z
      .array(
        z.enum([
          "linkedin",
          "twitter",
          "devto",
          "newsletter",
          "reddit",
          "youtube-script",
        ])
      )
      .optional()
      .describe("Formats to generate — defaults to all 6 if omitted"),
    tone: z
      .enum(["technical", "conversational", "educational", "thought-leader"])
      .default("educational"),
    target_audience: z
      .string()
      .optional()
      .describe("e.g. 'CTOs at Series B startups'"),
    call_to_action: z
      .string()
      .optional()
      .describe("CTA to include in all formats"),
  },
  async (args) => {
    try {
      const result = await draftContent(args);
      return { content: [{ type: "text", text: result }] };
    } catch (err) {
      return {
        isError: true,
        content: [{ type: "text", text: `Error: ${(err as Error).message}` }],
      };
    }
  }
);

// -------------------------------------------------------------------------
// Tool: generate_case_study
// -------------------------------------------------------------------------

server.tool(
  "generate_case_study",
  "Transform project metrics and outcomes into a professional case study. Returns { case_study, headline, stat_callouts, excerpt, linkedin_version }.",
  {
    project_name: z.string().describe("Name or codename of the project"),
    client_type: z
      .string()
      .describe("Industry or company type — anonymized is fine"),
    problem_statement: z
      .string()
      .describe("What was broken, missing, or painful before your work"),
    solution_description: z
      .string()
      .describe("What you built or implemented"),
    metrics: z
      .object({
        before: z
          .record(z.unknown())
          .optional()
          .describe("Baseline metrics (optional)"),
        after: z
          .record(z.unknown())
          .describe("Result metrics — e.g. { cost_reduction: '89%' }"),
        timeframe: z
          .string()
          .optional()
          .describe("e.g. '30 days', '3 months'"),
      })
      .describe("Before/after metrics"),
    tech_stack: z.array(z.string()).optional().describe("Technologies used"),
    format: z
      .enum(["star", "narrative", "one-pager", "linkedin-post"])
      .default("narrative")
      .describe("Output format for the case study"),
  },
  async (args) => {
    try {
      const result = await generateCaseStudy(args);
      return { content: [{ type: "text", text: result }] };
    } catch (err) {
      return {
        isError: true,
        content: [{ type: "text", text: `Error: ${(err as Error).message}` }],
      };
    }
  }
);

// -------------------------------------------------------------------------
// Start server
// -------------------------------------------------------------------------

async function main(): Promise<void> {
  if (!process.env.ANTHROPIC_API_KEY) {
    process.stderr.write(
      "Warning: ANTHROPIC_API_KEY is not set. Tool calls will fail.\n"
    );
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
  process.stderr.write("mcp-server-toolkit running on stdio\n");
}

main().catch((err) => {
  process.stderr.write(`Fatal error: ${err.message}\n`);
  process.exit(1);
});
