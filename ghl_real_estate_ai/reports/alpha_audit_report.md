
# Alpha Code Auditor Report
Generated: 2026-01-05

## Summary
- Files Analyzed: 281
- Total Lines: 92,564
- Issues Found: 180

## Issue Breakdown
- 🔴 Critical: 0
- 🟠 High: 72
- 🟡 Medium: 11
- 🔵 Low: 97

## Issues by Category

### Style (3 issues)
- [medium] tests/test_ghl_client_extended.py:14 - Wildcard import detected
- [medium] tests/test_memory_service_extended.py:14 - Wildcard import detected
- [medium] tests/test_reengagement_engine_extended.py:14 - Wildcard import detected

### Maintainability (103 issues)
- [low] core/conversation_manager.py:310 - Function 'generate_response' is very long (265 lines)
- [low] agents/iota_revenue_attribution.py:62 - Function 'create_attribution_service' is very long (336 lines)
- [low] agents/swarm_orchestrator.py:163 - Function '_initialize_tasks' is very long (203 lines)
- [low] agents/zeta_demo_mode.py:63 - Function 'create_demo_generator' is very long (316 lines)
- [low] agents/agent_08_phase3_orchestrator.py:18 - Function '__init__' is very long (101 lines)
- [low] agents/agent_07_documentation_implementation.py:40 - Function 'add_function_documentation' is very long (152 lines)
- [low] agents/agent_05_security_integration.py:108 - Function 'create_auth_routes' is very long (105 lines)
- [low] agents/agent_05_security_integration.py:293 - Function 'create_integration_tests' is very long (163 lines)
- [low] agents/alpha_integration_validator.py:189 - Function 'task_5_generate_report' is very long (123 lines)
- [low] agents/delta_executive_dashboard.py:62 - Function 'create_dashboard_service' is very long (317 lines)

### Security (75 issues)
- [high] core/llm_client.py:60 - Potential hardcoded secret detected
- [high] core/llm_client.py:91 - Potential hardcoded secret detected
- [high] core/llm_client.py:100 - Potential hardcoded secret detected
- [high] core/llm_client.py:117 - Potential hardcoded secret detected
- [high] tests/test_security_integration.py:25 - Potential hardcoded secret detected
- [high] tests/test_security_integration.py:33 - Potential hardcoded secret detected
- [high] tests/test_security_integration.py:50 - Potential hardcoded secret detected
- [high] tests/test_security_integration.py:58 - Potential hardcoded secret detected
- [high] tests/test_security_integration.py:65 - Potential hardcoded secret detected
- [high] tests/test_security_integration.py:76 - Potential hardcoded secret detected
