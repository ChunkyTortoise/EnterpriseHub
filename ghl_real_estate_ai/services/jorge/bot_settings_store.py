"""Runtime-editable bot settings store.

Provides hot-reloadable settings for seller and buyer bots:
  - system_prompt : optional persona prefix injected into Claude prompts
  - jorge_phrases : opener phrases prepended to qualification questions
  - questions     : keyed by "1"-"4", override default question text

Settings survive server restarts via optional JSON persistence at
BOT_SETTINGS_PATH (defaults to /tmp/jorge_bot_settings.json).
"""

from __future__ import annotations

import copy
import json
import os
from threading import Lock
from typing import Any

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

_PERSIST_PATH = os.getenv("BOT_SETTINGS_PATH", "/tmp/jorge_bot_settings.json")

_DEFAULTS: dict[str, dict[str, Any]] = {
    "seller": {
        "system_prompt": "",
        "jorge_phrases": [
            "Happy to help",
            "Just to clarify",
            "Quick one",
            "Good to know",
            "Thanks for sharing that",
        ],
        "questions": {
            "1": "What's making you think about selling, and where would you move to?",
            "2": "If our team sold your home within the next 30 to 45 days, would that work for you?",
            "3": "How would you describe your home — move in ready or would it need some work?",
            "4": "What price would make you feel good about selling?",
        },
    },
    "buyer": {
        "system_prompt": "",
        "jorge_phrases": [
            "Happy to help",
            "Good to know",
            "Quick follow-up",
            "Thanks for that",
            "Got it",
        ],
        "questions": {
            "1": "What's your price range? That helps me focus on the right options for you.",
            "2": "Have you spoken with a lender yet? Getting pre-approved opens up a lot more doors.",
            "3": "When are you hoping to be in your new home?",
            "4": "How many bedrooms are you looking for, and anything specific about the size or style?",
        },
    },
}

_store: dict[str, dict[str, Any]] = {}
_lock = Lock()
_initialized = False


def _load_from_disk() -> None:
    try:
        with open(_PERSIST_PATH) as f:
            saved = json.load(f)
        for bot in ("seller", "buyer"):
            if bot in saved:
                for key in ("system_prompt", "jorge_phrases", "questions"):
                    if key in saved[bot]:
                        _store[bot][key] = saved[bot][key]
        logger.info(f"Bot settings loaded from {_PERSIST_PATH}")
    except FileNotFoundError:
        pass
    except json.JSONDecodeError as exc:
        logger.warning(f"Bot settings file corrupt, using defaults: {exc}")


def _save_to_disk() -> None:
    try:
        with open(_PERSIST_PATH, "w") as f:
            json.dump(_store, f, indent=2)
    except Exception as exc:
        logger.warning(f"Could not persist bot settings: {exc}")


def _ensure_initialized() -> None:
    global _initialized
    if not _initialized:
        with _lock:
            if not _initialized:
                _store.update(copy.deepcopy(_DEFAULTS))
                _load_from_disk()
                _initialized = True


def get_all_settings() -> dict[str, dict[str, Any]]:
    _ensure_initialized()
    return copy.deepcopy(_store)


def get_bot_settings(bot: str) -> dict[str, Any]:
    _ensure_initialized()
    return copy.deepcopy(_store.get(bot, copy.deepcopy(_DEFAULTS.get(bot, {}))))


def update_bot_settings(bot: str, partial: dict[str, Any]) -> dict[str, Any]:
    """Merge partial into stored settings and persist. Returns updated settings."""
    _ensure_initialized()
    allowed = {"system_prompt", "jorge_phrases", "questions"}
    filtered = {k: v for k, v in partial.items() if k in allowed}
    with _lock:
        if bot not in _store:
            _store[bot] = copy.deepcopy(_DEFAULTS.get(bot, {}))
        _store[bot].update(filtered)
        _save_to_disk()
    logger.info(f"Bot settings updated for '{bot}': keys={list(filtered.keys())}")
    return get_bot_settings(bot)


def get_questions(bot: str) -> dict[str, str]:
    return get_bot_settings(bot).get("questions", {})


def get_phrases(bot: str) -> list[str]:
    return get_bot_settings(bot).get("jorge_phrases", [])


def get_system_prompt_override(bot: str) -> str:
    return get_bot_settings(bot).get("system_prompt", "")


def reset_to_defaults() -> None:
    """Reset store to defaults (used in tests)."""
    global _initialized
    with _lock:
        _store.clear()
        _store.update(copy.deepcopy(_DEFAULTS))
        _initialized = True
