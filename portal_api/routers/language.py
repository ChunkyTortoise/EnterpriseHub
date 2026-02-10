from __future__ import annotations

import re

from fastapi import APIRouter

from portal_api.models import LanguageDetectRequest, LanguageDetectResponse

router = APIRouter(prefix="/language", tags=["language"])

HEBREW_RE = re.compile(r"[\u0590-\u05FF]")
SPANISH_MARKS_RE = re.compile(r"[áéíóúñü¿¡ÁÉÍÓÚÑÜ]")
TOKEN_RE = re.compile(r"[A-Za-zÀ-ÿ\u0590-\u05FF']+")
SPANISH_STOPWORDS = {
    "de",
    "la",
    "el",
    "y",
    "en",
    "que",
    "los",
    "las",
    "una",
    "un",
    "para",
    "con",
    "quiero",
    "propiedad",
    "visita",
}
ENGLISH_STOPWORDS = {
    "the",
    "and",
    "is",
    "in",
    "for",
    "to",
    "of",
    "this",
    "that",
    "with",
    "on",
    "a",
    "an",
    "i",
    "you",
    "we",
    "would",
    "schedule",
    "property",
}


def _clamp_confidence(value: float) -> float:
    return max(0.0, min(1.0, round(value, 2)))


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _detect_language(text: str) -> LanguageDetectResponse:
    normalized = text.strip()
    if not normalized:
        return LanguageDetectResponse(language="unknown", confidence=0.0, strategy="empty_text")

    if HEBREW_RE.search(normalized):
        return LanguageDetectResponse(language="he", confidence=0.99, strategy="unicode_hebrew_range")

    tokens = _tokenize(normalized)
    if not tokens:
        return LanguageDetectResponse(language="unknown", confidence=0.1, strategy="non_alpha_input")

    spanish_stopword_hits = sum(1 for token in tokens if token in SPANISH_STOPWORDS)
    english_stopword_hits = sum(1 for token in tokens if token in ENGLISH_STOPWORDS)
    has_spanish_marks = bool(SPANISH_MARKS_RE.search(normalized))

    if has_spanish_marks or spanish_stopword_hits >= 2:
        confidence = 0.7 + (0.15 if has_spanish_marks else 0.0) + min(0.15, spanish_stopword_hits * 0.03)
        return LanguageDetectResponse(
            language="es",
            confidence=_clamp_confidence(confidence),
            strategy="accent_stopword_heuristic",
        )

    if english_stopword_hits >= 2:
        confidence = 0.68 + min(0.27, english_stopword_hits * 0.04)
        return LanguageDetectResponse(
            language="en",
            confidence=_clamp_confidence(confidence),
            strategy="ascii_stopword_heuristic",
        )

    if spanish_stopword_hits > english_stopword_hits and spanish_stopword_hits > 0:
        confidence = 0.55 + min(0.2, spanish_stopword_hits * 0.03)
        return LanguageDetectResponse(
            language="es",
            confidence=_clamp_confidence(confidence),
            strategy="relative_stopword_score",
        )

    if english_stopword_hits > spanish_stopword_hits and english_stopword_hits > 0:
        confidence = 0.52 + min(0.2, english_stopword_hits * 0.03)
        return LanguageDetectResponse(
            language="en",
            confidence=_clamp_confidence(confidence),
            strategy="relative_stopword_score",
        )

    return LanguageDetectResponse(language="unknown", confidence=0.25, strategy="ambiguous_low_signal")


@router.post("/detect", response_model=LanguageDetectResponse)
async def detect_language(payload: LanguageDetectRequest) -> LanguageDetectResponse:
    return _detect_language(payload.text)
