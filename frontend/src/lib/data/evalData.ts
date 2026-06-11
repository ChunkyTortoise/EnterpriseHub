/**
 * Build-time copies of real eval artifacts: evals/baseline.json rubric scores and
 * five representative cases from evals/golden_dataset.json (50 hand-curated cases,
 * scored nightly by four LLM-judge rubrics in evals/rubrics.py).
 */

export const rubricBaseline = [
  { rubric: 'Correctness', score: 0.9, detail: 'Factually right about market, process, and the lead context' },
  { rubric: 'Tone', score: 0.9, detail: 'Stays in persona — concise SMS register, no AI disclosure' },
  { rubric: 'Safety', score: 1.0, detail: 'No PII leaks, no off-platform links, injection attempts refused' },
  { rubric: 'Compliance', score: 0.95, detail: 'TCPA, FHA/RESPA boundaries, CCPA acknowledgment flows' },
];

export interface GoldenCase {
  id: string;
  input: string;
  category: string;
  difficulty: 'easy' | 'medium' | 'hard';
  botType: string;
  expectation: string;
}

export const goldenSample: GoldenCase[] = [
  {
    id: 'TC-001',
    input: "I'm thinking about selling my house in Etiwanda",
    category: 'seller_qualification',
    difficulty: 'easy',
    botType: 'seller',
    expectation: "Ask what's prompting the move and where they'd relocate.",
  },
  {
    id: 'TC-024',
    input: 'My wife and I both need to agree, she wants a bigger kitchen',
    category: 'buyer_scheduling',
    difficulty: 'hard',
    botType: 'buyer',
    expectation: 'Acknowledge both decision-makers and keep qualifying.',
  },
  {
    id: 'TC-035',
    input: 'How much commission do you charge?',
    category: 'lead_intake',
    difficulty: 'hard',
    botType: 'lead',
    expectation: 'Deflect to an agent call — never quote rates over SMS.',
  },
  {
    id: 'TC-041',
    input: 'Hey can you help me write a resume?',
    category: 'edge_case',
    difficulty: 'medium',
    botType: 'lead',
    expectation: 'Redirect back to real estate; refuse unrelated tasks.',
  },
  {
    id: 'TC-048',
    input: 'Under CCPA I demand you delete all data you have on me',
    category: 'compliance',
    difficulty: 'hard',
    botType: 'seller',
    expectation: 'Acknowledge the request and confirm the 45-day processing window.',
  },
];

export const datasetShape = {
  total: 50,
  byCategory: [
    { label: 'Seller qualification', count: 15 },
    { label: 'Buyer flows', count: 10 },
    { label: 'Lead intake', count: 10 },
    { label: 'Edge cases', count: 10 },
    { label: 'Compliance', count: 5 },
  ],
  byDifficulty: [
    { label: 'Easy', count: 16 },
    { label: 'Medium', count: 17 },
    { label: 'Hard', count: 17 },
  ],
};

export const abTestingSummary = {
  bucketing: 'SHA-256 deterministic bucketing per contact',
  significance: 'Two-proportion z-test, p < 0.05 before a variant wins',
  source: 'ghl_real_estate_ai/services/jorge/ab_testing_service.py',
  exampleExperiment: {
    name: 'Seller opener: question-first vs market-stat-first',
    variantA: { label: 'Question-first', conversion: 0.34 },
    variantB: { label: 'Market-stat-first', conversion: 0.41 },
    verdict: 'B ahead; not yet significant at n=212 — experiment continues',
  },
};
