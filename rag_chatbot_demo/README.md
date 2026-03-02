# RAG Chatbot Demo

Upload a PDF or paste a URL -- get an instant chatbot on your content in 60 seconds.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.43-red)
![ChromaDB](https://img.shields.io/badge/ChromaDB-0.6-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## What It Does

A production-grade RAG (Retrieval-Augmented Generation) chatbot that:

- **Ingests** PDFs, TXT, Markdown files, or web URLs
- **Chunks** text with sentence-boundary-aware splitting (800 tokens, 100 overlap)
- **Embeds** chunks via GLM, OpenAI, or Anthropic
- **Stores** vectors in ChromaDB (in-memory)
- **Retrieves** top-5 most relevant chunks via cosine similarity
- **Generates** cited answers with `[Source N]` references
- **Hybrid mode** -- BM25 + dense retrieval with Reciprocal Rank Fusion (RRF)

## Local Setup

```bash
git clone https://github.com/ChunkyTortoise/EnterpriseHub.git
cd EnterpriseHub/rag_chatbot_demo

pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your API keys

streamlit run app.py
```

## Streamlit Cloud Deploy

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Point to `rag_chatbot_demo/app.py` as the main file
4. In **Advanced settings > Secrets**, paste the contents of `.streamlit/secrets.toml.example` with your real keys
5. Set Python version to **3.12** (recommended)
6. Deploy

## Python Version

**Python 3.12 is recommended.** ChromaDB uses pydantic v1 internally, which has compatibility issues with Python 3.14+. If you encounter `ConfigError` on import, downgrade to Python 3.12.

## Tech Stack

| Component | Library |
|-----------|---------|
| UI | Streamlit |
| Vector Store | ChromaDB (EphemeralClient) |
| Embeddings | GLM embedding-3 / OpenAI text-embedding-3-small |
| LLM | GLM-4-Flash / GPT-4o-mini / Claude Haiku |
| PDF Parsing | pypdf |
| Web Scraping | httpx + BeautifulSoup4 |
| Sparse Retrieval | rank-bm25 (hybrid mode) |
| Dense Retrieval | sentence-transformers (hybrid mode) |

## Author

**Cayman Roden** -- [Upwork](https://www.upwork.com/freelancers/caymanroden) | [Fiverr](https://www.fiverr.com/caymanroden) | [LinkedIn](https://www.linkedin.com/in/caymanroden/)
