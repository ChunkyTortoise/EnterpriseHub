"""
Workflow State Management System

Handles persistence, recovery, and state management for workflow executions.
Supports resume functionality, state snapshots, and execution history.
"""

import json
import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ExecutionSnapshot:
    """Snapshot of workflow execution state"""

    execution_id: str
    workflow_id: str
    lead_id: str
    current_step_id: Optional[str]
    status: str
    lead_data: Dict[str, Any]
    variables: Dict[str, Any]
    execution_path: List[Dict[str, Any]]
    retry_count: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class WorkflowStateManager:
    """Manages workflow execution state persistence and recovery"""

    def __init__(self, db_path: str = "workflow_state.db"):
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()

    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            Path(db_dir).mkdir(parents=True, exist_ok=True)

    def _init_database(self):
        """Initialize SQLite database schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_executions (
                        execution_id TEXT PRIMARY KEY,
                        workflow_id TEXT NOT NULL,
                        lead_id TEXT NOT NULL,
                        current_step_id TEXT,
                        status TEXT NOT NULL,
                        lead_data TEXT NOT NULL,
                        variables TEXT NOT NULL,
                        execution_path TEXT NOT NULL,
                        retry_count INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        completed_at TEXT,
                        error_message TEXT
                    )
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_checkpoints (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        execution_id TEXT NOT NULL,
                        step_id TEXT NOT NULL,
                        checkpoint_data TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (execution_id) REFERENCES workflow_executions (execution_id)
                    )
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS workflow_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        execution_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        event_data TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (execution_id) REFERENCES workflow_executions (execution_id)
                    )
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_executions_workflow_id
                    ON workflow_executions(workflow_id)
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_executions_lead_id
                    ON workflow_executions(lead_id)
                """)

                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_executions_status
                    ON workflow_executions(status)
                """)

                conn.commit()

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def save_execution_state(self, execution_id: str, execution_context: Dict[str, Any]) -> bool:
        """Save or update workflow execution state"""
        try:
            # Convert datetime objects to ISO strings
            context_copy = execution_context.copy()
            for key, value in context_copy.items():
                if isinstance(value, datetime):
                    context_copy[key] = value.isoformat()

            # Prepare data for database
            data = (
                execution_id,
                context_copy.get("workflow_id", ""),
                context_copy.get("lead_id", ""),
                context_copy.get("current_step_id"),
                context_copy.get("status", "unknown"),
                json.dumps(context_copy.get("lead_data", {})),
                json.dumps(context_copy.get("variables", {})),
                json.dumps(context_copy.get("execution_path", [])),
                context_copy.get("retry_count", 0),
                context_copy.get("started_at", datetime.now().isoformat()),
                datetime.now().isoformat(),
                context_copy.get("completed_at"),
                context_copy.get("error"),
            )

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO workflow_executions (
                        execution_id, workflow_id, lead_id, current_step_id, status,
                        lead_data, variables, execution_path, retry_count,
                        created_at, updated_at, completed_at, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    data,
                )
                conn.commit()

            return True

        except Exception as e:
            logger.error(f"Failed to save execution state: {e}")
            return False

    async def load_execution_state(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Load workflow execution state"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM workflow_executions
                    WHERE execution_id = ?
                """,
                    (execution_id,),
                )

                row = cursor.fetchone()
                if not row:
                    return None

                # Convert back to execution context format
                execution_context = {
                    "id": row["execution_id"],
                    "workflow_id": row["workflow_id"],
                    "lead_id": row["lead_id"],
                    "current_step_id": row["current_step_id"],
                    "status": row["status"],
                    "lead_data": json.loads(row["lead_data"]),
                    "variables": json.loads(row["variables"]),
                    "execution_path": json.loads(row["execution_path"]),
                    "retry_count": row["retry_count"],
                    "started_at": self._parse_datetime(row["created_at"]),
                    "updated_at": self._parse_datetime(row["updated_at"]),
                    "completed_at": self._parse_datetime(row["completed_at"]) if row["completed_at"] else None,
                    "error": row["error_message"],
                }

                return execution_context

        except Exception as e:
            logger.error(f"Failed to load execution state: {e}")
            return None

    async def create_checkpoint(self, execution_id: str, step_id: str, checkpoint_data: Dict[str, Any]) -> bool:
        """Create execution checkpoint for rollback purposes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO workflow_checkpoints (
                        execution_id, step_id, checkpoint_data, created_at
                    ) VALUES (?, ?, ?, ?)
                """,
                    (execution_id, step_id, json.dumps(checkpoint_data), datetime.now().isoformat()),
                )
                conn.commit()

            return True

        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}")
            return False

    async def get_checkpoints(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get all checkpoints for execution"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM workflow_checkpoints
                    WHERE execution_id = ?
                    ORDER BY created_at DESC
                """,
                    (execution_id,),
                )

                checkpoints = []
                for row in cursor.fetchall():
                    checkpoints.append(
                        {
                            "id": row["id"],
                            "execution_id": row["execution_id"],
                            "step_id": row["step_id"],
                            "checkpoint_data": json.loads(row["checkpoint_data"]),
                            "created_at": self._parse_datetime(row["created_at"]),
                        }
                    )

                return checkpoints

        except Exception as e:
            logger.error(f"Failed to get checkpoints: {e}")
            return []

    async def log_workflow_event(self, execution_id: str, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Log workflow event"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO workflow_events (
                        execution_id, event_type, event_data, created_at
                    ) VALUES (?, ?, ?, ?)
                """,
                    (execution_id, event_type, json.dumps(event_data), datetime.now().isoformat()),
                )
                conn.commit()

            return True

        except Exception as e:
            logger.error(f"Failed to log workflow event: {e}")
            return False

    async def get_workflow_events(self, execution_id: str, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get workflow events"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if event_type:
                    cursor.execute(
                        """
                        SELECT * FROM workflow_events
                        WHERE execution_id = ? AND event_type = ?
                        ORDER BY created_at DESC
                    """,
                        (execution_id, event_type),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM workflow_events
                        WHERE execution_id = ?
                        ORDER BY created_at DESC
                    """,
                        (execution_id,),
                    )

                events = []
                for row in cursor.fetchall():
                    events.append(
                        {
                            "id": row["id"],
                            "execution_id": row["execution_id"],
                            "event_type": row["event_type"],
                            "event_data": json.loads(row["event_data"]),
                            "created_at": self._parse_datetime(row["created_at"]),
                        }
                    )

                return events

        except Exception as e:
            logger.error(f"Failed to get workflow events: {e}")
            return []

    async def get_executions_by_workflow(
        self, workflow_id: str, status: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get executions by workflow ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if status:
                    cursor.execute(
                        """
                        SELECT * FROM workflow_executions
                        WHERE workflow_id = ? AND status = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    """,
                        (workflow_id, status, limit),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM workflow_executions
                        WHERE workflow_id = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    """,
                        (workflow_id, limit),
                    )

                executions = []
                for row in cursor.fetchall():
                    executions.append(
                        {
                            "execution_id": row["execution_id"],
                            "workflow_id": row["workflow_id"],
                            "lead_id": row["lead_id"],
                            "current_step_id": row["current_step_id"],
                            "status": row["status"],
                            "retry_count": row["retry_count"],
                            "created_at": self._parse_datetime(row["created_at"]),
                            "updated_at": self._parse_datetime(row["updated_at"]),
                            "completed_at": self._parse_datetime(row["completed_at"]) if row["completed_at"] else None,
                            "error_message": row["error_message"],
                        }
                    )

                return executions

        except Exception as e:
            logger.error(f"Failed to get executions by workflow: {e}")
            return []

    async def get_executions_by_lead(
        self, lead_id: str, status: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get executions by lead ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if status:
                    cursor.execute(
                        """
                        SELECT * FROM workflow_executions
                        WHERE lead_id = ? AND status = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    """,
                        (lead_id, status, limit),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM workflow_executions
                        WHERE lead_id = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                    """,
                        (lead_id, limit),
                    )

                executions = []
                for row in cursor.fetchall():
                    executions.append(
                        {
                            "execution_id": row["execution_id"],
                            "workflow_id": row["workflow_id"],
                            "lead_id": row["lead_id"],
                            "current_step_id": row["current_step_id"],
                            "status": row["status"],
                            "retry_count": row["retry_count"],
                            "created_at": self._parse_datetime(row["created_at"]),
                            "updated_at": self._parse_datetime(row["updated_at"]),
                            "completed_at": self._parse_datetime(row["completed_at"]) if row["completed_at"] else None,
                            "error_message": row["error_message"],
                        }
                    )

                return executions

        except Exception as e:
            logger.error(f"Failed to get executions by lead: {e}")
            return []

    async def get_active_executions(self) -> List[Dict[str, Any]]:
        """Get all currently active (running/paused) executions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM workflow_executions
                    WHERE status IN ('running', 'paused')
                    ORDER BY created_at DESC
                """)

                executions = []
                for row in cursor.fetchall():
                    executions.append(
                        {
                            "execution_id": row["execution_id"],
                            "workflow_id": row["workflow_id"],
                            "lead_id": row["lead_id"],
                            "current_step_id": row["current_step_id"],
                            "status": row["status"],
                            "retry_count": row["retry_count"],
                            "created_at": self._parse_datetime(row["created_at"]),
                            "updated_at": self._parse_datetime(row["updated_at"]),
                        }
                    )

                return executions

        except Exception as e:
            logger.error(f"Failed to get active executions: {e}")
            return []

    async def cleanup_old_data(self, days_to_keep: int = 30, keep_failed: bool = True) -> Tuple[int, int, int]:
        """Clean up old workflow data"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.isoformat()

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get count of records to delete
                cursor = conn.cursor()

                if keep_failed:
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM workflow_executions
                        WHERE created_at < ? AND status NOT IN ('failed', 'error')
                    """,
                        (cutoff_str,),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT COUNT(*) FROM workflow_executions
                        WHERE created_at < ?
                    """,
                        (cutoff_str,),
                    )

                executions_to_delete = cursor.fetchone()[0]

                # Get execution IDs to delete for cascading cleanup
                if keep_failed:
                    cursor.execute(
                        """
                        SELECT execution_id FROM workflow_executions
                        WHERE created_at < ? AND status NOT IN ('failed', 'error')
                    """,
                        (cutoff_str,),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT execution_id FROM workflow_executions
                        WHERE created_at < ?
                    """,
                        (cutoff_str,),
                    )

                execution_ids = [row[0] for row in cursor.fetchall()]

                # Delete related records first
                checkpoints_deleted = 0
                events_deleted = 0

                if execution_ids:
                    placeholders = ",".join(["?"] * len(execution_ids))

                    # Delete checkpoints
                    cursor.execute(
                        f"""
                        DELETE FROM workflow_checkpoints
                        WHERE execution_id IN ({placeholders})
                    """,
                        execution_ids,
                    )
                    checkpoints_deleted = cursor.rowcount

                    # Delete events
                    cursor.execute(
                        f"""
                        DELETE FROM workflow_events
                        WHERE execution_id IN ({placeholders})
                    """,
                        execution_ids,
                    )
                    events_deleted = cursor.rowcount

                    # Delete executions
                    if keep_failed:
                        cursor.execute(
                            """
                            DELETE FROM workflow_executions
                            WHERE created_at < ? AND status NOT IN ('failed', 'error')
                        """,
                            (cutoff_str,),
                        )
                    else:
                        cursor.execute(
                            """
                            DELETE FROM workflow_executions
                            WHERE created_at < ?
                        """,
                            (cutoff_str,),
                        )

                conn.commit()

                logger.info(
                    f"Cleanup completed: {executions_to_delete} executions, "
                    f"{checkpoints_deleted} checkpoints, {events_deleted} events deleted"
                )

                return executions_to_delete, checkpoints_deleted, events_deleted

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return 0, 0, 0

    async def get_execution_statistics(self, workflow_id: Optional[str] = None, days_back: int = 30) -> Dict[str, Any]:
        """Get execution statistics"""
        start_date = datetime.now() - timedelta(days=days_back)
        start_str = start_date.isoformat()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Base query condition
                base_condition = "created_at >= ?"
                params = [start_str]

                if workflow_id:
                    base_condition += " AND workflow_id = ?"
                    params.append(workflow_id)

                # Total executions
                cursor.execute(
                    f"""
                    SELECT COUNT(*) FROM workflow_executions
                    WHERE {base_condition}
                """,
                    params,
                )
                total_executions = cursor.fetchone()[0]

                # Executions by status
                cursor.execute(
                    f"""
                    SELECT status, COUNT(*) FROM workflow_executions
                    WHERE {base_condition}
                    GROUP BY status
                """,
                    params,
                )
                status_counts = dict(cursor.fetchall())

                # Average execution time for completed workflows
                cursor.execute(
                    f"""
                    SELECT AVG(
                        (julianday(completed_at) - julianday(created_at)) * 86400
                    ) as avg_duration_seconds
                    FROM workflow_executions
                    WHERE {base_condition} AND status = 'completed'
                    AND completed_at IS NOT NULL
                """,
                    params,
                )
                avg_duration_result = cursor.fetchone()
                avg_duration_seconds = avg_duration_result[0] if avg_duration_result[0] else 0

                # Daily execution counts
                cursor.execute(
                    f"""
                    SELECT DATE(created_at) as execution_date, COUNT(*) as count
                    FROM workflow_executions
                    WHERE {base_condition}
                    GROUP BY DATE(created_at)
                    ORDER BY execution_date DESC
                    LIMIT 30
                """,
                    params,
                )
                daily_counts = dict(cursor.fetchall())

                return {
                    "total_executions": total_executions,
                    "status_counts": status_counts,
                    "avg_duration_seconds": round(avg_duration_seconds, 2) if avg_duration_seconds else 0,
                    "daily_counts": daily_counts,
                    "success_rate": round(status_counts.get("completed", 0) / total_executions * 100, 2)
                    if total_executions > 0
                    else 0,
                }

        except Exception as e:
            logger.error(f"Failed to get execution statistics: {e}")
            return {}

    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object"""
        if not datetime_str:
            return None
        try:
            return datetime.fromisoformat(datetime_str)
        except (ValueError, TypeError):
            return None

    async def export_execution_data(
        self, execution_id: str, include_events: bool = True, include_checkpoints: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Export complete execution data"""
        try:
            execution_state = await self.load_execution_state(execution_id)
            if not execution_state:
                return None

            export_data = {"execution_state": execution_state, "events": [], "checkpoints": []}

            if include_events:
                export_data["events"] = await self.get_workflow_events(execution_id)

            if include_checkpoints:
                export_data["checkpoints"] = await self.get_checkpoints(execution_id)

            return export_data

        except Exception as e:
            logger.error(f"Failed to export execution data: {e}")
            return None

    async def import_execution_data(self, import_data: Dict[str, Any]) -> bool:
        """Import execution data (for backup restoration)"""
        try:
            execution_state = import_data.get("execution_state")
            if not execution_state:
                return False

            # Import execution state
            success = await self.save_execution_state(execution_state["id"], execution_state)

            if not success:
                return False

            # Import events
            for event in import_data.get("events", []):
                await self.log_workflow_event(event["execution_id"], event["event_type"], event["event_data"])

            # Import checkpoints
            for checkpoint in import_data.get("checkpoints", []):
                await self.create_checkpoint(
                    checkpoint["execution_id"], checkpoint["step_id"], checkpoint["checkpoint_data"]
                )

            return True

        except Exception as e:
            logger.error(f"Failed to import execution data: {e}")
            return False

    async def backup_database(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            with sqlite3.connect(self.db_path) as source:
                with sqlite3.connect(backup_path) as backup:
                    source.backup(backup)

            logger.info(f"Database backup created: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False

    async def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False

            # Create backup of current database
            current_backup = f"{self.db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            await self.backup_database(current_backup)

            # Restore from backup
            with sqlite3.connect(backup_path) as source:
                with sqlite3.connect(self.db_path) as target:
                    source.backup(target)

            logger.info(f"Database restored from: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
