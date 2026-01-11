"""
ML Model Monitoring System Usage Example

This example demonstrates how to integrate and use the comprehensive ML monitoring
system with the existing GHL Real Estate AI services.

Examples include:
- Setting up monitoring for existing models
- Recording real-time performance metrics
- Configuring drift detection and alerts
- Running A/B tests for model improvements
- Accessing dashboard data for visualization

Author: EnterpriseHub AI - Production Examples
Date: 2026-01-10
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Example usage of the ML monitoring system
class MLMonitoringUsageExample:
    """Comprehensive examples for using the ML monitoring system"""

    def __init__(self):
        self.monitoring_service = None

    async def setup_monitoring_system(self):
        """Example: Set up the monitoring system"""
        print("🔧 Setting up ML Monitoring System")
        print("="*50)

        # In production, this would be:
        # from ghl_real_estate_ai.services.ml_model_monitoring import get_ml_monitoring_service
        # self.monitoring_service = await get_ml_monitoring_service()

        # For this example, we'll simulate the setup
        print("✅ Monitoring service initialized")
        print("✅ Connected to storage backend")
        print("✅ Registered models: Lead Scoring, Churn Prediction, Property Matching")
        print("✅ Default alerts configured")
        print("✅ Dashboard endpoints active")

    async def record_performance_metrics_example(self):
        """Example: Recording performance metrics for different models"""
        print("\n📊 Recording Performance Metrics")
        print("="*50)

        # Example 1: Lead Scoring Performance
        lead_scoring_metrics = {
            'accuracy': 0.962,
            'precision': 0.945,
            'recall': 0.938,
            'f1_score': 0.941,
            'auc_roc': 0.975,
            'inference_time_ms': 142.5,
            'prediction_count': 1247,
            'timestamp': datetime.now()
        }

        print("📈 Lead Scoring Metrics:")
        for metric, value in lead_scoring_metrics.items():
            if metric != 'timestamp':
                if 'time_ms' in metric:
                    print(f"   {metric}: {value:.1f}ms")
                elif metric in ['accuracy', 'precision', 'recall', 'f1_score', 'auc_roc']:
                    print(f"   {metric}: {value:.1%}")
                else:
                    print(f"   {metric}: {value}")

        # Example 2: Churn Prediction Performance
        churn_prediction_metrics = {
            'accuracy': 0.924,
            'precision': 0.948,
            'recall': 0.892,
            'f1_score': 0.919,
            'auc_roc': 0.956,
            'inference_time_ms': 187.2,
            'prediction_count': 856,
            'timestamp': datetime.now()
        }

        print("\n🔄 Churn Prediction Metrics:")
        for metric, value in churn_prediction_metrics.items():
            if metric != 'timestamp':
                if 'time_ms' in metric:
                    print(f"   {metric}: {value:.1f}ms")
                elif metric in ['accuracy', 'precision', 'recall', 'f1_score', 'auc_roc']:
                    print(f"   {metric}: {value:.1%}")
                else:
                    print(f"   {metric}: {value}")

        # Example 3: Property Matching Performance
        property_matching_metrics = {
            'satisfaction_score': 0.915,
            'match_quality': 0.874,
            'relevance_score': 0.923,
            'response_time_ms': 78.6,
            'prediction_count': 2134,
            'timestamp': datetime.now()
        }

        print("\n🏠 Property Matching Metrics:")
        for metric, value in property_matching_metrics.items():
            if metric != 'timestamp':
                if 'time_ms' in metric:
                    print(f"   {metric}: {value:.1f}ms")
                elif 'score' in metric:
                    print(f"   {metric}: {value:.1%}")
                else:
                    print(f"   {metric}: {value}")

        print("\n✅ All performance metrics recorded successfully")

    async def drift_detection_example(self):
        """Example: Setting up and running drift detection"""
        print("\n🔄 Drift Detection Example")
        print("="*50)

        # Example: Setting baseline distributions
        print("📊 Setting baseline feature distributions...")

        baseline_features = {
            'engagement_score': np.random.normal(0.7, 0.15, 1000),
            'budget_match': np.random.normal(0.6, 0.20, 1000),
            'response_time': np.random.exponential(2.0, 1000),
            'property_views': np.random.poisson(5, 1000)
        }

        print("✅ Baseline distributions set for Lead Scoring model")
        print(f"   - engagement_score: {len(baseline_features['engagement_score'])} samples")
        print(f"   - budget_match: {len(baseline_features['budget_match'])} samples")
        print(f"   - response_time: {len(baseline_features['response_time'])} samples")
        print(f"   - property_views: {len(baseline_features['property_views'])} samples")

        # Example: Detecting drift with current data
        print("\n🔍 Analyzing current feature distributions for drift...")

        # Simulate current data with some drift
        current_features = {
            'engagement_score': np.random.normal(0.65, 0.18, 500),  # Mean shift
            'budget_match': np.random.normal(0.62, 0.25, 500),     # Variance shift
            'response_time': np.random.exponential(3.2, 500),      # Distribution change
            'property_views': np.random.poisson(7, 500)            # Parameter change
        }

        # Simulate drift detection results
        drift_results = {
            'overall_drift_detected': True,
            'drift_magnitude': 0.12,
            'feature_drift_scores': {
                'engagement_score': 0.08,  # Significant drift
                'budget_match': 0.04,      # Moderate drift
                'response_time': 0.15,     # High drift
                'property_views': 0.11     # Significant drift
            },
            'recommended_actions': [
                'Investigate data quality issues',
                'Consider model retraining',
                'Review feature engineering pipeline'
            ]
        }

        print("🚨 Drift Detection Results:")
        print(f"   Overall drift detected: {drift_results['overall_drift_detected']}")
        print(f"   Drift magnitude: {drift_results['drift_magnitude']:.3f}")

        print("\n📈 Feature-level drift scores:")
        for feature, score in drift_results['feature_drift_scores'].items():
            status = "🚨 HIGH" if score > 0.1 else ("🟡 MEDIUM" if score > 0.05 else "✅ LOW")
            print(f"   {feature}: {score:.3f} - {status}")

        print("\n💡 Recommended Actions:")
        for action in drift_results['recommended_actions']:
            print(f"   • {action}")

    async def ab_testing_example(self):
        """Example: Setting up and managing A/B tests"""
        print("\n🧪 A/B Testing Example")
        print("="*50)

        # Example: Creating an A/B test
        test_config = {
            'name': 'Lead Scoring Model Enhancement',
            'model_a': 'lead_scoring_v2.1',  # Current production model
            'model_b': 'lead_scoring_v2.2',  # New improved model
            'traffic_split': 0.3,            # 30% to model B
            'success_metric': 'accuracy',
            'minimum_sample_size': 1000,
            'max_duration_days': 14
        }

        print("🏗️ Creating A/B Test:")
        print(f"   Test Name: {test_config['name']}")
        print(f"   Control Model: {test_config['model_a']}")
        print(f"   Treatment Model: {test_config['model_b']}")
        print(f"   Traffic Split: {(1-test_config['traffic_split'])*100:.0f}%/{test_config['traffic_split']*100:.0f}%")
        print(f"   Success Metric: {test_config['success_metric']}")
        print(f"   Duration: {test_config['max_duration_days']} days")

        test_id = "test_001"  # Would be generated by the system
        print(f"✅ A/B Test created with ID: {test_id}")

        # Example: Simulating test results over time
        print("\n📊 A/B Test Results (after 10 days):")

        # Simulate model A (control) results
        model_a_results = np.random.normal(0.951, 0.02, 1200)
        model_a_mean = np.mean(model_a_results)

        # Simulate model B (treatment) results - slightly better
        model_b_results = np.random.normal(0.967, 0.018, 520)
        model_b_mean = np.mean(model_b_results)

        improvement = ((model_b_mean - model_a_mean) / model_a_mean) * 100

        print(f"   Model A (Control): {model_a_mean:.1%} (n={len(model_a_results)})")
        print(f"   Model B (Treatment): {model_b_mean:.1%} (n={len(model_b_results)})")
        print(f"   Improvement: {improvement:+.1f}%")

        # Simulate statistical significance
        p_value = 0.028  # Simulated p-value
        is_significant = p_value < 0.05

        print(f"\n📈 Statistical Analysis:")
        print(f"   P-value: {p_value:.3f}")
        print(f"   Statistical Significance: {'✅ YES' if is_significant else '❌ NO'}")

        if is_significant and improvement > 0:
            print(f"   🚀 Recommendation: Deploy Model B")
            print(f"   💡 Expected accuracy improvement: {improvement:.1f}%")
        else:
            print(f"   📝 Recommendation: Continue testing")

    async def alert_configuration_example(self):
        """Example: Configuring alerts and monitoring"""
        print("\n🚨 Alert Configuration Example")
        print("="*50)

        # Example alert configurations
        alert_configs = [
            {
                'name': 'lead_scoring_accuracy_drop',
                'model': 'lead_scoring',
                'metric': 'accuracy',
                'threshold': 0.90,
                'comparison': 'less_than',
                'severity': 'high',
                'cooldown_minutes': 30
            },
            {
                'name': 'churn_prediction_latency_spike',
                'model': 'churn_prediction',
                'metric': 'inference_time_ms',
                'threshold': 250,
                'comparison': 'greater_than',
                'severity': 'medium',
                'cooldown_minutes': 15
            },
            {
                'name': 'property_matching_satisfaction_decline',
                'model': 'property_matching',
                'metric': 'satisfaction_score',
                'threshold': 0.80,
                'comparison': 'less_than',
                'severity': 'medium',
                'cooldown_minutes': 60
            }
        ]

        print("⚙️ Configuring Alerts:")
        for config in alert_configs:
            print(f"\n   Alert: {config['name']}")
            print(f"   Model: {config['model']}")
            print(f"   Condition: {config['metric']} {config['comparison']} {config['threshold']}")
            print(f"   Severity: {config['severity'].upper()}")
            print(f"   Cooldown: {config['cooldown_minutes']} minutes")

        print("\n✅ All alerts configured successfully")

        # Example: Simulating alert triggering
        print("\n🔔 Alert Simulation:")
        print("   Scenario: Lead scoring accuracy drops to 88.5%")

        alert_triggered = {
            'alert_name': 'lead_scoring_accuracy_drop',
            'model_name': 'lead_scoring',
            'metric': 'accuracy',
            'current_value': 0.885,
            'threshold': 0.90,
            'severity': 'high',
            'timestamp': datetime.now()
        }

        print(f"   🚨 ALERT TRIGGERED: {alert_triggered['alert_name']}")
        print(f"   📊 {alert_triggered['metric']}: {alert_triggered['current_value']:.1%}")
        print(f"   🎯 Threshold: {alert_triggered['threshold']:.1%}")
        print(f"   ⚠️  Severity: {alert_triggered['severity'].upper()}")
        print(f"   🕐 Time: {alert_triggered['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")

    async def dashboard_integration_example(self):
        """Example: Dashboard data integration"""
        print("\n📊 Dashboard Integration Example")
        print("="*50)

        # Example: Real-time dashboard data
        dashboard_data = {
            'current_metrics': {
                'lead_scoring': {
                    'accuracy': 0.962,
                    'inference_time_ms': 142.5,
                    'predictions_today': 1247,
                    'status': '✅ Healthy'
                },
                'churn_prediction': {
                    'precision': 0.948,
                    'inference_time_ms': 187.2,
                    'predictions_today': 856,
                    'status': '✅ Healthy'
                },
                'property_matching': {
                    'satisfaction_score': 0.915,
                    'response_time_ms': 78.6,
                    'matches_today': 2134,
                    'status': '🟡 Degraded'
                }
            },
            'system_health': {
                'active_alerts': 2,
                'models_with_drift': 1,
                'ab_tests_running': 1,
                'overall_status': 'Operational'
            }
        }

        print("📈 Real-time Model Performance:")
        for model_name, metrics in dashboard_data['current_metrics'].items():
            print(f"\n   {model_name.replace('_', ' ').title()}:")
            for metric, value in metrics.items():
                if metric == 'status':
                    print(f"      Status: {value}")
                elif 'time_ms' in metric:
                    print(f"      {metric.replace('_', ' ').title()}: {value}ms")
                elif metric in ['accuracy', 'precision', 'satisfaction_score']:
                    print(f"      {metric.replace('_', ' ').title()}: {value:.1%}")
                else:
                    print(f"      {metric.replace('_', ' ').title()}: {value}")

        print(f"\n🏥 System Health:")
        health = dashboard_data['system_health']
        print(f"   Active Alerts: {health['active_alerts']}")
        print(f"   Models with Drift: {health['models_with_drift']}")
        print(f"   A/B Tests Running: {health['ab_tests_running']}")
        print(f"   Overall Status: {health['overall_status']}")

        # Example: Historical performance data for charts
        print("\n📊 Historical Performance (Sample):")
        timestamps = [datetime.now() - timedelta(hours=i) for i in range(24, 0, -1)]

        print("   Lead Scoring Accuracy Trend (24h):")
        for i, timestamp in enumerate(timestamps[::6]):  # Every 6 hours
            accuracy = 0.96 - (i * 0.002) + np.random.normal(0, 0.005)
            print(f"      {timestamp.strftime('%H:%M')}: {accuracy:.1%}")

    async def production_integration_example(self):
        """Example: Production integration patterns"""
        print("\n🏭 Production Integration Example")
        print("="*50)

        print("🔗 Integration with Existing Services:")

        # Example: Lead Scoring Service Integration
        print("\n1. Lead Scoring Service Integration:")
        print("   📝 Add monitoring callback to prediction method:")
        print("   ```python")
        print("   async def score_lead(self, lead_data):")
        print("       start_time = time.time()")
        print("       result = await self._predict(lead_data)")
        print("       inference_time = (time.time() - start_time) * 1000")
        print("       ")
        print("       # Record performance metrics")
        print("       await record_lead_scoring_performance({")
        print("           'accuracy': result.confidence,")
        print("           'inference_time_ms': inference_time,")
        print("           'prediction_count': 1")
        print("       })")
        print("       return result")
        print("   ```")

        # Example: Churn Prediction Service Integration
        print("\n2. Churn Prediction Service Integration:")
        print("   📝 Add drift monitoring to feature extraction:")
        print("   ```python")
        print("   async def predict_churn_risk(self, lead_id):")
        print("       features = await self.extract_features(lead_id)")
        print("       prediction = await self._predict(features)")
        print("       ")
        print("       # Monitor for feature drift")
        print("       await detect_model_drift('churn_prediction', {")
        print("           'engagement_score': [features.engagement_score],")
        print("           'response_rate': [features.response_rate]")
        print("       })")
        print("       return prediction")
        print("   ```")

        # Example: Property Matching Service Integration
        print("\n3. Property Matching Service Integration:")
        print("   📝 Add satisfaction tracking:")
        print("   ```python")
        print("   def find_matches(self, preferences):")
        print("       start_time = time.time()")
        print("       matches = self._calculate_matches(preferences)")
        print("       response_time = (time.time() - start_time) * 1000")
        print("       ")
        print("       # Record performance metrics")
        print("       asyncio.create_task(record_property_matching_performance({")
        print("           'match_quality': self._calculate_quality(matches),")
        print("           'response_time_ms': response_time,")
        print("           'prediction_count': len(matches)")
        print("       }))")
        print("       return matches")
        print("   ```")

        print("\n✅ All production integrations configured")

    async def run_complete_example(self):
        """Run complete usage example"""
        print("🚀 ML Model Monitoring System - Complete Usage Example")
        print("="*70)

        examples = [
            self.setup_monitoring_system,
            self.record_performance_metrics_example,
            self.drift_detection_example,
            self.ab_testing_example,
            self.alert_configuration_example,
            self.dashboard_integration_example,
            self.production_integration_example
        ]

        for example in examples:
            await example()

        print("\n" + "="*70)
        print("🎉 Complete ML Monitoring System Example Finished!")
        print("\n📋 Summary of Demonstrated Features:")
        print("   ✅ Real-time performance monitoring")
        print("   ✅ Statistical drift detection")
        print("   ✅ A/B testing framework")
        print("   ✅ Automated alerting system")
        print("   ✅ Dashboard integration")
        print("   ✅ Production service integration")
        print("\n🚀 System ready for production deployment!")


async def main():
    """Run the ML monitoring usage example"""
    example = MLMonitoringUsageExample()
    await example.run_complete_example()


if __name__ == "__main__":
    asyncio.run(main())