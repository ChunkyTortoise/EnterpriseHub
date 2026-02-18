# Continuation Prompt: Jorge Bots Finalization

Use this prompt in a new continuation session.

---

Continue the Jorge bot finalization in `/Users/cave/Documents/GitHub/EnterpriseHub` using:
`/Users/cave/Documents/GitHub/EnterpriseHub/docs/handoffs/JORGE_BOTS_FINALIZATION_2026-02-17_SPEC.md`.

Goals:
1. Complete WS1-W6 exactly as defined in the spec.
2. Finish all four required tracks (regression sweep, regression tests, noise cleanup, clean commit package).
3. Produce a Jorge-ready delivery package with evidence and rollback instructions.

Operating constraints:
- The git worktree is dirty with unrelated changes. Do not revert or stage unrelated files.
- Keep changes scoped to Jorge bot stabilization and directly related tests/docs.
- Run tests with reproducible commands and summarize outcomes clearly.

Required outputs at completion:
1. A concise summary of fixes and what remains (if anything).
2. Exact list of files changed (absolute paths).
3. Commands run and pass/fail status.
4. Jorge delivery docs created/updated.
5. Suggested commit plan (or commit hashes if committed).

If blocked:
- State the blocker clearly.
- Provide the minimal next command set to unblock.

---
