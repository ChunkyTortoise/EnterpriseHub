"""
Test Data Generation for RAG System Benchmarks

Generates synthetic documents, queries, and ground truth data for:
- Performance benchmarking
- Quality evaluation
- Load testing
- Integration testing

Provides consistent, reproducible test data across benchmark runs.
"""

import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class Document:
    """Standard document structure for testing."""

    id: str
    content: str
    title: str
    source: str
    metadata: Dict[str, Any]
    created_at: str
    embedding: Optional[List[float]] = None


@dataclass
class TestQuery:
    """Test query with expected results."""

    id: str
    query: str
    expected_docs: List[str]
    relevance_scores: List[float]
    category: str
    difficulty: str
    metadata: Dict[str, Any]


class TestDataGenerator:
    """Generate comprehensive test data for RAG system evaluation."""

    def __init__(self, seed: int = 42):
        """
        Initialize generator with random seed for reproducibility.

        Args:
            seed: Random seed for consistent data generation
        """
        random.seed(seed)
        self.seed = seed

        # Domain-specific content templates
        self.content_templates = {
            "technical": [
                "The {technology} system implements {concept} through {method}. "
                "Key benefits include {benefit1}, {benefit2}, and {benefit3}. "
                "Implementation requires {requirement1} and {requirement2}. "
                "Performance characteristics show {performance} under typical workloads. "
                "Common challenges include {challenge1} and {challenge2}. "
                "Best practices recommend {practice1}, {practice2}, and regular {practice3}.",
                "{technology} architecture consists of {component1}, {component2}, and {component3}. "
                "The {component1} handles {responsibility1} while {component2} manages {responsibility2}. "
                "Scalability is achieved through {scaling_method} and {optimization}. "
                "Monitoring involves tracking {metric1}, {metric2}, and {metric3}. "
                "Troubleshooting typically focuses on {issue1} and {issue2}.",
                "Advanced {technology} features include {feature1}, {feature2}, and {feature3}. "
                "The {feature1} enables {capability1} through {mechanism}. "
                "Integration patterns support {pattern1} and {pattern2} architectures. "
                "Security considerations include {security1}, {security2}, and {security3}. "
                "Future developments focus on {development1} and {development2}.",
            ],
            "business": [
                "The business impact of {technology} includes {impact1}, {impact2}, and {impact3}. "
                "ROI analysis shows {roi_metric} improvement over {timeframe}. "
                "Implementation costs typically involve {cost1}, {cost2}, and {cost3}. "
                "Risk factors include {risk1} and {risk2}, mitigated by {mitigation}. "
                "Success metrics focus on {metric1}, {metric2}, and {metric3}.",
                "Market analysis reveals {trend1} and {trend2} in {technology} adoption. "
                "Competitive advantages include {advantage1}, {advantage2}, and {advantage3}. "
                "Customer requirements emphasize {requirement1} and {requirement2}. "
                "Pricing strategies consider {factor1}, {factor2}, and {factor3}. "
                "Partnership opportunities exist in {area1} and {area2}.",
                "Strategic planning for {technology} involves {strategy1}, {strategy2}, and {strategy3}. "
                "Resource allocation prioritizes {priority1} and {priority2}. "
                "Timeline considerations include {milestone1}, {milestone2}, and {milestone3}. "
                "Stakeholder engagement requires {engagement1} and {engagement2}. "
                "Success criteria are measured by {criteria1} and {criteria2}.",
            ],
            "operational": [
                "Operational procedures for {technology} include {procedure1}, {procedure2}, and {procedure3}. "
                "Daily maintenance involves {task1}, {task2}, and {task3}. "
                "Monitoring dashboards track {indicator1}, {indicator2}, and {indicator3}. "
                "Alert thresholds are set for {threshold1} and {threshold2}. "
                "Recovery procedures address {scenario1} and {scenario2}.",
                "Performance optimization focuses on {optimization1}, {optimization2}, and {optimization3}. "
                "Capacity planning considers {factor1}, {factor2}, and {factor3}. "
                "Backup strategies include {strategy1} and {strategy2}. "
                "Security protocols enforce {protocol1}, {protocol2}, and {protocol3}. "
                "Compliance requirements mandate {requirement1} and {requirement2}.",
                "Incident response procedures cover {incident1}, {incident2}, and {incident3}. "
                "Escalation paths involve {escalation1} and {escalation2}. "
                "Documentation standards require {standard1} and {standard2}. "
                "Training programs address {training1} and {training2}. "
                "Quality assurance includes {qa1} and {qa2}.",
            ],
        }

        # Technology domains
        self.technologies = [
            "vector databases",
            "semantic search",
            "embedding models",
            "retrieval systems",
            "neural networks",
            "transformer models",
            "attention mechanisms",
            "language models",
            "information retrieval",
            "machine learning",
            "deep learning",
            "natural language processing",
        ]

        # Content vocabulary for template filling
        self.vocabulary = {
            "concept": [
                "semantic similarity",
                "vector indexing",
                "dense retrieval",
                "sparse retrieval",
                "hybrid search",
                "neural ranking",
                "attention mechanisms",
                "contextual understanding",
            ],
            "method": [
                "HNSW indexing",
                "LSH hashing",
                "k-means clustering",
                "transformer encoding",
                "contrastive learning",
                "metric learning",
                "fine-tuning",
                "distillation",
            ],
            "benefit1": ["improved accuracy", "faster retrieval", "better scalability", "reduced latency"],
            "benefit2": ["enhanced relevance", "lower costs", "simplified architecture", "better user experience"],
            "benefit3": ["easier maintenance", "improved reliability", "better security", "increased throughput"],
            "requirement1": ["sufficient compute resources", "high-quality training data", "proper indexing"],
            "requirement2": ["careful hyperparameter tuning", "robust monitoring", "effective caching"],
            "performance": ["sub-100ms query latency", "95%+ accuracy", "linear scalability", "99.9% uptime"],
            "challenge1": ["data quality issues", "computational complexity", "memory constraints"],
            "challenge2": ["cold start problems", "domain adaptation", "evaluation difficulties"],
            "practice1": ["regular reindexing", "continuous monitoring", "automated testing"],
            "practice2": ["proper data preprocessing", "effective caching strategies", "security audits"],
            "practice3": ["performance tuning", "backup procedures", "documentation updates"],
        }

    def generate_synthetic_documents(
        self, count: int = 1000, domains: Optional[List[str]] = None, min_length: int = 100, max_length: int = 500
    ) -> List[Document]:
        """
        Generate synthetic documents for testing.

        Args:
            count: Number of documents to generate
            domains: List of content domains to cover
            min_length: Minimum document length in words
            max_length: Maximum document length in words

        Returns:
            List of synthetic documents
        """
        if domains is None:
            domains = list(self.content_templates.keys())

        documents = []

        for i in range(count):
            # Select domain and technology
            domain = random.choice(domains)
            technology = random.choice(self.technologies)

            # Generate content using template
            template = random.choice(self.content_templates[domain])
            content = self._fill_template(template, technology)

            # Extend content to meet length requirements
            target_length = random.randint(min_length, max_length)
            while len(content.split()) < target_length:
                additional_template = random.choice(self.content_templates[domain])
                additional_content = self._fill_template(additional_template, technology)
                content += f" {additional_content}"

            # Trim if too long
            if len(content.split()) > max_length:
                words = content.split()[:max_length]
                content = " ".join(words)

            # Generate document metadata
            doc_id = f"synthetic_doc_{domain}_{i:06d}"
            title = self._generate_title(technology, domain)
            source = f"{domain}_documentation_{i // 100}.txt"

            # Create document
            document = Document(
                id=doc_id,
                content=content,
                title=title,
                source=source,
                metadata={
                    "domain": domain,
                    "technology": technology,
                    "synthetic": True,
                    "generation_seed": self.seed,
                    "word_count": len(content.split()),
                    "char_count": len(content),
                },
                created_at=self._generate_timestamp(i, count),
            )

            documents.append(document)

        return documents

    def generate_test_queries(
        self, count: int = 100, documents: Optional[List[Document]] = None, query_types: Optional[List[str]] = None
    ) -> List[TestQuery]:
        """
        Generate test queries with ground truth relevance.

        Args:
            count: Number of queries to generate
            documents: Document collection for relevance mapping
            query_types: Types of queries to generate

        Returns:
            List of test queries with expected results
        """
        if query_types is None:
            query_types = ["factual", "conceptual", "procedural", "comparative", "analytical"]

        queries = []

        # Group documents by domain and technology for relevant mapping
        doc_groups = {}
        if documents:
            for doc in documents:
                domain = doc.metadata.get("domain", "general")
                technology = doc.metadata.get("technology", "unknown")
                key = f"{domain}_{technology}"
                if key not in doc_groups:
                    doc_groups[key] = []
                doc_groups[key].append(doc)

        for i in range(count):
            query_type = random.choice(query_types)
            domain = random.choice(list(self.content_templates.keys()))
            technology = random.choice(self.technologies)

            # Generate query based on type
            query_text = self._generate_query(query_type, technology, domain)

            # Find relevant documents
            if documents and doc_groups:
                expected_docs, relevance_scores = self._find_relevant_documents(
                    query_text, technology, domain, doc_groups
                )
            else:
                # Generate synthetic relevance when no documents provided
                num_relevant = random.randint(3, 8)
                expected_docs = [f"doc_{i}_{j}" for j in range(num_relevant)]
                relevance_scores = self._generate_relevance_scores(num_relevant)

            # Determine difficulty
            difficulty = self._assess_query_difficulty(query_text, query_type)

            query = TestQuery(
                id=f"test_query_{i:06d}",
                query=query_text,
                expected_docs=expected_docs,
                relevance_scores=relevance_scores,
                category=f"{domain}_{query_type}",
                difficulty=difficulty,
                metadata={
                    "query_type": query_type,
                    "domain": domain,
                    "technology": technology,
                    "synthetic": True,
                    "generation_seed": self.seed,
                },
            )

            queries.append(query)

        return queries

    def generate_performance_test_data(
        self, num_documents: int = 10000, num_queries: int = 1000, complexity_levels: Optional[List[str]] = None
    ) -> Tuple[List[Document], List[TestQuery]]:
        """
        Generate comprehensive test data for performance benchmarking.

        Args:
            num_documents: Number of documents in test corpus
            num_queries: Number of test queries
            complexity_levels: Query complexity levels to include

        Returns:
            Tuple of (documents, queries) for performance testing
        """
        if complexity_levels is None:
            complexity_levels = ["simple", "medium", "complex"]

        # Generate documents with varied characteristics
        documents = []

        # Distribution of document types
        domain_distribution = {"technical": 0.4, "business": 0.3, "operational": 0.3}

        for domain, ratio in domain_distribution.items():
            domain_count = int(num_documents * ratio)

            # Vary document lengths for realistic distribution
            short_docs = int(domain_count * 0.3)  # 50-150 words
            medium_docs = int(domain_count * 0.5)  # 150-400 words
            long_docs = domain_count - short_docs - medium_docs  # 400-800 words

            # Generate short documents
            documents.extend(self.generate_synthetic_documents(short_docs, [domain], 50, 150))

            # Generate medium documents
            documents.extend(self.generate_synthetic_documents(medium_docs, [domain], 150, 400))

            # Generate long documents
            documents.extend(self.generate_synthetic_documents(long_docs, [domain], 400, 800))

        # Generate queries with complexity distribution
        queries = []
        complexity_distribution = {"simple": 0.5, "medium": 0.3, "complex": 0.2}

        for complexity, ratio in complexity_distribution.items():
            complexity_count = int(num_queries * ratio)

            # Adjust query types based on complexity
            if complexity == "simple":
                query_types = ["factual", "conceptual"]
            elif complexity == "medium":
                query_types = ["procedural", "comparative"]
            else:
                query_types = ["analytical", "multi_intent"]

            complexity_queries = self.generate_test_queries(complexity_count, documents, query_types)

            # Override difficulty based on complexity level
            for query in complexity_queries:
                query.difficulty = complexity

            queries.extend(complexity_queries)

        return documents, queries

    def save_test_data(self, documents: List[Document], queries: List[TestQuery], output_dir: str) -> Dict[str, str]:
        """
        Save generated test data to files.

        Args:
            documents: Generated documents
            queries: Generated queries
            output_dir: Output directory path

        Returns:
            Dictionary with file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save documents
        docs_file = output_path / "test_documents.json"
        with docs_file.open("w") as f:
            json.dump([asdict(doc) for doc in documents], f, indent=2)

        # Save queries
        queries_file = output_path / "test_queries.json"
        with queries_file.open("w") as f:
            json.dump([asdict(query) for query in queries], f, indent=2)

        # Save metadata
        metadata_file = output_path / "test_metadata.json"
        metadata = {
            "generation_timestamp": datetime.now().isoformat(),
            "seed": self.seed,
            "document_count": len(documents),
            "query_count": len(queries),
            "domains": list(set(doc.metadata.get("domain", "unknown") for doc in documents)),
            "technologies": list(set(doc.metadata.get("technology", "unknown") for doc in documents)),
            "statistics": {
                "avg_doc_length": sum(len(doc.content.split()) for doc in documents) / len(documents),
                "avg_query_length": sum(len(query.query.split()) for query in queries) / len(queries),
                "difficulty_distribution": self._calculate_difficulty_distribution(queries),
            },
        }

        with metadata_file.open("w") as f:
            json.dump(metadata, f, indent=2)

        return {"documents": str(docs_file), "queries": str(queries_file), "metadata": str(metadata_file)}

    # Private helper methods

    def _fill_template(self, template: str, technology: str) -> str:
        """Fill template with vocabulary and technology."""
        content = template.format(technology=technology)

        # Replace remaining placeholders with vocabulary
        for placeholder in self.vocabulary:
            if f"{{{placeholder}}}" in content:
                replacement = random.choice(self.vocabulary[placeholder])
                content = content.replace(f"{{{placeholder}}}", replacement)

        # Fill any remaining generic placeholders
        placeholders = [
            "component1",
            "component2",
            "component3",
            "responsibility1",
            "responsibility2",
            "scaling_method",
            "optimization",
            "metric1",
            "metric2",
            "metric3",
            "issue1",
            "issue2",
            "feature1",
            "feature2",
            "feature3",
            "capability1",
            "mechanism",
            "pattern1",
            "pattern2",
            "security1",
            "security2",
            "security3",
            "development1",
            "development2",
        ]

        for placeholder in placeholders:
            if f"{{{placeholder}}}" in content:
                # Generate appropriate replacement based on placeholder type
                if placeholder.startswith("component"):
                    replacement = f"{random.choice(['data', 'processing', 'storage', 'interface', 'control'])} layer"
                elif placeholder.startswith("responsibility"):
                    replacement = f"{random.choice(['data management', 'query processing', 'result ranking', 'cache management'])}"
                elif placeholder.startswith("metric"):
                    replacement = (
                        f"{random.choice(['latency', 'throughput', 'accuracy', 'memory usage', 'CPU utilization'])}"
                    )
                else:
                    replacement = f"system {placeholder.replace('1', '').replace('2', '').replace('3', '')}"

                content = content.replace(f"{{{placeholder}}}", replacement)

        return content

    def _generate_title(self, technology: str, domain: str) -> str:
        """Generate appropriate title for document."""
        title_patterns = [
            f"{technology.title()} Implementation Guide",
            f"Advanced {technology.title()} Concepts",
            f"{technology.title()} Best Practices",
            f"Understanding {technology.title()} Architecture",
            f"{technology.title()} Performance Optimization",
            f"{domain.title()} Guide to {technology.title()}",
            f"{technology.title()} Troubleshooting Manual",
        ]
        return random.choice(title_patterns)

    def _generate_timestamp(self, index: int, total: int) -> str:
        """Generate realistic timestamp for document creation."""
        days_back = random.randint(1, 365)
        base_time = datetime.now() - timedelta(days=days_back)
        # Add some ordering based on index
        time_offset = timedelta(hours=index * 24 // total)
        return (base_time + time_offset).isoformat()

    def _generate_query(self, query_type: str, technology: str, domain: str) -> str:
        """Generate query based on type and technology."""
        query_patterns = {
            "factual": [
                f"What is {technology}?",
                f"Define {technology} and its components",
                f"Explain the concept of {technology}",
                f"What are the key features of {technology}?",
            ],
            "conceptual": [
                f"How does {technology} work?",
                f"What are the principles behind {technology}?",
                f"Explain the architecture of {technology}",
                f"What is the theory behind {technology}?",
            ],
            "procedural": [
                f"How to implement {technology}?",
                f"Steps to deploy {technology} in production",
                f"Best practices for {technology} implementation",
                f"How to configure {technology} for optimal performance?",
            ],
            "comparative": [
                f"Compare {technology} with alternative approaches",
                f"What are the advantages of {technology}?",
                f"When should you use {technology}?",
                f"What are the trade-offs of {technology}?",
            ],
            "analytical": [
                f"Analyze the performance characteristics of {technology}",
                f"What factors affect {technology} efficiency?",
                f"Evaluate the scalability of {technology}",
                f"What are the limitations of {technology}?",
            ],
        }

        patterns = query_patterns.get(query_type, query_patterns["factual"])
        return random.choice(patterns)

    def _find_relevant_documents(
        self, query: str, technology: str, domain: str, doc_groups: Dict[str, List[Document]]
    ) -> Tuple[List[str], List[float]]:
        """Find relevant documents and generate relevance scores."""
        # Primary match: same technology and domain
        primary_key = f"{domain}_{technology}"
        primary_docs = doc_groups.get(primary_key, [])

        # Secondary match: same technology, different domain
        secondary_docs = []
        for key, docs in doc_groups.items():
            if key.endswith(f"_{technology}") and key != primary_key:
                secondary_docs.extend(docs[:2])  # Limit secondary matches

        # Combine and score
        relevant_docs = []
        relevance_scores = []

        # High relevance for primary matches
        for doc in primary_docs[:4]:  # Top 4 primary matches
            relevant_docs.append(doc.id)
            relevance_scores.append(random.uniform(2.5, 3.0))

        # Medium relevance for secondary matches
        for doc in secondary_docs[:3]:  # Top 3 secondary matches
            relevant_docs.append(doc.id)
            relevance_scores.append(random.uniform(1.5, 2.5))

        # Low relevance for random matches
        all_docs = [doc for docs in doc_groups.values() for doc in docs]
        random_docs = random.sample(all_docs, min(2, len(all_docs)))
        for doc in random_docs:
            if doc.id not in relevant_docs:
                relevant_docs.append(doc.id)
                relevance_scores.append(random.uniform(0.5, 1.5))

        return relevant_docs, relevance_scores

    def _generate_relevance_scores(self, num_docs: int) -> List[float]:
        """Generate realistic relevance scores distribution."""
        scores = []

        # High relevance (2-3)
        high_count = max(1, num_docs // 3)
        scores.extend([random.uniform(2.0, 3.0) for _ in range(high_count)])

        # Medium relevance (1-2)
        medium_count = max(1, num_docs // 2)
        scores.extend([random.uniform(1.0, 2.0) for _ in range(medium_count)])

        # Low relevance (0-1)
        remaining = num_docs - len(scores)
        scores.extend([random.uniform(0.0, 1.0) for _ in range(remaining)])

        return scores[:num_docs]

    def _assess_query_difficulty(self, query: str, query_type: str) -> str:
        """Assess query difficulty based on characteristics."""
        words = query.split()

        if len(words) < 6 and query_type in ["factual", "conceptual"]:
            return "easy"
        elif len(words) > 12 or query_type in ["analytical", "comparative"]:
            return "hard"
        else:
            return "medium"

    def _calculate_difficulty_distribution(self, queries: List[TestQuery]) -> Dict[str, float]:
        """Calculate distribution of difficulty levels."""
        difficulties = [query.difficulty for query in queries]
        total = len(difficulties)

        return {difficulty: difficulties.count(difficulty) / total for difficulty in set(difficulties)}


# Convenience functions for common use cases


def generate_benchmark_data(
    num_docs: int = 1000, num_queries: int = 100, output_dir: str = "test_data", seed: int = 42
) -> Dict[str, str]:
    """Generate complete benchmark dataset."""
    generator = TestDataGenerator(seed)
    documents, queries = generator.generate_performance_test_data(num_docs, num_queries)
    return generator.save_test_data(documents, queries, output_dir)


def generate_quick_test_data(output_dir: str = "quick_test_data") -> Dict[str, str]:
    """Generate small dataset for quick testing."""
    return generate_benchmark_data(100, 20, output_dir)


def generate_load_test_data(output_dir: str = "load_test_data") -> Dict[str, str]:
    """Generate large dataset for load testing."""
    return generate_benchmark_data(10000, 1000, output_dir)


# Example usage
if __name__ == "__main__":
    print("Generating test data...")

    # Quick test
    generator = TestDataGenerator()

    # Generate small dataset for demonstration
    docs = generator.generate_synthetic_documents(10)
    queries = generator.generate_test_queries(5, docs)

    print(f"Generated {len(docs)} documents and {len(queries)} queries")
    print(f"Sample document title: {docs[0].title}")
    print(f"Sample query: {queries[0].query}")

    # Generate and save performance test data
    files = generate_quick_test_data("demo_data")
    print(f"Saved test data to: {files}")

    print("Test data generation completed successfully!")
