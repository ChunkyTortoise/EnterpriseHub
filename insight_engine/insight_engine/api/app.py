"""
Insight Engine REST API
Exposes Obsidian-themed dashboard components as a REST API.

Run:
    uvicorn insight_engine.api.app:app --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

import asyncio
import json
from typing import Literal, Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="Insight Engine API",
    description="REST API for Obsidian-themed Streamlit BI dashboard components",
    version="0.1.0",
)


# -- Request/Response Models ------------------------------------------------


class MetricRequest(BaseModel):
    value: str = Field(..., example="$2.4M")
    label: str = Field(..., example="Revenue This Quarter")
    variant: Literal["default", "success", "warning", "error", "info"] = "default"
    trend: Optional[Literal["up", "down", "neutral"]] = None
    comparison_value: Optional[str] = None


class CardRequest(BaseModel):
    title: str = Field(..., example="Hot Leads")
    content: str = Field(..., example="15 leads need attention")
    variant: Literal["default", "alert", "success", "info"] = "default"
    glow_color: Optional[str] = Field(None, example="#EF4444")
    icon: Optional[str] = None


class DashboardRequest(BaseModel):
    title: str = Field(..., example="Sales Dashboard")
    metrics: list[MetricRequest] = Field(default_factory=list)
    cards: list[CardRequest] = Field(default_factory=list)


class RenderResponse(BaseModel):
    html: str
    component_type: str


class HealthResponse(BaseModel):
    status: str
    version: str


# -- Rendering Helpers -------------------------------------------------------

OBSIDIAN_CSS = """
<style>
:root {
  --bg-primary: #0d1117; --bg-secondary: #161b22; --bg-card: #21262d;
  --border: #30363d; --text-primary: #e6edf3; --text-secondary: #8b949e;
  --accent-blue: #58a6ff; --accent-purple: #bc8cff;
  --success: #3fb950; --warning: #d29922; --error: #f85149;
}
body { background: var(--bg-primary); color: var(--text-primary); font-family: -apple-system, sans-serif; }
.ie-metric { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 20px; }
.ie-metric-value { font-size: 2rem; font-weight: 700; color: var(--accent-blue); }
.ie-metric-label { font-size: 0.875rem; color: var(--text-secondary); margin-top: 4px; }
.ie-metric-trend { font-size: 0.875rem; margin-top: 8px; }
.ie-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px; padding: 16px; }
.ie-card-title { font-weight: 600; font-size: 1.1rem; margin-bottom: 8px; }
.variant-success { border-left: 3px solid var(--success); }
.variant-alert { border-left: 3px solid var(--error); }
.variant-info { border-left: 3px solid var(--accent-blue); }
</style>
"""

TREND_ICONS = {"up": "\u2191", "down": "\u2193", "neutral": "\u2192"}
VARIANT_COLORS = {
    "success": "#3fb950",
    "warning": "#d29922",
    "error": "#f85149",
    "info": "#58a6ff",
    "default": "#8b949e",
}


def render_metric_html(req: MetricRequest) -> str:
    trend_html = ""
    if req.trend and req.comparison_value:
        color = "#3fb950" if req.trend == "up" else "#f85149" if req.trend == "down" else "#8b949e"
        trend_html = (
            f'<div class="ie-metric-trend" style="color:{color}">{TREND_ICONS[req.trend]} {req.comparison_value}</div>'
        )

    color = VARIANT_COLORS.get(req.variant, "#58a6ff")
    return f"""
    <div class="ie-metric">
        <div class="ie-metric-value" style="color:{color}">{req.value}</div>
        <div class="ie-metric-label">{req.label}</div>
        {trend_html}
    </div>"""


def render_card_html(req: CardRequest) -> str:
    glow = f"box-shadow: 0 0 20px {req.glow_color}40;" if req.glow_color else ""
    icon_html = f"<span style='margin-right:8px'>{req.icon}</span>" if req.icon else ""
    css_class = f"ie-card variant-{req.variant}" if req.variant != "default" else "ie-card"
    return f"""
    <div class="{css_class}" style="{glow}">
        <div class="ie-card-title">{icon_html}{req.title}</div>
        <div class="ie-card-content">{req.content}</div>
    </div>"""


def build_dashboard_html(title: str, metric_htmls: list[str], card_htmls: list[str]) -> str:
    metrics_grid = "".join(f'<div style="flex:1;min-width:200px">{h}</div>' for h in metric_htmls)
    cards_grid = "".join(f'<div style="flex:1;min-width:250px">{h}</div>' for h in card_htmls)
    return f"""<!DOCTYPE html>
<html><head><title>{title}</title>{OBSIDIAN_CSS}</head>
<body style="padding:24px;background:#0d1117">
<h1 style="background:linear-gradient(90deg,#58a6ff,#bc8cff);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{title}</h1>
<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:24px">{metrics_grid}</div>
<div style="display:flex;gap:16px;flex-wrap:wrap">{cards_grid}</div>
</body></html>"""


# -- Routes ------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/render/metric", response_model=RenderResponse, tags=["components"])
async def render_metric(req: MetricRequest) -> RenderResponse:
    html = OBSIDIAN_CSS + render_metric_html(req)
    return RenderResponse(html=html, component_type="metric")


@app.post("/render/card", response_model=RenderResponse, tags=["components"])
async def render_card(req: CardRequest) -> RenderResponse:
    html = OBSIDIAN_CSS + render_card_html(req)
    return RenderResponse(html=html, component_type="card")


@app.get("/theme", response_class=PlainTextResponse, tags=["theme"])
async def get_theme() -> str:
    """Return the Obsidian CSS theme as text/css."""
    return OBSIDIAN_CSS.replace("<style>", "").replace("</style>", "").strip()


@app.post("/dashboard", response_class=HTMLResponse, tags=["dashboard"])
async def generate_dashboard(req: DashboardRequest) -> str:
    metric_htmls = [render_metric_html(m) for m in req.metrics]
    card_htmls = [render_card_html(c) for c in req.cards]
    return build_dashboard_html(req.title, metric_htmls, card_htmls)


@app.post("/dashboard/stream", tags=["dashboard"])
async def stream_dashboard(req: DashboardRequest) -> StreamingResponse:
    """SSE streaming endpoint that assembles a dashboard piece by piece."""

    async def event_generator():
        yield f"data: {json.dumps({'event': 'start', 'title': req.title, 'total': len(req.metrics) + len(req.cards)})}\n\n"
        await asyncio.sleep(0.1)

        for i, metric in enumerate(req.metrics):
            html = render_metric_html(metric)
            yield f"data: {json.dumps({'event': 'metric', 'index': i, 'html': html, 'label': metric.label})}\n\n"
            await asyncio.sleep(0.05)

        for i, card in enumerate(req.cards):
            html = render_card_html(card)
            yield f"data: {json.dumps({'event': 'card', 'index': i, 'html': html, 'title': card.title})}\n\n"
            await asyncio.sleep(0.05)

        full_html = build_dashboard_html(
            req.title,
            [render_metric_html(m) for m in req.metrics],
            [render_card_html(c) for c in req.cards],
        )
        yield f"data: {json.dumps({'event': 'complete', 'html': full_html})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
