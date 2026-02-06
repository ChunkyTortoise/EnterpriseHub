"""
Advanced Streaming Analytics for Customer Intelligence Platform.

Provides real-time analytics, predictive customer journey mapping,
and advanced segmentation for comprehensive customer intelligence.
"""

import asyncio
import json
import uuid
import math
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import statistics

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

from ..core.event_bus import EventBus, EventType
from ..core.redis_conversation_context import RedisConversationContext
from ..database.service import DatabaseService
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MetricType(Enum):
    """Types of analytics metrics."""
    ENGAGEMENT_SCORE = "engagement_score"
    CONVERSION_PROBABILITY = "conversion_probability"
    CHURN_RISK = "churn_risk"
    CLV_PREDICTION = "clv_prediction"
    RESPONSE_TIME = "response_time"
    SATISFACTION_SCORE = "satisfaction_score"
    INTERACTION_FREQUENCY = "interaction_frequency"
    SESSION_DURATION = "session_duration"


class SegmentType(Enum):
    """Customer segment types."""
    HIGH_VALUE = "high_value"
    GROWTH_POTENTIAL = "growth_potential"
    AT_RISK = "at_risk"
    CHAMPION = "champion"
    LOYAL = "loyal"
    NEW_CUSTOMER = "new_customer"
    HIBERNATING = "hibernating"
    PRICE_SENSITIVE = "price_sensitive"


class JourneyStage(Enum):
    """Customer journey stages for predictive mapping."""
    AWARENESS = "awareness"
    CONSIDERATION = "consideration"
    EVALUATION = "evaluation"
    PURCHASE = "purchase"
    ONBOARDING = "onboarding"
    ADOPTION = "adoption"
    ADVOCACY = "advocacy"
    RENEWAL = "renewal"


@dataclass
class RealTimeMetric:
    """Real-time analytics metric."""
    metric_id: str
    customer_id: str
    tenant_id: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    metadata: Dict[str, Any]
    department_id: Optional[str] = None


@dataclass
class CustomerSegment:
    """Customer segment assignment."""
    segment_id: str
    customer_id: str
    tenant_id: str
    segment_type: SegmentType
    confidence: float
    features: Dict[str, float]
    created_at: datetime
    expires_at: Optional[datetime] = None


@dataclass
class JourneyPrediction:
    """Predictive customer journey mapping."""
    prediction_id: str
    customer_id: str
    tenant_id: str
    current_stage: JourneyStage
    predicted_next_stage: JourneyStage
    stage_probability: float
    estimated_timeline: timedelta
    influential_factors: List[str]
    created_at: datetime


class StreamingAnalyticsEngine:
    """Real-time streaming analytics processor."""
    
    def __init__(self):
        self.event_bus = EventBus()
        self.redis_context = RedisConversationContext()
        self.db_service = DatabaseService()
        
        # In-memory buffers for real-time processing
        self.metric_buffer: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.session_tracker: Dict[str, Dict] = {}
        
        # Analytics models (in production, load from trained models)
        self.engagement_model = None
        self.churn_model = None
        self.clv_model = None
        
    async def start_streaming(self):
        """Start the streaming analytics engine."""
        logger.info("Starting streaming analytics engine")
        
        # Subscribe to relevant events
        await self.event_bus.subscribe(
            EventType.CONVERSATION_MESSAGE_SENT,
            self._process_conversation_event
        )
        await self.event_bus.subscribe(
            EventType.CONVERSATION_STARTED,
            self._process_session_start
        )
        await self.event_bus.subscribe(
            EventType.CONVERSATION_ENDED,
            self._process_session_end
        )
        await self.event_bus.subscribe(
            EventType.LEAD_SCORED,
            self._process_lead_scoring_event
        )
        
        # Start background tasks
        asyncio.create_task(self._metric_aggregation_loop())
        asyncio.create_task(self._session_timeout_monitor())
        
    async def _process_conversation_event(self, event_data: Dict[str, Any]):
        """Process conversation message events for real-time analytics."""
        try:
            customer_id = event_data.get("customer_id")
            tenant_id = event_data.get("tenant_id")
            department_id = event_data.get("department_id")
            
            # Calculate engagement metrics
            await self._calculate_engagement_metrics(
                customer_id, 
                tenant_id, 
                event_data,
                department_id
            )
            
            # Update session tracking
            await self._update_session_tracking(customer_id, event_data)
            
            # Calculate response time if it's a system response
            if event_data.get("sender") == "system":
                await self._calculate_response_time(customer_id, tenant_id, event_data)
                
        except Exception as e:
            logger.error(f"Error processing conversation event: {e}")
    
    async def _process_session_start(self, event_data: Dict[str, Any]):
        """Process session start events."""
        customer_id = event_data.get("customer_id")
        session_id = event_data.get("session_id", str(uuid.uuid4()))
        
        self.session_tracker[customer_id] = {
            "session_id": session_id,
            "start_time": datetime.utcnow(),
            "message_count": 0,
            "last_activity": datetime.utcnow()
        }
    
    async def _process_session_end(self, event_data: Dict[str, Any]):
        """Process session end events."""
        customer_id = event_data.get("customer_id")
        
        if customer_id in self.session_tracker:
            session_data = self.session_tracker[customer_id]
            
            # Calculate session duration
            duration = datetime.utcnow() - session_data["start_time"]
            
            # Create session duration metric
            await self._emit_metric(
                customer_id=customer_id,
                tenant_id=event_data.get("tenant_id"),
                metric_type=MetricType.SESSION_DURATION,
                value=duration.total_seconds(),
                metadata={
                    "session_id": session_data["session_id"],
                    "message_count": session_data["message_count"],
                    "duration_minutes": duration.total_seconds() / 60
                }
            )
            
            # Clean up session tracking
            del self.session_tracker[customer_id]
    
    async def _process_lead_scoring_event(self, event_data: Dict[str, Any]):
        """Process lead scoring events."""
        customer_id = event_data.get("customer_id")
        tenant_id = event_data.get("tenant_id")
        lead_score = event_data.get("lead_score", 0)
        
        # Convert lead score to conversion probability
        conversion_prob = self._score_to_probability(lead_score)
        
        await self._emit_metric(
            customer_id=customer_id,
            tenant_id=tenant_id,
            metric_type=MetricType.CONVERSION_PROBABILITY,
            value=conversion_prob,
            metadata={
                "lead_score": lead_score,
                "score_tier": event_data.get("score_tier", "unknown")
            }
        )
    
    async def _calculate_engagement_metrics(
        self,
        customer_id: str,
        tenant_id: str,
        event_data: Dict[str, Any],
        department_id: Optional[str]
    ):
        """Calculate real-time engagement metrics."""
        
        # Get recent conversation history for context
        context_key = f"{department_id}:{customer_id}" if department_id else customer_id
        conversation_data = await self.redis_context.get_context(customer_id, department_id)
        
        # Calculate engagement score based on multiple factors
        engagement_factors = {
            "message_length": len(event_data.get("message", "")),
            "response_speed": event_data.get("response_time_seconds", 0),
            "conversation_depth": len(conversation_data.get("conversation_history", [])),
            "interaction_frequency": await self._get_interaction_frequency(customer_id)
        }
        
        # Weighted engagement score calculation
        engagement_score = self._calculate_weighted_engagement(engagement_factors)
        
        await self._emit_metric(
            customer_id=customer_id,
            tenant_id=tenant_id,
            metric_type=MetricType.ENGAGEMENT_SCORE,
            value=engagement_score,
            metadata=engagement_factors,
            department_id=department_id
        )
    
    async def _calculate_response_time(
        self,
        customer_id: str,
        tenant_id: str,
        event_data: Dict[str, Any]
    ):
        """Calculate response time metrics."""
        response_time = event_data.get("response_time_seconds")
        if response_time is not None:
            await self._emit_metric(
                customer_id=customer_id,
                tenant_id=tenant_id,
                metric_type=MetricType.RESPONSE_TIME,
                value=response_time,
                metadata={
                    "response_quality": event_data.get("response_quality", "unknown"),
                    "processing_time": event_data.get("processing_time_ms", 0)
                }
            )
    
    async def _update_session_tracking(self, customer_id: str, event_data: Dict[str, Any]):
        """Update session tracking data."""
        if customer_id in self.session_tracker:
            session = self.session_tracker[customer_id]
            session["message_count"] += 1
            session["last_activity"] = datetime.utcnow()
    
    async def _emit_metric(
        self,
        customer_id: str,
        tenant_id: str,
        metric_type: MetricType,
        value: float,
        metadata: Dict[str, Any],
        department_id: Optional[str] = None
    ):
        """Emit a real-time metric."""
        metric = RealTimeMetric(
            metric_id=str(uuid.uuid4()),
            customer_id=customer_id,
            tenant_id=tenant_id,
            metric_type=metric_type,
            value=value,
            timestamp=datetime.utcnow(),
            metadata=metadata,
            department_id=department_id
        )
        
        # Add to buffer for aggregation
        buffer_key = f"{tenant_id}:{metric_type.value}"
        self.metric_buffer[buffer_key].append(metric)
        
        # Store in database for historical analysis
        await self.db_service.store_metric(asdict(metric))
        
        # Publish metric event
        await self.event_bus.publish(
            EventType.REALTIME_METRIC_GENERATED,
            {
                "metric_id": metric.metric_id,
                "customer_id": customer_id,
                "tenant_id": tenant_id,
                "metric_type": metric_type.value,
                "value": value,
                "timestamp": metric.timestamp.isoformat()
            }
        )
    
    def _calculate_weighted_engagement(self, factors: Dict[str, float]) -> float:
        """Calculate weighted engagement score from multiple factors."""
        # Weights for different engagement factors
        weights = {
            "message_length": 0.2,
            "response_speed": 0.3,
            "conversation_depth": 0.3,
            "interaction_frequency": 0.2
        }
        
        # Normalize factors to 0-1 scale
        normalized_factors = {}
        
        # Message length: normalize to reasonable scale (0-500 chars)
        normalized_factors["message_length"] = min(factors.get("message_length", 0) / 500, 1.0)
        
        # Response speed: invert so faster = higher score (max 30 seconds)
        response_time = factors.get("response_speed", 30)
        normalized_factors["response_speed"] = max(0, 1 - (response_time / 30))
        
        # Conversation depth: normalize to reasonable scale (0-20 messages)
        normalized_factors["conversation_depth"] = min(factors.get("conversation_depth", 0) / 20, 1.0)
        
        # Interaction frequency: assume already normalized 0-1
        normalized_factors["interaction_frequency"] = factors.get("interaction_frequency", 0.5)
        
        # Calculate weighted score
        engagement_score = sum(
            weights[factor] * normalized_factors[factor]
            for factor in weights.keys()
        )
        
        return min(engagement_score * 100, 100)  # Scale to 0-100
    
    def _score_to_probability(self, score: int) -> float:
        """Convert lead score to conversion probability."""
        # Simple sigmoid transformation
        return 1 / (1 + math.exp(-0.1 * (score - 50)))
    
    async def _get_interaction_frequency(self, customer_id: str) -> float:
        """Get customer interaction frequency (interactions per day)."""
        # Get recent metrics from buffer or database
        # For now, return a placeholder value
        return 0.5  # Average interaction frequency
    
    async def _metric_aggregation_loop(self):
        """Background loop for metric aggregation."""
        while True:
            try:
                await asyncio.sleep(60)  # Aggregate every minute
                
                for buffer_key, metrics in self.metric_buffer.items():
                    if metrics:
                        await self._aggregate_metrics(buffer_key, list(metrics))
                        metrics.clear()
                        
            except Exception as e:
                logger.error(f"Error in metric aggregation loop: {e}")
    
    async def _session_timeout_monitor(self):
        """Monitor and clean up inactive sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                timeout_threshold = datetime.utcnow() - timedelta(minutes=30)
                expired_customers = []
                
                for customer_id, session_data in self.session_tracker.items():
                    if session_data["last_activity"] < timeout_threshold:
                        expired_customers.append(customer_id)
                
                # Process expired sessions
                for customer_id in expired_customers:
                    await self._process_session_timeout(customer_id)
                    
            except Exception as e:
                logger.error(f"Error in session timeout monitor: {e}")
    
    async def _aggregate_metrics(self, buffer_key: str, metrics: List[RealTimeMetric]):
        """Aggregate metrics for efficiency."""
        if not metrics:
            return
            
        # Calculate aggregated values
        values = [m.value for m in metrics]
        aggregation = {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0
        }
        
        # Store aggregated metrics
        await self.db_service.store_aggregated_metrics(
            buffer_key,
            aggregation,
            datetime.utcnow()
        )
    
    async def _process_session_timeout(self, customer_id: str):
        """Process session timeout."""
        if customer_id in self.session_tracker:
            session_data = self.session_tracker[customer_id]
            
            # Emit session end event
            await self.event_bus.publish(
                EventType.CONVERSATION_ENDED,
                {
                    "customer_id": customer_id,
                    "session_id": session_data["session_id"],
                    "reason": "timeout"
                }
            )
            
            del self.session_tracker[customer_id]


class CustomerSegmentationEngine:
    """Advanced customer segmentation using ML algorithms."""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.redis_context = RedisConversationContext()
        self.scaler = StandardScaler()
        self.kmeans_model = KMeans(n_clusters=8, random_state=42)
        
    async def perform_segmentation(self, tenant_id: str) -> List[CustomerSegment]:
        """Perform customer segmentation for a tenant."""
        logger.info(f"Starting customer segmentation for tenant {tenant_id}")
        
        # Get customer data
        customer_data = await self.db_service.get_tenant_customer_metrics(tenant_id)
        
        if not customer_data:
            logger.warning(f"No customer data found for tenant {tenant_id}")
            return []
        
        # Prepare feature matrix
        features_df = await self._prepare_feature_matrix(customer_data)
        
        # Perform clustering
        segments = await self._perform_clustering(features_df, tenant_id)
        
        # Store segments in database
        for segment in segments:
            await self.db_service.store_customer_segment(asdict(segment))
        
        logger.info(f"Segmentation complete: {len(segments)} customers segmented")
        return segments
    
    async def _prepare_feature_matrix(self, customer_data: List[Dict]) -> pd.DataFrame:
        """Prepare feature matrix for segmentation."""
        features = []
        
        for customer in customer_data:
            feature_vector = {
                "customer_id": customer["customer_id"],
                "engagement_score": customer.get("avg_engagement_score", 0),
                "interaction_frequency": customer.get("interaction_count", 0) / max(customer.get("days_active", 1), 1),
                "session_duration": customer.get("avg_session_duration", 0),
                "response_time": customer.get("avg_response_time", 0),
                "conversion_probability": customer.get("max_conversion_probability", 0),
                "churn_risk": customer.get("latest_churn_risk", 0.5),
                "clv_prediction": customer.get("predicted_clv", 0),
                "satisfaction_score": customer.get("avg_satisfaction_score", 0.5),
                "tenure_days": customer.get("tenure_days", 0)
            }
            features.append(feature_vector)
        
        return pd.DataFrame(features)
    
    async def _perform_clustering(
        self, 
        features_df: pd.DataFrame, 
        tenant_id: str
    ) -> List[CustomerSegment]:
        """Perform K-means clustering on customer features."""
        
        # Separate customer IDs from features
        customer_ids = features_df["customer_id"].values
        feature_columns = features_df.drop(["customer_id"], axis=1)
        
        # Scale features
        scaled_features = self.scaler.fit_transform(feature_columns.values)
        
        # Perform clustering
        cluster_labels = self.kmeans_model.fit_predict(scaled_features)
        
        # Map clusters to business segments
        segments = []
        for i, customer_id in enumerate(customer_ids):
            cluster_id = cluster_labels[i]
            
            # Determine segment type based on cluster characteristics
            segment_type = self._map_cluster_to_segment(
                cluster_id,
                feature_columns.iloc[i].to_dict()
            )
            
            # Calculate confidence score
            confidence = self._calculate_segment_confidence(
                scaled_features[i], 
                cluster_id
            )
            
            segment = CustomerSegment(
                segment_id=str(uuid.uuid4()),
                customer_id=customer_id,
                tenant_id=tenant_id,
                segment_type=segment_type,
                confidence=confidence,
                features=feature_columns.iloc[i].to_dict(),
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30)  # Refresh monthly
            )
            
            segments.append(segment)
        
        return segments
    
    def _map_cluster_to_segment(
        self, 
        cluster_id: int, 
        features: Dict[str, float]
    ) -> SegmentType:
        """Map cluster characteristics to business segment types."""
        
        # High-level segmentation logic based on feature values
        engagement = features.get("engagement_score", 0)
        frequency = features.get("interaction_frequency", 0)
        clv = features.get("clv_prediction", 0)
        churn_risk = features.get("churn_risk", 0.5)
        tenure = features.get("tenure_days", 0)
        
        # Champions: High engagement, high CLV, low churn
        if engagement > 70 and clv > 1000 and churn_risk < 0.3:
            return SegmentType.CHAMPION
        
        # High value: High CLV, moderate engagement
        elif clv > 1000 and engagement > 50:
            return SegmentType.HIGH_VALUE
        
        # At risk: High churn risk, previously valuable
        elif churn_risk > 0.7 and (clv > 500 or engagement > 40):
            return SegmentType.AT_RISK
        
        # Loyal: Long tenure, consistent engagement
        elif tenure > 90 and engagement > 40 and churn_risk < 0.5:
            return SegmentType.LOYAL
        
        # New customers: Short tenure
        elif tenure < 30:
            return SegmentType.NEW_CUSTOMER
        
        # Growth potential: Low current value but high engagement
        elif clv < 500 and engagement > 60:
            return SegmentType.GROWTH_POTENTIAL
        
        # Hibernating: Low recent activity but not high churn risk
        elif frequency < 0.1 and churn_risk < 0.6:
            return SegmentType.HIBERNATING
        
        # Default to price sensitive
        else:
            return SegmentType.PRICE_SENSITIVE
    
    def _calculate_segment_confidence(
        self, 
        feature_vector: np.ndarray, 
        cluster_id: int
    ) -> float:
        """Calculate confidence score for segment assignment."""
        
        # Get cluster center
        cluster_center = self.kmeans_model.cluster_centers_[cluster_id]
        
        # Calculate distance to cluster center
        distance = np.linalg.norm(feature_vector - cluster_center)
        
        # Convert distance to confidence (higher distance = lower confidence)
        max_distance = np.max([
            np.linalg.norm(center - cluster_center) 
            for center in self.kmeans_model.cluster_centers_
        ])
        
        confidence = max(0.0, 1.0 - (distance / max_distance))
        return confidence


class PredictiveJourneyMapper:
    """Predictive customer journey mapping using ML."""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.journey_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.stage_transitions = self._initialize_stage_transitions()
        
    def _initialize_stage_transitions(self) -> Dict[JourneyStage, List[Tuple[JourneyStage, float]]]:
        """Initialize stage transition probabilities."""
        return {
            JourneyStage.AWARENESS: [
                (JourneyStage.CONSIDERATION, 0.4),
                (JourneyStage.AWARENESS, 0.6)
            ],
            JourneyStage.CONSIDERATION: [
                (JourneyStage.EVALUATION, 0.5),
                (JourneyStage.AWARENESS, 0.2),
                (JourneyStage.CONSIDERATION, 0.3)
            ],
            JourneyStage.EVALUATION: [
                (JourneyStage.PURCHASE, 0.3),
                (JourneyStage.CONSIDERATION, 0.3),
                (JourneyStage.EVALUATION, 0.4)
            ],
            JourneyStage.PURCHASE: [
                (JourneyStage.ONBOARDING, 0.8),
                (JourneyStage.PURCHASE, 0.2)
            ],
            JourneyStage.ONBOARDING: [
                (JourneyStage.ADOPTION, 0.7),
                (JourneyStage.ONBOARDING, 0.3)
            ],
            JourneyStage.ADOPTION: [
                (JourneyStage.ADVOCACY, 0.2),
                (JourneyStage.RENEWAL, 0.6),
                (JourneyStage.ADOPTION, 0.2)
            ],
            JourneyStage.ADVOCACY: [
                (JourneyStage.RENEWAL, 0.8),
                (JourneyStage.ADVOCACY, 0.2)
            ],
            JourneyStage.RENEWAL: [
                (JourneyStage.ADOPTION, 0.7),
                (JourneyStage.RENEWAL, 0.3)
            ]
        }
    
    async def predict_journey(
        self, 
        customer_id: str, 
        tenant_id: str
    ) -> JourneyPrediction:
        """Predict next stage in customer journey."""
        
        # Get customer data and current metrics
        customer_data = await self.db_service.get_customer_journey_data(customer_id)
        current_metrics = await self.db_service.get_latest_customer_metrics(customer_id)
        
        # Determine current stage
        current_stage = self._determine_current_stage(customer_data, current_metrics)
        
        # Predict next stage
        next_stage, probability = self._predict_next_stage(
            current_stage, 
            current_metrics
        )
        
        # Estimate timeline
        estimated_timeline = self._estimate_timeline(
            current_stage, 
            next_stage, 
            current_metrics
        )
        
        # Identify influential factors
        influential_factors = self._identify_influential_factors(
            current_metrics, 
            next_stage
        )
        
        prediction = JourneyPrediction(
            prediction_id=str(uuid.uuid4()),
            customer_id=customer_id,
            tenant_id=tenant_id,
            current_stage=current_stage,
            predicted_next_stage=next_stage,
            stage_probability=probability,
            estimated_timeline=estimated_timeline,
            influential_factors=influential_factors,
            created_at=datetime.utcnow()
        )
        
        # Store prediction
        await self.db_service.store_journey_prediction(asdict(prediction))
        
        return prediction
    
    def _determine_current_stage(
        self, 
        customer_data: Dict, 
        metrics: Dict
    ) -> JourneyStage:
        """Determine customer's current journey stage."""
        
        # Simple rule-based stage determination
        # In production, this would use trained ML models
        
        interaction_count = customer_data.get("interaction_count", 0)
        has_purchased = customer_data.get("has_purchased", False)
        engagement_score = metrics.get("engagement_score", 0)
        tenure_days = customer_data.get("tenure_days", 0)
        
        if has_purchased:
            if tenure_days > 90:
                return JourneyStage.RENEWAL
            elif engagement_score > 70:
                return JourneyStage.ADVOCACY
            elif tenure_days > 30:
                return JourneyStage.ADOPTION
            else:
                return JourneyStage.ONBOARDING
        else:
            if interaction_count > 5 and engagement_score > 60:
                return JourneyStage.EVALUATION
            elif interaction_count > 2:
                return JourneyStage.CONSIDERATION
            else:
                return JourneyStage.AWARENESS
    
    def _predict_next_stage(
        self, 
        current_stage: JourneyStage, 
        metrics: Dict
    ) -> Tuple[JourneyStage, float]:
        """Predict next journey stage."""
        
        # Get possible transitions for current stage
        possible_transitions = self.stage_transitions.get(current_stage, [])
        
        if not possible_transitions:
            return current_stage, 1.0
        
        # Adjust probabilities based on customer metrics
        adjusted_transitions = []
        for next_stage, base_probability in possible_transitions:
            adjusted_prob = self._adjust_probability_by_metrics(
                current_stage, 
                next_stage, 
                base_probability, 
                metrics
            )
            adjusted_transitions.append((next_stage, adjusted_prob))
        
        # Normalize probabilities
        total_prob = sum(prob for _, prob in adjusted_transitions)
        if total_prob > 0:
            adjusted_transitions = [
                (stage, prob / total_prob) 
                for stage, prob in adjusted_transitions
            ]
        
        # Return most likely next stage
        return max(adjusted_transitions, key=lambda x: x[1])
    
    def _adjust_probability_by_metrics(
        self,
        current_stage: JourneyStage,
        next_stage: JourneyStage,
        base_probability: float,
        metrics: Dict
    ) -> float:
        """Adjust transition probability based on customer metrics."""
        
        engagement_score = metrics.get("engagement_score", 50)
        conversion_prob = metrics.get("conversion_probability", 0.5)
        churn_risk = metrics.get("churn_risk", 0.5)
        
        # Adjustment factors
        engagement_factor = engagement_score / 50  # Normalize around 50
        conversion_factor = conversion_prob * 2  # Scale to 0-2
        retention_factor = (1 - churn_risk) * 2  # Scale to 0-2
        
        # Different adjustments for different transitions
        if next_stage in [JourneyStage.PURCHASE, JourneyStage.RENEWAL]:
            # Purchase/renewal more likely with high engagement and conversion
            adjustment = (engagement_factor + conversion_factor) / 2
        elif next_stage in [JourneyStage.ADVOCACY, JourneyStage.ADOPTION]:
            # Advocacy/adoption more likely with high engagement and retention
            adjustment = (engagement_factor + retention_factor) / 2
        else:
            # Default adjustment based on overall health
            adjustment = (engagement_factor + retention_factor + conversion_factor) / 3
        
        return base_probability * max(0.1, min(2.0, adjustment))
    
    def _estimate_timeline(
        self,
        current_stage: JourneyStage,
        next_stage: JourneyStage,
        metrics: Dict
    ) -> timedelta:
        """Estimate timeline for stage transition."""
        
        # Base timelines for different transitions (in days)
        base_timelines = {
            (JourneyStage.AWARENESS, JourneyStage.CONSIDERATION): 7,
            (JourneyStage.CONSIDERATION, JourneyStage.EVALUATION): 14,
            (JourneyStage.EVALUATION, JourneyStage.PURCHASE): 21,
            (JourneyStage.PURCHASE, JourneyStage.ONBOARDING): 3,
            (JourneyStage.ONBOARDING, JourneyStage.ADOPTION): 30,
            (JourneyStage.ADOPTION, JourneyStage.ADVOCACY): 90,
            (JourneyStage.ADVOCACY, JourneyStage.RENEWAL): 180,
            (JourneyStage.RENEWAL, JourneyStage.ADOPTION): 7
        }
        
        base_days = base_timelines.get((current_stage, next_stage), 30)
        
        # Adjust based on engagement (higher engagement = faster progression)
        engagement_score = metrics.get("engagement_score", 50)
        engagement_factor = 50 / max(engagement_score, 1)  # Inverse relationship
        
        adjusted_days = base_days * engagement_factor
        return timedelta(days=max(1, int(adjusted_days)))
    
    def _identify_influential_factors(
        self, 
        metrics: Dict, 
        next_stage: JourneyStage
    ) -> List[str]:
        """Identify factors influencing journey progression."""
        
        factors = []
        
        # Check engagement impact
        engagement_score = metrics.get("engagement_score", 50)
        if engagement_score > 70:
            factors.append("high_engagement")
        elif engagement_score < 30:
            factors.append("low_engagement")
        
        # Check conversion probability
        conversion_prob = metrics.get("conversion_probability", 0.5)
        if conversion_prob > 0.7:
            factors.append("strong_purchase_intent")
        elif conversion_prob < 0.3:
            factors.append("weak_purchase_intent")
        
        # Check churn risk
        churn_risk = metrics.get("churn_risk", 0.5)
        if churn_risk > 0.7:
            factors.append("high_churn_risk")
        elif churn_risk < 0.3:
            factors.append("low_churn_risk")
        
        # Check response time
        response_time = metrics.get("response_time", 10)
        if response_time < 5:
            factors.append("fast_support_response")
        elif response_time > 30:
            factors.append("slow_support_response")
        
        return factors


class AdvancedAnalyticsOrchestrator:
    """
    Main orchestrator for advanced analytics capabilities.
    
    Coordinates real-time streaming analytics, customer segmentation,
    and predictive journey mapping.
    """
    
    def __init__(self):
        self.streaming_engine = StreamingAnalyticsEngine()
        self.segmentation_engine = CustomerSegmentationEngine()
        self.journey_mapper = PredictiveJourneyMapper()
        self.db_service = DatabaseService()
        
    async def start(self):
        """Start all analytics engines."""
        logger.info("Starting Advanced Analytics Orchestrator")
        
        # Start streaming analytics
        await self.streaming_engine.start_streaming()
        
        # Schedule periodic tasks
        asyncio.create_task(self._segmentation_scheduler())
        asyncio.create_task(self._journey_prediction_scheduler())
        
    async def get_customer_analytics(
        self, 
        customer_id: str, 
        tenant_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive analytics for a customer."""
        
        # Get real-time metrics
        recent_metrics = await self.db_service.get_recent_customer_metrics(
            customer_id, 
            hours=24
        )
        
        # Get current segment
        current_segment = await self.db_service.get_customer_segment(customer_id)
        
        # Get journey prediction
        journey_prediction = await self.journey_mapper.predict_journey(
            customer_id, 
            tenant_id
        )
        
        return {
            "customer_id": customer_id,
            "tenant_id": tenant_id,
            "real_time_metrics": recent_metrics,
            "segment": asdict(current_segment) if current_segment else None,
            "journey_prediction": asdict(journey_prediction),
            "analytics_timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_tenant_analytics_dashboard(self, tenant_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics dashboard for a tenant."""
        
        # Get aggregated metrics
        daily_metrics = await self.db_service.get_tenant_daily_metrics(tenant_id)
        
        # Get segment distribution
        segment_distribution = await self.db_service.get_segment_distribution(tenant_id)
        
        # Get journey stage distribution
        journey_distribution = await self.db_service.get_journey_stage_distribution(tenant_id)
        
        # Calculate key performance indicators
        kpis = await self._calculate_tenant_kpis(tenant_id)
        
        return {
            "tenant_id": tenant_id,
            "daily_metrics": daily_metrics,
            "segment_distribution": segment_distribution,
            "journey_distribution": journey_distribution,
            "kpis": kpis,
            "dashboard_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _segmentation_scheduler(self):
        """Schedule periodic customer segmentation."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Get all tenants
                tenants = await self.db_service.get_active_tenants()
                
                for tenant in tenants:
                    tenant_id = tenant["tenant_id"]
                    
                    # Check if segmentation is due (daily)
                    last_segmentation = await self.db_service.get_last_segmentation_time(tenant_id)
                    
                    if not last_segmentation or (datetime.utcnow() - last_segmentation).days >= 1:
                        logger.info(f"Running segmentation for tenant {tenant_id}")
                        await self.segmentation_engine.perform_segmentation(tenant_id)
                        
            except Exception as e:
                logger.error(f"Error in segmentation scheduler: {e}")
    
    async def _journey_prediction_scheduler(self):
        """Schedule periodic journey predictions."""
        while True:
            try:
                await asyncio.sleep(1800)  # Run every 30 minutes
                
                # Get active customers (had activity in last 7 days)
                active_customers = await self.db_service.get_active_customers(days=7)
                
                for customer in active_customers:
                    try:
                        await self.journey_mapper.predict_journey(
                            customer["customer_id"], 
                            customer["tenant_id"]
                        )
                    except Exception as e:
                        logger.error(f"Journey prediction failed for customer {customer['customer_id']}: {e}")
                        
            except Exception as e:
                logger.error(f"Error in journey prediction scheduler: {e}")
    
    async def _calculate_tenant_kpis(self, tenant_id: str) -> Dict[str, Any]:
        """Calculate key performance indicators for a tenant."""
        
        # Get metrics for the last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        metrics = await self.db_service.get_tenant_metrics_range(
            tenant_id, 
            start_date, 
            end_date
        )
        
        if not metrics:
            return {}
        
        # Calculate KPIs
        kpis = {
            "total_customers": len(set(m["customer_id"] for m in metrics)),
            "average_engagement_score": statistics.mean(
                m["engagement_score"] for m in metrics 
                if m.get("engagement_score") is not None
            ),
            "average_response_time": statistics.mean(
                m["response_time"] for m in metrics 
                if m.get("response_time") is not None
            ),
            "conversion_rate": statistics.mean(
                m["conversion_probability"] for m in metrics 
                if m.get("conversion_probability") is not None
            ),
            "churn_risk_average": statistics.mean(
                m["churn_risk"] for m in metrics 
                if m.get("churn_risk") is not None
            ),
            "total_interactions": sum(1 for m in metrics),
            "calculation_period_days": 30
        }
        
        return kpis


# Singleton instance
_analytics_orchestrator = None

def get_analytics_orchestrator() -> AdvancedAnalyticsOrchestrator:
    """Get the global analytics orchestrator instance."""
    global _analytics_orchestrator
    if _analytics_orchestrator is None:
        _analytics_orchestrator = AdvancedAnalyticsOrchestrator()
    return _analytics_orchestrator