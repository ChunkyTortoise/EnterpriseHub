"""
Closing Probability ML Model for Predictive Lead Scoring.

Uses Random Forest and XGBoost models to predict the probability
that a lead will close into a transaction based on conversation
features and market conditions.
"""

import asyncio
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import joblib
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import confusion_matrix, roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    _ML_AVAILABLE = True
except ImportError:
    joblib = None
    pd = None
    _ML_AVAILABLE = False

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ml.feature_engineering import ConversationFeatures, FeatureEngineer
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)
cache = get_cache_service()


@dataclass
class ModelPrediction:
    """Structured prediction output with confidence intervals."""

    closing_probability: float  # 0 to 1
    confidence_interval: Tuple[float, float]  # Lower and upper bounds
    risk_factors: List[str]  # Key factors reducing closing probability
    positive_signals: List[str]  # Key factors increasing closing probability
    model_confidence: float  # Model's confidence in prediction (0-1)
    feature_importance: Dict[str, float]  # Top contributing features


@dataclass
class ModelMetrics:
    """Model performance metrics."""

    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_score: float
    feature_importances: Dict[str, float]
    confusion_matrix: np.ndarray
    validation_date: datetime


class ClosingProbabilityModel:
    """
    Machine Learning model for predicting lead closing probability.

    Uses Random Forest as the base model with optional XGBoost ensemble.
    Includes automated retraining, feature importance analysis, and
    confidence interval estimation.
    """

    def __init__(self, model_dir: str = "data/models"):
        """
        Initialize the closing probability model.

        Args:
            model_dir: Directory to store model files
        """
        self.model_dir = model_dir
        self.model_path = os.path.join(model_dir, "closing_probability_model.pkl")
        self.scaler_path = os.path.join(model_dir, "feature_scaler.pkl")
        self.metadata_path = os.path.join(model_dir, "model_metadata.json")

        # Ensure model directory exists
        os.makedirs(model_dir, exist_ok=True)

        # Initialize components
        self.feature_engineer = FeatureEngineer()
        self.model: Optional[RandomForestClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
        self.last_training_date: Optional[datetime] = None
        self.model_metrics: Optional[ModelMetrics] = None

        # Thread safety for model loading
        self._loading_lock = threading.Lock()
        self._model_loaded = False
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ml-model")

        # Load existing model if available (lazy loading - only when needed)
        # Removed automatic loading to prevent asyncio conflicts

    async def _load_model(self) -> bool:
        """
        Load existing model from disk using non-blocking I/O.

        Returns:
            True if model loaded successfully, False otherwise
        """
        # Check if already loaded or loading in progress
        if self._model_loaded:
            return True

        # Use lock to prevent multiple simultaneous loads
        if not self._loading_lock.acquire(blocking=False):
            # Another thread is loading, wait briefly and check again
            await asyncio.sleep(0.1)
            return self._model_loaded

        try:
            loop = asyncio.get_event_loop()

            # Run blocking I/O operations in thread executor
            def _load_files():
                if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                    model = joblib.load(self.model_path)
                    scaler = joblib.load(self.scaler_path)

                    metadata = {}
                    if os.path.exists(self.metadata_path):
                        with open(self.metadata_path, "r") as f:
                            metadata = json.load(f)

                    return model, scaler, metadata
                return None, None, {}

            # Execute file loading in background thread
            model, scaler, metadata = await loop.run_in_executor(self._executor, _load_files)

            if model is not None and scaler is not None:
                self.model = model
                self.scaler = scaler
                self.feature_names = metadata.get("feature_names", [])

                if "last_training_date" in metadata:
                    self.last_training_date = datetime.fromisoformat(metadata["last_training_date"])

                self._model_loaded = True
                logger.info(f"Model loaded successfully, trained on {self.last_training_date}")
                return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")

        finally:
            self._loading_lock.release()

        return False

    async def _ensure_model_loaded(self) -> bool:
        """
        Ensure the model is loaded before use with lazy loading.

        Returns:
            True if model is available, False otherwise
        """
        if not self._model_loaded:
            return await self._load_model()
        return True

    async def _save_model(self) -> bool:
        """
        Save model and metadata to disk.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Save model and scaler
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)

            # Save metadata
            metadata = {
                "feature_names": self.feature_names,
                "last_training_date": self.last_training_date.isoformat(),
                "model_type": "RandomForestClassifier",
                "feature_count": len(self.feature_names),
            }

            with open(self.metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Model saved to {self.model_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False

    async def train_model(
        self,
        training_data: pd.DataFrame,
        target_column: str = "closed",
        validation_split: float = 0.2,
        random_state: int = 42,
    ) -> ModelMetrics:
        """
        Train the closing probability model.

        Args:
            training_data: DataFrame with features and target variable
            target_column: Name of the target column (0/1 for not closed/closed)
            validation_split: Proportion of data for validation
            random_state: Random seed for reproducibility

        Returns:
            ModelMetrics with training performance
        """
        logger.info("Starting model training...")

        try:
            # Prepare features and target
            if target_column not in training_data.columns:
                raise ValueError(f"Target column '{target_column}' not found in training data")

            X = training_data.drop(columns=[target_column])
            y = training_data[target_column]

            # Store feature names
            self.feature_names = list(X.columns)

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=validation_split, random_state=random_state, stratify=y
            )

            # Scale features
            self.scaler = StandardScaler()
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train Random Forest model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=random_state,
                class_weight="balanced",  # Handle class imbalance
            )

            self.model.fit(X_train_scaled, y_train)

            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]

            # Calculate metrics
            from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            auc = roc_auc_score(y_test, y_pred_proba)

            # Feature importances
            feature_importance_dict = dict(zip(self.feature_names, self.model.feature_importances_))

            # Store metrics
            self.model_metrics = ModelMetrics(
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                auc_score=auc,
                feature_importances=feature_importance_dict,
                confusion_matrix=confusion_matrix(y_test, y_pred),
                validation_date=datetime.now(),
            )

            self.last_training_date = datetime.now()

            # Save model
            await self._save_model()

            logger.info(f"Model training completed. Accuracy: {accuracy:.3f}, AUC: {auc:.3f}")
            return self.model_metrics

        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise

    async def predict_closing_probability(
        self, conversation_context: Dict[str, Any], location: Optional[str] = None
    ) -> ModelPrediction:
        """
        Predict closing probability for a lead.

        Args:
            conversation_context: Full conversation context with history and preferences
            location: Target location for market analysis

        Returns:
            ModelPrediction with probability and insights
        """
        cache_key = f"closing_pred:{hash(str(conversation_context))}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        try:
            # Ensure model is loaded before prediction
            if not await self._ensure_model_loaded():
                logger.warning("Model not available. Using baseline prediction.")
                return await self._baseline_prediction(conversation_context)

            # Extract features
            conv_features = await self.feature_engineer.extract_conversation_features(conversation_context)
            market_features = await self.feature_engineer.extract_market_features(location)

            # Create feature vector
            feature_vector = self.feature_engineer.create_feature_vector(conv_features, market_features)

            # Ensure feature vector matches trained model
            if len(feature_vector) != len(self.feature_names):
                logger.error(f"Feature mismatch: expected {len(self.feature_names)}, got {len(feature_vector)}")
                return await self._baseline_prediction(conversation_context)

            # Scale features
            feature_vector_scaled = self.scaler.transform([feature_vector])

            # Predict probability
            closing_probability = self.model.predict_proba(feature_vector_scaled)[0][1]

            # Calculate confidence interval using prediction variance
            # For Random Forest, we can use prediction variance across trees
            tree_predictions = [tree.predict_proba(feature_vector_scaled)[0][1] for tree in self.model.estimators_]
            prediction_std = np.std(tree_predictions)
            confidence_interval = (
                max(0.0, closing_probability - 1.96 * prediction_std),
                min(1.0, closing_probability + 1.96 * prediction_std),
            )

            # Model confidence based on prediction uncertainty
            model_confidence = 1.0 - min(prediction_std * 2, 1.0)

            # Analyze risk factors and positive signals
            feature_importance_dict = dict(zip(self.feature_names, self.model.feature_importances_))
            risk_factors, positive_signals = await self._analyze_prediction_factors(
                feature_vector, feature_importance_dict, conv_features
            )

            prediction = ModelPrediction(
                closing_probability=closing_probability,
                confidence_interval=confidence_interval,
                risk_factors=risk_factors,
                positive_signals=positive_signals,
                model_confidence=model_confidence,
                feature_importance=feature_importance_dict,
            )

            # Cache prediction for 30 minutes
            await cache.set(cache_key, prediction, 1800)
            return prediction

        except Exception as e:
            logger.error(f"Error predicting closing probability: {e}")
            return await self._baseline_prediction(conversation_context)

    async def _baseline_prediction(self, conversation_context: Dict[str, Any]) -> ModelPrediction:
        """
        Provide baseline prediction when model is not available.

        Args:
            conversation_context: Conversation context

        Returns:
            Baseline ModelPrediction
        """
        # Simple rule-based baseline
        prefs = conversation_context.get("extracted_preferences", {})
        message_count = len(conversation_context.get("conversation_history", []))

        # Simple scoring based on qualification completeness
        required_fields = ["budget", "location", "timeline", "motivation"]
        completed_fields = sum(1 for field in required_fields if prefs.get(field))
        baseline_probability = min(completed_fields / len(required_fields) * 0.8, 0.8)

        # Boost for high engagement
        if message_count > 10:
            baseline_probability = min(baseline_probability + 0.1, 0.9)

        return ModelPrediction(
            closing_probability=baseline_probability,
            confidence_interval=(max(0.0, baseline_probability - 0.2), min(1.0, baseline_probability + 0.2)),
            risk_factors=["Limited historical data", "Model not trained"],
            positive_signals=[f"Completed {completed_fields}/{len(required_fields)} key qualifications"],
            model_confidence=0.5,
            feature_importance={},
        )

    async def _analyze_prediction_factors(
        self, feature_vector: np.ndarray, feature_importances: Dict[str, float], conv_features: ConversationFeatures
    ) -> Tuple[List[str], List[str]]:
        """
        Analyze factors contributing to prediction.

        Args:
            feature_vector: Input features
            feature_importances: Feature importance scores
            conv_features: Conversation features for context

        Returns:
            Tuple of (risk_factors, positive_signals)
        """
        risk_factors = []
        positive_signals = []

        # Analyze key features
        feature_names = self.feature_engineer.get_feature_names()

        # Check qualification completeness
        qual_idx = feature_names.index("qualification_completeness")
        if feature_vector[qual_idx] < 0.5:
            risk_factors.append("Incomplete lead qualification")
        elif feature_vector[qual_idx] > 0.8:
            positive_signals.append("Highly qualified lead")

        # Check engagement
        engagement_idx = feature_names.index("engagement_score")
        if feature_vector[engagement_idx] < 0.3:
            risk_factors.append("Low engagement level")
        elif feature_vector[engagement_idx] > 0.7:
            positive_signals.append("High engagement and interest")

        # Check budget alignment
        budget_idx = feature_names.index("budget_market_ratio")
        if feature_vector[budget_idx] < 0.5:
            risk_factors.append("Budget below market expectations")
        elif feature_vector[budget_idx] > 0.8:
            positive_signals.append("Budget well-aligned with market")

        # Check urgency
        urgency_idx = feature_names.index("urgency_score")
        if feature_vector[urgency_idx] > 0.7:
            positive_signals.append("High urgency and timeline pressure")
        elif feature_vector[urgency_idx] < 0.2:
            risk_factors.append("Low urgency, extended timeline")

        # Check sentiment
        sentiment_idx = feature_names.index("sentiment_norm")
        if feature_vector[sentiment_idx] < 0.3:
            risk_factors.append("Negative sentiment in conversations")
        elif feature_vector[sentiment_idx] > 0.7:
            positive_signals.append("Positive sentiment and enthusiasm")

        return risk_factors, positive_signals

    async def get_model_performance(self) -> Optional[ModelMetrics]:
        """
        Get current model performance metrics.

        Returns:
            ModelMetrics if model is trained, None otherwise
        """
        return self.model_metrics

    async def needs_retraining(self, max_age_days: int = 30, min_new_data_points: int = 50) -> bool:
        """
        Check if model needs retraining.

        Args:
            max_age_days: Maximum age of model before retraining
            min_new_data_points: Minimum new data points to trigger retraining

        Returns:
            True if model needs retraining
        """
        if self.last_training_date is None:
            return True

        # Check age
        age_days = (datetime.now() - self.last_training_date).days
        if age_days > max_age_days:
            logger.info(f"Model is {age_days} days old, needs retraining")
            return True

        # In production, check for new data points
        # For now, assume we don't have enough new data
        return False

    def generate_synthetic_training_data(self, num_samples: int = 1000, positive_rate: float = 0.3) -> pd.DataFrame:
        """
        Generate synthetic training data for initial model training.

        Args:
            num_samples: Number of synthetic samples to generate
            positive_rate: Proportion of positive (closed) examples

        Returns:
            DataFrame with features and target variable
        """
        logger.info(f"Generating {num_samples} synthetic training samples...")

        # Get feature names
        feature_names = self.feature_engineer.get_feature_names()
        num_features = len(feature_names)

        # Generate feature matrix
        X = np.random.random((num_samples, num_features))

        # Create realistic patterns for closing probability
        closing_probabilities = []

        for i in range(num_samples):
            # Base probability from qualification completeness
            qual_score = X[i, feature_names.index("qualification_completeness")]
            engagement = X[i, feature_names.index("engagement_score")]
            urgency = X[i, feature_names.index("urgency_score")]
            budget_ratio = X[i, feature_names.index("budget_market_ratio")]

            # Calculate probability based on realistic patterns
            prob = (
                qual_score * 0.4  # Qualification is most important
                + engagement * 0.3  # Engagement matters
                + urgency * 0.2  # Urgency helps
                + budget_ratio * 0.1  # Budget alignment
            )

            # Add some noise
            prob += np.random.normal(0, 0.1)
            prob = max(0, min(1, prob))  # Clip to [0, 1]

            closing_probabilities.append(prob)

        # Convert probabilities to binary outcomes
        y = np.random.binomial(1, closing_probabilities)

        # Adjust to match desired positive rate
        current_positive_rate = np.mean(y)
        if current_positive_rate != positive_rate:
            # Simple adjustment by flipping some labels
            diff = positive_rate - current_positive_rate
            if diff > 0:  # Need more positives
                negatives = np.where(y == 0)[0]
                flip_count = int(abs(diff) * len(y))
                flip_indices = np.random.choice(negatives, min(flip_count, len(negatives)), replace=False)
                y[flip_indices] = 1
            else:  # Need fewer positives
                positives = np.where(y == 1)[0]
                flip_count = int(abs(diff) * len(y))
                flip_indices = np.random.choice(positives, min(flip_count, len(positives)), replace=False)
                y[flip_indices] = 0

        # Create DataFrame
        data = pd.DataFrame(X, columns=feature_names)
        data["closed"] = y

        logger.info(f"Generated synthetic data with {np.mean(y):.2%} positive rate")
        return data
