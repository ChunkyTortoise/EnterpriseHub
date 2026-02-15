"""
Insight Engine - Obsidian-themed Streamlit BI dashboard components.

A reusable component library for building premium dark-themed Streamlit dashboards
with glassmorphism effects, design tokens, and type-safe primitives.

Usage:
    from insight_engine import ObsidianThemeService, Colors, inject_elite_css
    from insight_engine.primitives import render_obsidian_card, CardConfig

Author: Cayman Roden
"""

__version__ = "0.1.0"
__author__ = "Cayman Roden"

from .theme.service import Colors, ObsidianThemeService, Spacing, Typography
from .theme.obsidian import (
    inject_elite_css,
    style_obsidian_chart,
    render_dossier_block,
    render_neural_progress,
    render_terminal_log,
    render_voice_waveform,
    render_journey_line,
    render_biometric_heartbeat,
    render_countdown_gauge,
    render_decision_stream,
)

__all__ = [
    "ObsidianThemeService",
    "Colors",
    "Typography",
    "Spacing",
    "inject_elite_css",
    "style_obsidian_chart",
    "render_dossier_block",
    "render_neural_progress",
    "render_terminal_log",
    "render_voice_waveform",
    "render_journey_line",
    "render_biometric_heartbeat",
    "render_countdown_gauge",
    "render_decision_stream",
]
