# GHL Real Estate AI - Backend API

This directory contains the production FastAPI backend for the Real Estate AI Qualification Assistant.

## Structure

- **api/**: FastAPI routes and webhook endpoints.
- **core/**: Configuration, settings, and base classes.
- **services/**: Business logic (Lead Scoring, Claude AI, RAG, GHL Integration).
- **data/**: Knowledge base and static data.
- **deployment/**: Docker and Railway configuration.

## Setup

1. Copy `.env.example` to `.env` and fill in credentials.
2. Install requirements: `pip install -r deployment/requirements.txt`
3. Run dev server: `uvicorn main:app --reload`
