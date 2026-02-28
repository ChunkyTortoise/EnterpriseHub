"""
Live E2E evaluation — Jorge Seller Bot on Render
=================================================

Grades each bot reply against four criteria:

  CLEAN       no AI disclosure footer or AI self-identification
  PROGRESSION right question at the right turn
               opener → Q1 motivation → Q2 timeline → Q3 condition → Q4 price
  PERSONA     human-sounding; no robotic customer-service boilerplate
  FORMAT      SMS-length (≤320 chars), no emojis

The module-scoped `seller_transcript` fixture runs the full 10-turn conversation
once and stores every (label, user_msg, bot_reply, latency) tuple. Individual
tests then assert on the stored transcript with no extra service calls.

Run:
    pytest tests/e2e/test_seller_bot_e2e.py -v -s --no-cov --timeout=600

Skip in normal CI (already guarded by `--run-e2e` convention):
    pytest -m "not e2e" ...
"""

import hashlib
import hmac
import json
import time
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import pytest

# ── Service config ─────────────────────────────────────────────────────────────

BASE_URL     = "https://jorge-realty-ai-xxdf.onrender.com"
HMAC_SECRET  = "ffb42fb9b69801686e04edbcb2f54f4f123eb3389bb1dedf9317930a0518bd10"
LOCATION_ID  = "3xt4qayAh35BlDLaUv7P"
SELLER_TAG   = "Needs Qualifying"
TURN_TIMEOUT = 90   # seconds — warm instance LLM calls take 40-60 s

# ── Seller conversation script ─────────────────────────────────────────────────
# T1 primes the bot; T2-T5 answer Jorge's 4 core questions in order;
# T6-T9 supply post-qualification details; T10 confirms scheduling.

SELLER_SCRIPT: List[Tuple[str, str]] = [
    ("T1-opener",    "Hi I want to sell my house"),
    ("T2-motivation","Relocating for work to Seattle, need to sell within 3 months"),
    ("T3-timeline",  "3 months ideally, sooner is better if price is right"),
    ("T4-condition", "Good condition — updated kitchen 2022, new HVAC, needs carpet"),
    ("T5-price",     "Hoping for around $650,000"),
    ("T6-liens",     "One mortgage, $380k remaining, no other liens"),
    ("T7-repairs",   "Cosmetic only — carpet and exterior paint, about $5k"),
    ("T8-history",   "Never listed before, first time selling"),
    ("T9-decision",  "I am the sole decision maker, wife on title and fully agrees"),
    ("T10-schedule", "Afternoon works for me, around 2pm"),
]

# ── Grading constants ──────────────────────────────────────────────────────────

AI_DISCLOSURE_PHRASES = [
    "[AI-assisted message]",
    "[ai-assisted message]",
    "AI assistant",
    "I am an AI",
    "I'm an AI",
    "as an AI",
    "This is Jorge's AI",
    "artificial intelligence",
    "language model",
    "chatbot",
    "bot here",
    "virtual assistant",
]

ROBOTIC_PHRASES = [
    "I understand your concern",
    "Thank you for sharing",
    "I'm here to help",
    "How can I assist",
    "Certainly!",
    "Absolutely!",
    "Great question",
    "Of course!",
    "I would be happy to",
    "Feel free to",
    "Please don't hesitate",
]

# Expected keyword signals per reply turn.
# The bot asks the *next* question after the user's answer, so:
#   T1 reply = Q1 (motivation), T2 reply = Q2 (timeline), etc.
Q1_KEYWORDS = ["making you think", "why sell", "where would you", "reason for", "move to"]
Q2_KEYWORDS = ["30", "45", "days", "timeline", "work for you"]
Q3_KEYWORDS = ["condition", "move in ready", "ready", "need some work", "describe", "fixer"]
Q4_KEYWORDS = ["price", "feel good", "number", "looking for", "expecting", "what price", "mind"]

# Keywords that confirm post-qualification handoff (expected after T5)
HANDOFF_KEYWORDS = [
    "morning", "afternoon", "schedule", "call", "team",
    "based on your answers", "exactly who we help", "next step",
    "get you scheduled", "discuss your options",
]

# Q keywords that should NOT appear after all 4 questions are answered
LINGERING_Q_KEYWORDS = ["making you think", "30 to 45", "move in ready", "feel good about selling"]

SMS_MAX_CHARS = 320  # Jorge's hard limit per the system prompt

# ── TurnResult dataclass ───────────────────────────────────────────────────────

@dataclass
class TurnResult:
    label:     str
    user_msg:  str
    bot_reply: Optional[str]
    latency:   float
    error:     Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.bot_reply is not None and self.error is None


# ── Session helper ─────────────────────────────────────────────────────────────

class SellerSession:
    """
    Sends HMAC-signed webhook POSTs to the Jorge seller bot and reads
    the bot reply from the JSON response body — no GHL API polling needed.
    """

    def __init__(self, contact_id: str) -> None:
        self.contact_id = contact_id

    def send(self, user_message: str, timeout: int = TURN_TIMEOUT) -> Tuple[Optional[str], Optional[str]]:
        """POST one inbound SMS. Returns (bot_reply, error_string)."""
        payload = json.dumps({
            "type": "InboundMessage",
            "locationId": LOCATION_ID,
            "contactId": self.contact_id,
            "tags": [SELLER_TAG],
            "message": {
                "body": user_message,
                "type": "SMS",
                "direction": "inbound",
            },
        }).encode()

        sig = hmac.new(HMAC_SECRET.encode(), payload, hashlib.sha256).hexdigest()
        req = urllib.request.Request(
            f"{BASE_URL}/api/ghl/webhook",
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "x-ghl-signature": sig,
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = json.loads(r.read())
            if body.get("success"):
                return body.get("message", ""), None
            return None, f"success=False body={body}"
        except urllib.error.HTTPError as exc:
            return None, f"HTTP {exc.code}: {exc.reason}"
        except Exception as exc:
            return None, str(exc)


# ── Module-scoped transcript fixture ──────────────────────────────────────────

@pytest.fixture(scope="module")
def seller_transcript() -> List[TurnResult]:
    """
    Run the full 10-turn seller conversation once per test module.
    Individual tests assert on the stored results; no extra calls are made.

    Uses a unique synthetic contact ID per run so we never pollute the
    production test contact's conversation history.
    """
    contact_id = f"e2e-seller-{int(time.time())}"
    session    = SellerSession(contact_id)
    results: List[TurnResult] = []

    print(f"\n{'='*62}")
    print(f"  SELLER BOT E2E  contact_id={contact_id}")
    print(f"{'='*62}")

    for label, user_msg in SELLER_SCRIPT:
        print(f"\n── YOU [{label}]: {user_msg}")
        t0 = time.time()
        reply, error = session.send(user_msg)
        latency = time.time() - t0

        results.append(TurnResult(
            label=label, user_msg=user_msg,
            bot_reply=reply, latency=latency, error=error,
        ))

        if error:
            print(f"   BOT: !! ERROR — {error}")
        else:
            print(f"   BOT ({latency:.1f}s): {reply}")

    print(f"\n{'='*62}")
    print(f"  TRANSCRIPT COMPLETE — {len(results)} turns")
    print(f"{'='*62}\n")
    return results


# ── Helper ─────────────────────────────────────────────────────────────────────

def _turn(transcript: List[TurnResult], label: str) -> TurnResult:
    """Return the named turn, or skip the test if that turn errored."""
    for t in transcript:
        if t.label == label:
            if not t.ok:
                pytest.skip(f"Turn {label} produced no reply: {t.error}")
            return t
    pytest.skip(f"Turn {label} not found in transcript")


# ── Group 1: Service reachability ─────────────────────────────────────────────

@pytest.mark.e2e
def test_service_health():
    """Health endpoint must return 200 and status=healthy."""
    try:
        with urllib.request.urlopen(f"{BASE_URL}/health", timeout=15) as r:
            status_code = r.status
            body = json.loads(r.read())
    except Exception as exc:
        pytest.fail(f"Health check raised: {exc}")

    assert status_code == 200, f"Expected 200, got {status_code}"
    assert body.get("status") == "healthy", f"Unexpected health body: {body}"


# ── Group 2: AI disclosure (hard requirement, all turns) ──────────────────────

@pytest.mark.e2e
def test_no_ai_disclosure(seller_transcript):
    """
    No reply may identify or hint at AI origin.
    Commits 8ccf48e5 and affdbbca removed the disclosure footer and prefix;
    this test guards against regressions in both.
    """
    failures = []
    for t in seller_transcript:
        if not t.ok:
            continue
        reply_lower = t.bot_reply.lower()
        for phrase in AI_DISCLOSURE_PHRASES:
            if phrase.lower() in reply_lower:
                failures.append(f"[{t.label}] found {phrase!r}  →  {t.bot_reply!r}")

    assert not failures, (
        f"AI disclosure detected in {len(failures)} turn(s):\n" + "\n".join(failures)
    )


# ── Group 3: Question progression ─────────────────────────────────────────────

@pytest.mark.e2e
def test_t1_opener_elicits_motivation_question(seller_transcript):
    """
    T1 reply: bot receives 'I want to sell my house' and must ask
    Jorge's Q1 — motivation / where would you move to.
    """
    t = _turn(seller_transcript, "T1-opener")
    reply_lower = t.bot_reply.lower()
    assert any(kw in reply_lower for kw in Q1_KEYWORDS), (
        f"T1 reply should ask motivation (Q1).\n"
        f"Got: {t.bot_reply!r}\n"
        f"Expected at least one of: {Q1_KEYWORDS}"
    )


@pytest.mark.e2e
def test_t2_motivation_answer_elicits_timeline_question(seller_transcript):
    """
    T2 reply: motivation answered → bot must ask Q2 (30-to-45-day timeline).
    """
    t = _turn(seller_transcript, "T2-motivation")
    reply_lower = t.bot_reply.lower()
    assert any(kw in reply_lower for kw in Q2_KEYWORDS), (
        f"T2 reply should ask 30-45 day timeline (Q2).\n"
        f"Got: {t.bot_reply!r}\n"
        f"Expected at least one of: {Q2_KEYWORDS}"
    )


@pytest.mark.e2e
def test_t3_timeline_answer_elicits_condition_question(seller_transcript):
    """
    T3 reply: timeline answered → bot must ask Q3 (property condition).
    """
    t = _turn(seller_transcript, "T3-timeline")
    reply_lower = t.bot_reply.lower()
    assert any(kw in reply_lower for kw in Q3_KEYWORDS), (
        f"T3 reply should ask property condition (Q3).\n"
        f"Got: {t.bot_reply!r}\n"
        f"Expected at least one of: {Q3_KEYWORDS}"
    )


@pytest.mark.e2e
def test_t4_condition_answer_elicits_price_question(seller_transcript):
    """
    T4 reply: condition answered → bot must ask Q4 (price expectations).
    """
    t = _turn(seller_transcript, "T4-condition")
    reply_lower = t.bot_reply.lower()
    assert any(kw in reply_lower for kw in Q4_KEYWORDS), (
        f"T4 reply should ask price expectations (Q4).\n"
        f"Got: {t.bot_reply!r}\n"
        f"Expected at least one of: {Q4_KEYWORDS}"
    )


@pytest.mark.e2e
def test_t5_after_all_questions_moves_to_handoff(seller_transcript):
    """
    T5 reply: all 4 questions answered → bot must NOT ask another
    qualification question; it should offer scheduling or classify as Hot.
    """
    t = _turn(seller_transcript, "T5-price")
    reply_lower = t.bot_reply.lower()

    still_qualifying = any(kw in reply_lower for kw in LINGERING_Q_KEYWORDS)
    assert not still_qualifying, (
        f"T5 reply loops back into qualification after all 4 Qs answered.\n"
        f"Got: {t.bot_reply!r}"
    )

    assert any(kw in reply_lower for kw in HANDOFF_KEYWORDS), (
        f"T5 reply should offer scheduling or confirm Hot status.\n"
        f"Got: {t.bot_reply!r}\n"
        f"Expected at least one of: {HANDOFF_KEYWORDS}"
    )


# ── Group 4: Format ────────────────────────────────────────────────────────────

@pytest.mark.e2e
def test_all_replies_within_sms_limit(seller_transcript):
    """Every reply must be ≤320 characters (Jorge's hard SMS limit)."""
    failures = []
    for t in seller_transcript:
        if not t.ok:
            continue
        if len(t.bot_reply) > SMS_MAX_CHARS:
            failures.append(f"[{t.label}] {len(t.bot_reply)} chars: {t.bot_reply!r}")

    assert not failures, (
        f"Replies exceeded {SMS_MAX_CHARS}-char limit:\n" + "\n".join(failures)
    )


@pytest.mark.e2e
def test_no_emojis_in_replies(seller_transcript):
    """Jorge explicitly prohibits emojis — none should appear in any reply."""
    failures = []
    for t in seller_transcript:
        if not t.ok:
            continue
        bad = [ch for ch in t.bot_reply if unicodedata.category(ch) in ("So", "Sm") or ord(ch) > 0x1F000]
        if bad:
            failures.append(f"[{t.label}] emoji chars {bad!r}: {t.bot_reply!r}")

    assert not failures, "Emojis found:\n" + "\n".join(failures)


# ── Group 5: Persona / tone ───────────────────────────────────────────────────

@pytest.mark.e2e
def test_no_robotic_boilerplate(seller_transcript):
    """
    Replies must not contain generic customer-service phrases.
    Jorge's style is direct — not corporate-polite.
    """
    failures = []
    for t in seller_transcript:
        if not t.ok:
            continue
        reply_lower = t.bot_reply.lower()
        for phrase in ROBOTIC_PHRASES:
            if phrase.lower() in reply_lower:
                failures.append(f"[{t.label}] robotic phrase {phrase!r}: {t.bot_reply!r}")

    assert not failures, "Robotic boilerplate detected:\n" + "\n".join(failures)


@pytest.mark.e2e
def test_replies_are_terse(seller_transcript):
    """
    Replies should be short SMS messages.
    Flag anything with more than 3 sentence-ending punctuation marks as verbose.
    """
    failures = []
    for t in seller_transcript:
        if not t.ok:
            continue
        sentences = t.bot_reply.count(".") + t.bot_reply.count("?") + t.bot_reply.count("!")
        if sentences > 3:
            failures.append(f"[{t.label}] {sentences} sentence-endings: {t.bot_reply!r}")

    assert not failures, "Overly verbose replies (>3 sentences):\n" + "\n".join(failures)


# ── Group 6: Reliability ──────────────────────────────────────────────────────

@pytest.mark.e2e
def test_no_failed_turns(seller_transcript):
    """All 10 turns must have received a bot reply (no timeouts or HTTP errors)."""
    failed = [(t.label, t.error) for t in seller_transcript if not t.ok]
    assert not failed, (
        "These turns got no reply:\n"
        + "\n".join(f"  {label}: {err}" for label, err in failed)
    )


@pytest.mark.e2e
def test_turn_latency_within_acceptable_range(seller_transcript):
    """
    Soft latency check — warns but does not fail.
    A warm Render instance should reply in <70 s; cold-start may exceed this.
    """
    slow = [(t.label, f"{t.latency:.1f}s") for t in seller_transcript if t.ok and t.latency > 70]
    if slow:
        # pytest.warns is for warnings; print so -s captures it
        print(f"\nPERF WARN — turns exceeded 70s: {slow}")
    # Not an assertion — latency is informational only


# ── Group 7: Human-readable summary ───────────────────────────────────────────

@pytest.mark.e2e
def test_print_graded_transcript(seller_transcript):
    """
    Always passes. Prints a graded transcript for manual review when run with -s.

    Each turn is annotated with any detected issues:
      ✓ clean  — no flags
      ⚠ flags  — AI_DISCLOSURE / ROBOTIC / TOO_LONG / EMOJI listed inline
    """
    lines = [f"\n{'='*62}", "  GRADED TRANSCRIPT", f"{'='*62}"]

    for t in seller_transcript:
        status = "OK  " if t.ok else "FAIL"
        lines.append(f"\n[{status}] {t.label}  ({t.latency:.1f}s)")
        lines.append(f"  YOU: {t.user_msg}")

        if not t.ok:
            lines.append(f"  BOT: !! ERROR — {t.error}")
            continue

        flags: List[str] = []
        reply_lower = t.bot_reply.lower()

        for phrase in AI_DISCLOSURE_PHRASES:
            if phrase.lower() in reply_lower:
                flags.append(f"AI_DISCLOSURE:{phrase!r}")

        for phrase in ROBOTIC_PHRASES:
            if phrase.lower() in reply_lower:
                flags.append(f"ROBOTIC:{phrase!r}")

        if len(t.bot_reply) > SMS_MAX_CHARS:
            flags.append(f"TOO_LONG:{len(t.bot_reply)}")

        bad_emoji = [ch for ch in t.bot_reply if unicodedata.category(ch) in ("So", "Sm") or ord(ch) > 0x1F000]
        if bad_emoji:
            flags.append(f"EMOJI:{bad_emoji!r}")

        lines.append(f"  BOT: {t.bot_reply}")
        lines.append(f"  {'⚠  ' + ', '.join(flags) if flags else '✓  clean'}")

    lines.append(f"\n{'='*62}\n")
    print("\n".join(lines))
