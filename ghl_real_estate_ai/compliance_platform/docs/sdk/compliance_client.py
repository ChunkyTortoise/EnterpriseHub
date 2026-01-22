"""
Enterprise AI Compliance Platform - Python SDK

A Pythonic wrapper for the Compliance API, providing easy integration for:
- AI Model Registration
- Compliance Assessments
- Violation Tracking
- Regulatory Reporting
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import httpx

logger = logging.getLogger(__name__)

class ComplianceAPIError(Exception):
    """Base exception for Compliance SDK errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response

class ComplianceClient:
    """
    Client for interacting with the AI Compliance Platform API.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize the Compliance Client.

        Args:
            base_url: The base URL of the Compliance API.
            api_key: Optional API key for authentication.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url.rstrip("/")
        self.api_v1 = f"{self.base_url}/api/v1/compliance"
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if api_key:
            self.headers["X-API-Key"] = api_key

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Internal helper for making async HTTP requests."""
        url = f"{self.api_v1}/{path.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(method, url, headers=self.headers, **kwargs)
                
                if response.status_code >= 400:
                    try:
                        error_detail = response.json().get("detail", response.text)
                    except Exception:
                        error_detail = response.text
                        
                    raise ComplianceAPIError(
                        f"API request failed with status {response.status_code}: {error_detail}",
                        status_code=response.status_code,
                        response=response.text
                    )
                
                return response.json()
            except httpx.RequestError as e:
                raise ComplianceAPIError(f"Network error occurred: {str(e)}")

    # =========================================================================
    # Model Management
    # =========================================================================

    async def register_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new AI model for compliance tracking.

        Args:
            model_data: Dictionary containing model details (name, version, etc.)
        """
        return await self._request("POST", "/models/register", json=model_data)

    async def list_models(
        self,
        skip: int = 0,
        limit: int = 100,
        risk_level: Optional[str] = None,
        compliance_status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all registered models with filtering."""
        params = {"skip": skip, "limit": limit}
        if risk_level:
            params["risk_level"] = risk_level
        if compliance_status:
            params["compliance_status"] = compliance_status
            
        return await self._request("GET", "/models", params=params)

    async def get_model(self, model_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific model."""
        return await self._request("GET", f"/models/{model_id}")

    # =========================================================================
    # Compliance Assessments
    # =========================================================================

    async def assess_model(
        self,
        model_id: str,
        async_mode: bool = False,
        check_types: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trigger a compliance assessment for a model.

        Args:
            model_id: ID of the model to assess.
            async_mode: Whether to run the assessment in the background.
            check_types: List of checks to perform (e.g., ["full"]).
            context: Additional context for the assessment.
        """
        payload = {
            "model_id": model_id,
            "async_mode": async_mode,
            "check_types": check_types or ["full"],
            "context": context
        }
        return await self._request("POST", "/assess", json=payload)

    async def get_assessment_status(self, assessment_id: str) -> Dict[str, Any]:
        """Get status of a background assessment."""
        return await self._request("GET", f"/assess/{assessment_id}")

    # =========================================================================
    # Violation Tracking
    # =========================================================================

    async def get_violations(self, model_id: str, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get active violations for a model."""
        params = {}
        if severity:
            params["severity"] = severity
        return await self._request("GET", f"/models/{model_id}/violations", params=params)

    async def acknowledge_violation(
        self,
        model_id: str,
        violation_id: str,
        acknowledged_by: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Acknowledge a specific violation."""
        payload = {"acknowledged_by": acknowledged_by, "notes": notes}
        return await self._request(
            "POST",
            f"/models/{model_id}/violations/{violation_id}/acknowledge",
            json=payload
        )

    # =========================================================================
    # Reporting
    # =========================================================================

    async def generate_report(
        self,
        report_type: str = "executive",
        model_id: Optional[str] = None,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Trigger report generation."""
        payload = {
            "report_type": report_type,
            "model_id": model_id,
            "period_days": period_days
        }
        return await self._request("POST", "/reports/generate", json=payload)

    async def get_report(self, report_id: str) -> Dict[str, Any]:
        """Fetch a generated report."""
        return await self._request("GET", f"/reports/{report_id}")

    # =========================================================================
    # System
    # =========================================================================

    async def check_health(self) -> Dict[str, Any]:
        """Check system health and database connectivity."""
        return await self._request("GET", "/health")
