"""Response translation pipeline stage.

Translates Jorge's outgoing message to match the language detected in the
user's most recent message (set by :class:`LanguageMirrorProcessor` earlier
in the pipeline).

Strategy
--------
1. If ``context.detected_language == "en"`` (or detection confidence < 0.7),
   the message is returned unchanged.
2. For **Spanish** (``"es"``), the stage first consults a static phrase
   dictionary that covers all ~20 fixed Jorge messages (qualification
   questions, scheduling prompts, post-confirm handoff, objection-exhaustion,
   take-away close, etc.).  Exact English strings are matched after
   case-folding and whitespace normalisation.
3. If the message is not in the dictionary (e.g. a dynamically-generated
   objection response), the stage falls through without modification and
   appends a ``"language_mismatch"`` compliance note so operators can audit
   which messages weren't translated.
"""

import logging
import re

from ghl_real_estate_ai.services.jorge.response_pipeline.base import (
    ResponseProcessorStage,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ComplianceFlag,
    ComplianceFlagSeverity,
    ProcessedResponse,
    ProcessingContext,
)

logger = logging.getLogger(__name__)

# ── Minimum confidence for language detection to trigger translation ─────────
_MIN_CONFIDENCE = 0.65

# ── Static Spanish translations for all fixed Jorge messages ─────────────────
# Keys are normalised English strings (lower-cased, collapsed whitespace).
# Values are the Spanish equivalents, preserving Jorge's direct tone.
_EN_TO_ES: dict[str, str] = {
    # Q1 — Motivation
    "what's making you think about selling, and where do you move to?":
        "¿Qué te está haciendo pensar en vender y a dónde te piensas mudar?",

    # Q2 — Timeline
    "if our team sold your home within the next 30 to 45 days, would that work for you?":
        "Si nuestro equipo vendiera tu casa en los próximos 30 a 45 días, ¿funcionaría eso para ti?",

    # Q3 — Condition
    "walk me through the condition — is it move-in ready, or does it need some work?":
        "Cuéntame sobre el estado de la propiedad — ¿está lista para mudarse o necesita algo de trabajo?",
    "walk me through the condition - is it move-in ready, or does it need some work?":
        "Cuéntame sobre el estado de la propiedad — ¿está lista para mudarse o necesita algo de trabajo?",

    # Q4 — Price
    "what price would make you feel good about selling?":
        "¿Qué precio te haría sentir bien con la venta?",

    # Scheduling — time ask
    "what time works best for a quick call — morning, afternoon, or evening? we'll lock it in.":
        "¿Qué horario te funciona mejor para una llamada rápida — mañana, tarde o noche? Lo confirmamos.",
    "what time works best for a quick call - morning, afternoon, or evening? we'll lock it in.":
        "¿Qué horario te funciona mejor para una llamada rápida — mañana, tarde o noche? Lo confirmamos.",
    "what time works best for a quick call morning, afternoon, or evening? we'll lock it in.":
        "¿Qué horario te funciona mejor para una llamada rápida — mañana, tarde o noche? Lo confirmamos.",
    "let's do it. what time works best for you — morning, afternoon, or evening? we'll get you on the calendar.":
        "¡Vamos! ¿Qué horario te funciona mejor — mañana, tarde o noche? Te ponemos en el calendario.",
    "let's do it. what time works best for you - morning, afternoon, or evening? we'll get you on the calendar.":
        "¡Vamos! ¿Qué horario te funciona mejor — mañana, tarde o noche? Te ponemos en el calendario.",

    # Scheduling — day ask
    "what day works best — this week or next?":
        "¿Qué día te funciona mejor — esta semana o la próxima?",
    "what day works best - this week or next?":
        "¿Qué día te funciona mejor — esta semana o la próxima?",
    "what day works best this week or next?":
        "¿Qué día te funciona mejor — esta semana o la próxima?",

    # Scheduling — confirm / wrap-up
    "perfect, i'll have jorge's team reach out to lock it in. talk soon!":
        "¡Perfecto, el equipo de Jorge se pondrá en contacto para confirmarlo. ¡Hasta pronto!",
    "you're all set. our team will reach out to confirm the details. talk soon!":
        "Todo listo. Nuestro equipo te contactará para confirmar los detalles. ¡Hasta pronto!",

    # F-10: Post-confirm handoff
    "our team has everything they need and will be reaching out soon. "
    "if you have any questions in the meantime, they'll be happy to help!":
        "Nuestro equipo tiene todo lo que necesita y se pondrá en contacto pronto. "
        "Si tienes alguna pregunta mientras tanto, estarán felices de ayudarte.",

    # F-11: Objection-exhaustion handoff
    "no problem at all — i appreciate your time. "
    "if your situation ever changes and you'd like to explore your options, "
    "our team would love to help. feel free to reach out anytime!":
        "Sin problema — agradezco tu tiempo. "
        "Si tu situación cambia y quieres explorar tus opciones, "
        "a nuestro equipo le encantaría ayudarte. ¡No dudes en contactarnos cuando quieras!",
}


def _normalise(text: str) -> str:
    """Lower-case and collapse internal whitespace for dictionary lookup."""
    return re.sub(r"\s+", " ", text.lower().strip())


class ResponseTranslationProcessor(ResponseProcessorStage):
    """Translates outgoing Jorge messages to match the user's detected language.

    Covers all ~20 fixed qualification / scheduling / handoff messages via a
    static dictionary.  Dynamically-generated messages that are not in the
    dictionary are passed through unchanged; a ``language_mismatch`` compliance
    note is appended so operators can audit coverage gaps.
    """

    @property
    def name(self) -> str:
        return "response_translation"

    async def process(
        self,
        response: ProcessedResponse,
        context: ProcessingContext,
    ) -> ProcessedResponse:
        lang = context.detected_language
        confidence = (
            context.metadata.get("language_detection", {}).get("confidence", 1.0)
        )

        # Only translate if confident and non-English
        if lang == "en" or confidence < _MIN_CONFIDENCE:
            return response

        if lang == "es":
            normalised = _normalise(response.message)
            translated = _EN_TO_ES.get(normalised)

            if translated:
                logger.debug(
                    "Translated message to Spanish for contact %s",
                    context.contact_id,
                )
                response.message = translated
            else:
                # Message not in static dictionary — log for coverage audit
                logger.warning(
                    "No Spanish translation available for contact %s message: %.80r",
                    context.contact_id,
                    response.message,
                )
                response.compliance_flags.append(
                    ComplianceFlag(
                        stage=self.name,
                        category="language_mismatch",
                        severity=ComplianceFlagSeverity.INFO,
                        description=(
                            f"Spanish user received English response (no static translation): "
                            f"{response.message[:80]!r}"
                        ),
                    )
                )
        # Future: add additional language branches here (pt, zh, vi, …)

        return response
