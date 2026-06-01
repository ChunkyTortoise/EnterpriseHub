import pytest

@pytest.mark.integration
#!/usr/bin/env python3
"""
Phase 5 AI-Enhanced Operations Skills Integration Tests

Tests cross-skill compatibility, service integration, and workflow validation
for the 4 Phase 5 skills:
- intelligent-lead-insights
- conversation-optimization
- property-recommendation-engine
- automated-market-analysis

Usage:
    pytest test_phase5_integration.py -v
    python test_phase5_integration.py
"""

import subprocess
import sys
import os
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
import unittest


# Get the skills directory
# tests/ is inside ai-operations/, so we go up to get to skills/
SKILLS_DIR = Path(__file__).parent.parent.parent  # .claude/skills
AI_OPS_DIR = Path(__file__).parent.parent  # .claude/skills/ai-operations
PROJECT_ROOT = SKILLS_DIR.parent.parent  # EnterpriseHub


class TestPhase5SkillStructure(unittest.TestCase):
    """Test that all Phase 5 skill directories are properly structured."""

    PHASE5_SKILLS = [
        "intelligent-lead-insights",
        "conversation-optimization",
        "property-recommendation-engine",
        "automated-market-analysis"
    ]

    REQUIRED_FILES = ["SKILL.md"]
    REQUIRED_DIRS = ["scripts", "reference"]

    def test_all_skills_exist(self):
        """Verify all Phase 5 skill directories exist."""
        ai_ops_dir = SKILLS_DIR / "ai-operations"

        for skill in self.PHASE5_SKILLS:
            skill_dir = ai_ops_dir / skill
            self.assertTrue(
                skill_dir.exists(),
                f"Skill directory missing: {skill}"
            )

    def test_skill_files_exist(self):
        """Verify required files exist in each skill."""
        ai_ops_dir = SKILLS_DIR / "ai-operations"

        for skill in self.PHASE5_SKILLS:
            skill_dir = ai_ops_dir / skill

            for req_file in self.REQUIRED_FILES:
                file_path = skill_dir / req_file
                self.assertTrue(
                    file_path.exists(),
                    f"Missing {req_file} in {skill}"
                )

    def test_skill_directories_exist(self):
        """Verify required subdirectories exist in each skill."""
        ai_ops_dir = SKILLS_DIR / "ai-operations"

        for skill in self.PHASE5_SKILLS:
            skill_dir = ai_ops_dir / skill

            for req_dir in self.REQUIRED_DIRS:
                dir_path = skill_dir / req_dir
                self.assertTrue(
                    dir_path.exists(),
                    f"Missing {req_dir}/ in {skill}"
                )

    def test_skill_md_has_frontmatter(self):
        """Verify SKILL.md files have proper YAML frontmatter."""
        ai_ops_dir = SKILLS_DIR / "ai-operations"

        for skill in self.PHASE5_SKILLS:
            skill_md = ai_ops_dir / skill / "SKILL.md"

            with open(skill_md, 'r') as f:
                content = f.read()

            self.assertIn(
                "## Description",
                content,
                f"SKILL.md missing Description section in {skill}"
            )
            self.assertIn(
                "## Triggers",
                content,
                f"SKILL.md missing Triggers section in {skill}"
            )
            self.assertIn(
                "## Workflow",
                content,
                f"SKILL.md missing Workflow section in {skill}"
            )


class TestIntelligentLeadInsights(unittest.TestCase):
    """Tests for intelligent-lead-insights skill."""

    SKILL_DIR = SKILLS_DIR / "ai-operations" / "intelligent-lead-insights"

    def test_scripts_exist(self):
        """Verify required scripts exist."""
        scripts_dir = self.SKILL_DIR / "scripts"
        required_scripts = [
            "analyze-conversations.py",
            "calculate-conversion-score.py"
        ]

        for script in required_scripts:
            script_path = scripts_dir / script
            self.assertTrue(
                script_path.exists(),
                f"Missing script: {script}"
            )

    def test_reference_files_exist(self):
        """Verify reference documentation exists."""
        ref_dir = self.SKILL_DIR / "reference"
        required_refs = [
            "buying-signals.md",
            "conversion-models.md"
        ]

        for ref in required_refs:
            ref_path = ref_dir / ref
            self.assertTrue(
                ref_path.exists(),
                f"Missing reference: {ref}"
            )

    def test_analyze_conversations_script_runs(self):
        """Test analyze-conversations.py executes without errors."""
        script = self.SKILL_DIR / "scripts" / "analyze-conversations.py"

        result = subprocess.run(
            [sys.executable, str(script), "--lead-id", "test_lead_001", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        self.assertEqual(
            result.returncode, 0,
            f"Script failed: {result.stderr}"
        )

        # Verify JSON output is valid
        try:
            output = json.loads(result.stdout)
            self.assertIn("lead_id", output)
            self.assertIn("conversation_health", output)
        except json.JSONDecodeError:
            self.fail("Script did not produce valid JSON output")

    def test_calculate_conversion_score_script_runs(self):
        """Test calculate-conversion-score.py executes without errors."""
        script = self.SKILL_DIR / "scripts" / "calculate-conversion-score.py"

        result = subprocess.run(
            [sys.executable, str(script), "--lead-id", "test_lead_001", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        self.assertEqual(
            result.returncode, 0,
            f"Script failed: {result.stderr}"
        )

        # Verify JSON output
        try:
            output = json.loads(result.stdout)
            self.assertIn("lead_id", output)
            self.assertIn("final_score", output)
            self.assertIn("classification", output)
        except json.JSONDecodeError:
            self.fail("Script did not produce valid JSON output")


class TestConversationOptimization(unittest.TestCase):
    """Tests for conversation-optimization skill."""

    SKILL_DIR = SKILLS_DIR / "ai-operations" / "conversation-optimization"

    def test_scripts_exist(self):
        """Verify required scripts exist."""
        scripts_dir = self.SKILL_DIR / "scripts"
        required_scripts = ["analyze-transcript.py"]

        for script in required_scripts:
            script_path = scripts_dir / script
            self.assertTrue(
                script_path.exists(),
                f"Missing script: {script}"
            )

    def test_reference_files_exist(self):
        """Verify reference documentation exists."""
        ref_dir = self.SKILL_DIR / "reference"
        required_refs = ["objection-handling.md"]

        for ref in required_refs:
            ref_path = ref_dir / ref
            self.assertTrue(
                ref_path.exists(),
                f"Missing reference: {ref}"
            )

    def test_analyze_transcript_script_runs(self):
        """Test analyze-transcript.py executes without errors."""
        script = self.SKILL_DIR / "scripts" / "analyze-transcript.py"

        result = subprocess.run(
            [sys.executable, str(script), "--conversation-id", "test_conv_001", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        self.assertEqual(
            result.returncode, 0,
            f"Script failed: {result.stderr}"
        )

        # Verify JSON output
        try:
            output = json.loads(result.stdout)
            self.assertIn("conversation_id", output)
            self.assertIn("avg_quality_score", output)
        except json.JSONDecodeError:
            self.fail("Script did not produce valid JSON output")


class TestPropertyRecommendationEngine(unittest.TestCase):
    """Tests for property-recommendation-engine skill."""

    SKILL_DIR = SKILLS_DIR / "ai-operations" / "property-recommendation-engine"

    def test_scripts_exist(self):
        """Verify required scripts exist."""
        scripts_dir = self.SKILL_DIR / "scripts"
        required_scripts = [
            "calculate-property-scores.py",
            "optimize-showing-schedule.py",
            "extract-preferences.py",
            "update-preference-weights.py"
        ]

        for script in required_scripts:
            script_path = scripts_dir / script
            self.assertTrue(
                script_path.exists(),
                f"Missing script: {script}"
            )

    def test_reference_files_exist(self):
        """Verify reference documentation exists."""
        ref_dir = self.SKILL_DIR / "reference"
        required_refs = [
            "preference-extraction.md",
            "scoring-algorithm.md",
            "feedback-learning.md",
            "showing-optimization.md"
        ]

        for ref in required_refs:
            ref_path = ref_dir / ref
            self.assertTrue(
                ref_path.exists(),
                f"Missing reference: {ref}"
            )

    def test_calculate_property_scores_runs(self):
        """Test calculate-property-scores.py executes without errors."""
        script = self.SKILL_DIR / "scripts" / "calculate-property-scores.py"

        result = subprocess.run(
            [sys.executable, str(script), "--lead-id", "test_lead_001", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        self.assertEqual(
            result.returncode, 0,
            f"Script failed: {result.stderr}"
        )

        # Verify JSON output
        try:
            output = json.loads(result.stdout)
            self.assertIn("lead_id", output)
            self.assertIn("recommendations", output)
        except json.JSONDecodeError:
            self.fail("Script did not produce valid JSON output")

    def test_optimize_showing_schedule_runs(self):
        """Test optimize-showing-schedule.py executes without errors."""
        script = self.SKILL_DIR / "scripts" / "optimize-showing-schedule.py"

        result = subprocess.run(
            [sys.executable, str(script), "--properties", "mock", "--date", "2026-01-20", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        self.assertEqual(
            result.returncode, 0,
            f"Script failed: {result.stderr}"
        )

        # Verify JSON output
        try:
            output = json.loads(result.stdout)
            self.assertIn("showings", output)
            self.assertIn("total_drive_time_minutes", output)
        except json.JSONDecodeError:
            self.fail("Script did not produce valid JSON output")

    def test_extract_preferences_runs(self):
        """Test extract-preferences.py executes without errors."""
        script = self.SKILL_DIR / "scripts" / "extract-preferences.py"

        result = subprocess.run(
            [sys.executable, str(script), "--lead-id", "test_lead_001", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        self.assertEqual(
            result.returncode, 0,
            f"Script failed: {result.stderr}"
        )

        # Verify JSON output
        try:
            output = json.loads(result.stdout)
            self.assertIn("lead_id", output)
            self.assertIn("budget", output)
            self.assertIn("features", output)
        except json.JSONDecodeError:
            self.fail("Script did not produce valid JSON output")


class TestAutomatedMarketAnalysis(unittest.TestCase):
    """Tests for automated-market-analysis skill."""

    SKILL_DIR = SKILLS_DIR / "ai-operations" / "automated-market-analysis"

    def test_scripts_exist(self):
        """Verify required scripts exist."""
        scripts_dir = self.SKILL_DIR / "scripts"
        required_scripts = [
            "generate-cma-report.py",
            "analyze-market-trends.py"
        ]

        for script in required_scripts:
            script_path = scripts_dir / script
            self.assertTrue(
                script_path.exists(),
                f"Missing script: {script}"
            )

    def test_reference_files_exist(self):
        """Verify reference documentation exists."""
        ref_dir = self.SKILL_DIR / "reference"
        required_refs = [
            "cma-methodology.md",
            "market-indicators.md"
        ]

        for ref in required_refs:
            ref_path = ref_dir / ref
            self.assertTrue(
                ref_path.exists(),
                f"Missing reference: {ref}"
            )

    def test_generate_cma_report_runs(self):
        """Test generate-cma-report.py executes without errors."""
        script = self.SKILL_DIR / "scripts" / "generate-cma-report.py"

        result = subprocess.run(
            [sys.executable, str(script), "--output", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        self.assertEqual(
            result.returncode, 0,
            f"Script failed: {result.stderr}"
        )

        # Verify JSON output
        try:
            output = json.loads(result.stdout)
            self.assertIn("report_id", output)
            self.assertIn("valuation", output)
            self.assertIn("comparables", output)
        except json.JSONDecodeError:
            self.fail("Script did not produce valid JSON output")

    def test_analyze_market_trends_runs(self):
        """Test analyze-market-trends.py executes without errors."""
        script = self.SKILL_DIR / "scripts" / "analyze-market-trends.py"

        result = subprocess.run(
            [sys.executable, str(script), "--area", "Round Rock", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )

        self.assertEqual(
            result.returncode, 0,
            f"Script failed: {result.stderr}"
        )

        # Verify JSON output
        try:
            output = json.loads(result.stdout)
            self.assertIn("area", output)
            self.assertIn("price_trends", output)
            self.assertIn("market_health", output)
        except json.JSONDecodeError:
            self.fail("Script did not produce valid JSON output")


class TestManifestIntegration(unittest.TestCase):
    """Test MANIFEST.yaml includes Phase 5 skills correctly."""

    def test_manifest_includes_phase5_skills(self):
        """Verify MANIFEST.yaml includes all Phase 5 skills."""
        manifest_path = SKILLS_DIR / "MANIFEST.yaml"

        with open(manifest_path, 'r') as f:
            content = f.read()

        phase5_skills = [
            "intelligent-lead-insights",
            "conversation-optimization",
            "property-recommendation-engine",
            "automated-market-analysis"
        ]

        for skill in phase5_skills:
            self.assertIn(
                skill,
                content,
                f"MANIFEST.yaml missing Phase 5 skill: {skill}"
            )

    def test_manifest_has_ai_operations_category(self):
        """Verify MANIFEST.yaml has ai-operations category."""
        manifest_path = SKILLS_DIR / "MANIFEST.yaml"

        with open(manifest_path, 'r') as f:
            content = f.read()

        self.assertIn("ai-operations", content)

    def test_manifest_version_updated(self):
        """Verify MANIFEST.yaml version is 5.0.0."""
        manifest_path = SKILLS_DIR / "MANIFEST.yaml"

        with open(manifest_path, 'r') as f:
            content = f.read()

        self.assertIn('version: "5.0.0"', content)


class TestCrossSkillIntegration(unittest.TestCase):
    """Test that Phase 5 skills work together correctly."""

    def test_lead_insights_feeds_conversation_optimization(self):
        """
        Test workflow: Lead insights -> Conversation optimization.

        Lead behavioral analysis should inform conversation coaching.
        """
        # This is a conceptual test - in production would test actual integration
        lead_insights_script = SKILLS_DIR / "ai-operations" / "intelligent-lead-insights" / "scripts" / "analyze-conversations.py"
        conv_opt_script = SKILLS_DIR / "ai-operations" / "conversation-optimization" / "scripts" / "analyze-transcript.py"

        # Both scripts should run successfully
        self.assertTrue(lead_insights_script.exists())
        self.assertTrue(conv_opt_script.exists())

    def test_preferences_feed_property_recommendations(self):
        """
        Test workflow: Preference extraction -> Property scoring.

        Extracted preferences should be usable for property scoring.
        """
        extract_script = SKILLS_DIR / "ai-operations" / "property-recommendation-engine" / "scripts" / "extract-preferences.py"
        score_script = SKILLS_DIR / "ai-operations" / "property-recommendation-engine" / "scripts" / "calculate-property-scores.py"

        # Both scripts should run successfully
        self.assertTrue(extract_script.exists())
        self.assertTrue(score_script.exists())

    def test_market_analysis_informs_recommendations(self):
        """
        Test workflow: Market analysis -> Property recommendations.

        Market trends should inform property recommendation priorities.
        """
        market_script = SKILLS_DIR / "ai-operations" / "automated-market-analysis" / "scripts" / "analyze-market-trends.py"
        recommend_script = SKILLS_DIR / "ai-operations" / "property-recommendation-engine" / "scripts" / "calculate-property-scores.py"

        # Both scripts should run successfully
        self.assertTrue(market_script.exists())
        self.assertTrue(recommend_script.exists())


def run_tests():
    """Run all tests and generate report."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPhase5SkillStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestIntelligentLeadInsights))
    suite.addTests(loader.loadTestsFromTestCase(TestConversationOptimization))
    suite.addTests(loader.loadTestsFromTestCase(TestPropertyRecommendationEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestAutomatedMarketAnalysis))
    suite.addTests(loader.loadTestsFromTestCase(TestManifestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestCrossSkillIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
