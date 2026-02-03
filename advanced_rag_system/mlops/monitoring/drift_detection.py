"""
Enterprise Model Drift Detection for RAG Systems
Demonstrates advanced MLOps monitoring and alerting capabilities
"""
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
from pathlib import Path
import scipy.stats as stats
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN

logger = logging.getLogger(__name__)


class DriftType(Enum):
    """Types of drift detection"""
    DATA_DRIFT = "data_drift"
    CONCEPT_DRIFT = "concept_drift"
    PERFORMANCE_DRIFT = "performance_drift"
    EMBEDDING_DRIFT = "embedding_drift"


class DriftSeverity(Enum):
    """Drift severity levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DriftAlert:
    """Drift detection alert"""
    timestamp: datetime
    drift_type: DriftType
    severity: DriftSeverity
    metric_name: str
    baseline_value: float
    current_value: float
    drift_score: float
    threshold: float
    description: str
    model_name: str
    model_version: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['drift_type'] = self.drift_type.value
        data['severity'] = self.severity.value
        return data


class StatisticalDriftDetector:
    """
    Statistical drift detection using multiple methods

    Implements enterprise-grade drift detection algorithms:
    - Kolmogorov-Smirnov test for distribution drift
    - Population Stability Index (PSI) for feature drift
    - Wasserstein distance for distribution comparison
    - Chi-square test for categorical drift
    """

    def __init__(self, baseline_window: int = 1000, detection_window: int = 100):
        """
        Initialize drift detector

        Args:
            baseline_window: Size of baseline data window
            detection_window: Size of detection data window
        """
        self.baseline_window = baseline_window
        self.detection_window = detection_window

    def kolmogorov_smirnov_test(
        self,
        baseline: np.ndarray,
        current: np.ndarray,
        alpha: float = 0.05
    ) -> Tuple[float, bool]:
        """
        Kolmogorov-Smirnov test for distribution drift

        Args:
            baseline: Baseline data distribution
            current: Current data distribution
            alpha: Significance level

        Returns:
            (KS statistic, is_drift)
        """
        try:
            ks_statistic, p_value = stats.ks_2samp(baseline, current)
            is_drift = p_value < alpha
            return ks_statistic, is_drift
        except Exception as e:
            logger.error(f"KS test failed: {e}")
            return 0.0, False

    def population_stability_index(
        self,
        baseline: np.ndarray,
        current: np.ndarray,
        bins: int = 10
    ) -> float:
        """
        Calculate Population Stability Index (PSI)

        PSI measures the change in distribution between two samples:
        - PSI < 0.1: No significant change
        - 0.1 ≤ PSI < 0.2: Moderate change
        - PSI ≥ 0.2: Significant change

        Args:
            baseline: Baseline data
            current: Current data
            bins: Number of bins for discretization

        Returns:
            PSI score
        """
        try:
            # Create bins based on baseline data
            _, bin_edges = np.histogram(baseline, bins=bins)

            # Calculate distributions
            baseline_dist, _ = np.histogram(baseline, bins=bin_edges, density=True)
            current_dist, _ = np.histogram(current, bins=bin_edges, density=True)

            # Normalize to get probabilities
            baseline_dist = baseline_dist / baseline_dist.sum()
            current_dist = current_dist / current_dist.sum()

            # Add small constant to avoid log(0)
            epsilon = 1e-10
            baseline_dist = baseline_dist + epsilon
            current_dist = current_dist + epsilon

            # Calculate PSI
            psi = np.sum((current_dist - baseline_dist) * np.log(current_dist / baseline_dist))
            return float(psi)

        except Exception as e:
            logger.error(f"PSI calculation failed: {e}")
            return 0.0

    def wasserstein_distance(
        self,
        baseline: np.ndarray,
        current: np.ndarray
    ) -> float:
        """
        Calculate Wasserstein (Earth Mover's) distance

        Args:
            baseline: Baseline data
            current: Current data

        Returns:
            Wasserstein distance
        """
        try:
            distance = stats.wasserstein_distance(baseline, current)
            return float(distance)
        except Exception as e:
            logger.error(f"Wasserstein distance calculation failed: {e}")
            return 0.0

    def chi_square_test(
        self,
        baseline: np.ndarray,
        current: np.ndarray,
        alpha: float = 0.05
    ) -> Tuple[float, bool]:
        """
        Chi-square test for categorical drift

        Args:
            baseline: Baseline categorical data
            current: Current categorical data
            alpha: Significance level

        Returns:
            (Chi-square statistic, is_drift)
        """
        try:
            # Get unique categories from both samples
            categories = np.unique(np.concatenate([baseline, current]))

            # Create contingency table
            baseline_counts = np.array([np.sum(baseline == cat) for cat in categories])
            current_counts = np.array([np.sum(current == cat) for cat in categories])

            # Perform chi-square test
            chi2_stat, p_value = stats.chisquare(current_counts, baseline_counts)
            is_drift = p_value < alpha
            return float(chi2_stat), is_drift

        except Exception as e:
            logger.error(f"Chi-square test failed: {e}")
            return 0.0, False


class EmbeddingDriftDetector:
    """
    Advanced drift detection for embedding models

    Detects drift in high-dimensional embedding spaces using:
    - Cosine similarity distribution changes
    - Principal component analysis
    - Clustering-based anomaly detection
    """

    def __init__(self, embedding_dim: int = 1536):
        """
        Initialize embedding drift detector

        Args:
            embedding_dim: Dimension of embeddings
        """
        self.embedding_dim = embedding_dim
        self.pca = None
        self.baseline_clusters = None

    def cosine_similarity_drift(
        self,
        baseline_embeddings: np.ndarray,
        current_embeddings: np.ndarray
    ) -> Dict[str, float]:
        """
        Detect drift in cosine similarity patterns

        Args:
            baseline_embeddings: Baseline embedding matrix (N x D)
            current_embeddings: Current embedding matrix (M x D)

        Returns:
            Drift metrics dictionary
        """
        try:
            # Calculate pairwise cosine similarities
            baseline_sim = cosine_similarity(baseline_embeddings)
            current_sim = cosine_similarity(current_embeddings)

            # Extract upper triangular similarities (excluding diagonal)
            baseline_sims = baseline_sim[np.triu_indices_from(baseline_sim, k=1)]
            current_sims = current_sim[np.triu_indices_from(current_sim, k=1)]

            # Statistical comparison
            detector = StatisticalDriftDetector()
            ks_stat, ks_drift = detector.kolmogorov_smirnov_test(baseline_sims, current_sims)
            psi_score = detector.population_stability_index(baseline_sims, current_sims)
            wasserstein_dist = detector.wasserstein_distance(baseline_sims, current_sims)

            return {
                "ks_statistic": ks_stat,
                "ks_drift_detected": ks_drift,
                "psi_score": psi_score,
                "wasserstein_distance": wasserstein_dist,
                "baseline_mean_similarity": float(np.mean(baseline_sims)),
                "current_mean_similarity": float(np.mean(current_sims)),
                "baseline_std_similarity": float(np.std(baseline_sims)),
                "current_std_similarity": float(np.std(current_sims))
            }

        except Exception as e:
            logger.error(f"Cosine similarity drift detection failed: {e}")
            return {}

    def pca_drift_detection(
        self,
        baseline_embeddings: np.ndarray,
        current_embeddings: np.ndarray,
        n_components: int = 50
    ) -> Dict[str, float]:
        """
        PCA-based drift detection for high-dimensional embeddings

        Args:
            baseline_embeddings: Baseline embedding matrix
            current_embeddings: Current embedding matrix
            n_components: Number of PCA components

        Returns:
            PCA drift metrics
        """
        try:
            # Fit PCA on baseline data
            self.pca = PCA(n_components=n_components)
            baseline_pca = self.pca.fit_transform(baseline_embeddings)

            # Transform current data using baseline PCA
            current_pca = self.pca.transform(current_embeddings)

            # Compare distributions in PCA space
            detector = StatisticalDriftDetector()
            drift_scores = []

            for i in range(n_components):
                psi = detector.population_stability_index(
                    baseline_pca[:, i], current_pca[:, i]
                )
                drift_scores.append(psi)

            return {
                "mean_pca_drift": float(np.mean(drift_scores)),
                "max_pca_drift": float(np.max(drift_scores)),
                "explained_variance_ratio": self.pca.explained_variance_ratio_.tolist()[:10],
                "drift_by_component": drift_scores[:10]  # Top 10 components
            }

        except Exception as e:
            logger.error(f"PCA drift detection failed: {e}")
            return {}

    def clustering_drift_detection(
        self,
        baseline_embeddings: np.ndarray,
        current_embeddings: np.ndarray,
        eps: float = 0.5,
        min_samples: int = 5
    ) -> Dict[str, Any]:
        """
        Clustering-based drift detection

        Args:
            baseline_embeddings: Baseline embedding matrix
            current_embeddings: Current embedding matrix
            eps: DBSCAN epsilon parameter
            min_samples: DBSCAN min_samples parameter

        Returns:
            Clustering drift metrics
        """
        try:
            # Cluster baseline data
            baseline_clusterer = DBSCAN(eps=eps, min_samples=min_samples)
            baseline_labels = baseline_clusterer.fit_predict(baseline_embeddings)

            # Cluster current data
            current_clusterer = DBSCAN(eps=eps, min_samples=min_samples)
            current_labels = current_clusterer.fit_predict(current_embeddings)

            # Compare cluster statistics
            baseline_n_clusters = len(set(baseline_labels)) - (1 if -1 in baseline_labels else 0)
            current_n_clusters = len(set(current_labels)) - (1 if -1 in current_labels else 0)

            baseline_noise_ratio = np.sum(baseline_labels == -1) / len(baseline_labels)
            current_noise_ratio = np.sum(current_labels == -1) / len(current_labels)

            # Calculate cluster size distributions
            baseline_cluster_sizes = [
                np.sum(baseline_labels == i) for i in set(baseline_labels) if i != -1
            ]
            current_cluster_sizes = [
                np.sum(current_labels == i) for i in set(current_labels) if i != -1
            ]

            return {
                "baseline_n_clusters": baseline_n_clusters,
                "current_n_clusters": current_n_clusters,
                "cluster_count_drift": abs(current_n_clusters - baseline_n_clusters),
                "baseline_noise_ratio": float(baseline_noise_ratio),
                "current_noise_ratio": float(current_noise_ratio),
                "noise_ratio_drift": float(abs(current_noise_ratio - baseline_noise_ratio)),
                "baseline_avg_cluster_size": float(np.mean(baseline_cluster_sizes)) if baseline_cluster_sizes else 0,
                "current_avg_cluster_size": float(np.mean(current_cluster_sizes)) if current_cluster_sizes else 0
            }

        except Exception as e:
            logger.error(f"Clustering drift detection failed: {e}")
            return {}


class PerformanceDriftDetector:
    """
    Performance-based drift detection for ML models

    Monitors model performance metrics over time and detects degradation
    """

    def __init__(self, baseline_window: int = 1000):
        """Initialize performance drift detector"""
        self.baseline_window = baseline_window

    def detect_metric_drift(
        self,
        baseline_metrics: List[float],
        current_metrics: List[float],
        metric_name: str,
        threshold: float = 0.05
    ) -> Dict[str, Any]:
        """
        Detect drift in performance metrics

        Args:
            baseline_metrics: Historical performance values
            current_metrics: Current performance values
            metric_name: Name of the metric
            threshold: Drift threshold (relative change)

        Returns:
            Drift detection results
        """
        try:
            baseline_mean = np.mean(baseline_metrics)
            current_mean = np.mean(current_metrics)

            # Calculate relative change
            relative_change = abs(current_mean - baseline_mean) / baseline_mean
            is_drift = relative_change > threshold

            # Statistical tests
            detector = StatisticalDriftDetector()
            ks_stat, ks_drift = detector.kolmogorov_smirnov_test(
                np.array(baseline_metrics), np.array(current_metrics)
            )

            return {
                "metric_name": metric_name,
                "baseline_mean": float(baseline_mean),
                "current_mean": float(current_mean),
                "relative_change": float(relative_change),
                "threshold": threshold,
                "is_drift": is_drift,
                "ks_statistic": ks_stat,
                "ks_drift_detected": ks_drift,
                "baseline_std": float(np.std(baseline_metrics)),
                "current_std": float(np.std(current_metrics))
            }

        except Exception as e:
            logger.error(f"Metric drift detection failed for {metric_name}: {e}")
            return {"error": str(e)}


class DriftMonitor:
    """
    Comprehensive drift monitoring system for RAG models

    Integrates multiple drift detection methods and provides alerting
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize drift monitor

        Args:
            config: Configuration dictionary with thresholds and parameters
        """
        self.config = config
        self.alerts: List[DriftAlert] = []
        self.statistical_detector = StatisticalDriftDetector()
        self.embedding_detector = EmbeddingDriftDetector()
        self.performance_detector = PerformanceDriftDetector()

        # Load baseline data if available
        self.baseline_data: Dict[str, Any] = {}
        self._load_baselines()

    def _load_baselines(self) -> None:
        """Load baseline data for comparison"""
        baseline_path = Path(self.config.get("baseline_path", "baselines"))
        if baseline_path.exists():
            for baseline_file in baseline_path.glob("*.json"):
                try:
                    with open(baseline_file, 'r') as f:
                        baseline_name = baseline_file.stem
                        self.baseline_data[baseline_name] = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading baseline {baseline_file}: {e}")

    def _determine_severity(self, drift_score: float, metric_name: str) -> DriftSeverity:
        """Determine drift severity based on score and thresholds"""
        thresholds = self.config.get("thresholds", {}).get(metric_name, {
            "low": 0.1,
            "moderate": 0.2,
            "high": 0.3,
            "critical": 0.5
        })

        if drift_score >= thresholds.get("critical", 0.5):
            return DriftSeverity.CRITICAL
        elif drift_score >= thresholds.get("high", 0.3):
            return DriftSeverity.HIGH
        elif drift_score >= thresholds.get("moderate", 0.2):
            return DriftSeverity.MODERATE
        else:
            return DriftSeverity.LOW

    def monitor_embedding_drift(
        self,
        embeddings: np.ndarray,
        model_name: str,
        model_version: str,
        baseline_key: str = "embedding_baseline"
    ) -> List[DriftAlert]:
        """Monitor embedding drift and generate alerts"""
        alerts = []

        if baseline_key not in self.baseline_data:
            logger.warning(f"No baseline data found for {baseline_key}")
            return alerts

        try:
            baseline_embeddings = np.array(self.baseline_data[baseline_key]["embeddings"])

            # Cosine similarity drift
            cos_results = self.embedding_detector.cosine_similarity_drift(
                baseline_embeddings, embeddings
            )

            if cos_results.get("psi_score", 0) > 0.1:
                severity = self._determine_severity(cos_results["psi_score"], "psi_score")
                alert = DriftAlert(
                    timestamp=datetime.utcnow(),
                    drift_type=DriftType.EMBEDDING_DRIFT,
                    severity=severity,
                    metric_name="cosine_similarity_psi",
                    baseline_value=0.0,
                    current_value=cos_results["psi_score"],
                    drift_score=cos_results["psi_score"],
                    threshold=0.1,
                    description=f"Cosine similarity drift detected (PSI: {cos_results['psi_score']:.3f})",
                    model_name=model_name,
                    model_version=model_version,
                    metadata=cos_results
                )
                alerts.append(alert)

            # PCA drift
            pca_results = self.embedding_detector.pca_drift_detection(
                baseline_embeddings, embeddings
            )

            if pca_results.get("mean_pca_drift", 0) > 0.2:
                severity = self._determine_severity(pca_results["mean_pca_drift"], "pca_drift")
                alert = DriftAlert(
                    timestamp=datetime.utcnow(),
                    drift_type=DriftType.EMBEDDING_DRIFT,
                    severity=severity,
                    metric_name="pca_drift",
                    baseline_value=0.0,
                    current_value=pca_results["mean_pca_drift"],
                    drift_score=pca_results["mean_pca_drift"],
                    threshold=0.2,
                    description=f"PCA drift detected (mean: {pca_results['mean_pca_drift']:.3f})",
                    model_name=model_name,
                    model_version=model_version,
                    metadata=pca_results
                )
                alerts.append(alert)

        except Exception as e:
            logger.error(f"Embedding drift monitoring failed: {e}")

        self.alerts.extend(alerts)
        return alerts

    def monitor_performance_drift(
        self,
        current_metrics: Dict[str, float],
        model_name: str,
        model_version: str,
        baseline_key: str = "performance_baseline"
    ) -> List[DriftAlert]:
        """Monitor performance drift and generate alerts"""
        alerts = []

        if baseline_key not in self.baseline_data:
            logger.warning(f"No baseline data found for {baseline_key}")
            return alerts

        baseline_metrics = self.baseline_data[baseline_key]

        for metric_name, current_value in current_metrics.items():
            if metric_name not in baseline_metrics:
                continue

            try:
                baseline_values = baseline_metrics[metric_name]
                if isinstance(baseline_values, list):
                    baseline_mean = np.mean(baseline_values)
                else:
                    baseline_mean = baseline_values

                # Calculate drift
                relative_change = abs(current_value - baseline_mean) / abs(baseline_mean)
                threshold = self.config.get("thresholds", {}).get(metric_name, {}).get("moderate", 0.1)

                if relative_change > threshold:
                    severity = self._determine_severity(relative_change, metric_name)
                    alert = DriftAlert(
                        timestamp=datetime.utcnow(),
                        drift_type=DriftType.PERFORMANCE_DRIFT,
                        severity=severity,
                        metric_name=metric_name,
                        baseline_value=baseline_mean,
                        current_value=current_value,
                        drift_score=relative_change,
                        threshold=threshold,
                        description=f"Performance drift in {metric_name}: {relative_change:.1%} change",
                        model_name=model_name,
                        model_version=model_version,
                        metadata={
                            "baseline_mean": baseline_mean,
                            "current_value": current_value,
                            "relative_change": relative_change
                        }
                    )
                    alerts.append(alert)

            except Exception as e:
                logger.error(f"Performance drift monitoring failed for {metric_name}: {e}")

        self.alerts.extend(alerts)
        return alerts

    def get_drift_report(
        self,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive drift report"""
        if time_window:
            cutoff_time = datetime.utcnow() - time_window
            relevant_alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]
        else:
            relevant_alerts = self.alerts

        # Group alerts by severity and type
        severity_counts = {}
        type_counts = {}

        for alert in relevant_alerts:
            severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1
            type_counts[alert.drift_type.value] = type_counts.get(alert.drift_type.value, 0) + 1

        return {
            "report_timestamp": datetime.utcnow().isoformat(),
            "time_window_hours": time_window.total_seconds() / 3600 if time_window else "all_time",
            "total_alerts": len(relevant_alerts),
            "alerts_by_severity": severity_counts,
            "alerts_by_type": type_counts,
            "recent_alerts": [alert.to_dict() for alert in relevant_alerts[-10:]],  # Last 10 alerts
            "critical_alerts": [
                alert.to_dict() for alert in relevant_alerts
                if alert.severity == DriftSeverity.CRITICAL
            ]
        }

    def save_baselines(
        self,
        embeddings: Optional[np.ndarray] = None,
        performance_metrics: Optional[Dict[str, Any]] = None,
        output_path: str = "baselines"
    ) -> None:
        """Save current data as baselines for future drift detection"""
        baseline_dir = Path(output_path)
        baseline_dir.mkdir(exist_ok=True)

        if embeddings is not None:
            baseline_data = {
                "embeddings": embeddings.tolist(),
                "timestamp": datetime.utcnow().isoformat(),
                "embedding_shape": embeddings.shape
            }
            with open(baseline_dir / "embedding_baseline.json", 'w') as f:
                json.dump(baseline_data, f)

        if performance_metrics is not None:
            baseline_data = {
                **performance_metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
            with open(baseline_dir / "performance_baseline.json", 'w') as f:
                json.dump(baseline_data, f)

        logger.info(f"Baselines saved to {output_path}")


# Example configuration for RAG system
def create_rag_drift_monitor() -> DriftMonitor:
    """Create drift monitor for RAG system"""
    config = {
        "baseline_path": "baselines",
        "thresholds": {
            "psi_score": {"low": 0.1, "moderate": 0.2, "high": 0.3, "critical": 0.5},
            "pca_drift": {"low": 0.15, "moderate": 0.25, "high": 0.35, "critical": 0.6},
            "recall_at_5": {"low": 0.02, "moderate": 0.05, "high": 0.1, "critical": 0.15},
            "ndcg_at_10": {"low": 0.02, "moderate": 0.05, "high": 0.1, "critical": 0.15},
            "response_latency": {"low": 0.1, "moderate": 0.2, "high": 0.3, "critical": 0.5}
        }
    }
    return DriftMonitor(config)