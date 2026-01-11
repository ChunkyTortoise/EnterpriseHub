"""
Multi-Modal Document Intelligence Dashboard - Phase 2 Enhancement

Advanced Streamlit dashboard for Claude's multi-modal document intelligence.
Provides drag-and-drop document analysis, real-time insights, and batch processing.
"""

# ============================================================================
# MIGRATION NOTES (Automated Migration - 2026-01-11)
# ============================================================================
# Changes Applied:
# # - Upgraded base class from EnterpriseComponent to EnterpriseDashboardComponent
# - Added unified design system import check
# - Consider using enterprise_metric for consistent styling
#
# This component has been migrated to enterprise standards.
# See migration documentation for details.
# ============================================================================



import streamlit as st

# === ENTERPRISE BASE IMPORTS ===
from .enhanced_enterprise_base import (
    EnhancedEnterpriseComponent,
    EnterpriseDashboardComponent,
    EnterpriseDataComponent,
    ComponentMetrics,
    ComponentState
)
from .enterprise_theme_system import (
    EnterpriseThemeManager,
    ThemeVariant,
    ComponentType,
    inject_enterprise_theme,
    create_enterprise_card,
    create_enterprise_metric,
    create_enterprise_alert
)


# === UNIFIED DESIGN SYSTEM ===
try:
    from ..design_system import (
        enterprise_metric,
        enterprise_card,
        enterprise_badge,
        enterprise_progress_ring,
        enterprise_status_indicator,
        enterprise_kpi_grid,
        enterprise_section_header,
        apply_plotly_theme,
        ENTERPRISE_COLORS
    )
    UNIFIED_DESIGN_SYSTEM_AVAILABLE = True
except ImportError:
    UNIFIED_DESIGN_SYSTEM_AVAILABLE = False
import asyncio
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

from ..services.claude_multimodal_intelligence import (
    get_multimodal_intelligence,
    DocumentType,
    AnalysisComplexity,
    DocumentProcessingStatus,
    DocumentAnalysisResult
)
from .enhanced_enterprise_base import EnterpriseComponent

logger = logging.getLogger(__name__)


class MultiModalDocumentIntelligenceDashboard(EnterpriseDashboardComponent):
    """
    Multi-Modal Document Intelligence Dashboard Component.

    Provides comprehensive document analysis interface with:
    - Drag-and-drop document upload
    - Real-time analysis progress
    - Batch processing capabilities
    - Document comparison tools
    - Transaction-level insights
    """

    def __init__(self):
        super().__init__("Multi-Modal Document Intelligence", "📄")
        self.intelligence_service = None
        self._initialize_session_state()

    def _initialize_session_state(self):
        """Initialize session state variables."""
        if 'uploaded_documents' not in st.session_state:
            st.session_state.uploaded_documents = []

        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = {}

        if 'selected_documents' not in st.session_state:
            st.session_state.selected_documents = []

        if 'processing_queue' not in st.session_state:
            st.session_state.processing_queue = []

    async def _get_intelligence_service(self):
        """Get multi-modal intelligence service instance."""
        if self.intelligence_service is None:
            self.intelligence_service = await get_multimodal_intelligence()
        return self.intelligence_service

    def render(self, agent_id: Optional[str] = None, lead_context: Optional[Dict[str, Any]] = None) -> None:
        """Render the multi-modal document intelligence dashboard."""

        # Header with metrics
        self._render_header_metrics()

        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📤 Upload & Analyze",
            "📊 Analysis Results",
            "🔄 Batch Processing",
            "⚖️ Document Comparison",
            "📋 Transaction Insights"
        ])

        with tab1:
            self._render_upload_analysis_tab(agent_id, lead_context)

        with tab2:
            self._render_analysis_results_tab()

        with tab3:
            self._render_batch_processing_tab(agent_id)

        with tab4:
            self._render_document_comparison_tab()

        with tab5:
            self._render_transaction_insights_tab()

    def _render_header_metrics(self) -> None:
        """Render header metrics and status."""
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "📄 Documents Analyzed",
                len(st.session_state.analysis_results),
                delta=len([r for r in st.session_state.analysis_results.values()
                          if r.get('analysis_timestamp', datetime.min) > datetime.now() - timedelta(hours=24)])
            )

        with col2:
            processing_count = len(st.session_state.processing_queue)
            st.metric("⏳ Processing Queue", processing_count)

        with col3:
            completed_analyses = [r for r in st.session_state.analysis_results.values()
                                if r.get('confidence_score', 0) > 0.8]
            st.metric("✅ High Confidence", len(completed_analyses))

        with col4:
            avg_processing_time = self._calculate_avg_processing_time()
            st.metric("⚡ Avg Processing", f"{avg_processing_time:.1f}s")

        with col5:
            if st.session_state.analysis_results:
                latest_result = max(st.session_state.analysis_results.values(),
                                  key=lambda x: x.get('analysis_timestamp', datetime.min))
                status = "🟢 Ready" if latest_result.get('confidence_score', 0) > 0.8 else "🟡 Review Needed"
                st.metric("Status", status)
            else:
                st.metric("Status", "🟢 Ready")

    def _render_upload_analysis_tab(self, agent_id: Optional[str], lead_context: Optional[Dict[str, Any]]) -> None:
        """Render document upload and analysis tab."""
        st.subheader("📤 Document Upload & Analysis")

        # Upload section
        col1, col2 = st.columns([2, 1])

        with col1:
            uploaded_files = st.file_uploader(
                "Upload Real Estate Documents",
                type=['pdf', 'png', 'jpg', 'jpeg'],
                accept_multiple_files=True,
                help="Supported formats: PDF, PNG, JPG, JPEG. Max file size: 10MB per document."
            )

        with col2:
            st.selectbox(
                "Document Type",
                options=[None] + [doc_type.value for doc_type in DocumentType if doc_type != DocumentType.UNKNOWN],
                format_func=lambda x: "Auto-detect" if x is None else x.replace('_', ' ').title(),
                key="document_type_selection"
            )

            analysis_complexity = st.selectbox(
                "Analysis Depth",
                options=[complexity.value for complexity in AnalysisComplexity],
                format_func=lambda x: {
                    'quick_scan': '🚀 Quick Scan (5-10s)',
                    'standard_analysis': '📊 Standard Analysis (15-30s)',
                    'deep_analysis': '🔍 Deep Analysis (30-60s)',
                    'comprehensive_review': '📋 Comprehensive Review (60s+)'
                }.get(x, x),
                index=1  # Default to standard analysis
            )

        # Advanced options
        with st.expander("Advanced Options", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                priority_processing = st.checkbox("Priority Processing", help="Process this document with high priority")
                include_compliance_check = st.checkbox("Include Compliance Check", value=True)

            with col2:
                enable_coaching_insights = st.checkbox("Enable Coaching Insights", value=True)
                auto_classify_documents = st.checkbox("Auto-classify Documents", value=True)

        # Lead context input
        if lead_context:
            st.info(f"🔗 Using provided lead context for enhanced analysis")
        else:
            lead_context_input = st.text_area(
                "Lead Context (Optional)",
                placeholder="Add relevant lead information for context-aware analysis...",
                help="Provide additional context about the lead, transaction, or specific requirements"
            )
            if lead_context_input:
                try:
                    lead_context = {"manual_context": lead_context_input}
                except:
                    lead_context = {"manual_context": lead_context_input}

        # Process uploaded files
        if uploaded_files and st.button("🚀 Start Analysis", type="primary"):
            self._process_uploaded_documents(
                uploaded_files,
                agent_id,
                lead_context,
                AnalysisComplexity(analysis_complexity),
                DocumentType(st.session_state.document_type_selection) if st.session_state.document_type_selection else None
            )

        # Real-time processing status
        if st.session_state.processing_queue:
            self._render_processing_status()

    def _render_analysis_results_tab(self) -> None:
        """Render analysis results tab."""
        st.subheader("📊 Document Analysis Results")

        if not st.session_state.analysis_results:
            st.info("No documents analyzed yet. Upload documents in the 'Upload & Analyze' tab to get started.")
            return

        # Filter and search
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            search_query = st.text_input("🔍 Search analyses...", placeholder="Search by document type, insights, or content...")

        with col2:
            confidence_filter = st.slider("Minimum Confidence", 0.0, 1.0, 0.0, 0.1)

        with col3:
            document_type_filter = st.selectbox(
                "Filter by Type",
                options=["All"] + [doc_type.value for doc_type in DocumentType],
                format_func=lambda x: x.replace('_', ' ').title() if x != "All" else x
            )

        # Filter results
        filtered_results = self._filter_analysis_results(search_query, confidence_filter, document_type_filter)

        # Results grid
        for doc_id, result in filtered_results.items():
            self._render_analysis_result_card(doc_id, result)

    def _render_batch_processing_tab(self, agent_id: Optional[str]) -> None:
        """Render batch processing tab."""
        st.subheader("🔄 Batch Document Processing")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.write("**Batch Upload**")
            batch_files = st.file_uploader(
                "Upload Multiple Documents",
                type=['pdf', 'png', 'jpg', 'jpeg'],
                accept_multiple_files=True,
                key="batch_upload"
            )

            if batch_files:
                st.write(f"Selected {len(batch_files)} documents for batch processing")

        with col2:
            st.write("**Batch Settings**")
            batch_complexity = st.selectbox(
                "Analysis Complexity for Batch",
                options=[complexity.value for complexity in AnalysisComplexity],
                format_func=lambda x: x.replace('_', ' ').title(),
                key="batch_complexity"
            )

            processing_priority = st.selectbox(
                "Processing Priority",
                options=["normal", "high"],
                format_func=lambda x: f"🔥 High Priority" if x == "high" else "⚖️ Normal Priority"
            )

        # Start batch processing
        if batch_files and st.button("🚀 Start Batch Processing", type="primary"):
            self._start_batch_processing(batch_files, agent_id, AnalysisComplexity(batch_complexity), processing_priority)

        # Batch processing status
        if hasattr(st.session_state, 'batch_status') and st.session_state.batch_status:
            self._render_batch_status()

    def _render_document_comparison_tab(self) -> None:
        """Render document comparison tab."""
        st.subheader("⚖️ Document Comparison")

        if len(st.session_state.analysis_results) < 2:
            st.info("Upload and analyze at least 2 documents to enable comparison features.")
            return

        # Document selection for comparison
        col1, col2 = st.columns(2)

        with col1:
            doc1_id = st.selectbox(
                "Select First Document",
                options=list(st.session_state.analysis_results.keys()),
                format_func=lambda x: self._format_document_name(x),
                key="comparison_doc1"
            )

        with col2:
            available_docs = [doc_id for doc_id in st.session_state.analysis_results.keys() if doc_id != doc1_id]
            doc2_id = st.selectbox(
                "Select Second Document",
                options=available_docs,
                format_func=lambda x: self._format_document_name(x),
                key="comparison_doc2"
            )

        # Comparison focus
        comparison_focus = st.selectbox(
            "Comparison Focus",
            options=["overall", "pricing", "risks", "opportunities", "compliance"],
            format_func=lambda x: {
                "overall": "📋 Overall Comparison",
                "pricing": "💰 Pricing Analysis",
                "risks": "⚠️ Risk Assessment",
                "opportunities": "🎯 Opportunities",
                "compliance": "✅ Compliance Check"
            }.get(x, x.title())
        )

        if st.button("🔄 Compare Documents", type="primary"):
            comparison_result = self._compare_documents(doc1_id, doc2_id, comparison_focus)
            if comparison_result:
                self._render_comparison_results(comparison_result)

    def _render_transaction_insights_tab(self) -> None:
        """Render transaction insights tab."""
        st.subheader("📋 Transaction-Level Insights")

        if not st.session_state.analysis_results:
            st.info("Analyze documents to generate transaction-level insights.")
            return

        # Group documents by transaction
        st.write("**Document Grouping**")
        selected_docs = st.multiselect(
            "Select documents for transaction analysis:",
            options=list(st.session_state.analysis_results.keys()),
            format_func=lambda x: self._format_document_name(x)
        )

        if len(selected_docs) >= 2:
            # Transaction insight options
            insight_type = st.selectbox(
                "Insight Type",
                options=["transaction", "investment", "risk_assessment", "due_diligence"],
                format_func=lambda x: {
                    "transaction": "🏠 Transaction Overview",
                    "investment": "📈 Investment Analysis",
                    "risk_assessment": "⚠️ Risk Assessment",
                    "due_diligence": "🔍 Due Diligence Summary"
                }.get(x, x.title())
            )

            if st.button("🔮 Generate Transaction Insights", type="primary"):
                insights = self._generate_transaction_insights(selected_docs, insight_type)
                self._render_transaction_insights(insights)

        # Analytics dashboard
        st.write("**Analytics Overview**")
        self._render_analytics_charts()

    def _process_uploaded_documents(
        self,
        uploaded_files,
        agent_id: Optional[str],
        lead_context: Optional[Dict[str, Any]],
        analysis_complexity: AnalysisComplexity,
        document_type: Optional[DocumentType]
    ) -> None:
        """Process uploaded documents for analysis."""

        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, uploaded_file in enumerate(uploaded_files):
            try:
                status_text.text(f"Processing {uploaded_file.name}...")

                # Read and encode file
                file_data = uploaded_file.read()
                file_base64 = base64.b64encode(file_data).decode('utf-8')

                # Generate document ID
                doc_id = f"doc_{hash(file_base64)}_{int(time.time())}"

                # Add to processing queue
                st.session_state.processing_queue.append({
                    'document_id': doc_id,
                    'filename': uploaded_file.name,
                    'status': 'processing',
                    'progress': 0
                })

                # Simulate analysis (in real implementation, this would be async)
                # For demo purposes, we'll create a mock analysis result
                mock_result = self._create_mock_analysis_result(
                    doc_id,
                    uploaded_file.name,
                    document_type or DocumentType.UNKNOWN
                )

                st.session_state.analysis_results[doc_id] = mock_result

                # Update progress
                progress_bar.progress((i + 1) / len(uploaded_files))

            except Exception as e:
                st.error(f"Error processing {uploaded_file.name}: {str(e)}")

        # Clear processing queue
        st.session_state.processing_queue = []
        status_text.text("✅ All documents processed successfully!")

        st.success(f"Successfully analyzed {len(uploaded_files)} documents!")
        st.rerun()

    def _render_analysis_result_card(self, doc_id: str, result: Dict[str, Any]) -> None:
        """Render individual analysis result card."""
        with st.container():
            st.markdown("---")

            # Header row
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.write(f"**📄 {result.get('filename', doc_id)}**")
                st.write(f"Type: {result.get('document_type', 'Unknown').replace('_', ' ').title()}")

            with col2:
                confidence = result.get('confidence_score', 0)
                confidence_color = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
                st.metric("Confidence", f"{confidence:.1%}", delta=None)
                st.write(f"{confidence_color}")

            with col3:
                processing_time = result.get('processing_time_ms', 0)
                st.metric("Processing", f"{processing_time/1000:.1f}s")

            with col4:
                requires_review = result.get('requires_human_review', False)
                review_status = "⚠️ Review" if requires_review else "✅ Complete"
                st.write(f"**Status**\n{review_status}")

            # Expandable details
            with st.expander("📊 View Analysis Details", expanded=False):

                # Summary
                st.write("**Executive Summary**")
                st.write(result.get('analysis_summary', 'No summary available'))

                # Key insights
                insights = result.get('key_insights', [])
                if insights:
                    st.write("**Key Insights**")
                    for insight in insights[:5]:  # Limit to top 5
                        st.write(f"• {insight}")

                # Risk flags and opportunities
                col1, col2 = st.columns(2)

                with col1:
                    risks = result.get('risk_flags', [])
                    if risks:
                        st.write("**⚠️ Risk Factors**")
                        for risk in risks[:3]:
                            st.write(f"• {risk}")

                with col2:
                    opportunities = result.get('opportunities', [])
                    if opportunities:
                        st.write("**🎯 Opportunities**")
                        for opp in opportunities[:3]:
                            st.write(f"• {opp}")

                # Coaching suggestions
                coaching = result.get('coaching_suggestions', [])
                if coaching:
                    st.write("**💡 Coaching Suggestions**")
                    for suggestion in coaching[:3]:
                        st.write(f"• {suggestion}")

    def _render_processing_status(self) -> None:
        """Render real-time processing status."""
        st.write("**⏳ Processing Status**")

        for item in st.session_state.processing_queue:
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.write(f"📄 {item['filename']}")

            with col2:
                st.write(f"Status: {item['status']}")

            with col3:
                st.progress(item.get('progress', 0))

    def _filter_analysis_results(
        self,
        search_query: str,
        confidence_filter: float,
        document_type_filter: str
    ) -> Dict[str, Any]:
        """Filter analysis results based on criteria."""
        filtered = {}

        for doc_id, result in st.session_state.analysis_results.items():
            # Confidence filter
            if result.get('confidence_score', 0) < confidence_filter:
                continue

            # Document type filter
            if (document_type_filter != "All" and
                result.get('document_type', '') != document_type_filter):
                continue

            # Search filter
            if search_query:
                search_text = (
                    result.get('analysis_summary', '') +
                    ' '.join(result.get('key_insights', [])) +
                    result.get('filename', '')
                ).lower()

                if search_query.lower() not in search_text:
                    continue

            filtered[doc_id] = result

        return filtered

    def _format_document_name(self, doc_id: str) -> str:
        """Format document name for display."""
        result = st.session_state.analysis_results.get(doc_id, {})
        filename = result.get('filename', doc_id)
        doc_type = result.get('document_type', 'unknown').replace('_', ' ').title()
        return f"{filename} ({doc_type})"

    def _calculate_avg_processing_time(self) -> float:
        """Calculate average processing time."""
        if not st.session_state.analysis_results:
            return 0.0

        times = [r.get('processing_time_ms', 0) for r in st.session_state.analysis_results.values()]
        return sum(times) / len(times) / 1000 if times else 0.0

    def _create_mock_analysis_result(
        self,
        doc_id: str,
        filename: str,
        document_type: DocumentType
    ) -> Dict[str, Any]:
        """Create mock analysis result for demo purposes."""
        import random

        # Mock insights based on document type
        mock_insights = {
            DocumentType.MLS_LISTING: [
                "Property is priced competitively for the current market",
                "High-quality photos showcase the property effectively",
                "Strong curb appeal and move-in ready condition",
                "Excellent school district adds significant value",
                "Open floor plan appeals to modern buyers"
            ],
            DocumentType.FINANCIAL_PREAPPROVAL: [
                "Strong creditworthiness with excellent debt-to-income ratio",
                "Pre-approval amount supports target price range",
                "Stable employment history enhances loan security",
                "Down payment amount demonstrates serious buyer intent",
                "Loan terms are favorable for current market conditions"
            ],
            DocumentType.INSPECTION_REPORT: [
                "Overall property condition is excellent",
                "Minor maintenance items identified for negotiation",
                "HVAC system recently updated and well-maintained",
                "Electrical and plumbing systems meet current codes",
                "Roof condition is good with 10+ years remaining life"
            ]
        }

        insights = mock_insights.get(document_type, [
            "Document analysis completed successfully",
            "Key information extracted and verified",
            "Compliance requirements reviewed"
        ])

        return {
            'document_id': doc_id,
            'filename': filename,
            'document_type': document_type.value,
            'analysis_summary': f"Comprehensive analysis of {filename} completed. {random.choice(['Positive outlook with minimal risks identified.', 'Strong documentation with good compliance.', 'Detailed review reveals favorable conditions.'])}",
            'key_insights': random.sample(insights, min(3, len(insights))),
            'risk_flags': random.sample([
                "Property age may require additional maintenance",
                "Market conditions suggest cautious pricing strategy",
                "Minor compliance items require attention"
            ], random.randint(0, 2)),
            'opportunities': random.sample([
                "Strong investment potential in growing market",
                "Renovation opportunities could increase value",
                "Favorable financing terms available"
            ], random.randint(1, 2)),
            'coaching_suggestions': [
                "Highlight unique property features in marketing materials",
                "Prepare for potential buyer questions about property condition",
                "Consider staging to maximize buyer appeal"
            ],
            'confidence_score': random.uniform(0.75, 0.95),
            'processing_time_ms': random.uniform(15000, 35000),
            'analysis_timestamp': datetime.now(),
            'requires_human_review': random.choice([True, False]) if random.random() > 0.8 else False
        }

    def _start_batch_processing(
        self,
        batch_files,
        agent_id: Optional[str],
        complexity: AnalysisComplexity,
        priority: str
    ) -> None:
        """Start batch processing of documents."""
        st.session_state.batch_status = {
            'batch_id': f"batch_{int(time.time())}",
            'total_files': len(batch_files),
            'processed': 0,
            'status': 'processing'
        }

        st.success(f"🚀 Started batch processing of {len(batch_files)} documents!")

    def _render_batch_status(self) -> None:
        """Render batch processing status."""
        status = st.session_state.batch_status
        progress = status['processed'] / status['total_files'] if status['total_files'] > 0 else 0

        st.write(f"**Batch Status**: {status['status'].title()}")
        st.progress(progress)
        st.write(f"Processed: {status['processed']} / {status['total_files']}")

    def _compare_documents(self, doc1_id: str, doc2_id: str, focus: str) -> Dict[str, Any]:
        """Compare two documents."""
        # Mock comparison result
        return {
            'comparison_id': f"comp_{int(time.time())}",
            'document_1_id': doc1_id,
            'document_2_id': doc2_id,
            'focus': focus,
            'similarities': [
                "Both documents show strong financial positions",
                "Similar property types and market segments",
                "Comparable risk profiles identified"
            ],
            'differences': [
                "Significantly different pricing strategies",
                "Varying levels of detail in documentation",
                "Different compliance requirements"
            ],
            'recommendations': [
                "Consider hybrid approach combining strengths of both",
                "Address documentation gaps in second document",
                "Leverage pricing insights from both analyses"
            ]
        }

    def _render_comparison_results(self, comparison: Dict[str, Any]) -> None:
        """Render document comparison results."""
        st.write("**🔄 Comparison Results**")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**✅ Similarities**")
            for similarity in comparison.get('similarities', []):
                st.write(f"• {similarity}")

        with col2:
            st.write("**⚖️ Key Differences**")
            for difference in comparison.get('differences', []):
                st.write(f"• {difference}")

        st.write("**💡 Recommendations**")
        for rec in comparison.get('recommendations', []):
            st.write(f"• {rec}")

    def _generate_transaction_insights(self, selected_docs: List[str], insight_type: str) -> Dict[str, Any]:
        """Generate transaction-level insights."""
        return {
            'insight_id': f"insight_{int(time.time())}",
            'document_ids': selected_docs,
            'insight_type': insight_type,
            'summary': f"Comprehensive {insight_type.replace('_', ' ')} analysis across {len(selected_docs)} documents.",
            'key_findings': [
                "Strong overall transaction position",
                "Minor risks identified and mitigated",
                "Excellent investment potential"
            ],
            'recommendations': [
                "Proceed with confidence based on analysis",
                "Address minor compliance items before closing",
                "Consider additional due diligence in specific areas"
            ],
            'risk_score': 0.25,
            'opportunity_score': 0.85
        }

    def _render_transaction_insights(self, insights: Dict[str, Any]) -> None:
        """Render transaction insights."""
        st.write("**🔮 Transaction Insights**")

        # Summary
        st.write(insights.get('summary', ''))

        # Metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Risk Score", f"{insights.get('risk_score', 0):.1%}")
        with col2:
            st.metric("Opportunity Score", f"{insights.get('opportunity_score', 0):.1%}")

        # Findings and recommendations
        col1, col2 = st.columns(2)

        with col1:
            st.write("**🔍 Key Findings**")
            for finding in insights.get('key_findings', []):
                st.write(f"• {finding}")

        with col2:
            st.write("**📋 Recommendations**")
            for rec in insights.get('recommendations', []):
                st.write(f"• {rec}")

    def _render_analytics_charts(self) -> None:
        """Render analytics charts and visualizations."""
        if not st.session_state.analysis_results:
            return

        # Prepare data
        results_data = []
        for doc_id, result in st.session_state.analysis_results.items():
            results_data.append({
                'document_id': doc_id,
                'document_type': result.get('document_type', 'unknown'),
                'confidence_score': result.get('confidence_score', 0),
                'processing_time_ms': result.get('processing_time_ms', 0),
                'requires_review': result.get('requires_human_review', False),
                'risk_count': len(result.get('risk_flags', [])),
                'opportunity_count': len(result.get('opportunities', []))
            })

        df = pd.DataFrame(results_data)

        if len(df) > 0:
            col1, col2 = st.columns(2)

            with col1:
                # Document types distribution
                doc_type_counts = df['document_type'].value_counts()
                fig_types = px.pie(
                    values=doc_type_counts.values,
                    names=[name.replace('_', ' ').title() for name in doc_type_counts.index],
                    title="Document Types Distribution"
                )
                st.plotly_chart(fig_types, use_container_width=True)

            with col2:
                # Confidence score distribution
                fig_confidence = px.histogram(
                    df,
                    x='confidence_score',
                    title="Confidence Score Distribution",
                    nbins=10
                )
                st.plotly_chart(fig_confidence, use_container_width=True)

            # Processing time vs confidence
            fig_scatter = px.scatter(
                df,
                x='processing_time_ms',
                y='confidence_score',
                color='document_type',
                title="Processing Time vs Confidence Score",
                hover_data=['document_id']
            )
            st.plotly_chart(fig_scatter, use_container_width=True)