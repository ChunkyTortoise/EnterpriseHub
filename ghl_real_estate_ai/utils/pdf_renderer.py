from io import BytesIO

from ghl_real_estate_ai.models.cma import CMAReport
from ghl_real_estate_ai.ghl_utils.logger import get_logger
import base64

logger = get_logger(__name__)

MAX_PDF_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB


class PDFGenerationError(Exception):
    """Raised when PDF generation fails."""
    pass


class PDFRenderer:
    """
    Renders CMA Reports into HTML/PDF format.
    """

    @staticmethod
    def render_cma_html(report: CMAReport) -> str:
        """
        Generates the HTML content for the CMA.
        """
        # Jinja2-style string formatting

        comps_rows = ""
        for comp in report.comparables:
            comps_rows += f"""
            <tr>
                <td>{comp.address}</td>
                <td>{comp.sale_date}</td>
                <td>${comp.sale_price:,.0f}</td>
                <td>{comp.sqft}</td>
                <td>${comp.price_per_sqft:.0f}</td>
                <td>{comp.adjustment_percent}%</td>
                <td><strong>${comp.adjusted_value:,.0f}</strong></td>
            </tr>
            """

        trend_icon = "📈" if report.market_context.price_trend > 0 else "📉"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #2c3e50; margin: 0; padding: 20px; background: #f8f9fa; }}
        .header {{ background: #2d5a7a; color: white; padding: 20px; border-radius: 8px; margin-bottom: 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .property-overview {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
        .section {{ background: white; padding: 15px; border-left: 4px solid #2d5a7a; border-radius: 4px; }}
        .section h3 {{ margin: 0 0 10px 0; color: #2d5a7a; font-size: 14px; text-transform: uppercase; }}
        .comps-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background: white; }}
        .comps-table th {{ background: #2d5a7a; color: white; padding: 12px; text-align: left; }}
        .comps-table td {{ padding: 10px 12px; border-bottom: 1px solid #e0e0e0; }}
        .valuation-box {{ background: linear-gradient(135deg, #2d5a7a, #1a3a52); color: white; padding: 20px; border-radius: 8px; margin: 30px 0; text-align: center; }}
        .value {{ font-size: 48px; font-weight: bold; margin: 10px 0; }}
        .zillow-comparison {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .variance {{ font-size: 18px; font-weight: bold; color: #ff6b6b; margin: 10px 0 0 0; }}
        .footer {{ margin-top: 40px; border-top: 1px solid #e0e0e0; padding-top: 20px; font-size: 12px; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Comparative Market Analysis (CMA)</h1>
        <p>{report.subject_property.address} | {report.market_context.market_name}</p>
    </div>

    <div class="property-overview">
        <div class="section">
            <h3>Subject Property</h3>
            <p><strong>Address:</strong> {report.subject_property.address}</p>
            <p><strong>Beds/Baths:</strong> {report.subject_property.beds}/{report.subject_property.baths}</p>
            <p><strong>Sq Ft:</strong> {report.subject_property.sqft:,.0f}</p>
            <p><strong>Year Built:</strong> {report.subject_property.year_built}</p>
            <p><strong>Condition:</strong> {report.subject_property.condition}</p>
        </div>

        <div class="section">
            <h3>Quick Stats</h3>
            <p><strong>Market Days:</strong> {report.market_context.dom_average} days average</p>
            <p><strong>Inventory:</strong> {report.market_context.inventory_level} homes</p>
            <p><strong>Price Trend:</strong> {trend_icon} {report.market_context.price_trend}% YoY</p>
            <p><strong>Report Date:</strong> {report.generated_at}</p>
        </div>
    </div>

    <h2>Comparable Properties Analysis</h2>
    <table class="comps-table">
        <thead>
            <tr>
                <th>Address</th>
                <th>Sale Date</th>
                <th>Sale Price</th>
                <th>Sq Ft</th>
                <th>$/Sq Ft</th>
                <th>Adj %</th>
                <th>Adj Value</th>
            </tr>
        </thead>
        <tbody>
            {comps_rows}
        </tbody>
    </table>

    <div class="valuation-box">
        <p>ESTIMATED MARKET VALUE</p>
        <div class="value">${report.estimated_value:,.0f}</div>
        <p>Range: ${report.value_range_low:,.0f} – ${report.value_range_high:,.0f}</p>
        <p style="margin-top: 15px; font-size: 12px; opacity: 0.9;">Confidence: {report.confidence_score}%</p>
    </div>

    <h2>Zillow vs. Reality</h2>
    <div class="zillow-comparison">
        <h4>Why Our Analysis Differs from Zillow</h4>
        <p>
            <strong>Zillow Zestimate:</strong> ${report.market_context.zillow_zestimate:,.0f}<br>
            <strong>Our AI Valuation:</strong> ${report.estimated_value:,.0f}
        </p>
        <div class="variance">
            Variance: ${report.zillow_variance_abs:,.0f} ({report.zillow_variance_percent}%)
        </div>
        <p style="margin-top: 15px; font-size: 13px;">
            {report.zillow_explanation}
        </p>
    </div>

    <h2>Market Narrative</h2>
    <p>{report.market_narrative}</p>

    <div class="footer">
        <div class="logo">EnterpriseHub Real Estate Intelligence</div>
        <p>Powered by AI analysis of MLS data, public records, and comparable market sales.</p>
    </div>
</body>
</html>
        """
        return html_content

    @staticmethod
    def generate_pdf_bytes(report: CMAReport) -> bytes:
        """
        Renders a CMA report to PDF bytes using reportlab.

        Returns:
            Raw PDF bytes (valid %PDF- header).

        Raises:
            PDFGenerationError: If rendering fails or output exceeds 2 MB.
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        )

        buffer = BytesIO()

        try:
            doc = SimpleDocTemplate(
                buffer, pagesize=letter,
                leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                topMargin=0.75 * inch, bottomMargin=0.75 * inch,
            )

            styles = getSampleStyleSheet()
            brand_color = colors.HexColor("#2d5a7a")
            warn_color = colors.HexColor("#ffc107")

            # Custom styles
            title_style = ParagraphStyle(
                "CMATitle", parent=styles["Title"],
                textColor=colors.white, fontSize=20, alignment=1,
                spaceAfter=4,
            )
            subtitle_style = ParagraphStyle(
                "CMASubtitle", parent=styles["Normal"],
                textColor=colors.white, fontSize=10, alignment=1,
            )
            heading_style = ParagraphStyle(
                "CMAHeading", parent=styles["Heading2"],
                textColor=brand_color, fontSize=14, spaceBefore=14,
                spaceAfter=6,
            )
            body_style = styles["Normal"]
            small_style = ParagraphStyle(
                "CMASmall", parent=styles["Normal"], fontSize=9,
            )
            value_style = ParagraphStyle(
                "CMAValue", parent=styles["Title"],
                textColor=colors.white, fontSize=28, alignment=1,
                spaceAfter=2, spaceBefore=2,
            )
            center_white = ParagraphStyle(
                "CenterWhite", parent=styles["Normal"],
                textColor=colors.white, alignment=1, fontSize=10,
            )

            elements = []

            # --- Header ---
            header_data = [[
                Paragraph("Comparative Market Analysis (CMA)", title_style),
            ], [
                Paragraph(
                    f"{report.subject_property.address} | {report.market_context.market_name}",
                    subtitle_style,
                ),
            ]]
            header_table = Table(header_data, colWidths=[7 * inch])
            header_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), brand_color),
                ("TOPPADDING", (0, 0), (-1, 0), 14),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 14),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 14))

            # --- Property overview (two-column table) ---
            prop = report.subject_property
            mkt = report.market_context
            trend_label = "UP" if mkt.price_trend > 0 else "DOWN"

            left_col = (
                f"<b>SUBJECT PROPERTY</b><br/>"
                f"<b>Address:</b> {prop.address}<br/>"
                f"<b>Beds/Baths:</b> {prop.beds}/{prop.baths}<br/>"
                f"<b>Sq Ft:</b> {prop.sqft:,}<br/>"
                f"<b>Year Built:</b> {prop.year_built}<br/>"
                f"<b>Condition:</b> {prop.condition}"
            )
            right_col = (
                f"<b>QUICK STATS</b><br/>"
                f"<b>Market Days:</b> {mkt.dom_average} days avg<br/>"
                f"<b>Inventory:</b> {mkt.inventory_level} homes<br/>"
                f"<b>Price Trend:</b> [{trend_label}] {mkt.price_trend}% YoY<br/>"
                f"<b>Report Date:</b> {report.generated_at}"
            )
            overview_data = [[
                Paragraph(left_col, small_style),
                Paragraph(right_col, small_style),
            ]]
            overview_table = Table(overview_data, colWidths=[3.4 * inch, 3.4 * inch])
            overview_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]))
            elements.append(overview_table)
            elements.append(Spacer(1, 10))

            # --- Comparables table ---
            elements.append(Paragraph("Comparable Properties Analysis", heading_style))

            comp_header = ["Address", "Sale Date", "Sale Price", "Sq Ft",
                           "$/Sq Ft", "Adj %", "Adj Value"]
            comp_data = [comp_header]
            for c in report.comparables:
                comp_data.append([
                    c.address, str(c.sale_date), f"${c.sale_price:,.0f}",
                    str(c.sqft), f"${c.price_per_sqft:.0f}",
                    f"{c.adjustment_percent}%", f"${c.adjusted_value:,.0f}",
                ])

            comp_table = Table(comp_data, repeatRows=1)
            comp_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), brand_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
            ]))
            elements.append(comp_table)
            elements.append(Spacer(1, 14))

            # --- Valuation box ---
            val_data = [
                [Paragraph("ESTIMATED MARKET VALUE", center_white)],
                [Paragraph(f"${report.estimated_value:,.0f}", value_style)],
                [Paragraph(
                    f"Range: ${report.value_range_low:,.0f} - ${report.value_range_high:,.0f}"
                    f"&nbsp;&nbsp;|&nbsp;&nbsp;Confidence: {report.confidence_score}%",
                    center_white,
                )],
            ]
            val_table = Table(val_data, colWidths=[7 * inch])
            val_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), brand_color),
                ("TOPPADDING", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]))
            elements.append(val_table)
            elements.append(Spacer(1, 14))

            # --- Zillow comparison ---
            elements.append(Paragraph("Zillow vs. Reality", heading_style))
            zillow_text = (
                f"<b>Zillow Zestimate:</b> ${mkt.zillow_zestimate:,.0f}<br/>"
                f"<b>Our AI Valuation:</b> ${report.estimated_value:,.0f}<br/>"
                f"<b>Variance:</b> ${report.zillow_variance_abs:,.0f} "
                f"({report.zillow_variance_percent}%)<br/><br/>"
                f"{report.zillow_explanation}"
            )
            zil_data = [[Paragraph(zillow_text, small_style)]]
            zil_table = Table(zil_data, colWidths=[7 * inch])
            zil_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff3cd")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            elements.append(zil_table)
            elements.append(Spacer(1, 10))

            # --- Market narrative ---
            elements.append(Paragraph("Market Narrative", heading_style))
            elements.append(Paragraph(report.market_narrative, body_style))
            elements.append(Spacer(1, 20))

            # --- Footer ---
            footer_style = ParagraphStyle(
                "CMAFooter", parent=styles["Normal"],
                fontSize=8, textColor=colors.grey, alignment=1,
            )
            elements.append(Paragraph(
                "<b>EnterpriseHub Real Estate Intelligence</b><br/>"
                "Powered by AI analysis of MLS data, public records, and comparable market sales.",
                footer_style,
            ))

            doc.build(elements)

        except PDFGenerationError:
            raise
        except Exception as exc:
            raise PDFGenerationError(f"reportlab rendering failed: {exc}") from exc

        pdf_bytes = buffer.getvalue()

        if len(pdf_bytes) == 0:
            raise PDFGenerationError("PDF generation produced empty output")

        if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
            raise PDFGenerationError(
                f"PDF size {len(pdf_bytes)} bytes exceeds {MAX_PDF_SIZE_BYTES} byte limit"
            )

        logger.info(f"Generated CMA PDF: {len(pdf_bytes)} bytes")
        return pdf_bytes

    @staticmethod
    def generate_pdf_url(report: CMAReport) -> str:
        """
        Mock generation of a PDF URL.
        In production, this would upload the rendered PDF to S3/GCS and return the link.
        """
        # For prototype: Create a data URL with the HTML content?
        # Or just a static mock link.
        # Let's try to return a data URL of the HTML for immediate preview.

        html = PDFRenderer.render_cma_html(report)
        b64_html = base64.b64encode(html.encode('utf-8')).decode('utf-8')
        return f"data:text/html;base64,{b64_html}"
