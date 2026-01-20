"""
Lead Scoring Pipeline - Customer Intelligence ML System

Manages automated machine learning pipelines for:
- Lead scoring model training and deployment
- Customer engagement prediction
- Conversion probability modeling
- Churn prediction and intervention
- Customer lifetime value estimation

Features:
- Automated model training and retraining
- Model versioning and deployment management
- Performance monitoring and drift detection
- Automated hyperparameter optimization
- Feature engineering pipeline management

Business Impact: Continuous ML model improvement for customer intelligence
Author: Customer Intelligence Platform
Created: 2026-01-19
"""

import asyncio
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from enum import Enum
import json
import pickle
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

# ML Libraries
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline

from ..utils.logger import get_logger

logger = get_logger(__name__)


class ModelType(Enum):
    """Types of ML models in the customer intelligence system."""

    LEAD_SCORING = "lead_scoring"
    ENGAGEMENT_PREDICTION = "engagement_prediction"
    CONVERSION_PREDICTION = "conversion_prediction"
    CHURN_PREDICTION = "churn_prediction"
    CUSTOMER_LTV = "customer_ltv"
    UPSELL_PREDICTION = "upsell_prediction"


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
    algorithm: str  # "random_forest", "logistic_regression", "gradient_boosting"
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    feature_selection_config: Dict[str, Any] = field(default_factory=dict)

    # Data configuration
    target_variable: str = ""
    feature_columns: List[str] = field(default_factory=list)

    # Training parameters
    test_size: float = 0.2
    validation_size: float = 0.15
    cross_validation_folds: int = 5

    # Performance thresholds
    min_accuracy: float = 0.75
    min_precision: float = 0.70
    min_recall: float = 0.70
    min_f1_score: float = 0.70
    min_auc: float = 0.80

    # Deployment configuration
    auto_deploy: bool = False
    a_b_test_percentage: float = 10.0

    # Retraining schedule
    retrain_frequency_days: int = 7
    retrain_on_performance_drop: bool = True
    performance_drop_threshold: float = 0.05

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
    conversion_rate_improvement: float = 0.0
    cost_reduction: float = 0.0
    customer_satisfaction_impact: float = 0.0

    # Model characteristics
    training_samples: int = 0
    feature_count: int = 0
    training_duration_minutes: float = 0.0
    model_size_mb: float = 0.0

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

    # Callbacks and notifications
    on_completion_callback: Optional[Callable] = None

    # Metadata
    created_by: str = ""
    department_id: str = ""
    tags: List[str] = field(default_factory=list)


class ModelRegistry:
    """Model registry for versioning and deployment management."""

    def __init__(self):
        self.models: Dict[str, ModelMetrics] = {}
        self.model_artifacts_path = Path("ml_models")
        self.model_artifacts_path.mkdir(exist_ok=True)

        # Production model tracking
        self.production_models: Dict[ModelType, str] = {}  # model_type -> model_id

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


class FeatureEngineer:
    """Feature engineering pipeline for ML models."""

    def __init__(self):
        self.feature_transformers = {}

    async def engineer_features(
        self,
        raw_data: pd.DataFrame,
        feature_config: Dict[str, Any],
        model_type: ModelType
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Engineer features for ML model training."""

        try:
            engineered_data = raw_data.copy()
            feature_names = []

            # Apply feature engineering based on model type
            if model_type == ModelType.LEAD_SCORING:
                engineered_data, features = await self._engineer_lead_scoring_features(engineered_data)
                feature_names.extend(features)

            elif model_type == ModelType.ENGAGEMENT_PREDICTION:
                engineered_data, features = await self._engineer_engagement_features(engineered_data)
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

        # Engagement features
        if 'message_count' in data.columns:
            data['message_engagement_ratio'] = data['message_count'] / (data['message_count'].mean() + 1e-6)
            features.append('message_engagement_ratio')

        # Time-based features
        if 'created_at' in data.columns:
            data['hour_of_day'] = pd.to_datetime(data['created_at']).dt.hour
            data['day_of_week'] = pd.to_datetime(data['created_at']).dt.dayofweek
            data['is_weekend'] = data['day_of_week'].isin([5, 6]).astype(int)
            features.extend(['hour_of_day', 'day_of_week', 'is_weekend'])

        # Budget-related features
        if 'budget' in data.columns:
            data['budget_log'] = np.log1p(data['budget'])
            features.append('budget_log')

        # Interaction features
        if 'response_time' in data.columns:
            data['response_time_log'] = np.log1p(data['response_time'])
            features.append('response_time_log')

        return data, features

    async def _engineer_engagement_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Engineer features for engagement prediction models."""

        features = []

        # Communication patterns
        if 'last_contact_days' in data.columns:
            data['contact_recency'] = 1 / (data['last_contact_days'] + 1)
            features.append('contact_recency')

        # Session features
        if 'session_duration' in data.columns:
            data['session_duration_log'] = np.log1p(data['session_duration'])
            features.append('session_duration_log')

        return data, features

    async def _engineer_churn_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Engineer features for churn prediction models."""

        features = []

        # Activity decline indicators
        if 'last_activity_date' in data.columns:
            data['days_since_last_activity'] = (datetime.now() - pd.to_datetime(data['last_activity_date'])).dt.days
            features.append('days_since_last_activity')

        # Support interaction features
        if 'support_tickets' in data.columns:
            data['support_ticket_rate'] = data['support_tickets'] / (data.get('account_age_days', 30) + 1)
            features.append('support_ticket_rate')

        return data, features

    async def _engineer_ltv_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Engineer features for customer lifetime value models."""

        features = []

        # Transaction patterns
        if 'total_spent' in data.columns and 'transaction_count' in data.columns:
            data['avg_transaction_value'] = data['total_spent'] / (data['transaction_count'] + 1)
            features.append('avg_transaction_value')

        # Loyalty indicators
        if 'account_age_days' in data.columns:
            data['account_age_months'] = data['account_age_days'] / 30.0
            features.append('account_age_months')

        return data, features

    async def _apply_common_transforms(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply common transformations to all feature sets."""

        # Normalize numerical columns
        numerical_columns = data.select_dtypes(include=[np.number]).columns
        for col in numerical_columns:
            if data[col].std() > 0:
                data[f"{col}_normalized"] = (data[col] - data[col].mean()) / data[col].std()

        return data


class ScoringPipeline:
    """Main ML pipeline orchestrator for customer intelligence scoring."""

    def __init__(self):
        self.model_registry = ModelRegistry()
        self.feature_engineer = FeatureEngineer()
        self.active_training_jobs: Dict[str, TrainingJob] = {}

        # Default model configurations
        self.default_configs = self._initialize_default_configs()

        logger.info("ScoringPipeline initialized")

    def _initialize_default_configs(self) -> Dict[ModelType, ModelConfig]:
        """Initialize default configurations for different model types."""

        configs = {}

        # Lead Scoring Model Config
        configs[ModelType.LEAD_SCORING] = ModelConfig(
            model_name="lead_scorer",
            model_type=ModelType.LEAD_SCORING,
            model_version="1.0.0",
            algorithm="random_forest",
            hyperparameters={
                "n_estimators": 100,
                "max_depth": 8,
                "min_samples_split": 5
            },
            target_variable="converted",
            min_accuracy=0.75,
            min_auc=0.80,
            retrain_frequency_days=7
        )

        # Engagement Prediction Model Config
        configs[ModelType.ENGAGEMENT_PREDICTION] = ModelConfig(
            model_name="engagement_predictor",
            model_type=ModelType.ENGAGEMENT_PREDICTION,
            model_version="1.0.0",
            algorithm="logistic_regression",
            hyperparameters={
                "C": 1.0,
                "max_iter": 1000,
                "solver": "lbfgs"
            },
            target_variable="high_engagement",
            min_accuracy=0.70,
            retrain_frequency_days=14
        )

        # Churn Prediction Model Config
        configs[ModelType.CHURN_PREDICTION] = ModelConfig(
            model_name="churn_predictor",
            model_type=ModelType.CHURN_PREDICTION,
            model_version="1.0.0",
            algorithm="gradient_boosting",
            hyperparameters={
                "n_estimators": 100,
                "learning_rate": 0.1,
                "max_depth": 6
            },
            target_variable="churned",
            min_precision=0.75,
            min_recall=0.70,
            retrain_frequency_days=7
        )

        return configs

    async def train_model(
        self,
        model_type: ModelType,
        training_data: pd.DataFrame,
        custom_config: Optional[ModelConfig] = None,
        department_id: str = ""
    ) -> TrainingJob:
        """Start automated model training pipeline."""

        # Get model configuration
        config = custom_config or self.default_configs.get(model_type)
        if not config:
            raise ValueError(f"No configuration available for model type: {model_type}")

        # Create training job
        job_id = f"{model_type.value}_{int(datetime.now().timestamp())}"
        training_job = TrainingJob(
            job_id=job_id,
            job_name=f"Train {config.model_name}",
            model_config=config,
            department_id=department_id
        )

        # Start training asynchronously
        self.active_training_jobs[job_id] = training_job
        asyncio.create_task(self._execute_training_pipeline(training_job, training_data))

        logger.info(f"Started training job {job_id} for {model_type}")
        return training_job

    async def _execute_training_pipeline(
        self,
        training_job: TrainingJob,
        training_data: pd.DataFrame
    ) -> None:
        """Execute the complete training pipeline."""

        try:
            training_job.status = TrainingStatus.RUNNING
            training_job.started_at = datetime.now()
            training_job.progress_percentage = 10.0

            config = training_job.model_config

            # Step 1: Feature Engineering
            training_job.training_logs.append("Starting feature engineering...")
            engineered_data, feature_names = await self.feature_engineer.engineer_features(
                training_data,
                config.feature_selection_config,
                config.model_type
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
            else:
                training_job.training_logs.append("Model did not meet performance thresholds")
                training_job.error_messages.append("Performance below minimum requirements")

            # Complete training job
            training_job.trained_model = trained_model
            training_job.model_metrics = model_metrics
            training_job.status = TrainingStatus.COMPLETED
            training_job.completed_at = datetime.now()
            training_job.execution_time_minutes = (training_job.completed_at - training_job.started_at).total_seconds() / 60
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

    def _prepare_training_data(
        self,
        data: pd.DataFrame,
        config: ModelConfig,
        feature_names: List[str]
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare training data for model training."""

        # Use specified features or all numeric features
        if config.feature_columns:
            feature_columns = [col for col in config.feature_columns if col in data.columns]
        else:
            feature_columns = [col for col in feature_names if col in data.columns]
            # Add any remaining numeric columns
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            feature_columns.extend([col for col in numeric_cols if col not in feature_columns and col != config.target_variable])

        X = data[feature_columns]
        y = data[config.target_variable] if config.target_variable in data.columns else pd.Series()

        return X, y

    async def _train_ml_model(self, X: pd.DataFrame, y: pd.Series, config: ModelConfig) -> Any:
        """Train ML model based on configuration."""

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=config.test_size, random_state=42
        )

        # Initialize model based on algorithm
        if config.algorithm == "random_forest":
            model = RandomForestRegressor(**config.hyperparameters, random_state=42)
        elif config.algorithm == "logistic_regression":
            model = LogisticRegression(**config.hyperparameters, random_state=42)
        elif config.algorithm == "gradient_boosting":
            model = GradientBoostingRegressor(**config.hyperparameters, random_state=42)
        else:
            raise ValueError(f"Unsupported algorithm: {config.algorithm}")

        # Train model
        model.fit(X_train, y_train)

        return model

    async def _evaluate_model(self, model: Any, X: pd.DataFrame, y: pd.Series, config: ModelConfig) -> ModelMetrics:
        """Evaluate model performance and create metrics."""

        # Split data for evaluation
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=config.test_size, random_state=42
        )

        # Make predictions
        y_pred = model.predict(X_test)

        # Calculate metrics based on problem type
        if config.model_type in [ModelType.LEAD_SCORING, ModelType.ENGAGEMENT_PREDICTION, ModelType.CHURN_PREDICTION]:
            # Classification metrics
            y_pred_binary = (y_pred > 0.5).astype(int)
            accuracy = accuracy_score(y_test, y_pred_binary)
            precision = precision_score(y_test, y_pred_binary, average='weighted', zero_division=0)
            recall = recall_score(y_test, y_pred_binary, average='weighted', zero_division=0)
            f1 = f1_score(y_test, y_pred_binary, average='weighted', zero_division=0)
            try:
                auc = roc_auc_score(y_test, y_pred)
            except ValueError:
                auc = 0.5  # Default for binary cases with single class
        else:
            # For regression tasks, use approximations
            accuracy = 1.0 - np.mean(np.abs(y_test - y_pred) / (np.abs(y_test) + 1e-6))
            precision = accuracy
            recall = accuracy
            f1 = accuracy
            auc = 0.5

        return ModelMetrics(
            model_id="",  # Will be set during registration
            model_name=config.model_name,
            model_version=config.model_version,
            model_type=config.model_type,
            accuracy=float(accuracy),
            precision=float(precision),
            recall=float(recall),
            f1_score=float(f1),
            auc_score=float(auc),
            training_samples=len(X),
            feature_count=X.shape[1]
        )

    def _meets_performance_thresholds(self, metrics: ModelMetrics, config: ModelConfig) -> bool:
        """Check if model meets minimum performance thresholds."""

        thresholds_met = [
            metrics.accuracy >= config.min_accuracy,
            metrics.precision >= config.min_precision,
            metrics.recall >= config.min_recall,
            metrics.f1_score >= config.min_f1_score,
            metrics.auc_score >= config.min_auc
        ]

        return all(thresholds_met)

    def get_training_job_status(self, job_id: str) -> Optional[TrainingJob]:
        """Get the current status of a training job."""
        return self.active_training_jobs.get(job_id)

    async def predict(
        self,
        model_type: ModelType,
        features: Dict[str, Any],
        department_id: Optional[str] = None
    ) -> Optional[float]:
        """Make prediction using production model."""

        # Get production model
        model_info = self.model_registry.get_production_model(model_type)
        if not model_info:
            logger.warning(f"No production model available for {model_type}")
            return None

        model_id, model = model_info

        try:
            # Convert features to DataFrame
            feature_df = pd.DataFrame([features])

            # Engineer features
            engineered_data, _ = await self.feature_engineer.engineer_features(
                feature_df,
                {},
                model_type
            )

            # Make prediction
            prediction = model.predict(engineered_data)[0]
            return float(prediction)

        except Exception as e:
            logger.error(f"Prediction failed for model {model_id}: {e}")
            return None


# Factory function
def create_scoring_pipeline() -> ScoringPipeline:
    """Create scoring pipeline instance."""
    return ScoringPipeline()


# Test function
async def test_scoring_pipeline() -> None:
    """Test scoring pipeline functionality."""

    pipeline = create_scoring_pipeline()

    # Create sample training data
    sample_data = pd.DataFrame({
        'message_count': np.random.randint(1, 20, 100),
        'budget': np.random.randint(1000, 100000, 100),
        'response_time': np.random.randint(1, 1440, 100),  # minutes
        'engagement_score': np.random.random(100),
        'converted': np.random.choice([0, 1], 100)
    })

    # Start training job
    training_job = await pipeline.train_model(
        ModelType.LEAD_SCORING,
        sample_data,
        department_id="test_department"
    )

    print(f"Training Job Started: {training_job.job_id}")
    print(f"Status: {training_job.status}")

    # Wait for completion
    await asyncio.sleep(5)

    # Check final status
    final_status = pipeline.get_training_job_status(training_job.job_id)
    if final_status:
        print(f"Final Status: {final_status.status}")
        print(f"Execution Time: {final_status.execution_time_minutes:.2f} minutes")
        print(f"Training Logs: {len(final_status.training_logs)} entries")


if __name__ == "__main__":
    # Run test when executed directly
    asyncio.run(test_scoring_pipeline())