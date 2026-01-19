#!/usr/bin/env python3
"""
Locust Load Testing Script for Jorge's Revenue Acceleration Platform
====================================================================

Realistic distributed load testing with Locust for enterprise-scale validation.

Usage:
    # Web UI mode (recommended)
    locust -f locustfile_jorge_platform.py --host=http://localhost:8000

    # Headless mode
    locust -f locustfile_jorge_platform.py --host=http://localhost:8000 \
           --users 1000 --spawn-rate 50 --run-time 10m --headless

    # Distributed mode (master)
    locust -f locustfile_jorge_platform.py --master --expect-workers 4

    # Distributed mode (worker)
    locust -f locustfile_jorge_platform.py --worker --master-host=localhost

Load Scenarios:
1. Normal Business Operations (70% of traffic)
   - Pricing calculations
   - Analytics queries
   - Health checks

2. Peak Traffic Simulation (20% of traffic)
   - ROI report generation
   - Pricing optimization
   - Export operations

3. Admin Operations (10% of traffic)
   - Configuration updates
   - System monitoring

Performance Targets:
- Response Time: <100ms (95th percentile)
- Throughput: 10,000+ requests/minute
- Error Rate: <0.1%
- Concurrent Users: 1000+

Author: Claude Code Agent Swarm
Created: 2026-01-17
"""

import random
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask


class JorgePlatformUser(HttpUser):
    """
    Simulates a real estate agent/agency using Jorge's platform.

    Behavior mix based on real-world usage patterns:
    - Frequent: Pricing calculations, analytics views
    - Moderate: ROI reports, comparisons
    - Rare: Configuration changes, exports
    """

    # Realistic wait time between requests (1-5 seconds)
    wait_time = between(1, 5)

    def on_start(self):
        """Initialize user session"""
        self.location_id = "3xt4qayAh35BlDLaUv7P"
        self.user_id = f"locust_user_{uuid.uuid4().hex[:8]}"

        # Simulate authentication (in production, would use real JWT)
        self.auth_headers = {
            "Authorization": f"Bearer test_token_{self.user_id}",
            "Content-Type": "application/json"
        }

        # Track user metrics
        self.requests_made = 0
        self.session_start = time.time()

    @task(50)  # 50% of all requests - most common operation
    def calculate_pricing(self):
        """Calculate dynamic pricing for a lead"""
        lead_data = {
            "contact_id": f"contact_{uuid.uuid4().hex[:8]}",
            "location_id": self.location_id,
            "context": {
                "questions_answered": random.randint(0, 7),
                "engagement_score": random.uniform(0.3, 1.0),
                "source": random.choice(["website_form", "referral", "cold_call", "social_media"]),
                "budget": random.randint(200000, 2000000),
                "timeline": random.choice(["immediate", "30_days", "60_days", "90_days"]),
                "property_type": random.choice(["single_family", "condo", "multi_family", "commercial"]),
                "location_preference": random.choice(["urban", "suburban", "rural"])
            }
        }

        with self.client.post(
            "/api/pricing/calculate",
            json=lead_data,
            headers=self.auth_headers,
            catch_response=True,
            name="Pricing Calculate"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("success"):
                        response.success()
                    else:
                        response.failure(f"API returned error: {result.get('error')}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(20)  # 20% of requests - analytics viewing
    def view_pricing_analytics(self):
        """View pricing analytics dashboard"""
        days = random.choice([7, 14, 30, 60, 90])

        with self.client.get(
            f"/api/pricing/analytics/{self.location_id}?days={days}",
            headers=self.auth_headers,
            catch_response=True,
            name="Pricing Analytics"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("success"):
                        response.success()
                    else:
                        response.failure(f"Analytics error: {result.get('error')}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(15)  # 15% of requests - ROI reporting
    def generate_roi_report(self):
        """Generate comprehensive ROI report"""
        days = random.choice([30, 60, 90])
        include_projections = random.choice([True, False])

        with self.client.get(
            f"/api/pricing/roi-report/{self.location_id}?days={days}&include_projections={include_projections}",
            headers=self.auth_headers,
            catch_response=True,
            name="ROI Report"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("success"):
                        response.success()
                    else:
                        response.failure(f"ROI report error: {result.get('error')}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(10)  # 10% of requests - savings calculator
    def calculate_savings(self):
        """Use interactive savings calculator"""
        calc_data = {
            "leads_per_month": random.randint(50, 500),
            "messages_per_lead": random.uniform(3.0, 15.0),
            "human_hourly_rate": random.uniform(15.0, 50.0)
        }

        with self.client.post(
            "/api/pricing/savings-calculator",
            json=calc_data,
            headers=self.auth_headers,
            catch_response=True,
            name="Savings Calculator"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("success"):
                        response.success()
                    else:
                        response.failure(f"Savings calc error: {result.get('error')}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(3)  # 3% of requests - human vs AI comparison
    def view_human_vs_ai_comparison(self):
        """View human vs AI performance comparison"""
        with self.client.get(
            f"/api/pricing/human-vs-ai/{self.location_id}",
            headers=self.auth_headers,
            catch_response=True,
            name="Human vs AI Comparison"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("success"):
                        response.success()
                    else:
                        response.failure(f"Comparison error: {result.get('error')}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)  # 1% of requests - pricing optimization (admin operation)
    def optimize_pricing(self):
        """Run ML-powered pricing optimization"""
        with self.client.post(
            f"/api/pricing/optimize/{self.location_id}",
            headers=self.auth_headers,
            catch_response=True,
            name="Pricing Optimization"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("success"):
                        response.success()
                    else:
                        response.failure(f"Optimization error: {result.get('error')}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)  # 1% of requests - health check monitoring
    def health_check(self):
        """Check system health"""
        with self.client.get(
            "/api/pricing/health",
            catch_response=True,
            name="Health Check"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get("status") == "healthy":
                        response.success()
                    else:
                        response.failure(f"Service unhealthy: {result}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")


class PeakTrafficUser(HttpUser):
    """
    Simulates peak traffic scenarios (marketing campaigns, events).
    More aggressive request patterns with burst behavior.
    """

    wait_time = between(0.5, 2)  # Faster requests during peak

    def on_start(self):
        """Initialize peak traffic user"""
        self.location_id = "3xt4qayAh35BlDLaUv7P"
        self.user_id = f"peak_user_{uuid.uuid4().hex[:8]}"
        self.auth_headers = {
            "Authorization": f"Bearer test_token_{self.user_id}",
            "Content-Type": "application/json"
        }

    @task(60)
    def rapid_pricing_calculations(self):
        """Rapid successive pricing calculations"""
        # Simulate lead funnel - multiple leads processed quickly
        num_leads = random.randint(3, 8)

        for _ in range(num_leads):
            lead_data = {
                "contact_id": f"peak_contact_{uuid.uuid4().hex[:8]}",
                "location_id": self.location_id,
                "context": {
                    "questions_answered": random.randint(4, 7),  # Higher quality during peaks
                    "engagement_score": random.uniform(0.6, 1.0),
                    "source": "marketing_campaign",
                    "budget": random.randint(400000, 2000000),
                    "timeline": "immediate"
                }
            }

            self.client.post(
                "/api/pricing/calculate",
                json=lead_data,
                headers=self.auth_headers,
                name="Peak Pricing Calculate"
            )

    @task(30)
    def analytics_monitoring(self):
        """Frequent analytics checks during peak"""
        self.client.get(
            f"/api/pricing/analytics/{self.location_id}?days=7",
            headers=self.auth_headers,
            name="Peak Analytics"
        )

    @task(10)
    def quick_roi_checks(self):
        """Quick ROI validation"""
        self.client.get(
            f"/api/pricing/roi-report/{self.location_id}?days=30&include_projections=false",
            headers=self.auth_headers,
            name="Peak ROI Quick Check"
        )


# Event handlers for custom metrics and reporting

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    print("\n" + "="*80)
    print("Jorge's Revenue Acceleration Platform - Load Test Starting")
    print("="*80)
    print(f"Target Host: {environment.host}")
    print(f"Start Time: {datetime.now().isoformat()}")
    print("="*80 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops - generate summary report"""
    print("\n" + "="*80)
    print("Jorge's Revenue Acceleration Platform - Load Test Complete")
    print("="*80)
    print(f"End Time: {datetime.now().isoformat()}")

    stats = environment.stats

    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {stats.total.fail_ratio:.2%}")
    print(f"Average Response Time: {stats.total.avg_response_time:.1f}ms")
    print(f"Median Response Time: {stats.total.median_response_time:.1f}ms")
    print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95):.1f}ms")
    print(f"99th Percentile: {stats.total.get_response_time_percentile(0.99):.1f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.1f}ms")
    print(f"RPS (Total): {stats.total.total_rps:.1f}")
    print(f"RPS (Current): {stats.total.current_rps:.1f}")

    print("\n" + "="*80)
    print("Performance Assessment:")
    print("="*80)

    # Assess against targets
    p95 = stats.total.get_response_time_percentile(0.95)
    fail_rate = stats.total.fail_ratio

    if p95 <= 100 and fail_rate <= 0.001:
        print("✅ EXCELLENT: All performance targets met!")
    elif p95 <= 200 and fail_rate <= 0.01:
        print("✅ GOOD: Performance within acceptable range")
    elif p95 <= 500 and fail_rate <= 0.05:
        print("⚠️  ACCEPTABLE: Performance acceptable but needs optimization")
    else:
        print("❌ NEEDS ATTENTION: Performance below target, optimization required")

    print("\nPerformance Targets:")
    print(f"  - P95 Response Time: {'✅' if p95 <= 100 else '❌'} {p95:.1f}ms (target: <100ms)")
    print(f"  - Error Rate: {'✅' if fail_rate <= 0.001 else '❌'} {fail_rate:.3%} (target: <0.1%)")
    print(f"  - Throughput: {'✅' if stats.total.total_rps >= 166.67 else '❌'} {stats.total.total_rps:.1f} rps (target: >166.67 rps = 10,000/min)")

    print("="*80 + "\n")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track individual requests for custom metrics"""
    # Could add custom logging, metrics export, etc.
    pass


# Custom user classes for different load profiles
class SmokeTestUser(JorgePlatformUser):
    """Light load for smoke testing"""
    wait_time = between(2, 5)
    weight = 1


class NormalLoadUser(JorgePlatformUser):
    """Normal business traffic"""
    wait_time = between(1, 3)
    weight = 7


class PeakLoadUser(PeakTrafficUser):
    """Peak traffic simulation"""
    wait_time = between(0.5, 2)
    weight = 2


if __name__ == "__main__":
    import os
    os.system("locust -f locustfile_jorge_platform.py --host=http://localhost:8000")
