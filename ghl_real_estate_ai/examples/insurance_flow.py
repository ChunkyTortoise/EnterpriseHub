"""
Insurance lead qualification demo — BANT scoring simulation.
Run: python examples/insurance_flow.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import yaml


def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config" / "industries" / "insurance.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


@dataclass
class BANTScore:
    budget: float = 0.0
    authority: float = 0.0
    need: float = 0.0
    timeline: float = 0.0
    signals_detected: List[str] = field(default_factory=list)

    @property
    def total(self) -> float:
        config_weights = {
            "budget": 0.25,
            "authority": 0.20,
            "need": 0.30,
            "timeline": 0.25,
        }
        return (
            self.budget * config_weights["budget"]
            + self.authority * config_weights["authority"]
            + self.need * config_weights["need"]
            + self.timeline * config_weights["timeline"]
        ) * 100

    def temperature(self) -> str:
        score = self.total
        if score >= 75:
            return "HOT"
        elif score >= 50:
            return "WARM"
        else:
            return "COLD"


def analyze_message(message: str, config: dict, bant: BANTScore) -> None:
    """Detect signals in a user message and update BANT scores."""
    msg_lower = message.lower()
    bant_config = config["bant_qualification"]

    # Budget signals
    for signal in bant_config["budget"].get("hot_signals", []):
        if signal.lower() in msg_lower:
            bant.budget = max(bant.budget, 1.0)
            bant.signals_detected.append(f"BUDGET: '{signal}'")

    # Authority signals
    for signal in bant_config["authority"].get("hot_signals", []):
        if signal.lower() in msg_lower:
            bant.authority = max(bant.authority, 1.0)
            bant.signals_detected.append(f"AUTHORITY: '{signal}'")

    # Need/urgency signals
    for signal in bant_config["need"].get("urgency_signals", []):
        if signal.lower() in msg_lower:
            bant.need = max(bant.need, 0.8)
            bant.signals_detected.append(f"NEED: '{signal}'")
    for signal in bant_config["need"].get("hot_signals", []):
        if signal.lower() in msg_lower:
            bant.need = max(bant.need, 1.0)
            bant.signals_detected.append(f"NEED (HOT): '{signal}'")

    # Timeline signals
    for signal in bant_config["timeline"].get("hot_signals", []):
        if signal.lower() in msg_lower:
            bant.timeline = max(bant.timeline, 1.0)
            bant.signals_detected.append(f"TIMELINE: '{signal}'")
    for signal in bant_config["timeline"].get("warm_signals", []):
        if signal.lower() in msg_lower:
            bant.timeline = max(bant.timeline, 0.5)
            bant.signals_detected.append(f"TIMELINE (WARM): '{signal}'")


def run_demo() -> BANTScore:
    config = load_config()
    bant = BANTScore()

    conversation = [
        ("Bot", config["personality"]["phrases"]["greeting"][0]),
        ("User", "Yeah I just bought a house and need homeowner's plus auto"),
        ("Bot", config["bant_qualification"]["budget"]["question"]),
        ("User", "I'm paying $200/mo for just auto, seems high and I'm open to change"),
        ("Bot", config["bant_qualification"]["need"]["question"]),
        ("User", "New home purchase, I need coverage in place within 30 days"),
        ("Bot", config["bant_qualification"]["authority"]["question"]),
        ("User", "Yes just me, I decide"),
    ]

    print("=" * 60)
    print("LYRIO INSURANCE BOT — DEMO CONVERSATION")
    print("=" * 60)

    for speaker, message in conversation:
        print(f"\n[{speaker}]: {message}")
        if speaker == "User":
            analyze_message(message, config, bant)

    print("\n" + "=" * 60)
    print("BANT SCORE ANALYSIS")
    print("=" * 60)
    print(f"Budget Score:    {bant.budget:.1f}")
    print(f"Authority Score: {bant.authority:.1f}")
    print(f"Need Score:      {bant.need:.1f}")
    print(f"Timeline Score:  {bant.timeline:.1f}")
    print(f"Total Score:     {bant.total:.1f} / 100")
    print(f"Temperature:     {bant.temperature()}")

    if bant.signals_detected:
        print("\nDetected Signals:")
        for signal in bant.signals_detected:
            print(f"  - {signal}")

    if bant.temperature() == "HOT":
        print("\n-> ACTION: Routing to licensed agent for immediate quote")
    elif bant.temperature() == "WARM":
        print("\n-> ACTION: Adding to nurture sequence, follow up day 3")
    else:
        print("\n-> ACTION: Adding to long-term drip campaign")

    return bant


if __name__ == "__main__":
    run_demo()
