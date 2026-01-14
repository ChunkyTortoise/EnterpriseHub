"""
Claude Enhanced Lead Scorer - Unified Intelligence Layer
Combines quantitative scoring with Claude AI reasoning for comprehensive lead analysis
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import json

from services.memory_service import MemoryService


@dataclass
class UnifiedScoringResult:
    """
    Comprehensive scoring result that combines all scoring dimensions
    with Claude AI reasoning and strategic insights
    """
    # Identity
    lead_id: str
    lead_name: str
    scored_at: datetime

    # Unified Scoring (0-100 scale)
    final_score: float
    confidence_score: float
    classification: str  # hot, warm, cold

    # Component Scores
    jorge_score: int  # 0-7 questions answered
    ml_conversion_score: float  # 0-100 conversion probability
    churn_risk_score: float  # 0-100 risk of churn
    engagement_score: float  # 0-100 engagement level

    # Claude AI Analysis
    strategic_summary: str  # Executive summary
    behavioral_insights: str  # Personality and behavior analysis
    reasoning: str  # Why this score makes sense
    risk_factors: List[str]  # Things that could go wrong
    opportunities: List[str]  # Growth and conversion opportunities

    # Actionable Intelligence
    recommended_actions: List[Dict[str, Any]]  # Prioritized action items
    next_best_action: str  # Single most important next step
    expected_timeline: str  # When to expect conversion/action
    success_probability: float  # 0-100 likelihood of success

    # Supporting Data
    feature_breakdown: Dict[str, Any]  # Which features drove the score
    conversation_context: Dict[str, Any]  # Memory and history
    sources: List[str]  # Data sources used in analysis

    # Performance Metrics
    analysis_time_ms: int
    claude_reasoning_time_ms: int


class ClaudeEnhancedLeadScorer:
    """
    Unified lead scoring system that combines:
    1. Jorge's question-based scoring (0-7)
    2. ML predictive scoring (0-100)
    3. Churn risk assessment (0-100)
    4. Claude AI strategic reasoning

    Provides comprehensive lead intelligence with actionable insights.
    """

    def __init__(self,
                 claude_orchestrator: Optional[Any] = None,
                 memory_service: Optional[MemoryService] = None):
        # Local imports to avoid circular dependencies
        from services.claude_orchestrator import get_claude_orchestrator
        from services.lead_scorer import LeadScorer
        from services.predictive_lead_scorer import PredictiveLeadScorer
        from services.churn_prediction_engine import ChurnPredictionEngine
        from services.lead_lifecycle import LeadLifecycleTracker
        from services.behavioral_triggers import BehavioralTriggerEngine

        # Core services
        self.claude = claude_orchestrator or get_claude_orchestrator()
        self.memory = memory_service or MemoryService()

        # Component scorers
        self.jorge_scorer = LeadScorer()
        self.ml_scorer = PredictiveLeadScorer()
        
        # Initialize dependencies for ChurnPredictionEngine
        try:
            self.lifecycle_tracker = LeadLifecycleTracker(location_id="demo_location")
            self.behavioral_engine = BehavioralTriggerEngine()
            
            self.churn_predictor = ChurnPredictionEngine(
                memory_service=self.memory,
                lifecycle_tracker=self.lifecycle_tracker,
                behavioral_engine=self.behavioral_engine,
                lead_scorer=self.jorge_scorer
            )
        except Exception as e:
            print(f"Warning: ChurnPredictionEngine initialization failed in ClaudeEnhancedLeadScorer: {e}")
            self.churn_predictor = None

        # Performance tracking
        self.metrics = {
            "analyses_completed": 0,
            "avg_analysis_time_ms": 0,
            "avg_claude_time_ms": 0,
            "errors": 0
        }

    async def analyze_lead_comprehensive(self,
                                       lead_id: str,
                                       lead_context: Dict[str, Any]) -> UnifiedScoringResult:
        """
        Comprehensive lead analysis combining all scoring systems with Claude reasoning.

        Args:
            lead_id: Unique identifier for the lead
            lead_context: Lead data including preferences, conversations, etc.

        Returns:
            UnifiedScoringResult with complete analysis and recommendations
        """
        start_time = datetime.now()

        try:
            # Step 1: Run all scoring systems in parallel
            jorge_result, ml_result, churn_result, memory_context = await asyncio.gather(
                self._run_jorge_scoring(lead_context),
                self._run_ml_scoring(lead_context),
                self._run_churn_analysis(lead_id, lead_context),
                self._get_memory_context(lead_id),
                return_exceptions=True
            )

            # Handle exceptions gracefully
            if isinstance(jorge_result, Exception):
                jorge_result = {"score": 0, "classification": "cold", "reasoning": f"Error: {jorge_result}"}
            if isinstance(ml_result, Exception):
                ml_result = {"score": 0, "confidence": 0.5, "reasoning": f"Error: {ml_result}"}
            if isinstance(churn_result, Exception):
                churn_result = {"risk_score_7d": 50, "risk_tier": "medium"}
            if isinstance(memory_context, Exception):
                memory_context = {"relevant_knowledge": "", "conversation_history": []}

            # Step 2: Calculate unified scores
            unified_scores = self._calculate_unified_scores(
                jorge_result, ml_result, churn_result
            )

            # Step 3: Generate Claude reasoning
            claude_start = datetime.now()
            claude_analysis = await self._generate_claude_reasoning(
                lead_id=lead_id,
                lead_context=lead_context,
                jorge_result=jorge_result,
                ml_result=ml_result,
                churn_result=churn_result,
                memory_context=memory_context,
                unified_scores=unified_scores
            )
            claude_time = (datetime.now() - claude_start).total_seconds() * 1000

            # Step 4: Build comprehensive result
            total_time = (datetime.now() - start_time).total_seconds() * 1000

            result = UnifiedScoringResult(
                # Identity
                lead_id=lead_id,
                lead_name=lead_context.get('name', 'Unknown Lead'),
                scored_at=datetime.now(),

                # Unified Scoring
                final_score=unified_scores['final_score'],
                confidence_score=unified_scores['confidence_score'],
                classification=unified_scores['classification'],

                # Component Scores
                jorge_score=jorge_result['score'],
                ml_conversion_score=ml_result.get('score', 0),
                churn_risk_score=churn_result.get('risk_score_7d', 50),
                engagement_score=self._calculate_engagement_score(lead_context, memory_context),

                # Claude Analysis
                strategic_summary=claude_analysis.get('strategic_summary', ''),
                behavioral_insights=claude_analysis.get('behavioral_insights', ''),
                reasoning=claude_analysis.get('reasoning', ''),
                risk_factors=claude_analysis.get('risk_factors', []),
                opportunities=claude_analysis.get('opportunities', []),

                # Actionable Intelligence
                recommended_actions=claude_analysis.get('recommended_actions', []),
                next_best_action=claude_analysis.get('next_best_action', ''),
                expected_timeline=claude_analysis.get('expected_timeline', 'Unknown'),
                success_probability=claude_analysis.get('success_probability', 50.0),

                # Supporting Data
                feature_breakdown={
                    "jorge_factors": jorge_result.get('reasoning', ''),
                    "ml_factors": ml_result.get('reasoning', []),
                    "churn_factors": churn_result.get('top_risk_factors', []),
                },
                conversation_context=memory_context,
                sources=claude_analysis.get('sources', []),

                # Performance
                analysis_time_ms=int(total_time),
                claude_reasoning_time_ms=int(claude_time)
            )

            # Update metrics
            self._update_metrics(int(total_time), int(claude_time), success=True)

            return result

        except Exception as e:
            self._update_metrics(0, 0, success=False)

            # Return error result with minimal data
            return UnifiedScoringResult(
                lead_id=lead_id,
                lead_name=lead_context.get('name', 'Unknown Lead'),
                scored_at=datetime.now(),
                final_score=0,
                confidence_score=0.1,
                classification="error",
                jorge_score=0,
                ml_conversion_score=0,
                churn_risk_score=50,
                engagement_score=0,
                strategic_summary=f"Analysis failed: {str(e)}",
                behavioral_insights="Unable to analyze due to error",
                reasoning=f"Error in scoring pipeline: {str(e)}",
                risk_factors=["System error prevented analysis"],
                opportunities=[],
                recommended_actions=[{"action": "Retry analysis", "priority": "high"}],
                next_best_action="Fix technical issue and retry analysis",
                expected_timeline="Unknown due to error",
                success_probability=0,
                feature_breakdown={},
                conversation_context={},
                sources=[],
                analysis_time_ms=0,
                claude_reasoning_time_ms=0
            )

    async def _run_jorge_scoring(self, lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """Run Jorge's question-based scoring"""
        try:
            result = self.jorge_scorer.calculate_with_reasoning(lead_context)
            return result
        except Exception as e:
            return {"score": 0, "classification": "cold", "reasoning": f"Jorge scoring error: {e}"}

    async def _run_ml_scoring(self, lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """Run ML predictive scoring"""
        try:
            lead_id = lead_context.get('lead_id', 'unknown')
            # score_lead is synchronous and returns a LeadScore dataclass
            score_result = self.ml_scorer.score_lead(lead_id, lead_context)
            return {
                "score": score_result.score,
                "confidence": score_result.confidence,
                "reasoning": score_result.reasoning,
                "tier": score_result.tier
            }
        except Exception as e:
            return {"score": 0, "confidence": 0.5, "reasoning": f"ML scoring error: {e}"}

    async def _run_churn_analysis(self, lead_id: str, lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """Run churn risk analysis"""
        try:
            # Note: This assumes churn predictor is async-compatible
            result = await asyncio.to_thread(
                self.churn_predictor.predict_churn_risk, lead_id
            )
            return result
        except Exception as e:
            return {"risk_score_7d": 50, "risk_tier": "medium", "error": str(e)}

    async def _get_memory_context(self, lead_id: str) -> Dict[str, Any]:
        """Get conversation history and semantic memory"""
        try:
            context = await self.memory.get_context(lead_id)
            return context
        except Exception as e:
            return {"relevant_knowledge": "", "conversation_history": [], "error": str(e)}

    def _calculate_unified_scores(self,
                                jorge_result: Dict[str, Any],
                                ml_result: Dict[str, Any],
                                churn_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate unified scores from component systems.

        Logic:
        - Jorge score (0-7) → normalized to 0-100
        - ML score is already 0-100
        - Churn risk (0-100) → inverted (high risk = low conversion)
        - Final score is weighted average with confidence adjustment
        """
        # Normalize Jorge score to 0-100
        jorge_normalized = (jorge_result.get('score', 0) / 7.0) * 100

        # Get ML score
        ml_score = ml_result.get('score', 0)
        ml_confidence = ml_result.get('confidence', 0.5)

        # Get churn risk (invert since high risk = bad)
        churn_risk = churn_result.get('risk_score_7d', 50)
        churn_adjusted = 100 - churn_risk  # Invert

        # Weighted average with confidence adjustment
        weights = {
            'jorge': 0.3,  # 30% weight on qualification questions
            'ml': 0.5,     # 50% weight on ML prediction
            'churn': 0.2   # 20% weight on churn risk
        }

        final_score = (
            (jorge_normalized * weights['jorge']) +
            (ml_score * weights['ml']) +
            (churn_adjusted * weights['churn'])
        )

        # Adjust confidence based on component confidences
        confidence_score = min(ml_confidence, 0.95)  # Cap at 95%

        # Determine classification
        if final_score >= 70:
            classification = "hot"
        elif final_score >= 40:
            classification = "warm"
        else:
            classification = "cold"

        return {
            'final_score': round(final_score, 1),
            'confidence_score': round(confidence_score, 2),
            'classification': classification
        }

    def _calculate_engagement_score(self,
                                  lead_context: Dict[str, Any],
                                  memory_context: Dict[str, Any]) -> float:
        """Calculate engagement score from conversation history"""
        history = memory_context.get('conversation_history', [])

        if not history:
            return 0.0

        # Simple engagement scoring
        message_count = len(history)
        user_messages = [msg for msg in history if msg.get('role') == 'user']

        # Score based on message count and recency
        base_score = min(message_count * 10, 70)  # Up to 70 points for activity

        # Bonus for recent activity
        try:
            last_message = history[-1]
            last_time = datetime.fromisoformat(last_message.get('timestamp', datetime.now().isoformat()))
            hours_since = (datetime.now() - last_time).total_seconds() / 3600

            if hours_since < 24:
                base_score += 20  # Recent activity bonus
            elif hours_since < 72:
                base_score += 10  # Somewhat recent
        except:
            pass  # Skip recency bonus on error

        return min(base_score, 100.0)

    async def _generate_claude_reasoning(self,
                                       lead_id: str,
                                       lead_context: Dict[str, Any],
                                       jorge_result: Dict[str, Any],
                                       ml_result: Dict[str, Any],
                                       churn_result: Dict[str, Any],
                                       memory_context: Dict[str, Any],
                                       unified_scores: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive Claude reasoning for the lead analysis"""

        analysis_context = {
            "lead_id": lead_id,
            "lead_context": lead_context,
            "jorge_result": jorge_result,
            "ml_result": ml_result,
            "churn_result": churn_result,
            "memory_context": memory_context,
            "unified_scores": unified_scores,
            "analysis_timestamp": datetime.now().isoformat()
        }

        prompt = f"""Analyze this comprehensive lead intelligence data and provide strategic insights:

LEAD ANALYSIS DATA:
{json.dumps(analysis_context, indent=2, default=str)}

Provide a comprehensive analysis in the following format:

STRATEGIC SUMMARY: (2-3 sentences capturing the essence of this lead's potential)

BEHAVIORAL INSIGHTS: (Analysis of personality, communication style, decision-making patterns)

REASONING: (Detailed explanation of why the unified score makes sense, referencing specific data points)

RISK FACTORS: (List 3-5 specific risks that could prevent conversion)

OPPORTUNITIES: (List 3-5 specific opportunities to increase conversion probability)

RECOMMENDED ACTIONS: (5-7 prioritized actions with rationale and timing)

NEXT BEST ACTION: (Single most important immediate step)

EXPECTED TIMELINE: (Realistic conversion timeline based on data)

SUCCESS PROBABILITY: (0-100 percentage with rationale)

SOURCES: (List key data sources that informed this analysis)

Focus on actionable insights Jorge can use to improve conversion outcomes."""

        try:
            claude_response = await self.claude.analyze_lead(
                lead_id=lead_id,
                include_scoring=False,  # We already have scores
                include_churn_analysis=False  # We already have churn data
            )

            # Parse Claude response into structured format
            return self._parse_claude_response(claude_response.content)

        except Exception as e:
            # Fallback reasoning if Claude fails
            return {
                "strategic_summary": f"Lead scored {unified_scores['final_score']}/100 with {unified_scores['classification']} classification",
                "behavioral_insights": "Unable to generate behavioral insights due to Claude API error",
                "reasoning": f"Combined Jorge score ({jorge_result.get('score', 0)}/7), ML score ({ml_result.get('score', 0)}/100), and churn risk analysis",
                "risk_factors": ["Claude reasoning unavailable"],
                "opportunities": ["Retry analysis when system available"],
                "recommended_actions": [{"action": "Manual review required", "priority": "medium"}],
                "next_best_action": "Review lead manually due to system error",
                "expected_timeline": "Unknown due to analysis error",
                "success_probability": unified_scores['final_score'],
                "sources": ["Jorge Scorer", "ML Predictor", "Churn Engine"],
                "error": str(e)
            }

    def _parse_claude_response(self, response_content: str) -> Dict[str, Any]:
        """Parse Claude's analysis response into structured data"""

        # This is a simplified parser - could be enhanced with more robust parsing
        result = {
            "strategic_summary": "",
            "behavioral_insights": "",
            "reasoning": "",
            "risk_factors": [],
            "opportunities": [],
            "recommended_actions": [],
            "next_best_action": "",
            "expected_timeline": "",
            "success_probability": 50.0,
            "sources": []
        }

        try:
            # Basic parsing logic - extract sections
            sections = response_content.split('\n\n')

            for section in sections:
                if section.startswith('STRATEGIC SUMMARY:'):
                    result['strategic_summary'] = section.replace('STRATEGIC SUMMARY:', '').strip()
                elif section.startswith('BEHAVIORAL INSIGHTS:'):
                    result['behavioral_insights'] = section.replace('BEHAVIORAL INSIGHTS:', '').strip()
                elif section.startswith('REASONING:'):
                    result['reasoning'] = section.replace('REASONING:', '').strip()
                elif section.startswith('NEXT BEST ACTION:'):
                    result['next_best_action'] = section.replace('NEXT BEST ACTION:', '').strip()
                elif section.startswith('EXPECTED TIMELINE:'):
                    result['expected_timeline'] = section.replace('EXPECTED TIMELINE:', '').strip()
                elif section.startswith('SUCCESS PROBABILITY:'):
                    prob_text = section.replace('SUCCESS PROBABILITY:', '').strip()
                    # Extract number from text
                    import re
                    prob_match = re.search(r'(\d+(?:\.\d+)?)', prob_text)
                    if prob_match:
                        result['success_probability'] = float(prob_match.group(1))

            # For lists, this would need more sophisticated parsing
            # For now, use the full response as reasoning
            if not result['reasoning']:
                result['reasoning'] = response_content

            return result

        except Exception as e:
            # Return basic result if parsing fails
            return {
                **result,
                "reasoning": response_content,
                "error": f"Parsing error: {e}"
            }

    def _update_metrics(self, total_time: int, claude_time: int, success: bool):
        """Update performance metrics"""
        if success:
            count = self.metrics["analyses_completed"]
            self.metrics["analyses_completed"] += 1

            # Update averages
            self.metrics["avg_analysis_time_ms"] = (
                (self.metrics["avg_analysis_time_ms"] * count + total_time) /
                (count + 1)
            )
            self.metrics["avg_claude_time_ms"] = (
                (self.metrics["avg_claude_time_ms"] * count + claude_time) /
                (count + 1)
            )
        else:
            self.metrics["errors"] += 1

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            **self.metrics,
            "success_rate": (
                self.metrics["analyses_completed"] /
                (self.metrics["analyses_completed"] + self.metrics["errors"])
                if (self.metrics["analyses_completed"] + self.metrics["errors"]) > 0
                else 0
            )
        }


# Convenience functions
async def analyze_lead_with_claude(lead_id: str, lead_context: Dict[str, Any]) -> UnifiedScoringResult:
    """
    Convenience function for comprehensive lead analysis.

    Usage:
        result = await analyze_lead_with_claude("lead_123", lead_data)
        print(f"Score: {result.final_score}, Action: {result.next_best_action}")
    """
    scorer = ClaudeEnhancedLeadScorer()
    return await scorer.analyze_lead_comprehensive(lead_id, lead_context)


def create_enhanced_scorer() -> ClaudeEnhancedLeadScorer:
    """Factory function to create enhanced scorer instance"""
    return ClaudeEnhancedLeadScorer()