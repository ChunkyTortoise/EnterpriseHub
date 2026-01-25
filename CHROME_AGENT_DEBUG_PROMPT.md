# Chrome Agent Debug Prompt for Jorge's Real Estate AI Platform

*Comprehensive debugging prompt for agents using Chrome automation to troubleshoot Jorge's platform*

---

## 🔧 **COPY THIS PROMPT TO DEBUG JORGE'S PLATFORM WITH CHROME AGENTS**

```markdown
---
JORGE'S REAL ESTATE AI PLATFORM - CHROME DEBUG SESSION
=======================================================

I need help debugging Jorge's Real Estate AI platform using Chrome automation.
This is a production-ready real estate platform with confrontational AI qualification bots.

## PLATFORM OVERVIEW

**Project**: EnterpriseHub - Jorge's AI Real Estate Command Center
**Status**: 100% Demo Ready (Version 6.0.0)
**Performance**: Industry-leading 2.61ms ML analytics
**Stack**: FastAPI backend + Streamlit frontend + PostgreSQL + Redis

## PLATFORM ARCHITECTURE

### Core Services (5 Required):
1. **FastAPI Backend** (Port 8002): http://localhost:8002
   - API Documentation: http://localhost:8002/docs
   - Jorge Seller Bot endpoint: /api/jorge-seller/process
   - ML Analytics endpoint: /api/performance/jorge

2. **Main Dashboard** (Port 8501): http://localhost:8501
   - Streamlit app with real-time insights and AI concierge
   - Fixed async event loop issues (safe async handling implemented)

3. **Jorge Command Center** (Port 8503): http://localhost:8503
   - Specialized bot management interface
   - Fixed import path resolution with graceful fallbacks

4. **PostgreSQL Database** (Port 5432): Lead data, analytics, conversation history
5. **Redis Cache** (Port 6379): Performance optimization, session management

### Jorge's Bot Ecosystem:
- **Jorge Seller Bot**: Confrontational qualification (FRS/PCS scoring)
- **Jorge Buyer Bot**: Consultative qualification (SMS compliance)
- **Lead Bot**: 3-7-30 day lifecycle automation
- **Intent Decoder**: 28-feature ML behavioral analysis
- **ML Analytics Engine**: <25ms response time, 95%+ accuracy

## RECENT CRITICAL FIXES (Jan 25, 2026)

### ✅ Frontend Fixes Deployed:
1. **Input Validation Fix** (ghl_real_estate_ai/api/middleware/input_validation.py):
   - Conversation-aware SQL injection detection
   - Natural language no longer triggers false positives
   - Relaxed validation for real estate conversation endpoints

2. **Async Event Loop Fix** (ghl_real_estate_ai/streamlit_demo/app.py):
   - Safe async handling with graceful fallbacks
   - Prevents "RuntimeError: no running event loop"
   - ASYNC_UTILS_AVAILABLE pattern for stability

3. **Import Path Fix** (ghl_real_estate_ai/streamlit_demo/jorge_bot_command_center.py):
   - Multiple fallback import strategies
   - Graceful degradation when components unavailable
   - Resolves ModuleNotFoundError for dashboard components

## COMMON ISSUES TO DEBUG

### Issue 1: Service Startup Problems
**Symptoms**: Services not responding, connection refused
**Debug Steps**:
1. Check if all 5 services are running and accessible
2. Validate FastAPI responds at http://localhost:8002/docs
3. Verify Streamlit apps load at ports 8501 and 8503
4. Test database connectivity (PostgreSQL, Redis)

### Issue 2: Jorge Bot API Errors
**Symptoms**: 500 errors, validation failures, conversation issues
**Debug Steps**:
1. Test Jorge endpoint: POST http://localhost:8002/api/jorge-seller/test
2. Check input validation with real estate messages
3. Verify conversation-aware validation is working
4. Test ML analytics performance: GET http://localhost:8002/api/performance/jorge

### Issue 3: Frontend Interface Problems
**Symptoms**: Streamlit errors, import failures, async issues
**Debug Steps**:
1. Check browser console for JavaScript errors
2. Verify Streamlit apps load without Python exceptions
3. Test component imports and graceful fallbacks
4. Validate async handling doesn't cause event loop conflicts

### Issue 4: Performance Issues
**Symptoms**: Slow responses, timeouts, high latency
**Debug Steps**:
1. Measure ML analytics response time (target: <25ms)
2. Check API response times (target: <100ms)
3. Verify cache hit rates and Redis connectivity
4. Monitor database query performance

## DEBUGGING WORKFLOW

### Phase 1: Service Health Check (5 minutes)
1. Navigate to each service URL and screenshot any errors
2. Test API documentation accessibility
3. Verify Jorge bot endpoints respond correctly
4. Check Streamlit interfaces load without crashes

### Phase 2: Conversation Testing (10 minutes)
1. Test Jorge Seller Bot with realistic messages:
   - "I'm thinking about selling my house. What's it worth?"
   - "I've had bad experiences with realtors before."
   - "I'm not in any hurry to sell, just exploring."
2. Verify confrontational responses are generated
3. Check ML scoring displays (FRS/PCS, temperature classification)
4. Confirm no input validation false positives

### Phase 3: Performance Validation (5 minutes)
1. Measure API response times for key endpoints
2. Test ML analytics speed and accuracy
3. Verify database connectivity and query performance
4. Check cache effectiveness and hit rates

### Phase 4: Error Documentation (10 minutes)
1. Screenshot any errors or unexpected behavior
2. Capture browser console logs for debugging
3. Document specific error messages and stack traces
4. Note performance metrics and response times

## SUCCESS CRITERIA

### ✅ All Systems Operational:
- FastAPI backend responds correctly (200 status)
- Streamlit apps load without errors
- Jorge bot generates confrontational responses
- ML analytics performs under 25ms target
- Database and cache services accessible

### ✅ Conversation Quality:
- Jorge responds with confrontational qualification
- Natural language doesn't trigger validation errors
- ML scoring displays accurate FRS/PCS values
- Temperature classification works correctly

### ✅ Professional Demo Readiness:
- All URLs accessible for client demonstrations
- No visible errors or technical issues
- Performance meets industry-leading standards
- Conversation flow natural and engaging

## AUTOMATION SCRIPTS AVAILABLE

### Startup Script: `./launch_demo_services.sh`
- Starts all 5 services with optimal configuration
- Provides health monitoring and status reporting
- Creates clean log files for debugging

### Validation Script: `python3 setup_demo_environment.py`
- Comprehensive health checks for all services
- Performance measurement and validation
- Demo readiness assessment with detailed reporting

## CONTACT INFO FOR ESCALATION

If you discover critical issues that need immediate attention:
- Focus on service accessibility and conversation functionality
- Document specific error messages and reproduction steps
- Note any performance degradation or timeout issues
- Verify the three recent frontend fixes are working correctly

## EXPECTED DEBUGGING OUTCOMES

After debugging session, I should have:
1. Confirmation all 5 services are healthy and accessible
2. Validation Jorge's confrontational qualification is working
3. Performance metrics confirming <25ms ML response times
4. Screenshots of successful operation or specific error documentation
5. Recommended fixes for any issues discovered

Jorge's platform should demonstrate industry-leading performance with
confrontational AI qualification that outperforms traditional "nice" approaches.

---

Please use Chrome automation to systematically debug this platform,
focusing on service health, conversation quality, and demo readiness.
Document any issues found and confirm the platform is ready for
professional client demonstrations.
```

## 🎯 **HOW TO USE THIS PROMPT**

### For Immediate Debugging:
1. **Copy the entire prompt above** (from the --- line to the end)
2. **Paste into a new Claude conversation** or agent system
3. **Agent will systematically test all platform components**
4. **Receive comprehensive debugging report** with screenshots and recommendations

### For Scheduled Monitoring:
- Use this prompt weekly to validate platform health
- Run before important client demonstrations
- Execute after any code deployments or updates
- Include in automated testing workflows

### For Team Debugging:
- Share this prompt with team members for consistent debugging approach
- Use as template for creating specialized debugging scenarios
- Customize for specific client environments or configurations

---

**Platform**: Jorge's Real Estate AI | **Status**: 100% Demo Ready | **Debug Level**: Professional