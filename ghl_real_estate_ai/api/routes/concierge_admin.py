"""
Concierge Admin API Routes
Provides tenant management and hot-reload endpoints for the Claude Concierge system.

# TODO: Add admin role check middleware once auth system supports it.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ghl_real_estate_ai.config.concierge_config_loader import _loader, get_concierge_config
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class TenantSummary(BaseModel):
    tenant_id: str
    domain: str
    client_name: str
    agent_count: int


class AgentInfo(BaseModel):
    name: str
    agent_type: str
    invoke_pattern: str


class TenantDetail(BaseModel):
    tenant_id: str
    domain: str
    client_name: str
    business_model: str
    market_context: str
    client_style: str
    agent_count: int
    agents: List[AgentInfo]
    compliance_requirements: List[str]
    platform_features: Dict[str, List[str]]


class ReloadResponse(BaseModel):
    tenant_id: str
    status: str
    domain: str
    client_name: str
    agent_count: int


class DeleteSessionResponse(BaseModel):
    tenant_id: str
    session_id: str
    deleted: bool


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/tenants", response_model=List[TenantSummary])
async def list_tenants():
    """List all cached tenant configs."""
    results = []
    for tenant_id, cfg in _loader._cache.items():
        results.append(
            TenantSummary(
                tenant_id=cfg.tenant_id,
                domain=cfg.domain,
                client_name=cfg.client_name,
                agent_count=len(cfg.available_agents),
            )
        )
    return results


@router.get("/tenants/{tenant_id}", response_model=TenantDetail)
async def get_tenant(tenant_id: str):
    """Return full config for a specific tenant."""
    if tenant_id not in _loader._cache:
        raise HTTPException(status_code=404, detail=f"Tenant '{tenant_id}' not found in cache")
    cfg = _loader._cache[tenant_id]
    return TenantDetail(
        tenant_id=cfg.tenant_id,
        domain=cfg.domain,
        client_name=cfg.client_name,
        business_model=cfg.business_model,
        market_context=cfg.market_context,
        client_style=cfg.client_style,
        agent_count=len(cfg.available_agents),
        agents=[
            AgentInfo(name=a.name, agent_type=a.agent_type, invoke_pattern=a.invoke_pattern)
            for a in cfg.available_agents
        ],
        compliance_requirements=cfg.compliance_requirements,
        platform_features=cfg.platform_features,
    )


@router.post("/tenants/{tenant_id}/reload", response_model=ReloadResponse)
async def reload_tenant(tenant_id: str):
    """Evict cache and reload tenant config from disk."""
    try:
        _loader.reload(tenant_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    cfg = _loader._cache[tenant_id]
    return ReloadResponse(
        tenant_id=cfg.tenant_id,
        status="reloaded",
        domain=cfg.domain,
        client_name=cfg.client_name,
        agent_count=len(cfg.available_agents),
    )


@router.delete("/sessions/{tenant_id}/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(tenant_id: str, session_id: str):
    """Delete a concierge session from cache."""
    cache = get_cache_service()
    key = f"concierge:{tenant_id}:session:{session_id}"
    deleted = await cache.delete(key)
    return DeleteSessionResponse(
        tenant_id=tenant_id,
        session_id=session_id,
        deleted=deleted,
    )
