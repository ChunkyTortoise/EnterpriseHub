"""
The Sensei: Automated scoring based on protocol.
Reference: AGENT_EVALUATION_PROTOCOL.md
"""

import logging
import json
from typing import List, Dict, Any
from ghl_real_estate_ai.core.llm_client import LLMClient

logger = logging.getLogger(__name__)

class DojoEvaluator:
    """
    Evaluates agent conversations based on the AGENT_EVALUATION_PROTOCOL.
    Evolved to use an LLM 'Sensei' for qualitative feedback.
    """
    
    def __init__(self):
        self.llm = LLMClient()
    
    async def grade_conversation(self, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Grades a conversation history on multiple dimensions.
        """
        # 1. Rule-based scoring (fallback/baseline)
        agent_messages = [m['content'] for m in history if m['role'] == 'assistant']
        all_agent_text = " ".join(agent_messages).lower()
        
        scores = {
            "empathy": 4.0,
            "goal_pursuit": 3.0,
            "accuracy": 5.0,
            "compliance": 5.0,
            "tone_match": 4.0
        }
        
        # Simple heuristic: Did the agent ask about budget?
        if "budget" in all_agent_text or "price" in all_agent_text:
            scores["goal_pursuit"] = 5.0
            
        # Compliance check (Fair Housing)
        unsafe_keywords = ["safe", "demographic", "neighborhood type"]
        if any(kw in all_agent_text for kw in unsafe_keywords):
            scores["compliance"] = 1.0
            
        # 2. LLM-based 'Sensei' Evaluation
        formatted_history = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history])
        
        sensei_prompt = f"""
        You are the Dojo Sensei, an elite Real Estate Sales Coach.
        Review the following conversation between a Real Estate AI Agent (ASSISTANT) and a Lead (USER).
        
        CONVERSATION:
        {formatted_history}
        
        Evaluate the AI Agent on:
        1. Empathy: Did it acknowledge the lead's feelings?
        2. Goal Pursuit: Did it try to qualify the lead?
        3. Compliance: Did it avoid fair housing violations?
        4. Tone: Was it professional yet engaging?
        
        Provide your evaluation in JSON format:
        {{
            "scores": {{
                "empathy": float (1-5),
                "goal_pursuit": float (1-5),
                "accuracy": float (1-5),
                "compliance": float (1-5),
                "tone_match": float (1-5)
            }},
            "feedback": "Concise qualitative feedback",
            "coaching_tips": ["Tip 1", "Tip 2"]
        }}
        """
        
        try:
            response = await self.llm.agenerate(
                prompt=sensei_prompt,
                model="gemini-2.0-flash", # Use fast model for evaluation
                temperature=0.1
            )
            
            # Extract JSON from response
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            llm_eval = json.loads(content)
            scores.update(llm_eval.get("scores", {}))
            feedback = llm_eval.get("feedback", "N/A")
            coaching_tips = llm_eval.get("coaching_tips", [])
        except Exception as e:
            logger.error(f"Sensei LLM Evaluation failed: {e}")
            feedback = "LLM Evaluation unavailable."
            coaching_tips = ["Rule-based fallback active."]

        scores["overall"] = sum(scores.values()) / len(scores)
        
        return {
            "scores": scores,
            "overall": scores["overall"],
            "feedback": feedback,
            "coaching_tips": coaching_tips
        }
