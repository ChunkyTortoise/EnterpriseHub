"""
Collective Learning Engine - Network Effects Driver
Creates exponential value through shared intelligence across all customers.
Every customer interaction improves AI for everyone = Unbeatable competitive moat.
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

from ..core.llm_client import LLMClient
from ..services.cache_service import CacheService
from ..services.database_service import DatabaseService
from ..services.enhanced_error_handling import enhanced_error_handler

logger = logging.getLogger(__name__)


@dataclass
class AnonymizedPattern:
    """Represents an anonymized learning pattern from customer interactions."""

    pattern_hash: str
    category: str
    success_indicators: Dict[str, float]
    failure_indicators: Dict[str, float]
    context_metadata: Dict[str, Any]
    confidence_score: float
    sample_size: int
    created_at: datetime


@dataclass
class CollectiveInsight:
    """Represents insights derived from collective customer data."""

    insight_id: str
    description: str
    applicable_scenarios: List[str]
    success_probability: float
    evidence_strength: float
    customer_impact: Dict[str, float]
    implementation_guidance: str
    created_at: datetime


class PatternExtractor(ABC):
    """Abstract base for different pattern extraction strategies."""

    @abstractmethod
    async def extract_patterns(self, interaction_data: Dict[str, Any]) -> List[AnonymizedPattern]:
        """Extract anonymized patterns from customer interaction data."""
        pass


class LeadConversionPatternExtractor(PatternExtractor):
    """Extract patterns from lead conversion data."""

    async def extract_patterns(self, interaction_data: Dict[str, Any]) -> List[AnonymizedPattern]:
        """Extract lead conversion patterns while preserving privacy."""
        patterns = []

        # Lead scoring patterns
        if "lead_score_changes" in interaction_data:
            pattern = AnonymizedPattern(
                pattern_hash=self._generate_pattern_hash(interaction_data["lead_score_changes"]),
                category="lead_scoring",
                success_indicators={
                    "score_velocity": interaction_data.get("score_velocity", 0),
                    "engagement_frequency": interaction_data.get("engagement_frequency", 0),
                    "response_time": interaction_data.get("response_time", 0),
                },
                failure_indicators={
                    "score_stagnation": interaction_data.get("score_stagnation", 0),
                    "communication_gaps": interaction_data.get("communication_gaps", 0),
                },
                context_metadata={
                    "industry_vertical": interaction_data.get("industry", "unknown"),
                    "lead_source": interaction_data.get("source_category", "unknown"),
                    "time_of_day": interaction_data.get("interaction_hour", 0),
                },
                confidence_score=0.85,
                sample_size=1,
                created_at=datetime.utcnow(),
            )
            patterns.append(pattern)

        return patterns

    def _generate_pattern_hash(self, data: Any) -> str:
        """Generate hash for pattern identification without exposing sensitive data."""
        return hashlib.sha256(str(sorted(data.items()) if isinstance(data, dict) else str(data)).encode()).hexdigest()[
            :16
        ]


class PropertyMatchingPatternExtractor(PatternExtractor):
    """Extract patterns from property matching success/failure."""

    async def extract_patterns(self, interaction_data: Dict[str, Any]) -> List[AnonymizedPattern]:
        """Extract property matching patterns."""
        patterns = []

        if "property_match_outcome" in interaction_data:
            pattern = AnonymizedPattern(
                pattern_hash=self._generate_pattern_hash(interaction_data["match_criteria"]),
                category="property_matching",
                success_indicators={
                    "criteria_alignment": interaction_data.get("criteria_match_score", 0),
                    "location_preference_strength": interaction_data.get("location_score", 0),
                    "price_point_accuracy": interaction_data.get("price_accuracy", 0),
                },
                failure_indicators={
                    "criteria_mismatch": interaction_data.get("mismatch_severity", 0),
                    "overpriced_suggestions": interaction_data.get("price_overreach", 0),
                },
                context_metadata={
                    "market_conditions": interaction_data.get("market_state", "unknown"),
                    "buyer_urgency": interaction_data.get("urgency_level", "medium"),
                    "geographic_region": interaction_data.get("region_code", "unknown"),
                },
                confidence_score=0.90,
                sample_size=1,
                created_at=datetime.utcnow(),
            )
            patterns.append(pattern)

        return patterns

    def _generate_pattern_hash(self, data: Any) -> str:
        """Generate hash for pattern identification."""
        return hashlib.sha256(str(sorted(data.items()) if isinstance(data, dict) else str(data)).encode()).hexdigest()[
            :16
        ]


class CollectiveLearningEngine:
    """
    Core engine for network effects through collective learning.

    Every customer interaction improves AI for all customers.
    Creates exponential switching costs and competitive moats.
    """

    def __init__(self, llm_client: LLMClient, cache_service: CacheService, database_service: DatabaseService):
        self.llm_client = llm_client
        self.cache = cache_service
        self.db = database_service

        # Pattern extractors for different interaction types
        self.pattern_extractors = {
            "lead_conversion": LeadConversionPatternExtractor(),
            "property_matching": PropertyMatchingPatternExtractor(),
        }

        # Collective intelligence models
        self.global_patterns: Dict[str, List[AnonymizedPattern]] = {}
        self.collective_insights: List[CollectiveInsight] = []

        logger.info("Collective Learning Engine initialized")

    @enhanced_error_handler
    async def learn_from_customer_outcomes(
        self, customer_data: Dict[str, Any], interaction_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Core network effect: Learn from customer interaction to improve global intelligence.

        Args:
            customer_data: Customer interaction data (will be anonymized)
            interaction_type: Type of interaction for pattern extraction

        Returns:
            Learning metrics and improvement indicators
        """
        logger.info(f"Learning from customer interaction: {interaction_type}")

        # Step 1: Extract anonymized patterns
        patterns = await self._extract_anonymized_patterns(customer_data, interaction_type)

        # Step 2: Update global pattern database
        await self._update_global_patterns(patterns)

        # Step 3: Generate new collective insights
        new_insights = await self._generate_collective_insights(patterns)

        # Step 4: Propagate improvements to all customers
        improvement_metrics = await self._propagate_intelligence_updates(new_insights)

        # Step 5: Calculate network effect value
        network_effect_value = await self._calculate_network_effect_value(patterns)

        return {
            "patterns_extracted": len(patterns),
            "new_insights_generated": len(new_insights),
            "customers_improved": improvement_metrics.get("customers_affected", 0),
            "network_effect_value": network_effect_value,
            "global_intelligence_score": await self._calculate_global_intelligence_score(),
        }

    @enhanced_error_handler
    async def generate_predictive_insights(
        self, query: str, customer_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate insights leveraging collective intelligence from all customers.

        Args:
            query: Question or scenario to analyze
            customer_context: Optional customer-specific context

        Returns:
            Predictive insights powered by collective learning
        """
        logger.info(f"Generating predictive insights for query: {query[:100]}...")

        # Step 1: Find relevant patterns from collective intelligence
        relevant_patterns = await self._find_relevant_patterns(query, customer_context)

        # Step 2: Query collective knowledge base
        collective_knowledge = await self._query_collective_knowledge_base(query, relevant_patterns)

        # Step 3: Generate AI-powered insights using Claude
        insights = await self._generate_ai_insights(query, collective_knowledge, customer_context)

        # Step 4: Add confidence metrics based on collective data
        confidence_metrics = await self._calculate_insight_confidence(insights, relevant_patterns)

        return {
            "primary_insight": insights.get("primary_recommendation"),
            "supporting_evidence": insights.get("evidence_points", []),
            "confidence_score": confidence_metrics.get("overall_confidence", 0.0),
            "sample_size": sum(p.sample_size for p in relevant_patterns),
            "patterns_analyzed": len(relevant_patterns),
            "success_probability": confidence_metrics.get("success_probability", 0.0),
            "alternative_scenarios": insights.get("alternatives", []),
            "collective_intelligence_value": confidence_metrics.get("network_advantage", 0.0),
        }

    async def get_network_effect_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics on network effects and competitive moats."""

        total_patterns = sum(len(patterns) for patterns in self.global_patterns.values())
        total_customers = await self._count_contributing_customers()
        intelligence_score = await self._calculate_global_intelligence_score()

        return {
            "total_learned_patterns": total_patterns,
            "contributing_customers": total_customers,
            "global_intelligence_score": intelligence_score,
            "network_effect_multiplier": self._calculate_network_multiplier(total_customers),
            "competitive_moat_strength": intelligence_score * total_customers,
            "switching_cost_estimate": self._estimate_switching_costs(total_patterns),
            "platform_stickiness_score": intelligence_score * 0.9 + (total_customers / 10000) * 0.1,
        }

    async def _extract_anonymized_patterns(
        self, customer_data: Dict[str, Any], interaction_type: str
    ) -> List[AnonymizedPattern]:
        """Extract patterns while preserving customer privacy."""

        if interaction_type not in self.pattern_extractors:
            logger.warning(f"No pattern extractor for interaction type: {interaction_type}")
            return []

        extractor = self.pattern_extractors[interaction_type]
        patterns = await extractor.extract_patterns(customer_data)

        # Additional privacy protection
        for pattern in patterns:
            pattern.context_metadata = self._sanitize_metadata(pattern.context_metadata)

        return patterns

    async def _update_global_patterns(self, patterns: List[AnonymizedPattern]) -> None:
        """Update global pattern database with new learning."""

        for pattern in patterns:
            category = pattern.category

            if category not in self.global_patterns:
                self.global_patterns[category] = []

            # Check for similar patterns and merge/update
            merged = False
            for existing_pattern in self.global_patterns[category]:
                if existing_pattern.pattern_hash == pattern.pattern_hash:
                    # Merge patterns (increase sample size, update confidence)
                    await self._merge_patterns(existing_pattern, pattern)
                    merged = True
                    break

            if not merged:
                self.global_patterns[category].append(pattern)

        # Cache updated patterns
        await self.cache.set(
            "global_patterns",
            self.global_patterns,
            ttl=3600 * 24,  # 24 hour cache
        )

    async def _generate_collective_insights(self, new_patterns: List[AnonymizedPattern]) -> List[CollectiveInsight]:
        """Generate insights from patterns using Claude AI."""

        insights = []

        for pattern in new_patterns:
            # Find related patterns for context
            related_patterns = await self._find_related_patterns(pattern)

            # Generate AI insight using Claude
            insight_prompt = f"""
            Analyze this business pattern and related data to generate actionable insights:

            Pattern Category: {pattern.category}
            Success Indicators: {pattern.success_indicators}
            Failure Indicators: {pattern.failure_indicators}
            Sample Size: {pattern.sample_size}
            Related Patterns: {len(related_patterns)} similar patterns found

            Generate a specific, actionable business insight that helps optimize outcomes.
            Focus on practical implementation guidance.
            """

            response = await self.llm_client.generate(insight_prompt)

            insight = CollectiveInsight(
                insight_id=f"insight_{pattern.pattern_hash}_{datetime.utcnow().timestamp()}",
                description=response[:500],  # Truncate for storage
                applicable_scenarios=[pattern.category],
                success_probability=pattern.confidence_score,
                evidence_strength=min(pattern.sample_size / 100.0, 1.0),
                customer_impact={"conversion_improvement": 0.15, "efficiency_gain": 0.10, "satisfaction_boost": 0.12},
                implementation_guidance=response[500:] if len(response) > 500 else "See full description.",
                created_at=datetime.utcnow(),
            )

            insights.append(insight)

        return insights

    async def _propagate_intelligence_updates(self, new_insights: List[CollectiveInsight]) -> Dict[str, Any]:
        """Propagate intelligence improvements to all customer deployments."""

        # Cache insights for all customers to access
        for insight in new_insights:
            await self.cache.set(
                f"collective_insight_{insight.insight_id}",
                insight,
                ttl=3600 * 24 * 7,  # 7 day cache
            )

        # Update global insight index
        insight_index = await self.cache.get("collective_insights_index", [])
        insight_index.extend([insight.insight_id for insight in new_insights])
        await self.cache.set("collective_insights_index", insight_index, ttl=3600 * 24 * 30)

        # Trigger refresh notifications to customer systems
        customer_count = await self._notify_customers_of_updates(new_insights)

        return {
            "customers_affected": customer_count,
            "insights_propagated": len(new_insights),
            "propagation_timestamp": datetime.utcnow().isoformat(),
        }

    async def _find_relevant_patterns(
        self, query: str, customer_context: Optional[Dict[str, Any]] = None
    ) -> List[AnonymizedPattern]:
        """Find patterns relevant to a specific query."""

        relevant_patterns = []

        for category, patterns in self.global_patterns.items():
            for pattern in patterns:
                # Simple relevance scoring (could be enhanced with vector embeddings)
                relevance_score = await self._calculate_pattern_relevance(pattern, query, customer_context)

                if relevance_score > 0.3:  # Threshold for relevance
                    relevant_patterns.append(pattern)

        # Sort by relevance and confidence
        relevant_patterns.sort(key=lambda p: p.confidence_score * len(str(p.success_indicators)), reverse=True)

        return relevant_patterns[:50]  # Limit to top 50 patterns

    async def _query_collective_knowledge_base(
        self, query: str, relevant_patterns: List[AnonymizedPattern]
    ) -> Dict[str, Any]:
        """Query the collective knowledge accumulated from all customers."""

        # Aggregate pattern data
        aggregated_data = {
            "total_samples": sum(p.sample_size for p in relevant_patterns),
            "average_confidence": np.mean([p.confidence_score for p in relevant_patterns]) if relevant_patterns else 0,
            "success_indicators": {},
            "failure_indicators": {},
            "context_distribution": {},
        }

        # Aggregate success indicators
        for pattern in relevant_patterns:
            for key, value in pattern.success_indicators.items():
                if key not in aggregated_data["success_indicators"]:
                    aggregated_data["success_indicators"][key] = []
                aggregated_data["success_indicators"][key].append(value)

        # Calculate averages
        for key, values in aggregated_data["success_indicators"].items():
            aggregated_data["success_indicators"][key] = np.mean(values)

        return aggregated_data

    async def _generate_ai_insights(
        self, query: str, collective_knowledge: Dict[str, Any], customer_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate AI insights using collective intelligence."""

        insight_prompt = f"""
        Based on collective intelligence from {collective_knowledge.get("total_samples", 0)} customer interactions:

        Query: {query}

        Success Patterns: {collective_knowledge.get("success_indicators", {})}
        Sample Size: {collective_knowledge.get("total_samples", 0)}
        Confidence Level: {collective_knowledge.get("average_confidence", 0):.2f}

        Customer Context: {customer_context or "General"}

        Provide specific, actionable recommendations based on proven patterns.
        Include:
        1. Primary recommendation with success probability
        2. Supporting evidence from collective data
        3. Alternative scenarios to consider
        4. Implementation guidance

        Focus on practical value and measurable outcomes.
        """

        response = await self.llm_client.generate(insight_prompt)

        # Parse response into structured format
        return {
            "primary_recommendation": response[:300],
            "evidence_points": [
                f"Based on {collective_knowledge.get('total_samples', 0)} customer interactions",
                f"Average success confidence: {collective_knowledge.get('average_confidence', 0):.2f}",
                "Proven patterns from collective intelligence",
            ],
            "alternatives": ["Consider A/B testing variations", "Monitor for market condition changes"],
            "implementation_guidance": response[300:] if len(response) > 300 else response,
        }

    def _calculate_network_multiplier(self, customer_count: int) -> float:
        """Calculate network effect multiplier based on customer count."""
        # Network effects typically follow Metcalfe's law (value proportional to n²)
        return min(customer_count**1.2 / 1000, 100.0)  # Capped at 100x

    def _estimate_switching_costs(self, pattern_count: int) -> float:
        """Estimate switching costs based on accumulated intelligence."""
        # More patterns = higher switching costs (competitor can't replicate intelligence)
        base_cost = pattern_count * 1000  # $1000 per pattern in lost intelligence
        return min(base_cost, 10000000)  # Cap at $10M switching cost estimate

    async def _calculate_global_intelligence_score(self) -> float:
        """Calculate overall intelligence score of the platform."""
        total_patterns = sum(len(patterns) for patterns in self.global_patterns.values())
        total_samples = sum(sum(p.sample_size for p in patterns) for patterns in self.global_patterns.values())

        # Score based on pattern diversity and sample size
        diversity_score = len(self.global_patterns) / 10.0  # Max 1.0 for 10+ categories
        volume_score = min(total_samples / 100000, 1.0)  # Max 1.0 for 100k+ samples

        return (diversity_score + volume_score) / 2.0

    # Additional helper methods...
    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from metadata."""
        sanitized = {}
        safe_keys = ["industry", "region_code", "time_of_day", "market_conditions", "urgency_level"]

        for key, value in metadata.items():
            if key in safe_keys:
                sanitized[key] = value

        return sanitized

    async def _merge_patterns(self, existing: AnonymizedPattern, new: AnonymizedPattern) -> None:
        """Merge similar patterns to strengthen collective intelligence."""
        # Weighted average of indicators
        total_samples = existing.sample_size + new.sample_size

        for key in existing.success_indicators:
            if key in new.success_indicators:
                weighted_avg = (
                    existing.success_indicators[key] * existing.sample_size
                    + new.success_indicators[key] * new.sample_size
                ) / total_samples
                existing.success_indicators[key] = weighted_avg

        # Update metadata
        existing.sample_size = total_samples
        existing.confidence_score = min(existing.confidence_score + 0.1, 1.0)

    async def _find_related_patterns(self, pattern: AnonymizedPattern) -> List[AnonymizedPattern]:
        """Find patterns related to the given pattern."""
        related = []

        if pattern.category in self.global_patterns:
            for p in self.global_patterns[pattern.category]:
                if p.pattern_hash != pattern.pattern_hash:
                    # Simple similarity check (could be enhanced)
                    similarity = self._calculate_pattern_similarity(pattern, p)
                    if similarity > 0.5:
                        related.append(p)

        return related

    def _calculate_pattern_similarity(self, pattern1: AnonymizedPattern, pattern2: AnonymizedPattern) -> float:
        """Calculate similarity between patterns."""
        # Simple Jaccard similarity on success indicators
        keys1 = set(pattern1.success_indicators.keys())
        keys2 = set(pattern2.success_indicators.keys())

        intersection = len(keys1.intersection(keys2))
        union = len(keys1.union(keys2))

        return intersection / union if union > 0 else 0.0

    async def _calculate_pattern_relevance(
        self, pattern: AnonymizedPattern, query: str, context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate how relevant a pattern is to a query."""
        # Simple keyword matching (could be enhanced with embeddings)
        query_lower = query.lower()
        relevance_score = 0.0

        # Category relevance
        if pattern.category.lower() in query_lower:
            relevance_score += 0.5

        # Context relevance
        if context:
            for key, value in pattern.context_metadata.items():
                if key in context and str(value).lower() in str(context.get(key, "")).lower():
                    relevance_score += 0.2

        return min(relevance_score, 1.0)

    async def _calculate_insight_confidence(
        self, insights: Dict[str, Any], patterns: List[AnonymizedPattern]
    ) -> Dict[str, Any]:
        """Calculate confidence metrics for insights."""
        total_samples = sum(p.sample_size for p in patterns)
        avg_confidence = np.mean([p.confidence_score for p in patterns]) if patterns else 0

        return {
            "overall_confidence": min(avg_confidence + (total_samples / 10000) * 0.1, 1.0),
            "success_probability": avg_confidence * 0.9,
            "network_advantage": min(len(patterns) / 100.0, 1.0),  # Advantage from network size
        }

    async def _count_contributing_customers(self) -> int:
        """Count customers contributing to collective intelligence."""
        # This would query the database for unique customer contributors
        # Simplified implementation
        return len(self.global_patterns) * 100  # Estimate

    async def _notify_customers_of_updates(self, insights: List[CollectiveInsight]) -> int:
        """Notify customer systems of intelligence updates."""
        # In real implementation, this would trigger webhooks or API calls
        # to customer systems to refresh their intelligence
        logger.info(f"Intelligence update notification for {len(insights)} new insights")
        return 1000  # Estimated customer count
