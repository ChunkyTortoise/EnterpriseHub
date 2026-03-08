"""
SDR Message Personalizer — Claude-powered personalization for outreach messages.

Uses LLMClient.agenerate() for:
- SMS personalization (max 160 chars, TCPA-compliant)
- Email personalization (subject + body)
- Objection rebuttal personalization
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from ghl_real_estate_ai.core.llm_client import LLMClient
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

SMS_MAX_CHARS = 160


@dataclass
class EmailContent:
    """Structured email output."""

    subject: str
    body: str


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_SMS_SYSTEM_PROMPT = (
    "You are a warm, consultative real estate outreach assistant. "
    "Generate a personalized SMS message for a prospect. "
    "Rules:\n"
    "- MUST be under 160 characters total\n"
    "- Warm and friendly tone — never pushy or salesy\n"
    "- TCPA compliant: no false urgency, no misleading claims\n"
    "- Include the prospect's first name if available\n"
    "- End with a soft call-to-action (question or offer)\n"
    "- Return ONLY the message text, nothing else"
)

_EMAIL_SYSTEM_PROMPT = (
    "You are a warm, consultative real estate outreach assistant. "
    "Generate a personalized email for a prospect. "
    "Rules:\n"
    "- Warm and friendly tone — never pushy or salesy\n"
    "- CAN-SPAM compliant: honest subject line, real identity\n"
    "- Include the prospect's first name if available\n"
    "- Keep subject under 60 characters\n"
    "- Body should be 3-5 short paragraphs\n"
    "- End with a clear but soft call-to-action\n"
    "- Return the subject on the first line prefixed with 'Subject: '\n"
    "- Then a blank line, then the body"
)

_REBUTTAL_SYSTEM_PROMPT = (
    "You are a warm, consultative real estate outreach assistant. "
    "A prospect has raised an objection. Generate a personalized rebuttal. "
    "Rules:\n"
    "- Empathetic and respectful — acknowledge their concern first\n"
    "- Never argue or dismiss\n"
    "- Offer value without pressure\n"
    "- Keep under 280 characters for SMS delivery\n"
    "- If the objection is 'not_interested', respond with a polite exit only\n"
    "- Return ONLY the message text, nothing else"
)


class SDRMessagePersonalizer:
    """Claude-powered message personalization for SDR outreach."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self._llm = llm_client or LLMClient()

    async def personalize_sms(
        self,
        step: str,
        lead_profile: Dict[str, Any],
    ) -> str:
        """
        Generate a personalized SMS for the given outreach step.

        Returns a string of max 160 characters, TCPA-compliant.
        """
        prompt = (
            f"Outreach step: {step}\n"
            f"Lead profile: {_format_profile(lead_profile)}\n\n"
            "Write the SMS message."
        )
        try:
            response = await self._llm.agenerate(
                prompt=prompt,
                system_prompt=_SMS_SYSTEM_PROMPT,
                max_tokens=256,
                temperature=0.7,
            )
            text = response.content.strip()
            # Hard-truncate to SMS limit as a safety net
            if len(text) > SMS_MAX_CHARS:
                text = text[: SMS_MAX_CHARS - 1] + "\u2026"
            return text
        except Exception:
            logger.exception("[SDR] personalize_sms failed, using fallback")
            name = lead_profile.get("first_name", "there")
            return f"Hey {name}, just checking in! Have any real estate questions I can help with?"

    async def personalize_email(
        self,
        step: str,
        lead_profile: Dict[str, Any],
    ) -> Dict[str, str]:
        """
        Generate a personalized email with subject and body.

        Returns ``{"subject": str, "body": str}``.
        """
        prompt = (
            f"Outreach step: {step}\n"
            f"Lead profile: {_format_profile(lead_profile)}\n\n"
            "Write the email."
        )
        try:
            response = await self._llm.agenerate(
                prompt=prompt,
                system_prompt=_EMAIL_SYSTEM_PROMPT,
                max_tokens=1024,
                temperature=0.7,
            )
            ec = _parse_email_response(response.content)
            return {"subject": ec.subject, "body": ec.body}
        except Exception:
            logger.exception("[SDR] personalize_email failed, using fallback")
            name = lead_profile.get("first_name", "there")
            return {
                "subject": "Quick question about your real estate goals",
                "body": f"Hi {name},\n\nI wanted to reach out and see if you have any real estate questions I can help with.\n\nBest regards",
            }

    async def personalize_rebuttal(
        self,
        objection_type: str,
        message: str,
        lead_profile: Dict[str, Any],
    ) -> str:
        """
        Generate a personalized rebuttal for a classified objection.

        Returns a rebuttal message string.
        """
        prompt = (
            f"Objection type: {objection_type}\n"
            f"Prospect's message: {message}\n"
            f"Lead profile: {_format_profile(lead_profile)}\n\n"
            "Write the rebuttal message."
        )
        try:
            response = await self._llm.agenerate(
                prompt=prompt,
                system_prompt=_REBUTTAL_SYSTEM_PROMPT,
                max_tokens=512,
                temperature=0.7,
            )
            return response.content.strip()
        except Exception:
            logger.exception("[SDR] personalize_rebuttal failed, using fallback")
            return "I completely understand. If anything changes, don't hesitate to reach out!"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_profile(profile: Dict[str, Any]) -> str:
    """Format lead profile dict into a concise string for the LLM prompt."""
    parts = []
    if profile.get("first_name"):
        parts.append(f"Name: {profile['first_name']}")
    if profile.get("lead_type"):
        parts.append(f"Type: {profile['lead_type']}")
    if profile.get("source"):
        parts.append(f"Source: {profile['source']}")
    if profile.get("location"):
        parts.append(f"Location: {profile['location']}")
    if profile.get("frs_score") is not None:
        parts.append(f"FRS: {profile['frs_score']}")
    if profile.get("pcs_score") is not None:
        parts.append(f"PCS: {profile['pcs_score']}")
    return ", ".join(parts) if parts else "No profile data"


def _parse_email_response(content: str) -> EmailContent:
    """Parse LLM response into subject + body."""
    lines = content.strip().split("\n", 1)
    subject = "Following up on your real estate goals"
    body = content.strip()

    if lines and lines[0].lower().startswith("subject:"):
        subject = lines[0].split(":", 1)[1].strip()
        body = lines[1].strip() if len(lines) > 1 else ""

    return EmailContent(subject=subject, body=body)
