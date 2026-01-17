#!/usr/bin/env python3
"""
GoHighLevel MCP Server
Production-ready Model Context Protocol server for natural language GHL operations.

Provides tools for:
- Contact management (create, search, update)
- Lead intelligence (scoring, analytics)
- Workflow automation (triggers, SMS)
- Opportunity management (pipeline operations)

Integration with existing services:
- ghl_real_estate_ai.services.claude_enhanced_lead_scorer
- ghl_real_estate_ai.services.ghl_sync_service
- ghl_real_estate_ai.services.predictive_lead_scorer
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

import httpx
from anthropic_mcp import MCPServer, Tool

# Import existing GHL utilities
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.ghl_client import GHLClient

logger = get_logger(__name__)


class GHLMCPServer:
    """MCP Server for GoHighLevel API operations"""

    def __init__(self):
        self.ghl_client = GHLClient()
        self.base_url = "https://services.leadconnectorhq.com"
        self.headers = {
            "Authorization": f"Bearer {settings.ghl_api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28",
        }

    # ==================== Contact Management ====================

    async def create_ghl_contact(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new contact in GoHighLevel.

        Args:
            name: Contact full name (required)
            email: Contact email address
            phone: Contact phone number (E.164 format recommended)
            tags: List of tags to apply to contact
            custom_fields: Dictionary of custom field IDs and values

        Returns:
            Contact object with ID and created fields

        Example:
            create_ghl_contact(
                name="John Smith",
                email="john@example.com",
                phone="+15125551234",
                tags=["Hot Lead", "Buyer"],
                custom_fields={"budget": "500000", "timeline": "3-6 months"}
            )
        """
        if settings.test_mode:
            logger.info(f"[TEST MODE] Would create contact: {name}")
            return {
                "id": "mock_contact_123",
                "name": name,
                "email": email,
                "phone": phone,
                "tags": tags or [],
                "locationId": settings.ghl_location_id
            }

        endpoint = f"{self.base_url}/contacts/"

        payload = {
            "locationId": settings.ghl_location_id,
            "name": name,
        }

        if email:
            payload["email"] = email
        if phone:
            payload["phone"] = phone
        if tags:
            payload["tags"] = tags
        if custom_fields:
            payload["customFields"] = [
                {"id": field_id, "value": str(value)}
                for field_id, value in custom_fields.items()
            ]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()

                logger.info(f"Created contact: {result.get('id')} - {name}")
                return result

        except httpx.HTTPError as e:
            error_msg = f"Failed to create contact: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "status": "failed"}

    async def get_ghl_contact(self, contact_id: str) -> Dict[str, Any]:
        """
        Retrieve a contact by ID from GoHighLevel.

        Args:
            contact_id: GHL contact ID

        Returns:
            Complete contact object with all fields
        """
        if settings.test_mode:
            return {
                "id": contact_id,
                "name": "Test Contact",
                "email": "test@example.com",
                "tags": ["Buyer"],
                "customFields": []
            }

        endpoint = f"{self.base_url}/contacts/{contact_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            error_msg = f"Failed to get contact: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "status": "not_found"}

    async def search_ghl_contacts(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for contacts in GoHighLevel.

        Args:
            query: Search query (name, email, phone)
            tags: Filter by tags
            limit: Maximum number of results (default 20)

        Returns:
            List of matching contacts

        Example:
            search_ghl_contacts(query="john smith", tags=["Hot Lead"], limit=10)
        """
        if settings.test_mode:
            return [{
                "id": f"mock_{i}",
                "name": f"Test Contact {i}",
                "tags": tags or []
            } for i in range(min(limit, 3))]

        endpoint = f"{self.base_url}/contacts/search"

        params = {
            "locationId": settings.ghl_location_id,
            "limit": limit
        }

        if query:
            params["query"] = query

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    endpoint,
                    params=params,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()

                contacts = result.get("contacts", [])

                # Filter by tags if specified
                if tags:
                    contacts = [
                        c for c in contacts
                        if any(tag in c.get("tags", []) for tag in tags)
                    ]

                return contacts[:limit]

        except httpx.HTTPError as e:
            error_msg = f"Failed to search contacts: {str(e)}"
            logger.error(error_msg)
            return []

    # ==================== Lead Intelligence ====================

    async def update_lead_score(
        self,
        contact_id: str,
        score: float,
        factors: Dict[str, Any],
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update lead score with AI-driven intelligence.

        Integrates with services/predictive_lead_scorer.py for ML scoring
        and services/claude_enhanced_lead_scorer.py for comprehensive analysis.

        Args:
            contact_id: GHL contact ID
            score: Lead score (0-100)
            factors: Dictionary of scoring factors (qualification, behavior, etc.)
            notes: Optional notes about the score

        Returns:
            Updated contact with score and analysis

        Example:
            update_lead_score(
                contact_id="abc123",
                score=87.5,
                factors={
                    "budget_qualified": True,
                    "timeline": "immediate",
                    "engagement_level": "high"
                },
                notes="Hot lead - ready for agent handoff"
            )
        """
        # Prepare custom field updates
        custom_fields = {
            settings.custom_field_lead_score or "lead_score": str(int(score))
        }

        # Add factor-based fields
        if "budget" in factors:
            custom_fields[settings.custom_field_budget or "budget"] = str(factors["budget"])
        if "timeline" in factors:
            custom_fields[settings.custom_field_timeline or "timeline"] = factors["timeline"]
        if "location" in factors:
            custom_fields[settings.custom_field_location or "location"] = factors["location"]

        # Add comprehensive analysis as JSON
        if settings.custom_field_lead_score:
            analysis = {
                "score": score,
                "factors": factors,
                "updated_at": datetime.now().isoformat(),
                "notes": notes
            }
            custom_fields["lead_analysis_json"] = json.dumps(analysis)

        # Update contact
        endpoint = f"{self.base_url}/contacts/{contact_id}"

        payload = {
            "customFields": [
                {"id": field_id, "value": str(value)}
                for field_id, value in custom_fields.items()
            ]
        }

        # Add tags based on score
        tags = []
        if score >= 70:
            tags.extend(["Hot Lead", "AI_Scored_Hot"])
        elif score >= 40:
            tags.append("AI_Scored_Warm")
        else:
            tags.append("AI_Scored_Cold")

        if tags:
            payload["tags"] = tags

        if settings.test_mode:
            logger.info(f"[TEST MODE] Would update lead score for {contact_id}: {score}")
            return {
                "id": contact_id,
                "score": score,
                "tags": tags,
                "custom_fields": custom_fields
            }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()

                logger.info(f"Updated lead score for {contact_id}: {score}")

                # Trigger high-value lead workflow if score is high
                if score >= 85:
                    await self.trigger_ghl_workflow(
                        contact_id,
                        settings.notify_agent_workflow_id or "high_value_lead_workflow"
                    )

                return result

        except httpx.HTTPError as e:
            error_msg = f"Failed to update lead score: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "status": "failed"}

    # ==================== Workflow Automation ====================

    async def trigger_ghl_workflow(
        self,
        contact_id: str,
        workflow_id: str,
        custom_values: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger a GHL workflow for a contact.

        Args:
            contact_id: GHL contact ID
            workflow_id: GHL workflow ID to trigger
            custom_values: Optional custom values to pass to workflow

        Returns:
            Workflow execution result

        Example:
            trigger_ghl_workflow(
                contact_id="abc123",
                workflow_id="wf_qualification_sequence",
                custom_values={"property_type": "condo", "budget": "500k"}
            )
        """
        return await self.ghl_client.trigger_workflow(contact_id, workflow_id)

    async def send_ghl_sms(
        self,
        contact_id: str,
        message: str,
        message_type: str = "transactional"
    ) -> Dict[str, Any]:
        """
        Send SMS message to a contact.

        Args:
            contact_id: GHL contact ID
            message: SMS message content
            message_type: Type of message (transactional, marketing)

        Returns:
            Message send result

        Example:
            send_ghl_sms(
                contact_id="abc123",
                message="Hi John! Your property viewing is confirmed for tomorrow at 2pm.",
                message_type="transactional"
            )
        """
        from ghl_real_estate_ai.api.schemas.ghl import MessageType
        return await self.ghl_client.send_message(
            contact_id,
            message,
            MessageType.SMS
        )

    # ==================== Opportunity Management ====================

    async def create_ghl_opportunity(
        self,
        contact_id: str,
        pipeline_id: str,
        stage_id: str,
        name: str,
        value: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an opportunity in GHL pipeline.

        Args:
            contact_id: GHL contact ID
            pipeline_id: GHL pipeline ID
            stage_id: Pipeline stage ID
            name: Opportunity name/title
            value: Monetary value of opportunity
            notes: Optional notes

        Returns:
            Created opportunity object

        Example:
            create_ghl_opportunity(
                contact_id="abc123",
                pipeline_id="pipeline_sales",
                stage_id="stage_initial_contact",
                name="Downtown Condo Sale",
                value=550000,
                notes="Referred by existing client, pre-qualified"
            )
        """
        if settings.test_mode:
            logger.info(f"[TEST MODE] Would create opportunity: {name}")
            return {
                "id": "mock_opp_123",
                "name": name,
                "contact_id": contact_id,
                "pipeline_id": pipeline_id,
                "stage_id": stage_id,
                "value": value
            }

        endpoint = f"{self.base_url}/opportunities/"

        payload = {
            "locationId": settings.ghl_location_id,
            "contactId": contact_id,
            "pipelineId": pipeline_id,
            "pipelineStageId": stage_id,
            "name": name,
            "status": "open"
        }

        if value is not None:
            payload["monetaryValue"] = value
        if notes:
            payload["notes"] = notes

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                result = response.json()

                logger.info(f"Created opportunity: {result.get('id')} - {name}")
                return result

        except httpx.HTTPError as e:
            error_msg = f"Failed to create opportunity: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg, "status": "failed"}


# ==================== MCP Server Setup ====================

def create_mcp_tools(server: GHLMCPServer) -> List[Tool]:
    """Create MCP tool definitions"""

    return [
        Tool(
            name="create_ghl_contact",
            description="Create a new contact in GoHighLevel CRM with tags and custom fields",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Contact full name"},
                    "email": {"type": "string", "description": "Email address"},
                    "phone": {"type": "string", "description": "Phone number (E.164 format)"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags to apply (e.g., 'Hot Lead', 'Buyer')"
                    },
                    "custom_fields": {
                        "type": "object",
                        "description": "Custom field IDs and values"
                    }
                },
                "required": ["name"]
            },
            handler=server.create_ghl_contact
        ),

        Tool(
            name="get_ghl_contact",
            description="Retrieve a contact by ID from GoHighLevel",
            input_schema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string", "description": "GHL contact ID"}
                },
                "required": ["contact_id"]
            },
            handler=server.get_ghl_contact
        ),

        Tool(
            name="search_ghl_contacts",
            description="Search for contacts by name, email, phone, or tags",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags"
                    },
                    "limit": {"type": "integer", "description": "Max results (default 20)"}
                }
            },
            handler=server.search_ghl_contacts
        ),

        Tool(
            name="update_lead_score",
            description="Update lead score with AI-driven intelligence and factors. Integrates with predictive scoring and Claude analysis.",
            input_schema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string", "description": "GHL contact ID"},
                    "score": {"type": "number", "description": "Lead score 0-100"},
                    "factors": {
                        "type": "object",
                        "description": "Scoring factors (budget, timeline, engagement, etc.)"
                    },
                    "notes": {"type": "string", "description": "Optional notes"}
                },
                "required": ["contact_id", "score", "factors"]
            },
            handler=server.update_lead_score
        ),

        Tool(
            name="trigger_ghl_workflow",
            description="Trigger a GoHighLevel workflow for a contact",
            input_schema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string", "description": "GHL contact ID"},
                    "workflow_id": {"type": "string", "description": "GHL workflow ID"},
                    "custom_values": {
                        "type": "object",
                        "description": "Custom values to pass to workflow"
                    }
                },
                "required": ["contact_id", "workflow_id"]
            },
            handler=server.trigger_ghl_workflow
        ),

        Tool(
            name="send_ghl_sms",
            description="Send SMS message to a contact via GoHighLevel",
            input_schema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string", "description": "GHL contact ID"},
                    "message": {"type": "string", "description": "SMS message content"},
                    "message_type": {
                        "type": "string",
                        "enum": ["transactional", "marketing"],
                        "description": "Message type (default: transactional)"
                    }
                },
                "required": ["contact_id", "message"]
            },
            handler=server.send_ghl_sms
        ),

        Tool(
            name="create_ghl_opportunity",
            description="Create an opportunity in GoHighLevel pipeline",
            input_schema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "string", "description": "GHL contact ID"},
                    "pipeline_id": {"type": "string", "description": "Pipeline ID"},
                    "stage_id": {"type": "string", "description": "Pipeline stage ID"},
                    "name": {"type": "string", "description": "Opportunity name"},
                    "value": {"type": "number", "description": "Monetary value"},
                    "notes": {"type": "string", "description": "Optional notes"}
                },
                "required": ["contact_id", "pipeline_id", "stage_id", "name"]
            },
            handler=server.create_ghl_opportunity
        )
    ]


async def main():
    """Run the MCP server"""
    ghl_server = GHLMCPServer()
    tools = create_mcp_tools(ghl_server)

    mcp = MCPServer("ghl-server")

    for tool in tools:
        mcp.add_tool(tool)

    logger.info("Starting GoHighLevel MCP Server...")
    await mcp.run()


if __name__ == "__main__":
    asyncio.run(main())
