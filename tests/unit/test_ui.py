"""Tests for UI/UX module (utils/ui.py)."""

from unittest.mock import MagicMock, patch


from utils import ui


class TestSetupInterface:
    """Test the setup_interface function."""

    @patch("utils.ui.st")
    def test_setup_interface_injects_css(self, mock_st):
        """Test that setup_interface injects custom CSS."""
        ui.setup_interface()

        # Verify st.markdown was called with unsafe_allow_html=True
        mock_st.markdown.assert_called_once()
        args, kwargs = mock_st.markdown.call_args
        assert kwargs.get("unsafe_allow_html") is True
        assert "<style>" in args[0]
        assert "</style>" in args[0]

    @patch("utils.ui.st")
    def test_setup_interface_includes_theme_colors(self, mock_st):
        """Test that CSS includes theme colors."""
        ui.setup_interface()

        args, _ = mock_st.markdown.call_args
        css_content = args[0]

        # Check for primary color
        assert ui.THEME["primary"] in css_content
        # Check for font family
        assert ui.THEME["font_family"] in css_content
        # Check for Inter font import
        assert "Inter" in css_content


class TestCardMetric:
    """Test the card_metric function."""

    @patch("utils.ui.st")
    def test_card_metric_with_all_params(self, mock_st):
        """Test card_metric with all parameters."""
        ui.card_metric(label="Test Label", value="100", delta="10%", help="Test help text")

        mock_st.metric.assert_called_once_with(
            label="Test Label", value="100", delta="10%", help="Test help text"
        )

    @patch("utils.ui.st")
    def test_card_metric_without_optional_params(self, mock_st):
        """Test card_metric without optional parameters."""
        ui.card_metric(label="Test", value="50")

        mock_st.metric.assert_called_once_with(label="Test", value="50", delta=None, help=None)


class TestSectionHeader:
    """Test the section_header function."""

    @patch("utils.ui.st")
    def test_section_header_with_subtitle(self, mock_st):
        """Test section_header with subtitle."""
        ui.section_header("Test Title", "Test Subtitle")

        # Should call markdown twice: once for title, once for subtitle
        assert mock_st.markdown.call_count == 2

        # Check title call
        title_call = mock_st.markdown.call_args_list[0]
        assert "## Test Title" in title_call[0][0]

        # Check subtitle call
        subtitle_call = mock_st.markdown.call_args_list[1]
        assert "Test Subtitle" in subtitle_call[0][0]
        assert subtitle_call[1].get("unsafe_allow_html") is True

    @patch("utils.ui.st")
    def test_section_header_without_subtitle(self, mock_st):
        """Test section_header without subtitle."""
        ui.section_header("Test Title")

        # Should only call markdown once for title
        mock_st.markdown.assert_called_once()
        args, _ = mock_st.markdown.call_args
        assert "## Test Title" in args[0]


class TestStatusBadge:
    """Test the status_badge function."""

    def test_status_badge_active(self):
        """Test status badge for 'active' status."""
        result = ui.status_badge("active")

        assert "background-color: #DCFCE7" in result
        assert "color: #166534" in result
        assert "active" in result.lower()

    def test_status_badge_new(self):
        """Test status badge for 'new' status."""
        result = ui.status_badge("new")

        assert "background-color: #DBEAFE" in result
        assert "color: #1E40AF" in result
        assert "new" in result.lower()

    def test_status_badge_hero(self):
        """Test status badge for 'hero' status."""
        result = ui.status_badge("hero")

        assert "background-color: #FEF3C7" in result
        assert "color: #92400E" in result
        assert "hero" in result.lower()

    def test_status_badge_pending(self):
        """Test status badge for 'pending' status."""
        result = ui.status_badge("pending")

        assert "background-color: #F1F5F9" in result
        assert "color: #475569" in result
        assert "pending" in result.lower()

    def test_status_badge_unknown_defaults_to_pending(self):
        """Test that unknown status defaults to pending colors."""
        result = ui.status_badge("unknown")

        # Should use pending colors as fallback
        assert "background-color: #F1F5F9" in result
        assert "color: #475569" in result

    def test_status_badge_case_insensitive(self):
        """Test that status badge is case-insensitive."""
        result_lower = ui.status_badge("active")
        result_upper = ui.status_badge("ACTIVE")

        # Both should have same colors
        assert "background-color: #DCFCE7" in result_lower
        assert "background-color: #DCFCE7" in result_upper


class TestFeatureCard:
    """Test the feature_card function."""

    @patch("utils.ui.st")
    def test_feature_card_with_default_status(self, mock_st):
        """Test feature_card with default status."""
        ui.feature_card(icon="🚀", title="Test Feature", description="Test description")

        mock_st.markdown.assert_called_once()
        args, kwargs = mock_st.markdown.call_args

        html = args[0]
        assert "Test Feature" in html
        assert "Test description" in html
        assert "🚀" in html
        assert 'role="article"' in html
        assert 'aria-label="Feature: Test Feature"' in html
        assert kwargs.get("unsafe_allow_html") is True

    @patch("utils.ui.st")
    def test_feature_card_with_custom_status(self, mock_st):
        """Test feature_card with custom status."""
        ui.feature_card(
            icon="🎯", title="Hero Feature", description="Special feature", status="hero"
        )

        args, _ = mock_st.markdown.call_args
        html = args[0]

        # Should include hero badge colors
        assert "hero" in html.lower()

    @patch("utils.ui.st")
    def test_feature_card_has_accessibility_attributes(self, mock_st):
        """Test that feature_card includes accessibility attributes."""
        ui.feature_card(icon="📊", title="Analytics", description="Data insights")

        args, _ = mock_st.markdown.call_args
        html = args[0]

        # Check for ARIA attributes
        assert 'role="article"' in html
        assert "aria-label" in html
        assert 'role="img"' in html


class TestHeroSection:
    """Test the hero_section function."""

    @patch("utils.ui.st")
    def test_hero_section_renders_title_and_subtitle(self, mock_st):
        """Test that hero_section renders title and subtitle."""
        ui.hero_section("Main Title", "Subtitle text")

        mock_st.markdown.assert_called_once()
        args, kwargs = mock_st.markdown.call_args

        html = args[0]
        assert "Main Title" in html
        assert "Subtitle text" in html
        assert "hero-title" in html
        assert "hero-subtitle" in html
        assert kwargs.get("unsafe_allow_html") is True

    @patch("utils.ui.st")
    def test_hero_section_has_semantic_html(self, mock_st):
        """Test that hero_section uses semantic HTML."""
        ui.hero_section("Test", "Description")

        args, _ = mock_st.markdown.call_args
        html = args[0]

        assert "<section" in html
        assert 'role="banner"' in html
        assert 'aria-label="Hero section"' in html


class TestUseCaseCard:
    """Test the use_case_card function."""

    @patch("utils.ui.st")
    def test_use_case_card_renders_content(self, mock_st):
        """Test that use_case_card renders all content."""
        ui.use_case_card(
            icon="💡",
            title="For Developers",
            description="<strong>Test</strong> description",
        )

        mock_st.markdown.assert_called_once()
        args, kwargs = mock_st.markdown.call_args

        html = args[0]
        assert "💡" in html
        assert "For Developers" in html
        assert "<strong>Test</strong> description" in html
        assert kwargs.get("unsafe_allow_html") is True

    @patch("utils.ui.st")
    def test_use_case_card_has_accessibility(self, mock_st):
        """Test that use_case_card has accessibility attributes."""
        ui.use_case_card(icon="📈", title="For Teams", description="Team features")

        args, _ = mock_st.markdown.call_args
        html = args[0]

        assert 'role="article"' in html
        assert 'aria-label="Use case: For Teams"' in html
        assert 'role="img"' in html


class TestComparisonTable:
    """Test the comparison_table function."""

    @patch("utils.ui.st")
    def test_comparison_table_renders(self, mock_st):
        """Test that comparison_table renders HTML table."""
        ui.comparison_table()

        mock_st.markdown.assert_called_once()
        args, kwargs = mock_st.markdown.call_args

        html = args[0]
        assert "<table" in html
        assert "<thead>" in html
        assert "<tbody>" in html
        assert "EnterpriseHub" in html
        assert kwargs.get("unsafe_allow_html") is True

    @patch("utils.ui.st")
    def test_comparison_table_has_all_columns(self, mock_st):
        """Test that comparison_table has all comparison columns."""
        ui.comparison_table()

        args, _ = mock_st.markdown.call_args
        html = args[0]

        # Check for all comparison columns
        assert "EnterpriseHub" in html
        assert "Excel Spreadsheets" in html
        assert "Bloomberg Terminal" in html
        assert "Agency Dashboards" in html

    @patch("utils.ui.st")
    def test_comparison_table_has_accessibility(self, mock_st):
        """Test that comparison_table has accessibility attributes."""
        ui.comparison_table()

        args, _ = mock_st.markdown.call_args
        html = args[0]

        assert "<section" in html
        assert 'role="table"' in html
        assert "aria-label" in html
        assert 'scope="col"' in html

    @patch("utils.ui.st")
    def test_comparison_table_has_comparison_rows(self, mock_st):
        """Test that comparison_table includes comparison metrics."""
        ui.comparison_table()

        args, _ = mock_st.markdown.call_args
        html = args[0]

        # Check for key comparison rows
        assert "Cost" in html
        assert "Setup Time" in html
        assert "Technical Analysis" in html
        assert "AI-Powered Insights" in html
        assert "Ownership" in html


class TestFooter:
    """Test the footer function."""

    @patch("utils.ui.st")
    def test_footer_renders_copyright(self, mock_st):
        """Test that footer renders copyright notice."""
        ui.footer()

        mock_st.markdown.assert_called_once()
        args, kwargs = mock_st.markdown.call_args

        html = args[0]
        assert "© 2025 Enterprise Hub" in html
        assert "Streamlit & Python" in html
        assert kwargs.get("unsafe_allow_html") is True

    @patch("utils.ui.st")
    def test_footer_has_links(self, mock_st):
        """Test that footer includes GitHub and LinkedIn links."""
        ui.footer()

        args, _ = mock_st.markdown.call_args
        html = args[0]

        assert "github.com/ChunkyTortoise/enterprise-hub" in html
        assert "linkedin.com/in/caymanroden" in html
        assert "View Source" in html
        assert "Contact Developer" in html

    @patch("utils.ui.st")
    def test_footer_has_semantic_html(self, mock_st):
        """Test that footer uses semantic HTML."""
        ui.footer()

        args, _ = mock_st.markdown.call_args
        html = args[0]

        assert "<footer" in html
        assert 'role="contentinfo"' in html
        assert "<nav" in html
        assert "aria-label" in html

    @patch("utils.ui.st")
    def test_footer_links_have_security_attributes(self, mock_st):
        """Test that footer links have security attributes."""
        ui.footer()

        args, _ = mock_st.markdown.call_args
        html = args[0]

        # External links should have rel="noopener noreferrer"
        assert 'rel="noopener noreferrer"' in html
        assert 'target="_blank"' in html


class TestThemeConstants:
    """Test the THEME constants."""

    def test_theme_has_all_colors(self):
        """Test that THEME dictionary has all required colors."""
        required_colors = [
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
        ]

        for color in required_colors:
            assert color in ui.THEME, f"Missing color: {color}"
            assert ui.THEME[color].startswith("#"), f"{color} should be hex color"

    def test_theme_has_font_family(self):
        """Test that THEME has font_family."""
        assert "font_family" in ui.THEME
        assert "Inter" in ui.THEME["font_family"]

    def test_theme_colors_are_valid_hex(self):
        """Test that all theme colors are valid hex codes."""
        import re

        hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")

        for key, value in ui.THEME.items():
            if key != "font_family":
                assert hex_pattern.match(value), f"{key} has invalid hex: {value}"


class TestResponsiveDesign:
    """Test responsive design CSS."""

    @patch("utils.ui.st")
    def test_css_has_mobile_breakpoints(self, mock_st):
        """Test that CSS includes mobile breakpoints."""
        ui.setup_interface()

        args, _ = mock_st.markdown.call_args
        css = args[0]

        # Check for responsive breakpoints
        assert "@media (max-width: 768px)" in css
        assert "@media (max-width: 1024px)" in css
        assert "@media (max-width: 480px)" in css

    @patch("utils.ui.st")
    def test_css_has_focus_states(self, mock_st):
        """Test that CSS includes focus states for accessibility."""
        ui.setup_interface()

        args, _ = mock_st.markdown.call_args
        css = args[0]

        # Check for focus states
        assert ":focus" in css
        assert "outline" in css


class TestSkeletonLoader:
    """Test the skeleton_loader function."""

    @patch("utils.ui.st")
    def test_skeleton_loader_card_type(self, mock_st):
        """Test skeleton_loader with card type."""
        ui.skeleton_loader("card")

        mock_st.markdown.assert_called_once()
        args, kwargs = mock_st.markdown.call_args

        html = args[0]
        assert "skeleton-card" in html
        assert "skeleton-circle" in html
        assert "skeleton-title" in html
        assert "skeleton-line" in html
        assert 'role="status"' in html
        assert 'aria-label="Loading content"' in html
        assert kwargs.get("unsafe_allow_html") is True

    @patch("utils.ui.st")
    def test_skeleton_loader_text_type(self, mock_st):
        """Test skeleton_loader with text type."""
        ui.skeleton_loader("text")

        args, _ = mock_st.markdown.call_args
        html = args[0]

        assert "skeleton-line" in html
        assert "width: 100%" in html
        assert "width: 95%" in html
        assert 'role="status"' in html
        assert 'aria-label="Loading text content"' in html

    @patch("utils.ui.st")
    def test_skeleton_loader_metric_type(self, mock_st):
        """Test skeleton_loader with metric type."""
        ui.skeleton_loader("metric")

        args, _ = mock_st.markdown.call_args
        html = args[0]

        assert "skeleton-card" in html
        assert "skeleton-line" in html
        assert 'role="status"' in html
        assert 'aria-label="Loading metric"' in html

    @patch("utils.ui.st")
    def test_skeleton_loader_table_type(self, mock_st):
        """Test skeleton_loader with table type."""
        ui.skeleton_loader("table")

        args, _ = mock_st.markdown.call_args
        html = args[0]

        assert "display: flex" in html
        assert "width: 25%" in html
        assert 'role="status"' in html
        assert 'aria-label="Loading table row"' in html

    @patch("utils.ui.st")
    def test_skeleton_loader_multiple_count(self, mock_st):
        """Test skeleton_loader renders multiple skeletons."""
        ui.skeleton_loader("card", count=3)

        args, _ = mock_st.markdown.call_args
        html = args[0]

        # Should have 3 skeleton cards
        assert html.count("skeleton-card") == 3
        assert html.count('role="status"') == 3

    @patch("utils.ui.st")
    def test_skeleton_loader_default_count(self, mock_st):
        """Test skeleton_loader with default count of 1."""
        ui.skeleton_loader("card")

        args, _ = mock_st.markdown.call_args
        html = args[0]

        # Should have exactly 1 skeleton card
        assert html.count("skeleton-card") == 1

    @patch("utils.ui.st")
    def test_skeleton_loader_invalid_type_defaults_to_card(self, mock_st):
        """Test skeleton_loader with invalid type defaults to card."""
        ui.skeleton_loader("invalid_type")

        args, _ = mock_st.markdown.call_args
        html = args[0]

        # Should default to card type
        assert "skeleton-card" in html
        assert "skeleton-circle" in html

    @patch("utils.ui.st")
    def test_skeleton_loader_has_accessibility_attributes(self, mock_st):
        """Test that skeleton_loader includes proper ARIA attributes."""
        ui.skeleton_loader("card")

        args, _ = mock_st.markdown.call_args
        html = args[0]

        assert 'role="status"' in html
        assert 'aria-live="polite"' in html
        assert 'aria-hidden="true"' in html
        assert "sr-only" in html


class TestToast:
    """Test the toast function."""

    @patch("utils.ui.st")
    def test_toast_uses_native_streamlit_when_available(self, mock_st):
        """Test toast uses st.toast when available."""
        # Simulate Streamlit 1.27+ with toast support
        mock_st.toast = MagicMock()

        ui.toast("Test message", "success")

        mock_st.toast.assert_called_once()
        args, kwargs = mock_st.toast.call_args
        assert "Test message" in args[0]
        assert "✓" in args[0]

    @patch("utils.ui.st")
    def test_toast_fallback_success(self, mock_st):
        """Test toast fallback implementation for success type."""
        # Remove toast attribute to simulate older Streamlit
        if hasattr(mock_st, "toast"):
            delattr(mock_st, "toast")

        ui.toast("Success message", "success")

        mock_st.markdown.assert_called_once()
        args, kwargs = mock_st.markdown.call_args

        html = args[0]
        assert "toast-success" in html
        assert "Success message" in html
        assert "✓" in html
        assert 'role="alert"' in html
        assert kwargs.get("unsafe_allow_html") is True

    @patch("utils.ui.st")
    def test_toast_fallback_error(self, mock_st):
        """Test toast fallback implementation for error type."""
        if hasattr(mock_st, "toast"):
            delattr(mock_st, "toast")

        ui.toast("Error message", "error")

        args, _ = mock_st.markdown.call_args
        html = args[0]

        assert "toast-error" in html
        assert "Error message" in html
        assert "✗" in html

    @patch("utils.ui.st")
    def test_toast_fallback_warning(self, mock_st):
        """Test toast fallback implementation for warning type."""
        if hasattr(mock_st, "toast"):
            delattr(mock_st, "toast")

        ui.toast("Warning message", "warning")

        args, _ = mock_st.markdown.call_args
        html = args[0]

        assert "toast-warning" in html
        assert "Warning message" in html
        assert "⚠" in html

    @patch("utils.ui.st")
    def test_toast_fallback_info(self, mock_st):
        """Test toast fallback implementation for info type."""
        if hasattr(mock_st, "toast"):
            delattr(mock_st, "toast")

        ui.toast("Info message", "info")

        args, _ = mock_st.markdown.call_args
        html = args[0]

        assert "toast-info" in html
        assert "Info message" in html
        assert "ℹ" in html

    @patch("utils.ui.st")
    def test_toast_custom_duration(self, mock_st):
        """Test toast with custom duration."""
        if hasattr(mock_st, "toast"):
            delattr(mock_st, "toast")

        ui.toast("Test", "success", duration=5000)

        args, _ = mock_st.markdown.call_args
        html = args[0]

        # Check that duration is in the JavaScript
        assert "5000" in html

    @patch("utils.ui.st")
    def test_toast_default_duration(self, mock_st):
        """Test toast with default duration of 3000ms."""
        if hasattr(mock_st, "toast"):
            delattr(mock_st, "toast")

        ui.toast("Test", "success")

        args, _ = mock_st.markdown.call_args
        html = args[0]

        # Check that default duration is used
        assert "3000" in html

    @patch("utils.ui.st")
    def test_toast_has_accessibility_attributes(self, mock_st):
        """Test that toast includes proper ARIA attributes."""
        if hasattr(mock_st, "toast"):
            delattr(mock_st, "toast")

        ui.toast("Test", "success")

        args, _ = mock_st.markdown.call_args
        html = args[0]

        assert 'role="alert"' in html
        assert 'aria-live="assertive"' in html
        assert 'aria-atomic="true"' in html

    @patch("utils.ui.st")
    def test_toast_includes_auto_dismiss_script(self, mock_st):
        """Test that toast includes JavaScript for auto-dismiss."""
        if hasattr(mock_st, "toast"):
            delattr(mock_st, "toast")

        ui.toast("Test", "success")

        args, _ = mock_st.markdown.call_args
        html = args[0]

        assert "<script>" in html
        assert "setTimeout" in html
        assert "slideOut" in html


class TestAnimations:
    """Test animation CSS."""

    @patch("utils.ui.st")
    def test_css_has_shimmer_animation(self, mock_st):
        """Test that CSS includes shimmer animation for skeletons."""
        ui.setup_interface()

        args, _ = mock_st.markdown.call_args
        css = args[0]

        assert "@keyframes shimmer" in css
        assert "animation: shimmer" in css

    @patch("utils.ui.st")
    def test_css_has_fade_in_animation(self, mock_st):
        """Test that CSS includes fade-in animation."""
        ui.setup_interface()

        args, _ = mock_st.markdown.call_args
        css = args[0]

        assert "@keyframes fadeIn" in css
        assert "animation: fadeIn" in css

    @patch("utils.ui.st")
    def test_css_has_bounce_animation(self, mock_st):
        """Test that CSS includes bounce animation for CTAs."""
        ui.setup_interface()

        args, _ = mock_st.markdown.call_args
        css = args[0]

        assert "@keyframes bounce" in css
        assert "cta-button" in css

    @patch("utils.ui.st")
    def test_css_has_slide_animations(self, mock_st):
        """Test that CSS includes slide animations for toasts."""
        ui.setup_interface()

        args, _ = mock_st.markdown.call_args
        css = args[0]

        assert "@keyframes slideIn" in css
        assert "@keyframes slideOut" in css

    @patch("utils.ui.st")
    def test_css_has_stagger_effect(self, mock_st):
        """Test that CSS includes stagger effect for cards."""
        ui.setup_interface()

        args, _ = mock_st.markdown.call_args
        css = args[0]

        assert "nth-child(1)" in css
        assert "nth-child(2)" in css
        assert "nth-child(3)" in css
        assert "animation-delay" in css

    @patch("utils.ui.st")
    def test_css_respects_reduced_motion(self, mock_st):
        """Test that CSS respects prefers-reduced-motion."""
        ui.setup_interface()

        args, _ = mock_st.markdown.call_args
        css = args[0]

        assert "prefers-reduced-motion: reduce" in css
        assert "animation-duration: 0.01ms" in css

    @patch("utils.ui.st")
    def test_css_has_smooth_transitions(self, mock_st):
        """Test that CSS includes smooth transitions."""
        ui.setup_interface()

        args, _ = mock_st.markdown.call_args
        css = args[0]

        assert "transition: all 0.2s ease-in-out" in css
