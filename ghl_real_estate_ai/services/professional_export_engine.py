"""
Professional Export Engine

Generates branded market reports, CMA summaries, and client presentations
in multiple formats (HTML, CSV, plain text).  Designed for Jorge's Rancho
Cucamonga real-estate practice with template-based customisation.

Usage::

    engine = get_export_engine()
    report = await engine.generate_market_report(
        neighborhood="victoria",
        report_type="monthly",
    )
    cma = await engine.generate_cma_report(
        address="123 Haven Ave",
        property_data={...},
        comparables=[...],
    )
    csv_data = await engine.export_leads_csv(leads=[...])
"""

import csv
import io
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class ReportFormat(Enum):
    HTML = "html"
    CSV = "csv"
    TEXT = "text"


class ReportType(Enum):
    MARKET_MONTHLY = "monthly"
    MARKET_WEEKLY = "weekly"
    CMA = "cma"
    CLIENT_PRESENTATION = "presentation"
    LEAD_EXPORT = "lead_export"


@dataclass
class ExportResult:
    """Result of an export/report generation."""

    report_id: str
    report_type: ReportType
    format: ReportFormat
    content: str
    filename: str
    size_bytes: int
    generated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CMAComparable:
    """Comparable property for CMA report."""

    address: str
    sale_price: int
    sale_date: str
    sqft: int
    bedrooms: int
    bathrooms: float
    price_per_sqft: int
    distance_miles: float
    adjustments: Dict[str, int] = field(default_factory=dict)


@dataclass
class BrandingConfig:
    """Branding configuration for reports."""

    agent_name: str = "Jorge"
    brokerage: str = "Rancho Cucamonga Real Estate"
    phone: str = "(909) 555-0100"
    email: str = "jorge@rcrealestate.com"
    logo_url: str = ""
    accent_color: str = "#2563EB"
    tagline: str = "Your Trusted Rancho Cucamonga Real Estate Expert"


# ---------------------------------------------------------------------------
# HTML templates
# ---------------------------------------------------------------------------

MARKET_REPORT_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{ font-family: 'Segoe UI', Tahoma, sans-serif; margin: 40px; color: #1a1a1a; }}
.header {{ background: {accent_color}; color: white; padding: 24px; border-radius: 8px; }}
.header h1 {{ margin: 0; font-size: 24px; }}
.header p {{ margin: 4px 0 0; opacity: 0.9; }}
.section {{ margin: 24px 0; }}
.section h2 {{ color: {accent_color}; border-bottom: 2px solid {accent_color}; padding-bottom: 8px; }}
table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
th {{ background: #f3f4f6; text-align: left; padding: 10px; border-bottom: 2px solid #e5e7eb; }}
td {{ padding: 10px; border-bottom: 1px solid #e5e7eb; }}
.metric {{ display: inline-block; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin: 8px; min-width: 140px; text-align: center; }}
.metric .value {{ font-size: 28px; font-weight: bold; color: {accent_color}; }}
.metric .label {{ font-size: 12px; color: #6b7280; margin-top: 4px; }}
.footer {{ margin-top: 40px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; }}
</style>
</head>
<body>
<div class="header">
  <h1>{title}</h1>
  <p>{subtitle}</p>
</div>
{body}
<div class="footer">
  <p>Prepared by {agent_name} | {brokerage} | {phone} | {email}</p>
  <p>{tagline}</p>
</div>
</body>
</html>"""

CMA_REPORT_HTML = """<div class="section">
<h2>Subject Property</h2>
<p><strong>{address}</strong></p>
<table>
<tr><td>Bedrooms</td><td>{bedrooms}</td><td>Bathrooms</td><td>{bathrooms}</td></tr>
<tr><td>Square Feet</td><td>{sqft:,}</td><td>Year Built</td><td>{year_built}</td></tr>
<tr><td>Lot Size</td><td>{lot_size}</td><td>Condition</td><td>{condition}</td></tr>
</table>
</div>
<div class="section">
<h2>Comparable Sales</h2>
<table>
<tr><th>Address</th><th>Sale Price</th><th>$/SqFt</th><th>Beds</th><th>Baths</th><th>SqFt</th><th>Adjusted</th></tr>
{comp_rows}
</table>
</div>
<div class="section">
<h2>Estimated Value Range</h2>
<div class="metric"><div class="value">${low_estimate:,}</div><div class="label">Low</div></div>
<div class="metric"><div class="value">${mid_estimate:,}</div><div class="label">Estimated</div></div>
<div class="metric"><div class="value">${high_estimate:,}</div><div class="label">High</div></div>
</div>"""


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class ProfessionalExportEngine:
    """
    Generates branded reports and data exports.

    Supports HTML market reports, CMA reports, client presentations,
    and CSV/text data exports.
    """

    def __init__(self, branding: Optional[BrandingConfig] = None):
        self.branding = branding or BrandingConfig()
        self._report_counter = 0

    # ------------------------------------------------------------------
    # Market report
    # ------------------------------------------------------------------

    async def generate_market_report(
        self,
        neighborhood: str,
        report_type: str = "monthly",
        market_data: Optional[Dict[str, Any]] = None,
        format: str = "html",
    ) -> ExportResult:
        """Generate a branded market report for a neighborhood."""
        self._report_counter += 1
        report_id = f"rpt_{self._report_counter}_{int(time.time())}"
        fmt = self._resolve_format(format)
        rtype = self._resolve_report_type(report_type)

        data = market_data or self._default_market_data(neighborhood)

        if fmt == ReportFormat.HTML:
            content = self._render_market_html(neighborhood, data, rtype)
        elif fmt == ReportFormat.CSV:
            content = self._render_market_csv(neighborhood, data)
        else:
            content = self._render_market_text(neighborhood, data)

        filename = f"market_report_{neighborhood}_{report_type}.{fmt.value}"

        return ExportResult(
            report_id=report_id,
            report_type=rtype,
            format=fmt,
            content=content,
            filename=filename,
            size_bytes=len(content.encode("utf-8")),
            metadata={"neighborhood": neighborhood},
        )

    # ------------------------------------------------------------------
    # CMA report
    # ------------------------------------------------------------------

    async def generate_cma_report(
        self,
        address: str,
        property_data: Dict[str, Any],
        comparables: List[Dict[str, Any]],
        format: str = "html",
    ) -> ExportResult:
        """Generate a Comparative Market Analysis report."""
        self._report_counter += 1
        report_id = f"cma_{self._report_counter}_{int(time.time())}"
        fmt = self._resolve_format(format)

        comps = [self._parse_comparable(c) for c in comparables]

        if fmt == ReportFormat.HTML:
            content = self._render_cma_html(address, property_data, comps)
        else:
            content = self._render_cma_text(address, property_data, comps)

        filename = f"cma_{address.replace(' ', '_')[:30]}.{fmt.value}"

        return ExportResult(
            report_id=report_id,
            report_type=ReportType.CMA,
            format=fmt,
            content=content,
            filename=filename,
            size_bytes=len(content.encode("utf-8")),
            metadata={"address": address, "comparables_count": len(comps)},
        )

    # ------------------------------------------------------------------
    # Lead export
    # ------------------------------------------------------------------

    async def export_leads_csv(self, leads: List[Dict[str, Any]]) -> ExportResult:
        """Export leads data as CSV."""
        self._report_counter += 1
        report_id = f"leads_{self._report_counter}_{int(time.time())}"

        if not leads:
            content = "No leads to export"
        else:
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=leads[0].keys())
            writer.writeheader()
            writer.writerows(leads)
            content = output.getvalue()

        return ExportResult(
            report_id=report_id,
            report_type=ReportType.LEAD_EXPORT,
            format=ReportFormat.CSV,
            content=content,
            filename=f"leads_export_{int(time.time())}.csv",
            size_bytes=len(content.encode("utf-8")),
            metadata={"lead_count": len(leads)},
        )

    # ------------------------------------------------------------------
    # Client presentation
    # ------------------------------------------------------------------

    async def generate_presentation(
        self,
        client_name: str,
        sections: List[Dict[str, str]],
    ) -> ExportResult:
        """Generate an HTML client presentation."""
        self._report_counter += 1
        report_id = f"pres_{self._report_counter}_{int(time.time())}"

        body_parts = []
        for section in sections:
            title = section.get("title", "")
            content = section.get("content", "")
            body_parts.append(f'<div class="section"><h2>{title}</h2><p>{content}</p></div>')

        body = "\n".join(body_parts)
        html = MARKET_REPORT_HTML.format(
            title=f"Presentation for {client_name}",
            subtitle=f"Prepared by {self.branding.agent_name}",
            accent_color=self.branding.accent_color,
            body=body,
            agent_name=self.branding.agent_name,
            brokerage=self.branding.brokerage,
            phone=self.branding.phone,
            email=self.branding.email,
            tagline=self.branding.tagline,
        )

        return ExportResult(
            report_id=report_id,
            report_type=ReportType.CLIENT_PRESENTATION,
            format=ReportFormat.HTML,
            content=html,
            filename=f"presentation_{client_name.replace(' ', '_')}.html",
            size_bytes=len(html.encode("utf-8")),
            metadata={"client": client_name, "sections": len(sections)},
        )

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------

    def _render_market_html(self, neighborhood: str, data: Dict[str, Any], rtype: ReportType) -> str:
        pretty_name = neighborhood.replace("_", " ").title()
        period = "Monthly" if rtype == ReportType.MARKET_MONTHLY else "Weekly"

        metrics_html = ""
        for label, key, prefix, suffix in [
            ("Median Price", "median_price", "$", ""),
            ("Avg DOM", "avg_dom", "", " days"),
            ("Inventory", "inventory", "", " listings"),
            ("Price/SqFt", "avg_sqft_price", "$", ""),
            ("Appreciation", "appreciation_1yr", "", ""),
        ]:
            val = data.get(key, 0)
            if key == "appreciation_1yr":
                display = f"{val * 100:.1f}%"
            elif isinstance(val, int) and val > 1000:
                display = f"{prefix}{val:,}{suffix}"
            else:
                display = f"{prefix}{val}{suffix}"
            metrics_html += (
                f'<div class="metric"><div class="value">{display}</div><div class="label">{label}</div></div>\n'
            )

        body = f'<div class="section"><h2>Market Overview — {pretty_name}</h2>\n{metrics_html}</div>'

        return MARKET_REPORT_HTML.format(
            title=f"{period} Market Report: {pretty_name}",
            subtitle=f"Rancho Cucamonga Real Estate Intelligence",
            accent_color=self.branding.accent_color,
            body=body,
            agent_name=self.branding.agent_name,
            brokerage=self.branding.brokerage,
            phone=self.branding.phone,
            email=self.branding.email,
            tagline=self.branding.tagline,
        )

    @staticmethod
    def _render_market_csv(neighborhood: str, data: Dict[str, Any]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Metric", "Value"])
        for key, val in data.items():
            writer.writerow([key, val])
        return output.getvalue()

    @staticmethod
    def _render_market_text(neighborhood: str, data: Dict[str, Any]) -> str:
        pretty = neighborhood.replace("_", " ").title()
        lines = [f"Market Report: {pretty}", "=" * 40]
        for key, val in data.items():
            label = key.replace("_", " ").title()
            if key == "appreciation_1yr":
                lines.append(f"{label}: {val * 100:.1f}%")
            elif isinstance(val, int) and val > 1000:
                lines.append(f"{label}: ${val:,}")
            else:
                lines.append(f"{label}: {val}")
        return "\n".join(lines)

    def _render_cma_html(
        self,
        address: str,
        prop: Dict[str, Any],
        comps: List[CMAComparable],
    ) -> str:
        comp_rows = ""
        for c in comps:
            adj_total = sum(c.adjustments.values())
            adjusted_price = c.sale_price + adj_total
            comp_rows += (
                f"<tr><td>{c.address}</td><td>${c.sale_price:,}</td>"
                f"<td>${c.price_per_sqft}</td><td>{c.bedrooms}</td>"
                f"<td>{c.bathrooms}</td><td>{c.sqft:,}</td>"
                f"<td>${adjusted_price:,}</td></tr>\n"
            )

        adjusted_prices = [c.sale_price + sum(c.adjustments.values()) for c in comps]
        if adjusted_prices:
            mid = int(sum(adjusted_prices) / len(adjusted_prices))
            low = min(adjusted_prices)
            high = max(adjusted_prices)
        else:
            mid = prop.get("estimated_value", 0)
            low = int(mid * 0.95)
            high = int(mid * 1.05)

        cma_body = CMA_REPORT_HTML.format(
            address=address,
            bedrooms=prop.get("bedrooms", "N/A"),
            bathrooms=prop.get("bathrooms", "N/A"),
            sqft=prop.get("sqft", 0),
            year_built=prop.get("year_built", "N/A"),
            lot_size=prop.get("lot_size", "N/A"),
            condition=prop.get("condition", "Average"),
            comp_rows=comp_rows,
            low_estimate=low,
            mid_estimate=mid,
            high_estimate=high,
        )

        return MARKET_REPORT_HTML.format(
            title=f"Comparative Market Analysis",
            subtitle=address,
            accent_color=self.branding.accent_color,
            body=cma_body,
            agent_name=self.branding.agent_name,
            brokerage=self.branding.brokerage,
            phone=self.branding.phone,
            email=self.branding.email,
            tagline=self.branding.tagline,
        )

    @staticmethod
    def _render_cma_text(
        address: str,
        prop: Dict[str, Any],
        comps: List[CMAComparable],
    ) -> str:
        lines = [f"CMA Report: {address}", "=" * 40]
        lines.append(f"Beds: {prop.get('bedrooms')} | Baths: {prop.get('bathrooms')} | SqFt: {prop.get('sqft', 0):,}")
        lines.append("\nComparables:")
        for c in comps:
            adj = sum(c.adjustments.values())
            lines.append(f"  {c.address}: ${c.sale_price:,} (adj: ${c.sale_price + adj:,})")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_comparable(data: Dict[str, Any]) -> CMAComparable:
        sqft = data.get("sqft", 1)
        price = data.get("sale_price", 0)
        return CMAComparable(
            address=data.get("address", "Unknown"),
            sale_price=price,
            sale_date=data.get("sale_date", ""),
            sqft=sqft,
            bedrooms=data.get("bedrooms", 0),
            bathrooms=data.get("bathrooms", 0),
            price_per_sqft=int(price / max(sqft, 1)),
            distance_miles=data.get("distance_miles", 0),
            adjustments=data.get("adjustments", {}),
        )

    @staticmethod
    def _default_market_data(neighborhood: str) -> Dict[str, Any]:
        from ghl_real_estate_ai.services.real_time_market_intelligence import (
            NEIGHBORHOOD_BASELINES,
            Neighborhood,
        )

        clean = neighborhood.lower().replace(" ", "_")
        for nb in Neighborhood:
            if nb.value == clean:
                return dict(NEIGHBORHOOD_BASELINES[nb])
        return dict(NEIGHBORHOOD_BASELINES[Neighborhood.CENTRAL_PARK])

    @staticmethod
    def _resolve_format(fmt: str) -> ReportFormat:
        try:
            return ReportFormat(fmt.lower())
        except ValueError:
            return ReportFormat.HTML

    @staticmethod
    def _resolve_report_type(rtype: str) -> ReportType:
        try:
            return ReportType(rtype.lower())
        except ValueError:
            return ReportType.MARKET_MONTHLY


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_engine: Optional[ProfessionalExportEngine] = None


def get_export_engine() -> ProfessionalExportEngine:
    global _engine
    if _engine is None:
        _engine = ProfessionalExportEngine()
    return _engine
