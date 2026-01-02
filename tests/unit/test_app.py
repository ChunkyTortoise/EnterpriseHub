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
            "🏗️ ARETE-Architect",
            "📊 Market Pulse",
            "💼 Financial Analyst",
            "💰 Margin Hunter",
            "🤖 Agent Logic",
            "✍️ Content Engine",
            "🔍 Data Detective",
            "📈 Marketing Analytics",
            "🤖 Multi-Agent Workflow",
            "🧠 Smart Forecast",
            "🏗️ DevOps Control",
            "🎨 Design System",
        ]

        for module in expected_modules:
            assert module in MODULES

    def test_modules_registry_has_correct_structure(self):
        """Test that each module entry has correct structure."""
        from app import MODULES

        for key, value in MODULES.items():
            assert isinstance(value, dict)
            assert "name" in value
            assert "title" in value
            assert "icon" in value
            assert "desc" in value
            assert "status" in value

    def test_module_names_are_valid_python_identifiers(self):
        """Test that module names are valid Python identifiers."""
        from app import MODULES

        for key, value in MODULES.items():
            # Module names should be valid Python identifiers
            assert value["name"].replace("_", "").isalnum()

    def test_module_icons_have_correct_paths(self):
        """Test that icon paths start with assets/icons/."""
        from app import MODULES

        for key, value in MODULES.items():
            icon_path = value["icon"]
            assert icon_path.startswith("assets/icons/")
            assert any(icon_path.endswith(ext) for ext in [".png", ".svg"])


class TestRenderOverview:
    """Tests for _render_overview function."""

    @patch("app.st")
    def test_overview_shows_hero_section(self, mock_st):
        """Test that overview shows hero section."""
        from app import _render_overview
        mock_ui = MagicMock()

        # Mock st.columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        _render_overview(mock_ui)

        mock_ui.hero_section.assert_called_once()
        args = mock_ui.hero_section.call_args[0]
        assert "Unified Enterprise Hub" in args[0]

    @patch("app.st")
    def test_overview_shows_metrics(self, mock_st):
        """Test that overview shows metrics."""
        from app import _render_overview
        mock_ui = MagicMock()

        # Mock st.columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        _render_overview(mock_ui)

        # Should call card_metric 4 times (one for each column)
        assert mock_ui.card_metric.call_count == 4

    @patch("app.st")
    def test_overview_shows_feature_cards(self, mock_st):
        """Test that overview shows feature cards."""
        from app import _render_overview
        mock_ui = MagicMock()

        # Mock st.columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        _render_overview(mock_ui)

        # Should call feature_card multiple times (12 modules shown)
        assert mock_ui.feature_card.call_count == 12

    @patch("app.st")
    def test_overview_shows_use_cases(self, mock_st):
        """Test that overview shows use case cards."""
        from app import _render_overview
        mock_ui = MagicMock()

        # Mock st.columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        _render_overview(mock_ui)

        # Should call use_case_card 4 times (2x2 grid)
        assert mock_ui.use_case_card.call_count == 4

    @patch("app.st")
    def test_overview_uses_spacers(self, mock_st):
        """Test that overview uses spacers for layout."""
        from app import _render_overview
        mock_ui = MagicMock()

        # Mock st.columns to return correct number of columns
        mock_st.columns.side_effect = lambda n: [
            MagicMock() for _ in range(n if isinstance(n, int) else len(n))
        ]

        _render_overview(mock_ui)

        # Should call spacer for spacing between sections
        assert mock_ui.spacer.call_count >= 2


class TestLoadAndRenderModule:
    """Tests for _load_and_render_module function."""

    @patch("streamlit.spinner")
    @patch("utils.ui")
    @patch("importlib.import_module")
    def test_loads_module_correctly(self, mock_import, mock_ui, mock_spinner):
        """Test that module loads and renders correctly."""
        from app import _load_and_render_module

        # Mock context manager for spinner
        mock_spinner.return_value.__enter__.return_value = None

        mock_module = MagicMock()
        mock_module.render = MagicMock()
        mock_import.return_value = mock_module

        _load_and_render_module("market_pulse", "Market Pulse")

        mock_import.assert_called_once_with("modules.market_pulse")
        mock_module.render.assert_called_once()

    @patch("streamlit.spinner")
    @patch("utils.ui")
    @patch("importlib.import_module")
    def test_calls_section_header(self, mock_import, mock_ui, mock_spinner):
        """Test that section header is called with module title."""
        from app import _load_and_render_module

        mock_spinner.return_value.__enter__.return_value = None
        
        mock_module = MagicMock()
        mock_module.render = MagicMock()
        mock_import.return_value = mock_module

        _load_and_render_module("market_pulse", "Market Pulse")

        mock_ui.section_header.assert_called_once_with("Market Pulse")

    @patch("streamlit.warning")
    @patch("streamlit.spinner")
    @patch("utils.ui")
    def test_handles_module_not_found(self, mock_ui, mock_spinner, mock_warning):
        """Test that module not found error is handled gracefully."""
        from app import _load_and_render_module

        mock_spinner.return_value.__enter__.return_value = None

        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ModuleNotFoundError("Module not found")

            _load_and_render_module("nonexistent", "Nonexistent")

            mock_warning.assert_called_once()
            warning_msg = str(mock_warning.call_args[0][0])
            assert "not yet deployed" in warning_msg.lower()

    @patch("streamlit.error")
    @patch("streamlit.spinner")
    @patch("utils.ui")
    def test_handles_module_load_error(self, mock_ui, mock_spinner, mock_error):
        """Test that module load errors are handled gracefully."""
        from app import _load_and_render_module

        mock_spinner.return_value.__enter__.return_value = None

        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = Exception("Load error")

            _load_and_render_module("market_pulse", "Market Pulse")

            mock_error.assert_called_once()
            error_msg = str(mock_error.call_args[0][0])
            assert "Failed to load" in error_msg


class TestModuleStructure:
    """Tests for module structure and imports."""

    def test_app_module_imports_successfully(self):
        """Test that app module imports without errors."""
        import app

        assert app is not None

    def test_modules_constant_is_defined(self):
        """Test that MODULES constant is defined."""
        from app import MODULES

        assert MODULES is not None
        assert len(MODULES) > 0

    def test_main_function_exists(self):
        """Test that main function is defined."""
        from app import main

        assert callable(main)


class TestModuleMetadata:
    """Tests for module metadata in MODULES registry."""

    def test_all_modules_have_unique_names(self):
        """Test that all module names are unique."""
        from app import MODULES

        module_names = [value["name"] for value in MODULES.values()]
        assert len(module_names) == len(set(module_names))

    def test_all_modules_have_unique_titles(self):
        """Test that all module titles are unique."""
        from app import MODULES

        module_titles = [value["title"] for value in MODULES.values()]
        assert len(module_titles) == len(set(module_titles))

    def test_module_count_matches_expected(self):
        """Test that we have exactly 12 modules."""
        from app import MODULES

        assert len(MODULES) == 12

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


class TestErrorScenarios:
    """Tests for various error scenarios."""

    @patch("streamlit.error")
    @patch("streamlit.spinner")
    @patch("utils.ui")
    def test_render_module_with_missing_render_method(self, mock_ui, mock_spinner, mock_error):
        """Test handling of module without render method."""
        from app import _load_and_render_module

        mock_spinner.return_value.__enter__.return_value = None

        with patch("importlib.import_module") as mock_import:
            mock_module = MagicMock(spec=[])  # No render method
            mock_import.return_value = mock_module

            # This should not raise but call st.error
            _load_and_render_module("broken_module", "Broken Module")
            mock_error.assert_called_once()

    @patch("streamlit.error")
    @patch("streamlit.spinner")
    @patch("utils.ui")
    @patch("importlib.import_module")
    def test_render_module_with_render_exception(self, mock_import, mock_ui, mock_spinner, mock_error):
        """Test handling of exception during module render."""
        from app import _load_and_render_module

        mock_spinner.return_value.__enter__.return_value = None

        mock_module = MagicMock()
        mock_module.render.side_effect = Exception("Render error")
        mock_import.return_value = mock_module

        # This should not raise but call st.error
        _load_and_render_module("error_module", "Error Module")
        mock_error.assert_called_once()
