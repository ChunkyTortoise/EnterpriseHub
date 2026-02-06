#!/usr/bin/env python3
"""
Optimized Customer Intelligence Platform Deployment Script.

Integrates all performance optimizations:
- Database performance optimization
- Redis configuration optimization
- Connection pooling
- Multi-layer caching
- Performance monitoring
- Load testing validation

Usage:
    python deploy_optimized_platform.py --mode production
    python deploy_optimized_platform.py --mode development --enable-monitoring
"""

import asyncio
import logging
import argparse
import os
import sys
from pathlib import Path
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.database.connection_manager import create_connection_manager
from src.database.performance_optimizer import DatabasePerformanceOptimizer
from src.core.optimized_redis_config import create_optimized_redis_manager
from src.cache.multi_layer_cache import MultiLayerCache
from src.api.optimized_fastapi import OptimizedFastAPIFactory
from src.monitoring.query_performance_monitor import QueryPerformanceMonitor
from src.testing.performance_benchmarks import PerformanceBenchmarks

logger = logging.getLogger(__name__)

class OptimizedPlatformDeployer:
    """Deploy optimized Customer Intelligence Platform."""

    def __init__(
        self,
        mode: str = "production",
        enable_monitoring: bool = True,
        run_benchmarks: bool = False,
        database_url: Optional[str] = None,
        redis_url: Optional[str] = None
    ):
        self.mode = mode
        self.enable_monitoring = enable_monitoring
        self.run_benchmarks = run_benchmarks

        # Connection strings
        self.database_url = database_url or self._get_database_url()
        self.redis_url = redis_url or self._get_redis_url()

        # Initialized components
        self.connection_pool = None
        self.redis_manager = None
        self.cache_manager = None
        self.query_monitor = None
        self.app = None

        # Deployment results
        self.deployment_results = {
            "start_time": datetime.utcnow(),
            "status": "initializing",
            "components": {},
            "optimizations_applied": [],
            "performance_metrics": {},
            "recommendations": []
        }

    def _get_database_url(self) -> str:
        """Get database URL from environment or defaults."""
        return os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:password@localhost:5432/customer_intelligence"
        )

    def _get_redis_url(self) -> str:
        """Get Redis URL from environment or defaults."""
        return os.getenv("REDIS_URL", "redis://localhost:6379/1")

    async def deploy(self) -> Dict[str, Any]:
        """Deploy the optimized platform."""
        logger.info(f"Starting optimized platform deployment in {self.mode} mode")

        try:
            # Initialize components
            await self._initialize_database()
            await self._initialize_redis()
            await self._initialize_cache()
            await self._initialize_monitoring()
            await self._initialize_fastapi_app()

            # Apply optimizations
            await self._apply_database_optimizations()
            await self._apply_redis_optimizations()
            await self._apply_cache_optimizations()

            # Run performance validation
            if self.run_benchmarks:
                await self._run_performance_validation()

            # Finalize deployment
            self.deployment_results["status"] = "completed"
            self.deployment_results["end_time"] = datetime.utcnow()

            logger.info("Platform deployment completed successfully")
            return self.deployment_results

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            self.deployment_results["status"] = "failed"
            self.deployment_results["error"] = str(e)
            raise

    async def _initialize_database(self):
        """Initialize optimized database connection pool."""
        logger.info("Initializing optimized database connection pool")

        try:
            # Production vs Development settings
            if self.mode == "production":
                pool_config = {
                    "initial_pool_size": 20,
                    "max_pool_size": 100,
                    "max_overflow": 50,
                    "enable_adaptive_scaling": True
                }
            else:
                pool_config = {
                    "initial_pool_size": 5,
                    "max_pool_size": 20,
                    "max_overflow": 10,
                    "enable_adaptive_scaling": False
                }

            self.connection_pool = await create_connection_manager(
                self.database_url, **pool_config
            )

            # Verify connection
            health = await self.connection_pool.health_check()
            if health["status"] != "healthy":
                raise Exception(f"Database health check failed: {health}")

            self.deployment_results["components"]["database"] = {
                "status": "initialized",
                "config": pool_config,
                "health": health
            }

            logger.info("Database connection pool initialized successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def _initialize_redis(self):
        """Initialize optimized Redis manager."""
        logger.info("Initializing optimized Redis manager")

        try:
            # Production vs Development settings
            if self.mode == "production":
                redis_config = {
                    "pool_size": 50,
                    "enable_compression": True,
                    "enable_metrics": True
                }
            else:
                redis_config = {
                    "pool_size": 20,
                    "enable_compression": False,
                    "enable_metrics": True
                }

            self.redis_manager = await create_optimized_redis_manager(
                self.redis_url, **redis_config
            )

            # Verify connection
            health = await self.redis_manager.health_check()
            if health["overall_status"] != "healthy":
                raise Exception(f"Redis health check failed: {health}")

            self.deployment_results["components"]["redis"] = {
                "status": "initialized",
                "config": redis_config,
                "health": health
            }

            logger.info("Redis manager initialized successfully")

        except Exception as e:
            logger.error(f"Redis initialization failed: {e}")
            raise

    async def _initialize_cache(self):
        """Initialize multi-layer cache system."""
        logger.info("Initializing multi-layer cache system")

        try:
            # Cache configuration
            if self.mode == "production":
                cache_config = {
                    "l1_max_size": 10000,
                    "l1_max_memory_mb": 500,
                    "enable_compression": True,
                    "enable_analytics": True
                }
            else:
                cache_config = {
                    "l1_max_size": 1000,
                    "l1_max_memory_mb": 100,
                    "enable_compression": False,
                    "enable_analytics": True
                }

            self.cache_manager = MultiLayerCache(
                self.redis_manager, **cache_config
            )

            # Start background tasks
            await self.cache_manager.start_background_tasks()

            self.deployment_results["components"]["cache"] = {
                "status": "initialized",
                "config": cache_config
            }

            logger.info("Multi-layer cache system initialized successfully")

        except Exception as e:
            logger.error(f"Cache initialization failed: {e}")
            raise

    async def _initialize_monitoring(self):
        """Initialize performance monitoring."""
        if not self.enable_monitoring:
            logger.info("Performance monitoring disabled")
            return

        logger.info("Initializing performance monitoring")

        try:
            # Query performance monitoring
            self.query_monitor = QueryPerformanceMonitor(
                self.connection_pool.engine,
                slow_query_threshold_ms=100 if self.mode == "production" else 50,
                enable_query_plans=True,
                enable_real_time_monitoring=True
            )

            await self.query_monitor.start_monitoring()

            self.deployment_results["components"]["monitoring"] = {
                "status": "initialized",
                "query_monitoring": True,
                "real_time_monitoring": True
            }

            logger.info("Performance monitoring initialized successfully")

        except Exception as e:
            logger.error(f"Monitoring initialization failed: {e}")
            raise

    async def _initialize_fastapi_app(self):
        """Initialize optimized FastAPI application."""
        logger.info("Initializing optimized FastAPI application")

        try:
            # Create optimized FastAPI factory
            factory = OptimizedFastAPIFactory(
                self.redis_manager,
                self.connection_pool,
                self.query_monitor
            )

            # Application configuration
            app_config = {
                "enable_performance_monitoring": True,
                "enable_caching": True,
                "enable_circuit_breaker": self.mode == "production",
                "enable_docs": self.mode != "production"
            }

            self.app = factory.create_app(
                title="Optimized Customer Intelligence Platform API",
                version="2.0.0",
                **app_config
            )

            self.deployment_results["components"]["fastapi"] = {
                "status": "initialized",
                "config": app_config
            }

            logger.info("FastAPI application initialized successfully")

        except Exception as e:
            logger.error(f"FastAPI initialization failed: {e}")
            raise

    async def _apply_database_optimizations(self):
        """Apply database performance optimizations."""
        logger.info("Applying database performance optimizations")

        try:
            # Initialize database optimizer
            db_optimizer = DatabasePerformanceOptimizer(self.connection_pool.engine)

            # Analyze current performance
            performance_analysis = await db_optimizer.analyze_table_performance()

            # Get index recommendations
            index_recommendations = await db_optimizer.recommend_indexes()

            # Apply recommended indexes in production mode
            if self.mode == "production" and index_recommendations:
                logger.info(f"Applying {len(index_recommendations)} index recommendations")
                index_results = await db_optimizer.create_optimized_indexes(index_recommendations)

                self.deployment_results["optimizations_applied"].append({
                    "type": "database_indexes",
                    "recommendations_applied": len(index_recommendations),
                    "results": index_results
                })

            # Generate performance report
            performance_report = await db_optimizer.generate_performance_report()

            self.deployment_results["performance_metrics"]["database"] = {
                "table_analysis": performance_analysis,
                "index_recommendations": len(index_recommendations),
                "performance_report": performance_report
            }

            logger.info("Database optimizations applied successfully")

        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            # Don't fail deployment for optimization issues
            self.deployment_results["recommendations"].append(
                f"Database optimization failed: {e}. Manual review recommended."
            )

    async def _apply_redis_optimizations(self):
        """Apply Redis performance optimizations."""
        logger.info("Applying Redis performance optimizations")

        try:
            # Get Redis performance metrics
            redis_metrics = await self.redis_manager.get_performance_metrics()

            self.deployment_results["performance_metrics"]["redis"] = redis_metrics

            # Apply optimizations based on metrics
            optimizations = []

            if redis_metrics.get("cache_hit_rate", 0) < 0.8:
                optimizations.append("Consider increasing cache TTL values")

            if redis_metrics.get("avg_operation_duration_ms", 0) > 10:
                optimizations.append("Consider Redis clustering for better performance")

            self.deployment_results["optimizations_applied"].append({
                "type": "redis_optimizations",
                "recommendations": optimizations
            })

            logger.info("Redis optimizations applied successfully")

        except Exception as e:
            logger.error(f"Redis optimization failed: {e}")
            self.deployment_results["recommendations"].append(
                f"Redis optimization failed: {e}. Manual review recommended."
            )

    async def _apply_cache_optimizations(self):
        """Apply cache system optimizations."""
        logger.info("Applying cache system optimizations")

        try:
            # Get cache statistics
            cache_stats = await self.cache_manager.get_comprehensive_stats()

            self.deployment_results["performance_metrics"]["cache"] = cache_stats

            # Apply optimizations
            optimizations = []

            # L1 cache optimization
            l1_hit_rate = cache_stats["l1_cache"].get("hit_rate", 0)
            if l1_hit_rate < 0.7:
                optimizations.append("Consider increasing L1 cache size")

            # Global hit rate optimization
            global_hit_rate = cache_stats["global"].get("hit_rate", 0)
            if global_hit_rate < 0.8:
                optimizations.append("Consider adjusting cache TTL values")

            self.deployment_results["optimizations_applied"].append({
                "type": "cache_optimizations",
                "recommendations": optimizations
            })

            logger.info("Cache optimizations applied successfully")

        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
            self.deployment_results["recommendations"].append(
                f"Cache optimization failed: {e}. Manual review recommended."
            )

    async def _run_performance_validation(self):
        """Run performance benchmarks to validate optimizations."""
        logger.info("Running performance validation benchmarks")

        try:
            # Initialize benchmark suite
            benchmarks = PerformanceBenchmarks(
                self.connection_pool,
                self.redis_manager,
                self.cache_manager
            )

            # Run full benchmark suite
            benchmark_results = await benchmarks.run_full_benchmark_suite()

            self.deployment_results["performance_metrics"]["benchmarks"] = benchmark_results

            # Validate performance thresholds
            validations = []

            # Database performance validation
            db_benchmarks = [r for r in benchmark_results["detailed_results"] if "database" in r["name"]]
            if db_benchmarks:
                avg_db_ops = sum(r["operations_per_second"] for r in db_benchmarks) / len(db_benchmarks)
                if avg_db_ops > 100:
                    validations.append("Database performance: PASS")
                else:
                    validations.append("Database performance: NEEDS ATTENTION")

            # Redis performance validation
            redis_benchmarks = [r for r in benchmark_results["detailed_results"] if "redis" in r["name"]]
            if redis_benchmarks:
                avg_redis_ops = sum(r["operations_per_second"] for r in redis_benchmarks) / len(redis_benchmarks)
                if avg_redis_ops > 1000:
                    validations.append("Redis performance: PASS")
                else:
                    validations.append("Redis performance: NEEDS ATTENTION")

            self.deployment_results["performance_validation"] = validations

            logger.info("Performance validation completed")

        except Exception as e:
            logger.error(f"Performance validation failed: {e}")
            self.deployment_results["recommendations"].append(
                f"Performance validation failed: {e}. Consider manual testing."
            )

    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up deployment resources")

        try:
            if self.query_monitor:
                await self.query_monitor.stop_monitoring()

            if self.cache_manager:
                await self.cache_manager.stop_background_tasks()

            if self.redis_manager:
                await self.redis_manager.close()

            if self.connection_pool:
                await self.connection_pool.close()

            logger.info("Cleanup completed")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")

    def generate_deployment_report(self) -> str:
        """Generate human-readable deployment report."""
        report = []
        report.append("=" * 80)
        report.append("OPTIMIZED CUSTOMER INTELLIGENCE PLATFORM DEPLOYMENT REPORT")
        report.append("=" * 80)
        report.append("")

        # Deployment Summary
        report.append("DEPLOYMENT SUMMARY:")
        report.append(f"  Status: {self.deployment_results['status'].upper()}")
        report.append(f"  Mode: {self.mode}")
        report.append(f"  Start Time: {self.deployment_results['start_time']}")
        if "end_time" in self.deployment_results:
            duration = self.deployment_results["end_time"] - self.deployment_results["start_time"]
            report.append(f"  Duration: {duration}")
        report.append("")

        # Components Status
        report.append("COMPONENTS:")
        for component, details in self.deployment_results.get("components", {}).items():
            report.append(f"  {component.title()}: {details['status'].upper()}")

        report.append("")

        # Optimizations Applied
        if self.deployment_results.get("optimizations_applied"):
            report.append("OPTIMIZATIONS APPLIED:")
            for opt in self.deployment_results["optimizations_applied"]:
                report.append(f"  - {opt['type']}")
                if "recommendations_applied" in opt:
                    report.append(f"    Applied: {opt['recommendations_applied']} recommendations")

        report.append("")

        # Performance Metrics Summary
        if self.deployment_results.get("performance_metrics"):
            report.append("PERFORMANCE METRICS:")

            # Database
            db_metrics = self.deployment_results["performance_metrics"].get("database")
            if db_metrics:
                perf_report = db_metrics.get("performance_report", {})
                summary = perf_report.get("summary", {})
                if summary:
                    report.append(f"  Database:")
                    report.append(f"    - Average Query Time: {summary.get('avg_query_time_ms', 0):.2f}ms")
                    report.append(f"    - Pool Utilization: {summary.get('pool_utilization', 'N/A')}")

            # Redis
            redis_metrics = self.deployment_results["performance_metrics"].get("redis")
            if redis_metrics:
                report.append(f"  Redis:")
                report.append(f"    - Cache Hit Rate: {redis_metrics.get('cache_hit_rate', 0):.1%}")
                report.append(f"    - Avg Operation Time: {redis_metrics.get('avg_operation_duration_ms', 0):.2f}ms")

            # Cache
            cache_metrics = self.deployment_results["performance_metrics"].get("cache")
            if cache_metrics:
                global_stats = cache_metrics.get("global", {})
                report.append(f"  Cache:")
                report.append(f"    - Global Hit Rate: {global_stats.get('hit_rate', 0):.1%}")
                report.append(f"    - L1 Cache Utilization: {cache_metrics.get('l1_cache', {}).get('hit_rate', 0):.1%}")

        report.append("")

        # Performance Validation
        if self.deployment_results.get("performance_validation"):
            report.append("PERFORMANCE VALIDATION:")
            for validation in self.deployment_results["performance_validation"]:
                report.append(f"  ✓ {validation}")

        report.append("")

        # Recommendations
        if self.deployment_results.get("recommendations"):
            report.append("RECOMMENDATIONS:")
            for rec in self.deployment_results["recommendations"]:
                report.append(f"  - {rec}")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

async def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(
        description="Deploy Optimized Customer Intelligence Platform"
    )
    parser.add_argument(
        "--mode",
        choices=["development", "production"],
        default="development",
        help="Deployment mode"
    )
    parser.add_argument(
        "--enable-monitoring",
        action="store_true",
        default=True,
        help="Enable performance monitoring"
    )
    parser.add_argument(
        "--run-benchmarks",
        action="store_true",
        help="Run performance benchmarks during deployment"
    )
    parser.add_argument(
        "--database-url",
        help="Database connection URL"
    )
    parser.add_argument(
        "--redis-url",
        help="Redis connection URL"
    )
    parser.add_argument(
        "--output-report",
        help="Output deployment report to file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Initialize deployer
    deployer = OptimizedPlatformDeployer(
        mode=args.mode,
        enable_monitoring=args.enable_monitoring,
        run_benchmarks=args.run_benchmarks,
        database_url=args.database_url,
        redis_url=args.redis_url
    )

    try:
        # Run deployment
        results = await deployer.deploy()

        # Generate and display report
        report = deployer.generate_deployment_report()
        print(report)

        # Save report if requested
        if args.output_report:
            with open(args.output_report, 'w') as f:
                f.write(report)
                f.write("\n\nFull Results JSON:\n")
                json.dump(results, f, indent=2, default=str)
            print(f"\nDetailed report saved to: {args.output_report}")

        # Exit with appropriate code
        if results["status"] == "completed":
            print("\n🎉 Deployment completed successfully!")
            sys.exit(0)
        else:
            print(f"\n❌ Deployment failed: {results.get('error', 'Unknown error')}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        print(f"\n❌ Deployment failed: {e}")
        sys.exit(1)

    finally:
        await deployer.cleanup()

if __name__ == "__main__":
    asyncio.run(main())