#!/usr/bin/env python3
"""
Pattern Analysis Job for Intelligent Cache Warming
==================================================

Standalone job for analyzing cache usage patterns and training ML models
for predictive cache warming. Can be run as a cron job or triggered manually.

Features:
- Historical usage data analysis
- ML model training for usage prediction
- Pattern detection and classification
- Performance metrics generation
- Integration with production monitoring

Author: Jorge Platform Engineering Team
Version: 2.0.0
Date: 2026-01-24
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import argparse
import signal

# Data analysis libraries
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

# Redis and monitoring
import redis
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# Internal services
from ghl_real_estate_ai.services.intelligent_cache_warming_service import (
    IntelligentCacheWarmingService,
    get_intelligent_cache_warming_service,
    UsageDataPoint,
    UsagePattern
)
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.ghl_utils.logger import get_logger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)

class PatternAnalysisJob:
    """
    Main pattern analysis job for cache warming optimization
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_default_config()
        self.cache_service = get_cache_service()
        self.warming_service = get_intelligent_cache_warming_service()

        # Analysis results
        self.analysis_results = {}
        self.performance_metrics = {}

        # Redis connection for historical data
        self.redis_client = None

        # Prometheus metrics for job monitoring
        self.registry = CollectorRegistry()
        self.job_duration = Gauge('cache_pattern_analysis_duration_seconds',
                                'Pattern analysis job duration', registry=self.registry)
        self.patterns_discovered = Gauge('cache_patterns_discovered_total',
                                      'Total patterns discovered', registry=self.registry)
        self.models_trained = Gauge('cache_models_trained_total',
                                  'Total ML models trained', registry=self.registry)
        self.prediction_accuracy = Gauge('cache_prediction_accuracy_score',
                                       'Model prediction accuracy', registry=self.registry)

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            'analysis_window_hours': int(os.getenv('ANALYSIS_WINDOW_HOURS', '168')),  # 7 days
            'min_data_points': int(os.getenv('MIN_DATA_POINTS', '100')),
            'model_retrain_threshold': float(os.getenv('MODEL_RETRAIN_THRESHOLD', '0.1')),
            'pattern_confidence_threshold': float(os.getenv('PATTERN_CONFIDENCE_THRESHOLD', '0.7')),
            'enable_pushgateway': os.getenv('ENABLE_PUSHGATEWAY', 'false').lower() == 'true',
            'pushgateway_url': os.getenv('PUSHGATEWAY_URL', 'http://prometheus-pushgateway:9091'),
            'redis_key_prefix': os.getenv('REDIS_KEY_PREFIX', 'jorge:cache_usage:'),
            'output_file': os.getenv('OUTPUT_FILE', '/tmp/pattern_analysis_results.json')
        }

    async def initialize(self):
        """Initialize job components"""
        try:
            logger.info("Initializing pattern analysis job...")

            # Initialize Redis connection for historical data
            redis_config = {
                'host': os.getenv('REDIS_CLUSTER_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_CLUSTER_PORT', '6379')),
                'password': os.getenv('REDIS_PASSWORD'),
                'decode_responses': True
            }

            if os.getenv('REDIS_CLUSTER_MODE', 'false').lower() == 'true':
                # Redis cluster mode
                from rediscluster import RedisCluster
                self.redis_client = RedisCluster(
                    startup_nodes=[{
                        'host': redis_config['host'],
                        'port': redis_config['port']
                    }],
                    password=redis_config['password'],
                    decode_responses=True
                )
            else:
                # Single Redis instance
                self.redis_client = redis.Redis(**redis_config)

            # Test Redis connection
            await asyncio.get_event_loop().run_in_executor(None, self.redis_client.ping)
            logger.info("Redis connection established")

            logger.info("Pattern analysis job initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize pattern analysis job: {e}")
            raise

    async def collect_historical_usage_data(self) -> List[UsageDataPoint]:
        """Collect historical cache usage data from Redis"""
        try:
            logger.info("Collecting historical usage data...")

            # Calculate time window
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=self.config['analysis_window_hours'])

            usage_data = []

            # Get usage data keys from Redis
            key_pattern = f"{self.config['redis_key_prefix']}*"

            def get_redis_keys():
                return self.redis_client.keys(key_pattern)

            keys = await asyncio.get_event_loop().run_in_executor(None, get_redis_keys)
            logger.info(f"Found {len(keys)} usage data keys")

            # Process each key
            for key in keys:
                try:
                    def get_usage_data():
                        return self.redis_client.lrange(key, 0, -1)

                    data_entries = await asyncio.get_event_loop().run_in_executor(None, get_usage_data)

                    for entry in data_entries:
                        try:
                            entry_data = json.loads(entry)
                            timestamp = datetime.fromisoformat(entry_data['timestamp'])

                            # Filter by time window
                            if start_time <= timestamp <= end_time:
                                usage_point = UsageDataPoint(
                                    timestamp=timestamp,
                                    cache_key=entry_data.get('cache_key', ''),
                                    hit_count=entry_data.get('hit_count', 0),
                                    miss_count=entry_data.get('miss_count', 0),
                                    response_time_ms=entry_data.get('response_time_ms', 0.0),
                                    lead_id=entry_data.get('lead_id'),
                                    user_session=entry_data.get('user_session')
                                )
                                usage_data.append(usage_point)

                        except Exception as e:
                            logger.warning(f"Error parsing usage entry: {e}")

                except Exception as e:
                    logger.warning(f"Error processing key {key}: {e}")

            logger.info(f"Collected {len(usage_data)} usage data points")
            return usage_data

        except Exception as e:
            logger.error(f"Failed to collect historical usage data: {e}")
            return []

    async def analyze_usage_patterns(self, usage_data: List[UsageDataPoint]) -> Dict[str, Any]:
        """Analyze usage patterns from historical data"""
        try:
            logger.info("Analyzing usage patterns...")

            if len(usage_data) < self.config['min_data_points']:
                logger.warning(f"Insufficient data points: {len(usage_data)} < {self.config['min_data_points']}")
                return {"status": "insufficient_data"}

            # Convert to DataFrame for analysis
            df_data = []
            for dp in usage_data:
                df_data.append({
                    'timestamp': dp.timestamp,
                    'hour': dp.timestamp.hour,
                    'day_of_week': dp.timestamp.weekday(),
                    'cache_key': dp.cache_key,
                    'total_access': dp.hit_count + dp.miss_count,
                    'miss_rate': dp.miss_count / max(1, dp.hit_count + dp.miss_count),
                    'response_time_ms': dp.response_time_ms,
                    'lead_id': dp.lead_id
                })

            df = pd.DataFrame(df_data)

            # Identify time-based patterns
            patterns = {}

            # Morning rush pattern (8-10 AM)
            morning_data = df[(df['hour'] >= 8) & (df['hour'] <= 10)]
            if len(morning_data) > 20:
                patterns[UsagePattern.MORNING_RUSH.value] = {
                    'avg_access_rate': float(morning_data['total_access'].mean()),
                    'peak_hour': int(morning_data.groupby('hour')['total_access'].mean().idxmax()),
                    'top_cache_keys': morning_data['cache_key'].value_counts().head(10).to_dict(),
                    'avg_response_time': float(morning_data['response_time_ms'].mean()),
                    'data_points': len(morning_data)
                }

            # Lunch activity pattern (12-1 PM)
            lunch_data = df[(df['hour'] >= 12) & (df['hour'] <= 13)]
            if len(lunch_data) > 20:
                patterns[UsagePattern.LUNCH_ACTIVITY.value] = {
                    'avg_access_rate': float(lunch_data['total_access'].mean()),
                    'peak_hour': int(lunch_data.groupby('hour')['total_access'].mean().idxmax()),
                    'top_cache_keys': lunch_data['cache_key'].value_counts().head(10).to_dict(),
                    'avg_response_time': float(lunch_data['response_time_ms'].mean()),
                    'data_points': len(lunch_data)
                }

            # Afternoon peak pattern (2-4 PM)
            afternoon_data = df[(df['hour'] >= 14) & (df['hour'] <= 16)]
            if len(afternoon_data) > 20:
                patterns[UsagePattern.AFTERNOON_PEAK.value] = {
                    'avg_access_rate': float(afternoon_data['total_access'].mean()),
                    'peak_hour': int(afternoon_data.groupby('hour')['total_access'].mean().idxmax()),
                    'top_cache_keys': afternoon_data['cache_key'].value_counts().head(10).to_dict(),
                    'avg_response_time': float(afternoon_data['response_time_ms'].mean()),
                    'data_points': len(afternoon_data)
                }

            # Weekend pattern
            weekend_data = df[df['day_of_week'].isin([5, 6])]  # Saturday, Sunday
            weekday_data = df[~df['day_of_week'].isin([5, 6])]
            if len(weekend_data) > 20 and len(weekday_data) > 20:
                patterns[UsagePattern.WEEKEND_PATTERN.value] = {
                    'avg_access_rate': float(weekend_data['total_access'].mean()),
                    'vs_weekday_ratio': float(weekend_data['total_access'].mean() / weekday_data['total_access'].mean()),
                    'top_cache_keys': weekend_data['cache_key'].value_counts().head(10).to_dict(),
                    'avg_response_time': float(weekend_data['response_time_ms'].mean()),
                    'data_points': len(weekend_data)
                }

            # Cache key popularity analysis
            cache_key_stats = df.groupby('cache_key').agg({
                'total_access': 'sum',
                'miss_rate': 'mean',
                'response_time_ms': 'mean'
            }).reset_index()

            cache_key_stats = cache_key_stats.sort_values('total_access', ascending=False)

            # Performance impact analysis
            high_access_keys = cache_key_stats.head(20)
            performance_impact = {
                'high_traffic_keys': high_access_keys.to_dict('records'),
                'avg_miss_rate': float(df['miss_rate'].mean()),
                'avg_response_time': float(df['response_time_ms'].mean()),
                'total_cache_accesses': int(df['total_access'].sum())
            }

            self.analysis_results = {
                'status': 'success',
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'data_points_analyzed': len(df),
                'time_window_hours': self.config['analysis_window_hours'],
                'patterns_discovered': patterns,
                'performance_impact': performance_impact,
                'cache_key_statistics': cache_key_stats.head(50).to_dict('records')
            }

            # Update metrics
            self.patterns_discovered.set(len(patterns))

            logger.info(f"Pattern analysis completed: {len(patterns)} patterns discovered")
            return self.analysis_results

        except Exception as e:
            logger.error(f"Error in pattern analysis: {e}")
            return {"status": "error", "error": str(e)}

    async def train_prediction_models(self, usage_data: List[UsageDataPoint]) -> Dict[str, Any]:
        """Train ML models for usage prediction"""
        try:
            logger.info("Training prediction models...")

            if len(usage_data) < self.config['min_data_points']:
                return {"status": "insufficient_data"}

            # Convert to DataFrame
            df_data = []
            for dp in usage_data:
                df_data.append({
                    'timestamp': dp.timestamp,
                    'hour': dp.timestamp.hour,
                    'day_of_week': dp.timestamp.weekday(),
                    'cache_key': dp.cache_key,
                    'total_access': dp.hit_count + dp.miss_count,
                    'response_time_ms': dp.response_time_ms
                })

            df = pd.DataFrame(df_data)

            # Get top cache keys for model training
            top_cache_keys = df['cache_key'].value_counts().head(20).index

            models_trained = 0
            model_performance = {}

            for cache_key in top_cache_keys:
                key_data = df[df['cache_key'] == cache_key].copy()

                if len(key_data) < 50:  # Need minimum training data
                    continue

                try:
                    # Feature engineering
                    key_data['hour_sin'] = np.sin(2 * np.pi * key_data['hour'] / 24)
                    key_data['hour_cos'] = np.cos(2 * np.pi * key_data['hour'] / 24)
                    key_data['day_sin'] = np.sin(2 * np.pi * key_data['day_of_week'] / 7)
                    key_data['day_cos'] = np.cos(2 * np.pi * key_data['day_of_week'] / 7)

                    # Prepare features and target
                    features = ['hour_sin', 'hour_cos', 'day_sin', 'day_cos']
                    target = 'total_access'

                    X = key_data[features].fillna(0)
                    y = key_data[target]

                    if len(X) < 20 or y.std() == 0:
                        continue

                    # Split data (80/20 train/test)
                    split_idx = int(len(X) * 0.8)
                    X_train, X_test = X[:split_idx], X[split_idx:]
                    y_train, y_test = y[:split_idx], y[split_idx:]

                    # Scale features
                    scaler = StandardScaler()
                    X_train_scaled = scaler.fit_transform(X_train)
                    X_test_scaled = scaler.transform(X_test)

                    # Train model
                    model = RandomForestRegressor(
                        n_estimators=50,
                        max_depth=10,
                        random_state=42,
                        n_jobs=1
                    )
                    model.fit(X_train_scaled, y_train)

                    # Evaluate model
                    train_pred = model.predict(X_train_scaled)
                    test_pred = model.predict(X_test_scaled)

                    train_r2 = r2_score(y_train, train_pred)
                    test_r2 = r2_score(y_test, test_pred)
                    test_mse = mean_squared_error(y_test, test_pred)

                    model_performance[cache_key] = {
                        'training_r2': float(train_r2),
                        'test_r2': float(test_r2),
                        'test_mse': float(test_mse),
                        'training_samples': len(X_train),
                        'test_samples': len(X_test),
                        'feature_importance': dict(zip(features, model.feature_importances_))
                    }

                    models_trained += 1

                    # Store model in warming service (simplified)
                    # In production, models would be serialized and stored properly
                    self.warming_service.usage_analyzer.pattern_models[cache_key] = model
                    self.warming_service.usage_analyzer.scalers[cache_key] = scaler

                    logger.info(f"Trained model for {cache_key}: R² = {test_r2:.3f}")

                except Exception as e:
                    logger.warning(f"Error training model for {cache_key}: {e}")

            # Calculate average prediction accuracy
            if model_performance:
                avg_accuracy = np.mean([perf['test_r2'] for perf in model_performance.values()])
                self.prediction_accuracy.set(max(0, avg_accuracy))  # Ensure non-negative
            else:
                avg_accuracy = 0.0

            # Update metrics
            self.models_trained.set(models_trained)

            training_results = {
                'status': 'success',
                'models_trained': models_trained,
                'average_accuracy': avg_accuracy,
                'model_performance': model_performance,
                'training_timestamp': datetime.utcnow().isoformat()
            }

            self.performance_metrics = training_results
            logger.info(f"Model training completed: {models_trained} models trained, avg R² = {avg_accuracy:.3f}")

            return training_results

        except Exception as e:
            logger.error(f"Error in model training: {e}")
            return {"status": "error", "error": str(e)}

    async def generate_warming_recommendations(self) -> Dict[str, Any]:
        """Generate cache warming recommendations based on analysis"""
        try:
            logger.info("Generating warming recommendations...")

            recommendations = {
                'immediate_actions': [],
                'scheduled_warming': [],
                'optimization_opportunities': [],
                'performance_insights': []
            }

            # Immediate actions based on pattern analysis
            if self.analysis_results.get('patterns_discovered'):
                patterns = self.analysis_results['patterns_discovered']

                # Morning rush preparation
                if UsagePattern.MORNING_RUSH.value in patterns:
                    morning_pattern = patterns[UsagePattern.MORNING_RUSH.value]
                    recommendations['immediate_actions'].append({
                        'action': 'schedule_morning_warming',
                        'description': 'Pre-warm high-traffic cache keys before morning rush',
                        'cache_keys': list(morning_pattern['top_cache_keys'].keys())[:10],
                        'schedule_time': '07:45:00',
                        'priority': 'high'
                    })

                # Afternoon peak preparation
                if UsagePattern.AFTERNOON_PEAK.value in patterns:
                    afternoon_pattern = patterns[UsagePattern.AFTERNOON_PEAK.value]
                    recommendations['immediate_actions'].append({
                        'action': 'schedule_afternoon_warming',
                        'description': 'Pre-warm cache keys for afternoon peak',
                        'cache_keys': list(afternoon_pattern['top_cache_keys'].keys())[:10],
                        'schedule_time': '13:45:00',
                        'priority': 'medium'
                    })

            # Performance optimization opportunities
            if self.analysis_results.get('performance_impact'):
                perf_data = self.analysis_results['performance_impact']

                if perf_data['avg_miss_rate'] > 0.2:  # >20% miss rate
                    recommendations['optimization_opportunities'].append({
                        'issue': 'high_miss_rate',
                        'description': f"Average miss rate is {perf_data['avg_miss_rate']:.1%}, target is <20%",
                        'suggestion': 'Increase cache warming frequency for high-traffic keys',
                        'impact': 'high'
                    })

                if perf_data['avg_response_time'] > 100:  # >100ms response time
                    recommendations['optimization_opportunities'].append({
                        'issue': 'slow_response_time',
                        'description': f"Average response time is {perf_data['avg_response_time']:.1f}ms",
                        'suggestion': 'Implement more aggressive pre-warming for slow queries',
                        'impact': 'medium'
                    })

            # Model-based recommendations
            if self.performance_metrics.get('model_performance'):
                model_perfs = self.performance_metrics['model_performance']

                high_accuracy_keys = [
                    key for key, perf in model_perfs.items()
                    if perf['test_r2'] > self.config['pattern_confidence_threshold']
                ]

                if high_accuracy_keys:
                    recommendations['scheduled_warming'].append({
                        'strategy': 'ml_predicted_warming',
                        'description': 'Use ML models to predict and pre-warm high-accuracy cache keys',
                        'cache_keys': high_accuracy_keys,
                        'confidence': 'high',
                        'frequency': 'every_15_minutes'
                    })

            # Performance insights
            recommendations['performance_insights'] = [
                {
                    'metric': 'patterns_discovered',
                    'value': len(self.analysis_results.get('patterns_discovered', {})),
                    'benchmark': '>=3 patterns expected for optimal performance'
                },
                {
                    'metric': 'models_trained',
                    'value': self.performance_metrics.get('models_trained', 0),
                    'benchmark': '>=10 models needed for comprehensive coverage'
                },
                {
                    'metric': 'average_model_accuracy',
                    'value': f"{self.performance_metrics.get('average_accuracy', 0):.1%}",
                    'benchmark': '>=70% accuracy target'
                }
            ]

            logger.info(f"Generated {len(recommendations['immediate_actions'])} immediate actions and {len(recommendations['scheduled_warming'])} warming strategies")
            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return {"status": "error", "error": str(e)}

    async def save_results(self, recommendations: Dict[str, Any]):
        """Save analysis results to file and cache"""
        try:
            logger.info("Saving analysis results...")

            # Prepare comprehensive results
            complete_results = {
                'job_metadata': {
                    'job_id': f"pattern_analysis_{int(time.time())}",
                    'execution_timestamp': datetime.utcnow().isoformat(),
                    'analysis_window_hours': self.config['analysis_window_hours'],
                    'version': '2.0.0'
                },
                'analysis_results': self.analysis_results,
                'model_training_results': self.performance_metrics,
                'recommendations': recommendations,
                'configuration': self.config
            }

            # Save to file
            output_file = self.config['output_file']
            with open(output_file, 'w') as f:
                json.dump(complete_results, f, indent=2, default=str)

            logger.info(f"Results saved to {output_file}")

            # Save to Redis cache for real-time access
            if self.redis_client:
                cache_key = "jorge:pattern_analysis:latest"
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.redis_client.set(
                        cache_key,
                        json.dumps(complete_results, default=str),
                        ex=86400  # 24 hour expiry
                    )
                )
                logger.info("Results cached in Redis")

            return complete_results

        except Exception as e:
            logger.error(f"Error saving results: {e}")
            raise

    async def push_metrics(self):
        """Push metrics to Prometheus pushgateway"""
        try:
            if not self.config['enable_pushgateway']:
                return

            logger.info("Pushing metrics to Prometheus...")

            from prometheus_client import push_to_gateway

            # Push metrics
            push_to_gateway(
                self.config['pushgateway_url'],
                job='cache_pattern_analysis',
                registry=self.registry
            )

            logger.info("Metrics pushed successfully")

        except Exception as e:
            logger.warning(f"Failed to push metrics: {e}")

    async def run_analysis(self) -> Dict[str, Any]:
        """Main analysis workflow"""
        start_time = time.time()

        try:
            logger.info("Starting pattern analysis job...")

            # Initialize components
            await self.initialize()

            # Collect historical data
            usage_data = await self.collect_historical_usage_data()
            if not usage_data:
                raise Exception("No usage data collected")

            # Analyze patterns
            pattern_results = await self.analyze_usage_patterns(usage_data)
            if pattern_results.get('status') != 'success':
                raise Exception(f"Pattern analysis failed: {pattern_results}")

            # Train prediction models
            model_results = await self.train_prediction_models(usage_data)
            if model_results.get('status') != 'success':
                logger.warning(f"Model training had issues: {model_results}")

            # Generate recommendations
            recommendations = await self.generate_warming_recommendations()

            # Save results
            complete_results = await self.save_results(recommendations)

            # Record job duration
            duration = time.time() - start_time
            self.job_duration.set(duration)

            # Push metrics
            await self.push_metrics()

            logger.info(f"Pattern analysis job completed successfully in {duration:.2f}s")
            return complete_results

        except Exception as e:
            logger.error(f"Pattern analysis job failed: {e}")
            # Record failure in metrics
            self.job_duration.set(-1)  # Negative value indicates failure
            await self.push_metrics()
            raise

def setup_signal_handlers():
    """Setup graceful shutdown signal handlers"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main entry point for the pattern analysis job"""
    parser = argparse.ArgumentParser(description='Cache Pattern Analysis Job')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--window-hours', type=int, default=168, help='Analysis window in hours')
    parser.add_argument('--min-data-points', type=int, default=100, help='Minimum data points required')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no model updates)')

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    config = {}
    if args.config and os.path.exists(args.config):
        with open(args.config) as f:
            config = json.load(f)

    # Override with command line arguments
    if args.window_hours:
        config['analysis_window_hours'] = args.window_hours
    if args.min_data_points:
        config['min_data_points'] = args.min_data_points
    if args.output:
        config['output_file'] = args.output

    # Setup signal handlers
    setup_signal_handlers()

    # Run the analysis job
    try:
        job = PatternAnalysisJob(config)
        results = asyncio.run(job.run_analysis())

        # Print summary
        logger.info("=== PATTERN ANALYSIS SUMMARY ===")
        logger.info(f"Patterns discovered: {len(results.get('analysis_results', {}).get('patterns_discovered', {}))}")
        logger.info(f"Models trained: {results.get('model_training_results', {}).get('models_trained', 0)}")
        logger.info(f"Average accuracy: {results.get('model_training_results', {}).get('average_accuracy', 0):.1%}")
        logger.info(f"Recommendations: {len(results.get('recommendations', {}).get('immediate_actions', []))}")
        logger.info("================================")

        return 0

    except KeyboardInterrupt:
        logger.info("Job interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Job failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())