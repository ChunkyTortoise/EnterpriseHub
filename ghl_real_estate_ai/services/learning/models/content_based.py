"""
Content-Based Filtering Model for Property Recommendations

Property feature similarity-based recommendations using user preference profiles
learned from behavioral patterns and property characteristics.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
import uuid
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler, LabelEncoder
from collections import defaultdict, Counter

from ..interfaces import (
    ILearningModel, ModelType, FeatureVector, ModelPrediction,
    TrainingResult, LearningContext, ConfidenceLevel,
    BehavioralEvent, EventType, ModelNotTrainedError,
    PredictionError, TrainingError
)

logger = logging.getLogger(__name__)


class ContentBasedModel(ILearningModel):
    """
    Property feature similarity-based recommendations using user preferences.

    Uses property characteristics and user interaction patterns to build
    preference profiles and calculate property similarity for recommendations.

    Key Features:
    - Property feature vector construction from listing characteristics
    - User preference profile learning from behavioral patterns
    - TF-IDF and cosine similarity for property matching
    - Feature importance scoring for explainable recommendations
    - Dynamic preference adaptation based on user feedback
    """

    def __init__(
        self,
        similarity_threshold: float = 0.1,
        min_interactions: int = 3,
        max_features: int = 1000,
        preference_decay: float = 0.9
    ):
        """
        Initialize content-based filtering model.

        Args:
            similarity_threshold: Minimum similarity for recommendations
            min_interactions: Minimum interactions needed for user profile
            max_features: Maximum features for TF-IDF vectorization
            preference_decay: Decay factor for older preferences
        """
        self._model_id = f"content_based_{uuid.uuid4().hex[:8]}"
        self._similarity_threshold = similarity_threshold
        self._min_interactions = min_interactions
        self._max_features = max_features
        self._preference_decay = preference_decay

        # Feature processing
        self._tfidf_vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words='english',
            lowercase=True,
            ngram_range=(1, 2)
        )
        self._scaler = StandardScaler()
        self._label_encoders: Dict[str, LabelEncoder] = {}

        # Property and user data
        self._property_features: Dict[str, Dict[str, Any]] = {}
        self._property_vectors: Optional[np.ndarray] = None
        self._property_ids: List[str] = []
        self._user_profiles: Dict[str, Dict[str, float]] = {}
        self._user_preferences: Dict[str, Dict[str, float]] = {}

        # Feature importance
        self._feature_importance: Dict[str, float] = {}
        self._feature_names: List[str] = []

        # Training state
        self._is_trained = False
        self._model_version = "1.0"
        self._training_timestamp: Optional[datetime] = None

        # Performance tracking
        self._prediction_count = 0
        self._training_count = 0

        logger.info(f"Initialized ContentBasedModel {self._model_id}")

    @property
    def model_id(self) -> str:
        """Unique identifier for this model"""
        return self._model_id

    @property
    def model_type(self) -> ModelType:
        """Type of machine learning model"""
        return ModelType.CONTENT_BASED

    @property
    def is_trained(self) -> bool:
        """Whether model has been trained and is ready for predictions"""
        return self._is_trained

    async def train(
        self,
        features: List[FeatureVector],
        targets: List[float],
        validation_features: Optional[List[FeatureVector]] = None,
        validation_targets: Optional[List[float]] = None,
        context: Optional[LearningContext] = None
    ) -> TrainingResult:
        """
        Train content-based model using property features and user interactions.

        Args:
            features: Feature vectors containing property and user data
            targets: Interaction scores (ratings, engagement, etc.)
            validation_features: Optional validation features
            validation_targets: Optional validation targets
            context: Training context

        Returns:
            Training result with metrics and model information
        """
        start_time = datetime.now()
        training_id = f"cb_training_{uuid.uuid4().hex[:8]}"

        try:
            logger.info(f"Starting content-based training {training_id}")

            # Validate input
            if len(features) != len(targets):
                raise TrainingError("Features and targets length mismatch")

            if len(features) < self._min_interactions:
                raise TrainingError(f"Need at least {self._min_interactions} interactions for training")

            # Extract property features and user interactions
            property_data, user_interactions = self._extract_training_data(features, targets)

            if len(property_data) == 0:
                raise TrainingError("No property data extracted from features")

            logger.info(f"Extracted {len(property_data)} properties and {len(user_interactions)} interactions")

            # Build property feature matrix
            property_vectors, property_ids = await self._build_property_vectors(property_data)

            # Store property data
            self._property_features = property_data
            self._property_vectors = property_vectors
            self._property_ids = property_ids

            # Build user preference profiles
            user_profiles = self._build_user_profiles(user_interactions, property_data)
            self._user_profiles = user_profiles
            self._user_preferences = self._extract_user_preferences(user_interactions, property_data)

            logger.info(f"Built profiles for {len(user_profiles)} users")

            # Calculate feature importance
            self._feature_importance = self._calculate_feature_importance(property_data, user_interactions)

            # Calculate training metrics
            training_loss = await self._calculate_training_loss(features, targets)
            validation_loss = None

            if validation_features and validation_targets:
                validation_loss = await self._calculate_validation_loss(
                    validation_features, validation_targets
                )

            # Mark as trained
            self._is_trained = True
            self._training_timestamp = datetime.now()
            self._training_count += 1

            duration = (datetime.now() - start_time).total_seconds()

            # Create training result
            result = TrainingResult(
                model_id=self._model_id,
                training_id=training_id,
                training_timestamp=start_time,
                training_loss=training_loss,
                validation_loss=validation_loss,
                model_version=self._model_version,
                training_duration_seconds=duration,
                training_samples=len(features),
                validation_samples=len(validation_features) if validation_features else 0,
                hyperparameters={
                    "similarity_threshold": self._similarity_threshold,
                    "min_interactions": self._min_interactions,
                    "max_features": self._max_features,
                    "preference_decay": self._preference_decay
                },
                feature_names=list(self._feature_importance.keys()),
                success=True
            )

            logger.info(f"Training completed successfully in {duration:.2f}s")
            return result

        except Exception as e:
            error_msg = f"Training failed: {str(e)}"
            logger.error(error_msg)

            return TrainingResult(
                model_id=self._model_id,
                training_id=training_id,
                training_timestamp=start_time,
                success=False,
                error_message=error_msg
            )

    async def predict(
        self,
        features: FeatureVector,
        context: Optional[LearningContext] = None
    ) -> ModelPrediction:
        """
        Make prediction for a single entity (recommend properties for lead).

        Args:
            features: Feature vector for lead
            context: Prediction context

        Returns:
            Model prediction with confidence and reasoning
        """
        if not self._is_trained:
            raise ModelNotTrainedError("Model must be trained before making predictions")

        start_time = datetime.now()

        try:
            # Extract lead ID from features
            lead_id = features.entity_id

            # Check if lead has profile
            if lead_id not in self._user_profiles:
                return await self._handle_cold_start_prediction(features, context)

            # Get user preference profile
            user_profile = self._user_profiles[lead_id]

            # Calculate scores for all properties
            property_scores = self._calculate_property_scores(user_profile)

            if len(property_scores) == 0:
                raise PredictionError("No properties available for prediction")

            # Get best recommendation
            best_property_id, best_score = max(property_scores.items(), key=lambda x: x[1])

            # Calculate confidence
            confidence = self._calculate_confidence(lead_id, best_property_id, best_score, property_scores)

            # Determine confidence level
            confidence_level = self._determine_confidence_level(confidence)

            # Generate reasoning
            reasoning = self._generate_reasoning(lead_id, best_property_id, user_profile)

            # Calculate feature importance for this prediction
            feature_importance = self._calculate_prediction_feature_importance(
                user_profile, best_property_id
            )

            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self._prediction_count += 1

            return ModelPrediction(
                entity_id=best_property_id,
                predicted_value=float(best_score),
                confidence=confidence,
                confidence_level=confidence_level,
                model_id=self._model_id,
                model_version=self._model_version,
                feature_importance=feature_importance,
                reasoning=reasoning,
                processing_time_ms=processing_time,
                model_metadata={
                    "prediction_type": "content_based",
                    "user_profile_size": len(user_profile),
                    "total_properties": len(self._property_ids),
                    "prediction_count": self._prediction_count
                }
            )

        except Exception as e:
            error_msg = f"Prediction failed: {str(e)}"
            logger.error(error_msg)
            raise PredictionError(error_msg)

    async def predict_batch(
        self,
        features: List[FeatureVector],
        context: Optional[LearningContext] = None
    ) -> List[ModelPrediction]:
        """
        Make predictions for multiple entities efficiently.

        Args:
            features: List of feature vectors
            context: Prediction context

        Returns:
            List of model predictions
        """
        if not self._is_trained:
            raise ModelNotTrainedError("Model must be trained before making predictions")

        logger.info(f"Making batch predictions for {len(features)} entities")

        # Process predictions in parallel
        tasks = [self.predict(feature, context) for feature in features]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log errors
        predictions = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch prediction {i} failed: {result}")
                # Create error prediction
                predictions.append(ModelPrediction(
                    entity_id=features[i].entity_id,
                    predicted_value=0.0,
                    confidence=0.0,
                    confidence_level=ConfidenceLevel.UNCERTAIN,
                    model_id=self._model_id,
                    model_version=self._model_version,
                    reasoning=[f"Prediction failed: {str(result)}"]
                ))
            else:
                predictions.append(result)

        logger.info(f"Completed batch predictions: {len(predictions)} results")
        return predictions

    async def update_online(
        self,
        features: FeatureVector,
        target: float,
        context: Optional[LearningContext] = None
    ) -> bool:
        """
        Update model with new training example (online learning).

        Args:
            features: New feature vector
            target: Target value
            context: Learning context

        Returns:
            True if update was successful
        """
        try:
            logger.info(f"Online update for {features.entity_id}")

            # Extract user and property information
            lead_id = features.entity_id
            property_id = features.metadata.get("property_id")

            if not property_id:
                logger.warning("No property_id in features metadata for online update")
                return False

            # Update user preferences
            if lead_id not in self._user_preferences:
                self._user_preferences[lead_id] = {}

            # Extract property features from the interaction
            property_features = self._extract_property_features_from_vector(features)

            # Update preferences based on interaction strength
            for feature_name, feature_value in property_features.items():
                if feature_name not in self._user_preferences[lead_id]:
                    self._user_preferences[lead_id][feature_name] = 0.0

                # Update with exponential moving average
                current_pref = self._user_preferences[lead_id][feature_name]
                updated_pref = self._preference_decay * current_pref + (1 - self._preference_decay) * target

                self._user_preferences[lead_id][feature_name] = updated_pref

            logger.info(f"Online update completed for {lead_id}")
            return True

        except Exception as e:
            logger.error(f"Online update failed: {str(e)}")
            return False

    async def save(self, path: str) -> bool:
        """
        Save model to disk.

        Args:
            path: File path to save model

        Returns:
            True if save was successful
        """
        try:
            model_data = {
                "model_id": self._model_id,
                "model_version": self._model_version,
                "similarity_threshold": self._similarity_threshold,
                "min_interactions": self._min_interactions,
                "max_features": self._max_features,
                "preference_decay": self._preference_decay,
                "is_trained": self._is_trained,
                "training_timestamp": self._training_timestamp.isoformat() if self._training_timestamp else None,
                "tfidf_vectorizer": self._tfidf_vectorizer,
                "scaler": self._scaler,
                "label_encoders": self._label_encoders,
                "property_features": self._property_features,
                "property_vectors": self._property_vectors,
                "property_ids": self._property_ids,
                "user_profiles": self._user_profiles,
                "user_preferences": self._user_preferences,
                "feature_importance": self._feature_importance,
                "feature_names": self._feature_names,
                "prediction_count": self._prediction_count,
                "training_count": self._training_count
            }

            joblib.dump(model_data, path)
            logger.info(f"Model saved to {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save model: {str(e)}")
            return False

    async def load(self, path: str) -> bool:
        """
        Load model from disk.

        Args:
            path: File path to load model from

        Returns:
            True if load was successful
        """
        try:
            model_data = joblib.load(path)

            self._model_id = model_data["model_id"]
            self._model_version = model_data["model_version"]
            self._similarity_threshold = model_data["similarity_threshold"]
            self._min_interactions = model_data["min_interactions"]
            self._max_features = model_data["max_features"]
            self._preference_decay = model_data["preference_decay"]
            self._is_trained = model_data["is_trained"]
            self._training_timestamp = datetime.fromisoformat(model_data["training_timestamp"]) if model_data["training_timestamp"] else None
            self._tfidf_vectorizer = model_data["tfidf_vectorizer"]
            self._scaler = model_data["scaler"]
            self._label_encoders = model_data["label_encoders"]
            self._property_features = model_data["property_features"]
            self._property_vectors = model_data["property_vectors"]
            self._property_ids = model_data["property_ids"]
            self._user_profiles = model_data["user_profiles"]
            self._user_preferences = model_data["user_preferences"]
            self._feature_importance = model_data["feature_importance"]
            self._feature_names = model_data["feature_names"]
            self._prediction_count = model_data.get("prediction_count", 0)
            self._training_count = model_data.get("training_count", 0)

            logger.info(f"Model loaded from {path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get feature importance scores for explainability.

        Returns:
            Dictionary mapping feature names to importance scores
        """
        return self._feature_importance.copy()

    # Helper methods

    def _extract_training_data(
        self,
        features: List[FeatureVector],
        targets: List[float]
    ) -> Tuple[Dict[str, Dict[str, Any]], List[Tuple[str, str, float]]]:
        """Extract property features and user interactions from training data"""
        property_data = {}
        user_interactions = []

        for feature, target in zip(features, targets):
            lead_id = feature.entity_id

            # Extract property information
            property_id = (
                feature.metadata.get("property_id") or
                feature.categorical_features.get("target_property_id") or
                feature.text_features.get("property_id")
            )

            if property_id:
                # Store property features
                if property_id not in property_data:
                    property_data[property_id] = self._extract_property_features_from_vector(feature)

                # Store user interaction
                user_interactions.append((lead_id, property_id, target))

        logger.info(f"Extracted {len(property_data)} properties, {len(user_interactions)} interactions")
        return property_data, user_interactions

    def _extract_property_features_from_vector(self, feature: FeatureVector) -> Dict[str, Any]:
        """Extract property features from feature vector"""
        property_features = {}

        # Numerical features (price, size, etc.)
        for name, value in feature.numerical_features.items():
            if any(keyword in name.lower() for keyword in ['price', 'size', 'sqft', 'bed', 'bath', 'lot']):
                property_features[name] = value

        # Categorical features (type, location, etc.)
        for name, value in feature.categorical_features.items():
            if any(keyword in name.lower() for keyword in ['type', 'location', 'style', 'status']):
                property_features[name] = value

        # Text features (descriptions, amenities)
        for name, value in feature.text_features.items():
            if any(keyword in name.lower() for keyword in ['description', 'amenities', 'features']):
                property_features[name] = value

        return property_features

    async def _build_property_vectors(
        self,
        property_data: Dict[str, Dict[str, Any]]
    ) -> Tuple[np.ndarray, List[str]]:
        """Build property feature vectors using TF-IDF and scaling"""

        property_ids = list(property_data.keys())
        if not property_ids:
            return np.array([]), []

        # Separate numerical and text features
        numerical_features = []
        text_features = []
        categorical_features = []

        # Collect all feature names for consistency
        all_numerical_features = set()
        all_categorical_features = set()

        for prop_id, features in property_data.items():
            for name, value in features.items():
                if isinstance(value, (int, float)):
                    all_numerical_features.add(name)
                elif isinstance(value, str):
                    if any(keyword in name.lower() for keyword in ['description', 'amenities', 'features']):
                        # Text feature
                        pass
                    else:
                        # Categorical feature
                        all_categorical_features.add(name)

        # Build feature matrices
        for prop_id in property_ids:
            features = property_data[prop_id]

            # Numerical features
            num_features = []
            for feature_name in sorted(all_numerical_features):
                num_features.append(features.get(feature_name, 0.0))
            numerical_features.append(num_features)

            # Categorical features
            cat_features = []
            for feature_name in sorted(all_categorical_features):
                cat_features.append(features.get(feature_name, "unknown"))
            categorical_features.append(cat_features)

            # Text features (combine all text)
            text_content = " ".join([
                str(value) for name, value in features.items()
                if isinstance(value, str) and any(keyword in name.lower()
                    for keyword in ['description', 'amenities', 'features'])
            ])
            text_features.append(text_content if text_content.strip() else "no description")

        # Process features
        vectors = []

        # Numerical features
        if numerical_features and len(numerical_features[0]) > 0:
            numerical_matrix = self._scaler.fit_transform(numerical_features)
            vectors.append(numerical_matrix)

        # Categorical features (label encoding)
        if categorical_features and len(categorical_features[0]) > 0:
            categorical_matrix = []
            for feature_idx, feature_name in enumerate(sorted(all_categorical_features)):
                if feature_name not in self._label_encoders:
                    self._label_encoders[feature_name] = LabelEncoder()

                feature_values = [cat_features[feature_idx] for cat_features in categorical_features]
                encoded_values = self._label_encoders[feature_name].fit_transform(feature_values)
                categorical_matrix.append(encoded_values)

            if categorical_matrix:
                categorical_matrix = np.array(categorical_matrix).T
                vectors.append(categorical_matrix)

        # Text features (TF-IDF)
        if text_features:
            tfidf_matrix = self._tfidf_vectorizer.fit_transform(text_features).toarray()
            vectors.append(tfidf_matrix)

        # Combine all feature vectors
        if vectors:
            combined_vectors = np.hstack(vectors)
        else:
            # Fallback: create identity matrix
            combined_vectors = np.eye(len(property_ids))

        logger.info(f"Built property vectors: {combined_vectors.shape}")
        return combined_vectors, property_ids

    def _build_user_profiles(
        self,
        user_interactions: List[Tuple[str, str, float]],
        property_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """Build user preference profiles from interactions"""

        user_profiles = defaultdict(lambda: defaultdict(float))

        # Group interactions by user
        user_interaction_groups = defaultdict(list)
        for lead_id, property_id, score in user_interactions:
            user_interaction_groups[lead_id].append((property_id, score))

        # Build profiles
        for lead_id, interactions in user_interaction_groups.items():
            if len(interactions) < self._min_interactions:
                continue

            # Weighted feature preferences
            total_weight = 0
            for property_id, score in interactions:
                if property_id in property_data:
                    weight = max(score, 0.1)  # Minimum weight
                    total_weight += weight

                    # Add weighted features to profile
                    for feature_name, feature_value in property_data[property_id].items():
                        if isinstance(feature_value, (int, float)):
                            user_profiles[lead_id][feature_name] += feature_value * weight
                        elif isinstance(feature_value, str):
                            # For categorical/text features, use frequency
                            feature_key = f"{feature_name}_{feature_value}"
                            user_profiles[lead_id][feature_key] += weight

            # Normalize by total weight
            if total_weight > 0:
                for feature_name in user_profiles[lead_id]:
                    user_profiles[lead_id][feature_name] /= total_weight

        return dict(user_profiles)

    def _extract_user_preferences(
        self,
        user_interactions: List[Tuple[str, str, float]],
        property_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """Extract explicit user preferences"""

        user_preferences = defaultdict(lambda: defaultdict(float))

        for lead_id, property_id, score in user_interactions:
            if property_id in property_data and score > 0.5:  # Only positive interactions
                for feature_name, feature_value in property_data[property_id].items():
                    if isinstance(feature_value, (int, float)):
                        user_preferences[lead_id][feature_name] = max(
                            user_preferences[lead_id][feature_name], score
                        )

        return dict(user_preferences)

    def _calculate_property_scores(self, user_profile: Dict[str, float]) -> Dict[str, float]:
        """Calculate scores for all properties based on user profile"""

        property_scores = {}

        if self._property_vectors is None or len(self._property_ids) == 0:
            return property_scores

        # Create user preference vector
        user_vector = self._create_user_vector(user_profile)

        # Calculate similarity with all properties
        if user_vector is not None and len(user_vector) == self._property_vectors.shape[1]:
            similarities = cosine_similarity([user_vector], self._property_vectors)[0]

            for i, property_id in enumerate(self._property_ids):
                similarity = similarities[i]
                if similarity >= self._similarity_threshold:
                    property_scores[property_id] = float(similarity)

        return property_scores

    def _create_user_vector(self, user_profile: Dict[str, float]) -> Optional[np.ndarray]:
        """Create user preference vector matching property vector dimensions"""

        if self._property_vectors is None:
            return None

        # For simplicity, use average of property vectors weighted by preferences
        # In production, this should be more sophisticated
        vector_dim = self._property_vectors.shape[1]
        user_vector = np.zeros(vector_dim)

        # Use preference weights to create average profile
        total_weight = sum(user_profile.values())
        if total_weight > 0:
            # Simple averaging approach - can be enhanced
            user_vector = np.mean(self._property_vectors, axis=0)

        return user_vector

    def _calculate_confidence(
        self,
        lead_id: str,
        property_id: str,
        score: float,
        all_scores: Dict[str, float]
    ) -> float:
        """Calculate prediction confidence"""

        # Base confidence from score
        max_score = max(all_scores.values()) if all_scores else 1.0
        min_score = min(all_scores.values()) if all_scores else 0.0
        score_confidence = (score - min_score) / (max_score - min_score + 1e-8)

        # Profile completeness factor
        profile_size = len(self._user_profiles.get(lead_id, {}))
        profile_confidence = min(profile_size / 10, 1.0)  # Normalize to 10 features

        # Combined confidence
        confidence = 0.7 * score_confidence + 0.3 * profile_confidence

        return float(np.clip(confidence, 0.0, 1.0))

    def _determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """Determine confidence level from numerical confidence"""
        if confidence >= 0.8:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.6:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.4:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCERTAIN

    def _generate_reasoning(
        self,
        lead_id: str,
        property_id: str,
        user_profile: Dict[str, float]
    ) -> List[str]:
        """Generate human-readable reasoning for the prediction"""
        reasoning = []

        # Profile-based reasoning
        profile_size = len(user_profile)
        reasoning.append(f"Recommendation based on {profile_size} learned preferences")

        # Feature matching
        if property_id in self._property_features:
            property_features = self._property_features[property_id]
            matching_features = []

            for feature_name in property_features:
                if any(pref_name in feature_name for pref_name in user_profile):
                    matching_features.append(feature_name)

            if matching_features:
                reasoning.append(f"Matches user preferences in: {', '.join(matching_features[:3])}")

        # Content-based signal
        reasoning.append("Recommendation uses property characteristics and user history")

        return reasoning

    def _calculate_prediction_feature_importance(
        self,
        user_profile: Dict[str, float],
        property_id: str
    ) -> Dict[str, float]:
        """Calculate feature importance for specific prediction"""
        importance = {}

        # User preference importance
        for feature_name, preference_value in user_profile.items():
            importance[f"user_pref_{feature_name}"] = abs(preference_value)

        # Property feature importance
        if property_id in self._property_features:
            property_features = self._property_features[property_id]
            for feature_name, feature_value in property_features.items():
                if isinstance(feature_value, (int, float)):
                    importance[f"property_{feature_name}"] = abs(feature_value) * 0.1

        return importance

    def _calculate_feature_importance(
        self,
        property_data: Dict[str, Dict[str, Any]],
        user_interactions: List[Tuple[str, str, float]]
    ) -> Dict[str, float]:
        """Calculate overall feature importance for explainability"""
        importance = defaultdict(float)

        # Feature frequency analysis
        feature_counts = Counter()
        interaction_weights = defaultdict(float)

        for lead_id, property_id, score in user_interactions:
            if property_id in property_data:
                for feature_name, feature_value in property_data[property_id].items():
                    feature_counts[feature_name] += 1
                    interaction_weights[feature_name] += abs(score)

        # Calculate importance scores
        total_interactions = len(user_interactions)
        for feature_name, count in feature_counts.items():
            frequency_score = count / total_interactions
            weight_score = interaction_weights[feature_name] / total_interactions
            importance[feature_name] = 0.6 * frequency_score + 0.4 * weight_score

        return dict(importance)

    async def _calculate_training_loss(
        self,
        features: List[FeatureVector],
        targets: List[float]
    ) -> float:
        """Calculate training loss (RMSE)"""
        predictions = await self.predict_batch(features)
        predicted_values = [pred.predicted_value for pred in predictions]

        mse = np.mean([(pred - target) ** 2 for pred, target in zip(predicted_values, targets)])
        rmse = np.sqrt(mse)

        return float(rmse)

    async def _calculate_validation_loss(
        self,
        validation_features: List[FeatureVector],
        validation_targets: List[float]
    ) -> float:
        """Calculate validation loss"""
        predictions = await self.predict_batch(validation_features)
        predicted_values = [pred.predicted_value for pred in predictions]

        mse = np.mean([(pred - target) ** 2 for pred, target in zip(predicted_values, validation_targets)])
        rmse = np.sqrt(mse)

        return float(rmse)

    async def _handle_cold_start_prediction(
        self,
        features: FeatureVector,
        context: Optional[LearningContext]
    ) -> ModelPrediction:
        """Handle prediction for new/unknown lead (cold start)"""

        lead_id = features.entity_id

        # Use most popular or average property
        if self._property_ids:
            popular_property_id = self._property_ids[0]
            predicted_value = 0.4  # Conservative score
        else:
            popular_property_id = "unknown"
            predicted_value = 0.0

        return ModelPrediction(
            entity_id=popular_property_id,
            predicted_value=predicted_value,
            confidence=0.3,  # Low confidence for cold start
            confidence_level=ConfidenceLevel.LOW,
            model_id=self._model_id,
            model_version=self._model_version,
            reasoning=[
                "Cold start prediction for new lead",
                "Using property popularity fallback",
                "Limited confidence due to no preference history"
            ],
            model_metadata={
                "prediction_type": "cold_start",
                "fallback_method": "property_popularity"
            }
        )