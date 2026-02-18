# DeepLearning.AI "Generative AI with LLMs" — Accelerated Study Plan

**Course**: Generative AI with LLMs (DeepLearning.AI + AWS, Coursera) | **Cost**: $49/mo
**Runtime**: ~16.5h total | **Target**: Done in 2 weeks given your background

---

## Course Modules

| Week | Topics | Lab |
|------|--------|-----|
| 1 | Transformer architecture, scaling laws (Chinchilla), parallelism, pre-training objectives | Dialogue summarization with FLAN-T5 (zero/one/few-shot) |
| 2 | Instruction fine-tuning, PEFT/LoRA, soft prompts, ROUGE/BLEU, benchmarks (MMLU, HELM) | Fine-tune FLAN-T5 with full FT then LoRA; compare ROUGE |
| 3 | RLHF (PPO + reward model), Constitutional AI, CoT, ReAct, PAL, RAG, LangChain, quantization | Fine-tune FLAN-T5 with PPO + reward model (SageMaker) |

---

## Accelerated 2-Week Plan

### Week 1 (Days 1-7)

**Day 1 (2h)** — Course Week 1 at 2x
- Watch all at 1.5-2x; skip lifecycle overview and basic prompt engineering (you know it)
- Slow down for: **Chinchilla scaling laws**, parallelism strategies, compute budget math
- Complete Lab 1 in 30 min (skim SageMaker boilerplate)

**Day 2 (2h)** — Course Week 2 at 2x
- Slow down for: **LoRA rank decomposition math**, ROUGE calculation internals, MMLU/HELM structure
- Do Lab 2 fully — LoRA lab is worth hands-on time

**Days 3-5 (1h/day)** — Apply to your stack
- Map LoRA to Jorge bots: which conversations would benefit from fine-tuning?
- Reproduce the LoRA lab on a small custom dataset (real estate Q&A pairs from GHL logs)

**Days 6-7 (2h each)** — Course Week 3
- Watch at 1.5x; **slow down for PPO mechanics, KL-divergence penalty, Constitutional AI**
- Complete Lab 3 fully — reward model training is the most novel part
- Watch RAG/ReAct sections (review for you, confirm course framing)

### Week 2 (Days 8-14)

**Days 8-9** — Fill gaps
- Read Chinchilla paper (Hoffmann et al., 2022) — Section 3 + 4 only (~30 min)
- Read InstructGPT paper (Ouyang et al., 2022) — PPO implementation details
- Compare course's RAG framing against your `advanced_rag_system/`

**Days 10-11** — Apply to your stack
- Implement a minimal Constitutional AI critique-revision loop with Claude API
- Map to Jorge bot safety layers

**Days 12-13** — Finish and submit
- Confirm all 3 quizzes passed, all 3 labs submitted
- Download certificate

**Day 14** — Publish cert
- LinkedIn post: what you knew + what surprised you (Chinchilla, PPO) + one concrete application

---

## What to Skip (Already Know)

- Intro to generative AI / LLM use cases
- Basic transformer architecture intro
- Zero-shot / few-shot prompting basics
- Top-k / top-p / temperature (already tuning in `claude_orchestrator.py`)
- LLM project lifecycle framework (you have deployment checklist)
- RAG overview and LangChain intro (built `advanced_rag_system/` from scratch)
- SageMaker boilerplate setup
- Basic chatbot patterns

---

## What to Focus On (Actual Gaps)

| Topic | Why | Week |
|-------|-----|------|
| **Chinchilla scaling laws** | Compute-optimal training math, informs model selection | 1 |
| **ROUGE/BLEU internals** | Client conversations, benchmark comparisons | 2 |
| **LoRA rank decomposition math** | `r * (d_in + d_out)` parameter count, rank selection | 2 |
| **PPO + KL-divergence penalty** | RLHF training loop — biggest gap | 3 |
| **Constitutional AI mechanics** | Why Claude behaves as it does, Jorge bot safety design | 3 |
| **PAL and ReAct patterns** | Enterprise RFP vocabulary, structured agent loops | 3 |
| **Benchmark landscape** (MMLU, BIG-Bench, HELM) | Model evaluation vocabulary for client proposals | 2 |

---

## What the Cert Signals

| Client Type | Signal |
|-------------|--------|
| Non-technical decision-maker | Formal credential from most-recognized AI training org, AWS-backed. Lower risk. |
| Technical evaluator | Full stack: pre-training → fine-tuning → RLHF → deployment. Not just API wrappers. |
| Enterprise procurement | Satisfies vendor qualification checklists requiring documented AI credentials. |

**The Andrew Ng / DeepLearning.AI brand** is the strongest signal in AI certs — recognized on Upwork RFPs and LinkedIn filters in a way Google/AWS standalone certs aren't (implies ML fundamentals, not just cloud platform familiarity).

**Lead with portfolio; cert removes objections.**

---

## Companion Resources (Post-Course)

| Resource | Topic |
|----------|-------|
| Anthropic: "Constitutional AI" (2022) | Primary source for Week 3 CAI technique |
| Ouyang et al., InstructGPT (2022) | RLHF PPO implementation details |
| Hoffmann et al., Chinchilla (2022) | Compute-optimal scaling, read Sections 3-4 |
| Hugging Face `trl.PPOTrainer` | Production RLHF code the course abstracts |
| Hu et al., LoRA paper (2021) | Section 4 maps directly to fine-tuning Jorge bots |
| Lilian Weng's blog (lilianweng.github.io) | RLHF, LLM agents, prompt engineering deep dives |
| Chip Huyen "AI Engineering" (O'Reilly, 2024) | Chapters 6 (RAG), 9 (fine-tuning), 10 (evaluation) |

---

## Time Budget

| Block | Hours |
|-------|-------|
| Weeks 1-3 videos (2x, skipping basics) | ~7h |
| All 3 labs | ~2.5h |
| Chinchilla + InstructGPT papers | 2h |
| TRL library minimal RLHF run | 2h |
| Custom LoRA experiment on RE data | 3h |
| **Total** | **~19h** |

At 3-4h/day → done in **5-7 days**. Certificate in under 2 weeks.
