"""
MCP Server Entrypoint for EnterpriseHub.
Exposes the SkillRegistry as a Model Context Protocol (MCP) server.

Usage:
    python mcp_server.py
"""
import asyncio
from ghl_real_estate_ai.agent_system.skills.base import registry
# Import skill modules to trigger @skill registration
import ghl_real_estate_ai.agent_system.skills.codebase
import ghl_real_estate_ai.agent_system.skills.real_estate
import ghl_real_estate_ai.agent_system.skills.monitoring
import ghl_real_estate_ai.agent_system.skills.lead_intelligence
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

def main():
    """Run the MCP server."""
    logger.info("Starting EnterpriseHub MCP Server...")
    
    # The registry has already initialized FastMCP and registered tools
    # via the @skill decorators in the loaded modules.
    
    # We need to ensure skills are loaded. 
    # In a real app, you might import specific skill modules here.
    # from ghl_real_estate_ai.skills import coding, research, etc.
    
    try:
        # FastMCP.run() handles the stdio/sse connection
        registry.mcp.run() 
    except Exception as e:
        logger.error(f"MCP Server crashed: {e}")
        raise

if __name__ == "__main__":
    main()
