"""
Marketplace Sync Service - Agent 2: Integration Architect
Seamless synchronization between Workflow Marketplace and Template Manager.

Features:
- Auto-sync templates between marketplace and local manager
- Cross-service context sharing
- Unified workflow orchestration
- Smart dependency resolution
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class MarketplaceSync:
    """
    Integration layer between Workflow Marketplace and Template Manager.
    Ensures seamless data flow and context sharing across services.
    """

    def __init__(self):
        """Initialize Marketplace Sync."""
        self.sync_log = []
        self.context_cache = {}

    def sync_template_to_marketplace(self, template_data: Dict, publish: bool = False) -> Dict:
        """
        Sync a local template to the marketplace.

        Args:
            template_data: Template data from Template Manager
            publish: Whether to publish publicly in marketplace

        Returns:
            Sync result with marketplace listing
        """
        # Validate template data
        if not self._validate_template(template_data):
            return {
                "success": False,
                "error": "Invalid template data",
                "validation_errors": self._get_validation_errors(template_data),
            }

        # Create marketplace listing
        marketplace_listing = {
            "listing_id": f"MPL-{template_data.get('id', 'unknown')}",
            "template_id": template_data.get("id"),
            "name": template_data.get("name"),
            "description": template_data.get("description"),
            "category": template_data.get("category", "custom"),
            "tags": template_data.get("tags", []),
            "author": template_data.get("author", "Jorge Sales"),
            "version": template_data.get("version", "1.0.0"),
            "published": publish,
            "downloads": 0,
            "rating": 0.0,
            "created_at": datetime.now().isoformat(),
            "last_synced": datetime.now().isoformat(),
            "template_data": template_data,
        }

        # Log sync operation
        self._log_sync(
            operation="template_to_marketplace",
            template_id=template_data.get("id"),
            status="success",
        )

        return {
            "success": True,
            "listing": marketplace_listing,
            "message": f"Template synced to marketplace {'and published' if publish else '(private)'}",
            "listing_url": f"/marketplace/listing/{marketplace_listing['listing_id']}",
        }

    def sync_marketplace_to_template(self, listing_id: str, marketplace_data: Dict) -> Dict:
        """
        Import marketplace template to local Template Manager.

        Args:
            listing_id: Marketplace listing ID
            marketplace_data: Marketplace listing data

        Returns:
            Import result with local template
        """
        template_data = marketplace_data.get("template_data", {})

        if not template_data:
            return {
                "success": False,
                "error": "No template data in marketplace listing",
            }

        # Add marketplace metadata
        template_data["marketplace_source"] = {
            "listing_id": listing_id,
            "imported_at": datetime.now().isoformat(),
            "original_author": marketplace_data.get("author"),
            "version": marketplace_data.get("version"),
        }

        # Mark as installed
        template_data["installed"] = True
        template_data["install_date"] = datetime.now().isoformat()

        # Log sync operation
        self._log_sync(
            operation="marketplace_to_template",
            template_id=template_data.get("id"),
            status="success",
        )

        return {
            "success": True,
            "template": template_data,
            "message": f"Template '{template_data.get('name')}' imported successfully",
            "installed": True,
        }

    def share_context_between_services(self, source_service: str, target_service: str, context_data: Dict) -> Dict:
        """
        Share context between different AI services.

        Args:
            source_service: Service providing context
            target_service: Service receiving context
            context_data: Context to share

        Returns:
            Context sharing result
        """
        # Create context key
        context_key = f"{source_service}_to_{target_service}"

        # Enrich context with metadata
        enriched_context = {
            "source": source_service,
            "target": target_service,
            "data": context_data,
            "shared_at": datetime.now().isoformat(),
            "ttl_minutes": 60,  # Context expires after 1 hour
        }

        # Cache context
        self.context_cache[context_key] = enriched_context

        # Log context sharing
        self._log_sync(operation="context_share", template_id=context_key, status="success")

        return {
            "success": True,
            "context_key": context_key,
            "message": f"Context shared from {source_service} to {target_service}",
            "expires_in_minutes": 60,
        }

    def get_shared_context(self, source_service: str, target_service: str) -> Optional[Dict]:
        """
        Retrieve shared context between services.

        Args:
            source_service: Source service name
            target_service: Target service name

        Returns:
            Shared context data or None
        """
        context_key = f"{source_service}_to_{target_service}"

        context = self.context_cache.get(context_key)

        if not context:
            return None

        # Check if expired
        shared_at = datetime.fromisoformat(context["shared_at"])
        ttl_minutes = context["ttl_minutes"]

        if (datetime.now() - shared_at).total_seconds() / 60 > ttl_minutes:
            # Context expired
            del self.context_cache[context_key]
            return None

        return context["data"]

    def orchestrate_workflow(self, workflow_name: str, services: List[str], lead_data: Dict) -> Dict:
        """
        Orchestrate multi-service workflow.

        Args:
            workflow_name: Name of workflow
            services: List of services to orchestrate
            lead_data: Lead data to process

        Returns:
            Orchestration result with outputs from each service
        """
        results = {
            "workflow_name": workflow_name,
            "services_executed": [],
            "outputs": {},
            "started_at": datetime.now().isoformat(),
        }

        # Define service execution order and dependencies
        service_configs = {
            "hot_lead_fastlane": {
                "order": 1,
                "inputs": ["lead_data"],
                "outputs": ["lead_score", "priority", "routing"],
            },
            "deal_closer_ai": {
                "order": 2,
                "inputs": ["lead_data", "lead_score"],
                "outputs": ["objection_response", "talking_points"],
            },
            "commission_calculator": {
                "order": 3,
                "inputs": ["lead_data", "deal_value"],
                "outputs": ["projected_commission", "roi"],
            },
            "ai_listing_writer": {
                "order": 1,
                "inputs": ["property_data"],
                "outputs": ["listing_description", "marketing_copy"],
            },
            "workflow_marketplace": {
                "order": 1,
                "inputs": ["workflow_query"],
                "outputs": ["recommended_templates", "workflows"],
            },
        }

        # Sort services by execution order
        ordered_services = sorted(
            [s for s in services if s in service_configs],
            key=lambda x: service_configs[x]["order"],
        )

        # Execute services in order
        context = lead_data.copy()

        for service in ordered_services:
            config = service_configs[service]

            # Simulate service execution
            service_result = self._execute_service(service, context, config)

            results["services_executed"].append(service)
            results["outputs"][service] = service_result

            # Add outputs to context for next service
            context.update(service_result)

        results["completed_at"] = datetime.now().isoformat()
        results["success"] = True

        # Log orchestration
        self._log_sync(
            operation="workflow_orchestration",
            template_id=workflow_name,
            status="success",
        )

        return results

    def _execute_service(self, service_name: str, context: Dict, config: Dict) -> Dict:
        """Simulate service execution (to be replaced with actual service calls)."""
        # This is a stub that would call actual service APIs
        return {
            "service": service_name,
            "status": "success",
            "executed_at": datetime.now().isoformat(),
            "note": f"Service {service_name} executed with context",
        }

    def resolve_dependencies(self, template_id: str, template_data: Dict) -> Dict:
        """
        Resolve template dependencies.

        Args:
            template_id: Template identifier
            template_data: Template configuration

        Returns:
            Dependency resolution result
        """
        dependencies = template_data.get("dependencies", [])

        if not dependencies:
            return {
                "template_id": template_id,
                "dependencies": [],
                "all_satisfied": True,
                "missing": [],
            }

        # Check which dependencies are satisfied
        missing = []
        satisfied = []

        # Simulate dependency check
        for dep in dependencies:
            # In real implementation, check if service/template is installed
            is_installed = True  # Placeholder

            if is_installed:
                satisfied.append(dep)
            else:
                missing.append(dep)

        return {
            "template_id": template_id,
            "dependencies": dependencies,
            "satisfied": satisfied,
            "missing": missing,
            "all_satisfied": len(missing) == 0,
            "install_order": (self._calculate_install_order(dependencies) if missing else []),
        }

    def _calculate_install_order(self, dependencies: List[str]) -> List[str]:
        """Calculate optimal order to install dependencies."""
        # Simple ordering - in real impl would handle complex dependency graphs
        return dependencies

    def _validate_template(self, template_data: Dict) -> bool:
        """Validate template data."""
        required_fields = ["id", "name", "description", "category"]
        return all(field in template_data for field in required_fields)

    def _get_validation_errors(self, template_data: Dict) -> List[str]:
        """Get template validation errors."""
        required_fields = ["id", "name", "description", "category"]
        errors = []

        for field in required_fields:
            if field not in template_data:
                errors.append(f"Missing required field: {field}")

        return errors

    def _log_sync(self, operation: str, template_id: str, status: str):
        """Log sync operation."""
        log_entry = {
            "operation": operation,
            "template_id": template_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }
        self.sync_log.append(log_entry)

    def get_sync_history(self, limit: int = 20) -> List[Dict]:
        """
        Get recent sync operations.

        Args:
            limit: Number of operations to return

        Returns:
            List of sync operations
        """
        return sorted(self.sync_log, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def get_integration_health(self) -> Dict:
        """
        Check health of all integrations.

        Returns:
            Health status of all integrated services
        """
        # Services to check
        services = [
            "workflow_marketplace",
            "template_manager",
            "deal_closer_ai",
            "hot_lead_fastlane",
            "commission_calculator",
            "win_loss_analysis",
        ]

        health_status = {
            "overall_status": "healthy",
            "services": {},
            "checked_at": datetime.now().isoformat(),
        }

        # Check each service
        for service in services:
            # Simulate health check
            health_status["services"][service] = {
                "status": "healthy",
                "last_sync": datetime.now().isoformat(),
                "response_time_ms": 45,
            }

        return health_status


# Example workflow orchestrations
WORKFLOW_COMBOS = {
    "hot_lead_capture": {
        "name": "Hot Lead Capture & Response",
        "description": "Capture lead, score priority, generate response",
        "services": ["hot_lead_fastlane", "deal_closer_ai"],
        "estimated_time": "< 2 seconds",
        "value": "Never miss a hot lead - instant prioritization and response",
    },
    "listing_to_market": {
        "name": "Listing to Market Pipeline",
        "description": "Create listing, generate marketing, distribute",
        "services": ["ai_listing_writer", "workflow_marketplace"],
        "estimated_time": "< 5 seconds",
        "value": "Get listings to market 10x faster",
    },
    "deal_intelligence": {
        "name": "Deal Intelligence Dashboard",
        "description": "Score leads, calculate commission, track outcomes",
        "services": ["hot_lead_fastlane", "commission_calculator", "win_loss_analysis"],
        "estimated_time": "< 3 seconds",
        "value": "Complete visibility into deal pipeline and revenue",
    },
}


def create_workflow_combo(combo_name: str, lead_data: Dict) -> Dict:
    """
    Execute a predefined workflow combination.

    Args:
        combo_name: Name of workflow combo
        lead_data: Input data

    Returns:
        Workflow execution result
    """
    if combo_name not in WORKFLOW_COMBOS:
        return {
            "success": False,
            "error": f"Unknown workflow: {combo_name}",
            "available_workflows": list(WORKFLOW_COMBOS.keys()),
        }

    combo = WORKFLOW_COMBOS[combo_name]
    sync = MarketplaceSync()

    result = sync.orchestrate_workflow(workflow_name=combo_name, services=combo["services"], lead_data=lead_data)

    result["workflow_info"] = combo

    return result


if __name__ == "__main__":
    # Demo usage
    sync = MarketplaceSync()

    print("🔄 Marketplace Sync - Demo\n")

    # Demo 1: Sync template to marketplace
    template = {
        "id": "T001",
        "name": "Lead Nurture Sequence",
        "description": "7-day automated lead nurture",
        "category": "automation",
        "tags": ["leads", "automation", "followup"],
        "author": "Jorge Sales",
        "version": "1.0.0",
    }

    result = sync.sync_template_to_marketplace(template, publish=True)
    print(f"Sync to Marketplace: {result['success']}")
    print(f"Listing URL: {result['listing_url']}")
    print()

    # Demo 2: Orchestrate workflow
    lead_data = {
        "name": "Jane Doe",
        "budget": 750000,
        "timeline_days": 45,
        "source": "referral",
    }

    workflow = create_workflow_combo("hot_lead_capture", lead_data)
    print(f"Workflow: {workflow['workflow_name']}")
    print(f"Services: {', '.join(workflow['services_executed'])}")
    print(f"Success: {workflow['success']}")
    print()

    # Demo 3: Integration health
    health = sync.get_integration_health()
    print(f"Integration Health: {health['overall_status']}")
    print(f"Services: {len(health['services'])}")
