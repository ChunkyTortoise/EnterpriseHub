"""
Inbound compliance pre-screener for Jorge bot endpoints.

Pure functions — no FastAPI, no database, no async I/O.
Imported by test_bots.py (router) AND by tests/api/test_test_bots_hardening.py
so that unit tests never pull in the full application import graph.

Covers four interception categories:
  1. TCPA opt-out        — must suppress further messages
  2. Fair Housing Act    — refuse discriminatory seller requests
  3. CCPA data-deletion  — acknowledge and suspend qualification
  4. Bot-identity        — honest disclosure when sincerely asked (SB 1001 / CA)
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple

# ── TCPA opt-out ──────────────────────────────────────────────────────────────
# Kept in sync with services/jorge/response_pipeline/stages/tcpa_opt_out.py
_TCPA_OPT_OUT_PHRASES: frozenset[str] = frozenset({
    "stop", "unsubscribe", "not interested", "opt out", "remove me",
    "don't contact me", "dont contact me", "no more messages", "cancel",
    "parar", "cancelar", "no más",
})

# Jorge spec §2.6 wording
_TCPA_RESPONSE = "No problem at all, reach out whenever you're ready"

# ── Fair Housing Act ──────────────────────────────────────────────────────────
_FAIR_HOUSING_PATTERNS: List[str] = [
    r"prefer\s+not\s+to\s+(?:sell|rent)\s+to",
    r"don[''t]*\s+want\s+.{0,30}\s+buyers?",
    r"no\s+.{0,20}\s+buyers?",
    r"only\s+(?:sell|rent)\s+to\s+(?:white|black|asian|hispanic|jewish|christian|muslim|gay|straight|american)",
    r"(?:racist|discriminat)\w*",
]

# ── Bot-identity (SB 1001) ────────────────────────────────────────────────────
# California SB 1001: a bot may not deny being a bot when sincerely asked.
# Pattern matches direct, sincere questions — not rhetorical or passing mentions.
_BOT_IDENTITY_RE = re.compile(
    r"\b("
    r"are you (a )?(real |actual |human |live )?(person|human|agent|bot|ai|robot|chatbot|computer)|"
    r"(is this|am i (talking|speaking|chatting) (to|with)) (a )?(real |actual |human |live )?(person|human|agent|bot|ai|robot)|"
    r"(you|this).{0,15}(real person|actual human|a bot|an ai|automated|a robot)|"
    r"(talk|speak|chat).{0,20}(human|real person|real agent|actual person)"
    r")\b",
    re.IGNORECASE,
)

_BOT_IDENTITY_RESPONSE = (
    "Just to be upfront — I'm an AI assistant, not a human agent. "
    "I'm here to help with your real estate questions. What can I do for you?"
)

# ── CCPA / right-to-deletion ──────────────────────────────────────────────────
_CCPA_PATTERNS: List[str] = [
    r"delete\s+(?:my\s+)?(?:data|information|records?)",
    r"remove\s+(?:my\s+)?(?:data|information|records?|profile)",
    r"\bccpa\b",
    r"right\s+to\s+be\s+forgotten",
    r"opt.?out\s+of\s+(?:data|information)",
    r"data\s+deletion\s+request",
]


def check_inbound_compliance(message: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
    """Return (intercepted, response_text, actions) for a user message.

    Returns ``(False, '', [])`` when the message is clean and should be
    forwarded to the bot engine.

    Called **before** the engine so the test scaffold behaves identically to
    the production pipeline (TCPAOptOutProcessor → ComplianceCheckProcessor).
    """
    msg_lower = message.lower().strip()

    # 1. TCPA opt-out — legally required short-circuit
    if any(phrase in msg_lower for phrase in _TCPA_OPT_OUT_PHRASES):
        return (
            True,
            _TCPA_RESPONSE,
            [
                {"type": "add_tag", "tag": "TCPA-Opt-Out"},
                {"type": "add_tag", "tag": "AI-Off"},
            ],
        )

    # 2. Fair Housing Act violation in inbound message
    for pattern in _FAIR_HOUSING_PATTERNS:
        if re.search(pattern, msg_lower, re.IGNORECASE):
            return (
                True,
                "I'm not able to assist with requests related to buyer or seller selection "
                "based on personal characteristics. Fair housing laws apply to all real estate "
                "transactions. I'm happy to help with questions about selling your home.",
                [
                    {"type": "add_tag", "tag": "Compliance-Review-Needed"},
                    {"type": "add_tag", "tag": "Fair-Housing-Alert"},
                ],
            )

    # 3. CCPA deletion request — acknowledge, suspend qualification
    for pattern in _CCPA_PATTERNS:
        if re.search(pattern, msg_lower, re.IGNORECASE):
            return (
                True,
                "We've received your data deletion request. Under CCPA we'll process it within "
                "45 days. For immediate assistance, contact privacy@jorgerealty.com.",
                [{"type": "add_tag", "tag": "CCPA-Deletion-Request"}],
            )

    # 4. Bot-identity — SB 1001: must not deny being a bot when sincerely asked
    if _BOT_IDENTITY_RE.search(message):
        return (True, _BOT_IDENTITY_RESPONSE, [])

    return (False, "", [])


def sanitise_message(message: str) -> str:
    """Sanitise an inbound message before passing it to the bot engine.

    If the raw message is valid JSON (e.g. ``{"motivation":"relocation"}``),
    wrap it as an opaque literal so the LLM extractor cannot parse its keys as
    qualification answers.  Empty / whitespace-only messages are returned
    unchanged; the engine handles them gracefully.
    """
    stripped = message.strip()
    if not stripped:
        return stripped
    try:
        json.loads(stripped)
        return f"[message: {repr(stripped)}]"
    except (json.JSONDecodeError, ValueError):
        pass
    return message
