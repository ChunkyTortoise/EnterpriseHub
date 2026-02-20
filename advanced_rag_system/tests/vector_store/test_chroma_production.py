"""Tests for production ChromaDB vector store."""

import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
from src.core.exceptions import NotFoundError, VectorStoreError
from src.core.types import DocumentChunk, Metadata
from src.vector_store.base import SearchOptions
from src.vector_store.chroma_production import (
    BackupConfig,
    BackupManager,
    BackupType,
    ConnectionPool,
    ConnectionPoolConfig,
    ConnectionPoolError,
    Migration,
    MigrationConfig,
    MigrationManager,
    MigrationStatus,
    ProductionChromaStore,
    ProductionVectorStoreConfig,
    RetryableError,
    RetryConfig,
    RetryExhaustedError,
    RetryManager,
)


@pytest.mark.integration

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
async def production_store(temp_dir):
    """Create and initialize production ChromaDB store."""
    config = ProductionVectorStoreConfig(
        collection_name="test_production",
        dimension=3,
        distance_metric="cosine",
        pool_config=ConnectionPoolConfig(min_connections=1, max_connections=3),
        retry_config=RetryConfig(max_retries=2, base_delay=0.1),
        backup_config=BackupConfig(enabled=True, storage_path=f"{temp_dir}/backups"),
        migration_config=MigrationConfig(auto_migrate=False),
    )
    store = ProductionChromaStore(config, persist_directory=temp_dir)
    await store.initialize()
    yield store
    await store.close()


@pytest.fixture
def retry_manager():
    """Create retry manager for tests."""
    config = RetryConfig(
        max_retries=2,
        base_delay=0.1,
        max_delay=1.0,
        retryable_exceptions=(RetryableError,),
    )
    return RetryManager(config)


@pytest.fixture
def connection_pool():
    """Create connection pool for tests."""
    config = ConnectionPoolConfig(
        min_connections=1,
        max_connections=3,
        connection_timeout=1.0,
    )

    def factory():
        return {"status": "connected"}

    return ConnectionPool(config, factory)


# ============================================================================
# ProductionChromaStore Tests
# ============================================================================


class TestProductionChromaStore:
    """Test cases for ProductionChromaStore."""

    @pytest.mark.asyncio
    async def test_initialization(self, temp_dir):
        """Test store initialization."""
        config = ProductionVectorStoreConfig(collection_name="test_init")
        store = ProductionChromaStore(config, persist_directory=temp_dir)
        await store.initialize()

        assert store._initialized is True
        assert store._connection_pool is not None
        assert store._retry_manager is not None

        await store.close()

    @pytest.mark.asyncio
    async def test_add_chunks_with_retry(self, production_store):
        """Test adding chunks with automatic retry."""
        chunks = [
            DocumentChunk(
                document_id=uuid4(),
                content="Test content",
                embedding=[0.1, 0.2, 0.3],
                metadata=Metadata(title="Test"),
            )
        ]

        await production_store.add_chunks(chunks)
        count = await production_store.count()
        assert count == 1

    @pytest.mark.asyncio
    async def test_search_with_retry(self, production_store):
        """Test search with automatic retry."""
        # Add test chunk
        chunk = DocumentChunk(
            document_id=uuid4(),
            content="Python programming",
            embedding=[1.0, 0.0, 0.0],
        )
        await production_store.add_chunks([chunk])

        # Search
        results = await production_store.search(
            query_embedding=[0.9, 0.1, 0.0],
            options=SearchOptions(top_k=5),
        )

        assert len(results) == 1
        assert results[0].chunk.content == "Python programming"

    @pytest.mark.asyncio
    async def test_delete_chunks_with_retry(self, production_store):
        """Test deleting chunks with automatic retry."""
        chunk = DocumentChunk(
            document_id=uuid4(),
            content="To be deleted",
            embedding=[0.1, 0.2, 0.3],
        )
        await production_store.add_chunks([chunk])
        assert await production_store.count() == 1

        await production_store.delete_chunks([chunk.id])
        assert await production_store.count() == 0

    @pytest.mark.asyncio
    async def test_get_metrics(self, production_store):
        """Test getting store metrics."""
        # Perform some operations
        chunk = DocumentChunk(
            document_id=uuid4(),
            content="Test",
            embedding=[0.1, 0.2, 0.3],
        )
        await production_store.add_chunks([chunk])
        await production_store.search(
            query_embedding=[0.1, 0.2, 0.3],
            options=SearchOptions(top_k=5),
        )

        metrics = production_store.get_metrics()

        assert "total_operations" in metrics
        assert metrics["total_operations"] > 0
        assert "retry_manager" in metrics
        assert "average_latency_ms" in metrics

    @pytest.mark.asyncio
    async def test_health_check(self, production_store):
        """Test health check functionality."""
        is_healthy = await production_store.health_check()
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_backup_manager_property(self, production_store):
        """Test backup manager property."""
        manager = production_store.backup_manager
        assert manager is not None
        assert isinstance(manager, BackupManager)

    @pytest.mark.asyncio
    async def test_migration_manager_property(self, production_store):
        """Test migration manager property."""
        manager = production_store.migration_manager
        assert manager is not None
        assert isinstance(manager, MigrationManager)

    @pytest.mark.asyncio
    async def test_backup_manager_not_initialized(self, temp_dir):
        """Test backup manager when not initialized."""
        config = ProductionVectorStoreConfig(
            collection_name="test",
            backup_config=BackupConfig(enabled=False),
        )
        store = ProductionChromaStore(config, persist_directory=temp_dir)
        await store.initialize()

        with pytest.raises(VectorStoreError) as exc_info:
            _ = store.backup_manager
        assert exc_info.value.error_code == "BACKUP_NOT_INITIALIZED"

        await store.close()


# ============================================================================
# RetryManager Tests
# ============================================================================


class TestRetryManager:
    """Test cases for RetryManager."""

    @pytest.mark.asyncio
    async def test_successful_operation(self, retry_manager):
        """Test operation that succeeds immediately."""

        async def operation():
            return "success"

        result = await retry_manager.execute(operation)
        assert result == "success"

        metrics = retry_manager.get_metrics()
        assert metrics["total_attempts"] == 1
        assert metrics["successful_retries"] == 0

    @pytest.mark.asyncio
    async def test_retry_then_success(self, retry_manager):
        """Test operation that fails then succeeds."""
        attempts = 0

        async def operation():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise RetryableError("Temporary failure")
            return "success"

        result = await retry_manager.execute(operation)
        assert result == "success"
        assert attempts == 2

        metrics = retry_manager.get_metrics()
        assert metrics["total_attempts"] == 2
        assert metrics["successful_retries"] == 1

    @pytest.mark.asyncio
    async def test_retry_exhausted(self, retry_manager):
        """Test operation that always fails."""

        async def operation():
            raise RetryableError("Persistent failure")

        with pytest.raises(RetryExhaustedError) as exc_info:
            await retry_manager.execute(operation)

        assert exc_info.value.attempts == 3  # Initial + 2 retries
        assert "Persistent failure" in str(exc_info.value.last_error)

    @pytest.mark.asyncio
    async def test_non_retryable_error(self, retry_manager):
        """Test that non-retryable errors are not retried."""

        async def operation():
            raise ValueError("Non-retryable")

        with pytest.raises(ValueError):
            await retry_manager.execute(operation)

        metrics = retry_manager.get_metrics()
        assert metrics["total_attempts"] == 1  # No retries

    @pytest.mark.asyncio
    async def test_wrap_decorator(self, retry_manager):
        """Test wrap decorator."""
        attempts = 0

        @retry_manager.wrap
        async def operation():
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise RetryableError("Temporary")
            return "wrapped"

        result = await operation()
        assert result == "wrapped"
        assert attempts == 2


# ============================================================================
# ConnectionPool Tests
# ============================================================================


class TestConnectionPool:
    """Test cases for ConnectionPool."""

    @pytest.mark.asyncio
    async def test_initialization(self, connection_pool):
        """Test pool initialization."""
        await connection_pool.initialize()
        assert connection_pool._initialized is True
        assert connection_pool._pool.qsize() == 1  # min_connections

        await connection_pool.close()

    @pytest.mark.asyncio
    async def test_acquire_and_release(self, connection_pool):
        """Test acquiring and releasing connections."""
        await connection_pool.initialize()

        # Acquire connection
        conn = await connection_pool.acquire()
        assert conn is not None
        assert conn.use_count == 1

        # Release connection
        await connection_pool.release(conn)

        await connection_pool.close()

    @pytest.mark.asyncio
    async def test_acquire_timeout(self):
        """Test acquire timeout."""
        config = ConnectionPoolConfig(
            min_connections=0,
            max_connections=1,
            connection_timeout=0.1,
        )

        def factory():
            # Slow factory
            import time

            time.sleep(1)
            return {"status": "connected"}

        pool = ConnectionPool(config, factory)
        await pool.initialize()

        with pytest.raises(ConnectionPoolError) as exc_info:
            await pool.acquire()

        assert "Timeout" in str(exc_info.value)

        await pool.close()

    @pytest.mark.asyncio
    async def test_get_metrics(self, connection_pool):
        """Test pool metrics."""
        await connection_pool.initialize()

        # Acquire and release to generate metrics
        conn = await connection_pool.acquire()
        await connection_pool.release(conn)

        metrics = connection_pool.get_metrics()
        assert "total_connections_created" in metrics
        assert "total_connections_reused" in metrics

        await connection_pool.close()


# ============================================================================
# BackupManager Tests
# ============================================================================


class TestBackupManager:
    """Test cases for BackupManager."""

    @pytest.fixture
    async def backup_manager(self, temp_dir):
        """Create backup manager."""
        config = BackupConfig(
            enabled=True,
            storage_path=f"{temp_dir}/backups",
            compression_enabled=False,
        )
        manager = BackupManager(
            config=config,
            persist_directory=temp_dir,
            chroma_version="0.4.18",
        )
        await manager.initialize()
        yield manager

    @pytest.mark.asyncio
    async def test_create_backup(self, backup_manager, temp_dir):
        """Test creating a backup."""
        # Create some test data
        test_file = Path(temp_dir) / "test_collection" / "data.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text('{"test": "data"}')

        metadata = await backup_manager.create_backup(BackupType.FULL)

        assert metadata.backup_id is not None
        assert metadata.backup_type == BackupType.FULL
        assert metadata.size_bytes > 0
        assert metadata.checksum is not None

    @pytest.mark.asyncio
    async def test_list_backups(self, backup_manager, temp_dir):
        """Test listing backups."""
        # Create test data and backup
        test_file = Path(temp_dir) / "test_collection" / "data.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text('{"test": "data"}')

        await backup_manager.create_backup(BackupType.FULL)
        await backup_manager.create_backup(BackupType.FULL)

        backups = await backup_manager.list_backups()
        assert len(backups) == 2

    @pytest.mark.asyncio
    async def test_delete_backup(self, backup_manager, temp_dir):
        """Test deleting a backup."""
        # Create test data and backup
        test_file = Path(temp_dir) / "test_collection" / "data.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text('{"test": "data"}')

        metadata = await backup_manager.create_backup(BackupType.FULL)
        backup_id = metadata.backup_id

        # Verify backup exists
        backups = await backup_manager.list_backups()
        assert len(backups) == 1

        # Delete backup
        await backup_manager.delete_backup(backup_id)

        # Verify backup deleted
        backups = await backup_manager.list_backups()
        assert len(backups) == 0

    @pytest.mark.asyncio
    async def test_verify_backup(self, backup_manager, temp_dir):
        """Test verifying backup integrity."""
        # Create test data and backup
        test_file = Path(temp_dir) / "test_collection" / "data.json"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text('{"test": "data"}')

        metadata = await backup_manager.create_backup(BackupType.FULL)

        is_valid = await backup_manager.verify_backup(metadata.backup_id)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_backup_not_found(self, backup_manager):
        """Test accessing non-existent backup."""
        with pytest.raises(NotFoundError):
            await backup_manager.restore_backup("non-existent-id")

    @pytest.mark.asyncio
    async def test_backups_disabled(self, temp_dir):
        """Test backup creation when disabled."""
        config = BackupConfig(enabled=False)
        manager = BackupManager(config, persist_directory=temp_dir)
        await manager.initialize()

        with pytest.raises(Exception) as exc_info:
            await manager.create_backup(BackupType.FULL)

        assert "disabled" in str(exc_info.value).lower()


# ============================================================================
# MigrationManager Tests
# ============================================================================


class TestMigrationManager:
    """Test cases for MigrationManager."""

    @pytest.fixture
    async def migration_manager(self, temp_dir):
        """Create migration manager."""
        config = MigrationConfig(auto_migrate=False)
        manager = MigrationManager(config, persist_directory=temp_dir)
        await manager.initialize()
        yield manager

    @pytest.mark.asyncio
    async def test_register_migration(self, migration_manager):
        """Test registering a migration."""

        async def apply():
            pass

        async def rollback():
            pass

        migration = Migration(
            version=1,
            name="test_migration",
            apply=apply,
            rollback=rollback,
        )

        migration_manager.register(migration)
        assert 1 in migration_manager._migrations

    @pytest.mark.asyncio
    async def test_register_duplicate_migration(self, migration_manager):
        """Test registering duplicate migration version."""

        async def apply():
            pass

        migration1 = Migration(version=1, name="first", apply=apply, rollback=apply)
        migration2 = Migration(version=1, name="second", apply=apply, rollback=apply)

        migration_manager.register(migration1)

        with pytest.raises(Exception) as exc_info:
            migration_manager.register(migration2)

        assert "already registered" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_migrate(self, migration_manager):
        """Test applying migrations."""
        applied = []

        async def apply1():
            applied.append(1)

        async def apply2():
            applied.append(2)

        migration_manager.register(Migration(version=1, name="first", apply=apply1, rollback=apply1))
        migration_manager.register(Migration(version=2, name="second", apply=apply2, rollback=apply2))

        records = await migration_manager.migrate()

        assert len(records) == 2
        assert records[0].version == 1
        assert records[0].status == MigrationStatus.COMPLETED
        assert records[1].version == 2
        assert records[1].status == MigrationStatus.COMPLETED
        assert applied == [1, 2]

    @pytest.mark.asyncio
    async def test_get_status(self, migration_manager):
        """Test getting migration status."""

        async def apply():
            pass

        migration_manager.register(Migration(version=1, name="test", apply=apply, rollback=apply))

        status = migration_manager.get_status()

        assert status["current_version"] == 0
        assert status["latest_version"] == 1
        assert status["pending_count"] == 1

    @pytest.mark.asyncio
    async def test_rollback_not_allowed(self, migration_manager):
        """Test rollback when not allowed."""
        migration_manager.config.allow_rollback = False

        with pytest.raises(Exception) as exc_info:
            await migration_manager.rollback(0)

        assert "not allowed" in str(exc_info.value).lower()


# ============================================================================
# Configuration Tests
# ============================================================================


class TestConfiguration:
    """Test cases for configuration classes."""

    def test_production_vector_store_config_defaults(self):
        """Test default configuration values."""
        config = ProductionVectorStoreConfig()

        assert config.collection_name == "default"
        assert config.dimension == 1536
        assert config.distance_metric == "cosine"
        assert config.pool_config.min_connections == 2
        assert config.pool_config.max_connections == 10
        assert config.retry_config.max_retries == 3
        assert config.backup_config.enabled is True
        assert config.migration_config.auto_migrate is False

    def test_retry_config_delay_calculation(self):
        """Test retry delay calculation."""
        config = RetryConfig(
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=10.0,
            jitter=False,
        )
        manager = RetryManager(config)

        # Test delay calculation
        delay0 = manager._calculate_delay(0)
        delay1 = manager._calculate_delay(1)
        delay2 = manager._calculate_delay(2)

        assert delay0 == 1.0
        assert delay1 == 2.0
        assert delay2 == 4.0

    def test_connection_pool_config_validation(self):
        """Test connection pool configuration."""
        config = ConnectionPoolConfig(
            min_connections=2,
            max_connections=5,
            connection_timeout=30.0,
        )

        assert config.min_connections <= config.max_connections
        assert config.connection_timeout > 0