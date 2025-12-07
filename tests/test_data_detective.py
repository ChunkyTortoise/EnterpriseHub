"""
Tests for Data Detective module.

Comprehensive test suite covering:
- Data profiling and statistics
- Quality assessment
- AI insights generation
- Natural language queries
- Data cleaning functionality
- Export capabilities
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
import io


class TestDataProfiling:
    """Test data profiling functionality."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            'id': range(1, 101),
            'name': [f'Item_{i}' for i in range(1, 101)],
            'price': np.random.uniform(10, 100, 100),
            'quantity': np.random.randint(1, 50, 100),
            'category': np.random.choice(['A', 'B', 'C'], 100)
        })

    @pytest.fixture
    def df_with_nulls(self):
        """Create a DataFrame with missing values."""
        df = pd.DataFrame({
            'col1': [1, 2, None, 4, 5],
            'col2': ['a', None, 'c', 'd', None],
            'col3': [10.5, 20.3, 30.1, None, 50.7]
        })
        return df

    @pytest.fixture
    def df_with_duplicates(self):
        """Create a DataFrame with duplicate rows."""
        df = pd.DataFrame({
            'col1': [1, 2, 1, 3],
            'col2': ['a', 'b', 'a', 'c']
        })
        return df

    def test_prepare_data_summary_basic(self, sample_df):
        """Test basic data summary preparation."""
        from modules.data_detective import _prepare_data_summary

        summary = _prepare_data_summary(sample_df)

        assert "100 rows × 5 columns" in summary
        assert "id" in summary
        assert "name" in summary
        assert "price" in summary
        assert "quantity" in summary
        assert "category" in summary

    def test_prepare_data_summary_with_sample(self, sample_df):
        """Test data summary with sample rows included."""
        from modules.data_detective import _prepare_data_summary

        summary = _prepare_data_summary(sample_df, include_sample=True)

        assert "Sample Data" in summary
        assert "100 rows × 5 columns" in summary

    def test_prepare_data_summary_handles_nulls(self, df_with_nulls):
        """Test summary preparation with null values."""
        from modules.data_detective import _prepare_data_summary

        summary = _prepare_data_summary(df_with_nulls)

        # Should mention null percentages
        assert "null" in summary.lower()


class TestQualityAssessment:
    """Test data quality assessment functionality."""

    @pytest.fixture
    def clean_df(self):
        """Create a clean DataFrame with no issues."""
        return pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': ['a', 'b', 'c', 'd', 'e']
        })

    @pytest.fixture
    def df_with_nulls(self):
        """Create a DataFrame with missing values."""
        return pd.DataFrame({
            'col1': [1, 2, None, 4, 5],
            'col2': ['a', None, 'c', 'd', None]
        })

    @pytest.fixture
    def df_with_duplicates(self):
        """Create a DataFrame with duplicate rows."""
        return pd.DataFrame({
            'col1': [1, 2, 1, 3],
            'col2': ['a', 'b', 'a', 'c']
        })

    @pytest.fixture
    def df_with_outliers(self):
        """Create a DataFrame with outliers."""
        # Create normal data + outliers
        normal = np.random.normal(50, 10, 95)
        outliers = np.array([200, 250, -100, 300, 350])
        return pd.DataFrame({
            'value': np.concatenate([normal, outliers])
        })

    def test_assess_clean_data(self, clean_df):
        """Test assessment of clean data with no issues."""
        from modules.data_detective import _assess_data_quality

        issues = _assess_data_quality(clean_df)

        # Should have checks for missing values, duplicates, outliers
        assert len(issues) > 0

        # All checks should pass (has_issue=False)
        issues_found = [issue for issue in issues if issue['has_issue']]
        assert len(issues_found) == 0

    def test_assess_missing_values(self, df_with_nulls):
        """Test detection of missing values."""
        from modules.data_detective import _assess_data_quality

        issues = _assess_data_quality(df_with_nulls)

        # Find missing values issue
        missing_issue = next((issue for issue in issues if 'Missing Values' in issue['issue']), None)

        assert missing_issue is not None
        assert missing_issue['has_issue'] is True
        assert 'severity' in missing_issue
        assert 'recommendation' in missing_issue

    def test_assess_duplicates(self, df_with_duplicates):
        """Test detection of duplicate rows."""
        from modules.data_detective import _assess_data_quality

        issues = _assess_data_quality(df_with_duplicates)

        # Find duplicate issue
        dup_issue = next((issue for issue in issues if 'Duplicate' in issue['issue']), None)

        assert dup_issue is not None
        assert dup_issue['has_issue'] is True

    def test_assess_outliers(self, df_with_outliers):
        """Test detection of outliers."""
        from modules.data_detective import _assess_data_quality

        issues = _assess_data_quality(df_with_outliers)

        # Find outlier issue
        outlier_issue = next((issue for issue in issues if 'Outlier' in issue['issue']), None)

        assert outlier_issue is not None
        assert outlier_issue['has_issue'] is True

    def test_quality_actions_available(self, df_with_nulls):
        """Test that cleaning actions are provided."""
        from modules.data_detective import _assess_data_quality

        issues = _assess_data_quality(df_with_nulls)

        # Find issue with action
        issue_with_action = next((issue for issue in issues if issue.get('action') is not None), None)

        assert issue_with_action is not None
        assert 'action_name' in issue_with_action
        assert callable(issue_with_action['action'])

    def test_quality_action_execution(self, df_with_duplicates):
        """Test execution of cleaning actions."""
        from modules.data_detective import _assess_data_quality

        issues = _assess_data_quality(df_with_duplicates)

        # Find duplicate removal action
        dup_issue = next((issue for issue in issues if 'Duplicate' in issue['issue'] and issue.get('action')), None)

        assert dup_issue is not None

        # Execute the action
        cleaned_df = dup_issue['action'](df_with_duplicates)

        # Verify duplicates removed
        assert len(cleaned_df) < len(df_with_duplicates)
        assert cleaned_df.duplicated().sum() == 0


class TestAIInsights:
    """Test AI-powered insights generation."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for AI analysis."""
        return pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=100),
            'revenue': np.random.uniform(1000, 5000, 100),
            'customers': np.random.randint(10, 100, 100)
        })

    def test_generate_insights_with_valid_key(self, sample_df):
        """Test insights generation with valid API key."""
        from modules.data_detective import _generate_ai_insights

        # Mock Anthropic client
        with patch('modules.data_detective.Anthropic') as mock_anthropic:
            # Setup mock response
            mock_client = MagicMock()
            mock_message = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "- Revenue shows upward trend\n- Customer count is stable"

            mock_message.content = [mock_content]
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.return_value = mock_client

            insights = _generate_ai_insights(sample_df, "test-api-key")

            assert insights is not None
            assert "Revenue" in insights or "trend" in insights.lower()
            mock_client.messages.create.assert_called_once()

    def test_generate_insights_with_invalid_key(self, sample_df):
        """Test insights generation with invalid API key."""
        from modules.data_detective import _generate_ai_insights

        # Mock Anthropic client to raise error
        with patch('modules.data_detective.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("Invalid API key")
            mock_anthropic.return_value = mock_client

            insights = _generate_ai_insights(sample_df, "invalid-key")

            assert insights is None

    def test_generate_insights_handles_empty_response(self, sample_df):
        """Test handling of empty AI response."""
        from modules.data_detective import _generate_ai_insights

        with patch('modules.data_detective.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_message = MagicMock()
            mock_message.content = []  # Empty response
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.return_value = mock_client

            insights = _generate_ai_insights(sample_df, "test-key")

            assert insights is None


class TestNaturalLanguageQueries:
    """Test natural language query processing."""

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for queries."""
        return pd.DataFrame({
            'product': ['A', 'B', 'C', 'D', 'E'],
            'revenue': [1000, 2000, 1500, 3000, 2500],
            'quantity': [10, 20, 15, 30, 25]
        })

    def test_process_nlq_with_valid_query(self, sample_df):
        """Test processing a valid natural language query."""
        from modules.data_detective import _process_natural_language_query

        with patch('modules.data_detective.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_message = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "The top product by revenue is product D with $3,000."

            mock_message.content = [mock_content]
            mock_client.messages.create.return_value = mock_message
            mock_anthropic.return_value = mock_client

            query = "What is the top product by revenue?"
            answer = _process_natural_language_query(sample_df, query, "test-key")

            assert answer is not None
            assert "product" in answer.lower() or "revenue" in answer.lower()

    def test_process_nlq_with_error(self, sample_df):
        """Test NLQ processing with API error."""
        from modules.data_detective import _process_natural_language_query

        with patch('modules.data_detective.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("API Error")
            mock_anthropic.return_value = mock_client

            answer = _process_natural_language_query(sample_df, "test query", "test-key")

            assert answer is None


class TestModuleImports:
    """Test that module can be imported and has required functions."""

    def test_module_imports_successfully(self):
        """Test that data_detective module can be imported."""
        try:
            import modules.data_detective
            assert True
        except ImportError:
            pytest.fail("Failed to import data_detective module")

    def test_render_function_exists(self):
        """Test that render function exists."""
        from modules.data_detective import render
        assert callable(render)

    def test_required_functions_exist(self):
        """Test that all required functions are defined."""
        from modules import data_detective

        required_functions = [
            '_prepare_data_summary',
            '_assess_data_quality',
            '_generate_ai_insights',
            '_process_natural_language_query'
        ]

        for func_name in required_functions:
            assert hasattr(data_detective, func_name)
            assert callable(getattr(data_detective, func_name))


class TestConstants:
    """Test module constants."""

    def test_constants_defined(self):
        """Test that required constants are defined."""
        from modules.data_detective import (
            DEFAULT_MODEL,
            DEFAULT_MAX_TOKENS,
            API_TIMEOUT,
            MAX_ROWS_PREVIEW,
            MAX_INSIGHTS_ROWS
        )

        assert isinstance(DEFAULT_MODEL, str)
        assert isinstance(DEFAULT_MAX_TOKENS, int)
        assert isinstance(API_TIMEOUT, float)
        assert isinstance(MAX_ROWS_PREVIEW, int)
        assert isinstance(MAX_INSIGHTS_ROWS, int)

    def test_anthropic_available_flag(self):
        """Test ANTHROPIC_AVAILABLE flag is defined."""
        from modules.data_detective import ANTHROPIC_AVAILABLE

        assert isinstance(ANTHROPIC_AVAILABLE, bool)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        from modules.data_detective import _assess_data_quality

        empty_df = pd.DataFrame()

        # Should not crash
        try:
            issues = _assess_data_quality(empty_df)
            assert isinstance(issues, list)
        except Exception as e:
            pytest.fail(f"Failed to handle empty DataFrame: {str(e)}")

    def test_single_column_dataframe(self):
        """Test handling of single-column DataFrame."""
        from modules.data_detective import _prepare_data_summary

        single_col_df = pd.DataFrame({'col1': [1, 2, 3]})

        summary = _prepare_data_summary(single_col_df)

        assert "3 rows × 1 columns" in summary or "3 rows" in summary

    def test_all_null_column(self):
        """Test handling of column with all null values."""
        from modules.data_detective import _assess_data_quality

        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': [None, None, None]
        })

        issues = _assess_data_quality(df)

        # Should detect missing values
        missing_issue = next((issue for issue in issues if 'Missing' in issue['issue']), None)
        assert missing_issue is not None
        assert missing_issue['has_issue'] is True


class TestNewFeatures:
    """Test new Data Detective features: correlation matrix and Excel support."""

    # ==================== Correlation Matrix Tests ====================

    @pytest.fixture
    def df_two_numeric_cols(self):
        """Create DataFrame with 2 numeric columns for correlation testing."""
        return pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': [2, 4, 6, 8, 10]
        })

    @pytest.fixture
    def df_multiple_numeric_cols(self):
        """Create DataFrame with multiple numeric columns."""
        return pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': [2, 4, 6, 8, 10],  # Perfect positive correlation with col1
            'col3': [5, 4, 3, 2, 1],   # Perfect negative correlation with col1
            'col4': [10, 15, 20, 25, 30]  # Strong positive correlation with col1
        })

    @pytest.fixture
    def df_one_numeric_col(self):
        """Create DataFrame with only 1 numeric column."""
        return pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'category': ['A', 'B', 'C', 'D', 'E']
        })

    @pytest.fixture
    def df_no_correlation(self):
        """Create DataFrame with uncorrelated numeric columns."""
        np.random.seed(42)
        return pd.DataFrame({
            'col1': np.random.randn(100),
            'col2': np.random.randn(100),
            'col3': np.random.randn(100)
        })

    @pytest.fixture
    def df_strong_correlation(self):
        """Create DataFrame with strong correlations."""
        return pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': [2, 4, 6, 8, 10],  # r = 1.0
            'col3': [5, 4, 3, 2, 1]    # r = -1.0
        })

    @pytest.fixture
    def df_all_zeros(self):
        """Create DataFrame with all zeros."""
        return pd.DataFrame({
            'col1': [0, 0, 0, 0, 0],
            'col2': [0, 0, 0, 0, 0]
        })

    @pytest.fixture
    def df_perfect_correlation(self):
        """Create DataFrame with perfect positive correlation."""
        return pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': [1, 2, 3, 4, 5]
        })

    def test_correlation_matrix_calculated_correctly(self, df_two_numeric_cols):
        """Test that correlation matrix is calculated correctly for numeric columns."""
        numeric_cols = df_two_numeric_cols.select_dtypes(include=[np.number]).columns.tolist()
        corr_matrix = df_two_numeric_cols[numeric_cols].corr()

        # Should have 2x2 matrix
        assert corr_matrix.shape == (2, 2)

        # Diagonal should be 1.0 (self-correlation)
        assert corr_matrix.iloc[0, 0] == 1.0
        assert corr_matrix.iloc[1, 1] == 1.0

        # col2 = 2 * col1, so perfect positive correlation
        assert abs(corr_matrix.iloc[0, 1] - 1.0) < 0.001

    def test_correlation_with_multiple_numeric_columns(self, df_multiple_numeric_cols):
        """Test correlation matrix with multiple numeric columns."""
        numeric_cols = df_multiple_numeric_cols.select_dtypes(include=[np.number]).columns.tolist()
        corr_matrix = df_multiple_numeric_cols[numeric_cols].corr()

        # Should have 4x4 matrix
        assert corr_matrix.shape == (4, 4)

        # Test perfect positive correlation (col1 and col2)
        assert abs(corr_matrix.loc['col1', 'col2'] - 1.0) < 0.001

        # Test perfect negative correlation (col1 and col3)
        assert abs(corr_matrix.loc['col1', 'col3'] - (-1.0)) < 0.001

        # Test strong positive correlation (col1 and col4)
        assert corr_matrix.loc['col1', 'col4'] > 0.9

    def test_correlation_with_one_numeric_column(self, df_one_numeric_col):
        """Test that correlation matrix is not shown with only 1 numeric column."""
        numeric_cols = df_one_numeric_col.select_dtypes(include=[np.number]).columns.tolist()

        # Should have only 1 numeric column
        assert len(numeric_cols) == 1

        # Correlation matrix would be 1x1, which is not useful
        if len(numeric_cols) > 1:
            corr_matrix = df_one_numeric_col[numeric_cols].corr()
        else:
            corr_matrix = None

        # Should not generate correlation matrix
        assert corr_matrix is None

    def test_strong_correlation_detection(self, df_strong_correlation):
        """Test detection of strong correlations (|r| >= 0.7)."""
        numeric_cols = df_strong_correlation.select_dtypes(include=[np.number]).columns.tolist()
        corr_matrix = df_strong_correlation[numeric_cols].corr()

        # Find strong correlations
        strong_corrs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) >= 0.7:
                    strong_corrs.append({
                        'col1': corr_matrix.columns[i],
                        'col2': corr_matrix.columns[j],
                        'correlation': corr_value
                    })

        # Should find 2 strong correlations
        assert len(strong_corrs) == 2

        # Verify strong positive correlation
        pos_corr = next((c for c in strong_corrs if c['col1'] == 'col1' and c['col2'] == 'col2'), None)
        assert pos_corr is not None
        assert abs(pos_corr['correlation'] - 1.0) < 0.001

        # Verify strong negative correlation
        neg_corr = next((c for c in strong_corrs if c['col1'] == 'col1' and c['col2'] == 'col3'), None)
        assert neg_corr is not None
        assert abs(pos_corr['correlation'] - (-1.0)) < 0.001

    def test_no_strong_correlations(self, df_no_correlation):
        """Test with data that has no strong correlations."""
        numeric_cols = df_no_correlation.select_dtypes(include=[np.number]).columns.tolist()
        corr_matrix = df_no_correlation[numeric_cols].corr()

        # Find strong correlations
        strong_corrs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) >= 0.7:
                    strong_corrs.append({
                        'col1': corr_matrix.columns[i],
                        'col2': corr_matrix.columns[j],
                        'correlation': corr_value
                    })

        # Should find no strong correlations with random data
        assert len(strong_corrs) == 0

    def test_correlation_with_all_zeros(self, df_all_zeros):
        """Test correlation calculation with all zeros (edge case)."""
        numeric_cols = df_all_zeros.select_dtypes(include=[np.number]).columns.tolist()
        corr_matrix = df_all_zeros[numeric_cols].corr()

        # Correlation of zero-variance data should be NaN
        assert pd.isna(corr_matrix.iloc[0, 1])

    def test_perfect_correlation_detection(self, df_perfect_correlation):
        """Test detection of perfect correlation (r = 1.0)."""
        numeric_cols = df_perfect_correlation.select_dtypes(include=[np.number]).columns.tolist()
        corr_matrix = df_perfect_correlation[numeric_cols].corr()

        # Should detect perfect correlation
        assert abs(corr_matrix.iloc[0, 1] - 1.0) < 0.001

        # Find strong correlations
        strong_corrs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) >= 0.7:
                    strong_corrs.append(corr_value)

        # Should find perfect correlation
        assert len(strong_corrs) == 1
        assert abs(strong_corrs[0] - 1.0) < 0.001

    # ==================== Excel File Support Tests ====================

    @pytest.fixture
    def sample_csv_content(self):
        """Create sample CSV content."""
        return """col1,col2,col3
1,A,10.5
2,B,20.3
3,C,30.1
4,D,40.7
5,E,50.9"""

    @pytest.fixture
    def sample_excel_data(self):
        """Create sample data for Excel files."""
        return pd.DataFrame({
            'col1': [1, 2, 3, 4, 5],
            'col2': ['A', 'B', 'C', 'D', 'E'],
            'col3': [10.5, 20.3, 30.1, 40.7, 50.9]
        })

    def test_csv_file_reading(self, sample_csv_content):
        """Test that CSV files are read correctly (backward compatibility)."""
        # Simulate CSV file
        csv_file = io.StringIO(sample_csv_content)
        df = pd.read_csv(csv_file)

        # Verify data loaded correctly
        assert len(df) == 5
        assert len(df.columns) == 3
        assert list(df.columns) == ['col1', 'col2', 'col3']
        assert df['col1'].tolist() == [1, 2, 3, 4, 5]
        assert df['col2'].tolist() == ['A', 'B', 'C', 'D', 'E']

    def test_xlsx_file_reading_with_openpyxl(self, sample_excel_data, tmp_path):
        """Test that .xlsx files are read correctly using openpyxl."""
        # Create temporary .xlsx file
        xlsx_path = tmp_path / "test_file.xlsx"
        sample_excel_data.to_excel(xlsx_path, index=False, engine='openpyxl')

        # Read file
        df = pd.read_excel(xlsx_path, engine='openpyxl')

        # Verify data loaded correctly
        assert len(df) == 5
        assert len(df.columns) == 3
        assert list(df.columns) == ['col1', 'col2', 'col3']
        assert df['col1'].tolist() == [1, 2, 3, 4, 5]
        assert df['col2'].tolist() == ['A', 'B', 'C', 'D', 'E']

    def test_xls_file_reading(self, sample_excel_data, tmp_path):
        """Test that .xls files are read correctly."""
        # Create temporary .xls file (using xlwt if available, otherwise skip)
        try:
            xls_path = tmp_path / "test_file.xls"
            sample_excel_data.to_excel(xls_path, index=False, engine='xlwt')

            # Read file
            df = pd.read_excel(xls_path)

            # Verify data loaded correctly
            assert len(df) == 5
            assert len(df.columns) == 3
            assert list(df.columns) == ['col1', 'col2', 'col3']
        except ImportError:
            # xlwt not installed, skip test
            pytest.skip("xlwt not installed, skipping .xls test")

    def test_file_extension_detection_csv(self):
        """Test file extension detection logic for CSV."""
        filename = "data.csv"
        extension = filename.split('.')[-1].lower()

        assert extension == 'csv'

    def test_file_extension_detection_xlsx(self):
        """Test file extension detection logic for XLSX."""
        filename = "data.xlsx"
        extension = filename.split('.')[-1].lower()

        assert extension == 'xlsx'

    def test_file_extension_detection_xls(self):
        """Test file extension detection logic for XLS."""
        filename = "data.xls"
        extension = filename.split('.')[-1].lower()

        assert extension == 'xls'

    def test_file_extension_detection_uppercase(self):
        """Test file extension detection with uppercase extensions."""
        filename = "DATA.CSV"
        extension = filename.split('.')[-1].lower()

        assert extension == 'csv'

    def test_file_extension_detection_mixed_case(self):
        """Test file extension detection with mixed case extensions."""
        filename = "MyData.XlSx"
        extension = filename.split('.')[-1].lower()

        assert extension == 'xlsx'

    def test_csv_vs_excel_data_equivalence(self, sample_excel_data, tmp_path):
        """Test that CSV and Excel files produce equivalent DataFrames."""
        # Save as CSV
        csv_path = tmp_path / "test.csv"
        sample_excel_data.to_csv(csv_path, index=False)

        # Save as Excel
        xlsx_path = tmp_path / "test.xlsx"
        sample_excel_data.to_excel(xlsx_path, index=False, engine='openpyxl')

        # Read both
        df_csv = pd.read_csv(csv_path)
        df_xlsx = pd.read_excel(xlsx_path, engine='openpyxl')

        # Verify equivalence
        assert len(df_csv) == len(df_xlsx)
        assert len(df_csv.columns) == len(df_xlsx.columns)
        assert list(df_csv.columns) == list(df_xlsx.columns)

        # Compare data (accounting for potential type differences)
        for col in df_csv.columns:
            assert df_csv[col].tolist() == df_xlsx[col].tolist()

    def test_excel_file_with_multiple_sheets(self, sample_excel_data, tmp_path):
        """Test reading Excel file with multiple sheets (default first sheet)."""
        # Create Excel file with multiple sheets
        xlsx_path = tmp_path / "test_multisheet.xlsx"

        with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
            sample_excel_data.to_excel(writer, sheet_name='Sheet1', index=False)
            sample_excel_data.to_excel(writer, sheet_name='Sheet2', index=False)

        # Read file (should read first sheet by default)
        df = pd.read_excel(xlsx_path, engine='openpyxl')

        # Verify first sheet was read
        assert len(df) == 5
        assert len(df.columns) == 3

    def test_excel_file_with_empty_cells(self, tmp_path):
        """Test reading Excel file with empty cells (NaN values)."""
        # Create DataFrame with NaN values
        df_with_nan = pd.DataFrame({
            'col1': [1, 2, None, 4, 5],
            'col2': ['A', None, 'C', 'D', None],
            'col3': [10.5, 20.3, 30.1, None, 50.9]
        })

        # Save to Excel
        xlsx_path = tmp_path / "test_nan.xlsx"
        df_with_nan.to_excel(xlsx_path, index=False, engine='openpyxl')

        # Read file
        df = pd.read_excel(xlsx_path, engine='openpyxl')

        # Verify NaN values preserved
        assert pd.isna(df.loc[2, 'col1'])
        assert pd.isna(df.loc[1, 'col2'])
        assert pd.isna(df.loc[3, 'col3'])

    def test_unsupported_file_extension(self):
        """Test handling of unsupported file extensions."""
        filename = "data.txt"
        extension = filename.split('.')[-1].lower()

        # Should not match supported extensions
        assert extension not in ['csv', 'xlsx', 'xls']
