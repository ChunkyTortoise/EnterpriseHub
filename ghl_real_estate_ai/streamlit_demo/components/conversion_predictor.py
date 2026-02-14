import datetime
import random

import plotly.graph_objects as go
import streamlit as st

from ghl_real_estate_ai.streamlit_demo.async_utils import run_async


def random_page_views(lead_id):
    random.seed(str(lead_id))
    return random.randint(5, 30)


def random_opens(lead_id):
    random.seed(str(lead_id) + "_opens")
    return random.randint(2, 15)


def render_conversion_predictor(services, selected_lead_name, analysis_result=None):
    """
    Renders the Predictive Conversion Insights tab.
    Offers deep statistical modeling, timeline visualization, and next best action logic.
    """
    st.markdown("### 🔮 Predictive Conversion Insights")
    st.markdown("*Statistical modeling of future lead actions and conversion probability*")

    if selected_lead_name == "-- Select a Lead --":
        st.info("Select a lead to view predictions")
        return

    # Use analysis_result if provided, otherwise run predictive models
    if analysis_result:
        prediction = {
            "probability": analysis_result.success_probability,
            "delta": 5,  # Mock delta
            "factors": {
                "ML Confidence": analysis_result.ml_conversion_score,
                "Engagement": analysis_result.engagement_score,
                "Qualification": analysis_result.jorge_score * 14.2,  # Normalize 7 to ~100
                "Retention": 100 - analysis_result.churn_risk_score,
            },
            "confidence": analysis_result.confidence_score,
            "timeline": analysis_result.expected_timeline,
            "next_action": analysis_result.next_best_action,
            "risk_factors": analysis_result.risk_factors,
            "opportunities": analysis_result.opportunities,
        }
    else:
        # Call predictive service
        with st.spinner("Running predictive models..."):
            # Resolve lead data from session state
            lead_options = st.session_state.get("lead_options", {})
            lead_data_raw = lead_options.get(selected_lead_name, {})
            lead_id = lead_data_raw.get("lead_id", "demo_lead")

            # Use Dynamic Scoring or Intent Scoring if available
            scorer = services["predictive_scorer"]
            if hasattr(scorer, "score_lead_with_intent"):
                try:
                    # Try async intent scoring

                    # Mock conversation history for demo
                    history = [
                        {
                            "role": "user",
                            "content": "I'm looking for a home in Rancho Cucamonga with a $500k budget. Must have a pool.",
                        },
                        {"role": "assistant", "content": "I can help with that! When are you planning to move?"},
                        {"role": "user", "content": "Within the next 45 days. I'm already pre-approved."},
                    ]

                    lead_data = {
                        "id": lead_id,
                        "budget": lead_data_raw.get("extracted_preferences", {}).get("budget", 0),
                        "location": lead_data_raw.get("extracted_preferences", {}).get("location", "Rancho Cucamonga, CA"),
                        "page_views": random_page_views(lead_id),
                        "email_opens": random_opens(lead_id),
                    }

                    intent_score = run_async(scorer.score_lead_with_intent(lead_id, lead_data, history))
                    prediction = {
                        "probability": intent_score.score,
                        "delta": 8,  # Higher delta due to new intent detection
                        "factors": {f["name"]: f["impact"] for f in intent_score.factors},
                        "confidence": intent_score.confidence,
                        "timeline": "45 Days",
                        "next_action": intent_score.recommendations[0],
                    }
                except Exception as e:
                    prediction = scorer.predict_next_action(lead_id)
                    prediction["confidence"] = 0.85
            elif hasattr(scorer, "score_lead_dynamic"):
                prediction = scorer.predict_next_action(lead_id)
                prediction["confidence"] = 0.85  # Default
                prediction["timeline"] = "45 Days"
                prediction["next_action"] = "Schedule follow-up"

    col1, col2 = st.columns([1, 1.2])

    with col1:
        # 1. Conversion Probability Gauge - Obsidian Style
        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

        st.markdown("#### CONFIDENCE SCORE")

        prob_value = prediction["probability"]
        delta_val = prediction.get("delta", 5)

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=prob_value,
                ontario_mills={"x": [0, 1], "y": [0, 1]},
                title={"text": "WIN PROBABILITY", "font": {"color": "#8B949E", "size": 12, "family": "Space Grotesk"}},
                delta={"reference": prob_value - delta_val, "increasing": {"color": "#10b981"}},
                number={"font": {"size": 44, "color": "#FFFFFF", "family": "Space Grotesk"}},
                gauge={
                    "axis": {"range": [None, 100], "tickwidth": 1, "tickcolor": "#8B949E"},
                    "bar": {"color": "#6366F1"},
                    "bgcolor": "rgba(255,255,255,0.05)",
                    "borderwidth": 1,
                    "bordercolor": "rgba(255,255,255,0.1)",
                    "steps": [
                        {"range": [0, 40], "color": "rgba(239, 68, 68, 0.1)"},
                        {"range": [40, 70], "color": "rgba(245, 158, 11, 0.1)"},
                        {"range": [70, 100], "color": "rgba(16, 185, 129, 0.1)"},
                    ],
                    "threshold": {"line": {"color": "#10b981", "width": 4}, "thickness": 0.75, "value": 90},
                },
            )
        )

        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)

        # 2. Key Risk Factors - Obsidian Style
        st.markdown("#### 🎯 IMPACT FACTORS")
        factors = prediction.get("factors", {})

        # Sort factors by impact
        sorted_factors = sorted(factors.items(), key=lambda x: abs(x[1]), reverse=True)

        for factor, impact in sorted_factors:
            color = "#10b981" if impact > 0 else "#ef4444"
            bar_width = min(abs(impact) * 4, 100)

            st.markdown(
                f"""
            <div style='margin-bottom: 12px;'>
                <div style='display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 6px;'>
                    <span style='color: #E6EDF3; font-weight: 600; font-size: 0.85rem; font-family: "Inter", sans-serif;'>{factor.upper()}</span>
                    <span style='color: {color}; font-weight: 700; font-family: "Space Grotesk", sans-serif;'>{"+" if impact > 0 else ""}{impact:.0f}%</span>
                </div>
                <div style='background: rgba(255,255,255,0.05); height: 6px; border-radius: 3px; position: relative; overflow: hidden; border: 1px solid rgba(255,255,255,0.02);'>
                    <div style='background: {color}; width: {bar_width}%; height: 100%; position: absolute; {"left: 0;" if impact > 0 else "right: 0;"} box-shadow: 0 0 10px {color}40;'></div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    with col2:
        # 3. Enhanced Timeline - Obsidian Style
        st.markdown("#### ⏱️ CONVERSION POTENTIAL")

        # Determine days based on probability or timeline text
        prob_val_float = float(prob_value) / 100

        timeline_text = prediction.get("timeline", "45 Days")
        import re

        days_match = re.search(r"(\d+)", timeline_text)
        if days_match:
            estimated_days = int(days_match.group(1))
        else:
            estimated_days = 45 if prob_val_float > 0.7 else 90 if prob_val_float > 0.4 else 120

        target_date = (datetime.datetime.now() + datetime.timedelta(days=estimated_days)).strftime("%b %d")

        # Predicted Deal Value calculation
        predicted_value = 850000 if "Luxury" in selected_lead_name or "Williams" in selected_lead_name else 450000
        risk_adjusted_value = predicted_value * prob_val_float

        st.markdown(
            f"""
        <div style='background: rgba(22, 27, 34, 0.7); 
                    padding: 2rem; border-radius: 16px; color: #FFFFFF; margin-bottom: 2rem; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6); backdrop-filter: blur(12px);'>
            <div style='display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1.5rem;'>
                <div>
                    <div style='font-size: 0.75rem; color: #8B949E; text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif; font-weight: 700;'>Estimated Timeline</div>
                    <div style='font-size: 2rem; font-weight: 700; line-height: 1.1; margin-top: 8px; font-family: "Space Grotesk", sans-serif; color: #6366F1;'>{timeline_text.upper()}</div>
                </div>
                <div style='text-align: right;'>
                    <div style='background: rgba(99, 102, 241, 0.15); color: #6366F1; padding: 6px 14px; border-radius: 8px; font-size: 0.75rem; font-weight: 700; border: 1px solid rgba(99, 102, 241, 0.3); font-family: "Space Grotesk", sans-serif;'>
                        TARGET: {target_date.upper()}
                    </div>
                </div>
            </div>
            
            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 1.5rem;'>
                <div>
                    <div style='font-size: 0.7rem; color: #8B949E; text-transform: uppercase; letter-spacing: 0.05em; font-family: "Space Grotesk", sans-serif; font-weight: 700;'>Predicted Value</div>
                    <div style='font-size: 1.25rem; font-weight: 700; color: #FFFFFF; font-family: "Space Grotesk", sans-serif;'>${predicted_value:,.0f}</div>
                    <div style='font-size: 0.75rem; color: #10b981; font-weight: 600; margin-top: 2px;'>Risk-Adj: ${risk_adjusted_value:,.0f}</div>
                </div>
                <div style='text-align: right;'>
                    <div style='font-size: 0.7rem; color: #8B949E; text-transform: uppercase; letter-spacing: 0.05em; font-family: "Space Grotesk", sans-serif; font-weight: 700;'>Contact Window</div>
                    <div style='font-size: 1.25rem; font-weight: 700; color: #FFFFFF; font-family: "Space Grotesk", sans-serif;'>TUE @ 2:15 PM</div>
                    <div style='font-size: 0.75rem; color: #6366F1; font-weight: 600; margin-top: 2px;'>MAX SIGNAL ZONE</div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # 4. Next Best Actions - Obsidian Style
        st.markdown("#### 🚀 RECOMMENDED STRATEGY")

        card_style = "background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 16px; border-radius: 12px; margin-bottom: 12px; display: flex; align-items: center; gap: 15px; transition: all 0.2s ease;"

        if analysis_result and analysis_result.recommended_actions:
            for action_item in analysis_result.recommended_actions[:3]:
                action_title = action_item.get("action", "Follow up")
                priority = action_item.get("priority", "medium")
                st.markdown(
                    f"""
                <div style='{card_style}'>
                    <div style='background: rgba(99, 102, 241, 0.1); width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; border: 1px solid rgba(99, 102, 241, 0.2);'>
                        🎯
                    </div>
                    <div style='flex: 1;'>
                        <div style='font-weight: 700; font-size: 0.95rem; color: #FFFFFF; font-family: "Space Grotesk", sans-serif;'>{action_title.upper()}</div>
                        <div style='font-size: 0.8rem; color: #8B949E; font-family: "Inter", sans-serif;'>Claude synthesis based on node trajectory.</div>
                    </div>
                    <div style='font-size: 0.65rem; font-weight: 800; color: #6366F1; background: rgba(99, 102, 241, 0.15); padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(99, 102, 241, 0.3); font-family: "Space Grotesk", sans-serif;'>
                        {priority.upper()}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            actions = [
                {
                    "title": "Schedule Viewing",
                    "desc": "Lead has viewed 'Teravista' property 3x.",
                    "impact": "High",
                    "icon": "🏠",
                },
                {
                    "title": "Send Financing Guide",
                    "desc": "Dwell time on 'Mortgage' page > 2 mins.",
                    "impact": "Medium",
                    "icon": "💰",
                },
                {
                    "title": "Video Follow-up",
                    "desc": "Personal connection needed to boost trust.",
                    "impact": "Medium",
                    "icon": "📹",
                },
            ]

            for action in actions:
                st.markdown(
                    f"""
                <div style='{card_style}'>
                    <div style='background: rgba(99, 102, 241, 0.1); width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; border: 1px solid rgba(99, 102, 241, 0.2);'>
                        {action["icon"]}
                    </div>
                    <div style='flex: 1;'>
                        <div style='font-weight: 700; font-size: 0.95rem; color: #FFFFFF; font-family: "Space Grotesk", sans-serif;'>{action["title"].upper()}</div>
                        <div style='font-size: 0.8rem; color: #8B949E; font-family: "Inter", sans-serif;'>{action["desc"]}</div>
                    </div>
                    <div style='font-size: 0.65rem; font-weight: 800; color: #6366F1; background: rgba(99, 102, 241, 0.15); padding: 4px 10px; border-radius: 6px; border: 1px solid rgba(99, 102, 241, 0.3); font-family: "Space Grotesk", sans-serif;'>
                        {action["impact"].upper()}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        if st.button("⚡ Auto-Execute Strategy", type="primary", use_container_width=True):
            with st.spinner("🤖 Orchestrating next best actions..."):
                import time

                time.sleep(1.2)
                st.toast("Workflows triggered in GHL", icon="✅")
                st.success("Strategy execution sequence started!")
