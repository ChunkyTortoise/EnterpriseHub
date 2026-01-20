"""
Corporate Relocation Service for Fortune 500 Programs

Comprehensive service for managing Fortune 500 corporate relocation programs,
multi-city employee housing coordination, and volume pricing management.
Targets $1M+ annual revenue through enterprise partnerships.

Key Features:
- Fortune 500 relocation program management
- Multi-city employee housing coordination
- Corporate client onboarding workflows
- Volume pricing and contract management
- Executive-level relocation concierge services
- Cross-market logistics coordination

Author: EnterpriseHub AI
Created: 2026-01-18
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import uuid

from ..markets.national_registry import (
    get_national_market_registry,
    CorporateHeadquarters,
    CorporatePartnerTier
)
from ..services.cache_service import get_cache_service
from ..services.claude_assistant import ClaudeAssistant
from ..ghl_utils.logger import get_logger

logger = get_logger(__name__)


class RelocationStatus(Enum):
    """Status stages for corporate relocations"""
    INITIATED = "initiated"
    NEEDS_ASSESSMENT = "needs_assessment"
    MARKET_ANALYSIS = "market_analysis"
    PROPERTY_SEARCH = "property_search"
    VIEWING_SCHEDULED = "viewing_scheduled"
    OFFER_NEGOTIATION = "offer_negotiation"
    CLOSING_PROCESS = "closing_process"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EmployeeLevel(Enum):
    """Employee levels for tiered relocation services"""
    C_SUITE = "c_suite"
    VP_DIRECTOR = "vp_director"
    SENIOR_MANAGER = "senior_manager"
    MANAGER = "manager"
    INDIVIDUAL_CONTRIBUTOR = "individual_contributor"
    NEW_GRADUATE = "new_graduate"


@dataclass
class RelocationRequest:
    """Corporate employee relocation request"""
    request_id: str
    company_name: str
    employee_name: str
    employee_email: str
    employee_level: EmployeeLevel
    source_location: Optional[str]
    target_market: str
    start_date: date
    timeline_requirement: str  # "flexible", "urgent", "specific_date"
    budget_range: Tuple[float, float]
    family_size: int
    special_requirements: List[str]
    housing_preferences: Dict[str, Any]
    relocation_package_tier: str
    status: RelocationStatus
    assigned_specialist: Optional[str]
    created_at: datetime
    updated_at: datetime
    completion_target: date
    notes: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class CorporateContract:
    """Corporate relocation contract and pricing"""
    contract_id: str
    company_name: str
    partnership_tier: CorporatePartnerTier
    annual_volume_commitment: int
    volume_discount_percentage: float
    service_level_agreement: Dict[str, Any]
    pricing_structure: Dict[str, float]
    contract_start_date: date
    contract_end_date: date
    auto_renewal: bool
    dedicated_specialist: Optional[str]
    billing_contact: Dict[str, str]
    performance_metrics: Dict[str, float]
    last_review_date: datetime


@dataclass
class MultiCityCoordination:
    """Multi-city relocation coordination"""
    coordination_id: str
    company_name: str
    project_name: str
    affected_markets: List[str]
    employee_count: int
    coordination_type: str  # "office_relocation", "expansion", "consolidation"
    timeline: Dict[str, date]
    budget_total: float
    project_manager: str
    status: str
    market_coordinators: Dict[str, str]  # market -> coordinator
    progress_tracking: Dict[str, float]  # market -> completion %
    created_at: datetime


class CorporateRelocationService:
    """
    Enterprise-grade corporate relocation service for Fortune 500 programs.

    Manages complex multi-city relocations, volume pricing, dedicated specialists,
    and executive-level concierge services targeting $1M+ annual revenue.
    """

    def __init__(self):
        """Initialize corporate relocation service"""
        self.cache = get_cache_service()
        self.claude_assistant = ClaudeAssistant()
        self.national_registry = get_national_market_registry()

        # Data storage paths
        self.data_dir = Path(__file__).parent.parent / "data" / "corporate_relocations"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.requests_file = self.data_dir / "relocation_requests.json"
        self.contracts_file = self.data_dir / "corporate_contracts.json"
        self.coordination_file = self.data_dir / "multi_city_projects.json"

        # In-memory data stores
        self.active_requests: Dict[str, RelocationRequest] = {}
        self.corporate_contracts: Dict[str, CorporateContract] = {}
        self.multi_city_projects: Dict[str, MultiCityCoordination] = {}

        # Service configuration
        self.service_tiers = self._initialize_service_tiers()
        self.pricing_structure = self._initialize_pricing_structure()

        # Load existing data
        self._load_data()

        logger.info("CorporateRelocationService initialized with enterprise-grade capabilities")

    def _initialize_service_tiers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize service tier definitions"""
        return {
            "platinum_concierge": {
                "description": "White-glove C-suite relocation concierge",
                "features": [
                    "Dedicated relocation specialist",
                    "24/7 emergency support",
                    "Private jet coordination",
                    "Luxury temporary housing",
                    "Family integration services",
                    "Cultural adaptation support",
                    "Executive home search",
                    "Closing coordination",
                    "Post-move support (90 days)"
                ],
                "response_time_hours": 1,
                "employee_levels": [EmployeeLevel.C_SUITE],
                "base_fee": 25000,
                "commission_rate": 0.025
            },
            "gold_executive": {
                "description": "Executive-level relocation management",
                "features": [
                    "Dedicated relocation coordinator",
                    "Priority scheduling",
                    "Executive housing search",
                    "School district analysis",
                    "Spouse career assistance",
                    "Moving logistics coordination",
                    "Temporary housing (30 days)",
                    "Post-move support (30 days)"
                ],
                "response_time_hours": 4,
                "employee_levels": [EmployeeLevel.VP_DIRECTOR, EmployeeLevel.SENIOR_MANAGER],
                "base_fee": 12000,
                "commission_rate": 0.02
            },
            "silver_professional": {
                "description": "Professional relocation services",
                "features": [
                    "Assigned relocation coordinator",
                    "Comprehensive housing search",
                    "Neighborhood analysis",
                    "Moving logistics support",
                    "School information",
                    "Area orientation",
                    "Post-move check-in"
                ],
                "response_time_hours": 8,
                "employee_levels": [EmployeeLevel.MANAGER],
                "base_fee": 7500,
                "commission_rate": 0.015
            },
            "bronze_standard": {
                "description": "Standard corporate relocation",
                "features": [
                    "Housing search assistance",
                    "Market information",
                    "Basic moving coordination",
                    "Local area resources",
                    "Standard response time"
                ],
                "response_time_hours": 24,
                "employee_levels": [EmployeeLevel.INDIVIDUAL_CONTRIBUTOR, EmployeeLevel.NEW_GRADUATE],
                "base_fee": 3500,
                "commission_rate": 0.01
            }
        }

    def _initialize_pricing_structure(self) -> Dict[str, float]:
        """Initialize volume pricing structure"""
        return {
            "base_relocation_fee": 5000,
            "volume_discounts": {
                "tier_1": {"min_volume": 50, "discount": 0.05},   # 5% for 50+ relocations
                "tier_2": {"min_volume": 100, "discount": 0.10},  # 10% for 100+ relocations
                "tier_3": {"min_volume": 200, "discount": 0.15},  # 15% for 200+ relocations
                "tier_4": {"min_volume": 500, "discount": 0.20}   # 20% for 500+ relocations
            },
            "rush_fees": {
                "urgent": 0.25,      # 25% surcharge for <30 days
                "expedited": 0.15    # 15% surcharge for 30-60 days
            },
            "additional_services": {
                "temporary_housing": 250,    # per day
                "spouse_career_assistance": 2500,
                "private_school_search": 1500,
                "cultural_integration": 3500,
                "tax_consulting": 1000,
                "pet_relocation": 750
            }
        }

    def _load_data(self) -> None:
        """Load existing relocation data"""
        try:
            # Load relocation requests
            if self.requests_file.exists():
                with open(self.requests_file, 'r') as f:
                    data = json.load(f)
                    for req_id, req_data in data.items():
                        # Convert date strings back to date objects
                        req_data['start_date'] = datetime.strptime(req_data['start_date'], '%Y-%m-%d').date()
                        req_data['completion_target'] = datetime.strptime(req_data['completion_target'], '%Y-%m-%d').date()
                        req_data['created_at'] = datetime.fromisoformat(req_data['created_at'])
                        req_data['updated_at'] = datetime.fromisoformat(req_data['updated_at'])
                        req_data['employee_level'] = EmployeeLevel(req_data['employee_level'])
                        req_data['status'] = RelocationStatus(req_data['status'])

                        self.active_requests[req_id] = RelocationRequest(**req_data)

            # Load corporate contracts
            if self.contracts_file.exists():
                with open(self.contracts_file, 'r') as f:
                    data = json.load(f)
                    for contract_id, contract_data in data.items():
                        contract_data['partnership_tier'] = CorporatePartnerTier(contract_data['partnership_tier'])
                        contract_data['contract_start_date'] = datetime.strptime(contract_data['contract_start_date'], '%Y-%m-%d').date()
                        contract_data['contract_end_date'] = datetime.strptime(contract_data['contract_end_date'], '%Y-%m-%d').date()
                        contract_data['last_review_date'] = datetime.fromisoformat(contract_data['last_review_date'])

                        self.corporate_contracts[contract_id] = CorporateContract(**contract_data)

            # Load multi-city coordination projects
            if self.coordination_file.exists():
                with open(self.coordination_file, 'r') as f:
                    data = json.load(f)
                    for coord_id, coord_data in data.items():
                        # Convert date strings in timeline
                        for key, date_str in coord_data['timeline'].items():
                            coord_data['timeline'][key] = datetime.strptime(date_str, '%Y-%m-%d').date()
                        coord_data['created_at'] = datetime.fromisoformat(coord_data['created_at'])

                        self.multi_city_projects[coord_id] = MultiCityCoordination(**coord_data)

            logger.info(f"Loaded {len(self.active_requests)} active requests, "
                       f"{len(self.corporate_contracts)} contracts, "
                       f"{len(self.multi_city_projects)} multi-city projects")

        except Exception as e:
            logger.error(f"Failed to load relocation data: {str(e)}")

    async def create_relocation_request(
        self,
        company_name: str,
        employee_details: Dict[str, Any],
        relocation_requirements: Dict[str, Any]
    ) -> str:
        """
        Create a new corporate relocation request

        Args:
            company_name: Name of the corporate client
            employee_details: Employee information and contact details
            relocation_requirements: Relocation specifications and preferences

        Returns:
            Unique request ID for tracking
        """
        # Generate unique request ID
        request_id = f"CR-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

        # Determine service tier based on employee level
        employee_level = EmployeeLevel(employee_details.get('level', 'individual_contributor'))
        service_tier = self._determine_service_tier(employee_level)

        # Calculate completion target based on timeline
        timeline_req = relocation_requirements.get('timeline_requirement', 'flexible')
        start_date = datetime.strptime(relocation_requirements['start_date'], '%Y-%m-%d').date()

        if timeline_req == 'urgent':
            completion_target = start_date - timedelta(days=14)
        elif timeline_req == 'expedited':
            completion_target = start_date - timedelta(days=45)
        else:
            completion_target = start_date - timedelta(days=90)

        # Create relocation request
        request = RelocationRequest(
            request_id=request_id,
            company_name=company_name,
            employee_name=employee_details['name'],
            employee_email=employee_details['email'],
            employee_level=employee_level,
            source_location=employee_details.get('current_location'),
            target_market=relocation_requirements['target_market'],
            start_date=start_date,
            timeline_requirement=timeline_req,
            budget_range=(relocation_requirements['budget_min'], relocation_requirements['budget_max']),
            family_size=employee_details.get('family_size', 1),
            special_requirements=relocation_requirements.get('special_requirements', []),
            housing_preferences=relocation_requirements.get('housing_preferences', {}),
            relocation_package_tier=service_tier,
            status=RelocationStatus.INITIATED,
            assigned_specialist=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            completion_target=completion_target,
            notes=[]
        )

        # Store request
        self.active_requests[request_id] = request

        # Assign specialist based on service tier and availability
        await self._assign_relocation_specialist(request_id)

        # Send initial welcome communication
        await self._send_welcome_communication(request_id)

        # Save data
        self._save_requests_data()

        logger.info(f"Created relocation request {request_id} for {company_name} - {employee_details['name']}")
        return request_id

    def _determine_service_tier(self, employee_level: EmployeeLevel) -> str:
        """Determine appropriate service tier based on employee level"""
        for tier_name, tier_config in self.service_tiers.items():
            if employee_level in tier_config['employee_levels']:
                return tier_name

        return "bronze_standard"  # Default fallback

    async def _assign_relocation_specialist(self, request_id: str) -> None:
        """Assign appropriate relocation specialist based on service tier"""
        request = self.active_requests.get(request_id)
        if not request:
            return

        # In a real implementation, this would connect to HR/assignment system
        # For now, we'll use mock specialist assignments
        specialist_assignments = {
            "platinum_concierge": "Sarah Johnson (Senior Executive Specialist)",
            "gold_executive": "Michael Chen (Executive Coordinator)",
            "silver_professional": "Jennifer Davis (Professional Coordinator)",
            "bronze_standard": "David Rodriguez (Standard Coordinator)"
        }

        specialist = specialist_assignments.get(request.relocation_package_tier)
        if specialist:
            request.assigned_specialist = specialist
            request.updated_at = datetime.now()

            # Add assignment note
            request.notes.append({
                "timestamp": datetime.now().isoformat(),
                "type": "specialist_assignment",
                "message": f"Assigned specialist: {specialist}",
                "author": "System"
            })

    async def _send_welcome_communication(self, request_id: str) -> None:
        """Send welcome communication to employee and corporate contact"""
        request = self.active_requests.get(request_id)
        if not request:
            return

        # Generate personalized welcome message using Claude
        context = {
            "employee_name": request.employee_name,
            "company_name": request.company_name,
            "target_market": request.target_market,
            "service_tier": request.relocation_package_tier,
            "assigned_specialist": request.assigned_specialist,
            "timeline": request.timeline_requirement
        }

        welcome_message = await self.claude_assistant.generate_welcome_message(
            "corporate_relocation",
            context
        )

        # In a real implementation, this would send actual emails
        # For now, we'll log the communication and add to notes
        request.notes.append({
            "timestamp": datetime.now().isoformat(),
            "type": "welcome_communication",
            "message": f"Welcome communication sent to {request.employee_email}",
            "content": welcome_message,
            "author": "System"
        })

        logger.info(f"Sent welcome communication for request {request_id}")

    async def get_relocation_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed status of a relocation request"""
        cache_key = f"relocation_status:{request_id}"

        # Try cache first
        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        request = self.active_requests.get(request_id)
        if not request:
            return None

        # Get corporate contract details
        contract = self._find_corporate_contract(request.company_name)

        # Calculate progress percentage
        progress = self._calculate_progress(request)

        # Get market insights for target market
        market_insights = await self.national_registry.get_corporate_relocation_program(request.company_name)

        status_details = {
            "request_id": request_id,
            "status": request.status.value,
            "progress_percentage": progress,
            "employee": {
                "name": request.employee_name,
                "email": request.employee_email,
                "level": request.employee_level.value
            },
            "relocation_details": {
                "source_location": request.source_location,
                "target_market": request.target_market,
                "start_date": request.start_date.isoformat(),
                "timeline_requirement": request.timeline_requirement,
                "completion_target": request.completion_target.isoformat()
            },
            "service_details": {
                "package_tier": request.relocation_package_tier,
                "assigned_specialist": request.assigned_specialist,
                "service_features": self.service_tiers.get(request.relocation_package_tier, {}).get('features', [])
            },
            "budget_information": {
                "budget_range": request.budget_range,
                "estimated_total_cost": self._estimate_total_cost(request),
                "volume_discount": contract.volume_discount_percentage if contract else 0
            },
            "market_insights": market_insights,
            "recent_notes": request.notes[-5:],  # Last 5 notes
            "next_steps": self._generate_next_steps(request),
            "last_updated": request.updated_at.isoformat()
        }

        # Cache for 30 minutes
        await self.cache.set(cache_key, status_details, ttl=1800)

        return status_details

    def _find_corporate_contract(self, company_name: str) -> Optional[CorporateContract]:
        """Find active corporate contract for company"""
        for contract in self.corporate_contracts.values():
            if contract.company_name.lower() == company_name.lower():
                return contract
        return None

    def _calculate_progress(self, request: RelocationRequest) -> float:
        """Calculate completion progress percentage"""
        status_progress = {
            RelocationStatus.INITIATED: 5,
            RelocationStatus.NEEDS_ASSESSMENT: 15,
            RelocationStatus.MARKET_ANALYSIS: 30,
            RelocationStatus.PROPERTY_SEARCH: 50,
            RelocationStatus.VIEWING_SCHEDULED: 65,
            RelocationStatus.OFFER_NEGOTIATION: 80,
            RelocationStatus.CLOSING_PROCESS: 95,
            RelocationStatus.COMPLETED: 100,
            RelocationStatus.CANCELLED: 0
        }

        return status_progress.get(request.status, 0)

    def _estimate_total_cost(self, request: RelocationRequest) -> float:
        """Estimate total cost for relocation"""
        tier_config = self.service_tiers.get(request.relocation_package_tier, {})
        base_fee = tier_config.get('base_fee', 5000)

        # Add rush fees if applicable
        days_until_start = (request.start_date - date.today()).days
        rush_multiplier = 1.0

        if days_until_start < 30:
            rush_multiplier = 1 + self.pricing_structure['rush_fees']['urgent']
        elif days_until_start < 60:
            rush_multiplier = 1 + self.pricing_structure['rush_fees']['expedited']

        estimated_cost = base_fee * rush_multiplier

        # Add special service costs
        for requirement in request.special_requirements:
            if requirement in self.pricing_structure['additional_services']:
                estimated_cost += self.pricing_structure['additional_services'][requirement]

        return estimated_cost

    def _generate_next_steps(self, request: RelocationRequest) -> List[str]:
        """Generate next steps based on current status"""
        next_steps_map = {
            RelocationStatus.INITIATED: [
                "Schedule initial consultation with assigned specialist",
                "Complete needs assessment questionnaire",
                "Review corporate relocation benefits package"
            ],
            RelocationStatus.NEEDS_ASSESSMENT: [
                "Finalize housing requirements and preferences",
                "Begin market analysis for target location",
                "Schedule virtual market orientation"
            ],
            RelocationStatus.MARKET_ANALYSIS: [
                "Review neighborhood recommendations",
                "Schedule property viewings",
                "Coordinate visit logistics"
            ],
            RelocationStatus.PROPERTY_SEARCH: [
                "Attend scheduled property viewings",
                "Provide feedback on viewed properties",
                "Prepare offer strategy with specialist"
            ],
            RelocationStatus.VIEWING_SCHEDULED: [
                "Complete property viewings",
                "Make offer decision",
                "Begin offer negotiation process"
            ],
            RelocationStatus.OFFER_NEGOTIATION: [
                "Finalize purchase terms",
                "Schedule home inspection",
                "Begin closing process"
            ],
            RelocationStatus.CLOSING_PROCESS: [
                "Complete final walkthrough",
                "Attend closing",
                "Begin move coordination"
            ],
            RelocationStatus.COMPLETED: [
                "Complete post-move checklist",
                "Provide feedback on services",
                "Access ongoing support resources"
            ]
        }

        return next_steps_map.get(request.status, ["Contact assigned specialist for status update"])

    async def create_multi_city_coordination(
        self,
        company_name: str,
        project_details: Dict[str, Any]
    ) -> str:
        """
        Create multi-city relocation coordination project

        Args:
            company_name: Corporate client name
            project_details: Project specifications and requirements

        Returns:
            Coordination project ID
        """
        coordination_id = f"MCP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

        # Parse timeline requirements
        timeline = {}
        for phase, date_str in project_details.get('timeline', {}).items():
            timeline[phase] = datetime.strptime(date_str, '%Y-%m-%d').date()

        coordination = MultiCityCoordination(
            coordination_id=coordination_id,
            company_name=company_name,
            project_name=project_details['project_name'],
            affected_markets=project_details['affected_markets'],
            employee_count=project_details['employee_count'],
            coordination_type=project_details['coordination_type'],
            timeline=timeline,
            budget_total=project_details['budget_total'],
            project_manager=project_details.get('project_manager', 'TBD'),
            status="initiated",
            market_coordinators={},
            progress_tracking={market: 0.0 for market in project_details['affected_markets']},
            created_at=datetime.now()
        )

        # Assign market coordinators
        await self._assign_market_coordinators(coordination_id)

        self.multi_city_projects[coordination_id] = coordination
        self._save_coordination_data()

        logger.info(f"Created multi-city coordination {coordination_id} for {company_name}")
        return coordination_id

    async def _assign_market_coordinators(self, coordination_id: str) -> None:
        """Assign coordinators for each market in multi-city project"""
        coordination = self.multi_city_projects.get(coordination_id)
        if not coordination:
            return

        # Mock coordinator assignments - in real implementation, this would
        # interface with staffing/assignment systems
        mock_coordinators = {
            "denver": "Alex Thompson",
            "phoenix": "Maria Garcia",
            "seattle": "James Liu",
            "austin": "Rachel Green",
            "dallas": "Mark Wilson",
            "houston": "Sandra Kim",
            "san_antonio": "Carlos Rodriguez"
        }

        for market in coordination.affected_markets:
            if market in mock_coordinators:
                coordination.market_coordinators[market] = mock_coordinators[market]

    async def get_corporate_dashboard(self, company_name: str) -> Dict[str, Any]:
        """Get comprehensive corporate dashboard for company"""
        cache_key = f"corporate_dashboard:{company_name}"

        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        # Get all requests for this company
        company_requests = [r for r in self.active_requests.values()
                          if r.company_name.lower() == company_name.lower()]

        # Get corporate contract
        contract = self._find_corporate_contract(company_name)

        # Get multi-city projects
        company_projects = [p for p in self.multi_city_projects.values()
                          if p.company_name.lower() == company_name.lower()]

        # Calculate metrics
        total_relocations = len(company_requests)
        completed_relocations = len([r for r in company_requests if r.status == RelocationStatus.COMPLETED])
        active_relocations = len([r for r in company_requests if r.status not in [RelocationStatus.COMPLETED, RelocationStatus.CANCELLED]])

        dashboard = {
            "company_name": company_name,
            "contract_details": {
                "partnership_tier": contract.partnership_tier.value if contract else "none",
                "volume_discount": contract.volume_discount_percentage if contract else 0,
                "annual_commitment": contract.annual_volume_commitment if contract else 0,
                "dedicated_specialist": contract.dedicated_specialist if contract else None
            },
            "relocation_metrics": {
                "total_relocations": total_relocations,
                "completed_relocations": completed_relocations,
                "active_relocations": active_relocations,
                "success_rate": (completed_relocations / total_relocations * 100) if total_relocations > 0 else 0,
                "average_timeline": self._calculate_average_timeline(company_requests)
            },
            "active_requests": [
                {
                    "request_id": r.request_id,
                    "employee_name": r.employee_name,
                    "target_market": r.target_market,
                    "status": r.status.value,
                    "progress": self._calculate_progress(r),
                    "completion_target": r.completion_target.isoformat()
                }
                for r in company_requests
                if r.status not in [RelocationStatus.COMPLETED, RelocationStatus.CANCELLED]
            ],
            "multi_city_projects": [
                {
                    "project_id": p.coordination_id,
                    "project_name": p.project_name,
                    "affected_markets": p.affected_markets,
                    "employee_count": p.employee_count,
                    "status": p.status,
                    "overall_progress": sum(p.progress_tracking.values()) / len(p.progress_tracking) if p.progress_tracking else 0
                }
                for p in company_projects
            ],
            "market_utilization": self._calculate_market_utilization(company_requests),
            "cost_summary": {
                "total_spent": self._calculate_total_spent(company_requests),
                "projected_savings": self._calculate_projected_savings(company_requests, contract),
                "cost_per_relocation": self._calculate_cost_per_relocation(company_requests)
            },
            "last_updated": datetime.now().isoformat()
        }

        # Cache for 1 hour
        await self.cache.set(cache_key, dashboard, ttl=3600)

        return dashboard

    def _calculate_average_timeline(self, requests: List[RelocationRequest]) -> float:
        """Calculate average timeline for completed relocations"""
        completed = [r for r in requests if r.status == RelocationStatus.COMPLETED]
        if not completed:
            return 0.0

        total_days = 0
        for request in completed:
            days = (request.start_date - request.created_at.date()).days
            total_days += days

        return total_days / len(completed)

    def _calculate_market_utilization(self, requests: List[RelocationRequest]) -> Dict[str, int]:
        """Calculate utilization by target market"""
        utilization = {}
        for request in requests:
            market = request.target_market
            utilization[market] = utilization.get(market, 0) + 1
        return utilization

    def _calculate_total_spent(self, requests: List[RelocationRequest]) -> float:
        """Calculate total amount spent on relocations"""
        return sum(self._estimate_total_cost(r) for r in requests
                  if r.status == RelocationStatus.COMPLETED)

    def _calculate_projected_savings(
        self,
        requests: List[RelocationRequest],
        contract: Optional[CorporateContract]
    ) -> float:
        """Calculate projected savings from volume discounts"""
        if not contract:
            return 0.0

        total_base_cost = sum(
            self.service_tiers.get(r.relocation_package_tier, {}).get('base_fee', 5000)
            for r in requests
        )

        savings = total_base_cost * contract.volume_discount_percentage
        return savings

    def _calculate_cost_per_relocation(self, requests: List[RelocationRequest]) -> float:
        """Calculate average cost per relocation"""
        if not requests:
            return 0.0

        total_cost = sum(self._estimate_total_cost(r) for r in requests)
        return total_cost / len(requests)

    def _save_requests_data(self) -> None:
        """Save relocation requests data to file"""
        serializable_data = {}
        for req_id, request in self.active_requests.items():
            data_dict = request.__dict__.copy()
            data_dict['start_date'] = request.start_date.isoformat()
            data_dict['completion_target'] = request.completion_target.isoformat()
            data_dict['created_at'] = request.created_at.isoformat()
            data_dict['updated_at'] = request.updated_at.isoformat()
            data_dict['employee_level'] = request.employee_level.value
            data_dict['status'] = request.status.value
            serializable_data[req_id] = data_dict

        with open(self.requests_file, 'w') as f:
            json.dump(serializable_data, f, indent=2)

    def _save_coordination_data(self) -> None:
        """Save multi-city coordination data to file"""
        serializable_data = {}
        for coord_id, coordination in self.multi_city_projects.items():
            data_dict = coordination.__dict__.copy()
            # Convert dates to strings
            timeline_str = {}
            for key, date_obj in coordination.timeline.items():
                timeline_str[key] = date_obj.isoformat()
            data_dict['timeline'] = timeline_str
            data_dict['created_at'] = coordination.created_at.isoformat()
            serializable_data[coord_id] = data_dict

        with open(self.coordination_file, 'w') as f:
            json.dump(serializable_data, f, indent=2)

    def health_check(self) -> Dict[str, Any]:
        """Perform service health check"""
        try:
            return {
                "status": "healthy",
                "service": "CorporateRelocationService",
                "metrics": {
                    "active_requests": len(self.active_requests),
                    "corporate_contracts": len(self.corporate_contracts),
                    "multi_city_projects": len(self.multi_city_projects),
                    "service_tiers": len(self.service_tiers)
                },
                "data_files": {
                    "requests_file": self.requests_file.exists(),
                    "contracts_file": self.contracts_file.exists(),
                    "coordination_file": self.coordination_file.exists()
                },
                "last_check": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }


# Global service instance
_corporate_relocation_service = None


def get_corporate_relocation_service() -> CorporateRelocationService:
    """Get the global corporate relocation service instance"""
    global _corporate_relocation_service
    if _corporate_relocation_service is None:
        _corporate_relocation_service = CorporateRelocationService()
    return _corporate_relocation_service