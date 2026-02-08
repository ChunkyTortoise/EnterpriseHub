# Upwork Proposal Templates

**Last Updated**: February 8, 2026
**Profile**: https://www.upwork.com/freelancers/~01ee20599d13f4c8c9
**Portfolio**: https://chunkytortoise.github.io

---

## Template 1: Build an AI Chatbot / LLM Integration

**Target jobs**: Chatbot development, LLM API integration, conversational AI, customer support automation, multi-agent systems

---

Hi [CLIENT NAME],

[SPECIFIC DETAIL FROM JOB POST — e.g., "Your idea for a customer support bot that routes between sales and technical queries is exactly the kind of multi-agent problem I've solved before."]

I build production AI chatbots with Python and FastAPI. A few things from my recent work that are directly relevant:

- **Multi-agent chatbot system** — Built 3 specialized real estate AI bots (lead qualification, buyer, seller) with cross-bot handoff, intent decoding, and A/B testing on response strategies. 279 tests, full CI. ([jorge_real_estate_bots](https://github.com/ChunkyTortoise/jorge_real_estate_bots))
- **LLM orchestration layer** — Built a provider-agnostic async interface across Claude, Gemini, OpenAI, and Perplexity with 3-tier caching that cut token costs by 89%. ([EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub))
- **CRM integration** — Connected chatbot outputs to GoHighLevel CRM with real-time lead scoring, temperature tagging, and automated workflow triggers.

My stack for this kind of work is typically FastAPI + PostgreSQL + Redis + whichever LLM fits the use case. I also have a [Multi-Agent Orchestration Starter Kit](https://chunkytortoise.github.io/projects.html) on Gumroad if you want to see how I structure these systems.

Happy to walk through the architecture I'd propose for [PROJECT NAME]. I could start [THIS WEEK / NEXT WEEK] and typically scope chatbot MVPs at 2-4 weeks.

— [YOUR NAME]

---

**Customization notes**:
- **Line 1**: Replace the bracketed hook with something specific from their job post. Mention their industry, their described pain point, or a feature they listed. Never be generic here — this is the line that determines whether they keep reading.
- **CRM bullet**: Swap GoHighLevel for whatever CRM/tool they mention (HubSpot, Salesforce, Zendesk, etc.). If no CRM is mentioned, replace this bullet with a deployment or scaling detail.
- **Timeline**: Adjust "2-4 weeks" based on the job's described scope. For simple single-bot projects, say "1-2 weeks." For enterprise multi-agent systems, say "4-8 weeks."
- **LLM provider**: If they specify OpenAI-only or Claude-only, emphasize that provider. The AgentForge repo demonstrates provider-agnostic capability, but match their language.
- **Rate**: For complex multi-agent work, quote toward $85/hr. For straightforward single-bot integrations, $65-75/hr is competitive.

---

## Template 2: Build a RAG System / Document Q&A

**Target jobs**: RAG pipelines, document search, knowledge base Q&A, embedding systems, internal search tools

---

Hi [CLIENT NAME],

[SPECIFIC DETAIL FROM JOB POST — e.g., "Searching across 10k+ PDF contracts with natural language queries is a great use case for RAG — and the accuracy issues you mentioned with basic embeddings are exactly why hybrid retrieval matters."]

I've built RAG systems from scratch and optimized existing ones. Here's what's relevant to your project:

- **Document Q&A engine** — Built a RAG pipeline with BM25 + dense hybrid retrieval, chunking strategies, and a prompt engineering lab for tuning answer quality. Includes cost tracking per query. 94 tests. ([docqa-engine](https://github.com/ChunkyTortoise/docqa-engine))
- **Production RAG with caching** — Implemented a 3-tier cache (L1/L2/L3) in a production system that reduced redundant embedding calls by 89% and kept response latency under 200ms. ([EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub))
- **RAG cost optimization** — Built tooling to analyze token usage, chunk sizing, and retrieval precision to balance accuracy vs. cost. ([Revenue-Sprint](https://github.com/ChunkyTortoise/Revenue-Sprint))

The typical architecture I'd propose: [EMBEDDING MODEL] for vectors, PostgreSQL with pgvector (or [THEIR PREFERRED VECTOR DB]) for storage, FastAPI for the API layer, and Redis for caching frequent queries. I tune chunking strategy and retrieval method to the document type — what works for legal contracts is different from what works for technical docs.

Want me to sketch out an architecture for [THEIR SPECIFIC DOCUMENT TYPE]? I'm available [THIS WEEK / NEXT WEEK].

— [YOUR NAME]

---

**Customization notes**:
- **Line 1**: Reference their specific document type (contracts, manuals, research papers, Confluence pages) and any pain point they described (accuracy, speed, cost). This shows you actually read the post.
- **Vector DB**: If they mention Pinecone, Weaviate, Chroma, or Qdrant, name-drop it. If they don't specify, suggest pgvector for simplicity or Pinecone for scale — and explain why briefly.
- **Embedding model**: Mention OpenAI `text-embedding-3-small` for cost efficiency or `text-embedding-3-large` for accuracy. If they're Claude-focused, mention Voyage AI embeddings.
- **Document type**: Adjust the closing question to reference their specific content. "Architecture for searching your support tickets" hits harder than "architecture for your documents."
- **Cost bullet**: If the client seems budget-conscious, lead with this bullet. If they seem quality-focused, lead with the hybrid retrieval bullet.
- **Rate**: RAG projects typically warrant $75-85/hr given the complexity of tuning retrieval quality.

---

## Template 3: Data Pipeline / Analytics Dashboard

**Target jobs**: Data processing, ETL pipelines, analytics dashboards, data visualization, ML models, reporting tools

---

Hi [CLIENT NAME],

[SPECIFIC DETAIL FROM JOB POST — e.g., "Pulling data from 5 different sources into a single dashboard with daily refreshes — I just built something very similar with auto-profiling and scheduled ETL."]

I build data pipelines and analytics dashboards in Python. Here's what matches your needs:

- **Analytics platform** — Built an auto-profiling engine that generates dashboards from raw datasets, including attribution analysis, predictive modeling (scikit-learn + XGBoost), and SHAP-based feature explanations. 63 tests. ([insight-engine](https://github.com/ChunkyTortoise/insight-engine))
- **BI dashboards** — Built Streamlit dashboards for a real estate platform: Monte Carlo simulations, sentiment tracking, churn detection, and pipeline forecasting with live PostgreSQL + Redis backends. ([EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub))
- **Data ingestion & transformation** — Built scraping pipelines with change detection, price monitoring with alerts, and Excel-to-SQLite converters with CRUD interfaces. ([scrape-and-serve](https://github.com/ChunkyTortoise/scrape-and-serve))

My typical stack: pandas/polars for processing, PostgreSQL or SQLite for storage, Streamlit or [THEIR PREFERRED TOOL] for dashboards, and Docker for deployment. For ML components I use scikit-learn and XGBoost — I keep it simple unless the problem genuinely needs deep learning.

I can scope this more precisely after a quick look at [THEIR DATA SOURCE / CURRENT SETUP]. Free to start [THIS WEEK / NEXT WEEK].

— [YOUR NAME]

---

**Customization notes**:
- **Line 1**: Mention their specific data sources (Shopify, Google Analytics, Salesforce exports, CSV dumps, APIs). The more specific, the better.
- **Dashboard tool**: If they want Plotly Dash, Retool, Metabase, or Tableau, swap out the Streamlit reference. If they don't specify, suggest Streamlit for speed-to-deploy and explain why.
- **ML bullet**: Only include the insight-engine bullet if the job mentions predictive modeling, forecasting, or ML. If it's pure ETL + dashboards, replace it with a bullet about data cleaning, scheduling, or error handling.
- **Data volume**: If they mention large datasets (millions of rows), add a note about polars or Dask for performance. If small-to-medium, pandas is fine and mentioning it keeps things approachable.
- **Third bullet**: Swap scrape-and-serve for a more relevant example if the job is about API integrations rather than scraping. The Revenue-Sprint repo has pipeline orchestration examples that may fit better.
- **Rate**: Pure dashboards and ETL can be quoted at $45-65/hr. If ML modeling or complex pipeline orchestration is involved, $65-85/hr.

---

## General Application Rules

1. **Never send a template unmodified.** The `[PLACEHOLDER]` sections exist because generic proposals get ignored. Spend 3-5 minutes reading the job post and customizing the hook and bullet ordering.

2. **Lead with the most relevant bullet.** If the job is 80% about cost optimization and 20% about building the system, put the cost/caching bullet first.

3. **Match their language.** If they say "chatbot," don't say "conversational AI agent." If they say "RAG pipeline," don't say "semantic search system." Use their words.

4. **Don't link more than 2 repos.** Three links feels like a portfolio dump. Pick the one or two that map most directly to their problem.

5. **Keep the CTA low-pressure.** "Want me to sketch out an architecture?" works better than "Let's schedule a call!" on Upwork. It shows you're ready to do work, not just talk.

6. **Attach the portfolio link only if they ask for more examples.** The in-proposal repo links are enough for the first message. Save https://chunkytortoise.github.io for follow-up conversations.

7. **Proposal length check.** If your customized version exceeds 275 words, cut. Hiring managers on Upwork skim. The templates above are 180-230 words each before customization — leave room for your personalized hook without bloating the total.
