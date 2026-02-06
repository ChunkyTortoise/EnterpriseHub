"""
SHAP Explainability Dashboard Component

Interactive dashboard component that provides transparent AI explanations for lead scoring
using SHAP (SHapley Additive exPlanations) values. Integrates seamlessly with the existing
Lead Intelligence Hub to provide "why" behind AI decisions.

Features:
- Interactive SHAP waterfall charts
- Feature importance analysis by category  
- What-if scenario analysis
- Business-friendly explanations
- Performance optimized with caching

Integration:
- Extends existing Lead Intelligence Hub
- Uses existing Obsidian theme patterns
- Follows existing async utility patterns
- Integrates with existing cache service
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from ghl_real_estate_ai.services.shap_explainer_service import (
    get_shap_explainer_service, 
    SHAPExplanation,
    SHAPExplainerService
)
from ghl_real_estate_ai.services.ml_lead_analyzer import get_ml_enhanced_lead_analyzer_async
from ghl_real_estate_ai.streamlit_demo.components.primitives.card import (
    render_obsidian_card,
    CardConfig,
)
try:
    from ghl_real_estate_ai.streamlit_demo.components.primitives.card import create_metric_card
except ImportError:
    def create_metric_card(title, value, **kwargs):
        render_obsidian_card(title=title, content=f"<p>{value}</p>", config=CardConfig())

try:
    from ghl_real_estate_ai.streamlit_demo.async_utils import run_async
except ImportError:
    import asyncio as _asyncio
    def run_async(coro):
        try:
            loop = _asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(_asyncio.run, coro).result()
        return _asyncio.run(coro)
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class SHAPExplainabilityDashboard:
    """
    Main dashboard component for SHAP explanations
    Provides interactive AI transparency for lead scoring
    """
    
    def __init__(self):
        self.shap_service = get_shap_explainer_service()
        
    def render(self, lead_name: str, lead_context: Dict[str, Any]) -> None:
        """
        Render the complete SHAP explainability dashboard
        
        Args:
            lead_name: Name of the lead to explain
            lead_context: Lead data context for analysis
        """
        st.markdown("### 🔍 AI Decision Transparency")
        
        # Initialize session state for SHAP data
        if f"shap_explanation_{lead_name}" not in st.session_state:
            st.session_state[f"shap_explanation_{lead_name}"] = None
            st.session_state[f"shap_loading_{lead_name}"] = False
        
        # Main dashboard layout
        self._render_explanation_section(lead_name, lead_context)
        
        # What-if analysis section (only if explanation is available)
        explanation = st.session_state.get(f"shap_explanation_{lead_name}")
        if explanation and explanation.what_if_ready:
            st.markdown("---")
            self._render_what_if_section(lead_name, explanation)
        
        # Performance metrics (admin view)
        if st.sidebar.checkbox("Show SHAP Performance Metrics", value=False):
            st.markdown("---")
            self._render_performance_metrics()
    
    def _render_explanation_section(self, lead_name: str, lead_context: Dict[str, Any]) -> None:
        """Render the main SHAP explanation section"""
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown("**Get AI Decision Explanation**")
            explanation_type = st.selectbox(
                "Explanation Detail Level:",
                ["Quick Overview", "Detailed Analysis", "Expert Mode"],
                key=f"explanation_type_{lead_name}"
            )
        
        with col2:
            if st.button(
                "🔍 Explain Decision", 
                key=f"explain_btn_{lead_name}",
                type="primary"
            ):
                st.session_state[f"shap_loading_{lead_name}"] = True
                st.rerun()
        
        with col3:
            if st.button(
                "🔄 Refresh", 
                key=f"refresh_shap_{lead_name}"
            ):
                st.session_state[f"shap_explanation_{lead_name}"] = None
                st.rerun()
        
        # Load explanation if requested
        if st.session_state.get(f"shap_loading_{lead_name}"):
            self._load_shap_explanation(lead_name, lead_context, explanation_type)
        
        # Display explanation if available
        explanation = st.session_state.get(f"shap_explanation_{lead_name}")
        if explanation:
            self._display_explanation(explanation, explanation_type)
    
    @st.cache_data(ttl=1800)  # 30 minute cache
    def _load_shap_explanation(self, lead_name: str, lead_context: Dict[str, Any], explanation_type: str) -> None:
        """Load SHAP explanation with caching"""
        
        with st.spinner(f"🧠 Analyzing AI decision for {lead_name}..."):
            try:
                # Get ML analyzer with SHAP capability
                ml_analyzer = run_async(get_ml_enhanced_lead_analyzer_async())
                
                # Ensure ML model is loaded
                await_result = run_async(ml_analyzer.ml_predictor.load_model())
                if not await_result:
                    st.error("❌ Unable to load ML model for explanation")
                    st.session_state[f"shap_loading_{lead_name}"] = False
                    return
                
                # Get ML prediction with SHAP explanation
                predictor = ml_analyzer.ml_predictor
                if not predictor.model or not predictor.shap_explainer:
                    st.error("❌ SHAP explainer not available")
                    st.session_state[f"shap_loading_{lead_name}"] = False
                    return
                
                # Extract features for explanation
                features = predictor._extract_features(lead_context)
                
                # Get prediction score
                score, confidence, _ = run_async(
                    predictor.predict_lead_score(lead_context)
                )
                
                # Generate SHAP explanation
                lead_id = lead_context.get('lead_id', f"lead_{lead_name.lower().replace(' ', '_')}")
                
                explanation = run_async(
                    self.shap_service.explain_prediction(
                        model=predictor.model,
                        scaler=predictor.scaler,
                        shap_explainer=predictor.shap_explainer,
                        feature_names=predictor.feature_names,
                        features=features,
                        lead_id=lead_id,
                        lead_name=lead_name,
                        prediction_score=score
                    )
                )
                
                # Store in session state
                st.session_state[f"shap_explanation_{lead_name}"] = explanation
                st.session_state[f"shap_loading_{lead_name}"] = False
                
                # Show success message
                cache_status = "📋 Cached" if explanation.cached else "✨ Fresh"
                st.success(
                    f"✅ AI decision explained in {explanation.explanation_time_ms:.0f}ms {cache_status}"
                )
                
                st.rerun()
                
            except Exception as e:
                logger.error(f"SHAP explanation failed for {lead_name}: {e}")
                st.error(f"❌ Explanation failed: {str(e)}")
                st.session_state[f"shap_loading_{lead_name}"] = False
    
    def _display_explanation(self, explanation: SHAPExplanation, explanation_type: str) -> None:
        """Display the SHAP explanation based on selected detail level"""
        
        if explanation_type == "Quick Overview":
            self._render_quick_overview(explanation)
        elif explanation_type == "Detailed Analysis":
            self._render_detailed_analysis(explanation)
        else:  # Expert Mode
            self._render_expert_mode(explanation)
    
    def _render_quick_overview(self, explanation: SHAPExplanation) -> None:
        """Render quick overview with key insights"""
        
        # Summary metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            create_metric_card(
                title="Final Score",
                value=f"{explanation.prediction:.0f}",
                delta=f"+{explanation.prediction - explanation.base_value:.0f} vs baseline",
                card_config=CardConfig(
                    background_color="#1E40AF" if explanation.prediction >= 70 else "#DC2626"
                )
            )
        
        with col2:
            top_driver = explanation.key_drivers[0] if explanation.key_drivers else None
            if top_driver:
                create_metric_card(
                    title="Top Factor",
                    value=top_driver['feature'],
                    delta=f"{top_driver['impact']:+.1f} impact",
                    card_config=CardConfig(
                        background_color="#059669" if top_driver['impact'] > 0 else "#DC2626"
                    )
                )
        
        with col3:
            create_metric_card(
                title="Risk Factors",
                value=str(len(explanation.risk_factors)),
                delta="Areas to address",
                card_config=CardConfig(background_color="#9333EA")
            )
        
        with col4:
            create_metric_card(
                title="Opportunities", 
                value=str(len(explanation.opportunities)),
                delta="Growth potential",
                card_config=CardConfig(background_color="#059669")
            )
        
        # Key insights
        st.markdown("#### 🎯 Key Insights")
        
        if explanation.key_drivers:
            top_3_drivers = explanation.key_drivers[:3]
            
            for i, driver in enumerate(top_3_drivers, 1):
                impact_color = "🟢" if driver['impact'] > 0 else "🔴"
                
                with st.container():
                    render_obsidian_card(
                        title=f"{i}. {driver['feature']} {impact_color}",
                        content=driver['explanation'],
                        card_config=CardConfig(
                            border_color="#059669" if driver['impact'] > 0 else "#DC2626",
                            show_border=True
                        )
                    )
        
        # Quick actions
        if explanation.key_drivers:
            st.markdown("#### 🎬 Quick Actions")
            action_driver = explanation.key_drivers[0]
            if action_driver['actionable_insight']:
                st.info(f"💡 **Next Step**: {action_driver['actionable_insight']}")
    
    def _render_detailed_analysis(self, explanation: SHAPExplanation) -> None:
        """Render detailed analysis with visualizations"""
        
        # Interactive waterfall chart
        st.markdown("#### 📊 Decision Breakdown")
        
        try:
            waterfall_fig = run_async(
                self.shap_service.create_waterfall_visualization(explanation)
            )
            st.plotly_chart(waterfall_fig, use_container_width=True)
        except Exception as e:
            logger.error(f"Waterfall chart failed: {e}")
            st.error("❌ Visualization temporarily unavailable")
        
        # Feature impact by category
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🎯 Key Drivers")
            for driver in explanation.key_drivers[:5]:
                impact_emoji = "📈" if driver['impact'] > 0 else "📉"
                category_emoji = self._get_category_emoji(driver['category'])
                
                with st.expander(f"{impact_emoji} {driver['feature']} ({driver['impact']:+.2f})"):
                    st.markdown(f"**{category_emoji} Category**: {driver['category'].title()}")
                    st.markdown(f"**Impact**: {driver['explanation']}")
                    if driver['actionable_insight']:
                        st.markdown(f"**Action**: {driver['actionable_insight']}")
        
        with col2:
            st.markdown("##### ⚠️ Risk Factors")
            if explanation.risk_factors:
                for risk in explanation.risk_factors:
                    st.markdown(f"• {risk}")
            else:
                st.success("✅ No significant risk factors identified")
            
            st.markdown("##### 🚀 Opportunities")
            if explanation.opportunities:
                for opp in explanation.opportunities:
                    st.markdown(f"• {opp}")
            else:
                st.info("💡 Focus on addressing risk factors first")
        
        # Business insights summary
        st.markdown("#### 💼 Business Summary")
        
        positive_impact = sum(v for v in explanation.shap_values.values() if v > 0)
        negative_impact = sum(v for v in explanation.shap_values.values() if v < 0)
        
        insight_text = f"""
        **Decision Summary for {explanation.lead_name}:**
        
        • **Final Score**: {explanation.prediction:.0f}/100 (started at {explanation.base_value:.0f} baseline)
        • **Positive Factors**: +{positive_impact:.1f} score impact from {len([v for v in explanation.shap_values.values() if v > 0])} features
        • **Negative Factors**: {negative_impact:.1f} score impact from {len([v for v in explanation.shap_values.values() if v < 0])} features
        • **Net Impact**: {explanation.prediction - explanation.base_value:+.1f} points vs average lead
        
        **Recommendation**: {'High priority follow-up' if explanation.prediction >= 75 else 'Standard nurture track' if explanation.prediction >= 50 else 'Long-term cultivation'}
        """
        
        st.markdown(insight_text)
    
    def _render_expert_mode(self, explanation: SHAPExplanation) -> None:
        """Render expert mode with technical details"""
        
        # Technical metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Baseline Value", f"{explanation.base_value:.3f}")
        with col2:
            st.metric("Prediction", f"{explanation.prediction:.3f}")
        with col3:
            st.metric("Total SHAP Sum", f"{sum(explanation.shap_values.values()):.3f}")
        
        # Detailed SHAP values table
        st.markdown("#### 🔬 Feature Analysis")
        
        # Convert to dataframe for table display
        shap_data = []
        for feature, shap_val in explanation.shap_values.items():
            context = self.shap_service.feature_mapper.feature_contexts.get(feature, {})
            shap_data.append({
                'Feature': context.get('display_name', feature),
                'SHAP Value': f"{shap_val:+.4f}",
                'Absolute Impact': f"{abs(shap_val):.4f}",
                'Category': context.get('category', 'unknown').title(),
                'Direction': '↗️ Positive' if shap_val > 0 else '↘️ Negative',
                'Business Explanation': explanation.business_explanations.get(feature, 'N/A')
            })
        
        # Sort by absolute impact
        shap_df = pd.DataFrame(shap_data)
        shap_df = shap_df.sort_values('Absolute Impact', ascending=False)
        
        st.dataframe(
            shap_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Feature importance heatmap
        st.markdown("#### 🎨 Feature Importance Visualization")
        
        try:
            importance_fig = run_async(
                self.shap_service.create_feature_importance_visualization(explanation)
            )
            st.plotly_chart(importance_fig, use_container_width=True)
        except Exception as e:
            logger.error(f"Feature importance chart failed: {e}")
            st.error("❌ Importance visualization temporarily unavailable")
        
        # Raw SHAP data (expandable)
        with st.expander("🔧 Raw SHAP Data"):
            st.json(explanation.shap_values)
        
        # Performance info
        with st.expander("⚡ Performance Metrics"):
            perf_data = {
                'Generation Time': f"{explanation.explanation_time_ms:.1f}ms",
                'Cached Result': explanation.cached,
                'Explanation Timestamp': explanation.explained_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Lead ID': explanation.lead_id,
                'What-If Available': explanation.what_if_ready
            }
            st.json(perf_data)
    
    def _render_what_if_section(self, lead_name: str, explanation: SHAPExplanation) -> None:
        """Render what-if scenario analysis section"""
        
        st.markdown("### 🔮 What-If Analysis")
        st.markdown("*Explore how changing lead behavior would impact the AI's decision*")
        
        # Feature selection for modification
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### 📝 Modify Features")
            
            # Get available features for modification
            modifiable_features = [
                'response_time_hours',
                'message_length_avg', 
                'questions_asked',
                'timeline_urgency',
                'price_range_mentioned'
            ]
            
            modified_values = {}
            
            for feature in modifiable_features:
                context = self.shap_service.feature_mapper.feature_contexts.get(feature, {})
                display_name = context.get('display_name', feature)
                
                # Get current value from SHAP explanation (approximate)
                current_shap = explanation.shap_values.get(feature, 0)
                
                # Create input based on feature type
                if feature == 'response_time_hours':
                    new_val = st.slider(
                        f"{display_name} (hours)",
                        min_value=0.1,
                        max_value=48.0,
                        value=2.0,
                        step=0.1,
                        key=f"whatif_{feature}_{lead_name}"
                    )
                elif feature == 'message_length_avg':
                    new_val = st.slider(
                        f"{display_name} (characters)",
                        min_value=5,
                        max_value=200,
                        value=50,
                        step=5,
                        key=f"whatif_{feature}_{lead_name}"
                    )
                elif feature == 'questions_asked':
                    new_val = st.slider(
                        f"{display_name} (count)",
                        min_value=0,
                        max_value=10,
                        value=2,
                        step=1,
                        key=f"whatif_{feature}_{lead_name}"
                    )
                elif feature == 'timeline_urgency':
                    new_val = st.slider(
                        f"{display_name} (1-5 scale)",
                        min_value=0,
                        max_value=5,
                        value=2,
                        step=1,
                        key=f"whatif_{feature}_{lead_name}"
                    )
                else:  # price_range_mentioned
                    new_val = 1 if st.checkbox(
                        f"{display_name}",
                        value=False,
                        key=f"whatif_{feature}_{lead_name}"
                    ) else 0
                
                modified_values[feature] = new_val
        
        with col2:
            st.markdown("#### 🎯 Analysis Results")
            
            if st.button(
                "🔮 Run What-If Analysis", 
                key=f"whatif_btn_{lead_name}",
                type="primary"
            ):
                with st.spinner("🧮 Analyzing scenario..."):
                    try:
                        # Only include features that were actually modified
                        # For demo purposes, we'll include all selected features
                        scenario_result = run_async(
                            self.shap_service.perform_what_if_analysis(
                                explanation, modified_values
                            )
                        )
                        
                        if 'error' in scenario_result:
                            st.error(f"❌ {scenario_result['error']}")
                        else:
                            self._display_what_if_results(scenario_result)
                    
                    except Exception as e:
                        logger.error(f"What-if analysis failed: {e}")
                        st.error(f"❌ Analysis failed: {str(e)}")
            
            # Scenario presets
            st.markdown("##### 🎛️ Quick Scenarios")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("🚀 Ideal Lead", key=f"ideal_{lead_name}"):
                    # Set ideal values
                    st.session_state[f"whatif_response_time_hours_{lead_name}"] = 0.5
                    st.session_state[f"whatif_message_length_avg_{lead_name}"] = 100
                    st.session_state[f"whatif_questions_asked_{lead_name}"] = 5
                    st.session_state[f"whatif_timeline_urgency_{lead_name}"] = 4
                    st.session_state[f"whatif_price_range_mentioned_{lead_name}"] = True
                    st.rerun()
            
            with col_b:
                if st.button("⚠️ At Risk", key=f"atrisk_{lead_name}"):
                    # Set concerning values  
                    st.session_state[f"whatif_response_time_hours_{lead_name}"] = 24.0
                    st.session_state[f"whatif_message_length_avg_{lead_name}"] = 15
                    st.session_state[f"whatif_questions_asked_{lead_name}"] = 0
                    st.session_state[f"whatif_timeline_urgency_{lead_name}"] = 0
                    st.session_state[f"whatif_price_range_mentioned_{lead_name}"] = False
                    st.rerun()
    
    def _display_what_if_results(self, scenario_result: Dict[str, Any]) -> None:
        """Display what-if scenario analysis results"""
        
        # Score comparison
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Original Score",
                f"{scenario_result['original_score']:.0f}",
                delta=None
            )
        
        with col2:
            st.metric(
                "Modified Score", 
                f"{scenario_result['modified_score']:.0f}",
                delta=f"{scenario_result['score_change']:+.1f}"
            )
        
        with col3:
            improvement = scenario_result['score_change'] > 0
            impact_level = "High" if abs(scenario_result['score_change']) > 10 else "Medium" if abs(scenario_result['score_change']) > 5 else "Low"
            st.metric(
                "Impact Level",
                impact_level,
                delta="Improvement" if improvement else "Decline"
            )
        
        # SHAP changes breakdown
        if 'shap_changes' in scenario_result:
            st.markdown("##### 🔄 Feature Impact Changes")
            
            shap_changes_data = []
            for feature, change in scenario_result['shap_changes'].items():
                context = self.shap_service.feature_mapper.feature_contexts.get(feature, {})
                display_name = context.get('display_name', feature)
                
                shap_changes_data.append({
                    'Feature': display_name,
                    'SHAP Change': f"{change:+.3f}",
                    'Modified Value': scenario_result['modified_features'].get(feature, 'N/A'),
                    'Impact': 'Positive' if change > 0 else 'Negative'
                })
            
            changes_df = pd.DataFrame(shap_changes_data)
            st.dataframe(changes_df, use_container_width=True, hide_index=True)
        
        # Feasibility assessment
        if 'scenario_feasible' in scenario_result:
            st.markdown("##### 🎯 Feasibility Assessment")
            
            feasibility = scenario_result['scenario_feasible']
            for feature, level in feasibility.items():
                context = self.shap_service.feature_mapper.feature_contexts.get(feature, {})
                display_name = context.get('display_name', feature)
                
                color = "🟢" if level == "High" else "🟡" if level == "Medium" else "🔴"
                st.markdown(f"**{display_name}**: {color} {level} Feasibility")
        
        # Recommendations
        if 'recommendations' in scenario_result:
            st.markdown("##### 💡 Recommendations")
            for rec in scenario_result['recommendations']:
                st.markdown(f"• {rec}")
    
    def _render_performance_metrics(self) -> None:
        """Render SHAP service performance metrics"""
        
        st.markdown("### ⚡ SHAP Performance Dashboard")
        
        try:
            metrics = self.shap_service.get_performance_metrics()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Explanations Generated",
                    metrics['explanations_generated']
                )
            
            with col2:
                st.metric(
                    "Cache Hit Rate",
                    f"{metrics['cache_hit_rate_percent']:.1f}%"
                )
            
            with col3:
                st.metric(
                    "Avg Time",
                    f"{metrics['avg_explanation_time_ms']:.0f}ms"
                )
            
            with col4:
                st.metric(
                    "What-If Scenarios",
                    metrics['what_if_scenarios']
                )
            
            # Performance chart
            if metrics['total_requests'] > 0:
                perf_data = {
                    'Cache Hits': metrics['cache_hits'],
                    'Fresh Explanations': metrics['explanations_generated']
                }
                
                fig = px.pie(
                    values=list(perf_data.values()),
                    names=list(perf_data.keys()),
                    title="Request Distribution",
                    color_discrete_map={
                        'Cache Hits': '#059669',
                        'Fresh Explanations': '#DC2626'
                    }
                )
                
                fig.update_layout(
                    template="plotly_dark",
                    paper_bgcolor='rgba(0,0,0,0)',
                    font={'color': '#E5E7EB'}
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        except Exception as e:
            st.error(f"❌ Unable to load performance metrics: {e}")
    
    def _get_category_emoji(self, category: str) -> str:
        """Get emoji for feature category"""
        emoji_map = {
            'behavioral': '🧠',
            'financial': '💰', 
            'temporal': '⏰',
            'engagement': '🗣️',
            'other': '📊'
        }
        return emoji_map.get(category, '📊')

# Factory function for integration
def render_shap_explainability_dashboard(lead_name: str, lead_context: Dict[str, Any]) -> None:
    """
    Factory function to render SHAP explainability dashboard
    Integrates with existing Lead Intelligence Hub
    """
    dashboard = SHAPExplainabilityDashboard()
    dashboard.render(lead_name, lead_context)

# Streamlit component entry point
def main():
    """
    Standalone entry point for testing the SHAP dashboard
    """
    st.set_page_config(
        page_title="SHAP Explainability Dashboard",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🔍 SHAP AI Explainability Dashboard")
    st.markdown("*Transparent AI decision explanations for real estate lead scoring*")
    
    # Demo data
    demo_lead_context = {
        'lead_id': 'demo_lead_001',
        'conversations': [
            {
                'timestamp': time.time() - 3600,
                'content': 'Hi, I\'m interested in selling my house. Can you help me understand the process and what my home might be worth? I need to move within the next 3 months for a new job.'
            },
            {
                'timestamp': time.time() - 3000,
                'content': 'Thanks for the quick response! I have a 3-bedroom house in downtown area. It needs some work but has good bones. What would you estimate?'
            }
        ],
        'extracted_preferences': {
            'budget': '$300-400k',
            'location': 'downtown area',
            'timeline': '3 months'
        }
    }
    
    # Render dashboard
    render_shap_explainability_dashboard("John Smith", demo_lead_context)

if __name__ == "__main__":
    main()