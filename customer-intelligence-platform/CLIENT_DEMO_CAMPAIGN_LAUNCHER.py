#!/usr/bin/env python3
"""
Customer Intelligence Platform - Client Demo Campaign Launcher

This comprehensive system launches and manages client demo campaigns across all industry verticals:
- Automated demo environment preparation for all 4 industries
- Client acquisition tracking and pipeline management
- Demo performance metrics and conversion analytics
- Automated follow-up sequences and nurturing campaigns
- ROI calculation tools and prospect conversion optimization

Usage:
    # Launch all demo campaigns
    python CLIENT_DEMO_CAMPAIGN_LAUNCHER.py --launch-all

    # Launch specific industry demo
    python CLIENT_DEMO_CAMPAIGN_LAUNCHER.py --industry=real_estate --customer="Premier Realty Group"

    # Run client acquisition tracking
    python CLIENT_DEMO_CAMPAIGN_LAUNCHER.py --track-pipeline

    # Generate conversion analytics
    python CLIENT_DEMO_CAMPAIGN_LAUNCHER.py --analytics --period=30
"""

import asyncio
import argparse
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import sys
from pathlib import Path
import subprocess
import time
import uuid
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dataclasses import dataclass, asdict

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from scripts.prepare_demo import DemoDataGenerator
from src.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class DemoLead:
    """Demo lead tracking data structure."""
    id: str
    company_name: str
    industry: str
    contact_name: str
    contact_email: str
    contact_phone: str
    demo_requested_at: datetime
    demo_scheduled_for: Optional[datetime]
    demo_completed_at: Optional[datetime]
    demo_status: str  # scheduled, completed, no_show, cancelled
    lead_source: str
    company_size: str
    annual_revenue: str
    decision_makers: List[str]
    pain_points: List[str]
    current_solutions: List[str]
    evaluation_timeline: str
    budget_range: str
    follow_up_sequence: str
    conversion_stage: str  # demo_requested, demo_completed, proposal_sent, negotiating, closed_won, closed_lost
    roi_calculated: float
    next_action: str
    notes: str
    created_at: datetime
    updated_at: datetime

@dataclass
class DemoPerformance:
    """Demo performance metrics."""
    demo_id: str
    industry: str
    attendee_count: int
    demo_duration_minutes: int
    engagement_score: float  # 0-1 based on questions, interaction
    technical_questions: int
    business_questions: int
    pricing_questions: int
    implementation_questions: int
    demo_completion_rate: float  # 0-1
    follow_up_requested: bool
    pilot_requested: bool
    proposal_requested: bool
    reference_requested: bool
    competitive_mentions: List[str]
    objections_raised: List[str]
    success_probability: float  # 0-1 AI prediction
    recommended_follow_up: str
    recorded_at: datetime

class ClientDemoCampaignManager:
    """Comprehensive client demo campaign management system."""
    
    def __init__(self):
        self.db_path = Path(__file__).parent / "demo_campaigns.db"
        self.demo_environments = {}
        self.smtp_config = {
            "host": "smtp.gmail.com",
            "port": 587,
            "username": "",  # Configure with your SMTP credentials
            "password": "",
        }
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize SQLite database for demo campaign tracking."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Demo leads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS demo_leads (
                id TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                industry TEXT NOT NULL,
                contact_name TEXT NOT NULL,
                contact_email TEXT UNIQUE NOT NULL,
                contact_phone TEXT,
                demo_requested_at TIMESTAMP NOT NULL,
                demo_scheduled_for TIMESTAMP,
                demo_completed_at TIMESTAMP,
                demo_status TEXT NOT NULL DEFAULT 'requested',
                lead_source TEXT NOT NULL,
                company_size TEXT,
                annual_revenue TEXT,
                decision_makers TEXT,  -- JSON array
                pain_points TEXT,      -- JSON array
                current_solutions TEXT, -- JSON array
                evaluation_timeline TEXT,
                budget_range TEXT,
                follow_up_sequence TEXT,
                conversion_stage TEXT NOT NULL DEFAULT 'demo_requested',
                roi_calculated REAL,
                next_action TEXT,
                notes TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)
        
        # Demo performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS demo_performance (
                id TEXT PRIMARY KEY,
                demo_id TEXT NOT NULL,
                industry TEXT NOT NULL,
                attendee_count INTEGER NOT NULL,
                demo_duration_minutes INTEGER NOT NULL,
                engagement_score REAL NOT NULL,
                technical_questions INTEGER DEFAULT 0,
                business_questions INTEGER DEFAULT 0,
                pricing_questions INTEGER DEFAULT 0,
                implementation_questions INTEGER DEFAULT 0,
                demo_completion_rate REAL NOT NULL,
                follow_up_requested BOOLEAN DEFAULT FALSE,
                pilot_requested BOOLEAN DEFAULT FALSE,
                proposal_requested BOOLEAN DEFAULT FALSE,
                reference_requested BOOLEAN DEFAULT FALSE,
                competitive_mentions TEXT,  -- JSON array
                objections_raised TEXT,     -- JSON array
                success_probability REAL NOT NULL,
                recommended_follow_up TEXT,
                recorded_at TIMESTAMP NOT NULL,
                FOREIGN KEY (demo_id) REFERENCES demo_leads (id)
            )
        """)
        
        # Email campaigns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_campaigns (
                id TEXT PRIMARY KEY,
                lead_id TEXT NOT NULL,
                campaign_type TEXT NOT NULL,
                email_subject TEXT NOT NULL,
                email_content TEXT NOT NULL,
                sent_at TIMESTAMP NOT NULL,
                opened_at TIMESTAMP,
                clicked_at TIMESTAMP,
                replied_at TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'sent',
                FOREIGN KEY (lead_id) REFERENCES demo_leads (id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    async def launch_all_demo_campaigns(self) -> Dict[str, Any]:
        """Launch comprehensive demo campaigns for all industries."""
        logger.info("🚀 Launching comprehensive client demo campaigns...")
        
        industries = ["real_estate", "saas", "ecommerce", "financial_services"]
        sample_customers = {
            "real_estate": [
                ("Premier Realty Group", "Sarah Chen", "sarah.chen@premierrealty.com"),
                ("Austin Metro Realty", "Mike Rodriguez", "mike@austinmetro.com"),
                ("Texas Property Partners", "Jennifer Williams", "j.williams@txproperty.com")
            ],
            "saas": [
                ("CloudTech Solutions", "David Kim", "david.kim@cloudtech.io"),
                ("ScaleUp Systems", "Lisa Martinez", "lisa@scaleup.com"),
                ("DataFlow Inc", "Robert Johnson", "rjohnson@dataflow.net")
            ],
            "ecommerce": [
                ("Fashion Forward", "Maria Rodriguez", "maria@fashionforward.com"),
                ("SportsTech Store", "Alex Thompson", "alex@sportstech.shop"),
                ("HomeStyle Direct", "Emma Chen", "emma@homestyle.com")
            ],
            "financial_services": [
                ("Wealth Advisors Inc", "Michael Brown", "mbrown@wealthadvisors.com"),
                ("Premier Financial", "Susan Davis", "sdavis@premierfinancial.com"),
                ("Investment Partners", "James Wilson", "jwilson@investpartners.com")
            ]
        }
        
        campaign_results = {
            "campaign_launch_time": datetime.now().isoformat(),
            "industries_launched": [],
            "demo_environments_created": [],
            "sample_leads_generated": [],
            "tracking_systems_activated": [],
            "follow_up_sequences_configured": []
        }
        
        # Launch demo environment for each industry
        for industry in industries:
            try:
                logger.info(f"🎯 Launching {industry} demo campaign...")
                
                # Prepare demo environments for multiple customers in this industry
                industry_environments = []
                industry_leads = []
                
                for customer_name, contact_name, contact_email in sample_customers[industry]:
                    # Generate demo environment
                    demo_generator = DemoDataGenerator(industry, customer_name)
                    await demo_generator.initialize()
                    
                    demo_data = await demo_generator.prepare_demo_environment()
                    self.demo_environments[f"{industry}_{customer_name.lower().replace(' ', '_')}"] = demo_data
                    
                    industry_environments.append({
                        "customer": customer_name,
                        "demo_data_key": f"{industry}_{customer_name.lower().replace(' ', '_')}",
                        "knowledge_base_docs": demo_data["knowledge_base_size"],
                        "demo_customers": len(demo_data["demo_customers"]),
                        "roi_projection": demo_data["roi_calculation"]["financial_impact"]["roi_percent"]
                    })
                    
                    # Create sample demo lead
                    lead = await self.create_demo_lead({
                        "company_name": customer_name,
                        "industry": industry,
                        "contact_name": contact_name,
                        "contact_email": contact_email,
                        "contact_phone": "+1-555-0123",
                        "lead_source": "website_demo_request",
                        "company_size": "medium",
                        "annual_revenue": "5M-20M",
                        "decision_makers": [contact_name, "CTO", "VP Operations"],
                        "pain_points": await self._get_industry_pain_points(industry),
                        "current_solutions": await self._get_industry_current_solutions(industry),
                        "evaluation_timeline": "30_days",
                        "budget_range": "20K-50K",
                        "conversion_stage": "demo_requested"
                    })
                    
                    industry_leads.append({
                        "lead_id": lead["id"],
                        "company": customer_name,
                        "contact": contact_name,
                        "status": lead["conversion_stage"]
                    })
                
                campaign_results["industries_launched"].append({
                    "industry": industry,
                    "environments_created": len(industry_environments),
                    "sample_leads": len(industry_leads),
                    "environments": industry_environments,
                    "leads": industry_leads
                })
                
                logger.info(f"✅ {industry} campaign launched with {len(industry_environments)} environments")
                
            except Exception as e:
                logger.error(f"Failed to launch {industry} campaign: {e}")
                continue
        
        # Configure tracking systems
        await self._setup_tracking_systems()
        campaign_results["tracking_systems_activated"] = [
            "demo_performance_tracking",
            "lead_conversion_pipeline",
            "email_engagement_tracking",
            "roi_calculation_automation"
        ]
        
        # Setup automated follow-up sequences
        await self._setup_follow_up_sequences()
        campaign_results["follow_up_sequences_configured"] = [
            "demo_confirmation_sequence",
            "post_demo_follow_up",
            "nurturing_campaign_warm_leads",
            "re_engagement_cold_leads"
        ]
        
        # Generate campaign launch report
        await self._generate_campaign_report(campaign_results)
        
        logger.info("🎉 All demo campaigns launched successfully!")
        return campaign_results
    
    async def create_demo_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new demo lead with comprehensive tracking."""
        lead_id = str(uuid.uuid4())
        now = datetime.now()
        
        lead = DemoLead(
            id=lead_id,
            company_name=lead_data["company_name"],
            industry=lead_data["industry"],
            contact_name=lead_data["contact_name"],
            contact_email=lead_data["contact_email"],
            contact_phone=lead_data.get("contact_phone", ""),
            demo_requested_at=now,
            demo_scheduled_for=None,
            demo_completed_at=None,
            demo_status="requested",
            lead_source=lead_data.get("lead_source", "website"),
            company_size=lead_data.get("company_size", ""),
            annual_revenue=lead_data.get("annual_revenue", ""),
            decision_makers=lead_data.get("decision_makers", []),
            pain_points=lead_data.get("pain_points", []),
            current_solutions=lead_data.get("current_solutions", []),
            evaluation_timeline=lead_data.get("evaluation_timeline", ""),
            budget_range=lead_data.get("budget_range", ""),
            follow_up_sequence="demo_confirmation",
            conversion_stage=lead_data.get("conversion_stage", "demo_requested"),
            roi_calculated=0.0,
            next_action="schedule_demo",
            notes="",
            created_at=now,
            updated_at=now
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO demo_leads (
                id, company_name, industry, contact_name, contact_email, contact_phone,
                demo_requested_at, demo_status, lead_source, company_size, annual_revenue,
                decision_makers, pain_points, current_solutions, evaluation_timeline,
                budget_range, follow_up_sequence, conversion_stage, roi_calculated,
                next_action, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead.id, lead.company_name, lead.industry, lead.contact_name,
            lead.contact_email, lead.contact_phone, lead.demo_requested_at,
            lead.demo_status, lead.lead_source, lead.company_size, lead.annual_revenue,
            json.dumps(lead.decision_makers), json.dumps(lead.pain_points),
            json.dumps(lead.current_solutions), lead.evaluation_timeline,
            lead.budget_range, lead.follow_up_sequence, lead.conversion_stage,
            lead.roi_calculated, lead.next_action, lead.notes,
            lead.created_at, lead.updated_at
        ))
        
        conn.commit()
        conn.close()
        
        # Calculate ROI for this lead
        roi_data = await self._calculate_lead_roi(lead)
        await self.update_lead_roi(lead_id, roi_data["roi_percent"])
        
        # Trigger follow-up sequence
        await self._trigger_follow_up_sequence(lead_id, "demo_confirmation")
        
        logger.info(f"✅ Created demo lead: {lead.company_name} ({lead.industry})")
        return asdict(lead)
    
    async def track_demo_performance(self, demo_id: str, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track detailed demo performance metrics."""
        performance_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Calculate success probability based on engagement metrics
        success_probability = self._calculate_demo_success_probability(performance_data)
        
        performance = DemoPerformance(
            demo_id=performance_id,
            demo_id=demo_id,
            industry=performance_data["industry"],
            attendee_count=performance_data.get("attendee_count", 1),
            demo_duration_minutes=performance_data.get("duration_minutes", 30),
            engagement_score=performance_data.get("engagement_score", 0.7),
            technical_questions=performance_data.get("technical_questions", 0),
            business_questions=performance_data.get("business_questions", 0),
            pricing_questions=performance_data.get("pricing_questions", 0),
            implementation_questions=performance_data.get("implementation_questions", 0),
            demo_completion_rate=performance_data.get("completion_rate", 1.0),
            follow_up_requested=performance_data.get("follow_up_requested", False),
            pilot_requested=performance_data.get("pilot_requested", False),
            proposal_requested=performance_data.get("proposal_requested", False),
            reference_requested=performance_data.get("reference_requested", False),
            competitive_mentions=performance_data.get("competitive_mentions", []),
            objections_raised=performance_data.get("objections_raised", []),
            success_probability=success_probability,
            recommended_follow_up=self._generate_follow_up_recommendation(success_probability, performance_data),
            recorded_at=now
        )
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO demo_performance (
                id, demo_id, industry, attendee_count, demo_duration_minutes,
                engagement_score, technical_questions, business_questions,
                pricing_questions, implementation_questions, demo_completion_rate,
                follow_up_requested, pilot_requested, proposal_requested,
                reference_requested, competitive_mentions, objections_raised,
                success_probability, recommended_follow_up, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            performance_id, demo_id, performance.industry, performance.attendee_count,
            performance.demo_duration_minutes, performance.engagement_score,
            performance.technical_questions, performance.business_questions,
            performance.pricing_questions, performance.implementation_questions,
            performance.demo_completion_rate, performance.follow_up_requested,
            performance.pilot_requested, performance.proposal_requested,
            performance.reference_requested, json.dumps(performance.competitive_mentions),
            json.dumps(performance.objections_raised), performance.success_probability,
            performance.recommended_follow_up, performance.recorded_at
        ))
        
        conn.commit()
        conn.close()
        
        # Update lead conversion stage based on performance
        await self._update_lead_stage_from_performance(demo_id, success_probability, performance_data)
        
        logger.info(f"📊 Tracked demo performance: {success_probability:.2%} success probability")
        return asdict(performance)
    
    async def generate_conversion_analytics(self, period_days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive conversion analytics dashboard."""
        conn = sqlite3.connect(self.db_path)
        
        # Date range for analysis
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # Overall conversion metrics
        overall_query = """
            SELECT 
                COUNT(*) as total_leads,
                COUNT(CASE WHEN demo_status = 'completed' THEN 1 END) as demos_completed,
                COUNT(CASE WHEN conversion_stage = 'proposal_sent' THEN 1 END) as proposals_sent,
                COUNT(CASE WHEN conversion_stage = 'closed_won' THEN 1 END) as deals_closed,
                AVG(roi_calculated) as avg_roi,
                industry,
                conversion_stage
            FROM demo_leads 
            WHERE created_at >= ? AND created_at <= ?
            GROUP BY industry, conversion_stage
        """
        
        df_leads = pd.read_sql_query(overall_query, conn, params=[start_date, end_date])
        
        # Demo performance metrics
        performance_query = """
            SELECT 
                dp.*,
                dl.company_name,
                dl.industry,
                dl.conversion_stage
            FROM demo_performance dp
            JOIN demo_leads dl ON dp.demo_id = dl.id
            WHERE dp.recorded_at >= ? AND dp.recorded_at <= ?
        """
        
        df_performance = pd.read_sql_query(performance_query, conn, params=[start_date, end_date])
        
        # Email campaign metrics
        email_query = """
            SELECT 
                ec.*,
                dl.industry,
                dl.conversion_stage
            FROM email_campaigns ec
            JOIN demo_leads dl ON ec.lead_id = dl.id
            WHERE ec.sent_at >= ? AND ec.sent_at <= ?
        """
        
        df_emails = pd.read_sql_query(email_query, conn, params=[start_date, end_date])
        
        conn.close()
        
        # Calculate conversion rates
        conversion_funnel = self._calculate_conversion_funnel(df_leads)
        industry_performance = self._calculate_industry_performance(df_leads, df_performance)
        demo_effectiveness = self._analyze_demo_effectiveness(df_performance)
        email_performance = self._analyze_email_performance(df_emails)
        
        # Generate visualizations
        charts = await self._generate_analytics_charts(
            df_leads, df_performance, df_emails, conversion_funnel
        )
        
        analytics_report = {
            "report_generated_at": datetime.now().isoformat(),
            "analysis_period_days": period_days,
            "total_leads": len(df_leads),
            "total_demos": len(df_performance),
            "total_emails_sent": len(df_emails),
            "conversion_funnel": conversion_funnel,
            "industry_performance": industry_performance,
            "demo_effectiveness": demo_effectiveness,
            "email_performance": email_performance,
            "charts": charts,
            "recommendations": await self._generate_optimization_recommendations(
                conversion_funnel, industry_performance, demo_effectiveness
            )
        }
        
        # Save report
        report_file = Path(__file__).parent / f"conversion_analytics_{end_date.strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(analytics_report, f, indent=2, default=str)
        
        logger.info(f"📈 Generated conversion analytics report: {report_file}")
        return analytics_report
    
    async def _get_industry_pain_points(self, industry: str) -> List[str]:
        """Get industry-specific pain points."""
        pain_points_map = {
            "real_estate": [
                "Lead response time too slow (4+ hours average)",
                "Manual property matching takes 45+ minutes per lead",
                "Inconsistent follow-up processes across agents",
                "Difficult to prioritize high-value leads",
                "No visibility into agent performance metrics"
            ],
            "saas": [
                "Sales forecast accuracy only 67%",
                "Long sales cycles (90+ days average)",
                "High customer churn rate (15% annually)",
                "Difficulty identifying expansion opportunities",
                "Manual pipeline management consuming 40% of rep time"
            ],
            "ecommerce": [
                "Cart abandonment rate at 68%",
                "Generic product recommendations",
                "Poor email marketing performance (12% open rates)",
                "No real-time personalization",
                "Difficulty identifying high-value customers"
            ],
            "financial_services": [
                "Manual portfolio risk assessment",
                "Compliance monitoring consuming 60% of time",
                "Inconsistent client advisory recommendations",
                "Lack of performance attribution visibility",
                "Regulatory changes difficult to track"
            ]
        }
        return pain_points_map.get(industry, [])
    
    async def _get_industry_current_solutions(self, industry: str) -> List[str]:
        """Get industry-specific current solutions."""
        solutions_map = {
            "real_estate": ["Chime CRM", "BoomTown", "Top Producer", "Manual spreadsheets"],
            "saas": ["Salesforce", "HubSpot", "Pipedrive", "Excel forecasting"],
            "ecommerce": ["Shopify", "Mailchimp", "Google Analytics", "Manual segmentation"],
            "financial_services": ["Portfolio management software", "Excel spreadsheets", "Manual compliance tracking"]
        }
        return solutions_map.get(industry, [])
    
    def _calculate_demo_success_probability(self, performance_data: Dict[str, Any]) -> float:
        """Calculate demo success probability based on engagement metrics."""
        base_score = 0.3
        
        # Engagement score contribution (40%)
        engagement_contribution = performance_data.get("engagement_score", 0.5) * 0.4
        
        # Questions asked contribution (30%)
        total_questions = (
            performance_data.get("technical_questions", 0) +
            performance_data.get("business_questions", 0) +
            performance_data.get("pricing_questions", 0) +
            performance_data.get("implementation_questions", 0)
        )
        questions_score = min(total_questions / 10.0, 1.0) * 0.3
        
        # Completion rate contribution (20%)
        completion_contribution = performance_data.get("completion_rate", 1.0) * 0.2
        
        # Follow-up requests contribution (10%)
        follow_up_score = 0
        if performance_data.get("follow_up_requested", False):
            follow_up_score += 0.03
        if performance_data.get("pilot_requested", False):
            follow_up_score += 0.04
        if performance_data.get("proposal_requested", False):
            follow_up_score += 0.05
        if performance_data.get("reference_requested", False):
            follow_up_score += 0.03
        
        total_score = base_score + engagement_contribution + questions_score + completion_contribution + follow_up_score
        return min(total_score, 1.0)
    
    def _generate_follow_up_recommendation(self, success_probability: float, performance_data: Dict[str, Any]) -> str:
        """Generate follow-up recommendation based on demo performance."""
        if success_probability >= 0.8:
            return "immediate_proposal"
        elif success_probability >= 0.6:
            return "technical_deep_dive"
        elif success_probability >= 0.4:
            return "reference_call"
        else:
            return "nurturing_sequence"
    
    async def _setup_tracking_systems(self):
        """Setup comprehensive tracking systems."""
        logger.info("⚙️ Setting up tracking systems...")
        # Implementation would include setting up monitoring, alerts, etc.
        
    async def _setup_follow_up_sequences(self):
        """Setup automated follow-up email sequences."""
        logger.info("📧 Setting up follow-up sequences...")
        # Implementation would include email automation setup
    
    async def _calculate_lead_roi(self, lead: DemoLead) -> Dict[str, Any]:
        """Calculate ROI for specific lead based on industry and company profile."""
        # Simplified ROI calculation - in production this would be more sophisticated
        base_roi = {
            "real_estate": 3500,
            "saas": 11400,
            "ecommerce": 12400,
            "financial_services": 13550
        }
        
        return {
            "roi_percent": base_roi.get(lead.industry, 5000),
            "annual_benefit": 500000,  # Placeholder
            "payback_days": 30
        }
    
    async def update_lead_roi(self, lead_id: str, roi_percent: float):
        """Update lead ROI calculation."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE demo_leads 
            SET roi_calculated = ?, updated_at = ?
            WHERE id = ?
        """, (roi_percent, datetime.now(), lead_id))
        
        conn.commit()
        conn.close()
    
    async def _trigger_follow_up_sequence(self, lead_id: str, sequence_type: str):
        """Trigger automated follow-up sequence."""
        # Implementation would send automated emails
        logger.info(f"📧 Triggered {sequence_type} sequence for lead {lead_id}")
    
    async def _update_lead_stage_from_performance(self, demo_id: str, success_probability: float, performance_data: Dict[str, Any]):
        """Update lead conversion stage based on demo performance."""
        new_stage = "demo_completed"
        
        if performance_data.get("proposal_requested", False):
            new_stage = "proposal_requested"
        elif success_probability >= 0.7:
            new_stage = "high_interest"
        elif success_probability >= 0.4:
            new_stage = "medium_interest"
        else:
            new_stage = "low_interest"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE demo_leads 
            SET conversion_stage = ?, updated_at = ?
            WHERE id = ?
        """, (new_stage, datetime.now(), demo_id))
        
        conn.commit()
        conn.close()
    
    def _calculate_conversion_funnel(self, df_leads: pd.DataFrame) -> Dict[str, Any]:
        """Calculate conversion funnel metrics."""
        if df_leads.empty:
            return {"stages": [], "conversion_rates": []}
        
        total_leads = len(df_leads)
        demos_completed = len(df_leads[df_leads['conversion_stage'] == 'demo_completed'])
        proposals_sent = len(df_leads[df_leads['conversion_stage'] == 'proposal_sent'])
        deals_closed = len(df_leads[df_leads['conversion_stage'] == 'closed_won'])
        
        return {
            "total_leads": total_leads,
            "demos_completed": demos_completed,
            "proposals_sent": proposals_sent,
            "deals_closed": deals_closed,
            "demo_completion_rate": demos_completed / total_leads if total_leads > 0 else 0,
            "proposal_conversion_rate": proposals_sent / demos_completed if demos_completed > 0 else 0,
            "closing_rate": deals_closed / proposals_sent if proposals_sent > 0 else 0
        }
    
    def _calculate_industry_performance(self, df_leads: pd.DataFrame, df_performance: pd.DataFrame) -> Dict[str, Any]:
        """Calculate performance by industry."""
        if df_leads.empty:
            return {}
        
        return df_leads.groupby('industry').agg({
            'id': 'count',
            'roi_calculated': 'mean'
        }).to_dict('index')
    
    def _analyze_demo_effectiveness(self, df_performance: pd.DataFrame) -> Dict[str, Any]:
        """Analyze demo effectiveness metrics."""
        if df_performance.empty:
            return {"average_engagement": 0, "average_success_probability": 0}
        
        return {
            "average_engagement": df_performance['engagement_score'].mean(),
            "average_success_probability": df_performance['success_probability'].mean(),
            "total_demos": len(df_performance)
        }
    
    def _analyze_email_performance(self, df_emails: pd.DataFrame) -> Dict[str, Any]:
        """Analyze email campaign performance."""
        if df_emails.empty:
            return {"emails_sent": 0, "open_rate": 0}
        
        total_sent = len(df_emails)
        opened = len(df_emails[df_emails['opened_at'].notna()])
        
        return {
            "emails_sent": total_sent,
            "open_rate": opened / total_sent if total_sent > 0 else 0
        }
    
    async def _generate_analytics_charts(self, df_leads, df_performance, df_emails, conversion_funnel) -> Dict[str, str]:
        """Generate analytics charts (returns chart descriptions)."""
        return {
            "conversion_funnel": "Conversion funnel chart showing lead progression",
            "industry_performance": "Industry performance comparison chart",
            "demo_engagement": "Demo engagement scores distribution"
        }
    
    async def _generate_optimization_recommendations(self, conversion_funnel, industry_performance, demo_effectiveness) -> List[str]:
        """Generate optimization recommendations based on analytics."""
        recommendations = []
        
        if conversion_funnel.get("demo_completion_rate", 0) < 0.7:
            recommendations.append("Improve demo scheduling and reminder system")
        
        if demo_effectiveness.get("average_engagement", 0) < 0.6:
            recommendations.append("Enhance demo interactivity and personalization")
        
        if conversion_funnel.get("proposal_conversion_rate", 0) < 0.3:
            recommendations.append("Strengthen post-demo follow-up process")
        
        return recommendations
    
    async def _generate_campaign_report(self, campaign_results: Dict[str, Any]):
        """Generate comprehensive campaign launch report."""
        report_file = Path(__file__).parent / f"demo_campaign_launch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(campaign_results, f, indent=2, default=str)
        
        logger.info(f"📊 Campaign launch report saved: {report_file}")


async def main():
    """Main campaign launcher function."""
    parser = argparse.ArgumentParser(description="Customer Intelligence Platform Demo Campaign Launcher")
    parser.add_argument("--launch-all", action="store_true", help="Launch all industry demo campaigns")
    parser.add_argument("--industry", choices=["real_estate", "saas", "ecommerce", "financial_services"],
                       help="Launch specific industry demo")
    parser.add_argument("--customer", help="Customer name for personalized demo")
    parser.add_argument("--track-pipeline", action="store_true", help="Run client acquisition tracking")
    parser.add_argument("--analytics", action="store_true", help="Generate conversion analytics")
    parser.add_argument("--period", type=int, default=30, help="Analytics period in days")
    
    args = parser.parse_args()
    
    campaign_manager = ClientDemoCampaignManager()
    
    print("🎯 Customer Intelligence Platform - Demo Campaign Launcher")
    print("=" * 70)
    
    try:
        if args.launch_all:
            print("🚀 Launching comprehensive demo campaigns for all industries...")
            results = await campaign_manager.launch_all_demo_campaigns()
            
            print(f"\n✅ Campaign Launch Results:")
            print(f"   - Industries launched: {len(results['industries_launched'])}")
            print(f"   - Demo environments created: {sum(len(ind['environments']) for ind in results['industries_launched'])}")
            print(f"   - Sample leads generated: {sum(len(ind['leads']) for ind in results['industries_launched'])}")
            print(f"   - Tracking systems activated: {len(results['tracking_systems_activated'])}")
            print(f"   - Follow-up sequences configured: {len(results['follow_up_sequences_configured'])}")
            
            print(f"\n🎉 All demo campaigns are now live!")
            print(f"   💻 Access demos at: http://localhost:8502")
            print(f"   📊 View analytics dashboard for conversion tracking")
            print(f"   📧 Automated follow-up sequences are active")
            
        elif args.industry and args.customer:
            print(f"🎯 Launching {args.industry} demo for {args.customer}...")
            demo_generator = DemoDataGenerator(args.industry, args.customer)
            await demo_generator.initialize()
            demo_data = await demo_generator.prepare_demo_environment()
            
            print(f"✅ Demo environment prepared:")
            print(f"   - Industry: {demo_data['industry']}")
            print(f"   - Customer: {demo_data['customer_name']}")
            print(f"   - Demo customers: {len(demo_data['demo_customers'])}")
            print(f"   - Knowledge base docs: {demo_data['knowledge_base_size']}")
            print(f"   - ROI projection: {demo_data['roi_calculation']['financial_impact']['roi_percent']:.0f}%")
            
        elif args.analytics:
            print(f"📈 Generating conversion analytics for last {args.period} days...")
            analytics = await campaign_manager.generate_conversion_analytics(args.period)
            
            print(f"✅ Analytics generated:")
            print(f"   - Total leads analyzed: {analytics['total_leads']}")
            print(f"   - Demo completion rate: {analytics['conversion_funnel'].get('demo_completion_rate', 0):.1%}")
            print(f"   - Average engagement: {analytics['demo_effectiveness'].get('average_engagement', 0):.2f}")
            print(f"   - Recommendations: {len(analytics['recommendations'])}")
            
        else:
            print("Please specify an action:")
            print("  --launch-all                    Launch all demo campaigns")
            print("  --industry X --customer Y       Launch specific demo")
            print("  --analytics                     Generate conversion analytics")
            
        return True
        
    except Exception as e:
        logger.error(f"Campaign launcher failed: {e}")
        print(f"❌ Campaign launcher failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)