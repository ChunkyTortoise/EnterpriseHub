"""Customer Support Pipeline — 2-agent chain: classify → respond.

Demonstrates AgentForge's async pipeline for support ticket routing.
No API keys required — fully self-contained.

Run:
    python examples/customer_support.py
"""
import asyncio
from dataclasses import dataclass, field


@dataclass
class AgentResult:
    agent: str
    output: str
    tokens_used: int = 0
    latency_ms: int = 0
    metadata: dict = field(default_factory=dict)


CATEGORY_KEYWORDS = {
    "billing": ["charge", "invoice", "payment", "refund", "subscription", "price", "cost", "bill"],
    "technical": ["error", "bug", "crash", "broken", "not working", "issue", "fail", "slow"],
    "account": ["password", "login", "access", "locked", "reset", "email", "profile", "settings"],
    "feature": ["feature", "request", "suggestion", "wish", "would like", "add", "improve"],
}

RESPONSE_TEMPLATES = {
    "billing": {
        "priority": "medium",
        "response": (
            "Thank you for reaching out about your billing concern. "
            "I've pulled up your account and can see the details. "
            "Our billing team will review this within 24 hours. "
            "If this is urgent, you can also reach billing directly at billing@example.com."
        ),
    },
    "technical": {
        "priority": "high",
        "response": (
            "I understand you're experiencing a technical issue. "
            "I've created a support ticket and escalated it to our engineering team. "
            "In the meantime, please try clearing your cache and restarting the application. "
            "We'll follow up within 4 hours with an update."
        ),
    },
    "account": {
        "priority": "medium",
        "response": (
            "I can help with your account access. "
            "For security, I've sent a verification link to your registered email. "
            "Please check your inbox (and spam folder) and follow the instructions. "
            "If you still need help, our support team is available 24/7."
        ),
    },
    "feature": {
        "priority": "low",
        "response": (
            "Thanks for the feedback! We love hearing from our users. "
            "I've logged your suggestion in our product backlog. "
            "Our product team reviews all submissions weekly. "
            "You can track feature requests at feedback.example.com."
        ),
    },
    "general": {
        "priority": "low",
        "response": (
            "Thank you for contacting support. "
            "I've reviewed your message and created a ticket for our team. "
            "We'll get back to you within 24 hours with a detailed response."
        ),
    },
}


async def classify_agent(message: str) -> AgentResult:
    """Classify a support ticket by category and sentiment."""
    await asyncio.sleep(0.06)
    msg_lower = message.lower()

    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        scores[category] = sum(1 for k in keywords if k in msg_lower)

    best = max(scores, key=scores.get) if max(scores.values()) > 0 else "general"
    confidence = min(scores.get(best, 0) / 3.0, 1.0) if best != "general" else 0.3

    negative_words = ["angry", "frustrated", "terrible", "worst", "awful", "hate", "unacceptable"]
    sentiment = "negative" if any(w in msg_lower for w in negative_words) else "neutral"

    return AgentResult(
        agent="ClassifierAgent",
        output=best,
        tokens_used=len(message.split()) * 2 + 30,
        latency_ms=58,
        metadata={"category": best, "confidence": round(confidence, 2), "sentiment": sentiment},
    )


async def respond_agent(category: str, original_message: str, sentiment: str) -> AgentResult:
    """Generate a response based on ticket classification."""
    await asyncio.sleep(0.08)
    template = RESPONSE_TEMPLATES.get(category, RESPONSE_TEMPLATES["general"])

    response = template["response"]
    if sentiment == "negative":
        response = "I sincerely apologize for the inconvenience. " + response

    return AgentResult(
        agent="ResponderAgent",
        output=response,
        tokens_used=len(response.split()) * 2 + 40,
        latency_ms=82,
        metadata={"priority": template["priority"], "category": category},
    )


async def run_pipeline(message: str) -> None:
    print(f"{'=' * 60}")
    print("AgentForge Customer Support Pipeline")
    print(f"Ticket: {message}")
    print(f"{'=' * 60}\n")

    print("[1/2] ClassifierAgent: Analyzing ticket...")
    classification = await classify_agent(message)
    meta = classification.metadata
    print(f"      Category: {meta['category']} (confidence: {meta['confidence']})")
    print(f"      Sentiment: {meta['sentiment']} ({classification.latency_ms}ms)\n")

    print("[2/2] ResponderAgent: Generating response...")
    response = await respond_agent(meta["category"], message, meta["sentiment"])
    print(f"      Priority: {response.metadata['priority']} ({response.latency_ms}ms)\n")

    print(f"{'─' * 60}")
    print(f"Category: {meta['category'].upper()}")
    print(f"Priority: {response.metadata['priority'].upper()}")
    print(f"Sentiment: {meta['sentiment']}")
    print(f"\nResponse:\n{response.output}")
    print(f"{'─' * 60}")

    total_tokens = classification.tokens_used + response.tokens_used
    total_ms = classification.latency_ms + response.latency_ms
    print(f"\nPipeline complete | {total_tokens} tokens | {total_ms}ms total")


async def run_demo() -> None:
    tickets = [
        "I was charged twice for my subscription last month and I'm frustrated!",
        "The app keeps crashing when I try to export reports",
        "I can't login to my account, password reset isn't working",
        "It would be great if you could add dark mode to the dashboard",
    ]
    for ticket in tickets:
        await run_pipeline(ticket)
        print("\n")


if __name__ == "__main__":
    asyncio.run(run_demo())
