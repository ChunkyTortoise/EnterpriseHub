"""
Tests for Content Engine module.

Comprehensive test suite covering:
- Template and tone configurations
- API key handling
- Content generation with various inputs
- Error handling (rate limits, timeouts, malformed responses)
- Edge cases and validation
- Retry logic
"""

import pytest
from unittest.mock import patch, MagicMock
import os


# Test constants
TEMPLATES = [
    "Professional Insight",
    "Thought Leadership",
    "Case Study",
    "How-To Guide",
    "Industry Trend",
    "Personal Story",
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
        mock_state = MagicMock()
        mock_state.anthropic_api_key = "sk-ant-session-key"
        # Support 'in' check
        mock_state.__contains__.side_effect = lambda x: x == "anthropic_api_key"

        with patch("streamlit.session_state", mock_state):
            with patch.dict(os.environ, {}, clear=True):
                api_key = _get_api_key()
                assert api_key == "sk-ant-session-key"

    def test_get_api_key_returns_none_when_missing(self):
        """Test API key returns None when not found."""
        from modules.content_engine import _get_api_key

        with patch.dict(os.environ, {}, clear=True):
            with patch("streamlit.session_state", {}):
                api_key = _get_api_key()
                assert api_key is None


class TestContentEngineGeneration:
    """Test content generation logic."""

    @patch("modules.content_engine.Anthropic")
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
            target_audience="CTOs",
        )

        # Assertions
        assert result == "This is a generated LinkedIn post about AI."
        mock_anthropic.assert_called_once_with(api_key="sk-ant-test-key")
        mock_client.messages.create.assert_called_once()

    @patch("modules.content_engine.Anthropic")
    def test_generate_post_api_error(self, mock_anthropic):
        """Test handling of API errors."""
        from modules.content_engine import _generate_post

        # Mock API error
        mock_client = MagicMock()
        from anthropic import APIError

        mock_client.messages.create.side_effect = APIError(
            "Rate limit exceeded", request=MagicMock(), body={}
        )
        mock_anthropic.return_value = mock_client

        # Call function (should handle error gracefully)
        with patch("streamlit.error"):
            result = _generate_post(
                api_key="sk-ant-test-key",
                topic="AI trends",
                template="Professional Insight",
                tone="Professional",
            )

        assert result is None

    @patch("modules.content_engine.Anthropic")
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
            target_audience="Tech leaders",
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

    @patch("modules.content_engine.Anthropic")
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
            tone="Professional",
        )

        # Get the prompt that was sent
        call_args = mock_client.messages.create.call_args
        messages = call_args[1]["messages"]
        prompt = messages[0]["content"]

        # Verify template prefix is in prompt
        template_prefix = TEMPLATES["Case Study"]["prompt_prefix"]
        assert template_prefix in prompt

    @patch("modules.content_engine.Anthropic")
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
            tone="Inspirational",
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


class TestContentEngineEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch("modules.content_engine.Anthropic")
    def test_generate_post_with_empty_keywords(self, mock_anthropic):
        """Test generation with empty keywords string."""
        from modules.content_engine import _generate_post

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Generated post"
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        result = _generate_post(
            api_key="sk-ant-test-key",
            topic="AI trends",
            template="Professional Insight",
            tone="Professional",
            keywords="",
            target_audience="",
        )

        assert result == "Generated post"

    @patch("modules.content_engine.Anthropic")
    def test_generate_post_with_whitespace_only_keywords(self, mock_anthropic):
        """Test generation with whitespace-only keywords."""
        from modules.content_engine import _generate_post

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Generated post"
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        result = _generate_post(
            api_key="sk-ant-test-key",
            topic="AI trends",
            template="Professional Insight",
            tone="Professional",
            keywords="   ",
            target_audience="   ",
        )

        assert result == "Generated post"

    @patch("modules.content_engine.Anthropic")
    def test_generate_post_with_very_long_topic(self, mock_anthropic):
        """Test generation with extremely long topic."""
        from modules.content_engine import _generate_post

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Generated post"
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        long_topic = "A" * 5000  # Very long topic
        result = _generate_post(
            api_key="sk-ant-test-key",
            topic=long_topic,
            template="Professional Insight",
            tone="Professional",
        )

        assert result == "Generated post"

    @patch("modules.content_engine.Anthropic")
    def test_generate_post_with_special_characters(self, mock_anthropic):
        """Test generation with special characters in topic."""
        from modules.content_engine import _generate_post

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Generated post"
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        result = _generate_post(
            api_key="sk-ant-test-key",
            topic="AI & ML: The Future! #Innovation @2025",
            template="Professional Insight",
            tone="Professional",
        )

        assert result == "Generated post"

    def test_validate_template_and_tone_invalid_template(self):
        """Test validation with invalid template."""
        from modules.content_engine import _validate_template_and_tone

        with pytest.raises(ValueError, match="Invalid template"):
            _validate_template_and_tone("NonexistentTemplate", "Professional")

    def test_validate_template_and_tone_invalid_tone(self):
        """Test validation with invalid tone."""
        from modules.content_engine import _validate_template_and_tone

        with pytest.raises(ValueError, match="Invalid tone"):
            _validate_template_and_tone("Professional Insight", "NonexistentTone")

    def test_validate_template_and_tone_both_invalid(self):
        """Test validation with both invalid template and tone."""
        from modules.content_engine import _validate_template_and_tone

        with pytest.raises(ValueError):
            _validate_template_and_tone("InvalidTemplate", "InvalidTone")

    @patch("modules.content_engine.Anthropic")
    def test_generate_post_with_empty_api_key(self, mock_anthropic):
        """Test generation with empty API key."""
        from modules.content_engine import _generate_post

        with patch("streamlit.error"):
            result = _generate_post(
                api_key="", topic="AI trends", template="Professional Insight", tone="Professional"
            )

        assert result is None

    @patch("modules.content_engine.Anthropic")
    def test_generate_post_with_whitespace_api_key(self, mock_anthropic):
        """Test generation with whitespace-only API key."""
        from modules.content_engine import _generate_post

        with patch("streamlit.error"):
            result = _generate_post(
                api_key="   ",
                topic="AI trends",
                template="Professional Insight",
                tone="Professional",
            )

        assert result is None

    @patch("modules.content_engine.Anthropic")
    def test_generate_post_with_empty_topic(self, mock_anthropic):
        """Test generation with empty topic."""
        from modules.content_engine import _generate_post

        with patch("streamlit.error"):
            result = _generate_post(
                api_key="sk-ant-test-key",
                topic="",
                template="Professional Insight",
                tone="Professional",
            )

        assert result is None

    def test_build_prompt_structure(self):
        """Test that prompt includes all required elements."""
        from modules.content_engine import _build_prompt

        prompt = _build_prompt(
            topic="AI automation",
            template="Professional Insight",
            tone="Professional",
            keywords="AI, automation, productivity",
            target_audience="CTOs",
        )

        assert "AI automation" in prompt
        assert "Target Audience: CTOs" in prompt
        assert "AI, automation, productivity" in prompt
        assert "150-250 words" in prompt
        assert "3-5 relevant hashtags" in prompt


class TestContentEngineRateLimiting:
    """Test rate limiting scenarios and retry logic."""

    @patch("modules.content_engine.Anthropic")
    @patch("modules.content_engine.time.sleep")  # Mock sleep to speed up tests
    def test_retry_on_rate_limit_success_after_retry(self, mock_sleep, mock_anthropic):
        """Test successful retry after rate limit error."""
        from modules.content_engine import _generate_post
        from anthropic import RateLimitError

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Generated post"
        mock_message.content = [mock_content]

        # First call raises RateLimitError, second succeeds
        mock_client.messages.create.side_effect = [
            RateLimitError("Rate limit exceeded", response=MagicMock(), body={}),
            mock_message,
        ]
        mock_anthropic.return_value = mock_client

        with patch("streamlit.error"):
            result = _generate_post(
                api_key="sk-ant-test-key",
                topic="AI trends",
                template="Professional Insight",
                tone="Professional",
            )

        assert result == "Generated post"
        assert mock_client.messages.create.call_count == 2
        mock_sleep.assert_called_once()  # Should sleep once before retry

    @patch("modules.content_engine.Anthropic")
    @patch("modules.content_engine.time.sleep")
    def test_retry_exhausted_on_rate_limit(self, mock_sleep, mock_anthropic):
        """Test when all retries are exhausted due to rate limiting."""
        from modules.content_engine import _generate_post
        from anthropic import RateLimitError

        mock_client = MagicMock()
        # Always raise RateLimitError
        mock_client.messages.create.side_effect = RateLimitError(
            "Rate limit exceeded", response=MagicMock(), body={}
        )
        mock_anthropic.return_value = mock_client

        with patch("streamlit.error"):
            with pytest.raises(RateLimitError):
                _generate_post(
                    api_key="sk-ant-test-key",
                    topic="AI trends",
                    template="Professional Insight",
                    tone="Professional",
                )

        # Should attempt 3 times (MAX_RETRY_ATTEMPTS)
        assert mock_client.messages.create.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep between attempts

    @patch("modules.content_engine.Anthropic")
    @patch("modules.content_engine.time.sleep")
    def test_exponential_backoff_delays(self, mock_sleep, mock_anthropic):
        """Test that retry delays follow exponential backoff."""
        from modules.content_engine import _generate_post
        from anthropic import RateLimitError

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = RateLimitError(
            "Rate limit exceeded", response=MagicMock(), body={}
        )
        mock_anthropic.return_value = mock_client

        with patch("streamlit.error"):
            with pytest.raises(RateLimitError):
                _generate_post(
                    api_key="sk-ant-test-key",
                    topic="AI trends",
                    template="Professional Insight",
                    tone="Professional",
                )

        # Check that sleep was called with increasing delays
        # First delay: 1.0s, Second delay: 2.0s (1.0 * 2.0)
        assert mock_sleep.call_count == 2
        calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert calls[0] == 1.0
        assert calls[1] == 2.0


class TestContentEngineMalformedResponses:
    """Test handling of malformed API responses."""

    @patch("modules.content_engine.Anthropic")
    def test_api_returns_empty_content_list(self, mock_anthropic):
        """Test when API returns message with empty content list."""
        from modules.content_engine import _call_claude_api

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = []  # Empty content
        mock_client.messages.create.return_value = mock_message

        with patch("streamlit.error"):
            with pytest.raises(ValueError, match="empty response"):
                _call_claude_api(mock_client, "test prompt")

    @patch("modules.content_engine.Anthropic")
    def test_api_returns_none_content(self, mock_anthropic):
        """Test when API returns None as content."""
        from modules.content_engine import _call_claude_api

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.content = None
        mock_client.messages.create.return_value = mock_message

        with patch("streamlit.error"):
            with pytest.raises(ValueError, match="empty response"):
                _call_claude_api(mock_client, "test prompt")

    @patch("modules.content_engine.Anthropic")
    def test_api_returns_malformed_content_object(self, mock_anthropic):
        """Test when API returns content without text attribute."""
        from modules.content_engine import _call_claude_api

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content = MagicMock(spec=[])  # No 'text' attribute
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message

        with patch("streamlit.error"):
            with pytest.raises(ValueError, match="malformed response"):
                _call_claude_api(mock_client, "test prompt")

    @patch("modules.content_engine.Anthropic")
    def test_api_returns_empty_text(self, mock_anthropic):
        """Test when API returns empty text string."""
        from modules.content_engine import _generate_post

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = ""  # Empty text
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        with patch("streamlit.error"):
            result = _generate_post(
                api_key="sk-ant-test-key",
                topic="AI trends",
                template="Professional Insight",
                tone="Professional",
            )

        assert result is None

    @patch("modules.content_engine.Anthropic")
    def test_api_returns_whitespace_only_text(self, mock_anthropic):
        """Test when API returns whitespace-only text."""
        from modules.content_engine import _generate_post

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "   \n\t  "  # Whitespace only
        mock_message.content = [mock_content]
        mock_client.messages.create.return_value = mock_message
        mock_anthropic.return_value = mock_client

        with patch("streamlit.error"):
            result = _generate_post(
                api_key="sk-ant-test-key",
                topic="AI trends",
                template="Professional Insight",
                tone="Professional",
            )

        assert result is None


class TestContentEngineNetworkFailures:
    """Test handling of network failures and timeouts."""

    @patch("modules.content_engine.Anthropic")
    @patch("modules.content_engine.time.sleep")
    def test_connection_error_with_retry(self, mock_sleep, mock_anthropic):
        """Test retry on connection error."""
        from modules.content_engine import _generate_post
        from anthropic import APIConnectionError

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Generated post"
        mock_message.content = [mock_content]

        # First call raises connection error, second succeeds
        mock_client.messages.create.side_effect = [
            APIConnectionError(message="Connection failed", request=MagicMock()),
            mock_message,
        ]
        mock_anthropic.return_value = mock_client

        with patch("streamlit.error"):
            result = _generate_post(
                api_key="sk-ant-test-key",
                topic="AI trends",
                template="Professional Insight",
                tone="Professional",
            )

        assert result == "Generated post"
        assert mock_client.messages.create.call_count == 2

    @patch("modules.content_engine.Anthropic")
    @patch("modules.content_engine.time.sleep")
    def test_timeout_error_with_retry(self, mock_sleep, mock_anthropic):
        """Test retry on timeout error."""
        from modules.content_engine import _generate_post
        from anthropic import APITimeoutError

        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Generated post"
        mock_message.content = [mock_content]

        # First call times out, second succeeds
        mock_client.messages.create.side_effect = [
            APITimeoutError(request=MagicMock()),
            mock_message,
        ]
        mock_anthropic.return_value = mock_client

        with patch("streamlit.error"):
            result = _generate_post(
                api_key="sk-ant-test-key",
                topic="AI trends",
                template="Professional Insight",
                tone="Professional",
            )

        assert result == "Generated post"
        assert mock_client.messages.create.call_count == 2

    @patch("modules.content_engine.Anthropic")
    @patch("modules.content_engine.time.sleep")
    def test_connection_error_exhausts_retries(self, mock_sleep, mock_anthropic):
        """Test when connection errors exhaust all retries."""
        from modules.content_engine import _generate_post
        from anthropic import APIConnectionError

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = APIConnectionError(
            message="Connection failed", request=MagicMock()
        )
        mock_anthropic.return_value = mock_client

        with patch("streamlit.error"):
            with pytest.raises(APIConnectionError):
                _generate_post(
                    api_key="sk-ant-test-key",
                    topic="AI trends",
                    template="Professional Insight",
                    tone="Professional",
                )

        assert mock_client.messages.create.call_count == 3

    @patch("modules.content_engine.Anthropic")
    def test_authentication_error_no_retry(self, mock_anthropic):
        """Test that authentication errors are not retried."""
        from modules.content_engine import _generate_post
        from anthropic import APIError

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = APIError(
            "Authentication failed", request=MagicMock(), body={}
        )
        mock_anthropic.return_value = mock_client

        with patch("streamlit.error"):
            result = _generate_post(
                api_key="sk-ant-invalid-key",
                topic="AI trends",
                template="Professional Insight",
                tone="Professional",
            )

        # Should only try once (no retry on auth errors)
        assert mock_client.messages.create.call_count == 1
        assert result is None


class TestContentEngineAPIKeyValidation:
    """Test API key validation and format checking."""

    def test_get_api_key_with_invalid_format_from_env(self):
        """Test API key with invalid format from environment."""
        from modules.content_engine import _get_api_key

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "invalid-key-format"}):
            api_key = _get_api_key()
            # Should still return the key even if format is invalid
            assert api_key == "invalid-key-format"

    def test_get_api_key_with_valid_format(self):
        """Test API key with valid format."""
        from modules.content_engine import _get_api_key

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-valid-key"}):
            api_key = _get_api_key()
            assert api_key == "sk-ant-valid-key"


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
            tone="Professional",
        )

        assert result is not None
        assert len(result) > 0
        assert isinstance(result, str)


class TestRenderFunction:
    """Tests for the main render() function."""

    @patch("modules.content_engine.st")
    @patch("modules.content_engine.ui")
    @patch("modules.content_engine.ANTHROPIC_AVAILABLE", True)
    @patch("modules.content_engine._get_api_key")
    @patch("modules.content_engine._render_four_panel_interface")
    def test_render_with_api_key(self, mock_interface, mock_get_key, mock_ui, mock_st):
        """Test render() with valid API key."""
        from modules.content_engine import render

        # Fix columns unpacking
        mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        mock_st.checkbox.return_value = False # Disable demo mode
        mock_get_key.return_value = "sk-ant-test-key"

        render()

        mock_ui.section_header.assert_called_once()
        mock_get_key.assert_called_once()
        mock_interface.assert_called_once_with("sk-ant-test-key")

    @patch("modules.content_engine.st")
    @patch("modules.content_engine.ui")
    @patch("modules.content_engine.ANTHROPIC_AVAILABLE", True)
    @patch("modules.content_engine._get_api_key")
    @patch("modules.content_engine._render_api_key_setup")
    def test_render_without_api_key(self, mock_setup, mock_get_key, mock_ui, mock_st):
        """Test render() without API key shows setup."""
        from modules.content_engine import render

        # Fix columns unpacking
        mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        mock_st.checkbox.return_value = False  # Disable demo mode
        mock_get_key.return_value = None

        render()

        mock_setup.assert_called_once()

    @patch("modules.content_engine.st")
    @patch("modules.content_engine.ui")
    @patch("modules.content_engine.ANTHROPIC_AVAILABLE", False)
    def test_render_without_anthropic_package(self, mock_ui, mock_st):
        """Test render() when Anthropic package not installed."""
        from modules.content_engine import render

        # Fix columns unpacking
        mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        mock_st.checkbox.return_value = False  # Disable demo mode

        render()

        mock_st.error.assert_called_once()
        error_msg = str(mock_st.error.call_args[0][0])
        assert "not installed" in error_msg.lower()

    @patch("modules.content_engine.st")
    @patch("modules.content_engine.ui")
    @patch("modules.content_engine.ANTHROPIC_AVAILABLE", True)
    @patch("modules.content_engine._get_api_key")
    @patch("modules.content_engine.logger")
    def test_render_handles_exception(self, mock_logger, mock_get_key, mock_ui, mock_st):
        """Test render() handles exceptions gracefully."""
        from modules.content_engine import render

        # Fix columns unpacking
        mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        mock_st.checkbox.return_value = False  # Disable demo mode
        mock_get_key.side_effect = Exception("Test error")

        render()

        mock_logger.error.assert_called_once()
        mock_st.error.assert_called()


class TestRenderAPIKeySetup:
    """Tests for _render_api_key_setup function."""

    @patch("modules.content_engine.st")
    @patch("modules.content_engine.logger")
    def test_api_key_setup_shows_warning(self, mock_logger, mock_st):
        """Test that API key setup shows warning message."""
        from modules.content_engine import _render_api_key_setup

        mock_form = MagicMock()
        mock_st.form.return_value.__enter__ = MagicMock(return_value=mock_form)
        mock_st.form.return_value.__exit__ = MagicMock(return_value=None)
        mock_form.form_submit_button.return_value = False

        _render_api_key_setup()

        mock_st.warning.assert_called_once()

    @patch("modules.content_engine.st")
    @patch("modules.content_engine.logger")
    def test_api_key_setup_shows_instructions(self, mock_logger, mock_st):
        """Test that API key setup shows instructions."""
        from modules.content_engine import _render_api_key_setup

        mock_form = MagicMock()
        mock_st.form.return_value.__enter__ = MagicMock(return_value=mock_form)
        mock_st.form.return_value.__exit__ = MagicMock(return_value=None)
        mock_form.form_submit_button.return_value = False

        _render_api_key_setup()

        mock_st.markdown.assert_called()

    @patch("modules.content_engine.st")
    @patch("modules.content_engine.logger")
    def test_api_key_setup_validates_format(self, mock_logger, mock_st):
        """Test that API key setup validates key format."""
        from modules.content_engine import _render_api_key_setup

        mock_st.session_state = MagicMock()
        mock_st.text_input.return_value = "invalid-key"
        mock_form = MagicMock()
        mock_st.form.return_value.__enter__ = MagicMock(return_value=mock_form)
        mock_st.form.return_value.__exit__ = MagicMock(return_value=None)
        mock_st.form_submit_button.return_value = True

        _render_api_key_setup()

        mock_st.error.assert_called()
        error_msg = str(mock_st.error.call_args[0][0])
        assert "sk-ant-" in error_msg

    @patch("modules.content_engine.st")
    @patch("modules.content_engine.logger")
    def test_api_key_setup_saves_valid_key(self, mock_logger, mock_st):
        """Test that valid API key is saved to session state."""
        from modules.content_engine import _render_api_key_setup

        mock_st.session_state = MagicMock()
        mock_st.text_input.return_value = "sk-ant-valid-key"
        mock_form = MagicMock()
        mock_st.form.return_value.__enter__ = MagicMock(return_value=mock_form)
        mock_st.form.return_value.__exit__ = MagicMock(return_value=None)
        mock_st.form_submit_button.return_value = True

        try:
            _render_api_key_setup()
        except:
            pass  # rerun will raise exception

        assert mock_st.session_state.anthropic_api_key == "sk-ant-valid-key"


class TestRenderFourPanelInterface:
    """Tests for _render_four_panel_interface function."""

    @patch("modules.content_engine.st")
    @patch("modules.content_engine.logger")
    def test_four_panel_initializes_session_state(self, mock_logger, mock_st):
        """Test that four panel interface initializes session state."""
        from modules.content_engine import _render_four_panel_interface

        mock_st.session_state = MagicMock()
        # Mock 'in' operator for session_state
        mock_st.session_state.__contains__.return_value = False

        # Mock st.columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        mock_st.selectbox.side_effect = ["Professional", "LinkedIn"]  # Tone, then Platform
        mock_st.text_input.return_value = "Test topic"
        mock_st.text_area.return_value = "Test keywords"
        mock_st.button.return_value = False

        _render_four_panel_interface("sk-ant-test-key")

        assert mock_st.session_state.generated_post is None

    @patch("modules.content_engine.st")
    @patch("modules.content_engine._generate_post")
    def test_four_panel_generates_post_on_button_click(self, mock_generate, mock_st):
        """Test that clicking generate button triggers post generation."""
        from modules.content_engine import _render_four_panel_interface

        mock_st.session_state = MagicMock()
        mock_st.session_state.generated_post = None
        mock_st.session_state.ab_test_variants = None
        mock_st.session_state.content_history = []
        mock_st.session_state.analytics_enabled = False
        # Mock st.columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        mock_st.selectbox.side_effect = ["Professional", "LinkedIn"]
        mock_st.radio.return_value = "Single Post"
        mock_st.text_input.return_value = "Test topic"
        mock_st.text_area.return_value = "Test keywords"

        # Mock st.button to return True only for generate button
        def button_side_effect(label, **kwargs):
            return "Generate" in label or "✨" in label

        mock_st.button.side_effect = button_side_effect

        mock_st.rerun.side_effect = Exception("st.rerun called")
        mock_generate.return_value = "Generated content"

        _render_four_panel_interface("sk-ant-test-key")

        mock_generate.assert_called_once()

        @patch("modules.content_engine.st")
        @patch("modules.content_engine.logger")
        def test_four_panel_shows_generated_content(self, mock_logger, mock_st):
            """Test that generated content is displayed."""
            from modules.content_engine import _render_four_panel_interface

            # Create a mock session state that supports both attribute access and 'in' operator
            class MockSessionState(dict):
                def __getattr__(self, key):
                    try:
                        return self[key]
                    except KeyError:
                        # Return a MagicMock for undefined attributes to mimic Streamlit behavior
                        # but don't store it yet to keep __contains__ accurate
                        return MagicMock()

                def __setattr__(self, key, value):
                    self[key] = value

            mock_state = MockSessionState()
            mock_state.generated_post = "Test generated content"
            mock_state.ab_test_variants = None
            mock_state.content_history = []
            mock_state.analytics_enabled = False
            mock_st.session_state = mock_state

            # Mock st.columns to return correct number of columns
            mock_st.columns.side_effect = lambda n: [
                MagicMock() for _ in range(n if isinstance(n, int) else len(n))
            ]

            mock_st.selectbox.side_effect = ["Professional", "LinkedIn"]
            mock_st.radio.return_value = "Single Post"

            # All buttons False for this test
            mock_st.button.return_value = False

            _render_four_panel_interface("sk-ant-test-key")

            # Check if text_area was called with the generated content
            found = False
            for call in mock_st.text_area.call_args_list:
                args, kwargs = call
                if "Test generated content" in str(args) or "Test generated content" in str(kwargs):
                    found = True
                    break

            assert found
