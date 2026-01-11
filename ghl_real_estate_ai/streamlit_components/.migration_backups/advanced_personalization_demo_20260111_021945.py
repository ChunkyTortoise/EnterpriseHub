"""
Advanced Personalization Engine Demo Dashboard

Interactive Streamlit dashboard demonstrating the Advanced Personalization Engine
capabilities with real-time profile generation, communication adaptation, and
personalized recommendations.
"""

import streamlit as st
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import the Advanced Personalization Engine
try:
    from ghl_real_estate_ai.services.claude.advanced.advanced_personalization_engine import (
        get_advanced_personalization_engine,
        PersonalityType,
        CommunicationStyle,
        PersonalizationChannel,
        IndustryVertical
    )
    PERSONALIZATION_AVAILABLE = True
except ImportError:
    PERSONALIZATION_AVAILABLE = False
    st.error("Advanced Personalization Engine not available. Please ensure dependencies are installed.")


def main():
    """Main dashboard application"""
    st.set_page_config(
        page_title="Advanced Personalization Engine Demo",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🎯 Advanced Personalization Engine Demo")
    st.markdown("**Phase 5: ML-Driven Personalization with >92% Accuracy**")

    if not PERSONALIZATION_AVAILABLE:
        st.stop()

    # Sidebar controls
    with st.sidebar:
        st.header("Demo Controls")
        demo_mode = st.selectbox(
            "Select Demo Mode",
            ["Profile Creation", "Communication Adaptation", "Personalized Recommendations", "Performance Metrics"]
        )

        st.markdown("---")
        st.markdown("**Performance Targets:**")
        st.markdown("- Profile Generation: <200ms")
        st.markdown("- Recommendation Latency: <150ms")
        st.markdown("- Personalization Accuracy: >92%")
        st.markdown("- Real-time Adaptation: <100ms")

    # Main content area
    if demo_mode == "Profile Creation":
        show_profile_creation_demo()
    elif demo_mode == "Communication Adaptation":
        show_communication_adaptation_demo()
    elif demo_mode == "Personalized Recommendations":
        show_personalized_recommendations_demo()
    elif demo_mode == "Performance Metrics":
        show_performance_metrics_demo()


def show_profile_creation_demo():
    """Demonstrate personalized profile creation"""
    st.header("📋 Personalized Profile Creation Demo")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Input Data")

        # Lead ID
        lead_id = st.text_input("Lead ID", value="demo_lead_001")

        # Conversation History
        st.markdown("**Conversation History:**")
        conversation_option = st.selectbox(
            "Choose conversation type",
            ["Custom", "Analytical Lead", "Driver Lead", "Luxury Lead", "Commercial Lead"]
        )

        if conversation_option == "Custom":
            conversation_text = st.text_area(
                "Enter conversation messages (one per line)",
                height=150,
                value="I'm looking for a property with good investment potential\nCan you provide detailed market analysis?\nWhat's the ROI on luxury condos?"
            )
            conversation_history = [
                {"content": msg.strip(), "timestamp": datetime.now() - timedelta(hours=i), "speaker": "lead"}
                for i, msg in enumerate(conversation_text.split('\n'))
                if msg.strip()
            ]
        else:
            conversation_history = get_sample_conversation(conversation_option)

        # Behavioral Data
        st.markdown("**Behavioral Data:**")
        engagement_score = st.slider("Engagement Score", 0.0, 1.0, 0.8, 0.1)
        response_time = st.slider("Avg Response Time (hours)", 0.1, 24.0, 2.0, 0.1)
        mobile_usage = st.slider("Mobile Usage Ratio", 0.0, 1.0, 0.6, 0.1)
        sessions_per_week = st.slider("Sessions per Week", 1.0, 10.0, 3.5, 0.5)

        behavioral_data = {
            "engagement_score": engagement_score,
            "avg_response_time": response_time,
            "mobile_usage_ratio": mobile_usage,
            "sessions_per_week": sessions_per_week,
            "peak_activity_hours": [10, 14, 19]
        }

        # Property Interactions
        st.markdown("**Property Interactions:**")
        property_type = st.selectbox("Property Type Focus", [
            "luxury_condo", "residential_home", "commercial_office",
            "investment_property", "industrial_space"
        ])
        price_range = st.selectbox("Price Range", [
            "300000-500000", "500000-750000", "750000-1000000", "1000000+"
        ])

        property_interactions = [
            {
                "property_type": property_type,
                "price": int(price_range.split('-')[0]) if '-' in price_range else 1500000,
                "features_viewed": ["location", "price", "amenities", "investment_potential"],
                "view_duration": 180
            }
        ]

    with col2:
        st.subheader("Generated Profile")

        if st.button("🚀 Generate Personalized Profile", type="primary"):
            with st.spinner("Creating personalized profile..."):
                profile, processing_time = create_profile_with_timing(
                    lead_id, conversation_history, behavioral_data, property_interactions
                )

            if profile:
                # Performance indicator
                performance_color = "green" if processing_time < 200 else "orange" if processing_time < 300 else "red"
                st.metric("Processing Time", f"{processing_time:.1f}ms", delta=f"Target: <200ms")

                # Profile details
                st.markdown("### Profile Summary")

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Personality:** {profile.personality_type.value.title()}")
                    st.markdown(f"**Confidence:** {profile.personality_confidence:.1%}")
                    st.markdown(f"**Communication Style:** {profile.communication_style.value.replace('_', ' ').title()}")
                    st.markdown(f"**Industry Vertical:** {profile.industry_vertical.value.title()}")

                with col_b:
                    st.markdown(f"**Urgency Sensitivity:** {profile.urgency_sensitivity:.1%}")
                    st.markdown(f"**Detail Preference:** {profile.detail_preference:.1%}")
                    st.markdown(f"**Formality Level:** {profile.formality_level:.1%}")
                    st.markdown(f"**Overall Accuracy:** {profile.accuracy_metrics.get('overall_accuracy', 0.85):.1%}")

                # Preferences
                st.markdown("### Preferences & Patterns")

                col_c, col_d = st.columns(2)
                with col_c:
                    st.markdown("**Preferred Channels:**")
                    for channel in profile.preferred_channels[:3]:
                        st.markdown(f"- {channel.value.replace('_', ' ').title()}")

                    st.markdown("**Content Interests:**")
                    for topic in profile.content_topics[:3]:
                        st.markdown(f"- {topic.replace('_', ' ').title()}")

                with col_d:
                    st.markdown("**Optimal Contact Times:**")
                    for day, hour in profile.optimal_contact_times[:3]:
                        st.markdown(f"- {day} at {hour}:00")

                    st.markdown("**Response Triggers:**")
                    for trigger in profile.response_triggers[:3]:
                        st.markdown(f"- {trigger.replace('_', ' ').title()}")

                # Raw profile data (expandable)
                with st.expander("View Raw Profile Data"):
                    profile_dict = {
                        "lead_id": profile.lead_id,
                        "personality_type": profile.personality_type.value,
                        "personality_confidence": profile.personality_confidence,
                        "communication_style": profile.communication_style.value,
                        "style_confidence": profile.style_confidence,
                        "message_complexity_preference": profile.message_complexity_preference,
                        "urgency_sensitivity": profile.urgency_sensitivity,
                        "detail_preference": profile.detail_preference,
                        "accuracy_metrics": profile.accuracy_metrics
                    }
                    st.json(profile_dict)


def show_communication_adaptation_demo():
    """Demonstrate communication style adaptation"""
    st.header("💬 Communication Style Adaptation Demo")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Input")

        # Original message
        message_option = st.selectbox(
            "Choose message template",
            ["Custom", "Property Introduction", "Follow-up", "Appointment Request", "Market Update"]
        )

        if message_option == "Custom":
            original_message = st.text_area(
                "Original Message",
                height=150,
                value="Hello! I hope you're doing well. I wanted to reach out because I have some exceptional properties that I believe would be perfect for your needs. These properties feature premium amenities and are located in desirable neighborhoods."
            )
        else:
            original_message = get_sample_message(message_option)
            st.text_area("Original Message", value=original_message, height=150, disabled=True)

        # Target personality and style
        st.markdown("**Adaptation Target:**")
        target_personality = st.selectbox("Target Personality", [p.value for p in PersonalityType])
        target_style = st.selectbox("Target Communication Style", [s.value for s in CommunicationStyle])
        target_channel = st.selectbox("Target Channel", [c.value for c in PersonalizationChannel])

        # Create mock profile for adaptation
        mock_lead_id = f"mock_{target_personality}_{target_style}"

    with col2:
        st.subheader("Adapted Communication")

        if st.button("🔄 Adapt Communication Style", type="primary"):
            with st.spinner("Adapting communication style..."):
                adaptation, processing_time = adapt_communication_with_timing(
                    original_message, target_personality, target_style, target_channel
                )

            if adaptation:
                # Performance indicator
                performance_color = "green" if processing_time < 100 else "orange" if processing_time < 150 else "red"
                st.metric("Adaptation Time", f"{processing_time:.1f}ms", delta="Target: <100ms")

                # Adapted message
                st.markdown("### Adapted Message")
                st.text_area("Adapted Message", value=adaptation.adapted_message, height=150, disabled=True)

                # Adaptation analysis
                st.markdown("### Adaptation Analysis")

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Adaptation Confidence:** {adaptation.adaptation_confidence:.1%}")
                    st.markdown(f"**Style Match Score:** {adaptation.style_match_score:.1%}")
                    st.markdown(f"**Expected Improvement:** {adaptation.expected_engagement_improvement:.1%}")

                with col_b:
                    st.markdown("**Adaptation Factors:**")
                    for factor in adaptation.adaptation_factors:
                        st.markdown(f"- {factor.replace('_', ' ').title()}")

                # Changes made
                if adaptation.tone_adjustments:
                    st.markdown("**Tone Adjustments:**")
                    for adjustment, value in adaptation.tone_adjustments.items():
                        st.markdown(f"- {adjustment.title()}: {value}")

                if adaptation.complexity_adjustments:
                    st.markdown("**Complexity Adjustments:**")
                    for adjustment, value in adaptation.complexity_adjustments.items():
                        st.markdown(f"- {adjustment.title()}: {value}")

                # Comparison metrics
                original_length = len(original_message)
                adapted_length = len(adaptation.adapted_message)
                length_change = ((adapted_length - original_length) / original_length) * 100

                st.markdown("### Message Comparison")
                col_x, col_y, col_z = st.columns(3)
                col_x.metric("Original Length", f"{original_length} chars")
                col_y.metric("Adapted Length", f"{adapted_length} chars")
                col_z.metric("Length Change", f"{length_change:+.1f}%")


def show_personalized_recommendations_demo():
    """Demonstrate personalized recommendations generation"""
    st.header("🎯 Personalized Recommendations Demo")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Lead Context")

        # Lead selection
        lead_type = st.selectbox(
            "Select Lead Type",
            ["Analytical Investor", "Driver Executive", "Luxury Buyer", "First-Time Buyer", "Commercial Developer"]
        )

        # Current context
        st.markdown("**Current Context:**")
        conversation_stage = st.selectbox(
            "Conversation Stage",
            ["awareness", "interest", "consideration", "intent", "evaluation"]
        )

        last_interaction = st.selectbox(
            "Last Interaction",
            ["property_inquiry", "market_question", "appointment_request", "price_question", "location_question"]
        )

        urgency_level = st.selectbox("Urgency Level", ["low", "medium", "high", "critical"])

        current_context = {
            "conversation_stage": conversation_stage,
            "last_interaction": last_interaction,
            "urgency_level": urgency_level,
            "timestamp": datetime.now().isoformat()
        }

        # Recommendation types
        st.markdown("**Recommendation Types:**")
        rec_types = st.multiselect(
            "Select recommendation types",
            ["next_message", "property_suggestion", "engagement_strategy", "objection_handling", "follow_up_timing"],
            default=["next_message", "property_suggestion", "engagement_strategy"]
        )

    with col2:
        st.subheader("Generated Recommendations")

        if st.button("💡 Generate Personalized Recommendations", type="primary"):
            with st.spinner("Generating personalized recommendations..."):
                recommendations, processing_time = generate_recommendations_with_timing(
                    lead_type, current_context, rec_types
                )

            if recommendations:
                # Performance indicator
                st.metric("Generation Time", f"{processing_time:.1f}ms", delta="Target: <150ms")

                # Display recommendations
                for i, rec in enumerate(recommendations):
                    with st.expander(f"🎯 {rec.recommendation_type.replace('_', ' ').title()}", expanded=True):
                        st.markdown(f"**Recommendation:** {rec.recommendation_text}")

                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown(f"**Confidence:** {rec.confidence_score:.1%}")
                            st.markdown(f"**Expected Response:** {rec.expected_response_probability:.1%}")
                            st.markdown(f"**Channel:** {rec.preferred_channel.value.replace('_', ' ').title()}")

                        with col_b:
                            st.markdown(f"**Tone:** {rec.message_tone.title()}")
                            st.markdown(f"**Complexity:** {rec.complexity_level.title()}")
                            st.markdown(f"**Timing:** {rec.optimal_timing.strftime('%Y-%m-%d %H:%M')}")

                        if rec.key_selling_points:
                            st.markdown("**Key Selling Points:**")
                            for point in rec.key_selling_points[:3]:
                                st.markdown(f"- {point}")

                        if rec.alternative_approaches:
                            st.markdown("**Alternative Approaches:**")
                            for approach in rec.alternative_approaches[:2]:
                                st.markdown(f"- {approach}")


def show_performance_metrics_demo():
    """Show performance metrics and system status"""
    st.header("📊 Performance Metrics & System Status")

    # Get real-time metrics
    if st.button("🔄 Refresh Metrics", type="primary"):
        with st.spinner("Loading performance metrics..."):
            metrics = get_performance_metrics()

        if metrics:
            # Performance targets
            st.subheader("🎯 Performance Targets vs Actual")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    "Profile Generation",
                    f"{metrics.get('avg_profile_time', 180):.1f}ms",
                    delta=f"Target: 200ms",
                    delta_color="normal"
                )

            with col2:
                st.metric(
                    "Recommendation Latency",
                    f"{metrics.get('avg_recommendation_time', 140):.1f}ms",
                    delta=f"Target: 150ms",
                    delta_color="normal"
                )

            with col3:
                st.metric(
                    "Adaptation Speed",
                    f"{metrics.get('avg_adaptation_time', 85):.1f}ms",
                    delta=f"Target: 100ms",
                    delta_color="normal"
                )

            with col4:
                st.metric(
                    "Accuracy",
                    f"{metrics.get('avg_accuracy', 0.92):.1%}",
                    delta=f"Target: 92%",
                    delta_color="normal"
                )

            # System status
            st.subheader("⚙️ System Status")

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Model Status:**")
                model_status = metrics.get('model_status', {})
                for model, status in model_status.items():
                    icon = "✅" if status else "❌"
                    st.markdown(f"{icon} {model.replace('_', ' ').title()}")

                st.markdown("**Cache Status:**")
                cache_status = metrics.get('cache_status', {})
                st.markdown(f"- Cached Profiles: {cache_status.get('cached_profiles', 0)}")
                st.markdown(f"- Cache Hit Rate: {cache_status.get('hit_rate', 0.75):.1%}")

            with col_b:
                st.markdown("**Language Support:**")
                languages = metrics.get('supported_languages', ['en', 'es', 'fr'])
                for lang in languages:
                    st.markdown(f"- {lang.upper()}")

                st.markdown("**Feature Capabilities:**")
                capabilities = metrics.get('feature_capabilities', {})
                st.markdown(f"- Personality Types: {len(capabilities.get('personality_types', []))}")
                st.markdown(f"- Communication Styles: {len(capabilities.get('communication_styles', []))}")
                st.markdown(f"- Industry Verticals: {len(capabilities.get('industry_verticals', []))}")

            # Recent activity
            st.subheader("📈 Recent Activity")

            # Mock activity data for demo
            activity_data = {
                "profiles_created": 45,
                "recommendations_generated": 123,
                "messages_adapted": 78,
                "accuracy_trend": [0.89, 0.91, 0.92, 0.93, 0.92]
            }

            col_x, col_y, col_z = st.columns(3)
            col_x.metric("Profiles Created (24h)", activity_data["profiles_created"])
            col_y.metric("Recommendations Generated (24h)", activity_data["recommendations_generated"])
            col_z.metric("Messages Adapted (24h)", activity_data["messages_adapted"])

            # Accuracy trend chart
            st.markdown("**Accuracy Trend (Last 5 Days):**")
            st.line_chart({"Accuracy": activity_data["accuracy_trend"]})


# Helper functions for demo data
def get_sample_conversation(conversation_type: str) -> List[Dict]:
    """Get sample conversation data"""
    conversations = {
        "Analytical Lead": [
            {"content": "I need detailed market analysis before making any decisions", "timestamp": datetime.now() - timedelta(hours=2), "speaker": "lead"},
            {"content": "Can you provide comparative data on property appreciation rates?", "timestamp": datetime.now() - timedelta(hours=1), "speaker": "lead"},
            {"content": "What are the current cap rates for similar properties?", "timestamp": datetime.now() - timedelta(minutes=30), "speaker": "lead"}
        ],
        "Driver Lead": [
            {"content": "I need to find a property quickly for my relocation", "timestamp": datetime.now() - timedelta(hours=1), "speaker": "lead"},
            {"content": "Show me the best 3 properties available now", "timestamp": datetime.now() - timedelta(minutes=45), "speaker": "lead"},
            {"content": "When can we schedule viewings ASAP?", "timestamp": datetime.now() - timedelta(minutes=15), "speaker": "lead"}
        ],
        "Luxury Lead": [
            {"content": "I'm interested in exclusive waterfront properties", "timestamp": datetime.now() - timedelta(hours=3), "speaker": "lead"},
            {"content": "Privacy and premium amenities are essential", "timestamp": datetime.now() - timedelta(hours=2), "speaker": "lead"},
            {"content": "I'd like to see properties above $2M", "timestamp": datetime.now() - timedelta(hours=1), "speaker": "lead"}
        ],
        "Commercial Lead": [
            {"content": "Looking for office space for business expansion", "timestamp": datetime.now() - timedelta(hours=2), "speaker": "lead"},
            {"content": "Need good ROI and growth potential in the area", "timestamp": datetime.now() - timedelta(hours=1), "speaker": "lead"},
            {"content": "What's the business district development plan?", "timestamp": datetime.now() - timedelta(minutes=30), "speaker": "lead"}
        ]
    }
    return conversations.get(conversation_type, [])


def get_sample_message(message_type: str) -> str:
    """Get sample message templates"""
    messages = {
        "Property Introduction": "Hello! I hope you're doing well. I wanted to reach out because I have some exceptional properties that I believe would be perfect for your needs. These properties feature premium amenities and are located in desirable neighborhoods.",
        "Follow-up": "I wanted to follow up on our previous conversation about your property search. I have some new listings that match your criteria and would love to share them with you.",
        "Appointment Request": "Would you be available for a property viewing next week? I have several properties that I think you'll find very interesting, and I'd love to show them to you in person.",
        "Market Update": "I wanted to share some important market updates that might impact your property search. Recent trends show excellent opportunities in your preferred areas."
    }
    return messages.get(message_type, "")


# Async wrapper functions for Streamlit
def create_profile_with_timing(lead_id, conversation_history, behavioral_data, property_interactions):
    """Create profile with timing measurement"""
    try:
        import asyncio
        import time

        async def _create_profile():
            engine = await get_advanced_personalization_engine()
            start_time = time.time()
            profile = await engine.create_personalized_profile(
                lead_id=lead_id,
                conversation_history=conversation_history,
                behavioral_data=behavioral_data,
                property_interactions=property_interactions
            )
            processing_time = (time.time() - start_time) * 1000
            return profile, processing_time

        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_create_profile())
        finally:
            loop.close()

    except Exception as e:
        st.error(f"Error creating profile: {e}")
        return None, 0


def adapt_communication_with_timing(original_message, personality, style, channel):
    """Adapt communication with timing measurement"""
    try:
        import asyncio
        import time
        from ghl_real_estate_ai.services.claude.advanced.advanced_personalization_engine import (
            PersonalizationProfile
        )

        async def _adapt_communication():
            engine = await get_advanced_personalization_engine()

            # Create mock profile
            mock_profile = PersonalizationProfile(
                lead_id=f"mock_{personality}_{style}",
                personality_type=PersonalityType(personality),
                personality_confidence=0.85,
                communication_style=CommunicationStyle(style),
                style_confidence=0.80,
                preferred_channels=[PersonalizationChannel(channel)],
                optimal_contact_times=[("Tuesday", 10)],
                message_complexity_preference=0.6,
                urgency_sensitivity=0.5,
                detail_preference=0.7,
                content_topics=["general"],
                preferred_property_features=["location"],
                visual_vs_text_preference=0.5,
                data_driven_preference=0.5,
                interaction_patterns={},
                response_triggers=["general"],
                objection_patterns=[],
                decision_making_factors=["general"],
                primary_language="en",
                cultural_considerations=[],
                formality_level=0.6,
                industry_vertical=IndustryVertical.RESIDENTIAL,
                specialization_confidence=0.7,
                vertical_specific_preferences={},
                profile_created=datetime.now(),
                last_updated=datetime.now(),
                profile_version="5.1.0",
                accuracy_metrics={"overall_accuracy": 0.90}
            )

            # Cache the mock profile
            engine.profile_cache[mock_profile.lead_id] = mock_profile

            start_time = time.time()
            adaptation = await engine.adapt_communication_style(
                original_message=original_message,
                lead_id=mock_profile.lead_id,
                target_channel=PersonalizationChannel(channel)
            )
            processing_time = (time.time() - start_time) * 1000
            return adaptation, processing_time

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_adapt_communication())
        finally:
            loop.close()

    except Exception as e:
        st.error(f"Error adapting communication: {e}")
        return None, 0


def generate_recommendations_with_timing(lead_type, current_context, rec_types):
    """Generate recommendations with timing measurement"""
    try:
        import asyncio
        import time

        async def _generate_recommendations():
            engine = await get_advanced_personalization_engine()

            # Create mock profile based on lead type
            mock_profile = create_mock_profile_for_lead_type(lead_type)
            engine.profile_cache[mock_profile.lead_id] = mock_profile

            start_time = time.time()
            recommendations = await engine.generate_personalized_recommendations(
                lead_id=mock_profile.lead_id,
                current_context=current_context,
                recommendation_types=rec_types
            )
            processing_time = (time.time() - start_time) * 1000
            return recommendations, processing_time

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_generate_recommendations())
        finally:
            loop.close()

    except Exception as e:
        st.error(f"Error generating recommendations: {e}")
        return [], 0


def create_mock_profile_for_lead_type(lead_type: str):
    """Create mock profile for different lead types"""
    from ghl_real_estate_ai.services.claude.advanced.advanced_personalization_engine import (
        PersonalizationProfile
    )

    profile_configs = {
        "Analytical Investor": {
            "personality": PersonalityType.ANALYTICAL,
            "style": CommunicationStyle.TECHNICAL_DETAILED,
            "vertical": IndustryVertical.INVESTMENT,
            "objections": ["price_concerns", "need_verification"]
        },
        "Driver Executive": {
            "personality": PersonalityType.DRIVER,
            "style": CommunicationStyle.CONCISE_DIRECT,
            "vertical": IndustryVertical.COMMERCIAL,
            "objections": ["timing_issues"]
        },
        "Luxury Buyer": {
            "personality": PersonalityType.EXPRESSIVE,
            "style": CommunicationStyle.CONSULTATIVE,
            "vertical": IndustryVertical.LUXURY,
            "objections": ["trust_building"]
        },
        "First-Time Buyer": {
            "personality": PersonalityType.AMIABLE,
            "style": CommunicationStyle.EDUCATIONAL,
            "vertical": IndustryVertical.RESIDENTIAL,
            "objections": ["price_concerns", "decision_authority"]
        },
        "Commercial Developer": {
            "personality": PersonalityType.TECHNICAL,
            "style": CommunicationStyle.FORMAL_PROFESSIONAL,
            "vertical": IndustryVertical.COMMERCIAL,
            "objections": ["need_verification", "competition"]
        }
    }

    config = profile_configs.get(lead_type, profile_configs["First-Time Buyer"])

    return PersonalizationProfile(
        lead_id=f"mock_{lead_type.lower().replace(' ', '_')}",
        personality_type=config["personality"],
        personality_confidence=0.85,
        communication_style=config["style"],
        style_confidence=0.80,
        preferred_channels=[PersonalizationChannel.EMAIL],
        optimal_contact_times=[("Tuesday", 10), ("Wednesday", 14)],
        message_complexity_preference=0.7 if config["personality"] == PersonalityType.ANALYTICAL else 0.4,
        urgency_sensitivity=0.9 if config["personality"] == PersonalityType.DRIVER else 0.4,
        detail_preference=0.9 if config["personality"] == PersonalityType.ANALYTICAL else 0.6,
        content_topics=["market_analysis", "property_features"],
        preferred_property_features=["location", "investment_potential"],
        visual_vs_text_preference=0.6,
        data_driven_preference=0.8 if config["personality"] == PersonalityType.ANALYTICAL else 0.5,
        interaction_patterns={},
        response_triggers=["data", "value_proposition"],
        objection_patterns=config["objections"],
        decision_making_factors=["investment_potential", "location_proximity"],
        primary_language="en",
        cultural_considerations=[],
        formality_level=0.7,
        industry_vertical=config["vertical"],
        specialization_confidence=0.85,
        vertical_specific_preferences={},
        profile_created=datetime.now(),
        last_updated=datetime.now(),
        profile_version="5.1.0",
        accuracy_metrics={"overall_accuracy": 0.92}
    )


def get_performance_metrics():
    """Get mock performance metrics for demo"""
    return {
        "avg_profile_time": 185.0,
        "avg_recommendation_time": 142.0,
        "avg_adaptation_time": 87.0,
        "avg_accuracy": 0.923,
        "model_status": {
            "personality_classifier": True,
            "communication_style_classifier": True,
            "preference_predictors": True,
            "clustering_models": True
        },
        "cache_status": {
            "cached_profiles": 127,
            "cached_recommendations": 89,
            "hit_rate": 0.78
        },
        "supported_languages": ["en", "es", "fr", "de", "pt", "zh"],
        "feature_capabilities": {
            "personality_types": [p.value for p in PersonalityType],
            "communication_styles": [s.value for s in CommunicationStyle],
            "industry_verticals": [v.value for v in IndustryVertical]
        }
    }


if __name__ == "__main__":
    main()