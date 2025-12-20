"""Unit tests for the marketing_analytics module's data integration."""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta
from modules import marketing_analytics
from utils.data_source_faker import generate_campaign_data # Import for actual data generation in tests

# Fixture for sample DataFrame matching generated data structure
@pytest.fixture
def sample_campaign_df():
    """Returns a sample DataFrame with expected campaign data columns."""
    return generate_campaign_data(platform="Google Ads", start_date="2023-01-01", days=10)

# --- Test _get_campaign_data_source ---
@patch('modules.marketing_analytics.st')
@patch('modules.marketing_analytics.pd')
def test_get_campaign_data_source_upload_csv(mock_pd, mock_st):
    """Test _get_campaign_data_source when 'Upload CSV/Excel' is selected and CSV is uploaded."""
    mock_st.radio.return_value = "Upload CSV/Excel"
    mock_uploaded_file = MagicMock()
    mock_uploaded_file.name = "test.csv"
    mock_uploaded_file.endswith.return_value = True # For .csv
    mock_uploaded_file.read.return_value = b"Date,Impressions\n2023-01-01,100"
    mock_pd.read_csv.return_value = pd.DataFrame({'Date': [datetime(2023,1,1)], 'Impressions': [100]})
    mock_pd.to_datetime.return_value = pd.Series([datetime(2023,1,1)])

    df = marketing_analytics._get_campaign_data_source()

    mock_st.radio.assert_called_once()
    mock_st.file_uploader.assert_called_once()
    mock_pd.read_csv.assert_called_once()
    assert not df.empty
    assert 'Date' in df.columns
    assert 'Impressions' in df.columns

@patch('modules.marketing_analytics.st')
@patch('modules.marketing_analytics.pd')
def test_get_campaign_data_source_upload_excel(mock_pd, mock_st):
    """Test _get_campaign_data_source when 'Upload CSV/Excel' is selected and Excel is uploaded."""
    mock_st.radio.return_value = "Upload CSV/Excel"
    mock_uploaded_file = MagicMock()
    mock_uploaded_file.name = "test.xlsx"
    mock_uploaded_file.endswith.side_effect = lambda x: x == '.xlsx' # For .xlsx
    mock_st.file_uploader.return_value = mock_uploaded_file

    mock_pd.read_excel.return_value = pd.DataFrame({'Date': [datetime(2023,1,1)], 'Clicks': [50]})
    mock_pd.to_datetime.return_value = pd.Series([datetime(2023,1,1)])

    df = marketing_analytics._get_campaign_data_source()

    mock_st.radio.assert_called_once()
    mock_st.file_uploader.assert_called_once()
    mock_pd.read_excel.assert_called_once()
    assert not df.empty
    assert 'Date' in df.columns
    assert 'Clicks' in df.columns

@patch('modules.marketing_analytics.st')
def test_get_campaign_data_source_simulate_new_data(mock_st):
    """Test _get_campaign_data_source when 'Simulate Marketing Data' is selected and new data is generated."""
    mock_st.radio.return_value = "Simulate Marketing Data"
    mock_st.selectbox.return_value = "Google Ads" # Return actual string
    mock_st.date_input.return_value = datetime(2023, 1, 1) # Return datetime object
    mock_st.slider.return_value = 5
    mock_st.button.return_value = True # Simulate button click
    
    # Configure mock_st.columns for this test
    mock_st.columns.return_value = [MagicMock(), MagicMock()]
    
    # Mock session state as a dictionary
    mock_st.session_state = {}

    df = marketing_analytics._get_campaign_data_source()

    mock_st.radio.assert_called_once()
    mock_st.selectbox.assert_called_once()
    mock_st.date_input.assert_called_once()
    mock_st.slider.assert_called_once()
    mock_st.button.assert_called_once()
    assert not df.empty
    assert 'simulated_campaign_data' in mock_st.session_state
    assert len(df) == 5 # 5 days of data

    mock_st.radio.assert_called_once()
    mock_st.selectbox.assert_called_once()
    mock_st.date_input.assert_called_once()
    mock_st.slider.assert_called_once()
    mock_st.button.assert_called_once()
    assert not df.empty
    assert 'simulated_campaign_data' in mock_st.session_state
    assert len(df) == 5 # 5 days of data

@patch('modules.marketing_analytics.st')
def test_get_campaign_data_source_simulate_existing_data(mock_st):
    """Test _get_campaign_data_source when 'Simulate Marketing Data' is selected and existing data is used."""
    mock_st.radio.return_value = "Simulate Marketing Data"
    # Pre-populate session state
    mock_st.session_state = {'simulated_campaign_data': generate_campaign_data(platform="Meta Ads", days=3)}
    
    # Configure mock_st.columns for this test
    mock_st.columns.return_value = [MagicMock(), MagicMock()]

    df = marketing_analytics._get_campaign_data_source()

    mock_st.radio.assert_called_once()
    # No calls to selectbox, date_input, slider, button if existing data is used
    mock_st.selectbox.assert_not_called()
    mock_st.button.assert_not_called()
    assert not df.empty
    assert len(df) == 3
    assert df['Platform'].iloc[0] == "Meta Ads"


# --- Test _render_campaign_dashboard ---
@patch('modules.marketing_analytics.st')
@patch('modules.marketing_analytics.ui')
@patch('modules.marketing_analytics._get_campaign_data_source')
@patch('modules.marketing_analytics._calculate_channel_metrics') # Patch the helper function
def test_render_campaign_dashboard_with_data(mock_calc_metrics, mock_get_data_source, mock_ui, mock_st, sample_campaign_df):
    """Test _render_campaign_dashboard renders correctly when data is available."""
    mock_get_data_source.return_value = sample_campaign_df
    mock_st.selectbox.return_value = "All Platforms" # Mock platform filter
    mock_st.date_input.side_effect = [sample_campaign_df['Date'].min(), sample_campaign_df['Date'].max()] # Mock date filters

    # Mock _calculate_channel_metrics to return a plausible dict
    mock_calc_metrics.return_value = {
        'spend': 10000, 'revenue': 30000, 'roi': 3.0, 'conversions': 500,
        'spend_change': 10, 'revenue_change': 15, 'roi_change': 5, 'conversion_change': 8
    }

    # Mock st.columns
    mock_st.columns.side_effect = lambda num_cols: [MagicMock() for _ in range(num_cols)]

    # Mock the Plotly figure methods that are called
    mock_st.plotly_chart.return_value = None

    marketing_analytics._render_campaign_dashboard()

    mock_get_data_source.assert_called_once()
    mock_st.subheader.assert_any_call("📈 Campaign Performance Dashboard")
    mock_st.selectbox.assert_called_once()
    mock_st.date_input.assert_called() # Twice for start and end
    mock_ui.card_metric.assert_called() # Should be called multiple times
    mock_st.plotly_chart.assert_called() # Should be called for trends and breakdown



@patch('modules.marketing_analytics.st')
@patch('modules.marketing_analytics.ui')
@patch('modules.marketing_analytics._get_campaign_data_source')
def test_render_campaign_dashboard_no_data(mock_get_data_source, mock_ui, mock_st):
    """Test _render_campaign_dashboard shows warning when no data is available."""
    mock_get_data_source.return_value = pd.DataFrame() # Return empty DataFrame
    
    marketing_analytics._render_campaign_dashboard()
    
    mock_get_data_source.assert_called_once()
    mock_st.warning.assert_called_once_with("Please provide or generate campaign data to continue.")
    mock_st.subheader.assert_called_once_with("📈 Campaign Performance Dashboard") # Subheader still renders

# --- Test _calculate_channel_metrics ---
def test_calculate_channel_metrics(sample_campaign_df):
    """Test _calculate_channel_metrics calculates correct values."""
    metrics = marketing_analytics._calculate_channel_metrics(sample_campaign_df)
    
    assert isinstance(metrics, dict)
    assert 'spend' in metrics
    assert 'revenue' in metrics
    assert 'roi' in metrics
    assert 'conversions' in metrics
    
    # Verify calculation logic (sum of sample data)
    assert metrics['spend'] == sample_campaign_df['Spend'].sum()
    assert metrics['revenue'] == sample_campaign_df['Revenue'].sum()
    assert metrics['conversions'] == sample_campaign_df['Conversions'].sum()
    
    expected_roi = (sample_campaign_df['Revenue'].sum() - sample_campaign_df['Spend'].sum()) / sample_campaign_df['Spend'].sum()
    assert metrics['roi'] == pytest.approx(expected_roi)

# --- Test _get_channel_breakdown ---
def test_get_channel_breakdown(sample_campaign_df):
    """Test _get_channel_breakdown correctly groups data by platform."""
    breakdown_df = marketing_analytics._get_channel_breakdown(sample_campaign_df)
    
    assert isinstance(breakdown_df, pd.DataFrame)
    assert 'channel' in breakdown_df.columns
    assert 'spend' in breakdown_df.columns
    assert 'revenue' in breakdown_df.columns
    assert 'conversions' in breakdown_df.columns
    
    # Verify grouping
    assert len(breakdown_df) == sample_campaign_df['Platform'].nunique()
    platform_spend = sample_campaign_df.groupby('Platform')['Spend'].sum().reset_index()
    assert breakdown_df['spend'].sum() == platform_spend['Spend'].sum()
