#!/usr/bin/env python3
"""
Conversation Analysis Script for Intelligent Lead Insights

Analyzes lead conversation patterns to extract behavioral signals,
engagement metrics, and conversation quality indicators.

Usage:
    python analyze-conversations.py --lead-id <lead_id> [--output json|text]
    python analyze-conversations.py --batch <leads_file.json> --output csv

Zero-Context Execution:
    This script runs independently without loading into Claude's context.
    Only the output is returned, saving tokens for actual analysis.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import statistics


@dataclass
class ConversationMetrics:
    """Metrics extracted from conversation analysis."""
    lead_id: str
    message_count: int
    agent_messages: int
    lead_messages: int
    avg_response_time_hours: float
    response_time_trend: str  # improving, stable, declining
    engagement_ratio: float  # lead_messages / agent_messages
    avg_message_length: float
    question_count: int
    detailed_question_count: int
    emotional_keywords_positive: int
    emotional_keywords_negative: int
    sentiment_score: float  # -1 to 1
    buying_signal_count: int
    objection_count: int
    last_activity_days: int
    conversation_health: str  # excellent, good, concerning, poor
    analysis_timestamp: str


@dataclass
class BuyingSignal:
    """Detected buying signal with context."""
    signal_type: str
    message_content: str
    timestamp: str
    confidence: float
    category: str  # financial, timeline, commitment, engagement


def load_conversation_history(lead_id: str) -> List[Dict[str, Any]]:
    """
    Load conversation history for a lead.

    In production, this connects to:
    - GHL API via ghl_conversation_bridge
    - Memory service for cached conversations
    - Redis for real-time messages
    """
    # Placeholder - in production, connect to actual data sources
    # This allows the script to be tested standalone
    try:
        import asyncio
        from ghl_real_estate_ai.services.memory_service import MemoryService

        memory = MemoryService()
        # Load from memory service
        return memory.get_conversation_history(lead_id)
    except ImportError:
        # Return sample data for standalone testing
        return [
            {"role": "lead", "content": "Hi, I'm looking for a home in Austin", "timestamp": "2026-01-15T10:00:00"},
            {"role": "agent", "content": "Great! What's your budget range?", "timestamp": "2026-01-15T10:05:00"},
            {"role": "lead", "content": "We're pre-approved for $750k", "timestamp": "2026-01-15T10:08:00"},
        ]


def calculate_response_times(messages: List[Dict]) -> List[float]:
    """Calculate response times between messages in hours."""
    response_times = []

    for i in range(1, len(messages)):
        try:
            prev_time = datetime.fromisoformat(messages[i-1].get("timestamp", ""))
            curr_time = datetime.fromisoformat(messages[i].get("timestamp", ""))
            diff_hours = (curr_time - prev_time).total_seconds() / 3600
            if diff_hours > 0:
                response_times.append(diff_hours)
        except (ValueError, TypeError):
            continue

    return response_times


def detect_buying_signals(messages: List[Dict]) -> List[BuyingSignal]:
    """Detect buying signals in conversation messages."""
    signals = []

    financial_keywords = [
        "pre-approved", "pre approved", "budget", "down payment",
        "mortgage", "afford", "financing", "loan"
    ]

    timeline_keywords = [
        "lease ends", "need to move", "moving", "timeline",
        "how soon", "when can", "by when", "deadline"
    ]

    commitment_keywords = [
        "offer", "put in an offer", "next steps", "how do we",
        "move forward", "secure", "schedule", "view"
    ]

    engagement_keywords = [
        "love", "perfect", "exactly", "interested",
        "tell me more", "show me", "can we see"
    ]

    for msg in messages:
        if msg.get("role") != "lead":
            continue

        content = msg.get("content", "").lower()
        timestamp = msg.get("timestamp", "")

        # Check financial signals
        for keyword in financial_keywords:
            if keyword in content:
                signals.append(BuyingSignal(
                    signal_type="financial_readiness",
                    message_content=msg.get("content", "")[:100],
                    timestamp=timestamp,
                    confidence=0.85,
                    category="financial"
                ))
                break

        # Check timeline signals
        for keyword in timeline_keywords:
            if keyword in content:
                signals.append(BuyingSignal(
                    signal_type="timeline_urgency",
                    message_content=msg.get("content", "")[:100],
                    timestamp=timestamp,
                    confidence=0.80,
                    category="timeline"
                ))
                break

        # Check commitment signals
        for keyword in commitment_keywords:
            if keyword in content:
                signals.append(BuyingSignal(
                    signal_type="commitment_indicator",
                    message_content=msg.get("content", "")[:100],
                    timestamp=timestamp,
                    confidence=0.90,
                    category="commitment"
                ))
                break

        # Check engagement signals
        for keyword in engagement_keywords:
            if keyword in content:
                signals.append(BuyingSignal(
                    signal_type="high_engagement",
                    message_content=msg.get("content", "")[:100],
                    timestamp=timestamp,
                    confidence=0.70,
                    category="engagement"
                ))
                break

    return signals


def detect_objections(messages: List[Dict]) -> int:
    """Count objection indicators in messages."""
    objection_keywords = [
        "too expensive", "out of budget", "can't afford",
        "need to think", "not sure", "talk to spouse",
        "looking at other", "competition", "another agent",
        "not ready", "waiting", "later"
    ]

    count = 0
    for msg in messages:
        if msg.get("role") != "lead":
            continue
        content = msg.get("content", "").lower()
        for keyword in objection_keywords:
            if keyword in content:
                count += 1
                break

    return count


def calculate_sentiment(messages: List[Dict]) -> float:
    """Calculate overall sentiment score from -1 to 1."""
    positive_words = [
        "love", "great", "perfect", "excited", "wonderful",
        "amazing", "beautiful", "exactly", "thank", "appreciate"
    ]

    negative_words = [
        "hate", "bad", "terrible", "disappointed", "frustrated",
        "annoyed", "worried", "concerned", "problem", "issue"
    ]

    positive_count = 0
    negative_count = 0

    for msg in messages:
        if msg.get("role") != "lead":
            continue
        content = msg.get("content", "").lower()

        for word in positive_words:
            if word in content:
                positive_count += 1

        for word in negative_words:
            if word in content:
                negative_count += 1

    total = positive_count + negative_count
    if total == 0:
        return 0.0

    return (positive_count - negative_count) / total


def count_questions(messages: List[Dict]) -> tuple:
    """Count total and detailed questions from lead."""
    question_count = 0
    detailed_count = 0

    detail_indicators = [
        "how much", "what's the", "can you tell me",
        "what about", "how does", "what if"
    ]

    for msg in messages:
        if msg.get("role") != "lead":
            continue
        content = msg.get("content", "")

        if "?" in content:
            question_count += 1
            # Check if it's a detailed question
            for indicator in detail_indicators:
                if indicator in content.lower():
                    detailed_count += 1
                    break

    return question_count, detailed_count


def determine_conversation_health(metrics: Dict) -> str:
    """Determine overall conversation health."""
    score = 0

    # Engagement ratio (max 25 points)
    if metrics["engagement_ratio"] >= 0.8:
        score += 25
    elif metrics["engagement_ratio"] >= 0.5:
        score += 15
    elif metrics["engagement_ratio"] >= 0.3:
        score += 5

    # Response time (max 25 points)
    if metrics["avg_response_time_hours"] < 1:
        score += 25
    elif metrics["avg_response_time_hours"] < 4:
        score += 20
    elif metrics["avg_response_time_hours"] < 24:
        score += 10

    # Sentiment (max 25 points)
    if metrics["sentiment_score"] > 0.3:
        score += 25
    elif metrics["sentiment_score"] > 0:
        score += 15
    elif metrics["sentiment_score"] > -0.3:
        score += 5

    # Buying signals vs objections (max 25 points)
    signal_ratio = metrics["buying_signal_count"] / max(metrics["objection_count"], 1)
    if signal_ratio >= 2:
        score += 25
    elif signal_ratio >= 1:
        score += 15
    elif signal_ratio >= 0.5:
        score += 5

    # Determine health category
    if score >= 80:
        return "excellent"
    elif score >= 60:
        return "good"
    elif score >= 40:
        return "concerning"
    else:
        return "poor"


def analyze_conversation(lead_id: str) -> ConversationMetrics:
    """
    Perform comprehensive conversation analysis.

    Args:
        lead_id: Lead identifier

    Returns:
        ConversationMetrics with analysis results
    """
    messages = load_conversation_history(lead_id)

    if not messages:
        return ConversationMetrics(
            lead_id=lead_id,
            message_count=0,
            agent_messages=0,
            lead_messages=0,
            avg_response_time_hours=0,
            response_time_trend="unknown",
            engagement_ratio=0,
            avg_message_length=0,
            question_count=0,
            detailed_question_count=0,
            emotional_keywords_positive=0,
            emotional_keywords_negative=0,
            sentiment_score=0,
            buying_signal_count=0,
            objection_count=0,
            last_activity_days=999,
            conversation_health="unknown",
            analysis_timestamp=datetime.now().isoformat()
        )

    # Count messages by role
    agent_messages = [m for m in messages if m.get("role") == "agent"]
    lead_messages = [m for m in messages if m.get("role") == "lead"]

    # Calculate response times
    response_times = calculate_response_times(messages)
    avg_response_time = statistics.mean(response_times) if response_times else 0

    # Determine response time trend
    if len(response_times) >= 3:
        first_half = response_times[:len(response_times)//2]
        second_half = response_times[len(response_times)//2:]
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        if second_avg < first_avg * 0.8:
            response_trend = "improving"
        elif second_avg > first_avg * 1.2:
            response_trend = "declining"
        else:
            response_trend = "stable"
    else:
        response_trend = "insufficient_data"

    # Calculate engagement ratio
    engagement_ratio = len(lead_messages) / max(len(agent_messages), 1)

    # Calculate average message length for lead
    msg_lengths = [len(m.get("content", "")) for m in lead_messages]
    avg_length = statistics.mean(msg_lengths) if msg_lengths else 0

    # Count questions
    question_count, detailed_count = count_questions(messages)

    # Detect buying signals
    signals = detect_buying_signals(messages)

    # Count objections
    objection_count = detect_objections(messages)

    # Calculate sentiment
    sentiment = calculate_sentiment(messages)

    # Calculate last activity
    try:
        last_msg_time = datetime.fromisoformat(messages[-1].get("timestamp", ""))
        last_activity_days = (datetime.now() - last_msg_time).days
    except (ValueError, IndexError):
        last_activity_days = 999

    # Build metrics dict for health calculation
    metrics_dict = {
        "engagement_ratio": engagement_ratio,
        "avg_response_time_hours": avg_response_time,
        "sentiment_score": sentiment,
        "buying_signal_count": len(signals),
        "objection_count": objection_count
    }

    # Determine health
    health = determine_conversation_health(metrics_dict)

    return ConversationMetrics(
        lead_id=lead_id,
        message_count=len(messages),
        agent_messages=len(agent_messages),
        lead_messages=len(lead_messages),
        avg_response_time_hours=round(avg_response_time, 2),
        response_time_trend=response_trend,
        engagement_ratio=round(engagement_ratio, 2),
        avg_message_length=round(avg_length, 0),
        question_count=question_count,
        detailed_question_count=detailed_count,
        emotional_keywords_positive=max(0, int(sentiment * 10)),  # Simplified
        emotional_keywords_negative=max(0, int(-sentiment * 10)),
        sentiment_score=round(sentiment, 2),
        buying_signal_count=len(signals),
        objection_count=objection_count,
        last_activity_days=last_activity_days,
        conversation_health=health,
        analysis_timestamp=datetime.now().isoformat()
    )


def main():
    parser = argparse.ArgumentParser(description="Analyze lead conversations")
    parser.add_argument("--lead-id", type=str, help="Lead ID to analyze")
    parser.add_argument("--batch", type=str, help="Path to JSON file with lead IDs")
    parser.add_argument("--output", type=str, default="json", choices=["json", "text", "csv"])

    args = parser.parse_args()

    if args.batch:
        # Batch analysis
        with open(args.batch, "r") as f:
            lead_ids = json.load(f)

        results = []
        for lead_id in lead_ids:
            metrics = analyze_conversation(lead_id)
            results.append(asdict(metrics))

        if args.output == "csv":
            import csv
            if results:
                writer = csv.DictWriter(sys.stdout, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
        else:
            print(json.dumps(results, indent=2))

    elif args.lead_id:
        # Single lead analysis
        metrics = analyze_conversation(args.lead_id)

        if args.output == "text":
            print(f"Conversation Analysis for {args.lead_id}")
            print("=" * 50)
            print(f"Messages: {metrics.message_count} ({metrics.lead_messages} from lead)")
            print(f"Avg Response Time: {metrics.avg_response_time_hours}h ({metrics.response_time_trend})")
            print(f"Engagement Ratio: {metrics.engagement_ratio}")
            print(f"Sentiment Score: {metrics.sentiment_score}")
            print(f"Buying Signals: {metrics.buying_signal_count}")
            print(f"Objections: {metrics.objection_count}")
            print(f"Last Activity: {metrics.last_activity_days} days ago")
            print(f"Health: {metrics.conversation_health.upper()}")
        else:
            print(json.dumps(asdict(metrics), indent=2))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
