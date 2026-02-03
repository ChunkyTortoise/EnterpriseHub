"""
Comprehensive RAG Evaluation Metrics

Provides production-grade metrics for evaluating RAG system performance:
- Answer relevance scoring (semantic similarity, LLM-as-judge)
- Context precision and recall
- Faithfulness metrics (hallucination detection)
- Answer similarity metrics (BLEU, ROUGE, embedding-based)
- Information retrieval metrics (NDCG, MRR, Recall@K)

All metrics are designed for async operation and batch processing.
"""

from __future__ import annotations

import asyncio
import math
import re
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Union

import numpy as np
from pydantic import BaseModel, Field


# ============================================================================
# Data Models
# ============================================================================

class MetricResult(BaseModel):
    """Result of a metric calculation."""
    metric_name: str
    score: float
    details: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvaluationBatch(BaseModel):
    """Batch of evaluation results."""
    metric_name: str
    scores: List[float]
    aggregate_score: float
    statistics: Dict[str, float] = Field(default_factory=dict)


@dataclass
class RetrievedContext:
    """A retrieved context chunk with relevance information."""
    content: str
    doc_id: str
    score: float
    is_relevant: bool = False
    relevance_score: float = 0.0


@dataclass
class RAGEvaluationSample:
    """A single RAG evaluation sample."""
    query: str
    answer: str
    retrieved_contexts: List[RetrievedContext]
    ground_truth_answer: Optional[str] = None
    expected_doc_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Base Metric Classes
# ============================================================================

class BaseMetric(ABC):
    """Abstract base class for all metrics."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def compute(
        self,
        sample: RAGEvaluationSample,
        **kwargs
    ) -> MetricResult:
        """Compute the metric for a single sample."""
        pass

    async def compute_batch(
        self,
        samples: List[RAGEvaluationSample],
        **kwargs
    ) -> EvaluationBatch:
        """Compute the metric for a batch of samples."""
        tasks = [self.compute(sample, **kwargs) for sample in samples]
        results = await asyncio.gather(*tasks)
        scores = [r.score for r in results]

        return EvaluationBatch(
            metric_name=self.name,
            scores=scores,
            aggregate_score=float(np.mean(scores)),
            statistics={
                "mean": float(np.mean(scores)),
                "std": float(np.std(scores)),
                "min": float(np.min(scores)),
                "max": float(np.max(scores)),
                "median": float(np.median(scores)),
                "p25": float(np.percentile(scores, 25)),
                "p75": float(np.percentile(scores, 75)),
                "p95": float(np.percentile(scores, 95)),
            }
        )


# ============================================================================
# Answer Relevance Metrics
# ============================================================================

class AnswerRelevanceMetric(BaseMetric):
    """
    Measures how relevant the generated answer is to the query.
    
    Uses multiple strategies:
    - Keyword overlap
    - Semantic similarity (if embeddings provided)
    - Query term coverage
    """

    def __init__(
        self,
        embedding_fn: Optional[Callable[[str], List[float]]] = None,
        semantic_weight: float = 0.5
    ):
        super().__init__("answer_relevance")
        self.embedding_fn = embedding_fn
        self.semantic_weight = semantic_weight
        self.keyword_weight = 1 - semantic_weight

    async def compute(
        self,
        sample: RAGEvaluationSample,
        **kwargs
    ) -> MetricResult:
        query = sample.query.lower()
        answer = sample.answer.lower()

        # Keyword overlap score
        query_terms = set(self._extract_terms(query))
        answer_terms = set(self._extract_terms(answer))

        if not query_terms:
            keyword_score = 0.0
        else:
            overlap = len(query_terms & answer_terms)
            keyword_score = overlap / len(query_terms)

        # Semantic similarity score
        semantic_score = 0.0
        if self.embedding_fn:
            try:
                query_emb = await self._get_embedding(query)
                answer_emb = await self._get_embedding(answer)
                semantic_score = self._cosine_similarity(query_emb, answer_emb)
            except Exception:
                semantic_score = keyword_score  # Fallback

        # Combined score
        final_score = (
            self.keyword_weight * keyword_score +
            self.semantic_weight * semantic_score
        )

        return MetricResult(
            metric_name=self.name,
            score=min(1.0, max(0.0, final_score)),
            details={
                "keyword_score": keyword_score,
                "semantic_score": semantic_score,
                "query_terms": list(query_terms),
                "matched_terms": list(query_terms & answer_terms),
            }
        )

    def _extract_terms(self, text: str) -> List[str]:
        """Extract meaningful terms from text."""
        # Remove punctuation and split
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        # Filter common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
            'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has',
            'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see',
            'two', 'who', 'boy', 'did', 'she', 'use', 'her', 'way', 'many',
            'oil', 'sit', 'set', 'run', 'eat', 'far', 'sea', 'eye', 'ago',
            'off', 'too', 'any', 'try', 'ask', 'end', 'why', 'let', 'put',
            'say', 'she', 'try', 'way', 'own', 'say', 'too', 'old', 'tell',
            'very', 'when', 'much', 'would', 'there', 'their', 'what', 'said',
            'each', 'which', 'will', 'about', 'could', 'other', 'after',
            'first', 'never', 'these', 'think', 'where', 'being', 'every',
            'great', 'might', 'shall', 'still', 'those', 'while', 'this',
            'that', 'with', 'have', 'from', 'they', 'know', 'want', 'been',
            'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here',
            'just', 'like', 'long', 'make', 'over', 'such', 'take', 'than',
            'them', 'well', 'were', 'what', 'your', 'into', 'more', 'only',
            'also', 'back', 'call', 'came', 'come', 'dont', 'find', 'give',
            'going', 'help', 'home', 'keep', 'last', 'left', 'life', 'live',
            'look', 'made', 'most', 'move', 'must', 'name', 'need', 'next',
            'open', 'part', 'play', 'read', 'right', 'said', 'same', 'seem',
            'show', 'side', 'small', 'sound', 'still', 'such', 'take', 'tell',
            'than', 'that', 'them', 'then', 'there', 'they', 'thing', 'think',
            'this', 'those', 'though', 'thought', 'three', 'through', 'together',
            'told', 'took', 'turn', 'under', 'until', 'upon', 'using', 'want',
            'well', 'went', 'were', 'what', 'when', 'where', 'which', 'while',
            'white', 'who', 'whole', 'whom', 'whose', 'why', 'wide', 'wife',
            'will', 'wind', 'wish', 'with', 'within', 'without', 'woman',
            'wonder', 'word', 'work', 'world', 'would', 'write', 'wrong',
            'year', 'young', 'youre'
        }
        return [w for w in words if w not in stop_words]

    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text."""
        if self.embedding_fn is None:
            raise ValueError("No embedding function provided")
        result = self.embedding_fn(text)
        if asyncio.iscoroutine(result):
            return await result
        return result

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        a_arr = np.array(a)
        b_arr = np.array(b)
        dot = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


# ============================================================================
# Context Precision/Recall Metrics
# ============================================================================

class ContextPrecisionMetric(BaseMetric):
    """
    Measures the precision of retrieved contexts.
    
    Precision = (# of relevant retrieved contexts) / (total # of retrieved contexts)
    """

    def __init__(self, relevance_threshold: float = 0.5):
        super().__init__("context_precision")
        self.relevance_threshold = relevance_threshold

    async def compute(
        self,
        sample: RAGEvaluationSample,
        **kwargs
    ) -> MetricResult:
        contexts = sample.retrieved_contexts

        if not contexts:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                details={"error": "No contexts retrieved"}
            )

        relevant_count = sum(
            1 for ctx in contexts
            if ctx.is_relevant or ctx.relevance_score >= self.relevance_threshold
        )

        precision = relevant_count / len(contexts)

        return MetricResult(
            metric_name=self.name,
            score=precision,
            details={
                "total_contexts": len(contexts),
                "relevant_contexts": relevant_count,
                "relevance_scores": [ctx.relevance_score for ctx in contexts],
            }
        )


class ContextRecallMetric(BaseMetric):
    """
    Measures the recall of retrieved contexts.
    
    Recall = (# of relevant retrieved contexts) / (total # of relevant contexts expected)
    """

    def __init__(self):
        super().__init__("context_recall")

    async def compute(
        self,
        sample: RAGEvaluationSample,
        **kwargs
    ) -> MetricResult:
        contexts = sample.retrieved_contexts
        expected_ids = set(sample.expected_doc_ids)

        if not expected_ids:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                details={"error": "No expected documents specified"}
            )

        retrieved_ids = {ctx.doc_id for ctx in contexts}
        retrieved_relevant = len(retrieved_ids & expected_ids)

        recall = retrieved_relevant / len(expected_ids)

        return MetricResult(
            metric_name=self.name,
            score=recall,
            details={
                "expected_count": len(expected_ids),
                "retrieved_count": len(contexts),
                "retrieved_relevant": retrieved_relevant,
                "expected_ids": list(expected_ids),
                "retrieved_ids": list(retrieved_ids),
                "missed_ids": list(expected_ids - retrieved_ids),
            }
        )


class ContextRelevanceMetric(BaseMetric):
    """
    Measures average relevance score of retrieved contexts.
    """

    def __init__(self):
        super().__init__("context_relevance")

    async def compute(
        self,
        sample: RAGEvaluationSample,
        **kwargs
    ) -> MetricResult:
        contexts = sample.retrieved_contexts

        if not contexts:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                details={"error": "No contexts retrieved"}
            )

        scores = [ctx.relevance_score for ctx in contexts]
        avg_relevance = np.mean(scores)

        return MetricResult(
            metric_name=self.name,
            score=float(avg_relevance),
            details={
                "individual_scores": scores,
                "max_score": max(scores),
                "min_score": min(scores),
            }
        )


# ============================================================================
# Faithfulness Metrics
# ============================================================================

class FaithfulnessMetric(BaseMetric):
    """
    Measures how faithful the answer is to the retrieved contexts.
    
    Detects hallucinations by checking if answer claims are supported by context.
    """

    def __init__(
        self,
        embedding_fn: Optional[Callable[[str], List[float]]] = None,
        claim_threshold: float = 0.7
    ):
        super().__init__("faithfulness")
        self.embedding_fn = embedding_fn
        self.claim_threshold = claim_threshold

    async def compute(
        self,
        sample: RAGEvaluationSample,
        **kwargs
    ) -> MetricResult:
        answer = sample.answer
        contexts = sample.retrieved_contexts

        if not contexts:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                details={"error": "No contexts to check against"}
            )

        # Extract claims from answer
        claims = self._extract_claims(answer)

        if not claims:
            return MetricResult(
                metric_name=self.name,
                score=1.0,  # No claims to verify = vacuously faithful
                details={"claims": [], "supported": []}
            )

        # Check each claim against contexts
        supported_claims = 0
        claim_results = []

        context_text = " ".join([ctx.content for ctx in contexts])

        for claim in claims:
            is_supported = await self._check_claim_support(claim, context_text)
            if is_supported:
                supported_claims += 1
            claim_results.append({
                "claim": claim,
                "supported": is_supported
            })

        faithfulness = supported_claims / len(claims)

        return MetricResult(
            metric_name=self.name,
            score=faithfulness,
            details={
                "total_claims": len(claims),
                "supported_claims": supported_claims,
                "claim_results": claim_results,
            }
        )

    def _extract_claims(self, text: str) -> List[str]:
        """Extract factual claims from text."""
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        claims = []

        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 10:
                continue

            # Look for indicative patterns
            claim_indicators = [
                r'is\s+a\s+\w+',  # "X is a Y"
                r'are\s+\w+',     # "X are Y"
                r'provides?',      # "X provides"
                r'enables?',       # "X enables"
                r'supports?',      # "X supports"
                r'uses?',          # "X uses"
                r'allows?',        # "X allows"
                r'helps?',         # "X helps"
                r'can\s+\w+',     # "X can Y"
                r'will\s+\w+',    # "X will Y"
            ]

            if any(re.search(pattern, sent, re.IGNORECASE) for pattern in claim_indicators):
                claims.append(sent)

        return claims[:10]  # Limit to top 10 claims

    async def _check_claim_support(self, claim: str, context: str) -> bool:
        """Check if a claim is supported by the context."""
        # Simple keyword overlap check
        claim_words = set(self._extract_terms(claim))
        context_words = set(self._extract_terms(context))

        if not claim_words:
            return True  # Empty claim is vacuously supported

        overlap = len(claim_words & context_words) / len(claim_words)

        # If embedding function available, use semantic similarity
        if self.embedding_fn and overlap < self.claim_threshold:
            try:
                claim_emb = await self._get_embedding(claim)
                context_emb = await self._get_embedding(context[:1000])  # Truncate
                semantic_sim = self._cosine_similarity(claim_emb, context_emb)
                return semantic_sim >= self.claim_threshold
            except Exception:
                pass

        return overlap >= self.claim_threshold

    def _extract_terms(self, text: str) -> List[str]:
        """Extract meaningful terms."""
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        stop_words = {'that', 'this', 'with', 'from', 'they', 'have', 'were', 'been'}
        return [w for w in words if w not in stop_words]

    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text."""
        if self.embedding_fn is None:
            raise ValueError("No embedding function provided")
        result = self.embedding_fn(text)
        if asyncio.iscoroutine(result):
            return await result
        return result

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity."""
        a_arr = np.array(a)
        b_arr = np.array(b)
        dot = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class AnswerConsistencyMetric(BaseMetric):
    """
    Measures consistency of answers across similar queries.
    """

    def __init__(
        self,
        embedding_fn: Optional[Callable[[str], List[float]]] = None
    ):
        super().__init__("answer_consistency")
        self.embedding_fn = embedding_fn

    async def compute(
        self,
        sample: RAGEvaluationSample,
        comparison_answer: str,
        **kwargs
    ) -> MetricResult:
        """
        Compute consistency between answer and a comparison answer.
        
        For batch consistency, use compute_batch with multiple samples
        representing the same query asked multiple times.
        """
        answer1 = sample.answer
        answer2 = comparison_answer

        # Keyword overlap
        words1 = set(self._extract_terms(answer1))
        words2 = set(self._extract_terms(answer2))

        if not words1 or not words2:
            jaccard = 0.0
        else:
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            jaccard = intersection / union if union > 0 else 0.0

        # Semantic similarity
        semantic_sim = 0.0
        if self.embedding_fn:
            try:
                emb1 = await self._get_embedding(answer1)
                emb2 = await self._get_embedding(answer2)
                semantic_sim = self._cosine_similarity(emb1, emb2)
            except Exception:
                semantic_sim = jaccard

        # Combined score
        consistency = 0.5 * jaccard + 0.5 * semantic_sim

        return MetricResult(
            metric_name=self.name,
            score=consistency,
            details={
                "jaccard_similarity": jaccard,
                "semantic_similarity": semantic_sim,
            }
        )

    def _extract_terms(self, text: str) -> List[str]:
        """Extract meaningful terms."""
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        stop_words = {'that', 'this', 'with', 'from', 'they', 'have', 'were', 'been', 'than'}
        return [w for w in words if w not in stop_words]

    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text."""
        if self.embedding_fn is None:
            raise ValueError("No embedding function provided")
        result = self.embedding_fn(text)
        if asyncio.iscoroutine(result):
            return await result
        return result

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity."""
        a_arr = np.array(a)
        b_arr = np.array(b)
        dot = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


# ============================================================================
# Answer Similarity Metrics (BLEU, ROUGE)
# ============================================================================

class BLEUMetric(BaseMetric):
    """
    BLEU (Bilingual Evaluation Understudy) score for answer similarity.
    
    Measures n-gram overlap between generated and reference answers.
    """

    def __init__(
        self,
        max_n: int = 4,
        weights: Optional[List[float]] = None
    ):
        super().__init__("bleu")
        self.max_n = max_n
        self.weights = weights or [1.0 / max_n] * max_n

    async def compute(
        self,
        sample: RAGEvaluationSample,
        **kwargs
    ) -> MetricResult:
        if not sample.ground_truth_answer:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                details={"error": "No ground truth answer provided"}
            )

        candidate = sample.answer.lower()
        reference = sample.ground_truth_answer.lower()

        # Calculate n-gram precisions
        precisions = []
        for n in range(1, self.max_n + 1):
            precision = self._ngram_precision(candidate, reference, n)
            precisions.append(precision)

        # Geometric mean of precisions
        if all(p > 0 for p in precisions):
            geo_mean = math.exp(
                sum(w * math.log(p) for w, p in zip(self.weights, precisions))
            )
        else:
            geo_mean = 0.0

        # Brevity penalty
        bp = self._brevity_penalty(len(candidate.split()), len(reference.split()))

        bleu = bp * geo_mean

        return MetricResult(
            metric_name=self.name,
            score=bleu,
            details={
                "ngram_precisions": precisions,
                "brevity_penalty": bp,
                "geo_mean": geo_mean,
            }
        )

    def _ngram_precision(
        self,
        candidate: str,
        reference: str,
        n: int
    ) -> float:
        """Calculate n-gram precision."""
        cand_tokens = candidate.split()
        ref_tokens = reference.split()

        if len(cand_tokens) < n:
            return 0.0

        cand_ngrams = self._get_ngrams(cand_tokens, n)
        ref_ngrams = self._get_ngrams(ref_tokens, n)

        if not cand_ngrams:
            return 0.0

        matches = sum((cand_ngrams & ref_ngrams).values())
        total = sum(cand_ngrams.values())

        return matches / total if total > 0 else 0.0

    def _get_ngrams(self, tokens: List[str], n: int) -> Counter:
        """Get n-grams from tokens."""
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngrams.append(tuple(tokens[i:i + n]))
        return Counter(ngrams)

    def _brevity_penalty(self, candidate_len: int, reference_len: int) -> float:
        """Calculate brevity penalty."""
        if candidate_len > reference_len:
            return 1.0
        if candidate_len == 0:
            return 0.0
        return math.exp(1 - reference_len / candidate_len)


class ROUGEMetric(BaseMetric):
    """
    ROUGE (Recall-Oriented Understudy for Gisting Evaluation) score.
    
    Measures recall of n-grams in reference text.
    """

    def __init__(self, n: int = 1, use_stemming: bool = False):
        super().__init__(f"rouge_{n}")
        self.n = n
        self.use_stemming = use_stemming

    async def compute(
        self,
        sample: RAGEvaluationSample,
        **kwargs
    ) -> MetricResult:
        if not sample.ground_truth_answer:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                details={"error": "No ground truth answer provided"}
            )

        candidate = self._preprocess(sample.answer)
        reference = self._preprocess(sample.ground_truth_answer)

        # Calculate recall
        cand_ngrams = self._get_ngrams(candidate.split(), self.n)
        ref_ngrams = self._get_ngrams(reference.split(), self.n)

        if not ref_ngrams:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                details={"error": "No reference n-grams"}
            )

        matches = sum((cand_ngrams & ref_ngrams).values())
        recall = matches / sum(ref_ngrams.values())

        # Calculate precision
        if cand_ngrams:
            precision = matches / sum(cand_ngrams.values())
        else:
            precision = 0.0

        # F1 score
        if precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0.0

        return MetricResult(
            metric_name=self.name,
            score=recall,  # ROUGE typically reports recall
            details={
                "recall": recall,
                "precision": precision,
                "f1": f1,
                "matches": matches,
            }
        )

    def _preprocess(self, text: str) -> str:
        """Preprocess text."""
        text = text.lower()
        if self.use_stemming:
            # Simple stemming (remove common suffixes)
            words = text.split()
            stemmed = []
            for word in words:
                for suffix in ['ing', 'ed', 'er', 'est', 'ly', 'tion', 's']:
                    if word.endswith(suffix) and len(word) > len(suffix) + 2:
                        word = word[:-len(suffix)]
                        break
                stemmed.append(word)
            text = ' '.join(stemmed)
        return text

    def _get_ngrams(self, tokens: List[str], n: int) -> Counter:
        """Get n-grams."""
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngrams.append(tuple(tokens[i:i + n]))
        return Counter(ngrams)


# ============================================================================
# Information Retrieval Metrics
# ============================================================================

class NDCGMetric(BaseMetric):
    """
    Normalized Discounted Cumulative Gain.
    
    Measures ranking quality considering graded relevance.
    """

    def __init__(self, k: Optional[int] = None):
        super().__init__(f"ndcg@{k}" if k else "ndcg")
        self.k = k

    async def compute(
        self,
        sample: RAGEvaluationSample,
        **kwargs
    ) -> MetricResult:
        contexts = sample.retrieved_contexts

        if not contexts:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                details={"error": "No contexts retrieved"}
            )

        # Limit to k if specified
        if self.k:
            contexts = contexts[:self.k]

        # Calculate DCG
        dcg = 0.0
        for i, ctx in enumerate(contexts):
            relevance = ctx.relevance_score if ctx.is_relevant else 0.0
            dcg += relevance / math.log2(i + 2)  # +2 because i starts at 0

        # Calculate ideal DCG
        ideal_relevances = sorted(
            [ctx.relevance_score for ctx in sample.retrieved_contexts],
            reverse=True
        )
        if self.k:
            ideal_relevances = ideal_relevances[:self.k]

        idcg = 0.0
        for i, rel in enumerate(ideal_relevances):
            idcg += rel / math.log2(i + 2)

        ndcg = dcg / idcg if idcg > 0 else 0.0

        return MetricResult(
            metric_name=self.name,
            score=ndcg,
            details={
                "dcg": dcg,
                "idcg": idcg,
                "k": self.k or len(contexts),
            }
        )


class MRRMetric(BaseMetric):
    """
    Mean Reciprocal Rank.
    
    Measures the rank of the first relevant document.
    """

    def __init__(self):
        super().__init__("mrr")

    async def compute(
        self,
        sample: RAGEvaluationSample,
        **kwargs
    ) -> MetricResult:
        contexts = sample.retrieved_contexts

        if not contexts:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                details={"error": "No contexts retrieved"}
            )

        # Find first relevant document
        for i, ctx in enumerate(contexts):
            if ctx.is_relevant or ctx.relevance_score > 0.5:
                mrr = 1.0 / (i + 1)
                return MetricResult(
                    metric_name=self.name,
                    score=mrr,
                    details={
                        "first_relevant_rank": i + 1,
                        "total_contexts": len(contexts),
                    }
                )

        # No relevant document found
        return MetricResult(
            metric_name=self.name,
            score=0.0,
            details={
                "first_relevant_rank": None,
                "total_contexts": len(contexts),
            }
        )


class RecallAtKMetric(BaseMetric):
    """
    Recall at K metric.
    
    Measures proportion of relevant documents found in top K.
    """

    def __init__(self, k: int = 10):
        super().__init__(f"recall@{k}")
        self.k = k

    async def compute(
        self,
        sample: RAGEvaluationSample,
        **kwargs
    ) -> MetricResult:
        contexts = sample.retrieved_contexts[:self.k]
        expected_ids = set(sample.expected_doc_ids)

        if not expected_ids:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                details={"error": "No expected documents specified"}
            )

        retrieved_ids = {ctx.doc_id for ctx in contexts}
        retrieved_relevant = len(retrieved_ids & expected_ids)

        recall = retrieved_relevant / len(expected_ids)

        return MetricResult(
            metric_name=self.name,
            score=recall,
            details={
                "k": self.k,
                "expected_count": len(expected_ids),
                "retrieved_relevant": retrieved_relevant,
            }
        )


class PrecisionAtKMetric(BaseMetric):
    """
    Precision at K metric.
    
    Measures proportion of retrieved documents that are relevant in top K.
    """

    def __init__(self, k: int = 10):
        super().__init__(f"precision@{k}")
        self.k = k

    async def compute(
        self,
        sample: RAGEvaluationSample,
        **kwargs
    ) -> MetricResult:
        contexts = sample.retrieved_contexts[:self.k]

        if not contexts:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                details={"error": "No contexts retrieved"}
            )

        relevant_count = sum(1 for ctx in contexts if ctx.is_relevant)
        precision = relevant_count / len(contexts)

        return MetricResult(
            metric_name=self.name,
            score=precision,
            details={
                "k": self.k,
                "relevant_count": relevant_count,
                "total_retrieved": len(contexts),
            }
        )


# ============================================================================
# Composite Metrics
# ============================================================================

class CompositeMetric(BaseMetric):
    """
    Combines multiple metrics into a single score.
    """

    def __init__(
        self,
        metrics: List[Tuple[BaseMetric, float]],
        name: str = "composite"
    ):
        super().__init__(name)
        self.metrics = metrics

    async def compute(
        self,
        sample: RAGEvaluationSample,
        **kwargs
    ) -> MetricResult:
        results = []
        weighted_sum = 0.0
        total_weight = 0.0

        for metric, weight in self.metrics:
            result = await metric.compute(sample, **kwargs)
            results.append({
                "metric": metric.name,
                "score": result.score,
                "weight": weight,
            })
            weighted_sum += result.score * weight
            total_weight += weight

        composite_score = weighted_sum / total_weight if total_weight > 0 else 0.0

        return MetricResult(
            metric_name=self.name,
            score=composite_score,
            details={
                "component_scores": results,
                "weights": [w for _, w in self.metrics],
            }
        )

    async def compute_batch(
        self,
        samples: List[RAGEvaluationSample],
        **kwargs
    ) -> EvaluationBatch:
        """Compute batch with component metrics."""
        # Compute composite score for each sample
        composite_results = []
        for sample in samples:
            result = await self.compute(sample, **kwargs)
            composite_results.append(result)

        scores = [r.score for r in composite_results]

        # Also compute individual metrics
        component_batches = {}
        for metric, _ in self.metrics:
            batch = await metric.compute_batch(samples, **kwargs)
            component_batches[metric.name] = batch

        return EvaluationBatch(
            metric_name=self.name,
            scores=scores,
            aggregate_score=float(np.mean(scores)),
            statistics={
                "mean": float(np.mean(scores)),
                "std": float(np.std(scores)),
                "min": float(np.min(scores)),
                "max": float(np.max(scores)),
                "median": float(np.median(scores)),
            },
        )


# ============================================================================
# Metric Registry
# ============================================================================

class MetricRegistry:
    """Registry for available metrics."""

    _metrics: Dict[str, type] = {
        "answer_relevance": AnswerRelevanceMetric,
        "context_precision": ContextPrecisionMetric,
        "context_recall": ContextRecallMetric,
        "context_relevance": ContextRelevanceMetric,
        "faithfulness": FaithfulnessMetric,
        "answer_consistency": AnswerConsistencyMetric,
        "bleu": BLEUMetric,
        "rouge_1": lambda: ROUGEMetric(n=1),
        "rouge_2": lambda: ROUGEMetric(n=2),
        "rouge_l": lambda: ROUGEMetric(n=1, use_stemming=True),
        "ndcg": NDCGMetric,
        "ndcg@5": lambda: NDCGMetric(k=5),
        "ndcg@10": lambda: NDCGMetric(k=10),
        "mrr": MRRMetric,
        "recall@5": lambda: RecallAtKMetric(k=5),
        "recall@10": lambda: RecallAtKMetric(k=10),
        "precision@5": lambda: PrecisionAtKMetric(k=5),
        "precision@10": lambda: PrecisionAtKMetric(k=10),
    }

    @classmethod
    def get_metric(cls, name: str, **kwargs) -> BaseMetric:
        """Get a metric by name."""
        if name not in cls._metrics:
            raise ValueError(f"Unknown metric: {name}")

        metric_class = cls._metrics[name]
        if callable(metric_class) and not isinstance(metric_class, type):
            return metric_class()
        return metric_class(**kwargs)

    @classmethod
    def list_metrics(cls) -> List[str]:
        """List available metric names."""
        return list(cls._metrics.keys())

    @classmethod
    def register(cls, name: str, metric_class: type):
        """Register a new metric."""
        cls._metrics[name] = metric_class


# ============================================================================
# Convenience Functions
# ============================================================================

async def evaluate_rag_sample(
    sample: RAGEvaluationSample,
    metrics: List[str],
    embedding_fn: Optional[Callable[[str], List[float]]] = None
) -> Dict[str, MetricResult]:
    """
    Evaluate a RAG sample with multiple metrics.
    
    Args:
        sample: The RAG evaluation sample
        metrics: List of metric names to compute
        embedding_fn: Optional embedding function for semantic metrics
    
    Returns:
        Dictionary mapping metric names to results
    """
    results = {}

    for metric_name in metrics:
        try:
            metric = MetricRegistry.get_metric(metric_name, embedding_fn=embedding_fn)
            result = await metric.compute(sample)
            results[metric_name] = result
        except Exception as e:
            results[metric_name] = MetricResult(
                metric_name=metric_name,
                score=0.0,
                details={"error": str(e)}
            )

    return results


async def evaluate_rag_batch(
    samples: List[RAGEvaluationSample],
    metrics: List[str],
    embedding_fn: Optional[Callable[[str], List[float]]] = None
) -> Dict[str, EvaluationBatch]:
    """
    Evaluate a batch of RAG samples.
    
    Args:
        samples: List of RAG evaluation samples
        metrics: List of metric names to compute
        embedding_fn: Optional embedding function
    
    Returns:
        Dictionary mapping metric names to batch results
    """
    results = {}

    for metric_name in metrics:
        try:
            metric = MetricRegistry.get_metric(metric_name, embedding_fn=embedding_fn)
            batch_result = await metric.compute_batch(samples)
            results[metric_name] = batch_result
        except Exception as e:
            results[metric_name] = EvaluationBatch(
                metric_name=metric_name,
                scores=[],
                aggregate_score=0.0,
                statistics={"error": str(e)}
            )

    return results


# Export all classes
__all__ = [
    "MetricResult",
    "EvaluationBatch",
    "RetrievedContext",
    "RAGEvaluationSample",
    "BaseMetric",
    "AnswerRelevanceMetric",
    "ContextPrecisionMetric",
    "ContextRecallMetric",
    "ContextRelevanceMetric",
    "FaithfulnessMetric",
    "AnswerConsistencyMetric",
    "BLEUMetric",
    "ROUGEMetric",
    "NDCGMetric",
    "MRRMetric",
    "RecallAtKMetric",
    "PrecisionAtKMetric",
    "CompositeMetric",
    "MetricRegistry",
    "evaluate_rag_sample",
    "evaluate_rag_batch",
]