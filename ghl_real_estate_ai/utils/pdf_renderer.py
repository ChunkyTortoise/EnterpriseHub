from ghl_real_estate_ai.models.cma import CMAReport
from ghl_real_estate_ai.ghl_utils.logger import get_logger
import base64

logger = get_logger(__name__)

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
