"""CRM adapter layer -- vendor-agnostic CRM integration."""

from .hubspot_adapter import HubSpotAdapter
from .protocol import CRMContact, CRMProtocol

__all__ = ["CRMContact", "CRMProtocol", "HubSpotAdapter"]
