#!/usr/bin/env python3
"""
Conversation Transcript Analyzer for Conversation Optimization

Analyzes full conversation transcripts for quality metrics, response
effectiveness, and coaching opportunities.

Usage:
    python analyze-transcript.py --conversation-id <id>
    python analyze-transcript.py --file <transcript.json> --output json|report

Zero-Context Execution:
    This script runs independently without loading into Claude's context.
"""

import argparse
import json
import sys
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import statistics


@dataclass
class ResponseQuality:
    """Quality assessment for a single response."""
    message_index: int
    relevance_score: float
    empathy_score: float
    completeness_score: float
    persuasiveness_score: float
    personalization_score: float
    overall_score: float
    improvement_suggestions: List[str]


@dataclass
class TranscriptAnalysis:
    """Complete transcript analysis results."""
    conversation_id: str
    message_count: int
    agent_response_count: int
    avg_quality_score: float
    quality_trend: str  # improving, stable, declining
    response_qualities: List[ResponseQuality]
    objections_detected: List[Dict]
    missed_opportunities: List[Dict]
    conversation_health: str
    coaching_summary: Dict[str, Any]
    analysis_timestamp: str


def load_transcript(conversation_id: str = None, file_path: str = None) -> List[Dict]:
    """Load conversation transcript."""
    if file_path:
        with open(file_path, "r") as f:
            data = json.load(f)
            return data.get("messages", data)

    # Production: Load from services
    try:
        from ghl_real_estate_ai.services.memory_service import MemoryService
        memory = MemoryService()
        return memory.get_conversation_history(conversation_id)
    except ImportError:
        # Sample data for testing
        return [
            {"role": "lead", "content": "Hi, I'm looking for a home in Austin around $700k"},
            {"role": "agent", "content": "Great! I'd love to help. What areas are you interested in?"},
            {"role": "lead", "content": "Probably Round Rock or Pflugerville for the schools"},
            {"role": "agent", "content": "Those are excellent choices for families. How many bedrooms do you need?"},
            {"role": "lead", "content": "At least 4, we have 3 kids"},
            {"role": "agent", "content": "Perfect. Are you pre-approved for financing?"},
            {"role": "lead", "content": "Yes, we're pre-approved for up to $750k"},
            {"role": "agent", "content": "Excellent! When do you need to move by?"},
            {"role": "lead", "content": "Our lease ends in 3 months, so ideally before then"},
            {"role": "agent", "content": "Got it. I have several options that could work. Can I send you some listings?"},
        ]


def analyze_relevance(agent_msg: str, lead_msg: str) -> Tuple[float, str]:
    """
    Analyze how relevant the agent response is to the lead's message.

    Returns score (0-1) and feedback.
    """
    lead_lower = lead_msg.lower()
    agent_lower = agent_msg.lower()

    # Check if response addresses keywords from lead message
    lead_keywords = set(re.findall(r'\b\w{4,}\b', lead_lower))
    agent_keywords = set(re.findall(r'\b\w{4,}\b', agent_lower))

    # Overlap calculation
    overlap = len(lead_keywords & agent_keywords)
    if len(lead_keywords) > 0:
        relevance = min(overlap / len(lead_keywords) * 2, 1.0)  # Scale up
    else:
        relevance = 0.5  # Neutral if no keywords to match

    # Check for question continuation (agent asking follow-up)
    if "?" in agent_msg:
        relevance = min(relevance + 0.2, 1.0)

    # Feedback generation
    if relevance >= 0.8:
        feedback = "Excellent relevance - directly addresses lead's topic"
    elif relevance >= 0.6:
        feedback = "Good relevance - covers main points"
    elif relevance >= 0.4:
        feedback = "Moderate - consider addressing specific points raised"
    else:
        feedback = "Low relevance - response may seem off-topic to lead"

    return round(relevance, 2), feedback


def analyze_empathy(agent_msg: str, lead_msg: str) -> Tuple[float, str]:
    """
    Analyze empathy level in agent response.

    Returns score (0-1) and feedback.
    """
    empathy_indicators = [
        r"\bi understand\b", r"\bi see\b", r"\bthat makes sense\b",
        r"\bof course\b", r"\babsolutely\b", r"\bgreat\b",
        r"\bexcellent\b", r"\bperfect\b", r"\bthank\b",
        r"\bappreciate\b", r"\bhappy to\b", r"\blove to\b"
    ]

    dismissive_indicators = [
        r"\bactually\b", r"\bbut\b.*first", r"\bno\b,",
        r"\bthat's not\b", r"\byou should\b"
    ]

    agent_lower = agent_msg.lower()

    # Count empathy indicators
    empathy_count = sum(1 for pattern in empathy_indicators if re.search(pattern, agent_lower))
    dismissive_count = sum(1 for pattern in dismissive_indicators if re.search(pattern, agent_lower))

    # Calculate score
    base_score = 0.5
    score = base_score + (empathy_count * 0.15) - (dismissive_count * 0.2)
    score = max(0, min(score, 1.0))

    # Feedback
    if score >= 0.8:
        feedback = "Strong empathy - lead feels heard and valued"
    elif score >= 0.6:
        feedback = "Adequate empathy - consider more acknowledgment phrases"
    elif score >= 0.4:
        feedback = "Limited empathy - add more validation before responding"
    else:
        feedback = "Empathy gap - response may feel dismissive"

    return round(score, 2), feedback


def analyze_completeness(agent_msg: str, lead_msg: str) -> Tuple[float, str]:
    """
    Analyze completeness of agent response.

    Returns score (0-1) and feedback.
    """
    # Check if lead asked a question
    lead_asked_question = "?" in lead_msg

    # Check response length
    word_count = len(agent_msg.split())

    # Check if response includes action/next step
    has_action = any(phrase in agent_msg.lower() for phrase in [
        "i'll", "i will", "let me", "would you like",
        "can i", "shall we", "how about"
    ])

    # Calculate score
    score = 0.5

    if word_count >= 20:
        score += 0.2
    elif word_count >= 10:
        score += 0.1

    if has_action:
        score += 0.2

    if lead_asked_question:
        # Check if response actually answers
        if "?" not in agent_msg or word_count > 15:
            score += 0.1
        else:
            score -= 0.1  # Deflected with another question

    score = max(0, min(score, 1.0))

    # Feedback
    if score >= 0.8:
        feedback = "Complete response with clear next steps"
    elif score >= 0.6:
        feedback = "Adequate coverage - consider adding specific action items"
    elif score >= 0.4:
        feedback = "Partial response - may leave lead with unanswered questions"
    else:
        feedback = "Incomplete - ensure all lead questions are addressed"

    return round(score, 2), feedback


def analyze_persuasiveness(agent_msg: str) -> Tuple[float, str]:
    """
    Analyze persuasive elements in response.

    Returns score (0-1) and feedback.
    """
    persuasive_elements = {
        "value_statement": [r"benefit", r"advantage", r"help you", r"save", r"best"],
        "social_proof": [r"other (buyers|clients)", r"many people", r"typically"],
        "urgency": [r"limited", r"available", r"soon", r"quickly"],
        "cta": [r"would you like", r"can i", r"shall we", r"let's", r"ready to"]
    }

    agent_lower = agent_msg.lower()
    elements_found = {}

    for element, patterns in persuasive_elements.items():
        elements_found[element] = any(re.search(p, agent_lower) for p in patterns)

    # Calculate score
    score = sum(0.25 for found in elements_found.values() if found)

    # Feedback
    if score >= 0.75:
        feedback = "Strong persuasive elements with clear call-to-action"
    elif score >= 0.5:
        feedback = "Some persuasive language - strengthen with value propositions"
    elif score >= 0.25:
        feedback = "Limited persuasion - add benefits and CTAs"
    else:
        feedback = "No persuasive elements - consider value-focused language"

    return round(score, 2), feedback


def analyze_personalization(agent_msg: str, conversation_context: List[Dict]) -> Tuple[float, str]:
    """
    Analyze personalization level based on context usage.

    Returns score (0-1) and feedback.
    """
    # Extract information mentioned by lead
    lead_info = {}
    for msg in conversation_context:
        if msg.get("role") == "lead":
            content = msg.get("content", "").lower()
            # Look for specific data
            if "$" in content or "budget" in content:
                lead_info["budget_mentioned"] = True
            if any(area in content for area in ["austin", "round rock", "pflugerville", "teravista"]):
                lead_info["location_mentioned"] = True
            if any(word in content for word in ["kids", "children", "family", "school"]):
                lead_info["family_mentioned"] = True

    # Check if agent references lead's specific info
    agent_lower = agent_msg.lower()
    references = 0

    if lead_info.get("budget_mentioned") and any(word in agent_lower for word in ["budget", "price", "range"]):
        references += 1
    if lead_info.get("location_mentioned") and any(word in agent_lower for word in ["area", "neighborhood", "location"]):
        references += 1
    if lead_info.get("family_mentioned") and any(word in agent_lower for word in ["family", "kids", "school"]):
        references += 1

    # Calculate score
    total_info = len([v for v in lead_info.values() if v])
    if total_info > 0:
        score = min(references / total_info, 1.0)
    else:
        score = 0.5  # Neutral if no lead info to reference

    # Feedback
    if score >= 0.8:
        feedback = "Excellent personalization - references specific lead details"
    elif score >= 0.5:
        feedback = "Some personalization - use more of lead's stated preferences"
    else:
        feedback = "Generic response - incorporate lead's specific needs"

    return round(score, 2), feedback


def detect_objections(messages: List[Dict]) -> List[Dict]:
    """Detect objections in conversation."""
    objections = []

    objection_patterns = {
        "price": [r"expensive", r"budget", r"afford", r"cheaper"],
        "timeline": [r"not ready", r"need time", r"think about", r"rush"],
        "features": [r"too small", r"doesn't have", r"need more"],
        "competition": [r"another agent", r"comparing", r"other homes"],
        "authority": [r"spouse", r"partner", r"family", r"check with"]
    }

    for i, msg in enumerate(messages):
        if msg.get("role") != "lead":
            continue

        content = msg.get("content", "").lower()

        for obj_type, patterns in objection_patterns.items():
            if any(re.search(p, content) for p in patterns):
                # Check if resolved in next agent message
                resolved = False
                if i + 1 < len(messages) and messages[i + 1].get("role") == "agent":
                    resolved = len(messages[i + 1].get("content", "")) > 50

                objections.append({
                    "type": obj_type,
                    "message_index": i,
                    "content_snippet": content[:100],
                    "resolved": resolved
                })
                break

    return objections


def detect_missed_opportunities(messages: List[Dict]) -> List[Dict]:
    """Detect missed opportunities in conversation."""
    opportunities = []

    # Check for unasked qualification questions
    qualification_questions = {
        "budget": ["budget", "price range", "afford"],
        "timeline": ["when", "timeline", "move by"],
        "pre_approval": ["pre-approved", "financing", "lender"],
        "motivation": ["why", "reason", "looking for"]
    }

    asked = set()
    for msg in messages:
        if msg.get("role") == "agent":
            content = msg.get("content", "").lower()
            for q_type, keywords in qualification_questions.items():
                if any(kw in content for kw in keywords):
                    asked.add(q_type)

    # Check what wasn't asked after 5+ exchanges
    if len(messages) >= 10:
        for q_type in qualification_questions:
            if q_type not in asked:
                opportunities.append({
                    "type": "missing_qualification",
                    "detail": f"Never asked about {q_type}",
                    "recommendation": f"Ask about {q_type} to better qualify lead"
                })

    # Check for buying signals that weren't followed up
    buying_signals = ["pre-approved", "lease ends", "need to move", "ready to"]
    for i, msg in enumerate(messages):
        if msg.get("role") == "lead":
            content = msg.get("content", "").lower()
            for signal in buying_signals:
                if signal in content:
                    # Check if agent followed up
                    if i + 1 < len(messages):
                        agent_response = messages[i + 1].get("content", "").lower()
                        if "schedule" not in agent_response and "view" not in agent_response:
                            opportunities.append({
                                "type": "missed_signal",
                                "detail": f"Lead mentioned '{signal}' but no viewing scheduled",
                                "recommendation": "Suggest scheduling property viewings"
                            })

    return opportunities


def calculate_quality_trend(qualities: List[ResponseQuality]) -> str:
    """Calculate quality trend over conversation."""
    if len(qualities) < 3:
        return "insufficient_data"

    scores = [q.overall_score for q in qualities]
    first_half = statistics.mean(scores[:len(scores)//2])
    second_half = statistics.mean(scores[len(scores)//2:])

    if second_half > first_half * 1.1:
        return "improving"
    elif second_half < first_half * 0.9:
        return "declining"
    else:
        return "stable"


def generate_coaching_summary(
    qualities: List[ResponseQuality],
    objections: List[Dict],
    missed_opportunities: List[Dict]
) -> Dict[str, Any]:
    """Generate coaching summary from analysis."""
    # Calculate average scores by category
    if not qualities:
        return {"status": "no_responses_to_analyze"}

    avg_scores = {
        "relevance": statistics.mean([q.relevance_score for q in qualities]),
        "empathy": statistics.mean([q.empathy_score for q in qualities]),
        "completeness": statistics.mean([q.completeness_score for q in qualities]),
        "persuasiveness": statistics.mean([q.persuasiveness_score for q in qualities]),
        "personalization": statistics.mean([q.personalization_score for q in qualities])
    }

    # Identify weakest areas
    sorted_scores = sorted(avg_scores.items(), key=lambda x: x[1])
    improvement_priorities = [
        {"area": area, "score": round(score, 2)}
        for area, score in sorted_scores[:2]  # Bottom 2
    ]

    # Calculate objection resolution rate
    if objections:
        resolved = sum(1 for o in objections if o.get("resolved"))
        resolution_rate = resolved / len(objections)
    else:
        resolution_rate = 1.0  # No objections = 100% resolved

    return {
        "avg_scores": {k: round(v, 2) for k, v in avg_scores.items()},
        "improvement_priorities": improvement_priorities,
        "objection_count": len(objections),
        "objection_resolution_rate": round(resolution_rate, 2),
        "missed_opportunity_count": len(missed_opportunities),
        "top_recommendations": [
            f"Focus on improving {improvement_priorities[0]['area']}" if improvement_priorities else "Maintain current performance",
            f"Address {len([o for o in objections if not o.get('resolved')])} unresolved objections" if objections else "No objections to address",
            missed_opportunities[0]["recommendation"] if missed_opportunities else "No missed opportunities detected"
        ]
    }


def analyze_transcript(
    conversation_id: str = None,
    file_path: str = None
) -> TranscriptAnalysis:
    """
    Perform comprehensive transcript analysis.

    Args:
        conversation_id: ID to load from services
        file_path: Path to transcript JSON file

    Returns:
        TranscriptAnalysis with complete results
    """
    messages = load_transcript(conversation_id, file_path)

    if not messages:
        return TranscriptAnalysis(
            conversation_id=conversation_id or "unknown",
            message_count=0,
            agent_response_count=0,
            avg_quality_score=0,
            quality_trend="unknown",
            response_qualities=[],
            objections_detected=[],
            missed_opportunities=[],
            conversation_health="unknown",
            coaching_summary={},
            analysis_timestamp=datetime.now().isoformat()
        )

    # Analyze each agent response
    qualities = []
    for i, msg in enumerate(messages):
        if msg.get("role") != "agent":
            continue

        # Get preceding lead message
        lead_msg = ""
        if i > 0 and messages[i-1].get("role") == "lead":
            lead_msg = messages[i-1].get("content", "")

        # Context is all messages up to this point
        context = messages[:i+1]

        # Analyze response quality
        relevance, _ = analyze_relevance(msg["content"], lead_msg)
        empathy, _ = analyze_empathy(msg["content"], lead_msg)
        completeness, _ = analyze_completeness(msg["content"], lead_msg)
        persuasiveness, _ = analyze_persuasiveness(msg["content"])
        personalization, _ = analyze_personalization(msg["content"], context)

        overall = (
            relevance * 0.25 +
            empathy * 0.20 +
            completeness * 0.20 +
            persuasiveness * 0.20 +
            personalization * 0.15
        )

        # Generate improvement suggestions
        suggestions = []
        if relevance < 0.6:
            suggestions.append("Address lead's specific question more directly")
        if empathy < 0.6:
            suggestions.append("Add acknowledgment before providing information")
        if completeness < 0.6:
            suggestions.append("Ensure all questions are fully answered")
        if persuasiveness < 0.6:
            suggestions.append("Include clear value proposition and call-to-action")
        if personalization < 0.6:
            suggestions.append("Reference lead's specific stated preferences")

        qualities.append(ResponseQuality(
            message_index=i,
            relevance_score=relevance,
            empathy_score=empathy,
            completeness_score=completeness,
            persuasiveness_score=persuasiveness,
            personalization_score=personalization,
            overall_score=round(overall, 2),
            improvement_suggestions=suggestions[:2]  # Top 2 per response
        ))

    # Detect objections and opportunities
    objections = detect_objections(messages)
    opportunities = detect_missed_opportunities(messages)

    # Calculate trend and health
    trend = calculate_quality_trend(qualities)

    avg_quality = statistics.mean([q.overall_score for q in qualities]) if qualities else 0
    if avg_quality >= 0.75:
        health = "excellent"
    elif avg_quality >= 0.6:
        health = "good"
    elif avg_quality >= 0.4:
        health = "concerning"
    else:
        health = "poor"

    # Generate coaching summary
    coaching = generate_coaching_summary(qualities, objections, opportunities)

    return TranscriptAnalysis(
        conversation_id=conversation_id or "file_input",
        message_count=len(messages),
        agent_response_count=len(qualities),
        avg_quality_score=round(avg_quality, 2),
        quality_trend=trend,
        response_qualities=qualities,
        objections_detected=objections,
        missed_opportunities=opportunities,
        conversation_health=health,
        coaching_summary=coaching,
        analysis_timestamp=datetime.now().isoformat()
    )


def main():
    parser = argparse.ArgumentParser(description="Analyze conversation transcript")
    parser.add_argument("--conversation-id", type=str, help="Conversation ID")
    parser.add_argument("--file", type=str, help="Path to transcript JSON")
    parser.add_argument("--output", type=str, default="json", choices=["json", "report"])

    args = parser.parse_args()

    if not args.conversation_id and not args.file:
        parser.print_help()
        sys.exit(1)

    analysis = analyze_transcript(args.conversation_id, args.file)

    if args.output == "report":
        print(f"Conversation Analysis Report")
        print(f"{'=' * 50}")
        print(f"Conversation ID: {analysis.conversation_id}")
        print(f"Messages: {analysis.message_count} ({analysis.agent_response_count} agent responses)")
        print(f"Average Quality Score: {analysis.avg_quality_score:.0%}")
        print(f"Quality Trend: {analysis.quality_trend}")
        print(f"Conversation Health: {analysis.conversation_health.upper()}")
        print()
        print("Objections Detected:")
        for obj in analysis.objections_detected:
            status = "Resolved" if obj["resolved"] else "UNRESOLVED"
            print(f"  - {obj['type'].title()}: {status}")
        print()
        print("Missed Opportunities:")
        for opp in analysis.missed_opportunities:
            print(f"  - {opp['detail']}")
        print()
        print("Coaching Recommendations:")
        for rec in analysis.coaching_summary.get("top_recommendations", []):
            print(f"  - {rec}")
    else:
        # Convert dataclasses to dicts for JSON
        output = {
            "conversation_id": analysis.conversation_id,
            "message_count": analysis.message_count,
            "agent_response_count": analysis.agent_response_count,
            "avg_quality_score": analysis.avg_quality_score,
            "quality_trend": analysis.quality_trend,
            "conversation_health": analysis.conversation_health,
            "objections_detected": analysis.objections_detected,
            "missed_opportunities": analysis.missed_opportunities,
            "coaching_summary": analysis.coaching_summary,
            "analysis_timestamp": analysis.analysis_timestamp
        }
        print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
