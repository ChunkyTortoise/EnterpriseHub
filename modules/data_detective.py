"""
Data Detective - AI-Powered Data Analysis and Insights.

Upload CSV files and get automated data profiling, AI-generated insights,
data quality assessment, and intelligent cleaning recommendations.
"""

import io
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import utils.ui as ui
from utils.logger import get_logger

# Conditional import for Claude API
try:
    from anthropic import (
        Anthropic,
        APIConnectionError,
        APIError,
        APITimeoutError,
        RateLimitError,
    )

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = get_logger(__name__)

# Constants
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
DEFAULT_MAX_TOKENS = 2048
API_TIMEOUT = 30.0
MAX_ROWS_PREVIEW = 1000
MAX_INSIGHTS_ROWS = 10000  # Max rows to analyze for insights


def render() -> None:
    """Main render function for Data Detective module."""
    ui.section_header("Data Detective", "AI-Powered Data Analysis & Insights")
    st.markdown(
        """
    Upload any CSV file and get instant AI-powered insights, data quality assessment,
    and intelligent cleaning recommendations. Perfect for exploratory data analysis!
    """
    )

    # Initialize session state
    if "uploaded_data" not in st.session_state:
        st.session_state.uploaded_data = None
    if "cleaned_data" not in st.session_state:
        st.session_state.cleaned_data = None

    # File upload section
    st.markdown("---")
    st.subheader("📤 Upload Your Data")

    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        help="Upload a CSV or Excel file to analyze. Maximum recommended size: 50MB",
    )

    if uploaded_file is not None:
        try:
            # Read the file based on extension
            file_extension = uploaded_file.name.split(".")[-1].lower()

            if file_extension == "csv":
                df = pd.read_csv(uploaded_file)
            elif file_extension in ["xlsx", "xls"]:
                df = pd.read_excel(
                    uploaded_file,
                    engine="openpyxl" if file_extension == "xlsx" else None,
                )
            else:
                st.error(f"❌ Unsupported file type: {file_extension}")
                return

            st.session_state.uploaded_data = df
            st.success(
                f"✅ Loaded {len(df):,} rows and {len(df.columns)} columns from {file_extension.upper()} file"
            )

            # Create tabs for different analysis sections
            tabs = st.tabs(
                [
                    "📊 Data Profile",
                    "🤖 AI Insights",
                    "🧹 Data Quality",
                    "💬 Ask Questions",
                    "📥 Export",
                ]
            )

            with tabs[0]:
                _render_data_profile(df)

            with tabs[1]:
                _render_ai_insights(df)

            with tabs[2]:
                _render_data_quality(df)

            with tabs[3]:
                _render_nlq_interface(df)

            with tabs[4]:
                _render_export_section(df)

        except Exception as e:
            logger.error(f"Error loading CSV: {str(e)}", exc_info=True)
            st.error(f"❌ Error loading CSV file: {str(e)}")
            st.info("💡 **Tip:** Make sure your file is a valid CSV format")
    else:
        # Show example/demo section
        _render_demo_section()


def _render_data_profile(df: pd.DataFrame) -> None:
    """Render automated data profiling section."""
    st.subheader("📊 Automated Data Profile")

    # Basic info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ui.card_metric("Total Rows", f"{len(df):,}")
    with col2:
        ui.card_metric("Total Columns", str(len(df.columns)))
    with col3:
        memory_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
        ui.card_metric("Memory Usage", f"{memory_mb:.2f} MB")
    with col4:
        duplicate_count = df.duplicated().sum()
        ui.card_metric("Duplicate Rows", f"{duplicate_count:,}")

    st.markdown("---")

    # Data preview
    st.subheader("📄 Data Preview")
    preview_rows = st.slider("Rows to display", 5, min(50, len(df)), 10)
    st.dataframe(df.head(preview_rows), use_container_width=True)

    st.markdown("---")

    # Column-by-column analysis
    st.subheader("📋 Column Analysis")

    # Create comprehensive column info
    column_info = []
    for col in df.columns:
        col_data = df[col]
        info = {
            "Column": col,
            "Type": str(col_data.dtype),
            "Non-Null": f"{col_data.count():,}",
            "Null": f"{col_data.isna().sum():,}",
            "Null %": f"{(col_data.isna().sum() / len(df) * 100):.1f}%",
            "Unique": f"{col_data.nunique():,}",
        }

        # Add type-specific info
        if pd.api.types.is_numeric_dtype(col_data):
            info["Min"] = f"{col_data.min():.2f}" if not col_data.isna().all() else "N/A"
            info["Max"] = f"{col_data.max():.2f}" if not col_data.isna().all() else "N/A"
            info["Mean"] = f"{col_data.mean():.2f}" if not col_data.isna().all() else "N/A"
        else:
            top_value = (
                col_data.value_counts().index[0] if len(col_data.value_counts()) > 0 else "N/A"
            )
            info["Top Value"] = str(top_value)[:30]  # Truncate long values

        column_info.append(info)

    column_df = pd.DataFrame(column_info)
    st.dataframe(column_df, use_container_width=True)

    st.markdown("---")

    # Visualizations
    st.subheader("📈 Data Distributions")

    # Select columns for visualization
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if numeric_cols:
        st.markdown("**Numeric Columns**")
        selected_numeric = st.selectbox("Select numeric column to visualize", numeric_cols)

        if selected_numeric:
            col1, col2 = st.columns(2)

            with col1:
                # Histogram
                fig_hist = px.histogram(
                    df,
                    x=selected_numeric,
                    title=f"Distribution of {selected_numeric}",
                    nbins=50,
                )
                st.plotly_chart(fig_hist, use_container_width=True)

            with col2:
                # Box plot
                fig_box = px.box(df, y=selected_numeric, title=f"Box Plot of {selected_numeric}")
                st.plotly_chart(fig_box, use_container_width=True)

    if categorical_cols:
        st.markdown("**Categorical Columns**")
        selected_categorical = st.selectbox(
            "Select categorical column to visualize", categorical_cols
        )

        if selected_categorical:
            # Get top 10 values
            value_counts = df[selected_categorical].value_counts().head(10)

            fig_bar = px.bar(
                x=value_counts.index,
                y=value_counts.values,
                title=f"Top 10 Values in {selected_categorical}",
                labels={"x": selected_categorical, "y": "Count"},
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    # Correlation matrix for numeric columns
    if len(numeric_cols) > 1:
        st.markdown("---")
        st.subheader("🔗 Correlation Matrix")
        st.markdown(
            "Identify relationships between numeric variables (-1 = perfect negative, +1 = perfect positive)"
        )

        # Calculate correlation matrix
        corr_matrix = df[numeric_cols].corr()

        fig_corr = px.imshow(
            corr_matrix,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="RdBu_r",
            color_continuous_midpoint=0,
            title="Correlation Heatmap",
            labels=dict(color="Correlation"),
            template=ui.get_plotly_template(),
        )
        fig_corr.update_xaxes(side="bottom")
        fig_corr.update_layout(height=max(400, len(numeric_cols) * 40))
        st.plotly_chart(fig_corr, use_container_width=True)

        # Highlight strong correlations
        st.markdown("**Strong Correlations** (|r| ≥ 0.7):")
        strong_corrs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) >= 0.7:
                    col1_name = corr_matrix.columns[i]
                    col2_name = corr_matrix.columns[j]
                    strong_corrs.append(
                        {
                            "Variable 1": col1_name,
                            "Variable 2": col2_name,
                            "Correlation": f"{corr_value:.3f}",
                            "Strength": "Strong Positive" if corr_value > 0 else "Strong Negative",
                        }
                    )

        if strong_corrs:
            strong_corr_df = pd.DataFrame(strong_corrs)
            st.dataframe(strong_corr_df, use_container_width=True)
        else:
            st.info("No strong correlations (|r| ≥ 0.7) found between variables")


def _render_ai_insights(df: pd.DataFrame) -> None:
    """Render AI-powered insights section."""
    st.subheader("🤖 AI-Powered Insights")

    if not ANTHROPIC_AVAILABLE:
        st.warning("⚠️ Anthropic package not installed. AI insights unavailable.")
        st.info("Install with: `pip install anthropic`")
        return

    # Get API key
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=os.getenv("ANTHROPIC_API_KEY", ""),
        help="Enter your Anthropic API key. Get one at https://console.anthropic.com/",
    )

    if not api_key:
        st.info("👆 Enter your Anthropic API key to generate AI insights")
        return

    st.markdown("---")

    # Generate insights button
    if st.button("🔮 Generate AI Insights", type="primary"):
        with st.spinner("🤖 Analyzing your data with Claude AI..."):
            insights = _generate_ai_insights(df, api_key)

            if insights:
                st.markdown("#### 💡 Key Findings")
                st.markdown(insights)
            else:
                st.error("❌ Failed to generate insights. Please check your API key and try again.")


def _render_data_quality(df: pd.DataFrame) -> None:
    """Render data quality assessment and cleaning recommendations."""
    st.subheader("🧹 Data Quality Assessment")

    # Calculate quality metrics
    quality_issues = _assess_data_quality(df)

    # Overall quality score
    total_checks = len(quality_issues)
    passed_checks = sum(1 for issue in quality_issues if not issue["has_issue"])
    quality_score = (passed_checks / total_checks * 100) if total_checks > 0 else 100

    col1, col2, col3 = st.columns(3)
    with col1:
        ui.card_metric("Quality Score", f"{quality_score:.0f}%")
    with col2:
        ui.card_metric("Issues Found", str(total_checks - passed_checks))
    with col3:
        ui.card_metric("Checks Passed", str(passed_checks))

    st.markdown("---")

    # Display issues and recommendations
    st.subheader("🔍 Quality Issues & Recommendations")

    for issue in quality_issues:
        if issue["has_issue"]:
            with st.expander(f"⚠️ {issue['issue']}", expanded=True):
                st.markdown(f"**Severity:** {issue['severity']}")
                st.markdown(f"**Description:** {issue['description']}")
                st.markdown(f"**Recommendation:** {issue['recommendation']}")

                # Show cleaning button if action is available
                if issue.get("action"):
                    if st.button(f"Apply Fix: {issue['action_name']}", key=issue["issue"]):
                        st.session_state.cleaned_data = issue["action"](df)
                        st.success(f"✅ Applied: {issue['action_name']}")
                        st.rerun()
        else:
            st.success(f"✅ {issue['issue']}: No issues detected")

    # Show cleaned data preview if available
    if st.session_state.cleaned_data is not None:
        st.markdown("---")
        st.subheader("🎉 Cleaned Data Preview")
        st.dataframe(st.session_state.cleaned_data.head(10), use_container_width=True)

        if st.button("Use Cleaned Data"):
            st.session_state.uploaded_data = st.session_state.cleaned_data
            st.success("✅ Now using cleaned data for analysis")
            st.rerun()


def _render_nlq_interface(df: pd.DataFrame) -> None:
    """Render natural language query interface."""
    st.subheader("💬 Ask Questions About Your Data")
    st.markdown("Ask questions in plain English and get AI-powered answers!")

    if not ANTHROPIC_AVAILABLE:
        st.warning("⚠️ Anthropic package not installed. Natural language queries unavailable.")
        return

    # Get API key
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=os.getenv("ANTHROPIC_API_KEY", ""),
        key="nlq_api_key",
        help="Enter your Anthropic API key",
    )

    if not api_key:
        st.info("👆 Enter your Anthropic API key to ask questions")
        return

    # Example questions
    st.markdown("**Example Questions:**")
    st.markdown(
        """
    - What are the top 5 values in the [column_name] column?
    - What's the correlation between [column1] and [column2]?
    - Are there any outliers in [numeric_column]?
    - What's the average value by [category_column]?
    """
    )

    # Query input
    query = st.text_area(
        "Your Question",
        placeholder="e.g., What are the top 5 customers by revenue?",
        height=100,
    )

    if st.button("🔍 Get Answer", type="primary"):
        if query:
            with st.spinner("🤖 Processing your question..."):
                answer = _process_natural_language_query(df, query, api_key)

                if answer:
                    st.markdown("#### 📝 Answer")
                    st.markdown(answer)
                else:
                    st.error("❌ Failed to process query. Please try rephrasing.")
        else:
            st.warning("⚠️ Please enter a question")


def _render_export_section(df: pd.DataFrame) -> None:
    """Render data export options."""
    st.subheader("📥 Export Your Data")

    # Choose which data to export
    data_to_export = st.radio(
        "Select data to export", ["Original Data", "Cleaned Data (if available)"]
    )

    export_df = (
        st.session_state.cleaned_data
        if data_to_export == "Cleaned Data (if available)"
        and st.session_state.cleaned_data is not None
        else df
    )

    # Export format options
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📄 Export as CSV")
        csv_buffer = io.StringIO()
        export_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        st.download_button(
            label="⬇️ Download CSV",
            data=csv_data,
            file_name=f"data_detective_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

    with col2:
        st.markdown("#### 📊 Export as Excel")
        excel_buffer = io.BytesIO()
        export_df.to_excel(excel_buffer, index=False, engine="openpyxl")
        excel_data = excel_buffer.getvalue()

        st.download_button(
            label="⬇️ Download Excel",
            data=excel_data,
            file_name=f"data_detective_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def _render_demo_section() -> None:
    """Render demo/example section when no file is uploaded."""
    st.info("👆 Upload a CSV file to get started!")

    st.markdown("---")
    st.subheader("✨ What You'll Get")

    col1, col2 = st.columns(2)

    with col1:
        ui.feature_card(
            icon="📊",
            title="Automated Data Profiling",
            description="Row/col stats, missing values, duplicates, and distribution plots.",
            status="active",
        )

    with col2:
        ui.feature_card(
            icon="🤖",
            title="AI-Powered Insights",
            description="Trend detection, anomaly identification, and business recommendations.",
            status="active",
        )

    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        ui.feature_card(
            icon="🧹",
            title="Data Quality Checks",
            description="Detect and fix missing values, outliers, and inconsistencies.",
            status="active",
        )

    with col4:
        ui.feature_card(
            icon="💬",
            title="Natural Language Queries",
            description="Ask questions in plain English and get instant AI-powered answers.",
            status="active",
        )

    st.markdown("---")
    st.subheader("🎯 Perfect For")
    st.markdown(
        """
    - **Business Analysts**: Quick data exploration and insights
    - **Data Scientists**: Initial data assessment before modeling
    - **Consultants**: Client data quality audits
    - **Anyone**: Understanding datasets without coding
    """
    )


def _generate_ai_insights(df: pd.DataFrame, api_key: str) -> Optional[str]:
    """
    Generate AI-powered insights about the dataset.

    Args:
        df: DataFrame to analyze
        api_key: Anthropic API key

    Returns:
        AI-generated insights as markdown string, or None if failed
    """
    try:
        # Prepare data summary for AI
        summary = _prepare_data_summary(df)

        # Create prompt
        prompt = f"""Analyze this dataset and provide 5-7 key insights in a clear, actionable format:

{summary}

Focus on:
1. Notable trends or patterns
2. Data quality issues
3. Potential outliers or anomalies
4. Relationships between variables
5. Business recommendations

Format your response as a bulleted list with clear, concise insights. Use markdown formatting."""

        # Call Claude API
        client = Anthropic(api_key=api_key)
        message = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=DEFAULT_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract response
        if message.content and len(message.content) > 0:
            return message.content[0].text
        return None

    except Exception as e:
        logger.error(f"Error generating AI insights: {str(e)}", exc_info=True)
        return None


def _process_natural_language_query(df: pd.DataFrame, query: str, api_key: str) -> Optional[str]:
    """
    Process a natural language query about the dataset.

    Args:
        df: DataFrame to query
        query: Natural language question
        api_key: Anthropic API key

    Returns:
        AI-generated answer, or None if failed
    """
    try:
        # Prepare data context
        summary = _prepare_data_summary(df, include_sample=True)

        # Create prompt
        prompt = f"""You are a data analyst assistant. Answer this question about the dataset:

Question: {query}

Dataset Information:
{summary}

Provide a clear, concise answer. If the question requires calculations, show the results. If it requires visualization suggestions, describe what would be helpful."""

        # Call Claude API
        client = Anthropic(api_key=api_key)
        message = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=DEFAULT_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract response
        if message.content and len(message.content) > 0:
            return message.content[0].text
        return None

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        return None


def _prepare_data_summary(df: pd.DataFrame, include_sample: bool = False) -> str:
    """
    Prepare a text summary of the dataset for AI analysis.

    Args:
        df: DataFrame to summarize
        include_sample: Whether to include sample rows

    Returns:
        Text summary of the dataset
    """
    summary_parts = []

    # Basic info
    summary_parts.append(f"Dataset Shape: {len(df)} rows × {len(df.columns)} columns\n")

    # Column information
    summary_parts.append("Columns:")
    for col in df.columns:
        col_data = df[col]
        dtype = str(col_data.dtype)
        null_pct = col_data.isna().sum() / len(df) * 100
        unique_count = col_data.nunique()

        summary_parts.append(
            f"  - {col} ({dtype}): {unique_count} unique values, {null_pct:.1f}% null"
        )

        # Add stats for numeric columns
        if pd.api.types.is_numeric_dtype(col_data) and not col_data.isna().all():
            summary_parts.append(
                f"    Range: {col_data.min():.2f} to {col_data.max():.2f}, Mean: {col_data.mean():.2f}"
            )

    # Sample data if requested
    if include_sample:
        summary_parts.append("\nSample Data (first 5 rows):")
        summary_parts.append(df.head(5).to_string())

    return "\n".join(summary_parts)


def _assess_data_quality(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Assess data quality and return list of issues with recommendations.

    Args:
        df: DataFrame to assess

    Returns:
        List of quality issues and recommendations
    """
    issues = []

    # Check for missing values
    missing_cols = df.columns[df.isna().any()].tolist()
    if missing_cols:
        total_missing = df.isna().sum().sum()
        pct_missing = total_missing / (len(df) * len(df.columns)) * 100

        issues.append(
            {
                "issue": "Missing Values",
                "has_issue": True,
                "severity": "High" if pct_missing > 10 else "Medium",
                "description": f"Found {total_missing:,} missing values across {len(missing_cols)} columns ({pct_missing:.2f}% of all data)",
                "recommendation": "Consider dropping rows with missing values or filling with appropriate values (mean, median, mode, or forward-fill)",
                "action": lambda df: df.dropna(),
                "action_name": "Drop all rows with missing values",
            }
        )
    else:
        issues.append(
            {
                "issue": "Missing Values",
                "has_issue": False,
                "severity": "None",
                "description": "No missing values detected",
                "recommendation": "N/A",
            }
        )

    # Check for duplicates
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        pct_duplicates = duplicate_count / len(df) * 100

        issues.append(
            {
                "issue": "Duplicate Rows",
                "has_issue": True,
                "severity": "Medium",
                "description": f"Found {duplicate_count:,} duplicate rows ({pct_duplicates:.2f}% of data)",
                "recommendation": "Remove duplicate rows to ensure data integrity",
                "action": lambda df: df.drop_duplicates(),
                "action_name": "Remove all duplicate rows",
            }
        )
    else:
        issues.append(
            {
                "issue": "Duplicate Rows",
                "has_issue": False,
                "severity": "None",
                "description": "No duplicate rows detected",
                "recommendation": "N/A",
            }
        )

    # Check for outliers in numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    outlier_cols = []

    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1

        outlier_count = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()

        if outlier_count > 0:
            outlier_cols.append((col, outlier_count))

    if outlier_cols:
        total_outliers = sum(count for _, count in outlier_cols)

        issues.append(
            {
                "issue": "Outliers Detected",
                "has_issue": True,
                "severity": "Low",
                "description": f"Found {total_outliers:,} outliers across {len(outlier_cols)} numeric columns",
                "recommendation": "Review outliers to determine if they are data errors or valid extreme values. Consider winsorization or removal if appropriate.",
                "action": None,
                "action_name": None,
            }
        )
    else:
        issues.append(
            {
                "issue": "Outliers",
                "has_issue": False,
                "severity": "None",
                "description": "No significant outliers detected",
                "recommendation": "N/A",
            }
        )

    return issues
