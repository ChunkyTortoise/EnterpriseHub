import asyncio
import io
from datetime import datetime
from typing import Any, Dict

from reportlab.lib.enums import TA_CENTER

# We'll use ReportLab for PDF generation. You'll need to install it:
# pip install reportlab
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.agent_state_sync import sync_service

logger = get_logger(__name__)


class ReportGeneratorService:
    """
    Service to generate various types of reports, including dashboard summaries.
    Utilizes ReportLab for PDF generation.
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name="CenteredTitle", alignment=TA_CENTER, fontSize=24, spaceAfter=20))
        self.styles.add(
            ParagraphStyle(name="H2Centered", alignment=TA_CENTER, fontSize=18, spaceAfter=10, spaceBefore=10)
        )
        self.styles.add(ParagraphStyle(name="NormalSmall", fontSize=10))

    async def generate_dashboard_summary_pdf(
        self, user_info: Dict[str, Any], date_range: str = "Last 24 Hours"
    ) -> io.BytesIO:
        """
        Generates a PDF summary of the current dashboard state.

        Args:
            user_info: Dictionary containing authenticated user details (e.g., name, tenant_id).
            date_range: String indicating the data period (e.g., "Last 24 Hours", "Last 7 Days").

        Returns:
            io.BytesIO: A byte stream containing the generated PDF.
        """

        logger.info(
            f"Generating dashboard summary PDF for user {user_info.get('user', {}).get('email')} "
            f"in tenant {user_info.get('tenant', {}).get('company_name')}"
        )

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # Title Page
        story.append(Paragraph("Enterprise AI Dashboard Summary", self.styles["CenteredTitle"]))
        story.append(
            Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}", self.styles["H2Centered"])
        )
        story.append(
            Paragraph(
                f"For: {user_info.get('tenant', {}).get('company_name', 'N/A')} - {user_info.get('user', {}).get('name', 'User')}",
                self.styles["Normal"],
            )
        )
        story.append(Paragraph(f"Date Range: {date_range}", self.styles["Normal"]))
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("Confidential & Proprietary - Lyrio.io", self.styles["NormalSmall"]))
        story.append(PageBreak())

        # Fetch current dashboard state
        state = sync_service.get_state()

        # Section: Key Performance Indicators
        story.append(Paragraph("1. Key Performance Indicators (KPIs)", self.styles["h1"]))
        story.append(Spacer(1, 0.2 * inch))
        for kpi_title, kpi_value in state.get("kpis", {}).items():
            story.append(Paragraph(f"<b>{kpi_title.replace('_', ' ').title()}:</b> {kpi_value}", self.styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

        # Section: Recent Agent Thoughts
        story.append(Paragraph("2. Recent Agent Thoughts", self.styles["h1"]))
        story.append(Spacer(1, 0.2 * inch))
        thoughts = state.get("recent_thoughts", [])
        if thoughts:
            for thought in thoughts[:5]:  # Limit to 5 for summary
                story.append(
                    Paragraph(
                        f"<b>{thought['agent']}</b> ({thought['timestamp']}): {thought['task']} [{thought['status']}]",
                        self.styles["Normal"],
                    )
                )
        else:
            story.append(Paragraph("No recent agent thoughts recorded.", self.styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

        # Section: Lead Intelligence Summary (Top 3 Leads)
        story.append(Paragraph("3. Top Lead Intelligence", self.styles["h1"]))
        story.append(Spacer(1, 0.2 * inch))
        leads = state.get("leads", [])
        if leads:
            for lead in leads[:3]:  # Limit to 3 for summary
                story.append(
                    Paragraph(
                        f"<b>Lead:</b> {lead['name']} | <b>Score:</b> {lead['score']}% | <b>Status:</b> {lead['classification']} | <b>Market:</b> {lead['extracted_preferences'].get('location', 'N/A')}",
                        self.styles["Normal"],
                    )
                )
                story.append(Paragraph(f"<i>Reasoning:</i> {lead['reasoning']}", self.styles["NormalSmall"]))
                story.append(Spacer(1, 0.05 * inch))
        else:
            story.append(Paragraph("No leads found.", self.styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

        # Section: Market Predictions
        story.append(Paragraph("4. Market Appreciation Forecast", self.styles["h1"]))
        story.append(Spacer(1, 0.2 * inch))
        predictions = state.get("market_predictions", [])
        if predictions:
            for pred in predictions[:3]:  # Limit to 3 for summary
                story.append(
                    Paragraph(
                        f"<b>Neighborhood:</b> {pred['neighborhood']} | <b>Prediction:</b> {pred['prediction']} | <b>Confidence:</b> {pred['confidence']}",
                        self.styles["Normal"],
                    )
                )
        else:
            story.append(Paragraph("No market predictions available.", self.styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

        # Build the PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    async def generate_v2_investor_report(self, data: Dict[str, Any]) -> io.BytesIO:
        """
        Generates a professional investor report from V2 Multi-Agent data.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # Title
        address = data.get("address", "Property")
        story.append(Paragraph(f"INVESTMENT_INTEL: {address.upper()}", self.styles["CenteredTitle"]))
        story.append(Spacer(1, 0.2 * inch))

        # 1. Executive Summary
        exec_data = data.get("executive", {})
        story.append(Paragraph("1. EXECUTIVE STRATEGY", self.styles["h1"]))
        story.append(Paragraph(f"<b>Verdict:</b> {exec_data.get('investment_verdict', 'N/A')}", self.styles["Normal"]))
        story.append(Paragraph(exec_data.get("executive_summary", "No summary provided."), self.styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

        # 2. Financial Analysis
        analysis_data = data.get("analysis", {})
        story.append(Paragraph("2. FINANCIAL PROJECTIONS", self.styles["h1"]))
        financials = analysis_data.get("financials", {})
        for k, v in financials.items():
            story.append(Paragraph(f"<b>{k.replace('_', ' ').title()}:</b> {v}", self.styles["Normal"]))
        story.append(Spacer(1, 0.2 * inch))

        # 3. Design & Staging
        design_data = data.get("design", {})
        story.append(Paragraph("3. VISUAL STAGING CONCEPTS", self.styles["h1"]))
        rooms = design_data.get("staged_rooms", [])
        for room in rooms:
            story.append(Paragraph(f"<b>{room.get('room_name')}:</b> {room.get('description')}", self.styles["Normal"]))
            story.append(
                Paragraph(f"<i>Palette:</i> {', '.join(room.get('color_palette', []))}", self.styles["NormalSmall"])
            )

        doc.build(story)
        buffer.seek(0)
        return buffer


report_generator_service = ReportGeneratorService()
