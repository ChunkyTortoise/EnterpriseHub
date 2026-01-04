"""
Advanced Analytics Engine (Agent C3)

Provides comprehensive metrics collection for:
- Lead-to-appointment conversion tracking
- Response time metrics
- SMS compliance monitoring
- Topic/keyword distribution analysis
- A/B testing framework integration

Performance target: <50ms overhead per conversation
"""
import time
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict
import statistics

from ghl_utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConversationMetrics:
    """Metrics captured for a single conversation event."""
    contact_id: str
    location_id: str
    timestamp: str

    # Conversion metrics
    lead_score: int
    previous_score: int
    score_delta: int
    classification: str  # "cold", "warm", "hot"
    appointment_scheduled: bool

    # Timing metrics
    response_time_ms: float
    message_count: int
    conversation_duration_seconds: float

    # Content metrics
    message_length: int
    question_count: int
    keywords_detected: List[str]
    topics: List[str]

    # Compliance metrics
    sms_length: int
    sms_compliant: bool
    tone_score: float  # 0-1: professional and direct

    # Metadata
    is_returning_lead: bool
    pathway: Optional[str] = None  # "wholesale" or "listing"
    experiment_id: Optional[str] = None
    variant: Optional[str] = None


@dataclass
class ConversionFunnel:
    """Conversion funnel metrics."""
    cold_leads: int = 0
    warm_leads: int = 0
    hot_leads: int = 0
    appointments_scheduled: int = 0

    # Conversion rates
    cold_to_warm_rate: float = 0.0
    warm_to_hot_rate: float = 0.0
    hot_to_appointment_rate: float = 0.0
    overall_conversion_rate: float = 0.0

    # Timing
    avg_time_to_hot: float = 0.0
    avg_messages_to_hot: float = 0.0


class MetricsCollector:
    """
    Collects and aggregates conversation metrics.

    Designed for minimal performance impact (<50ms per operation).
    """

    def __init__(self, storage_dir: str = "data/metrics"):
        """Initialize metrics collector."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._buffer: List[ConversationMetrics] = []
        self._buffer_size = 100  # Flush to disk every 100 metrics
        logger.info(f"Metrics collector initialized at {self.storage_dir}")

    def _get_metrics_file(self, location_id: str, date_str: Optional[str] = None) -> Path:
        """Get metrics file path for a location and date."""
        if not date_str:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")

        location_dir = self.storage_dir / location_id
        location_dir.mkdir(parents=True, exist_ok=True)

        return location_dir / f"metrics_{date_str}.jsonl"

    async def record_conversation_event(
        self,
        contact_id: str,
        location_id: str,
        lead_score: int,
        previous_score: int,
        message: str,
        response: str,
        response_time_ms: float,
        context: Dict[str, Any],
        appointment_scheduled: bool = False,
        experiment_data: Optional[Dict[str, str]] = None
    ) -> ConversationMetrics:
        """
        Record a conversation event with comprehensive metrics.

        Args:
            contact_id: Contact identifier
            location_id: Location identifier
            lead_score: Current lead score
            previous_score: Previous lead score
            message: User message
            response: AI response
            response_time_ms: Time to generate response (milliseconds)
            context: Conversation context
            appointment_scheduled: Whether appointment was scheduled
            experiment_data: Optional A/B test data {"experiment_id": "", "variant": ""}

        Returns:
            ConversationMetrics object
        """
        start_time = time.time()

        # Calculate classification
        if lead_score >= 70:
            classification = "hot"
        elif lead_score >= 40:
            classification = "warm"
        else:
            classification = "cold"

        # Analyze content
        keywords = self._extract_keywords(message)
        topics = self._classify_topics(message)
        question_count = message.count("?")

        # Check SMS compliance
        sms_compliant = len(response) <= 160
        tone_score = self._analyze_tone(response)

        # Calculate conversation duration
        created_at = context.get("created_at")
        if created_at:
            created_dt = datetime.fromisoformat(created_at) if isinstance(created_at, str) else created_at
            duration = (datetime.utcnow() - created_dt).total_seconds()
        else:
            duration = 0.0

        # Build metrics object
        metrics = ConversationMetrics(
            contact_id=contact_id,
            location_id=location_id,
            timestamp=datetime.utcnow().isoformat(),
            lead_score=lead_score,
            previous_score=previous_score,
            score_delta=lead_score - previous_score,
            classification=classification,
            appointment_scheduled=appointment_scheduled,
            response_time_ms=response_time_ms,
            message_count=len(context.get("conversation_history", [])) + 1,
            conversation_duration_seconds=duration,
            message_length=len(message),
            question_count=question_count,
            keywords_detected=keywords,
            topics=topics,
            sms_length=len(response),
            sms_compliant=sms_compliant,
            tone_score=tone_score,
            is_returning_lead=context.get("is_returning_lead", False),
            pathway=context.get("extracted_preferences", {}).get("pathway"),
            experiment_id=experiment_data.get("experiment_id") if experiment_data else None,
            variant=experiment_data.get("variant") if experiment_data else None
        )

        # Add to buffer
        self._buffer.append(metrics)

        # Async flush if buffer is full
        if len(self._buffer) >= self._buffer_size:
            await self._flush_buffer(location_id)

        # Log performance
        collection_time_ms = (time.time() - start_time) * 1000
        if collection_time_ms > 50:
            logger.warning(f"Metrics collection took {collection_time_ms:.2f}ms (target: <50ms)")

        return metrics

    async def _flush_buffer(self, location_id: str):
        """Flush metrics buffer to disk."""
        if not self._buffer:
            return

        metrics_file = self._get_metrics_file(location_id)

        try:
            with open(metrics_file, "a") as f:
                for metric in self._buffer:
                    f.write(json.dumps(asdict(metric)) + "\n")

            logger.debug(f"Flushed {len(self._buffer)} metrics to {metrics_file}")
            self._buffer.clear()
        except Exception as e:
            logger.error(f"Failed to flush metrics buffer: {e}")

    def _extract_keywords(self, message: str) -> List[str]:
        """Extract key real estate keywords from message."""
        keywords = []
        message_lower = message.lower()

        # Budget-related
        if any(word in message_lower for word in ["budget", "price", "afford", "$"]):
            keywords.append("budget")

        # Location
        if any(word in message_lower for word in ["location", "area", "neighborhood", "city"]):
            keywords.append("location")

        # Timeline
        if any(word in message_lower for word in ["when", "timeline", "soon", "asap", "urgent"]):
            keywords.append("timeline")

        # Property type
        if any(word in message_lower for word in ["bedroom", "bath", "sqft", "size"]):
            keywords.append("property_specs")

        # Financing
        if any(word in message_lower for word in ["mortgage", "financing", "pre-approved", "cash"]):
            keywords.append("financing")

        # Appointment
        if any(word in message_lower for word in ["appointment", "viewing", "tour", "schedule", "meet"]):
            keywords.append("appointment")

        return keywords

    def _classify_topics(self, message: str) -> List[str]:
        """Classify message into topic categories."""
        topics = []
        message_lower = message.lower()

        # Seller topics
        if any(word in message_lower for word in ["sell", "selling", "list", "listing"]):
            topics.append("seller")

        # Buyer topics
        if any(word in message_lower for word in ["buy", "buying", "purchase", "looking for"]):
            topics.append("buyer")

        # Wholesale
        if any(word in message_lower for word in ["as-is", "fast sale", "cash offer", "quick"]):
            topics.append("wholesale")

        # Investment
        if any(word in message_lower for word in ["investment", "rental", "flip", "roi"]):
            topics.append("investment")

        return topics

    def _analyze_tone(self, response: str) -> float:
        """
        Analyze tone for professional and direct communication.

        Returns score 0-1 (1 = perfect tone).
        """
        score = 1.0
        response_lower = response.lower()

        # Penalize overly casual language
        casual_words = ["lol", "haha", "omg", "btw", "idk"]
        for word in casual_words:
            if word in response_lower:
                score -= 0.1

        # Penalize excessive punctuation
        if response.count("!") > 2 or response.count("?") > 2:
            score -= 0.05

        # Reward professional markers
        professional_markers = ["would", "could", "please", "thank you"]
        for marker in professional_markers:
            if marker in response_lower:
                score += 0.05

        return max(0.0, min(1.0, score))

    async def get_metrics(
        self,
        location_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[ConversationMetrics]:
        """
        Retrieve metrics for a location within date range.

        Args:
            location_id: Location identifier
            start_date: Start date (YYYY-MM-DD), defaults to today
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            List of ConversationMetrics
        """
        # Ensure buffer is flushed
        await self._flush_buffer(location_id)

        if not start_date:
            start_date = datetime.utcnow().strftime("%Y-%m-%d")
        if not end_date:
            end_date = start_date

        metrics = []

        # Parse dates
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        # Iterate through date range
        current_dt = start_dt
        while current_dt <= end_dt:
            date_str = current_dt.strftime("%Y-%m-%d")
            metrics_file = self._get_metrics_file(location_id, date_str)

            if metrics_file.exists():
                try:
                    with open(metrics_file, "r") as f:
                        for line in f:
                            if line.strip():
                                data = json.loads(line)
                                metrics.append(ConversationMetrics(**data))
                except Exception as e:
                    logger.error(f"Failed to read metrics from {metrics_file}: {e}")

            current_dt += timedelta(days=1)

        return metrics


class ConversionTracker:
    """Tracks conversion funnel metrics."""

    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize conversion tracker."""
        self.metrics_collector = metrics_collector

    async def calculate_funnel(
        self,
        location_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> ConversionFunnel:
        """
        Calculate conversion funnel metrics.

        Args:
            location_id: Location identifier
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            ConversionFunnel with calculated metrics
        """
        metrics = await self.metrics_collector.get_metrics(location_id, start_date, end_date)

        if not metrics:
            return ConversionFunnel()

        # Track unique contacts at each stage
        contacts_by_stage: Dict[str, set] = {
            "cold": set(),
            "warm": set(),
            "hot": set(),
            "appointment": set()
        }

        # Track progression times
        contact_progression: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "first_seen": None,
            "became_hot": None,
            "message_count_to_hot": 0
        })

        for metric in metrics:
            contact_id = metric.contact_id
            classification = metric.classification

            # Track first seen
            if contact_progression[contact_id]["first_seen"] is None:
                contact_progression[contact_id]["first_seen"] = metric.timestamp

            # Track stage
            contacts_by_stage[classification].add(contact_id)

            if metric.appointment_scheduled:
                contacts_by_stage["appointment"].add(contact_id)

            # Track when they became hot
            if classification == "hot" and contact_progression[contact_id]["became_hot"] is None:
                contact_progression[contact_id]["became_hot"] = metric.timestamp
                contact_progression[contact_id]["message_count_to_hot"] = metric.message_count

        # Calculate counts
        funnel = ConversionFunnel(
            cold_leads=len(contacts_by_stage["cold"]),
            warm_leads=len(contacts_by_stage["warm"]),
            hot_leads=len(contacts_by_stage["hot"]),
            appointments_scheduled=len(contacts_by_stage["appointment"])
        )

        # Calculate conversion rates
        total_leads = len(set.union(*contacts_by_stage.values()))

        if total_leads > 0:
            funnel.cold_to_warm_rate = len(contacts_by_stage["warm"]) / total_leads
            funnel.warm_to_hot_rate = len(contacts_by_stage["hot"]) / max(len(contacts_by_stage["warm"]), 1)
            funnel.hot_to_appointment_rate = len(contacts_by_stage["appointment"]) / max(len(contacts_by_stage["hot"]), 1)
            funnel.overall_conversion_rate = len(contacts_by_stage["appointment"]) / total_leads

        # Calculate average time and messages to hot
        times_to_hot = []
        messages_to_hot = []

        for contact_id, data in contact_progression.items():
            if data["became_hot"]:
                first_seen = datetime.fromisoformat(data["first_seen"])
                became_hot = datetime.fromisoformat(data["became_hot"])
                time_diff = (became_hot - first_seen).total_seconds()
                times_to_hot.append(time_diff)
                messages_to_hot.append(data["message_count_to_hot"])

        if times_to_hot:
            funnel.avg_time_to_hot = statistics.mean(times_to_hot)
            funnel.avg_messages_to_hot = statistics.mean(messages_to_hot)

        return funnel


class ResponseTimeAnalyzer:
    """Analyzes response time metrics."""

    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize response time analyzer."""
        self.metrics_collector = metrics_collector

    async def analyze_response_times(
        self,
        location_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze response time patterns.

        Returns:
            {
                "avg_response_time_ms": float,
                "median_response_time_ms": float,
                "p95_response_time_ms": float,
                "p99_response_time_ms": float,
                "by_classification": {
                    "cold": {...},
                    "warm": {...},
                    "hot": {...}
                }
            }
        """
        metrics = await self.metrics_collector.get_metrics(location_id, start_date, end_date)

        if not metrics:
            return {"error": "No metrics found"}

        # Collect response times
        all_times = [m.response_time_ms for m in metrics]
        times_by_classification = defaultdict(list)

        for metric in metrics:
            times_by_classification[metric.classification].append(metric.response_time_ms)

        # Calculate overall statistics
        result = {
            "avg_response_time_ms": statistics.mean(all_times),
            "median_response_time_ms": statistics.median(all_times),
            "p95_response_time_ms": self._percentile(all_times, 0.95),
            "p99_response_time_ms": self._percentile(all_times, 0.99),
            "by_classification": {}
        }

        # Calculate by classification
        for classification, times in times_by_classification.items():
            result["by_classification"][classification] = {
                "avg": statistics.mean(times),
                "median": statistics.median(times),
                "p95": self._percentile(times, 0.95)
            }

        return result

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile."""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]


class ComplianceMonitor:
    """Monitors SMS compliance metrics."""

    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize compliance monitor."""
        self.metrics_collector = metrics_collector

    async def check_compliance(
        self,
        location_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check SMS compliance metrics.

        Returns:
            {
                "total_messages": int,
                "compliant_messages": int,
                "compliance_rate": float,
                "avg_message_length": float,
                "avg_tone_score": float,
                "violations": List[Dict]
            }
        """
        metrics = await self.metrics_collector.get_metrics(location_id, start_date, end_date)

        if not metrics:
            return {"error": "No metrics found"}

        total = len(metrics)
        compliant = sum(1 for m in metrics if m.sms_compliant)

        violations = []
        for metric in metrics:
            if not metric.sms_compliant:
                violations.append({
                    "contact_id": metric.contact_id,
                    "timestamp": metric.timestamp,
                    "length": metric.sms_length,
                    "exceeded_by": metric.sms_length - 160
                })

        message_lengths = [m.sms_length for m in metrics]
        tone_scores = [m.tone_score for m in metrics]

        return {
            "total_messages": total,
            "compliant_messages": compliant,
            "compliance_rate": compliant / total if total > 0 else 0.0,
            "avg_message_length": statistics.mean(message_lengths),
            "avg_tone_score": statistics.mean(tone_scores),
            "violations": violations[:10]  # Return first 10 violations
        }


class TopicDistributionAnalyzer:
    """Analyzes topic and keyword distribution."""

    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize topic analyzer."""
        self.metrics_collector = metrics_collector

    async def analyze_topics(
        self,
        location_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze topic and keyword distribution.

        Returns:
            {
                "keywords": {
                    "budget": {"count": int, "percentage": float},
                    ...
                },
                "topics": {
                    "buyer": {"count": int, "percentage": float},
                    ...
                },
                "pathways": {
                    "wholesale": int,
                    "listing": int
                }
            }
        """
        metrics = await self.metrics_collector.get_metrics(location_id, start_date, end_date)

        if not metrics:
            return {"error": "No metrics found"}

        # Count keywords
        keyword_counts = defaultdict(int)
        topic_counts = defaultdict(int)
        pathway_counts = defaultdict(int)

        total = len(metrics)

        for metric in metrics:
            for keyword in metric.keywords_detected:
                keyword_counts[keyword] += 1

            for topic in metric.topics:
                topic_counts[topic] += 1

            if metric.pathway:
                pathway_counts[metric.pathway] += 1

        # Calculate percentages
        keywords = {
            keyword: {
                "count": count,
                "percentage": (count / total) * 100
            }
            for keyword, count in keyword_counts.items()
        }

        topics = {
            topic: {
                "count": count,
                "percentage": (count / total) * 100
            }
            for topic, count in topic_counts.items()
        }

        return {
            "keywords": keywords,
            "topics": topics,
            "pathways": dict(pathway_counts)
        }


class AnalyticsEngine:
    """
    Main analytics engine integrating all metrics collectors.

    Usage:
        engine = AnalyticsEngine()

        # Record event
        await engine.record_event(
            contact_id="c123",
            location_id="loc456",
            lead_score=75,
            previous_score=50,
            message="I'm looking for a 3-bed home",
            response="Great! What's your budget?",
            response_time_ms=350.5,
            context={...}
        )

        # Get conversion funnel
        funnel = await engine.get_conversion_funnel("loc456")

        # Check compliance
        compliance = await engine.check_compliance("loc456")
    """

    def __init__(self, storage_dir: str = "data/metrics"):
        """Initialize analytics engine."""
        self.metrics_collector = MetricsCollector(storage_dir)
        self.conversion_tracker = ConversionTracker(self.metrics_collector)
        self.response_time_analyzer = ResponseTimeAnalyzer(self.metrics_collector)
        self.compliance_monitor = ComplianceMonitor(self.metrics_collector)
        self.topic_analyzer = TopicDistributionAnalyzer(self.metrics_collector)

        logger.info("Analytics engine initialized")

    async def record_event(
        self,
        contact_id: str,
        location_id: str,
        lead_score: int,
        previous_score: int,
        message: str,
        response: str,
        response_time_ms: float,
        context: Dict[str, Any],
        appointment_scheduled: bool = False,
        experiment_data: Optional[Dict[str, str]] = None
    ) -> ConversationMetrics:
        """Record a conversation event."""
        return await self.metrics_collector.record_conversation_event(
            contact_id=contact_id,
            location_id=location_id,
            lead_score=lead_score,
            previous_score=previous_score,
            message=message,
            response=response,
            response_time_ms=response_time_ms,
            context=context,
            appointment_scheduled=appointment_scheduled,
            experiment_data=experiment_data
        )

    async def get_conversion_funnel(
        self,
        location_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> ConversionFunnel:
        """Get conversion funnel metrics."""
        return await self.conversion_tracker.calculate_funnel(location_id, start_date, end_date)

    async def analyze_response_times(
        self,
        location_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze response times."""
        return await self.response_time_analyzer.analyze_response_times(location_id, start_date, end_date)

    async def check_compliance(
        self,
        location_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check SMS compliance."""
        return await self.compliance_monitor.check_compliance(location_id, start_date, end_date)

    async def analyze_topics(
        self,
        location_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze topic distribution."""
        return await self.topic_analyzer.analyze_topics(location_id, start_date, end_date)

    async def get_comprehensive_report(
        self,
        location_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics report.

        Returns all metrics in one call.
        """
        funnel, response_times, compliance, topics = await asyncio.gather(
            self.get_conversion_funnel(location_id, start_date, end_date),
            self.analyze_response_times(location_id, start_date, end_date),
            self.check_compliance(location_id, start_date, end_date),
            self.analyze_topics(location_id, start_date, end_date)
        )

        return {
            "location_id": location_id,
            "date_range": {
                "start": start_date or datetime.utcnow().strftime("%Y-%m-%d"),
                "end": end_date or datetime.utcnow().strftime("%Y-%m-%d")
            },
            "conversion_funnel": asdict(funnel),
            "response_times": response_times,
            "compliance": compliance,
            "topics": topics
        }


# Export main class
__all__ = ["AnalyticsEngine", "ConversationMetrics", "ConversionFunnel"]
