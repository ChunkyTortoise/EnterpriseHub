"""Warm Handoff Card Generator

Generates professional PDF qualification cards and structured text summaries
for Jorge bot handoffs. Cards provide agents with a quick visual summary
of lead qualification, including contact info, scores, and insights.

Performance target: <2s generation time
"""

import io
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# PDF generation imports
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)

# Brand colors
if REPORTLAB_AVAILABLE:
    BRAND_PRIMARY = colors.HexColor("#2563eb")
    BRAND_SECONDARY = colors.HexColor("#64748b")
    BRAND_ACCENT = colors.HexColor("#f97316")
    BRAND_SUCCESS = colors.HexColor("#22c55e")
    BRAND_WARNING = colors.HexColor("#eab308")
    BRAND_DANGER = colors.HexColor("#ef4444")
else:
    BRAND_PRIMARY = None
    BRAND_SECONDARY = None
    BRAND_ACCENT = None
    BRAND_SUCCESS = None
    BRAND_WARNING = None
    BRAND_DANGER = None


@dataclass
class HandoffCard:
    """Structured summary for handoff transitions."""

    # Source info
    source_bot: str
    target_bot: str
    handoff_reason: str
    confidence: float

    # Contact context
    contact_id: str
    contact_name: str = "Unknown"
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    # Conversation summary
    conversation_summary: str = ""
    key_facts: List[str] = field(default_factory=list)
    unanswered_questions: List[str] = field(default_factory=list)

    # Qualification data
    qualification_score: float = 0.0
    temperature: str = "unknown"
    budget_range: Optional[Dict[str, Any]] = None
    timeline: str = "unknown"
    property_address: Optional[str] = None

    # Recommended approach
    recommended_approach: str = ""
    priority_level: str = "normal"  # "urgent", "high", "normal", "low"

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_ghl_note(self) -> str:
        """Format as a GHL contact note."""
        lines = [
            f"=== 🤝 Handoff Card: {self.source_bot.title()} -> {self.target_bot.title()} ===",
            f"Reason: {self.handoff_reason}",
            f"Confidence: {self.confidence:.0%}",
            f"Priority: {self.priority_level.upper()}",
            "",
        ]
        if self.conversation_summary:
            lines.append(f"Summary: {self.conversation_summary}")
            lines.append("")

        if self.key_facts:
            lines.append("Key Facts:")
            for fact in self.key_facts:
                lines.append(f"  - {fact}")
            lines.append("")

        if self.unanswered_questions:
            lines.append("Open Questions:")
            for q in self.unanswered_questions:
                lines.append(f"  - {q}")
            lines.append("")

        lines.append(f"Qualification: {self.qualification_score:.0f}/100 | Temp: {self.temperature.upper()}")
        if self.budget_range:
            lines.append(f"Budget: ${self.budget_range.get('min', '?'):,} - ${self.budget_range.get('max', '?'):,}")
        if self.property_address:
            lines.append(f"Property: {self.property_address}")

        if self.timeline != "unknown":
            lines.append(f"Timeline: {self.timeline}")

        if self.recommended_approach:
            lines.append(f"\n💡 Recommended Approach: {self.recommended_approach}")

        lines.append(f"\nGenerated: {self.created_at}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)


class HandoffCardGenerator:
    """Generates professional PDF and text handoff cards."""

    PRIORITY_THRESHOLDS = {
        0.9: "urgent",
        0.8: "high",
        0.6: "normal",
        0.0: "low",
    }

    def __init__(self):
        """Initialize styles if reportlab is available."""
        if REPORTLAB_AVAILABLE:
            self.styles = getSampleStyleSheet()
            self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        """Set up custom paragraph styles for the PDF."""
        # Header style
        self.styles.add(
            ParagraphStyle(
                name="CardHeader",
                parent=self.styles["Heading1"],
                fontSize=18,
                textColor=BRAND_PRIMARY,
                spaceAfter=12,
                alignment=1,  # Center
            )
        )
        # Subheader style
        self.styles.add(
            ParagraphStyle(
                name="CardSubheader",
                parent=self.styles["Heading2"],
                fontSize=14,
                textColor=BRAND_SECONDARY,
                spaceAfter=8,
            )
        )
        # Body text style
        self.styles.add(
            ParagraphStyle(
                name="CardBody",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=6,
            )
        )

    def generate_card(self, handoff_data: Dict[str, Any]) -> HandoffCard:
        """Generate a HandoffCard object from handoff data."""
        source_bot = handoff_data.get("source_bot", "unknown")
        target_bot = handoff_data.get("target_bot", "unknown")
        confidence = handoff_data.get("confidence", 0.0)

        enriched = handoff_data.get("enriched_context")
        if hasattr(enriched, "__dataclass_fields__"):
            enriched_dict = asdict(enriched)
        else:
            enriched_dict = enriched or {}

        card = HandoffCard(
            source_bot=source_bot,
            target_bot=target_bot,
            handoff_reason=handoff_data.get("reason", "intent_detected"),
            confidence=confidence,
            contact_id=handoff_data.get("contact_id", "Unknown"),
            contact_name=handoff_data.get("contact_name", "Unknown"),
            contact_email=handoff_data.get("contact_email"),
            contact_phone=handoff_data.get("contact_phone"),
            priority_level=self._determine_priority(confidence),
            qualification_score=enriched_dict.get("source_qualification_score", 0.0),
            temperature=enriched_dict.get("source_temperature", "unknown"),
            budget_range=enriched_dict.get("budget_range"),
            property_address=enriched_dict.get("property_address"),
            conversation_summary=enriched_dict.get("conversation_summary", ""),
            timeline=enriched_dict.get("urgency_level", "unknown"),
        )

        key_insights = enriched_dict.get("key_insights", {})
        if key_insights:
            card.key_facts = [f"{k.replace('_', ' ').title()}: {v}" for k, v in key_insights.items()]

        card.recommended_approach = self._generate_approach(card)
        return card

    def generate_pdf(self, card: HandoffCard) -> bytes:
        """Generate a PDF version of the handoff card."""
        if not REPORTLAB_AVAILABLE:
            logger.error("ReportLab not available, cannot generate PDF")
            return b""

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        story = []

        # Header
        story.append(Paragraph("🤝 Warm Handoff Qualification Card", self.styles["CardHeader"]))
        story.append(Spacer(1, 0.2 * inch))

        # Contact Table
        story.append(Paragraph("Contact Information", self.styles["CardSubheader"]))
        contact_data = [
            ["Name:", card.contact_name],
            ["Email:", card.contact_email or "N/A"],
            ["Phone:", card.contact_phone or "N/A"],
            ["Contact ID:", card.contact_id],
        ]
        story.append(self._build_table(contact_data))
        story.append(Spacer(1, 0.2 * inch))

        # Handoff Table
        story.append(Paragraph("Handoff Details", self.styles["CardSubheader"]))
        handoff_data = [
            ["Route:", f"{card.source_bot.title()} → {card.target_bot.title()}"],
            ["Confidence:", f"{card.confidence:.1%}"],
            ["Priority:", card.priority_level.upper()],
            ["Reason:", card.handoff_reason],
        ]
        story.append(self._build_table(handoff_data))
        story.append(Spacer(1, 0.2 * inch))

        # Qualification Table
        story.append(Paragraph("Qualification Metrics", self.styles["CardSubheader"]))
        qual_data = [
            ["Score:", f"{card.qualification_score:.1f}/100"],
            ["Temperature:", card.temperature.upper()],
            ["Timeline:", card.timeline.replace("_", " ").title()],
        ]
        if card.budget_range:
            budget_str = f"${card.budget_range.get('min', 0):,} - ${card.budget_range.get('max', 0):,}"
            qual_data.append(["Budget:", budget_str])

        story.append(self._build_table(qual_data))
        story.append(Spacer(1, 0.2 * inch))

        # Summary
        if card.conversation_summary:
            story.append(Paragraph("Conversation Summary", self.styles["CardSubheader"]))
            story.append(Paragraph(card.conversation_summary, self.styles["CardBody"]))
            story.append(Spacer(1, 0.2 * inch))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _build_table(self, data: List[List[str]]) -> Any:
        table = Table(data, colWidths=[1.5 * inch, 5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 10),
                    ("FONT", (1, 0), (1, -1), "Helvetica", 10),
                    ("TEXTCOLOR", (0, 0), (0, -1), BRAND_SECONDARY),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return table

    def _determine_priority(self, confidence: float) -> str:
        for threshold, priority in sorted(self.PRIORITY_THRESHOLDS.items(), reverse=True):
            if confidence >= threshold:
                return priority
        return "normal"

    def _generate_approach(self, card: HandoffCard) -> str:
        parts = []
        if card.temperature in ("hot", "warm"):
            parts.append("Contact is highly engaged")
        if card.qualification_score > 70:
            parts.append("well-qualified")
        elif card.qualification_score > 40:
            parts.append("partially qualified")

        if card.unanswered_questions:
            parts.append(f"address {len(card.unanswered_questions)} open questions")

        return ". ".join(parts).capitalize() + "." if parts else "Follow standard qualification script."


# Convenience function
def generate_card(handoff_data: Dict[str, Any]) -> bytes:
    """Generate a PDF handoff card (convenience function)."""
    generator = HandoffCardGenerator()
    card = generator.generate_card(handoff_data)
    return generator.generate_pdf(card)


def get_handoff_card_generator() -> HandoffCardGenerator:
    """Get a singleton instance of HandoffCardGenerator."""
    return HandoffCardGenerator()
