"""
Real-time Configuration and Validation Service

Handles WebSocket and Redis configuration with environment-specific validation,
connection testing, and fallback management for the GHL Real Estate AI system.
"""

import asyncio
import json
import logging
import os
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import websockets

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

try:
    import aioredis

    AIOREDIS_AVAILABLE = True
except ImportError:
    AIOREDIS_AVAILABLE = False


logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Connection status enumeration"""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"
    NOT_CONFIGURED = "not_configured"


@dataclass
class RedisConfig:
    """Redis configuration with validation"""

    url: str
    password: Optional[str] = None
    db: int = 0
    max_connections: int = 20
    socket_timeout: int = 30
    socket_connect_timeout: int = 30
    retry_on_timeout: bool = True
    health_check_interval: int = 30

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis client"""
        config = {
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
            "retry_on_timeout": self.retry_on_timeout,
            "health_check_interval": self.health_check_interval,
            "max_connections": self.max_connections,
            "decode_responses": True,
        }

        if self.password:
            config["password"] = self.password

        return config


@dataclass
class WebSocketConfig:
    """WebSocket configuration with validation"""

    host: str = "localhost"
    port: int = 8765
    path: str = "/ws"
    protocol: str = "ws"
    secure: bool = False
    origins: str = "localhost:8501,127.0.0.1:8501"
    ping_interval: int = 20
    ping_timeout: int = 10
    close_timeout: int = 10
    max_size: int = 1048576  # 1MB
    max_queue: int = 32
    reconnect_attempts: int = 5
    reconnect_delay: int = 2
    fallback_to_polling: bool = True

    @property
    def url(self) -> str:
        """Get WebSocket URL"""
        protocol = "wss" if self.secure else "ws"
        return f"{protocol}://{self.host}:{self.port}{self.path}"

    @property
    def origins_list(self) -> list:
        """Get origins as list"""
        return [origin.strip() for origin in self.origins.split(",")]


@dataclass
class RealtimeConfig:
    """Real-time service configuration"""

    enabled: bool = True
    use_websocket: bool = True
    poll_interval: int = 2
    max_events: int = 1000
    cache_ttl: int = 3600
    event_dedup_window: int = 30
    high_priority_threshold: int = 3
    batch_size: int = 50


class RealtimeConfigManager:
    """
    Manages real-time configuration for WebSocket and Redis connections.

    Provides environment-specific validation, connection testing, and
    fallback management for production deployments.
    """

    def __init__(self):
        self.redis_config = self._load_redis_config()
        self.websocket_config = self._load_websocket_config()
        self.realtime_config = self._load_realtime_config()

        self._redis_client: Optional[redis.Redis] = None
        self._aioredis_client: Optional[Any] = None
        self._connection_status = {
            "redis": ConnectionStatus.NOT_CONFIGURED,
            "websocket": ConnectionStatus.NOT_CONFIGURED,
        }

    def _load_redis_config(self) -> RedisConfig:
        """Load Redis configuration from environment"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

        return RedisConfig(
            url=redis_url,
            password=os.getenv("REDIS_PASSWORD"),
            db=int(os.getenv("REDIS_DB", "0")),
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "20")),
            socket_timeout=int(os.getenv("REDIS_SOCKET_TIMEOUT", "30")),
            socket_connect_timeout=int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "30")),
            retry_on_timeout=os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true",
            health_check_interval=int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30")),
        )

    def _load_websocket_config(self) -> WebSocketConfig:
        """Load WebSocket configuration from environment"""
        return WebSocketConfig(
            host=os.getenv("WEBSOCKET_HOST", "localhost"),
            port=int(os.getenv("WEBSOCKET_PORT", "8765")),
            path=os.getenv("WEBSOCKET_PATH", "/ws"),
            protocol=os.getenv("WEBSOCKET_PROTOCOL", "ws"),
            secure=os.getenv("WEBSOCKET_SECURE", "false").lower() == "true",
            origins=os.getenv("WEBSOCKET_ORIGINS", "localhost:8501,127.0.0.1:8501"),
            ping_interval=int(os.getenv("WEBSOCKET_PING_INTERVAL", "20")),
            ping_timeout=int(os.getenv("WEBSOCKET_PING_TIMEOUT", "10")),
            close_timeout=int(os.getenv("WEBSOCKET_CLOSE_TIMEOUT", "10")),
            max_size=int(os.getenv("WEBSOCKET_MAX_SIZE", "1048576")),
            max_queue=int(os.getenv("WEBSOCKET_MAX_QUEUE", "32")),
            reconnect_attempts=int(os.getenv("WEBSOCKET_RECONNECT_ATTEMPTS", "5")),
            reconnect_delay=int(os.getenv("WEBSOCKET_RECONNECT_DELAY", "2")),
            fallback_to_polling=os.getenv("WEBSOCKET_FALLBACK_TO_POLLING", "true").lower() == "true",
        )

    def _load_realtime_config(self) -> RealtimeConfig:
        """Load real-time service configuration from environment"""
        return RealtimeConfig(
            enabled=os.getenv("REALTIME_ENABLED", "true").lower() == "true",
            use_websocket=os.getenv("REALTIME_USE_WEBSOCKET", "true").lower() == "true",
            poll_interval=int(os.getenv("REALTIME_POLL_INTERVAL", "2")),
            max_events=int(os.getenv("REALTIME_MAX_EVENTS", "1000")),
            cache_ttl=int(os.getenv("REALTIME_CACHE_TTL", "3600")),
            event_dedup_window=int(os.getenv("REALTIME_EVENT_DEDUP_WINDOW", "30")),
            high_priority_threshold=int(os.getenv("REALTIME_HIGH_PRIORITY_THRESHOLD", "3")),
            batch_size=int(os.getenv("REALTIME_BATCH_SIZE", "50")),
        )

    async def test_redis_connection(self) -> Tuple[bool, str]:
        """Test Redis connection and return status"""
        if not REDIS_AVAILABLE:
            return False, "Redis library not available"

        try:
            # Test sync Redis connection
            client = redis.from_url(self.redis_config.url, **self.redis_config.to_dict())
            client.ping()
            client.close()

            # Test async Redis connection if available
            if AIOREDIS_AVAILABLE:
                async_client = aioredis.from_url(self.redis_config.url)
                await async_client.ping()
                await async_client.close()

            self._connection_status["redis"] = ConnectionStatus.CONNECTED
            return True, "Redis connection successful"

        except Exception as e:
            self._connection_status["redis"] = ConnectionStatus.ERROR
            return False, f"Redis connection failed: {str(e)}"

    async def test_websocket_connection(self) -> Tuple[bool, str]:
        """Test WebSocket connection and return status"""
        if not WEBSOCKETS_AVAILABLE:
            return False, "WebSocket library not available"

        try:
            # Attempt to connect to WebSocket server
            async with websockets.connect(
                self.websocket_config.url,
                ping_interval=self.websocket_config.ping_interval,
                ping_timeout=self.websocket_config.ping_timeout,
                close_timeout=self.websocket_config.close_timeout,
                max_size=self.websocket_config.max_size,
                max_queue=self.websocket_config.max_queue,
            ) as websocket:
                # Send a test message
                test_message = {"type": "ping", "timestamp": asyncio.get_event_loop().time()}
                await websocket.send(json.dumps(test_message))

                # Wait for response with timeout
                try:
                    await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    self._connection_status["websocket"] = ConnectionStatus.CONNECTED
                    return True, "WebSocket connection successful"
                except asyncio.TimeoutError:
                    return True, "WebSocket connected but no response (server may not echo)"

        except ConnectionRefusedError:
            self._connection_status["websocket"] = ConnectionStatus.ERROR
            return False, "WebSocket server not running or refusing connections"
        except Exception as e:
            self._connection_status["websocket"] = ConnectionStatus.ERROR
            return False, f"WebSocket connection failed: {str(e)}"

    def get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client instance"""
        if not REDIS_AVAILABLE:
            return None

        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(self.redis_config.url, **self.redis_config.to_dict())
            except Exception as e:
                logger.error(f"Failed to create Redis client: {e}")
                return None

        return self._redis_client

    async def get_aioredis_client(self):
        """Get async Redis client instance"""
        if not AIOREDIS_AVAILABLE:
            return None

        if self._aioredis_client is None:
            try:
                self._aioredis_client = aioredis.from_url(self.redis_config.url)
            except Exception as e:
                logger.error(f"Failed to create async Redis client: {e}")
                return None

        return self._aioredis_client

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate complete configuration and return status report"""
        validation_report = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "components": {
                "redis": {
                    "available": REDIS_AVAILABLE,
                    "configured": bool(self.redis_config.url),
                    "status": self._connection_status["redis"].value,
                },
                "websocket": {
                    "available": WEBSOCKETS_AVAILABLE,
                    "configured": True,  # WebSocket config always has defaults
                    "status": self._connection_status["websocket"].value,
                },
                "realtime": {
                    "enabled": self.realtime_config.enabled,
                    "use_websocket": self.realtime_config.use_websocket and WEBSOCKETS_AVAILABLE,
                },
            },
            "configuration": {
                "redis": asdict(self.redis_config) if REDIS_AVAILABLE else None,
                "websocket": asdict(self.websocket_config),
                "realtime": asdict(self.realtime_config),
            },
        }

        # Check for configuration issues
        if not REDIS_AVAILABLE:
            validation_report["warnings"].append("Redis library not available - caching disabled")

        if not WEBSOCKETS_AVAILABLE:
            validation_report["warnings"].append("WebSocket library not available - falling back to polling")

        if self.realtime_config.use_websocket and not WEBSOCKETS_AVAILABLE:
            validation_report["errors"].append("WebSocket requested but library not available")
            validation_report["valid"] = False

        # Environment-specific warnings
        environment = os.getenv("ENVIRONMENT", "development").lower()
        if environment == "production":
            if not self.redis_config.password:
                validation_report["warnings"].append("Production environment without Redis password")

            if not self.websocket_config.secure:
                validation_report["warnings"].append("Production environment using unsecured WebSocket")

        return validation_report

    async def test_all_connections(self) -> Dict[str, Any]:
        """Test all connections and return comprehensive status"""
        results = {}

        # Test Redis
        redis_success, redis_message = await self.test_redis_connection()
        results["redis"] = {"success": redis_success, "message": redis_message, "available": REDIS_AVAILABLE}

        # Test WebSocket
        ws_success, ws_message = await self.test_websocket_connection()
        results["websocket"] = {"success": ws_success, "message": ws_message, "available": WEBSOCKETS_AVAILABLE}

        # Overall status
        results["overall"] = {
            "ready": redis_success and (ws_success or self.websocket_config.fallback_to_polling),
            "realtime_capable": redis_success and ws_success,
            "fallback_mode": redis_success and not ws_success and self.websocket_config.fallback_to_polling,
        }

        return results

    def get_connection_string_examples(self) -> Dict[str, str]:
        """Get example connection strings for documentation"""
        return {
            "redis_local": "redis://localhost:6379",
            "redis_password": "redis://:password@localhost:6379/0",
            "redis_railway": "redis://default:password@host:port",
            "websocket_local": "ws://localhost:8765/ws",
            "websocket_secure": "wss://your-ontario_mills.com/ws",
            "websocket_development": f"{self.websocket_config.url}",
        }

    def get_environment_template(self) -> str:
        """Get environment variables template for .env file"""
        return f"""# Real-time Configuration
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_MAX_CONNECTIONS=20
REDIS_SOCKET_TIMEOUT=30

# WebSocket Configuration
WEBSOCKET_HOST=localhost
WEBSOCKET_PORT=8765
WEBSOCKET_PATH=/ws
WEBSOCKET_SECURE=false
WEBSOCKET_ORIGINS=localhost:8501,127.0.0.1:8501

# Real-time Service
REALTIME_ENABLED=true
REALTIME_USE_WEBSOCKET=true
REALTIME_POLL_INTERVAL=2
REALTIME_MAX_EVENTS=1000
"""


# Global instance
_config_manager = None


def get_config_manager() -> RealtimeConfigManager:
    """Get or create global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = RealtimeConfigManager()
    return _config_manager


# Convenience functions
def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client instance"""
    return get_config_manager().get_redis_client()


async def get_aioredis_client():
    """Get async Redis client instance"""
    return await get_config_manager().get_aioredis_client()


def get_websocket_url() -> str:
    """Get WebSocket URL"""
    return get_config_manager().websocket_config.url


async def validate_realtime_setup() -> Dict[str, Any]:
    """Validate complete real-time setup"""
    manager = get_config_manager()
    validation_report = manager.validate_configuration()
    connection_results = await manager.test_all_connections()

    return {
        "validation": validation_report,
        "connections": connection_results,
        "ready_for_production": (
            validation_report["valid"]
            and connection_results["overall"]["ready"]
            and len(validation_report["errors"]) == 0
        ),
    }


if __name__ == "__main__":
    # Test the configuration
    async def test_config():
        manager = RealtimeConfigManager()

        print("=== Real-time Configuration Test ===")
        print(f"Redis Available: {REDIS_AVAILABLE}")
        print(f"WebSocket Available: {WEBSOCKETS_AVAILABLE}")
        print(f"Async Redis Available: {AIOREDIS_AVAILABLE}")

        validation = manager.validate_configuration()
        print(f"\nConfiguration Valid: {validation['valid']}")

        if validation["errors"]:
            print("Errors:", validation["errors"])
        if validation["warnings"]:
            print("Warnings:", validation["warnings"])

        # Test connections
        results = await manager.test_all_connections()
        print(f"\nConnection Test Results:")
        print(f"Redis: {results['redis']['message']}")
        print(f"WebSocket: {results['websocket']['message']}")
        print(f"Overall Ready: {results['overall']['ready']}")

        print("\nEnvironment Template:")
        print(manager.get_environment_template())

    asyncio.run(test_config())
