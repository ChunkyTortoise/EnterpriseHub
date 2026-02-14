"""
Transcript Analysis Framework for Real Estate AI.

Analyzes historical successful closing conversations to identify winning patterns
and extract actionable insights for improving bot responses.

This framework supports:
- Import from multiple formats (JSON, CSV)
- Pattern extraction (keywords, conversation flow, timing)
- Success metrics analysis
- Insights generation for prompt optimization

Author: Phase 2 Agent C2
Version: 1.0.0
"""

import csv
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConversationMetrics:
    """Metrics for a single conversation."""

    transcript_id: str
    lead_type: str
    outcome: str
    close_reason: str
    questions_answered: int
    duration_minutes: float
    message_count: int
    avg_response_time_seconds: float
    questions_asked: int
    pathway_identified: Optional[str] = None


@dataclass
class PatternInsights:
    """Insights extracted from pattern analysis."""

    winning_questions: List[Dict[str, Any]]
    successful_closing_phrases: List[str]
    optimal_question_order: List[str]
    avg_questions_to_close: float
    avg_conversation_duration: float
    keyword_patterns: Dict[str, int]
    close_rate_by_lead_type: Dict[str, float]
    successful_pathway_signals: Dict[str, List[str]]


class TranscriptAnalyzer:
    """
    Analyze conversation transcripts to identify successful patterns.
    """

    def __init__(self, data_dir: str = "data"):
        """
        Initialize transcript analyzer.

        Args:
            data_dir: Directory containing transcript data files
        """
        self.data_dir = Path(data_dir)
        self.transcripts: List[Dict[str, Any]] = []
        self.metrics: List[ConversationMetrics] = []

        logger.info(f"Transcript analyzer initialized with data_dir: {self.data_dir}")

    # ==============================================================================
    # IMPORT FUNCTIONS
    # ==============================================================================

    def import_json(self, filepath: str) -> int:
        """
        Import transcripts from JSON file.

        Supports both single transcript objects and arrays of transcripts.

        Args:
            filepath: Path to JSON file

        Returns:
            Number of transcripts imported

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is invalid or missing required fields
        """
        file_path = Path(filepath)

        if not file_path.exists():
            raise FileNotFoundError(f"Transcript file not found: {filepath}")

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            # Handle different JSON structures
            if isinstance(data, dict):
                if "transcripts" in data:
                    # Schema with metadata wrapper
                    transcripts = data["transcripts"]
                else:
                    # Single transcript object
                    transcripts = [data]
            elif isinstance(data, list):
                # Array of transcripts
                transcripts = data
            else:
                raise ValueError("Invalid JSON structure: expected dict or list")

            # Validate and add transcripts
            imported_count = 0
            for transcript in transcripts:
                if self._validate_transcript(transcript):
                    self.transcripts.append(transcript)
                    imported_count += 1
                else:
                    logger.warning(f"Skipped invalid transcript: {transcript.get('id', 'unknown')}")

            logger.info(f"Imported {imported_count} transcripts from {filepath}")
            return imported_count

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {filepath}: {e}")
        except Exception as e:
            logger.error(f"Error importing JSON: {e}")
            raise

    def import_csv(self, filepath: str) -> int:
        """
        Import transcripts from CSV file.

        Expected CSV format:
        - id: Unique transcript ID
        - date: ISO timestamp
        - lead_type: buyer/seller
        - outcome: closed/lost
        - speaker: bot/user
        - message: Message text
        - timestamp: Message timestamp

        Args:
            filepath: Path to CSV file

        Returns:
            Number of transcripts imported

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If CSV format is invalid
        """
        file_path = Path(filepath)

        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {filepath}")

        try:
            # Group messages by transcript ID
            transcripts_dict = defaultdict(lambda: {"messages": [], "metadata": {}})

            with open(file_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    transcript_id = row.get("id")
                    if not transcript_id:
                        logger.warning("Skipping row with missing ID")
                        continue

                    # Store metadata (same for all messages in transcript)
                    if not transcripts_dict[transcript_id]["metadata"]:
                        transcripts_dict[transcript_id]["metadata"] = {
                            "id": transcript_id,
                            "date": row.get("date"),
                            "lead_type": row.get("lead_type"),
                            "outcome": row.get("outcome"),
                            "close_reason": row.get("close_reason", ""),
                        }

                    # Add message
                    message = {
                        "timestamp": row.get("timestamp"),
                        "speaker": row.get("speaker"),
                        "message": row.get("message"),
                        "metadata": {},
                    }
                    transcripts_dict[transcript_id]["messages"].append(message)

            # Convert to transcript format
            imported_count = 0
            for transcript_id, data in transcripts_dict.items():
                transcript = {
                    **data["metadata"],
                    "messages": sorted(data["messages"], key=lambda m: m["timestamp"]),
                }

                if self._validate_transcript(transcript):
                    self.transcripts.append(transcript)
                    imported_count += 1

            logger.info(f"Imported {imported_count} transcripts from CSV {filepath}")
            return imported_count

        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            raise

    def _validate_transcript(self, transcript: Dict[str, Any]) -> bool:
        """
        Validate transcript has required fields.

        Args:
            transcript: Transcript dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["id", "lead_type", "outcome", "messages"]

        for field in required_fields:
            if field not in transcript:
                logger.warning(f"Transcript missing required field: {field}")
                return False

        if not isinstance(transcript["messages"], list) or len(transcript["messages"]) == 0:
            logger.warning(f"Transcript {transcript['id']} has no messages")
            return False

        return True

    # ==============================================================================
    # METRICS CALCULATION
    # ==============================================================================

    def calculate_metrics(self) -> List[ConversationMetrics]:
        """
        Calculate metrics for all imported transcripts.

        Returns:
            List of ConversationMetrics objects
        """
        self.metrics = []

        for transcript in self.transcripts:
            metrics = self._calculate_single_metrics(transcript)
            self.metrics.append(metrics)

        logger.info(f"Calculated metrics for {len(self.metrics)} transcripts")
        return self.metrics

    def _calculate_single_metrics(self, transcript: Dict[str, Any]) -> ConversationMetrics:
        """
        Calculate metrics for a single transcript.

        Args:
            transcript: Transcript dictionary

        Returns:
            ConversationMetrics object
        """
        messages = transcript.get("messages", [])

        # Duration calculation
        if len(messages) >= 2:
            start_time = datetime.fromisoformat(messages[0]["timestamp"].replace("Z", "+00:00"))
            end_time = datetime.fromisoformat(messages[-1]["timestamp"].replace("Z", "+00:00"))
            duration_minutes = (end_time - start_time).total_seconds() / 60
        else:
            duration_minutes = 0.0

        # Count questions asked by bot
        questions_asked = sum(1 for msg in messages if msg["speaker"] == "bot" and "?" in msg["message"])

        # Calculate average response time
        response_times = []
        for i in range(1, len(messages)):
            if messages[i]["speaker"] != messages[i - 1]["speaker"]:
                prev_time = datetime.fromisoformat(messages[i - 1]["timestamp"].replace("Z", "+00:00"))
                curr_time = datetime.fromisoformat(messages[i]["timestamp"].replace("Z", "+00:00"))
                response_times.append((curr_time - prev_time).total_seconds())

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0

        # Detect pathway if present
        pathway = self._detect_pathway(messages)

        return ConversationMetrics(
            transcript_id=transcript.get("id", ""),
            lead_type=transcript.get("lead_type", ""),
            outcome=transcript.get("outcome", ""),
            close_reason=transcript.get("close_reason", ""),
            questions_answered=transcript.get("questions_answered", 0),
            duration_minutes=duration_minutes,
            message_count=len(messages),
            avg_response_time_seconds=avg_response_time,
            questions_asked=questions_asked,
            pathway_identified=pathway,
        )

    def _detect_pathway(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """
        Detect wholesale vs listing pathway from conversation.

        Args:
            messages: List of message dictionaries

        Returns:
            "wholesale", "listing", or None
        """
        # Combine all messages into text
        text = " ".join(msg["message"].lower() for msg in messages)

        # Wholesale indicators
        wholesale_keywords = [
            "as-is",
            "cash offer",
            "fast sale",
            "quick",
            "inherited",
            "fixer",
            "needs work",
            "no repairs",
        ]

        # Listing indicators
        listing_keywords = [
            "top dollar",
            "best price",
            "market value",
            "move-in ready",
            "updated",
            "renovated",
            "excellent condition",
        ]

        wholesale_count = sum(1 for kw in wholesale_keywords if kw in text)
        listing_count = sum(1 for kw in listing_keywords if kw in text)

        if wholesale_count > listing_count and wholesale_count > 0:
            return "wholesale"
        elif listing_count > wholesale_count and listing_count > 0:
            return "listing"

        return None

    # ==============================================================================
    # PATTERN ANALYSIS
    # ==============================================================================

    def analyze_patterns(self) -> PatternInsights:
        """
        Analyze patterns across all transcripts to identify success factors.

        Returns:
            PatternInsights object with extracted patterns
        """
        if not self.metrics:
            self.calculate_metrics()

        # Filter to successful closes
        successful = [m for m in self.metrics if m.outcome == "closed"]

        if not successful:
            logger.warning("No successful transcripts to analyze")
            return PatternInsights(
                winning_questions=[],
                successful_closing_phrases=[],
                optimal_question_order=[],
                avg_questions_to_close=0.0,
                avg_conversation_duration=0.0,
                keyword_patterns={},
                close_rate_by_lead_type={},
                successful_pathway_signals={},
            )

        # Analyze question patterns
        winning_questions = self._extract_winning_questions(successful)

        # Analyze closing phrases
        closing_phrases = self._extract_closing_phrases(successful)

        # Determine optimal question order
        question_order = self._determine_question_order(successful)

        # Calculate averages
        avg_questions = sum(m.questions_answered for m in successful) / len(successful)
        avg_duration = sum(m.duration_minutes for m in successful) / len(successful)

        # Extract keyword patterns
        keywords = self._extract_keyword_patterns()

        # Close rate by lead type
        close_rates = self._calculate_close_rates()

        # Pathway signals
        pathway_signals = self._extract_pathway_signals()

        insights = PatternInsights(
            winning_questions=winning_questions,
            successful_closing_phrases=closing_phrases,
            optimal_question_order=question_order,
            avg_questions_to_close=avg_questions,
            avg_conversation_duration=avg_duration,
            keyword_patterns=keywords,
            close_rate_by_lead_type=close_rates,
            successful_pathway_signals=pathway_signals,
        )

        logger.info("Pattern analysis complete")
        return insights

    def _extract_winning_questions(self, metrics: List[ConversationMetrics]) -> List[Dict[str, Any]]:
        """
        Extract questions that appear in successful conversations.

        Args:
            metrics: List of successful conversation metrics

        Returns:
            List of question patterns with frequency and success correlation
        """
        question_patterns = []
        question_counter = Counter()

        for transcript in self.transcripts:
            if transcript["outcome"] == "closed":
                [
                    msg["message"]
                    for msg in transcript["messages"]
                    if msg["speaker"] == "bot" and "?" in msg["message"]
                ]

                # Extract question types from metadata
                for msg in transcript["messages"]:
                    if msg["speaker"] == "bot" and msg.get("metadata", {}).get("question_type"):
                        q_type = msg["metadata"]["question_type"]
                        question_counter[q_type] += 1

        # Convert to structured format
        total_closed = len(metrics)
        for q_type, count in question_counter.most_common():
            question_patterns.append(
                {
                    "question_type": q_type,
                    "frequency": count,
                    "appears_in_percent": ((count / total_closed) * 100 if total_closed > 0 else 0),
                    "recommended": count / total_closed > 0.5,  # Appears in >50% of successful convos
                }
            )

        return question_patterns

    def _extract_closing_phrases(self, metrics: List[ConversationMetrics]) -> List[str]:
        """
        Extract phrases used when successfully closing leads.

        Args:
            metrics: List of successful conversation metrics

        Returns:
            List of closing phrases
        """
        closing_phrases = []

        for transcript in self.transcripts:
            if transcript["outcome"] == "closed":
                messages = transcript["messages"]

                # Find closing stage messages
                closing_messages = [
                    msg["message"]
                    for msg in messages
                    if msg["speaker"] == "bot" and msg.get("metadata", {}).get("stage") == "closing"
                ]

                closing_phrases.extend(closing_messages)

        # Deduplicate and return most common
        phrase_counter = Counter(closing_phrases)
        return [phrase for phrase, count in phrase_counter.most_common(10)]

    def _determine_question_order(self, metrics: List[ConversationMetrics]) -> List[str]:
        """
        Determine the optimal order of qualifying questions.

        Args:
            metrics: List of successful conversation metrics

        Returns:
            List of question types in optimal order
        """
        question_order_sequences = []

        for transcript in self.transcripts:
            if transcript["outcome"] == "closed":
                sequence = []
                for msg in transcript["messages"]:
                    if msg["speaker"] == "bot" and msg.get("metadata", {}).get("question_type"):
                        q_type = msg["metadata"]["question_type"]
                        if q_type not in sequence:  # Only track first occurrence
                            sequence.append(q_type)

                if sequence:
                    question_order_sequences.append(sequence)

        # Find most common sequence pattern
        if not question_order_sequences:
            return []

        # Calculate question position averages
        position_scores = defaultdict(list)
        for sequence in question_order_sequences:
            for i, q_type in enumerate(sequence):
                position_scores[q_type].append(i)

        # Sort by average position (questions asked earlier have lower avg position)
        optimal_order = sorted(
            position_scores.keys(),
            key=lambda q: sum(position_scores[q]) / len(position_scores[q]),
        )

        return optimal_order

    def _extract_keyword_patterns(self) -> Dict[str, int]:
        """
        Extract common keywords from successful conversations.

        Returns:
            Dictionary of keywords and their frequencies
        """
        keyword_counter = Counter()

        # Keywords to track (expanded from insights)
        tracked_keywords = [
            "budget",
            "location",
            "timeline",
            "beds",
            "baths",
            "pre-approved",
            "asap",
            "urgent",
            "cash",
            "financing",
            "schools",
            "move-in ready",
            "fixer",
            "as-is",
            "renovated",
            "updated",
            "condition",
        ]

        for transcript in self.transcripts:
            if transcript["outcome"] == "closed":
                text = " ".join(msg["message"].lower() for msg in transcript["messages"])

                for keyword in tracked_keywords:
                    if keyword in text:
                        keyword_counter[keyword] += 1

        return dict(keyword_counter.most_common(20))

    def _calculate_close_rates(self) -> Dict[str, float]:
        """
        Calculate close rates by lead type and other dimensions.

        Returns:
            Dictionary of close rates
        """
        close_rates = {}

        # By lead type
        buyer_total = sum(1 for m in self.metrics if m.lead_type == "buyer")
        buyer_closed = sum(1 for m in self.metrics if m.lead_type == "buyer" and m.outcome == "closed")

        seller_total = sum(1 for m in self.metrics if m.lead_type == "seller")
        seller_closed = sum(1 for m in self.metrics if m.lead_type == "seller" and m.outcome == "closed")

        close_rates["buyer"] = (buyer_closed / buyer_total * 100) if buyer_total > 0 else 0.0
        close_rates["seller"] = (seller_closed / seller_total * 100) if seller_total > 0 else 0.0
        close_rates["overall"] = (
            ((buyer_closed + seller_closed) / (buyer_total + seller_total) * 100)
            if (buyer_total + seller_total) > 0
            else 0.0
        )

        return close_rates

    def _extract_pathway_signals(self) -> Dict[str, List[str]]:
        """
        Extract signals that indicate wholesale vs listing pathway.

        Returns:
            Dictionary with wholesale and listing signal keywords
        """
        pathway_signals = {"wholesale": [], "listing": []}

        # Analyze transcripts with identified pathways
        for transcript in self.transcripts:
            if transcript["outcome"] == "closed":
                pathway = self._detect_pathway(transcript["messages"])

                if pathway:
                    # Extract insights if available
                    insights = transcript.get("insights", {})
                    signals = insights.get("pathway_signals", [])

                    if signals and pathway in pathway_signals:
                        pathway_signals[pathway].extend(signals)

        # Deduplicate
        pathway_signals["wholesale"] = list(set(pathway_signals["wholesale"]))
        pathway_signals["listing"] = list(set(pathway_signals["listing"]))

        # Add known patterns if empty
        if not pathway_signals["wholesale"]:
            pathway_signals["wholesale"] = [
                "as-is",
                "fast",
                "cash offer",
                "no repairs",
                "inherited",
                "fixer",
            ]

        if not pathway_signals["listing"]:
            pathway_signals["listing"] = [
                "top dollar",
                "best price",
                "market value",
                "move-in ready",
                "updated",
                "renovated",
            ]

        return pathway_signals

    # ==============================================================================
    # INSIGHTS GENERATION
    # ==============================================================================

    def generate_insights_report(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive insights report.

        Args:
            output_path: Optional path to save JSON report

        Returns:
            Dictionary containing full insights report
        """
        if not self.metrics:
            self.calculate_metrics()

        patterns = self.analyze_patterns()

        # Build comprehensive report
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_transcripts": len(self.transcripts),
                "successful_closes": len([m for m in self.metrics if m.outcome == "closed"]),
                "close_rate": patterns.close_rate_by_lead_type.get("overall", 0.0),
                "avg_questions_to_close": patterns.avg_questions_to_close,
                "avg_conversation_duration_minutes": patterns.avg_conversation_duration,
            },
            "patterns": {
                "winning_questions": patterns.winning_questions,
                "successful_closing_phrases": patterns.successful_closing_phrases,
                "optimal_question_order": patterns.optimal_question_order,
                "keyword_patterns": patterns.keyword_patterns,
                "pathway_signals": patterns.successful_pathway_signals,
            },
            "metrics": {
                "close_rates": patterns.close_rate_by_lead_type,
                "conversations_by_type": self._get_type_breakdown(),
            },
            "recommendations": self._generate_recommendations(patterns),
        }

        # Save to file if requested
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)

            logger.info(f"Insights report saved to {output_path}")

        return report

    def _get_type_breakdown(self) -> Dict[str, int]:
        """Get breakdown of conversations by type."""
        return {
            "buyer": sum(1 for m in self.metrics if m.lead_type == "buyer"),
            "seller": sum(1 for m in self.metrics if m.lead_type == "seller"),
            "total": len(self.metrics),
        }

    def _generate_recommendations(self, patterns: PatternInsights) -> List[Dict[str, str]]:
        """
        Generate actionable recommendations based on patterns.

        Args:
            patterns: PatternInsights object

        Returns:
            List of recommendations
        """
        recommendations = []

        # Question order recommendation
        if patterns.optimal_question_order:
            recommendations.append(
                {
                    "category": "Question Sequencing",
                    "recommendation": f"Lead with {patterns.optimal_question_order[0]} question, "
                    f"followed by {', '.join(patterns.optimal_question_order[1:3])}",
                    "impact": "high",
                    "implementation": "Update system_prompts.py qualifying section",
                }
            )

        # Question count recommendation
        if patterns.avg_questions_to_close < 7:
            recommendations.append(
                {
                    "category": "Qualification Efficiency",
                    "recommendation": f"On average, {patterns.avg_questions_to_close:.1f} questions "
                    f"answered before close. Don't over-qualify - offer action after 3-4 questions.",
                    "impact": "high",
                    "implementation": "Adjust lead_scorer.py thresholds",
                }
            )

        # Duration recommendation
        if patterns.avg_conversation_duration < 10:
            recommendations.append(
                {
                    "category": "Conversation Pacing",
                    "recommendation": f"Successful conversations average {patterns.avg_conversation_duration:.1f} minutes. "
                    f"Keep it concise and move to action quickly.",
                    "impact": "medium",
                    "implementation": "Emphasize brevity in prompts",
                }
            )

        # Pathway signals
        if patterns.successful_pathway_signals:
            recommendations.append(
                {
                    "category": "Pathway Detection",
                    "recommendation": "Add pathway detection keywords to early qualification",
                    "impact": "high",
                    "implementation": f"Monitor for wholesale signals: {', '.join(patterns.successful_pathway_signals.get('wholesale', [])[:3])}",
                }
            )

        # Closing phrases
        if patterns.successful_closing_phrases:
            top_phrase = patterns.successful_closing_phrases[0] if patterns.successful_closing_phrases else ""
            recommendations.append(
                {
                    "category": "Closing Language",
                    "recommendation": f"Most successful closing phrase: '{top_phrase}'",
                    "impact": "medium",
                    "implementation": "Add to APPOINTMENT_SETTING_PROMPT templates",
                }
            )

        return recommendations

    # ==============================================================================
    # EXPORT FUNCTIONS
    # ==============================================================================

    def export_metrics_csv(self, output_path: str) -> None:
        """
        Export calculated metrics to CSV.

        Args:
            output_path: Path to save CSV file
        """
        if not self.metrics:
            self.calculate_metrics()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", newline="") as f:
            if not self.metrics:
                logger.warning("No metrics to export")
                return

            # Use dataclass fields as headers
            fieldnames = list(asdict(self.metrics[0]).keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for metric in self.metrics:
                writer.writerow(asdict(metric))

        logger.info(f"Exported metrics to {output_path}")


# ==============================================================================
# CLI INTERFACE (for testing)
# ==============================================================================

if __name__ == "__main__":
    import sys

    analyzer = TranscriptAnalyzer(data_dir="data")

    # Import sample data
    try:
        count = analyzer.import_json("data/sample_transcripts.json")
        print(f"Imported {count} transcripts")

        # Calculate metrics
        metrics = analyzer.calculate_metrics()
        print(f"\nCalculated metrics for {len(metrics)} conversations")

        # Analyze patterns
        patterns = analyzer.analyze_patterns()
        print(f"\nPattern Analysis:")
        print(f"  - Average questions to close: {patterns.avg_questions_to_close:.1f}")
        print(f"  - Average duration: {patterns.avg_conversation_duration:.1f} minutes")
        print(f"  - Optimal question order: {', '.join(patterns.optimal_question_order[:3])}")

        # Generate report
        report = analyzer.generate_insights_report(output_path="data/insights_report.json")
        print(f"\nInsights report generated: data/insights_report.json")
        print(f"\nTop Recommendations:")
        for i, rec in enumerate(report["recommendations"][:3], 1):
            print(f"  {i}. [{rec['category']}] {rec['recommendation']}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
