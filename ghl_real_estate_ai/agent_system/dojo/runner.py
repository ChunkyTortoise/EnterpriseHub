"""
Dojo Runner: Executes sparring matches between Trainee and Simulator.
Reference: CONTINUOUS_IMPROVEMENT_DOJO.md
"""

import logging

from ghl_real_estate_ai.agent_system.governance.guardrails import check_limits
from ghl_real_estate_ai.core.llm_client import LLMClient

from .evaluator import DojoEvaluator
from .personas import get_persona

logger = logging.getLogger(__name__)


class DojoRunner:
    """
    Orchestrates automated sparring matches for agent training.
    """

    def __init__(self):
        self.llm = LLMClient()
        self.evaluator = DojoEvaluator()

    async def run_sparring_match(
        self, regimen_name: str, persona_name: str, max_turns: int = 4, custom_agent_prompt: Optional[str] = None
    ):
        """
        Executes a single sparring match between the agent and a persona.
        """
        persona = get_persona(persona_name)
        logger.info(f"Starting sparring match: {regimen_name} with {persona_name}")

        history = []
        current_input = persona.get("initial_query", "")
        session_cost = 0.0

        for turn in range(max_turns):
            print(f"DEBUG: Turn {turn + 1}/{max_turns}")
            # 1. Trainee Agent (Assistant) responds
            if custom_agent_prompt:
                agent_system_prompt = custom_agent_prompt
            else:
                agent_system_prompt = f"""
                You are an elite Real Estate AI Agent.
                Your Goal: {persona.get("goal")}
                Context: You are talking to a lead who is {persona_name}.
                Behavioral Guidelines: Be professional, helpful, and strictly follow fair housing laws.
                """

            agent_messages = history + [{"role": "user", "content": current_input}]
            try:
                print(f"DEBUG: Calling Trainee with {len(agent_messages)} messages")
                agent_response_obj = await self.llm.chat(messages=agent_messages, system=agent_system_prompt)
                agent_text = agent_response_obj.content
                print(f"DEBUG: Trainee responded: {agent_text[:50]}...")

                # Track cost
                if agent_response_obj.input_tokens and agent_response_obj.output_tokens:
                    turn_cost = (agent_response_obj.input_tokens * 0.000003) + (
                        agent_response_obj.output_tokens * 0.000015
                    )
                    session_cost += turn_cost
                else:
                    session_cost += 0.005  # Lower mock cost
            except Exception as e:
                logger.error(f"Error calling Trainee LLM: {e}")
                agent_text = f"[AGENT ERROR: {str(e)}]"
                session_cost += 0.0

            # Check Governance Guardrails
            try:
                check_limits(session_cost, turn + 1)
            except Exception as e:
                logger.warning(f"Guardrail violation: {e}")
                history.append({"role": "user", "content": current_input})
                history.append({"role": "assistant", "content": f"[SYSTEM INTERRUPTION: {str(e)}]"})
                break

            history.append({"role": "user", "content": current_input})
            history.append({"role": "assistant", "content": agent_text})

            if "[AGENT ERROR" in agent_text:
                break

            # 2. Simulator Agent (User) responds
            simulator_system_prompt = f"""
            You are playing a persona: {persona_name}.
            Behavior: {persona.get("behavior")}
            Goal: {persona.get("goal")}
            
            Stay in character. Do not break persona. Respond to the agent's message.
            Keep your responses concise and realistic for a lead.
            """

            try:
                print(f"DEBUG: Calling Simulator with {len(history)} messages")
                simulator_response_obj = await self.llm.chat(messages=history, system=simulator_system_prompt)
                current_input = simulator_response_obj.content
                print(f"DEBUG: Simulator responded: {current_input[:50]}...")
            except Exception as e:
                logger.error(f"Error calling Simulator LLM: {e}")
                current_input = "I'm sorry, I'm having trouble connecting."
                break

        # 3. Evaluator grades
        print(f"DEBUG: Calling Evaluator with {len(history)} messages")
        score = await self.evaluator.grade_conversation(history)
        score["session_cost"] = session_cost
        score["turns"] = len(history) // 2
        score["history"] = history

        return score


async def run_sparring_match(regimen_name: str, persona_name: str):
    """Legacy function support."""
    runner = DojoRunner()
    return await runner.run_sparring_match(regimen_name, persona_name)


async def run_regimen(regimen_name: str, iterations: int = 1):
    """
    Executes a training regimen with multiple iterations.
    """
    runner = DojoRunner()
    logger.info(f"Executing Regimen: {regimen_name} ({iterations} iterations)")
    results = []

    # Map regimen to persona
    persona_map = {
        "Objection Handling": "The Aggressive Investor",
        "Compliance Drills": "The Fair Housing Trap",
        "Lead Qualification": "The Vague Browser",
        "Conflict ROI Defense": "The Litigious Seller",
        "Equity Protection": "The Repair Denier",
        "International Compliance": "The International Regulatory Skeptic",
        "The Gauntlet": "The Sophisticated Global Arbitrageur",
    }

    persona_name = persona_map.get(regimen_name, "The Confused First-Timer")

    for i in range(iterations):
        score = await runner.run_sparring_match(regimen_name, persona_name)
        results.append(score)

    avg_score = sum(s["overall"] for s in results) / len(results) if results else 0
    return {"regimen": regimen_name, "iterations": iterations, "average_score": avg_score, "results": results}
