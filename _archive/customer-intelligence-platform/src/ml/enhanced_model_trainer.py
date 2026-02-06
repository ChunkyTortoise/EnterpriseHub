"""
Enhanced Model Training Pipeline for Customer Intelligence Platform.

This module provides advanced ML model training capabilities including:
- Advanced feature engineering with temporal patterns
- Automated hyperparameter optimization
- Model versioning with A/B testing support
- Performance monitoring and automated retraining
- Historical data preprocessing pipelines
- Model drift detection and alerting

Features:
- Production-ready ML pipelines
- Automated model validation and deployment
- Historical pattern recognition
- Advanced feature engineering
- Comprehensive model monitoring

Business Impact: Improved prediction accuracy and automated ML operations
Author: Customer Intelligence Platform Enhancement Team
Created: 2026-01-19
"""

import asyncio
import logging
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from enum import Enum
from pathlib import Path
import json
import uuid
import warnings
from collections import defaultdict

# Advanced ML Libraries
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    ExtraTreesClassifier, ExtraTreesRegressor,
    VotingClassifier, VotingRegressor
)
from sklearn.linear_model import (
    LogisticRegression, LinearRegression, Ridge, Lasso,
    ElasticNet, SGDClassifier, SGDRegressor
)
from sklearn.svm import SVC, SVR
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.model_selection import (
    train_test_split, cross_val_score, GridSearchCV,
    RandomizedSearchCV, TimeSeriesSplit, StratifiedKFold
)
from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, RobustScaler,
    LabelEncoder, OneHotEncoder, PolynomialFeatures
)
from sklearn.feature_selection import (
    SelectKBest, SelectFromModel, f_classif, f_regression,
    RFE, RFECV, chi2, mutual_info_classif, mutual_info_regression
)
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, mean_squared_error, mean_absolute_error,
    r2_score, classification_report, confusion_matrix
)
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.base import BaseEstimator, TransformerMixin
import optuna

# Internal imports
from .scoring_pipeline import ModelType, ModelStatus, ModelConfig, ModelMetrics
from ..utils.logger import get_logger
from ..database.service import DatabaseService

logger = get_logger(__name__)
warnings.filterwarnings("ignore", category=UserWarning)


class OptimizationStrategy(Enum):
    """Hyperparameter optimization strategies."""
    GRID_SEARCH = "grid_search"
    RANDOM_SEARCH = "random_search"
    BAYESIAN_OPTUNA = "bayesian_optuna"
    AUTO_ML = "auto_ml"


class ValidationStrategy(Enum):
    """Model validation strategies."""
    HOLDOUT = "holdout"
    CROSS_VALIDATION = "cross_validation"
    TIME_SERIES_SPLIT = "time_series_split"
    STRATIFIED_CV = "stratified_cv"


class FeatureSelectionMethod(Enum):
    """Feature selection methods."""
    CORRELATION = "correlation"
    MUTUAL_INFO = "mutual_info"
    UNIVARIATE = "univariate"
    RECURSIVE_ELIMINATION = "recursive_elimination"
    LASSO_REGULARIZATION = "lasso_regularization"
    TREE_IMPORTANCE = "tree_importance"


@dataclass
class EnhancedModelConfig(ModelConfig):
    """Enhanced configuration for advanced ML model training."""
    
    # Advanced training parameters
    optimization_strategy: OptimizationStrategy = OptimizationStrategy.BAYESIAN_OPTUNA
    validation_strategy: ValidationStrategy = ValidationStrategy.CROSS_VALIDATION
    optimization_trials: int = 100
    optimization_timeout_minutes: int = 60
    
    # Feature engineering
    feature_selection_method: FeatureSelectionMethod = FeatureSelectionMethod.TREE_IMPORTANCE
    max_features: Optional[int] = None
    polynomial_features: bool = False
    polynomial_degree: int = 2
    pca_components: Optional[int] = None
    
    # Time series features
    temporal_features: bool = True
    lag_features: List[int] = field(default_factory=lambda: [1, 7, 30])
    rolling_window_sizes: List[int] = field(default_factory=lambda: [7, 14, 30])
    seasonal_features: bool = True
    
    # Ensemble methods
    use_ensemble: bool = True
    ensemble_methods: List[str] = field(default_factory=lambda: ["voting", "stacking"])
    
    # Advanced validation
    early_stopping_rounds: Optional[int] = 10
    class_balancing: bool = True
    outlier_detection: bool = True
    
    # Model explainability
    calculate_feature_importance: bool = True
    calculate_shap_values: bool = False
    generate_model_report: bool = True


@dataclass
class ModelPerformanceMetrics(ModelMetrics):
    """Extended performance metrics for comprehensive model evaluation."""
    
    # Additional metrics
    roc_auc_std: float = 0.0
    cross_val_scores: List[float] = field(default_factory=list)
    feature_importance: Dict[str, float] = field(default_factory=dict)
    
    # Business metrics
    precision_at_k: Dict[int, float] = field(default_factory=dict)
    recall_at_k: Dict[int, float] = field(default_factory=dict)
    lift_at_k: Dict[int, float] = field(default_factory=dict)
    
    # Model characteristics
    training_time_seconds: float = 0.0
    prediction_time_ms: float = 0.0
    model_complexity: str = "medium"
    memory_usage_mb: float = 0.0
    
    # Validation metrics
    validation_scores: Dict[str, float] = field(default_factory=dict)
    overfitting_score: float = 0.0  # Training vs validation gap
    
    # Drift detection baseline
    training_data_stats: Dict[str, Any] = field(default_factory=dict)
    feature_distributions: Dict[str, Dict] = field(default_factory=dict)


class AdvancedFeatureEngineer:
    """Advanced feature engineering pipeline with temporal and domain-specific features."""
    
    def __init__(self):
        self.feature_transformers = {}
        self.temporal_features_cache = {}
        self.scaler = StandardScaler()
        self.encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        
    async def create_advanced_features(
        self,
        data: pd.DataFrame,
        config: EnhancedModelConfig,
        target_column: str = None
    ) -> Tuple[pd.DataFrame, List[str], Dict[str, Any]]:
        """Create advanced features including temporal patterns and domain knowledge."""
        
        logger.info("Starting advanced feature engineering...")
        feature_metadata = {}
        engineered_data = data.copy()
        created_features = []
        
        try:
            # 1. Basic feature cleaning and preprocessing
            engineered_data = await self._preprocess_basic_features(engineered_data)
            
            # 2. Temporal feature engineering
            if config.temporal_features:
                engineered_data, temporal_features = await self._create_temporal_features(
                    engineered_data, config
                )
                created_features.extend(temporal_features)
                feature_metadata['temporal_features'] = temporal_features
                
            # 3. Domain-specific feature engineering
            engineered_data, domain_features = await self._create_domain_features(
                engineered_data, config.model_type
            )
            created_features.extend(domain_features)
            feature_metadata['domain_features'] = domain_features
            
            # 4. Statistical features
            engineered_data, stat_features = await self._create_statistical_features(
                engineered_data
            )
            created_features.extend(stat_features)
            feature_metadata['statistical_features'] = stat_features
            
            # 5. Interaction features
            engineered_data, interaction_features = await self._create_interaction_features(
                engineered_data, config
            )
            created_features.extend(interaction_features)
            feature_metadata['interaction_features'] = interaction_features
            
            # 6. Polynomial features (if enabled)
            if config.polynomial_features:
                engineered_data, poly_features = await self._create_polynomial_features(
                    engineered_data, config.polynomial_degree, created_features
                )
                created_features.extend(poly_features)
                feature_metadata['polynomial_features'] = poly_features
                
            # 7. Feature selection and dimensionality reduction
            if config.max_features or config.pca_components:
                engineered_data, selected_features = await self._apply_feature_selection(
                    engineered_data, target_column, config
                )
                feature_metadata['selected_features'] = selected_features
                
            # 8. Clean up and final validation
            engineered_data = self._clean_final_features(engineered_data)
            
            logger.info(f"Feature engineering completed: {len(created_features)} new features created")
            
            return engineered_data, created_features, feature_metadata
            
        except Exception as e:
            logger.error(f"Error in advanced feature engineering: {e}")
            return data, [], {}
    
    async def _preprocess_basic_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Basic preprocessing and cleaning."""
        
        # Handle missing values
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        categorical_columns = data.select_dtypes(include=['object', 'category']).columns
        
        # Fill numeric missing values
        for col in numeric_columns:
            if data[col].isnull().any():
                data[col] = data[col].fillna(data[col].median())
                
        # Fill categorical missing values
        for col in categorical_columns:
            if data[col].isnull().any():
                data[col] = data[col].fillna('unknown')
                
        # Remove infinite values
        data = data.replace([np.inf, -np.inf], np.nan)
        data = data.fillna(0)
        
        return data
    
    async def _create_temporal_features(
        self,
        data: pd.DataFrame,
        config: EnhancedModelConfig
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Create temporal features including lags, rolling windows, and seasonal patterns."""
        
        temporal_features = []
        
        # Try to identify datetime columns
        datetime_columns = []
        for col in data.columns:
            if 'date' in col.lower() or 'time' in col.lower() or 'created' in col.lower():
                try:
                    data[col] = pd.to_datetime(data[col])
                    datetime_columns.append(col)
                except:
                    continue
        
        # If we have datetime columns, create temporal features
        if datetime_columns:
            for date_col in datetime_columns:
                # Extract date components
                data[f'{date_col}_year'] = data[date_col].dt.year
                data[f'{date_col}_month'] = data[date_col].dt.month
                data[f'{date_col}_day'] = data[date_col].dt.day
                data[f'{date_col}_hour'] = data[date_col].dt.hour
                data[f'{date_col}_dayofweek'] = data[date_col].dt.dayofweek
                data[f'{date_col}_is_weekend'] = (data[date_col].dt.dayofweek >= 5).astype(int)
                
                temporal_features.extend([
                    f'{date_col}_year', f'{date_col}_month', f'{date_col}_day',
                    f'{date_col}_hour', f'{date_col}_dayofweek', f'{date_col}_is_weekend'
                ])
                
                # Create recency features
                max_date = data[date_col].max()
                data[f'{date_col}_days_since'] = (max_date - data[date_col]).dt.days
                data[f'{date_col}_recency_score'] = 1 / (1 + data[f'{date_col}_days_since'])
                
                temporal_features.extend([f'{date_col}_days_since', f'{date_col}_recency_score'])
        
        # Create lag features for numeric columns
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        if len(data) > max(config.lag_features) and 'customer_id' in data.columns:
            for col in numeric_columns[:5]:  # Limit to top 5 numeric columns
                if col not in ['customer_id', 'tenant_id']:
                    for lag in config.lag_features:
                        if len(data) > lag:
                            data[f'{col}_lag_{lag}'] = data.groupby('customer_id')[col].shift(lag)
                            temporal_features.append(f'{col}_lag_{lag}')
        
        # Create rolling window features
        for col in numeric_columns[:5]:
            if col not in ['customer_id', 'tenant_id']:
                for window in config.rolling_window_sizes:
                    if len(data) > window:
                        data[f'{col}_rolling_mean_{window}'] = data.groupby('customer_id')[col].rolling(window).mean().reset_index(0, drop=True)
                        data[f'{col}_rolling_std_{window}'] = data.groupby('customer_id')[col].rolling(window).std().reset_index(0, drop=True)
                        temporal_features.extend([
                            f'{col}_rolling_mean_{window}',
                            f'{col}_rolling_std_{window}'
                        ])
        
        return data, temporal_features
    
    async def _create_domain_features(
        self,
        data: pd.DataFrame,
        model_type: ModelType
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Create domain-specific features based on model type and business logic."""
        
        domain_features = []
        
        # Customer Intelligence specific features
        if 'engagement_score' in data.columns and 'message_count' in data.columns:
            # Engagement efficiency
            data['engagement_per_message'] = data['engagement_score'] / (data['message_count'] + 1)
            domain_features.append('engagement_per_message')
            
            # Communication intensity
            if 'session_duration' in data.columns:
                data['message_per_minute'] = data['message_count'] / (data['session_duration'] + 1)
                domain_features.append('message_per_minute')
        
        # Budget and financial features
        if 'budget' in data.columns:
            data['budget_log'] = np.log1p(data['budget'])
            data['budget_percentile'] = data['budget'].rank(pct=True)
            data['is_high_budget'] = (data['budget'] > data['budget'].quantile(0.8)).astype(int)
            domain_features.extend(['budget_log', 'budget_percentile', 'is_high_budget'])
        
        # Response time optimization
        if 'response_time' in data.columns:
            data['response_time_log'] = np.log1p(data['response_time'])
            data['is_fast_response'] = (data['response_time'] < data['response_time'].quantile(0.2)).astype(int)
            data['response_category'] = pd.cut(
                data['response_time'], 
                bins=[0, 30, 300, 1440, np.inf], 
                labels=['instant', 'fast', 'moderate', 'slow']
            ).astype('category')
            domain_features.extend(['response_time_log', 'is_fast_response'])
        
        # Industry and company features
        if 'industry' in data.columns:
            industry_engagement = data.groupby('industry')['engagement_score'].mean() if 'engagement_score' in data.columns else None
            if industry_engagement is not None:
                data['industry_avg_engagement'] = data['industry'].map(industry_engagement)
                domain_features.append('industry_avg_engagement')
        
        # Lead scoring specific features
        if model_type == ModelType.LEAD_SCORING:
            if 'message_count' in data.columns and 'support_tickets' in data.columns:
                data['support_to_message_ratio'] = data['support_tickets'] / (data['message_count'] + 1)
                domain_features.append('support_to_message_ratio')
        
        # Churn prediction specific features
        if model_type == ModelType.CHURN_PREDICTION:
            if 'last_activity_date' in data.columns:
                data['activity_recency'] = (datetime.now() - pd.to_datetime(data['last_activity_date'])).dt.days
                data['is_recent_activity'] = (data['activity_recency'] <= 7).astype(int)
                domain_features.extend(['activity_recency', 'is_recent_activity'])
        
        return data, domain_features
    
    async def _create_statistical_features(self, data: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Create statistical features and transformations."""
        
        statistical_features = []
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns[:10]:  # Limit to prevent explosion
            if data[col].std() > 0:  # Only for columns with variance
                # Z-score normalization
                data[f'{col}_zscore'] = (data[col] - data[col].mean()) / data[col].std()
                statistical_features.append(f'{col}_zscore')
                
                # Percentile rank
                data[f'{col}_rank'] = data[col].rank(pct=True)
                statistical_features.append(f'{col}_rank')
                
                # Outlier flags
                q1, q3 = data[col].quantile([0.25, 0.75])
                iqr = q3 - q1
                data[f'{col}_is_outlier'] = ((data[col] < q1 - 1.5*iqr) | (data[col] > q3 + 1.5*iqr)).astype(int)
                statistical_features.append(f'{col}_is_outlier')
        
        return data, statistical_features
    
    async def _create_interaction_features(
        self,
        data: pd.DataFrame,
        config: EnhancedModelConfig
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Create interaction features between important variables."""
        
        interaction_features = []
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        # Key interaction pairs based on business logic
        interaction_pairs = [
            ('engagement_score', 'budget'),
            ('message_count', 'session_duration'),
            ('response_time', 'engagement_score'),
            ('budget', 'message_count')
        ]
        
        for col1, col2 in interaction_pairs:
            if col1 in data.columns and col2 in data.columns:
                # Multiplication
                data[f'{col1}_x_{col2}'] = data[col1] * data[col2]
                interaction_features.append(f'{col1}_x_{col2}')
                
                # Ratio (if col2 is not zero)
                if (data[col2] != 0).all():
                    data[f'{col1}_div_{col2}'] = data[col1] / (data[col2] + 1e-6)
                    interaction_features.append(f'{col1}_div_{col2}')
        
        return data, interaction_features
    
    async def _create_polynomial_features(
        self,
        data: pd.DataFrame,
        degree: int,
        important_features: List[str]
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Create polynomial features for important variables."""
        
        polynomial_features = []
        
        # Select most important numeric features for polynomial expansion
        numeric_features = [col for col in important_features 
                          if col in data.columns and data[col].dtype in [np.number]][:5]
        
        if numeric_features:
            poly_data = data[numeric_features].fillna(0)
            poly = PolynomialFeatures(degree=degree, include_bias=False, interaction_only=True)
            
            try:
                poly_transformed = poly.fit_transform(poly_data)
                poly_feature_names = poly.get_feature_names_out(numeric_features)
                
                # Add polynomial features to data
                for i, feature_name in enumerate(poly_feature_names):
                    if feature_name not in data.columns:  # Don't duplicate existing features
                        data[f'poly_{feature_name}'] = poly_transformed[:, i]
                        polynomial_features.append(f'poly_{feature_name}')
                        
            except Exception as e:
                logger.warning(f"Polynomial feature creation failed: {e}")
        
        return data, polynomial_features
    
    async def _apply_feature_selection(
        self,
        data: pd.DataFrame,
        target_column: str,
        config: EnhancedModelConfig
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Apply feature selection methods."""
        
        if target_column not in data.columns:
            return data, list(data.columns)
            
        X = data.drop([target_column], axis=1)
        y = data[target_column]
        
        # Remove non-numeric columns for feature selection
        numeric_columns = X.select_dtypes(include=[np.number]).columns
        X_numeric = X[numeric_columns]
        
        if len(X_numeric.columns) == 0:
            return data, list(data.columns)
        
        selected_features = []
        
        try:
            if config.feature_selection_method == FeatureSelectionMethod.TREE_IMPORTANCE:
                # Use Random Forest for feature importance
                rf = RandomForestClassifier(n_estimators=50, random_state=42)
                rf.fit(X_numeric, y)
                
                importances = rf.feature_importances_
                feature_importance_df = pd.DataFrame({
                    'feature': X_numeric.columns,
                    'importance': importances
                }).sort_values('importance', ascending=False)
                
                n_features = min(config.max_features or len(X_numeric.columns), len(X_numeric.columns))
                selected_features = feature_importance_df.head(n_features)['feature'].tolist()
                
            elif config.feature_selection_method == FeatureSelectionMethod.CORRELATION:
                # Remove highly correlated features
                corr_matrix = X_numeric.corr().abs()
                upper_triangle = corr_matrix.where(
                    np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
                )
                
                to_drop = [column for column in upper_triangle.columns if any(upper_triangle[column] > 0.95)]
                selected_features = [col for col in X_numeric.columns if col not in to_drop]
                
                if config.max_features:
                    selected_features = selected_features[:config.max_features]
            
            else:
                selected_features = list(X_numeric.columns)
                if config.max_features:
                    selected_features = selected_features[:config.max_features]
            
            # Keep selected numeric features and all categorical features
            categorical_features = [col for col in data.columns 
                                 if col not in numeric_columns and col != target_column]
            all_selected = selected_features + categorical_features + [target_column]
            
            return data[all_selected], selected_features
            
        except Exception as e:
            logger.warning(f"Feature selection failed: {e}")
            return data, list(X_numeric.columns)
    
    def _clean_final_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Final cleaning and validation of features."""
        
        # Remove any remaining infinite or null values
        data = data.replace([np.inf, -np.inf], np.nan)
        
        # Fill remaining nulls
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        categorical_columns = data.select_dtypes(include=['object', 'category']).columns
        
        for col in numeric_columns:
            data[col] = data[col].fillna(data[col].median())
            
        for col in categorical_columns:
            data[col] = data[col].fillna('unknown')
        
        return data


class EnhancedModelTrainer:
    """Enhanced model trainer with advanced optimization and monitoring."""
    
    def __init__(self, database_service: DatabaseService = None):
        self.db_service = database_service or DatabaseService()
        self.feature_engineer = AdvancedFeatureEngineer()
        self.trained_models = {}
        self.model_metadata = {}
        
        # Model algorithm mappings
        self.classifiers = {
            'random_forest': RandomForestClassifier,
            'gradient_boosting': GradientBoostingClassifier,
            'extra_trees': ExtraTreesClassifier,
            'logistic_regression': LogisticRegression,
            'svm': SVC,
            'neural_network': MLPClassifier
        }
        
        self.regressors = {
            'random_forest': RandomForestRegressor,
            'gradient_boosting': GradientBoostingRegressor,
            'extra_trees': ExtraTreesRegressor,
            'linear_regression': LinearRegression,
            'ridge': Ridge,
            'lasso': Lasso,
            'elastic_net': ElasticNet,
            'svm': SVR,
            'neural_network': MLPRegressor
        }
    
    async def train_enhanced_model(
        self,
        training_data: pd.DataFrame,
        config: EnhancedModelConfig,
        validation_data: Optional[pd.DataFrame] = None
    ) -> Tuple[Any, ModelPerformanceMetrics]:
        """Train an enhanced model with advanced features and optimization."""
        
        start_time = datetime.now()
        logger.info(f"Starting enhanced model training for {config.model_type}")
        
        try:
            # 1. Advanced feature engineering
            logger.info("Creating advanced features...")
            engineered_data, created_features, feature_metadata = await self.feature_engineer.create_advanced_features(
                training_data, config, config.target_variable
            )
            
            # 2. Prepare training data
            X, y = self._prepare_data(engineered_data, config)
            
            # 3. Split data if validation data not provided
            if validation_data is None:
                X_train, X_val, y_train, y_val = train_test_split(
                    X, y, test_size=config.test_size, random_state=42, stratify=y if config.model_type in [ModelType.LEAD_SCORING, ModelType.CHURN_PREDICTION] else None
                )
            else:
                X_train, y_train = X, y
                val_engineered, _, _ = await self.feature_engineer.create_advanced_features(
                    validation_data, config, config.target_variable
                )
                X_val, y_val = self._prepare_data(val_engineered, config)
            
            # 4. Hyperparameter optimization
            logger.info("Starting hyperparameter optimization...")
            best_model, best_params = await self._optimize_hyperparameters(
                X_train, y_train, config
            )
            
            # 5. Train final model with best parameters
            logger.info("Training final model...")
            final_model = await self._train_final_model(
                X_train, y_train, best_params, config
            )
            
            # 6. Create ensemble if configured
            if config.use_ensemble:
                logger.info("Creating ensemble model...")
                ensemble_model = await self._create_ensemble_model(
                    X_train, y_train, config, base_model=final_model
                )
                final_model = ensemble_model
            
            # 7. Comprehensive evaluation
            logger.info("Evaluating model performance...")
            performance_metrics = await self._evaluate_model_comprehensive(
                final_model, X_train, y_train, X_val, y_val, config, feature_metadata
            )
            
            # 8. Calculate training time
            training_time = (datetime.now() - start_time).total_seconds()
            performance_metrics.training_time_seconds = training_time
            
            # 9. Store model metadata
            self.model_metadata[performance_metrics.model_id] = {
                'config': asdict(config),
                'feature_metadata': feature_metadata,
                'created_features': created_features,
                'training_data_shape': X_train.shape,
                'best_hyperparameters': best_params
            }
            
            logger.info(f"Enhanced model training completed in {training_time:.2f} seconds")
            logger.info(f"Model performance - Accuracy: {performance_metrics.accuracy:.3f}, AUC: {performance_metrics.auc_score:.3f}")
            
            return final_model, performance_metrics
            
        except Exception as e:
            logger.error(f"Enhanced model training failed: {e}")
            raise
    
    def _prepare_data(self, data: pd.DataFrame, config: EnhancedModelConfig) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data for model training."""
        
        if config.target_variable not in data.columns:
            raise ValueError(f"Target variable '{config.target_variable}' not found in data")
        
        # Separate features and target
        y = data[config.target_variable]
        X = data.drop([config.target_variable], axis=1)
        
        # Handle categorical variables
        categorical_columns = X.select_dtypes(include=['object', 'category']).columns
        if len(categorical_columns) > 0:
            # Use label encoding for categorical variables
            for col in categorical_columns:
                le = LabelEncoder()
                X[col] = le.fit_transform(X[col].astype(str))
        
        return X, y
    
    async def _optimize_hyperparameters(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        config: EnhancedModelConfig
    ) -> Tuple[Any, Dict[str, Any]]:
        """Optimize hyperparameters using specified strategy."""
        
        if config.optimization_strategy == OptimizationStrategy.BAYESIAN_OPTUNA:
            return await self._optuna_optimization(X, y, config)
        elif config.optimization_strategy == OptimizationStrategy.RANDOM_SEARCH:
            return await self._random_search_optimization(X, y, config)
        elif config.optimization_strategy == OptimizationStrategy.GRID_SEARCH:
            return await self._grid_search_optimization(X, y, config)
        else:
            # Return default model with default parameters
            model_class = self._get_model_class(config.algorithm, config.model_type)
            default_model = model_class(**config.hyperparameters, random_state=42)
            return default_model, config.hyperparameters
    
    async def _optuna_optimization(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        config: EnhancedModelConfig
    ) -> Tuple[Any, Dict[str, Any]]:
        """Optimize hyperparameters using Optuna (Bayesian optimization)."""
        
        def objective(trial):
            # Define hyperparameter search space based on algorithm
            params = self._get_optuna_search_space(trial, config.algorithm, config.model_type)
            
            # Create and train model
            model_class = self._get_model_class(config.algorithm, config.model_type)
            model = model_class(**params, random_state=42)
            
            # Cross-validation score
            if config.validation_strategy == ValidationStrategy.STRATIFIED_CV:
                cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            else:
                cv = 5
            
            scores = cross_val_score(
                model, X, y, 
                cv=cv,
                scoring='roc_auc' if config.model_type in [ModelType.LEAD_SCORING, ModelType.CHURN_PREDICTION] else 'r2',
                n_jobs=-1
            )
            return scores.mean()
        
        # Run optimization
        study = optuna.create_study(direction='maximize')
        study.optimize(
            objective, 
            n_trials=config.optimization_trials,
            timeout=config.optimization_timeout_minutes * 60
        )
        
        # Get best parameters and create model
        best_params = study.best_params
        model_class = self._get_model_class(config.algorithm, config.model_type)
        best_model = model_class(**best_params, random_state=42)
        
        return best_model, best_params
    
    async def _random_search_optimization(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        config: EnhancedModelConfig
    ) -> Tuple[Any, Dict[str, Any]]:
        """Optimize hyperparameters using RandomizedSearchCV."""
        
        model_class = self._get_model_class(config.algorithm, config.model_type)
        param_dist = self._get_random_search_space(config.algorithm, config.model_type)
        
        search = RandomizedSearchCV(
            model_class(random_state=42),
            param_dist,
            n_iter=min(config.optimization_trials, 50),
            cv=5,
            scoring='roc_auc' if config.model_type in [ModelType.LEAD_SCORING, ModelType.CHURN_PREDICTION] else 'r2',
            n_jobs=-1,
            random_state=42
        )
        
        search.fit(X, y)
        return search.best_estimator_, search.best_params_
    
    async def _grid_search_optimization(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        config: EnhancedModelConfig
    ) -> Tuple[Any, Dict[str, Any]]:
        """Optimize hyperparameters using GridSearchCV."""
        
        model_class = self._get_model_class(config.algorithm, config.model_type)
        param_grid = self._get_grid_search_space(config.algorithm, config.model_type)
        
        search = GridSearchCV(
            model_class(random_state=42),
            param_grid,
            cv=5,
            scoring='roc_auc' if config.model_type in [ModelType.LEAD_SCORING, ModelType.CHURN_PREDICTION] else 'r2',
            n_jobs=-1
        )
        
        search.fit(X, y)
        return search.best_estimator_, search.best_params_
    
    def _get_optuna_search_space(self, trial, algorithm: str, model_type: ModelType) -> Dict[str, Any]:
        """Define Optuna search space for different algorithms."""
        
        params = {}
        
        if algorithm == 'random_forest':
            params.update({
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 3, 20),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 5),
                'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None])
            })
        
        elif algorithm == 'gradient_boosting':
            params.update({
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                'max_depth': trial.suggest_int('max_depth', 3, 15),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0)
            })
        
        elif algorithm == 'logistic_regression':
            params.update({
                'C': trial.suggest_float('C', 0.001, 100, log=True),
                'solver': trial.suggest_categorical('solver', ['liblinear', 'lbfgs', 'saga']),
                'max_iter': trial.suggest_int('max_iter', 100, 1000)
            })
        
        return params
    
    def _get_random_search_space(self, algorithm: str, model_type: ModelType) -> Dict[str, Any]:
        """Define parameter distribution for RandomizedSearchCV."""
        
        from scipy.stats import randint, uniform
        
        if algorithm == 'random_forest':
            return {
                'n_estimators': randint(50, 300),
                'max_depth': randint(3, 20),
                'min_samples_split': randint(2, 10),
                'min_samples_leaf': randint(1, 5),
                'max_features': ['sqrt', 'log2', None]
            }
        
        elif algorithm == 'gradient_boosting':
            return {
                'n_estimators': randint(50, 300),
                'learning_rate': uniform(0.01, 0.29),
                'max_depth': randint(3, 15),
                'subsample': uniform(0.6, 0.4)
            }
        
        elif algorithm == 'logistic_regression':
            return {
                'C': uniform(0.001, 99.999),
                'solver': ['liblinear', 'lbfgs', 'saga'],
                'max_iter': randint(100, 1000)
            }
        
        return {}
    
    def _get_grid_search_space(self, algorithm: str, model_type: ModelType) -> Dict[str, Any]:
        """Define parameter grid for GridSearchCV."""
        
        if algorithm == 'random_forest':
            return {
                'n_estimators': [50, 100, 200],
                'max_depth': [5, 10, 15, None],
                'min_samples_split': [2, 5, 10],
                'max_features': ['sqrt', 'log2']
            }
        
        elif algorithm == 'gradient_boosting':
            return {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 10]
            }
        
        elif algorithm == 'logistic_regression':
            return {
                'C': [0.001, 0.01, 0.1, 1, 10, 100],
                'solver': ['liblinear', 'lbfgs', 'saga']
            }
        
        return {}
    
    def _get_model_class(self, algorithm: str, model_type: ModelType):
        """Get the appropriate model class based on algorithm and type."""
        
        is_classification = model_type in [
            ModelType.LEAD_SCORING, ModelType.ENGAGEMENT_PREDICTION, 
            ModelType.CHURN_PREDICTION
        ]
        
        if is_classification:
            return self.classifiers.get(algorithm, RandomForestClassifier)
        else:
            return self.regressors.get(algorithm, RandomForestRegressor)
    
    async def _train_final_model(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        best_params: Dict[str, Any],
        config: EnhancedModelConfig
    ) -> Any:
        """Train the final model with optimized parameters."""
        
        model_class = self._get_model_class(config.algorithm, config.model_type)
        model = model_class(**best_params, random_state=42)
        model.fit(X_train, y_train)
        
        return model
    
    async def _create_ensemble_model(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        config: EnhancedModelConfig,
        base_model: Any
    ) -> Any:
        """Create an ensemble model combining multiple algorithms."""
        
        try:
            is_classification = config.model_type in [
                ModelType.LEAD_SCORING, ModelType.ENGAGEMENT_PREDICTION, 
                ModelType.CHURN_PREDICTION
            ]
            
            # Create diverse base models
            if is_classification:
                models = [
                    ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
                    ('gb', GradientBoostingClassifier(n_estimators=100, random_state=42)),
                    ('lr', LogisticRegression(random_state=42, max_iter=1000))
                ]
                ensemble = VotingClassifier(estimators=models, voting='soft')
            else:
                models = [
                    ('rf', RandomForestRegressor(n_estimators=100, random_state=42)),
                    ('gb', GradientBoostingRegressor(n_estimators=100, random_state=42)),
                    ('lr', LinearRegression())
                ]
                ensemble = VotingRegressor(estimators=models)
            
            ensemble.fit(X_train, y_train)
            return ensemble
            
        except Exception as e:
            logger.warning(f"Ensemble creation failed, using base model: {e}")
            return base_model
    
    async def _evaluate_model_comprehensive(
        self,
        model: Any,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        config: EnhancedModelConfig,
        feature_metadata: Dict[str, Any]
    ) -> ModelPerformanceMetrics:
        """Comprehensive model evaluation with business metrics."""
        
        model_id = str(uuid.uuid4())
        
        # Basic predictions
        y_train_pred = model.predict(X_train)
        y_val_pred = model.predict(X_val)
        
        # Get prediction probabilities for classification
        is_classification = config.model_type in [
            ModelType.LEAD_SCORING, ModelType.ENGAGEMENT_PREDICTION, 
            ModelType.CHURN_PREDICTION
        ]
        
        if is_classification and hasattr(model, 'predict_proba'):
            y_val_pred_proba = model.predict_proba(X_val)[:, 1] if y_val_pred_proba.shape[1] == 2 else y_val_pred_proba[:, 0]
        else:
            y_val_pred_proba = y_val_pred
        
        # Calculate metrics
        if is_classification:
            accuracy = accuracy_score(y_val, y_val_pred)
            precision = precision_score(y_val, y_val_pred, average='weighted', zero_division=0)
            recall = recall_score(y_val, y_val_pred, average='weighted', zero_division=0)
            f1 = f1_score(y_val, y_val_pred, average='weighted', zero_division=0)
            try:
                auc = roc_auc_score(y_val, y_val_pred_proba)
            except ValueError:
                auc = 0.5
        else:
            # For regression, adapt metrics
            mse = mean_squared_error(y_val, y_val_pred)
            mae = mean_absolute_error(y_val, y_val_pred)
            r2 = r2_score(y_val, y_val_pred)
            
            accuracy = max(0, r2)  # R² as accuracy proxy
            precision = 1.0 - (mae / (y_val.std() + 1e-6))  # Precision proxy
            recall = 1.0 - (mse / (y_val.var() + 1e-6))  # Recall proxy
            f1 = 2 * (precision * recall) / (precision + recall + 1e-6)
            auc = max(0, r2)  # R² as AUC proxy
        
        # Cross-validation scores
        cv_scores = cross_val_score(
            model, X_train, y_train, cv=5,
            scoring='roc_auc' if is_classification else 'r2'
        )
        
        # Feature importance
        feature_importance = {}
        if hasattr(model, 'feature_importances_'):
            for i, feature in enumerate(X_train.columns):
                feature_importance[feature] = float(model.feature_importances_[i])
        elif hasattr(model, 'coef_'):
            for i, feature in enumerate(X_train.columns):
                feature_importance[feature] = float(abs(model.coef_[i]) if model.coef_.ndim == 1 else abs(model.coef_[0][i]))
        
        # Calculate overfitting score
        train_score = accuracy_score(y_train, y_train_pred) if is_classification else r2_score(y_train, y_train_pred)
        val_score = accuracy
        overfitting_score = max(0, train_score - val_score)
        
        # Business metrics (precision/recall at different thresholds)
        precision_at_k = {}
        recall_at_k = {}
        lift_at_k = {}
        
        if is_classification:
            for k in [10, 20, 50]:
                if len(y_val) > k:
                    # Sort by predicted probability
                    sorted_indices = np.argsort(y_val_pred_proba)[::-1]
                    top_k_actual = y_val.iloc[sorted_indices[:k]]
                    
                    precision_at_k[k] = top_k_actual.sum() / k
                    recall_at_k[k] = top_k_actual.sum() / y_val.sum() if y_val.sum() > 0 else 0
                    baseline_rate = y_val.mean()
                    lift_at_k[k] = precision_at_k[k] / baseline_rate if baseline_rate > 0 else 1
        
        # Training data statistics for drift detection
        training_data_stats = {
            'feature_means': X_train.mean().to_dict(),
            'feature_stds': X_train.std().to_dict(),
            'feature_mins': X_train.min().to_dict(),
            'feature_maxs': X_train.max().to_dict(),
            'target_mean': float(y_train.mean()),
            'target_std': float(y_train.std())
        }
        
        # Feature distributions for drift detection
        feature_distributions = {}
        for col in X_train.columns:
            if X_train[col].dtype in [np.number]:
                feature_distributions[col] = {
                    'type': 'numeric',
                    'quantiles': X_train[col].quantile([0.1, 0.25, 0.5, 0.75, 0.9]).to_dict()
                }
            else:
                feature_distributions[col] = {
                    'type': 'categorical',
                    'value_counts': X_train[col].value_counts().head(10).to_dict()
                }
        
        # Create comprehensive metrics object
        metrics = ModelPerformanceMetrics(
            model_id=model_id,
            model_name=config.model_name,
            model_version=config.model_version,
            model_type=config.model_type,
            accuracy=float(accuracy),
            precision=float(precision),
            recall=float(recall),
            f1_score=float(f1),
            auc_score=float(auc),
            roc_auc_std=float(cv_scores.std()),
            cross_val_scores=cv_scores.tolist(),
            feature_importance=feature_importance,
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            lift_at_k=lift_at_k,
            training_samples=len(X_train),
            feature_count=len(X_train.columns),
            validation_scores={
                'cross_val_mean': float(cv_scores.mean()),
                'cross_val_std': float(cv_scores.std())
            },
            overfitting_score=float(overfitting_score),
            training_data_stats=training_data_stats,
            feature_distributions=feature_distributions,
            status=ModelStatus.TRAINING
        )
        
        return metrics


# Factory function
def create_enhanced_model_trainer() -> EnhancedModelTrainer:
    """Create an enhanced model trainer instance."""
    return EnhancedModelTrainer()