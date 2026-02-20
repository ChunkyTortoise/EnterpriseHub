"""Market Intelligence Loader — loads market config from JSON, supports JORGE_MARKET env var."""
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

_CONFIG_PATH = Path(__file__).parent / "market_intelligence.json"


class MarketIntelligenceLoader:
    """Loads and provides active market configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        self._config_path = config_path or _CONFIG_PATH
        self._data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self._config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load market intelligence config: {e}")
            return {"active_market": "rancho_cucamonga", "markets": {}}

    def get_active_market(self) -> Dict[str, Any]:
        """Return the active market config. JORGE_MARKET env var overrides the JSON default."""
        active_key = os.getenv("JORGE_MARKET", self._data.get("active_market", "rancho_cucamonga"))
        markets = self._data.get("markets", {})
        if active_key not in markets:
            logger.warning(f"Market '{active_key}' not found; falling back to 'rancho_cucamonga'")
            active_key = "rancho_cucamonga"
        return markets.get(active_key, {})

    def get_market_key(self) -> str:
        return os.getenv("JORGE_MARKET", self._data.get("active_market", "rancho_cucamonga"))


_loader: Optional[MarketIntelligenceLoader] = None


def get_market_loader() -> MarketIntelligenceLoader:
    global _loader
    if _loader is None:
        _loader = MarketIntelligenceLoader()
    return _loader
