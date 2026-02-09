"""
Evaluator Agent for GHL Real Estate AI.
Judges output quality based on domain-specific rubrics.
"""

import json
from typing import Any, Dict

from ghl_real_estate_ai.core.llm_client import get_llm_client


class EvaluatorAgent:
    """
    AI Agent that evaluates LLM outputs against a set of criteria.
    """

    def __init__(self, model: str = "gemini-1.5-flash"):
        self.client = get_llm_client()
        self.model = model

    async def evaluate_response(
        self, response_text: str, context: Dict[str, Any], rubric_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Evaluate a response using a specific rubric.
        """
        rubrics = {
            "real_estate": {
                "correctness": "Does the response accurately reflect property details and market data?",
                "professionalism": "Is the tone suitable for a high-end real estate agent?",
                "persuasiveness": "Does it highlight the property's unique value propositions?",
                "ghl_compliance": "Does it follow GHL interaction rules (e.g., short SMS limits)?",
            },
            "general": {
                "accuracy": "Is the information factually correct?",
                "clarity": "Is the response easy to understand?",
                "completeness": "Does it address all parts of the user's request?",
            },
        }

        selected_rubric = rubrics.get(rubric_type, rubrics["general"])

        prompt = f"""
You are an expert quality evaluator for a Real Estate AI system.
Evaluate the following AI-generated response based on the provided rubric.

[AI RESPONSE]
{response_text}

[CONTEXT]
{json.dumps(context, indent=2)}

[RUBRIC]
{json.dumps(selected_rubric, indent=2)}

Return a JSON object with scores (0.0 to 1.0) for each criterion and a brief 'reasoning' for each.
Include an 'overall_score' and a 'pass' boolean (True if overall_score >= 0.8).
"""

        # Use Flash for cost-effective evaluation
        eval_resp = await self.client.agenerate(
            prompt=prompt,
            model=self.model,
            response_schema={
                "type": "object",
                "properties": {
                    "scores": {"type": "object"},
                    "reasoning": {"type": "object"},
                    "overall_score": {"type": "number"},
                    "pass": {"type": "boolean"},
                },
                "required": ["scores", "overall_score", "pass"],
            },
        )

        try:
            return json.loads(eval_resp.content)
        except Exception as e:
            return {"error": f"Failed to parse evaluation: {e}", "raw_response": eval_resp.content, "pass": False}


async def auto_evaluate_hook(ctx_output: Any, metadata: Dict[str, Any]):
    """
    Example of a post-generation hook that triggers evaluation.
    """
    if metadata.get("eval_required"):
        evaluator = EvaluatorAgent()
        result = await evaluator.evaluate_response(
            response_text=ctx_output.content,
            context=metadata.get("context", {}),
            rubric_type=metadata.get("rubric", "general"),
        )
        return result
    return None
