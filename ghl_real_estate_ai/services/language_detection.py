"""Bilingual language detection service with XLM-RoBERTa and heuristic fallback.

Uses the ``papluca/xlm-roberta-base-language-detection`` model from HuggingFace
when available.  The model is **lazy-loaded** on first call so import time is
unaffected.  When the ``transformers`` package is not installed or the model
cannot be loaded, the service falls back to a lightweight heuristic that checks
for common Spanish indicator words.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.models.language_preferences import (
    ContactLanguagePreference,
    LanguageDetection,
)

logger = logging.getLogger(__name__)

# ---- Heuristic fallback data ------------------------------------------------

_SPANISH_INDICATORS = frozenset(
    {
        "hola",
        "casa",
        "quiero",
        "comprar",
        "vender",
        "precio",
        "gracias",
        "bueno",
        "buenos",
        "buena",
        "bien",
        "como",
        "esta",
        "está",
        "para",
        "muy",
        "donde",
        "cuando",
        "porque",
        "tengo",
        "necesito",
        "propiedad",
        "parar",
        "cancelar",
        "más",
        "dinero",
        "cuanto",
        "cuánto",
        "cuándo",
        "dónde",
        "por",
        "favor",
        "ayuda",
        "barrio",
        "vecindario",
        "habitaciones",
        "baños",
        "cocina",
        "garaje",
        "jardín",
        "estoy",
        "interesado",
        "interesada",
        "venta",
        "alquiler",
        "hipoteca",
        "pago",
        "mensual",
        "enganche",
    }
)

_ENGLISH_INDICATORS = frozenset(
    {
        "interested",
        "properties",
        "property",
        "house",
        "home",
        "buy",
        "sell",
        "price",
        "financing",
        "mortgage",
        "bedroom",
        "bathroom",
        "kitchen",
        "garage",
        "yard",
        "neighborhood",
        "help",
        "looking",
        "ranch",
        "cucamonga",
        "sale",
        "rent",
        "payment",
        "monthly",
        "down",
        "deposit",
    }
)

_SENTENCE_RE = re.compile(r"[.!?]+\s+|\n+")


# ---- Service -----------------------------------------------------------------


class LanguageDetectionService:
    """Detects language using XLM-RoBERTa (lazy-loaded) with heuristic fallback."""

    def __init__(self) -> None:
        self._pipeline: Any = None
        self._pipeline_loaded: bool = False
        self._load_failed: bool = False
        self._contact_prefs: Dict[str, ContactLanguagePreference] = {}

    # -- lazy loading ----------------------------------------------------------

    def _ensure_pipeline(self) -> None:
        """Lazy-load the HuggingFace text-classification pipeline."""
        if self._pipeline_loaded or self._load_failed:
            return
        try:
            from transformers import pipeline as hf_pipeline  # type: ignore[import-untyped]

            self._pipeline = hf_pipeline(
                "text-classification",
                model="papluca/xlm-roberta-base-language-detection",
            )
            self._pipeline_loaded = True
            logger.info("XLM-RoBERTa language detection model loaded")
        except Exception:
            self._load_failed = True
            logger.warning(
                "Failed to load XLM-RoBERTa model; using heuristic fallback"
            )

    # -- public API ------------------------------------------------------------

    def detect(
        self, text: str, contact_id: Optional[str] = None
    ) -> LanguageDetection:
        """Detect the language of *text*.

        Args:
            text: Input text to classify.
            contact_id: Optional contact ID for preference tracking.

        Returns:
            LanguageDetection with language code, confidence, and
            code-switching info.
        """
        if not text or not text.strip():
            return LanguageDetection(language="en", confidence=1.0)

        self._ensure_pipeline()

        if self._pipeline is not None:
            detection = self._detect_with_model(text)
        else:
            detection = self._detect_heuristic(text)

        # Track per-contact preference when a contact_id is given
        if contact_id:
            if contact_id not in self._contact_prefs:
                self._contact_prefs[contact_id] = ContactLanguagePreference(
                    contact_id=contact_id
                )
            self._contact_prefs[contact_id].update(detection)

        return detection

    def get_contact_preference(
        self, contact_id: str
    ) -> Optional[ContactLanguagePreference]:
        """Retrieve accumulated language preference for a contact."""
        return self._contact_prefs.get(contact_id)

    # -- model-based detection -------------------------------------------------

    def _detect_with_model(self, text: str) -> LanguageDetection:
        """Detect language using XLM-RoBERTa model with heuristic validation.

        The model sometimes misclassifies Spanish/English as Italian/Portuguese.
        We use heuristic validation to correct these cases for en/es classification.
        """
        try:
            result = self._pipeline(text[:512])  # respect model token limit
            top = result[0]
            language: str = top["label"]
            confidence: float = top["score"]

            # Hybrid approach: validate model prediction with heuristic
            # for Romance language confusion (it/pt/es) and ensure en/es accuracy
            # Only validate if confidence is not very high (< 0.9) or model prediction is suspicious
            should_validate = (
                # Low confidence predictions should be validated
                (confidence < 0.9) or
                # Medium confidence Italian/Portuguese should be validated (might be Spanish)
                (language in ("it", "pt") and confidence < 0.95)
            )

            if should_validate:
                # Get heuristic opinion for validation
                heuristic_result = self._detect_heuristic(text)

                # Case 1: Model predicts Italian/Portuguese but might be Spanish
                if language in ("it", "pt") and heuristic_result.language == "es":
                    if heuristic_result.confidence > 0.7 and confidence < 0.9:
                        logger.debug(
                            "Model predicted %s (%.2f) but heuristic suggests Spanish (%.2f); using es",
                            language, confidence, heuristic_result.confidence
                        )
                        language = "es"
                        confidence = max(confidence, heuristic_result.confidence)

                # Case 2: Model has low confidence but heuristic has high confidence
                elif language != heuristic_result.language and heuristic_result.confidence > 0.8 and confidence < 0.85:
                    logger.debug(
                        "Model predicted %s (%.2f) but heuristic strongly suggests %s (%.2f); using heuristic",
                        language, confidence, heuristic_result.language, heuristic_result.confidence
                    )
                    language = heuristic_result.language
                    confidence = heuristic_result.confidence

            secondary = self._check_code_switching_model(text)

            return LanguageDetection(
                language=language,
                confidence=confidence,
                is_code_switching=secondary is not None,
                secondary_language=secondary,
            )
        except Exception:
            logger.warning("Model inference failed; falling back to heuristic")
            return self._detect_heuristic(text)

    def _check_code_switching_model(self, text: str) -> Optional[str]:
        """Detect code-switching by classifying individual sentences."""
        sentences = [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]
        if len(sentences) < 2:
            return None

        languages: set[str] = set()
        for sentence in sentences:
            try:
                result = self._pipeline(sentence[:512])
                languages.add(result[0]["label"])
            except Exception:
                continue

        if len(languages) >= 2:
            # Determine primary language from full text
            primary_result = self._pipeline(text[:512])
            primary: str = primary_result[0]["label"]
            for lang in languages:
                if lang != primary:
                    return lang

        return None

    # -- heuristic fallback ----------------------------------------------------

    def _detect_heuristic(self, text: str) -> LanguageDetection:
        """Fallback heuristic: check for common Spanish/English indicator words."""
        words = set(re.findall(r"\b\w+\b", text.lower()))
        spanish_matches = words & _SPANISH_INDICATORS
        english_matches = words & _ENGLISH_INDICATORS
        total_words = len(words) if words else 1

        spanish_ratio = len(spanish_matches) / total_words if spanish_matches else 0
        english_ratio = len(english_matches) / total_words if english_matches else 0

        # Strong Spanish signal
        if spanish_ratio >= 0.15:
            non_spanish = words - _SPANISH_INDICATORS
            # Code-switching: meaningful mix of Spanish and non-Spanish words
            is_switching = 0.2 <= spanish_ratio <= 0.8 and len(non_spanish) > 1

            return LanguageDetection(
                language="es",
                confidence=min(0.5 + spanish_ratio, 0.95),
                is_code_switching=is_switching,
                secondary_language="en" if is_switching else None,
            )

        # Strong English signal
        if english_ratio >= 0.15:
            return LanguageDetection(
                language="en",
                confidence=min(0.5 + english_ratio, 0.95),
            )

        # Default to English with lower confidence
        return LanguageDetection(language="en", confidence=0.8)


# ---- Singleton ---------------------------------------------------------------

_service: Optional[LanguageDetectionService] = None


def get_language_detection_service() -> LanguageDetectionService:
    """Singleton accessor for the language detection service."""
    global _service
    if _service is None:
        _service = LanguageDetectionService()
    return _service
