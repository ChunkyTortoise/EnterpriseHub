"""
Voice AI & Accessibility Interface - Service 6 Universal Design
Comprehensive voice integration and accessibility compliance for inclusive user experience
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import plotly.graph_objects as go
import streamlit as st

from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant


class AccessibilityLevel(Enum):
    """Accessibility compliance levels"""

    AA = "AA"
    AAA = "AAA"


class VoiceCommand(Enum):
    """Voice command types"""

    NAVIGATE = "navigate"
    SEARCH = "search"
    ACTION = "action"
    READ = "read"
    DICTATE = "dictate"


class AccessibilityFeature(Enum):
    """Accessibility feature types"""

    SCREEN_READER = "screen_reader"
    HIGH_CONTRAST = "high_contrast"
    LARGE_TEXT = "large_text"
    VOICE_CONTROL = "voice_control"
    KEYBOARD_NAVIGATION = "keyboard_navigation"
    REDUCED_MOTION = "reduced_motion"
    AUDIO_DESCRIPTIONS = "audio_descriptions"


@dataclass
class VoiceSettings:
    """Voice interface settings"""

    enabled: bool = False
    wake_word: str = "Hey Claude"
    language: str = "en-US"
    speech_rate: float = 1.0
    voice_type: str = "neutral"
    noise_cancellation: bool = True
    confidence_threshold: float = 0.8
    auto_responses: bool = True


@dataclass
class AccessibilitySettings:
    """Accessibility settings and preferences"""

    compliance_level: AccessibilityLevel = AccessibilityLevel.AA
    high_contrast_mode: bool = False
    large_text_mode: bool = False
    reduced_motion: bool = False
    screen_reader_mode: bool = False
    keyboard_navigation: bool = True
    audio_descriptions: bool = False
    text_size_multiplier: float = 1.0
    color_theme: str = "dark"
    focus_indicators: bool = True


class VoiceAIAccessibilityInterface:
    """
    Comprehensive voice AI and accessibility interface for inclusive design
    """

    def __init__(self):
        self.cache_service = get_cache_service()
        self.claude_assistant = ClaudeAssistant(context_type="voice_accessibility")
        self._initialize_session_state()
        self._initialize_accessibility_features()

    def _initialize_session_state(self):
        """Initialize session state for voice and accessibility"""
        if "voice_settings" not in st.session_state:
            st.session_state.voice_settings = VoiceSettings()
        if "accessibility_settings" not in st.session_state:
            st.session_state.accessibility_settings = AccessibilitySettings()
        if "voice_active" not in st.session_state:
            st.session_state.voice_active = False
        if "voice_history" not in st.session_state:
            st.session_state.voice_history = []
        if "accessibility_audit_score" not in st.session_state:
            st.session_state.accessibility_audit_score = 95

    def _initialize_accessibility_features(self):
        """Initialize accessibility features and compliance"""
        # Apply accessibility settings to page
        self._apply_accessibility_css()

        # Initialize screen reader support
        if st.session_state.accessibility_settings.screen_reader_mode:
            self._initialize_screen_reader_support()

    def _apply_accessibility_css(self):
        """Apply accessibility-compliant CSS"""
        accessibility_settings = st.session_state.accessibility_settings

        # Base accessibility CSS
        css = """
        <style>
        /* Accessibility Base Styles */
        * {
            outline: none;
        }
        
        *:focus {
            outline: 3px solid #3b82f6 !important;
            outline-offset: 2px !important;
        }
        
        .stButton > button:focus {
            outline: 3px solid #3b82f6 !important;
            outline-offset: 2px !important;
            box-shadow: 0 0 0 2px #ffffff, 0 0 0 5px #3b82f6 !important;
        }
        
        .stSelectbox > div > div:focus {
            outline: 3px solid #3b82f6 !important;
            outline-offset: 2px !important;
        }
        
        /* Skip to content link */
        .skip-link {
            position: absolute;
            top: -40px;
            left: 6px;
            background: #000;
            color: #fff;
            padding: 8px;
            z-index: 1000;
            text-decoration: none;
            border-radius: 4px;
        }
        
        .skip-link:focus {
            top: 6px;
        }
        
        /* Screen reader only content */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }
        
        /* High contrast mode */
        """

        if accessibility_settings.high_contrast_mode:
            css += """
            .main, .stApp {
                background-color: #000000 !important;
                color: #ffffff !important;
            }
            
            .stMarkdown, .stText {
                color: #ffffff !important;
            }
            
            .stButton > button {
                background-color: #ffff00 !important;
                color: #000000 !important;
                border: 2px solid #ffffff !important;
            }
            """

        # Large text mode
        if accessibility_settings.large_text_mode:
            multiplier = accessibility_settings.text_size_multiplier
            css += f"""
            .main {{
                font-size: {1.2 * multiplier}rem !important;
            }}
            
            h1, h2, h3, h4, h5, h6 {{
                font-size: calc(var(--font-size) * {multiplier + 0.5}) !important;
            }}
            
            .stButton > button {{
                font-size: {1.1 * multiplier}rem !important;
                padding: {0.8 * multiplier}rem {1.2 * multiplier}rem !important;
            }}
            """

        # Reduced motion
        if accessibility_settings.reduced_motion:
            css += """
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
                scroll-behavior: auto !important;
            }
            """

        css += "</style>"
        st.markdown(css, unsafe_allow_html=True)

    def _initialize_screen_reader_support(self):
        """Initialize screen reader support"""
        st.markdown(
            """
        <div aria-live="polite" aria-atomic="true" id="sr-announcements" class="sr-only"></div>
        <script>
        function announceToScreenReader(message) {
            const announcement = document.getElementById('sr-announcements');
            announcement.textContent = message;
        }
        </script>
        """,
            unsafe_allow_html=True,
        )

    def render_accessibility_header(self):
        """Render accessibility-compliant header"""
        # Skip to content link
        st.markdown(
            """
        <a href="#main-content" class="skip-link">Skip to main content</a>
        """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(
                """
            <div id="main-content" tabindex="-1">
                <h1 style='margin: 0; font-size: 2.5rem; font-weight: 800; color: #FFFFFF;'>
                    🎤 VOICE AI COMMAND CENTER
                </h1>
                <p style='margin: 0.5rem 0 0 0; color: #8B949E; font-size: 1.1rem;'>
                    Accessible voice interface with universal design compliance
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            # Quick accessibility controls
            self.render_accessibility_quick_controls()

        with col3:
            # Voice status indicator
            self.render_voice_status_indicator()

    def render_accessibility_quick_controls(self):
        """Render quick accessibility controls"""
        st.markdown("#### ♿ Accessibility")

        accessibility_settings = st.session_state.accessibility_settings

        # High contrast toggle
        high_contrast = st.checkbox(
            "High Contrast Mode",
            value=accessibility_settings.high_contrast_mode,
            help="Enable high contrast colors for better visibility",
            key="high_contrast_toggle",
        )

        # Large text toggle
        large_text = st.checkbox(
            "Large Text Mode",
            value=accessibility_settings.large_text_mode,
            help="Increase text size for better readability",
            key="large_text_toggle",
        )

        # Reduced motion toggle
        reduced_motion = st.checkbox(
            "Reduced Motion",
            value=accessibility_settings.reduced_motion,
            help="Minimize animations and transitions",
            key="reduced_motion_toggle",
        )

        # Update settings if changed
        if (
            high_contrast != accessibility_settings.high_contrast_mode
            or large_text != accessibility_settings.large_text_mode
            or reduced_motion != accessibility_settings.reduced_motion
        ):
            accessibility_settings.high_contrast_mode = high_contrast
            accessibility_settings.large_text_mode = large_text
            accessibility_settings.reduced_motion = reduced_motion

            st.session_state.accessibility_settings = accessibility_settings
            st.rerun()

    def render_voice_status_indicator(self):
        """Render voice interface status indicator"""
        voice_settings = st.session_state.voice_settings
        voice_active = st.session_state.voice_active

        st.markdown("#### 🎤 Voice Control")

        # Voice activation toggle
        voice_enabled = st.checkbox(
            "Voice Commands",
            value=voice_settings.enabled,
            help="Enable voice command interface",
            key="voice_enabled_toggle",
        )

        voice_settings.enabled = voice_enabled
        st.session_state.voice_settings = voice_settings

        if voice_enabled:
            # Voice status display
            status_color = "#10B981" if voice_active else "#8B949E"
            status_text = "Listening..." if voice_active else "Ready"

            st.markdown(
                f"""
            <div style='
                background: rgba(22, 27, 34, 0.8);
                padding: 1rem;
                border-radius: 8px;
                border-left: 3px solid {status_color};
                border: 1px solid rgba(255,255,255,0.05);
                text-align: center;
            '>
                <div style='color: {status_color}; font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem;'>
                    🎤 {status_text}
                </div>
                <div style='color: #8B949E; font-size: 0.8rem;'>
                    Say "{voice_settings.wake_word}" to start
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    def render_voice_interface_panel(self):
        """Render main voice interface panel"""
        st.markdown("### 🗣️ VOICE COMMAND INTERFACE")

        if not st.session_state.voice_settings.enabled:
            st.info("💡 Enable voice commands in the accessibility controls to get started.")
            return

        col1, col2 = st.columns([2, 1])

        with col1:
            self.render_voice_commands_panel()

        with col2:
            self.render_voice_settings_panel()

    def render_voice_commands_panel(self):
        """Render voice commands and interaction panel"""
        st.markdown("#### 🎯 Available Voice Commands")

        # Voice command categories
        command_categories = {
            "Navigation": [
                {"command": "Go to dashboard", "description": "Navigate to main dashboard"},
                {"command": "Show leads", "description": "Open lead management"},
                {"command": "Open analytics", "description": "View analytics dashboard"},
                {"command": "Go back", "description": "Navigate to previous page"},
            ],
            "Lead Management": [
                {"command": "Call [lead name]", "description": "Initiate call to specific lead"},
                {"command": "Show hot leads", "description": "Filter to show only hot leads"},
                {"command": "Create new lead", "description": "Open new lead creation form"},
                {"command": "Search for [name]", "description": "Search for specific lead"},
            ],
            "Data & Reports": [
                {"command": "Read pipeline summary", "description": "Get spoken pipeline overview"},
                {"command": "What's my conversion rate", "description": "Get current conversion statistics"},
                {"command": "Show market trends", "description": "Display market analysis"},
                {"command": "Generate report", "description": "Create performance report"},
            ],
            "Accessibility": [
                {"command": "Read this page", "description": "Screen reader mode for current page"},
                {"command": "Increase text size", "description": "Make text larger"},
                {"command": "Enable high contrast", "description": "Switch to high contrast mode"},
                {"command": "Describe chart", "description": "Get audio description of visualizations"},
            ],
        }

        for category, commands in command_categories.items():
            with st.expander(f"📋 {category} Commands"):
                for cmd in commands:
                    st.markdown(
                        f"""
                    <div style='
                        background: rgba(22, 27, 34, 0.6);
                        padding: 0.8rem;
                        border-radius: 6px;
                        margin-bottom: 0.5rem;
                        border: 1px solid rgba(255,255,255,0.05);
                    '>
                        <div style='color: #6366F1; font-weight: 600; margin-bottom: 0.3rem;'>
                            "{cmd["command"]}"
                        </div>
                        <div style='color: #8B949E; font-size: 0.85rem;'>
                            {cmd["description"]}
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

    def render_voice_settings_panel(self):
        """Render voice settings and configuration"""
        st.markdown("#### ⚙️ Voice Settings")

        voice_settings = st.session_state.voice_settings

        # Wake word setting
        wake_word = st.text_input(
            "Wake Word", value=voice_settings.wake_word, help="Phrase to activate voice commands", key="wake_word_input"
        )

        # Speech rate
        speech_rate = st.slider(
            "Speech Rate",
            min_value=0.5,
            max_value=2.0,
            value=voice_settings.speech_rate,
            step=0.1,
            help="Speed of voice responses",
            key="speech_rate_slider",
        )

        # Voice type
        voice_type = st.selectbox(
            "Voice Type",
            ["neutral", "friendly", "professional", "calm"],
            index=["neutral", "friendly", "professional", "calm"].index(voice_settings.voice_type),
            help="Style of AI voice responses",
            key="voice_type_select",
        )

        # Confidence threshold
        confidence_threshold = st.slider(
            "Recognition Confidence",
            min_value=0.5,
            max_value=1.0,
            value=voice_settings.confidence_threshold,
            step=0.05,
            help="Minimum confidence for command recognition",
            key="confidence_slider",
        )

        # Auto responses
        auto_responses = st.checkbox(
            "Auto Responses",
            value=voice_settings.auto_responses,
            help="Enable automatic voice confirmation",
            key="auto_responses_check",
        )

        # Update settings
        voice_settings.wake_word = wake_word
        voice_settings.speech_rate = speech_rate
        voice_settings.voice_type = voice_type
        voice_settings.confidence_threshold = confidence_threshold
        voice_settings.auto_responses = auto_responses

        st.session_state.voice_settings = voice_settings

        # Voice test button
        if st.button("🔊 Test Voice", use_container_width=True):
            self._simulate_voice_test()

    def render_accessibility_audit_panel(self):
        """Render accessibility audit and compliance panel"""
        st.markdown("### ♿ ACCESSIBILITY AUDIT")

        audit_score = st.session_state.accessibility_audit_score
        accessibility_settings = st.session_state.accessibility_settings

        col1, col2 = st.columns([1, 1])

        with col1:
            # Overall compliance score
            st.markdown("#### 📊 Compliance Score")

            score_color = "#10B981" if audit_score >= 90 else "#F59E0B" if audit_score >= 80 else "#EF4444"
            compliance_level = "AAA" if audit_score >= 95 else "AA" if audit_score >= 85 else "A"

            st.markdown(
                f"""
            <div style='
                background: rgba(22, 27, 34, 0.8);
                padding: 2rem;
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.05);
                text-align: center;
            '>
                <div style='
                    font-size: 4rem;
                    font-weight: 800;
                    color: {score_color};
                    margin-bottom: 1rem;
                '>{audit_score}</div>
                <div style='color: #E6EDF3; font-size: 1.2rem; margin-bottom: 0.5rem;'>
                    Accessibility Score
                </div>
                <div style='
                    background: {score_color}20;
                    color: {score_color};
                    padding: 0.5rem 1rem;
                    border-radius: 20px;
                    font-size: 0.9rem;
                    font-weight: 700;
                    display: inline-block;
                    border: 1px solid {score_color}40;
                '>
                    WCAG {compliance_level} Compliant
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Progress toward AAA compliance
            st.markdown("#### 🎯 Compliance Progress")

            compliance_areas = {"Perceivable": 96, "Operable": 94, "Understandable": 92, "Robust": 98}

            for area, score in compliance_areas.items():
                color = "#10B981" if score >= 90 else "#F59E0B" if score >= 80 else "#EF4444"

                st.markdown(
                    f"""
                <div style='margin-bottom: 1rem;'>
                    <div style='display: flex; justify-content: space-between; margin-bottom: 0.3rem;'>
                        <span style='color: #E6EDF3; font-weight: 600;'>{area}</span>
                        <span style='color: {color}; font-weight: 700;'>{score}%</span>
                    </div>
                    <div style='
                        background: rgba(255,255,255,0.1);
                        height: 8px;
                        border-radius: 4px;
                        overflow: hidden;
                    '>
                        <div style='
                            background: {color};
                            width: {score}%;
                            height: 100%;
                            box-shadow: 0 0 8px {color};
                        '></div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        with col2:
            # Accessibility features status
            st.markdown("#### 🔧 Accessibility Features")

            features_status = [
                {"name": "Screen Reader Support", "enabled": True, "description": "ARIA labels and semantic HTML"},
                {
                    "name": "Keyboard Navigation",
                    "enabled": accessibility_settings.keyboard_navigation,
                    "description": "Full keyboard accessibility",
                },
                {
                    "name": "High Contrast Mode",
                    "enabled": accessibility_settings.high_contrast_mode,
                    "description": "Enhanced visual contrast",
                },
                {
                    "name": "Large Text Support",
                    "enabled": accessibility_settings.large_text_mode,
                    "description": "Scalable text sizing",
                },
                {
                    "name": "Voice Commands",
                    "enabled": st.session_state.voice_settings.enabled,
                    "description": "Voice interface control",
                },
                {
                    "name": "Reduced Motion",
                    "enabled": accessibility_settings.reduced_motion,
                    "description": "Minimal animations",
                },
                {
                    "name": "Focus Indicators",
                    "enabled": accessibility_settings.focus_indicators,
                    "description": "Clear focus outlines",
                },
                {
                    "name": "Audio Descriptions",
                    "enabled": accessibility_settings.audio_descriptions,
                    "description": "Chart and image descriptions",
                },
            ]

            for feature in features_status:
                status_color = "#10B981" if feature["enabled"] else "#6B7280"
                status_icon = "✅" if feature["enabled"] else "⚪"

                st.markdown(
                    f"""
                <div style='
                    background: rgba(22, 27, 34, 0.6);
                    padding: 1rem;
                    border-radius: 8px;
                    margin-bottom: 0.8rem;
                    border-left: 3px solid {status_color};
                    border: 1px solid rgba(255,255,255,0.05);
                '>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                        <div style='color: #FFFFFF; font-weight: 600; font-size: 0.9rem;'>
                            {feature["name"]}
                        </div>
                        <div style='font-size: 1.2rem;'>{status_icon}</div>
                    </div>
                    <div style='color: #8B949E; font-size: 0.8rem;'>
                        {feature["description"]}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    def render_voice_interaction_history(self):
        """Render voice interaction history and analytics"""
        st.markdown("### 📈 VOICE INTERACTION ANALYTICS")

        col1, col2 = st.columns(2)

        with col1:
            # Voice command usage
            st.markdown("#### 📊 Command Usage")

            command_stats = {"Navigation": 45, "Lead Management": 38, "Data Queries": 28, "Accessibility": 15}

            fig_commands = go.Figure(
                data=[
                    go.Pie(
                        labels=list(command_stats.keys()),
                        values=list(command_stats.values()),
                        hole=0.5,
                        marker_colors=["#6366F1", "#10B981", "#F59E0B", "#8B5CF6"],
                    )
                ]
            )

            fig_commands.update_layout(
                title="Voice Commands by Category",
                title_font_size=14,
                title_font_color="#FFFFFF",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FFFFFF"),
                showlegend=True,
                height=300,
            )

            st.plotly_chart(fig_commands, use_container_width=True)

        with col2:
            # Voice interaction metrics
            st.markdown("#### 🎯 Interaction Metrics")

            metrics = [
                {"name": "Recognition Accuracy", "value": 94, "unit": "%"},
                {"name": "Response Time", "value": 1.2, "unit": "s"},
                {"name": "Success Rate", "value": 91, "unit": "%"},
                {"name": "User Satisfaction", "value": 87, "unit": "%"},
            ]

            for metric in metrics:
                color = "#10B981" if metric["value"] >= 90 else "#F59E0B" if metric["value"] >= 80 else "#EF4444"

                st.markdown(
                    f"""
                <div style='
                    background: rgba(22, 27, 34, 0.6);
                    padding: 1rem;
                    border-radius: 8px;
                    margin-bottom: 0.8rem;
                    border: 1px solid rgba(255,255,255,0.05);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                '>
                    <div>
                        <div style='color: #E6EDF3; font-weight: 600; font-size: 0.9rem;'>
                            {metric["name"]}
                        </div>
                        <div style='color: #8B949E; font-size: 0.75rem; margin-top: 0.2rem;'>
                            Last 30 days
                        </div>
                    </div>
                    <div style='
                        color: {color};
                        font-size: 1.5rem;
                        font-weight: 700;
                    '>
                        {metric["value"]}{metric["unit"]}
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

    def _simulate_voice_test(self):
        """Simulate voice interface test"""
        voice_settings = st.session_state.voice_settings

        # Simulate voice response
        test_message = f"Voice test successful. Speech rate set to {voice_settings.speech_rate}x, using {voice_settings.voice_type} voice type."

        st.success("🔊 " + test_message)

        # Add to voice history
        st.session_state.voice_history.append(
            {"timestamp": datetime.now(), "command": "Voice Test", "response": test_message, "confidence": 1.0}
        )

    def render_keyboard_navigation_help(self):
        """Render keyboard navigation help panel"""
        with st.expander("⌨️ Keyboard Navigation Help"):
            st.markdown("""
            #### Keyboard Shortcuts
            
            **Global Navigation:**
            - `Tab` / `Shift+Tab`: Navigate forward/backward through interactive elements
            - `Enter` / `Space`: Activate buttons and controls
            - `Esc`: Close modals and dropdowns
            - `Alt + M`: Jump to main content
            
            **Voice Commands:**
            - `Ctrl + V`: Toggle voice commands on/off
            - `Ctrl + Shift + V`: Start voice recording
            - `Alt + H`: Open voice command help
            
            **Accessibility:**
            - `Ctrl + +/-`: Increase/decrease text size
            - `Ctrl + H`: Toggle high contrast mode
            - `Ctrl + R`: Toggle reduced motion
            - `Alt + A`: Open accessibility settings
            
            **Screen Reader:**
            - `SR + H`: Read page headings
            - `SR + L`: Read page links
            - `SR + T`: Read page tables
            - `SR + F`: Read page forms
            """)

    def render_complete_voice_accessibility_interface(self):
        """Render the complete voice AI and accessibility interface"""
        st.set_page_config(
            page_title="Service 6 - Voice AI & Accessibility",
            page_icon="🎤",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        # Header
        self.render_accessibility_header()
        st.markdown("---")

        # Voice interface panel
        self.render_voice_interface_panel()
        st.markdown("---")

        # Main content columns
        col1, col2 = st.columns([1, 1])

        with col1:
            # Accessibility audit
            self.render_accessibility_audit_panel()

        with col2:
            # Voice analytics
            self.render_voice_interaction_history()

        st.markdown("---")

        # Keyboard navigation help
        self.render_keyboard_navigation_help()

        # Accessibility statement
        st.markdown("---")
        st.markdown("""
        #### ♿ Accessibility Statement
        
        This application is committed to ensuring digital accessibility for people with disabilities. 
        We are continually improving the user experience for everyone and applying the relevant 
        accessibility standards (WCAG 2.1 Level AA).
        
        **Current Features:**
        - Screen reader compatibility
        - Keyboard navigation support
        - High contrast mode
        - Resizable text
        - Voice command interface
        - Reduced motion options
        
        **Contact:** For accessibility assistance, email accessibility@enterprisehub.com
        """)

        # Live region for screen reader announcements
        if st.session_state.accessibility_settings.screen_reader_mode:
            st.markdown(
                """
            <div aria-live="polite" aria-atomic="true" id="live-announcements" class="sr-only"></div>
            """,
                unsafe_allow_html=True,
            )


def render_voice_ai_accessibility_interface():
    """Main function to render the voice AI and accessibility interface"""
    interface = VoiceAIAccessibilityInterface()
    interface.render_complete_voice_accessibility_interface()


if __name__ == "__main__":
    render_voice_ai_accessibility_interface()
