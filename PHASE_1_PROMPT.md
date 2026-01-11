# PHASE 1: Critical Foundation - Infrastructure + Quality

## Context
You are implementing Phase 1 of the coordinated agent swarm findings for EnterpriseHub GHL Real Estate AI platform. This phase addresses CRITICAL infrastructure security issues and test failures that prevent production stability. Agent analysis revealed hardcoded secrets (Grade: C → A needed) and 17/19 failing webhook tests that could cause $1000s/month in SMS overcharges.

## Your Mission
Execute infrastructure hardening and critical test fixes to establish a secure, stable foundation for all subsequent optimizations.

**Timeline:** Weeks 1-2 | **Priority:** CRITICAL | **Risk Mitigation:** Production security + integration stability

## Critical Tasks

### 🚨 Infrastructure Security (16 hours)
**Files to modify:**
- `/docker-compose.production.yml` (remove hardcoded passwords)
- Railway environment configuration
- `/nginx.conf` (add 2nd NGINX instance config)
- PostgreSQL replication setup

**Specific Actions:**
1. **Remove hardcoded secrets** from docker-compose.production.yml:
   - Lines 134-136: Replace `POSTGRES_PASSWORD=password` with Railway env vars
   - All database credentials → environment variable references
   - Implement secret rotation policy documentation

2. **PostgreSQL High Availability:**
   - Set up read replica with replication lag monitoring
   - Configure automatic failover procedures
   - Document RTO/RPO requirements

3. **Load Balancer Setup:**
   - Deploy 2nd NGINX instance with health checking
   - Configure upstream pools with proper timeouts
   - Implement session affinity for WebSocket connections

4. **Security Scanning:**
   - Add secret detection to CI/CD pipeline
   - Implement certificate auto-renewal (Let's Encrypt)
   - Enable HTTPS enforcement across all endpoints

### 🧪 Critical Test Fixes (8 hours)
**Files to modify:**
- `/ghl_real_estate_ai/services/ghl_webhook_service.py`
- `/ghl_real_estate_ai/tests/test_ghl_webhook_service.py`
- Performance test suite additions

**Specific Actions:**
1. **Fix webhook processor tests (17/19 currently failing):**
   - Implement deduplication logic with 5-minute windows
   - Add circuit breaker tests for GHL API failures
   - Test signature validation caching
   - Validate <1s end-to-end processing time

2. **Add performance benchmarks:**
   - Redis cache latency: <10ms target validation
   - Database write performance: <100ms target tests
   - ML inference timing: <500ms validation tests

3. **Integration test coverage:**
   - GHL webhook → Redis → ML pipeline testing
   - Error handling for API rate limits
   - Dead letter queue for failed webhooks

## Success Criteria
- [ ] Zero hardcoded secrets in production configuration
- [ ] 99.5% uptime capability with HA setup
- [ ] All 19 webhook tests passing (currently 17 failing)
- [ ] Performance benchmarks: All targets met
- [ ] Security scan: Zero critical vulnerabilities
- [ ] Test coverage: >84% (from current 72%)

## Skills to Leverage
```bash
invoke defense-in-depth --validate-ghl-inputs --security-layers
invoke testing-anti-patterns --scan-ml-models --fix-flaky-tests
invoke railway-deploy --production-hardening
invoke verification-before-completion --comprehensive
```

## Expected Deliverables
1. Secure production deployment configuration
2. High-availability infrastructure setup
3. Complete webhook test suite (100% passing)
4. Security compliance documentation
5. Infrastructure monitoring and alerting setup