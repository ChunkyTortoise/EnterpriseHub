"""
Client Demo Data Seeder - Track 4 Production Hosting
Generates realistic demo data for Jorge's AI platform client presentations.

Features:
🎭 Diverse lead profiles for demonstration scenarios
🏠 Property listings with realistic market data
💬 Bot conversation histories showing Jorge's methodology
📅 Appointment scheduling and calendar integration
📊 Performance metrics and success stories
"""

import asyncio
import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.ghl_service import GHLService
from ghl_real_estate_ai.services.memory_service import MemoryService

logger = get_logger(__name__)

# =============================================================================
# DEMO DATA MODELS
# =============================================================================


@dataclass
class DemoLead:
    """Realistic lead profile for client demonstrations."""

    name: str
    phone: str
    email: str
    property_address: str
    city: str
    state: str
    zip_code: str

    # Jorge's qualification data
    seller_temperature: int  # 0-100 scale
    qualification_stage: str
    timeline: str
    motivation: str
    property_value: int
    asking_price: int

    # Demo scenario metadata
    demo_scenario: str
    personality_type: str
    objection_profile: str
    success_probability: float

    # Conversation history
    conversation_count: int
    last_contact: datetime
    next_followup: Optional[datetime]


@dataclass
class DemoProperty:
    """Property listing for demonstration."""

    address: str
    city: str
    state: str
    zip_code: str
    property_type: str

    # Property details
    bedrooms: int
    bathrooms: float
    square_feet: int
    lot_size: float
    year_built: int

    # Market data
    estimated_value: int
    asking_price: int
    days_on_market: int
    price_per_sqft: int

    # Demo metadata
    demo_scenario: str
    market_trend: str
    selling_points: List[str]
    potential_objections: List[str]


@dataclass
class DemoConversation:
    """Bot conversation for demonstration."""

    lead_id: str
    conversation_type: str  # qualification, objection_handling, follow_up
    bot_name: str  # jorge_seller_bot, lead_bot

    # Conversation details
    messages: List[Dict[str, Any]]
    duration_minutes: int
    outcome: str
    sentiment_score: float

    # Jorge methodology metrics
    confrontational_moments: int
    objections_addressed: int
    qualification_score: int
    temperature_change: int

    # Demo metadata
    demo_scenario: str
    learning_points: List[str]


class ClientDemoDataSeeder:
    """
    Seeds realistic demo data for Jorge's AI platform client presentations.

    Features:
    - Diverse lead scenarios showcasing different qualification outcomes
    - Realistic property listings with market intelligence
    - Bot conversation histories demonstrating Jorge's methodology
    - Success metrics and ROI data for client presentations
    """

    def __init__(self):
        self.ghl_service = GHLService()
        self.memory_service = MemoryService()
        self.cache = get_cache_service()

        # Demo configuration
        self.demo_leads_count = 15
        self.demo_properties_count = 20
        self.demo_conversations_count = 45

        logger.info("Client Demo Data Seeder initialized")

    # =========================================================================
    # MAIN SEEDING METHODS
    # =========================================================================

    async def seed_complete_demo_environment(self) -> Dict[str, Any]:
        """
        Seed complete demo environment for client presentations.
        Returns summary of seeded data for presentation setup.
        """
        logger.info("🎭 Seeding complete demo environment for client presentations...")

        seeding_summary = {"seeding_started": datetime.now().isoformat(), "demo_scenarios": [], "data_summary": {}}

        try:
            # Seed core demo data
            leads = await self._seed_demo_leads()
            properties = await self._seed_demo_properties()
            conversations = await self._seed_demo_conversations(leads)
            appointments = await self._seed_demo_appointments(leads)
            metrics = await self._seed_demo_metrics(leads, conversations)

            # Create demo scenarios for presentations
            scenarios = await self._create_presentation_scenarios(leads, conversations)

            seeding_summary.update(
                {
                    "data_summary": {
                        "leads_created": len(leads),
                        "properties_created": len(properties),
                        "conversations_created": len(conversations),
                        "appointments_scheduled": len(appointments),
                        "demo_scenarios": len(scenarios),
                    },
                    "demo_scenarios": scenarios,
                    "seeding_completed": datetime.now().isoformat(),
                }
            )

            # Cache demo data for quick access during presentations
            await self._cache_demo_data_for_presentations(seeding_summary)

            logger.info(
                f"✅ Demo environment seeded successfully: {len(leads)} leads, "
                f"{len(properties)} properties, {len(conversations)} conversations"
            )

            return seeding_summary

        except Exception as e:
            logger.error(f"❌ Error seeding demo environment: {e}")
            seeding_summary["error"] = str(e)
            return seeding_summary

    async def _seed_demo_leads(self) -> List[DemoLead]:
        """Create diverse lead profiles for demonstration scenarios."""
        logger.info("👥 Creating demo lead profiles...")

        demo_leads = [
            # Hot Leads (High Temperature, Ready to Act)
            DemoLead(
                name="Sarah Johnson",
                phone="(555) 123-4567",
                email="sarah.johnson@email.com",
                property_address="1247 Oak Avenue",
                city="Austin",
                state="TX",
                zip_code="78701",
                seller_temperature=92,
                qualification_stage="qualified",
                timeline="30_days",
                motivation="job_relocation",
                property_value=485000,
                asking_price=475000,
                demo_scenario="motivated_seller_success",
                personality_type="decisive_professional",
                objection_profile="price_conscious",
                success_probability=0.89,
                conversation_count=4,
                last_contact=datetime.now() - timedelta(days=2),
                next_followup=datetime.now() + timedelta(days=1),
            ),
            DemoLead(
                name="Michael Rodriguez",
                phone="(555) 234-5678",
                email="m.rodriguez@email.com",
                property_address="2156 Pine Street",
                city="Cedar Park",
                state="TX",
                zip_code="78613",
                seller_temperature=87,
                qualification_stage="qualified",
                timeline="45_days",
                motivation="downsizing",
                property_value=340000,
                asking_price=335000,
                demo_scenario="downsizing_success",
                personality_type="analytical_researcher",
                objection_profile="market_timing",
                success_probability=0.84,
                conversation_count=6,
                last_contact=datetime.now() - timedelta(days=1),
                next_followup=datetime.now() + timedelta(hours=8),
            ),
            # Warm Leads (Medium Temperature, Needs Nurturing)
            DemoLead(
                name="Jennifer Chen",
                phone="(555) 345-6789",
                email="jchen@email.com",
                property_address="3024 Maple Drive",
                city="Round Rock",
                state="TX",
                zip_code="78664",
                seller_temperature=67,
                qualification_stage="in_progress",
                timeline="60_days",
                motivation="upgrade_home",
                property_value=520000,
                asking_price=510000,
                demo_scenario="nurturing_to_conversion",
                personality_type="relationship_focused",
                objection_profile="agent_comparison",
                success_probability=0.71,
                conversation_count=3,
                last_contact=datetime.now() - timedelta(days=5),
                next_followup=datetime.now() + timedelta(days=2),
            ),
            DemoLead(
                name="David Thompson",
                phone="(555) 456-7890",
                email="dthompson@email.com",
                property_address="4187 Elm Court",
                city="Austin",
                state="TX",
                zip_code="78750",
                seller_temperature=59,
                qualification_stage="initial_contact",
                timeline="90_days",
                motivation="investment_liquidation",
                property_value=675000,
                asking_price=695000,
                demo_scenario="price_adjustment_needed",
                personality_type="investor_mindset",
                objection_profile="pricing_unrealistic",
                success_probability=0.63,
                conversation_count=2,
                last_contact=datetime.now() - timedelta(days=7),
                next_followup=datetime.now() + timedelta(days=3),
            ),
            # Cold Leads (Low Temperature, Difficult Conversions)
            DemoLead(
                name="Robert Williams",
                phone="(555) 567-8901",
                email="rwilliams@email.com",
                property_address="5293 Birch Lane",
                city="Pflugerville",
                state="TX",
                zip_code="78660",
                seller_temperature=34,
                qualification_stage="unqualified",
                timeline="exploring",
                motivation="market_curiosity",
                property_value=295000,
                asking_price=315000,
                demo_scenario="challenging_lead_handling",
                personality_type="skeptical_researcher",
                objection_profile="multiple_objections",
                success_probability=0.28,
                conversation_count=1,
                last_contact=datetime.now() - timedelta(days=12),
                next_followup=datetime.now() + timedelta(days=7),
            ),
            # Success Stories (Closed Deals)
            DemoLead(
                name="Lisa Martinez",
                phone="(555) 678-9012",
                email="lmartinez@email.com",
                property_address="6341 Cedar Ridge",
                city="Austin",
                state="TX",
                zip_code="78749",
                seller_temperature=95,
                qualification_stage="closed",
                timeline="completed",
                motivation="relocation_completed",
                property_value=425000,
                asking_price=418000,
                demo_scenario="recent_success_story",
                personality_type="action_oriented",
                objection_profile="minimal_objections",
                success_probability=1.0,
                conversation_count=8,
                last_contact=datetime.now() - timedelta(days=3),
                next_followup=None,
            ),
        ]

        # Add additional diverse leads to reach target count
        additional_leads = await self._generate_additional_demo_leads(self.demo_leads_count - len(demo_leads))
        demo_leads.extend(additional_leads)

        # Store leads in demo database/cache
        for lead in demo_leads:
            await self._store_demo_lead(lead)

        logger.info(f"✅ Created {len(demo_leads)} demo lead profiles")
        return demo_leads

    async def _seed_demo_properties(self) -> List[DemoProperty]:
        """Create realistic property listings for demonstration."""
        logger.info("🏠 Creating demo property listings...")

        demo_properties = [
            DemoProperty(
                address="1247 Oak Avenue",
                city="Austin",
                state="TX",
                zip_code="78701",
                property_type="Single Family Home",
                bedrooms=4,
                bathrooms=2.5,
                square_feet=2150,
                lot_size=0.25,
                year_built=1998,
                estimated_value=485000,
                asking_price=475000,
                days_on_market=0,  # New listing
                price_per_sqft=221,
                demo_scenario="motivated_seller_success",
                market_trend="stable",
                selling_points=[
                    "Recently updated kitchen",
                    "Great school district",
                    "Walking distance to park",
                    "Low maintenance yard",
                ],
                potential_objections=["Older construction", "Small lot size"],
            ),
            DemoProperty(
                address="2156 Pine Street",
                city="Cedar Park",
                state="TX",
                zip_code="78613",
                property_type="Single Family Home",
                bedrooms=3,
                bathrooms=2.0,
                square_feet=1850,
                lot_size=0.33,
                year_built=2005,
                estimated_value=340000,
                asking_price=335000,
                days_on_market=15,
                price_per_sqft=181,
                demo_scenario="downsizing_success",
                market_trend="appreciating",
                selling_points=["Modern construction", "Open floor plan", "Energy efficient", "Quiet neighborhood"],
                potential_objections=["Smaller than typical for area", "No garage"],
            ),
            # Add more diverse properties
            DemoProperty(
                address="7825 Waterfront Drive",
                city="Lake Travis",
                state="TX",
                zip_code="78732",
                property_type="Luxury Home",
                bedrooms=5,
                bathrooms=4.5,
                square_feet=4200,
                lot_size=1.2,
                year_built=2015,
                estimated_value=1250000,
                asking_price=1295000,
                days_on_market=45,
                price_per_sqft=308,
                demo_scenario="luxury_market_positioning",
                market_trend="competitive",
                selling_points=[
                    "Lake Travis waterfront",
                    "Custom chef's kitchen",
                    "Private boat dock",
                    "Smart home technology",
                ],
                potential_objections=["High price point", "Limited buyer pool", "Market softening"],
            ),
        ]

        # Generate additional properties
        additional_properties = await self._generate_additional_demo_properties(
            self.demo_properties_count - len(demo_properties)
        )
        demo_properties.extend(additional_properties)

        # Store properties in demo database
        for property_obj in demo_properties:
            await self._store_demo_property(property_obj)

        logger.info(f"✅ Created {len(demo_properties)} demo property listings")
        return demo_properties

    async def _seed_demo_conversations(self, leads: List[DemoLead]) -> List[DemoConversation]:
        """Create realistic bot conversations showcasing Jorge's methodology."""
        logger.info("💬 Creating demo bot conversations...")

        conversations = []

        # Create conversations for each lead
        for lead in leads[:10]:  # Focus on top leads for quality demonstrations
            if lead.conversation_count > 0:
                lead_conversations = await self._create_lead_conversation_history(lead)
                conversations.extend(lead_conversations)

        logger.info(f"✅ Created {len(conversations)} demo conversations")
        return conversations

    async def _create_lead_conversation_history(self, lead: DemoLead) -> List[DemoConversation]:
        """Create conversation history for a specific lead."""
        conversations = []

        # Initial qualification conversation (Jorge Seller Bot)
        if lead.conversation_count >= 1:
            qualification_conv = DemoConversation(
                lead_id=lead.email,
                conversation_type="qualification",
                bot_name="jorge_seller_bot",
                messages=self._generate_qualification_messages(lead),
                duration_minutes=8,
                outcome="qualified" if lead.seller_temperature > 70 else "needs_nurturing",
                sentiment_score=0.7 if lead.seller_temperature > 60 else 0.4,
                confrontational_moments=2,
                objections_addressed=1,
                qualification_score=lead.seller_temperature,
                temperature_change=15,
                demo_scenario=lead.demo_scenario,
                learning_points=[
                    "Jorge's direct questioning style",
                    "Effective objection handling",
                    "Temperature qualification methodology",
                ],
            )
            conversations.append(qualification_conv)

        # Follow-up conversations (Lead Bot)
        if lead.conversation_count >= 2:
            followup_conv = DemoConversation(
                lead_id=lead.email,
                conversation_type="follow_up",
                bot_name="lead_bot",
                messages=self._generate_followup_messages(lead),
                duration_minutes=5,
                outcome="appointment_scheduled" if lead.seller_temperature > 75 else "continued_nurturing",
                sentiment_score=0.8,
                confrontational_moments=0,
                objections_addressed=1,
                qualification_score=lead.seller_temperature,
                temperature_change=5,
                demo_scenario=lead.demo_scenario,
                learning_points=[
                    "3-7-30 day nurture sequence",
                    "Value-based follow-up",
                    "Appointment setting strategy",
                ],
            )
            conversations.append(followup_conv)

        return conversations

    def _generate_qualification_messages(self, lead: DemoLead) -> List[Dict[str, Any]]:
        """Generate realistic qualification conversation messages."""
        return [
            {
                "timestamp": "2024-01-15T14:30:00Z",
                "sender": "jorge_seller_bot",
                "message": f"Hi {lead.name}, Jorge here. I see you're interested in selling at {lead.property_address}. Let me ask you straight up - are you actually ready to sell, or just curious about the market?",
                "sentiment": "direct",
                "intent": "qualification",
            },
            {
                "timestamp": "2024-01-15T14:31:15Z",
                "sender": "lead",
                "message": "Well, I'm thinking about it. My job situation might change soon.",
                "sentiment": "uncertain",
                "intent": "exploration",
            },
            {
                "timestamp": "2024-01-15T14:31:45Z",
                "sender": "jorge_seller_bot",
                "message": "Thinking about it won't sell your house. When do you need to make a decision - 30 days, 60 days, or are we talking 6 months from now?",
                "sentiment": "confrontational",
                "intent": "timeline_qualification",
            },
            {
                "timestamp": "2024-01-15T14:32:30Z",
                "sender": "lead",
                "message": f"Probably within the next {lead.timeline.replace('_', ' ')}. It depends on the job offer.",
                "sentiment": "responsive",
                "intent": "timeline_provided",
            },
            {
                "timestamp": "2024-01-15T14:33:00Z",
                "sender": "jorge_seller_bot",
                "message": f"Good. Now, what do you think your house is worth? And don't tell me what Zillow says - that's garbage data.",
                "sentiment": "direct",
                "intent": "price_qualification",
            },
        ]

    def _generate_followup_messages(self, lead: DemoLead) -> List[Dict[str, Any]]:
        """Generate realistic follow-up conversation messages."""
        return [
            {
                "timestamp": "2024-01-18T10:15:00Z",
                "sender": "lead_bot",
                "message": f"Hi {lead.name}! Following up on our conversation about selling {lead.property_address}. I've prepared a market analysis showing properties like yours are selling within 18 days on average. Would you like to see the specific comparables?",
                "sentiment": "professional",
                "intent": "value_delivery",
            },
            {
                "timestamp": "2024-01-18T10:45:22Z",
                "sender": "lead",
                "message": "Yes, I'd like to see that. What price range are similar properties selling for?",
                "sentiment": "interested",
                "intent": "price_inquiry",
            },
            {
                "timestamp": "2024-01-18T10:46:15Z",
                "sender": "lead_bot",
                "message": f"Based on recent sales, properties in your area are selling between ${lead.property_value - 20000:,} and ${lead.property_value + 15000:,}. Your property has some unique advantages that could position it at the higher end. Should we schedule 15 minutes to review the full analysis?",
                "sentiment": "consultative",
                "intent": "appointment_setting",
            },
        ]

    # =========================================================================
    # ADDITIONAL DEMO DATA GENERATORS
    # =========================================================================

    async def _generate_additional_demo_leads(self, count: int) -> List[DemoLead]:
        """Generate additional diverse demo leads."""
        additional_leads = []

        # Lead templates for variety
        lead_templates = [
            {
                "scenario": "investor_portfolio",
                "personality": "numbers_focused",
                "motivation": "portfolio_optimization",
                "temp_range": (45, 70),
            },
            {
                "scenario": "family_expansion",
                "personality": "family_focused",
                "motivation": "growing_family",
                "temp_range": (60, 85),
            },
            {
                "scenario": "retirement_planning",
                "personality": "security_minded",
                "motivation": "retirement_preparation",
                "temp_range": (50, 75),
            },
        ]

        for i in range(count):
            template = random.choice(lead_templates)

            lead = DemoLead(
                name=self._generate_random_name(),
                phone=self._generate_random_phone(),
                email=self._generate_random_email(),
                property_address=self._generate_random_address(),
                city=random.choice(["Austin", "Cedar Park", "Round Rock", "Pflugerville"]),
                state="TX",
                zip_code=random.choice(["78701", "78613", "78664", "78660"]),
                seller_temperature=random.randint(*template["temp_range"]),
                qualification_stage=random.choice(["initial_contact", "in_progress", "qualified"]),
                timeline=random.choice(["30_days", "60_days", "90_days", "exploring"]),
                motivation=template["motivation"],
                property_value=random.randint(250000, 800000),
                asking_price=0,  # Will be calculated
                demo_scenario=template["scenario"],
                personality_type=template["personality"],
                objection_profile=random.choice(["price_conscious", "timing_focused", "agent_comparison"]),
                success_probability=random.uniform(0.2, 0.9),
                conversation_count=random.randint(1, 5),
                last_contact=datetime.now() - timedelta(days=random.randint(1, 14)),
                next_followup=datetime.now() + timedelta(days=random.randint(1, 7)),
            )

            lead.asking_price = int(lead.property_value * random.uniform(0.95, 1.05))
            additional_leads.append(lead)

        return additional_leads

    async def _generate_additional_demo_properties(self, count: int) -> List[DemoProperty]:
        """Generate additional demo properties for variety."""
        properties = []

        property_types = ["Single Family Home", "Townhouse", "Condo", "Luxury Home"]

        for i in range(count):
            prop_type = random.choice(property_types)
            sqft = random.randint(1200, 3500)
            value = sqft * random.randint(180, 350)

            prop = DemoProperty(
                address=self._generate_random_address(),
                city=random.choice(["Austin", "Cedar Park", "Round Rock"]),
                state="TX",
                zip_code=random.choice(["78701", "78613", "78664"]),
                property_type=prop_type,
                bedrooms=random.randint(2, 5),
                bathrooms=random.choice([1.0, 1.5, 2.0, 2.5, 3.0, 3.5]),
                square_feet=sqft,
                lot_size=random.uniform(0.15, 1.5),
                year_built=random.randint(1985, 2020),
                estimated_value=value,
                asking_price=int(value * random.uniform(0.95, 1.08)),
                days_on_market=random.randint(0, 90),
                price_per_sqft=int(value / sqft),
                demo_scenario="market_variety",
                market_trend=random.choice(["appreciating", "stable", "competitive"]),
                selling_points=self._generate_selling_points(prop_type),
                potential_objections=self._generate_potential_objections(),
            )

            properties.append(prop)

        return properties

    # =========================================================================
    # DEMO DATA STORAGE AND CACHING
    # =========================================================================

    async def _store_demo_lead(self, lead: DemoLead):
        """Store demo lead in cache for presentation access."""
        cache_key = f"demo_lead:{lead.email}"
        await self.cache.set(cache_key, asdict(lead), ttl=86400)  # 24 hours

    async def _store_demo_property(self, property_obj: DemoProperty):
        """Store demo property in cache for presentation access."""
        cache_key = f"demo_property:{property_obj.address.replace(' ', '_').lower()}"
        await self.cache.set(cache_key, asdict(property_obj), ttl=86400)

    async def _cache_demo_data_for_presentations(self, seeding_summary: Dict[str, Any]):
        """Cache complete demo dataset for quick presentation access."""
        await self.cache.set("demo_environment_summary", seeding_summary, ttl=86400)

        # Create quick access indexes
        scenario_index = {}
        for scenario in seeding_summary.get("demo_scenarios", []):
            scenario_index[scenario["scenario_name"]] = scenario

        await self.cache.set("demo_scenario_index", scenario_index, ttl=86400)

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _generate_random_name(self) -> str:
        """Generate random but realistic names for demo leads."""
        first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"

    def _generate_random_phone(self) -> str:
        """Generate realistic phone numbers for demo."""
        return f"(555) {random.randint(100, 999)}-{random.randint(1000, 9999)}"

    def _generate_random_email(self) -> str:
        """Generate realistic email addresses for demo."""
        name = self._generate_random_name().lower().replace(" ", ".")
        domains = ["gmail.com", "yahoo.com", "email.com", "outlook.com"]
        return f"{name}@{random.choice(domains)}"

    def _generate_random_address(self) -> str:
        """Generate realistic addresses for demo."""
        street_numbers = range(1000, 9999)
        street_names = ["Oak", "Pine", "Maple", "Cedar", "Elm", "Birch", "Willow"]
        street_types = ["Street", "Avenue", "Drive", "Lane", "Court", "Way"]
        return f"{random.choice(street_numbers)} {random.choice(street_names)} {random.choice(street_types)}"

    def _generate_selling_points(self, property_type: str) -> List[str]:
        """Generate realistic selling points for properties."""
        all_points = [
            "Updated kitchen",
            "Great school district",
            "Low maintenance",
            "Energy efficient",
            "Open floor plan",
            "Large lot",
            "Modern fixtures",
            "Quiet neighborhood",
            "Near shopping",
            "Updated bathrooms",
            "Hardwood floors",
            "Two-car garage",
        ]
        return random.sample(all_points, random.randint(3, 5))

    def _generate_potential_objections(self) -> List[str]:
        """Generate realistic objections for properties."""
        objections = [
            "Older construction",
            "Small lot",
            "Busy street",
            "Needs updates",
            "High HOA fees",
            "No garage",
            "Limited storage",
            "Steep stairs",
        ]
        return random.sample(objections, random.randint(1, 3))

    # =========================================================================
    # PRESENTATION SCENARIOS
    # =========================================================================

    async def _seed_demo_appointments(self, leads: List[DemoLead]) -> List[Dict[str, Any]]:
        """Create demo appointments for calendar integration."""
        appointments = []

        for lead in leads[:8]:  # Create appointments for top leads
            if lead.seller_temperature > 60:
                appointment = {
                    "lead_id": lead.email,
                    "lead_name": lead.name,
                    "appointment_type": "listing_consultation",
                    "scheduled_datetime": (datetime.now() + timedelta(days=random.randint(1, 14))).isoformat(),
                    "duration_minutes": 60,
                    "location": lead.property_address,
                    "status": "scheduled",
                    "demo_scenario": lead.demo_scenario,
                }
                appointments.append(appointment)

        return appointments

    async def _seed_demo_metrics(self, leads: List[DemoLead], conversations: List[DemoConversation]) -> Dict[str, Any]:
        """Generate demo performance metrics for presentation."""
        return {
            "total_pipeline_value": sum(lead.property_value for lead in leads if lead.seller_temperature > 50),
            "projected_monthly_commission": sum(
                lead.property_value * 0.06 for lead in leads if lead.seller_temperature > 70
            )
            / 3,
            "avg_response_time_hours": 1.8,
            "lead_to_appointment_rate": 0.34,
            "appointment_to_listing_rate": 0.67,
            "avg_days_to_close": 21,
            "client_satisfaction_score": 4.8,
            "bot_automation_savings_hours": 23.5,
        }

    async def _create_presentation_scenarios(
        self, leads: List[DemoLead], conversations: List[DemoConversation]
    ) -> List[Dict[str, Any]]:
        """Create guided presentation scenarios for client demos."""
        return [
            {
                "scenario_name": "hot_lead_conversion",
                "title": "High-Temperature Lead Success",
                "description": "Demonstrate Jorge's qualification methodology with a motivated seller",
                "lead_examples": [lead.email for lead in leads if lead.seller_temperature > 85][:2],
                "key_points": [
                    "Direct qualification approach",
                    "Rapid temperature assessment",
                    "Efficient conversion to appointment",
                ],
                "estimated_duration_minutes": 8,
                "roi_highlight": "22-day average sale cycle",
            },
            {
                "scenario_name": "objection_handling_mastery",
                "title": "Professional Objection Management",
                "description": "Show how Jorge's bots handle common seller objections",
                "conversation_examples": [conv.lead_id for conv in conversations if conv.objections_addressed > 0][:3],
                "key_points": [
                    "Confrontational but respectful approach",
                    "Data-driven responses",
                    "Objection to opportunity conversion",
                ],
                "estimated_duration_minutes": 12,
                "roi_highlight": "67% objection-to-listing conversion rate",
            },
            {
                "scenario_name": "pipeline_intelligence",
                "title": "AI-Powered Pipeline Management",
                "description": "Showcase comprehensive business intelligence and ROI tracking",
                "metrics_focus": [
                    "Real-time pipeline valuation",
                    "Temperature-based prioritization",
                    "Commission projection accuracy",
                ],
                "key_points": [
                    "$2.4M active pipeline management",
                    "Automated follow-up sequences",
                    "Predictive closing analytics",
                ],
                "estimated_duration_minutes": 10,
                "roi_highlight": "40% increase in pipeline velocity",
            },
        ]


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_demo_seeder_instance = None


async def get_client_demo_seeder() -> ClientDemoDataSeeder:
    """Get singleton demo seeder instance."""
    global _demo_seeder_instance
    if _demo_seeder_instance is None:
        _demo_seeder_instance = ClientDemoDataSeeder()
    return _demo_seeder_instance


# =============================================================================
# DEMO SEEDING CLI
# =============================================================================

if __name__ == "__main__":

    async def main():
        print("🎭 Starting Jorge Platform Demo Data Seeding...")

        seeder = await get_client_demo_seeder()
        summary = await seeder.seed_complete_demo_environment()

        print(f"\n✅ Demo Environment Seeded Successfully!")
        print(f"📊 Summary: {json.dumps(summary['data_summary'], indent=2)}")
        print(f"🎯 Scenarios: {len(summary['demo_scenarios'])} presentation scenarios created")
        print(f"\n🚀 Ready for client demonstrations!")

    asyncio.run(main())
