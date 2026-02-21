import pytest

pytestmark = pytest.mark.integration

"""Tests for the bilingual language detection service and pipeline stage."""

from unittest.mock import MagicMock, patch

import pytest

from ghl_real_estate_ai.models.language_preferences import (
    ContactLanguagePreference,
    LanguageDetection,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ProcessedResponse,
    ProcessingAction,
    ProcessingContext,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.language_mirror import (
    LanguageMirrorProcessor,
)
from ghl_real_estate_ai.services.language_detection import (
    LanguageDetectionService,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_context(**kwargs) -> ProcessingContext:
    defaults = {
        "contact_id": "test_contact_1",
        "bot_mode": "lead",
        "channel": "sms",
        "user_message": "Hello",
        "detected_language": "en",
    }
    defaults.update(kwargs)
    return ProcessingContext(**defaults)


def _make_response(msg: str = "Bot reply") -> ProcessedResponse:
    return ProcessedResponse(message=msg, original_message=msg)


def _create_fresh_service() -> LanguageDetectionService:
    """Create a fresh service instance (not the singleton)."""
    return LanguageDetectionService()


# ---------------------------------------------------------------------------
# LanguageDetection dataclass
# ---------------------------------------------------------------------------


class TestLanguageDetectionDataclass:
    def test_defaults(self):
        d = LanguageDetection(language="en", confidence=0.95)
        assert d.language == "en"
        assert d.confidence == 0.95
        assert d.is_code_switching is False
        assert d.secondary_language is None

    def test_code_switching_fields(self):
        d = LanguageDetection(
            language="es",
            confidence=0.7,
            is_code_switching=True,
            secondary_language="en",
        )
        assert d.is_code_switching is True
        assert d.secondary_language == "en"


# ---------------------------------------------------------------------------
# ContactLanguagePreference
# ---------------------------------------------------------------------------


class TestContactLanguagePreference:
    def test_update_single_detection(self):
        pref = ContactLanguagePreference(contact_id="c1")
        pref.update(LanguageDetection(language="es", confidence=0.9))
        assert pref.primary_language == "es"
        assert pref.total_messages == 1
        assert pref.language_counts == {"es": 1}

    def test_update_multiple_detections_majority_wins(self):
        pref = ContactLanguagePreference(contact_id="c2")
        pref.update(LanguageDetection(language="es", confidence=0.9))
        pref.update(LanguageDetection(language="en", confidence=0.9))
        pref.update(LanguageDetection(language="es", confidence=0.9))
        assert pref.primary_language == "es"
        assert pref.total_messages == 3
        assert pref.language_counts == {"es": 2, "en": 1}

    def test_update_switches_primary_when_overtaken(self):
        pref = ContactLanguagePreference(contact_id="c3")
        pref.update(LanguageDetection(language="es", confidence=0.9))
        assert pref.primary_language == "es"
        pref.update(LanguageDetection(language="en", confidence=0.9))
        pref.update(LanguageDetection(language="en", confidence=0.9))
        assert pref.primary_language == "en"


# ---------------------------------------------------------------------------
# LanguageDetectionService — with model mock
# ---------------------------------------------------------------------------


class TestLanguageDetectionServiceWithModel:
    def test_english_detection(self):
        service = _create_fresh_service()
        mock_pipeline = MagicMock(return_value=[{"label": "en", "score": 0.98}])
        service._pipeline = mock_pipeline
        service._pipeline_loaded = True

        result = service.detect("Hello, I want to buy a house")
        assert result.language == "en"
        assert result.confidence == 0.98

    def test_spanish_detection(self):
        service = _create_fresh_service()
        mock_pipeline = MagicMock(return_value=[{"label": "es", "score": 0.95}])
        service._pipeline = mock_pipeline
        service._pipeline_loaded = True

        result = service.detect("Quiero comprar una casa")
        assert result.language == "es"
        assert result.confidence == 0.95

    def test_hybrid_spanish_correction_from_italian(self):
        """Test that hybrid approach corrects Italian misclassification to Spanish."""
        service = _create_fresh_service()
        # Model predicts Italian with medium confidence
        mock_pipeline = MagicMock(return_value=[{"label": "it", "score": 0.79}])
        service._pipeline = mock_pipeline
        service._pipeline_loaded = True

        result = service.detect("Quiero comprar una casa en Rancho Cucamonga")
        # Should be corrected to Spanish by heuristic validation
        assert result.language == "es"
        assert result.confidence >= 0.79

    def test_hybrid_spanish_correction_from_portuguese(self):
        """Test that hybrid approach corrects Portuguese misclassification to Spanish."""
        service = _create_fresh_service()
        # Model predicts Portuguese with medium confidence
        mock_pipeline = MagicMock(return_value=[{"label": "pt", "score": 0.85}])
        service._pipeline = mock_pipeline
        service._pipeline_loaded = True

        result = service.detect("Necesito ayuda con mi hipoteca")
        # Should be corrected to Spanish by heuristic validation
        assert result.language == "es"

    def test_hybrid_no_correction_for_high_confidence(self):
        """Test that hybrid approach doesn't override high-confidence predictions."""
        service = _create_fresh_service()
        # Model predicts Italian with HIGH confidence (>0.9)
        mock_pipeline = MagicMock(return_value=[{"label": "it", "score": 0.95}])
        service._pipeline = mock_pipeline
        service._pipeline_loaded = True

        result = service.detect("Voglio comprare una casa")  # Actual Italian
        # Should keep Italian since confidence is high
        assert result.language == "it"
        assert result.confidence == 0.95

    def test_code_switching_detection(self):
        service = _create_fresh_service()
        # Call sequence:
        # 1) full text                -> "es"
        # 2) sentence "Hello how are you"   -> "en"
        # 3) sentence "Quiero comprar una casa" -> "es"
        # 4) primary re-check on full text -> "es"
        mock_pipeline = MagicMock(
            side_effect=[
                [{"label": "es", "score": 0.8}],
                [{"label": "en", "score": 0.9}],
                [{"label": "es", "score": 0.9}],
                [{"label": "es", "score": 0.8}],
            ]
        )
        service._pipeline = mock_pipeline
        service._pipeline_loaded = True

        result = service.detect("Hello how are you. Quiero comprar una casa.")
        assert result.is_code_switching is True
        assert result.secondary_language == "en"

    def test_contact_preference_tracking(self):
        service = _create_fresh_service()
        mock_pipeline = MagicMock(return_value=[{"label": "es", "score": 0.9}])
        service._pipeline = mock_pipeline
        service._pipeline_loaded = True

        service.detect("Hola", contact_id="c1")
        service.detect("Buenos dias", contact_id="c1")

        pref = service.get_contact_preference("c1")
        assert pref is not None
        assert pref.primary_language == "es"
        assert pref.total_messages == 2


# ---------------------------------------------------------------------------
# LanguageDetectionService — heuristic fallback
# ---------------------------------------------------------------------------


class TestLanguageDetectionServiceHeuristic:
    def test_fallback_detects_spanish(self):
        service = _create_fresh_service()
        service._load_failed = True  # Force heuristic mode

        result = service.detect("Quiero comprar una casa en Rancho Cucamonga")
        assert result.language == "es"
        assert result.confidence > 0.5

    def test_fallback_detects_english(self):
        service = _create_fresh_service()
        service._load_failed = True

        result = service.detect("I want to buy a house in Rancho Cucamonga")
        assert result.language == "en"

    def test_fallback_empty_text(self):
        service = _create_fresh_service()
        service._load_failed = True

        result = service.detect("")
        assert result.language == "en"
        assert result.confidence == 1.0

    def test_fallback_whitespace_only(self):
        service = _create_fresh_service()
        service._load_failed = True

        result = service.detect("   ")
        assert result.language == "en"
        assert result.confidence == 1.0


# ---------------------------------------------------------------------------
# LanguageMirrorProcessor stage
# ---------------------------------------------------------------------------


class TestLanguageMirrorProcessor:
    @pytest.mark.asyncio
    async def test_sets_detected_language(self):
        stage = LanguageMirrorProcessor()
        ctx = _make_context(user_message="Quiero comprar una casa")
        resp = _make_response()

        with patch(
            "ghl_real_estate_ai.services.jorge.response_pipeline.stages.language_mirror.get_language_detection_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.detect.return_value = LanguageDetection(language="es", confidence=0.95)
            mock_get_service.return_value = mock_service

            result = await stage.process(resp, ctx)

        assert ctx.detected_language == "es"
        assert "language_detection" in ctx.metadata
        assert ctx.metadata["language_detection"]["language"] == "es"

    @pytest.mark.asyncio
    async def test_does_not_modify_message(self):
        stage = LanguageMirrorProcessor()
        ctx = _make_context(user_message="Hello there")
        resp = _make_response("Original bot reply")

        with patch(
            "ghl_real_estate_ai.services.jorge.response_pipeline.stages.language_mirror.get_language_detection_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.detect.return_value = LanguageDetection(language="en", confidence=0.98)
            mock_get_service.return_value = mock_service

            result = await stage.process(resp, ctx)

        assert result.message == "Original bot reply"
        assert result.action == ProcessingAction.PASS

    @pytest.mark.asyncio
    async def test_name_property(self):
        stage = LanguageMirrorProcessor()
        assert stage.name == "language_mirror"

    @pytest.mark.asyncio
    async def test_sets_metadata_dict(self):
        stage = LanguageMirrorProcessor()
        ctx = _make_context(user_message="Hola amigos")
        resp = _make_response()

        with patch(
            "ghl_real_estate_ai.services.jorge.response_pipeline.stages.language_mirror.get_language_detection_service"
        ) as mock_get_service:
            mock_service = MagicMock()
            mock_service.detect.return_value = LanguageDetection(
                language="es",
                confidence=0.92,
                is_code_switching=False,
                secondary_language=None,
            )
            mock_get_service.return_value = mock_service

            await stage.process(resp, ctx)

        meta = ctx.metadata["language_detection"]
        assert meta["language"] == "es"
        assert meta["confidence"] == 0.92
        assert meta["is_code_switching"] is False
        assert meta["secondary_language"] is None
