#!/usr/bin/env python3
"""
E3 Verification: Generate 10 sample seller responses and verify human tone.
Exercises the tone engine for all SIMPLE_MODE paths.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ghl_real_estate_ai.services.jorge.jorge_tone_engine import JorgeToneEngine

engine = JorgeToneEngine()

AI_PHRASES = [
    "i understand", "thank you for", "i'd be happy to", "let me help",
    "that's a great", "i appreciate", "based on my analysis",
    "certainly", "of course",
    "feel free", "don't hesitate", "rest assured"
]


def check(label, message):
    errors = []
    if len(message) > 160:
        errors.append(f"TOO LONG ({len(message)} chars)")
    if any(ord(c) > 0x1F600 for c in message):
        errors.append("HAS EMOJI")
    if '-' in message:
        errors.append("HAS HYPHEN")
    for phrase in AI_PHRASES:
        if phrase in message.lower():
            errors.append(f"AI PHRASE: '{phrase}'")
    status = "PASS" if not errors else f"FAIL: {', '.join(errors)}"
    print(f"  [{status}] {label}")
    print(f"    \"{message}\" ({len(message)} chars)")
    return len(errors) == 0


print("=" * 70)
print("E3: JORGE TONE VERIFICATION — 10 SAMPLE RESPONSES")
print("=" * 70)

results = []

# 1. Q1 ask (fresh contact)
msg = engine.generate_qualification_message(1, seller_name="Maria")
results.append(check("Q1: Motivation (fresh contact)", msg))

# 2. Q2 ask (after Q1 answered)
msg = engine.generate_qualification_message(2, seller_name="Carlos")
results.append(check("Q2: Timeline", msg))

# 3. Q3 ask
msg = engine.generate_qualification_message(3, seller_name="Susan")
results.append(check("Q3: Condition", msg))

# 4. Q4 ask
msg = engine.generate_qualification_message(4, seller_name="James")
results.append(check("Q4: Price", msg))

# 5. Hot seller handoff
msg = engine.generate_hot_seller_handoff(seller_name="Ana", agent_name="our team")
results.append(check("Hot Seller Handoff", msg))

# 6. Vague answer follow-up (Q1)
msg = engine.generate_follow_up_message(
    last_response="maybe idk", question_number=1, seller_name="Robert"
)
results.append(check("Vague Follow-up (Q1)", msg))

# 7. Take-away close (vague streak)
msg = engine.generate_take_away_close(seller_name="Linda", reason="vague")
results.append(check("Take-Away Close (vague)", msg))

# 8. No response follow-up (Q2)
msg = engine.generate_follow_up_message(
    last_response="", question_number=2, seller_name="David"
)
results.append(check("No Response Follow-up (Q2)", msg))

# 9. Warm nurture message
msg = engine._ensure_sms_compliance(
    "Thanks for the info. Let me have our team review your situation and get back to you with next steps."
)
results.append(check("Warm Nurture", msg))

# 10. Cold nurture message
msg = engine._ensure_sms_compliance(
    "I'll keep your info on file. Reach out if your timeline or situation changes."
)
results.append(check("Cold Nurture", msg))

print()
print(f"RESULTS: {sum(results)}/10 passed")
if all(results):
    print("ALL TONE CHECKS PASSED")
else:
    print("SOME TONE CHECKS FAILED — review above")
    sys.exit(1)
