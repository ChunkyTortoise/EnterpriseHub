"""
ML Pipeline Orchestrator - AI Revenue Optimization System

Manages automated machine learning pipelines for:
- Lead scoring model training and deployment
- Price elasticity modeling
- Demand forecasting
- Customer lifetime value prediction
- Churn prediction and intervention
- A/B testing optimization

Features:
- Automated model training and retraining
- Model versioning and deployment management
- Performance monitoring and drift detection
- Automated hyperparameter optimization
- Feature engineering pipeline management
- Model A/B testing and champion/challenger frameworks

Business Impact: Continuous ML model improvement for revenue optimization
Author: Claude Code Agent - ML Infrastructure Specialist
Created: 2026-01-18
"""

import asyncio
import json
import logging
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

# ML Libraries
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service

# Import existing services
from ghl_real_estate_ai.services.predictive_lead_scorer_v2 import PredictiveLeadScorerV2

logger = get_logger(__name__)
cache = get_cache_service()


class ModelType(Enum):
    """Types of ML models in the revenue optimization system."""

    LEAD_SCORING = "lead_scoring"
    PRICE_ELASTICITY = "price_elasticity"
    DEMAND_FORECASTING = "demand_forecasting"
    CUSTOMER_LTV = "customer_ltv"
    CHURN_PREDICTION = "churn_prediction"
    UPSELL_PREDICTION = "upsell_prediction"
    CONVERSION_OPTIMIZATION = "conversion_optimization"
    # Neural Property Matching components
    NEURAL_PROPERTY_MATCHER = "neural_property_matcher"
    NEURAL_FEATURE_ENGINEER = "neural_feature_engineer"
    NEURAL_INFERENCE_ENGINE = "neural_inference_engine"
    PRIVACY_PRESERVING_ML = "privacy_preserving_ml"
    VR_AR_ANALYTICS = "vr_ar_analytics"


class ModelStatus(Enum):
    """Model lifecycle status."""

    TRAINING = "training"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    FAILED = "failed"


class TrainingStatus(Enum):
    """Training pipeline status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ModelConfig:
    """Configuration for ML model training and deployment."""

    # Model identification
    model_name: str
    model_type: ModelType
    model_version: str

    # Training configuration
    algorithm: str  # "random_forest", "xgboost", "logistic_regression", etc.
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    feature_selection_config: Dict[str, Any] = field(default_factory=dict)

    # Data configuration
    training_data_query: str = ""
    feature_engineering_pipeline: List[str] = field(default_factory=list)
    target_variable: str = ""
    feature_columns: List[str] = field(default_factory=list)

    # Training parameters
    test_size: float = 0.2
    validation_size: float = 0.15
    cross_validation_folds: int = 5
    early_stopping_rounds: int = 50

    # Performance thresholds
    min_accuracy: float = 0.75
    min_precision: float = 0.70
    min_recall: float = 0.70
    min_f1_score: float = 0.70
    min_auc: float = 0.80

    # Deployment configuration
    auto_deploy: bool = False
    a_b_test_percentage: float = 10.0  # % of traffic for new model
    champion_challenger_enabled: bool = True

    # Retraining schedule
    retrain_frequency_days: int = 7
    retrain_on_performance_drop: bool = True
    performance_drop_threshold: float = 0.05  # 5% drop triggers retrain

    # Drift detection
    feature_drift_threshold: float = 0.1
    prediction_drift_threshold: float = 0.1
    data_quality_threshold: float = 0.9

    # Metadata
    created_by: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class ModelMetrics:
    """Model performance metrics and metadata."""

    # Model identification
    model_id: str
    model_name: str
    model_version: str
    model_type: ModelType

    # Performance metrics
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_score: float

    # Business impact metrics
    revenue_impact: float = 0.0
    conversion_rate_improvement: float = 0.0
    cost_reduction: float = 0.0
    customer_satisfaction_impact: float = 0.0

    # Model characteristics
    training_samples: int = 0
    feature_count: int = 0
    training_duration_minutes: float = 0.0
    model_size_mb: float = 0.0

    # Drift and quality metrics
    feature_drift_score: float = 0.0
    prediction_drift_score: float = 0.0
    data_quality_score: float = 1.0

    # A/B testing results
    ab_test_results: Dict[str, float] = field(default_factory=dict)
    statistical_significance: float = 0.0

    # Deployment info
    status: ModelStatus = ModelStatus.TRAINING
    deployed_at: Optional[datetime] = None
    last_retrain_date: Optional[datetime] = None
    next_retrain_scheduled: Optional[datetime] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TrainingJob:
    """ML model training job configuration and status."""

    # Job identification
    job_id: str
    job_name: str
    model_config: ModelConfig

    # Job status
    status: TrainingStatus = TrainingStatus.PENDING
    progress_percentage: float = 0.0

    # Execution info
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_minutes: float = 0.0

    # Results
    trained_model: Optional[Any] = None
    model_metrics: Optional[ModelMetrics] = None
    training_logs: List[str] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)

    # Resource usage
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    gpu_usage_percent: float = 0.0

    # Callbacks and notifications
    on_completion_callback: Optional[Callable] = None
    notification_channels: List[str] = field(default_factory=list)

    # Metadata
    created_by: str = ""
    location_id: str = ""
    tags: List[str] = field(default_factory=list)


class ModelRegistry:
    """Model registry for versioning and deployment management."""

    def __init__(self):
        self.models: Dict[str, ModelMetrics] = {}
        self.model_artifacts_path = Path("ml_models")
        self.model_artifacts_path.mkdir(exist_ok=True)

        # Production model tracking
        self.production_models: Dict[ModelType, str] = {}  # model_type -> model_id
        self.challenger_models: Dict[ModelType, List[str]] = {}  # model_type -> [model_ids]

        logger.info("ModelRegistry initialized")

    def register_model(self, model_metrics: ModelMetrics, model_artifact: Any) -> str:
        """Register a new model with versioning."""

        model_id = f"{model_metrics.model_name}_{model_metrics.model_version}_{int(datetime.now().timestamp())}"
        model_metrics.model_id = model_id

        # Store model metadata
        self.models[model_id] = model_metrics

        # Save model artifact
        artifact_path = self.model_artifacts_path / f"{model_id}.pkl"
        joblib.dump(model_artifact, artifact_path)

        logger.info(f"Model registered: {model_id}")
        return model_id

    def get_production_model(self, model_type: ModelType) -> Optional[Tuple[str, Any]]:
        """Get the current production model for a given type."""

        if model_type not in self.production_models:
            return None

        model_id = self.production_models[model_type]
        model_metrics = self.models.get(model_id)

        if not model_metrics:
            return None

        # Load model artifact
        artifact_path = self.model_artifacts_path / f"{model_id}.pkl"
        if artifact_path.exists():
            model_artifact = joblib.load(artifact_path)
            return model_id, model_artifact

        return None

    def promote_to_production(self, model_id: str) -> bool:
        """Promote a model to production status."""

        if model_id not in self.models:
            logger.error(f"Model {model_id} not found in registry")
            return False

        model_metrics = self.models[model_id]

        # Demote current production model
        current_production = self.production_models.get(model_metrics.model_type)
        if current_production and current_production in self.models:
            self.models[current_production].status = ModelStatus.DEPRECATED

        # Promote new model
        self.production_models[model_metrics.model_type] = model_id
        model_metrics.status = ModelStatus.PRODUCTION
        model_metrics.deployed_at = datetime.now()

        logger.info(f"Model {model_id} promoted to production for {model_metrics.model_type}")
        return True

    def add_challenger_model(self, model_id: str) -> bool:
        """Add a model as a challenger for A/B testing."""

        if model_id not in self.models:
            return False

        model_metrics = self.models[model_id]
        model_type = model_metrics.model_type

        if model_type not in self.challenger_models:
            self.challenger_models[model_type] = []

        self.challenger_models[model_type].append(model_id)
        model_metrics.status = ModelStatus.STAGING

        logger.info(f"Model {model_id} added as challenger for {model_type}")
        return True


class FeatureEngineer:
    """Feature engineering pipeline for ML models."""

    def __init__(self):
        self.feature_transformers = {}
        self.feature_importance_cache = {}

    async def engineer_features(
        self, raw_data: pd.DataFrame, feature_config: Dict[str, Any], model_type: ModelType
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Engineer features for ML model training."""

        try:
            engineered_data = raw_data.copy()
            feature_names = []

            # Apply feature engineering based on model type
            if model_type == ModelType.LEAD_SCORING:
                engineered_data, features = await self._engineer_lead_scoring_features(engineered_data)
                feature_names.extend(features)

            elif model_type == ModelType.PRICE_ELASTICITY:
                engineered_data, features = await self._engineer_pricing_features(engineered_data)
                feature_names.extend(features)

            elif model_type == ModelType.CHURN_PREDICTION:
                engineered_data, features = await self._engineer_churn_features(engineered_data)
                feature_names.extend(features)

            elif model_type == ModelType.CUSTOMER_LTV:
                engineered_data, features = await self._engineer_ltv_features(engineered_data)
                feature_names.extend(features)

            # Apply common transformations
            engineered_data = await self._apply_common_transforms(engineered_data)

            # Remove infinite and null values
            engineered_data = engineered_data.replace([np.inf, -np.inf], np.nan)
            engineered_data = engineered_data.fillna(0)

            logger.info(f"Feature engineering completed for {model_type}: {len(feature_names)} features")
            return engineered_data, feature_names

        except Exception as e:
            logger.error(f"Error in feature engineering: {e}")
            return raw_data, []

    async def _engineer_lead_scoring_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Engineer features specific to lead scoring models."""

        features = []

        # Behavioral features
        if "conversation_length" in data.columns:
            data["conversation_engagement_ratio"] = data["conversation_length"] / (
                data["conversation_length"].mean() + 1e-6
            )
            features.append("conversation_engagement_ratio")

        # Time-based features
        if "created_at" in data.columns:
            data["hour_of_day"] = pd.to_datetime(data["created_at"]).dt.hour
            data["day_of_week"] = pd.to_datetime(data["created_at"]).dt.dayofweek
            data["is_weekend"] = data["day_of_week"].isin([5, 6]).astype(int)
            features.extend(["hour_of_day", "day_of_week", "is_weekend"])

        # Budget-related features
        if all(col in data.columns for col in ["budget_min", "budget_max"]):
            data["budget_range"] = data["budget_max"] - data["budget_min"]
            data["budget_midpoint"] = (data["budget_min"] + data["budget_max"]) / 2
            features.extend(["budget_range", "budget_midpoint"])

        return data, features

    async def _engineer_pricing_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Engineer features for price elasticity models."""

        features = []

        # Price sensitivity indicators
        if "historical_prices" in data.columns:
            data["price_volatility"] = data["historical_prices"].rolling(window=7).std()
            features.append("price_volatility")

        # Market condition features
        if "competitor_prices" in data.columns:
            data["price_premium_ratio"] = data["current_price"] / (data["competitor_prices"] + 1e-6)
            features.append("price_premium_ratio")

        return data, features

    async def _engineer_churn_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Engineer features for churn prediction models."""

        features = []

        # Engagement decline indicators
        if "last_activity_date" in data.columns:
            data["days_since_last_activity"] = (datetime.now() - pd.to_datetime(data["last_activity_date"])).dt.days
            features.append("days_since_last_activity")

        # Communication frequency
        if "communication_frequency" in data.columns:
            data["communication_decline"] = data["communication_frequency"].pct_change()
            features.append("communication_decline")

        return data, features

    async def _engineer_ltv_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Engineer features for customer lifetime value models."""

        features = []

        # Transaction patterns
        if "transaction_history" in data.columns:
            data["avg_transaction_value"] = data["transaction_history"].apply(lambda x: np.mean(x) if x else 0)
            data["transaction_frequency"] = data["transaction_history"].apply(len)
            features.extend(["avg_transaction_value", "transaction_frequency"])

        return data, features

    async def _apply_common_transforms(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply common transformations to all feature sets."""

        # Normalize numerical columns
        numerical_columns = data.select_dtypes(include=[np.number]).columns
        for col in numerical_columns:
            if data[col].std() > 0:
                data[f"{col}_normalized"] = (data[col] - data[col].mean()) / data[col].std()

        # Create interaction features for key columns
        if len(numerical_columns) >= 2:
            col1, col2 = numerical_columns[:2]
            data[f"{col1}_{col2}_interaction"] = data[col1] * data[col2]

        return data


class MLPipelineOrchestrator:
    """Main ML pipeline orchestrator for automated model training and deployment."""

    def __init__(self):
        self.model_registry = ModelRegistry()
        self.feature_engineer = FeatureEngineer()
        self.active_training_jobs: Dict[str, TrainingJob] = {}
        self.cache = cache

        # Default model configurations
        self.default_configs = self._initialize_default_configs()

        # Neural ML integration (lazy loaded)
        self._neural_integrator = None

        logger.info("MLPipelineOrchestrator initialized")

    def _initialize_default_configs(self) -> Dict[ModelType, ModelConfig]:
        """Initialize default configurations for different model types."""

        configs = {}

        # Lead Scoring Model Config
        configs[ModelType.LEAD_SCORING] = ModelConfig(
            model_name="lead_scorer_v2",
            model_type=ModelType.LEAD_SCORING,
            model_version="2.1.0",
            algorithm="xgboost",
            hyperparameters={"n_estimators": 100, "max_depth": 8, "learning_rate": 0.1, "subsample": 0.8},
            target_variable="closed_deal",
            min_accuracy=0.80,
            min_auc=0.85,
            retrain_frequency_days=7,
        )

        # Price Elasticity Model Config
        configs[ModelType.PRICE_ELASTICITY] = ModelConfig(
            model_name="price_elasticity_v1",
            model_type=ModelType.PRICE_ELASTICITY,
            model_version="1.0.0",
            algorithm="random_forest",
            hyperparameters={"n_estimators": 200, "max_depth": 10, "min_samples_split": 5},
            target_variable="demand_response",
            min_accuracy=0.75,
            retrain_frequency_days=14,
        )

        # Churn Prediction Model Config
        configs[ModelType.CHURN_PREDICTION] = ModelConfig(
            model_name="churn_predictor_v1",
            model_type=ModelType.CHURN_PREDICTION,
            model_version="1.0.0",
            algorithm="logistic_regression",
            hyperparameters={"C": 1.0, "max_iter": 1000, "solver": "lbfgs"},
            target_variable="churned",
            min_precision=0.75,
            min_recall=0.70,
            retrain_frequency_days=7,
        )

        return configs

    async def train_model(
        self,
        model_type: ModelType,
        training_data: pd.DataFrame,
        custom_config: Optional[ModelConfig] = None,
        location_id: str = "",
    ) -> TrainingJob:
        """Start automated model training pipeline."""

        # Get model configuration
        config = custom_config or self.default_configs.get(model_type)
        if not config:
            raise ValueError(f"No configuration available for model type: {model_type}")

        # Create training job
        job_id = f"{model_type.value}_{int(datetime.now().timestamp())}"
        training_job = TrainingJob(
            job_id=job_id, job_name=f"Train {config.model_name}", model_config=config, location_id=location_id
        )

        # Start training asynchronously
        self.active_training_jobs[job_id] = training_job
        asyncio.create_task(self._execute_training_pipeline(training_job, training_data))

        logger.info(f"Started training job {job_id} for {model_type}")
        return training_job

    async def _execute_training_pipeline(self, training_job: TrainingJob, training_data: pd.DataFrame) -> None:
        """Execute the complete training pipeline."""

        try:
            training_job.status = TrainingStatus.RUNNING
            training_job.started_at = datetime.now()
            training_job.progress_percentage = 10.0

            config = training_job.model_config

            # Step 1: Feature Engineering
            training_job.training_logs.append("Starting feature engineering...")
            engineered_data, feature_names = await self.feature_engineer.engineer_features(
                training_data, config.feature_selection_config, config.model_type
            )
            training_job.progress_percentage = 30.0

            # Step 2: Data Preparation
            training_job.training_logs.append("Preparing training data...")
            X, y = self._prepare_training_data(engineered_data, config, feature_names)
            training_job.progress_percentage = 40.0

            # Step 3: Model Training
            training_job.training_logs.append("Training ML model...")
            trained_model = await self._train_ml_model(X, y, config)
            training_job.progress_percentage = 70.0

            # Step 4: Model Evaluation
            training_job.training_logs.append("Evaluating model performance...")
            model_metrics = await self._evaluate_model(trained_model, X, y, config)
            training_job.progress_percentage = 90.0

            # Step 5: Model Registration
            if self._meets_performance_thresholds(model_metrics, config):
                training_job.training_logs.append("Registering model...")
                model_id = self.model_registry.register_model(model_metrics, trained_model)
                training_job.training_logs.append(f"Model registered with ID: {model_id}")

                # Auto-deploy if configured
                if config.auto_deploy:
                    self.model_registry.promote_to_production(model_id)
                    training_job.training_logs.append("Model auto-deployed to production")
                elif config.champion_challenger_enabled:
                    self.model_registry.add_challenger_model(model_id)
                    training_job.training_logs.append("Model added as challenger for A/B testing")
            else:
                training_job.training_logs.append("Model did not meet performance thresholds")
                training_job.error_messages.append("Performance below minimum requirements")

            # Complete training job
            training_job.trained_model = trained_model
            training_job.model_metrics = model_metrics
            training_job.status = TrainingStatus.COMPLETED
            training_job.completed_at = datetime.now()
            training_job.execution_time_minutes = (
                training_job.completed_at - training_job.started_at
            ).total_seconds() / 60
            training_job.progress_percentage = 100.0

            # Execute completion callback
            if training_job.on_completion_callback:
                await training_job.on_completion_callback(training_job)

            logger.info(f"Training job {training_job.job_id} completed successfully")

        except Exception as e:
            training_job.status = TrainingStatus.FAILED
            training_job.error_messages.append(str(e))
            training_job.completed_at = datetime.now()

            logger.error(f"Training job {training_job.job_id} failed: {e}")

    # Continue with additional methods for the ML pipeline...

    def get_training_job_status(self, job_id: str) -> Optional[TrainingJob]:
        """Get the current status of a training job."""
        return self.active_training_jobs.get(job_id)

    async def schedule_automated_retraining(self) -> None:
        """Schedule automated retraining based on model configurations."""

        for model_type, production_model_id in self.model_registry.production_models.items():
            model_metrics = self.model_registry.models.get(production_model_id)

            if not model_metrics or not model_metrics.next_retrain_scheduled:
                continue

            # Check if retraining is due
            if datetime.now() >= model_metrics.next_retrain_scheduled:
                logger.info(f"Automated retraining due for {model_type}")

                # Get fresh training data
                training_data = await self._get_training_data_for_model(model_type)

                if not training_data.empty:
                    await self.train_model(model_type, training_data)

                    # Update next retrain schedule
                    config = self.default_configs.get(model_type)
                    if config:
                        model_metrics.next_retrain_scheduled = datetime.now() + timedelta(
                            days=config.retrain_frequency_days
                        )

    @property
    def neural_integrator(self):
        """Lazy-loaded neural ML integrator."""
        if self._neural_integrator is None:
            try:
                from ghl_real_estate_ai.ml.neural_ml_integration import create_neural_ml_integrator

                self._neural_integrator = create_neural_ml_integrator(self)
                logger.info("Neural ML integrator loaded successfully")
            except ImportError as e:
                logger.warning(f"Neural ML integration not available: {e}")
                self._neural_integrator = None
        return self._neural_integrator

    def supports_neural_models(self) -> bool:
        """Check if neural models are supported."""
        return self.neural_integrator is not None

    async def train_neural_model(
        self,
        neural_model_type: str,
        training_data: Dict[str, Any],
        custom_config: Optional[Any] = None,
        location_id: str = "",
    ) -> Optional[TrainingJob]:
        """Train neural models using the neural integrator."""

        if not self.supports_neural_models():
            logger.error("Neural models not supported - missing dependencies")
            return None

        try:
            from ghl_real_estate_ai.ml.neural_ml_integration import NeuralModelType

            # Convert string to NeuralModelType enum
            neural_type = None
            for nt in NeuralModelType:
                if nt.value == neural_model_type:
                    neural_type = nt
                    break

            if not neural_type:
                logger.error(f"Unsupported neural model type: {neural_model_type}")
                return None

            return await self.neural_integrator.train_neural_model(
                neural_type, training_data, custom_config, location_id
            )
        except Exception as e:
            logger.error(f"Failed to train neural model: {e}")
            return None

    async def get_neural_inference_engine(self):
        """Get neural inference engine for real-time predictions."""
        if not self.supports_neural_models():
            return None
        return await self.neural_integrator.get_neural_inference_engine()

    async def get_vr_ar_analytics_engine(self):
        """Get VR/AR analytics engine for spatial interaction tracking."""
        if not self.supports_neural_models():
            return None
        return await self.neural_integrator.get_vr_ar_analytics_engine()

    def supports_model_type(self, model_type: str) -> bool:
        """Check if a model type is supported (including neural models)."""

        # Check standard model types
        standard_types = [mt.value for mt in ModelType]
        if model_type in standard_types:
            return True

        # Check neural model types
        if self.supports_neural_models():
            return self.neural_integrator.supports_neural_model_type(model_type)

        return False


# Factory function
def create_ml_pipeline_orchestrator() -> MLPipelineOrchestrator:
    """Create ML pipeline orchestrator instance."""
    return MLPipelineOrchestrator()


# Test function
async def test_ml_pipeline() -> None:
    """Test ML pipeline orchestrator functionality."""

    orchestrator = create_ml_pipeline_orchestrator()

    # Create sample training data
    sample_data = pd.DataFrame(
        {
            "conversation_length": np.random.randint(5, 50, 100),
            "budget_min": np.random.randint(200000, 800000, 100),
            "budget_max": np.random.randint(300000, 1000000, 100),
            "engagement_score": np.random.random(100),
            "closed_deal": np.random.choice([0, 1], 100),
        }
    )

    # Start training job
    training_job = await orchestrator.train_model(ModelType.LEAD_SCORING, sample_data, location_id="test_location")

    print(f"Training Job Started: {training_job.job_id}")
    print(f"Status: {training_job.status}")

    # Wait for completion (in real scenario, would poll status)
    await asyncio.sleep(5)

    # Check final status
    final_status = orchestrator.get_training_job_status(training_job.job_id)
    if final_status:
        print(f"Final Status: {final_status.status}")
        print(f"Execution Time: {final_status.execution_time_minutes:.2f} minutes")
        print(f"Training Logs: {len(final_status.training_logs)} entries")


if __name__ == "__main__":
    # Run test when executed directly
    asyncio.run(test_ml_pipeline())
