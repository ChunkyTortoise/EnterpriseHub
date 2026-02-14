"""
Tests for Transcript Analyzer Service.

Tests cover:
- Import validation (JSON, CSV)
- Metrics calculation
- Pattern extraction
- Insights generation
- Error handling
"""

import csv
import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from ghl_real_estate_ai.services.transcript_analyzer import ConversationMetrics, PatternInsights, TranscriptAnalyzer

# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def sample_transcript():
    """Single valid transcript for testing."""
    return {
        "id": "test_001",
        "date": "2025-12-15T14:23:00Z",
        "lead_type": "buyer",
        "outcome": "closed",
        "close_reason": "scheduled_showing",
        "questions_answered": 5,
        "conversation_duration_minutes": 8,
        "messages": [
            {
                "timestamp": "2025-12-15T14:23:00Z",
                "speaker": "bot",
                "message": "Hey! What's up?",
                "metadata": {"stage": "initial_contact"},
            },
            {
                "timestamp": "2025-12-15T14:23:45Z",
                "speaker": "user",
                "message": "Looking to buy a house",
                "metadata": {},
            },
            {
                "timestamp": "2025-12-15T14:24:10Z",
                "speaker": "bot",
                "message": "What's your budget?",
                "metadata": {"stage": "qualifying", "question_type": "budget"},
            },
            {
                "timestamp": "2025-12-15T14:24:55Z",
                "speaker": "user",
                "message": "$400k",
                "metadata": {"extracted_data": {"budget": "400000"}},
            },
            {
                "timestamp": "2025-12-15T14:25:20Z",
                "speaker": "bot",
                "message": "Want me to get someone on the phone with you?",
                "metadata": {"stage": "closing", "action": "offer_appointment"},
            },
        ],
    }


@pytest.fixture
def sample_wholesale_transcript():
    """Seller transcript with wholesale pathway."""
    return {
        "id": "test_wholesale_001",
        "date": "2025-12-18T11:30:00Z",
        "lead_type": "seller",
        "outcome": "closed",
        "close_reason": "wholesale_offer",
        "questions_answered": 3,
        "messages": [
            {
                "timestamp": "2025-12-18T11:30:00Z",
                "speaker": "bot",
                "message": "Hey! What's up?",
                "metadata": {"stage": "initial_contact"},
            },
            {
                "timestamp": "2025-12-18T11:30:45Z",
                "speaker": "user",
                "message": "Need to sell my house ASAP, it's a fixer-upper",
                "metadata": {},
            },
            {
                "timestamp": "2025-12-18T11:31:15Z",
                "speaker": "bot",
                "message": "Interested in a fast cash offer? Sell as-is",
                "metadata": {"stage": "closing", "action": "offer_wholesale"},
            },
            {"timestamp": "2025-12-18T11:31:45Z", "speaker": "user", "message": "Yes exactly", "metadata": {}},
        ],
    }


@pytest.fixture
def analyzer():
    """TranscriptAnalyzer instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield TranscriptAnalyzer(data_dir=tmpdir)


# ==============================================================================
# IMPORT TESTS
# ==============================================================================


class TestImportJSON:
    """Test JSON import functionality."""

    def test_import_single_transcript(self, analyzer, sample_transcript):
        """Test importing a single transcript from JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_transcript, f)
            filepath = f.name

        try:
            count = analyzer.import_json(filepath)
            assert count == 1
            assert len(analyzer.transcripts) == 1
            assert analyzer.transcripts[0]["id"] == "test_001"
        finally:
            Path(filepath).unlink()

    def test_import_transcript_array(self, analyzer, sample_transcript):
        """Test importing array of transcripts."""
        transcripts = [sample_transcript, {**sample_transcript, "id": "test_002"}]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(transcripts, f)
            filepath = f.name

        try:
            count = analyzer.import_json(filepath)
            assert count == 2
            assert len(analyzer.transcripts) == 2
        finally:
            Path(filepath).unlink()

    def test_import_wrapped_transcripts(self, analyzer, sample_transcript):
        """Test importing transcripts with metadata wrapper."""
        data = {"schema_version": "1.0", "transcripts": [sample_transcript]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            filepath = f.name

        try:
            count = analyzer.import_json(filepath)
            assert count == 1
        finally:
            Path(filepath).unlink()

    def test_import_invalid_json(self, analyzer):
        """Test handling of invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json }")
            filepath = f.name

        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                analyzer.import_json(filepath)
        finally:
            Path(filepath).unlink()

    def test_import_missing_file(self, analyzer):
        """Test handling of missing file."""
        with pytest.raises(FileNotFoundError):
            analyzer.import_json("/nonexistent/file.json")

    def test_import_invalid_transcript_structure(self, analyzer):
        """Test handling of transcript missing required fields."""
        invalid = {
            "id": "test_001",
            # Missing lead_type, outcome, messages
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid, f)
            filepath = f.name

        try:
            count = analyzer.import_json(filepath)
            assert count == 0  # Invalid transcript should be skipped
        finally:
            Path(filepath).unlink()


class TestImportCSV:
    """Test CSV import functionality."""

    def test_import_csv_basic(self, analyzer):
        """Test basic CSV import."""
        csv_data = [
            ["id", "date", "lead_type", "outcome", "close_reason", "timestamp", "speaker", "message"],
            ["test_001", "2025-12-15T14:23:00Z", "buyer", "closed", "showing", "2025-12-15T14:23:00Z", "bot", "Hey!"],
            ["test_001", "2025-12-15T14:23:00Z", "buyer", "closed", "showing", "2025-12-15T14:23:45Z", "user", "Hi"],
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
            filepath = f.name

        try:
            count = analyzer.import_csv(filepath)
            assert count == 1
            assert len(analyzer.transcripts[0]["messages"]) == 2
        finally:
            Path(filepath).unlink()

    def test_import_csv_multiple_transcripts(self, analyzer):
        """Test importing multiple transcripts from CSV."""
        csv_data = [
            ["id", "date", "lead_type", "outcome", "timestamp", "speaker", "message"],
            ["test_001", "2025-12-15T14:23:00Z", "buyer", "closed", "2025-12-15T14:23:00Z", "bot", "Hey!"],
            ["test_002", "2025-12-15T14:24:00Z", "seller", "closed", "2025-12-15T14:24:00Z", "bot", "Hello!"],
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
            filepath = f.name

        try:
            count = analyzer.import_csv(filepath)
            assert count == 2
        finally:
            Path(filepath).unlink()

    def test_import_csv_missing_file(self, analyzer):
        """Test handling of missing CSV file."""
        with pytest.raises(FileNotFoundError):
            analyzer.import_csv("/nonexistent/file.csv")


# ==============================================================================
# METRICS CALCULATION TESTS
# ==============================================================================


class TestMetricsCalculation:
    """Test metrics calculation."""

    def test_calculate_single_metrics(self, analyzer, sample_transcript):
        """Test calculating metrics for single transcript."""
        analyzer.transcripts = [sample_transcript]
        metrics = analyzer.calculate_metrics()

        assert len(metrics) == 1
        metric = metrics[0]

        assert metric.transcript_id == "test_001"
        assert metric.lead_type == "buyer"
        assert metric.outcome == "closed"
        assert metric.questions_answered == 5
        assert metric.message_count == 5
        assert metric.questions_asked >= 1  # At least one question asked

    def test_calculate_duration(self, analyzer, sample_transcript):
        """Test conversation duration calculation."""
        analyzer.transcripts = [sample_transcript]
        metrics = analyzer.calculate_metrics()

        # Duration should be calculated from first to last message
        assert metrics[0].duration_minutes > 0
        assert metrics[0].duration_minutes < 10  # Sample is ~2 minutes

    def test_calculate_response_time(self, analyzer, sample_transcript):
        """Test average response time calculation."""
        analyzer.transcripts = [sample_transcript]
        metrics = analyzer.calculate_metrics()

        # Should have calculated average response time
        assert metrics[0].avg_response_time_seconds >= 0

    def test_pathway_detection_wholesale(self, analyzer, sample_wholesale_transcript):
        """Test wholesale pathway detection."""
        analyzer.transcripts = [sample_wholesale_transcript]
        metrics = analyzer.calculate_metrics()

        # Should detect wholesale pathway
        assert metrics[0].pathway_identified == "wholesale"

    def test_pathway_detection_listing(self, analyzer):
        """Test listing pathway detection."""
        listing_transcript = {
            "id": "test_listing",
            "lead_type": "seller",
            "outcome": "closed",
            "messages": [
                {
                    "timestamp": "2025-12-15T14:23:00Z",
                    "speaker": "user",
                    "message": "Want to list my move-in ready home for top dollar",
                    "metadata": {},
                }
            ],
        }

        analyzer.transcripts = [listing_transcript]
        metrics = analyzer.calculate_metrics()

        assert metrics[0].pathway_identified == "listing"


# ==============================================================================
# PATTERN ANALYSIS TESTS
# ==============================================================================


class TestPatternAnalysis:
    """Test pattern extraction and analysis."""

    def test_analyze_patterns_basic(self, analyzer, sample_transcript):
        """Test basic pattern analysis."""
        analyzer.transcripts = [sample_transcript]
        analyzer.calculate_metrics()

        patterns = analyzer.analyze_patterns()

        assert isinstance(patterns, PatternInsights)
        assert patterns.avg_questions_to_close >= 0
        assert patterns.avg_conversation_duration >= 0

    def test_winning_questions_extraction(self, analyzer, sample_transcript):
        """Test extraction of winning questions."""
        analyzer.transcripts = [sample_transcript]
        analyzer.calculate_metrics()

        patterns = analyzer.analyze_patterns()

        # Should extract question types from successful conversations
        assert isinstance(patterns.winning_questions, list)

    def test_closing_phrases_extraction(self, analyzer, sample_transcript):
        """Test extraction of closing phrases."""
        analyzer.transcripts = [sample_transcript]
        analyzer.calculate_metrics()

        patterns = analyzer.analyze_patterns()

        # Should extract phrases used at closing stage
        assert isinstance(patterns.successful_closing_phrases, list)

    def test_optimal_question_order(self, analyzer):
        """Test determination of optimal question order."""
        # Create transcript with defined question sequence
        transcript = {
            "id": "test_order",
            "lead_type": "buyer",
            "outcome": "closed",
            "questions_answered": 3,
            "messages": [
                {
                    "timestamp": "2025-12-15T14:23:00Z",
                    "speaker": "bot",
                    "message": "What's your budget?",
                    "metadata": {"question_type": "budget"},
                },
                {"timestamp": "2025-12-15T14:24:00Z", "speaker": "user", "message": "$400k", "metadata": {}},
                {
                    "timestamp": "2025-12-15T14:25:00Z",
                    "speaker": "bot",
                    "message": "What area?",
                    "metadata": {"question_type": "location"},
                },
                {"timestamp": "2025-12-15T14:26:00Z", "speaker": "user", "message": "Rancho Cucamonga", "metadata": {}},
            ],
        }

        analyzer.transcripts = [transcript]
        analyzer.calculate_metrics()

        patterns = analyzer.analyze_patterns()

        # Should identify question order
        assert "budget" in patterns.optimal_question_order or "location" in patterns.optimal_question_order

    def test_keyword_patterns(self, analyzer, sample_transcript):
        """Test keyword pattern extraction."""
        analyzer.transcripts = [sample_transcript]
        analyzer.calculate_metrics()

        patterns = analyzer.analyze_patterns()

        # Should extract keyword frequencies
        assert isinstance(patterns.keyword_patterns, dict)

    def test_close_rate_calculation(self, analyzer, sample_transcript):
        """Test close rate calculation by lead type."""
        # Add both closed and lost transcripts
        lost_transcript = {**sample_transcript, "id": "test_002", "outcome": "lost"}

        analyzer.transcripts = [sample_transcript, lost_transcript]
        analyzer.calculate_metrics()

        patterns = analyzer.analyze_patterns()

        # Should calculate close rates
        assert "buyer" in patterns.close_rate_by_lead_type
        assert 0 <= patterns.close_rate_by_lead_type["buyer"] <= 100

    def test_pathway_signals_extraction(self, analyzer, sample_wholesale_transcript):
        """Test extraction of pathway signals."""
        analyzer.transcripts = [sample_wholesale_transcript]
        analyzer.calculate_metrics()

        patterns = analyzer.analyze_patterns()

        # Should identify wholesale and listing signals
        assert "wholesale" in patterns.successful_pathway_signals
        assert "listing" in patterns.successful_pathway_signals


# ==============================================================================
# INSIGHTS GENERATION TESTS
# ==============================================================================


class TestInsightsGeneration:
    """Test insights report generation."""

    def test_generate_report_structure(self, analyzer, sample_transcript):
        """Test insights report has correct structure."""
        analyzer.transcripts = [sample_transcript]
        report = analyzer.generate_insights_report()

        # Check required sections
        assert "generated_at" in report
        assert "summary" in report
        assert "patterns" in report
        assert "metrics" in report
        assert "recommendations" in report

    def test_report_summary_metrics(self, analyzer, sample_transcript):
        """Test summary metrics in report."""
        analyzer.transcripts = [sample_transcript]
        report = analyzer.generate_insights_report()

        summary = report["summary"]
        assert summary["total_transcripts"] == 1
        assert summary["successful_closes"] == 1
        assert "avg_questions_to_close" in summary
        assert "avg_conversation_duration_minutes" in summary

    def test_recommendations_generation(self, analyzer, sample_transcript):
        """Test that recommendations are generated."""
        analyzer.transcripts = [sample_transcript]
        report = analyzer.generate_insights_report()

        recommendations = report["recommendations"]
        assert isinstance(recommendations, list)

        # Each recommendation should have required fields
        if recommendations:
            rec = recommendations[0]
            assert "category" in rec
            assert "recommendation" in rec
            assert "impact" in rec
            assert "implementation" in rec

    def test_save_report_to_file(self, analyzer, sample_transcript):
        """Test saving report to JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.json"

            analyzer.transcripts = [sample_transcript]
            report = analyzer.generate_insights_report(output_path=str(output_path))

            # File should exist
            assert output_path.exists()

            # Should be valid JSON
            with open(output_path, "r") as f:
                loaded_report = json.load(f)

            assert loaded_report["summary"]["total_transcripts"] == report["summary"]["total_transcripts"]


# ==============================================================================
# EXPORT TESTS
# ==============================================================================


class TestExport:
    """Test export functionality."""

    def test_export_metrics_csv(self, analyzer, sample_transcript):
        """Test exporting metrics to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metrics.csv"

            analyzer.transcripts = [sample_transcript]
            analyzer.calculate_metrics()
            analyzer.export_metrics_csv(str(output_path))

            # File should exist
            assert output_path.exists()

            # Should be valid CSV with correct data
            with open(output_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 1
            assert rows[0]["transcript_id"] == "test_001"

    def test_export_empty_metrics(self, analyzer):
        """Test exporting when no metrics calculated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metrics.csv"

            analyzer.export_metrics_csv(str(output_path))

            # File should be created but empty (header only or warning)
            assert output_path.exists()


# ==============================================================================
# EDGE CASES & ERROR HANDLING
# ==============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_transcript_list(self, analyzer):
        """Test handling of empty transcript list."""
        patterns = analyzer.analyze_patterns()

        # Should return empty insights without crashing
        assert patterns.avg_questions_to_close == 0.0
        assert len(patterns.winning_questions) == 0

    def test_transcript_with_no_messages(self, analyzer):
        """Test handling of transcript with empty messages."""
        invalid = {"id": "test_001", "lead_type": "buyer", "outcome": "closed", "messages": []}

        count = analyzer._validate_transcript(invalid)
        assert count is False

    def test_transcript_with_malformed_timestamps(self, analyzer):
        """Test handling of malformed timestamps."""
        transcript = {
            "id": "test_001",
            "lead_type": "buyer",
            "outcome": "closed",
            "messages": [{"timestamp": "invalid-timestamp", "speaker": "bot", "message": "Hello", "metadata": {}}],
        }

        analyzer.transcripts = [transcript]

        # Should handle gracefully (may skip or use defaults)
        try:
            analyzer.calculate_metrics()
        except Exception as e:
            # Expected to fail with timestamp parsing
            assert "invalid" in str(e).lower() or "format" in str(e).lower()

    def test_multiple_import_calls(self, analyzer, sample_transcript):
        """Test importing multiple times accumulates transcripts."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_transcript, f)
            filepath = f.name

        try:
            analyzer.import_json(filepath)
            analyzer.import_json(filepath)

            # Should accumulate
            assert len(analyzer.transcripts) == 2
        finally:
            Path(filepath).unlink()


# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================


class TestIntegration:
    """Integration tests using full sample data."""

    @pytest.mark.skip(reason="sample_transcripts.json has JSON formatting errors that need manual fixing")
    def test_full_workflow_with_sample_data(self):
        """Test complete workflow with sample_transcripts.json."""
        # This test requires actual sample_transcripts.json file
        analyzer = TranscriptAnalyzer(data_dir="data")

        try:
            # Import
            count = analyzer.import_json("data/sample_transcripts.json")
            assert count > 0

            # Calculate metrics
            metrics = analyzer.calculate_metrics()
            assert len(metrics) == count

            # Analyze patterns
            patterns = analyzer.analyze_patterns()
            assert patterns.avg_questions_to_close > 0

            # Generate report
            report = analyzer.generate_insights_report()
            assert report["summary"]["total_transcripts"] == count

        except FileNotFoundError:
            pytest.skip("sample_transcripts.json not found - expected in CI/CD environment")

    def test_cli_interface(self, sample_transcript):
        """Test CLI interface runs without errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "sample.json"

            with open(data_path, "w") as f:
                json.dump({"transcripts": [sample_transcript]}, f)

            # Import and run CLI simulation
            analyzer = TranscriptAnalyzer(data_dir=tmpdir)
            count = analyzer.import_json(str(data_path))
            metrics = analyzer.calculate_metrics()
            patterns = analyzer.analyze_patterns()
            report = analyzer.generate_insights_report()

            # Verify all steps completed
            assert count == 1
            assert len(metrics) == 1
            assert patterns.avg_questions_to_close > 0
            assert "recommendations" in report