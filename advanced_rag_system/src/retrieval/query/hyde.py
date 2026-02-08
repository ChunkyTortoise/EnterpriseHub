"""HyDE (Hypothetical Document Embedding) implementation.

HyDE improves retrieval by generating hypothetical documents that would
answer the query, then using those documents for embedding-based search.
This often improves semantic matching compared to query-only embeddings.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from src.core.exceptions import RetrievalError


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers used by HyDE generation.

    Any object implementing this interface can be used as the LLM backend
    for hypothetical document generation. The ``MockLLMProvider`` class
    provides a concrete implementation for testing.
    """

    async def generate(self, prompt: str, max_length: int = 512, temperature: float = 0.3) -> str:
        """Generate text from a prompt.

        Args:
            prompt: Input prompt text
            max_length: Maximum response length
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Generated text string
        """
        ...


@dataclass
class HyDEConfig:
    """Configuration for HyDE generation.

    Attributes:
        num_hypotheticals: Number of hypothetical documents to generate
        max_length: Maximum length of generated hypothetical documents
        temperature: Temperature for LLM generation (0.0-1.0)
        model: Model to use for generation
        use_caching: Whether to cache generated documents
        cache_ttl: Cache time-to-live in seconds
        prompt_template: Template for generating hypothetical documents
    """

    num_hypotheticals: int = 1
    max_length: int = 512
    temperature: float = 0.3
    model: str = "gpt-3.5-turbo"
    use_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    prompt_template: Optional[str] = None

    def __post_init__(self):
        """Initialize default prompt template if not provided."""
        if self.prompt_template is None:
            self.prompt_template = """Please write a detailed, informative paragraph that would answer the following question or query:

Query: {query}

Write a comprehensive response that includes relevant details, explanations, and context that would be found in a high-quality document addressing this topic. Focus on being factual and informative.

Response:"""


class MockLLMProvider:
    """Mock LLM provider for development and testing.

    This provides realistic hypothetical document generation without
    requiring external LLM API calls. Useful for testing and development.
    """

    def __init__(self, model: str = "mock-llm"):
        """Initialize mock LLM provider."""
        self.model = model

    async def generate(self, prompt: str, max_length: int = 512, temperature: float = 0.3) -> str:
        """Generate mock hypothetical document.

        Args:
            prompt: Input prompt
            max_length: Maximum response length
            temperature: Generation temperature

        Returns:
            Generated hypothetical document
        """
        # Extract query from prompt
        query = self._extract_query_from_prompt(prompt)

        # Generate realistic hypothetical document based on query content
        return self._generate_mock_document(query, max_length)

    def _extract_query_from_prompt(self, prompt: str) -> str:
        """Extract query from HyDE prompt."""
        # Simple extraction - look for "Query:" line
        lines = prompt.split("\n")
        for line in lines:
            if line.strip().startswith("Query:"):
                return line.strip().replace("Query:", "").strip()
        return "machine learning"  # Default fallback

    def _generate_mock_document(self, query: str, max_length: int) -> str:
        """Generate a realistic mock document for the query."""
        query_lower = query.lower()

        # Domain-specific mock responses
        mock_responses = {
            "machine learning": """Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed. It involves algorithms that can identify patterns in data and make predictions or decisions. Common techniques include supervised learning, unsupervised learning, and reinforcement learning. Popular algorithms include linear regression, decision trees, neural networks, and support vector machines. Machine learning applications span many fields including image recognition, natural language processing, recommendation systems, and predictive analytics.""",
            "neural networks": """Neural networks are computational models inspired by biological neural networks in animal brains. They consist of interconnected nodes or neurons organized in layers, including input layers, hidden layers, and output layers. Each connection has an associated weight that adjusts during training through backpropagation. Deep neural networks with multiple hidden layers enable deep learning, which has achieved remarkable success in tasks like image classification, speech recognition, and natural language understanding. Common architectures include feedforward networks, convolutional neural networks (CNNs), and recurrent neural networks (RNNs).""",
            "data science": """Data science is an interdisciplinary field that combines statistics, mathematics, computer science, and domain expertise to extract insights from structured and unstructured data. Data scientists collect, clean, and analyze large datasets to identify patterns, trends, and relationships. The process typically involves data collection, exploration, preprocessing, modeling, and visualization. Key tools include Python, R, SQL, Jupyter notebooks, and machine learning libraries. Data science applications include business intelligence, predictive modeling, customer analytics, and research across various industries.""",
            "python programming": """Python is a high-level, interpreted programming language known for its simplicity and readability. Created by Guido van Rossum in 1991, Python emphasizes code readability with its use of indentation and clear syntax. It supports multiple programming paradigms including procedural, object-oriented, and functional programming. Python has extensive libraries for web development, data analysis, machine learning, and scientific computing. Popular frameworks include Django and Flask for web development, NumPy and Pandas for data analysis, and TensorFlow and PyTorch for machine learning.""",
            "artificial intelligence": """Artificial Intelligence (AI) refers to the simulation of human intelligence in machines designed to think and learn like humans. AI systems can perform tasks that typically require human intelligence such as visual perception, speech recognition, decision-making, and language translation. The field encompasses machine learning, natural language processing, computer vision, robotics, and expert systems. AI applications range from virtual assistants and chatbots to autonomous vehicles and medical diagnosis systems. Current AI research focuses on developing more robust, explainable, and ethical AI systems.""",
        }

        # Find best matching response
        best_match = None
        for key, response in mock_responses.items():
            if key in query_lower:
                best_match = response
                break

        # Default response if no specific match
        if best_match is None:
            best_match = f"""This is a comprehensive overview of {query}. The topic involves multiple aspects and considerations that are important to understand. Various methods and approaches can be applied to address questions related to {query}. Research and practical applications in this area continue to evolve, with new developments and insights emerging regularly. Understanding the fundamentals and current state of knowledge about {query} is essential for effective analysis and application."""

        # Truncate to max length if needed
        if len(best_match) > max_length:
            sentences = best_match.split(". ")
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence + ". ") <= max_length:
                    truncated += sentence + ". "
                else:
                    break
            best_match = truncated.strip()

        return best_match


class HyDEGenerator:
    """HyDE generator using LLM to create hypothetical documents.

    This class generates hypothetical documents that would answer a given query,
    which can then be used for more effective embedding-based retrieval.

    Example:
        ```python
        config = HyDEConfig(num_hypotheticals=2, max_length=256)
        hyde = HyDEGenerator(config)

        # Generate hypothetical documents
        docs = await hyde.generate_hypothetical_documents("What is machine learning?")
        # Result: ["Machine learning is a subset of AI that...", "ML algorithms learn from data..."]
        ```
    """

    def __init__(self, config: Optional[HyDEConfig] = None, llm_provider: Optional[LLMProvider] = None):
        """Initialize HyDE generator.

        Args:
            config: HyDE configuration settings
            llm_provider: Optional LLM provider implementing the LLMProvider protocol.
                Defaults to MockLLMProvider.
        """
        self.config = config or HyDEConfig()
        self.llm_provider = llm_provider or MockLLMProvider(self.config.model)

        # Cache for generated documents
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for a query."""
        return f"{query.lower().strip()}_{self.config.num_hypotheticals}_{self.config.max_length}"

    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        if not self.config.use_caching:
            return False

        timestamp = cache_entry.get("timestamp", 0)
        return (time.time() - timestamp) < self.config.cache_ttl

    async def generate_hypothetical_documents(self, query: str) -> List[str]:
        """Generate hypothetical documents for a query.

        Args:
            query: Search query to generate documents for

        Returns:
            List of hypothetical documents

        Raises:
            RetrievalError: If generation fails
        """
        if not query or not query.strip():
            return []

        query = query.strip()

        # Check cache first
        cache_key = self._get_cache_key(query)
        if cache_key in self._cache and self._is_cache_valid(self._cache[cache_key]):
            return self._cache[cache_key]["documents"]

        try:
            documents = []

            # Generate multiple hypothetical documents if configured
            for i in range(self.config.num_hypotheticals):
                # Create prompt with slight variation for multiple generations
                prompt = self.config.prompt_template.format(query=query)

                if i > 0:
                    prompt += f"\n\nPlease provide a different perspective or additional details (variation {i + 1}):"

                # Generate hypothetical document
                hypothetical_doc = await self.llm_provider.generate(
                    prompt=prompt, max_length=self.config.max_length, temperature=self.config.temperature
                )

                if hypothetical_doc and hypothetical_doc.strip():
                    documents.append(hypothetical_doc.strip())

            # Cache results
            if self.config.use_caching and documents:
                self._cache[cache_key] = {"documents": documents, "timestamp": time.time()}

            return documents

        except Exception as e:
            raise RetrievalError(f"HyDE generation failed: {str(e)}") from e

    async def generate_enhanced_query(self, query: str) -> str:
        """Generate an enhanced query using hypothetical document content.

        Args:
            query: Original query

        Returns:
            Enhanced query incorporating hypothetical document terms

        Raises:
            RetrievalError: If enhancement fails
        """
        try:
            # Generate hypothetical documents
            hypotheticals = await self.generate_hypothetical_documents(query)

            if not hypotheticals:
                return query

            # Combine query with key terms from hypothetical documents
            enhanced_terms = set(query.lower().split())

            for doc in hypotheticals:
                # Extract key terms from hypothetical document
                # Simple approach: use first sentence + key nouns
                first_sentence = doc.split(".")[0] if "." in doc else doc[:100]
                words = first_sentence.lower().split()

                # Add meaningful words (simple filter)
                for word in words:
                    if (
                        len(word) > 3
                        and word.isalpha()
                        and word not in {"this", "that", "with", "from", "they", "have", "been", "will", "would"}
                    ):
                        enhanced_terms.add(word)

            # Combine terms, keeping original query prominent
            original_terms = query.split()
            additional_terms = [term for term in enhanced_terms if term not in query.lower()]

            # Limit additional terms
            additional_terms = list(additional_terms)[:5]

            enhanced_query = " ".join(original_terms + additional_terms)
            return enhanced_query

        except Exception as e:
            raise RetrievalError(f"Query enhancement failed: {str(e)}") from e

    def clear_cache(self) -> None:
        """Clear the document cache."""
        self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get HyDE generator statistics.

        Returns:
            Dictionary with statistics
        """
        cache_stats = {
            "total_entries": len(self._cache),
            "valid_entries": sum(1 for entry in self._cache.values() if self._is_cache_valid(entry)),
        }

        return {
            "config": {
                "num_hypotheticals": self.config.num_hypotheticals,
                "max_length": self.config.max_length,
                "temperature": self.config.temperature,
                "model": self.config.model,
                "use_caching": self.config.use_caching,
                "cache_ttl": self.config.cache_ttl,
            },
            "cache": cache_stats,
            "provider": type(self.llm_provider).__name__,
        }
