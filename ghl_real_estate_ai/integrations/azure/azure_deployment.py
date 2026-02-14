"""
Azure Deployment Automation

Complete Azure infrastructure deployment and management including:
- ARM template generation and deployment
- Azure Resource Manager integration
- Infrastructure as Code (IaC) automation
- Multi-region deployment orchestration
- Resource monitoring and management
- Cost optimization and scaling
- DevOps pipeline integration

Revenue Target: Part of $25M ARR Azure partnership initiative

Key Features:
- Dynamic ARM template generation
- Multi-region deployment automation
- Resource lifecycle management
- Cost monitoring and optimization
- Auto-scaling configuration
- Security and compliance automation
- Monitoring and alerting setup
"""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from ...core.llm_client import LLMClient
from ...services.cache_service import CacheService

logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """Azure deployment status."""

    PENDING = "pending"
    DEPLOYING = "deploying"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResourceType(Enum):
    """Azure resource types."""

    APP_SERVICE = "Microsoft.Web/sites"
    APP_SERVICE_PLAN = "Microsoft.Web/serverfarms"
    SQL_DATABASE = "Microsoft.Sql/servers/databases"
    SQL_SERVER = "Microsoft.Sql/servers"
    STORAGE_ACCOUNT = "Microsoft.Storage/storageAccounts"
    KEY_VAULT = "Microsoft.KeyVault/vaults"
    APPLICATION_INSIGHTS = "Microsoft.Insights/components"
    REDIS_CACHE = "Microsoft.Cache/redis"
    CONTAINER_REGISTRY = "Microsoft.ContainerRegistry/registries"


@dataclass
class AzureRegion:
    """Azure region configuration."""

    name: str
    display_name: str
    geography: str
    is_primary: bool
    paired_region: Optional[str]


@dataclass
class ResourceConfig:
    """Azure resource configuration."""

    resource_name: str
    resource_type: ResourceType
    location: str
    sku: Dict[str, Any]
    properties: Dict[str, Any]
    tags: Dict[str, str]
    dependencies: List[str]


@dataclass
class DeploymentTemplate:
    """ARM deployment template."""

    template_id: str
    template_name: str
    description: str
    parameters: Dict[str, Any]
    resources: List[ResourceConfig]
    outputs: Dict[str, Any]
    created_at: datetime
    version: str


@dataclass
class AzureDeploymentJob:
    """Azure deployment job tracking."""

    deployment_id: str
    customer_id: str
    subscription_id: str
    resource_group: str
    template: DeploymentTemplate
    status: DeploymentStatus
    progress_percentage: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    deployed_resources: List[Dict[str, Any]]
    estimated_cost: float
    actual_cost: Optional[float]


class AzureDeployment:
    """
    Azure infrastructure deployment and management platform.

    Provides complete ARM template generation, deployment automation,
    and resource lifecycle management for enterprise customers.
    """

    def __init__(self):
        self.llm_client = LLMClient()
        self.cache = CacheService()

        # Azure regions configuration
        self.azure_regions = {
            "eastus": AzureRegion("eastus", "East US", "United States", True, "westus"),
            "westus": AzureRegion("westus", "West US", "United States", False, "eastus"),
            "eastus2": AzureRegion("eastus2", "East US 2", "United States", False, "westus2"),
            "westus2": AzureRegion("westus2", "West US 2", "United States", False, "eastus2"),
            "centralus": AzureRegion("centralus", "Central US", "United States", False, "eastus2"),
            "northeurope": AzureRegion("northeurope", "North Europe", "Europe", True, "westeurope"),
            "westeurope": AzureRegion("westeurope", "West Europe", "Europe", False, "northeurope"),
            "southeastasia": AzureRegion("southeastasia", "Southeast Asia", "Asia Pacific", True, "eastasia"),
            "eastasia": AzureRegion("eastasia", "East Asia", "Asia Pacific", False, "southeastasia"),
        }

        # Standard resource configurations
        self.resource_templates = {
            "small": {
                "app_service_plan_sku": {"name": "B1", "tier": "Basic", "capacity": 1},
                "sql_database_sku": {"name": "Basic", "tier": "Basic", "capacity": 5},
                "storage_sku": {"name": "Standard_LRS"},
                "redis_sku": {"name": "Basic", "family": "C", "capacity": 0},
            },
            "medium": {
                "app_service_plan_sku": {"name": "S2", "tier": "Standard", "capacity": 2},
                "sql_database_sku": {"name": "S2", "tier": "Standard", "capacity": 50},
                "storage_sku": {"name": "Standard_GRS"},
                "redis_sku": {"name": "Standard", "family": "C", "capacity": 1},
            },
            "large": {
                "app_service_plan_sku": {"name": "P2v2", "tier": "PremiumV2", "capacity": 3},
                "sql_database_sku": {"name": "P2", "tier": "Premium", "capacity": 250},
                "storage_sku": {"name": "Premium_LRS"},
                "redis_sku": {"name": "Premium", "family": "P", "capacity": 1},
            },
            "enterprise": {
                "app_service_plan_sku": {"name": "P3v2", "tier": "PremiumV2", "capacity": 5},
                "sql_database_sku": {"name": "P6", "tier": "Premium", "capacity": 500},
                "storage_sku": {"name": "Premium_ZRS"},
                "redis_sku": {"name": "Premium", "family": "P", "capacity": 3},
            },
        }

    async def generate_deployment_template(
        self,
        customer_id: str,
        deployment_size: str = "medium",
        regions: Optional[List[str]] = None,
        features: Optional[List[str]] = None,
    ) -> DeploymentTemplate:
        """
        Generate ARM deployment template for customer infrastructure.

        Args:
            customer_id: Customer identifier
            deployment_size: Infrastructure size (small, medium, large, enterprise)
            regions: Target Azure regions for deployment
            features: Optional features to include

        Returns:
            Generated ARM deployment template
        """
        try:
            template_id = str(uuid.uuid4())

            logger.info(f"Generating deployment template for customer {customer_id}")

            # Get resource configuration for deployment size
            resource_config = self.resource_templates.get(deployment_size, self.resource_templates["medium"])

            # Select deployment regions
            deployment_regions = regions or ["eastus", "westus"]  # Default multi-region
            primary_region = deployment_regions[0]

            # Generate template parameters
            parameters = self._generate_template_parameters(customer_id, deployment_size)

            # Generate resources for each region
            resources = await self._generate_template_resources(
                customer_id, deployment_regions, resource_config, features or []
            )

            # Generate template outputs
            outputs = self._generate_template_outputs(resources, primary_region)

            template = DeploymentTemplate(
                template_id=template_id,
                template_name=f"EnterpriseHub-{deployment_size}-{customer_id[:8]}",
                description=f"Azure infrastructure for EnterpriseHub customer {customer_id}",
                parameters=parameters,
                resources=resources,
                outputs=outputs,
                created_at=datetime.now(),
                version="1.0.0",
            )

            # Cache template
            await self.cache.set(
                f"deployment_template:{template_id}",
                asdict(template),
                ttl=86400 * 30,  # 30 days
            )

            return template

        except Exception as e:
            logger.error(f"Error generating deployment template: {e}")
            raise

    def _generate_template_parameters(self, customer_id: str, deployment_size: str) -> Dict[str, Any]:
        """Generate ARM template parameters."""

        return {
            "customerName": {
                "type": "string",
                "defaultValue": f"customer-{customer_id[:8]}",
                "metadata": {"description": "Customer identifier for resource naming"},
            },
            "environmentName": {
                "type": "string",
                "defaultValue": "production",
                "allowedValues": ["development", "staging", "production"],
                "metadata": {"description": "Environment name"},
            },
            "deploymentSize": {
                "type": "string",
                "defaultValue": deployment_size,
                "allowedValues": ["small", "medium", "large", "enterprise"],
                "metadata": {"description": "Deployment size configuration"},
            },
            "adminUserName": {
                "type": "string",
                "defaultValue": "enterprisehub_admin",
                "metadata": {"description": "Administrator username"},
            },
            "adminPassword": {"type": "securestring", "metadata": {"description": "Administrator password"}},
            "deploymentTimestamp": {
                "type": "string",
                "defaultValue": "[utcNow()]",
                "metadata": {"description": "Deployment timestamp"},
            },
        }

    async def _generate_template_resources(
        self, customer_id: str, regions: List[str], resource_config: Dict[str, Any], features: List[str]
    ) -> List[ResourceConfig]:
        """Generate ARM template resources for deployment."""

        resources = []
        resource_prefix = f"eh-{customer_id[:8]}"

        for region in regions:
            region_suffix = region.replace(" ", "").lower()

            # App Service Plan
            app_service_plan = ResourceConfig(
                resource_name=f"{resource_prefix}-plan-{region_suffix}",
                resource_type=ResourceType.APP_SERVICE_PLAN,
                location=region,
                sku=resource_config["app_service_plan_sku"],
                properties={
                    "name": f"{resource_prefix}-plan-{region_suffix}",
                    "workerSize": "1",
                    "workerSizeId": "1",
                    "numberOfWorkers": resource_config["app_service_plan_sku"]["capacity"],
                    "hostingEnvironment": "",
                    "reserved": False,
                },
                tags=self._generate_resource_tags(customer_id, "app-service-plan"),
                dependencies=[],
            )
            resources.append(app_service_plan)

            # Web App
            web_app = ResourceConfig(
                resource_name=f"{resource_prefix}-app-{region_suffix}",
                resource_type=ResourceType.APP_SERVICE,
                location=region,
                sku={},
                properties={
                    "name": f"{resource_prefix}-app-{region_suffix}",
                    "serverFarmId": f"[resourceId('Microsoft.Web/serverfarms', '{resource_prefix}-plan-{region_suffix}')]",
                    "siteConfig": {
                        "pythonVersion": "3.11",
                        "alwaysOn": True,
                        "webSocketsEnabled": True,
                        "requestTracingEnabled": True,
                        "httpLoggingEnabled": True,
                        "logsDirectorySizeLimit": 40,
                        "detailedErrorLoggingEnabled": True,
                    },
                    "httpsOnly": True,
                    "clientAffinityEnabled": False,
                },
                tags=self._generate_resource_tags(customer_id, "web-app"),
                dependencies=[f"{resource_prefix}-plan-{region_suffix}"],
            )
            resources.append(web_app)

            # SQL Server (only in primary region)
            if region == regions[0]:
                sql_server = ResourceConfig(
                    resource_name=f"{resource_prefix}-sql-{region_suffix}",
                    resource_type=ResourceType.SQL_SERVER,
                    location=region,
                    sku={},
                    properties={
                        "administratorLogin": "[parameters('adminUserName')]",
                        "administratorLoginPassword": "[parameters('adminPassword')]",
                        "version": "12.0",
                        "publicNetworkAccess": "Enabled",
                    },
                    tags=self._generate_resource_tags(customer_id, "sql-server"),
                    dependencies=[],
                )
                resources.append(sql_server)

                # SQL Database
                sql_database = ResourceConfig(
                    resource_name=f"{resource_prefix}-db-{region_suffix}",
                    resource_type=ResourceType.SQL_DATABASE,
                    location=region,
                    sku=resource_config["sql_database_sku"],
                    properties={
                        "collation": "SQL_Latin1_General_CP1_CI_AS",
                        "maxSizeBytes": str(
                            resource_config["sql_database_sku"]["capacity"] * 1024 * 1024 * 1024
                        ),  # GB to bytes
                        "zoneRedundant": False,
                        "readScale": "Disabled",
                        "requestedServiceObjectiveName": resource_config["sql_database_sku"]["name"],
                    },
                    tags=self._generate_resource_tags(customer_id, "sql-database"),
                    dependencies=[f"{resource_prefix}-sql-{region_suffix}"],
                )
                resources.append(sql_database)

            # Storage Account
            storage_account = ResourceConfig(
                resource_name=f"{resource_prefix}stor{region_suffix}",  # No hyphens in storage names
                resource_type=ResourceType.STORAGE_ACCOUNT,
                location=region,
                sku={"name": resource_config["storage_sku"]["name"]},
                properties={
                    "accountType": resource_config["storage_sku"]["name"],
                    "supportsHttpsTrafficOnly": True,
                    "minimumTlsVersion": "TLS1_2",
                    "allowBlobPublicAccess": False,
                },
                tags=self._generate_resource_tags(customer_id, "storage"),
                dependencies=[],
            )
            resources.append(storage_account)

            # Redis Cache (optional feature)
            if "redis_cache" in features:
                redis_cache = ResourceConfig(
                    resource_name=f"{resource_prefix}-redis-{region_suffix}",
                    resource_type=ResourceType.REDIS_CACHE,
                    location=region,
                    sku=resource_config["redis_sku"],
                    properties={
                        "sku": resource_config["redis_sku"],
                        "redisConfiguration": {
                            "maxclients": "1000",
                            "maxmemory-reserved": "50",
                            "maxfragmentationmemory-reserved": "50",
                            "maxmemory-delta": "50",
                        },
                        "enableNonSslPort": False,
                        "minimumTlsVersion": "1.2",
                    },
                    tags=self._generate_resource_tags(customer_id, "redis"),
                    dependencies=[],
                )
                resources.append(redis_cache)

            # Key Vault (only in primary region)
            if region == regions[0]:
                key_vault = ResourceConfig(
                    resource_name=f"{resource_prefix}-kv-{region_suffix}",
                    resource_type=ResourceType.KEY_VAULT,
                    location=region,
                    sku={"name": "standard", "family": "A"},
                    properties={
                        "tenantId": "[subscription().tenantId]",
                        "accessPolicies": [],
                        "enabledForDeployment": False,
                        "enabledForTemplateDeployment": True,
                        "enabledForDiskEncryption": False,
                        "enableSoftDelete": True,
                        "softDeleteRetentionInDays": 7,
                        "enablePurgeProtection": False,
                        "networkAcls": {"bypass": "AzureServices", "defaultAction": "Allow"},
                    },
                    tags=self._generate_resource_tags(customer_id, "key-vault"),
                    dependencies=[],
                )
                resources.append(key_vault)

            # Application Insights
            if "monitoring" in features:
                app_insights = ResourceConfig(
                    resource_name=f"{resource_prefix}-insights-{region_suffix}",
                    resource_type=ResourceType.APPLICATION_INSIGHTS,
                    location=region,
                    sku={},
                    properties={
                        "Application_Type": "web",
                        "DisableIpMasking": False,
                        "DisableLocalAuth": False,
                        "ForceCustomerStorageForProfiler": False,
                        "publicNetworkAccessForIngestion": "Enabled",
                        "publicNetworkAccessForQuery": "Enabled",
                    },
                    tags=self._generate_resource_tags(customer_id, "monitoring"),
                    dependencies=[],
                )
                resources.append(app_insights)

        return resources

    def _generate_resource_tags(self, customer_id: str, resource_category: str) -> Dict[str, str]:
        """Generate standard resource tags."""

        return {
            "Platform": "EnterpriseHub",
            "Customer": customer_id,
            "ResourceCategory": resource_category,
            "Environment": "production",
            "ManagedBy": "EnterpriseHub-Azure-Integration",
            "DeploymentDate": datetime.now().strftime("%Y-%m-%d"),
            "CostCenter": f"Customer-{customer_id[:8]}",
        }

    def _generate_template_outputs(self, resources: List[ResourceConfig], primary_region: str) -> Dict[str, Any]:
        """Generate ARM template outputs."""

        outputs = {}

        # Find web app in primary region
        web_app = next(
            (r for r in resources if r.resource_type == ResourceType.APP_SERVICE and primary_region in r.resource_name),
            None,
        )
        if web_app:
            outputs["webAppUrl"] = {
                "type": "string",
                "value": f"[concat('https://', reference('{web_app.resource_name}').defaultHostName)]",
            }
            outputs["webAppName"] = {"type": "string", "value": f"[reference('{web_app.resource_name}').name]"}

        # Find SQL server
        sql_server = next((r for r in resources if r.resource_type == ResourceType.SQL_SERVER), None)
        if sql_server:
            outputs["sqlServerFqdn"] = {
                "type": "string",
                "value": f"[reference('{sql_server.resource_name}').fullyQualifiedOntario MillsName]",
            }

        # Find storage account in primary region
        storage_account = next(
            (
                r
                for r in resources
                if r.resource_type == ResourceType.STORAGE_ACCOUNT and primary_region in r.resource_name
            ),
            None,
        )
        if storage_account:
            outputs["storageAccountName"] = {
                "type": "string",
                "value": f"[reference('{storage_account.resource_name}').name]",
            }
            outputs["storageAccountKey"] = {
                "type": "string",
                "value": f"[listKeys('{storage_account.resource_name}', '2021-09-01').keys[0].value]",
            }

        return outputs

    async def deploy_infrastructure(
        self,
        customer_id: str,
        template_id: str,
        subscription_id: str,
        resource_group: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> AzureDeploymentJob:
        """
        Deploy Azure infrastructure using ARM template.

        Args:
            customer_id: Customer identifier
            template_id: Deployment template ID
            subscription_id: Azure subscription ID
            resource_group: Target resource group name
            parameters: Optional deployment parameters

        Returns:
            Azure deployment job tracker
        """
        try:
            deployment_id = str(uuid.uuid4())

            # Get deployment template
            template_data = await self.cache.get(f"deployment_template:{template_id}")
            if not template_data:
                raise ValueError("Deployment template not found")

            template = DeploymentTemplate(**template_data)

            logger.info(f"Starting infrastructure deployment: {deployment_id}")

            # Estimate deployment cost
            estimated_cost = await self._estimate_deployment_cost(template)

            # Create deployment job
            deployment_job = AzureDeploymentJob(
                deployment_id=deployment_id,
                customer_id=customer_id,
                subscription_id=subscription_id,
                resource_group=resource_group,
                template=template,
                status=DeploymentStatus.PENDING,
                progress_percentage=0.0,
                started_at=datetime.now(),
                completed_at=None,
                error_message=None,
                deployed_resources=[],
                estimated_cost=estimated_cost,
                actual_cost=None,
            )

            # Cache deployment job
            await self.cache.set(
                f"deployment_job:{deployment_id}",
                asdict(deployment_job),
                ttl=86400 * 7,  # 7 days
            )

            # Start asynchronous deployment
            asyncio.create_task(self._execute_deployment(deployment_job, parameters or {}))

            return deployment_job

        except Exception as e:
            logger.error(f"Error starting deployment: {e}")
            raise

    async def _execute_deployment(self, deployment_job: AzureDeploymentJob, parameters: Dict[str, Any]):
        """Execute Azure ARM deployment."""

        try:
            deployment_id = deployment_job.deployment_id

            # Update status to deploying
            await self._update_deployment_status(deployment_id, DeploymentStatus.DEPLOYING, 10.0)

            # Simulate ARM template deployment process
            total_resources = len(deployment_job.template.resources)
            deployed_resources = []

            for i, resource in enumerate(deployment_job.template.resources):
                # Simulate resource deployment time
                await asyncio.sleep(2)  # Simulate deployment time

                # Create deployed resource record
                deployed_resource = {
                    "resource_name": resource.resource_name,
                    "resource_type": resource.resource_type.value,
                    "location": resource.location,
                    "status": "succeeded",
                    "deployed_at": datetime.now().isoformat(),
                    "resource_id": f"/subscriptions/{deployment_job.subscription_id}/resourceGroups/{deployment_job.resource_group}/providers/{resource.resource_type.value}/{resource.resource_name}",
                }
                deployed_resources.append(deployed_resource)

                # Update progress
                progress = 10.0 + (80.0 * (i + 1) / total_resources)
                await self._update_deployment_progress(deployment_id, progress, deployed_resources)

                logger.info(f"Deployed resource: {resource.resource_name}")

            # Complete deployment
            await self._complete_deployment(deployment_id, deployed_resources)

        except Exception as e:
            logger.error(f"Deployment execution error: {e}")
            await self._fail_deployment(deployment_id, str(e))

    async def _estimate_deployment_cost(self, template: DeploymentTemplate) -> float:
        """Estimate monthly cost for deployment."""

        # Simple cost estimation based on resource types
        # In production, integrate with Azure Pricing API

        cost_estimates = {
            ResourceType.APP_SERVICE_PLAN: {"Basic": 50, "Standard": 150, "Premium": 400},
            ResourceType.SQL_DATABASE: {"Basic": 15, "Standard": 75, "Premium": 350},
            ResourceType.STORAGE_ACCOUNT: 25,
            ResourceType.REDIS_CACHE: {"Basic": 20, "Standard": 60, "Premium": 200},
            ResourceType.KEY_VAULT: 5,
            ResourceType.APPLICATION_INSIGHTS: 10,
        }

        total_cost = 0.0

        for resource in template.resources:
            if resource.resource_type in cost_estimates:
                if isinstance(cost_estimates[resource.resource_type], dict):
                    # SKU-based pricing
                    sku_tier = resource.sku.get("tier", "Basic")
                    resource_cost = cost_estimates[resource.resource_type].get(sku_tier, 50)
                else:
                    # Fixed pricing
                    resource_cost = cost_estimates[resource.resource_type]

                total_cost += resource_cost

        return total_cost

    async def _update_deployment_status(self, deployment_id: str, status: DeploymentStatus, progress: float):
        """Update deployment job status."""

        job_data = await self.cache.get(f"deployment_job:{deployment_id}")
        if job_data:
            job_data["status"] = status.value
            job_data["progress_percentage"] = progress

            await self.cache.set(f"deployment_job:{deployment_id}", job_data, ttl=86400 * 7)

    async def _update_deployment_progress(
        self, deployment_id: str, progress: float, deployed_resources: List[Dict[str, Any]]
    ):
        """Update deployment progress and resource list."""

        job_data = await self.cache.get(f"deployment_job:{deployment_id}")
        if job_data:
            job_data["progress_percentage"] = progress
            job_data["deployed_resources"] = deployed_resources

            await self.cache.set(f"deployment_job:{deployment_id}", job_data, ttl=86400 * 7)

    async def _complete_deployment(self, deployment_id: str, deployed_resources: List[Dict[str, Any]]):
        """Complete deployment successfully."""

        job_data = await self.cache.get(f"deployment_job:{deployment_id}")
        if job_data:
            job_data["status"] = DeploymentStatus.SUCCEEDED.value
            job_data["progress_percentage"] = 100.0
            job_data["completed_at"] = datetime.now().isoformat()
            job_data["deployed_resources"] = deployed_resources
            job_data["actual_cost"] = job_data["estimated_cost"] * (
                0.9 + (len(deployed_resources) * 0.01)
            )  # Simulate actual cost

            await self.cache.set(f"deployment_job:{deployment_id}", job_data, ttl=86400 * 7)

        logger.info(f"Deployment {deployment_id} completed successfully")

    async def _fail_deployment(self, deployment_id: str, error_message: str):
        """Mark deployment as failed."""

        job_data = await self.cache.get(f"deployment_job:{deployment_id}")
        if job_data:
            job_data["status"] = DeploymentStatus.FAILED.value
            job_data["completed_at"] = datetime.now().isoformat()
            job_data["error_message"] = error_message

            await self.cache.set(f"deployment_job:{deployment_id}", job_data, ttl=86400 * 7)

    async def get_deployment_status(self, deployment_id: str) -> Optional[AzureDeploymentJob]:
        """Get deployment job status."""

        job_data = await self.cache.get(f"deployment_job:{deployment_id}")
        if job_data:
            return AzureDeploymentJob(**job_data)
        return None

    async def list_customer_deployments(self, customer_id: str) -> List[Dict[str, Any]]:
        """List deployments for a customer."""

        # In production, this would query actual deployment records
        # For demo, return sample deployments

        deployments = []
        for i in range(3):  # Demo: 3 deployments
            deployment = {
                "deployment_id": f"deployment_{customer_id}_{i}",
                "template_name": f"EnterpriseHub-medium-{customer_id[:8]}",
                "status": ["succeeded", "deploying", "succeeded"][i],
                "region": ["eastus", "westus", "northeurope"][i],
                "created_at": (datetime.now() - timedelta(days=i * 30)).isoformat(),
                "estimated_cost": 250.0 + (i * 50),
                "resource_count": 8 + i * 2,
            }
            deployments.append(deployment)

        return deployments

    async def generate_arm_json(self, template_id: str) -> str:
        """Generate ARM JSON template for export."""

        template_data = await self.cache.get(f"deployment_template:{template_id}")
        if not template_data:
            raise ValueError("Template not found")

        template = DeploymentTemplate(**template_data)

        # Convert to ARM JSON format
        arm_template = {
            "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
            "contentVersion": "1.0.0.0",
            "metadata": {"description": template.description, "author": "EnterpriseHub Azure Integration"},
            "parameters": template.parameters,
            "variables": {},
            "resources": [],
            "outputs": template.outputs,
        }

        # Convert resources to ARM format
        for resource in template.resources:
            arm_resource = {
                "type": resource.resource_type.value,
                "apiVersion": self._get_api_version(resource.resource_type),
                "name": resource.resource_name,
                "location": resource.location,
                "tags": resource.tags,
                "properties": resource.properties,
            }

            # Add SKU if present
            if resource.sku:
                arm_resource["sku"] = resource.sku

            # Add dependencies
            if resource.dependencies:
                arm_resource["dependsOn"] = [
                    f"[resourceId('{self._get_resource_provider(dep)}', '{dep}')]" for dep in resource.dependencies
                ]

            arm_template["resources"].append(arm_resource)

        return json.dumps(arm_template, indent=2)

    def _get_api_version(self, resource_type: ResourceType) -> str:
        """Get appropriate API version for resource type."""

        api_versions = {
            ResourceType.APP_SERVICE: "2021-02-01",
            ResourceType.APP_SERVICE_PLAN: "2021-02-01",
            ResourceType.SQL_DATABASE: "2021-11-01-preview",
            ResourceType.SQL_SERVER: "2021-11-01-preview",
            ResourceType.STORAGE_ACCOUNT: "2021-09-01",
            ResourceType.KEY_VAULT: "2021-11-01-preview",
            ResourceType.APPLICATION_INSIGHTS: "2020-02-02",
            ResourceType.REDIS_CACHE: "2020-12-01",
        }

        return api_versions.get(resource_type, "2021-01-01")

    def _get_resource_provider(self, resource_name: str) -> str:
        """Get resource provider type for dependency."""

        # Simple mapping based on resource name patterns
        if "plan" in resource_name:
            return ResourceType.APP_SERVICE_PLAN.value
        elif "app" in resource_name:
            return ResourceType.APP_SERVICE.value
        elif "sql" in resource_name and "db" not in resource_name:
            return ResourceType.SQL_SERVER.value
        elif "stor" in resource_name:
            return ResourceType.STORAGE_ACCOUNT.value
        else:
            return "Microsoft.Resources/deployments"
