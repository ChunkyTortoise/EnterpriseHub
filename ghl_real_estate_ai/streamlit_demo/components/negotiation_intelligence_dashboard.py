"""
Negotiation Intelligence Dashboard

Comprehensive Streamlit interface for AI-powered negotiation analysis,
real-time coaching, and strategy optimization.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio

from ghl_real_estate_ai.services.ai_negotiation_partner import get_ai_negotiation_partner
from ghl_real_estate_ai.api.schemas.negotiation import (
    NegotiationAnalysisRequest,
    RealTimeCoachingRequest
)


@st.cache_resource
def get_negotiation_partner():
    """Get cached negotiation partner instance"""
    return get_ai_negotiation_partner()


class NegotiationIntelligenceDashboard:
    """
    Main Streamlit dashboard for negotiation intelligence with real-time coaching.
    """
    
    def __init__(self):
        self.negotiation_partner = get_negotiation_partner()
        
        # Initialize session state
        if 'current_negotiation' not in st.session_state:
            st.session_state.current_negotiation = None
        if 'coaching_history' not in st.session_state:
            st.session_state.coaching_history = []
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = None
    
    def render(self):
        """Render the complete negotiation intelligence dashboard"""
        
        st.title("🤝 AI Negotiation Partner")
        st.markdown("**Real-time negotiation intelligence for optimal deal outcomes**")
        
        # Dashboard tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Analysis", 
            "🎯 Strategy", 
            "💬 Real-Time Coaching", 
            "📈 Performance"
        ])
        
        with tab1:
            self.render_analysis_tab()
        
        with tab2:
            self.render_strategy_tab()
        
        with tab3:
            self.render_coaching_tab()
        
        with tab4:
            self.render_performance_tab()
    
    def render_analysis_tab(self):
        """Render negotiation analysis interface"""
        
        st.header("Negotiation Intelligence Analysis")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Analysis input form
            with st.form("negotiation_analysis"):
                st.subheader("Property & Lead Information")
                
                property_id = st.text_input("Property ID", value="PROP_789123")
                lead_id = st.text_input("Lead ID", value="LEAD_456789")
                
                col1a, col1b = st.columns(2)
                with col1a:
                    cash_offer = st.checkbox("Cash Offer", value=False)
                    flexible_timeline = st.checkbox("Flexible Timeline", value=True)
                
                with col1b:
                    pre_approved = st.checkbox("Pre-Approved", value=True)
                    first_time_buyer = st.checkbox("First-Time Buyer", value=False)
                
                submitted = st.form_submit_button("🔍 Analyze Negotiation Intelligence", type="primary")
                
                if submitted:
                    self.run_negotiation_analysis(property_id, lead_id, {
                        "cash_offer": cash_offer,
                        "flexible_timeline": flexible_timeline,
                        "pre_approved": pre_approved,
                        "first_time_buyer": first_time_buyer
                    })
        
        with col2:
            # Quick stats
            if st.session_state.analysis_results:
                self.render_quick_stats()
        
        # Display analysis results
        if st.session_state.analysis_results:
            self.render_analysis_results()
    
    def render_strategy_tab(self):
        """Render strategy details and recommendations"""
        
        st.header("Negotiation Strategy")
        
        if not st.session_state.analysis_results:
            st.info("Run an analysis to see strategic recommendations.")
            return
        
        analysis = st.session_state.analysis_results
        strategy = analysis.negotiation_strategy
        
        # Strategy overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Primary Tactic",
                strategy.primary_tactic.replace("_", " ").title(),
                delta=f"{strategy.confidence_score:.0f}% confidence"
            )
        
        with col2:
            st.metric(
                "Recommended Offer",
                f"${strategy.recommended_offer_price:,.0f}",
                delta=f"{(float(strategy.recommended_offer_price) / 750000 - 1) * 100:.1f}% of list"
            )
        
        with col3:
            st.metric(
                "Win Probability",
                f"{analysis.win_probability.win_probability:.1f}%",
                delta="vs baseline"
            )
        
        # Strategy details
        st.subheader("Strategic Elements")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Key Terms to Emphasize:**")
            for term in strategy.key_terms_to_emphasize:
                st.write(f"• {term.replace('_', ' ').title()}")
            
            st.write("**Concessions to Request:**")
            for concession in strategy.concessions_to_request:
                st.write(f"• {concession.replace('_', ' ').title()}")
        
        with col2:
            st.write("**Primary Talking Points:**")
            for point in strategy.primary_talking_points[:5]:
                st.write(f"• {point}")
        
        # Offer range visualization
        st.subheader("Optimal Offer Range")
        self.render_offer_range_chart(strategy)
        
        # Scenario analysis
        st.subheader("Win Probability Scenarios")
        self.render_scenario_analysis(analysis.win_probability)
    
    def render_coaching_tab(self):
        """Render real-time coaching interface"""
        
        st.header("Real-Time Negotiation Coaching")
        
        if not st.session_state.analysis_results:
            st.info("Run an analysis first to enable real-time coaching.")
            return
        
        # Coaching input
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Current Situation")
            
            conversation_context = st.text_area(
                "Conversation Context",
                placeholder="Enter the current conversation details...",
                height=150
            )
            
            current_situation = st.selectbox(
                "Current Situation",
                ["Initial offer presentation", "Seller counter-offer", "Price negotiation", 
                 "Terms discussion", "Final negotiations", "Closing timeline"]
            )
            
            col1a, col1b = st.columns(2)
            with col1a:
                buyer_feedback = st.text_input("Buyer Feedback (optional)")
            with col1b:
                seller_response = st.text_input("Seller Response (optional)")
            
            if st.button("🎯 Get Coaching", type="primary"):
                self.get_realtime_coaching(
                    conversation_context, current_situation, buyer_feedback, seller_response
                )
        
        with col2:
            # Coaching history
            st.subheader("Coaching History")
            if st.session_state.coaching_history:
                for i, coaching in enumerate(reversed(st.session_state.coaching_history[-5:])):
                    with st.expander(f"Session {len(st.session_state.coaching_history) - i}"):
                        st.write(f"**Situation:** {coaching['situation']}")
                        st.write(f"**Guidance:** {coaching['guidance']}")
        
        # Display latest coaching
        if st.session_state.coaching_history:
            latest_coaching = st.session_state.coaching_history[-1]
            self.render_coaching_response(latest_coaching['response'])
    
    def render_performance_tab(self):
        """Render performance metrics and analytics"""
        
        st.header("Performance Analytics")
        
        # Get performance metrics
        metrics = self.negotiation_partner.get_performance_metrics()
        
        # Performance overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Analyses", metrics["total_analyses"])
        
        with col2:
            st.metric("Avg Processing Time", f"{metrics['avg_processing_time_ms']:.0f}ms")
        
        with col3:
            st.metric("Active Negotiations", metrics["active_negotiations"])
        
        with col4:
            st.metric("Prediction History", metrics["prediction_history_count"])
        
        # Strategy effectiveness
        if metrics["strategy_averages"]:
            st.subheader("Strategy Effectiveness")
            
            strategy_df = pd.DataFrame([
                {"Strategy": strategy.replace("_", " ").title(), "Avg Win Probability": avg_prob}
                for strategy, avg_prob in metrics["strategy_averages"].items()
            ])
            
            fig = px.bar(
                strategy_df, 
                x="Strategy", 
                y="Avg Win Probability",
                title="Average Win Probability by Strategy",
                color="Avg Win Probability",
                color_continuous_scale="viridis"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent analysis trends (simulated data)
        self.render_performance_trends()
    
    def render_quick_stats(self):
        """Render quick statistics sidebar"""
        
        analysis = st.session_state.analysis_results
        
        st.subheader("Quick Stats")
        
        # Psychology stats
        st.metric(
            "Seller Urgency",
            f"{analysis.seller_psychology.urgency_score:.0f}/100",
            delta=analysis.seller_psychology.urgency_level
        )
        
        st.metric(
            "Market Leverage",
            f"{analysis.market_leverage.overall_leverage_score:.0f}/100",
            delta=analysis.market_leverage.market_condition.replace("_", " ").title()
        )
        
        st.metric(
            "Processing Time",
            f"{analysis.processing_time_ms}ms",
            delta="sub-3-second target"
        )
        
        # Risk alerts
        if analysis.win_probability.risk_factors:
            st.warning("⚠️ Risk Factors Detected")
            for risk in analysis.win_probability.risk_factors[:3]:
                st.write(f"• {risk}")
    
    def render_analysis_results(self):
        """Render comprehensive analysis results"""
        
        analysis = st.session_state.analysis_results
        
        st.divider()
        st.subheader("Intelligence Analysis Results")
        
        # Executive summary
        st.info(f"**Executive Summary:** {analysis.executive_summary}")
        
        # Key insights
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Key Insights:**")
            for insight in analysis.key_insights:
                st.write(f"• {insight}")
        
        with col2:
            st.write("**Action Items:**")
            for action in analysis.action_items:
                st.write(f"• {action}")
        
        # Detailed analysis sections
        tabs = st.tabs(["🧠 Psychology", "📈 Market", "🎯 Strategy", "🎲 Probability"])
        
        with tabs[0]:
            self.render_psychology_analysis(analysis.seller_psychology)
        
        with tabs[1]:
            self.render_market_analysis(analysis.market_leverage)
        
        with tabs[2]:
            self.render_strategy_details(analysis.negotiation_strategy)
        
        with tabs[3]:
            self.render_probability_analysis(analysis.win_probability)
    
    def render_psychology_analysis(self, psychology):
        """Render detailed seller psychology analysis"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Psychological Profile:**")
            st.write(f"• **Motivation Type:** {psychology.motivation_type.replace('_', ' ').title()}")
            st.write(f"• **Urgency Level:** {psychology.urgency_level.replace('_', ' ').title()}")
            st.write(f"• **Behavioral Pattern:** {psychology.behavioral_pattern.replace('_', ' ').title()}")
            st.write(f"• **Communication Style:** {psychology.communication_style or 'Not available'}")
        
        with col2:
            # Psychology scores visualization
            scores_data = {
                "Factor": ["Urgency", "Flexibility", "Emotional Attachment", "Financial Pressure", "Relationship Importance"],
                "Score": [
                    psychology.urgency_score,
                    psychology.flexibility_score,
                    psychology.emotional_attachment_score,
                    psychology.financial_pressure_score,
                    psychology.relationship_importance
                ]
            }
            
            fig = go.Figure(data=go.Bar(
                x=scores_data["Score"],
                y=scores_data["Factor"],
                orientation='h',
                marker_color='lightblue'
            ))
            fig.update_layout(
                title="Seller Psychology Scores",
                xaxis_title="Score (0-100)",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Primary concerns and hot buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if psychology.primary_concerns:
                st.write("**Primary Concerns:**")
                for concern in psychology.primary_concerns:
                    st.write(f"• {concern.replace('_', ' ').title()}")
        
        with col2:
            if psychology.negotiation_hot_buttons:
                st.write("**Negotiation Hot Buttons:**")
                for button in psychology.negotiation_hot_buttons:
                    st.write(f"• {button.replace('_', ' ').title()}")
    
    def render_market_analysis(self, leverage):
        """Render detailed market leverage analysis"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Market Conditions:**")
            st.write(f"• **Market Condition:** {leverage.market_condition.replace('_', ' ').title()}")
            st.write(f"• **Competitive Pressure:** {leverage.competitive_pressure:.0f}/100")
            st.write(f"• **Price Positioning:** {leverage.price_positioning.replace('_', ' ').title()}")
            st.write(f"• **Seasonal Advantage:** {leverage.seasonal_advantage:+.0f}%")
        
        with col2:
            # Leverage factors chart
            leverage_data = {
                "Factor": ["Overall Leverage", "Financing Strength", "Property Uniqueness", "Comparable Sales"],
                "Score": [
                    leverage.overall_leverage_score,
                    leverage.financing_strength,
                    leverage.property_uniqueness_score,
                    leverage.comparable_sales_strength
                ]
            }
            
            fig = px.radar(
                r=leverage_data["Score"],
                theta=leverage_data["Factor"],
                range_r=[0, 100],
                title="Market Leverage Factors"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Inventory levels
        if leverage.inventory_levels:
            st.write("**Inventory Analysis (Months):**")
            inventory_df = pd.DataFrame([
                {"Price Range": range_name.replace("_", " ").title(), "Months of Inventory": months}
                for range_name, months in leverage.inventory_levels.items()
            ])
            st.dataframe(inventory_df, use_container_width=True)
    
    def render_strategy_details(self, strategy):
        """Render detailed strategy information"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Tactical Approach:**")
            st.write(f"• **Opening Strategy:** {strategy.opening_strategy}")
            st.write(f"• **Timeline:** {strategy.negotiation_timeline.replace('_', ' ').title()}")
            st.write(f"• **Relationship Approach:** {strategy.relationship_building_approach.replace('_', ' ').title()}")
        
        with col2:
            st.write("**Counter-Offer Response:**")
            st.write(strategy.response_to_counter)
        
        # Objection responses
        if strategy.objection_responses:
            st.write("**Objection Response Scripts:**")
            for objection, response in strategy.objection_responses.items():
                with st.expander(f"Response to: {objection.replace('_', ' ').title()}"):
                    st.write(response)
    
    def render_probability_analysis(self, win_probability):
        """Render win probability analysis"""
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Probability gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=win_probability.win_probability,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Win Probability"},
                gauge={'axis': {'range': [None, 100]},
                      'bar': {'color': "darkgreen"},
                      'steps': [
                          {'range': [0, 50], 'color': "lightgray"},
                          {'range': [50, 80], 'color': "yellow"},
                          {'range': [80, 100], 'color': "lightgreen"}],
                      'threshold': {'line': {'color': "red", 'width': 4},
                                   'thickness': 0.75, 'value': 90}}))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Contributing factors
            if win_probability.factor_weights:
                st.write("**Contributing Factors:**")
                factors_df = pd.DataFrame([
                    {"Factor": factor.replace("_", " ").title(), "Weight": weight}
                    for factor, weight in win_probability.factor_weights.items()
                ])
                
                fig = px.bar(
                    factors_df,
                    x="Weight",
                    y="Factor",
                    orientation='h',
                    title="Factor Importance"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Success drivers and risk factors
        col1, col2 = st.columns(2)
        
        with col1:
            if win_probability.success_drivers:
                st.success("**Success Drivers:**")
                for driver in win_probability.success_drivers:
                    st.write(f"✅ {driver}")
        
        with col2:
            if win_probability.risk_factors:
                st.error("**Risk Factors:**")
                for risk in win_probability.risk_factors:
                    st.write(f"⚠️ {risk}")
    
    def render_offer_range_chart(self, strategy):
        """Render offer range visualization"""
        
        offer_range = strategy.offer_range
        
        fig = go.Figure()
        
        # Add range bar
        fig.add_trace(go.Scatter(
            x=[float(offer_range["min"]), float(offer_range["max"])],
            y=[1, 1],
            mode='lines',
            line=dict(width=20, color='lightblue'),
            name='Offer Range'
        ))
        
        # Add target point
        fig.add_trace(go.Scatter(
            x=[float(offer_range["target"])],
            y=[1],
            mode='markers',
            marker=dict(size=15, color='red', symbol='diamond'),
            name='Recommended Offer'
        ))
        
        fig.update_layout(
            title="Optimal Offer Range",
            xaxis_title="Offer Amount ($)",
            yaxis=dict(visible=False),
            showlegend=True,
            height=200
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def render_scenario_analysis(self, win_probability):
        """Render scenario analysis chart"""
        
        if not win_probability.scenarios:
            return
        
        scenarios_df = pd.DataFrame([
            {"Scenario": scenario.replace("_", " ").title(), "Win Probability": prob}
            for scenario, prob in win_probability.scenarios.items()
        ])
        
        fig = px.bar(
            scenarios_df,
            x="Scenario",
            y="Win Probability",
            title="Win Probability by Scenario",
            color="Win Probability",
            color_continuous_scale="viridis"
        )
        fig.update_xaxis(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    def render_coaching_response(self, coaching_response):
        """Render coaching response details"""
        
        st.subheader("💡 Coaching Guidance")
        
        # Immediate guidance
        st.info(f"**Immediate Guidance:** {coaching_response.immediate_guidance}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if coaching_response.tactical_adjustments:
                st.write("**Tactical Adjustments:**")
                for adjustment in coaching_response.tactical_adjustments:
                    st.write(f"• {adjustment}")
            
            if coaching_response.next_steps:
                st.write("**Next Steps:**")
                for step in coaching_response.next_steps:
                    st.write(f"• {step}")
        
        with col2:
            if coaching_response.conversation_suggestions:
                st.write("**Conversation Suggestions:**")
                for situation, suggestion in coaching_response.conversation_suggestions.items():
                    st.write(f"• **{situation.replace('_', ' ').title()}:** {suggestion}")
        
        # Risk alerts
        if coaching_response.risk_alerts:
            st.error("⚠️ **Risk Alerts:**")
            for alert in coaching_response.risk_alerts:
                st.write(f"• {alert}")
    
    def render_performance_trends(self):
        """Render performance trends (simulated data)"""
        
        st.subheader("Analysis Trends")
        
        # Simulated trend data
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='W')
        trend_data = {
            'Date': dates,
            'Analyses': [20 + i + (i % 4) * 5 for i in range(len(dates))],
            'Avg Win Probability': [65 + (i % 8) * 3 for i in range(len(dates))],
            'Processing Time': [2800 - i * 10 + (i % 3) * 200 for i in range(len(dates))]
        }
        
        trend_df = pd.DataFrame(trend_data)
        
        # Multi-line chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=trend_df['Date'],
            y=trend_df['Avg Win Probability'],
            mode='lines',
            name='Avg Win Probability (%)',
            yaxis='y'
        ))
        
        fig.add_trace(go.Scatter(
            x=trend_df['Date'],
            y=trend_df['Processing Time'],
            mode='lines',
            name='Processing Time (ms)',
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='Performance Trends Over Time',
            xaxis_title='Date',
            yaxis=dict(title='Win Probability (%)', side='left'),
            yaxis2=dict(title='Processing Time (ms)', side='right', overlaying='y'),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @st.cache_data
    def run_negotiation_analysis(self, property_id: str, lead_id: str, buyer_preferences: Dict[str, Any]):
        """Run negotiation intelligence analysis"""
        
        with st.spinner("🔄 Analyzing negotiation intelligence..."):
            try:
                request = NegotiationAnalysisRequest(
                    property_id=property_id,
                    lead_id=lead_id,
                    buyer_preferences=buyer_preferences
                )
                
                # Run async analysis (simplified for demo)
                # In production, this would use asyncio.run()
                analysis_result = {
                    "property_id": property_id,
                    "lead_id": lead_id,
                    "processing_time_ms": 2450,
                    "executive_summary": f"Seller shows financial motivation with high urgency. Market leverage score of 78/100 supports price-focused strategy. Recommended offer has 84% win probability.",
                    # Simulated results for demo
                }
                
                st.session_state.analysis_results = self._create_mock_analysis_result(property_id, lead_id)
                st.session_state.current_negotiation = property_id
                
                st.success("✅ Analysis complete! Scroll down to see results.")
                
            except Exception as e:
                st.error(f"Analysis failed: {e}")
    
    def get_realtime_coaching(self, conversation_context: str, current_situation: str, 
                           buyer_feedback: str, seller_response: str):
        """Get real-time coaching"""
        
        with st.spinner("🎯 Generating coaching..."):
            try:
                # Simulated coaching response
                coaching_response = {
                    "immediate_guidance": f"For {current_situation.lower()}, emphasize timeline flexibility and maintain confident position.",
                    "tactical_adjustments": [
                        "Increase urgency emphasis",
                        "Reference market comparables"
                    ],
                    "next_steps": [
                        "Present counter-offer within 24 hours",
                        "Emphasize buyer qualifications",
                        "Monitor seller response patterns"
                    ],
                    "conversation_suggestions": {
                        "opening": "Lead with market analysis",
                        "objection_handling": "Address price concerns with comps data",
                        "closing": "Reinforce win-win scenario"
                    },
                    "risk_alerts": []
                }
                
                # Add to coaching history
                coaching_session = {
                    "timestamp": datetime.now(),
                    "situation": current_situation,
                    "context": conversation_context,
                    "guidance": coaching_response["immediate_guidance"],
                    "response": type('obj', (object,), coaching_response)()
                }
                
                st.session_state.coaching_history.append(coaching_session)
                
                st.success("🎯 Coaching updated!")
                
            except Exception as e:
                st.error(f"Coaching failed: {e}")
    
    def _create_mock_analysis_result(self, property_id: str, lead_id: str):
        """Create mock analysis result for demo"""
        
        # This would be replaced with actual analysis results
        return type('MockAnalysis', (), {
            'property_id': property_id,
            'lead_id': lead_id,
            'analysis_timestamp': datetime.now(),
            'processing_time_ms': 2450,
            'executive_summary': "Seller shows financial motivation with high urgency. Market leverage score of 78/100 supports price-focused strategy. Recommended offer has 84% win probability.",
            'key_insights': [
                "Seller urgency level: high (85/100)",
                "Market leverage: 78/100 in buyers_market",
                "Optimal strategy: price_focused",
                "Win probability: 84.3%",
                "Property pricing: overpriced"
            ],
            'action_items': [
                "Execute price_focused strategy",
                "Offer $712,500",
                "Monitor seller response",
                "Prepare counter-strategy",
                "Track market changes"
            ],
            'seller_psychology': type('MockPsychology', (), {
                'motivation_type': 'financial',
                'urgency_level': 'high',
                'urgency_score': 85,
                'flexibility_score': 72,
                'emotional_attachment_score': 35,
                'financial_pressure_score': 78,
                'relationship_importance': 45,
                'behavioral_pattern': 'price_dropper',
                'communication_style': 'professional',
                'primary_concerns': ['time_pressure', 'financial_constraints'],
                'negotiation_hot_buttons': ['pricing_sensitivity', 'timeline_flexibility']
            })(),
            'market_leverage': type('MockLeverage', (), {
                'overall_leverage_score': 78,
                'market_condition': 'buyers_market',
                'competitive_pressure': 65,
                'price_positioning': 'overpriced',
                'seasonal_advantage': 12,
                'financing_strength': 85,
                'property_uniqueness_score': 45,
                'comparable_sales_strength': 88,
                'inventory_levels': {
                    'below_range': 4.2,
                    'target_range': 6.8,
                    'above_range': 8.5
                }
            })(),
            'negotiation_strategy': type('MockStrategy', (), {
                'primary_tactic': 'price_focused',
                'confidence_score': 82,
                'recommended_offer_price': 712500,
                'offer_range': {
                    'min': 705000,
                    'target': 712500,
                    'max': 720000
                },
                'key_terms_to_emphasize': ['competitive_price', 'market_value_analysis', 'quick_close'],
                'concessions_to_request': ['flexible_inspection', 'as_is_acceptance'],
                'relationship_building_approach': 'professional_analytical',
                'opening_strategy': 'Present 95.0% offer with strong market analysis supporting valuation',
                'response_to_counter': 'Focus on market data and comparable sales. Use factual analysis to justify position.',
                'negotiation_timeline': 'standard_timeline',
                'primary_talking_points': [
                    'Market analysis supports our valuation approach',
                    'Comparable sales data indicates fair market value',
                    'Recent market trends favor this pricing position'
                ],
                'objection_responses': {
                    'price_too_low': 'Market data supports this valuation approach',
                    'timing_issues': 'We can accommodate your preferred timeline'
                }
            })(),
            'win_probability': type('MockWinProbability', (), {
                'win_probability': 84.3,
                'confidence_interval': {'lower': 76.8, 'upper': 91.8},
                'factor_weights': {
                    'offer_ratio': 0.35,
                    'seller_psychology': 0.25,
                    'market_conditions': 0.20,
                    'buyer_strength': 0.20
                },
                'risk_factors': [],
                'success_drivers': [
                    'High seller urgency',
                    'Strong market leverage',
                    'Property overpriced'
                ],
                'scenarios': {
                    'current_offer': 84.3,
                    '3_percent_higher': 89.5,
                    'asking_price': 95.2,
                    'cash_offer_premium': 91.8
                }
            })()
        })()


def render_negotiation_intelligence_dashboard():
    """Main function to render the negotiation intelligence dashboard"""
    dashboard = NegotiationIntelligenceDashboard()
    dashboard.render()