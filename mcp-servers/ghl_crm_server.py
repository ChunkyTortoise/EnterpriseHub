#!/usr/bin/env python3
"""
GoHighLevel CRM MCP Server
Provides standardized MCP interface for GHL CRM operations
Replaces custom ghl_service.py with industry-standard MCP protocol
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime

# MCP Server framework (would use official MCP library in production)
class MCPServer:
    """Basic MCP server implementation for GHL CRM"""

    def __init__(self):
        self.capabilities = {
            "tools": True,
            "resources": False,
            "prompts": False,
            "logging": True
        }

        # Mock GHL client (would use actual GHL API in production)
        self.ghl_client = MockGHLClient()

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests"""

        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            if method == "initialize":
                return await self.handle_initialize(request_id, params)
            elif method == "tools/list":
                return await self.handle_list_tools(request_id)
            elif method == "tools/call":
                return await self.handle_call_tool(request_id, params)
            else:
                return self.error_response(request_id, "Unknown method", method)

        except Exception as e:
            return self.error_response(request_id, "Internal error", str(e))

    async def handle_initialize(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP initialization"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": self.capabilities,
                "serverInfo": {
                    "name": "ghl-crm-server",
                    "version": "1.0.0",
                    "description": "GoHighLevel CRM integration via MCP"
                }
            }
        }

    async def handle_list_tools(self, request_id: int) -> Dict[str, Any]:
        """List available GHL CRM tools"""
        tools = [
            {
                "name": "create_contact",
                "description": "Create a new contact in GHL CRM",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "first_name": {"type": "string", "description": "Contact first name"},
                        "last_name": {"type": "string", "description": "Contact last name"},
                        "email": {"type": "string", "description": "Contact email address"},
                        "phone": {"type": "string", "description": "Contact phone number"},
                        "custom_fields": {"type": "object", "description": "Custom field values"}
                    },
                    "required": ["first_name", "last_name"]
                }
            },

            {
                "name": "update_contact",
                "description": "Update an existing contact in GHL CRM",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "contact_id": {"type": "string", "description": "GHL contact ID"},
                        "first_name": {"type": "string"},
                        "last_name": {"type": "string"},
                        "email": {"type": "string"},
                        "phone": {"type": "string"},
                        "custom_fields": {"type": "object"}
                    },
                    "required": ["contact_id"]
                }
            },

            {
                "name": "get_contact",
                "description": "Retrieve contact information by ID",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "contact_id": {"type": "string", "description": "GHL contact ID"}
                    },
                    "required": ["contact_id"]
                }
            },

            {
                "name": "search_contacts",
                "description": "Search contacts by criteria",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Maximum results", "default": 20},
                        "filters": {"type": "object", "description": "Additional filters"}
                    },
                    "required": ["query"]
                }
            },

            {
                "name": "trigger_workflow",
                "description": "Trigger a GHL workflow for a contact",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "contact_id": {"type": "string", "description": "GHL contact ID"},
                        "workflow_id": {"type": "string", "description": "GHL workflow ID"},
                        "custom_data": {"type": "object", "description": "Custom workflow data"}
                    },
                    "required": ["contact_id", "workflow_id"]
                }
            },

            {
                "name": "set_custom_field",
                "description": "Set custom field value for a contact",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "contact_id": {"type": "string", "description": "GHL contact ID"},
                        "field_name": {"type": "string", "description": "Custom field name"},
                        "field_value": {"type": "string", "description": "Custom field value"}
                    },
                    "required": ["contact_id", "field_name", "field_value"]
                }
            }
        ]

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tools}
        }

    async def handle_call_tool(self, request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool execution requests"""

        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "create_contact":
            result = await self.create_contact(arguments)
        elif tool_name == "update_contact":
            result = await self.update_contact(arguments)
        elif tool_name == "get_contact":
            result = await self.get_contact(arguments)
        elif tool_name == "search_contacts":
            result = await self.search_contacts(arguments)
        elif tool_name == "trigger_workflow":
            result = await self.trigger_workflow(arguments)
        elif tool_name == "set_custom_field":
            result = await self.set_custom_field(arguments)
        else:
            return self.error_response(request_id, "Unknown tool", tool_name)

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    # GHL CRM tool implementations

    async def create_contact(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create new contact in GHL CRM"""
        contact_data = {
            "firstName": args["first_name"],
            "lastName": args["last_name"],
            "email": args.get("email"),
            "phone": args.get("phone"),
            "customFields": args.get("custom_fields", {})
        }

        # Call GHL API (mocked for demo)
        contact = await self.ghl_client.create_contact(contact_data)

        return {
            "success": True,
            "contact_id": contact["id"],
            "contact": contact,
            "message": f"Created contact: {args['first_name']} {args['last_name']}"
        }

    async def update_contact(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing contact in GHL CRM"""
        contact_id = args["contact_id"]

        update_data = {}
        if "first_name" in args:
            update_data["firstName"] = args["first_name"]
        if "last_name" in args:
            update_data["lastName"] = args["last_name"]
        if "email" in args:
            update_data["email"] = args["email"]
        if "phone" in args:
            update_data["phone"] = args["phone"]
        if "custom_fields" in args:
            update_data["customFields"] = args["custom_fields"]

        # Call GHL API (mocked for demo)
        contact = await self.ghl_client.update_contact(contact_id, update_data)

        return {
            "success": True,
            "contact_id": contact_id,
            "contact": contact,
            "message": f"Updated contact: {contact_id}"
        }

    async def get_contact(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve contact by ID"""
        contact_id = args["contact_id"]

        # Call GHL API (mocked for demo)
        contact = await self.ghl_client.get_contact(contact_id)

        if not contact:
            return {
                "success": False,
                "message": f"Contact not found: {contact_id}"
            }

        return {
            "success": True,
            "contact": contact
        }

    async def search_contacts(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search contacts by query"""
        query = args["query"]
        limit = args.get("limit", 20)
        filters = args.get("filters", {})

        # Call GHL API (mocked for demo)
        contacts = await self.ghl_client.search_contacts(query, limit, filters)

        return {
            "success": True,
            "query": query,
            "count": len(contacts),
            "contacts": contacts
        }

    async def trigger_workflow(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger GHL workflow"""
        contact_id = args["contact_id"]
        workflow_id = args["workflow_id"]
        custom_data = args.get("custom_data", {})

        # Call GHL API (mocked for demo)
        result = await self.ghl_client.trigger_workflow(contact_id, workflow_id, custom_data)

        return {
            "success": True,
            "workflow_triggered": True,
            "workflow_id": workflow_id,
            "contact_id": contact_id,
            "execution_id": result.get("execution_id")
        }

    async def set_custom_field(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Set custom field for contact"""
        contact_id = args["contact_id"]
        field_name = args["field_name"]
        field_value = args["field_value"]

        # Call GHL API (mocked for demo)
        result = await self.ghl_client.set_custom_field(contact_id, field_name, field_value)

        return {
            "success": True,
            "contact_id": contact_id,
            "field_name": field_name,
            "field_value": field_value,
            "updated": True
        }

    def error_response(self, request_id: int, error_type: str, details: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32000,
                "message": error_type,
                "data": details
            }
        }

class MockGHLClient:
    """Mock GHL client for demonstration (replace with actual GHL API client)"""

    def __init__(self):
        self.contacts = {}
        self.contact_counter = 1

    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock contact creation"""
        contact_id = f"contact_{self.contact_counter:05d}"
        self.contact_counter += 1

        contact = {
            "id": contact_id,
            "firstName": contact_data.get("firstName"),
            "lastName": contact_data.get("lastName"),
            "email": contact_data.get("email"),
            "phone": contact_data.get("phone"),
            "customFields": contact_data.get("customFields", {}),
            "created": datetime.now().isoformat(),
            "updated": datetime.now().isoformat()
        }

        self.contacts[contact_id] = contact
        return contact

    async def update_contact(self, contact_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock contact update"""
        if contact_id not in self.contacts:
            raise Exception(f"Contact not found: {contact_id}")

        contact = self.contacts[contact_id]
        contact.update(update_data)
        contact["updated"] = datetime.now().isoformat()

        return contact

    async def get_contact(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Mock contact retrieval"""
        return self.contacts.get(contact_id)

    async def search_contacts(self, query: str, limit: int, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Mock contact search"""
        results = []
        query_lower = query.lower()

        for contact in self.contacts.values():
            # Simple text search across name and email
            searchable_text = f"{contact.get('firstName', '')} {contact.get('lastName', '')} {contact.get('email', '')}".lower()

            if query_lower in searchable_text:
                results.append(contact)

                if len(results) >= limit:
                    break

        return results

    async def trigger_workflow(self, contact_id: str, workflow_id: str, custom_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock workflow trigger"""
        return {
            "execution_id": f"exec_{int(datetime.now().timestamp())}",
            "status": "triggered",
            "contact_id": contact_id,
            "workflow_id": workflow_id
        }

    async def set_custom_field(self, contact_id: str, field_name: str, field_value: str) -> Dict[str, Any]:
        """Mock custom field setting"""
        if contact_id not in self.contacts:
            raise Exception(f"Contact not found: {contact_id}")

        contact = self.contacts[contact_id]
        if "customFields" not in contact:
            contact["customFields"] = {}

        contact["customFields"][field_name] = field_value
        contact["updated"] = datetime.now().isoformat()

        return {"success": True}

async def main():
    """Run GHL CRM MCP server"""
    server = MCPServer()

    # Handle stdio communication (MCP standard)
    while True:
        try:
            # Read request from stdin
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break

            request = json.loads(line.strip())

            # Process request
            response = await server.handle_request(request)

            # Send response to stdout
            print(json.dumps(response))
            sys.stdout.flush()

        except json.JSONDecodeError as e:
            # Invalid JSON request
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error",
                    "data": str(e)
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

        except Exception as e:
            # Unexpected error
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32000,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())