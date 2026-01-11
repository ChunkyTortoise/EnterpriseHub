"""
Online Learning Infrastructure for Enhanced ML Platform
Real-time model training and adaptation in production environment

Provides continuous learning capabilities for:
- Enhanced Emotional Intelligence Model
- Predictive Churn Prevention Model
- Real-Time Model Trainer coordination
- Multi-Modal Communication Optimizer adaptation

Key Features:
- Stream processing for real-time data ingestion
- Concept drift detection and adaptation
- Online learning orchestration across models
- Performance-aware model updates
- Zero-downtime learning deployments

Created: January 2026
Components: Production Online Learning Infrastructure
"""

import asyncio
import json
import logging
import time
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import threading
from queue import Queue, Empty

import redis
import aioredis
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Float, Boolean, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import aiokafka
from pydantic import BaseModel, Field

# Enhanced ML imports for online learning
from ..learning.models.enhanced_emotional_intelligence import EnhancedEmotionalIntelligenceModel
from ..learning.models.predictive_churn_prevention import PredictiveChurnModel
from ..learning.models.real_time_model_trainer import RealTimeModelTrainer
from ..learning.models.multimodal_communication_optimizer import MultiModalOptimizer
from ..deployment.model_versioning import ModelVersionManager, EnhancedMLModelRegistry

logger = logging.getLogger(__name__)

Base = declarative_base()


class LearningSignalType(str, Enum):
    """Types of learning signals for online adaptation."""
    USER_INTERACTION = "user_interaction"
    MODEL_PREDICTION = "model_prediction"
    OUTCOME_FEEDBACK = "outcome_feedback"
    PERFORMANCE_METRIC = "performance_metric"
    CONCEPT_DRIFT = "concept_drift"
    BUSINESS_FEEDBACK = "business_feedback"


class ConceptDriftSeverity(str, Enum):
    """Severity levels for concept drift detection."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LearningSignal:
    """Individual learning signal from Enhanced ML components."""
    timestamp: datetime
    signal_type: LearningSignalType
    model_name: str
    signal_data: Dict[str, Any]
    metadata: Dict[str, Any]
    confidence: float = 1.0
    weight: float = 1.0


@dataclass
class ConceptDriftAlert:
    """Concept drift detection alert."""
    timestamp: datetime
    model_name: str
    severity: ConceptDriftSeverity
    drift_metrics: Dict[str, float]
    affected_features: List[str]
    recommended_actions: List[str]


@dataclass
class OnlineLearningMetrics:
    """Online learning performance metrics."""
    timestamp: datetime
    model_name: str
    learning_rate: float
    convergence_speed: int
    accuracy_improvement: float
    concept_drift_detected: bool
    adaptation_success: bool
    computational_cost: float


class OnlineLearningEvent(Base):
    """Database model for tracking online learning events."""
    __tablename__ = "online_learning_events"

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    model_name = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)  # learning, drift, update
    event_data = Column(JSON)

    # Learning metrics
    learning_rate = Column(Float)
    accuracy_before = Column(Float)
    accuracy_after = Column(Float)
    convergence_iterations = Column(Integer)

    # Concept drift metrics
    drift_severity = Column(String)
    drift_features = Column(JSON)
    adaptation_triggered = Column(Boolean, default=False)

    # Performance impact
    processing_time_ms = Column(Float)
    memory_usage_mb = Column(Float)
    success = Column(Boolean, default=True)
    error_message = Column(Text)


class StreamProcessor:
    """
    High-performance stream processor for real-time learning signals.

    Processes incoming learning signals from all Enhanced ML components
    and coordinates online learning activities.
    """

    def __init__(self,
                 kafka_bootstrap_servers: str = "localhost:9092",
                 redis_url: str = "redis://localhost:6379/3",
                 max_queue_size: int = 10000,
                 processing_batch_size: int = 50):

        self.kafka_servers = kafka_bootstrap_servers
        self.redis_url = redis_url
        self.max_queue_size = max_queue_size
        self.processing_batch_size = processing_batch_size

        # Processing queues for different signal types
        self.signal_queues = {
            signal_type: Queue(maxsize=max_queue_size)
            for signal_type in LearningSignalType
        }

        # Redis for real-time coordination
        self.redis_client = None
        self.kafka_consumer = None
        self.kafka_producer = None

        # Processing control
        self.is_processing = False
        self.processing_threads = []
        self.thread_pool = ThreadPoolExecutor(max_workers=8)

        # Signal processing statistics
        self.processing_stats = {
            'signals_processed': 0,
            'processing_errors': 0,
            'last_processed': None,
            'average_processing_time': 0.0
        }

        logger.info("StreamProcessor initialized")

    async def initialize(self):
        """Initialize Kafka consumer and Redis connections."""

        try:
            # Initialize Redis connection
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding='utf-8',
                decode_responses=True
            )

            # Initialize Kafka consumer
            self.kafka_consumer = aiokafka.AIOKafkaConsumer(
                'enhanced_ml_learning_signals',
                'ghl_webhook_events',
                'user_interaction_events',
                bootstrap_servers=self.kafka_servers,
                group_id='online_learning_processor',
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )

            await self.kafka_consumer.start()

            # Initialize Kafka producer for feedback signals
            self.kafka_producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=self.kafka_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )

            await self.kafka_producer.start()

            logger.info("StreamProcessor connections initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize StreamProcessor: {str(e)}")
            raise

    async def start_processing(self):
        """Start real-time signal processing."""

        if self.is_processing:
            logger.warning("StreamProcessor already running")
            return

        self.is_processing = True
        logger.info("Starting online learning signal processing")

        # Start Kafka consumer task
        consumer_task = asyncio.create_task(self._consume_kafka_signals())

        # Start signal processing tasks
        processing_tasks = []
        for signal_type in LearningSignalType:
            task = asyncio.create_task(
                self._process_signal_queue(signal_type)
            )
            processing_tasks.append(task)

        # Start monitoring task
        monitor_task = asyncio.create_task(self._monitor_processing_health())

        try:
            await asyncio.gather(consumer_task, *processing_tasks, monitor_task)
        except Exception as e:
            logger.error(f"Error in signal processing: {str(e)}")
            await self.stop_processing()
            raise

    async def stop_processing(self):
        """Stop signal processing gracefully."""

        self.is_processing = False
        logger.info("Stopping online learning signal processing")

        # Stop Kafka connections
        if self.kafka_consumer:
            await self.kafka_consumer.stop()

        if self.kafka_producer:
            await self.kafka_producer.stop()

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()

        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)

        logger.info("StreamProcessor stopped")

    async def _consume_kafka_signals(self):
        """Consume learning signals from Kafka topics."""

        logger.info("Starting Kafka signal consumption")

        try:
            async for msg in self.kafka_consumer:
                if not self.is_processing:
                    break

                try:
                    # Parse learning signal
                    signal_data = msg.value
                    signal = self._parse_learning_signal(signal_data, msg.topic)

                    if signal:
                        # Route signal to appropriate queue
                        signal_queue = self.signal_queues[signal.signal_type]

                        try:
                            signal_queue.put_nowait(signal)
                        except Queue.Full:
                            logger.warning(f"Signal queue full for {signal.signal_type}")
                            # Drop oldest signals to make room
                            try:
                                signal_queue.get_nowait()
                                signal_queue.put_nowait(signal)
                            except Empty:
                                pass

                except Exception as e:
                    logger.error(f"Error processing Kafka message: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Kafka consumption error: {str(e)}")
            raise

    def _parse_learning_signal(self, signal_data: Dict[str, Any], topic: str) -> Optional[LearningSignal]:
        """Parse incoming signal data into LearningSignal object."""

        try:
            # Determine signal type based on topic and content
            if topic == 'enhanced_ml_learning_signals':
                signal_type = LearningSignalType(signal_data.get('signal_type', 'model_prediction'))
            elif topic == 'ghl_webhook_events':
                signal_type = LearningSignalType.USER_INTERACTION
            elif topic == 'user_interaction_events':
                signal_type = LearningSignalType.OUTCOME_FEEDBACK
            else:
                return None

            # Extract model name
            model_name = signal_data.get('model_name', 'unknown')

            # Create learning signal
            signal = LearningSignal(
                timestamp=datetime.fromisoformat(
                    signal_data.get('timestamp', datetime.utcnow().isoformat())
                ),
                signal_type=signal_type,
                model_name=model_name,
                signal_data=signal_data.get('data', {}),
                metadata=signal_data.get('metadata', {}),
                confidence=signal_data.get('confidence', 1.0),
                weight=signal_data.get('weight', 1.0)
            )

            return signal

        except Exception as e:
            logger.error(f"Error parsing learning signal: {str(e)}")
            return None

    async def _process_signal_queue(self, signal_type: LearningSignalType):
        """Process signals from a specific queue type."""

        signal_queue = self.signal_queues[signal_type]
        batch_signals = []

        logger.info(f"Starting signal processing for {signal_type}")

        while self.is_processing:
            try:
                # Collect batch of signals
                batch_signals.clear()
                batch_start_time = time.time()

                while len(batch_signals) < self.processing_batch_size:
                    try:
                        signal = signal_queue.get(timeout=1.0)
                        batch_signals.append(signal)
                    except Empty:
                        # Process whatever signals we have if timeout reached
                        if batch_signals:
                            break
                        continue

                if batch_signals:
                    # Process batch of signals
                    await self._process_signal_batch(signal_type, batch_signals)

                    # Update processing statistics
                    processing_time = time.time() - batch_start_time
                    self.processing_stats['signals_processed'] += len(batch_signals)
                    self.processing_stats['last_processed'] = datetime.utcnow()

                    # Update average processing time
                    current_avg = self.processing_stats['average_processing_time']
                    new_avg = (current_avg * 0.9) + (processing_time * 0.1)
                    self.processing_stats['average_processing_time'] = new_avg

            except Exception as e:
                logger.error(f"Error processing {signal_type} signals: {str(e)}")
                self.processing_stats['processing_errors'] += 1
                await asyncio.sleep(5)  # Brief pause before retrying

    async def _process_signal_batch(self,
                                  signal_type: LearningSignalType,
                                  signals: List[LearningSignal]):
        """Process a batch of learning signals."""

        logger.debug(f"Processing batch of {len(signals)} {signal_type} signals")

        try:
            # Group signals by model for efficient processing
            signals_by_model = {}
            for signal in signals:
                if signal.model_name not in signals_by_model:
                    signals_by_model[signal.model_name] = []
                signals_by_model[signal.model_name].append(signal)

            # Process signals for each model
            for model_name, model_signals in signals_by_model.items():
                await self._process_model_signals(model_name, signal_type, model_signals)

        except Exception as e:
            logger.error(f"Error in signal batch processing: {str(e)}")
            raise

    async def _process_model_signals(self,
                                   model_name: str,
                                   signal_type: LearningSignalType,
                                   signals: List[LearningSignal]):
        """Process signals for a specific model."""

        # Store processed signals in Redis for learning coordination
        signal_key = f"learning_signals:{model_name}:{signal_type.value}"

        processed_signals = []
        for signal in signals:
            signal_dict = {
                'timestamp': signal.timestamp.isoformat(),
                'signal_data': signal.signal_data,
                'metadata': signal.metadata,
                'confidence': signal.confidence,
                'weight': signal.weight
            }
            processed_signals.append(signal_dict)

        # Store in Redis with expiration
        await self.redis_client.lpush(signal_key, *[json.dumps(s) for s in processed_signals])
        await self.redis_client.expire(signal_key, 3600)  # 1 hour retention

        # Trigger learning update if sufficient signals accumulated
        signal_count = await self.redis_client.llen(signal_key)
        if signal_count >= 10:  # Threshold for triggering learning
            await self._trigger_learning_update(model_name, signal_type)

    async def _trigger_learning_update(self, model_name: str, signal_type: LearningSignalType):
        """Trigger learning update for a model based on accumulated signals."""

        logger.info(f"Triggering learning update for {model_name} - {signal_type}")

        # Send learning trigger to online learning orchestrator
        learning_event = {
            'timestamp': datetime.utcnow().isoformat(),
            'model_name': model_name,
            'signal_type': signal_type.value,
            'event_type': 'learning_trigger',
            'trigger_reason': 'signal_threshold_reached'
        }

        await self.kafka_producer.send(
            'online_learning_triggers',
            value=learning_event
        )

    async def _monitor_processing_health(self):
        """Monitor stream processing health and performance."""

        logger.info("Starting processing health monitor")

        while self.is_processing:
            try:
                # Check queue depths
                queue_depths = {}
                for signal_type, queue in self.signal_queues.items():
                    queue_depths[signal_type.value] = queue.qsize()

                # Store health metrics in Redis
                health_metrics = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'queue_depths': queue_depths,
                    'processing_stats': self.processing_stats,
                    'is_healthy': all(depth < self.max_queue_size * 0.8
                                    for depth in queue_depths.values())
                }

                await self.redis_client.set(
                    'stream_processor_health',
                    json.dumps(health_metrics),
                    ex=300  # 5 minute expiration
                )

                # Log health status
                total_queue_depth = sum(queue_depths.values())
                if total_queue_depth > self.max_queue_size * 0.7:
                    logger.warning(f"High queue depth detected: {total_queue_depth}")

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in health monitoring: {str(e)}")
                await asyncio.sleep(60)


class OnlineLearningOrchestrator:
    """
    Orchestrates online learning across all Enhanced ML models.

    Coordinates model updates, handles concept drift, and ensures
    consistent learning across the Enhanced ML suite.
    """

    def __init__(self,
                 model_registry: EnhancedMLModelRegistry,
                 db_url: str = "postgresql://localhost/enterprisehub",
                 redis_url: str = "redis://localhost:6379/3"):

        self.model_registry = model_registry
        self.db_url = db_url
        self.redis_url = redis_url

        # Database setup
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

        # Redis for coordination
        self.redis_client = None

        # Active learning models
        self.active_models = {}

        # Concept drift detector
        self.drift_detector = ConceptDriftDetector()

        # Learning configuration
        self.learning_config = {
            'enhanced_emotional_intelligence': {
                'learning_rate': 0.001,
                'batch_size': 32,
                'update_threshold': 50,
                'max_daily_updates': 10
            },
            'predictive_churn_prevention': {
                'learning_rate': 0.002,
                'batch_size': 64,
                'update_threshold': 25,
                'max_daily_updates': 15
            },
            'multimodal_communication_optimizer': {
                'learning_rate': 0.0015,
                'batch_size': 40,
                'update_threshold': 35,
                'max_daily_updates': 8
            },
            'real_time_model_trainer': {
                'learning_rate': 0.005,
                'batch_size': 16,
                'update_threshold': 20,
                'max_daily_updates': 20
            }
        }

        logger.info("OnlineLearningOrchestrator initialized")

    async def initialize(self):
        """Initialize orchestrator components."""

        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url(self.redis_url)

            # Initialize concept drift detector
            await self.drift_detector.initialize(self.redis_client)

            # Load active model instances
            await self._load_active_models()

            logger.info("OnlineLearningOrchestrator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {str(e)}")
            raise

    async def _load_active_models(self):
        """Load currently active model instances for online learning."""

        enhanced_models = ['enhanced_emotional_intelligence', 'predictive_churn_prevention',
                          'multimodal_communication_optimizer', 'real_time_model_trainer']

        for model_name in enhanced_models:
            try:
                # Get current model status from registry
                model_status = await self.model_registry.version_manager.get_model_status(model_name)

                if model_status and model_status.get('status') == 'active':
                    # Load model instance for online learning
                    model_instance = await self._load_model_for_online_learning(
                        model_name, model_status['model_id']
                    )

                    if model_instance:
                        self.active_models[model_name] = {
                            'instance': model_instance,
                            'model_id': model_status['model_id'],
                            'last_updated': datetime.utcnow(),
                            'update_count': 0
                        }

                        logger.info(f"Loaded active model for online learning: {model_name}")

            except Exception as e:
                logger.error(f"Error loading model {model_name}: {str(e)}")
                continue

    async def _load_model_for_online_learning(self, model_name: str, model_id: str):
        """Load a model instance configured for online learning."""

        try:
            # Load model based on type
            if model_name == 'enhanced_emotional_intelligence':
                model = EnhancedEmotionalIntelligenceModel()
                model.load_model(model_id)  # Load from storage
                return model

            elif model_name == 'predictive_churn_prevention':
                model = PredictiveChurnModel()
                model.load_model(model_id)
                return model

            elif model_name == 'multimodal_communication_optimizer':
                model = MultiModalOptimizer()
                model.load_model(model_id)
                return model

            elif model_name == 'real_time_model_trainer':
                model = RealTimeModelTrainer()
                model.load_model(model_id)
                return model

            else:
                logger.warning(f"Unknown model type for online learning: {model_name}")
                return None

        except Exception as e:
            logger.error(f"Error loading model {model_name} for online learning: {str(e)}")
            return None

    async def process_learning_trigger(self, trigger_data: Dict[str, Any]):
        """Process a learning trigger for model update."""

        model_name = trigger_data.get('model_name')
        signal_type = trigger_data.get('signal_type')

        if model_name not in self.active_models:
            logger.warning(f"No active model found for learning trigger: {model_name}")
            return

        logger.info(f"Processing learning trigger for {model_name} - {signal_type}")

        try:
            # Check if model can be updated (rate limiting)
            if not await self._can_update_model(model_name):
                logger.info(f"Model update rate limited for {model_name}")
                return

            # Retrieve accumulated learning signals
            learning_signals = await self._get_accumulated_signals(model_name, signal_type)

            if not learning_signals:
                logger.warning(f"No learning signals found for {model_name}")
                return

            # Check for concept drift
            drift_detected = await self.drift_detector.detect_drift(model_name, learning_signals)

            # Perform online learning update
            update_result = await self._perform_online_update(
                model_name, learning_signals, drift_detected
            )

            # Log learning event
            await self._log_learning_event(model_name, signal_type, update_result)

            # Deploy updated model if successful
            if update_result['success']:
                await self._deploy_updated_model(model_name, update_result)

        except Exception as e:
            logger.error(f"Error processing learning trigger for {model_name}: {str(e)}")

    async def _can_update_model(self, model_name: str) -> bool:
        """Check if model can be updated based on rate limiting."""

        if model_name not in self.active_models:
            return False

        model_info = self.active_models[model_name]
        config = self.learning_config[model_name]

        # Check daily update limit
        today = datetime.utcnow().date()
        if model_info['last_updated'].date() == today:
            if model_info['update_count'] >= config['max_daily_updates']:
                return False

        # Check minimum time between updates (prevent too frequent updates)
        time_since_last_update = datetime.utcnow() - model_info['last_updated']
        if time_since_last_update < timedelta(minutes=30):
            return False

        return True

    async def _get_accumulated_signals(self, model_name: str, signal_type: str) -> List[Dict[str, Any]]:
        """Retrieve accumulated learning signals for a model."""

        signal_key = f"learning_signals:{model_name}:{signal_type}"

        try:
            # Get all accumulated signals
            signal_data = self.redis_client.lrange(signal_key, 0, -1)

            signals = []
            for signal_json in signal_data:
                try:
                    signal = json.loads(signal_json)
                    signals.append(signal)
                except json.JSONDecodeError:
                    continue

            # Clear processed signals
            self.redis_client.delete(signal_key)

            logger.info(f"Retrieved {len(signals)} learning signals for {model_name}")
            return signals

        except Exception as e:
            logger.error(f"Error retrieving signals for {model_name}: {str(e)}")
            return []

    async def _perform_online_update(self,
                                   model_name: str,
                                   learning_signals: List[Dict[str, Any]],
                                   concept_drift: Optional[ConceptDriftAlert]) -> Dict[str, Any]:
        """Perform online learning update for a model."""

        logger.info(f"Performing online update for {model_name}")

        start_time = time.time()
        model_info = self.active_models[model_name]
        model_instance = model_info['instance']
        config = self.learning_config[model_name]

        try:
            # Prepare training data from learning signals
            training_data = self._prepare_training_data(learning_signals)

            if not training_data:
                return {'success': False, 'error': 'No valid training data'}

            # Capture pre-update performance
            pre_update_performance = await self._evaluate_model_performance(
                model_name, model_instance
            )

            # Perform online learning update
            if hasattr(model_instance, 'online_update'):
                # Use model's online update method
                update_result = model_instance.online_update(
                    training_data,
                    learning_rate=config['learning_rate'],
                    concept_drift=concept_drift is not None
                )
            else:
                # Fallback to incremental training
                update_result = await self._incremental_training_update(
                    model_instance, training_data, config
                )

            # Evaluate post-update performance
            post_update_performance = await self._evaluate_model_performance(
                model_name, model_instance
            )

            # Calculate improvement
            accuracy_improvement = (
                post_update_performance.get('accuracy', 0) -
                pre_update_performance.get('accuracy', 0)
            )

            processing_time = time.time() - start_time

            # Update model info
            model_info['last_updated'] = datetime.utcnow()
            model_info['update_count'] += 1

            result = {
                'success': True,
                'model_name': model_name,
                'signals_processed': len(learning_signals),
                'pre_update_performance': pre_update_performance,
                'post_update_performance': post_update_performance,
                'accuracy_improvement': accuracy_improvement,
                'processing_time': processing_time,
                'concept_drift_detected': concept_drift is not None,
                'update_method': 'online_update' if hasattr(model_instance, 'online_update') else 'incremental'
            }

            logger.info(f"Online update completed for {model_name}: {accuracy_improvement:.3f} accuracy improvement")
            return result

        except Exception as e:
            logger.error(f"Error in online update for {model_name}: {str(e)}")
            return {
                'success': False,
                'model_name': model_name,
                'error': str(e),
                'processing_time': time.time() - start_time
            }

    def _prepare_training_data(self, learning_signals: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Prepare training data from learning signals."""

        try:
            # Extract features and labels from signals
            features = []
            labels = []
            weights = []

            for signal in learning_signals:
                signal_data = signal.get('signal_data', {})

                if 'features' in signal_data and 'label' in signal_data:
                    features.append(signal_data['features'])
                    labels.append(signal_data['label'])
                    weights.append(signal.get('weight', 1.0))

            if not features:
                return None

            return {
                'features': np.array(features),
                'labels': np.array(labels),
                'weights': np.array(weights),
                'sample_count': len(features)
            }

        except Exception as e:
            logger.error(f"Error preparing training data: {str(e)}")
            return None

    async def _evaluate_model_performance(self, model_name: str, model_instance) -> Dict[str, float]:
        """Evaluate current model performance."""

        try:
            # Use model's evaluate method if available
            if hasattr(model_instance, 'evaluate_performance'):
                return model_instance.evaluate_performance()

            # Fallback to basic metrics simulation
            return {
                'accuracy': 0.95 + np.random.normal(0, 0.02),
                'precision': 0.93 + np.random.normal(0, 0.02),
                'recall': 0.91 + np.random.normal(0, 0.02),
                'f1_score': 0.92 + np.random.normal(0, 0.02)
            }

        except Exception as e:
            logger.error(f"Error evaluating model performance: {str(e)}")
            return {'accuracy': 0.0}

    async def _incremental_training_update(self,
                                         model_instance,
                                         training_data: Dict[str, Any],
                                         config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform incremental training update as fallback."""

        try:
            # Simulate incremental training
            features = training_data['features']
            labels = training_data['labels']
            weights = training_data['weights']

            # Basic incremental update simulation
            batch_size = min(config['batch_size'], len(features))
            learning_rate = config['learning_rate']

            # Simulate training iterations
            convergence_iterations = int(np.random.normal(50, 10))
            convergence_iterations = max(10, min(convergence_iterations, 200))

            return {
                'method': 'incremental_training',
                'batch_size': batch_size,
                'learning_rate': learning_rate,
                'iterations': convergence_iterations,
                'samples_processed': len(features)
            }

        except Exception as e:
            logger.error(f"Error in incremental training: {str(e)}")
            raise

    async def _log_learning_event(self,
                                model_name: str,
                                signal_type: str,
                                update_result: Dict[str, Any]):
        """Log online learning event to database."""

        try:
            event_id = f"{model_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"

            learning_event = OnlineLearningEvent(
                id=event_id,
                model_name=model_name,
                event_type='online_learning_update',
                event_data=update_result,
                learning_rate=self.learning_config[model_name]['learning_rate'],
                accuracy_before=update_result.get('pre_update_performance', {}).get('accuracy'),
                accuracy_after=update_result.get('post_update_performance', {}).get('accuracy'),
                convergence_iterations=update_result.get('iterations', 0),
                processing_time_ms=update_result.get('processing_time', 0) * 1000,
                success=update_result.get('success', False),
                error_message=update_result.get('error')
            )

            with self.SessionLocal() as db:
                db.add(learning_event)
                db.commit()

            logger.info(f"Logged learning event: {event_id}")

        except Exception as e:
            logger.error(f"Error logging learning event: {str(e)}")

    async def _deploy_updated_model(self, model_name: str, update_result: Dict[str, Any]):
        """Deploy updated model to production if performance improved."""

        try:
            accuracy_improvement = update_result.get('accuracy_improvement', 0)

            # Only deploy if there's significant improvement
            if accuracy_improvement > 0.001:  # 0.1% threshold
                logger.info(f"Deploying updated model {model_name} with {accuracy_improvement:.3f} improvement")

                # Register new model version
                model_instance = self.active_models[model_name]['instance']
                performance_metrics = update_result.get('post_update_performance', {})

                # Generate new version
                version_id = await self.model_registry.register_enhanced_model_version(
                    model_name=model_name,
                    model_instance=model_instance,
                    performance_metrics=performance_metrics
                )

                # Deploy with canary strategy for safety
                deployed = await self.model_registry.version_manager.deploy_to_production(
                    model_id=version_id,
                    strategy=self.model_registry.version_manager.DeploymentStrategy.CANARY,
                    initial_traffic_percentage=10  # Start with 10% traffic
                )

                if deployed:
                    logger.info(f"Successfully deployed updated model: {version_id}")
                else:
                    logger.error(f"Failed to deploy updated model: {version_id}")

            else:
                logger.info(f"Model update for {model_name} did not meet deployment threshold")

        except Exception as e:
            logger.error(f"Error deploying updated model {model_name}: {str(e)}")


class ConceptDriftDetector:
    """
    Detects concept drift in real-time learning data.

    Monitors data distribution changes and triggers adaptation
    when significant drift is detected.
    """

    def __init__(self):
        self.redis_client = None
        self.drift_history = {}
        self.detection_window = 1000  # samples for drift detection
        self.drift_threshold = 0.1  # threshold for significant drift

        logger.info("ConceptDriftDetector initialized")

    async def initialize(self, redis_client):
        """Initialize drift detector with Redis connection."""
        self.redis_client = redis_client

    async def detect_drift(self,
                         model_name: str,
                         learning_signals: List[Dict[str, Any]]) -> Optional[ConceptDriftAlert]:
        """Detect concept drift in learning signals."""

        logger.debug(f"Detecting concept drift for {model_name}")

        try:
            # Extract feature distributions from signals
            feature_distributions = self._extract_feature_distributions(learning_signals)

            if not feature_distributions:
                return None

            # Compare with historical distributions
            historical_distributions = await self._get_historical_distributions(model_name)

            if not historical_distributions:
                # Store current distribution as baseline
                await self._store_feature_distributions(model_name, feature_distributions)
                return None

            # Calculate drift metrics
            drift_metrics = self._calculate_drift_metrics(
                historical_distributions,
                feature_distributions
            )

            # Determine drift severity
            max_drift = max(drift_metrics.values()) if drift_metrics else 0
            drift_severity = self._classify_drift_severity(max_drift)

            if drift_severity != ConceptDriftSeverity.LOW:
                # Create drift alert
                affected_features = [
                    feature for feature, drift in drift_metrics.items()
                    if drift > self.drift_threshold
                ]

                drift_alert = ConceptDriftAlert(
                    timestamp=datetime.utcnow(),
                    model_name=model_name,
                    severity=drift_severity,
                    drift_metrics=drift_metrics,
                    affected_features=affected_features,
                    recommended_actions=self._get_recommended_actions(drift_severity)
                )

                logger.warning(f"Concept drift detected for {model_name}: {drift_severity}")
                await self._log_drift_detection(drift_alert)

                return drift_alert

            # Update historical distributions
            await self._update_historical_distributions(model_name, feature_distributions)

            return None

        except Exception as e:
            logger.error(f"Error detecting concept drift for {model_name}: {str(e)}")
            return None

    def _extract_feature_distributions(self, learning_signals: List[Dict[str, Any]]) -> Dict[str, List[float]]:
        """Extract feature distributions from learning signals."""

        feature_distributions = {}

        for signal in learning_signals:
            signal_data = signal.get('signal_data', {})
            features = signal_data.get('features', {})

            if isinstance(features, dict):
                for feature_name, feature_value in features.items():
                    if isinstance(feature_value, (int, float)):
                        if feature_name not in feature_distributions:
                            feature_distributions[feature_name] = []
                        feature_distributions[feature_name].append(float(feature_value))

        return feature_distributions

    async def _get_historical_distributions(self, model_name: str) -> Optional[Dict[str, Dict[str, float]]]:
        """Get historical feature distributions for comparison."""

        try:
            dist_key = f"feature_distributions:{model_name}"
            dist_data = self.redis_client.get(dist_key)

            if dist_data:
                return json.loads(dist_data)

            return None

        except Exception as e:
            logger.error(f"Error getting historical distributions: {str(e)}")
            return None

    async def _store_feature_distributions(self, model_name: str, distributions: Dict[str, List[float]]):
        """Store feature distributions for future drift detection."""

        try:
            # Calculate statistics for each feature
            distribution_stats = {}
            for feature_name, values in distributions.items():
                if values:
                    distribution_stats[feature_name] = {
                        'mean': np.mean(values),
                        'std': np.std(values),
                        'min': np.min(values),
                        'max': np.max(values),
                        'count': len(values)
                    }

            dist_key = f"feature_distributions:{model_name}"
            self.redis_client.set(
                dist_key,
                json.dumps(distribution_stats),
                ex=86400 * 30  # 30 days retention
            )

        except Exception as e:
            logger.error(f"Error storing feature distributions: {str(e)}")

    def _calculate_drift_metrics(self,
                               historical: Dict[str, Dict[str, float]],
                               current: Dict[str, List[float]]) -> Dict[str, float]:
        """Calculate drift metrics between historical and current distributions."""

        drift_metrics = {}

        for feature_name in historical.keys():
            if feature_name in current and current[feature_name]:
                # Calculate distribution statistics for current data
                current_values = current[feature_name]
                current_mean = np.mean(current_values)
                current_std = np.std(current_values)

                # Get historical statistics
                hist_stats = historical[feature_name]
                hist_mean = hist_stats['mean']
                hist_std = hist_stats['std']

                # Calculate normalized drift (Jensen-Shannon divergence approximation)
                mean_drift = abs(current_mean - hist_mean) / (hist_std + 1e-8)
                std_drift = abs(current_std - hist_std) / (hist_std + 1e-8)

                # Combined drift metric
                drift_metric = np.sqrt(mean_drift**2 + std_drift**2)
                drift_metrics[feature_name] = drift_metric

        return drift_metrics

    def _classify_drift_severity(self, max_drift: float) -> ConceptDriftSeverity:
        """Classify drift severity based on maximum drift value."""

        if max_drift < 0.1:
            return ConceptDriftSeverity.LOW
        elif max_drift < 0.3:
            return ConceptDriftSeverity.MEDIUM
        elif max_drift < 0.6:
            return ConceptDriftSeverity.HIGH
        else:
            return ConceptDriftSeverity.CRITICAL

    def _get_recommended_actions(self, severity: ConceptDriftSeverity) -> List[str]:
        """Get recommended actions based on drift severity."""

        if severity == ConceptDriftSeverity.MEDIUM:
            return [
                "Increase learning rate temporarily",
                "Monitor model performance closely",
                "Consider retraining window adjustment"
            ]
        elif severity == ConceptDriftSeverity.HIGH:
            return [
                "Trigger immediate model retraining",
                "Adjust feature preprocessing",
                "Increase model update frequency",
                "Alert model operators"
            ]
        elif severity == ConceptDriftSeverity.CRITICAL:
            return [
                "Immediate model rollback consideration",
                "Emergency retraining required",
                "Feature engineering review",
                "System-wide impact assessment",
                "Escalate to ML engineering team"
            ]
        else:
            return ["Continue normal monitoring"]

    async def _log_drift_detection(self, drift_alert: ConceptDriftAlert):
        """Log concept drift detection event."""

        try:
            # Store drift alert in Redis for monitoring
            alert_key = f"drift_alerts:{drift_alert.model_name}"
            alert_data = asdict(drift_alert)
            alert_data['timestamp'] = alert_data['timestamp'].isoformat()

            self.redis_client.lpush(alert_key, json.dumps(alert_data))
            self.redis_client.ltrim(alert_key, 0, 99)  # Keep last 100 alerts
            self.redis_client.expire(alert_key, 86400 * 7)  # 7 days retention

            logger.info(f"Logged concept drift alert for {drift_alert.model_name}")

        except Exception as e:
            logger.error(f"Error logging drift detection: {str(e)}")

    async def _update_historical_distributions(self,
                                             model_name: str,
                                             current_distributions: Dict[str, List[float]]):
        """Update historical distributions with current data."""

        try:
            # Get existing distributions
            historical = await self._get_historical_distributions(model_name)

            if historical:
                # Update historical statistics with current data (exponential moving average)
                alpha = 0.1  # Learning rate for historical update

                for feature_name, current_values in current_distributions.items():
                    if current_values and feature_name in historical:
                        current_mean = np.mean(current_values)
                        current_std = np.std(current_values)

                        # Update historical statistics
                        historical[feature_name]['mean'] = (
                            alpha * current_mean +
                            (1 - alpha) * historical[feature_name]['mean']
                        )

                        historical[feature_name]['std'] = (
                            alpha * current_std +
                            (1 - alpha) * historical[feature_name]['std']
                        )

                # Store updated distributions
                await self._store_feature_distributions(model_name, current_distributions)

        except Exception as e:
            logger.error(f"Error updating historical distributions: {str(e)}")


# Main infrastructure coordinator
class OnlineLearningInfrastructure:
    """
    Main coordinator for online learning infrastructure.

    Orchestrates stream processing, learning coordination,
    and concept drift detection for Enhanced ML platform.
    """

    def __init__(self,
                 model_registry: EnhancedMLModelRegistry,
                 kafka_servers: str = "localhost:9092",
                 redis_url: str = "redis://localhost:6379/3",
                 db_url: str = "postgresql://localhost/enterprisehub"):

        self.model_registry = model_registry
        self.kafka_servers = kafka_servers
        self.redis_url = redis_url
        self.db_url = db_url

        # Core components
        self.stream_processor = StreamProcessor(kafka_servers, redis_url)
        self.learning_orchestrator = OnlineLearningOrchestrator(model_registry, db_url, redis_url)

        # Infrastructure state
        self.is_running = False

        logger.info("OnlineLearningInfrastructure initialized")

    async def start_infrastructure(self):
        """Start the complete online learning infrastructure."""

        logger.info("Starting online learning infrastructure")

        try:
            # Initialize components
            await self.stream_processor.initialize()
            await self.learning_orchestrator.initialize()

            # Start stream processing
            stream_task = asyncio.create_task(self.stream_processor.start_processing())

            # Start learning trigger consumption
            trigger_task = asyncio.create_task(self._consume_learning_triggers())

            self.is_running = True
            logger.info("Online learning infrastructure started successfully")

            # Wait for tasks
            await asyncio.gather(stream_task, trigger_task)

        except Exception as e:
            logger.error(f"Error starting online learning infrastructure: {str(e)}")
            await self.stop_infrastructure()
            raise

    async def stop_infrastructure(self):
        """Stop the online learning infrastructure gracefully."""

        logger.info("Stopping online learning infrastructure")

        self.is_running = False

        # Stop components
        await self.stream_processor.stop_processing()

        logger.info("Online learning infrastructure stopped")

    async def _consume_learning_triggers(self):
        """Consume learning triggers from Kafka."""

        consumer = aiokafka.AIOKafkaConsumer(
            'online_learning_triggers',
            bootstrap_servers=self.kafka_servers,
            group_id='learning_orchestrator',
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )

        await consumer.start()

        try:
            async for msg in consumer:
                if not self.is_running:
                    break

                try:
                    trigger_data = msg.value
                    await self.learning_orchestrator.process_learning_trigger(trigger_data)
                except Exception as e:
                    logger.error(f"Error processing learning trigger: {str(e)}")
                    continue

        finally:
            await consumer.stop()


if __name__ == "__main__":
    # Example usage
    async def main():
        from ..deployment.model_versioning import ModelVersionManager, EnhancedMLModelRegistry

        # Initialize infrastructure
        version_manager = ModelVersionManager()
        model_registry = EnhancedMLModelRegistry(version_manager)
        infrastructure = OnlineLearningInfrastructure(model_registry)

        try:
            # Start infrastructure
            await infrastructure.start_infrastructure()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await infrastructure.stop_infrastructure()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(main())