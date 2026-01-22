import streamlit as st
import json
import os
import asyncio
from datetime import datetime
from ghl_real_estate_ai.core.llm_client import get_llm_client
from ghl_real_estate_ai.core.evaluator_agent import EvaluatorAgent

st.set_page_config(page_title="Prompt Testing Lab", layout="wide")

st.title("🧪 Prompt Testing Lab")
st.markdown("Test, A/B compare, and refine your Gemini & Claude prompts.")

PROMPTS_DIR = "ghl_real_estate_ai/prompts"

def load_prompts():
    if not os.path.exists(PROMPTS_DIR):
        return []
    prompts = []
    for f in os.listdir(PROMPTS_DIR):
        if f.endswith(".json"):
            with open(os.path.join(PROMPTS_DIR, f), "r") as pf:
                prompts.append(json.load(pf))
    return sorted(prompts, key=lambda x: x["created_at"], reverse=True)

prompts = load_prompts()
prompt_names = list(set([p["name"] for p in prompts]))

mode = st.sidebar.radio("Lab Mode", ["Single Test", "A/B Compare"])

if not prompt_names:
    st.warning("No prompts found in library. Create one first!")
else:
    if mode == "Single Test":
        st.subheader("Single Prompt Testing")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            selected_name = st.selectbox("Select Prompt", prompt_names)
            versions = [p for p in prompts if p["name"] == selected_name]
            selected_version = st.selectbox("Version", [v["version"] for v in versions])
            
            p_data = next(v for v in versions if v["version"] == selected_version)
            
            persona = st.text_area("Persona", p_data["persona"], height=100)
            content = st.text_area("Prompt Content", p_data["content"], height=200)
            
            st.info("Variables like `{{property_data}}` will be replaced if found in context.")
            context_json = st.text_area("Input Context (JSON)", 
                                      '{"property_data": {"address": "123 Austin Way", "price": 450000}}',
                                      height=100)
            
        with col2:
            st.subheader("Result")
            if st.button("Run Test", type="primary"):
                with st.spinner("Generating..."):
                    try:
                        client = get_llm_client()
                        ctx = json.loads(context_json)
                        
                        final_prompt = content
                        for k, v in ctx.items():
                            final_prompt = final_prompt.replace(f"{{{{{k}}}}}", str(v))
                            
                        response = asyncio.run(client.agenerate(
                            prompt=final_prompt,
                            system_prompt=persona,
                            model="gemini-1.5-flash"
                        ))
                        
                        st.markdown(f"**Model:** {response.model}")
                        st.write(response.content)
                        
                        st.divider()
                        st.subheader("Auto-Evaluation")
                        evaluator = EvaluatorAgent()
                        eval_result = asyncio.run(evaluator.evaluate_response(
                            response_text=response.content,
                            context=ctx,
                            rubric_type="real_estate" if "sales" in p_data["tags"] else "general"
                        ))
                        
                        st.json(eval_result)
                        
                    except Exception as e:
                        st.error(f"Test failed: {e}")

    elif mode == "A/B Compare":
        st.subheader("A/B Prompt Comparison")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("### Variant A")
            name_a = st.selectbox("Prompt A", prompt_names, key="name_a")
            ver_a = st.selectbox("Version A", [v["version"] for v in prompts if v["name"] == name_a], key="ver_a")
            p_a = next(v for v in prompts if v["name"] == name_a and v["version"] == ver_a)
            
        with col_b:
            st.markdown("### Variant B")
            name_b = st.selectbox("Prompt B", prompt_names, key="name_b")
            ver_b = st.selectbox("Version B", [v["version"] for v in prompts if v["name"] == name_b], key="ver_b")
            p_b = next(v for v in prompts if v["name"] == name_b and v["version"] == ver_b)
            
        st.divider()
        context_json = st.text_area("Shared Input Context (JSON)", 
                                  '{"property_data": {"address": "123 Austin Way", "price": 450000}}',
                                  height=100, key="ab_ctx")
        
        if st.button("Run A/B Test", type="primary"):
            ctx = json.loads(context_json)
            client = get_llm_client()
            evaluator = EvaluatorAgent()
            
            res_a, res_b = st.columns(2)
            
            with res_a:
                with st.spinner("Variant A..."):
                    prompt_a = p_a["content"]
                    for k, v in ctx.items(): prompt_a = prompt_a.replace(f"{{{{{k}}}}}", str(v))
                    resp_a = asyncio.run(client.agenerate(prompt=prompt_a, system_prompt=p_a["persona"], model="gemini-1.5-flash"))
                    eval_a = asyncio.run(evaluator.evaluate_response(resp_a.content, ctx))
                    st.write(resp_a.content)
                    st.metric("Score A", f"{eval_a.get('overall_score', 0):.2f}")
                    
            with res_b:
                with st.spinner("Variant B..."):
                    prompt_b = p_b["content"]
                    for k, v in ctx.items(): prompt_b = prompt_b.replace(f"{{{{{k}}}}}", str(v))
                    resp_b = asyncio.run(client.agenerate(prompt=prompt_b, system_prompt=p_b["persona"], model="gemini-1.5-flash"))
                    eval_b = asyncio.run(evaluator.evaluate_response(resp_b.content, ctx))
                    st.write(resp_b.content)
                    st.metric("Score B", f"{eval_b.get('overall_score', 0):.2f}")
            
            score_diff = eval_a.get('overall_score', 0) - eval_b.get('overall_score', 0)
            if score_diff > 0:
                st.success(f"Winner: **Variant A** (+{abs(score_diff):.2f})")
            elif score_diff < 0:
                st.success(f"Winner: **Variant B** (+{abs(score_diff):.2f})")
            else:
                st.info("Tie!")
