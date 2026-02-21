"""
Performance benchmarks for bilingual language detection service.

This test suite validates that language detection meets the <100ms latency target
for production use with Jorge Bot.
"""

import time
from typing import List, Tuple

import pytest

from ghl_real_estate_ai.services.language_detection import (
    LanguageDetectionService,
    get_language_detection_service,
)

pytestmark = pytest.mark.integration


class TestLanguageDetectionPerformance:
    """Performance benchmarks for language detection service."""

    @pytest.fixture(scope="class")
    def service(self) -> LanguageDetectionService:
        """Warm up the service by loading the model."""
        svc = get_language_detection_service()
        # Warmup call to load model
        svc.detect("Hello")
        return svc

    @pytest.fixture
    def test_messages(self) -> List[Tuple[str, str]]:
        """Real estate ontario_mills test messages with expected languages."""
        return [
            ("Hello, I want to buy a house", "en"),
            ("I'm interested in properties in Rancho Cucamonga", "en"),
            ("What is the price range?", "en"),
            ("Can you help me with financing?", "en"),
            ("Quiero comprar una casa", "es"),
            ("Me interesa vender mi propiedad", "es"),
            ("¿Cuánto cuesta?", "es"),
            ("Necesito ayuda con mi hipoteca", "es"),
            ("Busco una casa de 3 habitaciones", "es"),
            ("Estoy buscando propiedades en Rancho Cucamonga", "es"),
        ]

    def test_single_detection_latency(self, service: LanguageDetectionService):
        """Test that single detection is under 100ms (after warmup)."""
        # Warmup
        service.detect("Test message")

        # Measure
        start = time.perf_counter()
        result = service.detect("I want to buy a house")
        latency_ms = (time.perf_counter() - start) * 1000

        assert latency_ms < 100, f"Single detection took {latency_ms:.1f}ms, target is <100ms"
        assert result.language == "en"

    def test_batch_detection_latency(self, service: LanguageDetectionService, test_messages: List[Tuple[str, str]]):
        """Test average latency across batch of messages."""
        latencies = []

        for message, expected_lang in test_messages:
            start = time.perf_counter()
            result = service.detect(message)
            latency_ms = (time.perf_counter() - start) * 1000
            latencies.append(latency_ms)

            assert result.language == expected_lang, f"Expected {expected_lang}, got {result.language} for: {message}"

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        print(f"\nLatency Stats:")
        print(f"  Average: {avg_latency:.1f}ms")
        print(f"  Max: {max_latency:.1f}ms")
        print(f"  P95: {p95_latency:.1f}ms")

        # P95 should be under 100ms
        assert p95_latency < 100, f"P95 latency {p95_latency:.1f}ms exceeds 100ms target"

    def test_accuracy_spanish_real_estate(self, service: LanguageDetectionService):
        """Test accuracy for Spanish real estate phrases (>95% target)."""
        spanish_tests = [
            "Hola, buenos días",
            "Quiero comprar una casa",
            "Me gustaría vender mi propiedad",
            "¿Cuánto cuesta?",
            "Estoy interesado en propiedades",
            "Necesito ayuda con mi hipoteca",
            "Busco una casa de 3 habitaciones",
            "¿Tiene casas en venta?",
            "Me interesa el mercado de Rancho Cucamonga",
            "¿Cuándo puedo ver la propiedad?",
        ]

        correct = 0
        for text in spanish_tests:
            result = service.detect(text)
            if result.language == "es":
                correct += 1

        accuracy = (correct / len(spanish_tests)) * 100
        print(f"\nSpanish Accuracy: {accuracy:.1f}%")

        assert accuracy >= 95.0, f"Spanish accuracy {accuracy:.1f}% below 95% target"

    def test_accuracy_english_real_estate(self, service: LanguageDetectionService):
        """Test accuracy for English real estate phrases (>95% target)."""
        english_tests = [
            "Hello, good morning",
            "I want to buy a house",
            "I would like to sell my property",
            "How much does it cost?",
            "I am interested in properties",
            "I need help with my mortgage",
            "I'm looking for a 3 bedroom house",
            "Do you have homes for sale?",
            "I'm interested in the Rancho Cucamonga market",
            "When can I see the property?",
        ]

        correct = 0
        for text in english_tests:
            result = service.detect(text)
            if result.language == "en":
                correct += 1

        accuracy = (correct / len(english_tests)) * 100
        print(f"\nEnglish Accuracy: {accuracy:.1f}%")

        assert accuracy >= 95.0, f"English accuracy {accuracy:.1f}% below 95% target"

    def test_code_switching_detection(self, service: LanguageDetectionService):
        """Test detection of Spanish/English code-switching."""
        code_switching_text = "Hello, I'm interested in buying. Pero necesito ayuda con el financiamiento."

        result = service.detect(code_switching_text)

        # Should detect code-switching
        assert result.is_code_switching, "Failed to detect code-switching"
        assert result.secondary_language is not None

    def test_contact_preference_tracking(self, service: LanguageDetectionService):
        """Test that contact preferences are tracked correctly."""
        contact_id = "test_contact_perf"

        # Send 3 Spanish messages, 1 English
        service.detect("Hola", contact_id=contact_id)
        service.detect("¿Cómo estás?", contact_id=contact_id)
        service.detect("Quiero comprar", contact_id=contact_id)
        service.detect("Hello", contact_id=contact_id)

        pref = service.get_contact_preference(contact_id)

        assert pref is not None
        assert pref.primary_language == "es"  # Majority is Spanish
        assert pref.total_messages == 4
