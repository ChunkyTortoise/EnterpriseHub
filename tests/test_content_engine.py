"""
Tests for Content Engine module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os


# Test constants
TEMPLATES = [
    "Professional Insight",
    "Thought Leadership",
    "Case Study",
    "How-To Guide",
    "Industry Trend",
    "Personal Story"
]

TONES = ["Professional", "Casual", "Inspirational", "Analytical", "Storytelling"]


class TestContentEngineTemplates:
    """Test template and tone configurations."""

    def test_all_templates_exist(self):
        """Verify all 6 templates are defined."""
        from modules.content_engine import TEMPLATES as MODULE_TEMPLATES
        assert len(MODULE_TEMPLATES) == 6
        for template in TEMPLATES:
            assert template in MODULE_TEMPLATES

    def test_templates_have_required_fields(self):
        """Verify each template has description, prompt_prefix, and style."""
        from modules.content_engine import TEMPLATES as MODULE_TEMPLATES
        for template_name, template_info in MODULE_TEMPLATES.items():
            assert "description" in template_info
            assert "prompt_prefix" in template_info
            assert "style" in template_info
            assert len(template_info["description"]) > 0
            assert len(template_info["prompt_prefix"]) > 0
            assert len(template_info["style"]) > 0

    def test_all_tones_exist(self):
        """Verify all 5 tones are defined."""
        from modules.content_engine import TONES as MODULE_TONES
        assert len(MODULE_TONES) == 5
        for tone in TONES:
            assert tone in MODULE_TONES

    def test_tones_have_instructions(self):
        """Verify each tone has instruction text."""
        from modules.content_engine import TONES as MODULE_TONES
        for tone, instruction in MODULE_TONES.items():
            assert isinstance(instruction, str)
            assert len(instruction) > 0


class TestContentEngineAPIKeyHandling:
    """Test API key retrieval and validation."""

    def test_get_api_key_from_env(self):
        """Test API key retrieval from environment variable."""
        from modules.content_engine import _get_api_key

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test-key"}):
            api_key = _get_api_key()
            assert api_key == "sk-ant-test-key"

    def test_get_api_key_from_session_state(self):
        """Test API key retrieval from Streamlit session state."""
        from modules.content_engine import _get_api_key

        # Mock Streamlit session state
        with patch('streamlit.session_state', {"anthropic_api_key": "sk-ant-session-key"}):
            with patch.dict(os.environ, {}, clear=True):
                api_key = _get_api_key()
                assert api_key == "sk-ant-session-key"

    def test_get_api_key_returns_none_when_missing(self):
        """Test API key returns None when not found."""
        from modules.content_engine import _get_api_key

        with patch.dict(os.environ, {}, clear=True):
            with patch('streamlit.session_state', {}):
                api_key = _get_api_key()
                assert api_key is None


class TestContentEngineGeneration:
    """Test content generation logic."""

    @patch('modules.content_engine.Anthropic')
    def test_generate_post_success(self, mock_anthropic):
        """Test successful post generation."""
        from modules.content_engine import _generate_post

        # Mock Anthropic API response
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "This is a generated LinkedIn post about AI."
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        # Call function
        result = _generate_post(
            api_key="sk-ant-test-key",
            topic="AI trends",
            template="Professional Insight",
            tone="Professional",
            keywords="AI, automation",
            target_audience="CTOs"
        )

        # Assertions
        assert result == "This is a generated LinkedIn post about AI."
        mock_anthropic.assert_called_once_with(api_key="sk-ant-test-key")
        mock_client.messages.create.assert_called_once()

    @patch('modules.content_engine.Anthropic')
    def test_generate_post_api_error(self, mock_anthropic):
        """Test handling of API errors."""
        from modules.content_engine import _generate_post

        # Mock API error
        mock_client = MagicMock()
        from anthropic import APIError
        mock_client.messages.create.side_effect = APIError("Rate limit exceeded")
        mock_anthropic.return_value = mock_client

        # Call function (should handle error gracefully)
        with patch('streamlit.error'):
            result = _generate_post(
                api_key="sk-ant-test-key",
                topic="AI trends",
                template="Professional Insight",
                tone="Professional"
            )

        assert result is None

    @patch('modules.content_engine.Anthropic')
    def test_generate_post_with_optional_params(self, mock_anthropic):
        """Test generation with optional keywords and target audience."""
        from modules.content_engine import _generate_post

        # Mock successful response
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Generated post"
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        # Call with optional params
        result = _generate_post(
            api_key="sk-ant-test-key",
            topic="AI trends",
            template="Thought Leadership",
            tone="Inspirational",
            keywords="innovation, future",
            target_audience="Tech leaders"
        )

        assert result == "Generated post"

        # Verify the prompt includes keywords and audience
        call_args = mock_client.messages.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]
        assert "innovation, future" in prompt
        assert "Tech leaders" in prompt


class TestContentEnginePromptConstruction:
    """Test prompt engineering and template integration."""

    @patch('modules.content_engine.Anthropic')
    def test_prompt_includes_template_prefix(self, mock_anthropic):
        """Verify prompt uses template-specific prefix."""
        from modules.content_engine import _generate_post, TEMPLATES

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Test"
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        _generate_post(
            api_key="sk-ant-test-key",
            topic="productivity",
            template="Case Study",
            tone="Professional"
        )

        # Get the prompt that was sent
        call_args = mock_client.messages.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        # Verify template prefix is in prompt
        template_prefix = TEMPLATES["Case Study"]["prompt_prefix"]
        assert template_prefix in prompt

    @patch('modules.content_engine.Anthropic')
    def test_prompt_includes_tone_instructions(self, mock_anthropic):
        """Verify prompt includes tone-specific instructions."""
        from modules.content_engine import _generate_post, TONES

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Test"
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        _generate_post(
            api_key="sk-ant-test-key",
            topic="leadership",
            template="Personal Story",
            tone="Inspirational"
        )

        # Get the prompt
        call_args = mock_client.messages.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        # Verify tone instruction is in prompt
        tone_instruction = TONES["Inspirational"]
        assert tone_instruction in prompt


class TestContentEngineImportSafety:
    """Test graceful handling of missing dependencies."""

    def test_anthropic_available_flag(self):
        """Verify ANTHROPIC_AVAILABLE flag is set correctly."""
        from modules.content_engine import ANTHROPIC_AVAILABLE
        # Should be True since we have it in requirements.txt
        assert isinstance(ANTHROPIC_AVAILABLE, bool)


# Integration test (requires actual API key - skip in CI)
@pytest.mark.skip(reason="Requires valid Anthropic API key")
class TestContentEngineIntegration:
    """Integration tests with real Anthropic API (manual testing only)."""

    def test_real_api_call(self):
        """Test actual API call (manual test with real key)."""
        from modules.content_engine import _generate_post

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            pytest.skip("No API key available")

        result = _generate_post(
            api_key=api_key,
            topic="test topic",
            template="Professional Insight",
            tone="Professional"
        )

        assert result is not None
        assert len(result) > 0
        assert isinstance(result, str)
