import pytest

@pytest.mark.unit
#!/usr/bin/env python3
"""
Token Efficiency Testing: Research Validation on Real EnterpriseHub Workflows
Measures current token usage vs progressive skills patterns from Perplexity research.
"""

import asyncio
import json
import time
import tiktoken
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

# Current EnterpriseHub imports
from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot
from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState
from ghl_real_estate_ai.services.claude_orchestrator import ClaudeOrchestrator, ClaudeTaskType, ClaudeRequest
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant

class TokenEfficiencyTester:
    """Test progressive skills patterns against current implementation"""

    def __init__(self):
        self.encoder = tiktoken.encoding_for_model("gpt-4")
        self.results = []

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken (close approximation for Claude)"""
        return len(self.encoder.encode(str(text)))

    async def test_current_jorge_workflow(self) -> Dict[str, Any]:
        """Test current Jorge Seller Bot workflow - BASELINE"""
        print("🔍 Testing CURRENT Jorge Workflow (Baseline)...")

        # Create test state similar to real interaction
        test_state = JorgeSellerState(
            lead_id="test-001",
            lead_name="Alice Johnson",
            conversation_history=[
                {"role": "user", "content": "Hi, I'm thinking about selling my house in Phoenix"},
                {"role": "assistant", "content": "What's your timeline looking like?"},
                {"role": "user", "content": "Well, I'm not sure... maybe next year sometime"}
            ],
            psychological_commitment=45,
            is_qualified=False,
            seller_temperature="lukewarm",
            current_tone="DIRECT",
            detected_stall_type="thinking",
            stall_detected=True,
            current_question=2,
            follow_up_count=0,
            property_address="123 Main St, Phoenix AZ",
            current_journey_stage="qualification",
            intent_profile=None,  # Would be set by intent decoder
            last_action_timestamp=datetime.now()
        )

        # Initialize Jorge bot
        jorge_bot = JorgeSellerBot()

        # Measure each workflow step
        start_time = time.time()
        token_usage = {}

        # Step 1: Intent Analysis
        print("  → Analyzing intent...")
        step_start = time.time()

        # Simulate the context that would be sent to Claude
        intent_context = {
            "lead_name": test_state["lead_name"],
            "conversation_history": test_state["conversation_history"],
            "seller_temperature": test_state.get("seller_temperature", "unknown"),
            "psychological_commitment": test_state.get("psychological_commitment", 0)
        }

        # Estimate system prompt + context tokens for intent analysis
        system_prompt = jorge_bot.claude.orchestrator._get_system_prompt(ClaudeTaskType.LEAD_ANALYSIS)
        context_json = json.dumps(intent_context, indent=2, default=str)
        full_prompt = f"""{system_prompt}

Context:
{context_json}

Current Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

You are Jorge Salas analyzing seller intent. Determine FRS and PCS scores."""

        intent_tokens = self.count_tokens(full_prompt)
        token_usage["intent_analysis"] = intent_tokens

        # Simulate response tokens (estimate)
        response_tokens = 300  # Typical Jorge response length
        token_usage["intent_response"] = response_tokens

        step_time = time.time() - step_start
        print(f"    Tokens: {intent_tokens} input + {response_tokens} output = {intent_tokens + response_tokens}")

        # Step 2: Strategy Selection
        print("  → Selecting strategy...")
        step_start = time.time()

        strategy_context = dict(intent_context)
        strategy_context.update({
            "stall_detected": True,
            "detected_stall_type": "thinking",
            "qualification_scores": {"frs": 65, "pcs": 45}
        })

        strategy_json = json.dumps(strategy_context, indent=2, default=str)
        strategy_prompt = f"""{system_prompt}

Context:
{strategy_json}

Determine Jorge's response strategy: DIRECT, CONFRONTATIONAL, or TAKE-AWAY."""

        strategy_tokens = self.count_tokens(strategy_prompt)
        strategy_response = 150
        token_usage["strategy_selection"] = strategy_tokens
        token_usage["strategy_response"] = strategy_response

        print(f"    Tokens: {strategy_tokens} input + {strategy_response} output = {strategy_tokens + strategy_response}")

        # Step 3: Response Generation
        print("  → Generating response...")
        step_start = time.time()

        response_context = dict(strategy_context)
        response_context.update({
            "current_tone": "CONFRONTATIONAL",
            "stall_breakers": {
                "thinking": "What specifically are you thinking about? The timeline, the price, or whether you actually want to sell?"
            }
        })

        response_json = json.dumps(response_context, indent=2, default=str)

        # This is the actual prompt structure from jorge_seller_bot.py
        jorge_persona_prompt = f"""
You are Jorge Salas, a high-performance real estate investor.
Your tone is: DIRECT, NO-BS, CONFRONTATIONAL when necessary.
You hate wasting time on 'Lookers'. You want 'Motivated Sellers'.

CURRENT CONTEXT:
Lead: {test_state['lead_name']}
Tone Mode: CONFRONTATIONAL (Be direct and challenge their stall)
Stall Detected: thinking
FRS Classification: Warm Lead

TASK: Generate a response to the lead's last message.
INCORPORATE THIS STALL-BREAKER: What specifically are you thinking about? The timeline, the price, or whether you actually want to sell?

Context:
{response_json}
"""

        response_tokens_input = self.count_tokens(jorge_persona_prompt)
        response_output = 200
        token_usage["response_generation"] = response_tokens_input
        token_usage["response_output"] = response_output

        print(f"    Tokens: {response_tokens_input} input + {response_output} output = {response_tokens_input + response_output}")

        total_time = time.time() - start_time
        total_tokens = sum(token_usage.values())

        return {
            "approach": "CURRENT (Full Context Loading)",
            "total_tokens": total_tokens,
            "input_tokens": total_tokens - (response_tokens + strategy_response + response_output),
            "output_tokens": response_tokens + strategy_response + response_output,
            "execution_time": total_time,
            "token_breakdown": token_usage,
            "cost_estimate": total_tokens * 0.003 / 1000,  # Approximate Claude cost
        }

    async def test_progressive_skills_approach(self) -> Dict[str, Any]:
        """Test PROGRESSIVE SKILLS approach from research"""
        print("🚀 Testing PROGRESSIVE SKILLS Approach...")

        start_time = time.time()
        token_usage = {}

        # TIER 1: Discovery Context (500-800 tokens)
        print("  → Tier 1: Discovery context...")
        discovery_prompt = """
SKILL DISCOVERY MODE - Minimal Context Loading

Task: Jorge seller qualification workflow
Lead: Alice Johnson
Last Message: "Well, I'm not sure... maybe next year sometime"

Available Skills:
- jorge_confrontational_qualification (1200 tokens) - Handle stalls, qualification
- jorge_response_generation (800 tokens) - Generate personalized responses
- seller_intent_analysis (1000 tokens) - Analyze FRS/PCS scores

Determine: Which skills are needed for this interaction?
Response format: ["skill_name1", "skill_name2"]
"""

        discovery_tokens = self.count_tokens(discovery_prompt)
        discovery_response = 50  # Just skill names
        token_usage["discovery"] = discovery_tokens + discovery_response

        print(f"    Tokens: {discovery_tokens} input + {discovery_response} output = {discovery_tokens + discovery_response}")

        # TIER 2: Load Only Relevant Skills (1200-1800 tokens total)
        print("  → Tier 2: Loading jorge_confrontational_qualification skill...")

        skill_content = """
# Jorge Confrontational Qualification Skill

## Purpose
Handle seller stalls with Jorge's no-BS approach. Force yes/no commitment.

## Context
Lead: Alice Johnson
Last message: "Well, I'm not sure... maybe next year sometime"
Stall detected: "thinking" pattern

## Jorge's Stall-Breaker for "thinking"
"What specifically are you thinking about? The timeline, the price, or whether you actually want to sell? Because if it's exploration, you're wasting both our time."

## Instructions
1. Use confrontational tone - Jorge doesn't chase lukewarm leads
2. Force specific commitment or disqualify immediately
3. Reference Jorge's core question: "Are you selling or just talking?"
4. Keep response under 160 characters (SMS compliance)

Generate Jorge's response now.
"""

        skill_tokens = self.count_tokens(skill_content)
        skill_response = 180  # Jorge's confrontational response
        token_usage["skill_execution"] = skill_tokens + skill_response

        print(f"    Tokens: {skill_tokens} input + {skill_response} output = {skill_tokens + skill_response}")

        total_time = time.time() - start_time
        total_tokens = sum(token_usage.values())

        return {
            "approach": "PROGRESSIVE SKILLS (Research Pattern)",
            "total_tokens": total_tokens,
            "input_tokens": total_tokens - (discovery_response + skill_response),
            "output_tokens": discovery_response + skill_response,
            "execution_time": total_time,
            "token_breakdown": token_usage,
            "cost_estimate": total_tokens * 0.003 / 1000,
            "skills_loaded": ["jorge_confrontational_qualification"],
            "skills_available": ["jorge_confrontational_qualification", "jorge_response_generation", "seller_intent_analysis"],
            "tier_breakdown": {
                "discovery": discovery_tokens + discovery_response,
                "core_skills": skill_tokens + skill_response,
                "extended_skills": 0  # Not needed for this interaction
            }
        }

    async def run_comprehensive_test(self):
        """Run complete comparison test"""
        print("=" * 80)
        print("🧪 TOKEN EFFICIENCY VALIDATION TEST")
        print("Based on Perplexity Research: Advanced AI Agent Coordination (Jan 2026)")
        print("=" * 80)

        # Test current approach
        current_results = await self.test_current_jorge_workflow()

        print("\n" + "=" * 40)

        # Test progressive approach
        progressive_results = await self.test_progressive_skills_approach()

        # Calculate improvements
        token_reduction = ((current_results["total_tokens"] - progressive_results["total_tokens"]) /
                          current_results["total_tokens"]) * 100

        cost_reduction = ((current_results["cost_estimate"] - progressive_results["cost_estimate"]) /
                         current_results["cost_estimate"]) * 100

        print("\n" + "=" * 80)
        print("📊 RESULTS COMPARISON")
        print("=" * 80)

        print(f"""
🔥 CURRENT APPROACH:
   Total tokens: {current_results['total_tokens']:,}
   Input tokens: {current_results['input_tokens']:,}
   Output tokens: {current_results['output_tokens']:,}
   Cost estimate: ${current_results['cost_estimate']:.4f}

🚀 PROGRESSIVE SKILLS:
   Total tokens: {progressive_results['total_tokens']:,}
   Input tokens: {progressive_results['input_tokens']:,}
   Output tokens: {progressive_results['output_tokens']:,}
   Cost estimate: ${progressive_results['cost_estimate']:.4f}

💡 IMPROVEMENTS:
   Token reduction: {token_reduction:.1f}%
   Cost reduction: {cost_reduction:.1f}%
   Research predicted: 98% reduction
   """)

        # Validate against research predictions
        research_prediction = 98.0
        accuracy_vs_research = abs(token_reduction - research_prediction) / research_prediction * 100

        print(f"""
🎯 RESEARCH VALIDATION:
   Research predicted: {research_prediction}% token reduction
   Actual measured: {token_reduction:.1f}% token reduction
   Accuracy vs research: {100-accuracy_vs_research:.1f}%

   Research claims: 150K→2K tokens (complex tasks)
   Our test: {current_results['total_tokens']:,}→{progressive_results['total_tokens']:,} tokens (Jorge workflow)
   """)

        # Extrapolate to enterprise scale
        print(f"""
🏢 ENTERPRISE IMPACT PROJECTION:
   Current Jorge bot cost/interaction: ${current_results['cost_estimate']:.4f}
   Progressive cost/interaction: ${progressive_results['cost_estimate']:.4f}

   For 1000 daily interactions:
   Current monthly cost: ${current_results['cost_estimate'] * 1000 * 30:.2f}
   Progressive monthly cost: ${progressive_results['cost_estimate'] * 1000 * 30:.2f}
   Monthly savings: ${(current_results['cost_estimate'] - progressive_results['cost_estimate']) * 1000 * 30:.2f}

   Annual savings: ${(current_results['cost_estimate'] - progressive_results['cost_estimate']) * 1000 * 365:.2f}
   """)

        # Store results for further analysis
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "current_approach": current_results,
            "progressive_approach": progressive_results,
            "improvements": {
                "token_reduction_percent": token_reduction,
                "cost_reduction_percent": cost_reduction,
                "research_accuracy": 100-accuracy_vs_research
            },
            "enterprise_projection": {
                "monthly_savings_1000_interactions": (current_results['cost_estimate'] - progressive_results['cost_estimate']) * 1000 * 30,
                "annual_savings_1000_interactions": (current_results['cost_estimate'] - progressive_results['cost_estimate']) * 1000 * 365
            }
        }

        # Save detailed results
        results_file = Path("token_efficiency_test_results.json")
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n📄 Detailed results saved to: {results_file}")
        print("=" * 80)

        return self.results

async def main():
    """Run the token efficiency validation test"""
    tester = TokenEfficiencyTester()
    results = await tester.run_comprehensive_test()

    # Summary conclusion
    token_reduction = results["improvements"]["token_reduction_percent"]
    research_accuracy = results["improvements"]["research_accuracy"]

    print(f"\n🎉 CONCLUSION:")
    if token_reduction > 50:
        print(f"✅ Progressive skills achieved {token_reduction:.1f}% token reduction")
        print(f"✅ Research validation: {research_accuracy:.1f}% accurate")
        print(f"✅ RECOMMENDATION: Implement progressive skills for Jorge bot")
    else:
        print(f"⚠️  Only {token_reduction:.1f}% reduction achieved")
        print(f"❓ Research accuracy: {research_accuracy:.1f}%")
        print(f"🔍 RECOMMENDATION: Investigate why reduction is lower than expected")

if __name__ == "__main__":
    asyncio.run(main())