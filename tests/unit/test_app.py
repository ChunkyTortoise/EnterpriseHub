"""
Unit tests for main application entry point (app.py).

Tests module registry, helper functions, and module loading logic.
"""

from unittest.mock import patch, MagicMock


class TestModuleRegistry:
    """Tests for MODULES registry."""

    def test_modules_registry_exists(self):
        """Test that MODULES registry exists."""
        from app import MODULES

        assert MODULES is not None
        assert isinstance(MODULES, dict)

    def test_modules_registry_has_expected_modules(self):
        """Test that MODULES registry contains expected modules."""
        from app import MODULES

        expected_modules = [
            "📊 Market Pulse",
            "💼 Financial Analyst",
            "💰 Margin Hunter",
            "🤖 Agent Logic",
            "✍️ Content Engine",
            "🔍 Data Detective",
            "📈 Marketing Analytics",
            "🤖 Multi-Agent Workflow",
            "🧠 Smart Forecast",
            "🎨 Design System",
        ]

        for module in expected_modules:
            assert module in MODULES

    def test_modules_registry_has_correct_structure(self):
        """Test that each module entry has correct structure."""
        from app import MODULES

        for key, value in MODULES.items():
            assert isinstance(value, tuple)
            assert len(value) == 3
            assert isinstance(value[0], str)  # module name
            assert isinstance(value[1], str)  # module title
            assert isinstance(value[2], str)  # icon path

    def test_module_names_are_valid_python_identifiers(self):
        """Test that module names are valid Python identifiers."""
        from app import MODULES

        for key, (module_name, _, _) in MODULES.items():
            # Module names should be valid Python identifiers
            assert module_name.replace("_", "").isalnum()

    def test_module_icons_have_correct_paths(self):
        """Test that icon paths start with assets/icons/."""
        from app import MODULES

        for key, (_, _, icon_path) in MODULES.items():
            assert icon_path.startswith("assets/icons/")
            assert any(icon_path.endswith(ext) for ext in [".png", ".svg"])


class TestHelperFunctions:
    """Tests for helper functions."""

    @patch("app.st")
    @patch("app.ui")
    def test_render_placeholder_shows_warning(self, mock_ui, mock_st):
        """Test that render_placeholder shows warning message."""
        from app import _render_placeholder

        _render_placeholder("Test Module")

        mock_st.warning.assert_called_once()
        warning_msg = str(mock_st.warning.call_args[0][0])
        assert "Test Module" in warning_msg
        assert "pending" in warning_msg.lower()

    @patch("app.st")
    @patch("app.ui")
    def test_render_placeholder_shows_roadmap(self, mock_ui, mock_st):
        """Test that render_placeholder shows roadmap."""
        from app import _render_placeholder

        _render_placeholder("Test Module")

        mock_st.expander.assert_called_once_with("View Roadmap", expanded=True)

    @patch("app.st")
    @patch("app.ui")
    def test_render_placeholder_calls_section_header(self, mock_ui, mock_st):
        """Test that render_placeholder calls section header."""
        from app import _render_placeholder

        _render_placeholder("Test Module")

        mock_ui.section_header.assert_called_once_with("Test Module")


class TestRenderOverview:
    """Tests for _render_overview function."""

    @patch("app.st")
    @patch("app.ui")
    def test_overview_shows_hero_section(self, mock_ui, mock_st):
        """Test that overview shows hero section."""
        from app import _render_overview

        # Mock st.columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        _render_overview()

        mock_ui.hero_section.assert_called_once()
        args = mock_ui.hero_section.call_args[0]
        assert "Unified Enterprise Hub" in args[0]

    @patch("app.st")
    @patch("app.ui")
    def test_overview_shows_metrics(self, mock_ui, mock_st):
        """Test that overview shows metrics."""
        from app import _render_overview

        # Mock st.columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        _render_overview()

        # Should call card_metric 4 times (one for each column)
        assert mock_ui.card_metric.call_count == 4

    @patch("app.st")
    @patch("app.ui")
    def test_overview_shows_feature_cards(self, mock_ui, mock_st):
        """Test that overview shows feature cards."""
        from app import _render_overview

        # Mock st.columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        _render_overview()

        # Should call feature_card multiple times (9 modules shown)
        assert mock_ui.feature_card.call_count == 9

    @patch("app.st")
    @patch("app.ui")
    def test_overview_shows_use_cases(self, mock_ui, mock_st):
        """Test that overview shows use case cards."""
        from app import _render_overview

        # Mock st.columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        _render_overview()

        # Should call use_case_card 4 times (2x2 grid)
        assert mock_ui.use_case_card.call_count == 4

    @patch("app.st")
    @patch("app.ui")
    def test_overview_shows_comparison_table(self, mock_ui, mock_st):
        """Test that overview shows comparison table."""
        from app import _render_overview

        # Mock st.columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        _render_overview()

        mock_ui.comparison_table.assert_called_once()

    @patch("app.st")
    @patch("app.ui")
    def test_overview_shows_section_headers(self, mock_ui, mock_st):
        """Test that overview shows multiple section headers."""
        from app import _render_overview

        # Mock st.columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        _render_overview()

        # Should call section_header multiple times
        assert mock_ui.section_header.call_count >= 3

    @patch("app.st")
    @patch("app.ui")
    def test_overview_uses_spacers(self, mock_ui, mock_st):
        """Test that overview uses spacers for layout."""
        from app import _render_overview

        # Mock st.columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        _render_overview()

        # Should call spacer for spacing between sections
        assert mock_ui.spacer.call_count >= 4


class TestRenderModule:
    """Tests for _render_module function."""

    @patch("app.st")
    @patch("app.ui")
    @patch("app.importlib.import_module")
    def test_loads_module_correctly(self, mock_import, mock_ui, mock_st):
        """Test that module loads and renders correctly."""
        from app import _render_module

        mock_module = MagicMock()
        mock_module.render = MagicMock()
        mock_import.return_value = mock_module

        _render_module("market_pulse", "Market Pulse")

        mock_import.assert_called_once_with("modules.market_pulse")
        mock_module.render.assert_called_once()

    @patch("app.st")
    @patch("app.ui")
    @patch("app.importlib.import_module")
    def test_calls_section_header(self, mock_import, mock_ui, mock_st):
        """Test that section header is called with module title."""
        from app import _render_module

        mock_module = MagicMock()
        mock_module.render = MagicMock()
        mock_import.return_value = mock_module

        _render_module("market_pulse", "Market Pulse")

        mock_ui.section_header.assert_called_once_with("Market Pulse")

    @patch("app.st")
    @patch("app.ui")
    @patch("app.logger")
    def test_handles_module_not_found(self, mock_logger, mock_ui, mock_st):
        """Test that module not found error is handled gracefully."""
        from app import _render_module

        with patch("app.importlib.import_module") as mock_import:
            mock_import.side_effect = ModuleNotFoundError("Module not found")

            _render_module("nonexistent", "Nonexistent")

            mock_logger.warning.assert_called_once()
            warning_msg = str(mock_logger.warning.call_args[0][0])
            assert "not found" in warning_msg.lower()

    @patch("app.st")
    @patch("app.ui")
    @patch("app.logger")
    def test_handles_module_load_error(self, mock_logger, mock_ui, mock_st):
        """Test that module load errors are handled gracefully."""
        from app import _render_module

        with patch("app.importlib.import_module") as mock_import:
            mock_import.side_effect = Exception("Load error")

            _render_module("market_pulse", "Market Pulse")

            mock_logger.error.assert_called_once()
            mock_st.error.assert_called_once()
            error_msg = str(mock_st.error.call_args[0][0])
            assert "Failed to load" in error_msg

    @patch("app.st")
    @patch("app.ui")
    @patch("app.logger")
    def test_shows_error_checkbox_on_failure(self, mock_logger, mock_ui, mock_st):
        """Test that error checkbox is shown on module load failure."""
        from app import _render_module

        with patch("app.importlib.import_module") as mock_import:
            mock_import.side_effect = Exception("Load error")

            _render_module("market_pulse", "Market Pulse")

            mock_st.checkbox.assert_called_once()
            checkbox_label = mock_st.checkbox.call_args[0][0]
            assert "error" in checkbox_label.lower()


class TestModuleLoading:
    """Tests for specific module loading scenarios."""

    @patch("app.importlib.import_module")
    def test_market_pulse_module_path(self, mock_import):
        """Test that Market Pulse has correct import path."""
        from app import _render_module

        mock_module = MagicMock()
        mock_module.render = MagicMock()
        mock_import.return_value = mock_module

        with patch("app.ui"), patch("app.st"):
            _render_module("market_pulse", "Market Pulse")

        mock_import.assert_called_with("modules.market_pulse")

    @patch("app.importlib.import_module")
    def test_financial_analyst_module_path(self, mock_import):
        """Test that Financial Analyst has correct import path."""
        from app import _render_module

        mock_module = MagicMock()
        mock_module.render = MagicMock()
        mock_import.return_value = mock_module

        with patch("app.ui"), patch("app.st"):
            _render_module("financial_analyst", "Financial Analyst")

        mock_import.assert_called_with("modules.financial_analyst")

    @patch("app.importlib.import_module")
    def test_content_engine_module_path(self, mock_import):
        """Test that Content Engine has correct import path."""
        from app import _render_module

        mock_module = MagicMock()
        mock_module.render = MagicMock()
        mock_import.return_value = mock_module

        with patch("app.ui"), patch("app.st"):
            _render_module("content_engine", "Content Engine")

        mock_import.assert_called_with("modules.content_engine")

    @patch("app.importlib.import_module")
    def test_multi_agent_module_path(self, mock_import):
        """Test that Multi-Agent has correct import path."""
        from app import _render_module

        mock_module = MagicMock()
        mock_module.render = MagicMock()
        mock_import.return_value = mock_module

        with patch("app.ui"), patch("app.st"):
            _render_module("multi_agent", "Multi-Agent Workflow")

        mock_import.assert_called_with("modules.multi_agent")

    @patch("app.importlib.import_module")
    def test_data_detective_module_path(self, mock_import):
        """Test that Data Detective has correct import path."""
        from app import _render_module

        mock_module = MagicMock()
        mock_module.render = MagicMock()
        mock_import.return_value = mock_module

        with patch("app.ui"), patch("app.st"):
            _render_module("data_detective", "Data Detective")

        mock_import.assert_called_with("modules.data_detective")

    @patch("app.importlib.import_module")
    def test_marketing_analytics_module_path(self, mock_import):
        """Test that Marketing Analytics has correct import path."""
        from app import _render_module

        mock_module = MagicMock()
        mock_module.render = MagicMock()
        mock_import.return_value = mock_module

        with patch("app.ui"), patch("app.st"):
            _render_module("marketing_analytics", "Marketing Analytics")

        mock_import.assert_called_with("modules.marketing_analytics")


class TestModuleStructure:
    """Tests for module structure and imports."""

    def test_app_module_imports_successfully(self):
        """Test that app module imports without errors."""
        import app

        assert app is not None

    def test_logger_is_initialized(self):
        """Test that logger is initialized."""
        from app import logger

        assert logger is not None

    def test_modules_constant_is_defined(self):
        """Test that MODULES constant is defined."""
        from app import MODULES

        assert MODULES is not None
        assert len(MODULES) > 0

    def test_helper_functions_exist(self):
        """Test that helper functions are defined."""
        from app import _render_overview, _render_module, _render_placeholder

        assert callable(_render_overview)
        assert callable(_render_module)
        assert callable(_render_placeholder)

    def test_main_function_exists(self):
        """Test that main function is defined."""
        from app import main

        assert callable(main)


class TestModuleMetadata:
    """Tests for module metadata in MODULES registry."""

    def test_all_modules_have_unique_names(self):
        """Test that all module names are unique."""
        from app import MODULES

        module_names = [value[0] for value in MODULES.values()]
        assert len(module_names) == len(set(module_names))

    def test_all_modules_have_unique_titles(self):
        """Test that all module titles are unique."""
        from app import MODULES

        module_titles = [value[1] for value in MODULES.values()]
        assert len(module_titles) == len(set(module_titles))

    def test_module_count_matches_expected(self):
        """Test that we have exactly 10 modules."""
        from app import MODULES

        assert len(MODULES) == 10

    def test_module_keys_have_emojis(self):
        """Test that module keys include emojis."""
        from app import MODULES

        for key in MODULES.keys():
            # Check that key contains at least one emoji
            # This is a simple check - emojis are typically non-ASCII
            assert any(ord(c) > 127 for c in key)


class TestPageConfiguration:
    """Tests for page configuration."""

    def test_page_config_constant_values(self):
        """Test that expected page config values are used."""
        # We can't directly test st.set_page_config calls,
        # but we can verify the module structure supports it
        import app

        # The module should import streamlit
        assert hasattr(app, "st")

    def test_ui_module_is_imported(self):
        """Test that UI module is imported."""
        import app

        assert hasattr(app, "ui")

    def test_logger_module_is_imported(self):
        """Test that logger module is imported."""
        import app

        assert hasattr(app, "logger")


class TestErrorScenarios:
    """Tests for various error scenarios."""

    @patch("app.st")
    @patch("app.ui")
    @patch("app.logger")
    def test_render_module_with_missing_render_method(self, mock_logger, mock_ui, mock_st):
        """Test handling of module without render method."""
        from app import _render_module

        with patch("app.importlib.import_module") as mock_import:
            mock_module = MagicMock(spec=[])  # No render method
            mock_import.return_value = mock_module

            # This should not raise but call st.error
            _render_module("broken_module", "Broken Module")
            mock_st.error.assert_called_once()

    @patch("app.st")
    @patch("app.ui")
    @patch("app.importlib.import_module")
    def test_render_module_with_render_exception(self, mock_import, mock_ui, mock_st):
        """Test handling of exception during module render."""
        from app import _render_module

        mock_module = MagicMock()
        mock_module.render.side_effect = Exception("Render error")
        mock_import.return_value = mock_module

        # This should not raise but call st.error
        _render_module("error_module", "Error Module")
        mock_st.error.assert_called_once()
