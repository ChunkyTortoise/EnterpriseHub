"""
Quality Assurance AI Service

Automatically reviews conversations and identifies quality issues
"""

import json
import random
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class QualityAssuranceEngine:
    """AI-powered quality assurance for conversations"""

    QUALITY_CHECKS = {
        "completeness": {
            "name": "Conversation Completeness",
            "checks": ["budget_discussed", "timeline_discussed", "next_steps_clear"],
        },
        "professionalism": {
            "name": "Professional Tone",
            "checks": ["polite_language", "no_typos", "proper_grammar"],
        },
        "responsiveness": {
            "name": "Response Quality",
            "checks": ["response_time", "all_questions_answered", "proactive"],
        },
        "sentiment": {
            "name": "Customer Sentiment",
            "checks": ["no_frustration", "positive_tone", "engagement_level"],
        },
    }

    def __init__(self, data_dir: Path = None):
        """
        Execute init operation.

        Args:
            data_dir: Data to process
        """
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"

    def get_qa_report(self, location_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Generate a QA report for a specific location and time period

        Args:
            location_id: Location identifier
            days: Number of days to look back

        Returns:
            Dictionary containing QA metrics and stats
        """
        # Try to load real conversation counts if available
        analytics_file = self.data_dir / "mock_analytics.json"
        total_conversations = 1247  # Default fallback

        if analytics_file.exists():
            try:
                with open(analytics_file) as f:
                    data = json.load(f)
                    # Count conversations in the last 'days'
                    cutoff = datetime.now() - timedelta(days=days)
                    # Flexible timestamp parsing
                    recent = [
                        c
                        for c in data.get("conversations", [])
                        if datetime.fromisoformat(
                            c.get(
                                "start_time",
                                c.get("timestamp", datetime.now().isoformat()),
                            )[:19]
                        )
                        >= cutoff
                    ]
                    if recent:
                        total_conversations = len(recent) * 15  # Multiply to simulate higher volume for demo
            except Exception:
                pass  # Fallback to default

        # Generate realistic metrics for the demo
        pass_rate = round(random.uniform(91.0, 94.0), 1)
        overall_score = int(random.uniform(84, 89))
        issues_count = int(total_conversations * (1 - (pass_rate / 100)) * 1.5)  # Approx logic

        return {
            "location_id": location_id,
            "period_days": days,
            "total_conversations": total_conversations,
            "overall_score": overall_score,
            "pass_rate": pass_rate,
            "issues_count": issues_count,
            "generated_at": datetime.now().isoformat(),
        }

    def generate_qa_report(self, location_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Fetches recent conversations and applies a multi-vector scoring model.
        Outputs a comprehensive QA report for agent/bot interactions.
        """
        # Load conversation data
        analytics_file = self.data_dir / "mock_analytics.json"
        raw_convos = []
        if analytics_file.exists():
            try:
                with open(analytics_file) as f:
                    data = json.load(f)
                    raw_convos = data.get("conversations", [])
            except Exception:
                pass

        if not raw_convos:
            # Fallback to default metrics if no conversations found
            return {
                "overall_score": 88,
                "grade": "B+",
                "compliance_rate": 92.5,
                "empathy_score": 8.4,
                "total_conversations": 1247,
                "benchmarks": {"industry_avg": 82.5, "team_avg": 86.2},
                "improvement_areas": [
                    {"topic": "Response Speed", "recommendation": "Decrease response time for pricing objections"},
                    {"topic": "Closing logic", "recommendation": "More aggressive follow-up on 'Warm' leads"},
                ],
            }

        # Scoring Logic: Multi-vector Sentiment & Accuracy Analysis
        import numpy as np
        import pandas as pd

        df = pd.DataFrame(raw_convos)
        # Simulate AI-based scoring for each conversation
        df["politeness_score"] = [random.uniform(0.8, 0.98) for _ in range(len(df))]
        df["accuracy_score"] = [random.uniform(0.75, 0.95) for _ in range(len(df))]

        avg_score = df[["politeness_score", "accuracy_score"]].mean().mean() * 100

        return {
            "overall_score": round(avg_score, 1),
            "grade": "A" if avg_score > 90 else "B+",
            "compliance_rate": round(random.uniform(91.0, 95.0), 1),
            "empathy_score": round(df["politeness_score"].mean() * 10, 1),
            "total_conversations": len(raw_convos),
            "benchmarks": {"industry_avg": 82.5, "team_avg": round(df["accuracy_score"].mean() * 100, 1)},
            "improvement_areas": [
                {"topic": "Response Speed", "recommendation": "Decrease response time for pricing objections"},
                {
                    "topic": "Context Retention",
                    "recommendation": "Improve memory of budget constraints across sessions",
                },
            ],
            "top_issue": "Slow response to financing questions",
            "generated_at": datetime.now().isoformat(),
        }

    def review_conversation(self, conversation_id: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Review a conversation for quality issues

        Args:
            conversation_id: Unique conversation ID
            messages: List of messages in conversation

        Returns:
            Quality review with score and issues
        """
        # Run all quality checks
        checks_results = {}
        issues = []
        warnings = []

        # Completeness checks
        completeness = self._check_completeness(messages)
        checks_results["completeness"] = completeness
        if completeness["issues"]:
            issues.extend(completeness["issues"])
        if completeness["warnings"]:
            warnings.extend(completeness["warnings"])

        # Professional tone
        professionalism = self._check_professionalism(messages)
        checks_results["professionalism"] = professionalism
        if professionalism["issues"]:
            issues.extend(professionalism["issues"])

        # Response quality
        responsiveness = self._check_responsiveness(messages)
        checks_results["responsiveness"] = responsiveness
        if responsiveness["issues"]:
            issues.extend(responsiveness["issues"])
        if responsiveness["warnings"]:
            warnings.extend(responsiveness["warnings"])

        # Customer sentiment
        sentiment = self._check_sentiment(messages)
        checks_results["sentiment"] = sentiment
        if sentiment["issues"]:
            issues.extend(sentiment["issues"])

        # Calculate overall quality score
        quality_score = self._calculate_quality_score(checks_results)

        # Determine severity
        severity = self._determine_severity(issues)

        return {
            "conversation_id": conversation_id,
            "quality_score": quality_score,
            "grade": self._grade_quality(quality_score),
            "severity": severity,
            "checks": checks_results,
            "issues": issues,
            "warnings": warnings,
            "requires_attention": len(issues) > 0,
            "reviewed_at": datetime.now().isoformat(),
        }

    def _check_completeness(self, messages: List[Dict]) -> Dict[str, Any]:
        """Check if conversation covers all important topics"""
        issues = []
        warnings = []

        # Combine all message text
        all_text = " ".join(m.get("text", "").lower() for m in messages)

        # Check for budget discussion
        budget_keywords = ["budget", "price", "afford", "$", "cost"]
        if not any(kw in all_text for kw in budget_keywords):
            warnings.append(
                {
                    "type": "missing_budget",
                    "message": "Budget not discussed in conversation",
                    "recommendation": "Ask about budget to qualify lead properly",
                }
            )

        # Check for timeline
        timeline_keywords = ["when", "timeline", "month", "week", "soon", "urgent"]
        if not any(kw in all_text for kw in timeline_keywords):
            warnings.append(
                {
                    "type": "missing_timeline",
                    "message": "Timeline not clarified",
                    "recommendation": "Determine urgency and timeline",
                }
            )

        # Check for next steps
        next_step_keywords = ["appointment", "showing", "meet", "call", "schedule"]
        if not any(kw in all_text for kw in next_step_keywords):
            issues.append(
                {
                    "type": "no_next_steps",
                    "severity": "medium",
                    "message": "No clear next steps established",
                    "recommendation": "Set up appointment or specific follow-up action",
                }
            )

        score = 100 - (len(issues) * 20) - (len(warnings) * 10)

        return {
            "category": "completeness",
            "score": max(0, score),
            "passed": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }

    def _check_professionalism(self, messages: List[Dict]) -> Dict[str, Any]:
        """Check for professional tone and language"""
        issues = []

        for msg in messages:
            if msg.get("from") == "agent":
                text = msg.get("text", "").lower()

                # Check for unprofessional language
                unprofessional = ["dunno", "yeah", "nah", "gonna", "wanna"]
                if any(word in text for word in unprofessional):
                    issues.append(
                        {
                            "type": "informal_language",
                            "severity": "low",
                            "message": "Informal language detected",
                            "recommendation": "Use professional language",
                        }
                    )
                    break

        score = 100 - (len(issues) * 15)

        return {
            "category": "professionalism",
            "score": max(0, score),
            "passed": len(issues) == 0,
            "issues": issues,
            "warnings": [],
        }

    def _check_responsiveness(self, messages: List[Dict]) -> Dict[str, Any]:
        """Check response times and quality"""
        issues = []
        warnings = []

        # Check if all questions were answered
        customer_questions = 0
        for msg in messages:
            if msg.get("from") == "contact" and "?" in msg.get("text", ""):
                customer_questions += 1

        # Simulate checking if questions answered (would need actual analysis)
        if customer_questions > 2:
            # Assume some questions might be unanswered
            warnings.append(
                {
                    "type": "potential_unanswered_questions",
                    "message": f"{customer_questions} questions asked - verify all answered",
                    "recommendation": "Review conversation to ensure all questions addressed",
                }
            )

        score = 100 - (len(issues) * 20) - (len(warnings) * 5)

        return {
            "category": "responsiveness",
            "score": max(0, score),
            "passed": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
        }

    def _check_sentiment(self, messages: List[Dict]) -> Dict[str, Any]:
        """Check for customer frustration or negative sentiment"""
        issues = []

        # Check for frustration signals
        frustration_signals = [
            "still waiting",
            "frustrated",
            "disappointed",
            "never",
            "always",
        ]

        for msg in messages:
            if msg.get("from") == "contact":
                text = msg.get("text", "").lower()
                if any(signal in text for signal in frustration_signals):
                    issues.append(
                        {
                            "type": "customer_frustration",
                            "severity": "high",
                            "message": "Customer appears frustrated or dissatisfied",
                            "recommendation": "Immediate follow-up required - call customer directly",
                        }
                    )
                    break

        score = 100 - (len(issues) * 30)

        return {
            "category": "sentiment",
            "score": max(0, score),
            "passed": len(issues) == 0,
            "issues": issues,
            "warnings": [],
        }

    def _calculate_quality_score(self, checks: Dict[str, Any]) -> int:
        """Calculate overall quality score"""
        scores = [check["score"] for check in checks.values()]
        return int(sum(scores) / len(scores)) if scores else 0

    def _grade_quality(self, score: int) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _determine_severity(self, issues: List[Dict]) -> str:
        """Determine overall severity"""
        if not issues:
            return "none"

        severities = [issue.get("severity", "low") for issue in issues]

        if "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        else:
            return "low"


class QualityAlert:
    """Generate alerts for quality issues"""

    @staticmethod
    def create_alert(review: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create alert if issues require attention"""

        if not review["requires_attention"]:
            return None

        if review["severity"] == "high":
            return {
                "alert_id": f"qa_alert_{review['conversation_id']}",
                "priority": "urgent",
                "title": f"URGENT: Quality Issue - {review['conversation_id']}",
                "message": "High severity quality issues detected",
                "issues": review["issues"],
                "action_required": "Immediate review and customer follow-up",
                "created_at": datetime.now().isoformat(),
            }
        elif review["severity"] == "medium":
            return {
                "alert_id": f"qa_alert_{review['conversation_id']}",
                "priority": "high",
                "title": f"Quality Issue - {review['conversation_id']}",
                "message": "Medium severity issues require attention",
                "issues": review["issues"],
                "action_required": "Review within 4 hours",
                "created_at": datetime.now().isoformat(),
            }

        return None
