"""
Behavioral Learning Engine Implementation.
Implements Collaborative Filtering and Content-Based models for real estate personalization.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from .interfaces import (
    ConfidenceLevel,
    FeatureVector,
    ILearningModel,
    LearningMode,
    ModelPrediction,
    ModelType,
    TrainingResult,
)


class CollaborativeFilteringModel(ILearningModel):
    """
    Implements a Collaborative Filtering model using Matrix Factorization principles.
    In a production system, this would use a library like Surprise or LightFM.
    This implementation uses a simplified SVD approach.
    """

    def __init__(self, model_id: str = "cf_v1"):
        self._model_id = model_id
        self._is_trained = False
        self.user_factors = {}
        self.item_factors = {}
        self.global_mean = 0.0

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def model_type(self) -> ModelType:
        return ModelType.COLLABORATIVE_FILTERING

    @property
    def is_trained(self) -> bool:
        return self._is_trained

    async def train(self, features: List[FeatureVector], targets: List[float], **kwargs) -> TrainingResult:
        # Simplified training logic: compute averages per user and item
        # In real world, we'd do SGD/ALS here
        user_ratings = {}
        item_ratings = {}

        for i, fv in enumerate(features):
            uid = fv.entity_id
            pid = fv.metadata.get("property_id")
            rating = targets[i]

            if uid not in user_ratings:
                user_ratings[uid] = []
            if pid not in item_ratings:
                item_ratings[pid] = []

            user_ratings[uid].append(rating)
            item_ratings[pid].append(rating)

        self.user_factors = {uid: float(np.mean(ratings)) for uid, ratings in user_ratings.items()}
        self.item_factors = {pid: float(np.mean(ratings)) for pid, ratings in item_ratings.items()}
        self.global_mean = float(np.mean(targets)) if targets else 0.0

        self._is_trained = True
        return TrainingResult(
            model_id=self._model_id,
            training_id="train_" + datetime.now().strftime("%Y%m%d%H%M%S"),
            training_timestamp=datetime.now(),
            success=True,
            training_samples=len(features),
        )

    async def predict(self, features: FeatureVector, **kwargs) -> ModelPrediction:
        uid = features.entity_id
        pid = features.metadata.get("property_id")

        # Simple baseline: Global Mean + User Bias + Item Bias
        user_bias = self.user_factors.get(uid, 0) - self.global_mean
        item_bias = self.item_factors.get(pid, 0) - self.global_mean

        score = self.global_mean + user_bias + item_bias
        # Clamp score to [0, 1]
        score = max(0.0, min(1.0, score))

        return ModelPrediction(
            entity_id=uid,
            predicted_value=float(score),
            confidence=0.7 if uid in self.user_factors else 0.3,
            confidence_level=ConfidenceLevel.MEDIUM if uid in self.user_factors else ConfidenceLevel.LOW,
            model_id=self._model_id,
            model_version="1.0",
            reasoning=[f"Based on user historical preferences (bias: {user_bias:.2f})"],
        )

    async def predict_batch(self, features: List[FeatureVector], **kwargs) -> List[ModelPrediction]:
        return [await self.predict(f) for f in features]

    async def update_online(self, features: FeatureVector, target: float, **kwargs) -> bool:
        # Simple online update (running average)
        uid = features.entity_id
        if uid in self.user_factors:
            self.user_factors[uid] = (self.user_factors[uid] * 0.9) + (target * 0.1)
        else:
            self.user_factors[uid] = target
        return True

    def _get_tenant_path(self, path: str, tenant_id: Optional[str] = None) -> str:
        if not tenant_id:
            return path
        directory, filename = os.path.split(path)
        return os.path.join(directory, f"{tenant_id}_{filename}")

    async def save(self, path: str, tenant_id: Optional[str] = None) -> bool:
        target_path = self._get_tenant_path(path, tenant_id)
        data = {
            "model_id": self._model_id,
            "user_factors": self.user_factors,
            "item_factors": self.item_factors,
            "global_mean": self.global_mean,
            "is_trained": self._is_trained,
        }
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w") as f:
            json.dump(data, f)
        return True

    async def load(self, path: str, tenant_id: Optional[str] = None) -> bool:
        target_path = self._get_tenant_path(path, tenant_id)
        if not os.path.exists(target_path):
            return False
        with open(target_path, "r") as f:
            data = json.load(f)
            self.user_factors = data.get("user_factors", {})
            self.item_factors = data.get("item_factors", {})
            self.global_mean = data.get("global_mean", 0.0)
            self._is_trained = data.get("is_trained", False)
        return True

    def get_feature_importance(self) -> Dict[str, float]:
        return {}


class ContentBasedModel(ILearningModel):
    """
    Implements a Content-Based Filtering model.
    Uses cosine similarity between user preference vectors and property feature vectors.
    """

    def __init__(self, model_id: str = "cb_v1"):
        self._model_id = model_id
        self._is_trained = False
        self.user_profiles = {}  # uid -> weight vector

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def model_type(self) -> ModelType:
        return ModelType.CONTENT_BASED

    @property
    def is_trained(self) -> bool:
        return self._is_trained

    async def train(self, features: List[FeatureVector], targets: List[float], **kwargs) -> TrainingResult:
        # Build user profiles by aggregating features of items they liked
        for i, fv in enumerate(features):
            uid = fv.entity_id
            rating = targets[i]

            # Simplified: Use numerical features as the vector
            vec = np.array(list(fv.numerical_features.values()))

            if uid not in self.user_profiles:
                self.user_profiles[uid] = vec * rating
            else:
                self.user_profiles[uid] += vec * rating

        self._is_trained = True
        return TrainingResult(
            model_id=self._model_id,
            training_id="cb_train_" + datetime.now().strftime("%Y%m%d%H%M%S"),
            training_timestamp=datetime.now(),
            success=True,
        )

    async def predict(self, features: FeatureVector, **kwargs) -> ModelPrediction:
        uid = features.entity_id
        item_vec = np.array(list(features.numerical_features.values()))

        if uid not in self.user_profiles or len(item_vec) == 0:
            return ModelPrediction(
                entity_id=uid,
                predicted_value=0.5,
                confidence=0.1,
                confidence_level=ConfidenceLevel.UNCERTAIN,
                model_id=self._model_id,
                model_version="1.0",
            )

        user_vec = self.user_profiles[uid]

        # Cosine similarity
        norm_u = np.linalg.norm(user_vec)
        norm_i = np.linalg.norm(item_vec)

        if norm_u == 0 or norm_i == 0:
            score = 0.5
        else:
            score = np.dot(user_vec, item_vec) / (norm_u * norm_i)

        return ModelPrediction(
            entity_id=uid,
            predicted_value=float(score),
            confidence=0.8,
            confidence_level=ConfidenceLevel.HIGH,
            model_id=self._model_id,
            model_version="1.0",
            reasoning=["Matches user preference for specific property features."],
        )

    async def predict_batch(self, features: List[FeatureVector], **kwargs) -> List[ModelPrediction]:
        return [await self.predict(f) for f in features]

    async def update_online(self, features: FeatureVector, target: float, **kwargs) -> bool:
        uid = features.entity_id
        item_vec = np.array(list(features.numerical_features.values()))
        if uid in self.user_profiles:
            self.user_profiles[uid] += item_vec * target
        else:
            self.user_profiles[uid] = item_vec * target
        return True

    def _get_tenant_path(self, path: str, tenant_id: Optional[str] = None) -> str:
        if not tenant_id:
            return path
        directory, filename = os.path.split(path)
        return os.path.join(directory, f"{tenant_id}_{filename}")

    async def save(self, path: str, tenant_id: Optional[str] = None) -> bool:
        target_path = self._get_tenant_path(path, tenant_id)
        # Convert numpy arrays to lists for JSON serialization
        serializable_profiles = {uid: vec.tolist() for uid, vec in self.user_profiles.items()}
        data = {"model_id": self._model_id, "user_profiles": serializable_profiles, "is_trained": self._is_trained}
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w") as f:
            json.dump(data, f)
        return True

    async def load(self, path: str, tenant_id: Optional[str] = None) -> bool:
        target_path = self._get_tenant_path(path, tenant_id)
        if not os.path.exists(target_path):
            return False
        with open(target_path, "r") as f:
            data = json.load(f)
            # Convert lists back to numpy arrays
            self.user_profiles = {uid: np.array(vec) for uid, vec in data.get("user_profiles", {}).items()}
            self._is_trained = data.get("is_trained", False)
        return True

    def get_feature_importance(self) -> Dict[str, float]:
        return {}
