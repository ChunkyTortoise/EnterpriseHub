"""
GHL Integration Handlers

Bot-specific webhook handlers for Lead, Seller, and Buyer bots.
"""

from ghl_integration.handlers.buyer_handlers import get_handler as get_buyer_handler
from ghl_integration.handlers.lead_handlers import get_handler as get_lead_handler
from ghl_integration.handlers.seller_handlers import get_handler as get_seller_handler

__all__ = [
    "get_lead_handler",
    "get_seller_handler", 
    "get_buyer_handler",
]
