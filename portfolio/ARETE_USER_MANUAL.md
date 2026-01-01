# 📖 ARETE: Owner's Manual
> **How to lead your AI Technical Co-Founder Swarm.**

Congratulations on your new AI Technical Co-Founder. ARETE is not a tool you "use"—it is a team you **lead**. This guide explains how to get the most out of your autonomous engineering swarm.

---

## 🏎️ Getting Started: The "Prime" Interface
You only ever talk to **Prime**. Prime is your CEO/Project Manager. He handles the delegation to the other agents so you don't have to.

### How to give orders:
- **Be Goal-Oriented**: Instead of "Write a Python function," say "Add a login page that uses Firebase."
- **Context is King**: "Look at our `decision_log.md` before you change the pricing model."
- **The Self-Evolution Command**: "ARETE, you need a way to send emails. Research the SendGrid API and build a tool for yourself to use it."

---

## 🛠️ The Workflow: What Happens Next?
When you give Prime a task, the swarm enters a **State Loop**:

1.  **Architect** creates a design spec (`docs/architecture/`).
2.  **Engineer** writes the code in a new branch.
3.  **Guardian** audits the code for security and runs tests.
4.  **DevOps** creates a Pull Request on GitHub.
5.  **You** receive a summary of the changes to approve.

---

## 💾 Memory & The Decision Log
ARETE never forgets. Everything important is recorded in:
- `decision_log.md`: Why we chose specific technologies.
- `requirements.md`: What the business actually needs.
- `state.json`: The long-term technical memory of the agents.

**Tip**: If ARETE seems "lost," tell him: *"Review the decision log and summarize our current priorities."*

---

## 🛡️ Safety & Controls
ARETE is powerful, but you are the boss.
- **Approval Gate**: By default, ARETE cannot merge code to `main` without your manual approval in the chat.
- **Rollback**: "ARETE, the last deployment broke the UI. Revert to the previous stable version immediately."
- **Sanitizer**: The Guardian agent is hard-coded to reject any code that tries to access your environment variables without permission.

---

## 🚀 The Self-Evolution Loop
Your co-founder gets smarter over time. 
Ask him to build "Tools":
> *"ARETE, I want you to start monitoring our competitor's pricing. Write a scraper tool for yourself and set it to run every Monday."*

**ARETE will now have a new skill he can use forever.**
