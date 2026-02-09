"""
Evaluation Datasets for RAG System Benchmarking

Provides access to standard benchmarking datasets and custom evaluation data:
- MS MARCO passage ranking
- Natural Questions dataset
- Custom QA datasets
- Synthetic test data generation

Used for quality benchmarks measuring retrieval accuracy, relevance, and answer quality.
"""

import asyncio
import json
import random
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import numpy as np
    import pandas as pd
except ImportError:
    # Fallback for environments without pandas/numpy
    pd = None
    np = None


@dataclass
class EvaluationQuery:
    """Standard structure for evaluation queries."""

    query_id: str
    query_text: str
    relevant_docs: List[str]
    relevance_scores: List[float]
    domain: str
    difficulty: str
    metadata: Dict[str, Any]


@dataclass
class EvaluationDocument:
    """Standard structure for evaluation documents."""

    doc_id: str
    content: str
    title: str
    source: str
    metadata: Dict[str, Any]


@dataclass
class QAPair:
    """Question-answer pair with context for answer quality evaluation."""

    question: str
    answer: str
    context: List[str]
    metadata: Dict[str, Any]


class DatasetManager:
    """Central manager for evaluation datasets."""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize dataset manager with optional caching.

        Args:
            cache_dir: Directory for caching downloaded datasets
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.cache_dir = Path(tempfile.gettempdir()) / "rag_evaluation_cache"
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def load_ms_marco_subset(self, size: int = 1000, split: str = "dev") -> List[EvaluationQuery]:
        """
        Load MS MARCO passage ranking subset for retrieval evaluation.

        Args:
            size: Number of queries to load
            split: Dataset split ('train', 'dev', 'test')

        Returns:
            List of evaluation queries with relevance judgments
        """
        print(f"Loading MS MARCO subset: {size} queries from {split} split")

        # Simulate MS MARCO data structure for demo purposes
        # In production, this would download and parse the actual dataset
        queries = []

        query_templates = [
            "what is {topic} and how does it work",
            "how to implement {topic} in production",
            "benefits and drawbacks of {topic}",
            "best practices for {topic}",
            "common problems with {topic} and solutions",
            "performance optimization for {topic}",
            "security considerations for {topic}",
            "cost analysis of {topic} implementation",
            "integration challenges with {topic}",
            "monitoring and maintenance of {topic}",
        ]

        topics = [
            "vector databases",
            "semantic search",
            "embedding models",
            "retrieval systems",
            "information retrieval",
            "document ranking",
            "neural networks",
            "transformer models",
            "attention mechanisms",
            "natural language processing",
            "machine learning",
            "deep learning",
        ]

        for i in range(size):
            template = random.choice(query_templates)
            topic = random.choice(topics)
            query_text = template.format(topic=topic)

            # Generate relevant document IDs (simulated)
            num_relevant = random.randint(2, 6)
            relevant_docs = [f"marco_doc_{i}_{j}" for j in range(num_relevant)]

            # Generate relevance scores (0-3 scale as in MS MARCO)
            relevance_scores = [random.choice([0, 1, 2, 3]) for _ in relevant_docs]

            # Determine difficulty based on query complexity
            difficulty = (
                "easy" if len(query_text.split()) < 8 else ("hard" if len(query_text.split()) > 12 else "medium")
            )

            query = EvaluationQuery(
                query_id=f"marco_{split}_{i}",
                query_text=query_text,
                relevant_docs=relevant_docs,
                relevance_scores=relevance_scores,
                domain="information_retrieval",
                difficulty=difficulty,
                metadata={"dataset": "ms_marco", "split": split, "topic": topic, "template": template},
            )
            queries.append(query)

        await self._cache_dataset(f"ms_marco_{split}_{size}", queries)
        return queries

    async def load_natural_questions(self, size: int = 500, split: str = "dev") -> List[QAPair]:
        """
        Load Natural Questions dataset for answer quality evaluation.

        Args:
            size: Number of QA pairs to load
            split: Dataset split ('train', 'dev', 'test')

        Returns:
            List of question-answer pairs with context
        """
        print(f"Loading Natural Questions subset: {size} pairs from {split} split")

        # Simulate Natural Questions data structure
        qa_pairs = []

        question_templates = [
            "What is {entity} known for?",
            "When was {entity} established?",
            "How does {process} work?",
            "Where is {location} located?",
            "Who invented {invention}?",
            "Why is {concept} important?",
            "What are the benefits of {topic}?",
            "How can you {action}?",
            "What causes {phenomenon}?",
            "When did {event} happen?",
        ]

        entities = [
            "machine learning",
            "artificial intelligence",
            "vector databases",
            "semantic search",
            "natural language processing",
            "deep learning",
            "computer vision",
            "reinforcement learning",
            "neural networks",
            "information retrieval",
        ]

        for i in range(size):
            template = random.choice(question_templates)
            entity = random.choice(entities)

            # Replace placeholders based on template type
            if "{entity}" in template:
                question = template.format(entity=entity)
            elif "{process}" in template:
                question = template.format(process=f"{entity} processing")
            elif "{location}" in template:
                question = template.format(location=f"{entity} research centers")
            elif "{invention}" in template:
                question = template.format(invention=entity)
            elif "{concept}" in template:
                question = template.format(concept=entity)
            elif "{topic}" in template:
                question = template.format(topic=entity)
            elif "{action}" in template:
                question = template.format(action=f"implement {entity}")
            elif "{phenomenon}" in template:
                question = template.format(phenomenon=f"{entity} behavior")
            elif "{event}" in template:
                question = template.format(event=f"{entity} development")
            else:
                question = template

            # Generate answer and context
            answer = (
                f"{entity.title()} is a fundamental concept in computer science and artificial intelligence. "
                f"It involves sophisticated algorithms and techniques that enable machines to process and understand data. "
                f"The field has evolved significantly over recent years with advances in computational power and methodology."
            )

            context = [
                f"Technical documentation about {entity} and its applications",
                f"Research paper on {entity} methodologies and best practices",
                f"Industry report covering {entity} implementation strategies",
                f"Academic textbook chapter on {entity} fundamentals",
            ]

            qa_pair = QAPair(
                question=question,
                answer=answer,
                context=context,
                metadata={
                    "dataset": "natural_questions",
                    "split": split,
                    "entity": entity,
                    "template": template,
                    "answer_length": len(answer.split()),
                },
            )
            qa_pairs.append(qa_pair)

        await self._cache_dataset(f"natural_questions_{split}_{size}", qa_pairs)
        return qa_pairs

    async def load_custom_qa(self, path: str) -> List[QAPair]:
        """
        Load custom QA dataset from file.

        Args:
            path: Path to JSON or CSV file with QA data

        Returns:
            List of question-answer pairs
        """
        file_path = Path(path)

        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        if file_path.suffix == ".json":
            return await self._load_json_qa(file_path)
        elif file_path.suffix == ".csv":
            return await self._load_csv_qa(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    async def create_synthetic_evaluation_set(
        self,
        num_queries: int = 100,
        domains: Optional[List[str]] = None,
        difficulty_distribution: Optional[Dict[str, float]] = None,
    ) -> List[EvaluationQuery]:
        """
        Create synthetic evaluation dataset for testing.

        Args:
            num_queries: Number of queries to generate
            domains: List of domains to cover
            difficulty_distribution: Distribution of difficulty levels

        Returns:
            List of synthetic evaluation queries
        """
        if domains is None:
            domains = ["technical", "business", "operational", "research"]

        if difficulty_distribution is None:
            difficulty_distribution = {"easy": 0.3, "medium": 0.5, "hard": 0.2}

        queries = []

        # Technical domain queries
        technical_patterns = [
            ("How to implement {technology} in {context}?", "medium"),
            ("What are the performance characteristics of {technology}?", "hard"),
            ("Explain the architecture of {technology}", "easy"),
            ("Best practices for {technology} optimization", "medium"),
            ("Troubleshooting common {technology} issues", "hard"),
            ("Integration patterns for {technology}", "medium"),
            ("Security considerations for {technology}", "hard"),
            ("Monitoring and observability for {technology}", "medium"),
        ]

        technologies = [
            "vector databases",
            "embedding models",
            "semantic search",
            "retrieval systems",
            "neural networks",
            "transformer models",
            "attention mechanisms",
            "language models",
        ]

        contexts = [
            "production environments",
            "cloud platforms",
            "enterprise systems",
            "real-time applications",
            "distributed systems",
            "microservices",
        ]

        for i in range(num_queries):
            # Select domain
            domain = random.choice(domains)

            if domain == "technical":
                pattern, base_difficulty = random.choice(technical_patterns)
                technology = random.choice(technologies)
                context = random.choice(contexts)
                query_text = pattern.format(technology=technology, context=context)

                # Generate relevant documents
                num_docs = random.randint(3, 7)
                relevant_docs = [f"synthetic_doc_{domain}_{i}_{j}" for j in range(num_docs)]

                # Generate relevance scores with some noise
                base_scores = [3, 3, 2, 2, 1, 1, 0]
                relevance_scores = random.sample(base_scores, num_docs)

            else:
                # Generate for other domains similarly
                query_text = f"Sample {domain} query about system implementation {i}"
                relevant_docs = [f"synthetic_doc_{domain}_{i}_{j}" for j in range(random.randint(2, 5))]
                relevance_scores = [random.randint(0, 3) for _ in relevant_docs]
                base_difficulty = random.choice(list(difficulty_distribution.keys()))

            # Apply difficulty distribution
            difficulty = (
                base_difficulty
                if random.random() < difficulty_distribution.get(base_difficulty, 0.33)
                else random.choice(list(difficulty_distribution.keys()))
            )

            query = EvaluationQuery(
                query_id=f"synthetic_{domain}_{i}",
                query_text=query_text,
                relevant_docs=relevant_docs,
                relevance_scores=relevance_scores,
                domain=domain,
                difficulty=difficulty,
                metadata={
                    "dataset": "synthetic",
                    "generation_timestamp": datetime.now().isoformat(),
                    "pattern": pattern if domain == "technical" else None,
                },
            )
            queries.append(query)

        await self._cache_dataset(f"synthetic_{num_queries}_{len(domains)}", queries)
        return queries

    async def create_adversarial_test_set(self, size: int = 50) -> List[EvaluationQuery]:
        """
        Create adversarial test cases to challenge retrieval system.

        Args:
            size: Number of adversarial queries to generate

        Returns:
            List of challenging evaluation queries
        """
        adversarial_queries = []

        # Different types of challenging queries
        challenge_types = [
            "ambiguous",  # Multiple valid interpretations
            "negation",  # Queries with negation that can confuse systems
            "multi_intent",  # Queries with multiple intents
            "domain_shift",  # Queries that span multiple domains
            "temporal",  # Time-sensitive queries
            "comparative",  # Queries requiring comparison
            "causal",  # Queries about cause and effect
            "counterfactual",  # What-if scenarios
        ]

        for i in range(size):
            challenge_type = random.choice(challenge_types)

            if challenge_type == "ambiguous":
                query_text = "How to scale systems effectively?"  # Could mean performance, team, or business scaling
                relevant_docs = [f"ambiguous_doc_{i}_{j}" for j in range(5)]
                relevance_scores = [2, 2, 2, 1, 1]  # Multiple moderately relevant docs

            elif challenge_type == "negation":
                query_text = "What should NOT be done when implementing vector search?"
                relevant_docs = [f"negation_doc_{i}_{j}" for j in range(4)]
                relevance_scores = [3, 3, 2, 1]

            elif challenge_type == "multi_intent":
                query_text = "Compare vector databases, explain implementation costs, and provide migration strategies"
                relevant_docs = [f"multi_intent_doc_{i}_{j}" for j in range(8)]
                relevance_scores = [3, 3, 3, 2, 2, 2, 1, 1]

            else:
                # Default challenging query
                query_text = f"Complex {challenge_type} query about system interactions"
                relevant_docs = [f"{challenge_type}_doc_{i}_{j}" for j in range(random.randint(3, 6))]
                relevance_scores = [random.randint(1, 3) for _ in relevant_docs]

            query = EvaluationQuery(
                query_id=f"adversarial_{challenge_type}_{i}",
                query_text=query_text,
                relevant_docs=relevant_docs,
                relevance_scores=relevance_scores,
                domain="adversarial",
                difficulty="hard",
                metadata={
                    "dataset": "adversarial",
                    "challenge_type": challenge_type,
                    "expected_challenge": f"Tests system robustness to {challenge_type} queries",
                },
            )
            adversarial_queries.append(query)

        await self._cache_dataset(f"adversarial_{size}", adversarial_queries)
        return adversarial_queries

    async def get_benchmark_suite(self) -> Dict[str, List[Any]]:
        """
        Get complete benchmark suite with multiple dataset types.

        Returns:
            Dictionary with different benchmark datasets
        """
        suite = {}

        # Load different dataset types
        suite["ms_marco_dev"] = await self.load_ms_marco_subset(200, "dev")
        suite["natural_questions"] = await self.load_natural_questions(100)
        suite["synthetic"] = await self.create_synthetic_evaluation_set(150)
        suite["adversarial"] = await self.create_adversarial_test_set(50)

        return suite

    # Private helper methods

    async def _cache_dataset(self, name: str, data: List[Any]) -> None:
        """Cache dataset to disk for reuse."""
        cache_file = self.cache_dir / f"{name}.json"

        # Convert dataclass objects to dictionaries for JSON serialization
        serializable_data = []
        for item in data:
            if hasattr(item, "__dict__"):
                serializable_data.append(asdict(item))
            else:
                serializable_data.append(item)

        try:
            with cache_file.open("w") as f:
                json.dump(
                    {
                        "metadata": {
                            "timestamp": datetime.now().isoformat(),
                            "size": len(data),
                            "type": type(data[0]).__name__ if data else "empty",
                        },
                        "data": serializable_data,
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            print(f"Warning: Could not cache dataset {name}: {e}")

    async def _load_json_qa(self, file_path: Path) -> List[QAPair]:
        """Load QA pairs from JSON file."""
        with file_path.open("r") as f:
            data = json.load(f)

        qa_pairs = []
        for item in data:
            qa_pair = QAPair(
                question=item["question"],
                answer=item["answer"],
                context=item.get("context", []),
                metadata=item.get("metadata", {}),
            )
            qa_pairs.append(qa_pair)

        return qa_pairs

    async def _load_csv_qa(self, file_path: Path) -> List[QAPair]:
        """Load QA pairs from CSV file."""
        if pd is None:
            raise ImportError("pandas required for CSV loading")

        df = pd.read_csv(file_path)
        qa_pairs = []

        for _, row in df.iterrows():
            qa_pair = QAPair(
                question=row["question"],
                answer=row["answer"],
                context=row.get("context", "").split("|") if "context" in row else [],
                metadata={"source": "csv", "row_id": row.name},
            )
            qa_pairs.append(qa_pair)

        return qa_pairs


# Convenience functions for direct access
async def get_retrieval_benchmark(size: int = 1000) -> List[EvaluationQuery]:
    """Get standard retrieval benchmark dataset."""
    manager = DatasetManager()
    return await manager.load_ms_marco_subset(size)


async def get_qa_benchmark(size: int = 500) -> List[QAPair]:
    """Get standard QA benchmark dataset."""
    manager = DatasetManager()
    return await manager.load_natural_questions(size)


async def get_full_benchmark_suite() -> Dict[str, List[Any]]:
    """Get complete benchmark suite for comprehensive evaluation."""
    manager = DatasetManager()
    return await manager.get_benchmark_suite()


# Example usage and testing
if __name__ == "__main__":

    async def main():
        print("Testing evaluation datasets...")

        manager = DatasetManager()

        # Test MS MARCO loading
        print("\n1. Loading MS MARCO subset...")
        ms_marco = await manager.load_ms_marco_subset(10)
        print(f"Loaded {len(ms_marco)} MS MARCO queries")
        print(f"Sample query: {ms_marco[0].query_text}")

        # Test Natural Questions loading
        print("\n2. Loading Natural Questions subset...")
        nq = await manager.load_natural_questions(5)
        print(f"Loaded {len(nq)} Natural Questions pairs")
        print(f"Sample question: {nq[0].question}")

        # Test synthetic data generation
        print("\n3. Creating synthetic evaluation set...")
        synthetic = await manager.create_synthetic_evaluation_set(20)
        print(f"Generated {len(synthetic)} synthetic queries")
        print(f"Sample synthetic query: {synthetic[0].query_text}")

        # Test adversarial data generation
        print("\n4. Creating adversarial test set...")
        adversarial = await manager.create_adversarial_test_set(5)
        print(f"Generated {len(adversarial)} adversarial queries")
        print(f"Sample adversarial query: {adversarial[0].query_text}")

        print("\nDataset generation test completed successfully!")

    # Run the test
    asyncio.run(main())
