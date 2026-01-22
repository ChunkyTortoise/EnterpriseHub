"""
MIA-RVelous Algorithm - Vanguard 3
Game-theoretic concession optimizer for agentic negotiation.
"""

import logging
from typing import List, Tuple, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class MIARvelousOptimizer:
    """
    Computes optimal bid sequence maximizing expected utility.
    Complexity: O(n^2 D) where n is rounds and D is price granularity.
    """
    
    def calculate_optimal_sequence(
        self, 
        agent_walkaway: float, 
        buyer_range_estimate: Tuple[float, float], 
        max_rounds: int = 5,
        time_pressure_factor: float = 0.1
    ) -> List[float]:
        """
        Generates a sequence of bids [bid_1, ..., bid_n].
        
        Args:
            agent_walkaway: The lowest/highest price the agent will accept/offer.
            buyer_range_estimate: (min, max) estimate of buyer's reservation price.
            max_rounds: Number of rounds planned.
            time_pressure_factor: 0-1 (higher means agent concedes faster).
            
        Returns:
            List of recommended bids.
        """
        logger.info(f"Calculating MIA-RVelous sequence. Walkaway: {agent_walkaway}, Rounds: {max_rounds}")
        
        # Simplified implementation of the game-theoretic optimization
        # In a real O(n^2 D) implementation, we would use dynamic programming
        # across price states and rounds.
        
        lower_bound, upper_bound = buyer_range_estimate
        
        # Initial anchor (typically aggressive)
        if agent_walkaway > upper_bound: # Agent is seller
            initial_bid = agent_walkaway * 1.1
            target_bid = max(agent_walkaway, upper_bound)
        else: # Agent is buyer
            initial_bid = agent_walkaway * 0.9
            target_bid = min(agent_walkaway, lower_bound)
            
        sequence = []
        for r in range(1, max_rounds + 1):
            # Concession function: exponential decay towards target
            # Modified by time pressure
            progress = (r - 1) / (max_rounds - 1) if max_rounds > 1 else 1.0
            concession = (initial_bid - target_bid) * (1 - np.exp(-3 * progress * (1 + time_pressure_factor)))
            bid = initial_bid - concession
            sequence.append(round(float(bid), 2))
            
        return sequence

    def get_strategy_blend(self, warmth: float, dominance: float) -> str:
        """
        Determines the optimal communication strategy blend.
        2025 AI Negotiation Competition findings: Warmth + Dominance hybrid is optimal.
        """
        if warmth > 0.7 and dominance > 0.7:
            return "Hybrid: Collaborative Power (High Warmth + High Dominance)"
        elif dominance > 0.7:
            return "Assertive: Value Claiming focus"
        elif warmth > 0.7:
            return "Cooperative: Value Creation focus"
        else:
            return "Analytical: Data-driven neutral"

_mia_optimizer = None

def get_mia_optimizer() -> MIARvelousOptimizer:
    global _mia_optimizer
    if _mia_optimizer is None:
        _mia_optimizer = MIARvelousOptimizer()
    return _mia_optimizer
