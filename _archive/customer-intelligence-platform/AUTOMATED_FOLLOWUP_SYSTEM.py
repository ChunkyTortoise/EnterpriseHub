#!/usr/bin/env python3
"""
Customer Intelligence Platform - Automated Follow-up System

Comprehensive automated follow-up and nurturing campaign system:
- Intelligent email sequence automation
- Personalized content based on demo performance
- Multi-channel outreach (email, LinkedIn, phone)
- ROI-driven messaging optimization
- Conversion tracking and optimization
"""

import asyncio
import smtplib
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
import jinja2
import logging
import uuid
import requests
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FollowUpSequence:
    """Follow-up sequence configuration."""
    name: str
    description: str
    trigger_conditions: Dict[str, Any]
    emails: List[Dict[str, Any]]
    success_metrics: Dict[str, float]

@dataclass
class EmailTemplate:
    """Email template with dynamic content."""
    subject_template: str
    content_template: str
    call_to_action: str
    personalization_fields: List[str]

class AutomatedFollowUpSystem:
    """Comprehensive automated follow-up and nurturing system."""
    
    def __init__(self):
        self.db_path = Path(__file__).parent / "demo_campaigns.db"
        self.templates_path = Path(__file__).parent / "email_templates"
        self.templates_path.mkdir(exist_ok=True)
        
        # Email configuration
        self.smtp_config = {
            "host": "smtp.gmail.com",
            "port": 587,
            "username": "",  # Configure with your SMTP credentials
            "password": "",
            "from_name": "Customer Intelligence Platform",
            "from_email": "demos@customerintelligence.ai"
        }
        
        # Jinja2 template environment
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_path)),
            autoescape=True
        )
        
        # Initialize follow-up sequences
        self.sequences = self._initialize_sequences()
        self._create_email_templates()
    
    def _initialize_sequences(self) -> Dict[str, FollowUpSequence]:
        """Initialize all follow-up sequences."""
        sequences = {
            "demo_confirmation": FollowUpSequence(
                name="Demo Confirmation",
                description="Confirms demo booking and sets expectations",
                trigger_conditions={"demo_status": "scheduled"},
                emails=[
                    {
                        "delay_hours": 1,
                        "template": "demo_confirmation.html",
                        "subject": "Your Customer Intelligence Platform Demo - Confirmed for {{ demo_date }}",
                        "priority": "high"
                    }
                ],
                success_metrics={"open_rate": 0.85, "response_rate": 0.15}
            ),
            
            "post_demo_followup": FollowUpSequence(
                name="Post-Demo Follow-up",
                description="Immediate follow-up after demo completion",
                trigger_conditions={"demo_status": "completed"},
                emails=[
                    {
                        "delay_hours": 2,
                        "template": "post_demo_immediate.html",
                        "subject": "Thank you for exploring our Customer Intelligence Platform",
                        "priority": "high"
                    },
                    {
                        "delay_hours": 24,
                        "template": "post_demo_24h.html", 
                        "subject": "{{ roi_percentage }}% ROI - Your Custom Analysis Inside",
                        "priority": "high",
                        "conditions": {"success_probability": ">0.5"}
                    },
                    {
                        "delay_hours": 72,
                        "template": "post_demo_72h.html",
                        "subject": "Next steps for {{ company_name }}",
                        "priority": "medium",
                        "conditions": {"no_response": True}
                    }
                ],
                success_metrics={"open_rate": 0.75, "click_rate": 0.35, "response_rate": 0.25}
            ),
            
            "high_intent_acceleration": FollowUpSequence(
                name="High Intent Acceleration",
                description="Accelerated sequence for high-probability prospects",
                trigger_conditions={"success_probability": ">0.7"},
                emails=[
                    {
                        "delay_hours": 4,
                        "template": "high_intent_proposal.html",
                        "subject": "{{ company_name }} - Implementation Proposal Ready",
                        "priority": "urgent"
                    },
                    {
                        "delay_hours": 48,
                        "template": "high_intent_urgency.html",
                        "subject": "Limited Q1 Implementation Slots - {{ company_name }}",
                        "priority": "high",
                        "conditions": {"no_response": True}
                    }
                ],
                success_metrics={"response_rate": 0.45, "conversion_rate": 0.65}
            ),
            
            "nurturing_warm": FollowUpSequence(
                name="Warm Lead Nurturing",
                description="Educational nurturing for engaged but not ready leads",
                trigger_conditions={"success_probability": "0.4-0.7"},
                emails=[
                    {
                        "delay_hours": 48,
                        "template": "nurturing_case_study.html",
                        "subject": "How {{ similar_company }} achieved {{ roi_example }}% ROI",
                        "priority": "medium"
                    },
                    {
                        "delay_days": 7,
                        "template": "nurturing_industry_insights.html",
                        "subject": "{{ industry }} Intelligence Report - Customer Trends",
                        "priority": "low"
                    },
                    {
                        "delay_days": 14,
                        "template": "nurturing_feature_spotlight.html",
                        "subject": "New: {{ industry }}-specific AI features",
                        "priority": "low"
                    },
                    {
                        "delay_days": 30,
                        "template": "nurturing_reengagement.html",
                        "subject": "Still evaluating customer intelligence solutions?",
                        "priority": "medium"
                    }
                ],
                success_metrics={"engagement_rate": 0.35, "reactivation_rate": 0.15}
            ),
            
            "cold_reactivation": FollowUpSequence(
                name="Cold Lead Reactivation",
                description="Reactivation sequence for disengaged leads",
                trigger_conditions={"success_probability": "<0.4", "days_since_demo": ">7"},
                emails=[
                    {
                        "delay_days": 14,
                        "template": "reactivation_value_prop.html",
                        "subject": "One more chance to see {{ roi_percentage }}% ROI",
                        "priority": "low"
                    },
                    {
                        "delay_days": 30,
                        "template": "reactivation_breakup.html",
                        "subject": "Should we close your file?",
                        "priority": "low"
                    }
                ],
                success_metrics={"reopen_rate": 0.20, "reengagement_rate": 0.08}
            ),
            
            "competitive_displacement": FollowUpSequence(
                name="Competitive Displacement",
                description="Specialized sequence when competitors are mentioned",
                trigger_conditions={"competitive_mentions": "exists"},
                emails=[
                    {
                        "delay_hours": 24,
                        "template": "competitive_comparison.html",
                        "subject": "{{ company_name }} - Platform Comparison Analysis",
                        "priority": "high"
                    },
                    {
                        "delay_days": 3,
                        "template": "competitive_differentiation.html",
                        "subject": "Why {{ reference_company }} chose us over {{ competitor }}",
                        "priority": "medium"
                    }
                ],
                success_metrics={"conversion_rate": 0.25, "competitive_win_rate": 0.35}
            )
        }
        
        return sequences
    
    def _create_email_templates(self):
        """Create comprehensive email templates."""
        templates = {
            "demo_confirmation.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Demo Confirmation</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #1e3a8a 0%, #3730a3 100%); color: white; padding: 20px; border-radius: 10px; }
        .content { padding: 20px 0; }
        .cta-button { background: #1e3a8a; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }
        .highlight { background: #f0f9ff; padding: 15px; border-left: 4px solid #1e3a8a; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Your Customer Intelligence Platform Demo is Confirmed!</h1>
        </div>
        
        <div class="content">
            <p>Hi {{ contact_name }},</p>
            
            <p>Thank you for your interest in our Customer Intelligence Platform! I'm excited to show you exactly how companies like {{ company_name }} are achieving <strong>{{ roi_projection }}% ROI</strong> through AI-powered customer insights.</p>
            
            <div class="highlight">
                <h3>📅 Demo Details:</h3>
                <ul>
                    <li><strong>Date:</strong> {{ demo_date }}</li>
                    <li><strong>Time:</strong> {{ demo_time }}</li>
                    <li><strong>Duration:</strong> 30 minutes</li>
                    <li><strong>Join Link:</strong> <a href="{{ demo_link }}">{{ demo_link }}</a></li>
                </ul>
            </div>
            
            <h3>🎯 What We'll Cover:</h3>
            <ul>
                <li>How to predict customer behavior with 90%+ accuracy</li>
                <li>Real-time insights that increase conversion rates by 25-40%</li>
                <li>{{ industry }}-specific use cases and success stories</li>
                <li>ROI calculation showing <strong>${{ projected_annual_benefit }}</strong> in potential benefits</li>
            </ul>
            
            <div class="highlight">
                <h3>💡 To Maximize Our Time:</h3>
                <p>Please have the following ready to discuss:</p>
                <ul>
                    <li>Current customer intelligence challenges</li>
                    <li>Key stakeholders who should be involved</li>
                    <li>Timeline for implementing new solutions</li>
                </ul>
            </div>
            
            <p>If you need to reschedule, please let me know at least 2 hours in advance.</p>
            
            <a href="{{ demo_link }}" class="cta-button">🚀 Join Demo ({{ demo_time }})</a>
            
            <p>Looking forward to showing you how AI can transform your customer intelligence!</p>
            
            <p>Best regards,<br>
            {{ rep_name }}<br>
            Customer Intelligence Platform<br>
            {{ rep_email }} | {{ rep_phone }}</p>
        </div>
    </div>
</body>
</html>
            """,
            
            "post_demo_immediate.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Thank You - Demo Follow-up</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #059669 0%, #047857 100%); color: white; padding: 20px; border-radius: 10px; }
        .content { padding: 20px 0; }
        .cta-button { background: #059669; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0; }
        .roi-box { background: #ecfdf5; border: 1px solid #10b981; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; }
        .next-steps { background: #f8fafc; padding: 15px; border-radius: 5px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Thank You for Exploring Our Platform!</h1>
        </div>
        
        <div class="content">
            <p>Hi {{ contact_name }},</p>
            
            <p>Thank you for taking the time to see our Customer Intelligence Platform demo today. I hope you found it valuable to see how the platform can help {{ company_name }} {{ specific_benefit }}.</p>
            
            <div class="roi-box">
                <h3>💰 Your Custom ROI Analysis</h3>
                <p><strong>{{ roi_projection }}% Annual ROI</strong></p>
                <p><strong>${{ annual_benefit }}</strong> in projected benefits</p>
                <p><strong>{{ payback_days }} days</strong> to payback</p>
            </div>
            
            <h3>🔑 Key Takeaways from Our Discussion:</h3>
            <ul>
                {% for takeaway in key_takeaways %}
                <li>{{ takeaway }}</li>
                {% endfor %}
            </ul>
            
            <div class="next-steps">
                <h3>🚀 Recommended Next Steps:</h3>
                <ol>
                    {% if success_probability > 0.7 %}
                    <li>📋 <strong>Custom Proposal</strong> - Detailed implementation plan and pricing</li>
                    <li>🧪 <strong>30-day Pilot Program</strong> - Risk-free trial with {{ pilot_users }} users</li>
                    <li>📞 <strong>Technical Deep-dive</strong> - With our Solutions Architect</li>
                    {% elif success_probability > 0.4 %}
                    <li>🤝 <strong>Reference Call</strong> - Speak with {{ similar_company }} about their results</li>
                    <li>📊 <strong>Custom ROI Analysis</strong> - Detailed financial impact projection</li>
                    <li>🔧 <strong>Technical Review</strong> - Integration and implementation planning</li>
                    {% else %}
                    <li>📚 <strong>Case Studies</strong> - Success stories from {{ industry }} companies</li>
                    <li>🎯 <strong>Industry Insights</strong> - Latest trends and benchmarks</li>
                    <li>📞 <strong>Follow-up Call</strong> - Address any questions or concerns</li>
                    {% endif %}
                </ol>
            </div>
            
            <p>Which option makes the most sense for {{ company_name }}? I'm happy to move forward with whichever approach feels right.</p>
            
            <a href="mailto:{{ rep_email }}?subject=Next Steps - {{ company_name }}" class="cta-button">📧 Let's Discuss Next Steps</a>
            
            <p>Thank you again for your time and interest. I look forward to helping {{ company_name }} achieve {{ specific_goal }}!</p>
            
            <p>Best regards,<br>
            {{ rep_name }}<br>
            {{ rep_email }} | {{ rep_phone }}</p>
        </div>
    </div>
</body>
</html>
            """,
            
            "high_intent_proposal.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Implementation Proposal Ready</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; padding: 20px; border-radius: 10px; }
        .content { padding: 20px 0; }
        .cta-button { background: #dc2626; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 15px 0; font-weight: bold; }
        .urgent-box { background: #fef2f2; border: 2px solid #dc2626; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .timeline { background: #f0fdf4; padding: 15px; border-radius: 5px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 {{ company_name }} - Implementation Proposal Ready!</h1>
        </div>
        
        <div class="content">
            <p>Hi {{ contact_name }},</p>
            
            <p>Based on our excellent demo session and your clear interest in moving forward, I've prepared a comprehensive implementation proposal specifically for {{ company_name }}.</p>
            
            <div class="urgent-box">
                <h3>⏰ Time-Sensitive Opportunity</h3>
                <p>We have <strong>limited Q1 implementation slots</strong> available, and based on your timeline, I want to ensure {{ company_name }} can start seeing results by {{ target_go_live_date }}.</p>
            </div>
            
            <h3>📋 Your Custom Proposal Includes:</h3>
            <ul>
                <li><strong>Implementation Roadmap</strong> - 1.5-day deployment timeline</li>
                <li><strong>Custom ROI Analysis</strong> - {{ roi_projection }}% return projection</li>
                <li><strong>{{ industry }} Configuration</strong> - Pre-built for your use cases</li>
                <li><strong>Training Program</strong> - {{ user_count }} user onboarding</li>
                <li><strong>Success Metrics</strong> - {{ success_metrics }}</li>
                <li><strong>Investment Details</strong> - Transparent pricing and terms</li>
            </ul>
            
            <div class="timeline">
                <h3>🗓️ Proposed Timeline:</h3>
                <ul>
                    <li><strong>Week 1:</strong> Contract finalization and kickoff</li>
                    <li><strong>Week 2:</strong> Platform configuration and integration</li>
                    <li><strong>Week 3:</strong> Team training and go-live</li>
                    <li><strong>Week 4:</strong> Results measurement and optimization</li>
                </ul>
            </div>
            
            <p>I've also included a <strong>risk-free 30-day pilot program</strong> option if you'd prefer to start smaller.</p>
            
            <a href="{{ proposal_link }}" class="cta-button">📄 View Your Custom Proposal</a>
            
            <p>I'm available for a quick call today or tomorrow to walk through the proposal and answer any questions. Given the limited Q1 slots, I'd recommend we connect soon to secure your implementation timeline.</p>
            
            <p>When would be a good time for a 15-minute call?</p>
            
            <p>Best regards,<br>
            {{ rep_name }}<br>
            {{ rep_email }} | {{ rep_phone }}</p>
        </div>
    </div>
</body>
</html>
            """,
            
            "nurturing_case_study.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Case Study</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%); color: white; padding: 20px; border-radius: 10px; }
        .content { padding: 20px 0; }
        .case-study-box { background: #faf5ff; border: 1px solid #7c3aed; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .results-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; }
        .result-item { background: white; padding: 10px; border-radius: 5px; text-align: center; border: 1px solid #e5e7eb; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 How {{ similar_company }} Achieved {{ roi_example }}% ROI</h1>
        </div>
        
        <div class="content">
            <p>Hi {{ contact_name }},</p>
            
            <p>I thought you'd be interested in this success story from {{ similar_company }}, a {{ industry }} company similar to {{ company_name }}.</p>
            
            <div class="case-study-box">
                <h3>🏢 Company Profile:</h3>
                <ul>
                    <li><strong>Industry:</strong> {{ case_study_industry }}</li>
                    <li><strong>Size:</strong> {{ case_study_size }} employees</li>
                    <li><strong>Revenue:</strong> {{ case_study_revenue }}</li>
                    <li><strong>Challenge:</strong> {{ case_study_challenge }}</li>
                </ul>
                
                <h3>🎯 Results After Implementation:</h3>
                <div class="results-grid">
                    <div class="result-item">
                        <strong>{{ metric_1_value }}</strong><br>
                        {{ metric_1_name }}
                    </div>
                    <div class="result-item">
                        <strong>{{ metric_2_value }}</strong><br>
                        {{ metric_2_name }}
                    </div>
                    <div class="result-item">
                        <strong>{{ metric_3_value }}</strong><br>
                        {{ metric_3_name }}
                    </div>
                    <div class="result-item">
                        <strong>{{ roi_example }}%</strong><br>
                        Annual ROI
                    </div>
                </div>
                
                <h3>💬 What Their {{ title }} Said:</h3>
                <blockquote>"{{ testimonial_quote }}"</blockquote>
                <p><em>- {{ testimonial_name }}, {{ testimonial_title }}</em></p>
            </div>
            
            <p>The challenges {{ similar_company }} faced are remarkably similar to what we discussed for {{ company_name }}:</p>
            <ul>
                {% for similarity in challenge_similarities %}
                <li>{{ similarity }}</li>
                {% endfor %}
            </ul>
            
            <p>I'd be happy to connect you with {{ testimonial_name }} for a brief reference call if you'd like to hear more about their experience.</p>
            
            <p>Would a 15-minute conversation about how this might apply to {{ company_name }} be valuable?</p>
            
            <p>Best regards,<br>
            {{ rep_name }}</p>
        </div>
    </div>
</body>
</html>
            """
        }
        
        # Save templates to files
        for template_name, template_content in templates.items():
            template_file = self.templates_path / template_name
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
    
    async def trigger_sequence(self, lead_id: str, sequence_name: str, context_data: Dict[str, Any]):
        """Trigger a specific follow-up sequence for a lead."""
        if sequence_name not in self.sequences:
            logger.error(f"Unknown sequence: {sequence_name}")
            return
        
        sequence = self.sequences[sequence_name]
        
        # Check if lead meets trigger conditions
        if not await self._check_trigger_conditions(lead_id, sequence.trigger_conditions):
            logger.info(f"Lead {lead_id} doesn't meet conditions for {sequence_name}")
            return
        
        # Schedule emails in the sequence
        for email_config in sequence.emails:
            await self._schedule_email(lead_id, sequence_name, email_config, context_data)
        
        logger.info(f"Triggered {sequence_name} for lead {lead_id}")
    
    async def process_scheduled_emails(self):
        """Process all scheduled emails that are due to be sent."""
        if not self.db_path.exists():
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get emails scheduled for sending
        cursor.execute("""
            SELECT id, lead_id, campaign_type, email_subject, email_content, 
                   scheduled_for, context_data
            FROM email_campaigns 
            WHERE status = 'scheduled' AND scheduled_for <= ?
            ORDER BY scheduled_for
        """, (datetime.now(),))
        
        scheduled_emails = cursor.fetchall()
        
        for email_data in scheduled_emails:
            email_id, lead_id, campaign_type, subject, content, scheduled_for, context_json = email_data
            
            try:
                context = json.loads(context_json) if context_json else {}
                
                # Send the email
                success = await self._send_email(lead_id, subject, content, context)
                
                if success:
                    # Mark as sent
                    cursor.execute("""
                        UPDATE email_campaigns 
                        SET status = 'sent', sent_at = ?
                        WHERE id = ?
                    """, (datetime.now(), email_id))
                    
                    logger.info(f"Email sent successfully: {email_id}")
                else:
                    # Mark as failed
                    cursor.execute("""
                        UPDATE email_campaigns 
                        SET status = 'failed'
                        WHERE id = ?
                    """, (email_id,))
                    
                    logger.error(f"Failed to send email: {email_id}")
                
            except Exception as e:
                logger.error(f"Error processing email {email_id}: {e}")
        
        conn.commit()
        conn.close()
    
    async def track_email_engagement(self, email_id: str, event_type: str):
        """Track email engagement events (open, click, reply)."""
        if not self.db_path.exists():
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update email engagement
        if event_type == "open":
            cursor.execute("""
                UPDATE email_campaigns 
                SET opened_at = ?
                WHERE id = ?
            """, (datetime.now(), email_id))
            
        elif event_type == "click":
            cursor.execute("""
                UPDATE email_campaigns 
                SET clicked_at = ?
                WHERE id = ?
            """, (datetime.now(), email_id))
            
        elif event_type == "reply":
            cursor.execute("""
                UPDATE email_campaigns 
                SET replied_at = ?, status = 'replied'
                WHERE id = ?
            """, (datetime.now(), email_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Tracked {event_type} for email {email_id}")
    
    async def analyze_sequence_performance(self) -> Dict[str, Any]:
        """Analyze performance of all follow-up sequences."""
        if not self.db_path.exists():
            return {}
        
        conn = sqlite3.connect(self.db_path)
        
        # Get sequence performance metrics
        performance_query = """
            SELECT 
                campaign_type,
                COUNT(*) as emails_sent,
                COUNT(opened_at) as emails_opened,
                COUNT(clicked_at) as emails_clicked, 
                COUNT(replied_at) as emails_replied,
                COUNT(CASE WHEN status = 'sent' THEN 1 END) as successful_sends
            FROM email_campaigns
            WHERE sent_at IS NOT NULL
            GROUP BY campaign_type
        """
        
        df_performance = pd.read_sql_query(performance_query, conn)
        conn.close()
        
        if df_performance.empty:
            return {"sequences": [], "overall_metrics": {}}
        
        # Calculate metrics for each sequence
        sequence_metrics = []
        for _, row in df_performance.iterrows():
            campaign_type = row['campaign_type']
            emails_sent = row['emails_sent']
            
            metrics = {
                "sequence_name": campaign_type,
                "emails_sent": emails_sent,
                "open_rate": (row['emails_opened'] / emails_sent) if emails_sent > 0 else 0,
                "click_rate": (row['emails_clicked'] / row['emails_opened']) if row['emails_opened'] > 0 else 0,
                "reply_rate": (row['emails_replied'] / emails_sent) if emails_sent > 0 else 0,
                "delivery_rate": (row['successful_sends'] / emails_sent) if emails_sent > 0 else 0
            }
            
            # Compare to target metrics
            if campaign_type in self.sequences:
                target_metrics = self.sequences[campaign_type].success_metrics
                metrics["performance_score"] = self._calculate_performance_score(metrics, target_metrics)
            
            sequence_metrics.append(metrics)
        
        # Overall metrics
        overall_metrics = {
            "total_emails_sent": df_performance['emails_sent'].sum(),
            "average_open_rate": df_performance['emails_opened'].sum() / df_performance['emails_sent'].sum(),
            "average_click_rate": df_performance['emails_clicked'].sum() / df_performance['emails_opened'].sum(),
            "average_reply_rate": df_performance['emails_replied'].sum() / df_performance['emails_sent'].sum()
        }
        
        return {
            "sequences": sequence_metrics,
            "overall_metrics": overall_metrics,
            "recommendations": self._generate_optimization_recommendations(sequence_metrics)
        }
    
    async def _check_trigger_conditions(self, lead_id: str, conditions: Dict[str, Any]) -> bool:
        """Check if a lead meets the trigger conditions for a sequence."""
        if not self.db_path.exists():
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get lead data
        cursor.execute("""
            SELECT * FROM demo_leads WHERE id = ?
        """, (lead_id,))
        
        lead_data = cursor.fetchone()
        if not lead_data:
            conn.close()
            return False
        
        # Check each condition
        for condition_key, condition_value in conditions.items():
            if condition_key == "demo_status":
                lead_index = 8  # demo_status column index
                if lead_data[lead_index] != condition_value:
                    conn.close()
                    return False
            
            elif condition_key == "success_probability":
                # Parse range conditions like ">0.7" or "0.4-0.7"
                if isinstance(condition_value, str):
                    if condition_value.startswith(">"):
                        threshold = float(condition_value[1:])
                        # Get success probability from demo_performance table
                        cursor.execute("""
                            SELECT success_probability FROM demo_performance 
                            WHERE demo_id = ? ORDER BY recorded_at DESC LIMIT 1
                        """, (lead_id,))
                        
                        perf_data = cursor.fetchone()
                        if not perf_data or perf_data[0] <= threshold:
                            conn.close()
                            return False
                    
                    elif "-" in condition_value:
                        min_val, max_val = map(float, condition_value.split("-"))
                        cursor.execute("""
                            SELECT success_probability FROM demo_performance 
                            WHERE demo_id = ? ORDER BY recorded_at DESC LIMIT 1
                        """, (lead_id,))
                        
                        perf_data = cursor.fetchone()
                        if not perf_data or not (min_val <= perf_data[0] <= max_val):
                            conn.close()
                            return False
        
        conn.close()
        return True
    
    async def _schedule_email(self, lead_id: str, sequence_name: str, email_config: Dict[str, Any], context_data: Dict[str, Any]):
        """Schedule an email to be sent at the specified time."""
        # Calculate send time
        now = datetime.now()
        
        if "delay_hours" in email_config:
            send_time = now + timedelta(hours=email_config["delay_hours"])
        elif "delay_days" in email_config:
            send_time = now + timedelta(days=email_config["delay_days"])
        else:
            send_time = now + timedelta(minutes=5)  # Default 5 minute delay
        
        # Render email content
        subject = await self._render_email_template(email_config["subject"], context_data)
        content = await self._render_email_template(email_config["template"], context_data)
        
        # Store in database
        if self.db_path.exists():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO email_campaigns (
                    id, lead_id, campaign_type, email_subject, email_content,
                    scheduled_for, status, context_data, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'scheduled', ?, ?)
            """, (
                str(uuid.uuid4()), lead_id, sequence_name, subject, content,
                send_time, json.dumps(context_data), now
            ))
            
            conn.commit()
            conn.close()
        
        logger.info(f"Scheduled {sequence_name} email for {send_time}")
    
    async def _render_email_template(self, template_name: str, context_data: Dict[str, Any]) -> str:
        """Render an email template with context data."""
        try:
            if template_name.endswith('.html'):
                template = self.template_env.get_template(template_name)
                return template.render(**context_data)
            else:
                # Simple string template for subject lines
                template = jinja2.Template(template_name)
                return template.render(**context_data)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            return template_name  # Return original if rendering fails
    
    async def _send_email(self, lead_id: str, subject: str, content: str, context: Dict[str, Any]) -> bool:
        """Send an email to a lead."""
        try:
            # Get lead email address
            if not self.db_path.exists():
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT contact_email, contact_name FROM demo_leads WHERE id = ?
            """, (lead_id,))
            
            lead_data = cursor.fetchone()
            conn.close()
            
            if not lead_data:
                logger.error(f"Lead not found: {lead_id}")
                return False
            
            to_email, to_name = lead_data
            
            # Create email message
            msg = MimeMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.smtp_config['from_name']} <{self.smtp_config['from_email']}>"
            msg['To'] = f"{to_name} <{to_email}>"
            
            # Add HTML content
            html_part = MimeText(content, 'html')
            msg.attach(html_part)
            
            # In production, you would send via SMTP here
            # For demo purposes, we'll just log the email
            logger.info(f"Email would be sent to {to_email}: {subject}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _calculate_performance_score(self, actual_metrics: Dict[str, float], target_metrics: Dict[str, float]) -> float:
        """Calculate performance score by comparing actual vs target metrics."""
        scores = []
        
        for metric_name, target_value in target_metrics.items():
            if metric_name in actual_metrics:
                actual_value = actual_metrics[metric_name]
                score = min(actual_value / target_value, 1.0) if target_value > 0 else 1.0
                scores.append(score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _generate_optimization_recommendations(self, sequence_metrics: List[Dict[str, Any]]) -> List[str]:
        """Generate optimization recommendations based on sequence performance."""
        recommendations = []
        
        for metrics in sequence_metrics:
            sequence_name = metrics["sequence_name"]
            
            if metrics["open_rate"] < 0.3:
                recommendations.append(f"{sequence_name}: Improve subject lines - open rate below 30%")
            
            if metrics["click_rate"] < 0.2:
                recommendations.append(f"{sequence_name}: Enhance email content - low click rate")
            
            if metrics["reply_rate"] < 0.1:
                recommendations.append(f"{sequence_name}: Include stronger call-to-action - few replies")
            
            if "performance_score" in metrics and metrics["performance_score"] < 0.7:
                recommendations.append(f"{sequence_name}: Overall performance below target - review strategy")
        
        return recommendations


async def run_follow_up_automation():
    """Run the automated follow-up system."""
    system = AutomatedFollowUpSystem()
    
    logger.info("🚀 Starting Automated Follow-up System...")
    
    while True:
        try:
            # Process scheduled emails
            await system.process_scheduled_emails()
            
            # Wait 5 minutes before next check
            await asyncio.sleep(300)
            
        except KeyboardInterrupt:
            logger.info("Follow-up system stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in follow-up system: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying


if __name__ == "__main__":
    asyncio.run(run_follow_up_automation())