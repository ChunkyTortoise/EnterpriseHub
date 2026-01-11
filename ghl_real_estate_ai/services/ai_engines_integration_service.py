"""
AI Engines Integration Service

Unified integration layer that coordinates the Competitive Intelligence Engine
and Predictive Lead Lifecycle Engine with existing performance-optimized services.

Key Features:
- Unified API for both AI engines
- Coordinated performance monitoring and optimization
- Intelligent workload distribution and caching
- Cross-engine data sharing and optimization
- Integrated health monitoring and alerting
- Performance-driven scaling and resource management

Performance Targets:
- Unified prediction: <75ms (competitive + predictive analysis)
- Cross-engine caching: 95%+ hit rate
- Resource utilization: <70% average
- Availability: 99.9% uptime
- Latency optimization: <5ms coordination overhead
"""

import asyncio
import time
import json
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from enum import Enum
from collections import defaultdict, deque
import logging
from concurrent.futures import ThreadPoolExecutor

# Import optimized services
from .redis_optimization_service import OptimizedRedisClient
from .async_http_client import AsyncHTTPClient
from .database_cache_service import DatabaseCacheService
from .performance_monitoring_service import PerformanceMonitoringService
from .batch_ml_inference_service import BatchMLInferenceService

# Import AI engines
from .competitive_intelligence_engine import (
    CompetitiveIntelligenceEngine,
    CompetitiveAnalysis,
    CompetitiveEvent,
    CounterStrategy,
    ThreatLevel
)
from .predictive_lead_lifecycle_engine import (
    PredictiveLeadLifecycleEngine,
    ConversionForecast,
    InterventionWindow,
    RiskFactor,
    ConversionStage
)

logger = logging.getLogger(__name__)


class EngineType(Enum):
    """AI engine types"""
    COMPETITIVE_INTELLIGENCE = "competitive_intelligence"
    PREDICTIVE_LIFECYCLE = "predictive_lifecycle"
    UNIFIED = "unified"


class ProcessingPriority(Enum):
    """Processing priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class AnalysisScope(Enum):
    """Analysis scope options"""
    COMPETITIVE_ONLY = "competitive_only"
    PREDICTIVE_ONLY = "predictive_only"
    UNIFIED_ANALYSIS = "unified_analysis"
    CROSS_ENGINE_FUSION = "cross_engine_fusion"


@dataclass
class EngineRequest:
    """Request for AI engine processing"""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str = ""
    engine_type: EngineType = EngineType.UNIFIED
    priority: ProcessingPriority = ProcessingPriority.NORMAL
    scope: AnalysisScope = AnalysisScope.UNIFIED_ANALYSIS

    # Context data
    lead_context: Optional[Dict[str, Any]] = None
    property_context: Optional[Dict[str, Any]] = None
    market_context: Optional[Dict[str, Any]] = None

    # Processing options
    use_cache: bool = True
    real_time_monitoring: bool = False
    include_interventions: bool = True
    include_risk_analysis: bool = True

    # Performance requirements
    max_processing_time_ms: float = 75.0
    accuracy_threshold: float = 0.95

    created_at: datetime = field(default_factory=datetime.now)

    def to_cache_key(self) -> str:
        """Generate cache key for request"""
        context_hash = hash(str(sorted(self.lead_context.items()))) if self.lead_context else 0
        return f"ai_engines:{self.lead_id}:{self.engine_type.value}:{self.scope.value}:{context_hash}"


@dataclass
class UnifiedAnalysisResult:
    """Unified analysis result from both engines"""

    request_id: str
    lead_id: str

    # Core analyses
    competitive_analysis: Optional[CompetitiveAnalysis] = None
    conversion_forecast: Optional[ConversionForecast] = None

    # Unified insights
    unified_insights: Dict[str, Any] = field(default_factory=dict)
    cross_engine_correlations: Dict[str, float] = field(default_factory=dict)

    # Action recommendations
    immediate_actions: List[str] = field(default_factory=list)
    strategic_recommendations: List[str] = field(default_factory=list)
    intervention_windows: List[InterventionWindow] = field(default_factory=list)

    # Risk assessment
    consolidated_risks: List[RiskFactor] = field(default_factory=list)
    risk_mitigation_strategies: List[str] = field(default_factory=list)

    # Performance metrics
    processing_time_ms: float = 0.0
    cache_hit: bool = False
    accuracy_score: float = 0.0
    confidence_level: float = 0.0

    # Engine-specific metrics
    competitive_processing_time: float = 0.0
    predictive_processing_time: float = 0.0
    fusion_processing_time: float = 0.0

    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()

        # Convert nested objects
        if self.competitive_analysis:
            data["competitive_analysis"] = self.competitive_analysis.to_dict()
        if self.conversion_forecast:
            data["conversion_forecast"] = self.conversion_forecast.to_dict()

        # Convert intervention windows
        data["intervention_windows"] = [
            {
                **asdict(iw),
                "start_date": iw.start_date.isoformat(),
                "end_date": iw.end_date.isoformat(),
                "intervention_type": iw.intervention_type.value
            }
            for iw in self.intervention_windows
        ]

        # Convert risk factors
        data["consolidated_risks"] = [
            {
                **asdict(rf),
                "risk_type": rf.risk_type.value
            }
            for rf in self.consolidated_risks
        ]

        return data


@dataclass
class PerformanceMetrics:
    """Integrated performance metrics"""

    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0

    # Performance metrics
    average_processing_time: float = 0.0
    p95_processing_time: float = 0.0
    p99_processing_time: float = 0.0

    # Engine-specific metrics
    competitive_engine_metrics: Dict[str, float] = field(default_factory=dict)
    predictive_engine_metrics: Dict[str, float] = field(default_factory=dict)

    # Resource utilization
    cpu_utilization: float = 0.0
    memory_utilization: float = 0.0
    redis_utilization: float = 0.0

    # Quality metrics
    average_accuracy: float = 0.0
    average_confidence: float = 0.0

    last_updated: datetime = field(default_factory=datetime.now)


class AIEnginesIntegrationService:
    """
    🎯 AI Engines Integration Service

    Unified coordination layer for Competitive Intelligence and Predictive Lifecycle engines
    with advanced performance optimization and cross-engine intelligence fusion.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize integration service with configuration"""
        self.config = config or {}

        # AI Engines
        self.competitive_engine: Optional[CompetitiveIntelligenceEngine] = None
        self.predictive_engine: Optional[PredictiveLeadLifecycleEngine] = None

        # Performance optimization services
        self.redis_client: Optional[OptimizedRedisClient] = None
        self.http_client: Optional[AsyncHTTPClient] = None
        self.db_cache: Optional[DatabaseCacheService] = None
        self.ml_service: Optional[BatchMLInferenceService] = None
        self.performance_monitor = PerformanceMonitoringService()

        # Cross-engine coordination
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.active_requests: Dict[str, EngineRequest] = {}
        self.result_cache: Dict[str, UnifiedAnalysisResult] = {}

        # Performance tracking
        self.metrics = PerformanceMetrics()
        self.processing_times = deque(maxlen=1000)

        # Resource management
        self.engine_semaphore = asyncio.Semaphore(10)  # Limit concurrent requests
        self.thread_executor = ThreadPoolExecutor(max_workers=4)

        logger.info("AI Engines Integration Service initialized")

    async def initialize(self) -> None:
        """Initialize integration service with all dependencies"""
        start_time = time.time()

        try:
            # Initialize optimized services
            await self._initialize_optimized_services()

            # Initialize AI engines
            await self._initialize_ai_engines()

            # Start background processes
            await self._start_background_processes()

            initialization_time = (time.time() - start_time) * 1000
            logger.info(f"AI Engines Integration Service initialized in {initialization_time:.1f}ms")

        except Exception as e:
            logger.error(f"Failed to initialize integration service: {e}")
            raise

    async def analyze_lead_unified(
        self,
        lead_id: str,
        analysis_scope: AnalysisScope = AnalysisScope.UNIFIED_ANALYSIS,
        priority: ProcessingPriority = ProcessingPriority.NORMAL,
        **kwargs
    ) -> UnifiedAnalysisResult:
        """
        Unified lead analysis using both AI engines with intelligent fusion

        Target Performance: <75ms total processing time
        """
        start_time = time.time()

        # Create analysis request
        request = EngineRequest(
            lead_id=lead_id,
            engine_type=EngineType.UNIFIED,
            priority=priority,
            scope=analysis_scope,
            lead_context=kwargs.get('lead_context'),
            property_context=kwargs.get('property_context'),
            market_context=kwargs.get('market_context'),
            use_cache=kwargs.get('use_cache', True),
            include_interventions=kwargs.get('include_interventions', True),
            include_risk_analysis=kwargs.get('include_risk_analysis', True)
        )

        try:
            # Check cache first
            if request.use_cache:
                cached_result = await self._get_cached_result(request.to_cache_key())
                if cached_result:
                    processing_time = (time.time() - start_time) * 1000
                    cached_result.processing_time_ms = processing_time
                    cached_result.cache_hit = True
                    self.metrics.cache_hits += 1
                    return cached_result

            # Execute unified analysis
            async with self.engine_semaphore:
                result = await self._execute_unified_analysis(request)

            # Cache result
            if request.use_cache and result:
                await self._cache_result(request.to_cache_key(), result)

            # Update metrics
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._update_metrics(processing_time, True)

            logger.info(f"Unified analysis completed in {processing_time:.1f}ms for lead {lead_id}")
            return result

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self._update_metrics(processing_time, False)
            logger.error(f"Unified analysis failed after {processing_time:.1f}ms: {e}")

            # Return fallback result
            return await self._create_fallback_result(request)

    async def analyze_competitive_intelligence(
        self,
        lead_id: str,
        property_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> CompetitiveAnalysis:
        """Analyze competitive landscape for lead"""
        if not self.competitive_engine:
            raise RuntimeError("Competitive Intelligence Engine not initialized")

        return await self.competitive_engine.analyze_competitive_landscape(
            lead_id, property_context
        )

    async def predict_lead_lifecycle(
        self,
        lead_id: str,
        force_refresh: bool = False,
        **kwargs
    ) -> ConversionForecast:
        """Predict lead conversion lifecycle"""
        if not self.predictive_engine:
            raise RuntimeError("Predictive Lead Lifecycle Engine not initialized")

        return await self.predictive_engine.predict_conversion_timeline(
            lead_id, force_refresh
        )

    async def detect_threats_and_opportunities(
        self,
        lead_id: str,
        monitoring_scope: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Detect competitive threats and conversion opportunities"""
        start_time = time.time()

        try:
            # Parallel execution of threat detection and opportunity analysis
            tasks = []

            if self.competitive_engine:
                tasks.append(
                    self.competitive_engine.detect_competitive_threats(
                        lead_id, monitoring_scope
                    )
                )

            if self.predictive_engine:
                tasks.append(
                    self.predictive_engine.predict_optimal_interventions(lead_id)
                )

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            threats = results[0] if len(results) > 0 and not isinstance(results[0], Exception) else []
            opportunities = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else []

            # Fusion and correlation analysis
            fused_insights = await self._fuse_threats_and_opportunities(
                lead_id, threats, opportunities
            )

            processing_time = (time.time() - start_time) * 1000
            logger.info(f"Threats and opportunities analysis completed in {processing_time:.1f}ms")

            return {
                "lead_id": lead_id,
                "competitive_threats": threats,
                "intervention_opportunities": opportunities,
                "fused_insights": fused_insights,
                "processing_time_ms": processing_time
            }

        except Exception as e:
            logger.error(f"Threats and opportunities analysis failed: {e}")
            return {
                "lead_id": lead_id,
                "competitive_threats": [],
                "intervention_opportunities": [],
                "fused_insights": {},
                "processing_time_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }

    async def generate_strategic_recommendations(
        self,
        lead_id: str,
        competitive_analysis: Optional[CompetitiveAnalysis] = None,
        conversion_forecast: Optional[ConversionForecast] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate strategic recommendations based on unified analysis"""
        start_time = time.time()

        try:
            # Get analyses if not provided
            if not competitive_analysis and self.competitive_engine:
                competitive_analysis = await self.competitive_engine.analyze_competitive_landscape(lead_id)

            if not conversion_forecast and self.predictive_engine:
                conversion_forecast = await self.predictive_engine.predict_conversion_timeline(lead_id)

            # Generate unified strategic recommendations
            recommendations = await self._generate_unified_strategy(
                lead_id, competitive_analysis, conversion_forecast
            )

            processing_time = (time.time() - start_time) * 1000
            recommendations["processing_time_ms"] = processing_time

            logger.info(f"Strategic recommendations generated in {processing_time:.1f}ms")
            return recommendations

        except Exception as e:
            logger.error(f"Strategic recommendations generation failed: {e}")
            return {
                "lead_id": lead_id,
                "immediate_actions": ["Contact lead within 1 hour", "Prepare market analysis"],
                "strategic_recommendations": ["Maintain competitive positioning"],
                "processing_time_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }

    # Private implementation methods

    async def _initialize_optimized_services(self):
        """Initialize optimized service connections"""
        # Redis client
        self.redis_client = OptimizedRedisClient(
            redis_url=self.config.get("redis_url", "redis://localhost:6379"),
            enable_compression=True
        )
        await self.redis_client.initialize()

        # HTTP client
        self.http_client = AsyncHTTPClient()
        await self.http_client.initialize()

        # Database cache
        self.db_cache = DatabaseCacheService(
            redis_client=self.redis_client,
            enable_l1_cache=True
        )
        await self.db_cache.initialize()

        # ML inference service
        self.ml_service = BatchMLInferenceService(
            model_cache_dir=self.config.get("model_cache_dir", "models"),
            enable_model_warming=True
        )
        await self.ml_service.initialize()

    async def _initialize_ai_engines(self):
        """Initialize AI engines with shared services"""
        # Competitive Intelligence Engine
        competitive_config = {
            **self.config,
            "shared_redis": self.redis_client,
            "shared_http": self.http_client,
            "shared_db_cache": self.db_cache
        }
        self.competitive_engine = CompetitiveIntelligenceEngine(competitive_config)
        await self.competitive_engine.initialize()

        # Predictive Lifecycle Engine
        predictive_config = {
            **self.config,
            "shared_redis": self.redis_client,
            "shared_ml_service": self.ml_service,
            "shared_db_cache": self.db_cache
        }
        self.predictive_engine = PredictiveLeadLifecycleEngine(predictive_config)
        await self.predictive_engine.initialize()

    async def _start_background_processes(self):
        """Start background monitoring and optimization processes"""
        # Performance monitoring
        asyncio.create_task(self._monitor_performance())

        # Cache optimization
        asyncio.create_task(self._optimize_cache_periodically())

        # Resource management
        asyncio.create_task(self._manage_resources())

    async def _execute_unified_analysis(self, request: EngineRequest) -> UnifiedAnalysisResult:
        """Execute unified analysis across both engines"""
        start_time = time.time()

        # Determine which engines to use based on scope
        use_competitive = request.scope in [
            AnalysisScope.COMPETITIVE_ONLY,
            AnalysisScope.UNIFIED_ANALYSIS,
            AnalysisScope.CROSS_ENGINE_FUSION
        ]
        use_predictive = request.scope in [
            AnalysisScope.PREDICTIVE_ONLY,
            AnalysisScope.UNIFIED_ANALYSIS,
            AnalysisScope.CROSS_ENGINE_FUSION
        ]

        # Parallel execution of engine analyses
        analysis_tasks = []

        if use_competitive and self.competitive_engine:
            analysis_tasks.append(
                self._time_execution(
                    self.competitive_engine.analyze_competitive_landscape(
                        request.lead_id, request.property_context
                    ),
                    "competitive"
                )
            )

        if use_predictive and self.predictive_engine:
            analysis_tasks.append(
                self._time_execution(
                    self.predictive_engine.predict_conversion_timeline(request.lead_id),
                    "predictive"
                )
            )

        # Execute analyses in parallel
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

        # Parse results
        competitive_result = None
        predictive_result = None
        competitive_time = 0.0
        predictive_time = 0.0

        for result, timing in results:
            if isinstance(result, Exception):
                logger.warning(f"Engine analysis failed: {result}")
                continue

            if hasattr(result, 'lead_id'):  # CompetitiveAnalysis
                competitive_result = result
                competitive_time = timing
            elif hasattr(result, 'expected_conversion_date'):  # ConversionForecast
                predictive_result = result
                predictive_time = timing

        # Cross-engine fusion
        fusion_start = time.time()
        unified_insights = await self._fuse_engine_results(
            request.lead_id, competitive_result, predictive_result
        )
        fusion_time = (time.time() - fusion_start) * 1000

        # Consolidate interventions and risks
        intervention_windows = []
        consolidated_risks = []

        if predictive_result:
            intervention_windows.extend(predictive_result.optimal_touchpoints)
            consolidated_risks.extend(predictive_result.risk_factors)

        if request.include_interventions and predictive_result:
            additional_interventions = await self.predictive_engine.predict_optimal_interventions(
                request.lead_id, predictive_result
            )
            intervention_windows.extend(additional_interventions)

        # Generate unified result
        result = UnifiedAnalysisResult(
            request_id=request.request_id,
            lead_id=request.lead_id,
            competitive_analysis=competitive_result,
            conversion_forecast=predictive_result,
            unified_insights=unified_insights,
            intervention_windows=intervention_windows,
            consolidated_risks=consolidated_risks,
            competitive_processing_time=competitive_time,
            predictive_processing_time=predictive_time,
            fusion_processing_time=fusion_time,
            accuracy_score=self._calculate_unified_accuracy(competitive_result, predictive_result),
            confidence_level=self._calculate_unified_confidence(competitive_result, predictive_result)
        )

        return result

    async def _time_execution(self, coro, label: str) -> Tuple[Any, float]:
        """Execute coroutine with timing"""
        start_time = time.time()
        result = await coro
        execution_time = (time.time() - start_time) * 1000
        return result, execution_time

    async def _fuse_engine_results(
        self,
        lead_id: str,
        competitive_analysis: Optional[CompetitiveAnalysis],
        conversion_forecast: Optional[ConversionForecast]
    ) -> Dict[str, Any]:
        """Fuse results from both engines into unified insights"""
        insights = {
            "cross_engine_correlations": {},
            "unified_timeline": {},
            "strategic_priorities": [],
            "risk_opportunity_matrix": {}
        }

        if competitive_analysis and conversion_forecast:
            # Timeline correlation
            competitive_urgency = len([
                threat for threat in competitive_analysis.active_threats
                if threat.threat_level in ["high", "critical"]
            ])

            predicted_days = (conversion_forecast.expected_conversion_date - datetime.now()).days

            # Correlate competitive pressure with conversion timeline
            if competitive_urgency > 2 and predicted_days > 30:
                insights["strategic_priorities"].append("accelerate_timeline")
                insights["unified_timeline"]["recommended_acceleration"] = 7  # days

            # Risk-opportunity matrix
            if competitive_analysis.win_probability > 0.8 and conversion_forecast.conversion_probability > 0.8:
                insights["risk_opportunity_matrix"]["high_confidence_conversion"] = True

            # Cross-correlations
            insights["cross_engine_correlations"] = {
                "competitive_pressure_vs_timeline": competitive_urgency / max(1, predicted_days / 10),
                "win_probability_alignment": abs(
                    competitive_analysis.win_probability - conversion_forecast.conversion_probability
                )
            }

        return insights

    async def _fuse_threats_and_opportunities(
        self,
        lead_id: str,
        threats: List[Any],
        opportunities: List[Any]
    ) -> Dict[str, Any]:
        """Fuse competitive threats with conversion opportunities"""
        fused_insights = {
            "threat_opportunity_balance": 0.0,
            "prioritized_actions": [],
            "timing_optimization": {}
        }

        # Calculate threat-opportunity balance
        threat_score = sum(
            0.8 if hasattr(t, 'threat_assessment') and t.threat_assessment == ThreatLevel.HIGH else 0.4
            for t in threats
        )

        opportunity_score = sum(
            opp.expected_impact if hasattr(opp, 'expected_impact') else 0.5
            for opp in opportunities
        )

        fused_insights["threat_opportunity_balance"] = opportunity_score - threat_score

        # Generate prioritized actions
        if threat_score > opportunity_score:
            fused_insights["prioritized_actions"] = [
                "Address competitive threats immediately",
                "Accelerate conversion timeline",
                "Implement defensive strategies"
            ]
        else:
            fused_insights["prioritized_actions"] = [
                "Capitalize on conversion opportunities",
                "Maintain competitive positioning",
                "Execute optimal intervention timing"
            ]

        return fused_insights

    async def _generate_unified_strategy(
        self,
        lead_id: str,
        competitive_analysis: Optional[CompetitiveAnalysis],
        conversion_forecast: Optional[ConversionForecast]
    ) -> Dict[str, Any]:
        """Generate unified strategic recommendations"""
        strategy = {
            "immediate_actions": [],
            "strategic_recommendations": [],
            "timeline_optimization": {},
            "resource_allocation": {}
        }

        # Immediate actions based on both analyses
        if competitive_analysis:
            strategy["immediate_actions"].extend(competitive_analysis.immediate_actions)

        if conversion_forecast:
            # Add conversion-specific actions
            days_to_conversion = (conversion_forecast.expected_conversion_date - datetime.now()).days
            if days_to_conversion < 14:
                strategy["immediate_actions"].append("Prepare for imminent conversion")
            elif days_to_conversion > 60:
                strategy["immediate_actions"].append("Implement long-term nurturing strategy")

        # Strategic recommendations fusion
        if competitive_analysis and conversion_forecast:
            if competitive_analysis.win_probability > 0.8 and conversion_forecast.conversion_probability > 0.8:
                strategy["strategic_recommendations"] = [
                    "Maintain current strategy - high success probability",
                    "Focus on execution excellence",
                    "Prepare for closing phase"
                ]
            elif competitive_analysis.win_probability < 0.5:
                strategy["strategic_recommendations"] = [
                    "Implement aggressive competitive strategy",
                    "Differentiate value proposition",
                    "Accelerate engagement timeline"
                ]

        return strategy

    async def _calculate_unified_accuracy(
        self,
        competitive_analysis: Optional[CompetitiveAnalysis],
        conversion_forecast: Optional[ConversionForecast]
    ) -> float:
        """Calculate unified accuracy score"""
        scores = []

        if competitive_analysis:
            scores.append(competitive_analysis.analysis_accuracy)

        if conversion_forecast:
            scores.append(conversion_forecast.prediction_accuracy_score)

        return sum(scores) / len(scores) if scores else 0.0

    async def _calculate_unified_confidence(
        self,
        competitive_analysis: Optional[CompetitiveAnalysis],
        conversion_forecast: Optional[ConversionForecast]
    ) -> float:
        """Calculate unified confidence level"""
        scores = []

        if competitive_analysis:
            scores.append(competitive_analysis.confidence_score)

        if conversion_forecast:
            # Derive confidence from accuracy and processing quality
            scores.append(conversion_forecast.prediction_accuracy_score)

        return sum(scores) / len(scores) if scores else 0.0

    # Caching and optimization methods

    async def _get_cached_result(self, cache_key: str) -> Optional[UnifiedAnalysisResult]:
        """Get cached unified result"""
        try:
            cached_data = await self.redis_client.optimized_get(cache_key)
            if cached_data:
                return UnifiedAnalysisResult(**cached_data)
        except Exception:
            pass
        return None

    async def _cache_result(self, cache_key: str, result: UnifiedAnalysisResult):
        """Cache unified result"""
        try:
            await self.redis_client.optimized_set(
                cache_key,
                result.to_dict(),
                ttl=1800  # 30 minutes
            )
        except Exception as e:
            logger.warning(f"Failed to cache unified result: {e}")

    async def _create_fallback_result(self, request: EngineRequest) -> UnifiedAnalysisResult:
        """Create fallback result when analysis fails"""
        return UnifiedAnalysisResult(
            request_id=request.request_id,
            lead_id=request.lead_id,
            unified_insights={"status": "fallback_mode"},
            immediate_actions=["Contact lead within 1 hour", "Prepare market analysis"],
            strategic_recommendations=["Maintain standard follow-up process"],
            accuracy_score=0.6,
            confidence_level=0.5
        )

    # Background monitoring and optimization

    async def _monitor_performance(self):
        """Background performance monitoring"""
        while True:
            try:
                # Update performance metrics
                await self._update_performance_metrics()

                # Check for performance regressions
                await self._check_performance_thresholds()

                # Optimize resource allocation
                await self._optimize_resource_allocation()

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(60)

    async def _optimize_cache_periodically(self):
        """Periodic cache optimization"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                # Cache cleanup and optimization
                await self._cleanup_expired_cache()
                await self._optimize_cache_hit_rate()

            except Exception as e:
                logger.error(f"Cache optimization error: {e}")

    async def _manage_resources(self):
        """Background resource management"""
        while True:
            try:
                await asyncio.sleep(120)  # Every 2 minutes

                # Monitor resource usage
                cpu_usage = await self._get_cpu_usage()
                memory_usage = await self._get_memory_usage()

                # Adjust concurrency limits based on resource usage
                if cpu_usage > 0.8:
                    self.engine_semaphore = asyncio.Semaphore(max(2, self.engine_semaphore._value - 1))
                elif cpu_usage < 0.5 and self.engine_semaphore._value < 10:
                    self.engine_semaphore = asyncio.Semaphore(self.engine_semaphore._value + 1)

            except Exception as e:
                logger.error(f"Resource management error: {e}")

    def _update_metrics(self, processing_time: float, success: bool):
        """Update performance metrics"""
        self.metrics.total_requests += 1
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1

        self.processing_times.append(processing_time)

        # Update averages
        if self.processing_times:
            self.metrics.average_processing_time = sum(self.processing_times) / len(self.processing_times)
            sorted_times = sorted(self.processing_times)
            self.metrics.p95_processing_time = sorted_times[int(len(sorted_times) * 0.95)]
            self.metrics.p99_processing_time = sorted_times[int(len(sorted_times) * 0.99)]

    async def _update_performance_metrics(self):
        """Update detailed performance metrics"""
        # Get engine-specific metrics
        if self.competitive_engine:
            competitive_health = await self.competitive_engine.health_check()
            self.metrics.competitive_engine_metrics = competitive_health.get("performance_metrics", {})

        if self.predictive_engine:
            predictive_health = await self.predictive_engine.health_check()
            self.metrics.predictive_engine_metrics = predictive_health.get("performance_metrics", {})

    async def _check_performance_thresholds(self):
        """Check performance against thresholds"""
        if self.metrics.average_processing_time > 75.0:  # Target: <75ms
            logger.warning(f"Average processing time {self.metrics.average_processing_time:.1f}ms exceeds target")

        if self.metrics.p95_processing_time > 100.0:  # Target: <100ms p95
            logger.warning(f"P95 processing time {self.metrics.p95_processing_time:.1f}ms exceeds target")

    async def _optimize_resource_allocation(self):
        """Optimize resource allocation based on current load"""
        # Implementation for dynamic resource optimization
        pass

    async def _cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        # Implementation for cache cleanup
        pass

    async def _optimize_cache_hit_rate(self):
        """Optimize cache hit rate"""
        # Implementation for cache optimization
        pass

    async def _get_cpu_usage(self) -> float:
        """Get current CPU usage"""
        # Simplified implementation
        return 0.6  # Would use actual system metrics

    async def _get_memory_usage(self) -> float:
        """Get current memory usage"""
        # Simplified implementation
        return 0.7  # Would use actual system metrics

    # Public API methods

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        return {
            "integration_service": asdict(self.metrics),
            "competitive_engine": self.metrics.competitive_engine_metrics,
            "predictive_engine": self.metrics.predictive_engine_metrics,
            "cache_hit_rate": (self.metrics.cache_hits / max(1, self.metrics.total_requests)) * 100,
            "success_rate": (self.metrics.successful_requests / max(1, self.metrics.total_requests)) * 100
        }

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for integration service"""
        try:
            # Check individual engines
            engine_healths = {}

            if self.competitive_engine:
                engine_healths["competitive"] = await self.competitive_engine.health_check()

            if self.predictive_engine:
                engine_healths["predictive"] = await self.predictive_engine.health_check()

            # Check optimized services
            service_healths = {
                "redis": await self.redis_client.health_check() if self.redis_client else {"healthy": False},
                "http_client": await self.http_client.health_check() if self.http_client else {"healthy": False},
                "db_cache": await self.db_cache.health_check() if self.db_cache else {"healthy": False},
                "ml_service": await self.ml_service.health_check() if self.ml_service else {"healthy": False}
            }

            # Determine overall health
            all_engines_healthy = all(
                health.get("healthy", False) for health in engine_healths.values()
            )
            all_services_healthy = all(
                health.get("healthy", False) for health in service_healths.values()
            )

            overall_healthy = all_engines_healthy and all_services_healthy

            return {
                "healthy": overall_healthy,
                "service": "ai_engines_integration_service",
                "version": "1.0.0",
                "engines": engine_healths,
                "services": service_healths,
                "performance_metrics": asdict(self.metrics),
                "active_requests": len(self.active_requests),
                "cache_size": len(self.result_cache)
            }

        except Exception as e:
            return {
                "healthy": False,
                "service": "ai_engines_integration_service",
                "error": str(e)
            }

    async def cleanup(self):
        """Cleanup integration service and all dependencies"""
        try:
            # Cleanup AI engines
            if self.competitive_engine:
                await self.competitive_engine.cleanup()

            if self.predictive_engine:
                await self.predictive_engine.cleanup()

            # Cleanup optimized services
            if self.redis_client:
                await self.redis_client.close()
            if self.http_client:
                await self.http_client.cleanup()
            if self.db_cache:
                await self.db_cache.cleanup()
            if self.ml_service:
                await self.ml_service.cleanup()

            # Cleanup thread executor
            self.thread_executor.shutdown(wait=True)

            logger.info("AI Engines Integration Service cleaned up")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")


# Factory function
async def get_ai_engines_integration_service(
    config: Optional[Dict[str, Any]] = None
) -> AIEnginesIntegrationService:
    """Factory function to create and initialize integration service"""
    service = AIEnginesIntegrationService(config)
    await service.initialize()
    return service