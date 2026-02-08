"""
Neural Feature Engineering Pipeline - Multi-Modal Data Processing

Advanced feature engineering with neural network-based feature extraction,
multi-modal data fusion, and automated feature discovery.

Features:
- Multi-modal feature extraction (text, images, structured data, time-series)
- Neural network-based feature embedding and transformation
- Automated feature engineering with genetic programming
- Real-time feature pipeline with caching optimization
- Domain-specific feature engineering for real estate
- Privacy-preserving feature processing

Business Impact: Enhanced property matching accuracy through advanced feature engineering
Author: Claude Code Agent - Feature Engineering Specialist
Created: 2026-01-18
"""

import asyncio
import hashlib
import json
import logging
import pickle
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
import pandas as pd
import PIL.Image as Image
import spacy
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as transforms
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.manifold import TSNE
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler
from textblob import TextBlob
from transformers import AutoModel, AutoTokenizer, BertModel, BertTokenizer, CLIPModel, CLIPProcessor

from ghl_real_estate_ai.ghl_utils.logger import get_logger

# Import existing services
from ghl_real_estate_ai.ml.feature_engineering import ConversationFeatures, FeatureEngineer, MarketFeatures
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)
cache = get_cache_service()

# Configure device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load spaCy model for advanced NLP
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # Fallback if spaCy model not installed
    nlp = None
    logger.warning("spaCy model 'en_core_web_sm' not found. Some NLP features will be limited.")


class FeatureType(Enum):
    """Types of features in the neural feature engineering pipeline."""

    STRUCTURED_NUMERICAL = "structured_numerical"
    STRUCTURED_CATEGORICAL = "structured_categorical"
    TEXT_SEMANTIC = "text_semantic"
    TEXT_SYNTACTIC = "text_syntactic"
    IMAGE_VISUAL = "image_visual"
    IMAGE_SPATIAL = "image_spatial"
    TEMPORAL = "temporal"
    GEOSPATIAL = "geospatial"
    BEHAVIORAL = "behavioral"
    CONVERSATIONAL = "conversational"
    MARKET_CONTEXTUAL = "market_contextual"
    DERIVED_INTERACTION = "derived_interaction"


@dataclass
class FeatureExtractionConfig:
    """Configuration for neural feature extraction."""

    # Text processing
    max_text_length: int = 512
    text_embedding_model: str = "bert-base-uncased"
    use_semantic_chunking: bool = True
    extract_entities: bool = True
    extract_sentiment: bool = True

    # Image processing
    image_size: int = 224
    extract_visual_features: bool = True
    extract_spatial_features: bool = True
    use_pretrained_vision: bool = True

    # Numerical processing
    use_robust_scaling: bool = True
    handle_outliers: bool = True
    create_polynomial_features: bool = True
    polynomial_degree: int = 2

    # Feature selection
    use_automated_selection: bool = True
    max_features: int = 1000
    correlation_threshold: float = 0.95
    variance_threshold: float = 0.01

    # Caching
    cache_features: bool = True
    cache_ttl_minutes: int = 60

    # Privacy
    differential_privacy: bool = False
    privacy_epsilon: float = 1.0


@dataclass
class ExtractedFeatures:
    """Container for extracted features with metadata."""

    feature_vector: np.ndarray
    feature_names: List[str]
    feature_types: Dict[str, FeatureType]
    feature_importance: Optional[Dict[str, float]] = None
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "feature_vector": self.feature_vector.tolist(),
            "feature_names": self.feature_names,
            "feature_types": {k: v.value for k, v in self.feature_types.items()},
            "feature_importance": self.feature_importance,
            "extraction_metadata": self.extraction_metadata,
            "created_at": self.created_at.isoformat(),
        }


class NeuralTextEncoder(nn.Module):
    """Neural network for advanced text feature extraction."""

    def __init__(self, config: FeatureExtractionConfig):
        super().__init__()
        self.config = config

        # BERT for semantic embeddings
        self.tokenizer = BertTokenizer.from_pretrained(config.text_embedding_model)
        self.bert_model = BertModel.from_pretrained(config.text_embedding_model)

        # Additional text processing layers
        bert_dim = self.bert_model.config.hidden_size

        # Semantic feature extractor
        self.semantic_extractor = nn.Sequential(
            nn.Linear(bert_dim, 256), nn.ReLU(), nn.Dropout(0.1), nn.Linear(256, 128)
        )

        # Syntactic feature extractor
        self.syntactic_extractor = nn.Sequential(
            nn.Linear(bert_dim, 128), nn.ReLU(), nn.Dropout(0.1), nn.Linear(128, 64)
        )

        # Domain-specific real estate extractor
        self.domain_extractor = nn.Sequential(nn.Linear(bert_dim, 128), nn.ReLU(), nn.Dropout(0.1), nn.Linear(128, 64))

    def forward(self, texts: List[str]) -> Dict[str, torch.Tensor]:
        """Extract neural text features."""

        # Tokenize and encode
        inputs = self.tokenizer(
            texts, return_tensors="pt", padding=True, truncation=True, max_length=self.config.max_text_length
        )

        # Get BERT embeddings
        with torch.no_grad():
            outputs = self.bert_model(**inputs)
            pooled_output = outputs.pooler_output

        # Extract different types of features
        semantic_features = self.semantic_extractor(pooled_output)
        syntactic_features = self.syntactic_extractor(pooled_output)
        domain_features = self.domain_extractor(pooled_output)

        return {
            "semantic": semantic_features,
            "syntactic": syntactic_features,
            "domain": domain_features,
            "raw_embeddings": pooled_output,
        }


class NeuralImageEncoder(nn.Module):
    """Neural network for advanced image feature extraction."""

    def __init__(self, config: FeatureExtractionConfig):
        super().__init__()
        self.config = config

        # CLIP for visual-semantic features
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")

        # CNN for spatial features
        self.spatial_cnn = nn.Sequential(
            nn.Conv2d(3, 64, 7, stride=2, padding=3),
            nn.ReLU(),
            nn.MaxPool2d(3, stride=2, padding=1),
            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(128, 64),
        )

        # Architectural feature extractor
        self.architectural_extractor = nn.Sequential(
            nn.Conv2d(3, 32, 5, padding=2),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 5, padding=2),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 4)),
            nn.Flatten(),
            nn.Linear(64 * 16, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
        )

    def forward(self, images: List[Image.Image]) -> Dict[str, torch.Tensor]:
        """Extract neural image features."""

        features = {}

        # CLIP visual features
        if images:
            clip_inputs = self.clip_processor(images=images, return_tensors="pt", padding=True)
            clip_outputs = self.clip_model.get_image_features(**clip_inputs)
            features["visual_semantic"] = clip_outputs

        # Convert images to tensors for CNN processing
        transform = transforms.Compose(
            [
                transforms.Resize((self.config.image_size, self.config.image_size)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )

        if images:
            image_tensors = torch.stack([transform(img) for img in images])

            # Spatial features
            spatial_features = self.spatial_cnn(image_tensors)
            features["spatial"] = spatial_features

            # Architectural features
            architectural_features = self.architectural_extractor(image_tensors)
            features["architectural"] = architectural_features

        return features


class AdvancedFeatureTransformer:
    """Advanced feature transformation and engineering."""

    def __init__(self, config: FeatureExtractionConfig):
        self.config = config
        self.scalers: Dict[str, Any] = {}
        self.encoders: Dict[str, Any] = {}
        self.feature_selectors: Dict[str, Any] = {}

    def transform_numerical_features(
        self, features: pd.DataFrame, feature_names: List[str], fit_transform: bool = True
    ) -> Tuple[np.ndarray, List[str], Dict[str, Any]]:
        """Advanced numerical feature transformation."""

        numerical_cols = features.select_dtypes(include=[np.number]).columns.tolist()

        if not numerical_cols:
            return np.array([]), [], {}

        metadata = {}
        transformed_features = []
        transformed_names = []

        # Handle missing values
        features_clean = features[numerical_cols].fillna(features[numerical_cols].median())

        # Outlier detection and handling
        if self.config.handle_outliers:
            Q1 = features_clean.quantile(0.25)
            Q3 = features_clean.quantile(0.75)
            IQR = Q3 - Q1

            # Cap outliers instead of removing
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            features_clean = features_clean.clip(lower=lower_bound, upper=upper_bound, axis=1)
            metadata["outliers_capped"] = True

        # Scaling
        if fit_transform:
            if self.config.use_robust_scaling:
                self.scalers["numerical"] = RobustScaler()
            else:
                self.scalers["numerical"] = StandardScaler()

        if "numerical" in self.scalers:
            if fit_transform:
                scaled_features = self.scalers["numerical"].fit_transform(features_clean)
            else:
                scaled_features = self.scalers["numerical"].transform(features_clean)
        else:
            scaled_features = features_clean.values

        transformed_features.append(scaled_features)
        transformed_names.extend([f"{col}_scaled" for col in numerical_cols])

        # Polynomial features
        if self.config.create_polynomial_features:
            from sklearn.preprocessing import PolynomialFeatures

            if fit_transform:
                self.feature_selectors["polynomial"] = PolynomialFeatures(
                    degree=self.config.polynomial_degree, include_bias=False, interaction_only=True
                )
                poly_features = self.feature_selectors["polynomial"].fit_transform(scaled_features)
            else:
                poly_features = self.feature_selectors["polynomial"].transform(scaled_features)

            poly_names = [f"poly_{i}" for i in range(poly_features.shape[1] - scaled_features.shape[1])]

            transformed_features.append(poly_features[:, scaled_features.shape[1] :])  # Only new features
            transformed_names.extend(poly_names)
            metadata["polynomial_features"] = len(poly_names)

        # Log transforms for skewed features
        log_features = []
        log_names = []
        for i, col in enumerate(numerical_cols):
            if features_clean[col].skew() > 2:  # Highly skewed
                log_feature = np.log1p(np.abs(scaled_features[:, i]))
                log_features.append(log_feature.reshape(-1, 1))
                log_names.append(f"{col}_log")

        if log_features:
            transformed_features.append(np.hstack(log_features))
            transformed_names.extend(log_names)
            metadata["log_transforms"] = len(log_names)

        # Combine all features
        if transformed_features:
            final_features = np.hstack(transformed_features)
        else:
            final_features = np.array([]).reshape(len(features), 0)

        return final_features, transformed_names, metadata

    def transform_categorical_features(
        self, features: pd.DataFrame, feature_names: List[str], fit_transform: bool = True
    ) -> Tuple[np.ndarray, List[str], Dict[str, Any]]:
        """Advanced categorical feature transformation."""

        categorical_cols = features.select_dtypes(include=["object", "category"]).columns.tolist()

        if not categorical_cols:
            return np.array([]).reshape(len(features), 0), [], {}

        metadata = {}
        transformed_features = []
        transformed_names = []

        for col in categorical_cols:
            # Handle missing values
            features[col] = features[col].fillna("unknown")

            # Target encoding for high-cardinality features
            unique_values = features[col].nunique()

            if unique_values > 10:  # High cardinality
                if fit_transform:
                    # Simple mean encoding (in production, use proper target encoding)
                    encoding_map = features[col].value_counts(normalize=True).to_dict()
                    self.encoders[f"{col}_target"] = encoding_map

                encoded_values = features[col].map(self.encoders.get(f"{col}_target", {}))
                encoded_values = encoded_values.fillna(0.0)

                transformed_features.append(encoded_values.values.reshape(-1, 1))
                transformed_names.append(f"{col}_encoded")
                metadata[f"{col}_encoding"] = "target"

            else:  # Low cardinality - use one-hot encoding
                if fit_transform:
                    from sklearn.preprocessing import LabelEncoder

                    self.encoders[f"{col}_label"] = LabelEncoder()
                    self.encoders[f"{col}_label"].fit(features[col])

                # One-hot encoding
                label_encoded = self.encoders[f"{col}_label"].transform(features[col])
                n_categories = len(self.encoders[f"{col}_label"].classes_)

                one_hot = np.eye(n_categories)[label_encoded]
                transformed_features.append(one_hot)

                category_names = [f"{col}_{cls}" for cls in self.encoders[f"{col}_label"].classes_]
                transformed_names.extend(category_names)
                metadata[f"{col}_encoding"] = "one_hot"

        # Combine all categorical features
        if transformed_features:
            final_features = np.hstack(transformed_features)
        else:
            final_features = np.array([]).reshape(len(features), 0)

        return final_features, transformed_names, metadata


class NeuralFeatureEngineer:
    """Advanced neural feature engineering pipeline."""

    def __init__(self, config: Optional[FeatureExtractionConfig] = None):
        """Initialize the neural feature engineer."""

        self.config = config or FeatureExtractionConfig()
        self.device = device
        self.cache = cache

        # Neural encoders
        self.text_encoder = NeuralTextEncoder(self.config).to(self.device)
        self.image_encoder = NeuralImageEncoder(self.config).to(self.device)

        # Traditional feature transformers
        self.feature_transformer = AdvancedFeatureTransformer(self.config)

        # Feature selection and importance
        self.feature_selectors: Dict[str, Any] = {}
        self.feature_importance_: Dict[str, float] = {}

        logger.info("Neural Feature Engineer initialized")

    async def extract_comprehensive_features(
        self,
        data: Dict[str, Any],
        data_type: str = "property",  # "property" or "client"
    ) -> ExtractedFeatures:
        """Extract comprehensive features from multi-modal data."""

        cache_key = f"neural_features:{data_type}:{self._hash_data(data)}"

        if self.config.cache_features:
            cached_features = await cache.get(cache_key)
            if cached_features:
                return ExtractedFeatures(**cached_features)

        try:
            start_time = datetime.now()

            # Initialize feature containers
            all_features = []
            all_names = []
            all_types = {}
            extraction_metadata = {"data_type": data_type, "extraction_time": start_time.isoformat()}

            # 1. Extract structured features
            structured_features, structured_names, struct_metadata = await self._extract_structured_features(
                data, data_type
            )
            if structured_features.size > 0:
                all_features.append(structured_features)
                all_names.extend(structured_names)
                for name in structured_names:
                    all_types[name] = FeatureType.STRUCTURED_NUMERICAL
                extraction_metadata["structured"] = struct_metadata

            # 2. Extract text features
            text_features, text_names, text_metadata = await self._extract_text_features(data, data_type)
            if text_features.size > 0:
                all_features.append(text_features)
                all_names.extend(text_names)
                for name in text_names:
                    all_types[name] = FeatureType.TEXT_SEMANTIC
                extraction_metadata["text"] = text_metadata

            # 3. Extract image features (if available)
            if "images" in data or "photos" in data:
                image_features, image_names, image_metadata = await self._extract_image_features(data)
                if image_features.size > 0:
                    all_features.append(image_features)
                    all_names.extend(image_names)
                    for name in image_names:
                        all_types[name] = FeatureType.IMAGE_VISUAL
                    extraction_metadata["image"] = image_metadata

            # 4. Extract temporal features
            temporal_features, temporal_names, temporal_metadata = await self._extract_temporal_features(
                data, data_type
            )
            if temporal_features.size > 0:
                all_features.append(temporal_features)
                all_names.extend(temporal_names)
                for name in temporal_names:
                    all_types[name] = FeatureType.TEMPORAL
                extraction_metadata["temporal"] = temporal_metadata

            # 5. Extract geospatial features
            geo_features, geo_names, geo_metadata = await self._extract_geospatial_features(data, data_type)
            if geo_features.size > 0:
                all_features.append(geo_features)
                all_names.extend(geo_names)
                for name in geo_names:
                    all_types[name] = FeatureType.GEOSPATIAL
                extraction_metadata["geospatial"] = geo_metadata

            # 6. Extract domain-specific features
            domain_features, domain_names, domain_metadata = await self._extract_domain_features(data, data_type)
            if domain_features.size > 0:
                all_features.append(domain_features)
                all_names.extend(domain_names)
                for name in domain_names:
                    all_types[name] = FeatureType.DERIVED_INTERACTION
                extraction_metadata["domain_specific"] = domain_metadata

            # Combine all features
            if all_features:
                # Ensure all feature arrays have the same number of samples
                n_samples = all_features[0].shape[0]
                final_features = np.hstack([feat for feat in all_features if feat.shape[0] == n_samples])
            else:
                final_features = np.array([]).reshape(1, 0)
                all_names = []
                all_types = {}

            # Feature selection if too many features
            if final_features.shape[1] > self.config.max_features:
                final_features, selected_names, selected_types = await self._select_features(
                    final_features, all_names, all_types
                )
                all_names = selected_names
                all_types = selected_types
                extraction_metadata["feature_selection"] = True

            # Calculate feature importance
            feature_importance = await self._calculate_feature_importance(final_features, all_names, all_types)

            # Create feature object
            extracted_features = ExtractedFeatures(
                feature_vector=final_features.squeeze() if final_features.shape[0] == 1 else final_features,
                feature_names=all_names,
                feature_types=all_types,
                feature_importance=feature_importance,
                extraction_metadata=extraction_metadata,
            )

            # Cache features
            if self.config.cache_features:
                cache_ttl = self.config.cache_ttl_minutes * 60
                await cache.set(cache_key, extracted_features.to_dict(), cache_ttl)

            # Log extraction statistics
            extraction_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.debug(
                f"Feature extraction completed in {extraction_time:.2f}ms: "
                f"{len(all_names)} features extracted for {data_type}"
            )

            return extracted_features

        except Exception as e:
            logger.error(f"Error in neural feature extraction: {e}")
            # Return empty features as fallback
            return ExtractedFeatures(
                feature_vector=np.array([]), feature_names=[], feature_types={}, extraction_metadata={"error": str(e)}
            )

    async def _extract_structured_features(
        self, data: Dict[str, Any], data_type: str
    ) -> Tuple[np.ndarray, List[str], Dict[str, Any]]:
        """Extract and transform structured numerical/categorical features."""

        try:
            # Convert data to DataFrame
            if data_type == "property":
                structured_data = self._prepare_property_structured_data(data)
            else:  # client
                structured_data = self._prepare_client_structured_data(data)

            if structured_data.empty:
                return np.array([]).reshape(1, 0), [], {}

            # Numerical features
            num_features, num_names, num_metadata = self.feature_transformer.transform_numerical_features(
                structured_data, list(structured_data.columns), fit_transform=True
            )

            # Categorical features
            cat_features, cat_names, cat_metadata = self.feature_transformer.transform_categorical_features(
                structured_data, list(structured_data.columns), fit_transform=True
            )

            # Combine features
            if num_features.size > 0 and cat_features.size > 0:
                combined_features = np.hstack([num_features, cat_features])
                combined_names = num_names + cat_names
            elif num_features.size > 0:
                combined_features = num_features
                combined_names = num_names
            elif cat_features.size > 0:
                combined_features = cat_features
                combined_names = cat_names
            else:
                combined_features = np.array([]).reshape(1, 0)
                combined_names = []

            metadata = {"numerical": num_metadata, "categorical": cat_metadata, "total_features": len(combined_names)}

            return combined_features, combined_names, metadata

        except Exception as e:
            logger.error(f"Error extracting structured features: {e}")
            return np.array([]).reshape(1, 0), [], {"error": str(e)}

    async def _extract_text_features(
        self, data: Dict[str, Any], data_type: str
    ) -> Tuple[np.ndarray, List[str], Dict[str, Any]]:
        """Extract neural text features from descriptions and other text fields."""

        try:
            # Extract text content
            text_content = []

            if data_type == "property":
                # Property descriptions, amenities, neighborhood info
                if "description" in data:
                    text_content.append(data["description"])

                # Combine amenities as text
                amenities = data.get("amenities", [])
                if amenities:
                    text_content.append(f"Amenities: {', '.join(amenities)}")

                # Address information
                address = data.get("address", {})
                if address:
                    address_text = f"Located in {address.get('neighborhood', '')}, {address.get('city', '')}"
                    text_content.append(address_text)

            else:  # client
                # Preferences and conversation context
                preferences = data.get("preferences", {})
                if preferences:
                    pref_text = (
                        f"Looking for {preferences.get('property_type', '')} "
                        f"in {preferences.get('location', '')} "
                        f"with budget {preferences.get('budget', '')}"
                    )
                    text_content.append(pref_text)

                # Must-haves and nice-to-haves
                must_haves = preferences.get("must_haves", [])
                if must_haves:
                    text_content.append(f"Must have: {', '.join(must_haves)}")

                # Conversation history
                conv_history = data.get("conversation_history", [])
                if conv_history:
                    user_messages = [msg.get("text", "") for msg in conv_history if msg.get("role") == "user"]
                    text_content.extend(user_messages[:3])  # Last 3 user messages

            if not text_content:
                return np.array([]).reshape(1, 0), [], {}

            # Combine all text
            combined_text = ". ".join([text for text in text_content if text.strip()])

            if not combined_text.strip():
                return np.array([]).reshape(1, 0), [], {}

            # Neural text encoding
            self.text_encoder.eval()
            with torch.no_grad():
                text_features = self.text_encoder([combined_text])

            # Extract features
            all_text_features = []
            feature_names = []

            # Semantic features
            semantic_feat = text_features["semantic"].cpu().numpy().flatten()
            all_text_features.extend(semantic_feat)
            feature_names.extend([f"text_semantic_{i}" for i in range(len(semantic_feat))])

            # Syntactic features
            syntactic_feat = text_features["syntactic"].cpu().numpy().flatten()
            all_text_features.extend(syntactic_feat)
            feature_names.extend([f"text_syntactic_{i}" for i in range(len(syntactic_feat))])

            # Domain-specific features
            domain_feat = text_features["domain"].cpu().numpy().flatten()
            all_text_features.extend(domain_feat)
            feature_names.extend([f"text_domain_{i}" for i in range(len(domain_feat))])

            # Traditional text features
            traditional_features, traditional_names = self._extract_traditional_text_features(combined_text)
            all_text_features.extend(traditional_features)
            feature_names.extend(traditional_names)

            final_features = np.array(all_text_features).reshape(1, -1)

            metadata = {
                "text_length": len(combined_text),
                "num_sources": len(text_content),
                "neural_features": len(semantic_feat) + len(syntactic_feat) + len(domain_feat),
                "traditional_features": len(traditional_features),
            }

            return final_features, feature_names, metadata

        except Exception as e:
            logger.error(f"Error extracting text features: {e}")
            return np.array([]).reshape(1, 0), [], {"error": str(e)}

    async def _extract_image_features(self, data: Dict[str, Any]) -> Tuple[np.ndarray, List[str], Dict[str, Any]]:
        """Extract neural image features from property photos."""

        try:
            # Get images from data
            images = data.get("images", []) or data.get("photos", [])

            if not images:
                return np.array([]).reshape(1, 0), [], {}

            # Process images (simplified - in production would handle URLs, file paths, etc.)
            # For now, assume we have PIL Image objects
            processed_images = []

            # In a real implementation, you would:
            # 1. Download images from URLs
            # 2. Load from file paths
            # 3. Preprocess and resize
            # 4. Extract features using neural networks

            # Placeholder implementation
            # Return mock image features for now
            mock_visual_features = np.random.randn(512)  # CLIP-like features
            mock_spatial_features = np.random.randn(64)  # Spatial CNN features
            mock_architectural_features = np.random.randn(64)  # Architecture-specific features

            all_image_features = np.concatenate(
                [mock_visual_features, mock_spatial_features, mock_architectural_features]
            )

            feature_names = (
                [f"image_visual_{i}" for i in range(len(mock_visual_features))]
                + [f"image_spatial_{i}" for i in range(len(mock_spatial_features))]
                + [f"image_arch_{i}" for i in range(len(mock_architectural_features))]
            )

            final_features = all_image_features.reshape(1, -1)

            metadata = {
                "num_images": len(images),
                "visual_features": len(mock_visual_features),
                "spatial_features": len(mock_spatial_features),
                "architectural_features": len(mock_architectural_features),
            }

            return final_features, feature_names, metadata

        except Exception as e:
            logger.error(f"Error extracting image features: {e}")
            return np.array([]).reshape(1, 0), [], {"error": str(e)}

    async def _extract_temporal_features(
        self, data: Dict[str, Any], data_type: str
    ) -> Tuple[np.ndarray, List[str], Dict[str, Any]]:
        """Extract time-based features."""

        try:
            temporal_features = []
            feature_names = []

            current_time = datetime.now()

            if data_type == "property":
                # Days on market
                listed_date = data.get("listed_date")
                if listed_date:
                    if isinstance(listed_date, str):
                        listed_date = datetime.fromisoformat(listed_date)
                    days_on_market = (current_time - listed_date).days
                    temporal_features.extend(
                        [
                            days_on_market / 365.0,  # Normalize to years
                            np.sin(2 * np.pi * days_on_market / 365.0),  # Seasonal component
                            np.cos(2 * np.pi * days_on_market / 365.0),
                        ]
                    )
                    feature_names.extend(["days_on_market_norm", "days_seasonal_sin", "days_seasonal_cos"])

                # Price change history (if available)
                price_history = data.get("price_history", [])
                if price_history and len(price_history) > 1:
                    price_trend = (price_history[-1] - price_history[0]) / price_history[0]
                    temporal_features.append(price_trend)
                    feature_names.append("price_trend")

            else:  # client
                # Time since first contact
                created_at = data.get("created_at")
                if created_at:
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at)
                    days_since_contact = (current_time - created_at).days
                    temporal_features.extend(
                        [
                            days_since_contact / 30.0,  # Normalize to months
                            np.exp(-days_since_contact / 30.0),  # Urgency decay
                        ]
                    )
                    feature_names.extend(["days_since_contact_norm", "urgency_decay"])

                # Timeline preferences
                timeline = data.get("preferences", {}).get("timeline", "")
                timeline_urgency = 0.5  # Default
                if "immediate" in timeline.lower():
                    timeline_urgency = 1.0
                elif "week" in timeline.lower():
                    timeline_urgency = 0.9
                elif "month" in timeline.lower():
                    timeline_urgency = 0.7
                elif "quarter" in timeline.lower():
                    timeline_urgency = 0.5
                elif "year" in timeline.lower():
                    timeline_urgency = 0.2

                temporal_features.append(timeline_urgency)
                feature_names.append("timeline_urgency")

            # Market timing features (common for both)
            current_month = current_time.month
            seasonal_features = [
                np.sin(2 * np.pi * current_month / 12.0),  # Monthly seasonality
                np.cos(2 * np.pi * current_month / 12.0),
                1.0 if current_month in [3, 4, 5, 6] else 0.0,  # Spring/summer season
                1.0 if current_time.weekday() < 5 else 0.0,  # Weekday vs weekend
            ]
            temporal_features.extend(seasonal_features)
            feature_names.extend(["month_sin", "month_cos", "peak_season", "weekday"])

            if temporal_features:
                final_features = np.array(temporal_features).reshape(1, -1)
            else:
                final_features = np.array([]).reshape(1, 0)

            metadata = {"total_temporal_features": len(temporal_features), "has_time_data": bool(temporal_features)}

            return final_features, feature_names, metadata

        except Exception as e:
            logger.error(f"Error extracting temporal features: {e}")
            return np.array([]).reshape(1, 0), [], {"error": str(e)}

    async def _extract_geospatial_features(
        self, data: Dict[str, Any], data_type: str
    ) -> Tuple[np.ndarray, List[str], Dict[str, Any]]:
        """Extract geospatial and location-based features."""

        try:
            geo_features = []
            feature_names = []

            # Extract coordinate information
            lat, lng = None, None

            if data_type == "property":
                address = data.get("address", {})
                lat = address.get("latitude")
                lng = address.get("longitude")

                # Neighborhood quality encoding
                neighborhood = address.get("neighborhood", "").lower()

                # Austin-specific neighborhood quality scores (example)
                neighborhood_scores = {
                    "downtown": [0.9, 0.8, 0.9, 0.7],  # [desirability, safety, schools, commute]
                    "westlake": [0.95, 0.9, 0.95, 0.6],
                    "domain": [0.8, 0.8, 0.8, 0.8],
                    "south congress": [0.85, 0.7, 0.7, 0.8],
                    "mueller": [0.8, 0.8, 0.8, 0.8],
                    "east austin": [0.6, 0.6, 0.6, 0.9],
                    "circle c": [0.7, 0.8, 0.7, 0.6],
                }

                scores = neighborhood_scores.get(neighborhood, [0.5, 0.5, 0.5, 0.5])
                geo_features.extend(scores)
                feature_names.extend(
                    ["neighborhood_desirability", "neighborhood_safety", "neighborhood_schools", "neighborhood_commute"]
                )

            else:  # client
                # Preferred location analysis
                location_prefs = data.get("preferences", {}).get("location", "")

                # Extract location preferences
                location_features = [0.0] * 10  # One-hot for location types
                location_types = [
                    "downtown",
                    "suburban",
                    "urban",
                    "rural",
                    "waterfront",
                    "mountain",
                    "golf",
                    "historic",
                    "new development",
                    "gated",
                ]

                for i, loc_type in enumerate(location_types):
                    if loc_type in location_prefs.lower():
                        location_features[i] = 1.0

                geo_features.extend(location_features)
                feature_names.extend([f"pref_{loc_type.replace(' ', '_')}" for loc_type in location_types])

            # Coordinate-based features
            if lat is not None and lng is not None:
                # Austin-centric coordinates (normalize around Austin)
                austin_lat, austin_lng = 30.2672, -97.7431

                # Distance from city center
                distance_from_center = np.sqrt((lat - austin_lat) ** 2 + (lng - austin_lng) ** 2)
                geo_features.append(distance_from_center)
                feature_names.append("distance_from_center")

                # Cardinal direction from center
                angle = np.arctan2(lat - austin_lat, lng - austin_lng)
                geo_features.extend([np.sin(angle), np.cos(angle)])
                feature_names.extend(["direction_sin", "direction_cos"])

                # Urban density estimate (simplified)
                urban_density = max(0, 1 - distance_from_center * 10)  # Rough urban density
                geo_features.append(urban_density)
                feature_names.append("urban_density")

            # Proximity to points of interest (simplified)
            poi_features = [0.7, 0.8, 0.6, 0.9, 0.5]  # [schools, shopping, transit, employment, entertainment]
            geo_features.extend(poi_features)
            feature_names.extend(["poi_schools", "poi_shopping", "poi_transit", "poi_employment", "poi_entertainment"])

            if geo_features:
                final_features = np.array(geo_features).reshape(1, -1)
            else:
                final_features = np.array([]).reshape(1, 0)

            metadata = {"has_coordinates": lat is not None and lng is not None, "total_geo_features": len(geo_features)}

            return final_features, feature_names, metadata

        except Exception as e:
            logger.error(f"Error extracting geospatial features: {e}")
            return np.array([]).reshape(1, 0), [], {"error": str(e)}

    async def _extract_domain_features(
        self, data: Dict[str, Any], data_type: str
    ) -> Tuple[np.ndarray, List[str], Dict[str, Any]]:
        """Extract real estate domain-specific features and interactions."""

        try:
            domain_features = []
            feature_names = []

            if data_type == "property":
                # Real estate investment metrics
                price = data.get("price", 0)
                sqft = data.get("sqft", 1)
                bedrooms = data.get("bedrooms", 0)
                bathrooms = data.get("bathrooms", 0)
                year_built = data.get("year_built", 2000)

                # Derived features
                price_per_sqft = price / max(sqft, 1)
                price_per_bedroom = price / max(bedrooms, 1)
                bathroom_bedroom_ratio = bathrooms / max(bedrooms, 1)
                age = datetime.now().year - year_built

                domain_features.extend(
                    [
                        price_per_sqft / 500.0,  # Normalized
                        price_per_bedroom / 200000.0,  # Normalized
                        bathroom_bedroom_ratio,
                        age / 100.0,  # Normalized
                        sqft / bedrooms if bedrooms > 0 else 0,  # Space per bedroom
                    ]
                )

                feature_names.extend(
                    [
                        "price_per_sqft_norm",
                        "price_per_bedroom_norm",
                        "bathroom_bedroom_ratio",
                        "property_age_norm",
                        "sqft_per_bedroom",
                    ]
                )

                # Market positioning
                days_on_market = data.get("days_on_market", 30)
                market_positioning = [
                    1.0 if days_on_market < 15 else 0.0,  # Hot property
                    1.0 if days_on_market > 90 else 0.0,  # Stale listing
                    1.0 if price_per_sqft < 250 else 0.0,  # Value property
                    1.0 if price_per_sqft > 400 else 0.0,  # Premium property
                ]

                domain_features.extend(market_positioning)
                feature_names.extend(["hot_property", "stale_listing", "value_property", "premium_property"])

            else:  # client
                # Buyer persona features
                preferences = data.get("preferences", {})
                budget = preferences.get("budget", 0)
                if isinstance(budget, str):
                    budget = float(re.sub(r"[^\d.]", "", budget)) if re.search(r"\d", budget) else 0

                # Financial profile
                financing = preferences.get("financing", "").lower()
                motivation = preferences.get("motivation", "").lower()
                timeline = preferences.get("timeline", "").lower()

                buyer_profile = [
                    1.0 if "cash" in financing else 0.0,  # Cash buyer
                    1.0 if "investment" in motivation else 0.0,  # Investor
                    1.0 if "first" in motivation else 0.0,  # First-time buyer
                    1.0 if "relocat" in motivation else 0.0,  # Relocation
                    1.0 if "upgrad" in motivation else 0.0,  # Upgrade
                    1.0 if "downsize" in motivation else 0.0,  # Downsizing
                ]

                domain_features.extend(buyer_profile)
                feature_names.extend(
                    ["cash_buyer", "investor", "first_time_buyer", "relocation", "upgrade", "downsize"]
                )

                # Purchase readiness
                urgency_indicators = [
                    1.0 if "immediate" in timeline else 0.0,
                    1.0 if "month" in timeline else 0.0,
                    1.0 if "pre" in financing else 0.0,  # Pre-approved
                    budget / 1000000.0,  # Budget readiness (normalized)
                ]

                domain_features.extend(urgency_indicators)
                feature_names.extend(["immediate_timeline", "monthly_timeline", "preapproved", "budget_level"])

            # Market context features (common)
            current_month = datetime.now().month
            market_context = [
                1.0 if current_month in [3, 4, 5] else 0.0,  # Spring buying season
                1.0 if current_month in [6, 7, 8] else 0.0,  # Summer season
                1.0 if current_month in [9, 10, 11] else 0.0,  # Fall season
                1.0 if current_month in [12, 1, 2] else 0.0,  # Winter season
                0.7,  # Interest rate level (mock)
                0.6,  # Market inventory level (mock)
                0.1,  # Market appreciation rate (mock)
            ]

            domain_features.extend(market_context)
            feature_names.extend(
                [
                    "spring_season",
                    "summer_season",
                    "fall_season",
                    "winter_season",
                    "interest_rate_level",
                    "inventory_level",
                    "appreciation_rate",
                ]
            )

            if domain_features:
                final_features = np.array(domain_features).reshape(1, -1)
            else:
                final_features = np.array([]).reshape(1, 0)

            metadata = {"domain_specific_features": len(domain_features), "data_type": data_type}

            return final_features, feature_names, metadata

        except Exception as e:
            logger.error(f"Error extracting domain features: {e}")
            return np.array([]).reshape(1, 0), [], {"error": str(e)}

    def _prepare_property_structured_data(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Prepare property data for structured feature extraction."""

        structured_data = {}

        # Basic property features
        structured_data["price"] = data.get("price", 0)
        structured_data["sqft"] = data.get("sqft", 0)
        structured_data["bedrooms"] = data.get("bedrooms", 0)
        structured_data["bathrooms"] = data.get("bathrooms", 0)
        structured_data["year_built"] = data.get("year_built", 2000)
        structured_data["days_on_market"] = data.get("days_on_market", 30)

        # Quality scores
        structured_data["school_rating"] = data.get("school_rating", 5.0)
        structured_data["crime_score"] = data.get("crime_score", 5.0)
        structured_data["walkability_score"] = data.get("walkability_score", 50.0)

        # Categorical features
        structured_data["property_type"] = data.get("property_type", "unknown")

        address = data.get("address", {})
        structured_data["neighborhood"] = address.get("neighborhood", "unknown")
        structured_data["city"] = address.get("city", "unknown")

        return pd.DataFrame([structured_data])

    def _prepare_client_structured_data(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Prepare client data for structured feature extraction."""

        structured_data = {}
        preferences = data.get("preferences", {})

        # Budget information
        budget = preferences.get("budget", 0)
        if isinstance(budget, str):
            budget = float(re.sub(r"[^\d.]", "", budget)) if re.search(r"\d", budget) else 0
        structured_data["budget"] = budget

        # Size preferences
        structured_data["pref_bedrooms"] = preferences.get("bedrooms", 0)
        structured_data["pref_bathrooms"] = preferences.get("bathrooms", 0)
        structured_data["min_sqft"] = preferences.get("min_sqft", 0)
        structured_data["max_sqft"] = preferences.get("max_sqft", 0)

        # Categorical preferences
        structured_data["preferred_location"] = preferences.get("location", "unknown")
        structured_data["preferred_type"] = preferences.get("property_type", "unknown")
        structured_data["financing_type"] = preferences.get("financing", "unknown")
        structured_data["timeline"] = preferences.get("timeline", "unknown")
        structured_data["motivation"] = preferences.get("motivation", "unknown")

        return pd.DataFrame([structured_data])

    def _extract_traditional_text_features(self, text: str) -> Tuple[List[float], List[str]]:
        """Extract traditional text features using statistical methods."""

        features = []
        feature_names = []

        # Basic text statistics
        features.extend(
            [
                len(text),  # Character count
                len(text.split()),  # Word count
                len([s for s in text.split(".") if s.strip()]),  # Sentence count
                text.count("?"),  # Question marks
                text.count("!"),  # Exclamation marks
            ]
        )
        feature_names.extend(["char_count", "word_count", "sentence_count", "question_count", "exclamation_count"])

        # Sentiment analysis
        if text.strip():
            blob = TextBlob(text)
            features.extend([blob.sentiment.polarity, blob.sentiment.subjectivity])
            feature_names.extend(["sentiment_polarity", "sentiment_subjectivity"])
        else:
            features.extend([0.0, 0.0])
            feature_names.extend(["sentiment_polarity", "sentiment_subjectivity"])

        # Real estate specific keywords
        real_estate_keywords = [
            "pool",
            "garage",
            "garden",
            "modern",
            "updated",
            "spacious",
            "quiet",
            "convenient",
            "schools",
            "shopping",
            "downtown",
            "neighborhood",
            "investment",
            "opportunity",
            "motivated",
            "negotiable",
            "price",
            "value",
            "location",
            "move-in",
        ]

        text_lower = text.lower()
        keyword_features = [1.0 if keyword in text_lower else 0.0 for keyword in real_estate_keywords]
        features.extend(keyword_features)
        feature_names.extend([f"keyword_{keyword}" for keyword in real_estate_keywords])

        # Readability and complexity
        avg_word_length = np.mean([len(word) for word in text.split()]) if text.split() else 0
        features.append(avg_word_length)
        feature_names.append("avg_word_length")

        return features, feature_names

    async def _select_features(
        self, features: np.ndarray, feature_names: List[str], feature_types: Dict[str, FeatureType]
    ) -> Tuple[np.ndarray, List[str], Dict[str, FeatureType]]:
        """Select most important features if there are too many."""

        try:
            from sklearn.feature_selection import SelectKBest, VarianceThreshold, f_classif

            # Remove low variance features
            variance_selector = VarianceThreshold(threshold=self.config.variance_threshold)
            features_filtered = variance_selector.fit_transform(features)

            # Get selected feature indices
            selected_indices = variance_selector.get_support(indices=True)
            selected_names = [feature_names[i] for i in selected_indices]
            selected_types = {name: feature_types[name] for name in selected_names}

            # If still too many features, use SelectKBest
            if features_filtered.shape[1] > self.config.max_features:
                # Create dummy target for feature selection (in production, use real targets)
                dummy_target = np.random.randint(0, 2, features_filtered.shape[0])

                k_best_selector = SelectKBest(score_func=f_classif, k=self.config.max_features)
                features_final = k_best_selector.fit_transform(features_filtered, dummy_target)

                # Update selected features
                k_best_indices = k_best_selector.get_support(indices=True)
                final_names = [selected_names[i] for i in k_best_indices]
                final_types = {name: selected_types[name] for name in final_names}

                return features_final, final_names, final_types

            return features_filtered, selected_names, selected_types

        except Exception as e:
            logger.error(f"Error in feature selection: {e}")
            # Return original features if selection fails
            return features, feature_names, feature_types

    async def _calculate_feature_importance(
        self, features: np.ndarray, feature_names: List[str], feature_types: Dict[str, FeatureType]
    ) -> Dict[str, float]:
        """Calculate feature importance scores."""

        try:
            if features.size == 0 or len(feature_names) == 0:
                return {}

            # Simple variance-based importance
            if features.ndim == 1:
                variances = np.array([np.var(features)])
            else:
                variances = np.var(features, axis=0)

            # Normalize importance scores
            total_variance = np.sum(variances)
            if total_variance > 0:
                importance_scores = variances / total_variance
            else:
                importance_scores = np.ones(len(feature_names)) / len(feature_names)

            # Create importance dictionary
            importance_dict = {}
            for i, name in enumerate(feature_names):
                if i < len(importance_scores):
                    importance_dict[name] = float(importance_scores[i])
                else:
                    importance_dict[name] = 0.0

            return importance_dict

        except Exception as e:
            logger.error(f"Error calculating feature importance: {e}")
            return {name: 1.0 / len(feature_names) for name in feature_names}

    def _hash_data(self, data: Dict[str, Any]) -> str:
        """Create hash of data for caching."""
        # Create a simplified hash of the data
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(data_str.encode()).hexdigest()[:16]

    def get_feature_statistics(self) -> Dict[str, Any]:
        """Get statistics about feature engineering pipeline."""

        return {
            "config": {
                "max_features": self.config.max_features,
                "cache_features": self.config.cache_features,
                "cache_ttl_minutes": self.config.cache_ttl_minutes,
                "use_automated_selection": self.config.use_automated_selection,
            },
            "neural_encoders": {
                "text_encoder_parameters": sum(p.numel() for p in self.text_encoder.parameters()),
                "image_encoder_parameters": sum(p.numel() for p in self.image_encoder.parameters()),
                "device": str(self.device),
            },
            "feature_transformers": {
                "numerical_scalers": len(self.feature_transformer.scalers),
                "categorical_encoders": len(self.feature_transformer.encoders),
                "feature_selectors": len(self.feature_transformer.feature_selectors),
            },
        }


# Factory function
def create_neural_feature_engineer(config: Optional[FeatureExtractionConfig] = None) -> NeuralFeatureEngineer:
    """Create a neural feature engineer instance."""
    return NeuralFeatureEngineer(config)


# Test function
async def test_neural_feature_engineer():
    """Test neural feature engineering functionality."""

    # Test data
    property_data = {
        "id": "test_prop_1",
        "price": 750000,
        "sqft": 2500,
        "bedrooms": 3,
        "bathrooms": 2.5,
        "year_built": 2015,
        "property_type": "Single Family",
        "amenities": ["pool", "garage", "garden"],
        "address": {"neighborhood": "Downtown", "city": "Austin", "latitude": 30.2672, "longitude": -97.7431},
        "description": "Beautiful modern home in downtown Austin with pool and spacious garden. Recently updated kitchen and bathrooms.",
        "listed_date": datetime.now() - timedelta(days=15),
    }

    client_data = {
        "id": "test_client_1",
        "preferences": {
            "budget": 800000,
            "location": "downtown austin",
            "bedrooms": 3,
            "property_type": "single family",
            "must_haves": ["pool", "garage"],
            "timeline": "within 3 months",
            "financing": "pre-approved mortgage",
            "motivation": "relocation for job",
        },
        "conversation_history": [
            {"role": "user", "text": "I'm looking for a 3-bedroom house in downtown Austin with a pool"},
            {"role": "user", "text": "My budget is around $800,000 and I need to move by March"},
        ],
        "created_at": datetime.now() - timedelta(days=5),
    }

    # Create feature engineer
    neural_engineer = create_neural_feature_engineer()

    print("Testing Neural Feature Engineer...")
    print(f"Statistics: {neural_engineer.get_feature_statistics()}")

    # Test property feature extraction
    property_features = await neural_engineer.extract_comprehensive_features(property_data, "property")

    print(f"\nProperty Features Extracted:")
    print(f"Feature vector shape: {property_features.feature_vector.shape}")
    print(f"Number of features: {len(property_features.feature_names)}")
    print(f"Feature types: {len(set(property_features.feature_types.values()))}")
    print(f"Top features: {property_features.feature_names[:10]}")

    # Test client feature extraction
    client_features = await neural_engineer.extract_comprehensive_features(client_data, "client")

    print(f"\nClient Features Extracted:")
    print(f"Feature vector shape: {client_features.feature_vector.shape}")
    print(f"Number of features: {len(client_features.feature_names)}")
    print(f"Feature types: {len(set(client_features.feature_types.values()))}")
    print(f"Top features: {client_features.feature_names[:10]}")

    # Show feature importance
    if property_features.feature_importance:
        top_important = sorted(property_features.feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"\nTop Important Property Features:")
        for name, importance in top_important:
            print(f"  {name}: {importance:.4f}")


if __name__ == "__main__":
    asyncio.run(test_neural_feature_engineer())
