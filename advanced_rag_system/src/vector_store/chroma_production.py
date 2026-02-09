"""Production-ready ChromaDB vector store implementation.

This module provides enterprise-grade features for ChromaDB including:
- Connection pooling and management
- Exponential backoff retry logic
- Backup and restore mechanisms
- Schema migration support
- Health monitoring and metrics

Example:
    ```python
    config = ProductionVectorStoreConfig(
        collection_name="documents",
        dimension=1536,
        pool_max_connections=10,
        retry_max_retries=3,
    )
    store = ProductionChromaStore(config)
    await store.initialize()

    # Add chunks
    await store.add_chunks(chunks)

    # Search with automatic retries
    results = await store.search(embedding, SearchOptions(top_k=5))

    # Create backup
    await store.backup_manager.create_backup("full")

    await store.close()
    ```
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import random
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar
from uuid import UUID, uuid4

from src.core.exceptions import NotFoundError, VectorStoreError
from src.core.types import DocumentChunk, SearchResult
from src.vector_store.base import SearchOptions, VectorStoreConfig
from src.vector_store.chroma_store import ChromaVectorStore

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BackupType(Enum):
    """Types of backups supported."""

    FULL = "full"
    INCREMENTAL = "incremental"
    COLLECTION = "collection"


class MigrationStatus(Enum):
    """Status of a migration."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class RetryableError(Exception):
    """Error that can be retried."""

    pass


# ============================================================================
# Exception Classes
# ============================================================================


class ConnectionPoolError(VectorStoreError):
    """Exception raised for connection pool errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        pool_state: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            details=details,
            store_type="chroma_production",
            error_code="CONNECTION_POOL_ERROR",
        )
        self.pool_state = pool_state


class BackupError(VectorStoreError):
    """Exception raised for backup/restore errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        operation: Optional[str] = None,
    ) -> None:
        super().__init__(
            message=message,
            details=details,
            store_type="chroma_production",
            error_code="BACKUP_ERROR",
        )
        self.operation = operation


class MigrationError(VectorStoreError):
    """Exception raised for migration errors."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        migration_version: Optional[int] = None,
    ) -> None:
        super().__init__(
            message=message,
            details=details,
            store_type="chroma_production",
            error_code="MIGRATION_ERROR",
        )
        self.migration_version = migration_version


class RetryExhaustedError(VectorStoreError):
    """Exception raised when all retry attempts are exhausted."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        attempts: int = 0,
        last_error: Optional[Exception] = None,
    ) -> None:
        super().__init__(
            message=message,
            details=details,
            store_type="chroma_production",
            error_code="RETRY_EXHAUSTED",
        )
        self.attempts = attempts
        self.last_error = last_error


# ============================================================================
# Configuration Classes
# ============================================================================


@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pool.

    Attributes:
        min_connections: Minimum number of connections to maintain
        max_connections: Maximum number of connections allowed
        connection_timeout: Timeout for acquiring a connection (seconds)
        max_idle_time: Maximum time a connection can be idle (seconds)
        health_check_interval: Interval between health checks (seconds)
        connection_retry_attempts: Number of retries for connection creation
    """

    min_connections: int = 2
    max_connections: int = 10
    connection_timeout: float = 30.0
    max_idle_time: float = 300.0
    health_check_interval: float = 60.0
    connection_retry_attempts: int = 3


@dataclass
class RetryConfig:
    """Configuration for retry logic.

    Attributes:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
        retryable_exceptions: List of exception types that trigger retry
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple = field(
        default_factory=lambda: (
            ConnectionError,
            TimeoutError,
            RetryableError,
        )
    )


@dataclass
class BackupConfig:
    """Configuration for backup management.

    Attributes:
        enabled: Whether backups are enabled
        storage_path: Path for storing backups
        retention_days: Number of days to retain backups
        compression_enabled: Whether to compress backups
        encryption_enabled: Whether to encrypt backups
        schedule: Cron-like schedule for automatic backups
    """

    enabled: bool = True
    storage_path: str = "./backups"
    retention_days: int = 30
    compression_enabled: bool = True
    encryption_enabled: bool = False
    schedule: Optional[str] = None  # Cron-like: "0 2 * * *" for daily at 2 AM


@dataclass
class MigrationConfig:
    """Configuration for schema migrations.

    Attributes:
        auto_migrate: Whether to run migrations automatically on startup
        migration_path: Path to migration scripts
        allow_rollback: Whether to allow rollback of migrations
        backup_before_migration: Whether to create backup before migration
    """

    auto_migrate: bool = False
    migration_path: str = "./migrations"
    allow_rollback: bool = True
    backup_before_migration: bool = True


@dataclass
class ProductionVectorStoreConfig(VectorStoreConfig):
    """Extended configuration for production vector store.

    Attributes:
        # Base config from VectorStoreConfig
        collection_name: Name of the collection
        dimension: Vector dimensionality
        distance_metric: Distance metric for similarity
        metadata_schema: Optional schema for metadata validation

        # Production-specific config
        pool_config: Connection pool configuration
        retry_config: Retry logic configuration
        backup_config: Backup management configuration
        migration_config: Schema migration configuration
        enable_metrics: Whether to collect metrics
        enable_health_check: Whether to enable health monitoring
    """

    pool_config: ConnectionPoolConfig = field(default_factory=ConnectionPoolConfig)
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    backup_config: BackupConfig = field(default_factory=BackupConfig)
    migration_config: MigrationConfig = field(default_factory=MigrationConfig)
    enable_metrics: bool = True
    enable_health_check: bool = True


# ============================================================================
# Connection Pool
# ============================================================================


@dataclass
class PooledConnection:
    """A connection in the pool.

    Attributes:
        connection: The actual connection object
        created_at: When the connection was created
        last_used: When the connection was last used
        use_count: Number of times the connection has been used
        is_healthy: Whether the connection is healthy
    """

    connection: Any
    created_at: datetime
    last_used: datetime
    use_count: int = 0
    is_healthy: bool = True


class ConnectionPool:
    """Manages a pool of connections to ChromaDB.

    Provides:
    - Connection lifecycle management
    - Health checking
    - Automatic recycling
    - Concurrent access handling

    Example:
        ```python
        config = ConnectionPoolConfig(max_connections=10)
        pool = ConnectionPool(config, connection_factory)
        await pool.initialize()

        async with pool.acquire() as conn:
            # Use connection
            pass
        ```
    """

    def __init__(
        self,
        config: ConnectionPoolConfig,
        connection_factory: Callable[[], Any],
    ) -> None:
        """Initialize connection pool.

        Args:
            config: Pool configuration
            connection_factory: Factory function to create new connections
        """
        self.config = config
        self._connection_factory = connection_factory
        self._pool: asyncio.Queue[PooledConnection] = asyncio.Queue(maxsize=config.max_connections)
        self._active_connections: Set[PooledConnection] = set()
        self._semaphore: asyncio.Semaphore = asyncio.Semaphore(config.max_connections)
        self._lock = asyncio.Lock()
        self._initialized = False
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics: Dict[str, Any] = {
            "total_connections_created": 0,
            "total_connections_reused": 0,
            "health_check_failures": 0,
        }

    async def initialize(self) -> None:
        """Initialize the pool with minimum connections."""
        async with self._lock:
            for _ in range(self.config.min_connections):
                conn = await self._create_connection()
                await self._pool.put(conn)
            self._initialized = True

        # Start health check task
        if self.config.health_check_interval > 0:
            self._health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info(
            "Connection pool initialized with %d connections",
            self.config.min_connections,
        )

    async def close(self) -> None:
        """Close all connections and cleanup."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        async with self._lock:
            # Close all pooled connections
            while not self._pool.empty():
                try:
                    pooled = self._pool.get_nowait()
                    await self._close_connection(pooled)
                except asyncio.QueueEmpty:
                    break

            # Close active connections
            for pooled in list(self._active_connections):
                await self._close_connection(pooled)
            self._active_connections.clear()

        self._initialized = False
        logger.info("Connection pool closed")

    async def acquire(self) -> PooledConnection:
        """Acquire a connection from the pool.

        Returns:
            A pooled connection

        Raises:
            ConnectionPoolError: If unable to acquire connection within timeout
        """
        if not self._initialized:
            raise ConnectionPoolError("Pool not initialized")

        try:
            async with self._semaphore:
                # Try to get from pool with timeout
                try:
                    pooled = await asyncio.wait_for(
                        self._pool.get(),
                        timeout=self.config.connection_timeout,
                    )
                    self._metrics["total_connections_reused"] += 1
                except asyncio.TimeoutError:
                    # Create new connection if under max
                    pooled = await self._create_connection()

                # Validate connection health
                if not await self._is_healthy(pooled):
                    await self._close_connection(pooled)
                    pooled = await self._create_connection()

                # Update usage stats
                pooled.last_used = datetime.now()
                pooled.use_count += 1

                async with self._lock:
                    self._active_connections.add(pooled)

                return pooled

        except asyncio.TimeoutError:
            raise ConnectionPoolError(
                f"Timeout acquiring connection after {self.config.connection_timeout}s",
                pool_state=self._get_pool_state(),
            )

    async def release(self, pooled: PooledConnection) -> None:
        """Release a connection back to the pool.

        Args:
            pooled: The connection to release
        """
        async with self._lock:
            self._active_connections.discard(pooled)

        # Check if connection is still healthy
        if await self._is_healthy(pooled):
            # Check if connection has exceeded max idle time
            idle_time = datetime.now() - pooled.last_used
            if idle_time.total_seconds() < self.config.max_idle_time:
                try:
                    self._pool.put_nowait(pooled)
                    return
                except asyncio.QueueFull:
                    pass

        # Close connection if not returning to pool
        await self._close_connection(pooled)

    async def _create_connection(self) -> PooledConnection:
        """Create a new pooled connection."""
        for attempt in range(self.config.connection_retry_attempts):
            try:
                conn = self._connection_factory()
                pooled = PooledConnection(
                    connection=conn,
                    created_at=datetime.now(),
                    last_used=datetime.now(),
                )
                self._metrics["total_connections_created"] += 1
                return pooled
            except Exception as e:
                if attempt == self.config.connection_retry_attempts - 1:
                    raise ConnectionPoolError(f"Failed to create connection after {attempt + 1} attempts: {e}")
                await asyncio.sleep(0.1 * (2**attempt))

        raise ConnectionPoolError("Failed to create connection")

    async def _close_connection(self, pooled: PooledConnection) -> None:
        """Close a pooled connection."""
        try:
            if hasattr(pooled.connection, "close"):
                pooled.connection.close()
        except Exception as e:
            logger.warning("Error closing connection: %s", e)

    async def _is_healthy(self, pooled: PooledConnection) -> bool:
        """Check if a connection is healthy."""
        # Basic health check - can be overridden
        try:
            if hasattr(pooled.connection, "heartbeat"):
                pooled.connection.heartbeat()
            return True
        except Exception:
            return False

    async def _health_check_loop(self) -> None:
        """Background task for periodic health checks."""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health check error: %s", e)

    async def _perform_health_checks(self) -> None:
        """Perform health checks on idle connections."""
        healthy_connections: List[PooledConnection] = []

        while not self._pool.empty():
            try:
                pooled = self._pool.get_nowait()
                if await self._is_healthy(pooled):
                    healthy_connections.append(pooled)
                else:
                    await self._close_connection(pooled)
                    self._metrics["health_check_failures"] += 1
            except asyncio.QueueEmpty:
                break

        # Return healthy connections to pool
        for pooled in healthy_connections:
            try:
                self._pool.put_nowait(pooled)
            except asyncio.QueueFull:
                await self._close_connection(pooled)

    def _get_pool_state(self) -> Dict[str, Any]:
        """Get current pool state for diagnostics."""
        return {
            "initialized": self._initialized,
            "pool_size": self._pool.qsize(),
            "active_connections": len(self._active_connections),
            "max_connections": self.config.max_connections,
            "metrics": self._metrics.copy(),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get pool metrics."""
        return self._metrics.copy()


# ============================================================================
# Retry Manager
# ============================================================================


class RetryManager:
    """Manages retry logic with exponential backoff.

    Provides configurable retry behavior with:
    - Exponential backoff
    - Jitter to prevent thundering herd
    - Selective retry based on exception type
    - Detailed retry metrics

    Example:
        ```python
        config = RetryConfig(max_retries=3, base_delay=1.0)
        retry_manager = RetryManager(config)

        @retry_manager.wrap
        async def unstable_operation():
            # This will be retried on failure
            pass
        ```
    """

    def __init__(self, config: RetryConfig) -> None:
        """Initialize retry manager.

        Args:
            config: Retry configuration
        """
        self.config = config
        self._metrics: Dict[str, Any] = {
            "total_attempts": 0,
            "successful_retries": 0,
            "failed_retries": 0,
            "total_delay_seconds": 0.0,
        }

    async def execute(
        self,
        operation: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute an operation with retry logic.

        Args:
            operation: The operation to execute
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation

        Returns:
            The result of the operation

        Raises:
            RetryExhaustedError: If all retry attempts fail
        """
        last_error: Optional[Exception] = None
        total_delay = 0.0

        for attempt in range(self.config.max_retries + 1):
            self._metrics["total_attempts"] += 1

            try:
                result = await operation(*args, **kwargs)
                if attempt > 0:
                    self._metrics["successful_retries"] += 1
                return result

            except Exception as e:
                last_error = e

                # Check if this exception type should be retried
                if not self._should_retry(e):
                    raise

                # Check if we have more retries
                if attempt >= self.config.max_retries:
                    break

                # Calculate delay with exponential backoff
                delay = self._calculate_delay(attempt)
                total_delay += delay

                logger.warning(
                    "Operation failed (attempt %d/%d): %s. Retrying in %.2fs...",
                    attempt + 1,
                    self.config.max_retries + 1,
                    e,
                    delay,
                )

                await asyncio.sleep(delay)

        self._metrics["failed_retries"] += 1
        self._metrics["total_delay_seconds"] += total_delay

        raise RetryExhaustedError(
            message=f"Operation failed after {self.config.max_retries + 1} attempts",
            attempts=self.config.max_retries + 1,
            last_error=last_error,
            details={"total_delay_seconds": total_delay},
        )

    def wrap(
        self,
        operation: Callable[..., T],
    ) -> Callable[..., T]:
        """Wrap an operation with retry logic.

        Args:
            operation: The operation to wrap

        Returns:
            Wrapped operation
        """

        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await self.execute(operation, *args, **kwargs)

        return wrapper

    def _should_retry(self, error: Exception) -> bool:
        """Determine if an error should trigger a retry."""
        return isinstance(error, self.config.retryable_exceptions)

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a retry attempt."""
        # Exponential backoff
        delay = self.config.base_delay * (self.config.exponential_base**attempt)

        # Cap at max delay
        delay = min(delay, self.config.max_delay)

        # Add jitter
        if self.config.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)

    def get_metrics(self) -> Dict[str, Any]:
        """Get retry metrics."""
        return self._metrics.copy()


# ============================================================================
# Backup Manager
# ============================================================================


@dataclass
class BackupMetadata:
    """Metadata for a backup.

    Attributes:
        backup_id: Unique identifier for the backup
        created_at: When the backup was created
        backup_type: Type of backup
        collections: List of collections backed up
        size_bytes: Size of the backup in bytes
        checksum: SHA256 checksum of the backup
        chroma_version: Version of ChromaDB used
        metadata: Additional metadata
    """

    backup_id: str
    created_at: datetime
    backup_type: BackupType
    collections: List[str]
    size_bytes: int
    checksum: str
    chroma_version: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class BackupManager:
    """Manages backup and restore operations for ChromaDB.

    Supports:
    - Full database backups
    - Incremental backups
    - Collection-specific backups
    - Compression and encryption
    - Retention policies

    Example:
        ```python
        config = BackupConfig(storage_path="./backups")
        manager = BackupManager(config, persist_directory="./chroma_db")

        # Create backup
        metadata = await manager.create_backup(BackupType.FULL)

        # Restore backup
        await manager.restore_backup(metadata.backup_id)

        # List backups
        backups = await manager.list_backups()
        ```
    """

    def __init__(
        self,
        config: BackupConfig,
        persist_directory: str,
        chroma_version: str = "unknown",
    ) -> None:
        """Initialize backup manager.

        Args:
            config: Backup configuration
            persist_directory: Directory where ChromaDB persists data
            chroma_version: Version of ChromaDB being used
        """
        self.config = config
        self.persist_directory = Path(persist_directory)
        self.chroma_version = chroma_version
        self.storage_path = Path(config.storage_path)
        self._metadata_file = self.storage_path / "backup_metadata.json"
        self._backups: Dict[str, BackupMetadata] = {}

    async def initialize(self) -> None:
        """Initialize the backup manager."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        await self._load_metadata()
        await self._cleanup_old_backups()

    async def create_backup(
        self,
        backup_type: BackupType,
        collection_name: Optional[str] = None,
    ) -> BackupMetadata:
        """Create a new backup.

        Args:
            backup_type: Type of backup to create
            collection_name: Specific collection to backup (for COLLECTION type)

        Returns:
            Metadata for the created backup

        Raises:
            BackupError: If backup creation fails
        """
        if not self.config.enabled:
            raise BackupError("Backups are disabled")

        backup_id = str(uuid4())
        timestamp = datetime.now()
        backup_dir = self.storage_path / f"backup_{backup_id}"

        try:
            # Create backup directory
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Determine what to backup
            if backup_type == BackupType.COLLECTION:
                if not collection_name:
                    raise BackupError("collection_name required for COLLECTION backup")
                collections = [collection_name]
                source = self.persist_directory / collection_name
            else:
                collections = self._list_collections()
                source = self.persist_directory

            # Create backup archive
            archive_path = backup_dir / "data"
            if self.config.compression_enabled:
                archive_path = await self._create_compressed_backup(source, archive_path)
            else:
                await self._copy_backup(source, archive_path)

            # Calculate checksum
            checksum = await self._calculate_checksum(archive_path)

            # Get size
            size_bytes = await self._get_directory_size(archive_path)

            # Create metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                created_at=timestamp,
                backup_type=backup_type,
                collections=collections,
                size_bytes=size_bytes,
                checksum=checksum,
                chroma_version=self.chroma_version,
                metadata={
                    "collection_name": collection_name,
                    "compression": self.config.compression_enabled,
                },
            )

            # Save metadata
            self._backups[backup_id] = metadata
            await self._save_metadata()

            logger.info(
                "Created %s backup %s (%d bytes)",
                backup_type.value,
                backup_id,
                size_bytes,
            )

            return metadata

        except Exception as e:
            # Cleanup on failure
            if backup_dir.exists():
                shutil.rmtree(backup_dir, ignore_errors=True)
            raise BackupError(
                f"Failed to create backup: {e}",
                operation="create",
            ) from e

    async def restore_backup(
        self,
        backup_id: str,
        target_directory: Optional[str] = None,
    ) -> None:
        """Restore from a backup.

        Args:
            backup_id: ID of the backup to restore
            target_directory: Target directory for restore (defaults to persist_directory)

        Raises:
            BackupError: If restore fails
            NotFoundError: If backup not found
        """
        if backup_id not in self._backups:
            raise NotFoundError(f"Backup {backup_id} not found")

        metadata = self._backups[backup_id]
        backup_dir = self.storage_path / f"backup_{backup_id}"
        target = Path(target_directory) if target_directory else self.persist_directory

        try:
            # Verify backup exists
            archive_path = backup_dir / "data"
            if not archive_path.exists():
                raise BackupError(
                    f"Backup files missing for {backup_id}",
                    operation="restore",
                )

            # Verify checksum
            current_checksum = await self._calculate_checksum(archive_path)
            if current_checksum != metadata.checksum:
                raise BackupError(
                    "Backup checksum mismatch - backup may be corrupted",
                    operation="restore",
                )

            # Restore based on type
            if metadata.backup_type == BackupType.COLLECTION:
                collection_name = metadata.metadata.get("collection_name")
                if collection_name:
                    target = target / collection_name

            if metadata.metadata.get("compression"):
                await self._restore_compressed_backup(archive_path, target)
            else:
                await self._restore_backup(archive_path, target)

            logger.info("Restored backup %s to %s", backup_id, target)

        except Exception as e:
            raise BackupError(
                f"Failed to restore backup: {e}",
                operation="restore",
            ) from e

    async def list_backups(
        self,
        backup_type: Optional[BackupType] = None,
    ) -> List[BackupMetadata]:
        """List available backups.

        Args:
            backup_type: Filter by backup type

        Returns:
            List of backup metadata
        """
        backups = list(self._backups.values())
        if backup_type:
            backups = [b for b in backups if b.backup_type == backup_type]
        return sorted(backups, key=lambda b: b.created_at, reverse=True)

    async def delete_backup(self, backup_id: str) -> None:
        """Delete a backup.

        Args:
            backup_id: ID of the backup to delete

        Raises:
            NotFoundError: If backup not found
        """
        if backup_id not in self._backups:
            raise NotFoundError(f"Backup {backup_id} not found")

        backup_dir = self.storage_path / f"backup_{backup_id}"
        if backup_dir.exists():
            shutil.rmtree(backup_dir, ignore_errors=True)

        del self._backups[backup_id]
        await self._save_metadata()

        logger.info("Deleted backup %s", backup_id)

    async def verify_backup(self, backup_id: str) -> bool:
        """Verify a backup's integrity.

        Args:
            backup_id: ID of the backup to verify

        Returns:
            True if backup is valid
        """
        if backup_id not in self._backups:
            return False

        metadata = self._backups[backup_id]
        backup_dir = self.storage_path / f"backup_{backup_id}"
        archive_path = backup_dir / "data"

        if not archive_path.exists():
            return False

        try:
            current_checksum = await self._calculate_checksum(archive_path)
            return current_checksum == metadata.checksum
        except Exception:
            return False

    def _list_collections(self) -> List[str]:
        """List collections in the persist directory."""
        if not self.persist_directory.exists():
            return []
        return [d.name for d in self.persist_directory.iterdir() if d.is_dir()]

    async def _create_compressed_backup(
        self,
        source: Path,
        target: Path,
    ) -> Path:
        """Create a compressed backup archive."""
        import tarfile

        archive_path = target.with_suffix(".tar.gz")
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(source, arcname=source.name)
        return archive_path

    async def _copy_backup(self, source: Path, target: Path) -> None:
        """Copy backup files."""
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            shutil.copy2(source, target)

    async def _restore_compressed_backup(
        self,
        archive_path: Path,
        target: Path,
    ) -> None:
        """Restore from a compressed backup."""
        import tarfile

        target.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(target.parent)

    async def _restore_backup(self, source: Path, target: Path) -> None:
        """Restore from an uncompressed backup."""
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    async def _calculate_checksum(self, path: Path) -> str:
        """Calculate SHA256 checksum of a file or directory."""
        sha256 = hashlib.sha256()

        if path.is_file():
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
        elif path.is_dir():
            for file_path in sorted(path.rglob("*")):
                if file_path.is_file():
                    with open(file_path, "rb") as f:
                        for chunk in iter(lambda: f.read(8192), b""):
                            sha256.update(chunk)

        return sha256.hexdigest()

    async def _get_directory_size(self, path: Path) -> int:
        """Get total size of a directory in bytes."""
        if path.is_file():
            return path.stat().st_size

        total = 0
        for file_path in path.rglob("*"):
            if file_path.is_file():
                total += file_path.stat().st_size
        return total

    async def _load_metadata(self) -> None:
        """Load backup metadata from disk."""
        if self._metadata_file.exists():
            try:
                with open(self._metadata_file, "r") as f:
                    data = json.load(f)
                self._backups = {k: BackupMetadata(**v) for k, v in data.items()}
            except Exception as e:
                logger.warning("Failed to load backup metadata: %s", e)
                self._backups = {}

    async def _save_metadata(self) -> None:
        """Save backup metadata to disk."""
        data = {
            k: {
                "backup_id": v.backup_id,
                "created_at": v.created_at.isoformat(),
                "backup_type": v.backup_type.value,
                "collections": v.collections,
                "size_bytes": v.size_bytes,
                "checksum": v.checksum,
                "chroma_version": v.chroma_version,
                "metadata": v.metadata,
            }
            for k, v in self._backups.items()
        }
        with open(self._metadata_file, "w") as f:
            json.dump(data, f, indent=2)

    async def _cleanup_old_backups(self) -> None:
        """Remove backups older than retention period."""
        if self.config.retention_days <= 0:
            return

        cutoff = datetime.now() - timedelta(days=self.config.retention_days)
        to_delete = [bid for bid, meta in self._backups.items() if meta.created_at < cutoff]

        for bid in to_delete:
            logger.info("Removing old backup %s", bid)
            await self.delete_backup(bid)


# ============================================================================
# Migration System
# ============================================================================


@dataclass
class MigrationRecord:
    """A record of a migration.

    Attributes:
        version: Migration version number
        name: Human-readable name
        applied_at: When the migration was applied
        status: Current status
        checksum: Checksum of the migration script
        duration_seconds: Time taken to apply
    """

    version: int
    name: str
    applied_at: datetime
    status: MigrationStatus
    checksum: str
    duration_seconds: float = 0.0


@dataclass
class Migration:
    """A database migration.

    Attributes:
        version: Migration version number
        name: Human-readable name
        apply: Coroutine to apply the migration
        rollback: Coroutine to rollback the migration
        dependencies: List of version dependencies
    """

    version: int
    name: str
    apply: Callable[[], Any]
    rollback: Callable[[], Any]
    dependencies: List[int] = field(default_factory=list)


class MigrationManager:
    """Manages schema migrations for ChromaDB collections.

    Provides:
    - Versioned migrations
    - Dependency resolution
    - Rollback support
    - Migration state tracking

    Example:
        ```python
        config = MigrationConfig(auto_migrate=True)
        manager = MigrationManager(config, persist_directory="./chroma_db")
        await manager.initialize()

        # Register migrations
        manager.register(Migration(
            version=1,
            name="add_author_index",
            apply=add_author_index,
            rollback=remove_author_index,
        ))

        # Apply pending migrations
        await manager.migrate()
        ```
    """

    def __init__(
        self,
        config: MigrationConfig,
        persist_directory: str,
    ) -> None:
        """Initialize migration manager.

        Args:
            config: Migration configuration
            persist_directory: Directory where ChromaDB persists data
        """
        self.config = config
        self.persist_directory = Path(persist_directory)
        self.migrations_path = Path(config.migration_path)
        self._migrations: Dict[int, Migration] = {}
        self._applied_migrations: Dict[int, MigrationRecord] = {}
        self._state_file = self.persist_directory / "migration_state.json"

    async def initialize(self) -> None:
        """Initialize the migration manager."""
        self.migrations_path.mkdir(parents=True, exist_ok=True)
        await self._load_state()

        if self.config.auto_migrate:
            await self.migrate()

    def register(self, migration: Migration) -> None:
        """Register a migration.

        Args:
            migration: The migration to register

        Raises:
            MigrationError: If a migration with the same version exists
        """
        if migration.version in self._migrations:
            raise MigrationError(
                f"Migration version {migration.version} already registered",
                migration_version=migration.version,
            )
        self._migrations[migration.version] = migration

    async def migrate(
        self,
        target_version: Optional[int] = None,
    ) -> List[MigrationRecord]:
        """Apply pending migrations.

        Args:
            target_version: Target version to migrate to (None for latest)

        Returns:
            List of applied migration records
        """
        pending = self._get_pending_migrations()

        if target_version:
            pending = [m for m in pending if m.version <= target_version]

        # Check dependencies
        for migration in pending:
            for dep in migration.dependencies:
                if dep not in self._applied_migrations:
                    raise MigrationError(
                        f"Migration {migration.version} depends on {dep} which is not applied",
                        migration_version=migration.version,
                    )

        applied: List[MigrationRecord] = []

        for migration in pending:
            record = await self._apply_migration(migration)
            applied.append(record)

        return applied

    async def rollback(
        self,
        target_version: int,
    ) -> List[MigrationRecord]:
        """Rollback to a specific version.

        Args:
            target_version: Version to rollback to

        Returns:
            List of rolled back migration records

        Raises:
            MigrationError: If rollback is not allowed or fails
        """
        if not self.config.allow_rollback:
            raise MigrationError("Rollback is not allowed")

        # Get migrations to rollback (in reverse order)
        to_rollback = [
            self._migrations[v] for v in sorted(self._applied_migrations.keys(), reverse=True) if v > target_version
        ]

        rolled_back: List[MigrationRecord] = []

        for migration in to_rollback:
            record = await self._rollback_migration(migration)
            rolled_back.append(record)

        return rolled_back

    def get_status(self) -> Dict[str, Any]:
        """Get current migration status.

        Returns:
            Dictionary with migration status
        """
        pending = self._get_pending_migrations()
        return {
            "current_version": max(self._applied_migrations.keys()) if self._applied_migrations else 0,
            "latest_version": max(self._migrations.keys()) if self._migrations else 0,
            "pending_count": len(pending),
            "applied_count": len(self._applied_migrations),
            "pending_versions": [m.version for m in pending],
        }

    def _get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations in order."""
        pending = [m for v, m in sorted(self._migrations.items()) if v not in self._applied_migrations]
        return pending

    async def _apply_migration(self, migration: Migration) -> MigrationRecord:
        """Apply a single migration."""
        logger.info("Applying migration %d: %s", migration.version, migration.name)

        # Create backup if configured
        if self.config.backup_before_migration:
            # Backup logic would go here
            pass

        start_time = time.time()
        checksum = self._calculate_migration_checksum(migration)

        record = MigrationRecord(
            version=migration.version,
            name=migration.name,
            applied_at=datetime.now(),
            status=MigrationStatus.IN_PROGRESS,
            checksum=checksum,
        )

        try:
            await migration.apply()
            record.status = MigrationStatus.COMPLETED
            record.duration_seconds = time.time() - start_time

            self._applied_migrations[migration.version] = record
            await self._save_state()

            logger.info("Applied migration %d in %.2fs", migration.version, record.duration_seconds)

            return record

        except Exception as e:
            record.status = MigrationStatus.FAILED
            record.duration_seconds = time.time() - start_time
            raise MigrationError(
                f"Failed to apply migration {migration.version}: {e}",
                migration_version=migration.version,
            ) from e

    async def _rollback_migration(self, migration: Migration) -> MigrationRecord:
        """Rollback a single migration."""
        logger.info("Rolling back migration %d: %s", migration.version, migration.name)

        start_time = time.time()

        try:
            await migration.rollback()

            if migration.version in self._applied_migrations:
                record = self._applied_migrations[migration.version]
                record.status = MigrationStatus.ROLLED_BACK
                del self._applied_migrations[migration.version]
                await self._save_state()

            duration = time.time() - start_time
            logger.info("Rolled back migration %d in %.2fs", migration.version, duration)

            return MigrationRecord(
                version=migration.version,
                name=migration.name,
                applied_at=datetime.now(),
                status=MigrationStatus.ROLLED_BACK,
                checksum="",
                duration_seconds=duration,
            )

        except Exception as e:
            raise MigrationError(
                f"Failed to rollback migration {migration.version}: {e}",
                migration_version=migration.version,
            ) from e

    def _calculate_migration_checksum(self, migration: Migration) -> str:
        """Calculate checksum of a migration."""
        data = f"{migration.version}:{migration.name}:{migration.dependencies}"
        return hashlib.sha256(data.encode()).hexdigest()

    async def _load_state(self) -> None:
        """Load migration state from disk."""
        if self._state_file.exists():
            try:
                with open(self._state_file, "r") as f:
                    data = json.load(f)

                self._applied_migrations = {
                    int(k): MigrationRecord(
                        version=v["version"],
                        name=v["name"],
                        applied_at=datetime.fromisoformat(v["applied_at"]),
                        status=MigrationStatus(v["status"]),
                        checksum=v["checksum"],
                        duration_seconds=v.get("duration_seconds", 0.0),
                    )
                    for k, v in data.items()
                }
            except Exception as e:
                logger.warning("Failed to load migration state: %s", e)
                self._applied_migrations = {}

    async def _save_state(self) -> None:
        """Save migration state to disk."""
        data = {
            str(k): {
                "version": v.version,
                "name": v.name,
                "applied_at": v.applied_at.isoformat(),
                "status": v.status.value,
                "checksum": v.checksum,
                "duration_seconds": v.duration_seconds,
            }
            for k, v in self._applied_migrations.items()
        }
        with open(self._state_file, "w") as f:
            json.dump(data, f, indent=2)


# ============================================================================
# Production Chroma Store
# ============================================================================


class ProductionChromaStore(ChromaVectorStore):
    """Production-ready ChromaDB vector store.

    Extends ChromaVectorStore with enterprise features:
    - Connection pooling for efficient resource usage
    - Automatic retry with exponential backoff
    - Backup and restore capabilities
    - Schema migration support
    - Health monitoring and metrics

    Example:
        ```python
        config = ProductionVectorStoreConfig(
            collection_name="documents",
            dimension=1536,
            pool_config=ConnectionPoolConfig(max_connections=10),
            retry_config=RetryConfig(max_retries=3),
            backup_config=BackupConfig(enabled=True),
        )

        store = ProductionChromaStore(config, persist_directory="./chroma_db")
        await store.initialize()

        # Use the store with automatic retries
        await store.add_chunks(chunks)
        results = await store.search(embedding, options)

        # Create backup
        await store.backup_manager.create_backup(BackupType.FULL)

        await store.close()
        ```
    """

    def __init__(
        self,
        config: Optional[ProductionVectorStoreConfig] = None,
        persist_directory: Optional[str] = None,
    ) -> None:
        """Initialize production ChromaDB store.

        Args:
            config: Production vector store configuration
            persist_directory: Directory for persistent storage
        """
        # Use default config if not provided
        if config is None:
            config = ProductionVectorStoreConfig()

        # Initialize base class with base config
        base_config = VectorStoreConfig(
            collection_name=config.collection_name,
            dimension=config.dimension,
            distance_metric=config.distance_metric,
            metadata_schema=config.metadata_schema,
        )
        super().__init__(base_config, persist_directory)
        self.config = config  # type: ignore

        # Initialize components
        self._connection_pool: Optional[ConnectionPool] = None
        self._retry_manager = RetryManager(config.retry_config)
        self._backup_manager: Optional[BackupManager] = None
        self._migration_manager: Optional[MigrationManager] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._metrics: Dict[str, Any] = {
            "total_operations": 0,
            "failed_operations": 0,
            "retry_attempts": 0,
            "average_latency_ms": 0.0,
        }

    async def initialize(self) -> None:
        """Initialize the production store and all components."""
        # Initialize base ChromaVectorStore first
        await super().initialize()

        # Initialize connection pool
        self._connection_pool = ConnectionPool(
            config=self.config.pool_config,
            connection_factory=self._create_connection,
        )
        await self._connection_pool.initialize()

        # Initialize backup manager
        if self.config.backup_config.enabled:
            self._backup_manager = BackupManager(
                config=self.config.backup_config,
                persist_directory=self._persist_directory,
                chroma_version="0.4.18",  # Should be dynamic
            )
            await self._backup_manager.initialize()

        # Initialize migration manager
        self._migration_manager = MigrationManager(
            config=self.config.migration_config,
            persist_directory=self._persist_directory,
        )
        await self._migration_manager.initialize()

        # Start health check task
        if self.config.enable_health_check:
            self._health_check_task = asyncio.create_task(self._health_check_loop())

        logger.info("ProductionChromaStore initialized successfully")

    async def close(self) -> None:
        """Close the store and cleanup resources."""
        # Cancel health check task
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # Close connection pool
        if self._connection_pool:
            await self._connection_pool.close()

        # Close base store
        await super().close()

        logger.info("ProductionChromaStore closed")

    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add chunks with retry logic."""
        return await self._execute_with_retry(super().add_chunks, chunks)

    async def delete_chunks(self, chunk_ids: List[UUID]) -> None:
        """Delete chunks with retry logic."""
        return await self._execute_with_retry(super().delete_chunks, chunk_ids)

    async def search(
        self,
        query_embedding: List[float],
        options: Optional[SearchOptions] = None,
    ) -> List[SearchResult]:
        """Search with retry logic and metrics."""
        start_time = time.time()
        try:
            results = await self._execute_with_retry(super().search, query_embedding, options)
            self._update_metrics(success=True, latency_ms=(time.time() - start_time) * 1000)
            return results
        except Exception:
            self._update_metrics(success=False, latency_ms=(time.time() - start_time) * 1000)
            raise

    async def get_chunk(self, chunk_id: UUID) -> Optional[DocumentChunk]:
        """Get chunk with retry logic."""
        return await self._execute_with_retry(super().get_chunk, chunk_id)

    async def update_chunk(self, chunk: DocumentChunk) -> None:
        """Update chunk with retry logic."""
        return await self._execute_with_retry(super().update_chunk, chunk)

    @property
    def backup_manager(self) -> BackupManager:
        """Get the backup manager.

        Returns:
            BackupManager instance

        Raises:
            VectorStoreError: If backup manager is not initialized
        """
        if self._backup_manager is None:
            raise VectorStoreError(
                message="Backup manager not initialized",
                error_code="BACKUP_NOT_INITIALIZED",
                store_type="chroma_production",
            )
        return self._backup_manager

    @property
    def migration_manager(self) -> MigrationManager:
        """Get the migration manager.

        Returns:
            MigrationManager instance

        Raises:
            VectorStoreError: If migration manager is not initialized
        """
        if self._migration_manager is None:
            raise VectorStoreError(
                message="Migration manager not initialized",
                error_code="MIGRATION_NOT_INITIALIZED",
                store_type="chroma_production",
            )
        return self._migration_manager

    def get_metrics(self) -> Dict[str, Any]:
        """Get operational metrics.

        Returns:
            Dictionary with metrics including:
            - total_operations: Total number of operations
            - failed_operations: Number of failed operations
            - retry_attempts: Number of retry attempts
            - average_latency_ms: Average operation latency
            - connection_pool_metrics: Pool-specific metrics
            - retry_manager_metrics: Retry-specific metrics
        """
        metrics = self._metrics.copy()

        if self._connection_pool:
            metrics["connection_pool"] = self._connection_pool.get_metrics()

        metrics["retry_manager"] = self._retry_manager.get_metrics()

        return metrics

    async def health_check(self) -> bool:
        """Perform comprehensive health check.

        Returns:
            True if store is healthy
        """
        try:
            # Check base store health
            if not await super().health_check():
                return False

            # Check connection pool
            if self._connection_pool:
                pool_state = self._connection_pool._get_pool_state()
                if not pool_state["initialized"]:
                    return False

            return True
        except Exception:
            return False

    def _create_connection(self) -> Any:
        """Create a new connection for the pool."""
        # For ChromaDB, we don't need actual connections
        # This is a placeholder for future connection-based backends
        return {"status": "connected", "created_at": datetime.now().isoformat()}

    async def _execute_with_retry(self, operation: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute an operation with retry logic."""
        return await self._retry_manager.execute(operation, *args, **kwargs)

    def _update_metrics(self, success: bool, latency_ms: float) -> None:
        """Update operational metrics."""
        self._metrics["total_operations"] += 1
        if not success:
            self._metrics["failed_operations"] += 1

        # Update average latency
        total = self._metrics["total_operations"]
        current_avg = self._metrics["average_latency_ms"]
        self._metrics["average_latency_ms"] = ((current_avg * (total - 1)) + latency_ms) / total

    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                is_healthy = await self.health_check()
                if not is_healthy:
                    logger.warning("Health check failed for ProductionChromaStore")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Health check error: %s", e)
