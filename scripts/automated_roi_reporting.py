#!/usr/bin/env python3
"""
Automated ROI Reporting System
=============================

Automated business impact reporting for Phase 3 deployment:
- Daily ROI calculations and alerts
- Weekly executive summaries
- Performance threshold monitoring
- Automated email reports
- Slack notifications
- Emergency escalation protocols

Usage:
    python scripts/automated_roi_reporting.py --mode daily
    python scripts/automated_roi_reporting.py --mode weekly --email
    python scripts/automated_roi_reporting.py --mode monitor --continuous
"""

import asyncio
import asyncpg
import smtplib
import logging
import argparse
import json
import schedule
import time
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import requests
import os
import sys
from pathlib import Path
from jinja2 import Template
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from io import BytesIO
import base64

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.calculate_business_impact import BusinessImpactCalculator, BusinessImpactResult
from config.database import get_database_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutomatedReportingSystem:
    """Automated ROI reporting and alerting system."""

    def __init__(self):
        self.database_url = get_database_url()
        self.calculator = BusinessImpactCalculator(self.database_url)

        # Configuration from environment
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'email_user': os.getenv('EMAIL_USER'),
            'email_password': os.getenv('EMAIL_PASSWORD'),
            'from_email': os.getenv('FROM_EMAIL', 'noreply@enterprisehub.ai')
        }

        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')

        # Alert thresholds from deployment plan
        self.thresholds = {
            'roi_critical': 200,  # Below 200% ROI is critical
            'roi_warning': 500,   # Below 500% ROI is warning
            'roi_excellent': 710, # Above 710% ROI is excellent

            'websocket_warning': 100,   # Above 100ms is warning
            'websocket_critical': 200,  # Above 200ms is critical

            'error_rate_warning': 2.0,   # Above 2% error rate is warning
            'error_rate_critical': 5.0,  # Above 5% error rate is critical

            'uptime_warning': 99.5,      # Below 99.5% uptime is warning
            'uptime_critical': 99.0,     # Below 99% uptime is critical

            'adoption_warning': 60,      # Below 60% adoption is warning
            'adoption_critical': 40,     # Below 40% adoption is critical

            'revenue_drop_warning': 0.15, # 15% revenue drop is warning
            'revenue_drop_critical': 0.30 # 30% revenue drop is critical
        }

        # Notification recipients
        self.notification_config = {
            'daily_reports': ['ops-team@company.com', 'product@company.com'],
            'weekly_reports': ['executives@company.com', 'leadership@company.com'],
            'critical_alerts': ['on-call@company.com', 'cto@company.com'],
            'slack_channels': {
                'alerts': '#phase3-alerts',
                'reports': '#phase3-reports',
                'deployment': '#phase3-deployment'
            }
        }

    async def get_database_connection(self):
        """Get database connection."""
        return await asyncpg.connect(self.database_url)

    async def check_performance_thresholds(self, impact_result: BusinessImpactResult) -> List[Dict]:
        """Check performance against thresholds and generate alerts."""
        alerts = []

        # ROI Checks
        roi = float(impact_result.roi_percentage)
        if roi < self.thresholds['roi_critical']:
            alerts.append({
                'type': 'critical',
                'category': 'roi',
                'message': f"CRITICAL: ROI at {roi:.1f}% (below {self.thresholds['roi_critical']}% threshold)",
                'value': roi,
                'threshold': self.thresholds['roi_critical'],
                'impact': 'high'
            })
        elif roi < self.thresholds['roi_warning']:
            alerts.append({
                'type': 'warning',
                'category': 'roi',
                'message': f"WARNING: ROI at {roi:.1f}% (below {self.thresholds['roi_warning']}% target)",
                'value': roi,
                'threshold': self.thresholds['roi_warning'],
                'impact': 'medium'
            })

        # Performance Checks
        avg_latency = impact_result.avg_response_time_ms
        if avg_latency > self.thresholds['websocket_critical']:
            alerts.append({
                'type': 'critical',
                'category': 'performance',
                'message': f"CRITICAL: Average response time {avg_latency:.1f}ms (above {self.thresholds['websocket_critical']}ms threshold)",
                'value': avg_latency,
                'threshold': self.thresholds['websocket_critical'],
                'impact': 'high'
            })
        elif avg_latency > self.thresholds['websocket_warning']:
            alerts.append({
                'type': 'warning',
                'category': 'performance',
                'message': f"WARNING: Average response time {avg_latency:.1f}ms (above {self.thresholds['websocket_warning']}ms target)",
                'value': avg_latency,
                'threshold': self.thresholds['websocket_warning'],
                'impact': 'medium'
            })

        # Error Rate Checks
        error_rate = impact_result.error_rate * 100
        if error_rate > self.thresholds['error_rate_critical']:
            alerts.append({
                'type': 'critical',
                'category': 'reliability',
                'message': f"CRITICAL: Error rate at {error_rate:.2f}% (above {self.thresholds['error_rate_critical']}% threshold)",
                'value': error_rate,
                'threshold': self.thresholds['error_rate_critical'],
                'impact': 'high'
            })
        elif error_rate > self.thresholds['error_rate_warning']:
            alerts.append({
                'type': 'warning',
                'category': 'reliability',
                'message': f"WARNING: Error rate at {error_rate:.2f}% (above {self.thresholds['error_rate_warning']}% target)",
                'value': error_rate,
                'threshold': self.thresholds['error_rate_warning'],
                'impact': 'medium'
            })

        # Uptime Checks
        uptime = impact_result.uptime_percentage
        if uptime < self.thresholds['uptime_critical']:
            alerts.append({
                'type': 'critical',
                'category': 'reliability',
                'message': f"CRITICAL: Uptime at {uptime:.2f}% (below {self.thresholds['uptime_critical']}% threshold)",
                'value': uptime,
                'threshold': self.thresholds['uptime_critical'],
                'impact': 'high'
            })
        elif uptime < self.thresholds['uptime_warning']:
            alerts.append({
                'type': 'warning',
                'category': 'reliability',
                'message': f"WARNING: Uptime at {uptime:.2f}% (below {self.thresholds['uptime_warning']}% target)",
                'value': uptime,
                'threshold': self.thresholds['uptime_warning'],
                'impact': 'medium'
            })

        # Feature Adoption Checks
        features = [
            ('Real-Time Intelligence', impact_result.lead_intelligence.adoption_rate),
            ('Property Intelligence', impact_result.property_intelligence.adoption_rate),
            ('Churn Prevention', impact_result.churn_prevention.adoption_rate),
            ('AI Coaching', impact_result.ai_coaching.adoption_rate)
        ]

        for feature_name, adoption_rate in features:
            adoption_pct = adoption_rate * 100
            if adoption_pct < self.thresholds['adoption_critical']:
                alerts.append({
                    'type': 'critical',
                    'category': 'adoption',
                    'message': f"CRITICAL: {feature_name} adoption at {adoption_pct:.1f}% (below {self.thresholds['adoption_critical']}% threshold)",
                    'value': adoption_pct,
                    'threshold': self.thresholds['adoption_critical'],
                    'impact': 'high',
                    'feature': feature_name
                })
            elif adoption_pct < self.thresholds['adoption_warning']:
                alerts.append({
                    'type': 'warning',
                    'category': 'adoption',
                    'message': f"WARNING: {feature_name} adoption at {adoption_pct:.1f}% (below {self.thresholds['adoption_warning']}% target)",
                    'value': adoption_pct,
                    'threshold': self.thresholds['adoption_warning'],
                    'impact': 'medium',
                    'feature': feature_name
                })

        return alerts

    async def store_alerts(self, alerts: List[Dict], impact_result: BusinessImpactResult):
        """Store alerts in database."""
        if not alerts:
            return

        conn = await self.get_database_connection()
        try:
            for alert in alerts:
                query = """
                INSERT INTO business_impact_alerts (
                    alert_type, severity, feature_name, message,
                    current_value, threshold_value
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """

                await conn.execute(
                    query,
                    alert['category'],
                    alert['type'],
                    alert.get('feature'),
                    alert['message'],
                    alert['value'],
                    alert['threshold']
                )

            logger.info(f"Stored {len(alerts)} alerts in database")

        finally:
            await conn.close()

    async def send_slack_notification(self, message: str, channel: str = 'alerts', severity: str = 'info'):
        """Send notification to Slack."""
        if not self.slack_webhook_url:
            logger.warning("No Slack webhook URL configured")
            return

        # Color coding based on severity
        color_map = {
            'critical': '#dc2626',  # Red
            'warning': '#f59e0b',   # Yellow
            'info': '#2563eb',      # Blue
            'success': '#10b981'    # Green
        }

        payload = {
            'channel': self.notification_config['slack_channels'].get(channel, '#general'),
            'username': 'Phase3-ROI-Bot',
            'icon_emoji': ':chart_with_upwards_trend:',
            'attachments': [{
                'color': color_map.get(severity, '#2563eb'),
                'text': message,
                'footer': 'EnterpriseHub Phase 3 ROI System',
                'ts': int(time.time())
            }]
        }

        try:
            response = requests.post(self.slack_webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"Slack notification sent successfully to {channel}")
            else:
                logger.error(f"Failed to send Slack notification: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")

    async def send_email_report(self, subject: str, html_content: str, recipients: List[str],
                              attachments: List[Dict] = None):
        """Send email report."""
        if not self.email_config['email_user'] or not self.email_config['email_password']:
            logger.warning("Email credentials not configured")
            return

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config['from_email']
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject

            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment["filename"]}'
                    )
                    msg.attach(part)

            # Send email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['email_user'], self.email_config['email_password'])

            text = msg.as_string()
            server.sendmail(self.email_config['from_email'], recipients, text)
            server.quit()

            logger.info(f"Email report sent successfully to {len(recipients)} recipients")

        except Exception as e:
            logger.error(f"Error sending email report: {e}")

    def create_performance_chart(self, daily_data: List[Dict]) -> str:
        """Create performance chart and return as base64 string."""
        if not daily_data:
            return ""

        # Create DataFrame
        df = pd.DataFrame(daily_data)
        df['date'] = pd.to_datetime(df['date'])

        # Set up the plot style
        plt.style.use('seaborn-v0_8')
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

        # ROI Trend
        roi_values = [float(row.get('net_roi_percentage', 0)) * 100 for row in daily_data]
        ax1.plot(df['date'], roi_values, marker='o', linewidth=2, markersize=6, color='#2563eb')
        ax1.axhline(y=710, color='green', linestyle='--', label='Target ROI (710%)')
        ax1.set_title('Daily ROI Trend', fontsize=14, fontweight='bold')
        ax1.set_ylabel('ROI %')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Revenue Impact
        revenue_values = [float(row.get('total_revenue_impact', 0)) for row in daily_data]
        cost_values = [float(row.get('total_operating_cost', 0)) for row in daily_data]

        ax2.bar(df['date'], revenue_values, label='Revenue', alpha=0.8, color='#10b981')
        ax2.bar(df['date'], cost_values, label='Costs', alpha=0.8, color='#ef4444')
        ax2.set_title('Revenue vs Costs', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Amount ($)')
        ax2.legend()

        # Performance Metrics
        performance_metrics = {
            'WebSocket': [float(row.get('websocket_avg_latency_ms', 0)) for row in daily_data],
            'ML Inference': [float(row.get('ml_inference_avg_latency_ms', 0)) for row in daily_data],
            'Vision Analysis': [float(row.get('vision_analysis_avg_time_ms', 0)) for row in daily_data],
            'Coaching': [float(row.get('coaching_analysis_avg_time_ms', 0)) for row in daily_data]
        }

        for metric, values in performance_metrics.items():
            if any(v > 0 for v in values):  # Only plot if we have data
                ax3.plot(df['date'], values, marker='o', label=metric, linewidth=2)

        ax3.set_title('Performance Latency Trends', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Latency (ms)')
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # Adoption Rates
        adoption_data = {
            'Real-Time Intelligence': [float(row.get('real_time_intelligence_adoption_rate', 0)) * 100 for row in daily_data],
            'Property Intelligence': [float(row.get('property_vision_adoption_rate', 0)) * 100 for row in daily_data],
            'Churn Prevention': [float(row.get('churn_prevention_adoption_rate', 0)) * 100 for row in daily_data],
            'AI Coaching': [float(row.get('ai_coaching_adoption_rate', 0)) * 100 for row in daily_data]
        }

        for feature, values in adoption_data.items():
            if any(v > 0 for v in values):  # Only plot if we have data
                ax4.plot(df['date'], values, marker='o', label=feature, linewidth=2)

        ax4.axhline(y=80, color='green', linestyle='--', label='Target (80%)')
        ax4.set_title('Feature Adoption Rates', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Adoption Rate %')
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        plt.tight_layout()

        # Convert to base64 string
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        return image_base64

    async def generate_daily_report(self, target_date: date = None, send_email: bool = False):
        """Generate daily ROI report."""
        if target_date is None:
            target_date = date.today()

        logger.info(f"Generating daily report for {target_date}")

        # Calculate business impact for the day
        impact_result = await self.calculator.calculate_daily_business_impact(target_date)

        # Check for alerts
        alerts = await self.check_performance_thresholds(impact_result)

        # Store alerts if any
        if alerts:
            await self.store_alerts(alerts, impact_result)

        # Get recent data for trends
        conn = await self.get_database_connection()
        try:
            query = """
            SELECT * FROM business_metrics_daily
            WHERE date >= $1 - INTERVAL '7 days'
            ORDER BY date DESC
            """
            recent_data = await conn.fetch(query, target_date)
            daily_data = [dict(row) for row in recent_data]
        finally:
            await conn.close()

        # Create performance chart
        chart_base64 = self.create_performance_chart(daily_data)

        # Generate HTML report
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .header { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }
                .metric-card { background: white; border-radius: 8px; padding: 20px; margin: 15px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .metric-value { font-size: 24px; font-weight: bold; color: #2563eb; }
                .alert-critical { background-color: #fee2e2; border-left: 4px solid #dc2626; padding: 15px; margin: 10px 0; }
                .alert-warning { background-color: #fef3c7; border-left: 4px solid #d97706; padding: 15px; margin: 10px 0; }
                .success { background-color: #dcfce7; border-left: 4px solid #16a34a; padding: 15px; margin: 10px 0; }
                .feature-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
                .chart-container { text-align: center; margin: 20px 0; }
                table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
                th { background-color: #f2f2f2; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Phase 3 Daily ROI Report</h1>
                <h3>{{ report_date }}</h3>
                <p>Real-time Business Impact Analysis</p>
            </div>

            {% if alerts %}
            <div class="metric-card">
                <h2>🚨 Active Alerts</h2>
                {% for alert in alerts %}
                <div class="alert-{{ alert.type }}">
                    <strong>{{ alert.message }}</strong>
                </div>
                {% endfor %}
            </div>
            {% endif %}

            <div class="metric-card">
                <h2>💰 Financial Performance Summary</h2>
                <div class="feature-grid">
                    <div>
                        <h4>Total Revenue Impact</h4>
                        <div class="metric-value">${{ total_revenue_impact }}</div>
                        <p>Annualized: ${{ (total_revenue_impact * 365)|round(0) }}K</p>
                    </div>
                    <div>
                        <h4>Operating Costs</h4>
                        <div class="metric-value">${{ total_operating_costs }}</div>
                        <p>Annualized: ${{ (total_operating_costs * 365 / 1000)|round(0) }}K</p>
                    </div>
                    <div>
                        <h4>Net Revenue</h4>
                        <div class="metric-value">${{ net_revenue }}</div>
                        <p>Annualized: ${{ (net_revenue * 365 / 1000)|round(0) }}K</p>
                    </div>
                    <div>
                        <h4>ROI Percentage</h4>
                        <div class="metric-value">{{ roi_percentage }}%</div>
                        <p>Target: 710%</p>
                    </div>
                </div>
            </div>

            <div class="metric-card">
                <h2>🚀 Feature Performance Breakdown</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Feature</th>
                            <th>Usage</th>
                            <th>Revenue Impact</th>
                            <th>Performance</th>
                            <th>Adoption Rate</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>Real-Time Intelligence</td>
                            <td>{{ lead_intelligence.usage_count }}</td>
                            <td>${{ lead_intelligence.revenue_impact }}</td>
                            <td>{{ lead_intelligence.performance_ms }}ms</td>
                            <td>{{ (lead_intelligence.adoption_rate * 100)|round(1) }}%</td>
                        </tr>
                        <tr>
                            <td>Property Intelligence</td>
                            <td>{{ property_intelligence.usage_count }}</td>
                            <td>${{ property_intelligence.revenue_impact }}</td>
                            <td>{{ property_intelligence.performance_ms }}ms</td>
                            <td>{{ (property_intelligence.adoption_rate * 100)|round(1) }}%</td>
                        </tr>
                        <tr>
                            <td>Churn Prevention</td>
                            <td>{{ churn_prevention.usage_count }}</td>
                            <td>${{ churn_prevention.revenue_impact }}</td>
                            <td>{{ churn_prevention.performance_ms }}ms</td>
                            <td>{{ (churn_prevention.adoption_rate * 100)|round(1) }}%</td>
                        </tr>
                        <tr>
                            <td>AI Coaching</td>
                            <td>{{ ai_coaching.usage_count }}</td>
                            <td>${{ ai_coaching.revenue_impact }}</td>
                            <td>{{ ai_coaching.performance_ms }}ms</td>
                            <td>{{ (ai_coaching.adoption_rate * 100)|round(1) }}%</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="metric-card">
                <h2>⚡ System Performance</h2>
                <div class="feature-grid">
                    <div>
                        <h4>Average Response Time</h4>
                        <div class="metric-value">{{ avg_response_time_ms }}ms</div>
                    </div>
                    <div>
                        <h4>Error Rate</h4>
                        <div class="metric-value">{{ (error_rate * 100)|round(3) }}%</div>
                    </div>
                    <div>
                        <h4>System Uptime</h4>
                        <div class="metric-value">{{ uptime_percentage }}%</div>
                    </div>
                    <div>
                        <h4>Health Status</h4>
                        <div class="metric-value">{{ health_status }}</div>
                    </div>
                </div>
            </div>

            {% if chart_base64 %}
            <div class="metric-card">
                <h2>📈 Performance Trends (7 Days)</h2>
                <div class="chart-container">
                    <img src="data:image/png;base64,{{ chart_base64 }}" alt="Performance Charts" style="max-width: 100%; height: auto;">
                </div>
            </div>
            {% endif %}

            <div class="metric-card">
                <h2>📋 Summary & Recommendations</h2>
                {% if roi_percentage > 710 %}
                <div class="success">
                    <strong>✅ EXCELLENT PERFORMANCE:</strong> ROI exceeding target by {{ (roi_percentage - 710)|round(1) }}%. All systems performing optimally.
                </div>
                {% elif roi_percentage > 500 %}
                <div class="success">
                    <strong>✅ GOOD PERFORMANCE:</strong> ROI within target range. Minor optimizations recommended.
                </div>
                {% elif roi_percentage > 200 %}
                <div class="alert-warning">
                    <strong>⚠️ BELOW TARGET:</strong> ROI below target. Performance optimization needed.
                </div>
                {% else %}
                <div class="alert-critical">
                    <strong>🚨 CRITICAL:</strong> ROI below minimum threshold. Immediate intervention required.
                </div>
                {% endif %}

                <h4>Key Actions:</h4>
                <ul>
                    {% if avg_response_time_ms > 100 %}
                    <li>Investigate performance bottlenecks - average response time above target</li>
                    {% endif %}
                    {% if error_rate > 0.02 %}
                    <li>Address system errors - error rate above 2% threshold</li>
                    {% endif %}
                    {% for feature in low_adoption_features %}
                    <li>Increase adoption for {{ feature }} - below 80% target</li>
                    {% endfor %}
                    {% if not alerts %}
                    <li>Continue monitoring - all metrics within acceptable ranges</li>
                    {% endif %}
                </ul>
            </div>

            <div style="text-align: center; margin-top: 30px; color: #666;">
                <p>Generated by EnterpriseHub Phase 3 ROI System | {{ timestamp }}</p>
                <p>For questions, contact: ops-team@company.com</p>
            </div>
        </body>
        </html>
        """

        # Prepare template data
        template_data = {
            'report_date': target_date.strftime('%B %d, %Y'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'alerts': alerts,
            'total_revenue_impact': f"{impact_result.total_revenue_impact:,.2f}",
            'total_operating_costs': f"{impact_result.total_operating_costs:,.2f}",
            'net_revenue': f"{impact_result.net_revenue:,.2f}",
            'roi_percentage': f"{impact_result.roi_percentage:,.1f}",
            'lead_intelligence': impact_result.lead_intelligence,
            'property_intelligence': impact_result.property_intelligence,
            'churn_prevention': impact_result.churn_prevention,
            'ai_coaching': impact_result.ai_coaching,
            'avg_response_time_ms': f"{impact_result.avg_response_time_ms:,.1f}",
            'error_rate': impact_result.error_rate,
            'uptime_percentage': f"{impact_result.uptime_percentage:,.2f}",
            'health_status': 'EXCELLENT' if impact_result.roi_percentage > 710 else 'GOOD' if impact_result.roi_percentage > 500 else 'FAIR',
            'chart_base64': chart_base64,
            'low_adoption_features': [
                f.name for f in [impact_result.lead_intelligence, impact_result.property_intelligence,
                                impact_result.churn_prevention, impact_result.ai_coaching]
                if f.adoption_rate < 0.8
            ]
        }

        # Render HTML report
        template = Template(html_template)
        html_content = template.render(**template_data)

        # Send email if requested
        if send_email:
            subject = f"Phase 3 Daily ROI Report - {target_date.strftime('%Y-%m-%d')} - ROI: {impact_result.roi_percentage:.1f}%"
            await self.send_email_report(
                subject=subject,
                html_content=html_content,
                recipients=self.notification_config['daily_reports']
            )

        # Send Slack notification for significant events
        if alerts:
            critical_alerts = [a for a in alerts if a['type'] == 'critical']
            warning_alerts = [a for a in alerts if a['type'] == 'warning']

            if critical_alerts:
                message = f"🚨 CRITICAL ALERT: {len(critical_alerts)} critical issues detected in Phase 3 deployment. Daily ROI: {impact_result.roi_percentage:.1f}%"
                await self.send_slack_notification(message, 'alerts', 'critical')
            elif warning_alerts:
                message = f"⚠️ Warning: {len(warning_alerts)} performance issues detected in Phase 3. Daily ROI: {impact_result.roi_percentage:.1f}%"
                await self.send_slack_notification(message, 'alerts', 'warning')
        else:
            if impact_result.roi_percentage > 710:
                message = f"✅ Phase 3 Performance Excellent: {impact_result.roi_percentage:.1f}% ROI (Target: 710%). All metrics within optimal ranges."
                await self.send_slack_notification(message, 'reports', 'success')

        logger.info(f"Daily report generated successfully. ROI: {impact_result.roi_percentage:.1f}%, Alerts: {len(alerts)}")

        return {
            'date': target_date,
            'roi_percentage': float(impact_result.roi_percentage),
            'alerts_count': len(alerts),
            'html_content': html_content,
            'impact_result': impact_result
        }

    async def run_continuous_monitoring(self, check_interval: int = 300):
        """Run continuous monitoring with specified check interval (seconds)."""
        logger.info(f"Starting continuous monitoring with {check_interval}s intervals")

        last_alert_time = {}

        while True:
            try:
                # Calculate current business impact
                impact_result = await self.calculator.calculate_daily_business_impact(date.today())

                # Check thresholds
                alerts = await self.check_performance_thresholds(impact_result)

                # Process new alerts (avoid spam)
                new_alerts = []
                for alert in alerts:
                    alert_key = f"{alert['category']}_{alert['type']}"
                    last_time = last_alert_time.get(alert_key, 0)

                    # Only send if it's been more than 1 hour since last alert of this type
                    if time.time() - last_time > 3600:
                        new_alerts.append(alert)
                        last_alert_time[alert_key] = time.time()

                # Send notifications for new alerts
                if new_alerts:
                    await self.store_alerts(new_alerts, impact_result)

                    for alert in new_alerts:
                        if alert['type'] == 'critical':
                            await self.send_slack_notification(
                                f"🚨 {alert['message']}",
                                'alerts',
                                'critical'
                            )
                        elif alert['type'] == 'warning':
                            await self.send_slack_notification(
                                f"⚠️ {alert['message']}",
                                'alerts',
                                'warning'
                            )

                    logger.info(f"Processed {len(new_alerts)} new alerts")

                # Log current status
                if len(alerts) == 0:
                    logger.info(f"✅ All systems healthy - ROI: {impact_result.roi_percentage:.1f}%")
                else:
                    logger.warning(f"⚠️ {len(alerts)} active issues - ROI: {impact_result.roi_percentage:.1f}%")

            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await self.send_slack_notification(
                    f"🚨 SYSTEM ERROR: Monitoring system encountered an error: {e}",
                    'alerts',
                    'critical'
                )

            # Wait for next check
            await asyncio.sleep(check_interval)

    def schedule_automated_reports(self):
        """Schedule automated reports using the schedule library."""
        logger.info("Setting up automated report scheduling")

        # Daily reports at 9 AM
        schedule.every().day.at("09:00").do(
            lambda: asyncio.run(self.generate_daily_report(send_email=True))
        )

        # Weekly reports on Mondays at 10 AM
        schedule.every().monday.at("10:00").do(
            lambda: asyncio.run(self.generate_weekly_report(send_email=True))
        )

        # Health checks every hour
        schedule.every().hour.do(
            lambda: asyncio.run(self.health_check())
        )

        # Start the scheduler
        while True:
            schedule.run_pending()
            time.sleep(60)

    async def health_check(self):
        """Perform system health check."""
        try:
            # Simple database connectivity check
            conn = await self.get_database_connection()
            await conn.fetchval("SELECT 1")
            await conn.close()

            # Check if recent data exists
            impact_result = await self.calculator.calculate_daily_business_impact(date.today())

            logger.info(f"Health check passed - ROI: {impact_result.roi_percentage:.1f}%")

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            await self.send_slack_notification(
                f"🚨 HEALTH CHECK FAILED: {e}",
                'alerts',
                'critical'
            )

    async def generate_weekly_report(self, send_email: bool = False):
        """Generate weekly executive summary report."""
        week_start = date.today() - timedelta(days=date.today().weekday())

        summary = await self.calculator.calculate_weekly_roi_summary(week_start)

        # Send weekly summary via email and Slack
        if send_email:
            subject = f"Phase 3 Weekly Executive Summary - ROI: {summary['roi_percentage']:.1f}%"
            # Simplified weekly email template would go here
            weekly_message = f"""
            Weekly Phase 3 Summary ({summary['week_start']} to {summary['week_end']}):

            📊 ROI Performance: {summary['roi_percentage']:.1f}%
            💰 Total Revenue Impact: ${summary['total_revenue_impact']:,.2f}
            💸 Total Costs: ${summary['total_costs']:,.2f}
            🏆 Net Revenue: ${summary['net_revenue']:,.2f}

            Deployment Status: {'🟢 Excellent' if summary['roi_percentage'] > 710 else '🟡 Good' if summary['roi_percentage'] > 500 else '🔴 Needs Attention'}
            """

            await self.send_email_report(
                subject=subject,
                html_content=f"<pre>{weekly_message}</pre>",
                recipients=self.notification_config['weekly_reports']
            )

        await self.send_slack_notification(weekly_message, 'reports', 'info')

        return summary


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Automated Phase 3 ROI Reporting System')
    parser.add_argument('--mode', choices=['daily', 'weekly', 'monitor', 'schedule'],
                       default='daily', help='Operation mode')
    parser.add_argument('--date', type=str,
                       help='Target date for reports (YYYY-MM-DD)')
    parser.add_argument('--email', action='store_true',
                       help='Send email reports')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuous monitoring')
    parser.add_argument('--interval', type=int, default=300,
                       help='Monitoring check interval in seconds')

    args = parser.parse_args()

    # Initialize reporting system
    reporting_system = AutomatedReportingSystem()

    try:
        if args.mode == 'daily':
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date() if args.date else date.today()
            result = await reporting_system.generate_daily_report(target_date, args.email)
            print(f"Daily report generated for {target_date}. ROI: {result['roi_percentage']:.1f}%")

        elif args.mode == 'weekly':
            result = await reporting_system.generate_weekly_report(args.email)
            print(f"Weekly report generated. ROI: {result['roi_percentage']:.1f}%")

        elif args.mode == 'monitor':
            if args.continuous:
                await reporting_system.run_continuous_monitoring(args.interval)
            else:
                await reporting_system.health_check()

        elif args.mode == 'schedule':
            reporting_system.schedule_automated_reports()

    except KeyboardInterrupt:
        logger.info("Shutting down automated reporting system")
    except Exception as e:
        logger.error(f"Error in automated reporting: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())