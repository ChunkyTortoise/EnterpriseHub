"""
Jorge's Real Estate AI Platform - Client Demonstration Service
Professional client demonstration environment with seeded data and scenario management
Version: 2.0.0
"""

import asyncio
import json
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ..database import get_async_session
from ..models.leads import Lead
from ..models.properties import Property
from ..services.cache_service import CacheService
from ..services.roi_calculator_service import ROICalculatorService
from ..services.performance_monitoring_service import performance_monitor
from ..services.claude_assistant import ClaudeAssistant
from .ml_analytics_engine import MLAnalyticsEngine
from .ghl_service import GHLService
import logging

logger = logging.getLogger(__name__)


class DemoScenario(Enum):
    """Professional client demonstration scenarios"""
    LUXURY_AGENT = "luxury_agent"
    MID_MARKET = "mid_market"
    FIRST_TIME_BUYER = "first_time_buyer"
    INVESTOR_FOCUSED = "investor_focused"
    HIGH_VOLUME = "high_volume"


@dataclass
class ClientProfile:
    """Client profile for demonstration purposes"""
    id: str
    name: str
    agency_name: str
    market_segment: DemoScenario
    monthly_leads: int
    avg_deal_size: int
    commission_rate: float
    current_challenges: List[str]
    goals: List[str]
    pain_points: List[str]
    geographic_market: str
    experience_level: str  # novice, experienced, expert
    tech_adoption: str     # low, medium, high


@dataclass
class DemoEnvironment:
    """Complete demonstration environment state"""
    session_id: str
    client_profile: ClientProfile
    demo_leads: List[Dict[str, Any]]
    demo_properties: List[Dict[str, Any]]
    demo_conversations: List[Dict[str, Any]]
    roi_calculation: Dict[str, Any]
    roi_assumptions: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    data_source: str
    data_provenance: Dict[str, Any]
    created_at: datetime
    expires_at: datetime


class ClientDemoService:
    """
    Enterprise-grade client demonstration service for Jorge's AI Platform

    Features:
    - Professional client scenarios (luxury, mid-market, investor)
    - Realistic demo data generation
    - ROI calculations with live metrics
    - Jorge bot conversation demonstrations
    - Performance benchmarking vs traditional methods
    - Client-safe data isolation with auto-cleanup
    """

    def __init__(self):
        self.cache = CacheService()
        self.redis = None
        self.roi_calculator = ROICalculatorService()
        self.claude_assistant = ClaudeAssistant()
        self.ml_analytics = MLAnalyticsEngine()
        self.ghl_service = GHLService()

        # Demo session configuration
        self.session_duration = timedelta(hours=2)  # Demo sessions expire after 2 hours
        self.demo_namespace = "demo"
        self.isolation_prefix = "client_demo"

    async def initialize(self):
        """Initialize Redis connection and demo environment"""
        self.redis = redis.Redis.from_url("redis://localhost:6379", decode_responses=True)
        logger.info("Client demo service initialized")

    def _get_demo_data_source(self) -> str:
        """Resolve demo data source preference."""
        return os.getenv("DEMO_DATA_SOURCE", "synthetic").strip().lower()

    def _build_data_provenance(self, source: str, demo_mode: bool, note: Optional[str] = None) -> Dict[str, Any]:
        """Standardize provenance metadata for enterprise credibility."""
        payload = {
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
            "demo_mode": demo_mode
        }
        if note:
            payload["note"] = note
        return payload

    async def _load_sandbox_data(self, client_profile: ClientProfile) -> Optional[Dict[str, Any]]:
        """
        Attempt to load sandbox data from the database.
        Returns None if sandbox data is unavailable or empty.
        """
        try:
            async with get_async_session() as session:  # type: AsyncSession
                lead_rows = (await session.execute(select(Lead).limit(25))).scalars().all()
                property_rows = (await session.execute(select(Property).limit(25))).scalars().all()

            if not lead_rows and not property_rows:
                return None

            demo_leads = []
            for lead in lead_rows:
                first = getattr(lead, "first_name", "") or ""
                last = getattr(lead, "last_name", "") or ""
                name = (f"{first} {last}").strip() or getattr(lead, "email", "Sandbox Lead")
                lead_score = getattr(lead, "lead_score", 50) or 50
                temperature = "hot" if lead_score >= 80 else "warm" if lead_score >= 50 else "cool"
                demo_leads.append(
                    {
                        "id": str(lead.id),
                        "name": name,
                        "created_at": getattr(lead, "created_at", datetime.utcnow()).isoformat(),
                        "status": getattr(lead, "qualification_stage", "new"),
                        "temperature": temperature,
                        "conversion_probability": min(0.95, max(0.05, lead_score / 100)),
                    }
                )

            demo_properties = [
                {
                    "id": str(prop.id),
                    "address": getattr(prop, "address", "Sandbox Property"),
                    "price": getattr(prop, "price", client_profile.avg_deal_size),
                    "status": getattr(prop, "status", "active"),
                    "market": getattr(prop, "market", client_profile.geographic_market),
                }
                for prop in property_rows
            ]

            return {
                "demo_leads": demo_leads,
                "demo_properties": demo_properties,
                "demo_conversations": []
            }
        except Exception as e:
            logger.warning(f"Sandbox data unavailable: {e}")
            return None

    def _build_roi_assumptions(self, client_profile: ClientProfile) -> Dict[str, Any]:
        """Expose ROI assumptions used for demo calculations."""
        return {
            "monthly_leads": client_profile.monthly_leads,
            "avg_deal_size": client_profile.avg_deal_size,
            "commission_rate": client_profile.commission_rate,
            "current_conversion_rate": 0.15,
            "target_conversion_rate": 0.25,
            "current_response_time_hours": 3.5,
            "jorge_response_time_seconds": 30,
            "current_accuracy": 0.65,
            "jorge_accuracy": 0.95
        }

    async def create_demo_session(
        self,
        scenario: DemoScenario,
        client_name: str = None,
        agency_name: str = None,
        custom_params: Dict[str, Any] = None
    ) -> DemoEnvironment:
        """
        Create a new client demonstration session with seeded data

        Args:
            scenario: Pre-configured demo scenario
            client_name: Optional custom client name
            agency_name: Optional custom agency name
            custom_params: Optional custom parameters to override defaults

        Returns:
            Complete demo environment ready for presentation
        """
        session_id = str(uuid.uuid4())

        # Create client profile based on scenario
        client_profile = self._create_client_profile(
            scenario,
            client_name or f"Demo {scenario.value.replace('_', ' ').title()}",
            agency_name,
            custom_params
        )

        # Generate demo data (sandbox preferred, fallback to synthetic)
        demo_source = self._get_demo_data_source()
        sandbox_payload = None
        if demo_source == "sandbox":
            sandbox_payload = await self._load_sandbox_data(client_profile)

        if sandbox_payload:
            demo_leads = sandbox_payload["demo_leads"]
            demo_properties = sandbox_payload["demo_properties"]
            demo_conversations = sandbox_payload["demo_conversations"]
            data_source = "sandbox"
            data_provenance = self._build_data_provenance(
                source="sandbox_db",
                demo_mode=False,
                note="Loaded from sandbox database"
            )
        else:
            demo_leads = await self._generate_demo_leads(client_profile)
            demo_properties = await self._generate_demo_properties(client_profile)
            demo_conversations = await self._generate_demo_conversations(client_profile, demo_leads)
            data_source = "synthetic"
            data_provenance = self._build_data_provenance(
                source="synthetic_generator",
                demo_mode=True,
                note="Generated demo data (sandbox unavailable)"
            )

        # Calculate ROI based on client profile
        roi_calculation = await self._calculate_demo_roi(client_profile)
        roi_assumptions = self._build_roi_assumptions(client_profile)

        # Generate performance metrics
        performance_metrics = await self._generate_performance_metrics(client_profile)

        # Record KPI telemetry for proof and export
        try:
            monthly_perf = performance_metrics.get("monthly_performance", {})
            performance_monitor.record_kpi_event(
                "leads_processed",
                monthly_perf.get("leads_processed"),
                {"source": data_source, "scenario": scenario.value}
            )
            performance_monitor.record_kpi_event(
                "traditional_conversions",
                monthly_perf.get("traditional_conversions"),
                {"source": data_source, "scenario": scenario.value}
            )
            performance_monitor.record_kpi_event(
                "jorge_conversions",
                monthly_perf.get("jorge_conversions"),
                {"source": data_source, "scenario": scenario.value}
            )
            performance_monitor.record_kpi_event(
                "response_time_jorge",
                performance_metrics.get("response_times", {}).get("jorge_avg"),
                {"source": data_source, "scenario": scenario.value}
            )
        except Exception as e:
            logger.warning(f"Failed to record KPI telemetry: {e}")

        # Create demo environment
        demo_env = DemoEnvironment(
            session_id=session_id,
            client_profile=client_profile,
            demo_leads=demo_leads,
            demo_properties=demo_properties,
            demo_conversations=demo_conversations,
            roi_calculation=roi_calculation,
            roi_assumptions=roi_assumptions,
            performance_metrics=performance_metrics,
            data_source=data_source,
            data_provenance=data_provenance,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.session_duration
        )

        # Store in Redis with expiration
        await self._store_demo_environment(demo_env)

        logger.info(f"Created demo session {session_id} for scenario {scenario.value}")
        return demo_env

    async def get_demo_session(self, session_id: str) -> Optional[DemoEnvironment]:
        """Retrieve existing demo session"""
        try:
            demo_data = await self.redis.get(f"{self.isolation_prefix}:session:{session_id}")
            if not demo_data:
                return None

            data = json.loads(demo_data)

            # Convert back to DemoEnvironment
            client_profile = ClientProfile(**data['client_profile'])
            demo_env = DemoEnvironment(
                session_id=data['session_id'],
                client_profile=client_profile,
                demo_leads=data['demo_leads'],
                demo_properties=data['demo_properties'],
                demo_conversations=data['demo_conversations'],
                roi_calculation=data['roi_calculation'],
                roi_assumptions=data.get('roi_assumptions', {}),
                performance_metrics=data['performance_metrics'],
                data_source=data.get('data_source', 'synthetic'),
                data_provenance=data.get('data_provenance', self._build_data_provenance("unknown", True, "Missing provenance")),
                created_at=datetime.fromisoformat(data['created_at']),
                expires_at=datetime.fromisoformat(data['expires_at'])
            )

            # Check if session has expired
            if datetime.utcnow() > demo_env.expires_at:
                await self.cleanup_demo_session(session_id)
                return None

            return demo_env

        except Exception as e:
            logger.error(f"Error retrieving demo session {session_id}: {str(e)}")
            return None

    async def extend_demo_session(self, session_id: str, additional_hours: int = 1) -> bool:
        """Extend demo session duration"""
        demo_env = await self.get_demo_session(session_id)
        if not demo_env:
            return False

        demo_env.expires_at += timedelta(hours=additional_hours)
        await self._store_demo_environment(demo_env)

        logger.info(f"Extended demo session {session_id} by {additional_hours} hours")
        return True

    async def reset_demo_session(self, session_id: str) -> DemoEnvironment:
        """Reset demo session with fresh data but same client profile"""
        demo_env = await self.get_demo_session(session_id)
        if not demo_env:
            raise ValueError(f"Demo session {session_id} not found")

        # Clean up old data
        await self.cleanup_demo_session(session_id)

        # Create new session with same client profile
        return await self.create_demo_session(
            demo_env.client_profile.market_segment,
            demo_env.client_profile.name,
            demo_env.client_profile.agency_name
        )

    async def cleanup_demo_session(self, session_id: str) -> bool:
        """Clean up demo session data"""
        try:
            # Remove from Redis
            await self.redis.delete(f"{self.isolation_prefix}:session:{session_id}")

            # Clean up any related cache entries
            pattern = f"{self.isolation_prefix}:data:{session_id}:*"
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)

            logger.info(f"Cleaned up demo session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error cleaning up demo session {session_id}: {str(e)}")
            return False

    async def cleanup_expired_sessions(self) -> int:
        """Clean up all expired demo sessions"""
        try:
            pattern = f"{self.isolation_prefix}:session:*"
            session_keys = await self.redis.keys(pattern)

            expired_count = 0
            for key in session_keys:
                session_data = await self.redis.get(key)
                if session_data:
                    data = json.loads(session_data)
                    expires_at = datetime.fromisoformat(data['expires_at'])

                    if datetime.utcnow() > expires_at:
                        session_id = data['session_id']
                        await self.cleanup_demo_session(session_id)
                        expired_count += 1

            logger.info(f"Cleaned up {expired_count} expired demo sessions")
            return expired_count

        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")
            return 0

    def _create_client_profile(
        self,
        scenario: DemoScenario,
        client_name: str,
        agency_name: str = None,
        custom_params: Dict[str, Any] = None
    ) -> ClientProfile:
        """Create client profile based on demonstration scenario"""

        scenario_configs = {
            DemoScenario.LUXURY_AGENT: {
                "agency_name": agency_name or "Elite Properties Group",
                "monthly_leads": 25,
                "avg_deal_size": 850000,
                "commission_rate": 0.06,
                "current_challenges": [
                    "High-net-worth clients expect immediate responses",
                    "Competitive luxury market with demanding clients",
                    "Managing multiple $1M+ transactions simultaneously",
                    "Maintaining white-glove service at scale"
                ],
                "goals": [
                    "Increase deal volume without compromising service quality",
                    "Improve response times to under 30 seconds",
                    "Automate initial qualification while maintaining luxury experience",
                    "Scale to handle 40+ high-value leads per month"
                ],
                "pain_points": [
                    "Missing qualified leads due to delayed responses",
                    "High operational costs with traditional staff",
                    "Difficulty maintaining consistency across team",
                    "Time-intensive manual lead qualification process"
                ],
                "geographic_market": "Beverly Hills, CA / Manhattan, NY",
                "experience_level": "expert",
                "tech_adoption": "medium"
            },

            DemoScenario.MID_MARKET: {
                "agency_name": agency_name or "Hometown Realty Partners",
                "monthly_leads": 45,
                "avg_deal_size": 425000,
                "commission_rate": 0.06,
                "current_challenges": [
                    "High volume of leads with limited staff",
                    "Inconsistent follow-up processes",
                    "Difficulty prioritizing qualified prospects",
                    "Manual CRM updates consuming valuable time"
                ],
                "goals": [
                    "Increase conversion rate from 15% to 25%",
                    "Automate initial lead qualification",
                    "Improve follow-up consistency",
                    "Scale team efficiency without hiring"
                ],
                "pain_points": [
                    "Leads falling through cracks in busy periods",
                    "Spending too much time on unqualified prospects",
                    "Inconsistent client communication",
                    "Manual administrative tasks reducing selling time"
                ],
                "geographic_market": "Austin, TX Metro Area",
                "experience_level": "experienced",
                "tech_adoption": "medium"
            },

            DemoScenario.FIRST_TIME_BUYER: {
                "agency_name": agency_name or "First Home Specialists",
                "monthly_leads": 60,
                "avg_deal_size": 320000,
                "commission_rate": 0.06,
                "current_challenges": [
                    "First-time buyers need extensive education",
                    "High volume of questions and concerns",
                    "Long sales cycles with emotional decisions",
                    "Managing complex financing scenarios"
                ],
                "goals": [
                    "Streamline first-time buyer education process",
                    "Reduce average time-to-close from 45 to 35 days",
                    "Improve client satisfaction scores",
                    "Handle more transactions with same team size"
                ],
                "pain_points": [
                    "Repetitive education conversations",
                    "High emotional support requirements",
                    "Complex financing coordination",
                    "Time-intensive hand-holding throughout process"
                ],
                "geographic_market": "Phoenix, AZ / Tampa, FL",
                "experience_level": "experienced",
                "tech_adoption": "high"
            },

            DemoScenario.INVESTOR_FOCUSED: {
                "agency_name": agency_name or "Investment Property Pros",
                "monthly_leads": 35,
                "avg_deal_size": 750000,
                "commission_rate": 0.06,
                "current_challenges": [
                    "Investors require detailed market analysis",
                    "Need rapid response for investment opportunities",
                    "Managing multiple portfolio acquisitions",
                    "Providing accurate ROI calculations on demand"
                ],
                "goals": [
                    "Provide instant market analysis and ROI projections",
                    "Increase deal velocity for time-sensitive opportunities",
                    "Expand investor client base",
                    "Automate property comparison reports"
                ],
                "pain_points": [
                    "Time-intensive financial analysis preparation",
                    "Missing opportunities due to slow response times",
                    "Manual research for market comparisons",
                    "Difficulty managing multiple investor portfolios"
                ],
                "geographic_market": "Dallas, TX / Atlanta, GA",
                "experience_level": "expert",
                "tech_adoption": "high"
            },

            DemoScenario.HIGH_VOLUME: {
                "agency_name": agency_name or "Metro Realty Network",
                "monthly_leads": 120,
                "avg_deal_size": 380000,
                "commission_rate": 0.05,  # Lower commission, higher volume
                "current_challenges": [
                    "Managing extremely high lead volume",
                    "Maintaining quality with quantity focus",
                    "Team coordination across multiple agents",
                    "Scaling systems for growth"
                ],
                "goals": [
                    "Increase monthly closings from 25 to 40",
                    "Maintain 90%+ client satisfaction despite volume",
                    "Automate lead distribution and initial contact",
                    "Optimize team productivity across all agents"
                ],
                "pain_points": [
                    "Lead management becomes overwhelming",
                    "Quality control difficult at scale",
                    "Agent burnout from high volume",
                    "Technology gaps limiting efficiency"
                ],
                "geographic_market": "Houston, TX / Orlando, FL",
                "experience_level": "experienced",
                "tech_adoption": "high"
            }
        }

        config = scenario_configs[scenario]

        # Apply custom parameters if provided
        if custom_params:
            config.update(custom_params)

        return ClientProfile(
            id=str(uuid.uuid4()),
            name=client_name,
            market_segment=scenario,
            **config
        )

    async def _generate_demo_leads(self, client_profile: ClientProfile) -> List[Dict[str, Any]]:
        """Generate realistic demo leads based on client profile"""
        leads = []

        # Generate leads for the past 30 days
        base_date = datetime.utcnow() - timedelta(days=30)

        # Lead templates based on market segment
        lead_templates = self._get_lead_templates(client_profile.market_segment)

        for i in range(client_profile.monthly_leads):
            lead_template = lead_templates[i % len(lead_templates)]

            # Create lead with realistic progression
            created_date = base_date + timedelta(
                days=i * 30 / client_profile.monthly_leads,
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60)
            )

            lead = {
                "id": str(uuid.uuid4()),
                "name": lead_template["name"],
                "email": f"{lead_template['name'].lower().replace(' ', '.')}@example.com",
                "phone": f"+1{np.random.randint(200, 999):03d}{np.random.randint(200, 999):03d}{np.random.randint(1000, 9999):04d}",
                "source": lead_template["source"],
                "budget_min": lead_template["budget_min"],
                "budget_max": lead_template["budget_max"],
                "location_preference": lead_template["location"],
                "urgency": lead_template["urgency"],
                "qualification_status": lead_template["status"],
                "temperature": lead_template["temperature"],
                "created_at": created_date.isoformat(),
                "last_contact": (created_date + timedelta(days=np.random.randint(1, 7))).isoformat(),
                "jorge_interactions": np.random.randint(1, 8),
                "conversion_probability": lead_template["conversion_prob"],
                "notes": lead_template["notes"]
            }

            leads.append(lead)

        return sorted(leads, key=lambda x: x['created_at'], reverse=True)

    async def _generate_demo_properties(self, client_profile: ClientProfile) -> List[Dict[str, Any]]:
        """Generate realistic demo properties for matching"""
        properties = []

        property_templates = self._get_property_templates(client_profile.market_segment)

        for i, template in enumerate(property_templates):
            property_data = {
                "id": str(uuid.uuid4()),
                "mls_id": f"MLS{np.random.randint(1000000, 9999999)}",
                "address": template["address"],
                "price": template["price"],
                "bedrooms": template["bedrooms"],
                "bathrooms": template["bathrooms"],
                "square_feet": template["sqft"],
                "property_type": template["type"],
                "listing_date": (datetime.utcnow() - timedelta(days=np.random.randint(1, 60))).isoformat(),
                "days_on_market": np.random.randint(1, 60),
                "price_per_sqft": template["price"] / template["sqft"],
                "neighborhood": template["neighborhood"],
                "features": template["features"],
                "status": template["status"],
                "agent_notes": template["notes"]
            }

            properties.append(property_data)

        return properties

    async def _generate_demo_conversations(
        self,
        client_profile: ClientProfile,
        demo_leads: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate realistic Jorge bot conversations"""
        conversations = []

        # Generate conversations for top 10 leads
        top_leads = demo_leads[:10]

        for lead in top_leads:
            conversation_templates = self._get_conversation_templates(
                client_profile.market_segment,
                lead["qualification_status"]
            )

            conversation = {
                "id": str(uuid.uuid4()),
                "lead_id": lead["id"],
                "lead_name": lead["name"],
                "conversation_type": "Jorge Seller Bot",
                "start_time": lead["created_at"],
                "end_time": (datetime.fromisoformat(lead["created_at"]) + timedelta(minutes=np.random.randint(5, 25))).isoformat(),
                "messages": conversation_templates["messages"],
                "sentiment_analysis": conversation_templates["sentiment"],
                "qualification_result": {
                    "financial_readiness_score": conversation_templates["frs_score"],
                    "psychological_commitment_score": conversation_templates["pcs_score"],
                    "overall_temperature": lead["temperature"],
                    "key_insights": conversation_templates["insights"],
                    "recommended_actions": conversation_templates["actions"]
                },
                "jorge_performance": {
                    "response_time_avg": "28 seconds",
                    "accuracy_score": 0.94,
                    "engagement_score": conversation_templates["engagement"],
                    "conversion_likelihood": lead["conversion_probability"]
                }
            }

            conversations.append(conversation)

        return conversations

    async def _calculate_demo_roi(self, client_profile: ClientProfile) -> Dict[str, Any]:
        """Calculate ROI demonstration using existing ROI calculator"""
        try:
            # Use existing ROI calculator with demo parameters
            demo_params = {
                "monthly_leads": client_profile.monthly_leads,
                "avg_deal_size": client_profile.avg_deal_size,
                "commission_rate": client_profile.commission_rate,
                "current_conversion_rate": 0.15,  # Industry average
                "target_conversion_rate": 0.25,   # With Jorge AI
                "current_response_time_hours": 3.5,
                "jorge_response_time_seconds": 30,
                "current_accuracy": 0.65,
                "jorge_accuracy": 0.95
            }

            roi_calculation = {
                "scenario": client_profile.market_segment.value,
                "time_horizon_months": 12,
                "traditional_costs": {
                    "agent_salary": 180000,  # $15k/month fully loaded cost
                    "commission_total": client_profile.monthly_leads * 0.15 * client_profile.avg_deal_size * client_profile.commission_rate * 12,
                    "marketing_costs": 36000,  # $3k/month
                    "administrative_overhead": 24000,  # $2k/month
                    "opportunity_cost": 48000  # Lost deals due to slow response
                },
                "jorge_costs": {
                    "platform_fee": 30000,   # $2.5k/month
                    "commission_total": client_profile.monthly_leads * 0.25 * client_profile.avg_deal_size * client_profile.commission_rate * 12,
                    "setup_cost": 5000       # One-time implementation
                },
                "jorge_benefits": {
                    "faster_response": {
                        "additional_conversions": client_profile.monthly_leads * 0.03 * 12,  # 3% improvement from speed
                        "value": client_profile.monthly_leads * 0.03 * 12 * client_profile.avg_deal_size * client_profile.commission_rate
                    },
                    "higher_accuracy": {
                        "additional_conversions": client_profile.monthly_leads * 0.07 * 12,  # 7% from better qualification
                        "value": client_profile.monthly_leads * 0.07 * 12 * client_profile.avg_deal_size * client_profile.commission_rate
                    },
                    "24_7_availability": {
                        "additional_conversions": client_profile.monthly_leads * 0.02 * 12,  # 2% from availability
                        "value": client_profile.monthly_leads * 0.02 * 12 * client_profile.avg_deal_size * client_profile.commission_rate
                    },
                    "cost_reduction": {
                        "staffing_savings": 150000,  # Reduced staffing needs
                        "operational_efficiency": 24000  # Less administrative overhead
                    }
                }
            }

            # Calculate totals
            traditional_total = sum(roi_calculation["traditional_costs"].values())
            jorge_total = sum(roi_calculation["jorge_costs"].values())
            benefits_total = sum([
                roi_calculation["jorge_benefits"]["faster_response"]["value"],
                roi_calculation["jorge_benefits"]["higher_accuracy"]["value"],
                roi_calculation["jorge_benefits"]["24_7_availability"]["value"],
                roi_calculation["jorge_benefits"]["cost_reduction"]["staffing_savings"],
                roi_calculation["jorge_benefits"]["cost_reduction"]["operational_efficiency"]
            ])

            roi_calculation["summary"] = {
                "traditional_total_cost": traditional_total,
                "jorge_total_cost": jorge_total,
                "total_benefits": benefits_total,
                "net_savings": benefits_total - (jorge_total - traditional_total),
                "roi_percentage": ((benefits_total - (jorge_total - traditional_total)) / traditional_total) * 100,
                "payback_period_months": (jorge_total - traditional_total) / ((benefits_total - (jorge_total - traditional_total)) / 12),
                "cost_reduction_percentage": ((traditional_total - jorge_total) / traditional_total) * 100
            }

            return roi_calculation

        except Exception as e:
            logger.error(f"Error calculating demo ROI: {str(e)}")
            # Return fallback calculation
            return {
                "error": "ROI calculation failed",
                "fallback_savings": "75%",
                "fallback_roi": "300%"
            }

    async def _generate_performance_metrics(self, client_profile: ClientProfile) -> Dict[str, Any]:
        """Generate realistic performance metrics for demonstration"""

        # Base metrics that scale with client profile
        base_conversions = client_profile.monthly_leads * 0.15  # 15% traditional conversion
        jorge_conversions = client_profile.monthly_leads * 0.25  # 25% with Jorge AI

        metrics = {
            "response_times": {
                "traditional_avg": "3.5 hours",
                "jorge_avg": "28 seconds",
                "improvement": "99.8%"
            },
            "conversion_rates": {
                "traditional": f"{15:.1f}%",
                "jorge": f"{25:.1f}%",
                "improvement": f"{((0.25 - 0.15) / 0.15) * 100:.1f}%"
            },
            "accuracy_scores": {
                "traditional": "65%",
                "jorge": "95%",
                "improvement": "46%"
            },
            "monthly_performance": {
                "leads_processed": client_profile.monthly_leads,
                "traditional_conversions": int(base_conversions),
                "jorge_conversions": int(jorge_conversions),
                "additional_deals": int(jorge_conversions - base_conversions),
                "additional_revenue": int((jorge_conversions - base_conversions) * client_profile.avg_deal_size * client_profile.commission_rate)
            },
            "operational_efficiency": {
                "traditional_hours_per_lead": 2.5,
                "jorge_hours_per_lead": 0.3,
                "time_savings_per_lead": 2.2,
                "monthly_time_savings": client_profile.monthly_leads * 2.2,
                "cost_savings_monthly": client_profile.monthly_leads * 2.2 * 75  # $75/hour agent cost
            },
            "client_satisfaction": {
                "traditional_nps": 7.2,
                "jorge_nps": 8.9,
                "satisfaction_improvement": "24%"
            },
            "business_impact": {
                "revenue_increase": f"${int((jorge_conversions - base_conversions) * client_profile.avg_deal_size * client_profile.commission_rate):,}/month",
                "cost_reduction": "75%",
                "roi": "300%",
                "payback_period": "3.2 months"
            }
        }

        return metrics

    async def _store_demo_environment(self, demo_env: DemoEnvironment):
        """Store demo environment in Redis with expiration"""
        try:
            # Convert to JSON-serializable format
            data = {
                "session_id": demo_env.session_id,
                "client_profile": asdict(demo_env.client_profile),
                "demo_leads": demo_env.demo_leads,
                "demo_properties": demo_env.demo_properties,
                "demo_conversations": demo_env.demo_conversations,
                "roi_calculation": demo_env.roi_calculation,
                "roi_assumptions": demo_env.roi_assumptions,
                "performance_metrics": demo_env.performance_metrics,
                "data_source": demo_env.data_source,
                "data_provenance": demo_env.data_provenance,
                "created_at": demo_env.created_at.isoformat(),
                "expires_at": demo_env.expires_at.isoformat()
            }

            # Store in Redis with TTL
            key = f"{self.isolation_prefix}:session:{demo_env.session_id}"
            await self.redis.setex(
                key,
                int(self.session_duration.total_seconds()),
                json.dumps(data, default=str)
            )

            logger.info(f"Stored demo environment {demo_env.session_id}")

        except Exception as e:
            logger.error(f"Error storing demo environment: {str(e)}")
            raise

    def _get_lead_templates(self, scenario: DemoScenario) -> List[Dict[str, Any]]:
        """Get lead templates based on scenario"""
        from .demo_data_templates import DemoDataTemplates
        return DemoDataTemplates.get_lead_templates(scenario)

    def _get_property_templates(self, scenario: DemoScenario) -> List[Dict[str, Any]]:
        """Get property templates based on scenario"""
        from .demo_data_templates import DemoDataTemplates
        return DemoDataTemplates.get_property_templates(scenario)

    def _get_conversation_templates(self, scenario: DemoScenario, status: str) -> Dict[str, Any]:
        """Get conversation templates based on scenario and qualification status"""
        from .demo_data_templates import DemoDataTemplates
        return DemoDataTemplates.get_conversation_templates(scenario, status)


# Import numpy for random number generation
import numpy as np
