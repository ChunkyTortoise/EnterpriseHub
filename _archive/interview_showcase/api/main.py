from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    import redis.asyncio as redis
except Exception:  # pragma: no cover
    redis = None


# -----------------------------
# Request/Response Models
# -----------------------------


class DemoMessageRequest(BaseModel):
    tenant_id: str = Field(min_length=2)
    user_id: str = Field(min_length=2)
    message: str = Field(min_length=1)
    channel: str = Field(default="web")
    requested_tenant_id: Optional[str] = None


class HandoffResult(BaseModel):
    source_bot: str
    target_bot: Optional[str] = None
    executed: bool
    prevented_loop: bool
    reason: Optional[str] = None


class DemoMessageResponse(BaseModel):
    tenant_id: str
    user_id: str
    language: str
    task_type: str
    response_text: str
    from_cache: bool
    latency_ms: float
    handoff: HandoffResult
    approval_required: bool = False
    approval_id: Optional[str] = None
    action_executed: bool = True


class ScenarioResponse(BaseModel):
    scenario: str
    steps: List[DemoMessageResponse]


class EventRecord(BaseModel):
    timestamp: str
    type: str
    tenant_id: str
    payload: Dict[str, Any]


class ApprovalItem(BaseModel):
    approval_id: str
    tenant_id: str
    user_id: str
    task_type: str
    message: str
    status: str
    created_at: str
    decided_at: Optional[str] = None
    decision_reason: Optional[str] = None


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(description="approve or reject")
    reason: Optional[str] = None


class MetricsResponse(BaseModel):
    total_requests: int
    cache_hits: int
    cache_misses: int
    cache_hit_rate: float
    blocked_cross_tenant: int
    handoffs_executed: int
    prevented_loops: int
    approvals_created: int
    approvals_approved: int
    approvals_rejected: int
    approvals_pending: int
    p50_latency_ms: float
    p95_latency_ms: float
    estimated_cost_savings_percent: float


# -----------------------------
# State
# -----------------------------


@dataclass
class HandoffLog:
    source_bot: str
    target_bot: str
    ts: float


class ShowcaseState:
    def __init__(self) -> None:
        self.events: deque[Dict[str, Any]] = deque(maxlen=1000)
        self.user_current_bot: Dict[str, str] = {}
        self.user_handoffs: Dict[str, List[HandoffLog]] = {}
        self.approvals: Dict[str, Dict[str, Any]] = {}
        self.mem_cache: Dict[str, Dict[str, Any]] = {}
        self.latencies_ms: List[float] = []

        self.metrics: Dict[str, float] = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "blocked_cross_tenant": 0,
            "handoffs_executed": 0,
            "prevented_loops": 0,
            "approvals_created": 0,
            "approvals_approved": 0,
            "approvals_rejected": 0,
            "cost_without_cache": 0.0,
            "actual_cost": 0.0,
        }

        self.redis_client = None

    async def connect_redis(self) -> None:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        if redis is None:
            return
        try:
            self.redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
            await self.redis_client.ping()
        except Exception:
            self.redis_client = None

    async def cache_get(self, key: str) -> Optional[Dict[str, Any]]:
        now = time.time()

        if self.redis_client:
            raw = await self.redis_client.get(key)
            if raw:
                return json.loads(raw)
            return None

        item = self.mem_cache.get(key)
        if not item:
            return None
        if item["expires_at"] < now:
            self.mem_cache.pop(key, None)
            return None
        return item["value"]

    async def cache_set(self, key: str, value: Dict[str, Any], ttl_seconds: int = 3600) -> None:
        if self.redis_client:
            await self.redis_client.set(key, json.dumps(value), ex=ttl_seconds)
            return

        self.mem_cache[key] = {"value": value, "expires_at": time.time() + ttl_seconds}


state = ShowcaseState()


# -----------------------------
# App
# -----------------------------


app = FastAPI(title="Interview Showcase API", version="1.0.0")


@app.on_event("startup")
async def startup_event() -> None:
    await state.connect_redis()


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_event(event_type: str, tenant_id: str, payload: Dict[str, Any]) -> None:
    state.events.append(
        {
            "timestamp": iso_now(),
            "type": event_type,
            "tenant_id": tenant_id,
            "payload": payload,
        }
    )


def detect_language(text: str) -> str:
    lower = text.lower()
    if any("\u0590" <= c <= "\u05ff" for c in text):
        return "he"
    if any(token in lower for token in ["hola", "¿", "gracias", "buenos", "buenas"]):
        return "es"
    if any(token in lower for token in ["bonjour", "merci", "s'il", "réunion"]):
        return "fr"
    return "en"


def classify_task(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in ["schedule", "calendar", "meeting", "availability", "book"]):
        return "calendar"
    if any(k in lower for k in ["email", "draft", "reply", "inbox", "send"]):
        return "email"
    if any(k in lower for k in ["research", "find", "look up", "investigate"]):
        return "research"
    if any(k in lower for k in ["remind", "reminder", "follow up", "follow-up"]):
        return "reminder"
    return "general"


def response_for(language: str, task_type: str, from_cache: bool) -> str:
    prefix = {
        "en": "Task routed",
        "es": "Tarea enrutada",
        "fr": "Tache acheminee",
        "he": "Task routed (he)",
    }.get(language, "Task routed")
    cache_note = "(cache hit)" if from_cache else "(fresh)"
    return f"{prefix}: {task_type} {cache_note}".strip()


def _requires_approval(task_type: str, text: str) -> bool:
    lower = text.lower()
    if task_type == "email" and any(token in lower for token in ["send", "email", "draft", "reply", "invite"]):
        return True
    if task_type == "calendar" and any(token in lower for token in ["schedule", "book", "meeting", "invite"]):
        return True
    return False


def _should_handoff(current_bot: str, text: str) -> tuple[Optional[str], Optional[str]]:
    lower = text.lower()

    buyer_signal = any(k in lower for k in ["buy", "buyer", "mortgage", "pre-approval", "home search"])
    seller_signal = any(k in lower for k in ["sell", "listing", "home value", "cma"])
    lead_signal = any(k in lower for k in ["not ready", "just browsing", "later", "not now"])

    if current_bot == "lead" and buyer_signal:
        return "buyer", "buyer_intent"
    if current_bot == "lead" and seller_signal:
        return "seller", "seller_intent"
    if current_bot == "buyer" and seller_signal:
        return "seller", "seller_intent_from_buyer"
    if current_bot == "seller" and buyer_signal:
        return "buyer", "buyer_intent_from_seller"
    if current_bot == "buyer" and lead_signal:
        return "lead", "requalification_needed"
    if current_bot == "seller" and lead_signal:
        return "lead", "requalification_needed"
    return None, None


def _circular_blocked(user_key: str, source_bot: str, target_bot: str, now_ts: float) -> bool:
    history = state.user_handoffs.get(user_key, [])
    if not history:
        return False

    last = history[-1]
    within_window = now_ts - last.ts <= 30 * 60
    reverse_route = last.source_bot == target_bot and last.target_bot == source_bot
    return within_window and reverse_route


async def _process_message(req: DemoMessageRequest) -> DemoMessageResponse:
    started = time.perf_counter()

    if req.requested_tenant_id and req.requested_tenant_id != req.tenant_id:
        state.metrics["blocked_cross_tenant"] += 1
        add_event(
            "tenant_violation_blocked",
            req.tenant_id,
            {
                "user_id": req.user_id,
                "requested_tenant_id": req.requested_tenant_id,
            },
        )
        raise HTTPException(status_code=403, detail="Cross-tenant access blocked")

    state.metrics["total_requests"] += 1
    state.metrics["cost_without_cache"] += 0.01

    cache_key = f"tenant:{req.tenant_id}:msg:{hashlib.sha256(req.message.encode()).hexdigest()}"
    cached = await state.cache_get(cache_key)

    user_key = f"{req.tenant_id}:{req.user_id}"
    current_bot = state.user_current_bot.get(user_key, "lead")
    approval_required = False
    approval_id: Optional[str] = None
    action_executed = True

    if cached:
        state.metrics["cache_hits"] += 1
        state.metrics["actual_cost"] += 0.001
        language = cached["language"]
        task_type = cached["task_type"]
        handoff = HandoffResult(source_bot=current_bot, executed=False, prevented_loop=False)
        response_text = response_for(language, task_type, from_cache=True)
        add_event("cache_hit", req.tenant_id, {"user_id": req.user_id, "task_type": task_type})
    else:
        state.metrics["cache_misses"] += 1
        state.metrics["actual_cost"] += 0.01

        language = detect_language(req.message)
        task_type = classify_task(req.message)

        target_bot, reason = _should_handoff(current_bot, req.message)
        now_ts = time.time()

        if target_bot:
            if _circular_blocked(user_key, current_bot, target_bot, now_ts):
                state.metrics["prevented_loops"] += 1
                handoff = HandoffResult(
                    source_bot=current_bot,
                    target_bot=target_bot,
                    executed=False,
                    prevented_loop=True,
                    reason="circular_prevention",
                )
                add_event(
                    "handoff_blocked",
                    req.tenant_id,
                    {
                        "user_id": req.user_id,
                        "source_bot": current_bot,
                        "target_bot": target_bot,
                    },
                )
            else:
                state.metrics["handoffs_executed"] += 1
                state.user_current_bot[user_key] = target_bot
                state.user_handoffs.setdefault(user_key, []).append(
                    HandoffLog(source_bot=current_bot, target_bot=target_bot, ts=now_ts)
                )
                handoff = HandoffResult(
                    source_bot=current_bot,
                    target_bot=target_bot,
                    executed=True,
                    prevented_loop=False,
                    reason=reason,
                )
                add_event(
                    "handoff_executed",
                    req.tenant_id,
                    {
                        "user_id": req.user_id,
                        "source_bot": current_bot,
                        "target_bot": target_bot,
                        "reason": reason,
                    },
                )
        else:
            handoff = HandoffResult(source_bot=current_bot, executed=False, prevented_loop=False)

        response_text = response_for(language, task_type, from_cache=False)
        await state.cache_set(cache_key, {"language": language, "task_type": task_type})

    if _requires_approval(task_type, req.message):
        approval_required = True
        action_executed = False
        approval_id = str(uuid.uuid4())
        state.approvals[approval_id] = {
            "approval_id": approval_id,
            "tenant_id": req.tenant_id,
            "user_id": req.user_id,
            "task_type": task_type,
            "message": req.message,
            "status": "pending",
            "created_at": iso_now(),
            "decided_at": None,
            "decision_reason": None,
        }
        state.metrics["approvals_created"] += 1
        response_text = f"{response_text}. Awaiting approval before execution."
        add_event(
            "approval_required",
            req.tenant_id,
            {
                "approval_id": approval_id,
                "user_id": req.user_id,
                "task_type": task_type,
            },
        )

    latency_ms = (time.perf_counter() - started) * 1000.0
    state.latencies_ms.append(latency_ms)

    add_event(
        "message_processed",
        req.tenant_id,
        {
            "user_id": req.user_id,
            "language": language,
            "task_type": task_type,
            "latency_ms": round(latency_ms, 2),
            "from_cache": bool(cached),
        },
    )

    return DemoMessageResponse(
        tenant_id=req.tenant_id,
        user_id=req.user_id,
        language=language,
        task_type=task_type,
        response_text=response_text,
        from_cache=bool(cached),
        latency_ms=round(latency_ms, 2),
        handoff=handoff,
        approval_required=approval_required,
        approval_id=approval_id,
        action_executed=action_executed,
    )


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = int((len(sorted_vals) - 1) * pct)
    return round(sorted_vals[idx], 2)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "timestamp": iso_now()}


@app.post("/v1/demo/message", response_model=DemoMessageResponse)
async def demo_message(req: DemoMessageRequest) -> DemoMessageResponse:
    return await _process_message(req)


@app.post("/v1/demo/scenario/{scenario_name}", response_model=ScenarioResponse)
async def run_scenario(
    scenario_name: str, tenant_id: str = "tenant-alpha", user_id: str = "demo-user"
) -> ScenarioResponse:
    if scenario_name not in {"kialash", "chase"}:
        raise HTTPException(status_code=404, detail="Scenario not found")

    if scenario_name == "kialash":
        messages = [
            "Hola, quiero comprar una casa",
            "I need to sell my current home first",
            "I am not ready yet, just browsing",
        ]
    else:
        messages = [
            "Draft an email reply to Alex",
            "Schedule a 30 minute meeting Thursday afternoon",
            "Remind me tomorrow at 9am to follow up",
        ]

    steps: List[DemoMessageResponse] = []
    for text in messages:
        steps.append(await _process_message(DemoMessageRequest(tenant_id=tenant_id, user_id=user_id, message=text)))

    return ScenarioResponse(scenario=scenario_name, steps=steps)


@app.get("/v1/events", response_model=List[EventRecord])
async def list_events(tenant_id: Optional[str] = None, limit: int = 100) -> List[EventRecord]:
    filtered = list(state.events)
    if tenant_id:
        filtered = [e for e in filtered if e["tenant_id"] == tenant_id]
    return [EventRecord(**e) for e in filtered[-limit:]]


@app.get("/v1/approvals", response_model=List[ApprovalItem])
async def list_approvals(tenant_id: Optional[str] = None, status: Optional[str] = None) -> List[ApprovalItem]:
    items = list(state.approvals.values())
    if tenant_id:
        items = [i for i in items if i["tenant_id"] == tenant_id]
    if status:
        items = [i for i in items if i["status"] == status]
    items.sort(key=lambda i: i["created_at"], reverse=True)
    return [ApprovalItem(**i) for i in items]


@app.post("/v1/approvals/{approval_id}/decision", response_model=ApprovalItem)
async def decide_approval(approval_id: str, req: ApprovalDecisionRequest) -> ApprovalItem:
    item = state.approvals.get(approval_id)
    if not item:
        raise HTTPException(status_code=404, detail="Approval not found")

    decision = req.decision.strip().lower()
    if decision not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="Decision must be approve or reject")

    if item["status"] != "pending":
        raise HTTPException(status_code=409, detail="Approval already decided")

    item["status"] = "approved" if decision == "approve" else "rejected"
    item["decided_at"] = iso_now()
    item["decision_reason"] = req.reason

    if item["status"] == "approved":
        state.metrics["approvals_approved"] += 1
    else:
        state.metrics["approvals_rejected"] += 1

    add_event(
        "approval_decided",
        item["tenant_id"],
        {
            "approval_id": approval_id,
            "status": item["status"],
            "user_id": item["user_id"],
        },
    )
    return ApprovalItem(**item)


@app.get("/v1/metrics", response_model=MetricsResponse)
async def metrics() -> MetricsResponse:
    total = int(state.metrics["total_requests"])
    hits = int(state.metrics["cache_hits"])
    misses = int(state.metrics["cache_misses"])
    hit_rate = round((hits / total), 4) if total else 0.0

    cost_without = float(state.metrics["cost_without_cache"])
    actual_cost = float(state.metrics["actual_cost"])
    savings = round(((cost_without - actual_cost) / cost_without) * 100, 2) if cost_without else 0.0
    approvals_pending = sum(1 for i in state.approvals.values() if i["status"] == "pending")

    return MetricsResponse(
        total_requests=total,
        cache_hits=hits,
        cache_misses=misses,
        cache_hit_rate=hit_rate,
        blocked_cross_tenant=int(state.metrics["blocked_cross_tenant"]),
        handoffs_executed=int(state.metrics["handoffs_executed"]),
        prevented_loops=int(state.metrics["prevented_loops"]),
        approvals_created=int(state.metrics["approvals_created"]),
        approvals_approved=int(state.metrics["approvals_approved"]),
        approvals_rejected=int(state.metrics["approvals_rejected"]),
        approvals_pending=int(approvals_pending),
        p50_latency_ms=_percentile(state.latencies_ms, 0.50),
        p95_latency_ms=_percentile(state.latencies_ms, 0.95),
        estimated_cost_savings_percent=savings,
    )
