# ⚡ QUICK START: Testing & Performance (Parallel Execution)

## 🚀 IMMEDIATE STARTUP (3 Terminals)

### Terminal 1: Backend Services
```bash
cd /Users/cave/Documents/GitHub/EnterpriseHub

# Start FastAPI backend (port 8000)
python app.py

# Expected output:
# INFO: Uvicorn running on http://0.0.0.0:8000
# ✅ Jorge Seller Bot: Ready
# ✅ Lead Bot: Ready
# ✅ Agent Ecosystem: Ready
```

### Terminal 2: Frontend Services
```bash
cd /Users/cave/Documents/GitHub/EnterpriseHub/enterprise-ui

# Install dependencies (if needed)
npm install

# Start Next.js frontend (port 3000)
npm run dev

# Expected output:
# ✓ Ready in 2.1s
# ✓ Local: http://localhost:3000
# ✅ Jorge API Route: Connected
# ✅ Lead Bot API Route: Connected
# ✅ Claude Concierge: Ready
```

### Terminal 3: Dependencies
```bash
cd /Users/cave/Documents/GitHub/EnterpriseHub

# Start Redis & PostgreSQL
docker-compose up -d

# Verify services
docker ps
# Should show: redis:latest, postgres:13
```

---

## 🧪 TRACK 1: END-TO-END TESTING (Execute Immediately)

### **Test 1: Jorge Seller Bot Integration**

#### Quick Health Check
```bash
# Backend health
curl http://localhost:8000/api/bots/health

# Jorge endpoint health
curl http://localhost:8000/api/jorge-seller/process -X POST \
  -H "Content-Type: application/json" \
  -d '{"contact_id":"test","location_id":"test","message":"test"}'
```

#### Full Jorge Qualification Test
```bash
# Test Jorge qualification workflow
curl -X POST http://localhost:3000/api/bots/jorge-seller \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "test_seller_001",
    "location_id": "jorge_test_location",
    "message": "I am thinking about selling my house",
    "contact_info": {
      "name": "Sarah Martinez",
      "phone": "+1-555-0123",
      "email": "sarah@example.com"
    }
  }'

# Expected Response Structure:
# {
#   "status": "success",
#   "data": {
#     "response_message": "Look, I'm not here to waste time...",
#     "seller_temperature": "warm",
#     "questions_answered": 1,
#     "qualification_complete": false,
#     "analytics": {
#       "frs_score": 65,
#       "pcs_score": 58,
#       "processing_time_ms": 42
#     }
#   },
#   "backend_status": "connected"
# }
```

### **Test 2: Lead Bot Automation Integration**

#### Lead Automation Test
```bash
# Test Lead Bot automation
curl -X POST http://localhost:3000/api/bots/lead-bot \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "test_lead_001",
    "location_id": "jorge_test_location",
    "automation_type": "day_3",
    "trigger_data": {
      "showing_date": "2026-01-27T10:00:00Z",
      "property_id": "prop_123"
    }
  }'

# Expected Response:
# {
#   "status": "success",
#   "data": {
#     "automation_id": "auto_1738012800_test_lea",
#     "automation_type": "day_3",
#     "status": "scheduled",
#     "actions_taken": [
#       {
#         "type": "sms_sequence",
#         "channel": "sms",
#         "content": "Hi! Jorge here. Just checking in...",
#         "scheduled_time": "2026-01-25T18:05:00Z"
#       }
#     ]
#   },
#   "backend_status": "connected"
# }
```

### **Test 3: Claude Concierge Integration**

#### Context Analysis Test
```bash
# Test Claude Concierge context analysis
curl -X POST http://localhost:3000/api/claude-concierge/context \
  -H "Content-Type: application/json" \
  -d '{
    "contextType": "conversation_intelligence",
    "conversationHistory": [
      {"role": "user", "content": "I want to sell my house"},
      {"role": "assistant", "content": "What is your timeline?"}
    ],
    "leadData": {
      "frs_score": 65,
      "pcs_score": 58,
      "temperature": "warm"
    }
  }'

# Expected: Intelligent coaching recommendations
```

### **Test 4: Agent Ecosystem Dashboard**

#### Agent Status Check
```bash
# Check agent ecosystem status
curl http://localhost:8000/api/agents/statuses

# Check agent metrics
curl http://localhost:8000/api/agents/metrics

# Check active coordinations
curl http://localhost:8000/api/agents/coordinations/active
```

---

## ⚡ TRACK 2: PERFORMANCE MONITORING (Execute in Parallel)

### **Step 1: Create Performance Monitor (Backend)**

Create file: `ghl_real_estate_ai/services/performance_monitor.py`

```python
"""
Performance monitoring service for Jorge's AI Empire
Tracks response times, throughput, and optimization metrics
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time
import asyncio
from collections import deque
import statistics

class PerformanceMonitor:
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.metrics = {
            "jorge_response_time": deque(maxlen=max_samples),
            "lead_automation_latency": deque(maxlen=max_samples),
            "concierge_processing_time": deque(maxlen=max_samples),
            "ml_inference_speed": deque(maxlen=max_samples),
            "cache_hit_rates": deque(maxlen=max_samples),
            "websocket_delivery_time": deque(maxlen=max_samples),
            "api_response_times": deque(maxlen=max_samples)
        }
        self.targets = {
            "jorge_response_time": 42,  # ms
            "lead_automation_latency": 500,  # ms
            "websocket_delivery_time": 10,  # ms
            "cache_hit_rate": 95,  # percentage
            "api_response_time": 200  # ms
        }

    async def track_jorge_performance(self, start_time: float, end_time: float,
                                    success: bool = True, metadata: Dict = None):
        """Track Jorge Seller Bot performance"""
        response_time = (end_time - start_time) * 1000  # Convert to ms

        self.metrics["jorge_response_time"].append({
            "timestamp": datetime.now(),
            "response_time_ms": response_time,
            "success": success,
            "target_ms": self.targets["jorge_response_time"],
            "metadata": metadata or {}
        })

        # Alert if exceeding target
        if response_time > self.targets["jorge_response_time"]:
            await self._performance_alert("jorge_response_time", response_time)

    async def track_lead_automation(self, automation_type: str, start_time: float,
                                  end_time: float, success: bool = True):
        """Track Lead Bot automation performance"""
        latency = (end_time - start_time) * 1000

        self.metrics["lead_automation_latency"].append({
            "timestamp": datetime.now(),
            "latency_ms": latency,
            "automation_type": automation_type,
            "success": success,
            "target_ms": self.targets["lead_automation_latency"]
        })

    async def track_api_call(self, endpoint: str, start_time: float,
                           end_time: float, status_code: int):
        """Track general API performance"""
        response_time = (end_time - start_time) * 1000

        self.metrics["api_response_times"].append({
            "timestamp": datetime.now(),
            "endpoint": endpoint,
            "response_time_ms": response_time,
            "status_code": status_code,
            "success": status_code < 400
        })

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        return {
            "jorge_bot": self._get_metric_summary("jorge_response_time"),
            "lead_automation": self._get_metric_summary("lead_automation_latency"),
            "api_performance": self._get_metric_summary("api_response_times"),
            "system_health": self._calculate_system_health(),
            "last_updated": datetime.now().isoformat()
        }

    def _get_metric_summary(self, metric_name: str) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        if not self.metrics[metric_name]:
            return {"status": "no_data"}

        recent_data = list(self.metrics[metric_name])[-100:]  # Last 100 samples

        if metric_name == "jorge_response_time":
            times = [d["response_time_ms"] for d in recent_data]
        elif metric_name == "lead_automation_latency":
            times = [d["latency_ms"] for d in recent_data]
        elif metric_name == "api_response_times":
            times = [d["response_time_ms"] for d in recent_data]
        else:
            times = [d.get("value", 0) for d in recent_data]

        return {
            "avg": round(statistics.mean(times), 2),
            "median": round(statistics.median(times), 2),
            "p95": round(statistics.quantiles(times, n=20)[18], 2),  # 95th percentile
            "min": min(times),
            "max": max(times),
            "samples": len(times),
            "target": self.targets.get(metric_name.replace("_time", "").replace("_latency", "")),
            "health": self._calculate_metric_health(times, metric_name)
        }

    def _calculate_metric_health(self, times: List[float], metric_name: str) -> str:
        """Calculate health status for a metric"""
        avg_time = statistics.mean(times)
        target_key = metric_name.replace("_time", "").replace("_latency", "")
        target = self.targets.get(target_key)

        if not target:
            return "unknown"

        if avg_time <= target:
            return "excellent"
        elif avg_time <= target * 1.2:
            return "good"
        elif avg_time <= target * 1.5:
            return "warning"
        else:
            return "critical"

    def _calculate_system_health(self) -> Dict[str, Any]:
        """Calculate overall system health score"""
        jorge_health = self._get_metric_summary("jorge_response_time").get("health", "unknown")
        lead_health = self._get_metric_summary("lead_automation_latency").get("health", "unknown")
        api_health = self._get_metric_summary("api_response_times").get("health", "unknown")

        health_scores = {
            "excellent": 100,
            "good": 80,
            "warning": 60,
            "critical": 30,
            "unknown": 50
        }

        overall_score = round(statistics.mean([
            health_scores[jorge_health],
            health_scores[lead_health],
            health_scores[api_health]
        ]))

        return {
            "score": overall_score,
            "status": self._score_to_status(overall_score),
            "components": {
                "jorge_bot": jorge_health,
                "lead_automation": lead_health,
                "api_performance": api_health
            }
        }

    def _score_to_status(self, score: int) -> str:
        """Convert numerical score to status"""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 50:
            return "warning"
        else:
            return "critical"

    async def _performance_alert(self, metric: str, value: float):
        """Send performance alert (implement with your alerting system)"""
        print(f"⚠️ PERFORMANCE ALERT: {metric} = {value}ms (target: {self.targets.get(metric)}ms)")

# Global instance
_performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor
```

### **Step 2: Add Performance Tracking to APIs**

Update `ghl_real_estate_ai/api/routes/bot_management.py`:

```python
# Add at top
from ghl_real_estate_ai.services.performance_monitor import get_performance_monitor

# In process_seller_message function (around line 554):
@router.post("/jorge-seller/process", response_model=SellerChatResponse)
async def process_seller_message(request: SellerChatRequest):
    """Enhanced with performance tracking"""
    start_time = time.time()
    performance_monitor = get_performance_monitor()

    try:
        # ... existing code ...

        # Track performance before returning
        end_time = time.time()
        await performance_monitor.track_jorge_performance(
            start_time=start_time,
            end_time=end_time,
            success=True,
            metadata={"contact_id": request.contact_id}
        )

        return response

    except Exception as e:
        end_time = time.time()
        await performance_monitor.track_jorge_performance(
            start_time=start_time,
            end_time=end_time,
            success=False,
            metadata={"error": str(e)}
        )
        raise
```

### **Step 3: Add Performance Endpoint**

Add to `bot_management.py`:

```python
@router.get("/performance/summary")
async def get_performance_summary():
    """Get comprehensive performance metrics"""
    performance_monitor = get_performance_monitor()
    return performance_monitor.get_performance_summary()
```

### **Step 4: Test Performance Monitoring**

```bash
# Run some Jorge tests to generate performance data
for i in {1..10}; do
  curl -X POST http://localhost:3000/api/bots/jorge-seller \
    -H "Content-Type: application/json" \
    -d '{
      "contact_id": "perf_test_'$i'",
      "location_id": "test",
      "message": "Performance test message '$i'"
    }' &
done

wait

# Check performance metrics
curl http://localhost:8000/api/performance/summary
```

---

## ⚡ PERFORMANCE OPTIMIZATION TARGETS

### **Current Baselines (Measure First)**
- **Jorge Response Time**: ~42ms (target: maintain)
- **Lead Automation**: ~150ms (target: <500ms)
- **API Response**: ~200ms (target: <200ms)
- **WebSocket Latency**: ~15ms (target: <10ms)

### **Quick Optimization Wins**
1. **Redis Caching**: Implement for frequently accessed data
2. **Connection Pooling**: Optimize database connections
3. **Async Processing**: Ensure non-blocking operations
4. **Response Compression**: Enable gzip for large responses

---

## ✅ SUCCESS CHECKPOINTS

### **Testing Track (20 minutes)**
- [ ] All services started successfully
- [ ] Jorge E2E test returns real backend data
- [ ] Lead Bot automation triggers correctly
- [ ] Claude Concierge context analysis works
- [ ] Agent ecosystem shows live data

### **Performance Track (30 minutes)**
- [ ] PerformanceMonitor class implemented
- [ ] Jorge response time tracking active
- [ ] Performance summary endpoint working
- [ ] Baseline metrics collected
- [ ] Optimization targets identified

### **Combined Success (60 minutes)**
- [ ] Both tracks executing in parallel
- [ ] Real-time performance monitoring
- [ ] E2E workflows validated with metrics
- [ ] Ready for production optimization phase

---

**🚀 EXECUTE NOW: Start both tracks immediately for comprehensive platform validation and optimization!**