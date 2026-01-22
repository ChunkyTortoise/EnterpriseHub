"""
Security & QA Hooks.
Implements: Security Sentry, Edge Case Generator.
"""

import random

from ghl_real_estate_ai.agent_system.hooks.governance import governance_auditor

class SecuritySentry:
    """Monitors for PII leaks, prompt injections, and off-topic deviations."""
    
    def scan_output(self, text: str, agent_name: str = "Unknown Agent") -> bool:
        """
        Scans agent output for security violations.
        Returns True if safe, False if a violation is detected.
        """
        # 1. Basic PII Check (Simulated)
        if "ssn" in text.lower() or "social security" in text.lower():
            governance_auditor.log_security_violation(agent_name, "PII Leak (SSN)", text)
            return False
            
        # 2. Prompt Injection patterns
        injection_patterns = ["ignore previous instructions", "system prompt", "developer mode"]
        if any(p in text.lower() for p in injection_patterns):
            governance_auditor.log_security_violation(agent_name, "Prompt Injection Attempt", text)
            return False
            
        return True

    def scan_input(self, text: str) -> bool:
        """Scans user input for malicious intent."""
        # Simple placeholder for MVP
        return True

class EdgeCaseGenerator:
    """Generates rare or difficult scenarios for agent testing."""
    
    def generate_scenario(self, domain: str) -> str:
        scenarios = {
            "real_estate": [
                "Lead is a sovereign citizen who refuses to use standard contracts.",
                "Property has a hidden cemetery discovered during inspection.",
                "Multiple offers received, but one is in Bitcoin from an unverified source.",
                "Lead wants to buy a house using a bartering system (e.g., gold bars)."
            ],
            "legal": [
                "Zoning laws changed 5 minutes after offer acceptance.",
                "Lead is actually a minor posing as an adult."
            ]
        }
        domain_scenarios = scenarios.get(domain, scenarios["real_estate"])
        return random.choice(domain_scenarios)
