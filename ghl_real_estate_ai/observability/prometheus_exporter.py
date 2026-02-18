"""Prometheus metrics exporter for Jorge bot system.

Exports key operational metrics in Prometheus exposition format:
- Cache hit rates (L1/L2/L3)
- Handoff counts by route
- Response latency P95 by bot type
- Error rates by bot type
- FRS/PCS score distributions
- Lead temperature tag publishes

Usage:
    from ghl_real_estate_ai.observability.prometheus_exporter import JorgePrometheusExporter

    exporter = JorgePrometheusExporter()
    exporter.observe_frs_score(85.5)
    exporter.inc_handoff("lead", "buyer")
"""

import logging
from typing import Optional

try:
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
        start_http_server,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Score distribution buckets aligned with temperature thresholds
_SCORE_BUCKETS = (0, 20, 40, 60, 80, 100)


class JorgePrometheusExporter:
    """Collects and exports Prometheus metrics for the Jorge bot system."""

    def __init__(self, registry: Optional["CollectorRegistry"] = None):
        if not PROMETHEUS_AVAILABLE:
            logger.warning(
                "prometheus_client not installed -- JorgePrometheusExporter is a no-op"
            )
            self._enabled = False
            return

        self._enabled = True
        self._registry = registry  # None means use the global default registry

        reg_kwargs = {"registry": registry} if registry is not None else {}

        # -- Gauges ----------------------------------------------------------
        self.cache_hit_rate = Gauge(
            "jorge_cache_hit_rate",
            "Cache hit rate by cache layer",
            ["layer"],
            **reg_kwargs,
        )

        self.response_latency_p95 = Gauge(
            "jorge_response_latency_p95",
            "P95 response latency in milliseconds by bot type",
            ["bot_type"],
            **reg_kwargs,
        )

        self.error_rate = Gauge(
            "jorge_error_rate",
            "Error rate (0.0-1.0) by bot type",
            ["bot_type"],
            **reg_kwargs,
        )

        # -- Counters --------------------------------------------------------
        self.handoff_total = Counter(
            "jorge_handoff_total",
            "Total handoff events by source and target bot",
            ["source_bot", "target_bot"],
            **reg_kwargs,
        )

        self.lead_temperature = Counter(
            "jorge_lead_temperature",
            "Lead temperature tag publishes",
            ["temperature"],
            **reg_kwargs,
        )

        # -- Histograms ------------------------------------------------------
        self.frs_score = Histogram(
            "jorge_frs_score",
            "FRS (Financial Readiness Score) distribution",
            buckets=_SCORE_BUCKETS,
            **reg_kwargs,
        )

        self.pcs_score = Histogram(
            "jorge_pcs_score",
            "PCS (Psychological Commitment Score) distribution",
            buckets=_SCORE_BUCKETS,
            **reg_kwargs,
        )

        logger.info("JorgePrometheusExporter initialized")

    # -- Convenience methods -------------------------------------------------

    def set_cache_hit_rate(self, layer: str, rate: float) -> None:
        """Set cache hit rate for a given layer (l1, l2, l3)."""
        if self._enabled:
            self.cache_hit_rate.labels(layer=layer).set(rate)

    def set_response_latency_p95(self, bot_type: str, latency_ms: float) -> None:
        """Set P95 response latency for a bot type."""
        if self._enabled:
            self.response_latency_p95.labels(bot_type=bot_type).set(latency_ms)

    def set_error_rate(self, bot_type: str, rate: float) -> None:
        """Set error rate for a bot type."""
        if self._enabled:
            self.error_rate.labels(bot_type=bot_type).set(rate)

    def inc_handoff(self, source_bot: str, target_bot: str) -> None:
        """Increment handoff counter for a given route."""
        if self._enabled:
            self.handoff_total.labels(
                source_bot=source_bot, target_bot=target_bot
            ).inc()

    def inc_lead_temperature(self, temperature: str) -> None:
        """Increment lead temperature counter (hot, warm, cold)."""
        if self._enabled:
            self.lead_temperature.labels(temperature=temperature).inc()

    def observe_frs_score(self, score: float) -> None:
        """Record an FRS score observation."""
        if self._enabled:
            self.frs_score.observe(score)

    def observe_pcs_score(self, score: float) -> None:
        """Record a PCS score observation."""
        if self._enabled:
            self.pcs_score.observe(score)

    def collect(self) -> bytes:
        """Generate Prometheus exposition format output.

        Returns:
            bytes of the latest metrics in text exposition format.
        """
        if not self._enabled:
            return b""
        return generate_latest(self._registry)

    def start_server(self, port: int = 8000) -> None:
        """Start a standalone Prometheus metrics HTTP server.

        This is useful for sidecar-style scraping. For FastAPI integration,
        use the ``/metrics`` route in health.py instead.

        Args:
            port: TCP port to listen on (default 8000).
        """
        if not self._enabled:
            logger.warning("Cannot start metrics server -- prometheus_client missing")
            return
        start_http_server(port, registry=self._registry)
        logger.info("Prometheus metrics server started on port %d", port)


# -- Singleton access --------------------------------------------------------

_exporter: Optional[JorgePrometheusExporter] = None


def get_prometheus_exporter() -> JorgePrometheusExporter:
    """Get or create the global JorgePrometheusExporter singleton."""
    global _exporter
    if _exporter is None:
        _exporter = JorgePrometheusExporter()
    return _exporter
