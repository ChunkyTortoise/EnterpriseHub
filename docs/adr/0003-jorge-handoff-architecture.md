# ADR 0003: Jorge Bot Handoff Architecture

## Status

Accepted

## Context

The Jorge bot system consists of three specialized bots — Lead, Buyer, and Seller — each handling a distinct phase of the real estate qualification process. When a lead's intent shifts (e.g., a general inquiry reveals buyer-specific signals like budget mentions or pre-approval), the conversation must transfer seamlessly to the appropriate specialist bot.

Naive handoff approaches create several problems:
- **Ping-pong loops**: Lead bot hands off to Buyer bot, which detects seller signals and hands back to Lead bot, creating infinite loops
- **Context loss**: Conversation history and qualification progress are lost during transitions
- **Simultaneous handoffs**: Two bots could attempt to claim the same contact concurrently
- **Threshold rigidity**: A fixed confidence threshold doesn't account for varying signal quality across different conversation types

## Decision

Implement a centralized `JorgeHandoffService` with the following safeguards:

**Confidence Threshold**: 0.7 minimum confidence score required before any handoff executes. Scores are computed from weighted pattern matching against known intent signals (e.g., "I want to buy" = 0.4, "budget $X" = 0.3, "pre-approved" = 0.3).

**Circular Prevention**: Maintain a 30-minute sliding window of recent handoff history per contact. If a source-to-target handoff pair has occurred within this window, the handoff is blocked and the current bot continues the conversation.

**Rate Limiting**: Maximum 3 handoffs per hour and 10 per day per contact. This prevents edge cases where ambiguous conversations trigger excessive transfers.

**Conflict Resolution**: Contact-level locking via Redis ensures only one handoff can execute per contact at any time. If a lock exists, the second handoff attempt is queued and retried after lock release.

**Pattern Learning**: After accumulating 10+ data points per handoff direction, the service adjusts confidence thresholds based on outcome history. Successful handoffs (measured by subsequent engagement) lower the threshold slightly; failed handoffs raise it.

## Consequences

### Positive
- Eliminates ping-pong loops entirely via circular prevention window
- Rate limiting prevents degraded experience from excessive bot switches
- Contact locking prevents data corruption from concurrent handoff attempts
- Pattern learning enables threshold tuning from real production data without manual intervention
- Full audit trail enables analysis of handoff patterns and optimization opportunities

### Negative
- Adds 10-30ms latency to each message evaluation for handoff signal checking
- 30-minute circular prevention window may occasionally block legitimate re-handoffs
- Pattern learning requires minimum 10 data points before activating, meaning initial thresholds are static
- Redis dependency for contact locking; Redis failure degrades to in-memory locking (single-worker only)
- Rate limit configuration (3/hr, 10/day) may need per-brokerage tuning for high-volume teams
