"""
Skill Registry for Phase 2 AI Orchestration.
Manages tool access and categorization across Discovery, Analysis, Strategy, Action, and Governance.
"""
from enum import Enum
from typing import Dict, List, Any, Optional

class SkillCategory(Enum):
    DISCOVERY = "Discovery"
    ANALYSIS = "Analysis"
    STRATEGY = "Strategy"
    ACTION = "Action"
    GOVERNANCE = "Governance"

class SkillRegistry:
    """
    Registry that manages tool access based on 5 core skill categories.
    Used by ClaudeOrchestrator to filter and organize tools for specialist agents.
    """
    def __init__(self):
        self.categories: Dict[SkillCategory, List[str]] = {cat: [] for cat in SkillCategory}
        self.tool_to_server: Dict[str, str] = {}
        self._initialize_mappings()

    def _initialize_mappings(self):
        # Discovery: Market and Property matching
        self._register("find_lifestyle_matches", SkillCategory.DISCOVERY, "PropertyIntelligence")
        self._register("predict_life_transitions", SkillCategory.DISCOVERY, "PropertyIntelligence")
        self._register("get_market_analysis", SkillCategory.DISCOVERY, "MarketIntelligence")
        self._register("compare_markets", SkillCategory.DISCOVERY, "MarketIntelligence")
        self._register("get_opportunity_score", SkillCategory.DISCOVERY, "MarketIntelligence")

        # Analysis: Lead and Property deep-dives
        self._register("analyze_lead", SkillCategory.ANALYSIS, "LeadIntelligence")
        self._register("get_lead_score_breakdown", SkillCategory.ANALYSIS, "LeadIntelligence")
        self._register("analyze_property_fit", SkillCategory.ANALYSIS, "PropertyIntelligence")
        self._register("get_daily_summary", SkillCategory.ANALYSIS, "AnalyticsIntelligence")
        self._register("get_conversion_metrics", SkillCategory.ANALYSIS, "AnalyticsIntelligence")

        # Strategy: Negotiation and complex planning
        self._register("analyze_negotiation", SkillCategory.STRATEGY, "NegotiationIntelligence")
        self._register("get_negotiation_strategy", SkillCategory.STRATEGY, "NegotiationIntelligence")

        # Action: Outreach and real-time coaching
        self._register("generate_lead_outreach_script", SkillCategory.ACTION, "LeadIntelligence")
        self._register("get_realtime_coaching", SkillCategory.ACTION, "NegotiationIntelligence")

        # Governance: ROI and platform health
        self._register("get_llm_roi", SkillCategory.GOVERNANCE, "AnalyticsIntelligence")

    def _register(self, tool_name: str, category: SkillCategory, server_name: str):
        if tool_name not in self.categories[category]:
            self.categories[category].append(tool_name)
        self.tool_to_server[tool_name] = server_name

    def get_tools_for_category(self, category: SkillCategory) -> List[str]:
        """Returns tool names for a given category."""
        return self.categories.get(category, [])

    def get_category_for_tool(self, tool_name: str) -> Optional[SkillCategory]:
        """Returns the category for a given tool name."""
        for cat, tools in self.categories.items():
            if tool_name in tools:
                return cat
        return None

    def get_server_for_tool(self, tool_name: str) -> Optional[str]:
        """Returns the MCP server name that hosts the tool."""
        return self.tool_to_server.get(tool_name)

    def get_all_tools(self) -> List[str]:
        """Returns all registered tool names."""
        return list(self.tool_to_server.keys())

# Singleton instance
skill_registry = SkillRegistry()
