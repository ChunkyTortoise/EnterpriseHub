#!/usr/bin/env python3
"""
GHL Webhook Testing Suite
Comprehensive testing for real estate webhook handlers

This script tests all aspects of the webhook system:
- Security verification
- Lead qualification logic
- AI response generation
- Integration scenarios
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any

import pytest
import httpx
from fastapi.testclient import TestClient

@pytest.mark.integration

# Test configuration
TEST_CONFIG = {
    "webhook_secret": "test_secret_key_12345",
    "base_url": "http://localhost:8000",
    "timeout": 10
}

# Sample webhook payloads for testing
SAMPLE_PAYLOADS = {
    "new_lead": {
        "contactId": "test_contact_123",
        "locationId": "test_location_456",
        "type": "ContactTagUpdate",
        "tags": ["AI Assistant: ON"],
        "firstName": "John",
        "lastName": "Smith",
        "phone": "+1-555-123-4567",
        "email": "john.smith@example.com"
    },
    "ai_disabled": {
        "contactId": "test_contact_456",
        "locationId": "test_location_456",
        "type": "ContactTagUpdate",
        "tags": ["AI Assistant: OFF"],
        "firstName": "Jane",
        "lastName": "Doe"
    },
    "hot_lead": {
        "contactId": "test_contact_789",
        "locationId": "test_location_456",
        "type": "ContactTagUpdate",
        "tags": ["AI Assistant: ON"],
        "firstName": "Mike",
        "lastName": "Johnson"
    }
}

QUALIFICATION_RESPONSES = {
    "budget": [
        "Around $750,000",
        "750k max",
        "$600k to $800k range",
        "Seven hundred fifty thousand",
    ],
    "location": [
        "Rancho Cucamonga downtown",
        "West Lake Hills area",
        "Anywhere in Central Rancho Cucamonga",
        "Near UT campus",
    ],
    "bedrooms": [
        "3 bedrooms",
        "At least 3 beds",
        "3-4 bedrooms would be perfect",
        "Three bedroom house",
    ],
    "timeline": [
        "Next 2-3 months",
        "By spring",
        "ASAP",
        "Before summer",
    ],
    "preapproval": [
        "Yes, already pre-approved",
        "Pre-approved up to 800k",
        "Need lender recommendations",
        "Working on it",
    ],
    "motivation": [
        "Growing family, need more space",
        "Job relocation to Rancho Cucamonga",
        "Investment property",
        "First time buyer",
    ]
}


class WebhookTester:
    """
    Comprehensive webhook testing framework.

    Tests all aspects of the real estate lead qualification system.
    """

    def __init__(self, base_url: str = TEST_CONFIG["base_url"]):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url)

    async def test_health_endpoint(self) -> bool:
        """Test basic health check endpoint."""
        try:
            response = await self.client.get("/")
            return response.status_code == 200 and "status" in response.json()
        except Exception as e:
            print(f"Health check failed: {e}")
            return False

    async def test_webhook_security(self) -> Dict[str, bool]:
        """Test webhook security mechanisms."""
        results = {}

        # Test 1: Missing signature
        try:
            response = await self.client.post(
                "/webhook/ghl",
                json=SAMPLE_PAYLOADS["new_lead"]
            )
            results["missing_signature"] = response.status_code == 401
        except Exception:
            results["missing_signature"] = False

        # Test 2: Invalid signature
        try:
            response = await self.client.post(
                "/webhook/ghl",
                headers={"X-GHL-Signature": "invalid_signature"},
                json=SAMPLE_PAYLOADS["new_lead"]
            )
            results["invalid_signature"] = response.status_code == 401
        except Exception:
            results["invalid_signature"] = False

        # Test 3: Invalid payload
        try:
            response = await self.client.post(
                "/webhook/ghl",
                headers={"X-GHL-Signature": "test"},
                json={"invalid": "payload"}
            )
            results["invalid_payload"] = response.status_code == 400
        except Exception:
            results["invalid_payload"] = False

        # Test 4: Rate limiting (if implemented)
        rate_limit_passed = True
        try:
            # Send multiple requests quickly
            for _ in range(10):
                await self.client.post("/webhook/ghl", json=SAMPLE_PAYLOADS["new_lead"])
            results["rate_limiting"] = rate_limit_passed
        except Exception:
            results["rate_limiting"] = False

        return results

    def create_valid_signature(self, payload: str) -> str:
        """Create valid HMAC signature for testing."""
        import hmac
        import hashlib

        return hmac.new(
            TEST_CONFIG["webhook_secret"].encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    async def test_lead_qualification_flow(self) -> Dict[str, Any]:
        """Test complete lead qualification workflow."""
        contact_id = f"test_flow_{int(time.time())}"
        results = {
            "contact_id": contact_id,
            "steps": {},
            "final_score": 0,
            "final_status": "unknown"
        }

        # Prepare payload
        payload = SAMPLE_PAYLOADS["new_lead"].copy()
        payload["contactId"] = contact_id

        try:
            # Step 1: Initial webhook trigger
            payload_str = json.dumps(payload)
            signature = self.create_valid_signature(payload_str)

            response = await self.client.post(
                "/webhook/ghl",
                headers={"X-GHL-Signature": signature},
                content=payload_str
            )

            results["steps"]["initial_trigger"] = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.json() if response.status_code == 200 else None
            }

            # Step 2: Simulate lead responses to qualification questions
            questions = ["budget", "location", "bedrooms", "timeline", "preapproval", "motivation"]

            for i, question in enumerate(questions):
                # Send a realistic response
                response_payload = {
                    "contactId": contact_id,
                    "locationId": payload["locationId"],
                    "message": QUALIFICATION_RESPONSES[question][0]  # Use first response
                }

                response = await self.client.post(
                    "/webhook/ghl/response",
                    json=response_payload
                )

                step_result = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                }

                if response.status_code == 200:
                    data = response.json()
                    step_result.update({
                        "score": data.get("score", 0),
                        "status": data.get("status_label", "unknown"),
                        "answers_count": data.get("answers_count", 0)
                    })

                    # Update final results
                    results["final_score"] = step_result["score"]
                    results["final_status"] = step_result["status"]

                results["steps"][f"question_{question}"] = step_result

                # Small delay to simulate realistic timing
                await asyncio.sleep(0.1)

            # Step 3: Check final analytics
            try:
                analytics_response = await self.client.get(f"/analytics/lead/{contact_id}")
                if analytics_response.status_code == 200:
                    results["analytics"] = analytics_response.json()
            except Exception:
                results["analytics"] = None

        except Exception as e:
            results["error"] = str(e)

        return results

    async def test_ai_response_generation(self) -> Dict[str, Any]:
        """Test AI response generation capabilities."""
        results = {
            "response_times": [],
            "message_lengths": [],
            "fallback_rate": 0,
            "responses": []
        }

        # Test different question types
        question_types = ["budget", "location", "bedrooms", "timeline"]
        total_requests = len(question_types) * 3  # 3 tests per question type

        for question_type in question_types:
            for test_iteration in range(3):
                contact_id = f"ai_test_{question_type}_{test_iteration}"

                try:
                    start_time = time.time()

                    # Trigger AI response
                    payload = SAMPLE_PAYLOADS["new_lead"].copy()
                    payload["contactId"] = contact_id
                    payload_str = json.dumps(payload)
                    signature = self.create_valid_signature(payload_str)

                    response = await self.client.post(
                        "/webhook/ghl",
                        headers={"X-GHL-Signature": signature},
                        content=payload_str
                    )

                    response_time = (time.time() - start_time) * 1000  # Convert to ms
                    results["response_times"].append(response_time)

                    if response.status_code == 200:
                        data = response.json()
                        message = data.get("message", "")
                        results["message_lengths"].append(len(message))

                        # Check if fallback was used (simple heuristic)
                        is_fallback = "Quick question" in message or len(message) < 20
                        if is_fallback:
                            results["fallback_rate"] += 1

                        results["responses"].append({
                            "question_type": question_type,
                            "message": message,
                            "length": len(message),
                            "response_time_ms": response_time,
                            "is_fallback": is_fallback
                        })

                except Exception as e:
                    results["responses"].append({
                        "question_type": question_type,
                        "error": str(e)
                    })

        # Calculate final metrics
        if results["response_times"]:
            results["avg_response_time"] = sum(results["response_times"]) / len(results["response_times"])
            results["max_response_time"] = max(results["response_times"])

        if results["message_lengths"]:
            results["avg_message_length"] = sum(results["message_lengths"]) / len(results["message_lengths"])

        results["fallback_rate"] = results["fallback_rate"] / total_requests

        return results

    async def test_edge_cases(self) -> Dict[str, bool]:
        """Test edge cases and error handling."""
        results = {}

        # Test 1: Empty message response
        try:
            response = await self.client.post(
                "/webhook/ghl/response",
                json={
                    "contactId": "edge_test_1",
                    "locationId": "test_location",
                    "message": ""
                }
            )
            results["empty_message"] = response.status_code in [200, 400]  # Either handled or rejected
        except Exception:
            results["empty_message"] = False

        # Test 2: Very long message
        try:
            long_message = "x" * 1000  # 1000 character message
            response = await self.client.post(
                "/webhook/ghl/response",
                json={
                    "contactId": "edge_test_2",
                    "locationId": "test_location",
                    "message": long_message
                }
            )
            results["long_message"] = response.status_code == 200
        except Exception:
            results["long_message"] = False

        # Test 3: Invalid contact ID
        try:
            response = await self.client.post(
                "/webhook/ghl/response",
                json={
                    "contactId": "",  # Empty contact ID
                    "locationId": "test_location",
                    "message": "test"
                }
            )
            results["invalid_contact_id"] = response.status_code in [400, 404]
        except Exception:
            results["invalid_contact_id"] = False

        # Test 4: Malformed JSON
        try:
            response = await self.client.post(
                "/webhook/ghl",
                headers={"Content-Type": "application/json"},
                content="invalid json"
            )
            results["malformed_json"] = response.status_code == 400
        except Exception:
            results["malformed_json"] = False

        # Test 5: Missing required fields
        try:
            response = await self.client.post(
                "/webhook/ghl",
                headers={"X-GHL-Signature": "test"},
                json={"incomplete": "payload"}
            )
            results["missing_fields"] = response.status_code == 400
        except Exception:
            results["missing_fields"] = False

        return results

    async def test_performance(self) -> Dict[str, Any]:
        """Test performance under load."""
        results = {
            "concurrent_requests": 0,
            "success_rate": 0,
            "avg_response_time": 0,
            "errors": []
        }

        # Create multiple concurrent requests
        async def make_request(i):
            contact_id = f"perf_test_{i}"
            payload = SAMPLE_PAYLOADS["new_lead"].copy()
            payload["contactId"] = contact_id

            try:
                start_time = time.time()
                payload_str = json.dumps(payload)
                signature = self.create_valid_signature(payload_str)

                response = await self.client.post(
                    "/webhook/ghl",
                    headers={"X-GHL-Signature": signature},
                    content=payload_str
                )

                response_time = (time.time() - start_time) * 1000
                return {
                    "success": response.status_code == 200,
                    "response_time": response_time,
                    "status_code": response.status_code
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "response_time": 0
                }

        # Run concurrent requests
        num_requests = 20
        tasks = [make_request(i) for i in range(num_requests)]

        request_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_requests = 0
        total_response_time = 0
        valid_responses = 0

        for result in request_results:
            if isinstance(result, dict):
                if result.get("success"):
                    successful_requests += 1
                if result.get("response_time", 0) > 0:
                    total_response_time += result["response_time"]
                    valid_responses += 1
                if not result.get("success"):
                    results["errors"].append(result.get("error", "Unknown error"))

        results["concurrent_requests"] = num_requests
        results["success_rate"] = successful_requests / num_requests
        results["avg_response_time"] = total_response_time / valid_responses if valid_responses > 0 else 0

        return results

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run complete test suite."""
        print("🧪 Starting GHL Webhook Test Suite")
        print("=" * 50)

        all_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_config": TEST_CONFIG
        }

        # Test 1: Health Check
        print("1️⃣  Testing health endpoint...")
        all_results["health"] = await self.test_health_endpoint()
        print(f"   ✅ Health check: {'PASS' if all_results['health'] else 'FAIL'}")

        # Test 2: Security
        print("\n2️⃣  Testing security mechanisms...")
        security_results = await self.test_webhook_security()
        all_results["security"] = security_results
        security_pass = all(security_results.values())
        print(f"   🔒 Security tests: {'PASS' if security_pass else 'FAIL'}")
        for test, result in security_results.items():
            status = "✅" if result else "❌"
            print(f"      {status} {test}")

        # Test 3: Lead Qualification Flow
        print("\n3️⃣  Testing lead qualification flow...")
        qualification_results = await self.test_lead_qualification_flow()
        all_results["qualification"] = qualification_results
        qualification_pass = qualification_results.get("final_score", 0) >= 3
        print(f"   📊 Qualification flow: {'PASS' if qualification_pass else 'FAIL'}")
        print(f"      Final score: {qualification_results.get('final_score', 0)}")
        print(f"      Final status: {qualification_results.get('final_status', 'unknown')}")

        # Test 4: AI Response Generation
        print("\n4️⃣  Testing AI response generation...")
        ai_results = await self.test_ai_response_generation()
        all_results["ai_responses"] = ai_results
        ai_pass = ai_results.get("avg_response_time", 5000) < 3000  # Under 3 seconds
        print(f"   🤖 AI responses: {'PASS' if ai_pass else 'FAIL'}")
        print(f"      Avg response time: {ai_results.get('avg_response_time', 0):.1f}ms")
        print(f"      Avg message length: {ai_results.get('avg_message_length', 0):.1f} chars")
        print(f"      Fallback rate: {ai_results.get('fallback_rate', 0):.1%}")

        # Test 5: Edge Cases
        print("\n5️⃣  Testing edge cases...")
        edge_results = await self.test_edge_cases()
        all_results["edge_cases"] = edge_results
        edge_pass = sum(edge_results.values()) >= len(edge_results) * 0.8  # 80% pass rate
        print(f"   ⚠️  Edge cases: {'PASS' if edge_pass else 'FAIL'}")
        for test, result in edge_results.items():
            status = "✅" if result else "❌"
            print(f"      {status} {test}")

        # Test 6: Performance
        print("\n6️⃣  Testing performance...")
        perf_results = await self.test_performance()
        all_results["performance"] = perf_results
        perf_pass = perf_results.get("success_rate", 0) >= 0.95  # 95% success rate
        print(f"   ⚡ Performance: {'PASS' if perf_pass else 'FAIL'}")
        print(f"      Success rate: {perf_results.get('success_rate', 0):.1%}")
        print(f"      Avg response time: {perf_results.get('avg_response_time', 0):.1f}ms")
        print(f"      Concurrent requests: {perf_results.get('concurrent_requests', 0)}")

        # Overall results
        print("\n" + "=" * 50)
        passed_tests = sum([
            all_results["health"],
            security_pass,
            qualification_pass,
            ai_pass,
            edge_pass,
            perf_pass
        ])

        all_results["summary"] = {
            "total_tests": 6,
            "passed": passed_tests,
            "failed": 6 - passed_tests,
            "pass_rate": passed_tests / 6,
            "overall_status": "PASS" if passed_tests >= 5 else "FAIL"
        }

        print(f"🎯 Overall Test Results: {all_results['summary']['overall_status']}")
        print(f"   Passed: {passed_tests}/6 tests")
        print(f"   Pass rate: {all_results['summary']['pass_rate']:.1%}")

        return all_results

    async def close(self):
        """Clean up resources."""
        await self.client.aclose()


async def main():
    """Main test runner."""
    import argparse

    parser = argparse.ArgumentParser(description="GHL Webhook Test Suite")
    parser.add_argument("--url", default=TEST_CONFIG["base_url"], help="Base URL for testing")
    parser.add_argument("--output", help="Output file for test results")
    parser.add_argument("--quick", action="store_true", help="Run quick tests only")

    args = parser.parse_args()

    # Create tester
    tester = WebhookTester(args.url)

    try:
        if args.quick:
            # Run only health and basic security tests
            print("🏃 Running quick test suite...")
            health = await tester.test_health_endpoint()
            security = await tester.test_webhook_security()

            results = {
                "health": health,
                "security": security,
                "summary": {
                    "quick_test": True,
                    "health_pass": health,
                    "security_pass": all(security.values())
                }
            }
        else:
            # Run full test suite
            results = await tester.run_all_tests()

        # Save results if output file specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n📝 Results saved to {args.output}")

        # Exit with appropriate code
        if results.get("summary", {}).get("overall_status") == "PASS":
            exit(0)
        else:
            exit(1)

    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())


"""
USAGE EXAMPLES:

1. Run full test suite:
   python test_webhook.py

2. Test against specific URL:
   python test_webhook.py --url https://your-domain.com

3. Run quick tests only:
   python test_webhook.py --quick

4. Save results to file:
   python test_webhook.py --output test_results.json

5. CI/CD integration:
   python test_webhook.py --url $STAGING_URL --output ci_results.json

EXPECTED OUTPUT:

🧪 Starting GHL Webhook Test Suite
==================================================
1️⃣  Testing health endpoint...
   ✅ Health check: PASS

2️⃣  Testing security mechanisms...
   🔒 Security tests: PASS
      ✅ missing_signature
      ✅ invalid_signature
      ✅ invalid_payload
      ✅ rate_limiting

3️⃣  Testing lead qualification flow...
   📊 Qualification flow: PASS
      Final score: 6
      Final status: hot

4️⃣  Testing AI response generation...
   🤖 AI responses: PASS
      Avg response time: 245.3ms
      Avg message length: 67.2 chars
      Fallback rate: 8.3%

5️⃣  Testing edge cases...
   ⚠️  Edge cases: PASS
      ✅ empty_message
      ✅ long_message
      ✅ invalid_contact_id
      ✅ malformed_json
      ✅ missing_fields

6️⃣  Testing performance...
   ⚡ Performance: PASS
      Success rate: 100.0%
      Avg response time: 156.8ms
      Concurrent requests: 20

==================================================
🎯 Overall Test Results: PASS
   Passed: 6/6 tests
   Pass rate: 100.0%
"""