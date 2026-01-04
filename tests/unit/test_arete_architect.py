"""
Unit tests for ARETE-Architect module.
"""
from unittest.mock import MagicMock, patch
import pytest
import sys

from modules import arete_architect

class TestAreteArchitect:
    
    @patch("modules.arete_architect.st")
    @patch("modules.arete_architect.ui")
    def test_render_shows_header(self, mock_ui, mock_st):
        """Test that render shows the correct section header."""
        # Fix columns unpacking
        mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        
        arete_architect.render()
        mock_ui.section_header.assert_called_once()
        args = mock_ui.section_header.call_args[0]
        assert "ARETE-Architect" in args[0]
    
    @patch("modules.arete_architect.st")
    @patch("modules.arete_architect.ui")
    @patch("modules.arete_architect.LANGGRAPH_AVAILABLE", False)
    def test_render_demo_mode_when_deps_missing(self, mock_ui, mock_st):
        """Test that render shows demo mode when LangGraph is missing."""
        # Fix columns unpacking
        mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        
        arete_architect.render()
        
        # Should show success message about demo mode
        mock_st.success.assert_called()
        success_msg = mock_st.success.call_args_list[0][0][0]
        assert "Demo Mode Active" in success_msg
        
        # Should show expanders for features
        assert mock_st.expander.call_count >= 5

    @patch("modules.arete_architect.st")
    @patch("modules.arete_architect.ui")
    def test_render_metrics_dashboard(self, mock_ui, mock_st):
        """Test that metrics dashboard renders correctly."""
        # Fix columns unpacking
        mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        
        with patch("modules.arete_architect.LANGGRAPH_AVAILABLE", False):
            arete_architect.render()
            
            # Check for animated metrics (we replaced st.metric with ui.animated_metric)
            assert mock_ui.animated_metric.call_count >= 10  # 4 in row 1, 6 in row 2
            
    @patch("modules.arete_architect.st")
    @patch("modules.arete_architect.ui")
    def test_render_roi_comparison(self, mock_ui, mock_st):
        """Test that ROI comparison renders correctly."""
        # Fix columns unpacking
        mock_st.columns.side_effect = lambda n: [MagicMock() for _ in range(n if isinstance(n, int) else len(n))]
        
        with patch("modules.arete_architect.LANGGRAPH_AVAILABLE", False):
            arete_architect.render()
            
            # Specific checks for ROI metrics
            calls = [args[0] for args, _ in mock_ui.animated_metric.call_args_list]
            assert "Time Savings" in calls
            assert "Cost Reduction" in calls
            assert "ROI Multiple" in calls

