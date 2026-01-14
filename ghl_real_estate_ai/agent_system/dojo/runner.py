"""
Dojo Runner: Executes sparring matches between Trainee and Simulator.
Reference: CONTINUOUS_IMPROVEMENT_DOJO.md
"""

import asyncio
import logging
from typing import List, Dict, Any
from .personas import get_persona
from .evaluator import DojoEvaluator

logger = logging.getLogger(__name__)

async def run_sparring_match(regimen_name: str, persona_name: str):
    """
    Executes a single sparring match between the agent and a persona.
    """
    evaluator = DojoEvaluator()
    persona = get_persona(persona_name)
    
    logger.info(f"Starting sparring match: {regimen_name} with {persona_name}")
    
    # Mock conversation loop for MVP
    history = []
    # 1. Simulator speaks
    history.append({"role": "user", "content": f"Hi, I'm interested in a property. {persona.get('initial_query', '')}"})
    
    # 2. Agent responds (Mocked for now, would call ClaudeOrchestrator)
    history.append({"role": "assistant", "content": "Hello! I'd love to help you with that. What's your budget?"})
    
    # 3. Evaluator grades
    score = evaluator.grade_conversation(history)
    return score

async def run_regimen(regimen_name: str, iterations: int = 1):
    """
    Executes a training regimen with multiple iterations.
    """
    logger.info(f"Executing Regimen: {regimen_name} ({iterations} iterations)")
    results = []
    
    # Map regimen to persona
    persona_map = {
        "Objection Handling": "The Aggressive Investor",
        "Compliance Drills": "The Fair Housing Trap",
        "Lead Qualification": "The Vague Browser"
    }
    
    persona = persona_map.get(regimen_name, "The Confused First-Timer")
    
    for i in range(iterations):
        score = await run_sparring_match(regimen_name, persona)
        results.append(score)
        
    avg_score = sum(s['overall'] for s in results) / len(results) if results else 0
    return {
        "regimen": regimen_name,
        "iterations": iterations,
        "average_score": avg_score,
        "results": results
    }
