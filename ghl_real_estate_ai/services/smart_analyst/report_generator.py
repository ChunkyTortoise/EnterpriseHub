"""PDF report generator for Smart Analyst."""
from __future__ import annotations

from typing import List, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib import colors


class ReportGenerator:
    def generate_report(
        self,
        output_path: str,
        title: str,
        summary: str,
        trends: List[str],
        charts: Optional[List[str]] = None,
        anomalies: Optional[List[List[str]]] = None,
    ) -> str:
        """Generate a PDF report and return the output path."""
        styles = getSampleStyleSheet()
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []

        story.append(Paragraph(title, styles["Title"]))
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("Executive Summary", styles["Heading2"]))
        story.append(Paragraph(summary, styles["BodyText"]))
        story.append(Spacer(1, 0.2 * inch))

        story.append(Paragraph("Key Trends", styles["Heading2"]))
        for trend in trends:
            story.append(Paragraph(f"• {trend}", styles["BodyText"]))
        story.append(Spacer(1, 0.2 * inch))

        if charts:
            story.append(Paragraph("Visualizations", styles["Heading2"]))
            for chart_path in charts:
                try:
                    story.append(Image(chart_path, width=6 * inch, height=3.5 * inch))
                    story.append(Spacer(1, 0.2 * inch))
                except Exception:
                    continue

        if anomalies:
            story.append(Paragraph("Data Anomalies", styles["Heading2"]))
            table = Table(anomalies)
            table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ])
            )
            story.append(table)

        doc.build(story)
        return output_path
