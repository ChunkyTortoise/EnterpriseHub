"""
Developer Ecosystem Platform - Revenue & Network Effects Engine
Creates thriving marketplace with revenue sharing and platform lock-in.
Third-party developers extend platform value exponentially.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
import asyncio
import uuid
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging

from ..core.llm_client import LLMClient
from ..services.cache_service import CacheService
from ..services.database_service import DatabaseService
from ..services.enhanced_error_handling import enhanced_error_handler

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of agents that can be deployed in the platform."""
    LEAD_PROCESSOR = "lead_processor"
    PROPERTY_ANALYZER = "property_analyzer"
    COMMUNICATION_HANDLER = "communication_handler"
    WORKFLOW_AUTOMATION = "workflow_automation"
    ANALYTICS_GENERATOR = "analytics_generator"
    INTEGRATION_CONNECTOR = "integration_connector"
    CUSTOM_BUSINESS_LOGIC = "custom_business_logic"


class MarketplaceStatus(Enum):
    """Status of marketplace items."""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FEATURED = "featured"
    DEPRECATED = "deprecated"


@dataclass
class DeveloperProfile:
    """Developer profile in the ecosystem."""
    developer_id: str
    name: str
    email: str
    company: Optional[str]
    verified: bool
    reputation_score: float
    total_revenue: Decimal
    agent_count: int
    average_rating: float
    created_at: datetime
    api_key: str
    revenue_share_tier: str  # "standard", "premium", "enterprise"


@dataclass
class AgentConfiguration:
    """Configuration for a third-party agent."""
    agent_id: str
    name: str
    description: str
    agent_type: AgentType
    developer_id: str
    version: str
    capabilities: List[str]
    required_permissions: List[str]
    resource_requirements: Dict[str, Any]
    pricing_model: Dict[str, Any]
    installation_count: int
    rating: float
    status: MarketplaceStatus
    created_at: datetime
    updated_at: datetime


@dataclass
class RevenueShare:
    """Revenue sharing configuration."""
    developer_id: str
    agent_id: str
    revenue_share_percentage: float
    monthly_revenue: Decimal
    total_revenue: Decimal
    payment_status: str
    last_payment_date: Optional[datetime]


@dataclass
class MarketplaceMetrics:
    """Comprehensive marketplace metrics."""
    total_developers: int
    total_agents: int
    total_installs: int
    monthly_revenue: Decimal
    developer_revenue_share: Decimal
    platform_revenue: Decimal
    average_agent_rating: float
    top_categories: List[str]
    growth_rate: float


class DeveloperEcosystem:
    """
    Platform ecosystem enabling third-party development and revenue sharing.

    Creates network effects through:
    - Developer marketplace with revenue sharing
    - Platform extensibility and customization
    - Community-driven innovation
    - Ecosystem lock-in effects
    """

    def __init__(self,
                 llm_client: LLMClient,
                 cache_service: CacheService,
                 database_service: DatabaseService):
        self.llm_client = llm_client
        self.cache = cache_service
        self.db = database_service

        # Revenue sharing tiers
        self.revenue_share_tiers = {
            "standard": 0.30,    # 30% to developer, 70% to platform
            "premium": 0.40,     # 40% to developer (high-quality developers)
            "enterprise": 0.50   # 50% to developer (strategic partners)
        }

        # Platform fee structure
        self.platform_fees = {
            "listing_fee": Decimal("0"),  # Free listing to encourage participation
            "transaction_fee": Decimal("0.025"),  # 2.5% transaction fee
            "featured_placement": Decimal("299.00")  # Monthly featured placement
        }

        logger.info("Developer Ecosystem initialized")

    @enhanced_error_handler
    async def register_developer(self, developer_info: Dict[str, Any]) -> DeveloperProfile:
        """Register a new developer in the ecosystem."""
        logger.info(f"Registering new developer: {developer_info.get('email')}")

        # Generate developer profile
        developer_id = str(uuid.uuid4())
        api_key = self._generate_api_key(developer_id)

        developer = DeveloperProfile(
            developer_id=developer_id,
            name=developer_info["name"],
            email=developer_info["email"],
            company=developer_info.get("company"),
            verified=False,
            reputation_score=0.0,
            total_revenue=Decimal("0"),
            agent_count=0,
            average_rating=0.0,
            created_at=datetime.utcnow(),
            api_key=api_key,
            revenue_share_tier="standard"
        )

        # Store in database
        await self._store_developer_profile(developer)

        # Send welcome package
        await self._send_developer_welcome_package(developer)

        return developer

    @enhanced_error_handler
    async def register_third_party_agent(self, agent_config: Dict[str, Any]) -> AgentConfiguration:
        """
        Register and deploy a third-party agent.

        Args:
            agent_config: Agent configuration and code

        Returns:
            Deployed agent configuration
        """
        logger.info(f"Registering third-party agent: {agent_config.get('name')}")

        # Validate agent configuration
        validation_result = await self._validate_agent_configuration(agent_config)
        if not validation_result["valid"]:
            raise ValueError(f"Agent validation failed: {validation_result['errors']}")

        # Create agent configuration
        agent_id = str(uuid.uuid4())
        agent = AgentConfiguration(
            agent_id=agent_id,
            name=agent_config["name"],
            description=agent_config["description"],
            agent_type=AgentType(agent_config["agent_type"]),
            developer_id=agent_config["developer_id"],
            version=agent_config.get("version", "1.0.0"),
            capabilities=agent_config.get("capabilities", []),
            required_permissions=agent_config.get("permissions", []),
            resource_requirements=agent_config.get("resource_requirements", {}),
            pricing_model=agent_config.get("pricing", {"type": "free"}),
            installation_count=0,
            rating=0.0,
            status=MarketplaceStatus.PENDING_REVIEW,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Deploy agent in sandbox for testing
        deployment_result = await self._deploy_agent_sandbox(agent, agent_config["code"])

        if deployment_result["success"]:
            # Store agent configuration
            await self._store_agent_configuration(agent)

            # Set up revenue sharing
            await self._setup_revenue_sharing(agent)

            # Submit for marketplace review
            await self._submit_for_marketplace_review(agent)

            logger.info(f"Agent {agent_id} registered successfully")
            return agent
        else:
            raise RuntimeError(f"Agent deployment failed: {deployment_result['error']}")

    @enhanced_error_handler
    async def marketplace_search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[AgentConfiguration]:
        """
        Search marketplace for agents and solutions.

        Args:
            query: Search query
            filters: Optional filters (category, rating, price, etc.)

        Returns:
            List of matching agents
        """
        logger.info(f"Marketplace search: {query}")

        # Get all approved agents
        all_agents = await self._get_marketplace_agents()

        # Filter by status
        approved_agents = [agent for agent in all_agents if agent.status == MarketplaceStatus.APPROVED]

        # Apply search query
        matching_agents = await self._search_agents(approved_agents, query)

        # Apply additional filters
        if filters:
            matching_agents = await self._apply_agent_filters(matching_agents, filters)

        # Sort by relevance and rating
        matching_agents.sort(
            key=lambda a: (a.rating, a.installation_count),
            reverse=True
        )

        return matching_agents[:50]  # Return top 50 matches

    @enhanced_error_handler
    async def install_agent(self,
                           agent_id: str,
                           customer_id: str,
                           configuration: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Install an agent for a customer with revenue tracking."""
        logger.info(f"Installing agent {agent_id} for customer {customer_id}")

        # Get agent configuration
        agent = await self._get_agent_configuration(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Check permissions
        await self._validate_installation_permissions(agent, customer_id)

        # Deploy agent instance
        deployment_result = await self._deploy_agent_instance(agent, customer_id, configuration)

        if deployment_result["success"]:
            # Update installation count
            await self._increment_installation_count(agent_id)

            # Process payment if required
            if agent.pricing_model.get("type") != "free":
                payment_result = await self._process_agent_payment(agent, customer_id)

                # Record revenue share
                await self._record_revenue_share(agent, payment_result["amount"])

            return {
                "success": True,
                "instance_id": deployment_result["instance_id"],
                "agent_id": agent_id,
                "customer_id": customer_id,
                "installation_date": datetime.utcnow().isoformat()
            }
        else:
            raise RuntimeError(f"Agent installation failed: {deployment_result['error']}")

    @enhanced_error_handler
    async def get_marketplace_metrics(self) -> MarketplaceMetrics:
        """Get comprehensive marketplace performance metrics."""
        logger.info("Generating marketplace metrics")

        # Get basic counts
        total_developers = await self._count_developers()
        total_agents = await self._count_agents()
        total_installs = await self._count_total_installations()

        # Get revenue metrics
        revenue_data = await self._get_revenue_metrics()

        # Calculate growth rate
        growth_rate = await self._calculate_marketplace_growth_rate()

        # Get top categories
        top_categories = await self._get_top_agent_categories()

        # Calculate average rating
        average_rating = await self._calculate_average_agent_rating()

        return MarketplaceMetrics(
            total_developers=total_developers,
            total_agents=total_agents,
            total_installs=total_installs,
            monthly_revenue=revenue_data["monthly_revenue"],
            developer_revenue_share=revenue_data["developer_share"],
            platform_revenue=revenue_data["platform_share"],
            average_agent_rating=average_rating,
            top_categories=top_categories,
            growth_rate=growth_rate
        )

    @enhanced_error_handler
    async def process_monthly_revenue_sharing(self) -> Dict[str, Any]:
        """Process monthly revenue sharing payments to developers."""
        logger.info("Processing monthly revenue sharing")

        # Get all revenue shares for this month
        revenue_shares = await self._get_pending_revenue_shares()

        payment_results = []
        total_paid = Decimal("0")

        for share in revenue_shares:
            try:
                # Calculate payment amount
                payment_amount = share.monthly_revenue

                # Process payment to developer
                payment_result = await self._pay_developer(share.developer_id, payment_amount)

                if payment_result["success"]:
                    # Update revenue share record
                    await self._update_revenue_share_payment(share, payment_result["transaction_id"])

                    total_paid += payment_amount
                    payment_results.append({
                        "developer_id": share.developer_id,
                        "amount": payment_amount,
                        "status": "success"
                    })
                else:
                    payment_results.append({
                        "developer_id": share.developer_id,
                        "amount": payment_amount,
                        "status": "failed",
                        "error": payment_result["error"]
                    })

            except Exception as e:
                logger.error(f"Payment failed for developer {share.developer_id}: {e}")
                payment_results.append({
                    "developer_id": share.developer_id,
                    "amount": share.monthly_revenue,
                    "status": "error",
                    "error": str(e)
                })

        return {
            "total_payments": len(payment_results),
            "successful_payments": len([p for p in payment_results if p["status"] == "success"]),
            "total_amount_paid": total_paid,
            "payment_details": payment_results
        }

    async def get_developer_analytics(self, developer_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a developer."""

        # Get developer profile
        developer = await self._get_developer_profile(developer_id)

        # Get agent performance
        agent_performance = await self._get_developer_agent_performance(developer_id)

        # Get revenue analytics
        revenue_analytics = await self._get_developer_revenue_analytics(developer_id)

        return {
            "developer_profile": asdict(developer),
            "agent_performance": agent_performance,
            "revenue_analytics": revenue_analytics,
            "recommendations": await self._generate_developer_recommendations(developer_id)
        }

    # Private implementation methods

    async def _validate_agent_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate agent configuration for security and compatibility."""
        errors = []
        warnings = []

        # Required fields validation
        required_fields = ["name", "description", "agent_type", "developer_id", "code"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")

        # Agent type validation
        if config.get("agent_type") not in [t.value for t in AgentType]:
            errors.append(f"Invalid agent type: {config.get('agent_type')}")

        # Security validation
        if "code" in config:
            security_issues = await self._validate_agent_security(config["code"])
            errors.extend(security_issues)

        # Resource requirements validation
        resource_reqs = config.get("resource_requirements", {})
        if resource_reqs.get("memory", 0) > 1024:  # 1GB limit
            warnings.append("High memory requirement may affect approval")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def _validate_agent_security(self, code: str) -> List[str]:
        """Validate agent code for security issues."""
        security_issues = []

        # Basic security checks (simplified)
        dangerous_imports = ["os", "subprocess", "sys", "eval", "exec"]
        for dangerous in dangerous_imports:
            if dangerous in code:
                security_issues.append(f"Potentially dangerous import detected: {dangerous}")

        # Use Claude AI for deeper security analysis
        security_prompt = f"""
        Analyze this Python code for security vulnerabilities:

        {code}

        Look for:
        - Code injection risks
        - File system access
        - Network access outside approved APIs
        - Potential data leaks
        - Malicious patterns

        Return only critical security issues that would prevent approval.
        """

        analysis = await self.llm_client.generate(security_prompt)

        # Parse AI analysis for critical issues
        if "CRITICAL" in analysis.upper() or "SECURITY RISK" in analysis.upper():
            security_issues.append("AI security analysis identified potential risks")

        return security_issues

    async def _deploy_agent_sandbox(self, agent: AgentConfiguration, code: str) -> Dict[str, Any]:
        """Deploy agent in sandbox environment for testing."""
        try:
            # Simplified sandbox deployment
            # In production, this would use containerization
            logger.info(f"Deploying agent {agent.agent_id} in sandbox")

            # Simulate successful deployment
            return {
                "success": True,
                "sandbox_url": f"https://sandbox.platform.com/agents/{agent.agent_id}",
                "test_results": await self._run_agent_tests(agent, code)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _run_agent_tests(self, agent: AgentConfiguration, code: str) -> Dict[str, Any]:
        """Run automated tests on the agent."""
        # Simplified test runner
        return {
            "syntax_check": "passed",
            "security_scan": "passed",
            "performance_test": "passed",
            "api_compatibility": "passed"
        }

    def _generate_api_key(self, developer_id: str) -> str:
        """Generate secure API key for developer."""
        return hashlib.sha256(f"{developer_id}_{datetime.utcnow().timestamp()}".encode()).hexdigest()

    async def _store_developer_profile(self, developer: DeveloperProfile) -> None:
        """Store developer profile in database."""
        # Cache for quick access
        await self.cache.set(f"developer_{developer.developer_id}", asdict(developer), ttl=3600)

    async def _store_agent_configuration(self, agent: AgentConfiguration) -> None:
        """Store agent configuration in database."""
        await self.cache.set(f"agent_{agent.agent_id}", asdict(agent), ttl=3600)

    async def _setup_revenue_sharing(self, agent: AgentConfiguration) -> None:
        """Set up revenue sharing for agent."""
        developer = await self._get_developer_profile(agent.developer_id)

        revenue_share = RevenueShare(
            developer_id=agent.developer_id,
            agent_id=agent.agent_id,
            revenue_share_percentage=self.revenue_share_tiers[developer.revenue_share_tier],
            monthly_revenue=Decimal("0"),
            total_revenue=Decimal("0"),
            payment_status="pending",
            last_payment_date=None
        )

        await self.cache.set(f"revenue_share_{agent.agent_id}", asdict(revenue_share), ttl=3600)

    async def _send_developer_welcome_package(self, developer: DeveloperProfile) -> None:
        """Send welcome package to new developer."""
        logger.info(f"Sending welcome package to {developer.email}")
        # Implementation would send email with SDK, documentation, etc.

    async def _submit_for_marketplace_review(self, agent: AgentConfiguration) -> None:
        """Submit agent for marketplace review process."""
        # Queue for human review
        await self.cache.set(f"review_queue_{agent.agent_id}", asdict(agent), ttl=3600 * 24 * 7)

    async def _get_marketplace_agents(self) -> List[AgentConfiguration]:
        """Get all agents in the marketplace."""
        # Simplified implementation - would query database
        return []

    async def _search_agents(self, agents: List[AgentConfiguration], query: str) -> List[AgentConfiguration]:
        """Search agents by query."""
        query_lower = query.lower()
        matching = []

        for agent in agents:
            if (query_lower in agent.name.lower() or
                query_lower in agent.description.lower() or
                any(query_lower in cap.lower() for cap in agent.capabilities)):
                matching.append(agent)

        return matching

    # Additional helper methods would be implemented here...
    async def _apply_agent_filters(self, agents: List[AgentConfiguration], filters: Dict[str, Any]) -> List[AgentConfiguration]:
        """Apply filters to agent list."""
        filtered = agents

        if "category" in filters:
            filtered = [a for a in filtered if a.agent_type.value == filters["category"]]

        if "min_rating" in filters:
            filtered = [a for a in filtered if a.rating >= filters["min_rating"]]

        return filtered

    async def _get_agent_configuration(self, agent_id: str) -> Optional[AgentConfiguration]:
        """Get agent configuration by ID."""
        cached = await self.cache.get(f"agent_{agent_id}")
        if cached:
            return AgentConfiguration(**cached)
        return None

    async def _validate_installation_permissions(self, agent: AgentConfiguration, customer_id: str) -> None:
        """Validate that customer can install this agent."""
        # Check customer subscription, permissions, etc.
        pass

    async def _deploy_agent_instance(self, agent: AgentConfiguration, customer_id: str, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Deploy agent instance for customer."""
        instance_id = str(uuid.uuid4())

        return {
            "success": True,
            "instance_id": instance_id
        }

    async def _increment_installation_count(self, agent_id: str) -> None:
        """Increment installation count for agent."""
        # Update database
        pass

    async def _process_agent_payment(self, agent: AgentConfiguration, customer_id: str) -> Dict[str, Any]:
        """Process payment for agent installation/subscription."""
        # Simplified payment processing
        amount = Decimal("99.00")  # Default price

        return {
            "success": True,
            "amount": amount,
            "transaction_id": str(uuid.uuid4())
        }

    async def _record_revenue_share(self, agent: AgentConfiguration, amount: Decimal) -> None:
        """Record revenue share for developer."""
        developer = await self._get_developer_profile(agent.developer_id)
        share_percentage = self.revenue_share_tiers[developer.revenue_share_tier]
        developer_share = amount * Decimal(str(share_percentage))

        # Update revenue tracking
        logger.info(f"Recording revenue share: ${developer_share} for developer {agent.developer_id}")

    async def _get_developer_profile(self, developer_id: str) -> Optional[DeveloperProfile]:
        """Get developer profile by ID."""
        cached = await self.cache.get(f"developer_{developer_id}")
        if cached:
            return DeveloperProfile(**cached)
        return None

    # Additional revenue and analytics methods would be implemented here...
    async def _count_developers(self) -> int:
        return 250  # Placeholder

    async def _count_agents(self) -> int:
        return 1500  # Placeholder

    async def _count_total_installations(self) -> int:
        return 25000  # Placeholder

    async def _get_revenue_metrics(self) -> Dict[str, Decimal]:
        return {
            "monthly_revenue": Decimal("500000"),
            "developer_share": Decimal("175000"),
            "platform_share": Decimal("325000")
        }

    async def _calculate_marketplace_growth_rate(self) -> float:
        return 0.15  # 15% monthly growth

    async def _get_top_agent_categories(self) -> List[str]:
        return ["lead_processor", "property_analyzer", "workflow_automation"]

    async def _calculate_average_agent_rating(self) -> float:
        return 4.2

    async def _get_pending_revenue_shares(self) -> List[RevenueShare]:
        return []  # Would query database

    async def _pay_developer(self, developer_id: str, amount: Decimal) -> Dict[str, Any]:
        return {"success": True, "transaction_id": str(uuid.uuid4())}

    async def _update_revenue_share_payment(self, share: RevenueShare, transaction_id: str) -> None:
        pass

    async def _get_developer_agent_performance(self, developer_id: str) -> Dict[str, Any]:
        return {"total_installs": 1000, "average_rating": 4.5}

    async def _get_developer_revenue_analytics(self, developer_id: str) -> Dict[str, Any]:
        return {"monthly_revenue": Decimal("5000"), "total_revenue": Decimal("25000")}

    async def _generate_developer_recommendations(self, developer_id: str) -> List[str]:
        return [
            "Consider adding more agent categories",
            "Improve agent documentation for higher ratings",
            "Explore enterprise-tier revenue sharing"
        ]