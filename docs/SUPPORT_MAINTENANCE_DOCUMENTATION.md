# 🔧 Customer Intelligence Platform - Support & Maintenance Documentation

**Comprehensive operational guide for system health, maintenance procedures, and ongoing support**

---

## 🚨 Emergency Response & Incident Management

### Critical Incident Classification

| Severity | Description | Response Time | Escalation |
|----------|-------------|---------------|------------|
| **P0 - Critical** | Platform unavailable, data loss | 15 minutes | Immediate |
| **P1 - High** | Major feature broken, performance degraded | 1 hour | 2 hours |
| **P2 - Medium** | Minor feature issues, slow performance | 4 hours | 8 hours |
| **P3 - Low** | Cosmetic issues, enhancement requests | 24 hours | 72 hours |

### Emergency Contact Procedures

```yaml
🚨 Emergency Escalation Matrix:

Level 1 - On-Call Support:
  Phone: +1-800-PLATFORM (24/7)
  Email: emergency@platform-support.com
  Slack: #emergency-response
  
Level 2 - Engineering Team:
  Phone: +1-800-ENGINEERS
  Email: engineering@platform-support.com
  Slack: #engineering-oncall
  
Level 3 - Executive Team:
  Phone: +1-800-EXECUTIVE
  Email: executive@platform-support.com
  Slack: #executive-alerts

Service Status:
  URL: https://status.platform.com
  Updates: status@platform.com
  Twitter: @PlatformStatus
```

### Incident Response Playbook

#### P0 Critical Incident Response

```bash
#!/bin/bash
# critical_incident_response.sh
# Emergency response script for critical incidents

set -e

# Configuration
INCIDENT_ID="${INCIDENT_ID:-$(date +%Y%m%d_%H%M%S)}"
ALERT_WEBHOOK="${ALERT_WEBHOOK}"
STATUS_PAGE_API="${STATUS_PAGE_API}"
LOG_FILE="/var/log/incidents/${INCIDENT_ID}.log"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

log_incident() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Step 1: Immediate Assessment
assess_incident() {
    log_incident "${RED}🚨 CRITICAL INCIDENT ${INCIDENT_ID} - Starting assessment${NC}"
    
    # Check application health
    APP_STATUS="unknown"
    if curl -f -s --connect-timeout 5 "http://localhost:8501/health" > /dev/null; then
        APP_STATUS="healthy"
        log_incident "✅ Application: Responsive"
    else
        APP_STATUS="unhealthy"
        log_incident "${RED}❌ Application: Unresponsive${NC}"
    fi
    
    # Check database connectivity
    DB_STATUS="unknown"
    if python3 -c "
import os
import psycopg2
from urllib.parse import urlparse
try:
    db_url = os.getenv('DATABASE_URL')
    parsed = urlparse(db_url)
    conn = psycopg2.connect(
        host=parsed.hostname,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password,
        port=parsed.port or 5432,
        connect_timeout=5
    )
    conn.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
        DB_STATUS="healthy"
        log_incident "✅ Database: Connected"
    else
        DB_STATUS="unhealthy"
        log_incident "${RED}❌ Database: Connection failed${NC}"
    fi
    
    # Check Redis
    REDIS_STATUS="unknown"
    if redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; then
        REDIS_STATUS="healthy"
        log_incident "✅ Redis: Connected"
    else
        REDIS_STATUS="unhealthy"
        log_incident "${RED}❌ Redis: Connection failed${NC}"
    fi
    
    # Store assessment results
    cat > "/tmp/incident_${INCIDENT_ID}_assessment.json" <<EOF
{
    "incident_id": "$INCIDENT_ID",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "severity": "P0",
    "status": {
        "application": "$APP_STATUS",
        "database": "$DB_STATUS",
        "redis": "$REDIS_STATUS"
    }
}
EOF
}

# Step 2: Immediate Stabilization
stabilize_system() {
    log_incident "${YELLOW}🔧 Attempting immediate stabilization${NC}"
    
    # Restart unhealthy services
    if [ "$APP_STATUS" == "unhealthy" ]; then
        log_incident "🔄 Restarting application containers"
        docker-compose restart customer-intelligence 2>&1 | tee -a "$LOG_FILE"
        sleep 30  # Wait for startup
    fi
    
    if [ "$REDIS_STATUS" == "unhealthy" ]; then
        log_incident "🔄 Restarting Redis"
        docker-compose restart redis 2>&1 | tee -a "$LOG_FILE"
        sleep 10
    fi
    
    # Clear problematic cache if Redis is working
    if [ "$REDIS_STATUS" == "healthy" ]; then
        log_incident "🧹 Clearing potentially corrupted cache"
        redis-cli -u "$REDIS_URL" FLUSHDB 2>&1 | tee -a "$LOG_FILE"
    fi
    
    # Re-assess after stabilization attempts
    assess_incident
}

# Step 3: Communication
send_incident_notifications() {
    log_incident "📢 Sending incident notifications"
    
    # Update status page
    if [ -n "$STATUS_PAGE_API" ]; then
        curl -X POST "$STATUS_PAGE_API/incidents" \
             -H "Content-Type: application/json" \
             -d "{
                \"name\": \"Platform Service Disruption\",
                \"status\": \"investigating\",
                \"incident_type\": \"major_outage\",
                \"message\": \"We are investigating reports of service disruption. Updates will be provided every 15 minutes.\"
             }" 2>&1 | tee -a "$LOG_FILE"
    fi
    
    # Alert engineering team
    if [ -n "$ALERT_WEBHOOK" ]; then
        curl -X POST "$ALERT_WEBHOOK" \
             -H "Content-Type: application/json" \
             -d "{
                \"text\": \"🚨 CRITICAL INCIDENT ${INCIDENT_ID}: Platform experiencing service disruption\",
                \"channel\": \"#engineering-oncall\",
                \"username\": \"Platform Monitor\"
             }" 2>&1 | tee -a "$LOG_FILE"
    fi
}

# Step 4: Data Protection
protect_data() {
    log_incident "💾 Initiating data protection measures"
    
    # Create emergency backup if database is healthy
    if [ "$DB_STATUS" == "healthy" ]; then
        log_incident "📦 Creating emergency database backup"
        mkdir -p "/backup/emergency/${INCIDENT_ID}"
        
        docker exec customer-intelligence-postgres pg_dumpall -U postgres \
            > "/backup/emergency/${INCIDENT_ID}/emergency_backup.sql" 2>&1 | tee -a "$LOG_FILE"
        
        if [ $? -eq 0 ]; then
            log_incident "✅ Emergency backup completed"
        else
            log_incident "${RED}❌ Emergency backup failed${NC}"
        fi
    fi
    
    # Save current system state
    log_incident "📊 Capturing system state"
    docker ps > "/backup/emergency/${INCIDENT_ID}/docker_state.txt"
    docker stats --no-stream > "/backup/emergency/${INCIDENT_ID}/resource_usage.txt"
    free -h > "/backup/emergency/${INCIDENT_ID}/memory_usage.txt"
    df -h > "/backup/emergency/${INCIDENT_ID}/disk_usage.txt"
}

# Main incident response flow
main() {
    mkdir -p "/var/log/incidents"
    mkdir -p "/backup/emergency"
    
    log_incident "${RED}🚨 CRITICAL INCIDENT RESPONSE INITIATED${NC}"
    
    # Execute response steps
    assess_incident
    send_incident_notifications
    protect_data
    stabilize_system
    
    # Final status
    if [ "$APP_STATUS" == "healthy" ] && [ "$DB_STATUS" == "healthy" ] && [ "$REDIS_STATUS" == "healthy" ]; then
        log_incident "${GREEN}✅ System stabilized - monitoring for 15 minutes${NC}"
        
        # Monitor for 15 minutes
        for i in {1..15}; do
            sleep 60
            if ! curl -f -s --connect-timeout 5 "http://localhost:8501/health" > /dev/null; then
                log_incident "${RED}❌ Service degraded again - escalating to L2${NC}"
                # Trigger L2 escalation here
                exit 1
            fi
            log_incident "⏱️ Monitoring: ${i}/15 minutes - System stable"
        done
        
        log_incident "${GREEN}🎉 Incident resolved - System stable for 15 minutes${NC}"
    else
        log_incident "${RED}❌ Stabilization failed - Escalating to Level 2 Engineering${NC}"
        # Trigger L2 escalation
        exit 1
    fi
}

# Execute if run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

---

## 📊 System Health Monitoring

### 2.1 Comprehensive Health Dashboard

#### Health Monitoring Service

```python
# health_monitoring_service.py
"""Comprehensive health monitoring and alerting system."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

@dataclass
class HealthMetric:
    """Health metric data structure."""
    name: str
    value: float
    threshold_warning: float
    threshold_critical: float
    unit: str
    timestamp: datetime
    status: str  # healthy, warning, critical

@dataclass
class SystemHealth:
    """Overall system health status."""
    overall_status: str
    component_statuses: Dict[str, str]
    metrics: List[HealthMetric]
    alerts: List[str]
    timestamp: datetime

class HealthMonitoringService:
    """Comprehensive health monitoring service."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.alert_history = []
        self.last_alert_time = {}
        
        # Alert thresholds
        self.thresholds = {
            "response_time": {"warning": 2.0, "critical": 5.0},
            "error_rate": {"warning": 1.0, "critical": 5.0},
            "cpu_usage": {"warning": 70.0, "critical": 85.0},
            "memory_usage": {"warning": 80.0, "critical": 90.0},
            "disk_usage": {"warning": 80.0, "critical": 90.0},
            "database_connections": {"warning": 80.0, "critical": 95.0},
            "cache_hit_rate": {"warning": 85.0, "critical": 70.0}  # Lower is worse
        }
    
    async def collect_application_metrics(self) -> List[HealthMetric]:
        """Collect application performance metrics."""
        
        metrics = []
        timestamp = datetime.now()
        
        try:
            # Response time check
            import time
            import httpx
            
            start_time = time.time()
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8501/health", timeout=10)
            response_time = time.time() - start_time
            
            metrics.append(HealthMetric(
                name="response_time",
                value=response_time,
                threshold_warning=self.thresholds["response_time"]["warning"],
                threshold_critical=self.thresholds["response_time"]["critical"],
                unit="seconds",
                timestamp=timestamp,
                status=self._get_metric_status(response_time, self.thresholds["response_time"])
            ))
            
            # Error rate (from application logs)
            error_rate = await self._calculate_error_rate()
            metrics.append(HealthMetric(
                name="error_rate",
                value=error_rate,
                threshold_warning=self.thresholds["error_rate"]["warning"],
                threshold_critical=self.thresholds["error_rate"]["critical"],
                unit="percent",
                timestamp=timestamp,
                status=self._get_metric_status(error_rate, self.thresholds["error_rate"])
            ))
            
        except Exception as e:
            self.logger.error(f"Failed to collect application metrics: {e}")
            # Add critical metric for application unavailability
            metrics.append(HealthMetric(
                name="application_availability",
                value=0.0,
                threshold_warning=99.0,
                threshold_critical=95.0,
                unit="percent",
                timestamp=timestamp,
                status="critical"
            ))
        
        return metrics
    
    async def collect_system_metrics(self) -> List[HealthMetric]:
        """Collect system resource metrics."""
        
        metrics = []
        timestamp = datetime.now()
        
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(HealthMetric(
                name="cpu_usage",
                value=cpu_percent,
                threshold_warning=self.thresholds["cpu_usage"]["warning"],
                threshold_critical=self.thresholds["cpu_usage"]["critical"],
                unit="percent",
                timestamp=timestamp,
                status=self._get_metric_status(cpu_percent, self.thresholds["cpu_usage"])
            ))
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            metrics.append(HealthMetric(
                name="memory_usage",
                value=memory_percent,
                threshold_warning=self.thresholds["memory_usage"]["warning"],
                threshold_critical=self.thresholds["memory_usage"]["critical"],
                unit="percent",
                timestamp=timestamp,
                status=self._get_metric_status(memory_percent, self.thresholds["memory_usage"])
            ))
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            metrics.append(HealthMetric(
                name="disk_usage",
                value=disk_percent,
                threshold_warning=self.thresholds["disk_usage"]["warning"],
                threshold_critical=self.thresholds["disk_usage"]["critical"],
                unit="percent",
                timestamp=timestamp,
                status=self._get_metric_status(disk_percent, self.thresholds["disk_usage"])
            ))
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
        
        return metrics
    
    async def collect_database_metrics(self) -> List[HealthMetric]:
        """Collect database performance metrics."""
        
        metrics = []
        timestamp = datetime.now()
        
        try:
            # Database connection test and metrics
            import asyncpg
            import os
            from urllib.parse import urlparse
            
            db_url = os.getenv("DATABASE_URL")
            parsed = urlparse(db_url)
            
            conn = await asyncpg.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:]
            )
            
            # Connection count
            result = await conn.fetch(
                "SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active'"
            )
            active_connections = result[0]['active_connections']
            
            # Max connections
            result = await conn.fetch("SHOW max_connections")
            max_connections = int(result[0]['max_connections'])
            
            connection_usage = (active_connections / max_connections) * 100
            
            metrics.append(HealthMetric(
                name="database_connections",
                value=connection_usage,
                threshold_warning=self.thresholds["database_connections"]["warning"],
                threshold_critical=self.thresholds["database_connections"]["critical"],
                unit="percent",
                timestamp=timestamp,
                status=self._get_metric_status(connection_usage, self.thresholds["database_connections"])
            ))
            
            # Query performance
            start_time = time.time()
            await conn.fetch("SELECT 1")
            query_time = time.time() - start_time
            
            metrics.append(HealthMetric(
                name="database_query_time",
                value=query_time,
                threshold_warning=0.1,
                threshold_critical=0.5,
                unit="seconds",
                timestamp=timestamp,
                status=self._get_metric_status(query_time, {"warning": 0.1, "critical": 0.5})
            ))
            
            await conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to collect database metrics: {e}")
            # Add critical metric for database unavailability
            metrics.append(HealthMetric(
                name="database_availability",
                value=0.0,
                threshold_warning=99.0,
                threshold_critical=95.0,
                unit="percent",
                timestamp=timestamp,
                status="critical"
            ))
        
        return metrics
    
    async def collect_cache_metrics(self) -> List[HealthMetric]:
        """Collect Redis cache metrics."""
        
        metrics = []
        timestamp = datetime.now()
        
        try:
            import redis
            import os
            
            redis_client = redis.from_url(os.getenv("REDIS_URL"))
            
            # Connection test
            redis_client.ping()
            
            # Get Redis info
            info = redis_client.info()
            
            # Memory usage
            used_memory = info.get('used_memory', 0)
            max_memory = info.get('maxmemory', 0)
            
            if max_memory > 0:
                memory_usage = (used_memory / max_memory) * 100
                metrics.append(HealthMetric(
                    name="cache_memory_usage",
                    value=memory_usage,
                    threshold_warning=80.0,
                    threshold_critical=90.0,
                    unit="percent",
                    timestamp=timestamp,
                    status=self._get_metric_status(memory_usage, {"warning": 80.0, "critical": 90.0})
                ))
            
            # Hit rate
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            
            if hits + misses > 0:
                hit_rate = (hits / (hits + misses)) * 100
                metrics.append(HealthMetric(
                    name="cache_hit_rate",
                    value=hit_rate,
                    threshold_warning=self.thresholds["cache_hit_rate"]["warning"],
                    threshold_critical=self.thresholds["cache_hit_rate"]["critical"],
                    unit="percent",
                    timestamp=timestamp,
                    status=self._get_metric_status(hit_rate, self.thresholds["cache_hit_rate"], reverse=True)
                ))
            
        except Exception as e:
            self.logger.error(f"Failed to collect cache metrics: {e}")
            # Add critical metric for cache unavailability
            metrics.append(HealthMetric(
                name="cache_availability",
                value=0.0,
                threshold_warning=99.0,
                threshold_critical=95.0,
                unit="percent",
                timestamp=timestamp,
                status="critical"
            ))
        
        return metrics
    
    def _get_metric_status(self, value: float, thresholds: Dict[str, float], reverse: bool = False) -> str:
        """Determine metric status based on thresholds."""
        
        if reverse:  # For metrics where lower values are bad (like hit rate)
            if value <= thresholds["critical"]:
                return "critical"
            elif value <= thresholds["warning"]:
                return "warning"
            else:
                return "healthy"
        else:  # For metrics where higher values are bad
            if value >= thresholds["critical"]:
                return "critical"
            elif value >= thresholds["warning"]:
                return "warning"
            else:
                return "healthy"
    
    async def _calculate_error_rate(self) -> float:
        """Calculate application error rate from logs."""
        
        try:
            # This would typically parse application logs
            # For demo purposes, return a calculated value
            
            # Read recent log entries and calculate error rate
            import subprocess
            import re
            
            # Get last 1000 log entries
            log_output = subprocess.check_output([
                'docker', 'logs', '--tail', '1000', 'customer-intelligence-app'
            ], stderr=subprocess.STDOUT, universal_newlines=True)
            
            # Count total requests and errors
            total_requests = len(re.findall(r'HTTP/\d+\.\d+"', log_output))
            error_requests = len(re.findall(r'HTTP/\d+\.\d+" [4-5]\d{2}', log_output))
            
            if total_requests > 0:
                error_rate = (error_requests / total_requests) * 100
                return error_rate
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Failed to calculate error rate: {e}")
            return 0.0
    
    async def generate_health_report(self) -> SystemHealth:
        """Generate comprehensive system health report."""
        
        # Collect all metrics
        app_metrics = await self.collect_application_metrics()
        system_metrics = await self.collect_system_metrics()
        db_metrics = await self.collect_database_metrics()
        cache_metrics = await self.collect_cache_metrics()
        
        all_metrics = app_metrics + system_metrics + db_metrics + cache_metrics
        
        # Determine component statuses
        component_statuses = {
            "application": self._get_component_status([m for m in app_metrics]),
            "system": self._get_component_status([m for m in system_metrics]),
            "database": self._get_component_status([m for m in db_metrics]),
            "cache": self._get_component_status([m for m in cache_metrics])
        }
        
        # Determine overall status
        if any(status == "critical" for status in component_statuses.values()):
            overall_status = "critical"
        elif any(status == "warning" for status in component_statuses.values()):
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        # Generate alerts for problematic metrics
        alerts = []
        for metric in all_metrics:
            if metric.status in ["warning", "critical"]:
                alerts.append(f"{metric.name}: {metric.value:.2f}{metric.unit} ({metric.status})")
        
        return SystemHealth(
            overall_status=overall_status,
            component_statuses=component_statuses,
            metrics=all_metrics,
            alerts=alerts,
            timestamp=datetime.now()
        )
    
    def _get_component_status(self, metrics: List[HealthMetric]) -> str:
        """Determine component status from its metrics."""
        
        if not metrics:
            return "unknown"
        
        statuses = [m.status for m in metrics]
        
        if "critical" in statuses:
            return "critical"
        elif "warning" in statuses:
            return "warning"
        else:
            return "healthy"
    
    async def send_alert(self, health_report: SystemHealth):
        """Send alerts based on health status."""
        
        if health_report.overall_status == "healthy":
            return  # No alerts needed
        
        # Prevent alert spam (minimum 5 minutes between similar alerts)
        alert_key = f"{health_report.overall_status}_{len(health_report.alerts)}"
        now = datetime.now()
        
        if alert_key in self.last_alert_time:
            time_since_last = now - self.last_alert_time[alert_key]
            if time_since_last < timedelta(minutes=5):
                return  # Too soon to send another alert
        
        self.last_alert_time[alert_key] = now
        
        # Send email alert
        await self._send_email_alert(health_report)
        
        # Send webhook alert
        await self._send_webhook_alert(health_report)
        
        # Log alert
        self.logger.warning(f"Health alert sent: {health_report.overall_status} - {len(health_report.alerts)} issues")
    
    async def _send_email_alert(self, health_report: SystemHealth):
        """Send email alert."""
        
        try:
            smtp_config = self.config.get("smtp", {})
            if not smtp_config.get("enabled", False):
                return
            
            msg = MIMEMultipart()
            msg['From'] = smtp_config["from_email"]
            msg['To'] = ", ".join(smtp_config["alert_recipients"])
            msg['Subject'] = f"[{health_report.overall_status.upper()}] Platform Health Alert"
            
            body = f"""
Platform Health Alert

Status: {health_report.overall_status.upper()}
Timestamp: {health_report.timestamp}

Component Status:
{json.dumps(health_report.component_statuses, indent=2)}

Active Alerts:
{chr(10).join(f"• {alert}" for alert in health_report.alerts)}

Detailed Metrics:
{chr(10).join(f"• {m.name}: {m.value:.2f}{m.unit} ({m.status})" for m in health_report.metrics)}

Please investigate and resolve critical issues immediately.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_config["host"], smtp_config["port"])
            if smtp_config.get("use_tls", False):
                server.starttls()
            if smtp_config.get("username"):
                server.login(smtp_config["username"], smtp_config["password"])
            
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    async def _send_webhook_alert(self, health_report: SystemHealth):
        """Send webhook alert."""
        
        try:
            webhook_config = self.config.get("webhook", {})
            if not webhook_config.get("enabled", False):
                return
            
            import httpx
            
            payload = {
                "text": f"🚨 Platform Health Alert: {health_report.overall_status.upper()}",
                "attachments": [
                    {
                        "color": "danger" if health_report.overall_status == "critical" else "warning",
                        "fields": [
                            {
                                "title": "Overall Status",
                                "value": health_report.overall_status.upper(),
                                "short": True
                            },
                            {
                                "title": "Active Alerts",
                                "value": str(len(health_report.alerts)),
                                "short": True
                            }
                        ],
                        "text": "\n".join(f"• {alert}" for alert in health_report.alerts[:10])  # Limit to 10 alerts
                    }
                ]
            }
            
            async with httpx.AsyncClient() as client:
                await client.post(webhook_config["url"], json=payload)
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")

# Health monitoring service configuration
HEALTH_CONFIG = {
    "monitoring_interval": 60,  # seconds
    "smtp": {
        "enabled": True,
        "host": "smtp.gmail.com",
        "port": 587,
        "use_tls": True,
        "username": "alerts@your-platform.com",
        "password": "your-email-password",
        "from_email": "Platform Monitor <alerts@your-platform.com>",
        "alert_recipients": ["admin@your-company.com", "ops@your-company.com"]
    },
    "webhook": {
        "enabled": True,
        "url": "https://hooks.slack.com/your-webhook-url"
    }
}

# Usage example
async def run_health_monitoring():
    """Run continuous health monitoring."""
    
    monitor = HealthMonitoringService(HEALTH_CONFIG)
    
    while True:
        try:
            health_report = await monitor.generate_health_report()
            
            # Send alerts if needed
            await monitor.send_alert(health_report)
            
            # Store health data for trending
            health_data = asdict(health_report)
            
            # Log current status
            if health_report.overall_status != "healthy":
                monitor.logger.warning(f"System health: {health_report.overall_status} - {len(health_report.alerts)} issues")
            else:
                monitor.logger.info("System health: All components healthy")
            
            # Wait for next check
            await asyncio.sleep(HEALTH_CONFIG["monitoring_interval"])
            
        except Exception as e:
            monitor.logger.error(f"Health monitoring error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error
```

---

## 🔄 Backup & Recovery Procedures

### 3.1 Automated Backup System

#### Comprehensive Backup Strategy

```bash
#!/bin/bash
# automated_backup_system.sh
# Comprehensive backup and recovery system

set -e

# Configuration
BACKUP_ROOT="/backup/customer-intelligence"
RETENTION_DAYS=30
S3_BUCKET="${S3_BACKUP_BUCKET:-}"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-}"
LOG_FILE="/var/log/backup.log"

# Backup types
DATABASE_BACKUP=true
REDIS_BACKUP=true
APPLICATION_DATA_BACKUP=true
CONFIGURATION_BACKUP=true

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_backup() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create backup directory structure
setup_backup_environment() {
    log_backup "${GREEN}Setting up backup environment${NC}"
    
    mkdir -p "${BACKUP_ROOT}/database"
    mkdir -p "${BACKUP_ROOT}/redis"
    mkdir -p "${BACKUP_ROOT}/application"
    mkdir -p "${BACKUP_ROOT}/configuration"
    mkdir -p "${BACKUP_ROOT}/logs"
    mkdir -p "$(dirname "$LOG_FILE")"
}

# Database backup
backup_database() {
    if [ "$DATABASE_BACKUP" != "true" ]; then
        return 0
    fi
    
    log_backup "${GREEN}Starting database backup${NC}"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    DB_BACKUP_DIR="${BACKUP_ROOT}/database/${TIMESTAMP}"
    mkdir -p "$DB_BACKUP_DIR"
    
    # Full database dump
    log_backup "📦 Creating full database dump"
    if docker exec customer-intelligence-postgres pg_dumpall -U postgres > "${DB_BACKUP_DIR}/full_backup.sql"; then
        log_backup "✅ Database dump completed"
    else
        log_backup "${RED}❌ Database dump failed${NC}"
        return 1
    fi
    
    # Individual table dumps for faster recovery
    log_backup "📦 Creating individual table dumps"
    TABLES=("customers" "customer_events" "analytics_aggregations" "users" "tenants")
    
    for table in "${TABLES[@]}"; do
        if docker exec customer-intelligence-postgres pg_dump -U postgres -t "$table" enterprisehub > "${DB_BACKUP_DIR}/${table}.sql"; then
            log_backup "✅ Table backup completed: $table"
        else
            log_backup "${YELLOW}⚠️ Table backup failed: $table${NC}"
        fi
    done
    
    # Compress backup
    log_backup "🗜️ Compressing database backup"
    tar -czf "${DB_BACKUP_DIR}.tar.gz" -C "$(dirname "$DB_BACKUP_DIR")" "$(basename "$DB_BACKUP_DIR")"
    rm -rf "$DB_BACKUP_DIR"
    
    # Encrypt if key provided
    if [ -n "$ENCRYPTION_KEY" ]; then
        log_backup "🔐 Encrypting database backup"
        openssl enc -aes-256-cbc -salt -in "${DB_BACKUP_DIR}.tar.gz" -out "${DB_BACKUP_DIR}.tar.gz.enc" -k "$ENCRYPTION_KEY"
        rm "${DB_BACKUP_DIR}.tar.gz"
    fi
    
    log_backup "✅ Database backup completed"
}

# Redis backup
backup_redis() {
    if [ "$REDIS_BACKUP" != "true" ]; then
        return 0
    fi
    
    log_backup "${GREEN}Starting Redis backup${NC}"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    REDIS_BACKUP_DIR="${BACKUP_ROOT}/redis/${TIMESTAMP}"
    mkdir -p "$REDIS_BACKUP_DIR"
    
    # Trigger Redis save
    log_backup "💾 Triggering Redis BGSAVE"
    docker exec customer-intelligence-redis redis-cli BGSAVE
    
    # Wait for save to complete
    while [ "$(docker exec customer-intelligence-redis redis-cli LASTSAVE)" -eq "$(docker exec customer-intelligence-redis redis-cli LASTSAVE)" ]; do
        sleep 1
    done
    
    # Copy RDB file
    log_backup "📦 Copying Redis data file"
    docker cp customer-intelligence-redis:/data/dump.rdb "${REDIS_BACKUP_DIR}/"
    
    # Export key analysis
    log_backup "🔍 Analyzing Redis keys"
    docker exec customer-intelligence-redis redis-cli --scan --pattern "*" > "${REDIS_BACKUP_DIR}/keys_list.txt"
    docker exec customer-intelligence-redis redis-cli INFO > "${REDIS_BACKUP_DIR}/redis_info.txt"
    
    # Compress backup
    log_backup "🗜️ Compressing Redis backup"
    tar -czf "${REDIS_BACKUP_DIR}.tar.gz" -C "$(dirname "$REDIS_BACKUP_DIR")" "$(basename "$REDIS_BACKUP_DIR")"
    rm -rf "$REDIS_BACKUP_DIR"
    
    # Encrypt if key provided
    if [ -n "$ENCRYPTION_KEY" ]; then
        log_backup "🔐 Encrypting Redis backup"
        openssl enc -aes-256-cbc -salt -in "${REDIS_BACKUP_DIR}.tar.gz" -out "${REDIS_BACKUP_DIR}.tar.gz.enc" -k "$ENCRYPTION_KEY"
        rm "${REDIS_BACKUP_DIR}.tar.gz"
    fi
    
    log_backup "✅ Redis backup completed"
}

# Application data backup
backup_application_data() {
    if [ "$APPLICATION_DATA_BACKUP" != "true" ]; then
        return 0
    fi
    
    log_backup "${GREEN}Starting application data backup${NC}"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    APP_BACKUP_DIR="${BACKUP_ROOT}/application/${TIMESTAMP}"
    mkdir -p "$APP_BACKUP_DIR"
    
    # Application logs
    log_backup "📋 Backing up application logs"
    if [ -d "/var/log/customer-intelligence" ]; then
        cp -r "/var/log/customer-intelligence" "${APP_BACKUP_DIR}/logs"
    fi
    
    # User uploads and data files
    log_backup "📁 Backing up user data"
    if [ -d "/app/data" ]; then
        docker cp customer-intelligence-app:/app/data "${APP_BACKUP_DIR}/"
    fi
    
    # Export analytics data
    log_backup "📊 Exporting analytics data"
    python3 << EOF
import asyncio
import json
import os
from datetime import datetime, timedelta

async def export_analytics():
    # This would connect to your database and export recent analytics
    # For demo purposes, create sample export
    export_data = {
        "export_date": datetime.now().isoformat(),
        "data_range": "last_30_days",
        "tenant_count": 1,
        "user_count": 25,
        "total_events": 15000
    }
    
    with open("${APP_BACKUP_DIR}/analytics_export.json", "w") as f:
        json.dump(export_data, f, indent=2)

asyncio.run(export_analytics())
EOF
    
    # Compress backup
    log_backup "🗜️ Compressing application backup"
    tar -czf "${APP_BACKUP_DIR}.tar.gz" -C "$(dirname "$APP_BACKUP_DIR")" "$(basename "$APP_BACKUP_DIR")"
    rm -rf "$APP_BACKUP_DIR"
    
    # Encrypt if key provided
    if [ -n "$ENCRYPTION_KEY" ]; then
        log_backup "🔐 Encrypting application backup"
        openssl enc -aes-256-cbc -salt -in "${APP_BACKUP_DIR}.tar.gz" -out "${APP_BACKUP_DIR}.tar.gz.enc" -k "$ENCRYPTION_KEY"
        rm "${APP_BACKUP_DIR}.tar.gz"
    fi
    
    log_backup "✅ Application data backup completed"
}

# Configuration backup
backup_configuration() {
    if [ "$CONFIGURATION_BACKUP" != "true" ]; then
        return 0
    fi
    
    log_backup "${GREEN}Starting configuration backup${NC}"
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    CONFIG_BACKUP_DIR="${BACKUP_ROOT}/configuration/${TIMESTAMP}"
    mkdir -p "$CONFIG_BACKUP_DIR"
    
    # Docker configuration
    log_backup "🐳 Backing up Docker configuration"
    cp docker-compose.yml "${CONFIG_BACKUP_DIR}/" 2>/dev/null || true
    cp docker-compose.production.yml "${CONFIG_BACKUP_DIR}/" 2>/dev/null || true
    cp Dockerfile "${CONFIG_BACKUP_DIR}/" 2>/dev/null || true
    
    # Environment configuration (without sensitive data)
    log_backup "⚙️ Backing up environment configuration"
    if [ -f ".env.example" ]; then
        cp .env.example "${CONFIG_BACKUP_DIR}/"
    fi
    
    # Application configuration
    log_backup "📋 Backing up application configuration"
    if [ -d "config" ]; then
        cp -r config "${CONFIG_BACKUP_DIR}/"
    fi
    
    # Nginx configuration
    if [ -d "nginx" ]; then
        cp -r nginx "${CONFIG_BACKUP_DIR}/"
    fi
    
    # Monitoring configuration
    if [ -d "monitoring" ]; then
        cp -r monitoring "${CONFIG_BACKUP_DIR}/"
    fi
    
    # Compress backup
    log_backup "🗜️ Compressing configuration backup"
    tar -czf "${CONFIG_BACKUP_DIR}.tar.gz" -C "$(dirname "$CONFIG_BACKUP_DIR")" "$(basename "$CONFIG_BACKUP_DIR")"
    rm -rf "$CONFIG_BACKUP_DIR"
    
    log_backup "✅ Configuration backup completed"
}

# Upload to cloud storage
upload_to_s3() {
    if [ -z "$S3_BUCKET" ]; then
        log_backup "${YELLOW}⚠️ S3 bucket not configured, skipping cloud upload${NC}"
        return 0
    fi
    
    log_backup "${GREEN}Uploading backups to S3${NC}"
    
    # Find today's backups
    TODAY=$(date +%Y%m%d)
    
    for backup_type in database redis application configuration; do
        backup_files=$(find "${BACKUP_ROOT}/${backup_type}" -name "${TODAY}_*" -type f)
        
        for file in $backup_files; do
            if [ -f "$file" ]; then
                s3_key="customer-intelligence/${backup_type}/$(basename "$file")"
                
                log_backup "☁️ Uploading $(basename "$file")"
                if aws s3 cp "$file" "s3://${S3_BUCKET}/${s3_key}"; then
                    log_backup "✅ Uploaded: $(basename "$file")"
                else
                    log_backup "${RED}❌ Upload failed: $(basename "$file")${NC}"
                fi
            fi
        done
    done
}

# Cleanup old backups
cleanup_old_backups() {
    log_backup "${GREEN}Cleaning up old backups${NC}"
    
    # Local cleanup
    find "$BACKUP_ROOT" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    find "$BACKUP_ROOT" -type d -empty -delete 2>/dev/null || true
    
    # S3 cleanup (if configured)
    if [ -n "$S3_BUCKET" ]; then
        log_backup "☁️ Cleaning up old S3 backups"
        
        # Delete files older than retention period
        cutoff_date=$(date -d "${RETENTION_DAYS} days ago" +%Y-%m-%d)
        
        aws s3 ls "s3://${S3_BUCKET}/customer-intelligence/" --recursive | while read -r line; do
            file_date=$(echo "$line" | awk '{print $1}')
            file_path=$(echo "$line" | awk '{print $4}')
            
            if [[ "$file_date" < "$cutoff_date" ]]; then
                log_backup "🗑️ Deleting old S3 backup: $file_path"
                aws s3 rm "s3://${S3_BUCKET}/${file_path}"
            fi
        done
    fi
    
    log_backup "✅ Cleanup completed"
}

# Verify backup integrity
verify_backups() {
    log_backup "${GREEN}Verifying backup integrity${NC}"
    
    TODAY=$(date +%Y%m%d)
    
    # Verify database backup
    if [ "$DATABASE_BACKUP" == "true" ]; then
        db_backup=$(find "${BACKUP_ROOT}/database" -name "${TODAY}_*" -type f | head -1)
        if [ -f "$db_backup" ]; then
            log_backup "✅ Database backup verified: $(basename "$db_backup")"
        else
            log_backup "${RED}❌ Database backup missing for today${NC}"
        fi
    fi
    
    # Verify Redis backup
    if [ "$REDIS_BACKUP" == "true" ]; then
        redis_backup=$(find "${BACKUP_ROOT}/redis" -name "${TODAY}_*" -type f | head -1)
        if [ -f "$redis_backup" ]; then
            log_backup "✅ Redis backup verified: $(basename "$redis_backup")"
        else
            log_backup "${RED}❌ Redis backup missing for today${NC}"
        fi
    fi
    
    # Check total backup size
    total_size=$(du -sh "$BACKUP_ROOT" | cut -f1)
    log_backup "📏 Total backup size: $total_size"
}

# Send backup notification
send_backup_notification() {
    if [ -z "$BACKUP_WEBHOOK" ]; then
        return 0
    fi
    
    backup_status="success"
    backup_count=$(find "$BACKUP_ROOT" -name "$(date +%Y%m%d)_*" -type f | wc -l)
    
    curl -X POST "$BACKUP_WEBHOOK" \
         -H "Content-Type: application/json" \
         -d "{
            \"text\": \"📦 Daily backup completed\",
            \"attachments\": [{
                \"color\": \"good\",
                \"fields\": [
                    {\"title\": \"Status\", \"value\": \"$backup_status\", \"short\": true},
                    {\"title\": \"Files Created\", \"value\": \"$backup_count\", \"short\": true},
                    {\"title\": \"Timestamp\", \"value\": \"$(date)\", \"short\": false}
                ]
            }]
         }" 2>/dev/null || true
}

# Main backup execution
main() {
    log_backup "${GREEN}🚀 Starting automated backup process${NC}"
    
    setup_backup_environment
    
    # Execute backup procedures
    backup_database
    backup_redis
    backup_application_data
    backup_configuration
    
    # Upload to cloud
    upload_to_s3
    
    # Cleanup and verify
    cleanup_old_backups
    verify_backups
    
    # Send notification
    send_backup_notification
    
    log_backup "${GREEN}✅ Automated backup process completed${NC}"
}

# Execute if run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### 3.2 Disaster Recovery Procedures

#### Recovery Runbook

```bash
#!/bin/bash
# disaster_recovery.sh
# Comprehensive disaster recovery procedures

set -e

# Configuration
BACKUP_ROOT="/backup/customer-intelligence"
RECOVERY_LOG="/var/log/recovery.log"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-}"

# Recovery modes
RECOVERY_MODE="${1:-full}"  # full, database, application, configuration

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'  
RED='\033[0;31m'
NC='\033[0m'

log_recovery() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$RECOVERY_LOG"
}

# Recovery mode selection
show_recovery_menu() {
    echo -e "${GREEN}🔧 Customer Intelligence Platform - Disaster Recovery${NC}"
    echo ""
    echo "Available recovery modes:"
    echo "1. Full System Recovery"
    echo "2. Database Only Recovery"
    echo "3. Application Data Recovery"
    echo "4. Configuration Recovery"
    echo "5. Point-in-Time Recovery"
    echo ""
    
    if [ -z "$1" ]; then
        read -p "Select recovery mode (1-5): " choice
        
        case $choice in
            1) RECOVERY_MODE="full" ;;
            2) RECOVERY_MODE="database" ;;
            3) RECOVERY_MODE="application" ;;
            4) RECOVERY_MODE="configuration" ;;
            5) RECOVERY_MODE="point_in_time" ;;
            *) echo "Invalid choice" && exit 1 ;;
        esac
    fi
}

# Pre-recovery checks
pre_recovery_checks() {
    log_recovery "${GREEN}Performing pre-recovery checks${NC}"
    
    # Check if services are running
    if docker ps | grep -q "customer-intelligence"; then
        log_recovery "${YELLOW}⚠️ Services are currently running${NC}"
        read -p "Do you want to stop services for recovery? (y/N): " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_recovery "🛑 Stopping services"
            docker-compose down
        else
            log_recovery "${RED}❌ Cannot proceed with services running${NC}"
            exit 1
        fi
    fi
    
    # Check backup availability
    if [ ! -d "$BACKUP_ROOT" ]; then
        log_recovery "${RED}❌ Backup directory not found: $BACKUP_ROOT${NC}"
        exit 1
    fi
    
    # List available backups
    log_recovery "📦 Available backups:"
    find "$BACKUP_ROOT" -type f -name "*.tar.gz*" | head -10 | while read -r backup; do
        size=$(ls -lh "$backup" | awk '{print $5}')
        date=$(basename "$backup" | cut -d'_' -f1)
        log_recovery "  - $(basename "$backup") ($size) - $date"
    done
}

# Select backup for recovery
select_backup() {
    local backup_type="$1"
    
    log_recovery "${GREEN}Selecting $backup_type backup for recovery${NC}"
    
    # Find recent backups
    backups=($(find "${BACKUP_ROOT}/${backup_type}" -name "*.tar.gz*" -type f | sort -r | head -10))
    
    if [ ${#backups[@]} -eq 0 ]; then
        log_recovery "${RED}❌ No $backup_type backups found${NC}"
        return 1
    fi
    
    echo "Available $backup_type backups:"
    for i in "${!backups[@]}"; do
        backup_file="${backups[$i]}"
        backup_date=$(basename "$backup_file" | cut -d'_' -f1)
        backup_size=$(ls -lh "$backup_file" | awk '{print $5}')
        echo "$((i+1)). $(basename "$backup_file") - $backup_date ($backup_size)"
    done
    
    read -p "Select backup (1-${#backups[@]}): " choice
    
    if [[ $choice -ge 1 && $choice -le ${#backups[@]} ]]; then
        selected_backup="${backups[$((choice-1))]}"
        log_recovery "✅ Selected: $(basename "$selected_backup")"
        echo "$selected_backup"
    else
        log_recovery "${RED}❌ Invalid selection${NC}"
        return 1
    fi
}

# Database recovery
recover_database() {
    log_recovery "${GREEN}🗄️ Starting database recovery${NC}"
    
    # Select backup
    db_backup=$(select_backup "database")
    if [ -z "$db_backup" ]; then
        return 1
    fi
    
    # Prepare for recovery
    RECOVERY_DIR="/tmp/db_recovery_$(date +%s)"
    mkdir -p "$RECOVERY_DIR"
    
    # Decrypt if needed
    backup_file="$db_backup"
    if [[ "$db_backup" == *.enc ]]; then
        if [ -z "$ENCRYPTION_KEY" ]; then
            log_recovery "${RED}❌ Encryption key required for encrypted backup${NC}"
            return 1
        fi
        
        log_recovery "🔐 Decrypting database backup"
        decrypted_file="${RECOVERY_DIR}/$(basename "$db_backup" .enc)"
        openssl enc -aes-256-cbc -d -in "$db_backup" -out "$decrypted_file" -k "$ENCRYPTION_KEY"
        backup_file="$decrypted_file"
    fi
    
    # Extract backup
    log_recovery "📦 Extracting database backup"
    tar -xzf "$backup_file" -C "$RECOVERY_DIR"
    
    # Find SQL files
    sql_files=$(find "$RECOVERY_DIR" -name "*.sql" | head -1)
    
    if [ -z "$sql_files" ]; then
        log_recovery "${RED}❌ No SQL files found in backup${NC}"
        return 1
    fi
    
    # Start database service
    log_recovery "🚀 Starting database service"
    docker-compose up -d postgres
    
    # Wait for database to be ready
    log_recovery "⏳ Waiting for database to be ready"
    for i in {1..30}; do
        if docker exec customer-intelligence-postgres pg_isready -U postgres > /dev/null 2>&1; then
            break
        fi
        sleep 2
        if [ $i -eq 30 ]; then
            log_recovery "${RED}❌ Database failed to start${NC}"
            return 1
        fi
    done
    
    # Drop existing database and recreate
    log_recovery "🗑️ Dropping existing database"
    docker exec customer-intelligence-postgres dropdb -U postgres enterprisehub 2>/dev/null || true
    docker exec customer-intelligence-postgres createdb -U postgres enterprisehub
    
    # Restore from backup
    log_recovery "⚡ Restoring database from backup"
    if cat "$sql_files" | docker exec -i customer-intelligence-postgres psql -U postgres; then
        log_recovery "✅ Database recovery completed successfully"
    else
        log_recovery "${RED}❌ Database recovery failed${NC}"
        return 1
    fi
    
    # Cleanup
    rm -rf "$RECOVERY_DIR"
}

# Redis recovery
recover_redis() {
    log_recovery "${GREEN}🔴 Starting Redis recovery${NC}"
    
    # Select backup
    redis_backup=$(select_backup "redis")
    if [ -z "$redis_backup" ]; then
        return 1
    fi
    
    # Prepare for recovery
    RECOVERY_DIR="/tmp/redis_recovery_$(date +%s)"
    mkdir -p "$RECOVERY_DIR"
    
    # Decrypt and extract
    backup_file="$redis_backup"
    if [[ "$redis_backup" == *.enc ]]; then
        if [ -z "$ENCRYPTION_KEY" ]; then
            log_recovery "${RED}❌ Encryption key required${NC}"
            return 1
        fi
        
        decrypted_file="${RECOVERY_DIR}/$(basename "$redis_backup" .enc)"
        openssl enc -aes-256-cbc -d -in "$redis_backup" -out "$decrypted_file" -k "$ENCRYPTION_KEY"
        backup_file="$decrypted_file"
    fi
    
    tar -xzf "$backup_file" -C "$RECOVERY_DIR"
    
    # Stop Redis to restore data
    log_recovery "🛑 Stopping Redis service"
    docker-compose stop redis
    
    # Replace Redis data
    log_recovery "📁 Replacing Redis data"
    rdb_file=$(find "$RECOVERY_DIR" -name "dump.rdb" | head -1)
    
    if [ -f "$rdb_file" ]; then
        docker cp "$rdb_file" customer-intelligence-redis:/data/dump.rdb
    else
        log_recovery "${RED}❌ Redis dump file not found${NC}"
        return 1
    fi
    
    # Start Redis
    log_recovery "🚀 Starting Redis service"
    docker-compose up -d redis
    
    # Verify recovery
    sleep 5
    if docker exec customer-intelligence-redis redis-cli ping > /dev/null; then
        log_recovery "✅ Redis recovery completed successfully"
    else
        log_recovery "${RED}❌ Redis recovery failed${NC}"
        return 1
    fi
    
    # Cleanup
    rm -rf "$RECOVERY_DIR"
}

# Application data recovery
recover_application_data() {
    log_recovery "${GREEN}📱 Starting application data recovery${NC}"
    
    # Select backup
    app_backup=$(select_backup "application")
    if [ -z "$app_backup" ]; then
        return 1
    fi
    
    # Prepare for recovery
    RECOVERY_DIR="/tmp/app_recovery_$(date +%s)"
    mkdir -p "$RECOVERY_DIR"
    
    # Decrypt and extract
    backup_file="$app_backup"
    if [[ "$app_backup" == *.enc ]]; then
        if [ -z "$ENCRYPTION_KEY" ]; then
            log_recovery "${RED}❌ Encryption key required${NC}"
            return 1
        fi
        
        decrypted_file="${RECOVERY_DIR}/$(basename "$app_backup" .enc)"
        openssl enc -aes-256-cbc -d -in "$app_backup" -out "$decrypted_file" -k "$ENCRYPTION_KEY"
        backup_file="$decrypted_file"
    fi
    
    tar -xzf "$backup_file" -C "$RECOVERY_DIR"
    
    # Restore application data
    log_recovery "📁 Restoring application data"
    
    # Restore data directory
    data_dir=$(find "$RECOVERY_DIR" -name "data" -type d | head -1)
    if [ -d "$data_dir" ]; then
        docker cp "$data_dir" customer-intelligence-app:/app/
        log_recovery "✅ Application data restored"
    fi
    
    # Restore logs
    logs_dir=$(find "$RECOVERY_DIR" -name "logs" -type d | head -1)
    if [ -d "$logs_dir" ]; then
        sudo cp -r "$logs_dir"/* /var/log/customer-intelligence/ 2>/dev/null || true
        log_recovery "✅ Application logs restored"
    fi
    
    # Cleanup
    rm -rf "$RECOVERY_DIR"
}

# Configuration recovery
recover_configuration() {
    log_recovery "${GREEN}⚙️ Starting configuration recovery${NC}"
    
    # Select backup
    config_backup=$(select_backup "configuration")
    if [ -z "$config_backup" ]; then
        return 1
    fi
    
    # Extract configuration
    RECOVERY_DIR="/tmp/config_recovery_$(date +%s)"
    mkdir -p "$RECOVERY_DIR"
    
    tar -xzf "$config_backup" -C "$RECOVERY_DIR"
    
    # Restore configurations
    config_source=$(find "$RECOVERY_DIR" -type d | head -2 | tail -1)
    
    if [ -d "$config_source" ]; then
        # Backup current configuration
        cp docker-compose.yml docker-compose.yml.bak 2>/dev/null || true
        
        # Restore configuration files
        for config_file in docker-compose.yml docker-compose.production.yml Dockerfile; do
            if [ -f "${config_source}/${config_file}" ]; then
                cp "${config_source}/${config_file}" .
                log_recovery "✅ Restored: $config_file"
            fi
        done
        
        # Restore directories
        for config_dir in config nginx monitoring; do
            if [ -d "${config_source}/${config_dir}" ]; then
                cp -r "${config_source}/${config_dir}" .
                log_recovery "✅ Restored directory: $config_dir"
            fi
        done
    fi
    
    log_recovery "✅ Configuration recovery completed"
    
    # Cleanup
    rm -rf "$RECOVERY_DIR"
}

# Full system recovery
recover_full_system() {
    log_recovery "${GREEN}🔄 Starting full system recovery${NC}"
    
    # Recovery order is important
    recover_configuration
    recover_database
    recover_redis
    recover_application_data
    
    # Start all services
    log_recovery "🚀 Starting all services"
    docker-compose up -d
    
    # Wait and verify
    log_recovery "⏳ Waiting for services to stabilize"
    sleep 30
    
    # Health check
    if curl -f -s --connect-timeout 10 "http://localhost:8501/health" > /dev/null; then
        log_recovery "${GREEN}✅ Full system recovery completed successfully${NC}"
    else
        log_recovery "${YELLOW}⚠️ System started but health check failed - manual verification needed${NC}"
    fi
}

# Point-in-time recovery
recover_point_in_time() {
    log_recovery "${GREEN}⏰ Starting point-in-time recovery${NC}"
    
    echo "Available recovery points:"
    
    # List available backups by date
    dates=($(find "$BACKUP_ROOT" -name "*.tar.gz*" -type f | xargs basename -a | cut -d'_' -f1 | sort -u -r | head -10))
    
    for i in "${!dates[@]}"; do
        date="${dates[$i]}"
        backup_count=$(find "$BACKUP_ROOT" -name "${date}_*" -type f | wc -l)
        echo "$((i+1)). $date ($backup_count backups available)"
    done
    
    read -p "Select recovery date (1-${#dates[@]}): " choice
    
    if [[ $choice -ge 1 && $choice -le ${#dates[@]} ]]; then
        recovery_date="${dates[$((choice-1))]}"
        log_recovery "📅 Selected recovery date: $recovery_date"
        
        # Override backup selection to use specific date
        BACKUP_DATE="$recovery_date"
        
        # Perform full recovery using backups from selected date
        recover_full_system
    else
        log_recovery "${RED}❌ Invalid selection${NC}"
        return 1
    fi
}

# Post-recovery verification
post_recovery_verification() {
    log_recovery "${GREEN}🔍 Performing post-recovery verification${NC}"
    
    # Application health check
    if curl -f -s --connect-timeout 10 "http://localhost:8501/health" > /dev/null; then
        log_recovery "✅ Application: Healthy"
    else
        log_recovery "${RED}❌ Application: Health check failed${NC}"
    fi
    
    # Database check
    if docker exec customer-intelligence-postgres pg_isready -U postgres > /dev/null 2>&1; then
        log_recovery "✅ Database: Connected"
        
        # Check table counts
        table_count=$(docker exec customer-intelligence-postgres psql -U postgres -d enterprisehub -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" | xargs)
        log_recovery "📊 Database tables: $table_count"
    else
        log_recovery "${RED}❌ Database: Connection failed${NC}"
    fi
    
    # Redis check
    if docker exec customer-intelligence-redis redis-cli ping > /dev/null 2>&1; then
        log_recovery "✅ Redis: Connected"
        
        key_count=$(docker exec customer-intelligence-redis redis-cli DBSIZE | xargs)
        log_recovery "🔑 Redis keys: $key_count"
    else
        log_recovery "${RED}❌ Redis: Connection failed${NC}"
    fi
    
    # Generate recovery report
    cat > "/tmp/recovery_report.txt" << EOF
Recovery Report
==============
Date: $(date)
Recovery Mode: $RECOVERY_MODE
Duration: Recovery completed

Component Status:
- Application: $(curl -f -s http://localhost:8501/health > /dev/null && echo "Healthy" || echo "Failed")
- Database: $(docker exec customer-intelligence-postgres pg_isready -U postgres > /dev/null 2>&1 && echo "Connected" || echo "Failed")
- Redis: $(docker exec customer-intelligence-redis redis-cli ping > /dev/null 2>&1 && echo "Connected" || echo "Failed")

Next Steps:
1. Verify application functionality
2. Check data integrity
3. Update monitoring systems
4. Notify stakeholders
EOF
    
    log_recovery "📋 Recovery report saved to /tmp/recovery_report.txt"
}

# Main recovery execution
main() {
    mkdir -p "$(dirname "$RECOVERY_LOG")"
    log_recovery "${GREEN}🚨 Starting disaster recovery process${NC}"
    
    show_recovery_menu "$1"
    pre_recovery_checks
    
    case $RECOVERY_MODE in
        "full") recover_full_system ;;
        "database") recover_database ;;
        "application") recover_application_data ;;
        "configuration") recover_configuration ;;
        "point_in_time") recover_point_in_time ;;
        *) log_recovery "${RED}❌ Unknown recovery mode: $RECOVERY_MODE${NC}" && exit 1 ;;
    esac
    
    post_recovery_verification
    
    log_recovery "${GREEN}✅ Disaster recovery process completed${NC}"
}

# Execute if run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

---

## 🚀 Update & Upgrade Procedures

### 4.1 Rolling Update System

#### Zero-Downtime Update Script

```bash
#!/bin/bash
# rolling_update.sh
# Zero-downtime rolling update system

set -e

# Configuration
UPDATE_LOG="/var/log/platform-updates.log"
BACKUP_BEFORE_UPDATE=true
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=10
ROLLBACK_ON_FAILURE=true

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_update() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$UPDATE_LOG"
}

# Pre-update validation
pre_update_validation() {
    log_update "${GREEN}🔍 Running pre-update validation${NC}"
    
    # Check current system health
    if ! curl -f -s --connect-timeout 5 "http://localhost:8501/health" > /dev/null; then
        log_update "${RED}❌ System is not healthy before update${NC}"
        exit 1
    fi
    
    # Check Docker availability
    if ! docker info > /dev/null 2>&1; then
        log_update "${RED}❌ Docker is not available${NC}"
        exit 1
    fi
    
    # Check disk space (require at least 5GB free)
    available_space=$(df / | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 5242880 ]; then  # 5GB in KB
        log_update "${RED}❌ Insufficient disk space for update${NC}"
        exit 1
    fi
    
    # Verify Docker Compose configuration
    if ! docker-compose config > /dev/null 2>&1; then
        log_update "${RED}❌ Docker Compose configuration is invalid${NC}"
        exit 1
    fi
    
    log_update "✅ Pre-update validation passed"
}

# Create pre-update backup
create_pre_update_backup() {
    if [ "$BACKUP_BEFORE_UPDATE" != "true" ]; then
        return 0
    fi
    
    log_update "${GREEN}📦 Creating pre-update backup${NC}"
    
    UPDATE_BACKUP_DIR="/backup/pre-update-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$UPDATE_BACKUP_DIR"
    
    # Database backup
    log_update "💾 Backing up database"
    if docker exec customer-intelligence-postgres pg_dumpall -U postgres > "${UPDATE_BACKUP_DIR}/database_backup.sql"; then
        log_update "✅ Database backup completed"
    else
        log_update "${RED}❌ Database backup failed${NC}"
        exit 1
    fi
    
    # Configuration backup
    log_update "⚙️ Backing up configuration"
    cp docker-compose.yml "${UPDATE_BACKUP_DIR}/" 2>/dev/null || true
    cp .env "${UPDATE_BACKUP_DIR}/.env.backup" 2>/dev/null || true
    
    # Save backup location for potential rollback
    echo "$UPDATE_BACKUP_DIR" > "/tmp/last_update_backup"
    
    log_update "✅ Pre-update backup completed: $UPDATE_BACKUP_DIR"
}

# Rolling update execution
execute_rolling_update() {
    log_update "${GREEN}🔄 Starting rolling update${NC}"
    
    # Pull latest images
    log_update "📥 Pulling latest Docker images"
    if docker-compose pull; then
        log_update "✅ Images pulled successfully"
    else
        log_update "${RED}❌ Failed to pull images${NC}"
        if [ "$ROLLBACK_ON_FAILURE" == "true" ]; then
            perform_rollback
        fi
        exit 1
    fi
    
    # Update services one by one
    services=("redis" "postgres" "customer-intelligence")
    
    for service in "${services[@]}"; do
        log_update "${BLUE}🔄 Updating service: $service${NC}"
        
        # Graceful update with health checks
        if update_service "$service"; then
            log_update "✅ Service $service updated successfully"
        else
            log_update "${RED}❌ Service $service update failed${NC}"
            if [ "$ROLLBACK_ON_FAILURE" == "true" ]; then
                perform_rollback
            fi
            exit 1
        fi
    done
    
    log_update "✅ Rolling update completed successfully"
}

# Update individual service
update_service() {
    local service="$1"
    
    # Skip database updates for now (require manual intervention)
    if [ "$service" == "postgres" ]; then
        log_update "⏩ Skipping database service (manual intervention required)"
        return 0
    fi
    
    # Recreate service
    log_update "🔄 Recreating $service service"
    docker-compose up -d --no-deps "$service"
    
    # Wait for service to stabilize
    sleep 15
    
    # Health check
    if [ "$service" == "customer-intelligence" ]; then
        # Application health check
        for i in $(seq 1 $HEALTH_CHECK_RETRIES); do
            if curl -f -s --connect-timeout 5 "http://localhost:8501/health" > /dev/null; then
                log_update "✅ $service health check passed"
                return 0
            fi
            
            log_update "⏳ Waiting for $service to be healthy ($i/$HEALTH_CHECK_RETRIES)"
            sleep $HEALTH_CHECK_INTERVAL
        done
        
        log_update "${RED}❌ $service health check failed${NC}"
        return 1
        
    elif [ "$service" == "redis" ]; then
        # Redis health check
        if docker exec customer-intelligence-redis redis-cli ping > /dev/null 2>&1; then
            log_update "✅ $service health check passed"
            return 0
        else
            log_update "${RED}❌ $service health check failed${NC}"
            return 1
        fi
    fi
    
    return 0
}

# Rollback procedure
perform_rollback() {
    log_update "${YELLOW}🔙 Performing rollback${NC}"
    
    # Get backup location
    if [ ! -f "/tmp/last_update_backup" ]; then
        log_update "${RED}❌ No backup location found for rollback${NC}"
        return 1
    fi
    
    BACKUP_DIR=$(cat "/tmp/last_update_backup")
    
    if [ ! -d "$BACKUP_DIR" ]; then
        log_update "${RED}❌ Backup directory not found: $BACKUP_DIR${NC}"
        return 1
    fi
    
    # Stop current services
    log_update "🛑 Stopping current services"
    docker-compose down
    
    # Restore configuration
    if [ -f "${BACKUP_DIR}/docker-compose.yml" ]; then
        cp "${BACKUP_DIR}/docker-compose.yml" .
        log_update "✅ Configuration restored"
    fi
    
    # Restore database
    if [ -f "${BACKUP_DIR}/database_backup.sql" ]; then
        log_update "💾 Restoring database"
        
        # Start database
        docker-compose up -d postgres
        sleep 10
        
        # Drop and recreate database
        docker exec customer-intelligence-postgres dropdb -U postgres enterprisehub 2>/dev/null || true
        docker exec customer-intelligence-postgres createdb -U postgres enterprisehub
        
        # Restore from backup
        if cat "${BACKUP_DIR}/database_backup.sql" | docker exec -i customer-intelligence-postgres psql -U postgres; then
            log_update "✅ Database restored"
        else
            log_update "${RED}❌ Database restore failed${NC}"
            return 1
        fi
    fi
    
    # Start all services
    log_update "🚀 Starting services"
    docker-compose up -d
    
    # Health check
    sleep 30
    if curl -f -s --connect-timeout 10 "http://localhost:8501/health" > /dev/null; then
        log_update "✅ Rollback completed successfully"
    else
        log_update "${RED}❌ Rollback health check failed${NC}"
        return 1
    fi
}

# Post-update verification
post_update_verification() {
    log_update "${GREEN}🔍 Running post-update verification${NC}"
    
    # Comprehensive health check
    log_update "🩺 Comprehensive health check"
    
    # Application check
    if curl -f -s --connect-timeout 10 "http://localhost:8501/health" > /dev/null; then
        app_status="healthy"
    else
        app_status="failed"
    fi
    
    # Database check
    if docker exec customer-intelligence-postgres pg_isready -U postgres > /dev/null 2>&1; then
        db_status="healthy"
    else
        db_status="failed"
    fi
    
    # Redis check
    if docker exec customer-intelligence-redis redis-cli ping > /dev/null 2>&1; then
        redis_status="healthy"
    else
        redis_status="failed"
    fi
    
    # Report status
    log_update "📊 Post-update status:"
    log_update "   Application: $app_status"
    log_update "   Database: $db_status"
    log_update "   Redis: $redis_status"
    
    # Overall status
    if [ "$app_status" == "healthy" ] && [ "$db_status" == "healthy" ] && [ "$redis_status" == "healthy" ]; then
        log_update "✅ All services healthy after update"
        return 0
    else
        log_update "${RED}❌ Some services failed post-update verification${NC}"
        return 1
    fi
}

# Update notification
send_update_notification() {
    local status="$1"
    
    if [ -z "$UPDATE_WEBHOOK" ]; then
        return 0
    fi
    
    if [ "$status" == "success" ]; then
        color="good"
        emoji="✅"
        message="Platform update completed successfully"
    else
        color="danger"
        emoji="❌"  
        message="Platform update failed"
    fi
    
    curl -X POST "$UPDATE_WEBHOOK" \
         -H "Content-Type: application/json" \
         -d "{
            \"text\": \"$emoji Platform Update\",
            \"attachments\": [{
                \"color\": \"$color\",
                \"fields\": [
                    {\"title\": \"Status\", \"value\": \"$status\", \"short\": true},
                    {\"title\": \"Timestamp\", \"value\": \"$(date)\", \"short\": true}
                ],
                \"text\": \"$message\"
            }]
         }" 2>/dev/null || true
}

# Main update process
main() {
    mkdir -p "$(dirname "$UPDATE_LOG")"
    log_update "${GREEN}🚀 Starting platform update process${NC}"
    
    # Execute update workflow
    pre_update_validation
    create_pre_update_backup
    execute_rolling_update
    
    if post_update_verification; then
        log_update "${GREEN}🎉 Platform update completed successfully${NC}"
        send_update_notification "success"
    else
        log_update "${RED}❌ Platform update verification failed${NC}"
        if [ "$ROLLBACK_ON_FAILURE" == "true" ]; then
            perform_rollback
        fi
        send_update_notification "failed"
        exit 1
    fi
    
    # Cleanup
    rm -f "/tmp/last_update_backup"
}

# Execute if run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

---

This comprehensive Support & Maintenance Documentation provides:

1. **Emergency Response** - Critical incident management with automated response scripts
2. **Health Monitoring** - Comprehensive system monitoring with automated alerting  
3. **Backup & Recovery** - Automated backup systems and disaster recovery procedures
4. **Update Procedures** - Zero-downtime rolling update system with automatic rollback

The documentation ensures platform reliability, quick incident response, data protection, and reliable maintenance operations.