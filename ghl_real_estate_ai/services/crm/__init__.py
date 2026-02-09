"""CRM adapter layer -- vendor-agnostic CRM integration."""

from .ghl_adapter import GHLAdapter
from .hubspot_adapter import HubSpotAdapter
from .protocol import CRMContact, CRMProtocol

__all__ = ["CRMContact", "CRMProtocol", "GHLAdapter", "HubSpotAdapter"]
