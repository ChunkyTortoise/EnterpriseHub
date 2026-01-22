"""
Defines the registry of available hooks.
Reference: EXTENSIVE_CLAUDE_HOOKS_V2.md
"""

HOOKS = {
    # Architecture
    "codebase_investigator": "hooks.architecture.CodebaseInvestigator",
    "pattern_architect": "hooks.architecture.PatternArchitect",
    "marketplace_governor": "hooks.architecture.MarketplaceGovernor",
    # Real Estate
    "market_oracle": "hooks.real_estate.MarketOracle",
    "lead_simulator": "hooks.real_estate.LeadPersonaSimulator",
    "sentiment_decoder": "hooks.real_estate.SentimentDecoder",
    "sensei_hook": "hooks.real_estate.SenseiHook",
    # Security
    "security_sentry": "hooks.security.SecuritySentry",
    "edge_case_generator": "hooks.security.EdgeCaseGenerator"
}
