# LinkedIn Week 2 -- Post 1

**Schedule**: Monday, February 17, 2026, 8:30 AM PT
**Topic**: Why I Test AI Systems Differently Than Regular Software
**Content Type**: Engineering philosophy / practical framework

---

Most AI testing advice is wrong.

"Mock the LLM and test the rest." That's the standard guidance. And it misses the point entirely.

I maintain 8,500+ automated tests across 11 production repositories. Here's what I've learned about testing AI systems that nobody told me upfront.

The problem with mocking LLMs: you're testing your parsing logic, not your system. An LLM mock always returns the format you expect. A real LLM returns whatever it feels like. Your test suite passes at 100%. Your production system breaks at 2 AM.

What actually works -- three layers:

**Layer 1: Deterministic tests (80% of your suite)**
Test everything that doesn't touch the LLM. Routing logic, cache behavior, rate limiting, input validation, output parsing with known good/bad inputs. These run in milliseconds and catch most regressions.

In EnterpriseHub, this means testing that a lead with budget signals routes to the Buyer bot, not that Claude correctly identifies budget signals. The routing is our code. The identification is Claude's problem.

**Layer 2: Contract tests (15% of your suite)**
Define the schema your system expects from the LLM. Test that your parsing handles every valid schema variant AND graceful degradation for invalid ones. Use snapshot testing -- capture 50 real LLM responses, test against those.

This catches the #1 production failure: the LLM changes its response format slightly and your parser throws a KeyError.

**Layer 3: Integration smoke tests (5% of your suite)**
Hit the real API with real prompts. Run these daily, not on every commit. They're slow and expensive. But they catch model behavior changes that contract tests can't.

The ratio matters. If your AI test suite is mostly integration tests, your CI takes 10 minutes and you stop running it. If it's mostly mocks, you're testing fiction.

8,500 tests. 80% run in under 100ms each. That's the target.

What's your AI testing strategy? Genuinely curious -- this is still an unsolved problem.

#AIEngineering #Testing #Python #SoftwareEngineering #TDD #LLMOps

---

**Engagement strategy**: This post will attract "but what about..." comments. Have responses ready for: evaluation frameworks (RAGAS, etc.), prompt regression testing, and "isn't 8,500 tests overkill" pushback. The honest answer to the last one: most are fast deterministic tests that take 2 minutes total to run.
