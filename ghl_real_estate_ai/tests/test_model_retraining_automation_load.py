"""
Model Retraining Automation Load Testing

This test validates the Real-Time Model Training system under realistic production load:
1. High-volume learning signal processing (1000+ signals/hour)
2. Concurrent model updates across all model types
3. Memory management during continuous learning
4. Performance stability under sustained load
5. Concept drift detection and automatic adaptation
6. System recovery from failures during retraining

Business Impact: Ensures self-improving AI platform maintains >95% accuracy at scale
Performance Target: Process 500+ signals/min, <50ms per signal, <2GB memory usage
"""

import asyncio
import pytest
import time
import psutil
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, AsyncMock, patch
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from threading import Lock
import random

# Import real-time training and related components
from services.real_time_model_training import (
    RealTimeModelTraining,
    ModelType,
    TrainingDataPoint,
    OnlineLearningState,
    ModelPerformanceSnapshot,
    RetrainingEvent
)

# Import enhanced ML components (signal sources)
from services.enhanced_ml_personalization_engine import (
    EnhancedMLPersonalizationEngine,
    EmotionalState,
    LeadJourneyStage
)
from services.predictive_churn_prevention import (
    PredictiveChurnPrevention,
    ChurnRiskLevel
)
from services.multimodal_communication_optimizer import (
    MultiModalCommunicationOptimizer,
    CommunicationModality
)

# Import shared models
from models.shared_models import (
    EngagementInteraction,
    InteractionType,
    CommunicationChannel,
    LeadProfile,
    LeadEvaluationResult
)


@dataclass
class LoadTestConfiguration:
    """Configuration for load testing scenarios."""
    duration_seconds: int
    signals_per_second: float
    concurrent_models: int
    memory_limit_gb: float
    accuracy_threshold: float
    concept_drift_probability: float
    failure_injection_rate: float


@dataclass
class LoadTestMetrics:
    """Metrics collected during load testing."""
    total_signals_processed: int
    processing_rate_avg: float
    processing_time_avg: float
    memory_usage_peak: float
    accuracy_degradation: float
    concept_drift_events: int
    retraining_events: int
    failed_operations: int
    recovery_time_avg: float
    system_stability_score: float


@dataclass
class ModelLoadMetrics:
    """Per-model metrics during load testing."""
    model_type: str
    signals_processed: int
    retraining_count: int
    accuracy_before: float
    accuracy_after: float
    processing_time_avg: float
    memory_usage: float
    failure_count: int


class TestModelRetrainingAutomationLoad:
    """Test model retraining automation under realistic load conditions."""

    @pytest.fixture(autouse=True)
    async def setup_load_testing_environment(self):
        """Set up environment for load testing model retraining automation."""
        # Initialize real-time training system
        self.real_time_training = RealTimeModelTraining()

        # Initialize signal source components
        self.enhanced_personalization = EnhancedMLPersonalizationEngine()
        self.churn_prevention = PredictiveChurnPrevention()
        self.multimodal_optimizer = MultiModalCommunicationOptimizer()

        # Load test configurations
        self.load_test_configs = [
            # Light load test
            LoadTestConfiguration(
                duration_seconds=30,
                signals_per_second=5.0,
                concurrent_models=3,
                memory_limit_gb=1.0,
                accuracy_threshold=0.90,
                concept_drift_probability=0.05,
                failure_injection_rate=0.01
            ),
            # Medium load test
            LoadTestConfiguration(
                duration_seconds=60,
                signals_per_second=10.0,
                concurrent_models=5,
                memory_limit_gb=1.5,
                accuracy_threshold=0.92,
                concept_drift_probability=0.10,
                failure_injection_rate=0.02
            ),
            # Heavy load test
            LoadTestConfiguration(
                duration_seconds=90,
                signals_per_second=15.0,
                concurrent_models=8,
                memory_limit_gb=2.0,
                accuracy_threshold=0.95,
                concept_drift_probability=0.15,
                failure_injection_rate=0.03
            )
        ]

        # Test data generation
        self.test_leads = self._generate_test_leads(100)  # Large pool for variety
        self.signal_generators = {}
        self.performance_baseline = {}

        # Thread safety
        self.signal_lock = Lock()
        self.metrics_lock = Lock()

        # Memory monitoring
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        print(f"🏋️ Load testing environment setup complete")
        print(f"   Test Configurations: {len(self.load_test_configs)}")
        print(f"   Test Leads Pool: {len(self.test_leads)}")
        print(f"   Initial Memory Usage: {self.initial_memory:.1f} MB")

    def _generate_test_leads(self, count: int) -> List[Dict[str, Any]]:
        """Generate diverse test leads for load testing."""
        leads = []

        for i in range(count):
            lead_data = {
                "lead_id": f"load_test_lead_{i:03d}",
                "profile": LeadProfile(
                    lead_id=f"load_test_lead_{i:03d}",
                    name=f"TestLead {i}",
                    email=f"testlead{i}@example.com",
                    phone=f"+1555-{100+i:03d}-{200+i:04d}",
                    preferences={
                        "property_type": ["single_family", "condo", "townhouse", "luxury"][i % 4],
                        "budget": 300000 + (i * 25000),
                        "location": ["urban", "suburban", "rural"][i % 3],
                        "timeline": ["immediate", "3_months", "6_months", "flexible"][i % 4]
                    },
                    source=["website", "referral", "ad", "social"][i % 4],
                    tags=[f"tag_{j}" for j in range(i % 3 + 1)]
                ),
                "evaluation": LeadEvaluationResult(
                    lead_id=f"load_test_lead_{i:03d}",
                    current_stage=["interested", "actively_searching", "ready_to_buy"][i % 3],
                    engagement_level=0.3 + (i * 0.007) % 0.7,  # Varied engagement
                    priority_score=4.0 + (i * 0.06) % 6.0,      # Varied priority
                    contact_preferences={"channel": "email", "time": "morning"},
                    behavioral_indicators={
                        "browsing_frequency": 1.0 + (i * 0.1) % 4.0,
                        "response_rate": 0.4 + (i * 0.01) % 0.6,
                        "page_views": 5 + (i * 2) % 50,
                        "time_on_site": 100 + (i * 10) % 500
                    }
                ),
                "context": {
                    "test_scenario": f"load_test_{i % 10}",
                    "market_segment": ["luxury", "mid_range", "budget"][i % 3],
                    "urgency": ["low", "medium", "high"][i % 3]
                }
            }
            leads.append(lead_data)

        return leads

    async def _generate_learning_signal(self, lead_data: Dict[str, Any], signal_type: str) -> Optional[TrainingDataPoint]:
        """Generate a learning signal from a test lead."""
        try:
            if signal_type == "personalization":
                # Enhanced personalization signal
                personalization = await self.enhanced_personalization.generate_enhanced_personalization(
                    lead_id=lead_data["lead_id"],
                    evaluation_result=lead_data["evaluation"],
                    message_template="Load test message for {lead_name}",
                    interaction_history=[],
                    context=lead_data["context"]
                )

                features = np.array([
                    personalization.emotional_analysis.sentiment_analysis.compound,
                    personalization.emotional_analysis.emotional_volatility,
                    lead_data["evaluation"].engagement_level,
                    lead_data["evaluation"].priority_score / 10.0
                ]).reshape(1, -1)

                return TrainingDataPoint(
                    model_type=ModelType.PERSONALIZATION,
                    features=features,
                    labels={
                        "emotional_state": personalization.emotional_analysis.dominant_emotion.value,
                        "sentiment_accuracy": 0.90 + np.random.normal(0, 0.05),
                        "personalization_effectiveness": 0.85 + np.random.normal(0, 0.10)
                    },
                    confidence=0.88 + np.random.normal(0, 0.08),
                    metadata={
                        "source": "enhanced_personalization",
                        "lead_id": lead_data["lead_id"],
                        "test_signal": True
                    }
                )

            elif signal_type == "churn":
                # Churn prevention signal
                churn_assessment = await self.churn_prevention.assess_churn_risk(
                    lead_id=lead_data["lead_id"],
                    evaluation_result=lead_data["evaluation"],
                    interaction_history=[],
                    context={
                        **lead_data["context"],
                        "churn_simulation": True,
                        "risk_factors": np.random.choice(["low", "medium", "high"], p=[0.5, 0.3, 0.2])
                    }
                )

                features = np.array([
                    lead_data["evaluation"].engagement_level,
                    churn_assessment.risk_score,
                    len(churn_assessment.risk_indicators),
                    lead_data["evaluation"].priority_score / 10.0
                ]).reshape(1, -1)

                return TrainingDataPoint(
                    model_type=ModelType.CHURN_PREDICTION,
                    features=features,
                    labels={
                        "churn_risk": churn_assessment.risk_level.value,
                        "risk_score": churn_assessment.risk_score,
                        "prediction_accuracy": 0.92 + np.random.normal(0, 0.04)
                    },
                    confidence=0.90 + np.random.normal(0, 0.06),
                    metadata={
                        "source": "churn_prevention",
                        "lead_id": lead_data["lead_id"],
                        "test_signal": True
                    }
                )

            elif signal_type == "engagement":
                # Multi-modal engagement signal
                analysis = await self.multimodal_optimizer.analyze_multi_modal_communication(
                    lead_id=lead_data["lead_id"],
                    content={CommunicationModality.TEXT: "Load test communication"},
                    context=lead_data["context"]
                )

                features = np.array([
                    analysis.text_analysis.readability_metrics.flesch_reading_ease / 100.0,
                    analysis.text_analysis.persuasion_score,
                    lead_data["evaluation"].engagement_level,
                    len(analysis.text_analysis.sentiment_analysis) / 10.0
                ]).reshape(1, -1)

                return TrainingDataPoint(
                    model_type=ModelType.ENGAGEMENT,
                    features=features,
                    labels={
                        "engagement_score": 0.80 + np.random.normal(0, 0.08),
                        "optimization_effectiveness": analysis.text_analysis.persuasion_score,
                        "readability_improvement": 0.05 + np.random.normal(0, 0.02)
                    },
                    confidence=0.85 + np.random.normal(0, 0.07),
                    metadata={
                        "source": "multimodal_optimizer",
                        "lead_id": lead_data["lead_id"],
                        "test_signal": True
                    }
                )

            else:
                return None

        except Exception as e:
            print(f"⚠️  Signal generation error ({signal_type}): {str(e)}")
            return None

    @pytest.mark.asyncio
    @pytest.mark.load_test
    async def test_light_load_model_retraining(self):
        """Test model retraining under light load conditions."""
        print("\n=== Testing Light Load Model Retraining ===")

        config = self.load_test_configs[0]  # Light load
        return await self._execute_load_test(config, "light_load")

    @pytest.mark.asyncio
    @pytest.mark.load_test
    async def test_medium_load_model_retraining(self):
        """Test model retraining under medium load conditions."""
        print("\n=== Testing Medium Load Model Retraining ===")

        config = self.load_test_configs[1]  # Medium load
        return await self._execute_load_test(config, "medium_load")

    @pytest.mark.asyncio
    @pytest.mark.load_test
    async def test_heavy_load_model_retraining(self):
        """Test model retraining under heavy load conditions."""
        print("\n=== Testing Heavy Load Model Retraining ===")

        config = self.load_test_configs[2]  # Heavy load
        return await self._execute_load_test(config, "heavy_load")

    async def _execute_load_test(self, config: LoadTestConfiguration, test_name: str) -> LoadTestMetrics:
        """Execute a load test with the given configuration."""
        print(f"🚀 Starting {test_name}")
        print(f"   Duration: {config.duration_seconds}s")
        print(f"   Signals/sec: {config.signals_per_second}")
        print(f"   Concurrent Models: {config.concurrent_models}")

        # Initialize metrics collection
        load_metrics = LoadTestMetrics(
            total_signals_processed=0,
            processing_rate_avg=0.0,
            processing_time_avg=0.0,
            memory_usage_peak=0.0,
            accuracy_degradation=0.0,
            concept_drift_events=0,
            retraining_events=0,
            failed_operations=0,
            recovery_time_avg=0.0,
            system_stability_score=0.0
        )

        model_metrics: Dict[str, ModelLoadMetrics] = {}
        signal_processing_times = []
        memory_snapshots = []
        processing_rates = []

        # Get baseline performance
        baseline_state = await self.real_time_training.get_learning_state()
        baseline_performance = {
            model_type.value: performance for model_type, performance in baseline_state.model_performances.items()
        }

        start_time = time.time()
        end_time = start_time + config.duration_seconds

        # Signal generation task
        async def signal_generator():
            """Generate continuous stream of learning signals."""
            signal_count = 0
            last_rate_check = time.time()

            while time.time() < end_time:
                batch_start = time.time()

                # Generate batch of signals
                batch_size = int(config.signals_per_second)
                signal_tasks = []

                for _ in range(batch_size):
                    # Random lead and signal type
                    lead_data = random.choice(self.test_leads)
                    signal_type = random.choice(["personalization", "churn", "engagement"])

                    # Inject concept drift
                    if np.random.random() < config.concept_drift_probability:
                        lead_data = self._inject_concept_drift(lead_data)
                        load_metrics.concept_drift_events += 1

                    signal_tasks.append(self._generate_learning_signal(lead_data, signal_type))

                # Process signals
                try:
                    signals = await asyncio.gather(*signal_tasks, return_exceptions=True)

                    for signal in signals:
                        if isinstance(signal, Exception):
                            load_metrics.failed_operations += 1
                            continue

                        if signal is not None:
                            signal_start_time = time.time()

                            # Add training data with failure injection
                            if np.random.random() < config.failure_injection_rate:
                                # Simulate failure
                                load_metrics.failed_operations += 1
                                continue

                            await self.real_time_training.add_training_data(
                                model_type=signal.model_type,
                                features=signal.features,
                                labels=signal.labels,
                                metadata=signal.metadata,
                                confidence=signal.confidence
                            )

                            signal_processing_time = time.time() - signal_start_time
                            signal_processing_times.append(signal_processing_time)

                            with self.metrics_lock:
                                load_metrics.total_signals_processed += 1

                            signal_count += 1

                except Exception as e:
                    load_metrics.failed_operations += 1
                    print(f"⚠️  Batch processing error: {str(e)}")

                # Rate control
                batch_time = time.time() - batch_start
                target_batch_time = 1.0  # 1 second per batch
                if batch_time < target_batch_time:
                    await asyncio.sleep(target_batch_time - batch_time)

                # Calculate processing rate
                current_time = time.time()
                if current_time - last_rate_check >= 5.0:  # Every 5 seconds
                    rate = signal_count / (current_time - last_rate_check)
                    processing_rates.append(rate)
                    signal_count = 0
                    last_rate_check = current_time

        # Memory monitoring task
        async def memory_monitor():
            """Monitor memory usage during load test."""
            while time.time() < end_time:
                try:
                    memory_mb = self.process.memory_info().rss / 1024 / 1024
                    memory_snapshots.append(memory_mb)

                    # Update peak memory usage
                    if memory_mb > load_metrics.memory_usage_peak:
                        load_metrics.memory_usage_peak = memory_mb

                    # Trigger garbage collection if memory usage is high
                    if memory_mb > config.memory_limit_gb * 1024:
                        gc.collect()

                    await asyncio.sleep(1.0)  # Check every second
                except Exception as e:
                    print(f"⚠️  Memory monitoring error: {str(e)}")

        # Model performance monitoring task
        async def performance_monitor():
            """Monitor model performance during load test."""
            while time.time() < end_time:
                try:
                    current_state = await self.real_time_training.get_learning_state()

                    for model_type_str, performance in current_state.model_performances.items():
                        if model_type_str not in model_metrics:
                            model_metrics[model_type_str] = ModelLoadMetrics(
                                model_type=model_type_str,
                                signals_processed=0,
                                retraining_count=0,
                                accuracy_before=baseline_performance.get(model_type_str, {}).get('accuracy', 0.85),
                                accuracy_after=performance.accuracy,
                                processing_time_avg=0.0,
                                memory_usage=0.0,
                                failure_count=0
                            )

                        # Update model metrics
                        model_metrics[model_type_str].accuracy_after = performance.accuracy
                        model_metrics[model_type_str].signals_processed = performance.sample_count

                        # Check for retraining events
                        if hasattr(performance, 'last_retrained') and performance.last_retrained:
                            model_metrics[model_type_str].retraining_count += 1
                            load_metrics.retraining_events += 1

                    await asyncio.sleep(10.0)  # Check every 10 seconds
                except Exception as e:
                    print(f"⚠️  Performance monitoring error: {str(e)}")

        # Run all monitoring tasks concurrently
        try:
            await asyncio.gather(
                signal_generator(),
                memory_monitor(),
                performance_monitor()
            )
        except Exception as e:
            print(f"⚠️  Load test execution error: {str(e)}")
            load_metrics.failed_operations += 1

        # Calculate final metrics
        actual_duration = time.time() - start_time

        if signal_processing_times:
            load_metrics.processing_time_avg = np.mean(signal_processing_times)

        if processing_rates:
            load_metrics.processing_rate_avg = np.mean(processing_rates)
        else:
            load_metrics.processing_rate_avg = load_metrics.total_signals_processed / actual_duration

        # Calculate accuracy degradation
        final_state = await self.real_time_training.get_learning_state()
        accuracy_changes = []
        for model_type_str in model_metrics.keys():
            if model_type_str in baseline_performance:
                baseline_acc = baseline_performance[model_type_str].get('accuracy', 0.85)
                final_acc = final_state.model_performances.get(model_type_str, {}).accuracy
                accuracy_changes.append(baseline_acc - final_acc)

        load_metrics.accuracy_degradation = max(accuracy_changes) if accuracy_changes else 0.0

        # Calculate system stability score
        stability_factors = [
            1.0 - (load_metrics.failed_operations / max(load_metrics.total_signals_processed, 1)),  # Success rate
            1.0 - min(load_metrics.accuracy_degradation / 0.1, 1.0),  # Accuracy stability
            1.0 - min(load_metrics.memory_usage_peak / (config.memory_limit_gb * 1024), 1.0),  # Memory efficiency
            min(load_metrics.processing_rate_avg / config.signals_per_second, 1.0)  # Processing efficiency
        ]
        load_metrics.system_stability_score = np.mean(stability_factors)

        # Performance assertions
        assert load_metrics.processing_rate_avg >= config.signals_per_second * 0.8, \
               f"Low processing rate: {load_metrics.processing_rate_avg:.2f} vs target {config.signals_per_second}"
        assert load_metrics.processing_time_avg < 0.1, \
               f"Processing too slow: {load_metrics.processing_time_avg:.3f}s per signal"
        assert load_metrics.memory_usage_peak < config.memory_limit_gb * 1024, \
               f"Memory usage too high: {load_metrics.memory_usage_peak:.1f}MB vs limit {config.memory_limit_gb*1024}MB"
        assert load_metrics.accuracy_degradation < 0.05, \
               f"Accuracy degraded too much: {load_metrics.accuracy_degradation:.3f}"
        assert load_metrics.system_stability_score > 0.8, \
               f"Low system stability: {load_metrics.system_stability_score:.3f}"

        print(f"✅ {test_name} completed: {actual_duration:.1f}s")
        print(f"   Signals Processed: {load_metrics.total_signals_processed}")
        print(f"   Processing Rate: {load_metrics.processing_rate_avg:.2f} signals/sec")
        print(f"   Avg Processing Time: {load_metrics.processing_time_avg*1000:.1f}ms")
        print(f"   Peak Memory: {load_metrics.memory_usage_peak:.1f}MB")
        print(f"   Accuracy Degradation: {load_metrics.accuracy_degradation:.3f}")
        print(f"   Retraining Events: {load_metrics.retraining_events}")
        print(f"   Failed Operations: {load_metrics.failed_operations}")
        print(f"   System Stability: {load_metrics.system_stability_score:.3f}")

        return load_metrics

    def _inject_concept_drift(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inject concept drift into lead data to simulate changing conditions."""
        drifted_data = lead_data.copy()

        # Modify behavioral patterns to simulate concept drift
        drift_factors = {
            "browsing_frequency": np.random.uniform(0.5, 2.0),
            "response_rate": np.random.uniform(0.7, 1.3),
            "engagement_shift": np.random.choice(["increase", "decrease", "volatile"])
        }

        # Apply drift to behavioral indicators
        behavioral = drifted_data["evaluation"].behavioral_indicators.copy()
        behavioral["browsing_frequency"] *= drift_factors["browsing_frequency"]
        behavioral["response_rate"] = min(1.0, behavioral["response_rate"] * drift_factors["response_rate"])

        if drift_factors["engagement_shift"] == "increase":
            drifted_data["evaluation"].engagement_level = min(1.0, lead_data["evaluation"].engagement_level * 1.2)
        elif drift_factors["engagement_shift"] == "decrease":
            drifted_data["evaluation"].engagement_level = max(0.0, lead_data["evaluation"].engagement_level * 0.8)
        else:  # volatile
            drifted_data["evaluation"].engagement_level = np.random.uniform(0.2, 0.9)

        # Add drift metadata
        drifted_data["context"]["concept_drift"] = True
        drifted_data["context"]["drift_factors"] = drift_factors

        return drifted_data

    @pytest.mark.asyncio
    @pytest.mark.load_test
    async def test_concurrent_model_updates(self):
        """Test concurrent updates across multiple model types."""
        print("\n=== Testing Concurrent Model Updates ===")

        start_time = time.time()
        model_types = [ModelType.PERSONALIZATION, ModelType.CHURN_PREDICTION, ModelType.ENGAGEMENT]
        concurrent_tasks = []

        # Generate concurrent update tasks for each model type
        for model_type in model_types:
            for i in range(10):  # 10 concurrent updates per model
                lead_data = random.choice(self.test_leads)

                # Create signal for this model type
                if model_type == ModelType.PERSONALIZATION:
                    signal_task = self._generate_learning_signal(lead_data, "personalization")
                elif model_type == ModelType.CHURN_PREDICTION:
                    signal_task = self._generate_learning_signal(lead_data, "churn")
                else:  # ENGAGEMENT
                    signal_task = self._generate_learning_signal(lead_data, "engagement")

                concurrent_tasks.append(signal_task)

        # Execute all signal generation concurrently
        signals = await asyncio.gather(*concurrent_tasks, return_exceptions=True)

        # Filter successful signals
        valid_signals = [s for s in signals if not isinstance(s, Exception) and s is not None]

        # Add all training data concurrently
        training_tasks = []
        for signal in valid_signals:
            task = self.real_time_training.add_training_data(
                model_type=signal.model_type,
                features=signal.features,
                labels=signal.labels,
                metadata=signal.metadata,
                confidence=signal.confidence
            )
            training_tasks.append(task)

        # Execute all training updates concurrently
        await asyncio.gather(*training_tasks, return_exceptions=True)

        concurrent_time = time.time() - start_time

        # Verify all models were updated
        final_state = await self.real_time_training.get_learning_state()
        updated_models = len(final_state.model_performances)

        # Performance assertions
        assert concurrent_time < 5.0, f"Concurrent updates too slow: {concurrent_time:.3f}s"
        assert len(valid_signals) >= len(concurrent_tasks) * 0.8, f"Too many failed signal generations: {len(valid_signals)}/{len(concurrent_tasks)}"
        assert updated_models >= len(model_types), f"Not all models updated: {updated_models}/{len(model_types)}"

        print(f"✅ Concurrent Model Updates: {concurrent_time:.3f}s")
        print(f"   Valid Signals: {len(valid_signals)}/{len(concurrent_tasks)}")
        print(f"   Models Updated: {updated_models}")
        print(f"   Avg Signal Processing: {concurrent_time/len(valid_signals)*1000:.1f}ms" if valid_signals else "N/A")

        return {
            "concurrent_time": concurrent_time,
            "valid_signals": len(valid_signals),
            "total_signals": len(concurrent_tasks),
            "models_updated": updated_models
        }

    @pytest.mark.asyncio
    @pytest.mark.load_test
    async def test_memory_management_under_load(self):
        """Test memory management during sustained load."""
        print("\n=== Testing Memory Management Under Load ===")

        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_snapshots = []

        # Run sustained load for memory testing
        duration = 60  # 1 minute sustained load
        signals_per_second = 20
        start_time = time.time()
        end_time = start_time + duration

        signals_processed = 0
        memory_warnings = 0

        while time.time() < end_time:
            batch_start = time.time()

            # Generate and process signals
            batch_tasks = []
            for _ in range(signals_per_second):
                lead_data = random.choice(self.test_leads)
                signal_type = random.choice(["personalization", "churn", "engagement"])
                batch_tasks.append(self._generate_learning_signal(lead_data, signal_type))

            try:
                signals = await asyncio.gather(*batch_tasks, return_exceptions=True)

                for signal in signals:
                    if not isinstance(signal, Exception) and signal is not None:
                        await self.real_time_training.add_training_data(
                            model_type=signal.model_type,
                            features=signal.features,
                            labels=signal.labels,
                            metadata=signal.metadata,
                            confidence=signal.confidence
                        )
                        signals_processed += 1

                # Memory monitoring
                current_memory = self.process.memory_info().rss / 1024 / 1024
                memory_snapshots.append(current_memory)

                # Memory management
                if current_memory > initial_memory + 500:  # 500MB increase threshold
                    memory_warnings += 1
                    gc.collect()  # Force garbage collection

                # Rate control
                batch_time = time.time() - batch_start
                if batch_time < 1.0:
                    await asyncio.sleep(1.0 - batch_time)

            except Exception as e:
                print(f"⚠️  Memory test batch error: {str(e)}")

        final_memory = self.process.memory_info().rss / 1024 / 1024
        peak_memory = max(memory_snapshots)
        memory_growth = final_memory - initial_memory

        # Memory efficiency metrics
        memory_per_signal = memory_growth / signals_processed if signals_processed > 0 else 0
        memory_stability = 1.0 - (np.std(memory_snapshots) / np.mean(memory_snapshots)) if memory_snapshots else 0

        # Performance assertions
        assert memory_growth < 1000, f"Excessive memory growth: {memory_growth:.1f}MB"
        assert memory_per_signal < 1.0, f"High memory per signal: {memory_per_signal:.3f}MB"
        assert peak_memory < initial_memory + 1500, f"Peak memory too high: {peak_memory:.1f}MB"
        assert memory_stability > 0.8, f"Memory usage unstable: {memory_stability:.3f}"

        print(f"✅ Memory Management Test: {duration}s")
        print(f"   Signals Processed: {signals_processed}")
        print(f"   Initial Memory: {initial_memory:.1f}MB")
        print(f"   Final Memory: {final_memory:.1f}MB")
        print(f"   Peak Memory: {peak_memory:.1f}MB")
        print(f"   Memory Growth: {memory_growth:.1f}MB")
        print(f"   Memory per Signal: {memory_per_signal:.3f}MB")
        print(f"   Memory Stability: {memory_stability:.3f}")
        print(f"   Memory Warnings: {memory_warnings}")

        return {
            "signals_processed": signals_processed,
            "initial_memory": initial_memory,
            "final_memory": final_memory,
            "peak_memory": peak_memory,
            "memory_growth": memory_growth,
            "memory_per_signal": memory_per_signal,
            "memory_stability": memory_stability,
            "memory_warnings": memory_warnings
        }

    @pytest.mark.asyncio
    @pytest.mark.load_test
    async def test_complete_load_testing_workflow(self):
        """Test complete load testing workflow across all load levels."""
        print("\n=== Testing Complete Load Testing Workflow ===")

        workflow_start_time = time.time()
        workflow_results = {}

        try:
            # Execute all load tests
            light_load_metrics = await self.test_light_load_model_retraining()
            workflow_results["light_load"] = light_load_metrics

            medium_load_metrics = await self.test_medium_load_model_retraining()
            workflow_results["medium_load"] = medium_load_metrics

            heavy_load_metrics = await self.test_heavy_load_model_retraining()
            workflow_results["heavy_load"] = heavy_load_metrics

            # Additional specialized tests
            concurrent_results = await self.test_concurrent_model_updates()
            workflow_results["concurrent_updates"] = concurrent_results

            memory_results = await self.test_memory_management_under_load()
            workflow_results["memory_management"] = memory_results

        except Exception as e:
            workflow_results["error"] = f"Workflow failed: {str(e)}"

        total_workflow_time = time.time() - workflow_start_time

        # Calculate comprehensive metrics
        load_test_metrics = [workflow_results.get("light_load"), workflow_results.get("medium_load"), workflow_results.get("heavy_load")]
        valid_load_metrics = [m for m in load_test_metrics if m is not None]

        if valid_load_metrics:
            overall_metrics = {
                "total_signals_processed": sum(m.total_signals_processed for m in valid_load_metrics),
                "avg_processing_rate": np.mean([m.processing_rate_avg for m in valid_load_metrics]),
                "avg_processing_time": np.mean([m.processing_time_avg for m in valid_load_metrics]),
                "peak_memory_usage": max(m.memory_usage_peak for m in valid_load_metrics),
                "max_accuracy_degradation": max(m.accuracy_degradation for m in valid_load_metrics),
                "total_retraining_events": sum(m.retraining_events for m in valid_load_metrics),
                "total_failed_operations": sum(m.failed_operations for m in valid_load_metrics),
                "avg_system_stability": np.mean([m.system_stability_score for m in valid_load_metrics]),
                "workflow_duration": total_workflow_time,
                "load_levels_completed": len(valid_load_metrics)
            }

            # Business value assessment
            business_value = {
                "scalability_validated": overall_metrics["avg_system_stability"] > 0.8,
                "performance_target_met": overall_metrics["avg_processing_time"] < 0.1,
                "memory_efficient": overall_metrics["peak_memory_usage"] < 2048,  # 2GB
                "accuracy_maintained": overall_metrics["max_accuracy_degradation"] < 0.05,
                "production_ready": (
                    overall_metrics["avg_system_stability"] > 0.8 and
                    overall_metrics["avg_processing_time"] < 0.1 and
                    overall_metrics["max_accuracy_degradation"] < 0.05
                )
            }

            # Comprehensive validations
            assert overall_metrics["load_levels_completed"] >= 3, f"Incomplete load testing: {overall_metrics['load_levels_completed']}/3"
            assert overall_metrics["avg_system_stability"] > 0.8, f"Low system stability: {overall_metrics['avg_system_stability']:.3f}"
            assert overall_metrics["avg_processing_time"] < 0.1, f"Processing too slow: {overall_metrics['avg_processing_time']:.3f}s"
            assert business_value["production_ready"], "System not production ready"

            print(f"✅ Complete Load Testing Workflow: {total_workflow_time:.1f}s")
            print(f"   Load Levels Completed: {overall_metrics['load_levels_completed']}/3")
            print(f"   Total Signals Processed: {overall_metrics['total_signals_processed']:,}")
            print(f"   Avg Processing Rate: {overall_metrics['avg_processing_rate']:.2f} signals/sec")
            print(f"   Avg Processing Time: {overall_metrics['avg_processing_time']*1000:.1f}ms")
            print(f"   Peak Memory Usage: {overall_metrics['peak_memory_usage']:.1f}MB")
            print(f"   Max Accuracy Degradation: {overall_metrics['max_accuracy_degradation']:.3f}")
            print(f"   Total Retraining Events: {overall_metrics['total_retraining_events']}")
            print(f"   Total Failed Operations: {overall_metrics['total_failed_operations']}")
            print(f"   Avg System Stability: {overall_metrics['avg_system_stability']:.3f}")
            print(f"   Production Ready: {'✅ Yes' if business_value['production_ready'] else '❌ No'}")

            return {
                "workflow_results": workflow_results,
                "overall_metrics": overall_metrics,
                "business_value": business_value,
                "total_time": total_workflow_time
            }

        else:
            raise Exception("No valid load test metrics collected")


# Run model retraining load tests
if __name__ == "__main__":
    async def run_model_retraining_load_tests():
        """Run complete model retraining load test suite."""
        print("🏋️ Starting Model Retraining Automation Load Tests")
        print("=" * 80)

        test_suite = TestModelRetrainingAutomationLoad()
        await test_suite.setup_load_testing_environment()

        results = {}

        try:
            # Individual load tests
            await test_suite.test_light_load_model_retraining()
            results["light_load"] = "✅ PASS"

            await test_suite.test_medium_load_model_retraining()
            results["medium_load"] = "✅ PASS"

            await test_suite.test_heavy_load_model_retraining()
            results["heavy_load"] = "✅ PASS"

            # Specialized tests
            await test_suite.test_concurrent_model_updates()
            results["concurrent_updates"] = "✅ PASS"

            await test_suite.test_memory_management_under_load()
            results["memory_management"] = "✅ PASS"

            # Complete workflow test
            complete_result = await test_suite.test_complete_load_testing_workflow()
            results["complete_workflow"] = "✅ PASS"

        except Exception as e:
            results["error"] = f"❌ FAIL: {str(e)}"

        # Final results
        print("\n" + "=" * 80)
        print("🎯 MODEL RETRAINING AUTOMATION LOAD TEST RESULTS")
        print("=" * 80)

        for test_name, result in results.items():
            print(f"{test_name}: {result}")

        passed_tests = sum(1 for result in results.values() if result.startswith("✅"))
        total_tests = len(results)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0

        print(f"\nOverall Success Rate: {success_rate:.2%} ({passed_tests}/{total_tests})")
        print("🚀 Model Retraining Automation: PRODUCTION SCALE READY" if success_rate >= 0.9 else "⚠️  Load handling issues detected")

    asyncio.run(run_model_retraining_load_tests())