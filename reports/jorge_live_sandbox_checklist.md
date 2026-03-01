# Jorge Live Sandbox Checklist (10 Minutes)

## Goal
Verify seller and buyer bots behave correctly in real conversation flow before production use.

## Preconditions
- Use production-like env: `.env.jorge`
- Start services the same way you deliver to Jorge.
- Keep one observer logging timestamps + outputs.

## Seller Flow (Stall + Pricing Objection)
1. Send seller opener:
   - "I might sell my house in Rancho Cucamonga, but I am not sure yet."
2. Validate behavior:
   - Bot responds consultatively (not pushy).
   - Response is short SMS style.
3. Send stall signal:
   - "Let me think about it."
4. Validate behavior:
   - Bot acknowledges stall empathetically.
   - No robotic fallback.
5. Send pricing objection:
   - "Zillow says 750k. Why are you saying different?"
6. Validate behavior:
   - Bot references local comp framing.
   - Tone remains helpful and specific.

## Buyer Flow (Hot Lead + Scheduling)
1. Send buyer opener:
   - "I am pre-approved and ready to buy in 30 days in Rancho Cucamonga. Budget 850k."
2. Validate behavior:
   - Bot returns relevant guidance/matching response.
   - Buyer is treated as high-intent.
3. Trigger next action scheduling step.
4. Validate behavior:
   - Follow-up timing for hot lead is 2 hours.
   - Next action is tour/scheduling oriented.

## Pass Criteria
- No runtime errors.
- No empty/garbled LLM payload text.
- Seller path handles stall + Zestimate objection cleanly.
- Buyer path keeps hot-lead urgency behavior (2-hour follow-up).

## Evidence to Capture
- Conversation transcript.
- Timestamped next action/follow-up metadata.
- Any warning/error logs from bot services.
