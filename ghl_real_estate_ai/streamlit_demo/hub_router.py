"""Centralized hub routing based on hub_mapping.json."""
from __future__ import annotations

import importlib
import json
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import streamlit as st


def _load_hub_mapping() -> Dict[str, Dict[str, Dict]]:
    mapping_path = Path(__file__).resolve().parent.parent / "hub_mapping.json"
    with mapping_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("consolidation_plan", {})


def _normalize_label(label: str) -> str:
    label = re.sub(r"\\.py$", "", label)
    label = re.sub(r"^\\d+_", "", label)
    label = re.sub(r"[^a-zA-Z0-9_]+", "_", label)
    return label.strip("_").lower()


def _component_modules() -> List[str]:
    components_dir = Path(__file__).resolve().parent / "components"
    modules = []
    for path in components_dir.glob("*.py"):
        if path.name.startswith("_") or path.name == "__init__.py":
            continue
        modules.append(path.stem)
    return sorted(modules)


def _assign_hub(module_name: str) -> str:
    name = module_name.lower()
    keyword_map = {
        "hub_1_executive_command": ["executive", "portfolio", "command", "enterprise", "war_room", "realtime_executive"],
        "hub_2_lead_intelligence": ["lead", "buyer", "seller", "segmentation", "personalization", "property", "journey", "customer", "churn", "valuation"],
        "hub_3_automation_studio": ["automation", "workflow", "sequence", "trigger", "bot", "agent", "marketplace", "notification", "scheduler"],
        "hub_4_sales_copilot": ["deal", "commission", "meeting", "document", "sales", "copilot", "negotiation", "pricing", "closer"],
        "hub_5_ops_optimization": ["ops", "optimization", "quality", "revenue", "benchmark", "coaching", "performance", "compliance", "security", "monitoring", "analytics", "analyst"],
    }
    for hub_key, keywords in keyword_map.items():
        if any(keyword in name for keyword in keywords):
            return hub_key
    return "hub_5_ops_optimization"


def _resolve_renderer(page_label: str, modules: List[str]) -> Optional[Callable[[], None]]:
    normalized = _normalize_label(page_label)
    candidates = [normalized]

    # Fallback: try token overlap with module names
    tokens = set(normalized.split("_"))
    scored: List[Tuple[float, str]] = []
    for module in modules:
        module_tokens = set(module.split("_"))
        overlap = len(tokens.intersection(module_tokens))
        union = len(tokens.union(module_tokens)) or 1
        scored.append((overlap / union, module))
    scored.sort(reverse=True)
    if scored and scored[0][0] >= 0.2:
        candidates.append(scored[0][1])

    for module_name in candidates:
        if module_name not in modules:
            continue
        try:
            module = importlib.import_module(f"ghl_real_estate_ai.streamlit_demo.components.{module_name}")
        except Exception:
            continue
        func_name = f"render_{module_name}"
        if hasattr(module, func_name):
            return getattr(module, func_name)
        for name, obj in vars(module).items():
            if callable(obj) and name.startswith("render_"):
                return obj
    return None


def _render_component_library(hub_key: str, modules: List[str]) -> None:
    assigned = [m for m in modules if _assign_hub(m) == hub_key]
    if not assigned:
        st.info("No components mapped yet.")
        return
    selection = st.selectbox("Select component", assigned, index=0)
    renderer = _resolve_renderer(selection, modules)
    if renderer:
        renderer()
    else:
        st.warning("Component renderer not found.")


def render_hub(hub_label: str) -> None:
    hubs = _load_hub_mapping()
    modules = _component_modules()

    # Find matching hub by name
    hub_key = None
    for key, hub in hubs.items():
        name = hub.get("name", "")
        if hub_label.lower() in name.lower() or _normalize_label(hub_label) in _normalize_label(name):
            hub_key = key
            break
    if not hub_key:
        st.warning("Hub mapping not found.")
        return

    hub = hubs[hub_key]
    pages = hub.get("pages", [])
    tabs = [re.sub(r"\\.py$", "", page) for page in pages]
    tabs.append("Component Library")
    tab_instances = st.tabs(tabs)

    for idx, page in enumerate(pages):
        with tab_instances[idx]:
            renderer = _resolve_renderer(page, modules)
            if renderer:
                renderer()
            else:
                st.info(f"Renderer not found for {page}. Use Component Library to access available modules.")

    with tab_instances[-1]:
        _render_component_library(hub_key, modules)
