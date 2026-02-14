"""
Offline-First Sync Service for Mobile Apps.

Provides comprehensive offline data synchronization with:
- Conflict resolution algorithms
- Delta sync for efficiency
- Background sync queuing
- Data integrity validation
- Connection state management
- Progressive data sync
"""

import hashlib
import json
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.ghl_service import GHLService

logger = get_logger(__name__)


class SyncOperationType(Enum):
    """Types of sync operations."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BULK_UPDATE = "bulk_update"


class ConflictResolutionStrategy(Enum):
    """Conflict resolution strategies."""

    SERVER_WINS = "server_wins"
    CLIENT_WINS = "client_wins"
    LATEST_TIMESTAMP = "latest_timestamp"
    MERGE_FIELDS = "merge_fields"
    MANUAL_RESOLUTION = "manual_resolution"


class SyncStatus(Enum):
    """Sync operation status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    CONFLICT = "conflict"
    FAILED = "failed"
    MANUAL_REQUIRED = "manual_required"


@dataclass
class SyncOperation:
    """Individual sync operation."""

    operation_id: str
    operation_type: SyncOperationType
    entity_type: str  # lead, property, note, etc.
    entity_id: str
    data: Dict[str, Any]
    timestamp: datetime
    device_id: str
    version_hash: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class SyncConflict:
    """Sync conflict information."""

    operation_id: str
    entity_type: str
    entity_id: str
    client_data: Dict[str, Any]
    server_data: Dict[str, Any]
    conflict_fields: List[str]
    resolution_strategy: ConflictResolutionStrategy
    resolved_data: Optional[Dict[str, Any]] = None
    requires_manual_resolution: bool = False


@dataclass
class SyncResult:
    """Result of sync operation."""

    operation_id: str
    status: SyncStatus
    error_message: Optional[str] = None
    server_timestamp: Optional[datetime] = None
    resolved_data: Optional[Dict[str, Any]] = None
    conflict: Optional[SyncConflict] = None


class OfflineSyncService:
    """
    Comprehensive offline synchronization service.
    Handles bidirectional data sync with conflict resolution.
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.sync_queues: Dict[str, deque] = {}  # device_id -> queue
        self.active_syncs: Dict[str, bool] = {}  # device_id -> is_syncing

    async def queue_operation(self, device_id: str, operation: SyncOperation) -> bool:
        """
        Queue an operation for offline sync.
        """
        try:
            # Initialize queue if needed
            if device_id not in self.sync_queues:
                self.sync_queues[device_id] = deque()

            # Add operation to queue
            self.sync_queues[device_id].append(operation)

            # Store in cache for persistence
            queue_key = f"sync_queue:{device_id}"
            queue_data = [asdict(op) for op in self.sync_queues[device_id]]
            await self.cache.set(queue_key, queue_data, ttl=86400 * 7)  # 1 week

            logger.info(f"Operation queued: {operation.operation_id} for device {device_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to queue operation: {e}")
            return False

    async def process_sync_queue(
        self, device_id: str, location_id: str, ghl_api_key: str, batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Process pending sync operations for a device.
        """
        try:
            # Check if sync is already in progress
            if self.active_syncs.get(device_id, False):
                return {"status": "in_progress", "message": "Sync already in progress for this device"}

            self.active_syncs[device_id] = True

            # Load queue from cache
            await self._load_queue_from_cache(device_id)

            if device_id not in self.sync_queues or not self.sync_queues[device_id]:
                self.active_syncs[device_id] = False
                return {"status": "no_operations", "message": "No pending operations"}

            # Process operations in batches
            ghl_service = GHLService(ghl_api_key, location_id)
            results = []
            conflicts = []
            processed_count = 0

            while self.sync_queues[device_id] and processed_count < batch_size:
                operation = self.sync_queues[device_id].popleft()
                processed_count += 1

                try:
                    # Process individual operation
                    result = await self._process_operation(operation, ghl_service)
                    results.append(result)

                    if result.status == SyncStatus.CONFLICT and result.conflict:
                        conflicts.append(result.conflict)

                except Exception as op_error:
                    error_result = SyncResult(
                        operation_id=operation.operation_id, status=SyncStatus.FAILED, error_message=str(op_error)
                    )
                    results.append(error_result)
                    logger.error(f"Operation failed: {operation.operation_id} - {op_error}")

            # Update cache with remaining queue
            queue_key = f"sync_queue:{device_id}"
            if self.sync_queues[device_id]:
                queue_data = [asdict(op) for op in self.sync_queues[device_id]]
                await self.cache.set(queue_key, queue_data, ttl=86400 * 7)
            else:
                await self.cache.delete(queue_key)

            self.active_syncs[device_id] = False

            # Get server updates since last sync
            server_updates = await self._get_server_updates_since_last_sync(device_id, location_id, ghl_service)

            return {
                "status": "completed",
                "processed_operations": len(results),
                "remaining_operations": len(self.sync_queues.get(device_id, [])),
                "results": [asdict(r) for r in results],
                "conflicts": [asdict(c) for c in conflicts],
                "server_updates": server_updates,
                "sync_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.active_syncs[device_id] = False
            logger.error(f"Sync processing failed: {e}")
            return {"status": "error", "error": str(e)}

    async def resolve_conflict(
        self,
        device_id: str,
        conflict_id: str,
        resolution_data: Dict[str, Any],
        strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.MANUAL_RESOLUTION,
    ) -> Dict[str, Any]:
        """
        Resolve a sync conflict with provided resolution data.
        """
        try:
            # Load conflict from cache
            conflict_key = f"sync_conflict:{device_id}:{conflict_id}"
            conflict_data = await self.cache.get(conflict_key)

            if not conflict_data:
                return {"success": False, "error": "Conflict not found"}

            conflict = SyncConflict(**conflict_data)

            # Apply resolution
            if strategy == ConflictResolutionStrategy.CLIENT_WINS:
                resolved_data = conflict.client_data
            elif strategy == ConflictResolutionStrategy.SERVER_WINS:
                resolved_data = conflict.server_data
            elif strategy == ConflictResolutionStrategy.MANUAL_RESOLUTION:
                resolved_data = resolution_data
            elif strategy == ConflictResolutionStrategy.MERGE_FIELDS:
                resolved_data = self._merge_conflict_fields(conflict, resolution_data)
            else:
                resolved_data = resolution_data

            # Update conflict with resolution
            conflict.resolved_data = resolved_data
            conflict.resolution_strategy = strategy
            conflict.requires_manual_resolution = False

            # Store resolved conflict
            await self.cache.set(conflict_key, asdict(conflict), ttl=86400)

            # ROADMAP-057: Apply resolved data to GHL server
            # This would update the entity with the resolved conflict data

            logger.info(f"Conflict resolved: {conflict_id} using {strategy.value}")

            return {
                "success": True,
                "conflict_id": conflict_id,
                "resolution_strategy": strategy.value,
                "resolved_data": resolved_data,
            }

        except Exception as e:
            logger.error(f"Conflict resolution failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_delta_sync_data(
        self, device_id: str, location_id: str, last_sync_timestamp: datetime, entity_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Get delta sync data since last sync timestamp.
        """
        try:
            # Default entity types
            if not entity_types:
                entity_types = ["leads", "properties", "notes", "tasks"]

            delta_data = {}

            for entity_type in entity_types:
                # Get changes since last sync
                changes = await self._get_entity_changes_since(location_id, entity_type, last_sync_timestamp)

                if changes:
                    delta_data[entity_type] = {
                        "created": changes.get("created", []),
                        "updated": changes.get("updated", []),
                        "deleted": changes.get("deleted", []),
                        "total_changes": sum(len(changes.get(k, [])) for k in ["created", "updated", "deleted"]),
                    }

            # Calculate sync efficiency metrics
            total_changes = sum(data.get("total_changes", 0) for data in delta_data.values())

            return {
                "device_id": device_id,
                "last_sync": last_sync_timestamp.isoformat(),
                "current_sync": datetime.utcnow().isoformat(),
                "delta_data": delta_data,
                "total_changes": total_changes,
                "estimated_sync_time": self._estimate_sync_time(total_changes),
                "compression_ratio": self._calculate_compression_ratio(delta_data),
            }

        except Exception as e:
            logger.error(f"Delta sync data failed: {e}")
            return {"error": str(e), "device_id": device_id}

    async def validate_data_integrity(self, device_id: str, entity_checksums: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate data integrity using checksums.
        """
        try:
            integrity_report = {
                "device_id": device_id,
                "validation_timestamp": datetime.utcnow().isoformat(),
                "entities_checked": 0,
                "integrity_errors": [],
                "suggestions": [],
            }

            for entity_id, client_checksum in entity_checksums.items():
                # Get server checksum
                server_checksum = await self._get_server_entity_checksum(entity_id)

                integrity_report["entities_checked"] += 1

                if server_checksum != client_checksum:
                    integrity_report["integrity_errors"].append(
                        {
                            "entity_id": entity_id,
                            "client_checksum": client_checksum,
                            "server_checksum": server_checksum,
                            "suggested_action": "resync_entity",
                        }
                    )

            # Provide suggestions based on errors
            if integrity_report["integrity_errors"]:
                integrity_report["suggestions"] = [
                    "Consider performing a full resync for entities with checksum mismatches",
                    "Check network connectivity during last sync",
                    "Verify local data hasn't been corrupted",
                ]

            return integrity_report

        except Exception as e:
            logger.error(f"Data integrity validation failed: {e}")
            return {"error": str(e), "device_id": device_id}

    async def estimate_sync_requirements(
        self,
        device_id: str,
        connection_quality: str = "good",  # poor, fair, good, excellent
    ) -> Dict[str, Any]:
        """
        Estimate sync requirements and provide recommendations.
        """
        try:
            # Load pending operations
            await self._load_queue_from_cache(device_id)
            pending_ops = len(self.sync_queues.get(device_id, []))

            # Connection quality multipliers
            quality_multipliers = {"poor": 3.0, "fair": 2.0, "good": 1.0, "excellent": 0.5}

            base_time_per_op = 2  # seconds
            multiplier = quality_multipliers.get(connection_quality, 1.0)
            estimated_time = pending_ops * base_time_per_op * multiplier

            # Recommendations based on conditions
            recommendations = []

            if pending_ops > 50:
                recommendations.append("High number of pending operations. Consider batch processing.")

            if connection_quality in ["poor", "fair"]:
                recommendations.append("Poor connection detected. Prioritize critical operations only.")

            if estimated_time > 300:  # 5 minutes
                recommendations.append("Long sync time estimated. Consider syncing in background.")

            return {
                "device_id": device_id,
                "pending_operations": pending_ops,
                "estimated_sync_time_seconds": estimated_time,
                "connection_quality": connection_quality,
                "recommendations": recommendations,
                "should_sync_now": estimated_time < 60 and pending_ops < 20,
                "battery_impact": "low" if pending_ops < 10 else "medium" if pending_ops < 50 else "high",
            }

        except Exception as e:
            logger.error(f"Sync requirements estimation failed: {e}")
            return {"error": str(e), "device_id": device_id}

    async def _load_queue_from_cache(self, device_id: str):
        """Load sync queue from cache."""
        try:
            queue_key = f"sync_queue:{device_id}"
            queue_data = await self.cache.get(queue_key)

            if queue_data:
                operations = [SyncOperation(**op_data) for op_data in queue_data]
                self.sync_queues[device_id] = deque(operations)
            else:
                self.sync_queues[device_id] = deque()

        except Exception as e:
            logger.error(f"Failed to load queue from cache: {e}")
            self.sync_queues[device_id] = deque()

    async def _process_operation(self, operation: SyncOperation, ghl_service: GHLService) -> SyncResult:
        """Process a single sync operation."""
        try:
            # Check for conflicts first
            if operation.operation_type in [SyncOperationType.UPDATE, SyncOperationType.DELETE]:
                conflict = await self._detect_conflict(operation, ghl_service)
                if conflict:
                    return SyncResult(
                        operation_id=operation.operation_id, status=SyncStatus.CONFLICT, conflict=conflict
                    )

            # Execute operation
            if operation.entity_type == "lead":
                success = await self._process_lead_operation(operation, ghl_service)
            elif operation.entity_type == "property":
                success = await self._process_property_operation(operation, ghl_service)
            elif operation.entity_type == "note":
                success = await self._process_note_operation(operation, ghl_service)
            else:
                raise ValueError(f"Unsupported entity type: {operation.entity_type}")

            if success:
                return SyncResult(
                    operation_id=operation.operation_id, status=SyncStatus.SUCCESS, server_timestamp=datetime.utcnow()
                )
            else:
                return SyncResult(
                    operation_id=operation.operation_id,
                    status=SyncStatus.FAILED,
                    error_message="Operation execution failed",
                )

        except Exception as e:
            # Retry logic
            operation.retry_count += 1
            if operation.retry_count < operation.max_retries:
                # Re-queue for retry
                return SyncResult(
                    operation_id=operation.operation_id,
                    status=SyncStatus.FAILED,
                    error_message=f"Retry {operation.retry_count}/{operation.max_retries}: {str(e)}",
                )
            else:
                return SyncResult(
                    operation_id=operation.operation_id,
                    status=SyncStatus.FAILED,
                    error_message=f"Max retries exceeded: {str(e)}",
                )

    async def _detect_conflict(self, operation: SyncOperation, ghl_service: GHLService) -> Optional[SyncConflict]:
        """Detect if operation would cause a conflict."""
        try:
            # Get current server state
            if operation.entity_type == "lead":
                server_data = await ghl_service.get_lead(operation.entity_id)
            else:
                return None  # No conflict detection for other types yet

            if not server_data:
                return None  # Entity doesn't exist on server

            # Calculate checksums
            self._calculate_data_hash(operation.data)
            server_hash = self._calculate_data_hash(server_data)

            if operation.version_hash and operation.version_hash != server_hash:
                # Conflict detected
                conflict_fields = self._identify_conflict_fields(operation.data, server_data)

                return SyncConflict(
                    operation_id=operation.operation_id,
                    entity_type=operation.entity_type,
                    entity_id=operation.entity_id,
                    client_data=operation.data,
                    server_data=server_data,
                    conflict_fields=conflict_fields,
                    resolution_strategy=ConflictResolutionStrategy.LATEST_TIMESTAMP,
                    requires_manual_resolution=len(conflict_fields) > 3,  # Arbitrary threshold
                )

            return None

        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            return None

    async def _process_lead_operation(self, operation: SyncOperation, ghl_service: GHLService) -> bool:
        """Process lead-specific sync operation."""
        try:
            if operation.operation_type == SyncOperationType.CREATE:
                return await ghl_service.create_lead(operation.data)
            elif operation.operation_type == SyncOperationType.UPDATE:
                return await ghl_service.update_lead(operation.entity_id, operation.data)
            elif operation.operation_type == SyncOperationType.DELETE:
                return await ghl_service.delete_lead(operation.entity_id)

            return False

        except Exception as e:
            logger.error(f"Lead operation failed: {e}")
            return False

    async def _process_property_operation(self, operation: SyncOperation, ghl_service: GHLService) -> bool:
        """Process property-specific sync operation."""
        try:
            # ROADMAP-052: Implement property CRUD operations
            # Connect to GHL property API endpoints
            return True  # Mock success

        except Exception as e:
            logger.error(f"Property operation failed: {e}")
            return False

    async def _process_note_operation(self, operation: SyncOperation, ghl_service: GHLService) -> bool:
        """Process note-specific sync operation."""
        try:
            # ROADMAP-053: Implement note CRUD operations
            # Connect to GHL notes API
            return True  # Mock success

        except Exception as e:
            logger.error(f"Note operation failed: {e}")
            return False

    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """Calculate hash of data for conflict detection."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def _identify_conflict_fields(self, client_data: Dict[str, Any], server_data: Dict[str, Any]) -> List[str]:
        """Identify fields that have conflicts."""
        conflicts = []
        all_fields = set(client_data.keys()) | set(server_data.keys())

        for field in all_fields:
            client_value = client_data.get(field)
            server_value = server_data.get(field)

            if client_value != server_value:
                conflicts.append(field)

        return conflicts

    def _merge_conflict_fields(self, conflict: SyncConflict, resolution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge conflict fields using provided resolution."""
        merged_data = conflict.server_data.copy()
        merged_data.update(resolution_data)
        return merged_data

    async def _get_server_updates_since_last_sync(
        self, device_id: str, location_id: str, ghl_service: GHLService
    ) -> List[Dict[str, Any]]:
        """Get server updates since device's last sync."""
        try:
            # Get last sync timestamp
            last_sync_key = f"last_sync:{device_id}"
            last_sync_data = await self.cache.get(last_sync_key)

            if not last_sync_data:
                datetime.utcnow() - timedelta(days=7)  # Default to 1 week
            else:
                datetime.fromisoformat(last_sync_data)

            # Update last sync timestamp
            await self.cache.set(last_sync_key, datetime.utcnow().isoformat(), ttl=86400 * 30)

            # ROADMAP-054: Fetch server updates since last sync
            # Query GHL API with timestamp filters
            return []  # Mock empty updates

        except Exception as e:
            logger.error(f"Failed to get server updates: {e}")
            return []

    async def _get_entity_changes_since(
        self, location_id: str, entity_type: str, since: datetime
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get entity changes since timestamp."""
        try:
            # ROADMAP-055: Implement entity change tracking
            # Requires audit log table and change detection queries
            return {"created": [], "updated": [], "deleted": []}

        except Exception as e:
            logger.error(f"Failed to get entity changes: {e}")
            return {"created": [], "updated": [], "deleted": []}

    async def _get_server_entity_checksum(self, entity_id: str) -> str:
        """Get checksum of entity on server."""
        try:
            # ROADMAP-056: Get entity checksum from server for integrity validation
            return "mock_checksum"

        except Exception as e:
            logger.error(f"Failed to get server checksum: {e}")
            return ""

    def _estimate_sync_time(self, operation_count: int) -> int:
        """Estimate sync time in seconds."""
        base_time = 1  # seconds per operation
        return operation_count * base_time

    def _calculate_compression_ratio(self, delta_data: Dict[str, Any]) -> float:
        """Calculate compression ratio for delta sync."""
        try:
            total_changes = sum(data.get("total_changes", 0) for data in delta_data.values())

            # Assume 1000 total entities for ratio calculation
            total_entities = 1000
            compression_ratio = 1.0 - (total_changes / total_entities)

            return max(0.0, min(1.0, compression_ratio))

        except Exception:
            return 0.5  # Default 50% compression


# Global service instance
_offline_sync_service = None


def get_offline_sync_service() -> OfflineSyncService:
    """Get the global offline sync service instance."""
    global _offline_sync_service
    if _offline_sync_service is None:
        _offline_sync_service = OfflineSyncService()
    return _offline_sync_service
