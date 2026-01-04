"""
Integration tests for Phase 1 fixes.
Tests all 6 swarm agent fixes.
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.lead_scorer import LeadScorer
from core.conversation_manager import ConversationManager
from ghl_utils.config import settings


class TestSMSConstraintEnforcement:
    """Test SMS 160-character constraint enforcement."""

    def test_max_tokens_reduced_to_150(self):
        """Verify max_tokens is 150 (not 500)."""
        assert settings.max_tokens == 150, f"Expected max_tokens=150, got {settings.max_tokens}"

    def test_sms_truncation_logic_exists(self):
        """Verify truncation logic is in conversation_manager.py."""
        # Read the file and check for truncation logic
        manager_file = Path(__file__).parent.parent / "core" / "conversation_manager.py"
        content = manager_file.read_text()

        assert "if len(ai_response.content) > 160:" in content, "SMS truncation logic missing"
        assert 'ai_response.content[:157] + "..."' in content, "Truncation to 157 chars missing"


class TestCalendarFallback:
    """Test calendar fallback logic for Hot leads."""

    def test_fallback_message_exists(self):
        """Verify fallback message is in conversation_manager.py."""
        manager_file = Path(__file__).parent.parent / "core" / "conversation_manager.py"
        content = manager_file.read_text()

        assert "I'll have Jorge call you directly" in content, "Calendar fallback message missing"
        assert "elif lead_score >= 3:" in content, "Fallback condition missing"


class TestRedundancyPrevention:
    """Test redundancy prevention (pre-extraction on first message)."""

    def test_pre_extraction_logic_exists(self):
        """Verify pre-extraction logic is in conversation_manager.py."""
        manager_file = Path(__file__).parent.parent / "core" / "conversation_manager.py"
        content = manager_file.read_text()

        assert "Pre-extract data from first message to avoid redundancy" in content, "Pre-extraction comment missing"
        assert 'if not context.get("conversation_history"):' in content, "First message detection missing"


class TestRAGPathwayFiltering:
    """Test RAG pathway-aware search filtering."""

    def test_pathway_enhancement_logic_exists(self):
        """Verify pathway-aware query enhancement is in conversation_manager.py."""
        manager_file = Path(__file__).parent.parent / "core" / "conversation_manager.py"
        content = manager_file.read_text()

        assert "pathway-aware" in content, "Pathway-aware comment missing"
        assert "wholesale cash offer as-is quick sale" in content, "Wholesale keywords missing"
        assert "MLS listing top dollar market value" in content, "Listing keywords missing"


class TestToneEnhancement:
    """Test tone enhancement (direct questions)."""

    def test_direct_budget_question(self):
        """Verify budget question is direct."""
        prompts_file = Path(__file__).parent.parent / "prompts" / "system_prompts.py"
        content = prompts_file.read_text()

        assert "What's your budget?" in content, "Direct budget question missing"
        # Should NOT have the old version
        assert "What price range are you comfortable with?" not in content, "Old polite version still exists"

    def test_direct_timeline_question(self):
        """Verify timeline question is direct."""
        prompts_file = Path(__file__).parent.parent / "prompts" / "system_prompts.py"
        content = prompts_file.read_text()

        assert "When do you need to move?" in content, "Direct timeline question missing"


class TestDocumentationSimplification:
    """Test HOW_TO_RUN.md simplification."""

    def test_howtorun_has_3step_structure(self):
        """Verify HOW_TO_RUN.md has 3-step structure."""
        howto_file = Path(__file__).parent.parent / "HOW_TO_RUN.md"
        content = howto_file.read_text()

        assert "3-Step Setup" in content, "3-Step Setup header missing"
        assert "Step 1:" in content, "Step 1 missing"
        assert "Step 2:" in content, "Step 2 missing"
        assert "Step 3:" in content, "Step 3 missing"

    def test_howtorun_is_nontechnical(self):
        """Verify HOW_TO_RUN.md is non-technical."""
        howto_file = Path(__file__).parent.parent / "HOW_TO_RUN.md"
        content = howto_file.read_text()

        # Should have simple language
        assert "in your browser" in content or "dashboard" in content, "Non-technical language missing"
        # Should NOT have complex bash commands (streamlit is OK)
        assert "venv/bin/activate" not in content, "Technical venv command found"


class TestAdminDashboardFix:
    """Test admin.py integration bug fix."""

    def test_save_tenant_config_method_exists(self):
        """Verify save_tenant_config method exists in tenant_service.py."""
        tenant_file = Path(__file__).parent.parent / "services" / "tenant_service.py"
        content = tenant_file.read_text()

        assert "async def save_tenant_config" in content, "save_tenant_config method missing"
        assert "location_id: str" in content, "save_tenant_config parameters missing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
