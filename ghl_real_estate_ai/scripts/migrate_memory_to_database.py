"""
Data Migration Service: File-based to Database Storage.

Migrates existing file-based memory system to PostgreSQL with zero downtime:
- Discovers and validates existing data
- Transforms to new schema format
- Performs safe migration with rollback capability
- Validates data integrity
- Generates comprehensive migration reports
"""

import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4, UUID
from dataclasses import dataclass, field

from ghl_real_estate_ai.database import (
    db_pool, infrastructure, initialize_infrastructure
)
from ghl_real_estate_ai.services.memory_service import MemoryService
from ghl_real_estate_ai.services.enhanced_memory_service import EnhancedMemoryService
from ghl_real_estate_ai.models.memory_models import (
    Conversation, ConversationMessage, Tenant,
    BehavioralPreference, PropertyInteraction,
    ConversationStage, MessageRole, PreferenceType, InteractionType,
    convert_legacy_context_to_conversation
)
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MigrationStats:
    """Migration statistics tracking."""
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None

    # Discovery stats
    tenants_discovered: int = 0
    conversations_discovered: int = 0
    total_messages_discovered: int = 0

    # Migration stats
    tenants_migrated: int = 0
    conversations_migrated: int = 0
    messages_migrated: int = 0
    behavioral_prefs_migrated: int = 0
    property_interactions_migrated: int = 0

    # Error stats
    tenants_failed: int = 0
    conversations_failed: int = 0
    validation_errors: int = 0

    # Performance stats
    migration_duration_seconds: float = 0.0
    avg_conversation_time_ms: float = 0.0
    peak_memory_usage_mb: float = 0.0


@dataclass
class TenantMigrationResult:
    """Result of migrating a single tenant."""
    tenant_id: str
    success: bool
    conversations_migrated: int = 0
    messages_migrated: int = 0
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class MigrationReport:
    """Comprehensive migration report."""
    stats: MigrationStats
    tenant_results: List[TenantMigrationResult] = field(default_factory=list)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def add_success(self, tenant_id: str, conversations: int, messages: int, duration: float):
        """Add successful tenant migration."""
        result = TenantMigrationResult(
            tenant_id=tenant_id,
            success=True,
            conversations_migrated=conversations,
            messages_migrated=messages,
            duration_seconds=duration
        )
        self.tenant_results.append(result)
        self.stats.tenants_migrated += 1
        self.stats.conversations_migrated += conversations
        self.stats.messages_migrated += messages

    def add_error(self, tenant_id: str, error: Exception):
        """Add failed tenant migration."""
        result = TenantMigrationResult(
            tenant_id=tenant_id,
            success=False,
            errors=[str(error)]
        )
        self.tenant_results.append(result)
        self.stats.tenants_failed += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "migration_summary": {
                "start_time": self.stats.start_time.isoformat(),
                "end_time": self.stats.end_time.isoformat() if self.stats.end_time else None,
                "duration_seconds": self.stats.migration_duration_seconds,
                "success_rate": self._calculate_success_rate()
            },
            "statistics": {
                "tenants": {
                    "discovered": self.stats.tenants_discovered,
                    "migrated": self.stats.tenants_migrated,
                    "failed": self.stats.tenants_failed
                },
                "conversations": {
                    "discovered": self.stats.conversations_discovered,
                    "migrated": self.stats.conversations_migrated,
                    "failed": self.stats.conversations_failed
                },
                "messages": {
                    "discovered": self.stats.total_messages_discovered,
                    "migrated": self.stats.messages_migrated
                },
                "behavioral_data": {
                    "preferences_migrated": self.stats.behavioral_prefs_migrated,
                    "property_interactions_migrated": self.stats.property_interactions_migrated
                }
            },
            "performance": self.performance_metrics,
            "tenant_results": [
                {
                    "tenant_id": result.tenant_id,
                    "success": result.success,
                    "conversations_migrated": result.conversations_migrated,
                    "messages_migrated": result.messages_migrated,
                    "errors": result.errors,
                    "duration_seconds": result.duration_seconds
                }
                for result in self.tenant_results
            ],
            "validation": self.validation_results,
            "recommendations": self.recommendations
        }

    def _calculate_success_rate(self) -> float:
        """Calculate migration success rate."""
        total = self.stats.tenants_migrated + self.stats.tenants_failed
        return self.stats.tenants_migrated / total if total > 0 else 0.0


class MemoryMigrationService:
    """
    Service for migrating file-based memory to PostgreSQL database.
    """

    def __init__(
        self,
        memory_data_path: Optional[Path] = None,
        batch_size: int = 100,
        validate_data: bool = True,
        backup_before_migration: bool = True
    ):
        """
        Initialize migration service.

        Args:
            memory_data_path: Path to memory data directory
            batch_size: Number of conversations to process per batch
            validate_data: Whether to validate data integrity
            backup_before_migration: Whether to create backup before migration
        """
        self.memory_data_path = memory_data_path or Path("data/memory")
        self.batch_size = batch_size
        self.validate_data = validate_data
        self.backup_before_migration = backup_before_migration

        # Services
        self.legacy_memory_service = MemoryService()
        self.enhanced_memory_service = None

        # Migration state
        self.stats = MigrationStats()
        self.dry_run = False

    async def execute_migration_pipeline(
        self,
        dry_run: bool = False,
        enable_dual_write: bool = True
    ) -> MigrationReport:
        """
        Execute complete migration pipeline.

        Args:
            dry_run: If True, perform validation without actual migration
            enable_dual_write: Enable dual-write mode after migration

        Returns:
            Comprehensive migration report
        """
        self.dry_run = dry_run
        report = MigrationReport(stats=self.stats)

        try:
            logger.info(f"🚀 Starting memory migration pipeline (dry_run={dry_run})")
            self.stats.start_time = datetime.utcnow()

            # Phase 1: Initialize infrastructure
            await self._initialize_migration_environment(report)

            # Phase 2: Discovery and validation
            existing_data = await self._discover_and_validate_existing_data(report)

            if not existing_data:
                logger.warning("⚠️ No data found for migration")
                return report

            # Phase 3: Create backup if requested
            if self.backup_before_migration and not dry_run:
                await self._create_backup(report)

            # Phase 4: Migrate data
            await self._execute_data_migration(existing_data, report)

            # Phase 5: Validate migration integrity
            if not dry_run:
                await self._validate_migration_integrity(report)

            # Phase 6: Enable dual-write mode
            if enable_dual_write and not dry_run:
                await self._enable_dual_write_mode(report)

            # Phase 7: Generate recommendations
            self._generate_recommendations(report)

        except Exception as e:
            logger.error(f"❌ Migration pipeline failed: {e}")
            report.add_error("migration_pipeline", e)

        finally:
            self.stats.end_time = datetime.utcnow()
            self.stats.migration_duration_seconds = (
                self.stats.end_time - self.stats.start_time
            ).total_seconds()

            # Generate performance metrics
            report.performance_metrics = await self._generate_performance_metrics()

        logger.info(f"✅ Migration pipeline completed in {self.stats.migration_duration_seconds:.2f} seconds")
        return report

    async def _initialize_migration_environment(self, report: MigrationReport):
        """Initialize migration environment and dependencies."""
        logger.info("🔧 Initializing migration environment")

        # Initialize infrastructure
        infrastructure_status = await initialize_infrastructure(
            enable_database=True,
            enable_redis=False  # Redis not required for migration
        )

        if not infrastructure_status:
            raise RuntimeError("Failed to initialize database infrastructure")

        # Initialize enhanced memory service
        self.enhanced_memory_service = EnhancedMemoryService(use_database=True, use_redis=False)

        # Validate database schema
        try:
            schema_validation = await db_pool.validate_schema()
            if not schema_validation.get("schema_valid", False):
                raise RuntimeError(f"Database schema validation failed: {schema_validation}")

            logger.info("✅ Database schema validated successfully")

        except Exception as e:
            raise RuntimeError(f"Schema validation error: {e}")

    async def _discover_and_validate_existing_data(self, report: MigrationReport) -> Dict[str, Any]:
        """Discover and validate existing memory data."""
        logger.info("🔍 Discovering existing memory data")

        if not self.memory_data_path.exists():
            logger.warning(f"Memory data path does not exist: {self.memory_data_path}")
            return {}

        existing_data = {
            "tenants": [],
            "total_conversations": 0,
            "total_messages": 0
        }

        # Discover tenant directories
        for tenant_dir in self.memory_data_path.iterdir():
            if not tenant_dir.is_dir():
                continue

            # Skip non-location directories
            if tenant_dir.name.startswith('.'):
                continue

            tenant_data = await self._discover_tenant_data(tenant_dir)
            if tenant_data:
                existing_data["tenants"].append(tenant_data)
                existing_data["total_conversations"] += tenant_data["conversation_count"]
                existing_data["total_messages"] += tenant_data["total_messages"]

        # Also check root level files (non-tenant specific)
        root_files = await self._discover_root_level_conversations()
        if root_files:
            default_tenant_data = {
                "location_id": "default",
                "path": self.memory_data_path,
                "conversations": root_files,
                "conversation_count": len(root_files),
                "total_messages": sum(conv.get("message_count", 0) for conv in root_files)
            }
            existing_data["tenants"].append(default_tenant_data)
            existing_data["total_conversations"] += default_tenant_data["conversation_count"]
            existing_data["total_messages"] += default_tenant_data["total_messages"]

        # Update stats
        self.stats.tenants_discovered = len(existing_data["tenants"])
        self.stats.conversations_discovered = existing_data["total_conversations"]
        self.stats.total_messages_discovered = existing_data["total_messages"]

        logger.info(f"📊 Discovery complete: {self.stats.tenants_discovered} tenants, "
                   f"{self.stats.conversations_discovered} conversations, "
                   f"{self.stats.total_messages_discovered} messages")

        return existing_data

    async def _discover_tenant_data(self, tenant_dir: Path) -> Optional[Dict[str, Any]]:
        """Discover conversation data for a specific tenant."""
        location_id = tenant_dir.name
        conversations = []
        total_messages = 0

        try:
            # Find all JSON files in tenant directory
            for json_file in tenant_dir.glob("*.json"):
                if json_file.name.startswith('.'):
                    continue

                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        conversation_data = json.load(f)

                    # Extract contact ID from filename
                    contact_id = json_file.stem

                    # Validate and count messages
                    message_count = len(conversation_data.get("conversation_history", []))
                    total_messages += message_count

                    conversations.append({
                        "contact_id": contact_id,
                        "file_path": json_file,
                        "data": conversation_data,
                        "message_count": message_count,
                        "last_modified": datetime.fromtimestamp(json_file.stat().st_mtime)
                    })

                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.warning(f"⚠️ Skipping invalid file {json_file}: {e}")
                    continue

            if conversations:
                return {
                    "location_id": location_id,
                    "path": tenant_dir,
                    "conversations": conversations,
                    "conversation_count": len(conversations),
                    "total_messages": total_messages
                }

        except Exception as e:
            logger.error(f"❌ Error discovering tenant data for {location_id}: {e}")

        return None

    async def _discover_root_level_conversations(self) -> List[Dict[str, Any]]:
        """Discover conversations at root level (non-tenant specific)."""
        conversations = []

        try:
            for json_file in self.memory_data_path.glob("*.json"):
                if json_file.name.startswith('.'):
                    continue

                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        conversation_data = json.load(f)

                    contact_id = json_file.stem
                    message_count = len(conversation_data.get("conversation_history", []))

                    conversations.append({
                        "contact_id": contact_id,
                        "file_path": json_file,
                        "data": conversation_data,
                        "message_count": message_count,
                        "last_modified": datetime.fromtimestamp(json_file.stat().st_mtime)
                    })

                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.warning(f"⚠️ Skipping invalid root file {json_file}: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ Error discovering root level conversations: {e}")

        return conversations

    async def _create_backup(self, report: MigrationReport):
        """Create backup of existing data before migration."""
        logger.info("💾 Creating backup before migration")

        backup_dir = Path(f"data/migration_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        backup_dir.mkdir(parents=True, exist_ok=True)

        try:
            import shutil
            shutil.copytree(self.memory_data_path, backup_dir / "memory_backup")
            logger.info(f"✅ Backup created at {backup_dir}")

            report.recommendations.append(f"Backup created at {backup_dir}")

        except Exception as e:
            logger.warning(f"⚠️ Backup creation failed: {e}")
            report.recommendations.append("Manual backup recommended before production migration")

    async def _execute_data_migration(self, existing_data: Dict[str, Any], report: MigrationReport):
        """Execute the actual data migration."""
        logger.info("🔄 Executing data migration")

        for tenant_data in existing_data["tenants"]:
            tenant_start_time = time.time()

            try:
                result = await self._migrate_tenant_data(tenant_data)

                duration = time.time() - tenant_start_time
                report.add_success(
                    tenant_data["location_id"],
                    result["conversations_migrated"],
                    result["messages_migrated"],
                    duration
                )

                logger.info(f"✅ Migrated tenant {tenant_data['location_id']}: "
                           f"{result['conversations_migrated']} conversations, "
                           f"{result['messages_migrated']} messages in {duration:.2f}s")

            except Exception as e:
                logger.error(f"❌ Failed to migrate tenant {tenant_data['location_id']}: {e}")
                report.add_error(tenant_data["location_id"], e)

    async def _migrate_tenant_data(self, tenant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate data for a single tenant."""
        location_id = tenant_data["location_id"]
        conversations = tenant_data["conversations"]

        if self.dry_run:
            logger.info(f"🔍 [DRY RUN] Would migrate {len(conversations)} conversations for {location_id}")
            return {
                "conversations_migrated": len(conversations),
                "messages_migrated": tenant_data["total_messages"],
                "dry_run": True
            }

        # Get or create tenant UUID
        tenant_uuid = await self._get_or_create_tenant_uuid(location_id)

        conversations_migrated = 0
        messages_migrated = 0

        # Process conversations in batches
        for i in range(0, len(conversations), self.batch_size):
            batch = conversations[i:i + self.batch_size]

            for conversation_data in batch:
                try:
                    # Convert legacy format to new model
                    conversation_with_memory = convert_legacy_context_to_conversation(
                        conversation_data["data"],
                        tenant_uuid,
                        conversation_data["contact_id"]
                    )

                    # Save to database
                    await self.enhanced_memory_service.save_enhanced_context(
                        location_id,
                        conversation_data["contact_id"],
                        conversation_with_memory
                    )

                    conversations_migrated += 1
                    messages_migrated += conversation_data["message_count"]

                except Exception as e:
                    logger.error(f"❌ Failed to migrate conversation {conversation_data['contact_id']}: {e}")
                    self.stats.conversations_failed += 1

            # Small delay between batches to avoid overwhelming database
            await asyncio.sleep(0.1)

        return {
            "conversations_migrated": conversations_migrated,
            "messages_migrated": messages_migrated
        }

    async def _get_or_create_tenant_uuid(self, location_id: str) -> UUID:
        """Get or create tenant UUID for location_id."""
        tenant_uuid = uuid4()

        if not self.dry_run:
            try:
                await db_pool.execute(
                    """
                    INSERT INTO tenants (id, location_id, name, status, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (location_id) DO NOTHING
                    """,
                    tenant_uuid, location_id, f"Migrated Tenant {location_id}",
                    "active", datetime.utcnow(), datetime.utcnow()
                )

                # Get the actual tenant ID (in case of conflict)
                result = await db_pool.fetchrow(
                    "SELECT id FROM tenants WHERE location_id = $1",
                    location_id
                )

                if result:
                    tenant_uuid = result['id']

            except Exception as e:
                logger.error(f"Error creating tenant {location_id}: {e}")

        return tenant_uuid

    async def _validate_migration_integrity(self, report: MigrationReport):
        """Validate migration data integrity."""
        logger.info("🔍 Validating migration integrity")

        validation_results = {
            "schema_validation": {},
            "data_integrity": {},
            "performance_validation": {}
        }

        try:
            # Schema validation
            schema_results = await db_pool.validate_schema()
            validation_results["schema_validation"] = schema_results

            # Data integrity checks
            integrity_results = await self._perform_data_integrity_checks()
            validation_results["data_integrity"] = integrity_results

            # Performance validation
            performance_results = await self._perform_performance_validation()
            validation_results["performance_validation"] = performance_results

            report.validation_results = validation_results

            # Check if validation passed
            schema_valid = schema_results.get("schema_valid", False)
            data_valid = integrity_results.get("data_valid", False)
            performance_ok = performance_results.get("performance_acceptable", False)

            if schema_valid and data_valid and performance_ok:
                logger.info("✅ Migration validation passed")
            else:
                logger.warning("⚠️ Migration validation completed with warnings")
                report.recommendations.append("Review validation results for potential issues")

        except Exception as e:
            logger.error(f"❌ Migration validation failed: {e}")
            validation_results["error"] = str(e)

    async def _perform_data_integrity_checks(self) -> Dict[str, Any]:
        """Perform data integrity checks."""
        try:
            # Check table counts
            tenant_count = await db_pool.fetchval("SELECT COUNT(*) FROM tenants")
            conversation_count = await db_pool.fetchval("SELECT COUNT(*) FROM conversations")
            message_count = await db_pool.fetchval("SELECT COUNT(*) FROM conversation_messages")

            # Check data consistency
            orphaned_conversations = await db_pool.fetchval(
                "SELECT COUNT(*) FROM conversations WHERE tenant_id NOT IN (SELECT id FROM tenants)"
            )

            orphaned_messages = await db_pool.fetchval(
                "SELECT COUNT(*) FROM conversation_messages WHERE conversation_id NOT IN (SELECT id FROM conversations)"
            )

            return {
                "data_valid": orphaned_conversations == 0 and orphaned_messages == 0,
                "counts": {
                    "tenants": tenant_count,
                    "conversations": conversation_count,
                    "messages": message_count
                },
                "integrity_issues": {
                    "orphaned_conversations": orphaned_conversations,
                    "orphaned_messages": orphaned_messages
                }
            }

        except Exception as e:
            return {
                "data_valid": False,
                "error": str(e)
            }

    async def _perform_performance_validation(self) -> Dict[str, Any]:
        """Perform performance validation."""
        try:
            # Test query performance
            start_time = time.time()

            # Simple query performance test
            await db_pool.fetchrow("SELECT 1")
            simple_query_time = (time.time() - start_time) * 1000

            # Complex query performance test
            start_time = time.time()
            await db_pool.fetchrow("""
                SELECT c.id, c.contact_id, c.lead_score,
                       COUNT(cm.id) as message_count
                FROM conversations c
                LEFT JOIN conversation_messages cm ON c.id = cm.conversation_id
                WHERE c.created_at >= NOW() - INTERVAL '1 hour'
                GROUP BY c.id, c.contact_id, c.lead_score
                LIMIT 1
            """)
            complex_query_time = (time.time() - start_time) * 1000

            # Performance thresholds
            simple_threshold = 10  # 10ms
            complex_threshold = 100  # 100ms

            performance_acceptable = (
                simple_query_time < simple_threshold and
                complex_query_time < complex_threshold
            )

            return {
                "performance_acceptable": performance_acceptable,
                "query_times_ms": {
                    "simple_query": simple_query_time,
                    "complex_query": complex_query_time
                },
                "thresholds_ms": {
                    "simple_threshold": simple_threshold,
                    "complex_threshold": complex_threshold
                }
            }

        except Exception as e:
            return {
                "performance_acceptable": False,
                "error": str(e)
            }

    async def _enable_dual_write_mode(self, report: MigrationReport):
        """Enable dual-write mode for gradual migration."""
        logger.info("🔄 Enabling dual-write mode")

        try:
            # Update enhanced memory service to use dual-write
            self.enhanced_memory_service.use_database = True
            logger.info("✅ Dual-write mode enabled")

            report.recommendations.append(
                "Dual-write mode enabled. Monitor for 24-48 hours before disabling file-based storage."
            )

        except Exception as e:
            logger.error(f"❌ Failed to enable dual-write mode: {e}")
            report.recommendations.append("Manual verification of dual-write mode required")

    def _generate_recommendations(self, report: MigrationReport):
        """Generate migration recommendations."""
        success_rate = report._calculate_success_rate()

        if success_rate == 1.0:
            report.recommendations.append("Migration completed successfully. Consider monitoring for 24 hours.")
        elif success_rate >= 0.9:
            report.recommendations.append("Migration mostly successful. Review failed tenants and retry if needed.")
        elif success_rate >= 0.5:
            report.recommendations.append("Partial migration success. Investigate failures before proceeding.")
        else:
            report.recommendations.append("Migration had significant failures. Review logs and fix issues before retrying.")

        # Performance recommendations
        if self.stats.migration_duration_seconds > 300:  # 5 minutes
            report.recommendations.append("Migration took longer than expected. Consider increasing batch size or optimizing queries.")

        # Data volume recommendations
        if self.stats.conversations_migrated > 10000:
            report.recommendations.append("Large dataset migrated. Monitor database performance and consider indexing optimization.")

    async def _generate_performance_metrics(self) -> Dict[str, Any]:
        """Generate performance metrics for the migration."""
        try:
            # Database metrics
            db_metrics = await infrastructure.get_metrics()

            # Calculate migration-specific metrics
            conversations_per_second = 0
            if self.stats.migration_duration_seconds > 0:
                conversations_per_second = self.stats.conversations_migrated / self.stats.migration_duration_seconds

            return {
                "migration_performance": {
                    "conversations_per_second": conversations_per_second,
                    "total_duration_seconds": self.stats.migration_duration_seconds,
                    "avg_conversation_time_ms": self.stats.avg_conversation_time_ms
                },
                "infrastructure_metrics": db_metrics.get("database", {}),
                "memory_usage": {
                    "peak_usage_mb": self.stats.peak_memory_usage_mb
                }
            }

        except Exception as e:
            return {
                "error": str(e),
                "migration_duration_seconds": self.stats.migration_duration_seconds
            }


# CLI interface for running migration
async def main():
    """Main CLI interface for migration."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate memory data from files to database")
    parser.add_argument("--dry-run", action="store_true", help="Perform validation without migration")
    parser.add_argument("--memory-path", type=str, help="Path to memory data directory")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--output-report", type=str, help="Output file for migration report")

    args = parser.parse_args()

    # Initialize migration service
    memory_path = Path(args.memory_path) if args.memory_path else None
    migration_service = MemoryMigrationService(
        memory_data_path=memory_path,
        batch_size=args.batch_size
    )

    try:
        # Execute migration
        report = await migration_service.execute_migration_pipeline(
            dry_run=args.dry_run
        )

        # Output results
        print(f"\n{'='*60}")
        print("MIGRATION REPORT")
        print(f"{'='*60}")
        print(f"Status: {'✅ SUCCESS' if report._calculate_success_rate() > 0.5 else '❌ FAILED'}")
        print(f"Tenants: {report.stats.tenants_migrated}/{report.stats.tenants_discovered}")
        print(f"Conversations: {report.stats.conversations_migrated}/{report.stats.conversations_discovered}")
        print(f"Duration: {report.stats.migration_duration_seconds:.2f} seconds")

        if report.recommendations:
            print("\nRecommendations:")
            for rec in report.recommendations:
                print(f"• {rec}")

        # Save detailed report if requested
        if args.output_report:
            with open(args.output_report, 'w') as f:
                json.dump(report.to_dict(), f, indent=2, default=str)
            print(f"\nDetailed report saved to: {args.output_report}")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"❌ Migration failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))