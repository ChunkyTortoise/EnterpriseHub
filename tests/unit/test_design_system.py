"""
Tests for Design System module.

Test suite covering:
- Module rendering without errors
- Tab structure and organization
- Helper function behavior
- Color palette completeness
"""

from unittest.mock import MagicMock, patch


class TestDesignSystemModule:
    """Test Design System module core functionality."""

    @patch("streamlit.title")
    @patch("streamlit.markdown")
    @patch("streamlit.tabs")
    def test_render_function_exists(self, mock_tabs, mock_markdown, mock_title):
        """Verify render() function exists and is callable."""
        from modules.design_system import render

        # Mock tabs to return a list of mock contexts
        mock_tab_contexts = [MagicMock() for _ in range(5)]
        mock_tabs.return_value = mock_tab_contexts

        # Mock __enter__ and __exit__ for context managers
        for ctx in mock_tab_contexts:
            ctx.__enter__ = MagicMock(return_value=ctx)
            ctx.__exit__ = MagicMock(return_value=False)

        render()

        # Verify title was called
        mock_title.assert_called_once_with("Design System Gallery")

        # Verify tabs were created with correct labels
        assert mock_tabs.called
        # Check the labels of the first tabs call
        tab_labels = mock_tabs.call_args_list[0][0][0]
        assert len(tab_labels) == 5
        assert "🎨 Colors" in tab_labels
        assert "📝 Typography" in tab_labels
        assert "🧩 Components" in tab_labels
        assert "🎯 Interactive Elements" in tab_labels
        assert "📋 Patterns" in tab_labels

    def test_module_imports(self):
        """Verify all required imports are present."""
        import modules.design_system as ds

        # Check that module has required imports
        assert hasattr(ds, "st")
        assert hasattr(ds, "ui")
        assert hasattr(ds, "logger")
        assert hasattr(ds, "Dict")

    def test_render_function_signature(self):
        """Verify render() has correct signature."""
        import inspect

        from modules.design_system import render

        sig = inspect.signature(render)
        assert len(sig.parameters) == 0
        assert sig.return_annotation is None


class TestColorPaletteRendering:
    """Test color palette helper functions."""

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    def test_render_color_palette_light_theme(self, mock_columns, mock_markdown):
        """Test rendering light theme color palette."""
        import utils.ui as ui
        from modules.design_system import _render_color_palette

        # Mock columns to return list of mock column contexts
        mock_col = MagicMock()
        mock_col.__enter__ = MagicMock(return_value=mock_col)
        mock_col.__exit__ = MagicMock(return_value=False)
        mock_columns.return_value = [mock_col] * 5

        _render_color_palette(ui.LIGHT_THEME, "light")

        # Verify markdown was called for section headers
        assert mock_markdown.call_count > 0

    @patch("streamlit.markdown")
    @patch("streamlit.columns")
    def test_render_color_palette_dark_theme(self, mock_columns, mock_markdown):
        """Test rendering dark theme color palette."""
        import utils.ui as ui
        from modules.design_system import _render_color_palette

        mock_col = MagicMock()
        mock_col.__enter__ = MagicMock(return_value=mock_col)
        mock_col.__exit__ = MagicMock(return_value=False)
        mock_columns.return_value = [mock_col] * 5

        _render_color_palette(ui.DARK_THEME, "dark")

        assert mock_markdown.call_count > 0

    @patch("streamlit.markdown")
    def test_render_color_swatch(self, mock_markdown):
        """Test rendering individual color swatch."""
        from modules.design_system import _render_color_swatch

        _render_color_swatch("primary", "#4338CA", "light")

        # Verify HTML was rendered
        mock_markdown.assert_called_once()
        call_args = mock_markdown.call_args
        html_content = call_args[0][0]

        # Verify HTML contains color code
        assert "#4338CA" in html_content
        assert "primary" in html_content

        # Verify unsafe_allow_html is True
        assert call_args[1]["unsafe_allow_html"] is True


class TestTabRenderFunctions:
    """Test individual tab rendering functions."""

    @patch("modules.design_system.st.markdown")
    @patch("modules.design_system.st.columns")
    @patch("modules.design_system.st.code")
    def test_render_colors_tab(self, mock_code, mock_columns, mock_markdown):
        """Test colors tab rendering."""
        from modules.design_system import _render_colors_tab

        # Mock columns - use lambda to dynamically generate based on num_cols
        mock_col = MagicMock()
        mock_col.__enter__ = MagicMock(return_value=mock_col)
        mock_col.__exit__ = MagicMock(return_value=False)
        # Return appropriate number of columns based on what was requested
        mock_columns.side_effect = lambda num_cols: [mock_col] * num_cols

        _render_colors_tab()

        # Verify markdown was called for headers
        assert mock_markdown.call_count > 0

    @patch("modules.design_system.st.markdown")
    @patch("modules.design_system.st.columns")
    @patch("modules.design_system.st.expander")
    def test_render_typography_tab(self, mock_expander, mock_columns, mock_markdown):
        """Test typography tab rendering."""
        from modules.design_system import _render_typography_tab

        # Mock columns
        mock_col = MagicMock()
        mock_col.__enter__ = MagicMock(return_value=mock_col)
        mock_col.__exit__ = MagicMock(return_value=False)
        mock_columns.return_value = [mock_col] * 2

        _render_typography_tab()

        # Verify typography content was rendered
        assert mock_markdown.call_count > 0

    @patch("modules.design_system.st.markdown")
    @patch("modules.design_system.st.columns")
    @patch("modules.design_system.st.expander")
    @patch("utils.ui.hero_section")
    @patch("utils.ui.feature_card")
    @patch("utils.ui.use_case_card")
    @patch("utils.ui.status_badge")
    @patch("utils.ui.section_header")
    @patch("utils.ui.comparison_table")
    def test_render_components_tab(
        self,
        mock_comparison,
        mock_header,
        mock_badge,
        mock_use_case,
        mock_feature,
        mock_hero,
        mock_expander,
        mock_columns,
        mock_markdown,
    ):
        """Test components tab rendering."""
        from modules.design_system import _render_components_tab

        # Mock columns (called with 3 for feature cards, 2 for use case cards, 4 for badges)
        mock_col = MagicMock()
        mock_col.__enter__ = MagicMock(return_value=mock_col)
        mock_col.__exit__ = MagicMock(return_value=False)
        mock_columns.side_effect = [
            [mock_col] * 3,  # Hero/Feature cards
            [mock_col] * 2,  # Use case cards
            [mock_col] * 4,  # Status badges
        ]

        # Mock expander context
        mock_exp_ctx = MagicMock()
        mock_exp_ctx.__enter__ = MagicMock(return_value=mock_exp_ctx)
        mock_exp_ctx.__exit__ = MagicMock(return_value=False)
        mock_expander.return_value = mock_exp_ctx

        # Mock status_badge to return HTML
        mock_badge.return_value = "<span>badge</span>"

        _render_components_tab()

        # Verify UI components were called
        assert mock_hero.call_count >= 1
        assert mock_feature.call_count >= 1
        assert mock_use_case.call_count >= 1
        assert mock_header.call_count >= 1
        assert mock_comparison.call_count >= 1

    @patch("modules.design_system.st.markdown")
    @patch("modules.design_system.st.columns")
    @patch("modules.design_system.st.button")
    @patch("modules.design_system.st.expander")
    @patch("utils.ui.card_metric")
    def test_render_interactive_tab(
        self, mock_metric, mock_expander, mock_button, mock_columns, mock_markdown
    ):
        """Test interactive elements tab rendering."""
        from modules.design_system import _render_interactive_tab

        # Mock columns (called with 3 for buttons, 4 for metrics, 2 for form elements)
        mock_col = MagicMock()
        mock_col.__enter__ = MagicMock(return_value=mock_col)
        mock_col.__exit__ = MagicMock(return_value=False)
        mock_columns.side_effect = [
            [mock_col] * 3,  # Buttons
            [mock_col] * 4,  # Metrics
            [mock_col] * 2,  # Form elements
        ]

        # Mock expander
        mock_exp_ctx = MagicMock()
        mock_exp_ctx.__enter__ = MagicMock(return_value=mock_exp_ctx)
        mock_exp_ctx.__exit__ = MagicMock(return_value=False)
        mock_expander.return_value = mock_exp_ctx

        _render_interactive_tab()

        # Verify metrics were rendered
        assert mock_metric.call_count >= 4

    @patch("modules.design_system.st.markdown")
    @patch("modules.design_system.st.columns")
    @patch("modules.design_system.st.tabs")
    @patch("modules.design_system.st.expander")
    def test_render_patterns_tab(self, mock_expander, mock_tabs, mock_columns, mock_markdown):
        """Test patterns tab rendering."""
        from modules.design_system import _render_patterns_tab

        # Mock columns (called with 2, 3, 2, 2 for different patterns)
        mock_col = MagicMock()
        mock_col.__enter__ = MagicMock(return_value=mock_col)
        mock_col.__exit__ = MagicMock(return_value=False)
        mock_columns.side_effect = [
            [mock_col] * 2,
            [mock_col] * 3,
            [mock_col] * 2,
            [mock_col] * 2,  # Design principles section
        ]

        # Mock expander
        mock_exp_ctx = MagicMock()
        mock_exp_ctx.__enter__ = MagicMock(return_value=mock_exp_ctx)
        mock_exp_ctx.__exit__ = MagicMock(return_value=False)
        mock_expander.return_value = mock_exp_ctx

        # Mock tabs
        mock_tab_ctx = MagicMock()
        mock_tab_ctx.__enter__ = MagicMock(return_value=mock_tab_ctx)
        mock_tab_ctx.__exit__ = MagicMock(return_value=False)
        mock_tabs.side_effect = [
            [mock_tab_ctx] * 3,  # demo_tabs
        ]

        _render_patterns_tab()

        # Verify content was rendered
        assert mock_markdown.call_count > 0


class TestColorSwatchLogic:
    """Test color swatch text color logic."""

    def test_color_swatch_text_contrast_light_theme(self):
        """Test text color contrast for light theme swatches."""
        from modules.design_system import _render_color_swatch

        with patch("streamlit.markdown") as mock_markdown:
            # Test dark color on light theme (should use white text)
            _render_color_swatch("primary", "#4338CA", "light")
            html = mock_markdown.call_args[0][0]
            # Dark background should have light text for contrast
            assert "#FFFFFF" in html or "#0F172A" in html

    def test_color_swatch_text_contrast_dark_theme(self):
        """Test text color contrast for dark theme swatches."""
        from modules.design_system import _render_color_swatch

        with patch("streamlit.markdown") as mock_markdown:
            # Test light color on dark theme (should use dark text)
            _render_color_swatch("primary", "#A5B4FC", "dark")
            html = mock_markdown.call_args[0][0]
            # Light background should have dark text for contrast
            assert "#FFFFFF" in html or "#0F172A" in html


class TestDesignSystemIntegration:
    """Test integration with utils.ui module."""

    def test_imports_ui_components(self):
        """Verify design_system imports all necessary UI components."""
        import utils.ui as ui

        # Verify LIGHT_THEME and DARK_THEME are accessible
        assert hasattr(ui, "LIGHT_THEME")
        assert hasattr(ui, "DARK_THEME")
        assert hasattr(ui, "THEME")

    def test_imports_ui_functions(self):
        """Verify design_system can access UI helper functions."""
        import utils.ui as ui

        # Verify all UI functions exist
        assert callable(ui.hero_section)
        assert callable(ui.feature_card)
        assert callable(ui.use_case_card)
        assert callable(ui.status_badge)
        assert callable(ui.section_header)
        assert callable(ui.comparison_table)
        assert callable(ui.card_metric)
        assert callable(ui.footer)


class TestDesignSystemDictStructure:
    """Test color palette dictionary structure."""

    def test_light_theme_has_all_colors(self):
        """Verify light theme has all required color keys."""
        import utils.ui as ui

        required_keys = [
            "primary",
            "primary_dark",
            "primary_light",
            "secondary",
            "background",
            "surface",
            "text_main",
            "text_light",
            "success",
            "warning",
            "danger",
            "border",
            "button_text",
        ]

        for key in required_keys:
            assert key in ui.LIGHT_THEME, f"Missing key: {key}"

    def test_dark_theme_has_all_colors(self):
        """Verify dark theme has all required color keys."""
        import utils.ui as ui

        required_keys = [
            "primary",
            "primary_dark",
            "primary_light",
            "secondary",
            "background",
            "surface",
            "text_main",
            "text_light",
            "success",
            "warning",
            "danger",
            "border",
            "button_text",
        ]

        for key in required_keys:
            assert key in ui.DARK_THEME, f"Missing key: {key}"

    def test_color_values_are_hex_codes(self):
        """Verify all color values are valid hex codes."""
        import re

        import utils.ui as ui

        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")

        # Test light theme
        for key, value in ui.LIGHT_THEME.items():
            if key != "font_family":
                assert hex_pattern.match(value), f"Invalid hex code for {key}: {value}"

        # Test dark theme
        for key, value in ui.DARK_THEME.items():
            if key != "font_family":
                assert hex_pattern.match(value), f"Invalid hex code for {key}: {value}"
