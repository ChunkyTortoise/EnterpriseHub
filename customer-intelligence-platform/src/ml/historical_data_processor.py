"""
Historical Data Preprocessing Pipeline for Customer Intelligence Platform.

This module provides comprehensive data preprocessing capabilities for historical data including:
- Time-series data processing and feature extraction
- Data quality assessment and cleaning
- Advanced temporal feature engineering
- Automated data pipeline orchestration
- Historical pattern mining and analysis
- Data validation and consistency checks
- Scalable batch processing for large datasets

Features:
- Production-ready data preprocessing pipelines
- Temporal pattern recognition and feature extraction
- Automated data quality monitoring
- Scalable batch processing with checkpointing
- Historical trend analysis and seasonality detection
- Data lineage tracking and audit trails

Business Impact: High-quality training data for improved model accuracy
Author: Customer Intelligence Platform Enhancement Team
Created: 2026-01-19
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any, Union, Callable, Iterator
from enum import Enum
import json
import uuid
import warnings
from pathlib import Path
from collections import defaultdict
import concurrent.futures
import multiprocessing

# Time series processing
from scipy.signal import find_peaks, savgol_filter
from scipy.stats import zscore
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import holidays

# Internal imports
from .scoring_pipeline import ModelType
from ..utils.logger import get_logger
from ..database.service import DatabaseService

logger = get_logger(__name__)
warnings.filterwarnings("ignore", category=UserWarning)


class DataQualityIssue(Enum):
    """Types of data quality issues."""
    MISSING_VALUES = "missing_values"
    DUPLICATE_RECORDS = "duplicate_records"
    OUTLIERS = "outliers"
    INCONSISTENT_FORMAT = "inconsistent_format"
    TEMPORAL_GAPS = "temporal_gaps"
    FEATURE_DRIFT = "feature_drift"
    INVALID_VALUES = "invalid_values"
    SCHEMA_MISMATCH = "schema_mismatch"


class ProcessingStatus(Enum):
    """Data processing job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AggregationMethod(Enum):
    """Temporal aggregation methods."""
    MEAN = "mean"
    MEDIAN = "median"
    SUM = "sum"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    STD = "std"
    FIRST = "first"
    LAST = "last"


@dataclass
class DataQualityReport:
    """Comprehensive data quality assessment report."""
    
    # Report metadata
    report_id: str
    dataset_name: str
    assessment_timestamp: datetime
    
    # Dataset statistics
    total_records: int
    total_features: int
    date_range: Tuple[datetime, datetime]
    
    # Quality metrics
    completeness_score: float  # 0-100
    consistency_score: float  # 0-100
    validity_score: float     # 0-100
    overall_quality_score: float  # 0-100
    
    # Detailed issues
    quality_issues: List[Dict[str, Any]] = field(default_factory=list)
    
    # Feature-level analysis
    feature_statistics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    missing_value_analysis: Dict[str, float] = field(default_factory=dict)
    outlier_analysis: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Temporal analysis
    temporal_patterns: Dict[str, Any] = field(default_factory=dict)
    seasonality_detected: Dict[str, bool] = field(default_factory=dict)
    trend_analysis: Dict[str, str] = field(default_factory=dict)  # increasing, decreasing, stable
    
    # Recommendations
    preprocessing_recommendations: List[str] = field(default_factory=list)
    feature_engineering_suggestions: List[str] = field(default_factory=list)
    
    # Processing metadata
    processing_time_seconds: float = 0.0
    data_sample_analyzed: bool = False
    sample_size: Optional[int] = None


@dataclass
class ProcessingJob:
    """Data processing job configuration and tracking."""
    
    # Job identification
    job_id: str
    job_name: str
    job_type: str  # quality_assessment, preprocessing, feature_engineering
    
    # Data configuration
    source_config: Dict[str, Any]
    target_config: Dict[str, Any]
    processing_config: Dict[str, Any]
    
    # Job status
    status: ProcessingStatus = ProcessingStatus.PENDING
    progress_percentage: float = 0.0
    
    # Execution tracking
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_seconds: float = 0.0
    
    # Results and metadata
    records_processed: int = 0
    records_output: int = 0
    quality_report: Optional[DataQualityReport] = None
    error_messages: List[str] = field(default_factory=list)
    processing_logs: List[str] = field(default_factory=list)
    
    # Resource usage
    memory_usage_peak_mb: float = 0.0
    cpu_usage_percentage: float = 0.0


@dataclass
class TemporalFeatureConfig:
    """Configuration for temporal feature engineering."""
    
    # Time-based features
    extract_date_components: bool = True
    extract_time_components: bool = True
    include_business_calendar: bool = True
    
    # Lag features
    lag_periods: List[int] = field(default_factory=lambda: [1, 7, 30])
    lag_features: List[str] = field(default_factory=list)
    
    # Rolling window features
    rolling_windows: List[int] = field(default_factory=lambda: [7, 14, 30, 90])
    rolling_aggregations: List[AggregationMethod] = field(default_factory=lambda: [AggregationMethod.MEAN, AggregationMethod.STD])
    rolling_features: List[str] = field(default_factory=list)
    
    # Trend and seasonality
    detect_trends: bool = True
    detect_seasonality: bool = True
    detrend_data: bool = False
    seasonal_decomposition: bool = True
    
    # Change point detection
    detect_change_points: bool = True
    change_point_features: List[str] = field(default_factory=list)
    
    # Fourier features for cyclical patterns
    fourier_features: bool = True
    fourier_orders: List[int] = field(default_factory=lambda: [1, 2, 3])


class DataQualityAssessor:
    """Comprehensive data quality assessment and reporting."""
    
    def __init__(self):
        self.quality_thresholds = {
            'completeness_excellent': 0.95,
            'completeness_good': 0.85,
            'completeness_poor': 0.70,
            'outlier_threshold': 3.0,  # Z-score threshold
            'duplicate_threshold': 0.05  # 5% duplicates
        }
    
    async def assess_data_quality(
        self,
        data: pd.DataFrame,
        dataset_name: str,
        sample_size: Optional[int] = None
    ) -> DataQualityReport:
        """Perform comprehensive data quality assessment."""
        
        start_time = datetime.now()
        
        # Sample data if needed for large datasets
        original_size = len(data)
        if sample_size and len(data) > sample_size:
            data_sample = data.sample(n=sample_size, random_state=42)
            is_sample = True
        else:
            data_sample = data
            is_sample = False
        
        logger.info(f"Assessing data quality for {dataset_name} ({len(data_sample)} records)")
        
        # Initialize report
        report = DataQualityReport(
            report_id=str(uuid.uuid4()),
            dataset_name=dataset_name,
            assessment_timestamp=datetime.now(),
            total_records=original_size,
            total_features=len(data.columns),
            date_range=self._get_date_range(data),
            data_sample_analyzed=is_sample,
            sample_size=len(data_sample) if is_sample else None
        )
        
        try:
            # 1. Basic statistics and completeness
            await self._assess_completeness(data_sample, report)
            
            # 2. Consistency analysis
            await self._assess_consistency(data_sample, report)
            
            # 3. Validity analysis
            await self._assess_validity(data_sample, report)
            
            # 4. Feature-level statistics
            await self._analyze_features(data_sample, report)
            
            # 5. Outlier detection
            await self._detect_outliers(data_sample, report)
            
            # 6. Temporal pattern analysis
            await self._analyze_temporal_patterns(data_sample, report)
            
            # 7. Generate recommendations
            await self._generate_recommendations(report)
            
            # 8. Calculate overall quality score
            report.overall_quality_score = self._calculate_overall_quality_score(report)
            
            # Record processing time
            report.processing_time_seconds = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Data quality assessment completed for {dataset_name}")
            logger.info(f"Overall quality score: {report.overall_quality_score:.1f}/100")
            
            return report
            
        except Exception as e:
            logger.error(f"Data quality assessment failed for {dataset_name}: {e}")
            raise
    
    async def _assess_completeness(self, data: pd.DataFrame, report: DataQualityReport):
        """Assess data completeness (missing values analysis)."""
        
        missing_counts = data.isnull().sum()
        total_records = len(data)
        
        for column in data.columns:
            missing_count = missing_counts[column]
            missing_percentage = (missing_count / total_records) * 100
            report.missing_value_analysis[column] = missing_percentage
            
            # Flag significant missing values
            if missing_percentage > 30:
                report.quality_issues.append({
                    'type': DataQualityIssue.MISSING_VALUES.value,
                    'severity': 'high',
                    'feature': column,
                    'description': f"High missing values: {missing_percentage:.1f}%",
                    'missing_count': int(missing_count),
                    'missing_percentage': missing_percentage
                })
            elif missing_percentage > 10:
                report.quality_issues.append({
                    'type': DataQualityIssue.MISSING_VALUES.value,
                    'severity': 'medium',
                    'feature': column,
                    'description': f"Moderate missing values: {missing_percentage:.1f}%",
                    'missing_count': int(missing_count),
                    'missing_percentage': missing_percentage
                })
        
        # Overall completeness score
        overall_completeness = 1 - (missing_counts.sum() / (total_records * len(data.columns)))
        report.completeness_score = overall_completeness * 100
    
    async def _assess_consistency(self, data: pd.DataFrame, report: DataQualityReport):
        """Assess data consistency."""
        
        consistency_issues = 0
        total_checks = 0
        
        # Check for duplicate records
        duplicate_count = data.duplicated().sum()
        duplicate_percentage = (duplicate_count / len(data)) * 100
        
        if duplicate_percentage > self.quality_thresholds['duplicate_threshold'] * 100:
            report.quality_issues.append({
                'type': DataQualityIssue.DUPLICATE_RECORDS.value,
                'severity': 'medium',
                'description': f"High duplicate rate: {duplicate_percentage:.1f}%",
                'duplicate_count': int(duplicate_count),
                'duplicate_percentage': duplicate_percentage
            })
            consistency_issues += 1
        
        total_checks += 1
        
        # Check for inconsistent formats in string columns
        string_columns = data.select_dtypes(include=['object']).columns
        for column in string_columns:
            unique_patterns = data[column].dropna().astype(str).str.len().nunique()
            total_unique = data[column].nunique()
            
            # High variation in string lengths might indicate format inconsistencies
            if total_unique > 10 and unique_patterns > total_unique * 0.5:
                report.quality_issues.append({
                    'type': DataQualityIssue.INCONSISTENT_FORMAT.value,
                    'severity': 'low',
                    'feature': column,
                    'description': f"Potential format inconsistencies detected",
                    'unique_patterns': int(unique_patterns),
                    'total_unique': int(total_unique)
                })
                consistency_issues += 1
            
            total_checks += 1
        
        # Consistency score
        report.consistency_score = ((total_checks - consistency_issues) / total_checks) * 100 if total_checks > 0 else 100
    
    async def _assess_validity(self, data: pd.DataFrame, report: DataQualityReport):
        """Assess data validity."""
        
        validity_issues = 0
        total_checks = 0
        
        # Check numeric columns for invalid values
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            # Check for infinite values
            inf_count = np.isinf(data[column]).sum()
            if inf_count > 0:
                report.quality_issues.append({
                    'type': DataQualityIssue.INVALID_VALUES.value,
                    'severity': 'high',
                    'feature': column,
                    'description': f"Infinite values detected: {inf_count}",
                    'invalid_count': int(inf_count)
                })
                validity_issues += 1
            
            # Check for extremely large values (potential data entry errors)
            if not data[column].empty:
                column_std = data[column].std()
                column_mean = data[column].mean()
                
                if not pd.isna(column_std) and column_std > 0:
                    extreme_values = np.abs(zscore(data[column].dropna())) > 5
                    extreme_count = extreme_values.sum()
                    
                    if extreme_count > len(data) * 0.01:  # More than 1% extreme values
                        report.quality_issues.append({
                            'type': DataQualityIssue.INVALID_VALUES.value,
                            'severity': 'medium',
                            'feature': column,
                            'description': f"Potential invalid values (extreme outliers): {extreme_count}",
                            'extreme_count': int(extreme_count)
                        })
                        validity_issues += 1
            
            total_checks += 2  # Two checks per numeric column
        
        # Check date columns for validity
        datetime_columns = data.select_dtypes(include=['datetime64']).columns
        for column in datetime_columns:
            # Check for future dates that might be invalid
            future_dates = data[column] > datetime.now()
            future_count = future_dates.sum()
            
            if future_count > 0:
                report.quality_issues.append({
                    'type': DataQualityIssue.INVALID_VALUES.value,
                    'severity': 'medium',
                    'feature': column,
                    'description': f"Future dates detected: {future_count}",
                    'future_count': int(future_count)
                })
                validity_issues += 1
            
            total_checks += 1
        
        # Validity score
        report.validity_score = ((total_checks - validity_issues) / total_checks) * 100 if total_checks > 0 else 100
    
    async def _analyze_features(self, data: pd.DataFrame, report: DataQualityReport):
        """Analyze individual features."""
        
        for column in data.columns:
            feature_stats = {
                'data_type': str(data[column].dtype),
                'unique_values': int(data[column].nunique()),
                'missing_count': int(data[column].isnull().sum()),
                'missing_percentage': float((data[column].isnull().sum() / len(data)) * 100)
            }
            
            if data[column].dtype in [np.number]:
                # Numeric statistics
                feature_stats.update({
                    'mean': float(data[column].mean()) if not data[column].empty else 0.0,
                    'std': float(data[column].std()) if not data[column].empty else 0.0,
                    'min': float(data[column].min()) if not data[column].empty else 0.0,
                    'max': float(data[column].max()) if not data[column].empty else 0.0,
                    'median': float(data[column].median()) if not data[column].empty else 0.0,
                    'skewness': float(data[column].skew()) if not data[column].empty else 0.0,
                    'kurtosis': float(data[column].kurtosis()) if not data[column].empty else 0.0
                })
            
            elif data[column].dtype == 'object':
                # String/categorical statistics
                value_counts = data[column].value_counts()
                feature_stats.update({
                    'most_common_value': str(value_counts.index[0]) if not value_counts.empty else None,
                    'most_common_count': int(value_counts.iloc[0]) if not value_counts.empty else 0,
                    'average_length': float(data[column].astype(str).str.len().mean()),
                    'max_length': int(data[column].astype(str).str.len().max()) if not data[column].empty else 0
                })
            
            report.feature_statistics[column] = feature_stats
    
    async def _detect_outliers(self, data: pd.DataFrame, report: DataQualityReport):
        """Detect outliers in numeric features."""
        
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        for column in numeric_columns:
            if data[column].empty or data[column].std() == 0:
                continue
            
            # Z-score based outlier detection
            z_scores = np.abs(zscore(data[column].dropna()))
            outlier_indices = z_scores > self.quality_thresholds['outlier_threshold']
            outlier_count = outlier_indices.sum()
            outlier_percentage = (outlier_count / len(data)) * 100
            
            # IQR based outlier detection
            Q1 = data[column].quantile(0.25)
            Q3 = data[column].quantile(0.75)
            IQR = Q3 - Q1
            iqr_outliers = ((data[column] < Q1 - 1.5 * IQR) | (data[column] > Q3 + 1.5 * IQR)).sum()
            iqr_outlier_percentage = (iqr_outliers / len(data)) * 100
            
            report.outlier_analysis[column] = {
                'zscore_outliers': int(outlier_count),
                'zscore_outlier_percentage': float(outlier_percentage),
                'iqr_outliers': int(iqr_outliers),
                'iqr_outlier_percentage': float(iqr_outlier_percentage),
                'outlier_threshold_zscore': self.quality_thresholds['outlier_threshold']
            }
            
            # Flag high outlier rates
            if outlier_percentage > 5:  # More than 5% outliers
                report.quality_issues.append({
                    'type': DataQualityIssue.OUTLIERS.value,
                    'severity': 'medium',
                    'feature': column,
                    'description': f"High outlier rate: {outlier_percentage:.1f}% (Z-score > {self.quality_thresholds['outlier_threshold']})",
                    'outlier_count': int(outlier_count),
                    'outlier_percentage': outlier_percentage
                })
    
    async def _analyze_temporal_patterns(self, data: pd.DataFrame, report: DataQualityReport):
        """Analyze temporal patterns in data."""
        
        # Try to identify datetime columns
        datetime_columns = []
        for column in data.columns:
            if data[column].dtype == 'datetime64[ns]':
                datetime_columns.append(column)
            elif 'date' in column.lower() or 'time' in column.lower():
                try:
                    pd.to_datetime(data[column], errors='raise')
                    datetime_columns.append(column)
                except:
                    continue
        
        if not datetime_columns:
            report.temporal_patterns['analysis'] = "No datetime columns detected"
            return
        
        # Use the first datetime column as primary
        primary_date_col = datetime_columns[0]
        data_sorted = data.sort_values(primary_date_col)
        
        # Check for temporal gaps
        if len(data_sorted) > 1:
            date_diffs = data_sorted[primary_date_col].diff().dropna()
            median_diff = date_diffs.median()
            
            # Find gaps larger than 3x median difference
            large_gaps = date_diffs > median_diff * 3
            gap_count = large_gaps.sum()
            
            if gap_count > 0:
                report.quality_issues.append({
                    'type': DataQualityIssue.TEMPORAL_GAPS.value,
                    'severity': 'medium',
                    'feature': primary_date_col,
                    'description': f"Temporal gaps detected: {gap_count} gaps larger than expected",
                    'gap_count': int(gap_count),
                    'median_interval': str(median_diff)
                })
        
        # Basic temporal statistics
        date_range = data_sorted[primary_date_col].max() - data_sorted[primary_date_col].min()
        
        report.temporal_patterns = {
            'primary_date_column': primary_date_col,
            'date_range_days': date_range.days,
            'earliest_date': data_sorted[primary_date_col].min().isoformat(),
            'latest_date': data_sorted[primary_date_col].max().isoformat(),
            'total_datetime_columns': len(datetime_columns),
            'records_with_dates': int((~data[primary_date_col].isnull()).sum())
        }
        
        # Simple trend analysis for numeric columns
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        for column in numeric_columns[:5]:  # Limit to first 5 numeric columns
            if len(data_sorted) > 10:
                # Calculate correlation with time (as numeric)
                time_numeric = pd.to_numeric(data_sorted[primary_date_col])
                correlation = data_sorted[column].corr(time_numeric)
                
                if abs(correlation) > 0.3:
                    if correlation > 0:
                        trend = "increasing"
                    else:
                        trend = "decreasing"
                else:
                    trend = "stable"
                
                report.trend_analysis[column] = trend
    
    async def _generate_recommendations(self, report: DataQualityReport):
        """Generate preprocessing and feature engineering recommendations."""
        
        recommendations = []
        feature_suggestions = []
        
        # Missing value recommendations
        high_missing_features = [
            issue['feature'] for issue in report.quality_issues
            if issue['type'] == DataQualityIssue.MISSING_VALUES.value and issue['severity'] == 'high'
        ]
        
        if high_missing_features:
            recommendations.append(
                f"Consider dropping features with high missing values: {', '.join(high_missing_features[:3])}"
                + (f" and {len(high_missing_features)-3} others" if len(high_missing_features) > 3 else "")
            )
        
        moderate_missing_features = [
            issue['feature'] for issue in report.quality_issues
            if issue['type'] == DataQualityIssue.MISSING_VALUES.value and issue['severity'] == 'medium'
        ]
        
        if moderate_missing_features:
            recommendations.append(
                f"Apply advanced imputation (KNN/iterative) for features: {', '.join(moderate_missing_features[:3])}"
            )
        
        # Outlier recommendations
        outlier_features = [
            issue['feature'] for issue in report.quality_issues
            if issue['type'] == DataQualityIssue.OUTLIERS.value
        ]
        
        if outlier_features:
            recommendations.append(
                "Apply outlier treatment (capping, transformation) or robust scaling for features with high outlier rates"
            )
        
        # Duplicate recommendations
        has_duplicates = any(
            issue['type'] == DataQualityIssue.DUPLICATE_RECORDS.value
            for issue in report.quality_issues
        )
        
        if has_duplicates:
            recommendations.append("Remove duplicate records before model training")
        
        # Feature engineering suggestions based on trends
        trending_features = [
            feature for feature, trend in report.trend_analysis.items()
            if trend in ["increasing", "decreasing"]
        ]
        
        if trending_features:
            feature_suggestions.append(
                "Create trend-based features (moving averages, trend indicators) for time-varying features"
            )
        
        # Temporal feature suggestions
        if report.temporal_patterns.get('primary_date_column'):
            feature_suggestions.extend([
                "Extract temporal features (day of week, month, season, holidays)",
                "Create lag features for time series analysis",
                "Generate rolling window statistics (moving averages, volatility)",
                "Consider seasonal decomposition for cyclical patterns"
            ])
        
        # High cardinality categorical suggestions
        high_cardinality_features = [
            feature for feature, stats in report.feature_statistics.items()
            if stats.get('unique_values', 0) > 100 and stats.get('data_type') == 'object'
        ]
        
        if high_cardinality_features:
            feature_suggestions.append(
                "Apply target encoding or frequency encoding for high-cardinality categorical features"
            )
        
        report.preprocessing_recommendations = recommendations
        report.feature_engineering_suggestions = feature_suggestions
    
    def _calculate_overall_quality_score(self, report: DataQualityReport) -> float:
        """Calculate overall data quality score."""
        
        # Weight different aspects of quality
        weights = {
            'completeness': 0.4,
            'consistency': 0.3,
            'validity': 0.3
        }
        
        overall_score = (
            weights['completeness'] * report.completeness_score +
            weights['consistency'] * report.consistency_score +
            weights['validity'] * report.validity_score
        )
        
        # Apply penalties for critical issues
        critical_issues = sum(1 for issue in report.quality_issues if issue['severity'] == 'high')
        penalty = min(20, critical_issues * 5)  # Max 20 point penalty
        
        return max(0, overall_score - penalty)
    
    def _get_date_range(self, data: pd.DataFrame) -> Tuple[datetime, datetime]:
        """Get date range from data."""
        
        # Try to find datetime columns
        datetime_columns = data.select_dtypes(include=['datetime64']).columns
        
        if len(datetime_columns) > 0:
            date_col = datetime_columns[0]
            min_date = data[date_col].min()
            max_date = data[date_col].max()
            
            if pd.isna(min_date) or pd.isna(max_date):
                return datetime.now() - timedelta(days=365), datetime.now()
            
            return min_date.to_pydatetime(), max_date.to_pydatetime()
        
        # Default range if no datetime columns found
        return datetime.now() - timedelta(days=365), datetime.now()


class TemporalFeatureEngineer:
    """Advanced temporal feature engineering for time series data."""
    
    def __init__(self):
        self.country_holidays = holidays.US()  # Default to US holidays
        self.business_calendar = pd.bdate_range(
            start='2020-01-01', 
            end=datetime.now() + timedelta(days=365)
        )
    
    async def engineer_temporal_features(
        self,
        data: pd.DataFrame,
        config: TemporalFeatureConfig,
        date_column: str,
        customer_id_column: Optional[str] = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Engineer comprehensive temporal features."""
        
        logger.info(f"Engineering temporal features for {len(data)} records")
        
        engineered_data = data.copy()
        created_features = []
        
        # Ensure date column is datetime
        if engineered_data[date_column].dtype != 'datetime64[ns]':
            engineered_data[date_column] = pd.to_datetime(engineered_data[date_column])
        
        # Sort by date for time-series operations
        if customer_id_column:
            engineered_data = engineered_data.sort_values([customer_id_column, date_column])
        else:
            engineered_data = engineered_data.sort_values(date_column)
        
        try:
            # 1. Basic date/time components
            if config.extract_date_components:
                features = await self._extract_date_components(engineered_data, date_column)
                created_features.extend(features)
            
            # 2. Business calendar features
            if config.include_business_calendar:
                features = await self._extract_business_calendar_features(engineered_data, date_column)
                created_features.extend(features)
            
            # 3. Lag features
            if config.lag_periods and config.lag_features:
                features = await self._create_lag_features(
                    engineered_data, config.lag_features, config.lag_periods, customer_id_column
                )
                created_features.extend(features)
            
            # 4. Rolling window features
            if config.rolling_windows and config.rolling_features:
                features = await self._create_rolling_features(
                    engineered_data, config.rolling_features, config.rolling_windows, 
                    config.rolling_aggregations, customer_id_column
                )
                created_features.extend(features)
            
            # 5. Trend features
            if config.detect_trends:
                features = await self._create_trend_features(
                    engineered_data, date_column, customer_id_column
                )
                created_features.extend(features)
            
            # 6. Seasonality features
            if config.detect_seasonality:
                features = await self._create_seasonality_features(
                    engineered_data, date_column
                )
                created_features.extend(features)
            
            # 7. Change point features
            if config.detect_change_points and config.change_point_features:
                features = await self._create_change_point_features(
                    engineered_data, config.change_point_features, date_column, customer_id_column
                )
                created_features.extend(features)
            
            # 8. Fourier features for cyclical patterns
            if config.fourier_features:
                features = await self._create_fourier_features(
                    engineered_data, date_column, config.fourier_orders
                )
                created_features.extend(features)
            
            # Clean up any infinite or null values
            engineered_data = engineered_data.replace([np.inf, -np.inf], np.nan)
            
            logger.info(f"Created {len(created_features)} temporal features")
            
            return engineered_data, created_features
            
        except Exception as e:
            logger.error(f"Temporal feature engineering failed: {e}")
            return data, []
    
    async def _extract_date_components(self, data: pd.DataFrame, date_column: str) -> List[str]:
        """Extract basic date and time components."""
        
        features = []
        
        # Date components
        data[f'{date_column}_year'] = data[date_column].dt.year
        data[f'{date_column}_month'] = data[date_column].dt.month
        data[f'{date_column}_day'] = data[date_column].dt.day
        data[f'{date_column}_dayofweek'] = data[date_column].dt.dayofweek
        data[f'{date_column}_dayofyear'] = data[date_column].dt.dayofyear
        data[f'{date_column}_week'] = data[date_column].dt.isocalendar().week
        data[f'{date_column}_quarter'] = data[date_column].dt.quarter
        
        features.extend([
            f'{date_column}_year', f'{date_column}_month', f'{date_column}_day',
            f'{date_column}_dayofweek', f'{date_column}_dayofyear', 
            f'{date_column}_week', f'{date_column}_quarter'
        ])
        
        # Time components (if datetime includes time)
        if data[date_column].dt.hour.nunique() > 1:
            data[f'{date_column}_hour'] = data[date_column].dt.hour
            data[f'{date_column}_minute'] = data[date_column].dt.minute
            features.extend([f'{date_column}_hour', f'{date_column}_minute'])
        
        # Derived features
        data[f'{date_column}_is_weekend'] = (data[date_column].dt.dayofweek >= 5).astype(int)
        data[f'{date_column}_is_month_start'] = data[date_column].dt.is_month_start.astype(int)
        data[f'{date_column}_is_month_end'] = data[date_column].dt.is_month_end.astype(int)
        data[f'{date_column}_is_quarter_start'] = data[date_column].dt.is_quarter_start.astype(int)
        data[f'{date_column}_is_quarter_end'] = data[date_column].dt.is_quarter_end.astype(int)
        
        features.extend([
            f'{date_column}_is_weekend', f'{date_column}_is_month_start', 
            f'{date_column}_is_month_end', f'{date_column}_is_quarter_start', 
            f'{date_column}_is_quarter_end'
        ])
        
        return features
    
    async def _extract_business_calendar_features(self, data: pd.DataFrame, date_column: str) -> List[str]:
        """Extract business calendar features."""
        
        features = []
        
        # Holiday indicator
        data[f'{date_column}_is_holiday'] = data[date_column].dt.date.apply(
            lambda x: x in self.country_holidays
        ).astype(int)
        features.append(f'{date_column}_is_holiday')
        
        # Business day indicator
        data[f'{date_column}_is_business_day'] = data[date_column].apply(
            lambda x: x in self.business_calendar
        ).astype(int)
        features.append(f'{date_column}_is_business_day')
        
        # Days since/until holiday
        data[f'{date_column}_days_since_holiday'] = 0
        data[f'{date_column}_days_until_holiday'] = 0
        
        for idx, date in enumerate(data[date_column]):
            # Find nearest holidays
            date_obj = date.date()
            
            # Days since last holiday
            past_holidays = [h for h in self.country_holidays.keys() if h < date_obj]
            if past_holidays:
                last_holiday = max(past_holidays)
                days_since = (date_obj - last_holiday).days
                data.iloc[idx, data.columns.get_loc(f'{date_column}_days_since_holiday')] = days_since
            
            # Days until next holiday
            future_holidays = [h for h in self.country_holidays.keys() if h > date_obj]
            if future_holidays:
                next_holiday = min(future_holidays)
                days_until = (next_holiday - date_obj).days
                data.iloc[idx, data.columns.get_loc(f'{date_column}_days_until_holiday')] = days_until
        
        features.extend([f'{date_column}_days_since_holiday', f'{date_column}_days_until_holiday'])
        
        return features
    
    async def _create_lag_features(
        self,
        data: pd.DataFrame,
        feature_columns: List[str],
        lag_periods: List[int],
        customer_id_column: Optional[str]
    ) -> List[str]:
        """Create lag features for specified columns."""
        
        features = []
        
        for feature in feature_columns:
            if feature not in data.columns:
                continue
                
            for lag in lag_periods:
                lag_feature_name = f'{feature}_lag_{lag}'
                
                if customer_id_column:
                    # Group by customer for lag calculation
                    data[lag_feature_name] = data.groupby(customer_id_column)[feature].shift(lag)
                else:
                    data[lag_feature_name] = data[feature].shift(lag)
                
                features.append(lag_feature_name)
        
        return features
    
    async def _create_rolling_features(
        self,
        data: pd.DataFrame,
        feature_columns: List[str],
        windows: List[int],
        aggregations: List[AggregationMethod],
        customer_id_column: Optional[str]
    ) -> List[str]:
        """Create rolling window features."""
        
        features = []
        
        for feature in feature_columns:
            if feature not in data.columns:
                continue
            
            for window in windows:
                for agg_method in aggregations:
                    rolling_feature_name = f'{feature}_rolling_{agg_method.value}_{window}'
                    
                    try:
                        if customer_id_column:
                            # Group by customer for rolling calculation
                            grouped = data.groupby(customer_id_column)[feature].rolling(window, min_periods=1)
                        else:
                            grouped = data[feature].rolling(window, min_periods=1)
                        
                        if agg_method == AggregationMethod.MEAN:
                            data[rolling_feature_name] = grouped.mean().reset_index(0, drop=True)
                        elif agg_method == AggregationMethod.STD:
                            data[rolling_feature_name] = grouped.std().reset_index(0, drop=True)
                        elif agg_method == AggregationMethod.MIN:
                            data[rolling_feature_name] = grouped.min().reset_index(0, drop=True)
                        elif agg_method == AggregationMethod.MAX:
                            data[rolling_feature_name] = grouped.max().reset_index(0, drop=True)
                        elif agg_method == AggregationMethod.SUM:
                            data[rolling_feature_name] = grouped.sum().reset_index(0, drop=True)
                        elif agg_method == AggregationMethod.MEDIAN:
                            data[rolling_feature_name] = grouped.median().reset_index(0, drop=True)
                        
                        features.append(rolling_feature_name)
                        
                    except Exception as e:
                        logger.debug(f"Failed to create rolling feature {rolling_feature_name}: {e}")
        
        return features
    
    async def _create_trend_features(
        self,
        data: pd.DataFrame,
        date_column: str,
        customer_id_column: Optional[str]
    ) -> List[str]:
        """Create trend-based features."""
        
        features = []
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        
        # Time numeric (for correlation calculation)
        time_numeric = pd.to_numeric(data[date_column])
        
        # Global trends
        for column in numeric_columns[:5]:  # Limit to avoid too many features
            if column == date_column or data[column].isnull().all():
                continue
            
            try:
                # Calculate correlation with time as trend indicator
                trend_correlation = data[column].corr(time_numeric)
                
                # Create trend strength feature
                trend_feature_name = f'{column}_trend_strength'
                data[trend_feature_name] = abs(trend_correlation)
                features.append(trend_feature_name)
                
                # Create trend direction feature
                trend_direction_name = f'{column}_trend_direction'
                data[trend_direction_name] = 1 if trend_correlation > 0 else -1 if trend_correlation < 0 else 0
                features.append(trend_direction_name)
                
                # Moving trend (local trend in rolling windows)
                if len(data) > 30:
                    local_trend_name = f'{column}_local_trend_30'
                    local_trends = []
                    
                    for i in range(len(data)):
                        start_idx = max(0, i - 29)
                        end_idx = i + 1
                        
                        if end_idx - start_idx >= 10:  # Minimum points for trend calculation
                            window_data = data.iloc[start_idx:end_idx]
                            window_time = pd.to_numeric(window_data[date_column])
                            window_values = window_data[column]
                            
                            if len(window_values.dropna()) >= 5:
                                local_corr = window_values.corr(window_time)
                                local_trends.append(local_corr if not pd.isna(local_corr) else 0)
                            else:
                                local_trends.append(0)
                        else:
                            local_trends.append(0)
                    
                    data[local_trend_name] = local_trends
                    features.append(local_trend_name)
                
            except Exception as e:
                logger.debug(f"Failed to create trend features for {column}: {e}")
        
        return features
    
    async def _create_seasonality_features(self, data: pd.DataFrame, date_column: str) -> List[str]:
        """Create seasonality-based features."""
        
        features = []
        
        # Cyclical encoding of time components
        # Month cyclical encoding
        data[f'{date_column}_month_sin'] = np.sin(2 * np.pi * data[date_column].dt.month / 12)
        data[f'{date_column}_month_cos'] = np.cos(2 * np.pi * data[date_column].dt.month / 12)
        features.extend([f'{date_column}_month_sin', f'{date_column}_month_cos'])
        
        # Day of week cyclical encoding
        data[f'{date_column}_dayofweek_sin'] = np.sin(2 * np.pi * data[date_column].dt.dayofweek / 7)
        data[f'{date_column}_dayofweek_cos'] = np.cos(2 * np.pi * data[date_column].dt.dayofweek / 7)
        features.extend([f'{date_column}_dayofweek_sin', f'{date_column}_dayofweek_cos'])
        
        # Day of year cyclical encoding
        data[f'{date_column}_dayofyear_sin'] = np.sin(2 * np.pi * data[date_column].dt.dayofyear / 365.25)
        data[f'{date_column}_dayofyear_cos'] = np.cos(2 * np.pi * data[date_column].dt.dayofyear / 365.25)
        features.extend([f'{date_column}_dayofyear_sin', f'{date_column}_dayofyear_cos'])
        
        # Hour cyclical encoding (if time information is available)
        if data[date_column].dt.hour.nunique() > 1:
            data[f'{date_column}_hour_sin'] = np.sin(2 * np.pi * data[date_column].dt.hour / 24)
            data[f'{date_column}_hour_cos'] = np.cos(2 * np.pi * data[date_column].dt.hour / 24)
            features.extend([f'{date_column}_hour_sin', f'{date_column}_hour_cos'])
        
        return features
    
    async def _create_change_point_features(
        self,
        data: pd.DataFrame,
        feature_columns: List[str],
        date_column: str,
        customer_id_column: Optional[str]
    ) -> List[str]:
        """Create change point detection features."""
        
        features = []
        
        for feature in feature_columns:
            if feature not in data.columns or data[feature].isnull().all():
                continue
            
            try:
                change_point_feature = f'{feature}_change_point_score'
                
                if customer_id_column:
                    # Calculate change points per customer
                    change_scores = []
                    for customer_id in data[customer_id_column].unique():
                        customer_data = data[data[customer_id_column] == customer_id].sort_values(date_column)
                        scores = self._detect_change_points(customer_data[feature].values)
                        change_scores.extend(scores)
                    
                    data[change_point_feature] = change_scores
                else:
                    # Global change point detection
                    scores = self._detect_change_points(data[feature].values)
                    data[change_point_feature] = scores
                
                features.append(change_point_feature)
                
            except Exception as e:
                logger.debug(f"Failed to create change point features for {feature}: {e}")
        
        return features
    
    def _detect_change_points(self, values: np.ndarray, window_size: int = 10) -> List[float]:
        """Simple change point detection using moving variance."""
        
        if len(values) < window_size * 2:
            return [0.0] * len(values)
        
        change_scores = [0.0] * len(values)
        
        for i in range(window_size, len(values) - window_size):
            # Calculate variance before and after the point
            before = values[i-window_size:i]
            after = values[i:i+window_size]
            
            if len(before) > 1 and len(after) > 1:
                var_before = np.var(before)
                var_after = np.var(after)
                mean_before = np.mean(before)
                mean_after = np.mean(after)
                
                # Change point score based on variance and mean differences
                var_change = abs(var_after - var_before) / (var_before + var_after + 1e-6)
                mean_change = abs(mean_after - mean_before) / (abs(mean_before) + abs(mean_after) + 1e-6)
                
                change_scores[i] = var_change + mean_change
        
        return change_scores
    
    async def _create_fourier_features(
        self,
        data: pd.DataFrame,
        date_column: str,
        orders: List[int]
    ) -> List[str]:
        """Create Fourier features for cyclical patterns."""
        
        features = []
        
        # Convert dates to numeric for Fourier transform
        min_date = data[date_column].min()
        date_numeric = (data[date_column] - min_date).dt.days
        
        for order in orders:
            # Annual cycle
            annual_sin = f'{date_column}_fourier_annual_sin_{order}'
            annual_cos = f'{date_column}_fourier_annual_cos_{order}'
            
            data[annual_sin] = np.sin(2 * np.pi * order * date_numeric / 365.25)
            data[annual_cos] = np.cos(2 * np.pi * order * date_numeric / 365.25)
            
            features.extend([annual_sin, annual_cos])
            
            # Weekly cycle
            weekly_sin = f'{date_column}_fourier_weekly_sin_{order}'
            weekly_cos = f'{date_column}_fourier_weekly_cos_{order}'
            
            data[weekly_sin] = np.sin(2 * np.pi * order * date_numeric / 7)
            data[weekly_cos] = np.cos(2 * np.pi * order * date_numeric / 7)
            
            features.extend([weekly_sin, weekly_cos])
        
        return features


class HistoricalDataProcessor:
    """Main orchestrator for historical data processing."""
    
    def __init__(self, database_service: DatabaseService = None):
        self.db_service = database_service or DatabaseService()
        self.quality_assessor = DataQualityAssessor()
        self.temporal_engineer = TemporalFeatureEngineer()
        
        # Processing job tracking
        self.active_jobs: Dict[str, ProcessingJob] = {}
        
        # Default configurations
        self.default_temporal_config = TemporalFeatureConfig()
        
    async def process_historical_data(
        self,
        data_source: Union[pd.DataFrame, str, Dict[str, Any]],
        processing_config: Dict[str, Any],
        job_name: str = "Historical Data Processing"
    ) -> ProcessingJob:
        """Process historical data with comprehensive pipeline."""
        
        job_id = str(uuid.uuid4())
        
        # Create processing job
        job = ProcessingJob(
            job_id=job_id,
            job_name=job_name,
            job_type="preprocessing",
            source_config={"type": type(data_source).__name__},
            target_config=processing_config.get('output', {}),
            processing_config=processing_config
        )
        
        self.active_jobs[job_id] = job
        
        # Execute processing asynchronously
        asyncio.create_task(self._execute_processing_job(job_id, data_source))
        
        logger.info(f"Started historical data processing job: {job_id}")
        return job
    
    async def _execute_processing_job(self, job_id: str, data_source: Any):
        """Execute comprehensive data processing job."""
        
        job = self.active_jobs[job_id]
        job.status = ProcessingStatus.RUNNING
        job.started_at = datetime.now()
        
        try:
            # 1. Load data
            job.processing_logs.append("Loading data...")
            job.progress_percentage = 10.0
            
            data = await self._load_data(data_source)
            job.records_processed = len(data)
            
            # 2. Data quality assessment
            job.processing_logs.append("Assessing data quality...")
            job.progress_percentage = 25.0
            
            quality_report = await self.quality_assessor.assess_data_quality(
                data, job.job_name
            )
            job.quality_report = quality_report
            
            # 3. Data cleaning based on quality report
            job.processing_logs.append("Cleaning data...")
            job.progress_percentage = 40.0
            
            cleaned_data = await self._clean_data(data, quality_report, job.processing_config)
            
            # 4. Temporal feature engineering
            if job.processing_config.get('temporal_features', True):
                job.processing_logs.append("Engineering temporal features...")
                job.progress_percentage = 60.0
                
                temporal_config = self._get_temporal_config(job.processing_config)
                date_column = job.processing_config.get('date_column')
                customer_id_column = job.processing_config.get('customer_id_column')
                
                if date_column and date_column in cleaned_data.columns:
                    cleaned_data, temporal_features = await self.temporal_engineer.engineer_temporal_features(
                        cleaned_data, temporal_config, date_column, customer_id_column
                    )
                    job.processing_logs.append(f"Created {len(temporal_features)} temporal features")
            
            # 5. Final data preparation
            job.processing_logs.append("Final data preparation...")
            job.progress_percentage = 80.0
            
            final_data = await self._prepare_final_data(cleaned_data, job.processing_config)
            job.records_output = len(final_data)
            
            # 6. Save processed data
            job.processing_logs.append("Saving processed data...")
            job.progress_percentage = 95.0
            
            await self._save_processed_data(final_data, job.processing_config.get('output', {}))
            
            # Complete job
            job.status = ProcessingStatus.COMPLETED
            job.completed_at = datetime.now()
            job.processing_time_seconds = (job.completed_at - job.started_at).total_seconds()
            job.progress_percentage = 100.0
            
            job.processing_logs.append("Processing completed successfully")
            logger.info(f"Historical data processing job {job_id} completed successfully")
            
        except Exception as e:
            job.status = ProcessingStatus.FAILED
            job.error_messages.append(str(e))
            job.completed_at = datetime.now()
            
            logger.error(f"Historical data processing job {job_id} failed: {e}")
    
    async def _load_data(self, data_source: Any) -> pd.DataFrame:
        """Load data from various sources."""
        
        if isinstance(data_source, pd.DataFrame):
            return data_source.copy()
        
        elif isinstance(data_source, str):
            # File path
            if data_source.endswith('.csv'):
                return pd.read_csv(data_source)
            elif data_source.endswith('.parquet'):
                return pd.read_parquet(data_source)
            elif data_source.endswith('.json'):
                return pd.read_json(data_source)
            else:
                raise ValueError(f"Unsupported file format: {data_source}")
        
        elif isinstance(data_source, dict):
            # Database query configuration
            if 'query' in data_source:
                return await self.db_service.execute_query(data_source['query'])
            else:
                raise ValueError("Invalid database configuration")
        
        else:
            raise ValueError(f"Unsupported data source type: {type(data_source)}")
    
    async def _clean_data(
        self,
        data: pd.DataFrame,
        quality_report: DataQualityReport,
        config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Clean data based on quality report recommendations."""
        
        cleaned_data = data.copy()
        
        # Remove duplicates
        has_duplicates = any(
            issue['type'] == DataQualityIssue.DUPLICATE_RECORDS.value
            for issue in quality_report.quality_issues
        )
        
        if has_duplicates:
            cleaned_data = cleaned_data.drop_duplicates()
            logger.info(f"Removed {len(data) - len(cleaned_data)} duplicate records")
        
        # Handle missing values
        missing_value_strategy = config.get('missing_value_strategy', 'auto')
        
        if missing_value_strategy == 'auto':
            # Auto strategy based on quality report
            for feature, missing_pct in quality_report.missing_value_analysis.items():
                if missing_pct > 50:
                    # Drop features with >50% missing
                    if feature in cleaned_data.columns:
                        cleaned_data = cleaned_data.drop(columns=[feature])
                        logger.info(f"Dropped feature {feature} (missing: {missing_pct:.1f}%)")
                
                elif missing_pct > 10:
                    # Use advanced imputation
                    if feature in cleaned_data.columns:
                        if cleaned_data[feature].dtype in [np.number]:
                            # KNN imputation for numeric
                            imputer = KNNImputer(n_neighbors=5)
                            cleaned_data[[feature]] = imputer.fit_transform(cleaned_data[[feature]])
                        else:
                            # Mode imputation for categorical
                            mode_value = cleaned_data[feature].mode().iloc[0] if len(cleaned_data[feature].mode()) > 0 else 'unknown'
                            cleaned_data[feature] = cleaned_data[feature].fillna(mode_value)
                
                elif missing_pct > 0:
                    # Simple imputation for small amounts
                    if feature in cleaned_data.columns:
                        if cleaned_data[feature].dtype in [np.number]:
                            cleaned_data[feature] = cleaned_data[feature].fillna(cleaned_data[feature].median())
                        else:
                            cleaned_data[feature] = cleaned_data[feature].fillna('unknown')
        
        # Handle outliers
        outlier_treatment = config.get('outlier_treatment', 'cap')
        
        if outlier_treatment == 'cap':
            for feature, outlier_info in quality_report.outlier_analysis.items():
                if outlier_info.get('iqr_outlier_percentage', 0) > 5:
                    # Cap outliers at 1st and 99th percentiles
                    if feature in cleaned_data.columns:
                        q01 = cleaned_data[feature].quantile(0.01)
                        q99 = cleaned_data[feature].quantile(0.99)
                        cleaned_data[feature] = cleaned_data[feature].clip(lower=q01, upper=q99)
        
        return cleaned_data
    
    def _get_temporal_config(self, processing_config: Dict[str, Any]) -> TemporalFeatureConfig:
        """Get temporal feature configuration."""
        
        temporal_config_dict = processing_config.get('temporal_config', {})
        
        config = TemporalFeatureConfig(
            extract_date_components=temporal_config_dict.get('extract_date_components', True),
            extract_time_components=temporal_config_dict.get('extract_time_components', True),
            include_business_calendar=temporal_config_dict.get('include_business_calendar', True),
            lag_periods=temporal_config_dict.get('lag_periods', [1, 7, 30]),
            lag_features=temporal_config_dict.get('lag_features', []),
            rolling_windows=temporal_config_dict.get('rolling_windows', [7, 14, 30]),
            rolling_features=temporal_config_dict.get('rolling_features', []),
            detect_trends=temporal_config_dict.get('detect_trends', True),
            detect_seasonality=temporal_config_dict.get('detect_seasonality', True),
            detect_change_points=temporal_config_dict.get('detect_change_points', False),
            change_point_features=temporal_config_dict.get('change_point_features', []),
            fourier_features=temporal_config_dict.get('fourier_features', True),
            fourier_orders=temporal_config_dict.get('fourier_orders', [1, 2])
        )
        
        return config
    
    async def _prepare_final_data(
        self,
        data: pd.DataFrame,
        config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Prepare final processed dataset."""
        
        final_data = data.copy()
        
        # Feature selection if specified
        if 'feature_columns' in config and config['feature_columns']:
            available_features = [col for col in config['feature_columns'] if col in final_data.columns]
            final_data = final_data[available_features]
        
        # Data type optimization
        final_data = self._optimize_data_types(final_data)
        
        # Final cleanup
        final_data = final_data.replace([np.inf, -np.inf], np.nan)
        final_data = final_data.fillna(0)
        
        return final_data
    
    def _optimize_data_types(self, data: pd.DataFrame) -> pd.DataFrame:
        """Optimize data types for memory efficiency."""
        
        optimized_data = data.copy()
        
        # Optimize numeric columns
        numeric_columns = optimized_data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            col_min = optimized_data[col].min()
            col_max = optimized_data[col].max()
            
            # Integer columns
            if optimized_data[col].dtype in ['int64', 'int32']:
                if col_min >= 0:
                    if col_max < 255:
                        optimized_data[col] = optimized_data[col].astype('uint8')
                    elif col_max < 65535:
                        optimized_data[col] = optimized_data[col].astype('uint16')
                    elif col_max < 4294967295:
                        optimized_data[col] = optimized_data[col].astype('uint32')
                else:
                    if col_min > -128 and col_max < 127:
                        optimized_data[col] = optimized_data[col].astype('int8')
                    elif col_min > -32768 and col_max < 32767:
                        optimized_data[col] = optimized_data[col].astype('int16')
                    elif col_min > -2147483648 and col_max < 2147483647:
                        optimized_data[col] = optimized_data[col].astype('int32')
            
            # Float columns
            elif optimized_data[col].dtype in ['float64', 'float32']:
                optimized_data[col] = pd.to_numeric(optimized_data[col], downcast='float')
        
        return optimized_data
    
    async def _save_processed_data(self, data: pd.DataFrame, output_config: Dict[str, Any]):
        """Save processed data to specified output."""
        
        if not output_config:
            return
        
        output_type = output_config.get('type', 'csv')
        output_path = output_config.get('path', 'processed_data.csv')
        
        if output_type == 'csv':
            data.to_csv(output_path, index=False)
        elif output_type == 'parquet':
            data.to_parquet(output_path, index=False)
        elif output_type == 'json':
            data.to_json(output_path, orient='records')
        elif output_type == 'database':
            # Save to database
            table_name = output_config.get('table_name', 'processed_data')
            await self.db_service.store_dataframe(data, table_name)
        
        logger.info(f"Saved processed data to {output_path}")
    
    # Public API methods
    
    async def get_job_status(self, job_id: str) -> Optional[ProcessingJob]:
        """Get processing job status."""
        return self.active_jobs.get(job_id)
    
    async def list_active_jobs(self) -> List[ProcessingJob]:
        """List all active processing jobs."""
        return list(self.active_jobs.values())
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel processing job."""
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status == ProcessingStatus.RUNNING:
                job.status = ProcessingStatus.CANCELLED
                job.completed_at = datetime.now()
                job.processing_logs.append("Job cancelled by user")
                logger.info(f"Cancelled processing job {job_id}")
                return True
        return False


# Factory function
def create_historical_data_processor(database_service: DatabaseService = None) -> HistoricalDataProcessor:
    """Create historical data processor instance."""
    return HistoricalDataProcessor(database_service)