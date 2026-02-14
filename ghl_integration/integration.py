"""
GHL Integration Module - Integration Points

This module provides integration points for connecting the GHL webhook
infrastructure to the existing EnterpriseHub FastAPI applications.

Usage:
    from ghl_integration import ghl_router
    app.include_router(ghl_router, prefix="/ghl")
"""

import logging
from typing import Optional

from fastapi import FastAPI

from .router import router as ghl_router, get_ghl_router, _ghl_router
from .retry_manager import get_retry_manager, WebhookRetryManager
from .handlers import lead_handlers, seller_handlers, buyer_handlers

logger = logging.getLogger(__name__)


async def initialize_ghl_integration(app: Optional[FastAPI] = None) -> dict:
    """
    Initialize the GHL integration module.
    
    This function:
    1. Registers all webhook handlers
    2. Initializes the retry manager
    3. Optionally mounts the router to a FastAPI app
    
    Args:
        app: Optional FastAPI app to mount router to
        
    Returns:
        dict with initialization status
    """
    try:
        logger.info("Initializing GHL Integration...")
        
        # Register lead bot handlers
        _register_lead_handlers()
        logger.info("Lead bot handlers registered")
        
        # Register seller bot handlers
        _register_seller_handlers()
        logger.info("Seller bot handlers registered")
        
        # Register buyer bot handlers
        _register_buyer_handlers()
        logger.info("Buyer bot handlers registered")
        
        # Initialize retry manager
        retry_manager = await get_retry_manager()
        logger.info("Retry manager initialized")
        
        # Mount router if app provided
        if app:
            app.include_router(ghl_router)
            logger.info("GHL router mounted to FastAPI app")
        
        return {
            "success": True,
            "message": "GHL integration initialized successfully",
            "handlers_registered": {
                "lead": len(lead_handlers._handlers),
                "seller": len(seller_handlers._handlers),
                "buyer": len(buyer_handlers._handlers),
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize GHL integration: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def _register_lead_handlers():
    """Register all lead bot handlers with the router"""
    router = get_ghl_router()
    
    # Map event types to handlers
    router.register_handler("lead", "contact.create", lead_handlers.handle_new_lead)
    router.register_handler("lead", "conversation.message.created", lead_handlers.handle_lead_response)
    router.register_handler("lead", "contact.update", lead_handlers.handle_lead_update)
    
    logger.debug(f"Registered {len(lead_handlers._handlers)} lead handlers")


def _register_seller_handlers():
    """Register all seller bot handlers with the router"""
    router = get_ghl_router()
    
    router.register_handler("seller", "contact.create", seller_handlers.handle_seller_inquiry)
    router.register_handler("seller", "opportunity.create", seller_handlers.handle_listing_created)
    router.register_handler("seller", "conversation.message.created", seller_handlers.handle_seller_response)
    
    logger.debug(f"Registered {len(seller_handlers._handlers)} seller handlers")


def _register_buyer_handlers():
    """Register all buyer bot handlers with the router"""
    router = get_ghl_router()
    
    router.register_handler("buyer", "contact.create", buyer_handlers.handle_buyer_inquiry)
    router.register_handler("buyer", "conversation.message.created", buyer_handlers.handle_buyer_response)
    router.register_handler("buyer", "pipeline.stage.changed", buyer_handlers.handle_pipeline_change)
    
    logger.debug(f"Registered {len(buyer_handlers._handlers)} buyer handlers")


async def shutdown_ghl_integration():
    """
    Shutdown the GHL integration module.
    
    Cleans up resources and stops background workers.
    """
    try:
        logger.info("Shutting down GHL Integration...")
        
        retry_manager = await get_retry_manager()
        await retry_manager.shutdown()
        
        logger.info("GHL integration shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during GHL integration shutdown: {e}")


def mount_to_app(app: FastAPI, prefix: str = "/ghl"):
    """
    Mount GHL webhook router to a FastAPI application.
    
    Args:
        app: FastAPI application
        prefix: URL prefix for webhook endpoints (default: /ghl)
    """
    app.include_router(ghl_router, prefix=prefix)
    logger.info(f"GHL webhook router mounted at {prefix}")


# Environment configuration helpers
def verify_environment() -> dict:
    """
    Verify that all required environment variables are set.
    
    Returns:
        dict with verification results
    """
    import os
    
    required_vars = [
        "GHL_API_KEY",
        "GHL_LOCATION_ID",
    ]
    
    optional_vars = [
        "GHL_WEBHOOK_SECRET",
        "GHL_SELLER_PIPELINE_IDS",
        "GHL_BUYER_PIPELINE_IDS",
    ]
    
    results = {
        "required": {},
        "optional": {},
        "missing_required": [],
        "ready": True,
    }
    
    for var in required_vars:
        value = os.getenv(var)
        results["required"][var] = bool(value)
        if not value:
            results["missing_required"].append(var)
            results["ready"] = False
    
    for var in optional_vars:
        value = os.getenv(var)
        results["optional"][var] = bool(value)
    
    return results


def get_webhook_urls(base_url: str) -> dict:
    """
    Generate webhook URLs for GHL configuration.
    
    Args:
        base_url: Base URL of the application (e.g., https://api.example.com)
        
    Returns:
        dict with webhook URLs for each bot type
    """
    return {
        "lead_bot": {
            "new_lead": f"{base_url}/ghl/webhook/lead/new-lead",
            "lead_response": f"{base_url}/ghl/webhook/lead/lead-response",
            "lead_update": f"{base_url}/ghl/webhook/lead/lead-update",
        },
        "seller_bot": {
            "seller_inquiry": f"{base_url}/ghl/webhook/seller/seller-inquiry",
            "listing_created": f"{base_url}/ghl/webhook/seller/listing-created",
            "seller_response": f"{base_url}/ghl/webhook/seller/seller-response",
        },
        "buyer_bot": {
            "buyer_inquiry": f"{base_url}/ghl/webhook/buyer/buyer-inquiry",
            "buyer_response": f"{base_url}/ghl/webhook/buyer/buyer-response",
            "pipeline_change": f"{base_url}/ghl/webhook/buyer/pipeline-change",
        },
    }


# FastAPI lifespan helper (for use with FastAPI 0.100+)
async def lifespan_integration(app: FastAPI):
    """
    FastAPI lifespan context manager for GHL integration.
    
    Usage:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            async with lifespan_integration(app):
                yield
                
        app = FastAPI(lifespan=lifespan)
    """
    result = await initialize_ghl_integration(app)
    if not result.get("success"):
        logger.error(f"GHL integration failed to initialize: {result.get('error')}")
    
    try:
        yield
    finally:
        await shutdown_ghl_integration()
