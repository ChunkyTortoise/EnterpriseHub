# GHL Real Estate AI - Backend API

This directory contains the production FastAPI backend for the Real Estate AI Qualification Assistant.

## Project Structure

```
backend/
├── api/                # FastAPI routes and endpoints
├── core/               # Configuration and core logic
├── services/           # Business logic (Lead Scoring, RAG, etc.)
├── data/               # Knowledge base and static assets
├── deployment/         # Deployment configuration (Docker, Railway)
├── tests/              # Unit and integration tests
└── main.py             # Application entry point
```

## Setup & Installation

1.  **Environment Setup**:
    ```bash
    cp .env.example .env
    # Edit .env with your API keys
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r deployment/requirements.txt
    ```

3.  **Run Tests**:
    ```bash
    pytest tests/
    ```

4.  **Run Development Server**:
    ```bash
    uvicorn main:app --reload
    ```

5.  **Docker Build**:
    ```bash
    docker build -t ghl-backend -f deployment/Dockerfile .
    ```

## Key Components

-   **Lead Scorer**: `services/lead_scorer.py` (100% test coverage)
-   **Config**: `core/config.py` (Pydantic-based settings)

## Status

-   [x] Project skeleton created
-   [x] Lead scorer migrated and tested
-   [x] Basic FastAPI app running
-   [ ] GHL Webhook integration (Pending system audit)
-   [ ] RAG Engine implementation
-   [ ] Conversation logic
