#!/usr/bin/env python3
"""
Security Validation Test Suite for Jorge's BI Dashboard System

This script conducts comprehensive security testing to validate system security
posture and compliance with security best practices.

SECURITY TESTING AREAS:
1. Authentication and Authorization
2. Input Validation and Sanitization
3. SQL Injection Protection
4. XSS Protection
5. Rate Limiting and DoS Protection
6. HTTPS and TLS Configuration
7. CORS Configuration
8. Data Leakage Prevention

Security Standards:
- OWASP Top 10 compliance
- Input validation on all parameters
- Proper authentication enforcement
- Rate limiting protection
- Secure headers implementation

Author: Claude Sonnet 4
Date: 2026-01-25
"""

import asyncio
import json
import sys
import base64
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Installing...")
    import os
    os.system("pip install httpx")
    import httpx

@dataclass
class SecurityTestResult:
    """Security test result."""
    test_name: str
    status: str  # PASS, FAIL, WARNING, SKIP
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    details: Dict[str, Any]
    recommendations: List[str]

class SecurityValidator:
    """Comprehensive security validation testing."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results: List[SecurityTestResult] = []

    async def run_security_tests(self) -> Dict[str, Any]:
        """Run comprehensive security validation tests."""
        print("🛡️ Security Validation Testing - Jorge's BI Dashboard System")
        print("=" * 80)

        security_tests = [
            ("Authentication Bypass Testing", self._test_authentication_bypass),
            ("Authorization Testing", self._test_authorization),
            ("SQL Injection Testing", self._test_sql_injection),
            ("XSS Protection Testing", self._test_xss_protection),
            ("Input Validation Testing", self._test_input_validation),
            ("Rate Limiting Testing", self._test_rate_limiting),
            ("Information Disclosure Testing", self._test_information_disclosure),
            ("HTTP Security Headers", self._test_security_headers),
            ("CORS Configuration", self._test_cors_configuration),
            ("File Upload Security", self._test_file_upload_security),
        ]

        for test_name, test_function in security_tests:
            print(f"\n🔒 {test_name}")
            print("-" * 60)

            try:
                await test_function()
                print(f"✅ {test_name} completed")
            except Exception as e:
                print(f"❌ {test_name} failed: {e}")
                self._add_security_result(
                    test_name, "FAIL", "HIGH", f"Test execution failed: {e}",
                    {"error": str(e)}, ["Investigate test execution failure"]
                )

        return await self._generate_security_report()

    async def _test_authentication_bypass(self):
        """Test authentication bypass vulnerabilities."""
        print("  🔑 Testing authentication bypass...")

        bypass_tests = [
            ("Direct endpoint access", "/api/bi/dashboard-kpis", {}),
            ("Admin endpoint access", "/api/bi/trigger-aggregation", {}),
            ("Sensitive data endpoint", "/api/bi/cache-analytics", {}),
            ("Real-time endpoint", "/api/bi/real-time-metrics", {}),
        ]

        bypass_successful = []
        properly_protected = []

        async with httpx.AsyncClient() as client:
            for test_name, endpoint, params in bypass_tests:
                try:
                    response = await client.get(f"{self.base_url}{endpoint}", params=params, timeout=10.0)

                    if response.status_code == 200:
                        # Successful bypass - security issue
                        bypass_successful.append({"endpoint": endpoint, "status_code": 200})
                        print(f"    ❌ {endpoint} - Authentication bypass successful")
                    elif response.status_code == 401:
                        # Properly protected
                        properly_protected.append({"endpoint": endpoint, "status_code": 401})
                        print(f"    ✅ {endpoint} - Properly protected")
                    elif response.status_code == 403:
                        # Forbidden - also good protection
                        properly_protected.append({"endpoint": endpoint, "status_code": 403})
                        print(f"    ✅ {endpoint} - Access forbidden (good)")
                    else:
                        print(f"    ⚠️ {endpoint} - Unexpected status: {response.status_code}")

                except Exception as e:
                    print(f"    ❌ {endpoint} - Test error: {e}")

        # Assess results
        if bypass_successful:
            self._add_security_result(
                "Authentication Bypass", "FAIL", "CRITICAL",
                f"Authentication bypass found on {len(bypass_successful)} endpoints",
                {"bypassed_endpoints": bypass_successful, "protected_endpoints": properly_protected},
                ["Implement proper authentication on all endpoints", "Review JWT implementation", "Add authentication middleware"]
            )
        else:
            self._add_security_result(
                "Authentication Bypass", "PASS", "LOW",
                "No authentication bypass vulnerabilities found",
                {"protected_endpoints": properly_protected},
                ["Continue monitoring authentication effectiveness"]
            )

    async def _test_authorization(self):
        """Test authorization and privilege escalation."""
        print("  👤 Testing authorization...")

        # Test with various malformed or crafted tokens
        auth_tests = [
            ("No token", None),
            ("Empty token", ""),
            ("Invalid token", "invalid-token"),
            ("Expired token", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MDk0NTkyMDB9.invalid"),
            ("Admin impersonation", "Bearer admin-token"),
            ("SQL injection in token", "'; DROP TABLE users; --"),
        ]

        authorization_issues = []

        async with httpx.AsyncClient() as client:
            for test_name, token in auth_tests:
                headers = {"Authorization": f"Bearer {token}"} if token else {}

                try:
                    response = await client.get(
                        f"{self.base_url}/api/bi/dashboard-kpis",
                        headers=headers,
                        timeout=10.0
                    )

                    if response.status_code == 200:
                        authorization_issues.append({"test": test_name, "token": token, "status": 200})
                        print(f"    ❌ {test_name} - Unauthorized access granted")
                    elif response.status_code in [401, 403]:
                        print(f"    ✅ {test_name} - Access properly denied")
                    else:
                        print(f"    ⚠️ {test_name} - Unexpected status: {response.status_code}")

                except Exception as e:
                    print(f"    ❌ {test_name} - Test error: {e}")

        if authorization_issues:
            self._add_security_result(
                "Authorization", "FAIL", "HIGH",
                f"Authorization bypass found with {len(authorization_issues)} token variations",
                {"authorization_issues": authorization_issues},
                ["Implement proper token validation", "Add role-based access control", "Validate token expiration"]
            )
        else:
            self._add_security_result(
                "Authorization", "PASS", "LOW",
                "Authorization working correctly",
                {},
                ["Continue monitoring token validation"]
            )

    async def _test_sql_injection(self):
        """Test SQL injection vulnerabilities."""
        print("  💉 Testing SQL injection...")

        # Common SQL injection payloads
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "' OR 1=1 --",
            "admin'--",
            "' OR 'x'='x",
            "'; EXEC xp_cmdshell('dir'); --",
            "' AND 1=CONVERT(int, CHAR(65)) --",
            "' OR (SELECT COUNT(*) FROM sysobjects) > 0 --"
        ]

        # Test endpoints that might interact with database
        test_endpoints = [
            ("/api/bi/dashboard-kpis", "location_id"),
            ("/api/bi/revenue-intelligence", "location_id"),
            ("/api/bi/bot-performance", "location_id"),
            ("/api/bi/predictive-insights", "location_id"),
            ("/api/bi/drill-down", "location_id"),
        ]

        sql_injection_found = []

        async with httpx.AsyncClient() as client:
            for endpoint, param_name in test_endpoints:
                for payload in sql_payloads:
                    params = {param_name: payload, "timeframe": "24h"}

                    try:
                        response = await client.get(
                            f"{self.base_url}{endpoint}",
                            params=params,
                            timeout=15.0
                        )

                        # Check for SQL injection indicators
                        response_text = response.text.lower()
                        error_indicators = [
                            "sql syntax error",
                            "mysql error",
                            "postgresql error",
                            "ora-",
                            "microsoft ole db provider",
                            "unclosed quotation mark",
                            "syntax error near",
                            "microsoft jet database",
                            "odbc drivers error"
                        ]

                        if any(indicator in response_text for indicator in error_indicators):
                            sql_injection_found.append({
                                "endpoint": endpoint,
                                "parameter": param_name,
                                "payload": payload,
                                "status_code": response.status_code,
                                "response_snippet": response_text[:200]
                            })
                            print(f"    ❌ SQL injection found: {endpoint} with payload '{payload[:20]}...'")

                        # Also check for unexpected successful responses
                        elif response.status_code == 200 and "internal server error" not in response_text:
                            print(f"    ⚠️ {endpoint} with '{payload[:20]}...' - Status 200 (investigate)")

                    except Exception as e:
                        # Timeouts or errors might indicate SQL injection impact
                        if "timeout" in str(e).lower():
                            sql_injection_found.append({
                                "endpoint": endpoint,
                                "parameter": param_name,
                                "payload": payload,
                                "error": "timeout",
                                "impact": "potential_dos"
                            })
                            print(f"    ❌ Timeout with payload '{payload[:20]}...' on {endpoint}")

        if sql_injection_found:
            self._add_security_result(
                "SQL Injection", "FAIL", "CRITICAL",
                f"SQL injection vulnerabilities found on {len(sql_injection_found)} tests",
                {"sql_injection_issues": sql_injection_found},
                [
                    "Use parameterized queries for all database interactions",
                    "Implement input validation and sanitization",
                    "Use ORM framework with SQL injection protection",
                    "Add database query logging and monitoring"
                ]
            )
        else:
            self._add_security_result(
                "SQL Injection", "PASS", "LOW",
                "No SQL injection vulnerabilities detected",
                {},
                ["Continue using parameterized queries", "Regular security testing"]
            )

    async def _test_xss_protection(self):
        """Test Cross-Site Scripting (XSS) protection."""
        print("  🕸️ Testing XSS protection...")

        # XSS payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<input autofocus onfocus=alert('XSS')>",
            "\"><script>alert('XSS')</script>",
            "<script>fetch('/api/bi/dashboard-kpis')</script>"
        ]

        # Test parameters that might be reflected in responses
        test_params = ["location_id", "timeframe", "components", "limit"]

        xss_vulnerabilities = []

        async with httpx.AsyncClient() as client:
            for payload in xss_payloads:
                for param in test_params:
                    params = {param: payload}

                    try:
                        response = await client.get(
                            f"{self.base_url}/api/bi/real-time-metrics",
                            params=params,
                            timeout=10.0
                        )

                        # Check if payload is reflected in response
                        if payload in response.text:
                            xss_vulnerabilities.append({
                                "parameter": param,
                                "payload": payload,
                                "endpoint": "/api/bi/real-time-metrics",
                                "reflected": True
                            })
                            print(f"    ❌ XSS vulnerability: {param} parameter reflects payload")

                    except Exception as e:
                        pass  # Continue with other tests

        # Test error pages for XSS
        try:
            response = await client.get(f"{self.base_url}/nonexistent?param=<script>alert('XSS')</script>")
            if "<script>" in response.text:
                xss_vulnerabilities.append({
                    "location": "404_error_page",
                    "payload": "<script>alert('XSS')</script>",
                    "reflected": True
                })
                print("    ❌ XSS vulnerability in 404 error page")
        except:
            pass

        if xss_vulnerabilities:
            self._add_security_result(
                "XSS Protection", "FAIL", "HIGH",
                f"XSS vulnerabilities found in {len(xss_vulnerabilities)} locations",
                {"xss_vulnerabilities": xss_vulnerabilities},
                [
                    "Implement output encoding for all user input",
                    "Use Content Security Policy (CSP) headers",
                    "Sanitize all input parameters",
                    "Validate and encode data in error pages"
                ]
            )
        else:
            self._add_security_result(
                "XSS Protection", "PASS", "LOW",
                "No XSS vulnerabilities detected",
                {},
                ["Continue input validation practices", "Implement CSP headers"]
            )

    async def _test_input_validation(self):
        """Test input validation and sanitization."""
        print("  📝 Testing input validation...")

        # Invalid input tests
        validation_tests = [
            ("Negative numbers", {"limit": "-1", "timeframe": "-24h"}),
            ("Large numbers", {"limit": "999999999", "offset": "999999999"}),
            ("Special characters", {"location_id": "!@#$%^&*()"}),
            ("Unicode injection", {"location_id": "\u0000\u0001\u0002"}),
            ("Path traversal", {"location_id": "../../../etc/passwd"}),
            ("Command injection", {"location_id": "; cat /etc/passwd"}),
            ("Format string", {"location_id": "%s%s%s%s"}),
            ("Buffer overflow attempt", {"location_id": "A" * 10000}),
            ("Null bytes", {"location_id": "test\x00admin"}),
            ("HTML tags", {"location_id": "<h1>Test</h1>"}),
        ]

        validation_issues = []

        async with httpx.AsyncClient() as client:
            for test_name, params in validation_tests:
                try:
                    response = await client.get(
                        f"{self.base_url}/api/bi/dashboard-kpis",
                        params=params,
                        timeout=10.0
                    )

                    # Check if server handled invalid input properly
                    if response.status_code == 500:
                        validation_issues.append({
                            "test": test_name,
                            "params": params,
                            "issue": "server_error_on_invalid_input",
                            "status_code": 500
                        })
                        print(f"    ❌ {test_name} - Server error (500) on invalid input")
                    elif response.status_code == 200:
                        # Might be accepting invalid input
                        validation_issues.append({
                            "test": test_name,
                            "params": params,
                            "issue": "invalid_input_accepted",
                            "status_code": 200
                        })
                        print(f"    ⚠️ {test_name} - Invalid input potentially accepted")
                    elif response.status_code in [400, 422]:
                        print(f"    ✅ {test_name} - Properly rejected with {response.status_code}")
                    else:
                        print(f"    ⚠️ {test_name} - Unexpected status: {response.status_code}")

                except Exception as e:
                    if "timeout" in str(e).lower():
                        validation_issues.append({
                            "test": test_name,
                            "params": params,
                            "issue": "timeout_on_invalid_input",
                            "error": str(e)
                        })
                        print(f"    ❌ {test_name} - Timeout (potential DoS)")

        if validation_issues:
            severity = "HIGH" if any(issue["issue"] == "server_error_on_invalid_input" for issue in validation_issues) else "MEDIUM"
            self._add_security_result(
                "Input Validation", "FAIL", severity,
                f"Input validation issues found in {len(validation_issues)} tests",
                {"validation_issues": validation_issues},
                [
                    "Implement comprehensive input validation",
                    "Add parameter type checking",
                    "Set reasonable limits on input length",
                    "Sanitize all user inputs",
                    "Return appropriate error codes for invalid input"
                ]
            )
        else:
            self._add_security_result(
                "Input Validation", "PASS", "LOW",
                "Input validation working correctly",
                {},
                ["Continue input validation practices"]
            )

    async def _test_rate_limiting(self):
        """Test rate limiting protection."""
        print("  🚦 Testing rate limiting...")

        # Test rapid requests to see if rate limiting kicks in
        rapid_requests = 50
        time_window = 10  # seconds

        rate_limit_triggered = False
        status_codes = []

        async with httpx.AsyncClient() as client:
            start_time = asyncio.get_event_loop().time()

            # Send rapid requests
            tasks = []
            for i in range(rapid_requests):
                task = client.get(f"{self.base_url}/api/bi/real-time-metrics", timeout=5.0)
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for response in responses:
                if isinstance(response, Exception):
                    status_codes.append("ERROR")
                else:
                    status_codes.append(response.status_code)
                    if response.status_code == 429:  # Too Many Requests
                        rate_limit_triggered = True

        # Analyze results
        success_codes = [code for code in status_codes if code in [200, 401]]
        error_codes = [code for code in status_codes if code == 429]
        other_codes = [code for code in status_codes if code not in [200, 401, 429, "ERROR"]]

        rate_limit_percentage = (len(error_codes) / len(status_codes)) * 100 if status_codes else 0

        print(f"    📊 Sent {rapid_requests} rapid requests")
        print(f"    📈 Success/Auth: {len(success_codes)}, Rate Limited: {len(error_codes)}, Other: {len(other_codes)}")
        print(f"    🚦 Rate Limit Triggered: {rate_limit_triggered}")

        if rate_limit_triggered:
            self._add_security_result(
                "Rate Limiting", "PASS", "LOW",
                f"Rate limiting active - {rate_limit_percentage:.1f}% of requests rate limited",
                {
                    "rapid_requests_sent": rapid_requests,
                    "rate_limited_responses": len(error_codes),
                    "rate_limit_percentage": rate_limit_percentage
                },
                ["Monitor rate limit thresholds", "Consider adaptive rate limiting"]
            )
        else:
            self._add_security_result(
                "Rate Limiting", "FAIL", "MEDIUM",
                "No rate limiting detected - potential DoS vulnerability",
                {
                    "rapid_requests_sent": rapid_requests,
                    "all_requests_processed": len(success_codes)
                },
                [
                    "Implement rate limiting on all API endpoints",
                    "Configure appropriate rate limit thresholds",
                    "Add rate limiting middleware",
                    "Consider using Redis for distributed rate limiting"
                ]
            )

    async def _test_information_disclosure(self):
        """Test for information disclosure vulnerabilities."""
        print("  📋 Testing information disclosure...")

        disclosure_issues = []

        async with httpx.AsyncClient() as client:
            # Test error pages for information disclosure
            test_urls = [
                "/api/bi/nonexistent-endpoint",
                "/api/bi/dashboard-kpis?invalid=parameter",
                "/api/bi/revenue-intelligence?timeframe=invalid",
            ]

            for url in test_urls:
                try:
                    response = await client.get(f"{self.base_url}{url}", timeout=10.0)

                    # Check for sensitive information in error responses
                    response_text = response.text.lower()
                    sensitive_info = [
                        "traceback",
                        "stack trace",
                        "internal server error",
                        "database",
                        "sql",
                        "password",
                        "secret",
                        "api_key",
                        "jwt_secret",
                        "connection string",
                        "file not found",
                        "/users/",
                        "c:\\",
                        "debug",
                    ]

                    found_info = [info for info in sensitive_info if info in response_text]
                    if found_info:
                        disclosure_issues.append({
                            "url": url,
                            "status_code": response.status_code,
                            "disclosed_info": found_info,
                            "response_snippet": response.text[:500]
                        })
                        print(f"    ❌ Information disclosure in {url}: {found_info}")

                except Exception as e:
                    pass

            # Test for debug endpoints
            debug_endpoints = [
                "/debug",
                "/api/debug",
                "/.env",
                "/config",
                "/status",
                "/health?debug=true",
            ]

            for endpoint in debug_endpoints:
                try:
                    response = await client.get(f"{self.base_url}{endpoint}", timeout=5.0)
                    if response.status_code == 200:
                        disclosure_issues.append({
                            "endpoint": endpoint,
                            "status_code": 200,
                            "issue": "debug_endpoint_accessible",
                            "response_length": len(response.content)
                        })
                        print(f"    ❌ Debug endpoint accessible: {endpoint}")
                except:
                    pass

        if disclosure_issues:
            severity = "HIGH" if any("password" in str(issue) or "secret" in str(issue) for issue in disclosure_issues) else "MEDIUM"
            self._add_security_result(
                "Information Disclosure", "FAIL", severity,
                f"Information disclosure found in {len(disclosure_issues)} locations",
                {"disclosure_issues": disclosure_issues},
                [
                    "Configure custom error pages",
                    "Remove debug information from production",
                    "Disable debug endpoints in production",
                    "Implement proper logging without sensitive data"
                ]
            )
        else:
            self._add_security_result(
                "Information Disclosure", "PASS", "LOW",
                "No information disclosure vulnerabilities found",
                {},
                ["Continue secure error handling practices"]
            )

    async def _test_security_headers(self):
        """Test HTTP security headers."""
        print("  🛡️ Testing security headers...")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/bi/real-time-metrics", timeout=10.0)
                headers = response.headers

                # Check for important security headers
                security_headers = {
                    "Content-Security-Policy": "CSP protection against XSS",
                    "X-Frame-Options": "Clickjacking protection",
                    "X-Content-Type-Options": "MIME type sniffing protection",
                    "Strict-Transport-Security": "HTTPS enforcement",
                    "X-XSS-Protection": "Browser XSS protection",
                    "Referrer-Policy": "Referrer information control",
                }

                missing_headers = []
                present_headers = []

                for header, description in security_headers.items():
                    if header in headers:
                        present_headers.append({"header": header, "value": headers[header], "description": description})
                        print(f"    ✅ {header}: {headers[header]}")
                    else:
                        missing_headers.append({"header": header, "description": description})
                        print(f"    ❌ Missing: {header}")

                # Check for insecure headers
                insecure_headers = []
                if "Server" in headers:
                    insecure_headers.append({"header": "Server", "value": headers["Server"], "issue": "server_disclosure"})
                    print(f"    ⚠️ Server header reveals: {headers['Server']}")

                if missing_headers:
                    self._add_security_result(
                        "Security Headers", "FAIL", "MEDIUM",
                        f"Missing {len(missing_headers)} important security headers",
                        {
                            "missing_headers": missing_headers,
                            "present_headers": present_headers,
                            "insecure_headers": insecure_headers
                        },
                        [
                            "Implement Content Security Policy (CSP)",
                            "Add X-Frame-Options to prevent clickjacking",
                            "Set X-Content-Type-Options to nosniff",
                            "Configure Strict-Transport-Security for HTTPS",
                            "Remove or obscure Server header information"
                        ]
                    )
                else:
                    self._add_security_result(
                        "Security Headers", "PASS", "LOW",
                        "All important security headers present",
                        {"present_headers": present_headers},
                        ["Continue monitoring security header implementation"]
                    )

            except Exception as e:
                self._add_security_result(
                    "Security Headers", "FAIL", "MEDIUM",
                    f"Failed to test security headers: {e}",
                    {"error": str(e)},
                    ["Ensure API endpoints are accessible for security testing"]
                )

    async def _test_cors_configuration(self):
        """Test CORS configuration."""
        print("  🌐 Testing CORS configuration...")

        async with httpx.AsyncClient() as client:
            # Test preflight request
            try:
                response = await client.options(
                    f"{self.base_url}/api/bi/dashboard-kpis",
                    headers={
                        "Origin": "https://malicious-site.com",
                        "Access-Control-Request-Method": "GET",
                        "Access-Control-Request-Headers": "authorization"
                    },
                    timeout=10.0
                )

                cors_headers = {
                    "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                    "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                    "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
                    "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials"),
                }

                cors_issues = []

                # Check for overly permissive CORS
                if cors_headers["Access-Control-Allow-Origin"] == "*":
                    cors_issues.append("Wildcard origin allows any domain")
                    print("    ❌ CORS allows any origin (*)")

                if cors_headers["Access-Control-Allow-Credentials"] == "true" and cors_headers["Access-Control-Allow-Origin"] == "*":
                    cors_issues.append("Credentials allowed with wildcard origin (security risk)")
                    print("    ❌ Credentials + wildcard origin (critical risk)")

                if cors_issues:
                    self._add_security_result(
                        "CORS Configuration", "FAIL", "MEDIUM",
                        "CORS configuration has security issues",
                        {"cors_headers": cors_headers, "issues": cors_issues},
                        [
                            "Restrict CORS origins to trusted domains only",
                            "Avoid wildcard origins in production",
                            "Review credentials policy with CORS"
                        ]
                    )
                else:
                    self._add_security_result(
                        "CORS Configuration", "PASS", "LOW",
                        "CORS configuration appears secure",
                        {"cors_headers": cors_headers},
                        ["Continue monitoring CORS configuration"]
                    )

            except Exception as e:
                self._add_security_result(
                    "CORS Configuration", "WARNING", "LOW",
                    f"Could not test CORS configuration: {e}",
                    {"error": str(e)},
                    ["Ensure CORS is properly configured"]
                )

    async def _test_file_upload_security(self):
        """Test file upload security (if applicable)."""
        print("  📁 Testing file upload security...")

        # Check if there are any file upload endpoints
        upload_endpoints = [
            "/api/bi/upload",
            "/api/upload",
            "/upload",
        ]

        upload_found = False

        async with httpx.AsyncClient() as client:
            for endpoint in upload_endpoints:
                try:
                    # Test with a simple POST to see if endpoint exists
                    response = await client.post(f"{self.base_url}{endpoint}", timeout=5.0)
                    if response.status_code != 404:
                        upload_found = True
                        print(f"    ⚠️ Upload endpoint found: {endpoint} (status: {response.status_code})")
                        # Would need to test actual file uploads here
                except:
                    pass

        if upload_found:
            self._add_security_result(
                "File Upload Security", "WARNING", "MEDIUM",
                "File upload endpoints detected - manual security review needed",
                {"detected_endpoints": upload_endpoints},
                [
                    "Implement file type validation",
                    "Scan uploaded files for malware",
                    "Limit file size and count",
                    "Store uploads outside web root",
                    "Validate file content, not just extension"
                ]
            )
        else:
            self._add_security_result(
                "File Upload Security", "PASS", "LOW",
                "No file upload endpoints detected",
                {},
                ["If adding file upload, implement security controls"]
            )

    def _add_security_result(self, test_name: str, status: str, severity: str,
                           description: str, details: Dict[str, Any], recommendations: List[str]):
        """Add a security test result."""
        result = SecurityTestResult(
            test_name=test_name,
            status=status,
            severity=severity,
            description=description,
            details=details,
            recommendations=recommendations
        )
        self.test_results.append(result)

    async def _generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        print("\n" + "=" * 80)
        print("🛡️ SECURITY VALIDATION REPORT")
        print("=" * 80)

        # Calculate overall statistics
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == "PASS"])
        failed_tests = len([r for r in self.test_results if r.status == "FAIL"])
        warning_tests = len([r for r in self.test_results if r.status == "WARNING"])

        # Security severity counts
        critical_issues = len([r for r in self.test_results if r.severity == "CRITICAL"])
        high_issues = len([r for r in self.test_results if r.severity == "HIGH"])
        medium_issues = len([r for r in self.test_results if r.severity == "MEDIUM"])
        low_issues = len([r for r in self.test_results if r.severity == "LOW"])

        print(f"Total Security Tests: {total_tests}")
        print(f"Passed: {passed_tests} | Failed: {failed_tests} | Warnings: {warning_tests}")
        print(f"Security Issues by Severity:")
        print(f"  🔴 Critical: {critical_issues}")
        print(f"  🟠 High: {high_issues}")
        print(f"  🟡 Medium: {medium_issues}")
        print(f"  🟢 Low: {low_issues}")

        # Security posture assessment
        security_score = self._calculate_security_score()
        print(f"\n🛡️ Security Posture Score: {security_score}/100")

        if security_score >= 90:
            posture = "🟢 EXCELLENT SECURITY"
        elif security_score >= 75:
            posture = "🟡 GOOD SECURITY"
        elif security_score >= 50:
            posture = "🟠 NEEDS IMPROVEMENT"
        else:
            posture = "🔴 CRITICAL SECURITY ISSUES"

        print(f"Overall Security Posture: {posture}")

        # Failed tests details
        if failed_tests > 0:
            print(f"\n❌ FAILED SECURITY TESTS ({failed_tests})")
            print("-" * 50)
            for result in self.test_results:
                if result.status == "FAIL":
                    print(f"🔴 {result.test_name} ({result.severity})")
                    print(f"   {result.description}")

        # Top recommendations
        print(f"\n💡 TOP SECURITY RECOMMENDATIONS")
        print("-" * 50)
        all_recommendations = []
        for result in self.test_results:
            if result.status in ["FAIL", "WARNING"]:
                all_recommendations.extend(result.recommendations)

        # Get unique recommendations, prioritizing by severity
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        for i, rec in enumerate(unique_recommendations[:10], 1):
            print(f"{i}. {rec}")

        print("\n" + "=" * 80)

        # Generate report data structure
        report = {
            "security_assessment": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "warning_tests": warning_tests,
                "security_score": security_score,
                "security_posture": posture
            },
            "severity_breakdown": {
                "critical": critical_issues,
                "high": high_issues,
                "medium": medium_issues,
                "low": low_issues
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "status": r.status,
                    "severity": r.severity,
                    "description": r.description,
                    "details": r.details,
                    "recommendations": r.recommendations
                }
                for r in self.test_results
            ],
            "top_recommendations": unique_recommendations[:10],
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

        return report

    def _calculate_security_score(self) -> float:
        """Calculate overall security score."""
        if not self.test_results:
            return 0.0

        # Base score from test pass rate
        pass_rate = len([r for r in self.test_results if r.status == "PASS"]) / len(self.test_results)
        base_score = pass_rate * 70  # 70% base from passing tests

        # Penalty for security issues by severity
        critical_penalty = len([r for r in self.test_results if r.severity == "CRITICAL"]) * 15
        high_penalty = len([r for r in self.test_results if r.severity == "HIGH"]) * 10
        medium_penalty = len([r for r in self.test_results if r.severity == "MEDIUM"]) * 5

        total_penalty = critical_penalty + high_penalty + medium_penalty
        final_score = max(0, base_score - total_penalty + 30)  # Add base 30 for partial credit

        return min(100, final_score)

async def main():
    """Main security validation execution."""
    print("🔒 Starting Security Validation Testing...")

    validator = SecurityValidator()

    try:
        report = await validator.run_security_tests()

        # Save security report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"security_validation_report_{timestamp}.json"

        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Security validation report saved: {report_filename}")
        print("🛡️ Security validation testing completed!")

        # Return appropriate exit code
        critical_issues = report["severity_breakdown"]["critical"]
        if critical_issues > 0:
            print(f"\n🔴 Critical security issues found! Address immediately.")
            return 2
        elif report["security_assessment"]["failed_tests"] > 0:
            print(f"\n🟡 Security improvements needed.")
            return 1
        else:
            print(f"\n🟢 Security validation passed!")
            return 0

    except Exception as e:
        print(f"\n❌ Security validation failed: {e}")
        return 3

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)