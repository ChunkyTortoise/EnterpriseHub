"""
Defines the registry of available hooks.
Reference: EXTENSIVE_CLAUDE_HOOKS_V2.md
"""

HOOKS = {
    # Architecture
    "codebase_investigator": "hooks.architecture.CodebaseInvestigator",
    "pattern_architect": "hooks.architecture.PatternArchitect",
    # Real Estate
    "market_oracle": "hooks.real_estate.MarketOracle",
    "lead_simulator": "hooks.real_estate.LeadPersonaSimulator",
    # ... add others from specs
}
