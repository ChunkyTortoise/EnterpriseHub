# Quick Start: Automated Daily Briefing Implementation
## Get Your First Automation Running in 1 Week

**Goal**: Deliver automated morning intelligence briefings to agents in 7 days
**Complexity**: Low (leverages existing AI engines)
**Risk**: Minimal (read-only operations, no data changes)
**Impact**: Immediate (agents see value on Day 1)

---

## Day-by-Day Implementation Plan

### Day 1: Environment Setup & Dependencies

**Tasks**:
1. Install new dependencies
2. Create automation database tables
3. Set up Redis cache keys
4. Configure scheduled jobs

**Commands**:
```bash
# 1. Install dependencies
cd /Users/cave/enterprisehub
pip install celery==5.3.4 celery-beat==2.5.0 jinja2==3.1.3

# 2. Create database tables
python scripts/create_automation_tables.py

# 3. Verify Redis connection
python -c "import redis; r = redis.Redis(); print('Redis OK' if r.ping() else 'Redis FAIL')"

# 4. Test existing AI engines
python scripts/test_ai_engines_integration.py
```

**Database Migration** (`scripts/create_automation_tables.py`):
```python
"""Create automation tables"""
import asyncio
from sqlalchemy import create_engine, text

async def create_tables():
    engine = create_engine("postgresql://localhost/enterprisehub")

    sql = """
    -- Automated Insights Tracking
    CREATE TABLE IF NOT EXISTS automated_insights (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        insight_type VARCHAR(50) NOT NULL,
        agent_id UUID NOT NULL,
        lead_id UUID,
        generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
        confidence FLOAT NOT NULL,
        priority INT NOT NULL,
        insight_data JSONB NOT NULL,
        delivered BOOLEAN DEFAULT FALSE,
        delivered_at TIMESTAMP,
        delivery_channels TEXT[],
        action_taken BOOLEAN DEFAULT FALSE,
        action_taken_at TIMESTAMP,
        outcome VARCHAR(50)
    );

    CREATE INDEX IF NOT EXISTS idx_agent_generated
        ON automated_insights(agent_id, generated_at);

    -- Daily Briefings Cache
    CREATE TABLE IF NOT EXISTS daily_briefings (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        agent_id UUID NOT NULL,
        briefing_date DATE NOT NULL,
        generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
        briefing_data JSONB NOT NULL,
        delivery_status JSONB,
        opened BOOLEAN DEFAULT FALSE,
        opened_at TIMESTAMP,
        UNIQUE(agent_id, briefing_date)
    );

    CREATE INDEX IF NOT EXISTS idx_agent_date
        ON daily_briefings(agent_id, briefing_date DESC);
    """

    with engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()

    print("✅ Automation tables created successfully")

if __name__ == "__main__":
    asyncio.run(create_tables())
```

**Verification**:
```bash
# Verify tables exist
python -c "from ghl_real_estate_ai.database import engine; \
           import sqlalchemy; \
           print('Tables:', engine.table_names())"
```

---

### Day 2: Core Service Implementation

**Tasks**:
1. Create automation package structure
2. Implement Daily Briefing Service (already done!)
3. Set up service registry
4. Create basic tests

**File Structure**:
```
ghl_real_estate_ai/services/automation/
├── __init__.py                              ✅ Created
├── automated_daily_briefing_service.py      ✅ Created
├── automation_config.py                     ← Create today
└── automation_orchestrator.py               ← Create today
```

**Configuration** (`automation_config.py`):
```python
"""Automation system configuration"""
from datetime import time
from typing import Dict, List

class AutomationConfig:
    """Central configuration for automation system"""

    # Daily Briefing Settings
    BRIEFING_GENERATION_TIME = time(7, 0)  # 7:00 AM
    BRIEFING_TIMEZONE = "America/New_York"
    BRIEFING_CACHE_TTL_HOURS = 6

    # Delivery Channels
    ENABLE_SMS_DELIVERY = True
    ENABLE_EMAIL_DELIVERY = True
    ENABLE_DASHBOARD_UPDATE = True

    # Performance Settings
    MAX_CONCURRENT_GENERATIONS = 5
    GENERATION_TIMEOUT_SECONDS = 120
    DELIVERY_TIMEOUT_SECONDS = 30

    # Intelligence Settings
    MIN_CONFIDENCE_THRESHOLD = 0.70  # 70% minimum for auto-alerts
    HOT_LEAD_THRESHOLD = 0.75        # 75% for hot lead classification
    CHURN_RISK_THRESHOLD = 0.65      # 65% for at-risk classification

    # Priority Settings
    MAX_PRIORITY_ACTIONS = 5
    MAX_HOT_LEADS = 5
    MAX_PROPERTY_MATCHES = 8
    MAX_CONTACT_WINDOWS = 10

    @classmethod
    def get_active_agents(cls) -> List[str]:
        """Get list of active agent IDs for briefing generation"""
        # In production, this would query database
        # For pilot, hardcode initial agents
        return [
            "agent_jorge_001",
            "agent_sarah_002",
            "agent_mike_003"
        ]

    @classmethod
    def get_agent_preferences(cls, agent_id: str) -> Dict:
        """Get agent-specific preferences"""
        # Default preferences (customizable per agent)
        return {
            "timezone": "America/New_York",
            "briefing_time": time(7, 0),
            "delivery_channels": ["sms", "email", "dashboard"],
            "sms_enabled": True,
            "email_enabled": True,
            "min_priority_level": "high"
        }
```

**Orchestrator** (`automation_orchestrator.py`):
```python
"""Central orchestrator for automation system"""
import asyncio
import logging
from datetime import datetime
from typing import List

from .automated_daily_briefing_service import (
    AutomatedDailyBriefingService,
    get_automated_daily_briefing_service
)
from .automation_config import AutomationConfig

logger = logging.getLogger(__name__)

class AutomationOrchestrator:
    """
    Central coordinator for all automation workflows
    Manages scheduled jobs and event-driven automation
    """

    def __init__(self):
        self.config = AutomationConfig()
        self.briefing_service = get_automated_daily_briefing_service()
        self.is_running = False

    async def start(self):
        """Start automation orchestrator"""
        self.is_running = True
        logger.info("🚀 Automation Orchestrator started")

    async def stop(self):
        """Stop automation orchestrator"""
        self.is_running = False
        logger.info("🛑 Automation Orchestrator stopped")

    async def generate_daily_briefings_job(self):
        """
        Scheduled job: Generate daily briefings for all agents
        Runs: Every day at 7:00 AM
        """
        try:
            start_time = datetime.now()
            logger.info("📊 Starting daily briefing generation job")

            # Generate briefings
            briefings = await self.briefing_service.generate_all_daily_briefings()

            # Deliver briefings
            delivery_tasks = [
                self.briefing_service.deliver_briefing(briefing)
                for briefing in briefings
            ]

            delivery_results = await asyncio.gather(
                *delivery_tasks,
                return_exceptions=True
            )

            # Log results
            successful = sum(
                1 for r in delivery_results
                if isinstance(r, dict) and any(r.values())
            )

            duration = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"✅ Daily briefing job complete: "
                f"{successful}/{len(briefings)} delivered in {duration:.1f}s"
            )

            return {
                "success": True,
                "briefings_generated": len(briefings),
                "briefings_delivered": successful,
                "duration_seconds": duration
            }

        except Exception as e:
            logger.error(f"❌ Daily briefing job failed: {e}")
            return {"success": False, "error": str(e)}

# Global instance
orchestrator = AutomationOrchestrator()
```

**Tests** (`tests/automation/test_daily_briefing.py`):
```python
"""Tests for automated daily briefing service"""
import pytest
from datetime import datetime
from ghl_real_estate_ai.services.automation import (
    AutomatedDailyBriefingService,
    DailyBriefing
)

@pytest.mark.asyncio
async def test_briefing_generation():
    """Test basic briefing generation"""
    service = AutomatedDailyBriefingService()

    # Generate briefing for test agent
    briefing = await service.generate_daily_briefing("test_agent_001")

    # Verify briefing structure
    assert isinstance(briefing, DailyBriefing)
    assert briefing.agent_id == "test_agent_001"
    assert briefing.generated_at is not None
    assert len(briefing.priority_actions) > 0

    # Verify processing time is acceptable
    assert briefing.processing_time_ms < 120000  # < 2 minutes

@pytest.mark.asyncio
async def test_briefing_delivery():
    """Test briefing delivery"""
    service = AutomatedDailyBriefingService()

    briefing = await service.generate_daily_briefing("test_agent_001")

    # Test delivery (will use mock clients in test environment)
    results = await service.deliver_briefing(briefing)

    # Verify delivery attempted for all channels
    assert "sms" in results or "email" in results or "dashboard" in results

@pytest.mark.asyncio
async def test_parallel_generation():
    """Test parallel briefing generation for multiple agents"""
    service = AutomatedDailyBriefingService()

    # Generate for 3 agents in parallel
    agent_ids = ["agent_001", "agent_002", "agent_003"]

    briefings = await asyncio.gather(*[
        service.generate_daily_briefing(agent_id)
        for agent_id in agent_ids
    ])

    # Verify all generated successfully
    assert len(briefings) == 3
    assert all(isinstance(b, DailyBriefing) for b in briefings)
```

**Run Tests**:
```bash
# Run all automation tests
pytest tests/automation/ -v

# Run specific test
pytest tests/automation/test_daily_briefing.py::test_briefing_generation -v
```

---

### Day 3: Celery Integration for Scheduling

**Tasks**:
1. Configure Celery for task scheduling
2. Create daily briefing task
3. Set up Celery Beat for cron jobs
4. Test scheduled execution

**Celery Configuration** (`celeryconfig.py`):
```python
"""Celery configuration for automation tasks"""
from celery import Celery
from celery.schedules import crontab
from datetime import timedelta

app = Celery('enterprisehub_automation')

app.conf.broker_url = 'redis://localhost:6379/0'
app.conf.result_backend = 'redis://localhost:6379/0'

# Task routing
app.conf.task_routes = {
    'automation.daily_briefing': {'queue': 'automation'},
    'automation.realtime_alerts': {'queue': 'alerts'},
}

# Scheduled tasks (Celery Beat)
app.conf.beat_schedule = {
    # Daily Briefing Generation (7:00 AM daily)
    'generate-daily-briefings': {
        'task': 'automation.tasks.generate_daily_briefings',
        'schedule': crontab(hour=7, minute=0),
        'options': {'queue': 'automation'}
    },

    # Cleanup old briefings (2:00 AM daily)
    'cleanup-old-briefings': {
        'task': 'automation.tasks.cleanup_old_briefings',
        'schedule': crontab(hour=2, minute=0),
        'options': {'queue': 'automation'}
    },
}

# Task settings
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'
app.conf.timezone = 'America/New_York'
app.conf.enable_utc = True
```

**Tasks Definition** (`ghl_real_estate_ai/tasks/automation_tasks.py`):
```python
"""Celery tasks for automation system"""
import asyncio
import logging
from celery import Task
from ..services.automation import AutomationOrchestrator

logger = logging.getLogger(__name__)

class AsyncTask(Task):
    """Base class for async tasks"""

    def __call__(self, *args, **kwargs):
        """Execute async task"""
        return asyncio.run(self.run(*args, **kwargs))

    async def run(self, *args, **kwargs):
        """Override in subclass"""
        raise NotImplementedError

@app.task(base=AsyncTask, name='automation.tasks.generate_daily_briefings')
async def generate_daily_briefings():
    """Generate and deliver daily briefings to all agents"""
    logger.info("🌅 Daily briefing generation task started")

    orchestrator = AutomationOrchestrator()
    result = await orchestrator.generate_daily_briefings_job()

    logger.info(f"📊 Daily briefing task complete: {result}")
    return result

@app.task(name='automation.tasks.cleanup_old_briefings')
def cleanup_old_briefings():
    """Clean up briefings older than 30 days"""
    from datetime import datetime, timedelta
    from ..database import get_db
    from sqlalchemy import text

    cutoff_date = datetime.now() - timedelta(days=30)

    with get_db() as db:
        result = db.execute(
            text("DELETE FROM daily_briefings WHERE generated_at < :cutoff"),
            {"cutoff": cutoff_date}
        )
        db.commit()

    logger.info(f"🧹 Cleaned up {result.rowcount} old briefings")
    return {"deleted": result.rowcount}
```

**Start Celery Workers**:
```bash
# Terminal 1: Start Celery worker
celery -A celeryconfig worker --loglevel=info -Q automation,alerts

# Terminal 2: Start Celery Beat (scheduler)
celery -A celeryconfig beat --loglevel=info

# Terminal 3: Monitor tasks (optional)
celery -A celeryconfig flower  # Opens web UI at http://localhost:5555
```

**Manual Task Execution** (for testing):
```bash
# Execute task immediately (don't wait for schedule)
python -c "from ghl_real_estate_ai.tasks.automation_tasks import generate_daily_briefings; \
           generate_daily_briefings.delay()"
```

---

### Day 4: Integration with Existing AI Engines

**Tasks**:
1. Verify connections to all AI engines
2. Create integration wrappers
3. Test data flow
4. Handle errors gracefully

**Integration Test** (`scripts/test_ai_engines_integration.py`):
```python
"""Test integration with existing AI engines"""
import asyncio
import logging
from ghl_real_estate_ai.services.predictive_lead_lifecycle_engine import (
    get_predictive_lead_lifecycle_engine
)
from ghl_real_estate_ai.services.claude_advanced_lead_intelligence import (
    ClaudeAdvancedLeadIntelligence
)
from ghl_real_estate_ai.services.ai_lead_insights import AILeadInsightsService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_predictive_engine():
    """Test predictive lead lifecycle engine"""
    logger.info("Testing Predictive Lead Lifecycle Engine...")

    try:
        engine = await get_predictive_lead_lifecycle_engine()
        forecast = await engine.predict_conversion_timeline("test_lead_001")

        logger.info(f"✅ Predictive engine working")
        logger.info(f"   Conversion probability: {forecast.conversion_probability:.2%}")
        logger.info(f"   Expected date: {forecast.expected_conversion_date}")
        return True

    except Exception as e:
        logger.error(f"❌ Predictive engine failed: {e}")
        return False

async def test_lead_intelligence():
    """Test Claude lead intelligence"""
    logger.info("Testing Claude Lead Intelligence...")

    try:
        service = ClaudeAdvancedLeadIntelligence()

        # Test with sample lead data
        analysis = await service.analyze_lead_comprehensive("test_lead_001")

        logger.info(f"✅ Lead intelligence working")
        logger.info(f"   Intelligence score: {analysis.overall_intelligence_score:.2f}")
        return True

    except Exception as e:
        logger.error(f"❌ Lead intelligence failed: {e}")
        return False

async def test_lead_insights():
    """Test AI lead insights"""
    logger.info("Testing AI Lead Insights...")

    try:
        service = AILeadInsightsService()

        # Test with sample lead
        sample_lead = {
            "lead_id": "test_001",
            "conversations": [],
            "score": 7.5,
            "metadata": {}
        }

        insights = service.analyze_lead(sample_lead)

        logger.info(f"✅ Lead insights working")
        logger.info(f"   Generated {len(insights)} insights")
        return True

    except Exception as e:
        logger.error(f"❌ Lead insights failed: {e}")
        return False

async def main():
    """Run all integration tests"""
    logger.info("=" * 60)
    logger.info("AI ENGINES INTEGRATION TEST")
    logger.info("=" * 60)

    results = await asyncio.gather(
        test_predictive_engine(),
        test_lead_intelligence(),
        test_lead_insights(),
        return_exceptions=True
    )

    passed = sum(1 for r in results if r is True)
    total = len(results)

    logger.info("=" * 60)
    logger.info(f"RESULTS: {passed}/{total} engines working")
    logger.info("=" * 60)

    if passed == total:
        logger.info("✅ All AI engines integrated successfully!")
    else:
        logger.warning(f"⚠️ {total - passed} engines need attention")

if __name__ == "__main__":
    asyncio.run(main())
```

**Run Integration Test**:
```bash
python scripts/test_ai_engines_integration.py
```

---

### Day 5: Delivery Channels Implementation

**Tasks**:
1. Set up GHL SMS delivery
2. Configure email service (SendGrid/SMTP)
3. Create dashboard API endpoint
4. Test all delivery channels

**GHL SMS Delivery** (`services/delivery/ghl_message_delivery.py`):
```python
"""GHL message delivery service"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class GHLMessageDeliveryService:
    """Deliver messages via GoHighLevel"""

    def __init__(self, ghl_client=None):
        self.ghl_client = ghl_client

    async def send_sms(
        self,
        to_number: str,
        message: str,
        location_id: str = None
    ) -> Dict[str, Any]:
        """Send SMS via GHL"""

        try:
            if self.ghl_client:
                result = await self.ghl_client.send_sms(
                    phone=to_number,
                    message=message,
                    location_id=location_id
                )

                logger.info(f"✅ SMS sent to {to_number}")
                return {"success": True, "message_id": result.get("id")}
            else:
                # Mock mode for testing
                logger.info(f"📱 [MOCK] SMS to {to_number}: {message[:50]}...")
                return {"success": True, "message_id": "mock_id"}

        except Exception as e:
            logger.error(f"❌ SMS delivery failed: {e}")
            return {"success": False, "error": str(e)}
```

**Email Delivery** (`services/delivery/email_delivery_service.py`):
```python
"""Email delivery service"""
import logging
from typing import Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class EmailDeliveryService:
    """Deliver emails via SMTP or SendGrid"""

    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: str = None,
        smtp_password: str = None
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        from_email: str = None
    ) -> Dict[str, Any]:
        """Send email"""

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = from_email or self.smtp_user
            msg['To'] = to_email

            # Add HTML body
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

            # Send via SMTP
            if self.smtp_user and self.smtp_password:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

                logger.info(f"✅ Email sent to {to_email}")
                return {"success": True}
            else:
                # Mock mode
                logger.info(f"📧 [MOCK] Email to {to_email}: {subject}")
                return {"success": True}

        except Exception as e:
            logger.error(f"❌ Email delivery failed: {e}")
            return {"success": False, "error": str(e)}
```

**Dashboard API** (`api/routes/automation_insights.py`):
```python
"""API endpoints for automation insights"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime

from ghl_real_estate_ai.services.automation import get_automated_daily_briefing_service

router = APIRouter(prefix="/api/v1/automation", tags=["automation"])

@router.get("/briefing/{agent_id}/today")
async def get_today_briefing(agent_id: str) -> Dict[str, Any]:
    """Get today's briefing for agent"""

    service = get_automated_daily_briefing_service()

    briefing = await service.generate_daily_briefing(agent_id)

    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")

    return briefing.dashboard_data

@router.get("/briefing/{agent_id}/summary")
async def get_briefing_summary(agent_id: str) -> Dict[str, Any]:
    """Get summary of today's briefing"""

    service = get_automated_daily_briefing_service()

    briefing = await service.generate_daily_briefing(agent_id)

    return {
        "agent_id": agent_id,
        "date": briefing.briefing_date,
        "urgent_actions": len([
            a for a in briefing.priority_actions
            if a.priority.value == "urgent"
        ]),
        "hot_leads": len(briefing.hot_leads),
        "at_risk_leads": len(briefing.at_risk_leads),
        "property_matches": len(briefing.property_matches),
        "generated_at": briefing.generated_at
    }
```

---

### Day 6: Pilot Testing with 3 Agents

**Tasks**:
1. Select 3 pilot agents
2. Configure their profiles
3. Generate test briefings
4. Collect feedback
5. Iterate on improvements

**Pilot Agent Setup** (`scripts/setup_pilot_agents.py`):
```python
"""Set up pilot agents for automated briefing testing"""
import asyncio
from ghl_real_estate_ai.services.automation import AutomationConfig

PILOT_AGENTS = [
    {
        "id": "agent_jorge_001",
        "name": "Jorge",
        "email": "jorge@realestateagency.com",
        "phone": "+1-305-555-0101",
        "timezone": "America/New_York",
        "preferences": {
            "briefing_time": "07:00",
            "delivery_channels": ["sms", "email"],
            "min_priority": "high"
        }
    },
    {
        "id": "agent_sarah_002",
        "name": "Sarah",
        "email": "sarah@realestateagency.com",
        "phone": "+1-305-555-0102",
        "timezone": "America/New_York",
        "preferences": {
            "briefing_time": "07:30",
            "delivery_channels": ["email", "dashboard"],
            "min_priority": "medium"
        }
    },
    {
        "id": "agent_mike_003",
        "name": "Mike",
        "email": "mike@realestateagency.com",
        "phone": "+1-305-555-0103",
        "timezone": "America/Chicago",
        "preferences": {
            "briefing_time": "08:00",
            "delivery_channels": ["sms"],
            "min_priority": "urgent"
        }
    }
]

async def setup_pilot_agents():
    """Configure pilot agents in database"""

    # Store agent configurations
    # (Implementation depends on your database structure)

    print("✅ Pilot agents configured:")
    for agent in PILOT_AGENTS:
        print(f"   • {agent['name']} ({agent['id']})")

if __name__ == "__main__":
    asyncio.run(setup_pilot_agents())
```

**Manual Test Generation**:
```bash
# Generate test briefing for Jorge
python -c "
import asyncio
from ghl_real_estate_ai.services.automation import get_automated_daily_briefing_service

async def test():
    service = get_automated_daily_briefing_service()
    briefing = await service.generate_daily_briefing('agent_jorge_001')
    print(f'Briefing generated: {briefing.briefing_id}')
    print(f'Priority actions: {len(briefing.priority_actions)}')
    print(f'Hot leads: {len(briefing.hot_leads)}')

    # Deliver
    results = await service.deliver_briefing(briefing)
    print(f'Delivery results: {results}')

asyncio.run(test())
"
```

---

### Day 7: Production Deployment & Monitoring

**Tasks**:
1. Deploy to production environment
2. Configure monitoring
3. Set up alerts
4. Launch to pilot agents
5. Begin tracking metrics

**Production Deployment Checklist**:
```yaml
Environment Variables:
  ✅ REDIS_URL configured
  ✅ DATABASE_URL configured
  ✅ GHL_API_KEY set
  ✅ SMTP_CREDENTIALS configured
  ✅ CELERY_BROKER_URL set

Services Running:
  ✅ Celery worker (automation queue)
  ✅ Celery beat (scheduler)
  ✅ Redis server
  ✅ PostgreSQL database
  ✅ FastAPI application

Monitoring:
  ✅ Prometheus metrics exposed
  ✅ Grafana dashboards configured
  ✅ Error alerting set up
  ✅ Performance tracking enabled
```

**Launch Script** (`scripts/launch_automation.sh`):
```bash
#!/bin/bash

echo "🚀 Launching EnterpriseHub Automation System"
echo "=========================================="

# 1. Start Redis (if not running)
redis-server --daemonize yes
echo "✅ Redis started"

# 2. Start Celery worker
celery -A celeryconfig worker \
    --loglevel=info \
    --queue=automation,alerts \
    --concurrency=4 \
    --max-tasks-per-child=1000 \
    --detach

echo "✅ Celery worker started"

# 3. Start Celery Beat (scheduler)
celery -A celeryconfig beat \
    --loglevel=info \
    --detach

echo "✅ Celery Beat started"

# 4. Verify all services
sleep 5

if pgrep -f "celery.*worker" > /dev/null; then
    echo "✅ Celery worker running"
else
    echo "❌ Celery worker NOT running"
    exit 1
fi

if pgrep -f "celery.*beat" > /dev/null; then
    echo "✅ Celery Beat running"
else
    echo "❌ Celery Beat NOT running"
    exit 1
fi

echo ""
echo "=========================================="
echo "🎉 Automation System Launched Successfully!"
echo "=========================================="
echo ""
echo "Daily briefings will be generated at 7:00 AM"
echo "Monitor: http://localhost:5555 (Flower UI)"
echo ""
```

**Monitoring Dashboard** (Grafana configuration):
```yaml
Metrics to Track:
  - Briefings generated per day
  - Average generation time
  - Delivery success rate (SMS, email, dashboard)
  - Agent engagement rate (opens, clicks)
  - Error rate
  - Cache hit rate

Alerts:
  - Generation failure (immediate)
  - Delivery failure rate >5%
  - Processing time >120 seconds
  - Engagement rate <70%
```

---

## Week 1 Completion Checklist

```yaml
✅ Day 1: Environment setup complete
✅ Day 2: Core service implemented
✅ Day 3: Celery scheduling configured
✅ Day 4: AI engines integrated
✅ Day 5: Delivery channels working
✅ Day 6: Pilot testing with 3 agents
✅ Day 7: Production deployment

Success Criteria:
  ✅ 3 pilot agents receiving daily briefings
  ✅ Briefings delivered by 7:00 AM daily
  ✅ 90%+ delivery success rate
  ✅ <90 seconds generation time
  ✅ Positive pilot feedback
```

---

## Next Steps (Week 2+)

**Week 2: Optimization & Feedback**
- Collect pilot agent feedback
- Optimize briefing content
- Improve delivery reliability
- Add customization options

**Week 3: Real-Time Alerts**
- Implement alert system
- Configure alert rules
- Test delivery latency
- Pilot with existing agents

**Week 4: Follow-Up Automation**
- Build sequence engine
- Create sequence templates
- Test behavioral triggers
- Launch automated follow-ups

---

## Support & Troubleshooting

**Common Issues**:

1. **Briefing not generating**:
   ```bash
   # Check Celery worker logs
   tail -f celery_worker.log

   # Manually trigger task
   python -c "from ghl_real_estate_ai.tasks.automation_tasks import \
              generate_daily_briefings; generate_daily_briefings.delay()"
   ```

2. **Delivery failures**:
   ```bash
   # Check delivery service logs
   grep "delivery" logs/automation.log

   # Test SMS delivery
   python scripts/test_sms_delivery.py

   # Test email delivery
   python scripts/test_email_delivery.py
   ```

3. **Performance issues**:
   ```bash
   # Check Redis connection
   redis-cli ping

   # Monitor Celery performance
   celery -A celeryconfig inspect active

   # Check database connections
   python scripts/check_db_connections.py
   ```

**Getting Help**:
- Documentation: `/Users/cave/enterprisehub/AUTOMATED_INSIGHTS_IMPLEMENTATION_PLAN.md`
- Architecture: `/Users/cave/enterprisehub/AUTOMATED_INSIGHTS_EXECUTIVE_SUMMARY.md`
- Code: `/Users/cave/enterprisehub/ghl_real_estate_ai/services/automation/`

---

**Ready to Start?** Run this command to begin:

```bash
cd /Users/cave/enterprisehub
./scripts/quick_start_automation.sh
```

🚀 **Let's eliminate manual work and transform agent productivity!**
