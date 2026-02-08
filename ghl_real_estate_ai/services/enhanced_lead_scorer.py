#!/usr/bin/env python3
"""
🎯 Enhanced Lead Scorer - Integration Layer
==========================================

Unified lead scoring service that integrates:
- Original question-count scoring (Jorge's requirement)
- ML-powered predictive scoring
- Dynamic adaptive weights system
- Market condition adjustments
- A/B testing framework

This service acts as a facade, orchestrating all scoring methods
and providing a single interface for the application.

Features:
- Backwards compatibility with existing scorers
- Intelligent fallback mechanisms
- Performance monitoring
- Explainable scoring decisions
- Real-time weight adaptation

Author: Claude Sonnet 4
Date: 2026-01-09
Version: 1.0.0
"""

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from .ai_predictive_lead_scoring import PredictiveLeadScorer
from .dynamic_scoring_weights import DynamicScoringOrchestrator, LeadSegment, MarketMetrics, ScoringWeights
from .lead_scorer import LeadScorer


@dataclass
class ScoringMode:
    """Scoring mode configuration"""

    JORGE_ORIGINAL = "jorge_original"  # Question count only
    ML_ENHANCED = "ml_enhanced"  # ML + questions
    DYNAMIC_ADAPTIVE = "dynamic_adaptive"  # Full dynamic system
    HYBRID = "hybrid"  # All systems combined


@dataclass
class EnhancedScoringResult:
    """Comprehensive scoring result from all systems"""

    # Core results
    lead_id: str
    final_score: float  # 0-100 unified score
    classification: str  # hot/warm/cold
    confidence: float  # 0-1 confidence level

    # Component scores
    jorge_score: int  # Original question count (0-7)
    ml_score: float  # ML prediction score (0-100)
    dynamic_score: float  # Dynamic weighted score (0-100)

    # Metadata
    segment: str
    market_condition: str
    weights_profile: Dict[str, float]
    scoring_mode: str

    # Explanations
    reasoning: str
    factors: List[Dict[str, Any]]
    recommended_actions: List[str]

    # System info
    scored_at: datetime
    response_time_ms: int
    fallback_used: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        result = asdict(self)
        result["scored_at"] = self.scored_at.isoformat()
        return result


class ScoringFallbackManager:
    """
    Manages graceful degradation when components fail

    Fallback hierarchy:
    1. Dynamic Adaptive (full system)
    2. ML Enhanced (ML + questions)
    3. Jorge Original (questions only)
    4. Static fallback (basic heuristics)
    """

    def __init__(self):
        self.failure_counts = {}
        self.last_failures = {}
        self.circuit_breakers = {}

    def is_circuit_open(self, component: str) -> bool:
        """Check if circuit breaker is open for component"""
        if component not in self.circuit_breakers:
            return False

        failure_count, last_failure = self.circuit_breakers[component]

        # Open circuit if too many failures recently
        if failure_count >= 3 and last_failure > datetime.now() - timedelta(minutes=5):
            return True

        # Reset if enough time has passed
        if last_failure < datetime.now() - timedelta(minutes=10):
            self.circuit_breakers[component] = (0, datetime.now())

        return False

    def record_failure(self, component: str):
        """Record a failure for circuit breaker logic"""
        if component not in self.circuit_breakers:
            self.circuit_breakers[component] = (0, datetime.now())

        count, _ = self.circuit_breakers[component]
        self.circuit_breakers[component] = (count + 1, datetime.now())

    def record_success(self, component: str):
        """Record success - helps reset circuit breaker"""
        if component in self.circuit_breakers:
            count, last_failure = self.circuit_breakers[component]
            if count > 0:
                self.circuit_breakers[component] = (max(0, count - 1), last_failure)


class EnhancedLeadScorer:
    """
    Unified lead scoring service with intelligent orchestration

    Provides:
    - Backwards compatible API
    - Intelligent scoring mode selection
    - Graceful degradation
    - Performance monitoring
    - A/B testing support
    """

    def __init__(self, redis_url: Optional[str] = None, default_mode: str = ScoringMode.HYBRID):
        # Initialize component scorers
        self.jorge_scorer = LeadScorer()
        self.ml_scorer = PredictiveLeadScorer()
        self.dynamic_orchestrator = DynamicScoringOrchestrator(redis_url)

        # Configuration
        self.default_mode = default_mode
        self.fallback_manager = ScoringFallbackManager()

        # Performance tracking
        self.performance_stats = {"total_scores": 0, "avg_response_time": 0, "mode_usage": {}, "fallback_rate": 0}

    async def score_lead(
        self,
        lead_id: str,
        context: Dict[str, Any],
        tenant_id: str = "default",
        mode: Optional[str] = None,
        segment: Optional[LeadSegment] = None,
    ) -> EnhancedScoringResult:
        """
        Score a lead using the enhanced scoring system

        Args:
            lead_id: Lead identifier
            context: Lead context data (compatible with original format)
            tenant_id: Tenant identifier for multi-tenant support
            mode: Scoring mode override
            segment: Lead segment override

        Returns:
            Comprehensive scoring result
        """
        start_time = datetime.now()
        scoring_mode = mode or self.default_mode
        fallback_used = False

        try:
            # Attempt scoring with requested mode
            if scoring_mode == ScoringMode.DYNAMIC_ADAPTIVE:
                result = await self._score_dynamic_adaptive(lead_id, context, tenant_id, segment)
            elif scoring_mode == ScoringMode.ML_ENHANCED:
                result = await self._score_ml_enhanced(lead_id, context, tenant_id, segment)
            elif scoring_mode == ScoringMode.HYBRID:
                result = await self._score_hybrid(lead_id, context, tenant_id, segment)
            else:  # JORGE_ORIGINAL
                result = await self._score_jorge_original(lead_id, context, tenant_id, segment)

        except Exception as e:
            # Fallback to simpler modes
            print(f"Scoring failed for mode {scoring_mode}: {e}")
            fallback_used = True
            self.fallback_manager.record_failure(scoring_mode)

            result = await self._fallback_scoring(lead_id, context, tenant_id, segment, scoring_mode)

        # Calculate response time
        response_time = datetime.now() - start_time
        result.response_time_ms = int(response_time.total_seconds() * 1000)
        result.fallback_used = fallback_used

        # Update performance stats
        self._update_performance_stats(scoring_mode, result.response_time_ms, fallback_used)

        # Record success if no fallback
        if not fallback_used:
            self.fallback_manager.record_success(scoring_mode)

        return result

    async def _score_dynamic_adaptive(
        self, lead_id: str, context: Dict[str, Any], tenant_id: str, segment: Optional[LeadSegment]
    ) -> EnhancedScoringResult:
        """Score using full dynamic adaptive system"""

        if self.fallback_manager.is_circuit_open("dynamic_adaptive"):
            raise Exception("Dynamic adaptive circuit breaker is open")

        # Convert context to dynamic scorer format
        lead_data = self._convert_context_to_lead_data(context)

        # Get dynamic score
        dynamic_result = await self.dynamic_orchestrator.score_lead_with_dynamic_weights(
            tenant_id=tenant_id, lead_id=lead_id, lead_data=lead_data, segment=segment
        )

        # Get Jorge score for comparison
        jorge_result = self.jorge_scorer.calculate_with_reasoning(context)

        # Get ML score for additional insight
        try:
            ml_result = self.ml_scorer.score_lead(lead_id, lead_data, include_explanation=True)
            ml_score = ml_result.score
        except:
            ml_score = None

        # Create unified result
        return self._create_unified_result(
            lead_id=lead_id,
            jorge_result=jorge_result,
            ml_score=ml_score,
            dynamic_result=dynamic_result,
            scoring_mode=ScoringMode.DYNAMIC_ADAPTIVE,
        )

    async def _score_ml_enhanced(
        self, lead_id: str, context: Dict[str, Any], tenant_id: str, segment: Optional[LeadSegment]
    ) -> EnhancedScoringResult:
        """Score using ML enhanced mode"""

        if self.fallback_manager.is_circuit_open("ml_enhanced"):
            raise Exception("ML enhanced circuit breaker is open")

        # Get Jorge score
        jorge_result = self.jorge_scorer.calculate_with_reasoning(context)

        # Get ML score
        lead_data = self._convert_context_to_lead_data(context)
        ml_result = self.ml_scorer.score_lead(lead_id, lead_data, include_explanation=True)

        # Combine scores (weighted average)
        jorge_weight = 0.4  # 40% Jorge (questions)
        ml_weight = 0.6  # 60% ML prediction

        combined_score = (jorge_result["score"] / 7.0 * 100 * jorge_weight) + (ml_result.score * ml_weight)

        # Determine classification
        classification = self._classify_combined_score(combined_score, ml_result.confidence)

        return EnhancedScoringResult(
            lead_id=lead_id,
            final_score=combined_score,
            classification=classification,
            confidence=ml_result.confidence,
            jorge_score=jorge_result["score"],
            ml_score=ml_result.score,
            dynamic_score=0.0,  # Not used in this mode
            segment=segment.value if segment else "unknown",
            market_condition="unknown",
            weights_profile={},
            scoring_mode=ScoringMode.ML_ENHANCED,
            reasoning=f"{jorge_result['reasoning']} | ML: {ml_result.score:.1f}/100",
            factors=ml_result.factors,
            recommended_actions=jorge_result["recommended_actions"],
            scored_at=datetime.now(),
            response_time_ms=0,
        )

    async def _score_jorge_original(
        self, lead_id: str, context: Dict[str, Any], tenant_id: str, segment: Optional[LeadSegment]
    ) -> EnhancedScoringResult:
        """Score using original Jorge method only"""

        jorge_result = self.jorge_scorer.calculate_with_reasoning(context)

        # Convert question count to 0-100 score
        final_score = (jorge_result["score"] / 7.0) * 100

        return EnhancedScoringResult(
            lead_id=lead_id,
            final_score=final_score,
            classification=jorge_result["classification"],
            confidence=0.9,  # High confidence in simple method
            jorge_score=jorge_result["score"],
            ml_score=0.0,
            dynamic_score=0.0,
            segment=segment.value if segment else "unknown",
            market_condition="unknown",
            weights_profile={},
            scoring_mode=ScoringMode.JORGE_ORIGINAL,
            reasoning=jorge_result["reasoning"],
            factors=[],
            recommended_actions=jorge_result["recommended_actions"],
            scored_at=datetime.now(),
            response_time_ms=0,
        )

    async def _score_hybrid(
        self, lead_id: str, context: Dict[str, Any], tenant_id: str, segment: Optional[LeadSegment]
    ) -> EnhancedScoringResult:
        """Score using hybrid approach - all systems combined"""

        # Try to get all scores
        jorge_result = self.jorge_scorer.calculate_with_reasoning(context)
        lead_data = self._convert_context_to_lead_data(context)

        ml_score = None
        dynamic_result = None

        # Try ML scoring
        try:
            if not self.fallback_manager.is_circuit_open("ml_scorer"):
                ml_result = self.ml_scorer.score_lead(lead_id, lead_data, include_explanation=True)
                ml_score = ml_result.score
        except:
            self.fallback_manager.record_failure("ml_scorer")

        # Try dynamic scoring
        try:
            if not self.fallback_manager.is_circuit_open("dynamic_scorer"):
                dynamic_result = await self.dynamic_orchestrator.score_lead_with_dynamic_weights(
                    tenant_id=tenant_id, lead_id=lead_id, lead_data=lead_data, segment=segment
                )
        except:
            self.fallback_manager.record_failure("dynamic_scorer")

        # Combine available scores intelligently
        return self._create_hybrid_result(
            lead_id=lead_id,
            jorge_result=jorge_result,
            ml_score=ml_score,
            dynamic_result=dynamic_result,
            segment=segment,
        )

    async def _fallback_scoring(
        self, lead_id: str, context: Dict[str, Any], tenant_id: str, segment: Optional[LeadSegment], failed_mode: str
    ) -> EnhancedScoringResult:
        """Fallback scoring when primary method fails"""

        # Try progressively simpler modes
        if failed_mode == ScoringMode.DYNAMIC_ADAPTIVE:
            try:
                return await self._score_ml_enhanced(lead_id, context, tenant_id, segment)
            except:
                pass

        if failed_mode in [ScoringMode.DYNAMIC_ADAPTIVE, ScoringMode.ML_ENHANCED]:
            try:
                return await self._score_jorge_original(lead_id, context, tenant_id, segment)
            except:
                pass

        # Final fallback - static heuristics
        return self._static_fallback_score(lead_id, context, segment)

    def _static_fallback_score(
        self, lead_id: str, context: Dict[str, Any], segment: Optional[LeadSegment]
    ) -> EnhancedScoringResult:
        """Static fallback when all else fails"""

        prefs = context.get("extracted_preferences", {})

        # Simple heuristic scoring
        score = 30  # Base score

        if prefs.get("budget"):
            score += 20
        if prefs.get("location"):
            score += 15
        if prefs.get("timeline"):
            score += 15
        if prefs.get("bedrooms") or prefs.get("bathrooms"):
            score += 10
        if prefs.get("financing"):
            score += 10

        classification = "hot" if score >= 70 else "warm" if score >= 50 else "cold"

        return EnhancedScoringResult(
            lead_id=lead_id,
            final_score=min(score, 100),
            classification=classification,
            confidence=0.5,  # Low confidence in fallback
            jorge_score=0,
            ml_score=0.0,
            dynamic_score=0.0,
            segment=segment.value if segment else "unknown",
            market_condition="unknown",
            weights_profile={},
            scoring_mode="static_fallback",
            reasoning="Static fallback due to system failures",
            factors=[],
            recommended_actions=["Manual review required", "System failures detected"],
            scored_at=datetime.now(),
            response_time_ms=0,
            fallback_used=True,
        )

    def _create_unified_result(
        self,
        lead_id: str,
        jorge_result: Dict[str, Any],
        ml_score: Optional[float],
        dynamic_result: Dict[str, Any],
        scoring_mode: str,
    ) -> EnhancedScoringResult:
        """Create unified result from all scoring components"""

        # Use dynamic score as primary
        final_score = dynamic_result["score"]
        classification = dynamic_result["tier"]

        # Build comprehensive reasoning
        reasoning_parts = [f"Questions: {jorge_result['reasoning']}", f"Dynamic: {final_score:.1f}/100"]

        if ml_score:
            reasoning_parts.append(f"ML: {ml_score:.1f}/100")

        # Combine factors from all sources
        factors = dynamic_result.get("feature_contributions", {})
        factor_list = [
            {"name": name.replace("_", " ").title(), "value": f"{value:.3f}", "impact": round(value * 100, 1)}
            for name, value in factors.items()
        ]

        return EnhancedScoringResult(
            lead_id=lead_id,
            final_score=final_score,
            classification=classification,
            confidence=dynamic_result.get("confidence", 0.8),
            jorge_score=jorge_result["score"],
            ml_score=ml_score or 0.0,
            dynamic_score=final_score,
            segment=dynamic_result.get("segment", "unknown"),
            market_condition=dynamic_result.get("market_condition", "unknown"),
            weights_profile=dynamic_result.get("weights_used", {}),
            scoring_mode=scoring_mode,
            reasoning=" | ".join(reasoning_parts),
            factors=factor_list,
            recommended_actions=jorge_result["recommended_actions"],
            scored_at=datetime.now(),
            response_time_ms=0,
        )

    def _create_hybrid_result(
        self,
        lead_id: str,
        jorge_result: Dict[str, Any],
        ml_score: Optional[float],
        dynamic_result: Optional[Dict[str, Any]],
        segment: Optional[LeadSegment],
    ) -> EnhancedScoringResult:
        """Create result from hybrid scoring approach"""

        # Determine which scores are available
        jorge_score_normalized = (jorge_result["score"] / 7.0) * 100

        available_scores = [jorge_score_normalized]
        weights = [0.4]  # Jorge base weight

        if ml_score is not None:
            available_scores.append(ml_score)
            weights.append(0.3)  # ML weight

        if dynamic_result is not None:
            available_scores.append(dynamic_result["score"])
            weights.append(0.3)  # Dynamic weight

        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        # Calculate weighted average
        final_score = sum(score * weight for score, weight in zip(available_scores, weights))

        # Determine classification
        classification = self._classify_combined_score(final_score, 0.8)

        # Build reasoning
        reasoning_parts = [f"Questions: {jorge_result['reasoning']}"]
        if ml_score:
            reasoning_parts.append(f"ML: {ml_score:.1f}")
        if dynamic_result:
            reasoning_parts.append(f"Dynamic: {dynamic_result['score']:.1f}")

        return EnhancedScoringResult(
            lead_id=lead_id,
            final_score=final_score,
            classification=classification,
            confidence=0.85 if len(available_scores) > 1 else 0.6,
            jorge_score=jorge_result["score"],
            ml_score=ml_score or 0.0,
            dynamic_score=dynamic_result["score"] if dynamic_result else 0.0,
            segment=segment.value if segment else "unknown",
            market_condition=dynamic_result.get("market_condition", "unknown") if dynamic_result else "unknown",
            weights_profile=dynamic_result.get("weights_used", {}) if dynamic_result else {},
            scoring_mode=ScoringMode.HYBRID,
            reasoning=" | ".join(reasoning_parts),
            factors=dynamic_result.get("factors", []) if dynamic_result else [],
            recommended_actions=jorge_result["recommended_actions"],
            scored_at=datetime.now(),
            response_time_ms=0,
        )

    def _convert_context_to_lead_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Convert original context format to lead_data format for ML/dynamic scorers"""

        prefs = context.get("extracted_preferences", {})
        messages = context.get("conversation_history", [])

        # Extract budget
        budget = 0
        budget_str = prefs.get("budget", "")
        if budget_str:
            try:
                # Simple budget parsing
                budget_str = str(budget_str).replace("$", "").replace(",", "").replace("k", "000")
                budget = float(budget_str)
            except:
                budget = 0

        # Convert to lead_data format
        lead_data = {
            "budget": budget,
            "location": prefs.get("location", ""),
            "timeline": prefs.get("timeline", ""),
            "bedrooms": prefs.get("bedrooms", 0),
            "bathrooms": prefs.get("bathrooms", 0),
            "financing": prefs.get("financing", ""),
            "motivation": prefs.get("motivation", ""),
            "messages": [{"content": msg.get("content", "")} for msg in messages],
            "source": "direct",  # Default
            "page_views": len(messages),  # Approximate
            "email_opens": max(1, len(messages) // 2),  # Approximate
            "emails_sent": max(1, len(messages) // 3),  # Approximate
            "property_matches": 0,  # Would need actual data
            "communication_quality": min(len(" ".join(msg.get("content", "") for msg in messages)) / 200.0, 1.0),
        }

        return lead_data

    def _classify_combined_score(self, score: float, confidence: float) -> str:
        """Classify combined score into tier"""
        # Adjust thresholds based on confidence
        if confidence > 0.8:
            hot_threshold = 70
            warm_threshold = 50
        else:
            hot_threshold = 75
            warm_threshold = 55

        if score >= hot_threshold:
            return "hot"
        elif score >= warm_threshold:
            return "warm"
        else:
            return "cold"

    def _update_performance_stats(self, mode: str, response_time: int, fallback_used: bool):
        """Update performance statistics"""
        self.performance_stats["total_scores"] += 1

        # Update average response time
        current_avg = self.performance_stats["avg_response_time"]
        total_scores = self.performance_stats["total_scores"]
        self.performance_stats["avg_response_time"] = (current_avg * (total_scores - 1) + response_time) / total_scores

        # Update mode usage
        if mode not in self.performance_stats["mode_usage"]:
            self.performance_stats["mode_usage"][mode] = 0
        self.performance_stats["mode_usage"][mode] += 1

        # Update fallback rate
        if fallback_used:
            self.performance_stats["fallback_rate"] = (
                self.performance_stats["fallback_rate"] * (total_scores - 1) + 1
            ) / total_scores
        else:
            self.performance_stats["fallback_rate"] = (
                self.performance_stats["fallback_rate"] * (total_scores - 1)
            ) / total_scores

    # Backwards compatible methods
    def calculate(self, context: Dict[str, Any]) -> int:
        """Backwards compatible calculate method (returns Jorge score)"""
        result = asyncio.run(self.score_lead("unknown", context, mode=ScoringMode.JORGE_ORIGINAL))
        return result.jorge_score

    def classify(self, score: int) -> str:
        """Backwards compatible classify method"""
        return self.jorge_scorer.classify(score)

    def calculate_with_reasoning(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Backwards compatible reasoning method"""
        result = asyncio.run(self.score_lead("unknown", context, mode=ScoringMode.JORGE_ORIGINAL))

        return {
            "score": result.jorge_score,
            "classification": result.classification,
            "reasoning": result.reasoning,
            "recommended_actions": result.recommended_actions,
        }

    # New enhanced methods
    async def score_with_explanation(
        self, lead_id: str, context: Dict[str, Any], tenant_id: str = "default"
    ) -> Dict[str, Any]:
        """Score lead with full explanation - new enhanced API"""

        result = await self.score_lead(lead_id, context, tenant_id, mode=ScoringMode.HYBRID)
        return result.to_dict()

    async def batch_score_leads(
        self, leads: List[Dict[str, Any]], tenant_id: str = "default", mode: Optional[str] = None
    ) -> List[EnhancedScoringResult]:
        """Score multiple leads efficiently"""

        tasks = []
        for lead in leads:
            lead_id = lead.get("id", f"batch_{hash(str(lead))}")
            context = lead.get("context", lead)

            task = self.score_lead(lead_id, context, tenant_id, mode)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return valid results
        valid_results = [r for r in results if isinstance(r, EnhancedScoringResult)]
        return valid_results

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get scorer performance statistics"""
        stats = self.performance_stats.copy()

        # Add circuit breaker status
        stats["circuit_breakers"] = {}
        for component in ["dynamic_adaptive", "ml_enhanced", "ml_scorer", "dynamic_scorer"]:
            stats["circuit_breakers"][component] = {
                "is_open": self.fallback_manager.is_circuit_open(component),
                "failure_count": self.fallback_manager.circuit_breakers.get(component, (0, None))[0],
            }

        return stats

    async def record_conversion(
        self, lead_id: str, converted: bool, conversion_value: float = 0.0, context: Optional[Dict[str, Any]] = None
    ):
        """Record conversion outcome for optimization"""
        if context:
            lead_data = self._convert_context_to_lead_data(context)

            await self.dynamic_orchestrator.record_conversion_outcome(
                tenant_id="default",
                lead_id=lead_id,
                converted=converted,
                conversion_value=conversion_value,
                lead_data=lead_data,
            )


# Factory function for easy initialization
def create_enhanced_scorer(redis_url: Optional[str] = None, mode: str = ScoringMode.HYBRID) -> EnhancedLeadScorer:
    """
    Factory function to create enhanced lead scorer

    Args:
        redis_url: Redis URL for caching and optimization
        mode: Default scoring mode

    Returns:
        Configured EnhancedLeadScorer instance
    """
    return EnhancedLeadScorer(redis_url=redis_url, default_mode=mode)


# Example usage and testing
if __name__ == "__main__":

    async def main():
        # Create enhanced scorer
        scorer = create_enhanced_scorer(mode=ScoringMode.HYBRID)

        # Example context (original format)
        context = {
            "extracted_preferences": {
                "budget": "$750,000",
                "location": "Austin, TX",
                "timeline": "next 2 months",
                "bedrooms": 3,
                "bathrooms": 2,
                "financing": "pre-approved",
                "motivation": "growing family",
            },
            "conversation_history": [
                {"content": "Looking for a 3-bedroom house in Austin"},
                {"content": "Budget is around $750k, need to move by spring"},
                {"content": "Already pre-approved for mortgage"},
            ],
            "created_at": datetime.now(),
        }

        # Test different scoring modes
        print("🎯 Enhanced Lead Scoring Results:\n")

        modes = [ScoringMode.JORGE_ORIGINAL, ScoringMode.ML_ENHANCED, ScoringMode.HYBRID]

        for mode in modes:
            result = await scorer.score_lead(lead_id="test_123", context=context, tenant_id="demo_tenant", mode=mode)

            print(f"📊 {mode.replace('_', ' ').upper()}:")
            print(f"   Final Score: {result.final_score:.1f}/100")
            print(f"   Classification: {result.classification.upper()}")
            print(f"   Confidence: {result.confidence:.1%}")
            print(f"   Response Time: {result.response_time_ms}ms")
            print(f"   Fallback Used: {result.fallback_used}")

            if result.jorge_score > 0:
                print(f"   Jorge Score: {result.jorge_score}/7 questions")
            if result.ml_score > 0:
                print(f"   ML Score: {result.ml_score:.1f}/100")
            if result.dynamic_score > 0:
                print(f"   Dynamic Score: {result.dynamic_score:.1f}/100")

            print(f"   Reasoning: {result.reasoning[:100]}...")
            print()

        # Test backwards compatibility
        print("🔄 Backwards Compatibility Test:")
        jorge_score = scorer.calculate(context)
        classification = scorer.classify(jorge_score)
        reasoning_result = scorer.calculate_with_reasoning(context)

        print(f"   Original API - Score: {jorge_score}, Classification: {classification}")
        print(f"   Reasoning: {reasoning_result['reasoning'][:50]}...")
        print()

        # Test batch scoring
        print("📦 Batch Scoring Test:")
        leads = [{"id": "batch_1", "context": context}, {"id": "batch_2", "context": context}]

        batch_results = await scorer.batch_score_leads(leads)
        print(f"   Scored {len(batch_results)} leads successfully")
        print()

        # Show performance stats
        print("📈 Performance Stats:")
        stats = scorer.get_performance_stats()
        print(f"   Total Scores: {stats['total_scores']}")
        print(f"   Avg Response Time: {stats['avg_response_time']:.1f}ms")
        print(f"   Fallback Rate: {stats['fallback_rate']:.1%}")
        print(f"   Mode Usage: {stats['mode_usage']}")

    # Run the example
    asyncio.run(main())
