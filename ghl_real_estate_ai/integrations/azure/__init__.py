"""
Microsoft Azure Marketplace Integration

Complete Azure marketplace integration for enterprise distribution including:
- Azure marketplace listing and certification
- Azure AD/Entra ID SSO integration
- Azure billing and subscription management
- ARM template deployment automation
- Azure DevOps CI/CD integration

Revenue Target: $25M ARR through marketplace distribution

Key Components:
- Azure Marketplace: Listing, billing, and customer acquisition
- Azure Auth: SSO and multi-tenant authentication
- Azure Deployment: ARM templates and infrastructure automation
- Azure Billing: Marketplace billing integration and SaaS offers
"""

from .azure_marketplace import AzureMarketplace
from .azure_auth import AzureAuthIntegration
from .azure_deployment import AzureDeployment
from .azure_billing import AzureBilling

__all__ = [
    "AzureMarketplace",
    "AzureAuthIntegration",
    "AzureDeployment",
    "AzureBilling"
]

# Azure integration configuration
AZURE_CONFIG = {
    "target_revenue": 25_000_000,  # $25M ARR
    "marketplace_category": "Analytics",
    "saas_offer_types": [
        "per_user_monthly",
        "per_user_annual", 
        "flat_rate_monthly",
        "flat_rate_annual"
    ],
    "azure_services": [
        "Azure AD",
        "Azure App Service",
        "Azure Container Instances",
        "Azure Key Vault",
        "Azure Monitor",
        "Azure SQL Database"
    ],
    "pricing_plans": {
        "starter": {
            "monthly_cost": 299,
            "annual_cost": 2999,
            "user_limit": 10
        },
        "professional": {
            "monthly_cost": 999,
            "annual_cost": 9999,
            "user_limit": 100
        },
        "enterprise": {
            "monthly_cost": 2999,
            "annual_cost": 29999,
            "user_limit": "unlimited"
        }
    }
}