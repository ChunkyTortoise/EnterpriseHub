#!/usr/bin/env python3
"""
Test ML Scoring API Endpoints
Comprehensive testing script for Phase 4B ML scoring API implementation.

Features tested:
- Individual lead scoring endpoint
- Batch lead scoring endpoint
- Health check endpoints
- Model status endpoint
- Authentication and error handling
- Performance benchmarking (<50ms target)
"""

import asyncio
import aiohttp
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import statistics


@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    response_time_ms: float
    status_code: int
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None


class MLScoringAPITester:
    """Comprehensive ML Scoring API testing suite"""

    def __init__(self, base_url: str = "http://localhost:8000", auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.results: List[TestResult] = []

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all API tests and return summary"""
        print("🚀 Starting ML Scoring API Test Suite")
        print(f"Base URL: {self.base_url}")
        print(f"Authentication: {'Enabled' if self.auth_token else 'Disabled'}")
        print("=" * 60)

        async with aiohttp.ClientSession() as session:
            # Test 1: Health Check
            await self.test_health_check(session)

            # Test 2: Model Status
            await self.test_model_status(session)

            # Test 3: Individual Lead Scoring
            await self.test_individual_lead_scoring(session)

            # Test 4: Batch Lead Scoring
            await self.test_batch_lead_scoring(session)

            # Test 5: Lead Score Retrieval
            await self.test_lead_score_retrieval(session)

            # Test 6: Performance Benchmarking
            await self.test_performance_benchmarking(session)

            # Test 7: Error Handling
            await self.test_error_handling(session)

        return self.generate_test_summary()

    async def test_health_check(self, session: aiohttp.ClientSession):
        """Test health check endpoint"""
        print("\n🔍 Testing Health Check Endpoint...")

        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}/api/v1/ml/health") as response:
                response_time = (time.time() - start_time) * 1000
                response_data = await response.json()

                self.results.append(TestResult(
                    test_name="Health Check",
                    success=response.status == 200,
                    response_time_ms=response_time,
                    status_code=response.status,
                    response_data=response_data
                ))

                if response.status == 200:
                    print(f"✅ Health check passed ({response_time:.1f}ms)")
                    print(f"   Status: {response_data.get('status', 'unknown')}")
                    print(f"   ML Model: {response_data.get('ml_model_status', 'unknown')}")
                    print(f"   Cache: {response_data.get('cache_status', 'unknown')}")
                else:
                    print(f"❌ Health check failed: {response.status}")

        except Exception as e:
            self.results.append(TestResult(
                test_name="Health Check",
                success=False,
                response_time_ms=(time.time() - start_time) * 1000,
                status_code=0,
                error_message=str(e)
            ))
            print(f"❌ Health check error: {str(e)}")

    async def test_model_status(self, session: aiohttp.ClientSession):
        """Test ML model status endpoint"""
        print("\n🔍 Testing Model Status Endpoint...")

        if not self.auth_token:
            print("⏭️  Skipping model status test (no auth token)")
            return

        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}

        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}/api/v1/ml/model/status", headers=headers) as response:
                response_time = (time.time() - start_time) * 1000
                response_data = await response.json()

                self.results.append(TestResult(
                    test_name="Model Status",
                    success=response.status == 200,
                    response_time_ms=response_time,
                    status_code=response.status,
                    response_data=response_data
                ))

                if response.status == 200:
                    print(f"✅ Model status retrieved ({response_time:.1f}ms)")
                    print(f"   Model: {response_data.get('model_name', 'unknown')}")
                    print(f"   Available: {response_data.get('is_available', False)}")
                    print(f"   Accuracy: {response_data.get('accuracy', 'N/A')}")
                else:
                    print(f"❌ Model status failed: {response.status}")

        except Exception as e:
            self.results.append(TestResult(
                test_name="Model Status",
                success=False,
                response_time_ms=(time.time() - start_time) * 1000,
                status_code=0,
                error_message=str(e)
            ))
            print(f"❌ Model status error: {str(e)}")

    async def test_individual_lead_scoring(self, session: aiohttp.ClientSession):
        """Test individual lead scoring endpoint"""
        print("\n🔍 Testing Individual Lead Scoring...")

        if not self.auth_token:
            print("⏭️  Skipping lead scoring test (no auth token)")
            return

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}"
        } if self.auth_token else {"Content-Type": "application/json"}

        # Create test lead data
        test_lead = {
            "lead_id": f"test_{uuid.uuid4().hex[:8]}",
            "lead_name": "Sarah Johnson",
            "email": "sarah.johnson@email.com",
            "phone": "+1-555-123-4567",
            "message_content": "Hi, I'm looking for a 3-bedroom house in downtown area with a budget around $400,000. I need to move by next month. Can you help me find something?",
            "source": "website_contact_form",
            "response_time_hours": 2.5,
            "message_length": 150,
            "questions_asked": 2,
            "price_mentioned": True,
            "timeline_mentioned": True,
            "location_mentioned": True,
            "financing_mentioned": False,
            "family_mentioned": False,
            "budget_range": "$350,000 - $450,000",
            "property_type": "house",
            "bedrooms": 3,
            "location_preference": "downtown",
            "timeline_urgency": "next_month",
            "previous_interactions": 0,
            "referral_source": "google_search",
            "include_explanations": True,
            "timeout_ms": 5000
        }

        start_time = time.time()
        try:
            async with session.post(
                f"{self.base_url}/api/v1/ml/score",
                headers=headers,
                json=test_lead
            ) as response:
                response_time = (time.time() - start_time) * 1000
                response_data = await response.json()

                success = response.status == 200 and response_time < 100  # <100ms target

                self.results.append(TestResult(
                    test_name="Individual Lead Scoring",
                    success=success,
                    response_time_ms=response_time,
                    status_code=response.status,
                    response_data=response_data
                ))

                if response.status == 200:
                    score = response_data.get('ml_score', 0)
                    classification = response_data.get('classification', 'unknown')
                    confidence = response_data.get('ml_confidence', 0)
                    source = response_data.get('score_source', 'unknown')

                    print(f"✅ Lead scored successfully ({response_time:.1f}ms)")
                    print(f"   Score: {score:.1f}% ({classification})")
                    print(f"   Confidence: {confidence:.2f}")
                    print(f"   Source: {source}")
                    print(f"   Commission Est: ${response_data.get('estimated_commission', 0):,.2f}")

                    # Performance check
                    if response_time > 50:
                        print(f"⚠️  Performance warning: {response_time:.1f}ms > 50ms target")
                    else:
                        print(f"🚀 Performance excellent: {response_time:.1f}ms < 50ms target")

                else:
                    print(f"❌ Lead scoring failed: {response.status}")
                    print(f"   Error: {response_data.get('detail', 'Unknown error')}")

        except Exception as e:
            self.results.append(TestResult(
                test_name="Individual Lead Scoring",
                success=False,
                response_time_ms=(time.time() - start_time) * 1000,
                status_code=0,
                error_message=str(e)
            ))
            print(f"❌ Lead scoring error: {str(e)}")

    async def test_batch_lead_scoring(self, session: aiohttp.ClientSession):
        """Test batch lead scoring endpoint"""
        print("\n🔍 Testing Batch Lead Scoring...")

        if not self.auth_token:
            print("⏭️  Skipping batch scoring test (no auth token)")
            return

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}"
        } if self.auth_token else {"Content-Type": "application/json"}

        # Create test batch data (5 leads)
        batch_request = {
            "leads": [
                {
                    "lead_id": f"batch_test_{i}_{uuid.uuid4().hex[:6]}",
                    "lead_name": f"Test Lead {i+1}",
                    "email": f"test{i+1}@example.com",
                    "phone": f"+1-555-000-{i+1:04d}",
                    "message_content": f"Test message from lead {i+1} with {10 + i*5} words about buying property.",
                    "source": "batch_test",
                    "message_length": 10 + i*5,
                    "questions_asked": i % 3,
                    "price_mentioned": i % 2 == 0,
                    "timeline_mentioned": i % 3 == 0,
                    "budget_range": f"${200 + i*50}k - ${250 + i*50}k",
                    "bedrooms": 2 + (i % 3),
                    "include_explanations": False  # Faster processing
                }
                for i in range(5)
            ],
            "parallel_processing": True,
            "include_summary": True,
            "timeout_ms": 15000
        }

        start_time = time.time()
        try:
            async with session.post(
                f"{self.base_url}/api/v1/ml/batch-score",
                headers=headers,
                json=batch_request
            ) as response:
                response_time = (time.time() - start_time) * 1000
                response_data = await response.json()

                success = response.status == 200

                self.results.append(TestResult(
                    test_name="Batch Lead Scoring",
                    success=success,
                    response_time_ms=response_time,
                    status_code=response.status,
                    response_data=response_data
                ))

                if response.status == 200:
                    total_leads = response_data.get('total_leads', 0)
                    successful = response_data.get('successful_scores', 0)
                    failed = response_data.get('failed_scores', 0)
                    avg_score = response_data.get('average_score', 0)
                    throughput = response_data.get('throughput_scores_per_second', 0)

                    print(f"✅ Batch scoring completed ({response_time:.1f}ms)")
                    print(f"   Total: {total_leads}, Success: {successful}, Failed: {failed}")
                    print(f"   Average Score: {avg_score:.1f}%")
                    print(f"   Throughput: {throughput:.1f} scores/sec")

                    if successful == total_leads:
                        print("🎯 All leads scored successfully!")
                    else:
                        print(f"⚠️  {failed} leads failed to score")

                else:
                    print(f"❌ Batch scoring failed: {response.status}")

        except Exception as e:
            self.results.append(TestResult(
                test_name="Batch Lead Scoring",
                success=False,
                response_time_ms=(time.time() - start_time) * 1000,
                status_code=0,
                error_message=str(e)
            ))
            print(f"❌ Batch scoring error: {str(e)}")

    async def test_lead_score_retrieval(self, session: aiohttp.ClientSession):
        """Test lead score retrieval endpoint"""
        print("\n🔍 Testing Lead Score Retrieval...")

        if not self.auth_token:
            print("⏭️  Skipping score retrieval test (no auth token)")
            return

        headers = {"Authorization": f"Bearer {self.auth_token}"} if self.auth_token else {}

        # Try to retrieve a non-existent lead (should return 404)
        test_lead_id = f"nonexistent_{uuid.uuid4().hex[:8]}"

        start_time = time.time()
        try:
            async with session.get(
                f"{self.base_url}/api/v1/ml/score/{test_lead_id}",
                headers=headers
            ) as response:
                response_time = (time.time() - start_time) * 1000
                response_data = await response.json() if response.content_type == 'application/json' else {}

                # Expect 404 for non-existent lead
                success = response.status == 404

                self.results.append(TestResult(
                    test_name="Lead Score Retrieval",
                    success=success,
                    response_time_ms=response_time,
                    status_code=response.status,
                    response_data=response_data
                ))

                if response.status == 404:
                    print(f"✅ Score retrieval correctly returned 404 ({response_time:.1f}ms)")
                elif response.status == 200:
                    print(f"⚠️  Unexpectedly found score for non-existent lead")
                else:
                    print(f"❌ Score retrieval failed: {response.status}")

        except Exception as e:
            self.results.append(TestResult(
                test_name="Lead Score Retrieval",
                success=False,
                response_time_ms=(time.time() - start_time) * 1000,
                status_code=0,
                error_message=str(e)
            ))
            print(f"❌ Score retrieval error: {str(e)}")

    async def test_performance_benchmarking(self, session: aiohttp.ClientSession):
        """Test API performance with multiple requests"""
        print("\n🔍 Testing Performance Benchmarking...")

        if not self.auth_token:
            print("⏭️  Skipping performance test (no auth token)")
            return

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}"
        } if self.auth_token else {"Content-Type": "application/json"}

        # Run 10 concurrent requests to test performance
        test_leads = []
        for i in range(10):
            test_leads.append({
                "lead_id": f"perf_test_{i}_{uuid.uuid4().hex[:6]}",
                "lead_name": f"Performance Test {i+1}",
                "email": f"perf{i+1}@test.com",
                "message_content": "Quick performance test message",
                "source": "performance_test",
                "include_explanations": False,  # Faster processing
                "timeout_ms": 3000
            })

        start_time = time.time()
        response_times = []

        try:
            # Send concurrent requests
            tasks = []
            for lead in test_leads:
                task = session.post(
                    f"{self.base_url}/api/v1/ml/score",
                    headers=headers,
                    json=lead
                )
                tasks.append(task)

            # Wait for all requests to complete
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            total_time = (time.time() - start_time) * 1000

            # Process responses
            successful_requests = 0
            for response in responses:
                if isinstance(response, Exception):
                    continue

                if response.status == 200:
                    successful_requests += 1
                    # Note: We can't easily measure individual response times
                    # in this concurrent setup, so we'll estimate
                    response_times.append(total_time / len(test_leads))

            # Calculate performance metrics
            if response_times:
                avg_response_time = statistics.mean(response_times)
                min_response_time = min(response_times)
                max_response_time = max(response_times)
                throughput = (successful_requests / total_time) * 1000  # requests per second

                success = avg_response_time < 100 and successful_requests >= 8  # 80% success rate

                self.results.append(TestResult(
                    test_name="Performance Benchmarking",
                    success=success,
                    response_time_ms=avg_response_time,
                    status_code=200,
                    response_data={
                        "successful_requests": successful_requests,
                        "total_requests": len(test_leads),
                        "avg_response_time": avg_response_time,
                        "min_response_time": min_response_time,
                        "max_response_time": max_response_time,
                        "throughput_per_second": throughput
                    }
                ))

                print(f"✅ Performance test completed")
                print(f"   Successful: {successful_requests}/{len(test_leads)}")
                print(f"   Avg Response: {avg_response_time:.1f}ms")
                print(f"   Range: {min_response_time:.1f}ms - {max_response_time:.1f}ms")
                print(f"   Throughput: {throughput:.1f} requests/sec")

                if avg_response_time < 50:
                    print("🚀 Excellent performance: <50ms average")
                elif avg_response_time < 100:
                    print("👍 Good performance: <100ms average")
                else:
                    print("⚠️  Performance needs improvement: >100ms average")

            else:
                print("❌ Performance test failed: No successful responses")

        except Exception as e:
            self.results.append(TestResult(
                test_name="Performance Benchmarking",
                success=False,
                response_time_ms=(time.time() - start_time) * 1000,
                status_code=0,
                error_message=str(e)
            ))
            print(f"❌ Performance test error: {str(e)}")

    async def test_error_handling(self, session: aiohttp.ClientSession):
        """Test error handling with invalid requests"""
        print("\n🔍 Testing Error Handling...")

        if not self.auth_token:
            print("⏭️  Skipping error handling test (no auth token)")
            return

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_token}"
        } if self.auth_token else {"Content-Type": "application/json"}

        # Test invalid request data
        invalid_lead = {
            "lead_id": "",  # Invalid empty lead_id
            "lead_name": "",  # Invalid empty name
            "email": "invalid-email",  # Invalid email format
            "phone": "123",  # Invalid phone format
        }

        start_time = time.time()
        try:
            async with session.post(
                f"{self.base_url}/api/v1/ml/score",
                headers=headers,
                json=invalid_lead
            ) as response:
                response_time = (time.time() - start_time) * 1000
                response_data = await response.json()

                # Expect 422 for validation errors
                success = response.status == 422

                self.results.append(TestResult(
                    test_name="Error Handling",
                    success=success,
                    response_time_ms=response_time,
                    status_code=response.status,
                    response_data=response_data
                ))

                if response.status == 422:
                    print(f"✅ Error handling correctly returned 422 ({response_time:.1f}ms)")
                    print(f"   Validation errors detected and handled properly")
                else:
                    print(f"❌ Unexpected status for invalid data: {response.status}")

        except Exception as e:
            self.results.append(TestResult(
                test_name="Error Handling",
                success=False,
                response_time_ms=(time.time() - start_time) * 1000,
                status_code=0,
                error_message=str(e)
            ))
            print(f"❌ Error handling test error: {str(e)}")

    def generate_test_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - successful_tests

        # Calculate performance metrics
        response_times = [r.response_time_ms for r in self.results if r.response_time_ms > 0]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0

        # Performance targets
        performance_target_met = avg_response_time < 100  # <100ms overall target
        ml_target_met = any(
            r.test_name == "Individual Lead Scoring" and r.success and r.response_time_ms < 50
            for r in self.results
        )

        summary = {
            "test_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": (successful_tests / max(total_tests, 1)) * 100
            },
            "performance_metrics": {
                "avg_response_time_ms": avg_response_time,
                "min_response_time_ms": min_response_time,
                "max_response_time_ms": max_response_time,
                "performance_target_met": performance_target_met,
                "ml_scoring_target_met": ml_target_met
            },
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "response_time_ms": r.response_time_ms,
                    "status_code": r.status_code,
                    "error_message": r.error_message
                }
                for r in self.results
            ],
            "timestamp": datetime.utcnow().isoformat()
        }

        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {summary['test_summary']['success_rate']:.1f}%")
        print()
        print("Performance Metrics:")
        print(f"  Average Response Time: {avg_response_time:.1f}ms")
        print(f"  Response Time Range: {min_response_time:.1f}ms - {max_response_time:.1f}ms")
        print(f"  Performance Target (<100ms): {'✅ MET' if performance_target_met else '❌ MISSED'}")
        print(f"  ML Scoring Target (<50ms): {'✅ MET' if ml_target_met else '❌ MISSED'}")
        print()

        # Individual test results
        for result in self.results:
            status = "✅" if result.success else "❌"
            print(f"{status} {result.test_name}: {result.response_time_ms:.1f}ms (HTTP {result.status_code})")

        return summary


async def main():
    """Main test execution"""
    print("🚀 ML Scoring API Test Suite - Phase 4B")
    print("Testing Jorge's Real Estate AI ML Scoring API")
    print()

    # Configuration
    base_url = "http://localhost:8000"  # Adjust as needed
    auth_token = None  # Add JWT token if available

    # Note about authentication
    if not auth_token:
        print("⚠️  No authentication token provided.")
        print("   Some tests will be skipped.")
        print("   To test authenticated endpoints, set auth_token variable.")
        print()

    # Initialize tester
    tester = MLScoringAPITester(base_url=base_url, auth_token=auth_token)

    # Run tests
    try:
        summary = await tester.run_all_tests()

        # Save results to file
        with open("ml_api_test_results.json", "w") as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"\n📁 Test results saved to: ml_api_test_results.json")

        # Exit with appropriate code
        success_rate = summary["test_summary"]["success_rate"]
        exit_code = 0 if success_rate >= 80 else 1  # 80% success threshold

        print(f"\n🏁 Test Suite Complete - Exit Code: {exit_code}")
        return exit_code

    except Exception as e:
        print(f"\n❌ Test Suite Failed: {str(e)}")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)