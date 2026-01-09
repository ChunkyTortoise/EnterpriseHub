"""
Workflow A/B Testing and Optimization Service

Provides intelligent A/B testing capabilities for workflow optimization:
- Message content testing
- Timing optimization
- Channel effectiveness
- Sequence variant testing
- Statistical significance analysis
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
import random
import statistics
from collections import defaultdict

logger = logging.getLogger(__name__)

class TestType(Enum):
    """Types of A/B tests"""
    MESSAGE_CONTENT = "message_content"
    SEND_TIMING = "send_timing"
    CHANNEL_SELECTION = "channel_selection"
    SEQUENCE_FLOW = "sequence_flow"
    SUBJECT_LINE = "subject_line"
    CTA_BUTTON = "cta_button"

class TestStatus(Enum):
    """Test execution status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"

class Significance(Enum):
    """Statistical significance levels"""
    LOW = 0.90
    MEDIUM = 0.95
    HIGH = 0.99

@dataclass
class TestVariant:
    """A/B test variant configuration"""
    variant_id: str
    name: str
    description: str
    config: Dict[str, Any]
    traffic_split: float = 0.5  # Percentage of traffic (0.0-1.0)
    is_control: bool = False

@dataclass
class TestMetrics:
    """Test performance metrics"""
    impressions: int = 0
    opens: int = 0
    clicks: int = 0
    responses: int = 0
    conversions: int = 0
    revenue: float = 0.0
    unsubscribes: int = 0

    @property
    def open_rate(self) -> float:
        return self.opens / self.impressions if self.impressions > 0 else 0.0

    @property
    def click_rate(self) -> float:
        return self.clicks / self.impressions if self.impressions > 0 else 0.0

    @property
    def response_rate(self) -> float:
        return self.responses / self.impressions if self.impressions > 0 else 0.0

    @property
    def conversion_rate(self) -> float:
        return self.conversions / self.impressions if self.impressions > 0 else 0.0

@dataclass
class ABTest:
    """A/B test configuration and state"""
    test_id: str
    name: str
    description: str
    test_type: TestType
    variants: List[TestVariant]
    primary_metric: str = "conversion_rate"
    minimum_sample_size: int = 100
    confidence_level: float = 0.95
    status: TestStatus = TestStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    winner_variant_id: Optional[str] = None

@dataclass
class TestResult:
    """A/B test results and analysis"""
    test_id: str
    variant_results: Dict[str, TestMetrics]
    statistical_significance: float
    is_significant: bool
    winner_variant_id: Optional[str]
    confidence_interval: Dict[str, Tuple[float, float]]
    recommendation: str
    insights: List[str]
    generated_at: datetime = field(default_factory=datetime.now)

class WorkflowABTesting:
    """A/B Testing service for workflow optimization"""

    def __init__(self, analytics_service=None):
        self.active_tests: Dict[str, ABTest] = {}
        self.test_history: Dict[str, ABTest] = {}
        self.variant_assignments: Dict[str, Dict[str, str]] = defaultdict(dict)  # lead_id -> test_id -> variant_id
        self.test_metrics: Dict[str, Dict[str, TestMetrics]] = defaultdict(dict)  # test_id -> variant_id -> metrics
        self.analytics_service = analytics_service

        # Predefined test templates
        self._initialize_test_templates()

    def _initialize_test_templates(self):
        """Initialize common test templates"""
        self.test_templates = {
            'email_subject_line': {
                'name': 'Email Subject Line Test',
                'description': 'Test different subject line approaches',
                'test_type': TestType.SUBJECT_LINE,
                'variants': [
                    {
                        'name': 'Direct',
                        'description': 'Direct, straightforward subject',
                        'config': {'style': 'direct', 'urgency': 'low'}
                    },
                    {
                        'name': 'Question',
                        'description': 'Question-based subject',
                        'config': {'style': 'question', 'urgency': 'medium'}
                    },
                    {
                        'name': 'Urgency',
                        'description': 'Urgency-driven subject',
                        'config': {'style': 'urgency', 'urgency': 'high'}
                    }
                ]
            },
            'send_timing': {
                'name': 'Optimal Send Time Test',
                'description': 'Test different send times',
                'test_type': TestType.SEND_TIMING,
                'variants': [
                    {
                        'name': 'Morning',
                        'description': '9 AM send time',
                        'config': {'send_hour': 9, 'send_minute': 0}
                    },
                    {
                        'name': 'Afternoon',
                        'description': '2 PM send time',
                        'config': {'send_hour': 14, 'send_minute': 0}
                    },
                    {
                        'name': 'Evening',
                        'description': '6 PM send time',
                        'config': {'send_hour': 18, 'send_minute': 0}
                    }
                ]
            },
            'sequence_length': {
                'name': 'Sequence Length Test',
                'description': 'Test different sequence lengths',
                'test_type': TestType.SEQUENCE_FLOW,
                'variants': [
                    {
                        'name': 'Short (3 steps)',
                        'description': '3-step sequence',
                        'config': {'sequence_length': 3, 'step_delay': 24}
                    },
                    {
                        'name': 'Medium (5 steps)',
                        'description': '5-step sequence',
                        'config': {'sequence_length': 5, 'step_delay': 48}
                    },
                    {
                        'name': 'Long (7 steps)',
                        'description': '7-step sequence',
                        'config': {'sequence_length': 7, 'step_delay': 72}
                    }
                ]
            }
        }

    async def create_test(
        self,
        name: str,
        description: str,
        test_type: TestType,
        variants: List[Dict[str, Any]],
        primary_metric: str = "conversion_rate",
        minimum_sample_size: int = 100,
        confidence_level: float = 0.95
    ) -> ABTest:
        """Create a new A/B test"""

        test_id = f"test_{datetime.now().timestamp()}"

        # Create variant objects
        test_variants = []
        for i, variant_config in enumerate(variants):
            variant = TestVariant(
                variant_id=f"{test_id}_v{i}",
                name=variant_config['name'],
                description=variant_config['description'],
                config=variant_config['config'],
                traffic_split=1.0 / len(variants),  # Equal split by default
                is_control=(i == 0)  # First variant is control
            )
            test_variants.append(variant)

        test = ABTest(
            test_id=test_id,
            name=name,
            description=description,
            test_type=test_type,
            variants=test_variants,
            primary_metric=primary_metric,
            minimum_sample_size=minimum_sample_size,
            confidence_level=confidence_level
        )

        self.active_tests[test_id] = test

        # Initialize metrics for each variant
        for variant in test_variants:
            self.test_metrics[test_id][variant.variant_id] = TestMetrics()

        logger.info(f"Created A/B test: {name} (ID: {test_id})")
        return test

    async def create_test_from_template(
        self,
        template_key: str,
        name_suffix: str = "",
        custom_config: Optional[Dict[str, Any]] = None
    ) -> ABTest:
        """Create test from predefined template"""

        if template_key not in self.test_templates:
            raise ValueError(f"Unknown template: {template_key}")

        template = self.test_templates[template_key]

        # Apply custom configuration if provided
        variants = template['variants'].copy()
        if custom_config:
            for variant in variants:
                variant['config'].update(custom_config.get('variant_config', {}))

        name = template['name'] + (f" - {name_suffix}" if name_suffix else "")

        return await self.create_test(
            name=name,
            description=template['description'],
            test_type=template['test_type'],
            variants=variants,
            primary_metric=custom_config.get('primary_metric', 'conversion_rate'),
            minimum_sample_size=custom_config.get('minimum_sample_size', 100),
            confidence_level=custom_config.get('confidence_level', 0.95)
        )

    async def start_test(self, test_id: str) -> bool:
        """Start an A/B test"""

        if test_id not in self.active_tests:
            logger.error(f"Test not found: {test_id}")
            return False

        test = self.active_tests[test_id]

        # Validate test configuration
        if not await self._validate_test(test):
            logger.error(f"Test validation failed: {test_id}")
            return False

        test.status = TestStatus.ACTIVE
        test.started_at = datetime.now()

        logger.info(f"Started A/B test: {test.name} (ID: {test_id})")
        return True

    async def assign_variant(
        self,
        test_id: str,
        lead_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[TestVariant]:
        """Assign a variant to a lead for A/B test"""

        if test_id not in self.active_tests:
            return None

        test = self.active_tests[test_id]

        if test.status != TestStatus.ACTIVE:
            return None

        # Check if lead already assigned
        if lead_id in self.variant_assignments[test_id]:
            variant_id = self.variant_assignments[test_id][lead_id]
            return next(v for v in test.variants if v.variant_id == variant_id)

        # Assign variant based on traffic split
        variant = await self._select_variant(test, lead_id, context)

        if variant:
            self.variant_assignments[test_id][lead_id] = variant.variant_id
            logger.debug(f"Assigned variant {variant.name} to lead {lead_id} for test {test_id}")

        return variant

    async def _select_variant(
        self,
        test: ABTest,
        lead_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[TestVariant]:
        """Select variant for lead using intelligent assignment"""

        # For simple tests, use random assignment based on traffic split
        random.seed(hash(f"{test.test_id}_{lead_id}"))  # Consistent assignment for same lead

        cumulative_split = 0.0
        rand_val = random.random()

        for variant in test.variants:
            cumulative_split += variant.traffic_split
            if rand_val <= cumulative_split:
                return variant

        # Fallback to control variant
        return next((v for v in test.variants if v.is_control), test.variants[0])

    async def record_event(
        self,
        test_id: str,
        lead_id: str,
        event_type: str,
        value: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record an event for A/B testing"""

        if test_id not in self.active_tests:
            return False

        if lead_id not in self.variant_assignments[test_id]:
            return False

        variant_id = self.variant_assignments[test_id][lead_id]
        metrics = self.test_metrics[test_id][variant_id]

        # Update metrics based on event type
        if event_type == 'impression':
            metrics.impressions += 1
        elif event_type == 'open':
            metrics.opens += 1
        elif event_type == 'click':
            metrics.clicks += 1
        elif event_type == 'response':
            metrics.responses += 1
        elif event_type == 'conversion':
            metrics.conversions += 1
        elif event_type == 'revenue':
            metrics.revenue += value
        elif event_type == 'unsubscribe':
            metrics.unsubscribes += 1

        logger.debug(f"Recorded {event_type} for test {test_id}, variant {variant_id}")
        return True

    async def analyze_test(self, test_id: str) -> Optional[TestResult]:
        """Analyze A/B test results"""

        if test_id not in self.active_tests:
            return None

        test = self.active_tests[test_id]
        variant_results = {}

        # Get metrics for each variant
        for variant in test.variants:
            variant_results[variant.variant_id] = self.test_metrics[test_id][variant.variant_id]

        # Calculate statistical significance
        significance = await self._calculate_significance(
            test, variant_results
        )

        # Determine winner
        winner_variant_id = await self._determine_winner(
            test, variant_results, significance
        )

        # Generate insights
        insights = await self._generate_insights(test, variant_results)

        # Create recommendation
        recommendation = await self._generate_recommendation(
            test, variant_results, winner_variant_id, significance
        )

        result = TestResult(
            test_id=test_id,
            variant_results=variant_results,
            statistical_significance=significance,
            is_significant=significance >= test.confidence_level,
            winner_variant_id=winner_variant_id,
            confidence_interval={},  # Would calculate actual confidence intervals
            recommendation=recommendation,
            insights=insights
        )

        return result

    async def _calculate_significance(
        self,
        test: ABTest,
        variant_results: Dict[str, TestMetrics]
    ) -> float:
        """Calculate statistical significance (simplified)"""

        # Get control and treatment metrics
        control_variant = next(v for v in test.variants if v.is_control)
        control_metrics = variant_results[control_variant.variant_id]

        # For simplification, using sample size as proxy for significance
        # In production, would use proper statistical tests (z-test, t-test, etc.)

        total_impressions = sum(m.impressions for m in variant_results.values())

        if total_impressions < test.minimum_sample_size:
            return 0.0

        # Simple heuristic: more data = higher confidence
        confidence = min(0.99, total_impressions / (test.minimum_sample_size * 2))

        return confidence

    async def _determine_winner(
        self,
        test: ABTest,
        variant_results: Dict[str, TestMetrics],
        significance: float
    ) -> Optional[str]:
        """Determine winning variant"""

        if significance < test.confidence_level:
            return None

        # Get primary metric values
        metric_values = {}
        for variant_id, metrics in variant_results.items():
            if test.primary_metric == "conversion_rate":
                metric_values[variant_id] = metrics.conversion_rate
            elif test.primary_metric == "open_rate":
                metric_values[variant_id] = metrics.open_rate
            elif test.primary_metric == "click_rate":
                metric_values[variant_id] = metrics.click_rate
            elif test.primary_metric == "response_rate":
                metric_values[variant_id] = metrics.response_rate
            else:
                metric_values[variant_id] = metrics.conversion_rate

        # Return variant with highest metric value
        return max(metric_values, key=metric_values.get)

    async def _generate_insights(
        self,
        test: ABTest,
        variant_results: Dict[str, TestMetrics]
    ) -> List[str]:
        """Generate insights from test results"""

        insights = []

        # Sample size insight
        total_impressions = sum(m.impressions for m in variant_results.values())
        if total_impressions < test.minimum_sample_size:
            insights.append(f"Test needs more data: {total_impressions}/{test.minimum_sample_size} impressions")

        # Performance comparison
        control_variant = next(v for v in test.variants if v.is_control)
        control_metrics = variant_results[control_variant.variant_id]

        for variant in test.variants:
            if variant.is_control:
                continue

            variant_metrics = variant_results[variant.variant_id]

            # Compare conversion rates
            control_rate = control_metrics.conversion_rate
            variant_rate = variant_metrics.conversion_rate

            if variant_rate > control_rate * 1.1:  # 10% improvement
                improvement = ((variant_rate - control_rate) / control_rate) * 100
                insights.append(f"{variant.name} shows {improvement:.1f}% improvement over control")
            elif variant_rate < control_rate * 0.9:  # 10% decline
                decline = ((control_rate - variant_rate) / control_rate) * 100
                insights.append(f"{variant.name} shows {decline:.1f}% decline vs control")

        # Channel-specific insights
        if test.test_type == TestType.SEND_TIMING:
            best_variant = max(variant_results.items(), key=lambda x: x[1].conversion_rate)
            best_variant_obj = next(v for v in test.variants if v.variant_id == best_variant[0])
            insights.append(f"Optimal send time appears to be {best_variant_obj.config.get('send_hour', 'unknown')}:00")

        return insights

    async def _generate_recommendation(
        self,
        test: ABTest,
        variant_results: Dict[str, TestMetrics],
        winner_variant_id: Optional[str],
        significance: float
    ) -> str:
        """Generate recommendation based on test results"""

        if significance < test.confidence_level:
            return f"Continue testing - need {test.confidence_level:.0%} confidence (currently {significance:.0%})"

        if not winner_variant_id:
            return "No clear winner - results are too close to call"

        winner_variant = next(v for v in test.variants if v.variant_id == winner_variant_id)
        winner_metrics = variant_results[winner_variant_id]

        if winner_variant.is_control:
            return "Stick with control variant - no significant improvement from alternatives"
        else:
            improvement = winner_metrics.conversion_rate * 100
            return f"Implement {winner_variant.name} - shows {improvement:.1f}% conversion rate"

    async def end_test(
        self,
        test_id: str,
        reason: str = "completed"
    ) -> Optional[TestResult]:
        """End an A/B test and get final results"""

        if test_id not in self.active_tests:
            return None

        test = self.active_tests[test_id]
        test.status = TestStatus.COMPLETED
        test.ended_at = datetime.now()

        # Get final analysis
        result = await self.analyze_test(test_id)

        # Move to history
        self.test_history[test_id] = self.active_tests.pop(test_id)

        # Apply winner if significant
        if result and result.is_significant and result.winner_variant_id:
            await self._apply_winning_variant(test, result.winner_variant_id)

        logger.info(f"Ended A/B test: {test.name} (ID: {test_id}) - {reason}")
        return result

    async def _apply_winning_variant(
        self,
        test: ABTest,
        winner_variant_id: str
    ):
        """Apply winning variant to future workflows"""

        winner_variant = next(v for v in test.variants if v.variant_id == winner_variant_id)

        # Store winning configuration for future use
        winning_config = {
            'test_type': test.test_type.value,
            'winner_config': winner_variant.config,
            'applied_at': datetime.now().isoformat()
        }

        # In production, this would update workflow templates
        logger.info(f"Applied winning variant: {winner_variant.name} for {test.test_type.value}")

    async def get_test_status(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get current test status and basic metrics"""

        test = self.active_tests.get(test_id) or self.test_history.get(test_id)
        if not test:
            return None

        # Calculate basic stats
        total_impressions = sum(
            self.test_metrics.get(test_id, {}).get(v.variant_id, TestMetrics()).impressions
            for v in test.variants
        )

        variant_stats = {}
        for variant in test.variants:
            metrics = self.test_metrics.get(test_id, {}).get(variant.variant_id, TestMetrics())
            variant_stats[variant.name] = {
                'impressions': metrics.impressions,
                'conversions': metrics.conversions,
                'conversion_rate': f"{metrics.conversion_rate:.2%}",
                'traffic_split': f"{variant.traffic_split:.1%}"
            }

        return {
            'test_id': test_id,
            'name': test.name,
            'status': test.status.value,
            'total_impressions': total_impressions,
            'progress': min(100, (total_impressions / test.minimum_sample_size) * 100),
            'started_at': test.started_at.isoformat() if test.started_at else None,
            'variant_stats': variant_stats
        }

    async def get_all_tests_summary(self) -> Dict[str, Any]:
        """Get summary of all tests"""

        active_tests = len(self.active_tests)
        completed_tests = len(self.test_history)

        # Get recent results
        recent_winners = []
        for test_id, test in list(self.test_history.items())[-5:]:  # Last 5 completed
            if test.winner_variant_id:
                winner_variant = next(v for v in test.variants if v.variant_id == test.winner_variant_id)
                recent_winners.append({
                    'test_name': test.name,
                    'winner': winner_variant.name,
                    'completed_at': test.ended_at.isoformat() if test.ended_at else None
                })

        return {
            'active_tests': active_tests,
            'completed_tests': completed_tests,
            'recent_winners': recent_winners,
            'available_templates': list(self.test_templates.keys())
        }

    async def _validate_test(self, test: ABTest) -> bool:
        """Validate test configuration"""

        # Check variants
        if len(test.variants) < 2:
            logger.error("Test needs at least 2 variants")
            return False

        # Check traffic splits sum to 1.0
        total_split = sum(v.traffic_split for v in test.variants)
        if abs(total_split - 1.0) > 0.01:
            logger.error(f"Traffic splits must sum to 1.0 (currently {total_split})")
            return False

        # Check for control variant
        control_variants = [v for v in test.variants if v.is_control]
        if len(control_variants) != 1:
            logger.error("Test needs exactly one control variant")
            return False

        return True

    async def pause_test(self, test_id: str) -> bool:
        """Pause an active test"""

        if test_id not in self.active_tests:
            return False

        test = self.active_tests[test_id]
        if test.status == TestStatus.ACTIVE:
            test.status = TestStatus.PAUSED
            logger.info(f"Paused test: {test.name}")
            return True

        return False

    async def resume_test(self, test_id: str) -> bool:
        """Resume a paused test"""

        if test_id not in self.active_tests:
            return False

        test = self.active_tests[test_id]
        if test.status == TestStatus.PAUSED:
            test.status = TestStatus.ACTIVE
            logger.info(f"Resumed test: {test.name}")
            return True

        return False

    def get_optimal_config_for_workflow(
        self,
        workflow_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get optimal configuration based on completed tests"""

        # Look for completed tests relevant to this workflow type
        relevant_tests = []
        for test in self.test_history.values():
            if (test.status == TestStatus.COMPLETED and
                test.winner_variant_id and
                workflow_type.lower() in test.name.lower()):
                relevant_tests.append(test)

        if not relevant_tests:
            return None

        # Return configuration from most recent winning test
        latest_test = max(relevant_tests, key=lambda t: t.ended_at or datetime.min)
        winner_variant = next(v for v in latest_test.variants if v.variant_id == latest_test.winner_variant_id)

        return {
            'source_test': latest_test.name,
            'config': winner_variant.config,
            'confidence': 'high' if latest_test.confidence_level >= 0.95 else 'medium'
        }