"""
Mobile Advanced UI Demo (Phase 5: Mobile Platform Integration)

Interactive Streamlit demo showcasing touch-optimized UI components for
advanced mobile AI features. Demonstrates gesture recognition, voice commands,
haptic feedback simulation, and mobile-specific optimizations.

Features Demonstrated:
- Touch gesture simulation and recognition
- Voice command interface
- Multi-language mobile coaching
- Behavioral predictions mobile display
- Battery optimization interface
- Offline capability indicators
- Responsive design for mobile devices
- Accessibility features
- Performance monitoring
"""

import streamlit as st
import time
import json
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Import mobile services
try:
    from ghl_real_estate_ai.services.claude.mobile import (
        AdvancedMobileIntegrationService,
        MobileAdvancedFeaturesService,
        MobileAdvancedFeatureType,
        MobilePlatformMode,
        MobileDeviceCapability,
        TouchGestureType,
        VoiceCommandType,
        MobileNotificationType
    )
    from ghl_real_estate_ai.services.claude.advanced.multi_language_voice_service import (
        SupportedLanguage, CulturalContext
    )
    from ghl_real_estate_ai.config.mobile.settings import (
        ADVANCED_MOBILE_CONFIG,
        TOUCH_GESTURE_CONFIG,
        VOICE_COMMAND_CONFIG,
        MOBILE_NOTIFICATION_CONFIG
    )
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False


def main():
    """Main Mobile Advanced UI Demo"""
    st.set_page_config(
        page_title="📱 Mobile Advanced AI Features Demo",
        page_icon="📱",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Custom CSS for mobile-optimized styling
    st.markdown("""
    <style>
    .mobile-demo-container {
        max-width: 425px;
        margin: 0 auto;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 25px;
        padding: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    }

    .mobile-screen {
        background: #1a1a1a;
        border-radius: 20px;
        padding: 15px;
        min-height: 600px;
        color: white;
        position: relative;
    }

    .touch-zone {
        border: 2px dashed #4CAF50;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        background: rgba(76, 175, 80, 0.1);
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .touch-zone:hover {
        background: rgba(76, 175, 80, 0.2);
        transform: scale(1.02);
    }

    .coaching-panel {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .quick-action-btn {
        display: inline-block;
        padding: 12px 20px;
        margin: 5px;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        border: none;
        border-radius: 25px;
        color: white;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .quick-action-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }

    .haptic-feedback {
        animation: pulse 0.3s ease-in-out;
    }

    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }

    .performance-indicator {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(255, 255, 255, 0.1);
        padding: 8px 12px;
        border-radius: 8px;
        margin: 5px 0;
        font-size: 12px;
    }

    .battery-level {
        width: 30px;
        height: 15px;
        border: 1px solid white;
        border-radius: 2px;
        position: relative;
        margin-left: 10px;
    }

    .battery-fill {
        background: #4CAF50;
        height: 100%;
        border-radius: 1px;
        transition: width 0.3s ease;
    }

    .offline-indicator {
        position: absolute;
        top: 10px;
        right: 10px;
        background: rgba(255, 193, 7, 0.9);
        color: black;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 11px;
        font-weight: bold;
    }

    .language-selector {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
        color: white;
    }

    .prediction-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        color: white;
    }

    .prediction-score {
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        margin: 10px 0;
    }

    .notification-popup {
        position: fixed;
        top: 20px;
        right: 20px;
        background: #2196F3;
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        z-index: 1000;
        animation: slideIn 0.3s ease-out;
    }

    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    .voice-indicator {
        width: 20px;
        height: 20px;
        background: #F44336;
        border-radius: 50%;
        animation: blink 1s infinite;
        margin: 0 5px;
    }

    @keyframes blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.3; }
    }
    </style>
    """, unsafe_allow_html=True)

    # Main title
    st.title("📱 Mobile Advanced AI Features Demo")
    st.markdown("**Phase 5: Complete Mobile Platform Integration**")

    if not SERVICES_AVAILABLE:
        st.error("❌ Mobile services not available. Please check imports.")
        return

    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Demo Controls")

        # Device simulation
        device_type = st.selectbox(
            "📱 Device Type",
            ["iPhone Pro", "Android Flagship", "Budget Android", "Tablet", "Foldable"],
            help="Simulate different device capabilities"
        )

        # Platform mode
        platform_mode = st.selectbox(
            "⚡ Platform Mode",
            ["Full Features", "Battery Optimized", "Data Saver", "Offline Capable", "Performance First"],
            help="Choose mobile platform optimization mode"
        )

        # Language selection
        language = st.selectbox(
            "🌐 Language",
            ["English (US)", "Spanish (Mexico)", "Mandarin (China)", "French (France)"],
            help="Select coaching language"
        )

        # Battery level simulation
        battery_level = st.slider(
            "🔋 Battery Level",
            min_value=0,
            max_value=100,
            value=75,
            help="Simulate battery level for optimization testing"
        )

        # Network status
        network_status = st.selectbox(
            "📡 Network",
            ["WiFi", "Cellular", "Offline"],
            help="Simulate network conditions"
        )

        st.markdown("---")

        # Demo mode
        demo_mode = st.radio(
            "🎯 Demo Focus",
            ["Touch Gestures", "Voice Commands", "Multi-Language", "Predictions", "Performance"],
            help="Choose which feature to demonstrate"
        )

    # Main demo area
    col1, col2 = st.columns([1, 1])

    with col1:
        render_mobile_device_simulator(
            device_type, platform_mode, language, battery_level,
            network_status, demo_mode
        )

    with col2:
        render_feature_controls_and_metrics(demo_mode)


def render_mobile_device_simulator(device_type: str, platform_mode: str,
                                 language: str, battery_level: int,
                                 network_status: str, demo_mode: str):
    """Render mobile device simulator"""

    st.markdown(f"""
    <div class="mobile-demo-container">
        <div class="mobile-screen">
            <div class="performance-indicator">
                <span>{device_type}</span>
                <span>{network_status}</span>
                <div class="battery-level">
                    <div class="battery-fill" style="width: {battery_level}%"></div>
                </div>
            </div>

            {render_offline_indicator(network_status) if network_status == "Offline" else ""}

            <h3 style="text-align: center; margin: 20px 0; color: #4ECDC4;">
                Claude AI Mobile Coach
            </h3>
    """, unsafe_allow_html=True)

    # Render demo based on mode
    if demo_mode == "Touch Gestures":
        render_touch_gesture_demo()
    elif demo_mode == "Voice Commands":
        render_voice_command_demo()
    elif demo_mode == "Multi-Language":
        render_multi_language_demo(language)
    elif demo_mode == "Predictions":
        render_predictions_demo()
    elif demo_mode == "Performance":
        render_performance_demo(battery_level, network_status)

    st.markdown("</div></div>", unsafe_allow_html=True)


def render_offline_indicator(network_status: str) -> str:
    """Render offline indicator"""
    if network_status == "Offline":
        return '<div class="offline-indicator">📴 Offline Mode</div>'
    return ""


def render_touch_gesture_demo():
    """Render touch gesture demonstration"""
    st.markdown("""
        <div class="coaching-panel">
            <h4>🎯 Touch Gesture Demo</h4>
            <p>Try these gestures:</p>
        </div>
    """, unsafe_allow_html=True)

    # Touch zones for different gestures
    gesture_zones = [
        ("👆 Tap", "Next coaching suggestion", "tap"),
        ("👆👆 Double Tap", "Quick action menu", "double_tap"),
        ("👆➡️ Long Press", "Context options", "long_press"),
        ("👈 Swipe Left", "Previous suggestion", "swipe_left"),
        ("👉 Swipe Right", "Next suggestion", "swipe_right"),
        ("👆⬆️ Swipe Up", "Detailed view", "swipe_up"),
        ("🤏 Pinch Out", "Zoom analytics", "pinch_out")
    ]

    for gesture_name, description, gesture_type in gesture_zones:
        if st.button(f"{gesture_name}: {description}", key=f"gesture_{gesture_type}"):
            simulate_haptic_feedback(gesture_type)
            show_gesture_response(gesture_name, description)


def render_voice_command_demo():
    """Render voice command demonstration"""
    st.markdown("""
        <div class="coaching-panel">
            <h4>🎤 Voice Command Demo</h4>
            <div style="text-align: center; margin: 20px 0;">
                <span class="voice-indicator"></span>
                <span>Listening for "Hey Claude"</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Voice command buttons
    voice_commands = [
        ("🗣️ Next Suggestion", "next_suggestion"),
        ("🌐 Translate", "translate"),
        ("📊 Get Prediction", "get_prediction"),
        ("📝 Take Note", "take_note"),
        ("🔋 Battery Saver", "battery_saver"),
        ("🔄 Switch Language", "switch_language")
    ]

    cols = st.columns(2)
    for i, (command_name, command_type) in enumerate(voice_commands):
        col = cols[i % 2]
        with col:
            if st.button(command_name, key=f"voice_{command_type}"):
                simulate_voice_command(command_name, command_type)


def render_multi_language_demo(language: str):
    """Render multi-language coaching demo"""
    # Language mapping
    lang_map = {
        "English (US)": ("en-US", "Hello! I'm here to help with your real estate coaching."),
        "Spanish (Mexico)": ("es-MX", "¡Hola! Estoy aquí para ayudarte con tu coaching inmobiliario."),
        "Mandarin (China)": ("zh-CN", "你好！我在这里帮助您进行房地产指导。"),
        "French (France)": ("fr-FR", "Bonjour ! Je suis là pour vous aider avec votre coaching immobilier.")
    }

    lang_code, sample_text = lang_map.get(language, lang_map["English (US)"])

    st.markdown(f"""
        <div class="coaching-panel">
            <h4>🌐 Multi-Language Coaching</h4>
            <div class="language-selector">
                <strong>Current Language:</strong> {language}<br>
                <strong>Cultural Context:</strong> {"Latin American" if "Spanish" in language else "North American" if "English" in language else "Asian Pacific" if "Mandarin" in language else "European"}
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin: 10px 0;">
                <em>"{sample_text}"</em>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Cultural adaptation features
    if st.button("🎭 Apply Cultural Adaptations", key="cultural_adapt"):
        show_cultural_adaptations(language)

    # Translation demo
    if st.button("🔄 Real-time Translation", key="translate_demo"):
        show_translation_demo(language)


def render_predictions_demo():
    """Render behavioral predictions demo"""
    # Generate sample prediction data
    predictions = generate_sample_predictions()

    st.markdown("""
        <div class="coaching-panel">
            <h4>🔮 Behavioral Predictions</h4>
        </div>
    """, unsafe_allow_html=True)

    for prediction in predictions:
        score_color = "#4CAF50" if prediction['score'] > 0.7 else "#FF9800" if prediction['score'] > 0.4 else "#F44336"

        st.markdown(f"""
            <div class="prediction-card">
                <h5>{prediction['name']}</h5>
                <div class="prediction-score" style="color: {score_color};">
                    {prediction['score']:.0%}
                </div>
                <p style="font-size: 12px; margin: 0;">
                    {prediction['description']}
                </p>
            </div>
        """, unsafe_allow_html=True)

    # Prediction controls
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Predictions", key="refresh_predictions"):
            st.rerun()

    with col2:
        if st.button("⚠️ Alert Settings", key="prediction_alerts"):
            show_prediction_alerts()


def render_performance_demo(battery_level: int, network_status: str):
    """Render performance monitoring demo"""
    # Calculate performance metrics based on conditions
    base_response_time = 45  # ms
    battery_factor = 1.0 + (0.5 if battery_level < 30 else 0.2 if battery_level < 60 else 0.0)
    network_factor = 1.0 if network_status == "WiFi" else 1.5 if network_status == "Cellular" else 3.0

    response_time = base_response_time * battery_factor * network_factor

    st.markdown(f"""
        <div class="coaching-panel">
            <h4>⚡ Performance Monitoring</h4>

            <div class="performance-indicator">
                <span>Response Time</span>
                <span style="color: {'#4CAF50' if response_time < 100 else '#FF9800' if response_time < 200 else '#F44336'};">
                    {response_time:.0f}ms
                </span>
            </div>

            <div class="performance-indicator">
                <span>Battery Impact</span>
                <span style="color: {'#4CAF50' if battery_level > 50 else '#FF9800' if battery_level > 20 else '#F44336'};">
                    {2.5 if battery_level > 50 else 1.8 if battery_level > 20 else 1.2:.1f}%/hour
                </span>
            </div>

            <div class="performance-indicator">
                <span>Data Usage</span>
                <span style="color: {'#4CAF50' if network_status == 'WiFi' else '#FF9800'};">
                    {"Optimized" if network_status != "WiFi" else "Normal"}
                </span>
            </div>

            <div class="performance-indicator">
                <span>Offline Features</span>
                <span style="color: {'#4CAF50' if network_status == 'Offline' else '#666'};">
                    {"80% Available" if network_status == "Offline" else "100% Available"}
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Performance optimization controls
    if battery_level < 30:
        if st.button("🔋 Enable Battery Saver", key="battery_saver_enable"):
            show_battery_optimization()

    if network_status == "Cellular":
        if st.button("📱 Optimize for Mobile Data", key="data_optimize"):
            show_data_optimization()


def render_feature_controls_and_metrics(demo_mode: str):
    """Render feature controls and performance metrics"""
    st.subheader("🎛️ Feature Controls & Metrics")

    # Performance metrics
    with st.expander("📊 Real-time Performance Metrics", expanded=True):
        # Generate sample metrics
        metrics_data = generate_performance_metrics(demo_mode)

        # Display metrics as charts
        fig_response = create_response_time_chart(metrics_data['response_times'])
        st.plotly_chart(fig_response, use_container_width=True)

        # Performance indicators
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Avg Response",
                f"{metrics_data['avg_response_time']:.0f}ms",
                delta=f"{metrics_data['response_time_delta']:.0f}ms",
                help="Average response time for mobile features"
            )

        with col2:
            st.metric(
                "Battery Impact",
                f"{metrics_data['battery_impact']:.1f}%/hr",
                delta=f"{metrics_data['battery_delta']:.1f}%/hr",
                help="Estimated battery consumption rate"
            )

        with col3:
            st.metric(
                "Data Saved",
                f"{metrics_data['data_saved']:.0f}%",
                delta=f"{metrics_data['data_delta']:.0f}%",
                help="Data usage reduction vs desktop"
            )

    # Feature configuration
    with st.expander("⚙️ Feature Configuration", expanded=False):
        render_feature_configuration(demo_mode)

    # Mobile integration status
    with st.expander("🔍 Integration Status", expanded=False):
        render_integration_status()


def render_feature_configuration(demo_mode: str):
    """Render feature configuration controls"""
    st.markdown("**Customize mobile feature behavior:**")

    if demo_mode == "Touch Gestures":
        st.checkbox("🤚 Haptic Feedback", value=True, help="Enable haptic feedback for gestures")
        st.slider("👆 Touch Sensitivity", 0.5, 2.0, 1.0, 0.1, help="Adjust gesture sensitivity")
        st.checkbox("♿ Accessibility Mode", value=False, help="Larger touch targets for accessibility")

    elif demo_mode == "Voice Commands":
        st.slider("🎤 Voice Confidence", 0.5, 1.0, 0.7, 0.05, help="Minimum confidence for voice recognition")
        st.checkbox("🔇 Background Listening", value=False, help="Listen for commands in background")
        st.selectbox("🔊 Voice Feedback", ["Enabled", "Disabled", "Silent Mode"], help="Voice response configuration")

    elif demo_mode == "Multi-Language":
        st.checkbox("🔄 Auto-detect Language", value=True, help="Automatically detect spoken language")
        st.checkbox("🌍 Cultural Adaptation", value=True, help="Apply cultural context adaptations")
        st.slider("⚡ Translation Speed", 50, 200, 125, 25, help="Translation processing speed (ms)")

    elif demo_mode == "Predictions":
        st.multiselect(
            "📊 Prediction Types",
            ["Conversion Likelihood", "Churn Risk", "Intervention Timing", "Anomaly Detection"],
            default=["Conversion Likelihood", "Intervention Timing"],
            help="Select which predictions to generate"
        )
        st.slider("⏰ Prediction Frequency", 5, 60, 15, 5, help="Prediction update frequency (minutes)")

    elif demo_mode == "Performance":
        st.checkbox("🔋 Adaptive Performance", value=True, help="Automatically adjust based on battery")
        st.checkbox("📊 Background Optimization", value=True, help="Optimize performance in background")
        st.selectbox("🎯 Priority Mode", ["Balanced", "Battery Life", "Performance", "Data Saver"], help="Optimization priority")


def render_integration_status():
    """Render mobile integration status information"""
    # Simulate integration status
    integration_status = {
        "Mobile Services": "✅ Active",
        "Touch Recognition": "✅ Enabled",
        "Voice Commands": "✅ Ready",
        "Multi-Language": "✅ 4 Languages",
        "Behavioral Predictions": "✅ ML Models Loaded",
        "Offline Capabilities": "✅ 80% Available",
        "Performance Optimization": "✅ Adaptive",
        "Cross-platform Sync": "✅ Synchronized"
    }

    st.markdown("**Current integration status:**")

    for service, status in integration_status.items():
        st.markdown(f"- **{service}**: {status}")

    # System health indicators
    st.markdown("---")
    st.markdown("**System Health:**")

    health_data = pd.DataFrame({
        'Component': ['Touch System', 'Voice Engine', 'ML Models', 'Cache System', 'Sync Service'],
        'Status': ['Healthy', 'Healthy', 'Healthy', 'Healthy', 'Healthy'],
        'Response Time (ms)': [15, 180, 95, 25, 350],
        'Memory Usage (MB)': [12, 45, 120, 35, 28]
    })

    st.dataframe(health_data, use_container_width=True)


def simulate_haptic_feedback(gesture_type: str):
    """Simulate haptic feedback for gestures"""
    # In a real implementation, this would trigger actual haptic hardware
    feedback_messages = {
        "tap": "Light tap feedback",
        "double_tap": "Double pulse feedback",
        "long_press": "Strong haptic feedback",
        "swipe_left": "Directional feedback",
        "swipe_right": "Directional feedback",
        "swipe_up": "Rising feedback pattern",
        "pinch_out": "Expanding feedback"
    }

    message = feedback_messages.get(gesture_type, "Generic haptic feedback")
    st.info(f"📳 {message}")


def show_gesture_response(gesture_name: str, description: str):
    """Show response to gesture"""
    responses = {
        "👆 Tap": "Advancing to next coaching suggestion...",
        "👆👆 Double Tap": "Opening quick action menu...",
        "👆➡️ Long Press": "Displaying context options...",
        "👈 Swipe Left": "Moving to previous suggestion...",
        "👉 Swipe Right": "Moving to next suggestion...",
        "👆⬆️ Swipe Up": "Expanding to detailed view...",
        "🤏 Pinch Out": "Zooming into analytics view..."
    }

    response = responses.get(gesture_name, f"Executing {description}")
    st.success(f"✨ {response}")


def simulate_voice_command(command_name: str, command_type: str):
    """Simulate voice command processing"""
    processing_messages = {
        "next_suggestion": "Moving to next coaching suggestion",
        "translate": "Translating to selected language",
        "get_prediction": "Generating behavioral predictions",
        "take_note": "Recording voice note",
        "battery_saver": "Enabling battery optimization",
        "switch_language": "Switching interface language"
    }

    message = processing_messages.get(command_type, "Processing voice command")
    st.success(f"🎤 {message}...")


def show_cultural_adaptations(language: str):
    """Show cultural adaptations for selected language"""
    adaptations = {
        "Spanish (Mexico)": [
            "🏠 Formal address forms (Usted)",
            "👨‍👩‍👧‍👦 Family-centric decision making",
            "⏰ Flexible timing approach",
            "🤝 Relationship-first communication"
        ],
        "Mandarin (China)": [
            "🎎 Hierarchical communication style",
            "👥 Group consultation considerations",
            "📊 Detailed analytical approach",
            "🕐 Long-term decision perspective"
        ],
        "French (France)": [
            "📋 Formal business protocols",
            "📖 Detailed documentation preference",
            "⚖️ Systematic evaluation process",
            "🎨 Aesthetic and quality focus"
        ]
    }

    if language in adaptations:
        st.info("🎭 **Cultural Adaptations Applied:**")
        for adaptation in adaptations[language]:
            st.markdown(f"- {adaptation}")
    else:
        st.info("🌍 **Standard North American adaptations applied**")


def show_translation_demo(language: str):
    """Show real-time translation demo"""
    translations = {
        "English (US)": "The client is showing strong interest in this property.",
        "Spanish (Mexico)": "El cliente está mostrando un fuerte interés en esta propiedad.",
        "Mandarin (China)": "客户对这个房产表现出强烈的兴趣。",
        "French (France)": "Le client montre un vif intérêt pour cette propriété."
    }

    original_text = "The client is showing strong interest in this property."
    translated_text = translations.get(language, original_text)

    st.success(f"""
    🔄 **Real-time Translation:**

    **Original:** {original_text}

    **Translated ({language}):** {translated_text}

    ⚡ Translation completed in 125ms
    """)


def generate_sample_predictions() -> List[Dict[str, Any]]:
    """Generate sample behavioral prediction data"""
    return [
        {
            "name": "Conversion Likelihood",
            "score": 0.78,
            "description": "High probability based on engagement patterns"
        },
        {
            "name": "Churn Risk",
            "score": 0.23,
            "description": "Low risk - consistent communication"
        },
        {
            "name": "Intervention Timing",
            "score": 0.91,
            "description": "Optimal time for follow-up contact"
        },
        {
            "name": "Decision Readiness",
            "score": 0.65,
            "description": "Approaching decision point"
        }
    ]


def show_prediction_alerts():
    """Show prediction alert configuration"""
    st.info("""
    ⚠️ **Prediction Alert Settings:**

    - 🔔 Conversion probability > 80% → Immediate notification
    - ⚠️ Churn risk > 70% → High priority alert
    - ⏰ Optimal intervention timing → Scheduled reminder
    - 🎯 Decision readiness > 85% → Action recommendation
    """)


def show_battery_optimization():
    """Show battery optimization features"""
    st.info("""
    🔋 **Battery Saver Mode Activated:**

    - ⚡ Reduced background processing
    - 📱 Lower refresh rate
    - 🔇 Disabled haptic feedback
    - 🎨 Simplified animations
    - 📊 Limited real-time predictions

    ⏱️ Estimated additional usage: +2.5 hours
    """)


def show_data_optimization():
    """Show data usage optimization"""
    st.info("""
    📱 **Mobile Data Optimization:**

    - 🗜️ Response compression enabled
    - 📷 Reduced image quality
    - 📊 Cached analytics data
    - ⏸️ Paused background sync
    - 🔄 WiFi-only updates

    💾 Data savings: ~75% vs WiFi mode
    """)


def generate_performance_metrics(demo_mode: str) -> Dict[str, Any]:
    """Generate sample performance metrics"""
    # Base metrics with some variation
    base_response = 45
    variation = np.random.normal(0, 10, 20)
    response_times = np.clip(base_response + variation, 20, 200)

    return {
        'response_times': response_times,
        'avg_response_time': np.mean(response_times),
        'response_time_delta': np.random.uniform(-5, 15),
        'battery_impact': 2.8 + np.random.uniform(-0.5, 1.0),
        'battery_delta': np.random.uniform(-0.3, 0.5),
        'data_saved': 72 + np.random.uniform(-5, 8),
        'data_delta': np.random.uniform(-2, 5)
    }


def create_response_time_chart(response_times):
    """Create response time performance chart"""
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            y=response_times,
            mode='lines+markers',
            name='Response Time',
            line=dict(color='#4ECDC4', width=2),
            marker=dict(size=4)
        ))

        # Add target line
        fig.add_hline(
            y=100,
            line_dash="dash",
            line_color="red",
            annotation_text="Target: 100ms"
        )

        fig.update_layout(
            title="Mobile Response Time Performance",
            xaxis_title="Time (last 20 measurements)",
            yaxis_title="Response Time (ms)",
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

        return fig

    except ImportError:
        # Fallback to simple line chart if plotly not available
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(response_times, marker='o', linewidth=2, markersize=3)
        ax.axhline(y=100, color='r', linestyle='--', alpha=0.7, label='Target: 100ms')
        ax.set_xlabel('Time (last 20 measurements)')
        ax.set_ylabel('Response Time (ms)')
        ax.set_title('Mobile Response Time Performance')
        ax.legend()
        ax.grid(True, alpha=0.3)

        return fig


if __name__ == "__main__":
    main()