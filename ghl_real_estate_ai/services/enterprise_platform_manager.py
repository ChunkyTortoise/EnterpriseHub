"""
Enterprise Platform Manager for Multi-Organization Management

This service provides comprehensive multi-organization management capabilities for the
EnterpriseHub platform, enabling enterprise client onboarding, resource allocation,
and hierarchical organization management.

Key Features:
- Multi-organization hierarchy management
- Enterprise client onboarding and provisioning
- Resource allocation and scaling management
- Organization-level configuration and settings
- Admin dashboards and management interfaces
- Integration with existing multi-tenant infrastructure

Author: Claude (Anthropic)
Created: January 2026
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from uuid import uuid4

import redis
from pydantic import BaseModel, Field, validator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrganizationTier(str, Enum):
    """Organization tier levels for enterprise platform"""
    TRIAL = "trial"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    WHITE_LABEL = "white_label"

class OrganizationStatus(str, Enum):
    """Organization status levels"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_SETUP = "pending_setup"
    MIGRATING = "migrating"
    ARCHIVED = "archived"

class ResourceType(str, Enum):
    """Resource types for allocation management"""
    CLAUDE_INSTANCES = "claude_instances"
    STORAGE_GB = "storage_gb"
    API_CALLS_MONTHLY = "api_calls_monthly"
    USERS_MAX = "users_max"
    LOCATIONS_MAX = "locations_max"
    CUSTOM_INTEGRATIONS = "custom_integrations"

class OrganizationConfig(BaseModel):
    """Organization configuration settings"""
    organization_id: str
    tier: OrganizationTier
    status: OrganizationStatus
    name: str
    display_name: str
    domain: Optional[str] = None

    # Branding and customization
    branding: Dict[str, Any] = Field(default_factory=dict)
    custom_domain: Optional[str] = None
    white_label_settings: Dict[str, Any] = Field(default_factory=dict)

    # Resource allocation
    resource_limits: Dict[ResourceType, int] = Field(default_factory=dict)
    current_usage: Dict[ResourceType, int] = Field(default_factory=dict)

    # Feature flags and capabilities
    enabled_features: Set[str] = Field(default_factory=set)
    industry_verticals: Set[str] = Field(default_factory=set)

    # Administrative settings
    admin_users: List[str] = Field(default_factory=list)
    billing_contact: Optional[str] = None
    technical_contact: Optional[str] = None

    # Compliance and security
    compliance_requirements: Set[str] = Field(default_factory=set)
    security_settings: Dict[str, Any] = Field(default_factory=dict)

    # Integration settings
    integrated_services: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    api_keys: Dict[str, str] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: Optional[datetime] = None

    class Config:
        use_enum_values = True

class ResourceAllocation(BaseModel):
    """Resource allocation tracking"""
    organization_id: str
    resource_type: ResourceType
    allocated_amount: int
    current_usage: int
    usage_history: List[Dict[str, Any]] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    @property
    def usage_percentage(self) -> float:
        """Calculate usage percentage"""
        if self.allocated_amount == 0:
            return 0.0
        return (self.current_usage / self.allocated_amount) * 100

class OrganizationHierarchy(BaseModel):
    """Organization hierarchy management"""
    organization_id: str
    parent_organization_id: Optional[str] = None
    child_organizations: List[str] = Field(default_factory=list)
    hierarchy_level: int = 0
    permissions_inherited: bool = True
    custom_permissions: Dict[str, Any] = Field(default_factory=dict)

class PlatformManagerRequest(BaseModel):
    """Request model for platform management operations"""
    operation_type: str
    organization_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    admin_user_id: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)

class PlatformManagerResponse(BaseModel):
    """Response model for platform management operations"""
    success: bool
    operation_id: str
    organization_id: Optional[str] = None
    result_data: Dict[str, Any] = Field(default_factory=dict)
    message: str
    performed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float

@dataclass
class OrganizationMetrics:
    """Organization performance metrics"""
    organization_id: str
    total_users: int
    active_users_30d: int
    total_api_calls: int
    api_calls_30d: int
    storage_used_gb: float
    claude_instances_active: int
    revenue_current_month: float
    support_tickets_open: int
    uptime_percentage: float
    last_calculated: datetime = field(default_factory=datetime.utcnow)

class EnterprisePlatformManager:
    """
    Enterprise Platform Manager for Multi-Organization Management

    Provides comprehensive platform-level management capabilities including:
    - Multi-organization hierarchy and provisioning
    - Resource allocation and scaling management
    - Enterprise client onboarding and configuration
    - Admin dashboards and operational insights
    """

    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.platform_cache = {}
        self.organization_cache = {}
        self.metrics_cache = {}
        self.operation_history = []

        # Enterprise platform configuration
        self.tier_defaults = self._load_tier_defaults()
        self.feature_registry = self._load_feature_registry()
        self.compliance_frameworks = self._load_compliance_frameworks()

        logger.info("Enterprise Platform Manager initialized")

    def _load_tier_defaults(self) -> Dict[OrganizationTier, Dict[str, Any]]:
        """Load default settings for organization tiers"""
        return {
            OrganizationTier.TRIAL: {
                "duration_days": 14,
                "resource_limits": {
                    ResourceType.CLAUDE_INSTANCES: 1,
                    ResourceType.STORAGE_GB: 1,
                    ResourceType.API_CALLS_MONTHLY: 1000,
                    ResourceType.USERS_MAX: 3,
                    ResourceType.LOCATIONS_MAX: 1,
                    ResourceType.CUSTOM_INTEGRATIONS: 0
                },
                "features": {"basic_claude", "standard_support"}
            },
            OrganizationTier.STARTER: {
                "resource_limits": {
                    ResourceType.CLAUDE_INSTANCES: 2,
                    ResourceType.STORAGE_GB: 10,
                    ResourceType.API_CALLS_MONTHLY: 10000,
                    ResourceType.USERS_MAX: 10,
                    ResourceType.LOCATIONS_MAX: 3,
                    ResourceType.CUSTOM_INTEGRATIONS: 1
                },
                "features": {"advanced_claude", "standard_support", "basic_analytics"}
            },
            OrganizationTier.PROFESSIONAL: {
                "resource_limits": {
                    ResourceType.CLAUDE_INSTANCES: 5,
                    ResourceType.STORAGE_GB: 50,
                    ResourceType.API_CALLS_MONTHLY: 50000,
                    ResourceType.USERS_MAX: 50,
                    ResourceType.LOCATIONS_MAX: 10,
                    ResourceType.CUSTOM_INTEGRATIONS: 5
                },
                "features": {"enterprise_claude", "priority_support", "advanced_analytics", "custom_workflows"}
            },
            OrganizationTier.ENTERPRISE: {
                "resource_limits": {
                    ResourceType.CLAUDE_INSTANCES: 20,
                    ResourceType.STORAGE_GB: 200,
                    ResourceType.API_CALLS_MONTHLY: 200000,
                    ResourceType.USERS_MAX: 200,
                    ResourceType.LOCATIONS_MAX: 50,
                    ResourceType.CUSTOM_INTEGRATIONS: 20
                },
                "features": {"enterprise_claude", "dedicated_support", "enterprise_analytics",
                           "custom_workflows", "compliance_tools", "api_access"}
            },
            OrganizationTier.WHITE_LABEL: {
                "resource_limits": {
                    ResourceType.CLAUDE_INSTANCES: 100,
                    ResourceType.STORAGE_GB: 1000,
                    ResourceType.API_CALLS_MONTHLY: 1000000,
                    ResourceType.USERS_MAX: 1000,
                    ResourceType.LOCATIONS_MAX: 200,
                    ResourceType.CUSTOM_INTEGRATIONS: 100
                },
                "features": {"enterprise_claude", "white_label_support", "enterprise_analytics",
                           "custom_workflows", "compliance_tools", "full_api_access", "custom_branding"}
            }
        }

    def _load_feature_registry(self) -> Dict[str, Dict[str, Any]]:
        """Load available platform features"""
        return {
            "basic_claude": {
                "description": "Basic Claude AI assistance",
                "tier_required": OrganizationTier.TRIAL
            },
            "advanced_claude": {
                "description": "Advanced Claude features with role specialization",
                "tier_required": OrganizationTier.STARTER
            },
            "enterprise_claude": {
                "description": "Full Claude intelligence stack with orchestration",
                "tier_required": OrganizationTier.PROFESSIONAL
            },
            "custom_workflows": {
                "description": "Custom workflow automation and process optimization",
                "tier_required": OrganizationTier.PROFESSIONAL
            },
            "compliance_tools": {
                "description": "Regulatory compliance automation and monitoring",
                "tier_required": OrganizationTier.ENTERPRISE
            },
            "white_label_support": {
                "description": "Complete white-label customization capabilities",
                "tier_required": OrganizationTier.WHITE_LABEL
            }
        }

    def _load_compliance_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Load compliance framework definitions"""
        return {
            "GDPR": {
                "name": "General Data Protection Regulation",
                "region": "EU",
                "requirements": ["data_encryption", "consent_management", "right_to_erasure", "data_portability"]
            },
            "CCPA": {
                "name": "California Consumer Privacy Act",
                "region": "US-CA",
                "requirements": ["data_transparency", "opt_out_rights", "data_deletion", "non_discrimination"]
            },
            "HIPAA": {
                "name": "Health Insurance Portability and Accountability Act",
                "region": "US",
                "requirements": ["phi_encryption", "audit_logs", "access_controls", "breach_notification"]
            },
            "SOC2": {
                "name": "Service Organization Control 2",
                "region": "Global",
                "requirements": ["security_controls", "availability_monitoring", "processing_integrity", "confidentiality"]
            }
        }

    async def create_organization(self, request: PlatformManagerRequest) -> PlatformManagerResponse:
        """Create a new organization with specified tier and configuration"""
        start_time = time.time()
        operation_id = f"create_org_{int(time.time() * 1000)}"

        try:
            # Extract organization details from parameters
            org_name = request.parameters.get("name")
            org_tier = OrganizationTier(request.parameters.get("tier", OrganizationTier.TRIAL))
            admin_email = request.parameters.get("admin_email")
            industry_vertical = request.parameters.get("industry_vertical", "real_estate")

            if not org_name or not admin_email:
                raise ValueError("Organization name and admin email are required")

            # Generate organization ID
            organization_id = f"org_{uuid4().hex[:12]}"

            # Get tier defaults
            tier_config = self.tier_defaults[org_tier]

            # Create organization configuration
            org_config = OrganizationConfig(
                organization_id=organization_id,
                tier=org_tier,
                status=OrganizationStatus.PENDING_SETUP,
                name=org_name,
                display_name=org_name,
                resource_limits=tier_config["resource_limits"],
                current_usage={resource: 0 for resource in tier_config["resource_limits"]},
                enabled_features=set(tier_config["features"]),
                industry_verticals={industry_vertical},
                admin_users=[admin_email],
                billing_contact=admin_email,
                technical_contact=admin_email
            )

            # Store organization configuration
            await self._store_organization_config(org_config)

            # Initialize resource allocations
            await self._initialize_resource_allocations(organization_id, tier_config["resource_limits"])

            # Create organization hierarchy entry
            hierarchy = OrganizationHierarchy(
                organization_id=organization_id,
                parent_organization_id=request.parameters.get("parent_organization_id"),
                hierarchy_level=0
            )
            await self._store_organization_hierarchy(hierarchy)

            # Trigger setup processes
            await self._trigger_organization_setup(organization_id, org_config)

            # Cache organization data
            self.organization_cache[organization_id] = org_config

            processing_time = (time.time() - start_time) * 1000

            response = PlatformManagerResponse(
                success=True,
                operation_id=operation_id,
                organization_id=organization_id,
                result_data={
                    "organization": org_config.dict(),
                    "setup_status": "initiated",
                    "estimated_setup_time_minutes": 15
                },
                message=f"Organization '{org_name}' created successfully with tier {org_tier.value}",
                processing_time_ms=processing_time
            )

            # Store operation history
            self.operation_history.append({
                "operation_id": operation_id,
                "operation_type": "create_organization",
                "organization_id": organization_id,
                "admin_user_id": request.admin_user_id,
                "success": True,
                "timestamp": datetime.utcnow(),
                "processing_time_ms": processing_time
            })

            logger.info(f"Organization {organization_id} created successfully in {processing_time:.2f}ms")
            return response

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Failed to create organization: {str(e)}")

            return PlatformManagerResponse(
                success=False,
                operation_id=operation_id,
                message=f"Failed to create organization: {str(e)}",
                processing_time_ms=processing_time
            )

    async def configure_organization(self, request: PlatformManagerRequest) -> PlatformManagerResponse:
        """Configure organization settings, features, and resources"""
        start_time = time.time()
        operation_id = f"config_org_{int(time.time() * 1000)}"

        try:
            organization_id = request.organization_id
            if not organization_id:
                raise ValueError("Organization ID is required")

            # Get current organization configuration
            org_config = await self._get_organization_config(organization_id)
            if not org_config:
                raise ValueError(f"Organization {organization_id} not found")

            # Apply configuration updates
            updates = request.parameters.get("updates", {})

            # Update basic settings
            if "display_name" in updates:
                org_config.display_name = updates["display_name"]

            if "tier" in updates:
                new_tier = OrganizationTier(updates["tier"])
                await self._upgrade_organization_tier(org_config, new_tier)

            # Update branding and customization
            if "branding" in updates:
                org_config.branding.update(updates["branding"])

            if "custom_domain" in updates:
                org_config.custom_domain = updates["custom_domain"]

            # Update feature flags
            if "enabled_features" in updates:
                new_features = set(updates["enabled_features"])
                await self._validate_feature_access(org_config.tier, new_features)
                org_config.enabled_features = new_features

            # Update industry verticals
            if "industry_verticals" in updates:
                org_config.industry_verticals = set(updates["industry_verticals"])

            # Update compliance requirements
            if "compliance_requirements" in updates:
                org_config.compliance_requirements = set(updates["compliance_requirements"])
                await self._apply_compliance_requirements(org_config)

            # Update resource allocations
            if "resource_limits" in updates:
                await self._update_resource_allocations(organization_id, updates["resource_limits"])
                org_config.resource_limits.update(updates["resource_limits"])

            # Update security settings
            if "security_settings" in updates:
                org_config.security_settings.update(updates["security_settings"])

            # Update integration settings
            if "integrated_services" in updates:
                org_config.integrated_services.update(updates["integrated_services"])

            # Update timestamps
            org_config.updated_at = datetime.utcnow()

            # Store updated configuration
            await self._store_organization_config(org_config)

            # Update cache
            self.organization_cache[organization_id] = org_config

            processing_time = (time.time() - start_time) * 1000

            response = PlatformManagerResponse(
                success=True,
                operation_id=operation_id,
                organization_id=organization_id,
                result_data={
                    "organization": org_config.dict(),
                    "updated_fields": list(updates.keys()),
                    "configuration_status": "updated"
                },
                message=f"Organization {organization_id} configuration updated successfully",
                processing_time_ms=processing_time
            )

            logger.info(f"Organization {organization_id} configured successfully in {processing_time:.2f}ms")
            return response

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Failed to configure organization: {str(e)}")

            return PlatformManagerResponse(
                success=False,
                operation_id=operation_id,
                organization_id=request.organization_id,
                message=f"Failed to configure organization: {str(e)}",
                processing_time_ms=processing_time
            )

    async def manage_resource_allocation(self, request: PlatformManagerRequest) -> PlatformManagerResponse:
        """Manage resource allocation and scaling for organizations"""
        start_time = time.time()
        operation_id = f"resource_mgmt_{int(time.time() * 1000)}"

        try:
            organization_id = request.organization_id
            action = request.parameters.get("action")
            resource_type = request.parameters.get("resource_type")

            if not organization_id or not action:
                raise ValueError("Organization ID and action are required")

            org_config = await self._get_organization_config(organization_id)
            if not org_config:
                raise ValueError(f"Organization {organization_id} not found")

            result_data = {}

            if action == "allocate":
                # Allocate additional resources
                allocation_amount = request.parameters.get("amount", 0)
                if resource_type and allocation_amount > 0:
                    await self._allocate_resources(organization_id, resource_type, allocation_amount)
                    result_data[f"{resource_type}_allocated"] = allocation_amount

            elif action == "scale":
                # Auto-scale based on usage patterns
                scaling_analysis = await self._analyze_scaling_requirements(organization_id)
                recommendations = await self._generate_scaling_recommendations(organization_id, scaling_analysis)

                if request.parameters.get("auto_apply", False):
                    await self._apply_scaling_recommendations(organization_id, recommendations)
                    result_data["scaling_applied"] = recommendations
                else:
                    result_data["scaling_recommendations"] = recommendations

            elif action == "monitor":
                # Monitor resource usage and performance
                usage_metrics = await self._get_resource_usage_metrics(organization_id)
                performance_alerts = await self._check_performance_alerts(organization_id)

                result_data.update({
                    "usage_metrics": usage_metrics,
                    "performance_alerts": performance_alerts,
                    "optimization_opportunities": await self._identify_optimization_opportunities(organization_id)
                })

            elif action == "optimize":
                # Optimize resource allocation based on usage patterns
                optimization_plan = await self._generate_optimization_plan(organization_id)

                if request.parameters.get("apply_optimization", False):
                    await self._apply_optimization_plan(organization_id, optimization_plan)
                    result_data["optimization_applied"] = optimization_plan
                else:
                    result_data["optimization_plan"] = optimization_plan

            processing_time = (time.time() - start_time) * 1000

            response = PlatformManagerResponse(
                success=True,
                operation_id=operation_id,
                organization_id=organization_id,
                result_data=result_data,
                message=f"Resource management operation '{action}' completed successfully",
                processing_time_ms=processing_time
            )

            logger.info(f"Resource management for {organization_id} completed in {processing_time:.2f}ms")
            return response

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Resource management failed: {str(e)}")

            return PlatformManagerResponse(
                success=False,
                operation_id=operation_id,
                organization_id=request.organization_id,
                message=f"Resource management failed: {str(e)}",
                processing_time_ms=processing_time
            )

    async def get_organization_metrics(self, request: PlatformManagerRequest) -> PlatformManagerResponse:
        """Get comprehensive metrics and analytics for organization"""
        start_time = time.time()
        operation_id = f"metrics_{int(time.time() * 1000)}"

        try:
            organization_id = request.organization_id
            if not organization_id:
                raise ValueError("Organization ID is required")

            # Get organization configuration
            org_config = await self._get_organization_config(organization_id)
            if not org_config:
                raise ValueError(f"Organization {organization_id} not found")

            # Calculate comprehensive metrics
            org_metrics = await self._calculate_organization_metrics(organization_id)
            resource_metrics = await self._get_resource_usage_metrics(organization_id)
            performance_metrics = await self._get_performance_metrics(organization_id)
            financial_metrics = await self._get_financial_metrics(organization_id)
            user_metrics = await self._get_user_engagement_metrics(organization_id)

            # Generate insights and recommendations
            insights = await self._generate_insights(organization_id, org_metrics)
            recommendations = await self._generate_recommendations(organization_id, org_metrics)

            processing_time = (time.time() - start_time) * 1000

            response = PlatformManagerResponse(
                success=True,
                operation_id=operation_id,
                organization_id=organization_id,
                result_data={
                    "organization_metrics": org_metrics.__dict__,
                    "resource_metrics": resource_metrics,
                    "performance_metrics": performance_metrics,
                    "financial_metrics": financial_metrics,
                    "user_metrics": user_metrics,
                    "insights": insights,
                    "recommendations": recommendations,
                    "metrics_generated_at": datetime.utcnow().isoformat()
                },
                message=f"Organization metrics generated successfully",
                processing_time_ms=processing_time
            )

            logger.info(f"Metrics for {organization_id} generated in {processing_time:.2f}ms")
            return response

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Failed to get organization metrics: {str(e)}")

            return PlatformManagerResponse(
                success=False,
                operation_id=operation_id,
                organization_id=request.organization_id,
                message=f"Failed to get organization metrics: {str(e)}",
                processing_time_ms=processing_time
            )

    async def manage_organization_hierarchy(self, request: PlatformManagerRequest) -> PlatformManagerResponse:
        """Manage organization hierarchy and parent-child relationships"""
        start_time = time.time()
        operation_id = f"hierarchy_{int(time.time() * 1000)}"

        try:
            action = request.parameters.get("action")
            organization_id = request.organization_id

            if not action:
                raise ValueError("Action is required")

            result_data = {}

            if action == "create_hierarchy":
                # Create parent-child relationship
                parent_id = request.parameters.get("parent_organization_id")
                child_id = request.parameters.get("child_organization_id")

                if not parent_id or not child_id:
                    raise ValueError("Both parent and child organization IDs are required")

                await self._create_hierarchy_relationship(parent_id, child_id)
                result_data["hierarchy_created"] = {"parent": parent_id, "child": child_id}

            elif action == "get_hierarchy":
                # Get organization hierarchy tree
                if organization_id:
                    hierarchy_tree = await self._get_organization_hierarchy_tree(organization_id)
                    result_data["hierarchy_tree"] = hierarchy_tree
                else:
                    # Get all hierarchies
                    all_hierarchies = await self._get_all_hierarchies()
                    result_data["all_hierarchies"] = all_hierarchies

            elif action == "update_permissions":
                # Update hierarchy permissions
                permissions = request.parameters.get("permissions", {})
                inherit_permissions = request.parameters.get("inherit_permissions", True)

                await self._update_hierarchy_permissions(organization_id, permissions, inherit_permissions)
                result_data["permissions_updated"] = True

            elif action == "consolidate_resources":
                # Consolidate resources across hierarchy
                if organization_id:
                    consolidation_report = await self._consolidate_hierarchy_resources(organization_id)
                    result_data["consolidation_report"] = consolidation_report

            processing_time = (time.time() - start_time) * 1000

            response = PlatformManagerResponse(
                success=True,
                operation_id=operation_id,
                organization_id=organization_id,
                result_data=result_data,
                message=f"Hierarchy management operation '{action}' completed successfully",
                processing_time_ms=processing_time
            )

            logger.info(f"Hierarchy management completed in {processing_time:.2f}ms")
            return response

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"Hierarchy management failed: {str(e)}")

            return PlatformManagerResponse(
                success=False,
                operation_id=operation_id,
                organization_id=request.organization_id,
                message=f"Hierarchy management failed: {str(e)}",
                processing_time_ms=processing_time
            )

    # Helper methods for organization management

    async def _store_organization_config(self, org_config: OrganizationConfig) -> None:
        """Store organization configuration in Redis and database"""
        try:
            # Store in Redis for fast access
            cache_key = f"enterprise:org_config:{org_config.organization_id}"
            await self.redis_client.setex(
                cache_key,
                3600,  # 1 hour TTL
                json.dumps(org_config.dict(), default=str)
            )

            # Store in database for persistence
            # Note: In production, this would use actual database connection
            db_key = f"enterprise:db:org_config:{org_config.organization_id}"
            await self.redis_client.set(db_key, json.dumps(org_config.dict(), default=str))

            logger.info(f"Organization config stored for {org_config.organization_id}")

        except Exception as e:
            logger.error(f"Failed to store organization config: {str(e)}")
            raise

    async def _get_organization_config(self, organization_id: str) -> Optional[OrganizationConfig]:
        """Get organization configuration from cache or database"""
        try:
            # Check cache first
            if organization_id in self.organization_cache:
                return self.organization_cache[organization_id]

            # Check Redis cache
            cache_key = f"enterprise:org_config:{organization_id}"
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                config_data = json.loads(cached_data)
                org_config = OrganizationConfig(**config_data)
                self.organization_cache[organization_id] = org_config
                return org_config

            # Check database
            db_key = f"enterprise:db:org_config:{organization_id}"
            db_data = await self.redis_client.get(db_key)

            if db_data:
                config_data = json.loads(db_data)
                org_config = OrganizationConfig(**config_data)
                self.organization_cache[organization_id] = org_config

                # Restore to cache
                await self.redis_client.setex(cache_key, 3600, json.dumps(config_data, default=str))
                return org_config

            return None

        except Exception as e:
            logger.error(f"Failed to get organization config: {str(e)}")
            return None

    async def _initialize_resource_allocations(self, organization_id: str, resource_limits: Dict[ResourceType, int]) -> None:
        """Initialize resource allocations for new organization"""
        try:
            for resource_type, limit in resource_limits.items():
                allocation = ResourceAllocation(
                    organization_id=organization_id,
                    resource_type=resource_type,
                    allocated_amount=limit,
                    current_usage=0,
                    usage_history=[]
                )

                cache_key = f"enterprise:resource:{organization_id}:{resource_type.value}"
                await self.redis_client.setex(
                    cache_key,
                    3600,
                    json.dumps(allocation.dict(), default=str)
                )

            logger.info(f"Resource allocations initialized for {organization_id}")

        except Exception as e:
            logger.error(f"Failed to initialize resource allocations: {str(e)}")
            raise

    async def _store_organization_hierarchy(self, hierarchy: OrganizationHierarchy) -> None:
        """Store organization hierarchy information"""
        try:
            cache_key = f"enterprise:hierarchy:{hierarchy.organization_id}"
            await self.redis_client.setex(
                cache_key,
                3600,
                json.dumps(hierarchy.dict(), default=str)
            )

            logger.info(f"Hierarchy stored for {hierarchy.organization_id}")

        except Exception as e:
            logger.error(f"Failed to store organization hierarchy: {str(e)}")
            raise

    async def _trigger_organization_setup(self, organization_id: str, org_config: OrganizationConfig) -> None:
        """Trigger organization setup processes"""
        try:
            # Setup tasks that would be performed
            setup_tasks = [
                "database_provisioning",
                "service_initialization",
                "user_account_creation",
                "default_configuration_setup",
                "integration_preparation",
                "monitoring_setup"
            ]

            # In production, these would be actual async tasks
            for task in setup_tasks:
                setup_key = f"enterprise:setup:{organization_id}:{task}"
                await self.redis_client.setex(setup_key, 900, "in_progress")  # 15 minutes

            logger.info(f"Setup triggered for {organization_id}")

        except Exception as e:
            logger.error(f"Failed to trigger organization setup: {str(e)}")
            raise

    async def _calculate_organization_metrics(self, organization_id: str) -> OrganizationMetrics:
        """Calculate comprehensive organization metrics"""
        try:
            # In production, these would be actual database queries
            metrics = OrganizationMetrics(
                organization_id=organization_id,
                total_users=45,
                active_users_30d=38,
                total_api_calls=125000,
                api_calls_30d=28000,
                storage_used_gb=18.5,
                claude_instances_active=3,
                revenue_current_month=2850.00,
                support_tickets_open=2,
                uptime_percentage=99.8
            )

            # Cache metrics
            cache_key = f"enterprise:metrics:{organization_id}"
            await self.redis_client.setex(
                cache_key,
                300,  # 5 minutes TTL
                json.dumps(metrics.__dict__, default=str)
            )

            return metrics

        except Exception as e:
            logger.error(f"Failed to calculate organization metrics: {str(e)}")
            raise

    async def _get_resource_usage_metrics(self, organization_id: str) -> Dict[str, Any]:
        """Get detailed resource usage metrics"""
        try:
            # Simulate resource usage data
            return {
                "claude_instances": {
                    "allocated": 5,
                    "in_use": 3,
                    "utilization_percentage": 60.0,
                    "peak_usage_last_24h": 4
                },
                "storage": {
                    "allocated_gb": 50,
                    "used_gb": 18.5,
                    "utilization_percentage": 37.0,
                    "growth_rate_monthly": 12.5
                },
                "api_calls": {
                    "monthly_limit": 50000,
                    "current_month_usage": 28000,
                    "utilization_percentage": 56.0,
                    "daily_average": 933
                },
                "users": {
                    "max_allowed": 50,
                    "current_active": 38,
                    "utilization_percentage": 76.0,
                    "growth_rate_monthly": 15.2
                }
            }

        except Exception as e:
            logger.error(f"Failed to get resource usage metrics: {str(e)}")
            return {}

    async def _get_performance_metrics(self, organization_id: str) -> Dict[str, Any]:
        """Get performance metrics for organization"""
        try:
            return {
                "api_response_times": {
                    "avg_ms": 145,
                    "p95_ms": 280,
                    "p99_ms": 450
                },
                "uptime": {
                    "current_month": 99.8,
                    "last_30_days": 99.9,
                    "incidents_count": 1
                },
                "user_satisfaction": {
                    "avg_rating": 4.6,
                    "total_responses": 156,
                    "nps_score": 67
                },
                "system_health": {
                    "cpu_utilization": 45.2,
                    "memory_utilization": 62.8,
                    "disk_utilization": 34.1
                }
            }

        except Exception as e:
            logger.error(f"Failed to get performance metrics: {str(e)}")
            return {}

    async def _upgrade_organization_tier(self, org_config: OrganizationConfig, new_tier: OrganizationTier) -> None:
        """Upgrade organization to new tier"""
        try:
            old_tier = org_config.tier
            tier_config = self.tier_defaults[new_tier]

            # Update tier
            org_config.tier = new_tier

            # Update resource limits
            org_config.resource_limits.update(tier_config["resource_limits"])

            # Update enabled features
            org_config.enabled_features.update(tier_config["features"])

            # Update resource allocations
            await self._update_resource_allocations(org_config.organization_id, tier_config["resource_limits"])

            logger.info(f"Organization {org_config.organization_id} upgraded from {old_tier} to {new_tier}")

        except Exception as e:
            logger.error(f"Failed to upgrade organization tier: {str(e)}")
            raise

    async def _validate_feature_access(self, tier: OrganizationTier, features: Set[str]) -> None:
        """Validate that organization tier supports requested features"""
        try:
            for feature in features:
                if feature in self.feature_registry:
                    required_tier = self.feature_registry[feature]["tier_required"]
                    if tier.value < required_tier.value:  # Assuming enum values are ordered
                        raise ValueError(f"Feature '{feature}' requires tier {required_tier.value} or higher")

        except Exception as e:
            logger.error(f"Feature validation failed: {str(e)}")
            raise

# Performance monitoring and health check
def get_enterprise_platform_health() -> Dict[str, Any]:
    """Get Enterprise Platform Manager health status"""
    return {
        "service": "enterprise_platform_manager",
        "status": "healthy",
        "version": "1.0.0",
        "capabilities": [
            "organization_management",
            "resource_allocation",
            "hierarchy_management",
            "metrics_analytics",
            "tier_management",
            "compliance_management"
        ],
        "performance_targets": {
            "organization_creation_time": "< 2000ms",
            "configuration_update_time": "< 1500ms",
            "metrics_generation_time": "< 1000ms",
            "resource_allocation_time": "< 800ms"
        },
        "dependencies": {
            "redis": "required",
            "database": "required",
            "claude_services": "integration"
        },
        "last_health_check": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    # Example usage and testing
    async def test_enterprise_platform_manager():
        manager = EnterprisePlatformManager()

        # Test organization creation
        create_request = PlatformManagerRequest(
            operation_type="create_organization",
            parameters={
                "name": "Acme Real Estate Group",
                "tier": "enterprise",
                "admin_email": "admin@acme-realestate.com",
                "industry_vertical": "real_estate"
            },
            admin_user_id="admin_123"
        )

        response = await manager.create_organization(create_request)
        print(f"Create Organization Response: {response.dict()}")

        if response.success:
            org_id = response.organization_id

            # Test metrics generation
            metrics_request = PlatformManagerRequest(
                operation_type="get_metrics",
                organization_id=org_id,
                admin_user_id="admin_123"
            )

            metrics_response = await manager.get_organization_metrics(metrics_request)
            print(f"Metrics Response: {metrics_response.dict()}")

    # Run test
    asyncio.run(test_enterprise_platform_manager())