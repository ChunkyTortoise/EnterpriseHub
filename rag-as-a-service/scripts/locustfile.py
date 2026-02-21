"""Locust load test for RAG-as-a-Service API.

Usage:
    locust -f scripts/locustfile.py --host http://localhost:8000

Target: 50 concurrent users, p95 < 500ms.
"""

from __future__ import annotations

import os

from locust import HttpUser, between, task

API_KEY = os.environ.get("RAG_API_KEY", "")


class RAGUser(HttpUser):
    """Simulates a tenant hitting the RAG API."""

    wait_time = between(0.1, 0.5)

    def on_start(self):
        self.headers = {}
        if API_KEY:
            self.headers["X-API-Key"] = API_KEY

    @task(5)
    def health_check(self):
        self.client.get("/health")

    @task(10)
    def query_documents(self):
        self.client.post(
            "/api/v1/query",
            json={"query": "What are the key features?", "top_k": 5},
            headers=self.headers,
        )

    @task(2)
    def upload_document(self):
        content = b"This is a test document for load testing the RAG pipeline."
        self.client.post(
            "/api/v1/documents",
            files={"file": ("test.txt", content, "text/plain")},
            headers=self.headers,
        )

    @task(3)
    def list_collections(self):
        self.client.get("/api/v1/collections", headers=self.headers)
