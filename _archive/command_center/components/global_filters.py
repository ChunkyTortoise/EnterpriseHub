"""
Global Filters Component - Enterprise Command Center

Provides consistent filtering capabilities across all dashboard components:
- Date range selection
- Lead source filtering
- Geographic filters
- Quality score ranges
- Agent/team filtering

Designed to integrate seamlessly with the Predictive Insights Dashboard
and other command center components.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class FilterType(Enum):
    """Available filter types"""
    DATE_RANGE = "date_range"
    LEAD_SOURCE = "lead_source"
    GEOGRAPHIC = "geographic"
    QUALITY_RANGE = "quality_range"
    AGENT_TEAM = "agent_team"
    DEAL_STAGE = "deal_stage"

@dataclass
class FilterConfig:
    """Filter configuration"""
    filter_type: FilterType
    label: str
    options: Optional[List[str]] = None
    default_value: Any = None
    enabled: bool = True

class GlobalFilters:
    """
    Global filtering system for enterprise dashboards
    
    Features:
    - Consistent filter UI across components
    - Real-time filter synchronization
    - Filter state persistence
    - Advanced filter combinations
    """
    
    def __init__(self, key_prefix: str = "global"):
        self.key_prefix = key_prefix
        self.filters = self._initialize_filters()
        
        # Initialize session state
        if f'{key_prefix}_filters_applied' not in st.session_state:
            st.session_state[f'{key_prefix}_filters_applied'] = False
    
    def render_filters(self, layout: str = "horizontal", compact: bool = False) -> Dict[str, Any]:
        """
        Render filter controls
        
        Args:
            layout: 'horizontal', 'vertical', or 'sidebar'
            compact: Use compact styling
            
        Returns:
            Dictionary of current filter values
        """
        if compact:
            return self._render_compact_filters()
        elif layout == "sidebar":
            return self._render_sidebar_filters()
        elif layout == "vertical":
            return self._render_vertical_filters()
        else:
            return self._render_horizontal_filters()
    
    def _render_horizontal_filters(self) -> Dict[str, Any]:
        """Render filters in horizontal layout"""
        st.markdown("""
        <style>
        .filter-container {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            backdrop-filter: blur(10px);
        }
        
        .filter-header {
            font-family: 'Inter', sans-serif;
            font-size: 1.1rem;
            font-weight: 600;
            color: #f8fafc;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="filter-container">', unsafe_allow_html=True)
            st.markdown('<div class="filter-header">🔧 Global Filters</div>', unsafe_allow_html=True)
            
            # Create columns for filters
            cols = st.columns([2, 2, 1.5, 1.5, 2])
            
            filter_values = {}
            
            # Date Range Filter
            with cols[0]:
                filter_values['date_range'] = st.date_input(
                    "📅 Date Range",
                    value=(datetime.now() - timedelta(days=30), datetime.now()),
                    key=f"{self.key_prefix}_date_range",
                    help="Select date range for analysis"
                )
            
            # Lead Source Filter
            with cols[1]:
                source_options = ['All Sources', 'Google Ads', 'Facebook', 'Organic', 'Referral', 'Direct', 'Email']
                filter_values['lead_source'] = st.multiselect(
                    "📍 Lead Sources",
                    options=source_options[1:],  # Exclude 'All Sources' from options
                    default=source_options[1:],
                    key=f"{self.key_prefix}_lead_source",
                    help="Select lead sources to include"
                )
            
            # Geographic Filter
            with cols[2]:
                geo_options = ['All Regions', 'North', 'South', 'East', 'West', 'Central']
                filter_values['geographic'] = st.selectbox(
                    "🌍 Region",
                    options=geo_options,
                    key=f"{self.key_prefix}_geographic",
                    help="Geographic region filter"
                )
            
            # Quality Range Filter
            with cols[3]:
                filter_values['quality_range'] = st.slider(
                    "⭐ Quality Range",
                    min_value=0,
                    max_value=100,
                    value=(60, 100),
                    key=f"{self.key_prefix}_quality_range",
                    help="Lead quality score range"
                )
            
            # Agent/Team Filter
            with cols[4]:
                team_options = ['All Teams', 'Team Alpha', 'Team Beta', 'Team Gamma', 'Individual Agents']
                filter_values['agent_team'] = st.selectbox(
                    "👥 Team",
                    options=team_options,
                    key=f"{self.key_prefix}_agent_team",
                    help="Team or agent filter"
                )
            
            # Filter actions
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button("🔄 Apply Filters", key=f"{self.key_prefix}_apply", type="primary"):
                    st.session_state[f'{self.key_prefix}_filters_applied'] = True
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Reset", key=f"{self.key_prefix}_reset"):
                    self._reset_filters()
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            return filter_values
    
    def _render_compact_filters(self) -> Dict[str, Any]:
        """Render compact filter controls"""
        with st.expander("🔧 Filters", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            filter_values = {}
            
            with col1:
                # Quick date presets
                date_preset = st.selectbox(
                    "📅 Time Period",
                    ['Last 7 days', 'Last 30 days', 'Last 90 days', 'Custom'],
                    key=f"{self.key_prefix}_date_preset"
                )
                
                if date_preset == 'Custom':
                    filter_values['date_range'] = st.date_input(
                        "Custom Range",
                        value=(datetime.now() - timedelta(days=30), datetime.now()),
                        key=f"{self.key_prefix}_custom_date"
                    )
                else:
                    days_map = {'Last 7 days': 7, 'Last 30 days': 30, 'Last 90 days': 90}
                    days = days_map.get(date_preset, 30)
                    filter_values['date_range'] = (
                        datetime.now() - timedelta(days=days), 
                        datetime.now()
                    )
            
            with col2:
                # Source filter
                filter_values['lead_source'] = st.multiselect(
                    "📍 Sources",
                    ['Google Ads', 'Facebook', 'Organic', 'Referral'],
                    default=['Google Ads', 'Facebook'],
                    key=f"{self.key_prefix}_compact_source"
                )
            
            with col3:
                # Quality filter
                filter_values['quality_range'] = st.slider(
                    "⭐ Min Quality",
                    0, 100, 70,
                    key=f"{self.key_prefix}_compact_quality"
                )
        
        return filter_values
    
    def _render_sidebar_filters(self) -> Dict[str, Any]:
        """Render filters in sidebar"""
        with st.sidebar:
            st.markdown("### 🔧 Dashboard Filters")
            
            filter_values = {}
            
            # Date Range
            st.markdown("**📅 Time Period**")
            filter_values['date_range'] = st.date_input(
                "Select Date Range",
                value=(datetime.now() - timedelta(days=30), datetime.now()),
                key=f"{self.key_prefix}_sidebar_date"
            )
            
            st.divider()
            
            # Lead Sources
            st.markdown("**📍 Lead Sources**")
            filter_values['lead_source'] = st.multiselect(
                "Select Sources",
                ['Google Ads', 'Facebook', 'Organic', 'Referral', 'Direct', 'Email'],
                default=['Google Ads', 'Facebook', 'Organic'],
                key=f"{self.key_prefix}_sidebar_source"
            )
            
            st.divider()
            
            # Geographic
            st.markdown("**🌍 Geography**")
            filter_values['geographic'] = st.selectbox(
                "Region",
                ['All Regions', 'North', 'South', 'East', 'West', 'Central'],
                key=f"{self.key_prefix}_sidebar_geo"
            )
            
            # Quality Range
            st.markdown("**⭐ Quality Score**")
            filter_values['quality_range'] = st.slider(
                "Quality Range",
                0, 100, (60, 100),
                key=f"{self.key_prefix}_sidebar_quality"
            )
            
            st.divider()
            
            # Team/Agent
            st.markdown("**👥 Team**")
            filter_values['agent_team'] = st.selectbox(
                "Select Team",
                ['All Teams', 'Team Alpha', 'Team Beta', 'Team Gamma', 'Individual'],
                key=f"{self.key_prefix}_sidebar_team"
            )
            
            # Deal Stage
            st.markdown("**🎯 Deal Stage**")
            filter_values['deal_stage'] = st.multiselect(
                "Select Stages",
                ['New', 'Qualified', 'Proposal', 'Negotiation', 'Closing', 'Closed Won', 'Closed Lost'],
                default=['New', 'Qualified', 'Proposal', 'Negotiation'],
                key=f"{self.key_prefix}_sidebar_stage"
            )
            
            st.divider()
            
            # Actions
            if st.button("🔄 Apply All Filters", key=f"{self.key_prefix}_sidebar_apply"):
                st.session_state[f'{self.key_prefix}_filters_applied'] = True
                st.rerun()
            
            if st.button("🗑️ Reset All", key=f"{self.key_prefix}_sidebar_reset"):
                self._reset_filters()
                st.rerun()
        
        return filter_values
    
    def _render_vertical_filters(self) -> Dict[str, Any]:
        """Render filters in vertical layout"""
        filter_values = {}
        
        with st.container():
            st.markdown("### 🔧 Filters & Controls")
            
            # Date Range Section
            with st.expander("📅 Date & Time Filters", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    filter_values['date_range'] = st.date_input(
                        "Date Range",
                        value=(datetime.now() - timedelta(days=30), datetime.now()),
                        key=f"{self.key_prefix}_vert_date"
                    )
                with col2:
                    filter_values['time_of_day'] = st.select_slider(
                        "Time of Day",
                        options=['All Day', 'Morning', 'Afternoon', 'Evening'],
                        value='All Day',
                        key=f"{self.key_prefix}_vert_time"
                    )
            
            # Source & Channel Filters
            with st.expander("📍 Source & Channel Filters", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    filter_values['lead_source'] = st.multiselect(
                        "Lead Sources",
                        ['Google Ads', 'Facebook', 'Organic', 'Referral', 'Direct', 'Email'],
                        default=['Google Ads', 'Facebook', 'Organic'],
                        key=f"{self.key_prefix}_vert_source"
                    )
                with col2:
                    filter_values['campaign_type'] = st.selectbox(
                        "Campaign Type",
                        ['All Types', 'Search', 'Display', 'Social', 'Video', 'Email'],
                        key=f"{self.key_prefix}_vert_campaign"
                    )
            
            # Performance Filters
            with st.expander("⭐ Performance & Quality Filters", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    filter_values['quality_range'] = st.slider(
                        "Quality Score Range",
                        0, 100, (60, 100),
                        key=f"{self.key_prefix}_vert_quality"
                    )
                with col2:
                    filter_values['conversion_rate'] = st.slider(
                        "Min Conversion Rate (%)",
                        0.0, 50.0, 5.0,
                        key=f"{self.key_prefix}_vert_conversion"
                    )
        
        return filter_values
    
    def _initialize_filters(self) -> List[FilterConfig]:
        """Initialize available filter configurations"""
        return [
            FilterConfig(
                FilterType.DATE_RANGE,
                "Date Range",
                default_value=(datetime.now() - timedelta(days=30), datetime.now())
            ),
            FilterConfig(
                FilterType.LEAD_SOURCE,
                "Lead Sources",
                options=['Google Ads', 'Facebook', 'Organic', 'Referral', 'Direct', 'Email'],
                default_value=['Google Ads', 'Facebook', 'Organic']
            ),
            FilterConfig(
                FilterType.GEOGRAPHIC,
                "Geographic Region",
                options=['All Regions', 'North', 'South', 'East', 'West', 'Central'],
                default_value='All Regions'
            ),
            FilterConfig(
                FilterType.QUALITY_RANGE,
                "Quality Score Range",
                default_value=(60, 100)
            ),
            FilterConfig(
                FilterType.AGENT_TEAM,
                "Agent/Team",
                options=['All Teams', 'Team Alpha', 'Team Beta', 'Team Gamma'],
                default_value='All Teams'
            ),
            FilterConfig(
                FilterType.DEAL_STAGE,
                "Deal Stage",
                options=['New', 'Qualified', 'Proposal', 'Negotiation', 'Closing', 'Closed Won'],
                default_value=['New', 'Qualified', 'Proposal', 'Negotiation']
            )
        ]
    
    def _reset_filters(self):
        """Reset all filters to default values"""
        # Clear session state for all filter keys
        keys_to_clear = [
            key for key in st.session_state.keys() 
            if key.startswith(self.key_prefix)
        ]
        for key in keys_to_clear:
            del st.session_state[key]
        
        st.session_state[f'{self.key_prefix}_filters_applied'] = False
    
    def get_filter_query(self, filter_values: Dict[str, Any]) -> str:
        """
        Generate SQL-like query string from filter values
        
        Args:
            filter_values: Dictionary of filter values
            
        Returns:
            SQL WHERE clause string
        """
        conditions = []
        
        # Date range condition
        if 'date_range' in filter_values and filter_values['date_range']:
            if isinstance(filter_values['date_range'], tuple) and len(filter_values['date_range']) == 2:
                start_date, end_date = filter_values['date_range']
                conditions.append(f"date BETWEEN '{start_date}' AND '{end_date}'")
        
        # Lead source condition
        if 'lead_source' in filter_values and filter_values['lead_source']:
            sources = "', '".join(filter_values['lead_source'])
            conditions.append(f"lead_source IN ('{sources}')")
        
        # Geographic condition
        if 'geographic' in filter_values and filter_values['geographic'] != 'All Regions':
            conditions.append(f"region = '{filter_values['geographic']}'")
        
        # Quality range condition
        if 'quality_range' in filter_values and filter_values['quality_range']:
            if isinstance(filter_values['quality_range'], tuple):
                min_qual, max_qual = filter_values['quality_range']
                conditions.append(f"quality_score BETWEEN {min_qual} AND {max_qual}")
            else:
                conditions.append(f"quality_score >= {filter_values['quality_range']}")
        
        # Team condition
        if 'agent_team' in filter_values and filter_values['agent_team'] != 'All Teams':
            conditions.append(f"team = '{filter_values['agent_team']}'")
        
        # Deal stage condition
        if 'deal_stage' in filter_values and filter_values['deal_stage']:
            stages = "', '".join(filter_values['deal_stage'])
            conditions.append(f"deal_stage IN ('{stages}')")
        
        return " AND ".join(conditions) if conditions else "1=1"
    
    def filter_dataframe(self, df: pd.DataFrame, filter_values: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply filters to a pandas DataFrame
        
        Args:
            df: DataFrame to filter
            filter_values: Dictionary of filter values
            
        Returns:
            Filtered DataFrame
        """
        filtered_df = df.copy()
        
        # Date range filter
        if 'date_range' in filter_values and 'date' in filtered_df.columns:
            if isinstance(filter_values['date_range'], tuple) and len(filter_values['date_range']) == 2:
                start_date, end_date = filter_values['date_range']
                filtered_df = filtered_df[
                    (pd.to_datetime(filtered_df['date']).dt.date >= start_date) &
                    (pd.to_datetime(filtered_df['date']).dt.date <= end_date)
                ]
        
        # Lead source filter
        if 'lead_source' in filter_values and filter_values['lead_source'] and 'lead_source' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['lead_source'].isin(filter_values['lead_source'])]
        
        # Geographic filter
        if 'geographic' in filter_values and filter_values['geographic'] != 'All Regions' and 'region' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['region'] == filter_values['geographic']]
        
        # Quality range filter
        if 'quality_range' in filter_values and 'quality_score' in filtered_df.columns:
            if isinstance(filter_values['quality_range'], tuple):
                min_qual, max_qual = filter_values['quality_range']
                filtered_df = filtered_df[
                    (filtered_df['quality_score'] >= min_qual) &
                    (filtered_df['quality_score'] <= max_qual)
                ]
            else:
                filtered_df = filtered_df[filtered_df['quality_score'] >= filter_values['quality_range']]
        
        return filtered_df
    
    def export_filter_config(self, filter_values: Dict[str, Any]) -> Dict[str, Any]:
        """Export current filter configuration for sharing or saving"""
        return {
            'timestamp': datetime.now().isoformat(),
            'filters': filter_values,
            'key_prefix': self.key_prefix
        }
    
    def import_filter_config(self, config: Dict[str, Any]):
        """Import filter configuration from saved config"""
        if 'filters' in config:
            for key, value in config['filters'].items():
                st.session_state[f"{self.key_prefix}_{key}"] = value
            st.session_state[f'{self.key_prefix}_filters_applied'] = True


def create_global_filters(key_prefix: str = "global") -> GlobalFilters:
    """Factory function to create global filters instance"""
    return GlobalFilters(key_prefix=key_prefix)


# Standalone component testing
if __name__ == "__main__":
    st.title("🔧 Global Filters Test")
    
    filters = create_global_filters("test")
    filter_values = filters.render_filters(layout="horizontal")
    
    st.write("**Current Filter Values:**")
    st.json(filter_values)
    
    st.write("**Generated Query:**")
    st.code(filters.get_filter_query(filter_values), language="sql")