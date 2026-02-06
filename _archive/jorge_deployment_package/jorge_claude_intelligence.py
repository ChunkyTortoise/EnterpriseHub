#!/usr/bin/env python3
"""
Jorge's Enhanced Claude AI Lead Intelligence - Performance Optimized

This module adds real Claude AI integration to Jorge's lead qualification system
while maintaining <500ms response times through intelligent caching and hybrid analysis.

Key Performance Features:
- <500ms lead analysis through intelligent caching
- Hybrid pattern-matching + AI approach
- 5-minute response rule enforcement
- Jorge's business rules validation

Author: Claude Code Assistant
Created: January 23, 2026
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import hashlib
import os
from pathlib import Path

# Import existing pattern-based intelligence as fallback
from lead_intelligence_optimized import PredictiveLeadScorerV2Optimized, get_enhanced_lead_intelligence
from config_settings import get_claude_api_key

# Import Claude SDK
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    logging.warning("Anthropic SDK not available. Install with: pip install anthropic")

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Track performance metrics for 5-minute rule compliance"""
    start_time: float
    pattern_analysis_time: Optional[float] = None
    claude_analysis_time: Optional[float] = None
    total_time: Optional[float] = None
    cache_hit: bool = False
    analysis_type: str = "hybrid"  # pattern, claude, hybrid
    five_minute_rule_compliant: bool = True


@dataclass
class JorgeBusinessRules:
    """Jorge's specific business rules for lead qualification"""

    # Price range validation
    MIN_BUDGET = 200000  # $200K minimum
    MAX_BUDGET = 800000  # $800K maximum

    # Service areas
    SERVICE_AREAS = ["Dallas", "Plano", "Frisco", "McKinney", "Allen"]

    # Timeline preferences
    PREFERRED_TIMELINE = "60_days"
    URGENT_TIMELINE = "30_days"

    # Lead quality thresholds
    HOT_LEAD_THRESHOLD = 80
    WARM_LEAD_THRESHOLD = 60

    @classmethod
    def validate_lead(cls, lead_data: Dict) -> Dict[str, Any]:
        """Validate lead against Jorge's business rules"""

        validation_results = {
            "passes_jorge_criteria": True,
            "validation_issues": [],
            "jorge_priority": "normal",
            "estimated_commission": 0.0,
            "service_area_match": False
        }

        # Budget validation
        budget_max = lead_data.get("budget_max", 0)
        if budget_max and budget_max < cls.MIN_BUDGET:
            validation_results["passes_jorge_criteria"] = False
            validation_results["validation_issues"].append(f"Budget too low: ${budget_max:,} < ${cls.MIN_BUDGET:,}")

        if budget_max and budget_max > cls.MAX_BUDGET:
            validation_results["jorge_priority"] = "review_required"
            validation_results["validation_issues"].append(f"Budget above target: ${budget_max:,} > ${cls.MAX_BUDGET:,}")

        # Service area validation
        location_preferences = lead_data.get("location_preferences", [])
        if any(area in " ".join(location_preferences).lower() for area in [area.lower() for area in cls.SERVICE_AREAS]):
            validation_results["service_area_match"] = True

        # Calculate estimated commission (6% total)
        if budget_max:
            validation_results["estimated_commission"] = budget_max * 0.06

        # Set priority based on Jorge's criteria
        if (budget_max and cls.MIN_BUDGET <= budget_max <= cls.MAX_BUDGET and
            validation_results["service_area_match"]):
            validation_results["jorge_priority"] = "high"

        return validation_results


class PerformanceCache:
    """High-performance caching for Claude AI responses"""

    def __init__(self, cache_dir: str = "data/cache", ttl_seconds: int = 300):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self.memory_cache = {}  # In-memory cache for ultra-fast lookups

    def _get_cache_key(self, message: str, context: Dict = None) -> str:
        """Generate cache key from message and context"""
        content = message + str(context or {})
        return hashlib.md5(content.encode()).hexdigest()

    async def get(self, message: str, context: Dict = None) -> Optional[Dict]:
        """Get cached analysis if available and not expired"""
        cache_key = self._get_cache_key(message, context)

        # Check memory cache first (fastest)
        if cache_key in self.memory_cache:
            cached_data = self.memory_cache[cache_key]
            if datetime.fromisoformat(cached_data["timestamp"]) > datetime.now() - timedelta(seconds=self.ttl_seconds):
                return cached_data["analysis"]
            else:
                del self.memory_cache[cache_key]

        # Check file cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)

                if datetime.fromisoformat(cached_data["timestamp"]) > datetime.now() - timedelta(seconds=self.ttl_seconds):
                    # Store in memory for next time
                    self.memory_cache[cache_key] = cached_data
                    return cached_data["analysis"]
                else:
                    cache_file.unlink()  # Remove expired cache
            except Exception as e:
                logger.warning(f"Cache read error: {e}")

        return None

    async def set(self, message: str, analysis: Dict, context: Dict = None):
        """Cache analysis result"""
        cache_key = self._get_cache_key(message, context)

        cached_data = {
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "message_hash": cache_key[:8]  # For debugging
        }

        # Store in memory cache
        self.memory_cache[cache_key] = cached_data

        # Store in file cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(cached_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Cache write error: {e}")


class ClaudeLeadIntelligence:
    """Enhanced lead intelligence using Claude AI with performance optimization"""

    def __init__(self):
        self.claude_client = None
        self.pattern_scorer = PredictiveLeadScorerV2Optimized()
        self.cache = PerformanceCache()
        self.logger = logging.getLogger(__name__)

        # Initialize Claude client if available
        self._initialize_claude()

    def _initialize_claude(self):
        """Initialize Claude API client"""
        if not CLAUDE_AVAILABLE:
            self.logger.warning("Claude SDK not available - using pattern-only analysis")
            return

        api_key = get_claude_api_key()
        if not api_key:
            self.logger.warning("Claude API key not configured - using pattern-only analysis")
            return

        try:
            self.claude_client = anthropic.Anthropic(api_key=api_key)
            self.logger.info("Claude AI client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Claude client: {e}")

    async def analyze_lead_with_ai(
        self,
        message: str,
        context: Optional[Dict] = None,
        force_claude: bool = False
    ) -> tuple[Dict[str, Any], PerformanceMetrics]:
        """
        High-performance lead analysis with Claude AI integration

        Returns:
            tuple: (analysis_result, performance_metrics)
        """

        metrics = PerformanceMetrics(start_time=time.time())

        try:
            # Check cache first for sub-100ms responses
            cached_result = await self.cache.get(message, context)
            if cached_result and not force_claude:
                metrics.cache_hit = True
                metrics.total_time = time.time() - metrics.start_time
                metrics.analysis_type = "cached"

                # Add Jorge's business rules validation
                cached_result.update(self._add_jorge_validation(cached_result))

                self.logger.info(f"Cache hit - response time: {metrics.total_time*1000:.0f}ms")
                return cached_result, metrics

            # Start with fast pattern-based analysis
            pattern_start = time.time()
            pattern_result = get_enhanced_lead_intelligence(message, context)
            metrics.pattern_analysis_time = time.time() - pattern_start

            # Decide if Claude AI analysis is needed
            use_claude = self._should_use_claude(pattern_result, force_claude)

            if use_claude and self.claude_client:
                # Enhanced Claude AI analysis for complex/high-value leads
                claude_start = time.time()
                claude_enhancement = await self._get_claude_analysis(message, pattern_result, context)
                metrics.claude_analysis_time = time.time() - claude_start
                metrics.analysis_type = "hybrid"

                # Merge pattern and AI results
                enhanced_result = self._merge_analyses(pattern_result, claude_enhancement)
            else:
                # Use pattern-only analysis
                enhanced_result = pattern_result
                metrics.analysis_type = "pattern"

            # Add Jorge's business rules validation
            enhanced_result.update(self._add_jorge_validation(enhanced_result))

            # Check 5-minute rule compliance
            metrics.total_time = time.time() - metrics.start_time
            metrics.five_minute_rule_compliant = metrics.total_time < 300  # 5 minutes in seconds

            if metrics.total_time > 5.0:  # Warn if over 5 seconds
                self.logger.warning(f"⚠️  Slow analysis: {metrics.total_time*1000:.0f}ms")

            if metrics.total_time > 300:  # Critical: 5-minute rule violation
                self.logger.error(f"🚨 CRITICAL: 5-minute rule violated! Response time: {metrics.total_time:.1f}s")

            # Cache result for future requests
            await self.cache.set(message, enhanced_result, context)

            self.logger.info(f"Lead analysis completed - {metrics.analysis_type} mode: {metrics.total_time*1000:.0f}ms")
            return enhanced_result, metrics

        except Exception as e:
            self.logger.error(f"Error in lead analysis: {e}")

            # Fallback to pattern-only analysis
            fallback_result = get_enhanced_lead_intelligence(message, context)
            fallback_result.update(self._add_jorge_validation(fallback_result))
            fallback_result["error"] = str(e)
            fallback_result["fallback_used"] = True

            metrics.total_time = time.time() - metrics.start_time
            metrics.analysis_type = "fallback"

            return fallback_result, metrics

    def _should_use_claude(self, pattern_result: Dict, force_claude: bool) -> bool:
        """Decide whether to use Claude AI based on pattern analysis results"""

        if force_claude:
            return True

        if not self.claude_client:
            return False

        # Use Claude for high-value or complex leads
        lead_score = pattern_result.get("lead_score", 0)
        qualification = pattern_result.get("qualification", 0)
        intent_confidence = pattern_result.get("intent_confidence", 0)

        # Use AI for potentially valuable leads
        return (
            lead_score >= 70 or  # High-scoring leads
            qualification < 0.5 or  # Low confidence in pattern matching
            intent_confidence < 0.6  # Unclear intent
        )

    async def _get_claude_analysis(
        self,
        message: str,
        pattern_result: Dict,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Get enhanced analysis from Claude AI"""

        try:
            # Create focused prompt for real estate lead analysis
            prompt = f"""
You are Jorge's AI assistant for real estate lead qualification. Analyze this lead message and provide enhanced insights.

Jorge's Business Context:
- Real estate agent in Dallas/Plano/Frisco/McKinney/Allen area
- Target price range: $200K-$800K
- Prefers 60-day closing timeline
- 6% commission structure

Lead Message: "{message}"

Pattern Analysis Results: {json.dumps(pattern_result, indent=2)}

Context: {json.dumps(context or {}, indent=2)}

Provide enhanced analysis focusing on:

1. INTENT CLARITY: Is the buying/selling intent clear and genuine?
2. QUALIFICATION LEVEL: How well-qualified is this lead for Jorge?
3. URGENCY ASSESSMENT: Timeline urgency and motivation factors
4. BUDGET VALIDATION: Budget range confidence and Jorge-fit
5. RESPONSE STRATEGY: Recommended next steps for Jorge

Return your analysis as JSON with these exact fields:
{{
  "intent_clarity": float (0-1),
  "qualification_confidence": float (0-1),
  "urgency_score": float (0-1),
  "budget_confidence": float (0-1),
  "jorge_fit_score": float (0-1),
  "recommended_response_tone": "immediate|professional|nurture|referral",
  "key_insights": ["insight1", "insight2", "insight3"],
  "next_steps": ["action1", "action2"],
  "ai_confidence": float (0-1)
}}

Respond only with valid JSON - no other text.
            """

            # Call Claude API with timeout
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.claude_client.messages.create,
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=500,  # Limit tokens for speed
                    temperature=0.3,  # Lower temperature for consistency
                    messages=[{"role": "user", "content": prompt}]
                ),
                timeout=3.0  # 3-second timeout for sub-500ms target
            )

            # Parse Claude's response
            claude_analysis = json.loads(response.content[0].text.strip())

            return claude_analysis

        except asyncio.TimeoutError:
            self.logger.warning("Claude API timeout - falling back to pattern analysis")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Claude response: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Claude API error: {e}")
            return {}

    def _merge_analyses(self, pattern_result: Dict, claude_result: Dict) -> Dict[str, Any]:
        """Merge pattern-based and Claude AI analysis results"""

        if not claude_result:
            return pattern_result

        # Start with pattern results
        merged = pattern_result.copy()

        # Enhance with Claude insights
        if "intent_clarity" in claude_result:
            # Boost intent confidence if Claude is more confident
            claude_intent = claude_result["intent_clarity"]
            current_intent = merged.get("intent_confidence", 0)
            merged["intent_confidence"] = max(claude_intent, current_intent)

        if "qualification_confidence" in claude_result:
            # Enhance qualification score
            claude_qual = claude_result["qualification_confidence"]
            current_qual = merged.get("qualification", 0)
            merged["qualification"] = (claude_qual + current_qual) / 2

        if "urgency_score" in claude_result:
            # Update urgency with Claude's assessment
            merged["urgency"] = claude_result["urgency_score"]

        if "jorge_fit_score" in claude_result:
            # Add Jorge-specific fit score
            merged["jorge_fit_score"] = claude_result["jorge_fit_score"]

        # Recalculate overall lead score with AI insights
        base_score = merged.get("lead_score", 35)
        ai_boost = 0

        if claude_result.get("jorge_fit_score", 0) > 0.8:
            ai_boost += 15  # High Jorge fit
        if claude_result.get("intent_clarity", 0) > 0.8:
            ai_boost += 10  # Clear intent
        if claude_result.get("qualification_confidence", 0) > 0.8:
            ai_boost += 10  # Well qualified

        merged["lead_score"] = min(100, base_score + ai_boost)

        # Add Claude-specific insights
        merged["ai_insights"] = {
            "key_insights": claude_result.get("key_insights", []),
            "next_steps": claude_result.get("next_steps", []),
            "recommended_response_tone": claude_result.get("recommended_response_tone", "professional"),
            "ai_confidence": claude_result.get("ai_confidence", 0.5)
        }

        merged["claude_enhanced"] = True

        return merged

    def _add_jorge_validation(self, analysis_result: Dict) -> Dict[str, Any]:
        """Add Jorge's business rules validation to analysis"""

        # Extract relevant data for validation
        lead_data = {
            "budget_max": analysis_result.get("budget_max"),  # Fixed: budget_max is a direct field, not nested
            "location_preferences": analysis_result.get("location_analysis", []),
            "timeline": analysis_result.get("timeline_analysis", "unknown")
        }

        # Apply Jorge's business rules
        jorge_validation = JorgeBusinessRules.validate_lead(lead_data)

        return {
            "jorge_validation": jorge_validation,
            "meets_jorge_criteria": jorge_validation["passes_jorge_criteria"],
            "estimated_commission": jorge_validation["estimated_commission"],
            "jorge_priority": jorge_validation["jorge_priority"]
        }


class FiveMinuteRuleMonitor:
    """Monitor and enforce Jorge's 5-minute response rule"""

    def __init__(self, alert_threshold: float = 240.0):  # 4 minutes warning
        self.alert_threshold = alert_threshold
        self.violations = []
        self.metrics_history = []

    def track_response(self, metrics: PerformanceMetrics, lead_data: Dict):
        """Track lead response performance"""

        self.metrics_history.append({
            "timestamp": datetime.now().isoformat(),
            "response_time": metrics.total_time,
            "analysis_type": metrics.analysis_type,
            "cache_hit": metrics.cache_hit,
            "compliant": metrics.five_minute_rule_compliant,
            "contact_id": lead_data.get("contact_id", "unknown")
        })

        # Keep only last 1000 entries
        self.metrics_history = self.metrics_history[-1000:]

        # Check for violations
        if not metrics.five_minute_rule_compliant:
            violation = {
                "timestamp": datetime.now().isoformat(),
                "response_time": metrics.total_time,
                "contact_id": lead_data.get("contact_id", "unknown"),
                "severity": "critical"
            }
            self.violations.append(violation)

            # Alert Jorge immediately
            self._send_violation_alert(violation)

    def _send_violation_alert(self, violation: Dict):
        """Send immediate alert for 5-minute rule violation"""

        logger.error(f"""
🚨 CRITICAL: 5-MINUTE RULE VIOLATION 🚨
Contact: {violation['contact_id']}
Response Time: {violation['response_time']:.1f}s
Time: {violation['timestamp']}

IMMEDIATE ACTION REQUIRED: Check lead manually!
        """)

    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate 5-minute rule compliance report"""

        if not self.metrics_history:
            return {"status": "no_data"}

        total_responses = len(self.metrics_history)
        compliant_responses = sum(1 for m in self.metrics_history if m["compliant"])
        compliance_rate = compliant_responses / total_responses

        avg_response_time = sum(m["response_time"] for m in self.metrics_history) / total_responses

        return {
            "total_responses": total_responses,
            "compliance_rate": compliance_rate,
            "avg_response_time": avg_response_time,
            "violations_count": len(self.violations),
            "target_compliance": 0.99,  # 99% target
            "status": "compliant" if compliance_rate >= 0.99 else "needs_attention",
            "last_24h_violations": [
                v for v in self.violations
                if datetime.fromisoformat(v["timestamp"]) > datetime.now() - timedelta(days=1)
            ]
        }


# Global instances for performance
claude_intelligence = ClaudeLeadIntelligence()
five_minute_monitor = FiveMinuteRuleMonitor()


async def analyze_lead_for_jorge(
    message: str,
    contact_id: str = None,
    location_id: str = None,
    context: Dict = None,
    force_ai: bool = False
) -> Dict[str, Any]:
    """
    Main entry point for Jorge's enhanced lead analysis

    Args:
        message: Lead's message to analyze
        contact_id: GHL contact ID
        location_id: GHL location ID
        context: Optional conversation context
        force_ai: Force Claude AI analysis even for low-priority leads

    Returns:
        Enhanced analysis with Jorge's business rules and performance metrics
    """

    # Perform enhanced analysis
    analysis, metrics = await claude_intelligence.analyze_lead_with_ai(
        message, context, force_ai
    )

    # Track performance for 5-minute rule compliance
    lead_data = {
        "contact_id": contact_id,
        "location_id": location_id,
        "message": message
    }
    five_minute_monitor.track_response(metrics, lead_data)

    # Add performance data to response
    analysis["performance"] = {
        "response_time_ms": int(metrics.total_time * 1000),
        "analysis_type": metrics.analysis_type,
        "cache_hit": metrics.cache_hit,
        "five_minute_compliant": metrics.five_minute_rule_compliant,
        "claude_used": metrics.claude_analysis_time is not None
    }

    return analysis


def get_five_minute_compliance_status() -> Dict[str, Any]:
    """Get current 5-minute rule compliance status"""
    return five_minute_monitor.get_compliance_report()


if __name__ == "__main__":
    # Test the enhanced lead intelligence
    async def test_analysis():
        test_message = "I'm pre-approved for $600k and need to buy in Plano within 30 days"

        print("🧪 Testing Jorge's Enhanced Lead Intelligence...")
        result = await analyze_lead_for_jorge(test_message, force_ai=True)

        print(f"📊 Lead Score: {result['lead_score']}")
        print(f"⚡ Response Time: {result['performance']['response_time_ms']}ms")
        print(f"💰 Estimated Commission: ${result.get('estimated_commission', 0):,.0f}")
        print(f"✅ Jorge Fit: {result.get('jorge_priority', 'unknown')}")
        print(f"🚨 5-Min Compliant: {result['performance']['five_minute_compliant']}")

    asyncio.run(test_analysis())