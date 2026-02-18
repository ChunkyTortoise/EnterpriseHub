# Jorge Bots Completion Kickoff Prompt

Use the spec below as the single source of truth and execute it end-to-end:

`/Users/cave/Documents/New project/enterprisehub/plans/JORGE_BOTS_COMPLETION_EXECUTION_SPEC_FEB16_2026.md`

You are implementing remaining Epics A-G for Jorge Lead/Seller/Buyer bots.  
Execute in this order:

1. WS-1 Routing + contract hardening.
2. WS-2 Seller qualification/persistence hardening.
3. WS-3 Appointment engine optimization.
4. WS-4 Follow-up lifecycle redesign.
5. WS-5 Tone/compliance lock.
6. WS-6 Metrics + experiment loop.

Execution rules:

1. Make production-safe incremental commits per workstream.
2. Run targeted tests after each workstream and summarize failures before fixing.
3. Do not regress existing seller/buyer/lead route behavior.
4. Enforce canonical seller contract write policy:
   no null overwrite, required mapping validation, deterministic qualification state.
5. Enforce cross-bot opt-out suppression standard:
   apply `AI-Off` + `Do-Not-Contact`, remove activation/automation tags, stop follow-ups.
6. Ensure HOT seller booking strictly uses 30-minute consultation appointment type with 3-slot offer and fallback.
7. Keep all outbound language consultative/friendly and SMS-safe.

Output format each cycle:

1. What changed (files + behavior).
2. Tests run and results.
3. Risks/open decisions.
4. Next step.

Start now with WS-1 and WS-2, then pause for validation summary before WS-3.
