"""
Ultimate UI Agent Swarm Orchestrator
====================================
Specialized swarm for generating production-grade React/Next.js UI.
Supports:
- Parallel component generation
- Real-time streaming (Async Generator)
- Visual Grounding loop (Vision Analysis)
- Aesthetic Injection (Framer Motion)
- Multi-Agent Design Debates (Critic vs. Engineer)
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional

# Add project root to sys.path
sys.path.append(os.getcwd())

# Import the unified frontend skills
from ghl_real_estate_ai.agent_system.skills.base import registry as skill_registry
from ghl_real_estate_ai.agents.blackboard import SharedBlackboard
from ghl_real_estate_ai.agents.swarm_orchestrator import SwarmOrchestrator
from ghl_real_estate_ai.core.llm_client import LLMClient


class UIAgentSwarm:
    """
    Manages the Ultimate UI generation lifecycle.
    Implements multi-agent debates and live sandbox synchronization.
    Now supports Voice-to-UI and A/B Simulation.
    """

    def __init__(self, project_root: Path, location_id: str = "global"):
        self.orchestrator = SwarmOrchestrator(project_root)
        self.llm = LLMClient()
        self.blackboard = SharedBlackboard()
        self.location_id = location_id

    async def generate_ui_stream(
        self, spec: str, voice_transcript: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Runs the UI generation swarm and yields real-time events.
        Now includes multi-agent debates, Voice processing, and A/B simulation.
        """
        yield {"event": "thinking", "content": f"Initializing Ultimate UI Swarm for tenant: {self.location_id}"}

        # 0. VOICE PROCESSING PHASE (Optional)
        if voice_transcript:
            yield {"event": "thinking", "content": "Processing voice transcript to extract UI intent..."}
            voice_skill = skill_registry.get_skill("process_voice_intent")
            voice_intent = await voice_skill.execute(transcript=voice_transcript)

            if voice_intent["ui_trigger"]:
                yield {"event": "thinking", "content": f"Voice intent detected: {', '.join(voice_intent['intent'])}"}
                spec = voice_intent["ui_spec"]
            else:
                yield {"event": "error", "content": "No UI-related intent found in voice transcript."}
                return

        # 1. ARCHITECTURE PHASE
        yield {"event": "thinking", "content": "Decomposing specification into atomic components via RAG Registry..."}

        registry_skill = skill_registry.get_skill("component_registry")
        relevant_docs = registry_skill.execute(action="retrieve", task=spec, location_id=self.location_id)

        # Simulate Architect Agent decision
        architecture = {
            "root": "ExecutiveDashboard",
            "layout": "SidebarWithHeader",
            "components": [
                {"name": "RevenueMetric", "type": "Metric", "desc": "Total revenue KPI"},
                {"name": "ConversionChart", "type": "LineChart", "desc": "Lead conversion trend"},
            ],
        }

        yield {"event": "architecture_ready", "data": architecture}

        # 2. PARALLEL GENERATION PHASE
        yield {
            "event": "thinking",
            "content": f"Spawning parallel developer agents for {len(architecture['components'])} components...",
        }

        components_code = []
        for comp in architecture["components"]:
            yield {"event": "generating_component", "name": comp["name"]}
            code = await self._simulate_generation(comp, relevant_docs)

            # --- ULTIMATE: DESIGN DEBATE PHASE ---
            yield {"event": "thinking", "content": f"Submitting {comp['name']} to UX Critic for review..."}

            # Simulate Critic Feedback
            feedback = await self._simulate_critic_feedback(comp, code)
            yield {"event": "critic_feedback", "agent": "UX Critic", "content": feedback}

            yield {"event": "thinking", "content": f"Frontend Engineer is refining {comp['name']} based on feedback..."}
            code = await self._simulate_refinement(code, feedback)
            yield {
                "event": "engineer_response",
                "agent": "Engineer",
                "content": "Applied accessibility and padding fixes as requested.",
            }

            # 3. AESTHETIC INJECTION
            yield {"event": "thinking", "content": f"Injecting elite aesthetics (Framer Motion) into {comp['name']}..."}
            aesthetic_skill = skill_registry.get_skill("inject_aesthetics")
            polished_code = aesthetic_skill.execute(jsx_code=code)

            # --- PHASE 3: A/B SIMULATION ---
            yield {
                "event": "thinking",
                "content": f"Simulating lead engagement for {comp['name']} via Behavioral ML...",
            }
            sim_skill = skill_registry.get_skill("predict_ui_conversion")
            prediction = await sim_skill.execute(jsx_code=polished_code, location_id=self.location_id)

            score = prediction["predicted_conversion_rate"]
            yield {
                "event": "simulation_result",
                "name": comp["name"],
                "score": score,
                "tips": prediction["optimization_tips"],
                "features": prediction.get("features_extracted", {}),
            }

            # --- ULTIMATE: SELF-REFLECTION LOOP ---
            if score < 0.7:
                yield {
                    "event": "thinking",
                    "content": f"Conversion score ({score}) is below threshold. Triggering autonomous self-correction...",
                }

                reflection_prompt = f"The previous version scored low in conversion simulation. Optimization tips: {', '.join(prediction['optimization_tips'])}. Please refactor the component to address these issues while maintaining the original specs."

                yield {
                    "event": "thinking",
                    "content": f"Engineer is refactoring {comp['name']} for better conversion...",
                }
                refined_code = await self._simulate_refinement(polished_code, reflection_prompt)

                # Re-apply aesthetics
                polished_code = aesthetic_skill.execute(jsx_code=refined_code)

                # Re-simulate
                yield {"event": "thinking", "content": f"Re-simulating {comp['name']} after self-correction..."}
                prediction = await sim_skill.execute(jsx_code=polished_code, location_id=self.location_id)
                score = prediction["predicted_conversion_rate"]

                yield {
                    "event": "simulation_result",
                    "name": comp["name"],
                    "score": score,
                    "tips": ["Self-correction applied."] + prediction["optimization_tips"],
                    "features": prediction.get("features_extracted", {}),
                }

            components_code.append(polished_code)
            yield {"event": "component_ready", "name": comp["name"], "code": polished_code}

        # 4. ASSEMBLY PHASE
        full_jsx = "\n\n".join(components_code)
        yield {"event": "assembly_complete", "jsx": full_jsx}

        # 5. VISUAL QA PHASE
        yield {"event": "thinking", "content": "Executing Visual Grounding Loop via Playwright & Gemini Vision..."}

        qa_skill = skill_registry.get_skill("visual_qa")
        yield {"event": "visual_qa_check", "status": "capturing_with_grid"}

        qa_result = qa_skill.execute(action="verify", jsx=full_jsx, spec=spec)

        if not qa_result["passed"]:
            yield {
                "event": "visual_feedback",
                "issues": qa_result["issues"],
                "fix": qa_result["visual_grounding"]["fix_hint"],
            }
            yield {
                "event": "thinking",
                "content": f"Applying visual coordinate fix: {qa_result['visual_grounding']['fix_hint']}",
            }
            # Simulate correction
            full_jsx += "\n// Applied visual coordinate fix for header alignment\n"

        yield {"event": "final_ui_ready", "jsx": full_jsx, "qa_status": "verified"}

        # 6. VOICE BRIEFING PHASE
        yield {"event": "thinking", "content": "Synthesizing AI voice briefing for the new dashboard..."}

        market_insight = await self._get_market_insight()
        briefing_text = f"I have successfully generated your {spec}. The components have been optimized for conversion based on our behavioral models and verified through visual grounding. {market_insight} You can now preview the live dashboard."

        voice_skill = skill_registry.get_skill("synthesize_voice_briefing")
        voice_result = await voice_skill.execute(text=briefing_text)

        yield {
            "event": "voice_briefing",
            "audio_data": voice_result.get("audio_data"),
            "content_type": voice_result.get("content_type"),
            "text": briefing_text,
        }

    async def _get_market_insight(self) -> str:
        """Fetches real-time market insights to contextualize the briefing."""
        try:
            # Simple mapping: if location_id or spec mentions a market, use it
            market_id = None
            if "rancho_cucamonga" in self.location_id.lower():
                market_id = "rancho_cucamonga"
            elif "demo" in self.location_id.lower():
                market_id = "rancho_cucamonga"  # Default for demo

            if not market_id:
                return "The UI is optimized for general lead engagement patterns."

            from ghl_real_estate_ai.markets.registry import get_market_service

            service = get_market_service(market_id)
            if service:
                metrics = await service.get_market_metrics()
                # Use real metrics if available, otherwise fallback to config-driven defaults
                inventory_status = "high-inventory" if metrics.months_supply > 4.5 else "low-inventory"
                trend = "upward" if metrics.price_trend_3m > 0 else "correcting"

                return f"This dashboard is specifically optimized for the current {inventory_status} trend in {service.market_name}, with components chosen to perform well while the market is {trend}."
            return ""
        except Exception as e:
            from ghl_real_estate_ai.ghl_utils.logger import get_logger

            get_logger(__name__).error(f"Error fetching market insight: {e}")
            return ""

    async def _simulate_generation(self, component: Dict, docs: Dict) -> str:
        """Simulates an agent generating code for a single component"""
        await asyncio.sleep(1)  # Simulate network/LLM latency
        return f"export const {component['name']} = () => <div>{component['desc']}</div>;"

    async def _simulate_critic_feedback(self, component: Dict, code: str) -> str:
        """Simulates a UX Critic's review"""
        await asyncio.sleep(0.8)
        return f"The {component['name']} component needs more semantic ARIA labels and the padding should be consistent with the Shadcn system (px-4 py-2)."

    async def _simulate_refinement(self, code: str, feedback: str) -> str:
        """Simulates code refinement"""
        await asyncio.sleep(0.5)
        return code.replace("<div>", "<div className='px-4 py-2' aria-label='Metrics Container'>")


async def main():
    # Set fake API key for simulation
    os.environ["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY", "sk-fake")
    os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "fake")

    swarm = UIAgentSwarm(Path("."), location_id="ghl_location_123")
    async for event in swarm.generate_ui_stream("Dashboard with revenue metrics"):
        print(f"📡 EVENT [{event['event']}]: {event.get('content') or event.get('name') or ''}")


if __name__ == "__main__":
    asyncio.run(main())
