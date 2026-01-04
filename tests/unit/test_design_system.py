"""
Unit tests for the Design System module.
"""

from unittest.mock import MagicMock, patch
import pytest
import streamlit as st

class TestDesignSystemModule:
    """Test suite for the design system module."""

    @patch("streamlit.title")
    @patch("streamlit.markdown")
    @patch("streamlit.tabs")
    @patch("streamlit.sidebar")
    @patch("streamlit.radio")
    def test_render_function_exists(self, mock_radio, mock_sidebar, mock_tabs, mock_markdown, mock_title):
        """Verify render() function exists and is callable."""
        from modules.design_system import render

        # Mock radio to return "Light"
        mock_radio.return_value = "Light"
        
        # Mock sidebar context manager
        mock_sidebar.__enter__ = MagicMock(return_value=mock_sidebar)
        mock_sidebar.__exit__ = MagicMock(return_value=None)

        # Mock tabs to return a list of mock contexts
        mock_tab_contexts = [MagicMock() for _ in range(6)]
        mock_tabs.return_value = mock_tab_contexts

        # Mock __enter__ and __exit__ for context managers
        for ctx in mock_tab_contexts:
            ctx.__enter__ = MagicMock(return_value=ctx)
            ctx.__exit__ = MagicMock(return_value=False)

        render()
        
        # Verify basic UI calls
        mock_tabs.assert_called_once()
        assert mock_markdown.call_count > 0

    def test_module_imports(self):
        """Verify all required imports are present."""
        import modules.design_system as ds

        # Check that module has required imports
        assert hasattr(ds, "st")
        assert hasattr(ds, "ui")
        assert hasattr(ds, "logger")

    def test_render_function_signature(self):
        """Verify render() has correct signature."""
        import inspect
        from modules.design_system import render

        sig = inspect.signature(render)
        assert len(sig.parameters) == 0
        assert sig.return_annotation is None

class TestTabRenderFunctions:
    """Test individual tab rendering functions."""

    @patch("modules.design_system.st.markdown")
    @patch("modules.design_system.st.columns")
    def test_render_design_tokens(self, mock_columns, mock_markdown):
        """Test design tokens tab rendering."""
        from modules.design_system import render_design_tokens

        # Mock columns to return correct number of columns
        mock_columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        render_design_tokens()

        # Verify markdown was called for headers
        assert mock_markdown.call_count > 0

    @patch("modules.design_system.st.markdown")
    @patch("modules.design_system.st.expander")
    def test_render_accessibility_guide(self, mock_expander, mock_markdown):
        """Test accessibility guide rendering."""
        from modules.design_system import render_accessibility_guide

        # Mock expander context manager
        mock_expander.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_expander.return_value.__exit__ = MagicMock(return_value=None)

        render_accessibility_guide()

        assert mock_markdown.call_count > 0

    @patch("modules.design_system.st.markdown")
    def test_render_before_after(self, mock_markdown):
        """Test before/after tab rendering."""
        from modules.design_system import render_before_after

        render_before_after()

        assert mock_markdown.call_count > 0

    @patch("modules.design_system.st.markdown")
    def test_render_button_showcase(self, mock_markdown):
        """Test button showcase rendering."""
        from modules.design_system import render_button_showcase

        render_button_showcase()

        assert mock_markdown.call_count > 0
        # Verify that HTML buttons are rendered
        button_html_found = False
        for call in mock_markdown.call_args_list:
            if "<button" in str(call):
                button_html_found = True
                break
        assert button_html_found