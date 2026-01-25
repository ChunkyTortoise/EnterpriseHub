# Workflow Standards: EnterpriseHub

## Development Lifecycle
1. **Track Creation:** All work must start with `/conductor:newTrack`.
2. **Spec Review:** The `spec.md` must be reviewed for edge cases (security, performance).
3. **Plan Approval:** The `plan.md` must include explicit testing tasks for every logic change.
4. **Implementation:** Use `/conductor:implement` to maintain persistent progress tracking.
5. **Validation:** All code must pass `pytest` and `ruff check` before being marked complete.

## Testing Strategy
- **Unit Tests:** Mandatory for all new functions.
- **Integration Tests:** Required for API endpoints and WebSocket handlers.
- **Performance Benchmarks:** Sub-50ms latency for financial core logic.
- **Visual Regression:** Required for UI changes (using Playwright).

## Code Style
- **Python:** Strict PEP8 compliance.
- **Typing:** Type hints are mandatory for all public functions.
- **Documentation:** Google-style docstrings.

## Deployment Protocol
- **Safety:** Use Conductor checkpoints before high-impact migrations.
- **Traceability:** All commits must reference the Conductor track ID.
