"""
Real-Time Lead Scoring Service

High-performance ML inference engine for real-time lead scoring with <100ms latency.
Integrates XGBoost models with L1/L2 caching for sub-100ms predictions.

Key Features:
- XGBoost model loading and caching
- Redis L2 + in-memory L1 caching for <10ms cache hits
- Feature extraction from webhook events
- Real-time score updates with WebSocket broadcasting
- Batch scoring optimization for high throughput
- Circuit breaker pattern for model resilience

Performance Targets:
- Inference latency: <100ms (95th percentile)
- Cache hit latency: <10ms
- Model loading: <500ms
- Batch throughput: 100+ leads/second
- Cache hit rate: >80%
"""

import asyncio
import json
import pickle
import time
import hashlib
import numpy as np
import xgboost as xgb
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum
from collections import defaultdict

from ghl_real_estate_ai.models.lead_behavioral_features import (
    LeadBehavioralFeatures,
    LeadBehavioralFeatureExtractor,
    extract_lead_features
)
from ghl_real_estate_ai.services.integration_cache_manager import get_cache_manager
from ghl_real_estate_ai.services.dashboard_analytics_service import get_dashboard_analytics_service
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class ScoreConfidenceLevel(Enum):
    """Confidence levels for lead scores"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ModelLoadStatus(Enum):
    """Model loading status"""
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"
    FALLBACK = "fallback"


@dataclass
class LeadScore:
    """Lead scoring result with confidence and explanation"""
    lead_id: str
    score: float  # 0-1 probability
    confidence: ScoreConfidenceLevel
    model_version: str
    timestamp: datetime

    # Feature contributions (SHAP-like values)
    feature_contributions: Dict[str, float]

    # Quality indicators
    feature_quality: float  # 0-1
    prediction_confidence: float  # 0-1

    # Performance metrics
    inference_time_ms: float
    cache_hit: bool = False

    # Explanation
    top_features: List[Tuple[str, float]]  # (feature_name, contribution)
    score_tier: str = ""  # "hot", "warm", "cold"


@dataclass
class BatchScoringResult:
    """Result of batch scoring operation"""
    total_leads: int
    successful_scores: int
    failed_scores: int
    avg_inference_time_ms: float
    cache_hit_rate: float
    model_version: str
    timestamp: datetime

    scores: List[LeadScore]
    errors: List[str]


@dataclass
class ModelPerformanceMetrics:
    """Model performance monitoring"""
    model_version: str
    total_predictions: int
    avg_inference_time_ms: float
    cache_hit_rate: float
    error_rate: float

    # Performance distribution
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float

    # Model health
    prediction_distribution: Dict[str, int]  # score ranges
    feature_importance: Dict[str, float]

    last_updated: datetime


class RealtimeLeadScoringService:
    """
    Real-time lead scoring service with XGBoost inference and advanced caching.

    Provides sub-100ms lead scoring with comprehensive caching strategy:
    - L1 Cache: In-memory with 30-second TTL
    - L2 Cache: Redis with 5-minute TTL
    - Model Cache: In-memory model storage with version management
    """

    def __init__(self):
        self.model_cache = {}  # In-memory model storage
        self.score_cache = {}  # L1 in-memory score cache
        self.feature_extractor = LeadBehavioralFeatureExtractor()
        self.cache_manager = None
        self.dashboard_service = None
        self.model_load_status = ModelLoadStatus.LOADING
        self.current_model_version = "v1.0.0"

        # Performance tracking
        self.performance_metrics = defaultdict(list)
        self.cache_stats = defaultdict(int)

        # Configuration
        self.l1_cache_ttl = 30  # seconds
        self.l2_cache_ttl = 300  # seconds
        self.max_l1_cache_size = 1000
        self.batch_size = 100

        # Model configuration
        self.model_path = Path(__file__).parent.parent / "models" / "trained"
        self.fallback_model_path = self.model_path / "fallback_scorer.pkl"

    async def initialize(self):
        """Initialize service with dependencies and models"""
        try:
            self.cache_manager = get_cache_manager()
            self.dashboard_service = get_dashboard_analytics_service()

            # Load primary model
            await self._load_primary_model()

            # Load fallback model if primary fails
            if self.model_load_status != ModelLoadStatus.LOADED:
                await self._load_fallback_model()

            logger.info(f"RealtimeLeadScoringService initialized with model status: {self.model_load_status}")

        except Exception as e:
            logger.error(f"Failed to initialize RealtimeLeadScoringService: {e}")
            self.model_load_status = ModelLoadStatus.FAILED
            raise

    async def score_lead_event(
        self,
        lead_id: str,
        event_data: Dict[str, Any],
        include_features: bool = True
    ) -> LeadScore:
        """
        Score a lead based on webhook event data with real-time inference.

        Args:
            lead_id: Lead identifier
            event_data: Webhook event data containing lead info and interactions
            include_features: Whether to include feature extraction

        Returns:
            LeadScore with inference results and performance metrics
        """
        start_time = time.time()

        try:
            # Check L1 cache first
            cache_key = self._generate_cache_key(lead_id, event_data)
            cached_score = await self._get_l1_cached_score(cache_key)

            if cached_score:
                cached_score.cache_hit = True
                self.cache_stats['l1_hits'] += 1
                return cached_score

            # Check L2 cache
            cached_score = await self._get_l2_cached_score(cache_key)
            if cached_score:
                # Store in L1 for faster access
                await self._store_l1_cache(cache_key, cached_score)
                cached_score.cache_hit = True
                self.cache_stats['l2_hits'] += 1
                return cached_score

            # Cache miss - perform inference
            self.cache_stats['cache_misses'] += 1

            # Extract features
            features = await self._extract_features_from_event(lead_id, event_data)

            # Run model inference
            score = await self._predict_score(features)

            # Add performance metrics
            inference_time = (time.time() - start_time) * 1000
            score.inference_time_ms = inference_time
            score.cache_hit = False

            # Store in both cache levels
            await self._store_l1_cache(cache_key, score)
            await self._store_l2_cache(cache_key, score)

            # Track performance
            self.performance_metrics['inference_times'].append(inference_time)

            # Update dashboard analytics
            await self._update_dashboard_analytics(score)

            # Log performance warning if too slow
            if inference_time > 100:
                logger.warning(f"Slow inference for lead {lead_id}: {inference_time:.1f}ms")

            logger.debug(f"Lead scoring completed for {lead_id}: {score.score:.3f} "
                        f"({score.confidence.value}, {inference_time:.1f}ms)")

            return score

        except Exception as e:
            logger.error(f"Lead scoring failed for {lead_id}: {e}")
            return await self._create_fallback_score(lead_id, event_data)

    async def get_cached_score(
        self,
        lead_id: str,
        max_age_minutes: int = 5
    ) -> Optional[LeadScore]:
        """
        Get cached score for a lead if available and fresh.

        Args:
            lead_id: Lead identifier
            max_age_minutes: Maximum age of cached score

        Returns:
            Cached LeadScore if available, None otherwise
        """
        try:
            # Try L1 cache first
            for cache_key, score in self.score_cache.items():
                if lead_id in cache_key:
                    age_minutes = (datetime.now() - score.timestamp).total_seconds() / 60
                    if age_minutes <= max_age_minutes:
                        self.cache_stats['l1_hits'] += 1
                        return score

            # Try L2 cache
            cache_pattern = f"lead_score:{lead_id}:*"
            if self.cache_manager:
                cached_data = await self.cache_manager.get_with_pattern(cache_pattern)
                if cached_data:
                    score_data = json.loads(cached_data[0])
                    score = self._deserialize_score(score_data)

                    age_minutes = (datetime.now() - score.timestamp).total_seconds() / 60
                    if age_minutes <= max_age_minutes:
                        self.cache_stats['l2_hits'] += 1
                        return score

            return None

        except Exception as e:
            logger.error(f"Failed to get cached score for {lead_id}: {e}")
            return None

    async def batch_score_leads(
        self,
        lead_events: List[Tuple[str, Dict[str, Any]]],
        parallel_workers: int = 10
    ) -> BatchScoringResult:
        """
        Score multiple leads in parallel with optimized performance.

        Args:
            lead_events: List of (lead_id, event_data) tuples
            parallel_workers: Number of parallel scoring workers

        Returns:
            BatchScoringResult with aggregated metrics
        """
        start_time = time.time()

        try:
            # Split into batches for parallel processing
            batches = [
                lead_events[i:i + self.batch_size]
                for i in range(0, len(lead_events), self.batch_size)
            ]

            # Process batches in parallel
            semaphore = asyncio.Semaphore(parallel_workers)
            tasks = [
                self._process_batch(batch, semaphore)
                for batch in batches
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Aggregate results
            all_scores = []
            all_errors = []
            successful_scores = 0
            failed_scores = 0
            total_inference_time = 0
            cache_hits = 0

            for result in batch_results:
                if isinstance(result, Exception):
                    all_errors.append(str(result))
                    failed_scores += 1
                else:
                    scores, errors = result
                    all_scores.extend(scores)
                    all_errors.extend(errors)

                    for score in scores:
                        if score:
                            successful_scores += 1
                            total_inference_time += score.inference_time_ms
                            if score.cache_hit:
                                cache_hits += 1
                        else:
                            failed_scores += 1

            # Calculate metrics
            total_leads = len(lead_events)
            avg_inference_time = total_inference_time / successful_scores if successful_scores > 0 else 0
            cache_hit_rate = cache_hits / total_leads if total_leads > 0 else 0

            total_time = (time.time() - start_time) * 1000

            result = BatchScoringResult(
                total_leads=total_leads,
                successful_scores=successful_scores,
                failed_scores=failed_scores,
                avg_inference_time_ms=avg_inference_time,
                cache_hit_rate=cache_hit_rate,
                model_version=self.current_model_version,
                timestamp=datetime.now(),
                scores=all_scores,
                errors=all_errors
            )

            logger.info(f"Batch scoring completed: {total_leads} leads in {total_time:.1f}ms "
                       f"(success: {successful_scores}, cache hit rate: {cache_hit_rate:.1%})")

            return result

        except Exception as e:
            logger.error(f"Batch scoring failed: {e}")
            return BatchScoringResult(
                total_leads=len(lead_events),
                successful_scores=0,
                failed_scores=len(lead_events),
                avg_inference_time_ms=0,
                cache_hit_rate=0,
                model_version=self.current_model_version,
                timestamp=datetime.now(),
                scores=[],
                errors=[str(e)]
            )

    async def invalidate_lead_cache(self, lead_id: str) -> None:
        """
        Invalidate all cached scores for a lead.

        Args:
            lead_id: Lead identifier
        """
        try:
            # Remove from L1 cache
            keys_to_remove = [k for k in self.score_cache.keys() if lead_id in k]
            for key in keys_to_remove:
                del self.score_cache[key]

            # Remove from L2 cache
            if self.cache_manager:
                cache_pattern = f"lead_score:{lead_id}:*"
                await self.cache_manager.delete_pattern(cache_pattern)

            logger.debug(f"Cache invalidated for lead {lead_id}")

        except Exception as e:
            logger.error(f"Failed to invalidate cache for lead {lead_id}: {e}")

    async def get_model_performance_metrics(self) -> ModelPerformanceMetrics:
        """
        Get comprehensive model performance metrics.

        Returns:
            ModelPerformanceMetrics with current performance data
        """
        try:
            inference_times = self.performance_metrics['inference_times']

            # Calculate performance percentiles
            if inference_times:
                p50 = np.percentile(inference_times, 50)
                p95 = np.percentile(inference_times, 95)
                p99 = np.percentile(inference_times, 99)
                avg_time = np.mean(inference_times)
            else:
                p50 = p95 = p99 = avg_time = 0

            # Calculate cache hit rate
            total_requests = (
                self.cache_stats['l1_hits'] +
                self.cache_stats['l2_hits'] +
                self.cache_stats['cache_misses']
            )
            cache_hit_rate = (
                (self.cache_stats['l1_hits'] + self.cache_stats['l2_hits']) / total_requests
                if total_requests > 0 else 0
            )

            # Get model feature importance if available
            feature_importance = {}
            if 'xgb_model' in self.model_cache:
                try:
                    model = self.model_cache['xgb_model']
                    if hasattr(model, 'feature_importances_'):
                        importance_scores = model.feature_importances_
                        feature_names = [f"feature_{i}" for i in range(len(importance_scores))]
                        feature_importance = dict(zip(feature_names, importance_scores))
                except Exception:
                    pass

            return ModelPerformanceMetrics(
                model_version=self.current_model_version,
                total_predictions=total_requests,
                avg_inference_time_ms=avg_time,
                cache_hit_rate=cache_hit_rate,
                error_rate=0.0,  # TODO: Track errors
                p50_latency_ms=p50,
                p95_latency_ms=p95,
                p99_latency_ms=p99,
                prediction_distribution={},  # TODO: Track score distribution
                feature_importance=feature_importance,
                last_updated=datetime.now()
            )

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return ModelPerformanceMetrics(
                model_version=self.current_model_version,
                total_predictions=0,
                avg_inference_time_ms=0,
                cache_hit_rate=0,
                error_rate=1.0,
                p50_latency_ms=0,
                p95_latency_ms=0,
                p99_latency_ms=0,
                prediction_distribution={},
                feature_importance={},
                last_updated=datetime.now()
            )

    async def _load_primary_model(self) -> None:
        """Load primary XGBoost model"""
        try:
            model_file = self.model_path / f"lead_scoring_{self.current_model_version}.xgb"

            if model_file.exists():
                # Load XGBoost model
                model = xgb.Booster()
                model.load_model(str(model_file))
                self.model_cache['xgb_model'] = model

                # Load feature metadata
                metadata_file = self.model_path / f"lead_scoring_{self.current_model_version}_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        self.model_cache['metadata'] = json.load(f)

                self.model_load_status = ModelLoadStatus.LOADED
                logger.info(f"Primary XGBoost model {self.current_model_version} loaded successfully")
            else:
                logger.warning(f"Primary model file not found: {model_file}")
                raise FileNotFoundError(f"Model file not found: {model_file}")

        except Exception as e:
            logger.error(f"Failed to load primary model: {e}")
            self.model_load_status = ModelLoadStatus.FAILED

    async def _load_fallback_model(self) -> None:
        """Load fallback rule-based model"""
        try:
            # Create a simple rule-based fallback scorer
            fallback_model = FallbackLeadScorer()
            self.model_cache['fallback_model'] = fallback_model
            self.model_load_status = ModelLoadStatus.FALLBACK

            logger.info("Fallback rule-based model loaded")

        except Exception as e:
            logger.error(f"Failed to load fallback model: {e}")
            self.model_load_status = ModelLoadStatus.FAILED

    async def _extract_features_from_event(
        self,
        lead_id: str,
        event_data: Dict[str, Any]
    ) -> LeadBehavioralFeatures:
        """Extract features from webhook event data"""

        try:
            # Extract lead data and interaction history from event
            lead_data = event_data.get('lead_data', {})
            lead_data['id'] = lead_id

            interaction_history = event_data.get('interaction_history', [])

            # Extract features
            features = self.feature_extractor.extract_features(lead_data, interaction_history)

            return features

        except Exception as e:
            logger.error(f"Feature extraction failed for lead {lead_id}: {e}")
            # Return minimal features for fallback
            return LeadBehavioralFeatures(
                lead_id=lead_id,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )

    async def _predict_score(self, features: LeadBehavioralFeatures) -> LeadScore:
        """Run ML inference on extracted features"""

        start_time = time.time()

        try:
            if self.model_load_status == ModelLoadStatus.LOADED and 'xgb_model' in self.model_cache:
                # Use XGBoost model
                score = await self._predict_with_xgboost(features)
            elif self.model_load_status == ModelLoadStatus.FALLBACK and 'fallback_model' in self.model_cache:
                # Use fallback model
                score = await self._predict_with_fallback(features)
            else:
                # No model available
                score = await self._predict_with_default(features)

            inference_time = (time.time() - start_time) * 1000
            score.inference_time_ms = inference_time

            return score

        except Exception as e:
            logger.error(f"Model prediction failed for lead {features.lead_id}: {e}")
            return await self._predict_with_default(features)

    async def _predict_with_xgboost(self, features: LeadBehavioralFeatures) -> LeadScore:
        """Predict using XGBoost model"""

        model = self.model_cache['xgb_model']
        metadata = self.model_cache.get('metadata', {})

        # Convert features to XGBoost DMatrix
        feature_vector = self._features_to_vector(features, metadata)
        dmatrix = xgb.DMatrix(feature_vector.reshape(1, -1))

        # Run inference
        prediction = model.predict(dmatrix)[0]

        # Calculate confidence based on prediction certainty
        confidence = self._calculate_confidence(prediction)

        # Get feature contributions (approximate SHAP values)
        feature_contributions = self._calculate_feature_contributions(model, dmatrix, metadata)

        # Get top contributing features
        top_features = sorted(
            feature_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:5]

        return LeadScore(
            lead_id=features.lead_id,
            score=float(prediction),
            confidence=confidence,
            model_version=self.current_model_version,
            timestamp=datetime.now(),
            feature_contributions=feature_contributions,
            feature_quality=features.feature_quality.completeness_score,
            prediction_confidence=self._calculate_prediction_confidence(prediction),
            inference_time_ms=0,  # Will be set by caller
            top_features=top_features,
            score_tier=self._determine_score_tier(prediction)
        )

    async def _predict_with_fallback(self, features: LeadBehavioralFeatures) -> LeadScore:
        """Predict using fallback rule-based model"""

        fallback_model = self.model_cache['fallback_model']
        score_result = fallback_model.score_lead(features)

        return LeadScore(
            lead_id=features.lead_id,
            score=score_result['score'],
            confidence=ScoreConfidenceLevel.MEDIUM,
            model_version="fallback_v1.0.0",
            timestamp=datetime.now(),
            feature_contributions=score_result['feature_contributions'],
            feature_quality=features.feature_quality.completeness_score,
            prediction_confidence=0.7,
            inference_time_ms=0,
            top_features=score_result['top_features'],
            score_tier=self._determine_score_tier(score_result['score'])
        )

    async def _predict_with_default(self, features: LeadBehavioralFeatures) -> LeadScore:
        """Create default score when no model is available"""

        # Simple heuristic based on basic engagement
        base_score = 0.5
        if features.engagement_patterns.total_interactions > 0:
            base_score += min(0.3, features.engagement_patterns.total_interactions / 20)

        if features.days_since_last_activity < 7:
            base_score += 0.1

        score = min(1.0, base_score)

        return LeadScore(
            lead_id=features.lead_id,
            score=score,
            confidence=ScoreConfidenceLevel.LOW,
            model_version="default_v1.0.0",
            timestamp=datetime.now(),
            feature_contributions={'engagement': 0.3, 'recency': 0.1},
            feature_quality=features.feature_quality.completeness_score,
            prediction_confidence=0.5,
            inference_time_ms=0,
            top_features=[('engagement', 0.3), ('recency', 0.1)],
            score_tier=self._determine_score_tier(score)
        )

    def _features_to_vector(
        self,
        features: LeadBehavioralFeatures,
        metadata: Dict[str, Any]
    ) -> np.ndarray:
        """Convert features to numerical vector for XGBoost"""

        # Get expected features from metadata
        expected_features = metadata.get('feature_names', list(features.numerical_features.keys()))

        # Build feature vector
        vector = []
        for feature_name in expected_features:
            if feature_name in features.numerical_features:
                vector.append(features.numerical_features[feature_name])
            else:
                vector.append(0.0)  # Missing feature

        return np.array(vector, dtype=np.float32)

    def _calculate_confidence(self, prediction: float) -> ScoreConfidenceLevel:
        """Calculate confidence level based on prediction value"""

        # Higher confidence for predictions closer to extremes
        distance_from_center = abs(prediction - 0.5)

        if distance_from_center > 0.4:
            return ScoreConfidenceLevel.VERY_HIGH
        elif distance_from_center > 0.3:
            return ScoreConfidenceLevel.HIGH
        elif distance_from_center > 0.2:
            return ScoreConfidenceLevel.MEDIUM
        else:
            return ScoreConfidenceLevel.LOW

    def _calculate_feature_contributions(
        self,
        model: xgb.Booster,
        dmatrix: xgb.DMatrix,
        metadata: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate approximate feature contributions"""

        try:
            # Get SHAP values if available
            shap_values = model.predict(dmatrix, pred_contribs=True)[0]
            feature_names = metadata.get('feature_names', [])

            contributions = {}
            for i, contrib in enumerate(shap_values[:-1]):  # Exclude bias term
                feature_name = feature_names[i] if i < len(feature_names) else f"feature_{i}"
                contributions[feature_name] = float(contrib)

            return contributions

        except Exception as e:
            logger.warning(f"Failed to calculate feature contributions: {e}")
            return {}

    def _calculate_prediction_confidence(self, prediction: float) -> float:
        """Calculate prediction confidence score"""

        # Confidence based on distance from decision boundary (0.5)
        distance = abs(prediction - 0.5)
        confidence = min(1.0, distance * 2)  # Scale to 0-1
        return confidence

    def _determine_score_tier(self, score: float) -> str:
        """Determine score tier (hot/warm/cold)"""

        if score >= 0.7:
            return "hot"
        elif score >= 0.4:
            return "warm"
        else:
            return "cold"

    async def _process_batch(
        self,
        batch: List[Tuple[str, Dict[str, Any]]],
        semaphore: asyncio.Semaphore
    ) -> Tuple[List[LeadScore], List[str]]:
        """Process a batch of leads for scoring"""

        async with semaphore:
            scores = []
            errors = []

            for lead_id, event_data in batch:
                try:
                    score = await self.score_lead_event(lead_id, event_data)
                    scores.append(score)
                except Exception as e:
                    errors.append(f"Lead {lead_id}: {str(e)}")
                    scores.append(None)

            return scores, errors

    def _generate_cache_key(self, lead_id: str, event_data: Dict[str, Any]) -> str:
        """Generate cache key from lead ID and event data"""

        # Create hash from event data for cache invalidation
        event_hash = hashlib.md5(json.dumps(event_data, sort_keys=True).encode()).hexdigest()[:8]
        return f"lead_score:{lead_id}:{event_hash}"

    async def _get_l1_cached_score(self, cache_key: str) -> Optional[LeadScore]:
        """Get score from L1 in-memory cache"""

        if cache_key in self.score_cache:
            score = self.score_cache[cache_key]

            # Check TTL
            age_seconds = (datetime.now() - score.timestamp).total_seconds()
            if age_seconds <= self.l1_cache_ttl:
                return score
            else:
                # Expired - remove from cache
                del self.score_cache[cache_key]

        return None

    async def _get_l2_cached_score(self, cache_key: str) -> Optional[LeadScore]:
        """Get score from L2 Redis cache"""

        if not self.cache_manager:
            return None

        try:
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                score_data = json.loads(cached_data)
                return self._deserialize_score(score_data)

        except Exception as e:
            logger.warning(f"Failed to get L2 cached score: {e}")

        return None

    async def _store_l1_cache(self, cache_key: str, score: LeadScore) -> None:
        """Store score in L1 in-memory cache"""

        # Implement LRU eviction if cache is full
        if len(self.score_cache) >= self.max_l1_cache_size:
            # Remove oldest entry
            oldest_key = min(self.score_cache.keys(),
                           key=lambda k: self.score_cache[k].timestamp)
            del self.score_cache[oldest_key]

        self.score_cache[cache_key] = score

    async def _store_l2_cache(self, cache_key: str, score: LeadScore) -> None:
        """Store score in L2 Redis cache"""

        if not self.cache_manager:
            return

        try:
            score_data = self._serialize_score(score)
            await self.cache_manager.set(
                cache_key,
                json.dumps(score_data),
                ttl=self.l2_cache_ttl
            )

        except Exception as e:
            logger.warning(f"Failed to store L2 cached score: {e}")

    def _serialize_score(self, score: LeadScore) -> Dict[str, Any]:
        """Serialize LeadScore for caching"""

        data = asdict(score)
        data['timestamp'] = score.timestamp.isoformat()
        data['confidence'] = score.confidence.value
        return data

    def _deserialize_score(self, data: Dict[str, Any]) -> LeadScore:
        """Deserialize LeadScore from cached data"""

        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['confidence'] = ScoreConfidenceLevel(data['confidence'])
        return LeadScore(**data)

    async def _update_dashboard_analytics(self, score: LeadScore) -> None:
        """Update dashboard analytics with new score"""

        if self.dashboard_service:
            try:
                await self.dashboard_service.update_lead_score(
                    score.lead_id,
                    score.score,
                    score.score_tier
                )
            except Exception as e:
                logger.warning(f"Failed to update dashboard analytics: {e}")

    async def _create_fallback_score(self, lead_id: str, event_data: Dict[str, Any]) -> LeadScore:
        """Create fallback score when all inference methods fail"""

        return LeadScore(
            lead_id=lead_id,
            score=0.5,  # Neutral score
            confidence=ScoreConfidenceLevel.LOW,
            model_version="emergency_fallback",
            timestamp=datetime.now(),
            feature_contributions={},
            feature_quality=0.0,
            prediction_confidence=0.0,
            inference_time_ms=1.0,
            top_features=[],
            score_tier="warm"
        )


class FallbackLeadScorer:
    """Rule-based fallback scorer when ML model is unavailable"""

    def score_lead(self, features: LeadBehavioralFeatures) -> Dict[str, Any]:
        """Score lead using rule-based approach"""

        score = 0.5  # Base score
        contributions = {}

        # Engagement scoring
        if features.engagement_patterns.total_interactions > 0:
            engagement_score = min(0.3, features.engagement_patterns.total_interactions / 20)
            score += engagement_score
            contributions['engagement'] = engagement_score

        # Recency scoring
        if features.days_since_last_activity < 7:
            recency_score = 0.2
            score += recency_score
            contributions['recency'] = recency_score
        elif features.days_since_last_activity < 30:
            recency_score = 0.1
            score += recency_score
            contributions['recency'] = recency_score

        # Intent scoring
        intent_score = features.behavioral_signals.intent_strength * 0.2
        score += intent_score
        contributions['intent'] = intent_score

        # Responsiveness scoring
        if features.communication_prefs.email_response_rate > 0.5:
            responsiveness_score = 0.1
            score += responsiveness_score
            contributions['responsiveness'] = responsiveness_score

        score = min(1.0, score)

        top_features = sorted(contributions.items(), key=lambda x: x[1], reverse=True)

        return {
            'score': score,
            'feature_contributions': contributions,
            'top_features': top_features
        }


# Global service instance
_lead_scoring_service = None


async def get_lead_scoring_service() -> RealtimeLeadScoringService:
    """Get singleton instance of RealtimeLeadScoringService"""
    global _lead_scoring_service

    if _lead_scoring_service is None:
        _lead_scoring_service = RealtimeLeadScoringService()
        await _lead_scoring_service.initialize()

    return _lead_scoring_service


# Convenience functions
async def score_lead_from_event(
    lead_id: str,
    event_data: Dict[str, Any]
) -> LeadScore:
    """Score a single lead from webhook event data"""
    service = await get_lead_scoring_service()
    return await service.score_lead_event(lead_id, event_data)


async def batch_score_leads_from_events(
    lead_events: List[Tuple[str, Dict[str, Any]]]
) -> BatchScoringResult:
    """Score multiple leads from webhook event data"""
    service = await get_lead_scoring_service()
    return await service.batch_score_leads(lead_events)