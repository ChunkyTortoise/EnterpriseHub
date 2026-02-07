"""
Unit tests for DevOps Control module.
"""
from unittest.mock import MagicMock, patch
import pytest
import sys

from modules import devops_control

class TestDevOpsControl:
    
    @patch("modules.devops_control.px")
    @patch("modules.devops_control.go")
    @patch("modules.devops_control.st")
    @patch("modules.devops_control.ui")
    def test_render_shows_header(self, mock_ui, mock_st, mock_go, mock_px):
        """Test that render shows the correct section header."""
        # Fix columns unpacking
        mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        # Fix tabs unpacking
        mock_st.tabs.side_effect = lambda tabs: [MagicMock() for _ in tabs]
        
        # Configure ui mocks to avoid Plotly validation errors
        mock_ui.get_plotly_template.return_value = {}
        mock_ui.THEME = {
            "primary": "#000000",
            "success": "#00FF00",
            "warning": "#FFFF00",
            "danger": "#FF0000",
            "surface": "#FFFFFF",
            "accent": "#0000FF",
            "text_main": "#000000",
            "text_light": "#CCCCCC",
        }
        
        devops_control.render()
        mock_ui.section_header.assert_called_once()
        args = mock_ui.section_header.call_args[0]
        assert "DevOps Control Center" in args[0]

    @patch("modules.devops_control.px")
    @patch("modules.devops_control.go")
    @patch("modules.devops_control.st")
    @patch("modules.devops_control.ui")
    def test_render_shows_pipeline_status(self, mock_ui, mock_st, mock_go, mock_px):
        """Test that pipeline status section is rendered."""
        # Fix columns unpacking
        mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        # Fix tabs unpacking
        mock_st.tabs.side_effect = lambda tabs: [MagicMock() for _ in tabs]
        
        # Configure ui mocks
        mock_ui.get_plotly_template.return_value = {}
        mock_ui.THEME = {
            "primary": "#000000",
            "success": "#00FF00",
            "warning": "#FFFF00",
            "danger": "#FF0000",
            "surface": "#FFFFFF",
            "accent": "#0000FF",
            "text_main": "#000000",
            "text_light": "#CCCCCC",
        }

        devops_control.render()
        
        # Should create columns for pipeline stages
        mock_st.columns.assert_called()
        
        # Check for pipeline stage indicators (Build, Tests, etc.)
        # These are rendered via st.markdown with HTML
        assert mock_st.markdown.call_count > 5 

    @patch("modules.devops_control.px")
    @patch("modules.devops_control.go")
    @patch("modules.devops_control.st")
    @patch("modules.devops_control.ui")
    def test_render_shows_animated_metrics(self, mock_ui, mock_st, mock_go, mock_px):
        """Test that key metrics are shown using animated_metric."""
        # Fix columns unpacking
        mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        # Fix tabs unpacking
        mock_st.tabs.side_effect = lambda tabs: [MagicMock() for _ in tabs]
        
        # Configure ui mocks
        mock_ui.get_plotly_template.return_value = {}
        mock_ui.THEME = {
            "primary": "#000000",
            "success": "#00FF00",
            "warning": "#FFFF00",
            "danger": "#FF0000",
            "surface": "#FFFFFF",
            "accent": "#0000FF",
            "text_main": "#000000",
            "text_light": "#CCCCCC",
        }

        devops_control.render()
        
        # Top row metrics
        calls = [args[0] for args, _ in mock_ui.animated_metric.call_args_list]
        assert "Agent Status" in calls
        assert "Build Pipeline" in calls
        assert "Test Coverage" in calls
        assert "Deployment" in calls

    @patch("modules.devops_control.px")
    @patch("modules.devops_control.go")
    @patch("modules.devops_control.st")
    @patch("modules.devops_control.ui")
    def test_render_agent_command_center(self, mock_ui, mock_st, mock_go, mock_px):
        """Test that agent command center tabs are rendered."""
        # Fix columns unpacking
        mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        # Fix tabs unpacking
        mock_st.tabs.side_effect = lambda tabs: [MagicMock() for _ in tabs]
        
        # Configure ui mocks
        mock_ui.get_plotly_template.return_value = {}
        mock_ui.THEME = {
            "primary": "#000000",
            "success": "#00FF00",
            "warning": "#FFFF00",
            "danger": "#FF0000",
            "surface": "#FFFFFF",
            "accent": "#0000FF",
            "text_main": "#000000",
            "text_light": "#CCCCCC",
        }

        devops_control.render()
        
        mock_st.tabs.assert_called_with(
            ["💬 Task Executor", "📈 Performance Monitor", "🔍 Code Analysis"]
        )
