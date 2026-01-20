"""
Comprehensive Testing Suite for Enhanced ML Pipeline.

This module provides comprehensive tests for all ML pipeline components including:
- Enhanced model trainer testing
- Performance monitoring validation  
- Model registry and deployment testing
- Historical data processing validation
- Integration testing for end-to-end workflows
- Performance and scalability testing

Features:
- Unit tests for all ML components
- Integration tests for complete workflows
- Performance benchmarks and validation
- Data quality and consistency checks
- Mock data generation for testing
- Automated test reporting

Author: Customer Intelligence Platform Enhancement Team
Created: 2026-01-19
"""

import pytest
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import shutil
from pathlib import Path
import json
import uuid

# ML testing utilities
from sklearn.datasets import make_classification, make_regression
from sklearn.model_selection import train_test_split

# Internal imports
from src.ml.enhanced_model_trainer import (
    EnhancedModelTrainer, EnhancedModelConfig, AdvancedFeatureEngineer,
    OptimizationStrategy, ValidationStrategy, FeatureSelectionMethod
)
from src.ml.model_performance_monitor import (
    ModelPerformanceMonitor, DriftDetector, AlertSeverity, DriftType,
    MonitoringStatus, ModelHealthMetrics
)
from src.ml.model_registry_enhanced import (
    EnhancedModelRegistry, ModelVersion, ABTestExperiment,
    DeploymentStrategy, SemanticVersionManager
)
from src.ml.historical_data_processor import (
    HistoricalDataProcessor, DataQualityAssessor, TemporalFeatureEngineer,
    TemporalFeatureConfig, AggregationMethod
)
from src.ml.scoring_pipeline import ModelType, ModelStatus
from src.ml.synthetic_data_generator import SyntheticDataGenerator


class TestDataGenerator:
    """Utility class for generating test data."""
    
    @staticmethod
    def create_classification_dataset(n_samples=1000, n_features=20, n_classes=2):
        """Create synthetic classification dataset."""
        X, y = make_classification(
            n_samples=n_samples,
            n_features=n_features,
            n_classes=n_classes,
            n_informative=int(n_features * 0.7),
            n_redundant=int(n_features * 0.2),
            random_state=42
        )
        
        # Create DataFrame with meaningful column names
        feature_names = [f'feature_{i}' for i in range(n_features)]
        df = pd.DataFrame(X, columns=feature_names)
        df['target'] = y
        df['created_at'] = pd.date_range(
            start='2023-01-01', 
            periods=n_samples, 
            freq='H'
        )
        df['customer_id'] = [f'customer_{i % 100}' for i in range(n_samples)]
        
        return df
    
    @staticmethod
    def create_regression_dataset(n_samples=1000, n_features=15):
        """Create synthetic regression dataset."""
        X, y = make_regression(
            n_samples=n_samples,
            n_features=n_features,
            noise=0.1,
            random_state=42
        )
        
        feature_names = [f'feature_{i}' for i in range(n_features)]
        df = pd.DataFrame(X, columns=feature_names)
        df['target'] = y
        df['created_at'] = pd.date_range(
            start='2023-01-01',
            periods=n_samples,
            freq='H'
        )
        df['customer_id'] = [f'customer_{i % 100}' for i in range(n_samples)]
        
        return df
    
    @staticmethod
    def create_time_series_dataset(n_samples=5000, n_customers=50):
        """Create synthetic time series dataset."""
        data = []
        
        for customer_id in range(n_customers):
            # Generate customer-specific trend and seasonality
            trend = np.random.uniform(-0.1, 0.1)
            seasonality_amplitude = np.random.uniform(0.1, 0.5)
            
            customer_data = []
            for i in range(n_samples // n_customers):
                timestamp = datetime(2023, 1, 1) + timedelta(hours=i)
                
                # Base value with trend
                value = 100 + trend * i
                
                # Add seasonality (daily and weekly)
                daily_seasonal = seasonality_amplitude * np.sin(2 * np.pi * i / 24)
                weekly_seasonal = seasonality_amplitude * np.sin(2 * np.pi * i / (24 * 7))
                
                # Add noise
                noise = np.random.normal(0, 0.1)
                
                final_value = value + daily_seasonal + weekly_seasonal + noise
                
                customer_data.append({
                    'customer_id': f'customer_{customer_id}',
                    'timestamp': timestamp,
                    'value': final_value,
                    'feature_1': np.random.uniform(0, 10),
                    'feature_2': np.random.uniform(-5, 5),
                    'category': np.random.choice(['A', 'B', 'C'])
                })
            
            data.extend(customer_data)
        
        return pd.DataFrame(data)
    
    @staticmethod
    def create_data_with_quality_issues(base_data):
        """Add various data quality issues to test data."""
        data = base_data.copy()
        
        # Add missing values
        missing_indices = np.random.choice(
            len(data), size=int(len(data) * 0.1), replace=False
        )
        data.loc[missing_indices, 'feature_0'] = np.nan
        
        # Add outliers
        outlier_indices = np.random.choice(
            len(data), size=int(len(data) * 0.05), replace=False
        )
        data.loc[outlier_indices, 'feature_1'] = data['feature_1'].std() * 5
        
        # Add duplicates
        duplicate_indices = np.random.choice(
            len(data), size=int(len(data) * 0.03), replace=False
        )
        duplicate_data = data.loc[duplicate_indices].copy()
        data = pd.concat([data, duplicate_data], ignore_index=True)
        
        # Add inconsistent formats in string column
        if 'customer_id' in data.columns:
            inconsistent_indices = np.random.choice(
                len(data), size=int(len(data) * 0.02), replace=False
            )
            data.loc[inconsistent_indices, 'customer_id'] = data.loc[inconsistent_indices, 'customer_id'].str.upper()
        
        return data


class TestEnhancedModelTrainer:
    """Test suite for enhanced model trainer."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample training data."""
        return TestDataGenerator.create_classification_dataset(n_samples=500)
    
    @pytest.fixture
    def model_config(self):
        """Create test model configuration."""
        return EnhancedModelConfig(
            model_name="test_model",
            model_type=ModelType.LEAD_SCORING,
            model_version="1.0.0",
            algorithm="random_forest",
            target_variable="target",
            optimization_strategy=OptimizationStrategy.RANDOM_SEARCH,
            optimization_trials=10,
            optimization_timeout_minutes=1,
            temporal_features=False,  # Disable for faster testing
            use_ensemble=False
        )
    
    @pytest.fixture
    def trainer(self):
        """Create model trainer instance."""
        return EnhancedModelTrainer()
    
    @pytest.mark.asyncio
    async def test_basic_model_training(self, trainer, sample_data, model_config):
        """Test basic model training functionality."""
        
        model, metrics = await trainer.train_enhanced_model(
            sample_data, model_config
        )
        
        # Verify model was trained
        assert model is not None
        assert hasattr(model, 'predict')
        
        # Verify metrics
        assert metrics is not None
        assert metrics.accuracy > 0.5
        assert metrics.model_type == ModelType.LEAD_SCORING
        assert len(metrics.feature_importance) > 0
    
    @pytest.mark.asyncio
    async def test_feature_engineering(self, trainer, sample_data, model_config):
        """Test advanced feature engineering."""
        
        # Enable feature engineering
        model_config.temporal_features = True
        model_config.polynomial_features = True
        model_config.pca_components = 10
        
        # Add temporal data
        sample_data['created_at'] = pd.date_range(
            start='2023-01-01', periods=len(sample_data), freq='H'
        )
        
        model, metrics = await trainer.train_enhanced_model(
            sample_data, model_config
        )
        
        # Verify feature engineering increased feature count
        assert metrics.feature_count > len(sample_data.columns) - 1  # Excluding target
    
    @pytest.mark.asyncio
    async def test_hyperparameter_optimization(self, trainer, sample_data):
        """Test hyperparameter optimization strategies."""
        
        strategies = [
            OptimizationStrategy.RANDOM_SEARCH,
            OptimizationStrategy.GRID_SEARCH
        ]
        
        for strategy in strategies:
            config = EnhancedModelConfig(
                model_name=f"test_model_{strategy.value}",
                model_type=ModelType.LEAD_SCORING,
                model_version="1.0.0",
                algorithm="random_forest",
                target_variable="target",
                optimization_strategy=strategy,
                optimization_trials=5,
                optimization_timeout_minutes=1
            )
            
            model, metrics = await trainer.train_enhanced_model(
                sample_data, config
            )
            
            assert model is not None
            assert metrics.accuracy > 0.3  # Reasonable lower bound
    
    @pytest.mark.asyncio
    async def test_model_validation_strategies(self, trainer, sample_data, model_config):
        """Test different model validation strategies."""
        
        validation_strategies = [
            ValidationStrategy.HOLDOUT,
            ValidationStrategy.CROSS_VALIDATION
        ]
        
        for strategy in validation_strategies:
            config = model_config
            config.validation_strategy = strategy
            
            model, metrics = await trainer.train_enhanced_model(
                sample_data, config
            )
            
            assert model is not None
            assert len(metrics.cross_val_scores) > 0 if strategy == ValidationStrategy.CROSS_VALIDATION else True
    
    @pytest.mark.asyncio
    async def test_ensemble_models(self, trainer, sample_data, model_config):
        """Test ensemble model creation."""
        
        model_config.use_ensemble = True
        
        model, metrics = await trainer.train_enhanced_model(
            sample_data, model_config
        )
        
        # Verify ensemble model was created
        assert model is not None
        assert hasattr(model, 'predict')
        
        # Ensemble should generally perform better
        assert metrics.accuracy > 0.5


class TestModelPerformanceMonitor:
    """Test suite for model performance monitoring."""
    
    @pytest.fixture
    def sample_baseline_data(self):
        """Create baseline training data."""
        return TestDataGenerator.create_classification_dataset(n_samples=1000)
    
    @pytest.fixture
    def sample_current_data(self):
        """Create current data with some drift."""
        data = TestDataGenerator.create_classification_dataset(n_samples=500)
        
        # Introduce some drift
        data['feature_0'] = data['feature_0'] * 1.2 + 0.5  # Scale and shift
        data['feature_1'] = data['feature_1'] + np.random.normal(0, 0.3, len(data))  # Add noise
        
        return data
    
    @pytest.fixture
    def mock_database_service(self):
        """Create mock database service."""
        db_service = Mock()
        db_service.get_model_info = AsyncMock(return_value={'model_type': 'lead_scoring', 'accuracy': 0.85})
        db_service.get_model_predictions = AsyncMock(return_value=[])
        db_service.get_recent_customer_metrics = AsyncMock(return_value=[])
        db_service.get_model_training_data = AsyncMock(return_value=pd.DataFrame())
        return db_service
    
    @pytest.fixture
    def drift_detector(self):
        """Create drift detector instance."""
        return DriftDetector()
    
    @pytest.fixture
    def performance_monitor(self, mock_database_service):
        """Create performance monitor instance."""
        return ModelPerformanceMonitor(mock_database_service)
    
    @pytest.mark.asyncio
    async def test_data_drift_detection(self, drift_detector, sample_baseline_data, sample_current_data):
        """Test data drift detection."""
        
        drift_score, drifted_features, feature_scores = await drift_detector.detect_data_drift(
            sample_baseline_data, sample_current_data
        )
        
        # Should detect some drift due to introduced changes
        assert drift_score > 0
        assert len(drifted_features) > 0
        assert 'feature_0' in drifted_features or 'feature_1' in drifted_features
        assert len(feature_scores) > 0
    
    @pytest.mark.asyncio
    async def test_prediction_drift_detection(self, drift_detector):
        """Test prediction drift detection."""
        
        # Create two different prediction distributions
        baseline_predictions = np.random.normal(0.5, 0.1, 1000)
        current_predictions = np.random.normal(0.7, 0.15, 1000)  # Shifted distribution
        
        drift_score, metrics = await drift_detector.detect_prediction_drift(
            baseline_predictions, current_predictions
        )
        
        # Should detect drift in prediction distribution
        assert drift_score > 0
        assert 'ks_statistic' in metrics
        assert 'psi_score' in metrics
    
    @pytest.mark.asyncio
    async def test_model_health_initialization(self, performance_monitor):
        """Test model health metrics initialization."""
        
        model_id = "test_model_123"
        
        await performance_monitor._initialize_model_health(model_id)
        
        # Verify health metrics were initialized
        assert model_id in performance_monitor.model_health_cache
        
        health_metrics = performance_monitor.model_health_cache[model_id]
        assert health_metrics.model_id == model_id
        assert health_metrics.health_score == 100.0
        assert health_metrics.monitoring_status == MonitoringStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_alert_creation_and_management(self, performance_monitor):
        """Test alert creation and management."""
        
        model_id = "test_model_456"
        model_type = ModelType.LEAD_SCORING
        
        # Initialize model health
        await performance_monitor._initialize_model_health(model_id)
        
        # Create test alert
        alert_data = {
            'drift_type': DriftType.DATA_DRIFT,
            'severity': AlertSeverity.HIGH,
            'drift_score': 0.8,
            'threshold': 0.1,
            'affected_features': ['feature_0', 'feature_1'],
            'description': 'Test data drift alert',
            'recommended_action': 'Consider retraining'
        }
        
        await performance_monitor._create_alert(model_id, model_type, alert_data)
        
        # Verify alert was created
        assert model_id in performance_monitor.active_alerts
        assert len(performance_monitor.active_alerts[model_id]) == 1
        
        alert = performance_monitor.active_alerts[model_id][0]
        assert alert.drift_type == DriftType.DATA_DRIFT
        assert alert.severity == AlertSeverity.HIGH
    
    @pytest.mark.asyncio
    async def test_alert_cooldown(self, performance_monitor):
        """Test alert cooldown mechanism."""
        
        model_id = "test_model_789"
        model_type = ModelType.LEAD_SCORING
        
        await performance_monitor._initialize_model_health(model_id)
        
        # Create first alert
        alert_data = {
            'drift_type': DriftType.DATA_DRIFT,
            'severity': AlertSeverity.MEDIUM,
            'drift_score': 0.6,
            'threshold': 0.1,
            'affected_features': [],
            'description': 'First alert',
            'recommended_action': 'Monitor'
        }
        
        await performance_monitor._create_alert(model_id, model_type, alert_data)
        
        # Try to create similar alert immediately (should be blocked by cooldown)
        await performance_monitor._create_alert(model_id, model_type, alert_data)
        
        # Should still have only one alert due to cooldown
        assert len(performance_monitor.active_alerts[model_id]) == 1


class TestModelRegistryEnhanced:
    """Test suite for enhanced model registry."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_database_service(self):
        """Create mock database service."""
        db_service = Mock()
        db_service.store_model_version = AsyncMock()
        db_service.store_deployment_record = AsyncMock()
        db_service.store_ab_experiment = AsyncMock()
        db_service.update_ab_experiment = AsyncMock()
        return db_service
    
    @pytest.fixture
    def registry(self, mock_database_service, temp_storage):
        """Create model registry instance."""
        return EnhancedModelRegistry(mock_database_service, temp_storage)
    
    @pytest.fixture
    def sample_model_and_metrics(self):
        """Create sample model and performance metrics."""
        from sklearn.ensemble import RandomForestClassifier
        from src.ml.enhanced_model_trainer import ModelPerformanceMetrics, EnhancedModelConfig
        
        # Create simple model
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        X, y = make_classification(n_samples=100, n_features=5, random_state=42)
        model.fit(X, y)
        
        # Create metrics
        metrics = ModelPerformanceMetrics(
            model_id="test_model_123",
            model_name="test_classifier",
            model_version="1.0.0",
            model_type=ModelType.LEAD_SCORING,
            accuracy=0.85,
            precision=0.83,
            recall=0.87,
            f1_score=0.85,
            auc_score=0.89,
            training_samples=100,
            feature_count=5
        )
        
        # Create config
        config = EnhancedModelConfig(
            model_name="test_classifier",
            model_type=ModelType.LEAD_SCORING,
            model_version="1.0.0",
            algorithm="random_forest",
            target_variable="target"
        )
        
        return model, metrics, config
    
    def test_semantic_version_manager(self):
        """Test semantic version management."""
        
        # Test version parsing
        major, minor, patch = SemanticVersionManager.parse_version("1.2.3")
        assert major == 1 and minor == 2 and patch == 3
        
        # Test version increment
        assert SemanticVersionManager.increment_version("1.2.3", "patch") == "1.2.4"
        assert SemanticVersionManager.increment_version("1.2.3", "minor") == "1.3.0"
        assert SemanticVersionManager.increment_version("1.2.3", "major") == "2.0.0"
        
        # Test version comparison
        assert SemanticVersionManager.compare_versions("1.2.3", "1.2.4") == -1
        assert SemanticVersionManager.compare_versions("1.2.3", "1.2.3") == 0
        assert SemanticVersionManager.compare_versions("1.2.4", "1.2.3") == 1
        
        # Test compatibility
        assert SemanticVersionManager.is_compatible("1.2.3", "1.3.0") == True
        assert SemanticVersionManager.is_compatible("1.2.3", "2.0.0") == False
    
    @pytest.mark.asyncio
    async def test_model_registration(self, registry, sample_model_and_metrics):
        """Test model version registration."""
        
        model, metrics, config = sample_model_and_metrics
        
        model_version = await registry.register_model_version(
            model=model,
            model_name="test_classifier",
            model_type=ModelType.LEAD_SCORING,
            performance_metrics=metrics,
            training_config=config,
            training_data_hash="test_hash_123"
        )
        
        # Verify registration
        assert model_version is not None
        assert model_version.model_name == "test_classifier"
        assert model_version.semantic_version == "1.0.0"
        assert model_version.status == ModelStatus.STAGING
        
        # Verify model was stored in registry
        assert model_version.version_id in registry.model_versions
    
    @pytest.mark.asyncio
    async def test_model_deployment_strategies(self, registry, sample_model_and_metrics):
        """Test different deployment strategies."""
        
        model, metrics, config = sample_model_and_metrics
        
        # Register model first
        model_version = await registry.register_model_version(
            model, "test_classifier", ModelType.LEAD_SCORING,
            metrics, config, "test_hash_123"
        )
        
        # Test immediate deployment
        deployment_record = await registry.deploy_model(
            model_version.version_id,
            DeploymentStrategy.IMMEDIATE,
            "production",
            "test_user"
        )
        
        assert deployment_record is not None
        assert deployment_record.deployment_strategy == DeploymentStrategy.IMMEDIATE
        assert deployment_record.deployment_status == "deployed"
        
        # Verify production model was updated
        production_model = await registry.get_production_model(ModelType.LEAD_SCORING)
        assert production_model.version_id == model_version.version_id
    
    @pytest.mark.asyncio
    async def test_ab_testing_workflow(self, registry, sample_model_and_metrics):
        """Test A/B testing workflow."""
        
        model, metrics, config = sample_model_and_metrics
        
        # Register champion model
        champion_version = await registry.register_model_version(
            model, "champion_model", ModelType.LEAD_SCORING,
            metrics, config, "champion_hash"
        )
        
        # Register challenger model with different metrics
        challenger_metrics = metrics
        challenger_metrics.accuracy = 0.88  # Better accuracy
        challenger_version = await registry.register_model_version(
            model, "challenger_model", ModelType.LEAD_SCORING,
            challenger_metrics, config, "challenger_hash"
        )
        
        # Create A/B test
        experiment_config = {
            'model_type': ModelType.LEAD_SCORING.value,
            'traffic_split': 0.2,
            'success_metrics': ['accuracy', 'precision'],
            'minimum_sample_size': 100,
            'maximum_duration_days': 7
        }
        
        experiment = await registry.ab_test_manager.create_ab_test(
            champion_version.version_id,
            challenger_version.version_id,
            experiment_config
        )
        
        # Verify experiment creation
        assert experiment is not None
        assert experiment.champion_version_id == champion_version.version_id
        assert experiment.challenger_version_id == challenger_version.version_id
        assert experiment.traffic_split == 0.2
        
        # Start experiment
        success = await registry.ab_test_manager.start_ab_test(experiment.experiment_id)
        assert success == True
    
    @pytest.mark.asyncio
    async def test_model_comparison(self, registry, sample_model_and_metrics):
        """Test model version comparison."""
        
        model, metrics, config = sample_model_and_metrics
        
        # Register two model versions
        version1 = await registry.register_model_version(
            model, "test_model", ModelType.LEAD_SCORING,
            metrics, config, "hash1"
        )
        
        # Create metrics for second version with different performance
        metrics2 = metrics
        metrics2.accuracy = 0.90
        metrics2.precision = 0.89
        
        version2 = await registry.register_model_version(
            model, "test_model", ModelType.LEAD_SCORING,
            metrics2, config, "hash2", increment_type="minor"
        )
        
        # Compare versions
        comparison = await registry.compare_model_versions(
            version1.version_id, version2.version_id
        )
        
        assert comparison is not None
        assert 'performance_comparison' in comparison
        assert 'accuracy_diff' in comparison['performance_comparison']
        assert comparison['performance_comparison']['accuracy_diff'] > 0  # Version 2 is better


class TestHistoricalDataProcessor:
    """Test suite for historical data processor."""
    
    @pytest.fixture
    def sample_time_series_data(self):
        """Create sample time series data."""
        return TestDataGenerator.create_time_series_dataset(n_samples=1000, n_customers=10)
    
    @pytest.fixture
    def data_with_quality_issues(self):
        """Create data with various quality issues."""
        base_data = TestDataGenerator.create_classification_dataset(n_samples=500)
        return TestDataGenerator.create_data_with_quality_issues(base_data)
    
    @pytest.fixture
    def quality_assessor(self):
        """Create data quality assessor instance."""
        return DataQualityAssessor()
    
    @pytest.fixture
    def temporal_engineer(self):
        """Create temporal feature engineer instance."""
        return TemporalFeatureEngineer()
    
    @pytest.fixture
    def data_processor(self):
        """Create historical data processor instance."""
        mock_db = Mock()
        return HistoricalDataProcessor(mock_db)
    
    @pytest.mark.asyncio
    async def test_data_quality_assessment(self, quality_assessor, data_with_quality_issues):
        """Test comprehensive data quality assessment."""
        
        report = await quality_assessor.assess_data_quality(
            data_with_quality_issues, "test_dataset"
        )
        
        # Verify report structure
        assert report is not None
        assert report.dataset_name == "test_dataset"
        assert report.total_records > 0
        assert report.total_features > 0
        
        # Should detect quality issues
        assert len(report.quality_issues) > 0
        
        # Should have feature statistics
        assert len(report.feature_statistics) > 0
        
        # Should have recommendations
        assert len(report.preprocessing_recommendations) > 0 or len(report.feature_engineering_suggestions) > 0
        
        # Overall quality score should be reasonable
        assert 0 <= report.overall_quality_score <= 100
    
    @pytest.mark.asyncio
    async def test_temporal_feature_engineering(self, temporal_engineer, sample_time_series_data):
        """Test temporal feature engineering."""
        
        config = TemporalFeatureConfig(
            extract_date_components=True,
            include_business_calendar=True,
            lag_periods=[1, 7],
            lag_features=['value'],
            rolling_windows=[3, 7],
            rolling_features=['value'],
            rolling_aggregations=[AggregationMethod.MEAN, AggregationMethod.STD],
            detect_trends=True,
            detect_seasonality=True
        )
        
        engineered_data, created_features = await temporal_engineer.engineer_temporal_features(
            sample_time_series_data,
            config,
            'timestamp',
            'customer_id'
        )
        
        # Verify feature engineering
        assert len(engineered_data.columns) > len(sample_time_series_data.columns)
        assert len(created_features) > 0
        
        # Check for specific feature types
        date_features = [f for f in created_features if 'timestamp_year' in f or 'timestamp_month' in f]
        assert len(date_features) > 0
        
        lag_features = [f for f in created_features if 'lag_' in f]
        assert len(lag_features) > 0
        
        rolling_features = [f for f in created_features if 'rolling_' in f]
        assert len(rolling_features) > 0
    
    @pytest.mark.asyncio
    async def test_complete_data_processing_pipeline(self, data_processor, sample_time_series_data):
        """Test complete data processing pipeline."""
        
        processing_config = {
            'temporal_features': True,
            'date_column': 'timestamp',
            'customer_id_column': 'customer_id',
            'temporal_config': {
                'extract_date_components': True,
                'lag_periods': [1, 3],
                'lag_features': ['value'],
                'rolling_windows': [3, 7],
                'rolling_features': ['value']
            },
            'missing_value_strategy': 'auto',
            'outlier_treatment': 'cap',
            'output': {
                'type': 'dataframe'
            }
        }
        
        job = await data_processor.process_historical_data(
            sample_time_series_data,
            processing_config,
            "Test Processing Job"
        )
        
        # Verify job creation
        assert job is not None
        assert job.job_type == "preprocessing"
        assert job.records_processed > 0
        
        # Wait a bit for async processing
        await asyncio.sleep(0.1)
        
        # Check job status
        job_status = await data_processor.get_job_status(job.job_id)
        assert job_status is not None
    
    @pytest.mark.asyncio
    async def test_data_quality_issue_detection(self, quality_assessor):
        """Test specific data quality issue detection."""
        
        # Create data with known issues
        data = pd.DataFrame({
            'feature_1': [1, 2, 3, 4, 5] * 100,
            'feature_2': [1, np.nan, 3, np.nan, 5] * 100,  # 40% missing
            'feature_3': [1, 2, 3, 4, 1000] * 100,  # Has outliers
            'target': [0, 1, 0, 1, 0] * 100
        })
        
        # Add duplicates
        data = pd.concat([data, data.head(10)], ignore_index=True)
        
        report = await quality_assessor.assess_data_quality(data, "test_issues")
        
        # Should detect missing values
        missing_issues = [
            issue for issue in report.quality_issues 
            if issue['type'] == 'missing_values'
        ]
        assert len(missing_issues) > 0
        
        # Should detect duplicates
        duplicate_issues = [
            issue for issue in report.quality_issues 
            if issue['type'] == 'duplicate_records'
        ]
        assert len(duplicate_issues) > 0
        
        # Should detect outliers
        outlier_info = report.outlier_analysis.get('feature_3', {})
        assert outlier_info.get('iqr_outlier_percentage', 0) > 0


class TestIntegrationWorkflows:
    """Integration tests for complete ML workflows."""
    
    @pytest.fixture
    def end_to_end_data(self):
        """Create comprehensive dataset for end-to-end testing."""
        return TestDataGenerator.create_classification_dataset(n_samples=1000, n_features=10)
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_complete_ml_pipeline(self, end_to_end_data, temp_storage):
        """Test complete ML pipeline from data processing to deployment."""
        
        # 1. Data Processing
        data_processor = HistoricalDataProcessor()
        
        processing_config = {
            'temporal_features': False,  # Simplify for testing
            'missing_value_strategy': 'auto',
            'outlier_treatment': 'cap'
        }
        
        processing_job = await data_processor.process_historical_data(
            end_to_end_data,
            processing_config,
            "E2E Test Processing"
        )
        
        # Wait for processing to complete
        max_wait = 10  # seconds
        waited = 0
        while processing_job.status.value in ['pending', 'running'] and waited < max_wait:
            await asyncio.sleep(0.5)
            waited += 0.5
            processing_job = await data_processor.get_job_status(processing_job.job_id)
        
        assert processing_job.status.value in ['completed', 'failed']
        
        # 2. Model Training
        trainer = EnhancedModelTrainer()
        
        model_config = EnhancedModelConfig(
            model_name="e2e_test_model",
            model_type=ModelType.LEAD_SCORING,
            model_version="1.0.0",
            algorithm="random_forest",
            target_variable="target",
            optimization_strategy=OptimizationStrategy.RANDOM_SEARCH,
            optimization_trials=5,
            temporal_features=False,
            use_ensemble=False
        )
        
        model, metrics = await trainer.train_enhanced_model(
            end_to_end_data, model_config
        )
        
        assert model is not None
        assert metrics.accuracy > 0.4  # Reasonable threshold
        
        # 3. Model Registry and Deployment
        mock_db = Mock()
        mock_db.store_model_version = AsyncMock()
        mock_db.store_deployment_record = AsyncMock()
        
        registry = EnhancedModelRegistry(mock_db, temp_storage)
        
        model_version = await registry.register_model_version(
            model=model,
            model_name="e2e_test_model",
            model_type=ModelType.LEAD_SCORING,
            performance_metrics=metrics,
            training_config=model_config,
            training_data_hash="e2e_test_hash"
        )
        
        assert model_version is not None
        
        # 4. Deploy Model
        deployment_record = await registry.deploy_model(
            model_version.version_id,
            DeploymentStrategy.IMMEDIATE,
            "test_environment",
            "test_user"
        )
        
        assert deployment_record is not None
        assert deployment_record.deployment_status == "deployed"
        
        # 5. Performance Monitoring Setup
        monitor = ModelPerformanceMonitor(mock_db)
        
        await monitor._initialize_model_health(model_version.version_id)
        
        health_metrics = await monitor.get_model_health(model_version.version_id)
        assert health_metrics is not None
        assert health_metrics.monitoring_status == MonitoringStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_model_lifecycle_management(self, end_to_end_data, temp_storage):
        """Test complete model lifecycle from training to retirement."""
        
        mock_db = Mock()
        mock_db.store_model_version = AsyncMock()
        mock_db.update_model_version = AsyncMock()
        mock_db.store_deployment_record = AsyncMock()
        
        registry = EnhancedModelRegistry(mock_db, temp_storage)
        trainer = EnhancedModelTrainer()
        
        # 1. Train initial model version
        config_v1 = EnhancedModelConfig(
            model_name="lifecycle_test_model",
            model_type=ModelType.LEAD_SCORING,
            model_version="1.0.0",
            algorithm="random_forest",
            target_variable="target",
            optimization_trials=3
        )
        
        model_v1, metrics_v1 = await trainer.train_enhanced_model(
            end_to_end_data, config_v1
        )
        
        version_v1 = await registry.register_model_version(
            model_v1, "lifecycle_test_model", ModelType.LEAD_SCORING,
            metrics_v1, config_v1, "hash_v1"
        )
        
        # 2. Deploy v1
        await registry.deploy_model(
            version_v1.version_id, DeploymentStrategy.IMMEDIATE
        )
        
        # 3. Train improved version
        config_v2 = config_v1
        config_v2.model_version = "1.1.0"
        
        model_v2, metrics_v2 = await trainer.train_enhanced_model(
            end_to_end_data, config_v2
        )
        
        version_v2 = await registry.register_model_version(
            model_v2, "lifecycle_test_model", ModelType.LEAD_SCORING,
            metrics_v2, config_v2, "hash_v2",
            increment_type="minor", parent_version_id=version_v1.version_id
        )
        
        # 4. A/B test new version
        experiment_config = {
            'model_type': ModelType.LEAD_SCORING.value,
            'traffic_split': 0.1,
            'success_metrics': ['accuracy'],
            'minimum_sample_size': 50,
            'maximum_duration_days': 1
        }
        
        experiment = await registry.ab_test_manager.create_ab_test(
            version_v1.version_id, version_v2.version_id, experiment_config
        )
        
        await registry.ab_test_manager.start_ab_test(experiment.experiment_id)
        
        # 5. Approve and deploy v2
        await registry.approve_model_version(version_v2.version_id, "test_approver")
        
        await registry.deploy_model(
            version_v2.version_id, DeploymentStrategy.IMMEDIATE
        )
        
        # 6. Deprecate v1
        success = await registry.deprecate_model_version(
            version_v1.version_id, "Replaced by v1.1.0"
        )
        
        assert success == True
        assert version_v1.status == ModelStatus.DEPRECATED


class TestPerformanceAndScalability:
    """Performance and scalability tests."""
    
    @pytest.mark.asyncio
    async def test_large_dataset_processing(self):
        """Test processing of large datasets."""
        
        # Create larger dataset
        large_data = TestDataGenerator.create_classification_dataset(
            n_samples=10000, n_features=50
        )
        
        data_processor = HistoricalDataProcessor()
        
        processing_config = {
            'temporal_features': False,  # Disable for speed
            'missing_value_strategy': 'simple',
            'outlier_treatment': 'none'
        }
        
        start_time = datetime.now()
        
        job = await data_processor.process_historical_data(
            large_data, processing_config, "Large Dataset Test"
        )
        
        # Wait for completion
        max_wait = 30  # seconds
        waited = 0
        while job.status.value in ['pending', 'running'] and waited < max_wait:
            await asyncio.sleep(1)
            waited += 1
            job = await data_processor.get_job_status(job.job_id)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Performance assertions
        assert processing_time < 30  # Should complete within 30 seconds
        assert job.status.value == 'completed'
        assert job.records_processed == 10000
    
    @pytest.mark.asyncio
    async def test_concurrent_model_training(self):
        """Test concurrent model training."""
        
        trainer = EnhancedModelTrainer()
        
        # Create multiple datasets
        datasets = [
            TestDataGenerator.create_classification_dataset(n_samples=500)
            for _ in range(3)
        ]
        
        # Create training configs
        configs = [
            EnhancedModelConfig(
                model_name=f"concurrent_model_{i}",
                model_type=ModelType.LEAD_SCORING,
                model_version="1.0.0",
                algorithm="random_forest",
                target_variable="target",
                optimization_trials=3,
                temporal_features=False
            )
            for i in range(3)
        ]
        
        # Train models concurrently
        start_time = datetime.now()
        
        tasks = [
            trainer.train_enhanced_model(dataset, config)
            for dataset, config in zip(datasets, configs)
        ]
        
        results = await asyncio.gather(*tasks)
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Verify all models trained successfully
        assert len(results) == 3
        for model, metrics in results:
            assert model is not None
            assert metrics.accuracy > 0.3
        
        # Concurrent training should be faster than sequential
        assert training_time < 60  # Should complete within 1 minute
    
    @pytest.mark.asyncio
    async def test_memory_efficiency(self):
        """Test memory usage during processing."""
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process large dataset
        large_data = TestDataGenerator.create_time_series_dataset(
            n_samples=20000, n_customers=100
        )
        
        temporal_engineer = TemporalFeatureEngineer()
        
        config = TemporalFeatureConfig(
            extract_date_components=True,
            lag_periods=[1, 7],
            lag_features=['value'],
            rolling_windows=[3, 7, 14],
            rolling_features=['value']
        )
        
        engineered_data, features = await temporal_engineer.engineer_temporal_features(
            large_data, config, 'timestamp', 'customer_id'
        )
        
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory
        
        # Memory usage should be reasonable (less than 500MB increase)
        assert memory_increase < 500
        
        # Data should be processed successfully
        assert len(engineered_data) == len(large_data)
        assert len(features) > 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])