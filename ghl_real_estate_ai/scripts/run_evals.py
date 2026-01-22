"""
Automated Evaluation Pipeline.
Runs prompts from the library against test cases and logs results.
"""

import asyncio
import json
import os
from ghl_real_estate_ai.core.evaluator_agent import EvaluatorAgent
from ghl_real_estate_ai.core.llm_client import get_llm_client
from ghl_real_estate_ai.core.gemini_logger import log_metrics

PROMPTS_DIR = "ghl_real_estate_ai/prompts"

async def run_evaluation_suite():
    print("🚀 Starting Gemini Stack Evaluation Suite...")
    evaluator = EvaluatorAgent()
    client = get_llm_client()
    
    # Example Test Cases (In production, these would be loaded from a JSON file)
    test_cases = [
        {
            "prompt_name": "sales_pitch",
            "context": {
                "property_data": {"address": "123 Maple St", "price": 500000, "features": ["Pool", "Modern Kitchen"]},
                "buyer_profile": {"name": "Alice", "interests": ["Outdoor living", "Cooking"]}
            },
            "rubric": "real_estate"
        }
    ]
    
    for case in test_cases:
        prompt_name = case["prompt_name"]
        print(f"  Evaluating: {prompt_name}...")
        
        # 1. Load latest prompt from library
        # (For now, we'll manually find the latest file in the directory)
        prompt_files = sorted([f for f in os.listdir(PROMPTS_DIR) if f.startswith(prompt_name)], reverse=True)
        if not prompt_files:
            print(f"    ❌ Prompt '{prompt_name}' not found in library.")
            continue
            
        with open(os.path.join(PROMPTS_DIR, prompt_files[0]), "r") as f:
            prompt_data = json.load(f)
            
        # 2. Generate response
        system_instr = prompt_data.get("persona")
        prompt_text = prompt_data.get("content").replace("{{property_data}}", str(case["context"]["property_data"]))
        prompt_text = prompt_text.replace("{{buyer_profile}}", str(case["context"]["buyer_profile"]))
        
        response = await client.agenerate(
            prompt=prompt_text,
            system_prompt=system_instr,
            model="gemini-1.5-flash"
        )
        
        # 3. Evaluate response
        eval_result = await evaluator.evaluate_response(
            response_text=response.content,
            context=case["context"],
            rubric_type=case["rubric"]
        )
        
        # 4. Log results
        accuracy = eval_result.get("overall_score", 0.0)
        print(f"    ✅ Result: {accuracy:.2%} (Pass: {eval_result.get('pass')})")
        
        # Update metrics log with the accuracy score
        log_metrics(
            provider="gemini",
            model=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            task_type=f"EVAL_{prompt_name}",
            accuracy_score=accuracy
        )

if __name__ == "__main__":
    asyncio.run(run_evaluation_suite())
