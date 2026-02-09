"""
Locust Load Testing for RAG API

Simulates realistic user load patterns:
- Basic query requests (most common)
- Hybrid retrieval queries (moderate load)
- Streaming queries (resource intensive)
- Document ingestion (background load)

Targets:
- 100 concurrent users baseline
- 500 concurrent users stretch
- <100ms p95 response time under load
- <1% error rate
"""

import json
import random
import time

from locust import HttpUser, between, events, task


class RAGUser(HttpUser):
    """Simulate realistic RAG API usage patterns."""

    # Wait time between requests (1-5 seconds)
    wait_time = between(1, 5)

    def on_start(self):
        """Initialize user session with test data."""

        # Diverse query categories for realistic load testing
        self.queries = {
            "technical": [
                "What is vector similarity search?",
                "How does semantic retrieval work?",
                "Explain embedding models and their applications",
                "What are the benefits of hybrid search approaches?",
                "How to optimize RAG system performance?",
                "What is the difference between dense and sparse retrieval?",
                "Explain the concept of retrieval-augmented generation",
                "How do you implement context-aware search?",
                "What are best practices for document chunking?",
                "How to measure retrieval system accuracy?",
            ],
            "business": [
                "What are the cost implications of RAG systems?",
                "How to scale retrieval systems for enterprise use?",
                "What ROI can be expected from implementing RAG?",
                "How to ensure data privacy in retrieval systems?",
                "What are compliance considerations for AI systems?",
                "How to manage knowledge base versioning?",
                "What infrastructure is needed for production RAG?",
                "How to monitor and maintain RAG systems?",
                "What are common implementation challenges?",
                "How to train teams on RAG technology?",
            ],
            "operational": [
                "How to monitor RAG system health?",
                "What metrics should be tracked for retrieval quality?",
                "How to debug poor search results?",
                "What causes high latency in RAG systems?",
                "How to handle system failures gracefully?",
                "What are effective caching strategies?",
                "How to optimize memory usage in retrieval?",
                "What backup and recovery procedures are needed?",
                "How to perform A/B testing on RAG systems?",
                "What are security best practices for RAG?",
            ],
        }

        # Flatten all queries for random selection
        self.all_queries = []
        for category_queries in self.queries.values():
            self.all_queries.extend(category_queries)

        # Document templates for ingestion testing
        self.document_templates = [
            "Technical documentation about {topic} including implementation details and best practices.",
            "Business guide covering {topic} with ROI analysis and strategic considerations.",
            "Operational handbook for {topic} with monitoring and maintenance procedures.",
            "Research findings on {topic} with experimental results and conclusions.",
            "Tutorial content explaining {topic} with step-by-step instructions.",
        ]

        self.topics = [
            "vector databases",
            "machine learning",
            "data engineering",
            "cloud computing",
            "system architecture",
            "performance optimization",
            "security protocols",
            "API design",
            "data analytics",
            "automation",
        ]

        # Session-level metrics
        self.session_start = time.time()
        self.request_count = 0

    @task(10)  # Highest frequency task
    def query_basic(self):
        """
        Basic query request - most common user interaction.

        Weight: 10 (highest frequency)
        Expected: <50ms p95 latency
        """
        query = random.choice(self.all_queries)

        with self.client.post(
            "/query",
            json={"query": query, "retrieval_config": {"top_k": 5, "retrieval_mode": "dense"}},
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="query_basic",
        ) as response:
            self._validate_query_response(response, "basic")
            self.request_count += 1

    @task(5)  # Moderate frequency
    def query_hybrid(self):
        """
        Hybrid retrieval query - combines dense and sparse search.

        Weight: 5 (moderate frequency)
        Expected: <75ms p95 latency
        """
        query = random.choice(self.all_queries)

        with self.client.post(
            "/query",
            json={
                "query": query,
                "retrieval_config": {
                    "top_k": 10,
                    "retrieval_mode": "hybrid",
                    "rerank": True,
                    "alpha": 0.7,  # Dense/sparse balance
                },
            },
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="query_hybrid",
        ) as response:
            self._validate_query_response(response, "hybrid")
            self.request_count += 1

    @task(3)  # Lower frequency, higher resource usage
    def query_streaming(self):
        """
        Streaming query request - real-time response generation.

        Weight: 3 (lower frequency due to resource intensity)
        Expected: Initial response <100ms, streaming completion <5s
        """
        query = random.choice(self.all_queries)

        with self.client.post(
            "/query/stream",
            json={
                "query": query,
                "generation_config": {"stream": True, "max_tokens": 500, "temperature": 0.7},
                "retrieval_config": {"top_k": 5},
            },
            headers={"Content-Type": "application/json"},
            catch_response=True,
            stream=True,
            name="query_streaming",
        ) as response:
            self._validate_streaming_response(response)
            self.request_count += 1

    @task(2)  # Background load
    def ingest_document(self):
        """
        Document ingestion - simulates knowledge base updates.

        Weight: 2 (background task, lower frequency)
        Expected: <200ms for single document
        """
        template = random.choice(self.document_templates)
        topic = random.choice(self.topics)
        content = template.format(topic=topic)

        doc_id = f"load_test_{int(time.time())}_{random.randint(1000, 9999)}"

        with self.client.post(
            "/ingest",
            json={
                "documents": [
                    {
                        "id": doc_id,
                        "content": content,
                        "metadata": {
                            "source": "load_test",
                            "category": random.choice(list(self.queries.keys())),
                            "timestamp": time.time(),
                            "user_session": self.environment.runner.user_id
                            if hasattr(self.environment.runner, "user_id")
                            else "anonymous",
                        },
                    }
                ]
            },
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="ingest_document",
        ) as response:
            self._validate_ingestion_response(response)

    @task(1)  # Rare but important
    def health_check(self):
        """
        Health check endpoint - monitoring and diagnostics.

        Weight: 1 (monitoring task)
        Expected: <10ms response
        """
        with self.client.get("/health", catch_response=True, name="health_check") as response:
            if response.status_code == 200:
                try:
                    health_data = response.json()
                    if "status" in health_data:
                        response.success()
                    else:
                        response.failure("Invalid health response format")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON in health response")
            else:
                response.failure(f"Health check failed with status {response.status_code}")

    @task(1)  # Performance testing
    def batch_query(self):
        """
        Batch query processing - multiple queries in one request.

        Weight: 1 (performance testing)
        Expected: <200ms for 3 queries
        """
        queries = random.sample(self.all_queries, 3)

        with self.client.post(
            "/query/batch",
            json={"queries": queries, "retrieval_config": {"top_k": 3}},
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="batch_query",
        ) as response:
            if response.status_code == 200:
                try:
                    batch_results = response.json()
                    if isinstance(batch_results, list) and len(batch_results) == 3:
                        response.success()
                    else:
                        response.failure("Invalid batch response format")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON in batch response")
            else:
                response.failure(f"Batch query failed with status {response.status_code}")

    def _validate_query_response(self, response, query_type: str):
        """Validate standard query response format and performance."""
        if response.status_code == 200:
            try:
                result = response.json()

                # Validate required fields
                required_fields = ["answer", "sources", "metadata"]
                missing_fields = [field for field in required_fields if field not in result]

                if missing_fields:
                    response.failure(f"Missing required fields: {missing_fields}")
                    return

                # Validate answer quality
                if len(result["answer"]) < 10:
                    response.failure("Answer too short")
                    return

                # Validate sources
                if not result["sources"] or len(result["sources"]) == 0:
                    response.failure("No sources returned")
                    return

                # Performance validation
                response_time_ms = response.elapsed.total_seconds() * 1000

                if query_type == "basic" and response_time_ms > 100:
                    response.failure(f"Basic query too slow: {response_time_ms:.1f}ms")
                elif query_type == "hybrid" and response_time_ms > 150:
                    response.failure(f"Hybrid query too slow: {response_time_ms:.1f}ms")
                else:
                    response.success()

            except json.JSONDecodeError:
                response.failure("Invalid JSON response")
        else:
            response.failure(f"HTTP {response.status_code}: {response.text[:100]}")

    def _validate_streaming_response(self, response):
        """Validate streaming query response."""
        if response.status_code == 200:
            try:
                # Check if response headers indicate streaming
                content_type = response.headers.get("content-type", "")
                if "stream" not in content_type.lower():
                    response.failure("Response not marked as streaming")
                    return

                # For streaming, we can't easily validate content in Locust
                # but we can check that we got a valid response start
                response.success()

            except Exception as e:
                response.failure(f"Streaming validation error: {str(e)}")
        else:
            response.failure(f"Streaming request failed: {response.status_code}")

    def _validate_ingestion_response(self, response):
        """Validate document ingestion response."""
        if response.status_code == 200:
            try:
                result = response.json()
                if "status" in result and result["status"] == "success":
                    response.success()
                else:
                    response.failure("Ingestion did not report success")
            except json.JSONDecodeError:
                response.failure("Invalid JSON in ingestion response")
        else:
            response.failure(f"Ingestion failed: {response.status_code}")

    def on_stop(self):
        """Cleanup and final metrics when user stops."""
        session_duration = time.time() - self.session_start
        print(f"User session ended: {self.request_count} requests in {session_duration:.1f}s")


# Load test scenarios
class QuickLoadUser(RAGUser):
    """Lighter load for quick testing."""

    wait_time = between(2, 8)  # Slower request rate


class HeavyLoadUser(RAGUser):
    """Heavy load simulation for stress testing."""

    wait_time = between(0.5, 2)  # Faster request rate

    # Increase frequency of resource-intensive tasks
    @task(15)
    def query_basic(self):
        return super().query_basic()

    @task(10)
    def query_hybrid(self):
        return super().query_hybrid()

    @task(8)
    def query_streaming(self):
        return super().query_streaming()


# Custom events for detailed metrics
@events.request.add_listener
def record_custom_metrics(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Record custom performance metrics."""
    if exception is None and response:
        # Track response time percentiles by endpoint
        if hasattr(events.Environment, "stats"):
            pass  # Custom metrics would be implemented here


# Configuration for different test scenarios
def create_load_test_config():
    """Return configuration for different load test scenarios."""
    return {
        "baseline": {"users": 100, "spawn_rate": 10, "run_time": "5m", "description": "Baseline load test - 100 users"},
        "stress": {"users": 500, "spawn_rate": 25, "run_time": "10m", "description": "Stress test - 500 users"},
        "spike": {"users": 200, "spawn_rate": 50, "run_time": "2m", "description": "Spike test - rapid user ramp"},
        "endurance": {
            "users": 150,
            "spawn_rate": 5,
            "run_time": "30m",
            "description": "Endurance test - sustained load",
        },
    }
