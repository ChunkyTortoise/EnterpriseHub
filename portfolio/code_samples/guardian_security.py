"""
🛡️ ARETE Guardian Agent (Security Audit Logic)
This snippet shows how the Guardian agent prevents the 'Engineer' 
from deploying unsafe code or leaking secrets.
"""

import re

class GuardianAgent:
    def __init__(self):
        self.forbidden_patterns = [
            r"sk-[a-zA-Z0-9]{32,}",  # Generic API Keys
            r"postgres://.*:.*@",    # Hardcoded DB Credentials
            r"import os; os\.system\(", # Direct Shell Execution Risks
        ]

    def audit_code(self, code: str) -> dict:
        """
        Scans code for security vulnerabilities before DevOps is allowed to commit.
        """
        print("🛡️ Guardian: Performing deep security audit...")
        
        leaks = []
        for pattern in self.forbidden_patterns:
            if re.search(pattern, code):
                leaks.append(pattern)
        
        if leaks:
            return {
                "security_clearance": False,
                "reason": f"Vulnerability detected: {leaks}",
                "action": "REJECT"
            }
            
        print("✅ Guardian: Code passed security audit.")
        return {
            "security_clearance": True,
            "action": "APPROVE"
        }

# Example Usage
guardian = GuardianAgent()
unsafe_code = "api_key = 'sk-1234567890abcdef1234567890abcdef'"
result = guardian.audit_code(unsafe_code)
# Result: {'security_clearance': False, 'reason': "Vulnerability detected: ['sk-[a-zA-Z0-9]{32,}']", 'action': 'REJECT'}
