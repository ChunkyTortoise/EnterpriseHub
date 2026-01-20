
import pytest
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime

# Mock streamlit before importing the component
mock_st = MagicMock()
sys.modules['streamlit'] = mock_st

# Import the component to test
from ghl_real_estate_ai.streamlit_demo.components.voice_ai_interface import (
    VoiceAIInterface,
    render_voice_ai_interface,
    VoiceInteractionType
)

class SessionState(dict):
    """Mock session state that supports attribute access."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

@pytest.mark.asyncio
class TestVoiceAIInterface:

    @pytest.fixture(autouse=True)
    def cleanup_test_data(self):
        """Override global cleanup fixture to avoid async issues."""
        yield

    @pytest.fixture
    def voice_interface(self):
        with patch('ghl_real_estate_ai.streamlit_demo.components.voice_ai_interface.get_cached_voice_service') as mock_get_service:
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service
            interface = VoiceAIInterface()
            return interface

    def setup_method(self):
        # Reset mock_st and session_state for each test
        mock_st.reset_mock()
        mock_st.session_state = SessionState()
        
        # Configure st.columns to return list of mocks
        def columns_side_effect(spec):
            if isinstance(spec, int):
                count = spec
            else:
                count = len(spec)
            return [MagicMock() for _ in range(count)]
        
        mock_st.columns.side_effect = columns_side_effect
        
        # Default button to not clicked
        mock_st.button.return_value = False

    async def test_initialization(self, voice_interface):
        """Test that the interface initializes correctly."""
        assert voice_interface.voice_service is not None
        assert 'voice_session_active' in mock_st.session_state
        assert mock_st.session_state['voice_session_active'] is False
        assert mock_st.session_state['voice_transcript'] == []
        assert mock_st.session_state['ai_responses'] == []
        assert mock_st.session_state['voice_analytics'] == {}

    async def test_render_voice_controls(self, voice_interface):
        """Test rendering of voice controls."""
        # Setup session state
        mock_st.session_state['voice_session_active'] = False
        
        # Mock selectbox return value
        mock_st.selectbox.return_value = "Lead Qualification"
        
        result = voice_interface.render_voice_controls("test_agent")
        
        # Verify controls were rendered
        mock_st.markdown.assert_any_call("### 🎤 **Jorge's Voice AI Assistant**")
        mock_st.selectbox.assert_called()
        mock_st.button.assert_called()
        
        assert result['session_active'] is False

    async def test_start_voice_session(self, voice_interface):
        """Test starting a voice session."""
        mock_st.session_state['voice_session_active'] = False
        
        voice_interface._start_voice_session(
            "test_agent",
            VoiceInteractionType.LEAD_QUALIFICATION,
            "LEAD_123"
        )
        
        assert mock_st.session_state['voice_session_active'] is True
        assert mock_st.session_state['current_interaction_id'] is not None
        assert "voice_test_agent_" in mock_st.session_state['current_interaction_id']
        mock_st.success.assert_called()

    async def test_end_voice_session(self, voice_interface):
        """Test ending a voice session."""
        mock_st.session_state['voice_session_active'] = True
        mock_st.session_state['current_interaction_id'] = "test_interaction_id"
        mock_st.session_state['voice_transcript'] = [{"content": "hi"}]
        
        voice_interface._end_voice_session()
        
        assert mock_st.session_state['voice_session_active'] is False
        assert mock_st.session_state['current_interaction_id'] is None
        mock_st.success.assert_called_with("✅ Voice session ended successfully!")

    async def test_process_simulated_input(self, voice_interface):
        """Test processing of simulated voice input."""
        mock_st.session_state['voice_transcript'] = []
        mock_st.session_state['ai_responses'] = []
        
        input_text = "I want to buy a house"
        voice_interface._process_simulated_input(input_text)
        
        # Check transcript updated
        transcript = mock_st.session_state['voice_transcript']
        assert len(transcript) == 2  # Client input + AI response
        assert transcript[0]['speaker'] == 'Client'
        assert transcript[0]['content'] == input_text
        assert transcript[1]['speaker'] == 'Jorge AI'
        
        # Check AI responses updated
        assert len(mock_st.session_state['ai_responses']) == 1

    async def test_render_voice_analytics(self, voice_interface):
        """Test rendering of analytics dashboard."""
        analytics = voice_interface.render_voice_analytics()
        
        assert "total_interactions" in analytics
        assert "sentiment_distribution" in analytics
        mock_st.metric.assert_called()
        mock_st.plotly_chart.assert_called()

    async def test_render_component_function(self):
        """Test the main component render function."""
        with patch('ghl_real_estate_ai.streamlit_demo.components.voice_ai_interface.VoiceAIInterface') as MockInterface:
            mock_instance = MockInterface.return_value
            mock_instance.render_voice_controls.return_value = {"session_active": False}
            mock_instance.render_voice_analytics.return_value = {"some": "data"}
            
            result = render_voice_ai_interface("test_agent")
            
            assert "session_active" in result
            assert "analytics" in result
            mock_instance.render_voice_controls.assert_called_with("test_agent")
            mock_instance.render_live_interaction.assert_called()
            mock_instance.render_voice_analytics.assert_called()
