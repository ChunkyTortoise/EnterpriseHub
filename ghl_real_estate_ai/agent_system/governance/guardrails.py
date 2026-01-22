"""
Operational Limits & Kill Switches.
Reference: AGENT_GOVERNANCE_PROTOCOL.md
"""
from ..config import MAX_COST_PER_SESSION, MAX_TURNS

class GovernanceError(Exception):
    """Raised when an agent violates governance protocols."""
    pass

def check_limits(session_cost: float, turn_count: int):
    """
    Validates current session state against defined guardrails.
    """
    if turn_count > MAX_TURNS:
        raise GovernanceError(f"Turn count limit exceeded: {turn_count} > {MAX_TURNS}")
    
    if session_cost > MAX_COST_PER_SESSION:
        raise GovernanceError(f"Session cost limit exceeded: ${session_cost:.2f} > ${MAX_COST_PER_SESSION:.2f}")
    
    return True
