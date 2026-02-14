# Claude Code Integration Guide: EnterpriseHub

This guide explains how to leverage the newly integrated agents, skills, and MCP tools for the EnterpriseHub project.

## 🤖 Specialized Agents
You can now invoke specific "personas" for different development tasks. Mention these agents in your prompts to activate their specialized reasoning.

| Agent | Task |
|-------|------|
| **Market Intelligence Specialist** | Use for market analysis, property valuation logic, and Rancho Cucamonga-specific trends. |
| **Chatbot Architect** | Use for LangGraph orchestration, GHL sync, and conversation design. |
| **BI Performance Specialist** | Use for auditing latency, optimizing SQL/Redis, and load testing. |

**Example Prompt**:
> "As the **Market Intelligence Specialist**, analyze the inventory trends for zip code 78704 using the `market-intelligence` MCP tool."

## 📚 Domain Skills
Claude automatically discovers skills in `.claude/skills/`. The following new skill is available:

- **Rancho Cucamonga Market Intelligence**: Provides deep context on Rancho Cucamonga zip codes, tech corridors, and economic drivers.

**Example Prompt**:
> "Using the **Rancho Cucamonga Market Data skill**, explain the impact of Tesla Giga Texas on property values in Del Valle."

## 🔌 MCP Tools (Model Context Protocol)
The system is configured to use specialized servers for live data access. These are defined in `.claude/mcp-servers.json`.

| Server | Tools |
|--------|-------|
| `mls-data` | `search_properties`, `get_property_details`, `find_comparables` |
| `market-intelligence` | `analyze_neighborhood`, `get_price_trends`, `get_demographic_data` |
| `ghl-crm` | `create_contact`, `search_contacts`, `trigger_workflow` |
| `valuation-engine` | `get_property_valuation`, `calculate_investment_metrics` |

**Example Prompt**:
> "Use the `mls-data` tool to find 3-bedroom properties in 78746 under $1.5M and then run a `valuation-engine` risk assessment on the top match."

## 🛠️ Verification & Quality Gates
Before committing changes, Claude uses the validation scripts in `.claude/scripts/` to ensure project standards are met.

- **Pre-Commit**: Automatically runs ruff, mypy, and pytest.
- **BI Audit**: Run `python comprehensive_bi_verification.py` to validate performance improvements.

---
*Created: January 25, 2026 | Optimized for EnterpriseHub Production Readiness*
