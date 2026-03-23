"""
Structured logging configuration using structlog.

Call configure_structlog() once at application startup (api/main.py).
Use structlog.get_logger(__name__) in modules that want structured output.
Modules using the legacy get_logger() from ghl_utils.logger continue to work
via the stdlib bridge — structlog processes their records through the same pipeline.

Log format:
- Development (LOG_FORMAT=console): colored, aligned human-readable output
- Production (default): JSON per-line, compatible with Elasticsearch / Loki
"""

import logging
import os
import sys

import structlog


def configure_structlog() -> None:
    """Configure structlog with stdlib bridge. Call once at app startup."""

    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    is_dev = os.getenv("LOG_FORMAT", "json").lower() == "console"

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
    ]

    if is_dev:
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
