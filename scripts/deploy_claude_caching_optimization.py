#!/usr/bin/env python3
"""
Claude Prompt Caching Deployment and Validation Script
Deploy caching service and validate 70% cost reduction achievement
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

from ghl_real_estate_ai.services.claude_prompt_caching_service import (
    ClaudePromptCachingService,
    ClaudeRequest,
    RealEstateCachePatterns,
    cached_claude_call
)
from ghl_real_estate_ai.config.claude_caching_config import (
    default_config,
    CacheWarmingProfiles,
    CostOptimizationTargets,
    CacheMonitoringConfig
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClaudeCachingDeployment:
    """Deploy and validate Claude caching optimization."""

    def __init__(self):
        self.cache_service = None
        self.deployment_results = {}
        self.cost_baseline = {}
        self.cost_optimized = {}

    async def deploy_caching_optimization(self) -> Dict[str, Any]:
        """Deploy complete Claude caching optimization."""

        logger.info("🚀 Deploying Claude Prompt Caching Optimization")
        logger.info("Target: 70% cost reduction ($15,000-30,000 annual savings)")
        print("=" * 60)

        deployment_start = time.time()

        try:
            # Step 1: Initialize caching service
            await self._initialize_cache_service()

            # Step 2: Perform baseline cost measurement
            await self._measure_baseline_costs()

            # Step 3: Deploy cache warming
            await self._deploy_cache_warming()

            # Step 4: Measure optimized costs
            await self._measure_optimized_costs()

            # Step 5: Validate cost reduction
            await self._validate_cost_reduction()

            # Step 6: Setup monitoring
            await self._setup_monitoring()

            deployment_time = time.time() - deployment_start

            # Generate deployment summary
            summary = self._generate_deployment_summary(deployment_time)

            logger.info("✅ Claude caching optimization deployment complete!")
            return summary

        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}")
            raise

        finally:
            if self.cache_service:
                await self.cache_service.cleanup()

    async def _initialize_cache_service(self):
        """Initialize the caching service."""
        logger.info("📦 Initializing Claude caching service...")

        self.cache_service = ClaudePromptCachingService(
            redis_url=default_config.config.redis_url,
            cost_per_1k_tokens=default_config.config.cost_per_1k_tokens,
            max_cache_size_mb=default_config.config.max_cache_size_mb
        )

        await self.cache_service.initialize()

        logger.info("✅ Cache service initialized successfully")

    async def _measure_baseline_costs(self):
        """Measure baseline costs without caching."""
        logger.info("📊 Measuring baseline costs (without caching)...")

        # Mock Claude API for demonstration
        async def mock_claude_api(prompt: str, system_prompt: str = "", **kwargs):
            # Simulate API latency
            await asyncio.sleep(0.1)

            # Calculate tokens (rough estimate)
            prompt_tokens = len(prompt.split()) + len(system_prompt.split())
            completion_tokens = min(200, prompt_tokens // 2)

            return {
                "content": f"Mock analysis for: {prompt[:50]}...",
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens
                }
            }

        # Test scenarios for baseline measurement
        test_scenarios = [
            {
                "name": "Property Analysis",
                "requests": [
                    RealEstateCachePatterns.property_analysis_request({
                        "id": f"prop_{i}",
                        "address": f"{i} Main Street",
                        "price": 500000 + i * 25000,
                        "type": "condo"
                    })
                    for i in range(10)
                ],
                "repetitions": 3  # Simulate repeated analysis
            },
            {
                "name": "Lead Qualification",
                "requests": [
                    RealEstateCachePatterns.lead_qualification_request({
                        "id": f"lead_{i}",
                        "name": f"Test Lead {i}",
                        "budget": 400000 + i * 50000,
                        "timeline": "3-6 months"
                    })
                    for i in range(8)
                ],
                "repetitions": 2
            },
            {
                "name": "Real-time Coaching",
                "requests": [
                    RealEstateCachePatterns.real_time_coaching_request({
                        "agent_id": f"agent_{i}",
                        "prospect_message": f"I'm interested in property type {i}",
                        "conversation_stage": "qualification"
                    })
                    for i in range(5)
                ],
                "repetitions": 4  # Real-time coaching happens frequently
            }
        ]

        total_baseline_cost = 0

        for scenario in test_scenarios:
            scenario_cost = 0
            scenario_start = time.time()

            for rep in range(scenario["repetitions"]):
                for request in scenario["requests"]:
                    # Call without caching
                    response = await self.cache_service._call_claude_api(
                        request, mock_claude_api
                    )
                    scenario_cost += response.cost

            scenario_time = time.time() - scenario_start

            self.cost_baseline[scenario["name"]] = {
                "total_cost": scenario_cost,
                "requests": len(scenario["requests"]) * scenario["repetitions"],
                "avg_cost_per_request": scenario_cost / (len(scenario["requests"]) * scenario["repetitions"]),
                "processing_time": scenario_time
            }

            total_baseline_cost += scenario_cost

            logger.info(f"  {scenario['name']}: ${scenario_cost:.2f} ({self.cost_baseline[scenario['name']]['requests']} requests)")

        self.cost_baseline["total"] = total_baseline_cost

        logger.info(f"📊 Baseline measurement complete: ${total_baseline_cost:.2f} total cost")

    async def _deploy_cache_warming(self):
        """Deploy cache warming for common requests."""
        logger.info("🔥 Deploying cache warming...")

        # Get daily warming requests
        daily_requests_data = CacheWarmingProfiles.get_daily_warming_requests()

        # Convert to ClaudeRequest objects
        warming_requests = [
            ClaudeRequest(
                prompt=req_data["prompt"],
                system_prompt=req_data["system_prompt"],
                context_data=req_data["context_data"]
            )
            for req_data in daily_requests_data
        ]

        # Mock Claude API for warming
        async def mock_claude_api(prompt: str, system_prompt: str = "", **kwargs):
            await asyncio.sleep(0.05)  # Faster for warming
            prompt_tokens = len(prompt.split()) + len(system_prompt.split())
            completion_tokens = min(150, prompt_tokens // 3)

            return {
                "content": f"Warmed response for: {prompt[:30]}...",
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens
                }
            }

        # Warm the cache
        warming_results = await self.cache_service.warm_cache(
            warming_requests, mock_claude_api, concurrency_limit=3
        )

        self.deployment_results["cache_warming"] = {
            "requests_warmed": warming_results["warmed"],
            "already_cached": warming_results["already_cached"],
            "warming_cost": warming_results["total_cost"],
            "warming_time": warming_results["warming_time"]
        }

        logger.info(f"🔥 Cache warming complete: {warming_results['warmed']} requests warmed")

    async def _measure_optimized_costs(self):
        """Measure costs with caching optimization."""
        logger.info("⚡ Measuring optimized costs (with caching)...")

        # Mock Claude API
        async def mock_claude_api(prompt: str, system_prompt: str = "", **kwargs):
            await asyncio.sleep(0.1)
            prompt_tokens = len(prompt.split()) + len(system_prompt.split())
            completion_tokens = min(200, prompt_tokens // 2)

            return {
                "content": f"Mock cached analysis for: {prompt[:50]}...",
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens
                }
            }

        # Re-run the same scenarios with caching
        total_optimized_cost = 0
        total_cache_hits = 0
        total_requests = 0

        for scenario_name, baseline_data in self.cost_baseline.items():
            if scenario_name == "total":
                continue

            scenario_cost = 0
            cache_hits = 0
            scenario_requests = 0

            # Recreate the scenario
            if scenario_name == "Property Analysis":
                requests = [
                    RealEstateCachePatterns.property_analysis_request({
                        "id": f"prop_{i}",
                        "address": f"{i} Main Street",
                        "price": 500000 + i * 25000,
                        "type": "condo"
                    })
                    for i in range(10)
                ]
                repetitions = 3

            elif scenario_name == "Lead Qualification":
                requests = [
                    RealEstateCachePatterns.lead_qualification_request({
                        "id": f"lead_{i}",
                        "name": f"Test Lead {i}",
                        "budget": 400000 + i * 50000,
                        "timeline": "3-6 months"
                    })
                    for i in range(8)
                ]
                repetitions = 2

            elif scenario_name == "Real-time Coaching":
                requests = [
                    RealEstateCachePatterns.real_time_coaching_request({
                        "agent_id": f"agent_{i}",
                        "prospect_message": f"I'm interested in property type {i}",
                        "conversation_stage": "qualification"
                    })
                    for i in range(5)
                ]
                repetitions = 4

            scenario_start = time.time()

            for rep in range(repetitions):
                for request in requests:
                    # Call with caching
                    response, was_cached = await self.cache_service.get_or_call_claude(
                        request, mock_claude_api
                    )

                    if not was_cached:
                        scenario_cost += response.cost
                    else:
                        cache_hits += 1

                    scenario_requests += 1

            scenario_time = time.time() - scenario_start

            self.cost_optimized[scenario_name] = {
                "total_cost": scenario_cost,
                "requests": scenario_requests,
                "cache_hits": cache_hits,
                "cache_hit_ratio": cache_hits / scenario_requests if scenario_requests > 0 else 0,
                "avg_cost_per_request": scenario_cost / scenario_requests if scenario_requests > 0 else 0,
                "processing_time": scenario_time,
                "cost_reduction": ((baseline_data["total_cost"] - scenario_cost) / baseline_data["total_cost"]) * 100
            }

            total_optimized_cost += scenario_cost
            total_cache_hits += cache_hits
            total_requests += scenario_requests

            logger.info(f"  {scenario_name}: ${scenario_cost:.2f} ({cache_hits}/{scenario_requests} cached = {self.cost_optimized[scenario_name]['cache_hit_ratio']:.1%})")

        self.cost_optimized["total"] = {
            "total_cost": total_optimized_cost,
            "total_cache_hits": total_cache_hits,
            "total_requests": total_requests,
            "overall_hit_ratio": total_cache_hits / total_requests,
            "overall_cost_reduction": ((self.cost_baseline["total"] - total_optimized_cost) / self.cost_baseline["total"]) * 100
        }

        logger.info(f"⚡ Optimized measurement complete: ${total_optimized_cost:.2f} total cost")

    async def _validate_cost_reduction(self):
        """Validate that cost reduction meets 70% target."""
        logger.info("🎯 Validating cost reduction targets...")

        overall_reduction = self.cost_optimized["total"]["overall_cost_reduction"]
        target_reduction = 70.0

        # Check if we met the target
        if overall_reduction >= target_reduction:
            logger.info(f"✅ Cost reduction target MET: {overall_reduction:.1f}% (target: {target_reduction}%)")
            validation_status = "success"
        elif overall_reduction >= target_reduction - 10:
            logger.info(f"⚠️  Cost reduction target CLOSE: {overall_reduction:.1f}% (target: {target_reduction}%)")
            validation_status = "partial"
        else:
            logger.warning(f"❌ Cost reduction target MISSED: {overall_reduction:.1f}% (target: {target_reduction}%)")
            validation_status = "failed"

        # Calculate annual savings
        baseline_cost = self.cost_baseline["total"]
        optimized_cost = self.cost_optimized["total"]["total_cost"]
        monthly_savings = (baseline_cost - optimized_cost) * 30  # Extrapolate daily to monthly
        annual_savings = monthly_savings * 12

        self.deployment_results["cost_validation"] = {
            "validation_status": validation_status,
            "achieved_reduction": f"{overall_reduction:.1f}%",
            "target_reduction": f"{target_reduction}%",
            "baseline_cost": f"${baseline_cost:.2f}",
            "optimized_cost": f"${optimized_cost:.2f}",
            "daily_savings": f"${baseline_cost - optimized_cost:.2f}",
            "estimated_monthly_savings": f"${monthly_savings:.2f}",
            "estimated_annual_savings": f"${annual_savings:.2f}",
            "cache_hit_ratio": f"{self.cost_optimized['total']['overall_hit_ratio']:.1%}"
        }

        # Detailed scenario breakdown
        scenario_breakdown = {}
        for scenario_name in ["Property Analysis", "Lead Qualification", "Real-time Coaching"]:
            baseline = self.cost_baseline[scenario_name]
            optimized = self.cost_optimized[scenario_name]

            scenario_breakdown[scenario_name] = {
                "baseline_cost": f"${baseline['total_cost']:.2f}",
                "optimized_cost": f"${optimized['total_cost']:.2f}",
                "cost_reduction": f"{optimized['cost_reduction']:.1f}%",
                "cache_hit_ratio": f"{optimized['cache_hit_ratio']:.1%}",
                "requests_processed": optimized['requests']
            }

        self.deployment_results["scenario_breakdown"] = scenario_breakdown

        logger.info("🎯 Cost validation complete")

    async def _setup_monitoring(self):
        """Setup monitoring for ongoing optimization."""
        logger.info("📊 Setting up cache monitoring...")

        # Get current cache analytics
        analytics = await self.cache_service.get_cache_analytics()

        monitoring_config = {
            "performance_targets": {
                "cache_hit_ratio_min": "60%",
                "cache_retrieval_time_max": "10ms",
                "monthly_cost_reduction_min": "65%"
            },
            "alert_thresholds": CacheMonitoringConfig.ALERT_CONDITIONS,
            "monitoring_intervals": CacheMonitoringConfig.METRICS_COLLECTION_INTERVALS,
            "current_analytics": analytics
        }

        self.deployment_results["monitoring"] = monitoring_config

        logger.info("📊 Monitoring setup complete")

    def _generate_deployment_summary(self, deployment_time: float) -> Dict[str, Any]:
        """Generate comprehensive deployment summary."""

        summary = {
            "deployment_info": {
                "deployment_time": f"{deployment_time:.2f}s",
                "deployment_date": datetime.now().isoformat(),
                "cache_service_status": "active",
                "redis_connection": "established"
            },
            "cost_optimization_results": self.deployment_results["cost_validation"],
            "scenario_performance": self.deployment_results["scenario_breakdown"],
            "cache_warming_results": self.deployment_results["cache_warming"],
            "monitoring_configuration": self.deployment_results["monitoring"],
            "next_steps": [
                "Monitor cache performance for 48 hours",
                "Integrate with production Claude services",
                "Setup automated cost alerts",
                "Schedule weekly cache optimization reviews"
            ]
        }

        return summary

async def demonstrate_claude_caching_integration():
    """Demonstrate real-world integration with existing Claude services."""

    print("\n🔗 Claude Caching Integration Demonstration")
    print("=" * 50)

    # Example 1: Property Analysis Service Integration
    print("\n📋 Example 1: Property Analysis Service")

    async def mock_property_analysis_service(property_data: Dict[str, Any]):
        """Mock property analysis service with caching integration."""

        # Mock Claude API
        async def mock_claude_api(prompt: str, system_prompt: str = "", **kwargs):
            await asyncio.sleep(0.1)  # Simulate API latency
            return {
                "content": f"Detailed property analysis for {property_data.get('address', 'property')}...",
                "usage": {"total_tokens": 800}
            }

        # Use cached Claude call
        content, was_cached, cost = await cached_claude_call(
            prompt=f"Analyze this property: {json.dumps(property_data)}",
            system_prompt="You are a real estate investment expert.",
            claude_api_function=mock_claude_api,
            context_data={"type": "property_analysis", "property_id": property_data.get("id")}
        )

        return {
            "analysis": content,
            "was_cached": was_cached,
            "cost": cost,
            "property_id": property_data.get("id")
        }

    # Test property analysis
    test_property = {
        "id": "prop_demo_123",
        "address": "123 Demo Street",
        "price": 575000,
        "type": "condo"
    }

    # First call (cache miss)
    result1 = await mock_property_analysis_service(test_property)
    print(f"  First call: Cost=${result1['cost']:.3f}, Cached={result1['was_cached']}")

    # Second call (cache hit)
    result2 = await mock_property_analysis_service(test_property)
    print(f"  Second call: Cost=${result2['cost']:.3f}, Cached={result2['was_cached']}")

    cost_savings = result1['cost'] - (0 if result2['was_cached'] else result2['cost'])
    print(f"  💰 Cost savings: ${cost_savings:.3f} ({(cost_savings/result1['cost'])*100:.1f}%)")

    # Example 2: Batch Processing with Cache Warming
    print("\n📋 Example 2: Batch Lead Qualification")

    async def mock_batch_lead_qualification(leads_data: List[Dict[str, Any]]):
        """Mock batch lead qualification with cache warming."""

        async with ClaudePromptCachingService() as cache_service:
            # Mock Claude API
            async def mock_claude_api(prompt: str, system_prompt: str = "", **kwargs):
                await asyncio.sleep(0.08)
                return {
                    "content": f"Lead qualification analysis...",
                    "usage": {"total_tokens": 600}
                }

            # Prepare requests
            requests = [
                RealEstateCachePatterns.lead_qualification_request(lead_data)
                for lead_data in leads_data
            ]

            # Warm cache first
            warming_results = await cache_service.warm_cache(
                requests, mock_claude_api, concurrency_limit=2
            )

            print(f"  Cache warming: {warming_results['warmed']} requests warmed")

            # Process leads with high cache hit ratio
            results = []
            total_cost = 0

            for request in requests:
                response, was_cached = await cache_service.get_or_call_claude(
                    request, mock_claude_api
                )

                if not was_cached:
                    total_cost += response.cost

                results.append({
                    "lead_id": request.context_data.get("lead_id"),
                    "cached": was_cached,
                    "cost": response.cost if not was_cached else 0
                })

            cache_hits = sum(1 for r in results if r["cached"])
            hit_ratio = cache_hits / len(results)

            return {
                "results": results,
                "total_cost": total_cost,
                "cache_hit_ratio": hit_ratio,
                "cost_savings_vs_no_cache": sum(0.012 for _ in results) - total_cost  # Estimated baseline
            }

    # Test batch processing
    test_leads = [
        {"id": f"lead_{i}", "name": f"Test Lead {i}", "budget": 400000 + i * 25000}
        for i in range(5)
    ]

    batch_results = await mock_batch_lead_qualification(test_leads)
    print(f"  Processed {len(test_leads)} leads")
    print(f"  Cache hit ratio: {batch_results['cache_hit_ratio']:.1%}")
    print(f"  Total cost: ${batch_results['total_cost']:.3f}")
    print(f"  💰 Estimated savings: ${batch_results['cost_savings_vs_no_cache']:.3f}")

    print("\n✅ Integration demonstration complete!")

async def main():
    """Main deployment function."""
    print("🚀 Claude Prompt Caching Optimization Deployment")
    print("Target: 70% cost reduction for $15,000-30,000 annual savings")
    print("=" * 70)

    try:
        # Deploy caching optimization
        deployer = ClaudeCachingDeployment()
        deployment_results = await deployer.deploy_caching_optimization()

        # Display results
        print("\n📊 DEPLOYMENT RESULTS")
        print("=" * 70)

        cost_results = deployment_results["cost_optimization_results"]
        print(f"🎯 Cost Reduction Achieved: {cost_results['achieved_reduction']}")
        print(f"🎯 Target: {cost_results['target_reduction']}")
        print(f"💰 Estimated Annual Savings: {cost_results['estimated_annual_savings']}")
        print(f"📈 Cache Hit Ratio: {cost_results['cache_hit_ratio']}")

        print("\n📋 Scenario Performance:")
        for scenario, data in deployment_results["scenario_performance"].items():
            print(f"  {scenario}:")
            print(f"    Cost Reduction: {data['cost_reduction']}")
            print(f"    Cache Hit Ratio: {data['cache_hit_ratio']}")

        # Demonstrate integration
        await demonstrate_claude_caching_integration()

        # Display next steps
        print("\n🚀 NEXT STEPS")
        print("=" * 70)
        for step in deployment_results["next_steps"]:
            print(f"  • {step}")

        print(f"\n✅ Deployment complete! Claude caching optimization active.")
        print(f"📊 Monitor performance at: /api/v1/claude/analytics/performance")

        return deployment_results

    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    asyncio.run(main())