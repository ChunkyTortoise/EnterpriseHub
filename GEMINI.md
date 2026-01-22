# Gemini Workflow Guidelines

## Project Context
- **Primary focus**: Real estate AI, chatbot development, code optimization (Jorge Salas / Lyrio.io)
- **Typical tasks**: Code review, sales pitch generation, chatbot refinement, codebase analysis
- **Budget constraint**: $100/month (optimize for Flash first)
- **Quality bar**: 80%+ accuracy on all production tasks

## Task-Specific Personas

### Task: Code Review for Performance
```
You are a senior performance engineer with 10+ years of optimization experience.
Your goal: Review code for latency bottlenecks, memory leaks, and inefficiencies.
Output format: JSON with {"findings": [...], "priority": "high|medium|low", "fix_effort": "1h|4h|1d"}
```

### Task: Real Estate Sales Pitch
```
You are a top-performing real estate agent known for closing deals.
Your goal: Generate a personalized, compelling pitch highlighting property features for a specific buyer.
Tone: Warm, professional, enthusiastic.
Output: 2-3 sentences, max 150 words.
```

### Task: Chatbot Refinement
```
You are a conversation designer specializing in user retention and satisfaction.
Your goal: Evaluate chatbot responses and suggest improvements for clarity, helpfulness, and engagement.
Output format: JSON with {"score": 0-1, "feedback": "...", "suggestion": "..."}
```

## Context Compression Tips

- **Large codebases**: Use context compressor to extract only relevant functions/files
- **Long documents**: Summarize to key points + section headers before sending
- **Chat history**: Archive messages older than 20 turns to keep context fresh

## Model Selection Heuristic

| Task | Model | Rationale |
|------|-------|-----------|
| Code review, summarization, pitch generation | Flash | Fast, cheap, sufficient for most tasks |
| Complex reasoning, novel problem-solving | Pro | Worth the cost for harder tasks |
| Real-time interaction, Live API | Flash or Pro (try Flash first) | Use session resumption for context |

## Prompt Template (Reusable)

```
[PERSONA]
[Your persona here]

[TASK]
[Clear, specific task description]

[INPUT]
[User or system input]

[OUTPUT FORMAT]
[Desired output structure: JSON, markdown, plain text, etc.]

[CONSTRAINTS]
- Max tokens: [if applicable]
- Tone: [if applicable]
- Quality bar: [e.g., "80% accuracy on test suite"]
```

## Cost Tracking

- Log all API calls: `timestamp, model, task_type, input_tokens, output_tokens, cost`
- Weekly review: total spend + breakdown by task
- Monthly goal: < $100
