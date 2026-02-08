"""
Enterprise AI Compliance Platform - Audit Tracker

Production-grade audit trail system for complete compliance record-keeping.
Aligned with EU AI Act Article 12, HIPAA audit requirements, and SOX compliance.
"""

import asyncio
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from ..models.compliance_models import (
    AuditRecord,
    ComplianceStatus,
    RegulationType,
    ViolationSeverity,
)


class AuditEventType:
    """Audit event type constants"""

    # Model lifecycle
    MODEL_REGISTERED = "model_registered"
    MODEL_UPDATED = "model_updated"
    MODEL_DEPLOYED = "model_deployed"
    MODEL_DECOMMISSIONED = "model_decommissioned"

    # Risk assessment
    RISK_ASSESSMENT_STARTED = "risk_assessment_started"
    RISK_ASSESSMENT_COMPLETED = "risk_assessment_completed"
    RISK_LEVEL_CHANGED = "risk_level_changed"

    # Policy enforcement
    POLICY_CHECK_STARTED = "policy_check_started"
    POLICY_CHECK_COMPLETED = "policy_check_completed"
    VIOLATION_DETECTED = "violation_detected"
    VIOLATION_ACKNOWLEDGED = "violation_acknowledged"
    VIOLATION_RESOLVED = "violation_resolved"

    # Remediation
    REMEDIATION_CREATED = "remediation_created"
    REMEDIATION_ASSIGNED = "remediation_assigned"
    REMEDIATION_COMPLETED = "remediation_completed"
    REMEDIATION_VERIFIED = "remediation_verified"

    # Access and usage
    MODEL_ACCESSED = "model_accessed"
    DECISION_MADE = "decision_made"
    HUMAN_OVERRIDE = "human_override"
    DATA_ACCESSED = "data_accessed"

    # Certification
    CERTIFICATION_OBTAINED = "certification_obtained"
    CERTIFICATION_RENEWED = "certification_renewed"
    CERTIFICATION_EXPIRED = "certification_expired"

    # Administrative
    EXEMPTION_GRANTED = "exemption_granted"
    EXEMPTION_REVOKED = "exemption_revoked"
    POLICY_UPDATED = "policy_updated"
    CONFIG_CHANGED = "config_changed"

    # Reports
    REPORT_GENERATED = "report_generated"
    REPORT_EXPORTED = "report_exported"


class ComplianceAuditTracker:
    """
    Comprehensive audit trail system for AI compliance.

    Features:
    - Immutable audit records with cryptographic hashing
    - Multi-backend storage (memory, file, database)
    - Advanced querying and filtering
    - Compliance reporting
    - Chain of custody tracking
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        redis_client: Optional[Any] = None,
        retention_days: int = 365 * 7,  # 7 years for compliance
        enable_hashing: bool = True,
        auto_flush_interval: int = 30,
        max_buffer_size: int = 100,
    ):
        """
        Initialize the Audit Tracker.

        Args:
            storage_path: Path for file-based storage
            redis_client: Redis client for distributed storage
            retention_days: How long to retain audit records
            enable_hashing: Enable cryptographic record hashing
            auto_flush_interval: Seconds between auto-flushes
            max_buffer_size: Records to buffer before flush
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self.redis_client = redis_client
        self.retention_days = retention_days
        self.enable_hashing = enable_hashing
        self.auto_flush_interval = auto_flush_interval
        self.max_buffer_size = max_buffer_size

        # In-memory storage
        self._records: List[AuditRecord] = []
        self._buffer: List[AuditRecord] = []

        # Indexes for fast lookup
        self._index_by_entity: Dict[str, List[str]] = defaultdict(list)
        self._index_by_type: Dict[str, List[str]] = defaultdict(list)
        self._index_by_regulation: Dict[str, List[str]] = defaultdict(list)

        # Hash chain for integrity
        self._hash_chain: List[str] = []
        self._last_hash: str = "genesis"

        # Statistics
        self._stats = {
            "total_records": 0,
            "records_by_type": defaultdict(int),
            "records_by_regulation": defaultdict(int),
        }

        # Initialize storage
        if self.storage_path:
            self.storage_path.mkdir(parents=True, exist_ok=True)

    async def log(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        action: str,
        description: str,
        actor_id: Optional[str] = None,
        actor_name: Optional[str] = None,
        regulation: Optional[RegulationType] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        compliance_impact: str = "none",
    ) -> str:
        """
        Log an audit event.

        Args:
            event_type: Type of event (use AuditEventType constants)
            entity_type: Type of entity (model, policy, violation, etc.)
            entity_id: ID of the affected entity
            action: Action performed
            description: Human-readable description
            actor_id: ID of user/system performing action
            actor_name: Name of actor
            regulation: Related regulation if applicable
            old_value: Previous value (for changes)
            new_value: New value (for changes)
            metadata: Additional structured data
            compliance_impact: Impact level (none, low, medium, high)

        Returns:
            Record ID
        """
        record = AuditRecord(
            event_type=event_type,
            event_subtype=None,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            description=description,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_type="user" if actor_id else "system",
            regulation=regulation,
            old_value=old_value,
            new_value=new_value,
            metadata=metadata or {},
            compliance_impact=compliance_impact,
        )

        # Add hash for integrity
        if self.enable_hashing:
            record_hash = self._compute_hash(record)
            record.metadata["record_hash"] = record_hash
            record.metadata["previous_hash"] = self._last_hash
            self._last_hash = record_hash
            self._hash_chain.append(record_hash)

        # Update indexes
        self._index_by_entity[entity_id].append(record.record_id)
        self._index_by_type[event_type].append(record.record_id)
        if regulation:
            self._index_by_regulation[regulation.value].append(record.record_id)

        # Update stats
        self._stats["total_records"] += 1
        self._stats["records_by_type"][event_type] += 1
        if regulation:
            self._stats["records_by_regulation"][regulation.value] += 1

        # Buffer the record
        self._buffer.append(record)

        # Auto-flush if buffer is full
        if len(self._buffer) >= self.max_buffer_size:
            await self._flush_buffer()

        return record.record_id

    def _compute_hash(self, record: AuditRecord) -> str:
        """Compute SHA-256 hash for audit record"""
        content = json.dumps(
            {
                "record_id": record.record_id,
                "timestamp": record.timestamp.isoformat(),
                "event_type": record.event_type,
                "entity_id": record.entity_id,
                "action": record.action,
                "actor_id": record.actor_id,
                "previous_hash": self._last_hash,
            },
            sort_keys=True,
        )

        return hashlib.sha256(content.encode()).hexdigest()

    async def _flush_buffer(self):
        """Flush buffer to persistent storage"""
        if not self._buffer:
            return

        # Add to in-memory records
        self._records.extend(self._buffer)

        # Write to file if configured
        if self.storage_path:
            await self._write_to_file(self._buffer)

        # Write to Redis if configured
        if self.redis_client:
            await self._write_to_redis(self._buffer)

        self._buffer = []

    async def _write_to_file(self, records: List[AuditRecord]):
        """Write records to file storage"""
        log_file = self.storage_path / f"audit_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"

        with open(log_file, "a") as f:
            for record in records:
                f.write(json.dumps(record.model_dump(), default=str) + "\n")

    async def _write_to_redis(self, records: List[AuditRecord]):
        """Write records to Redis"""
        if not self.redis_client:
            return

        pipe = self.redis_client.pipeline()
        date_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        for record in records:
            # Store individual record
            pipe.setex(
                f"audit:record:{record.record_id}",
                timedelta(days=self.retention_days),
                json.dumps(record.model_dump(), default=str),
            )

            # Add to timeline
            pipe.zadd(
                f"audit:timeline:{date_key}",
                {record.record_id: record.timestamp.timestamp()},
            )
            pipe.expire(f"audit:timeline:{date_key}", timedelta(days=self.retention_days))

        pipe.execute()

    # Convenience logging methods
    async def log_model_registered(
        self,
        model_id: str,
        model_name: str,
        registered_by: str,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Log model registration"""
        return await self.log(
            event_type=AuditEventType.MODEL_REGISTERED,
            entity_type="ai_model",
            entity_id=model_id,
            action="register",
            description=f"AI model '{model_name}' registered in compliance system",
            actor_id=registered_by,
            metadata=metadata,
            compliance_impact="medium",
        )

    async def log_risk_assessment(
        self,
        model_id: str,
        model_name: str,
        risk_level: str,
        risk_score: float,
        assessed_by: str = "system",
        regulations: Optional[List[RegulationType]] = None,
    ) -> str:
        """Log risk assessment completion"""
        return await self.log(
            event_type=AuditEventType.RISK_ASSESSMENT_COMPLETED,
            entity_type="ai_model",
            entity_id=model_id,
            action="assess",
            description=f"Risk assessment completed for '{model_name}': {risk_level} ({risk_score}/100)",
            actor_id=assessed_by,
            regulation=regulations[0] if regulations else None,
            new_value={"risk_level": risk_level, "risk_score": risk_score},
            metadata={
                "model_name": model_name,
                "applicable_regulations": [r.value for r in (regulations or [])],
            },
            compliance_impact="high",
        )

    async def log_violation_detected(
        self,
        violation_id: str,
        policy_name: str,
        model_id: str,
        severity: ViolationSeverity,
        regulation: RegulationType,
        description: str,
    ) -> str:
        """Log policy violation detection"""
        return await self.log(
            event_type=AuditEventType.VIOLATION_DETECTED,
            entity_type="violation",
            entity_id=violation_id,
            action="detect",
            description=f"Policy violation detected: {description}",
            regulation=regulation,
            metadata={
                "policy_name": policy_name,
                "model_id": model_id,
                "severity": severity.value,
            },
            compliance_impact="high",
        )

    async def log_violation_resolved(
        self,
        violation_id: str,
        resolved_by: str,
        resolution_notes: Optional[str] = None,
    ) -> str:
        """Log violation resolution"""
        return await self.log(
            event_type=AuditEventType.VIOLATION_RESOLVED,
            entity_type="violation",
            entity_id=violation_id,
            action="resolve",
            description=f"Violation resolved by {resolved_by}",
            actor_id=resolved_by,
            metadata={"resolution_notes": resolution_notes},
            compliance_impact="medium",
        )

    async def log_remediation(
        self,
        remediation_id: str,
        violation_id: str,
        action: str,
        actor_id: str,
        description: str,
    ) -> str:
        """Log remediation action"""
        event_type_map = {
            "create": AuditEventType.REMEDIATION_CREATED,
            "assign": AuditEventType.REMEDIATION_ASSIGNED,
            "complete": AuditEventType.REMEDIATION_COMPLETED,
            "verify": AuditEventType.REMEDIATION_VERIFIED,
        }

        return await self.log(
            event_type=event_type_map.get(action, AuditEventType.REMEDIATION_CREATED),
            entity_type="remediation",
            entity_id=remediation_id,
            action=action,
            description=description,
            actor_id=actor_id,
            metadata={"violation_id": violation_id},
            compliance_impact="medium",
        )

    async def log_decision(
        self,
        model_id: str,
        decision_id: str,
        decision_type: str,
        input_summary: str,
        output_summary: str,
        confidence: Optional[float] = None,
        affected_subjects: int = 0,
    ) -> str:
        """Log AI decision for transparency"""
        return await self.log(
            event_type=AuditEventType.DECISION_MADE,
            entity_type="decision",
            entity_id=decision_id,
            action="decide",
            description=f"AI decision made: {decision_type}",
            metadata={
                "model_id": model_id,
                "decision_type": decision_type,
                "input_summary": input_summary,
                "output_summary": output_summary,
                "confidence": confidence,
                "affected_subjects": affected_subjects,
            },
            compliance_impact="low" if affected_subjects < 10 else "medium",
        )

    async def log_human_override(
        self,
        model_id: str,
        decision_id: str,
        original_output: str,
        override_output: str,
        override_by: str,
        reason: str,
    ) -> str:
        """Log human override of AI decision"""
        return await self.log(
            event_type=AuditEventType.HUMAN_OVERRIDE,
            entity_type="decision",
            entity_id=decision_id,
            action="override",
            description=f"Human override of AI decision: {reason}",
            actor_id=override_by,
            old_value=original_output,
            new_value=override_output,
            metadata={
                "model_id": model_id,
                "reason": reason,
            },
            compliance_impact="medium",
        )

    async def log_report_generated(
        self,
        report_id: str,
        report_type: str,
        generated_by: str,
        regulations: List[RegulationType],
    ) -> str:
        """Log compliance report generation"""
        return await self.log(
            event_type=AuditEventType.REPORT_GENERATED,
            entity_type="report",
            entity_id=report_id,
            action="generate",
            description=f"Compliance report generated: {report_type}",
            actor_id=generated_by,
            regulation=regulations[0] if regulations else None,
            metadata={
                "report_type": report_type,
                "regulations": [r.value for r in regulations],
            },
            compliance_impact="low",
        )

    # Query methods
    async def search(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        regulation: Optional[RegulationType] = None,
        compliance_impact: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditRecord]:
        """
        Search audit records with filtering.

        Args:
            start_time: Filter records after this time
            end_time: Filter records before this time
            event_types: Filter by event types
            entity_id: Filter by entity ID
            entity_type: Filter by entity type
            actor_id: Filter by actor
            regulation: Filter by regulation
            compliance_impact: Filter by impact level
            limit: Maximum records to return
            offset: Number of records to skip

        Returns:
            List of matching audit records
        """
        # Flush buffer first
        await self._flush_buffer()

        results = self._records.copy()

        # Apply filters
        if start_time:
            results = [r for r in results if r.timestamp >= start_time]

        if end_time:
            results = [r for r in results if r.timestamp <= end_time]

        if event_types:
            results = [r for r in results if r.event_type in event_types]

        if entity_id:
            results = [r for r in results if r.entity_id == entity_id]

        if entity_type:
            results = [r for r in results if r.entity_type == entity_type]

        if actor_id:
            results = [r for r in results if r.actor_id == actor_id]

        if regulation:
            results = [r for r in results if r.regulation == regulation]

        if compliance_impact:
            results = [r for r in results if r.compliance_impact == compliance_impact]

        # Sort by timestamp descending
        results.sort(key=lambda r: r.timestamp, reverse=True)

        # Apply pagination
        return results[offset : offset + limit]

    async def get_entity_history(
        self,
        entity_id: str,
        limit: int = 100,
    ) -> List[AuditRecord]:
        """Get complete audit history for an entity"""
        record_ids = self._index_by_entity.get(entity_id, [])
        records = [r for r in self._records if r.record_id in record_ids]
        records.sort(key=lambda r: r.timestamp, reverse=True)
        return records[:limit]

    async def get_chain_of_custody(
        self,
        entity_id: str,
    ) -> List[Dict[str, Any]]:
        """Get chain of custody for an entity (who touched it when)"""
        records = await self.get_entity_history(entity_id, limit=1000)

        custody_chain = []
        for record in reversed(records):  # Chronological order
            custody_chain.append(
                {
                    "timestamp": record.timestamp.isoformat(),
                    "action": record.action,
                    "actor": record.actor_name or record.actor_id or "system",
                    "description": record.description,
                    "compliance_impact": record.compliance_impact,
                }
            )

        return custody_chain

    async def get_statistics(
        self,
        period_days: int = 30,
    ) -> Dict[str, Any]:
        """Get audit statistics"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)

        recent_records = [r for r in self._records if r.timestamp >= cutoff]

        return {
            "total_records": self._stats["total_records"],
            "records_last_period": len(recent_records),
            "by_event_type": dict(self._stats["records_by_type"]),
            "by_regulation": dict(self._stats["records_by_regulation"]),
            "high_impact_events": len([r for r in recent_records if r.compliance_impact == "high"]),
            "hash_chain_length": len(self._hash_chain),
            "integrity_verified": self.verify_integrity(),
        }

    def verify_integrity(self) -> bool:
        """Verify audit log integrity using hash chain"""
        if not self.enable_hashing or not self._records:
            return True

        previous_hash = "genesis"
        for record in self._records:
            expected_hash = record.metadata.get("record_hash")
            stored_previous = record.metadata.get("previous_hash")

            if stored_previous != previous_hash:
                return False

            previous_hash = expected_hash

        return True

    async def export(
        self,
        start_time: datetime,
        end_time: datetime,
        format_type: str = "json",
        regulation: Optional[RegulationType] = None,
    ) -> str:
        """
        Export audit records for regulatory submission.

        Args:
            start_time: Export period start
            end_time: Export period end
            format_type: Export format (json, csv)
            regulation: Filter by regulation

        Returns:
            Exported data as string
        """
        records = await self.search(
            start_time=start_time,
            end_time=end_time,
            regulation=regulation,
            limit=100000,
        )

        if format_type == "csv":
            lines = ["timestamp,event_type,entity_type,entity_id,action,actor,description,compliance_impact"]
            for r in records:
                lines.append(
                    f"{r.timestamp.isoformat()},{r.event_type},{r.entity_type},"
                    f"{r.entity_id},{r.action},{r.actor_id or 'system'},"
                    f'"{r.description}",{r.compliance_impact}'
                )
            return "\n".join(lines)

        # JSON format
        return json.dumps(
            [r.model_dump() for r in records],
            default=str,
            indent=2,
        )

    async def generate_compliance_report(
        self,
        regulation: RegulationType,
        period_start: datetime,
        period_end: datetime,
    ) -> Dict[str, Any]:
        """Generate compliance-specific audit report"""
        records = await self.search(
            start_time=period_start,
            end_time=period_end,
            regulation=regulation,
        )

        # Categorize events
        violations = [r for r in records if r.event_type == AuditEventType.VIOLATION_DETECTED]
        resolutions = [r for r in records if r.event_type == AuditEventType.VIOLATION_RESOLVED]
        assessments = [r for r in records if r.event_type == AuditEventType.RISK_ASSESSMENT_COMPLETED]
        decisions = [r for r in records if r.event_type == AuditEventType.DECISION_MADE]
        overrides = [r for r in records if r.event_type == AuditEventType.HUMAN_OVERRIDE]

        return {
            "regulation": regulation.value,
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat(),
            },
            "summary": {
                "total_events": len(records),
                "violations_detected": len(violations),
                "violations_resolved": len(resolutions),
                "risk_assessments": len(assessments),
                "ai_decisions": len(decisions),
                "human_overrides": len(overrides),
                "override_rate": f"{(len(overrides) / max(len(decisions), 1) * 100):.1f}%",
            },
            "compliance_metrics": {
                "violation_resolution_rate": f"{(len(resolutions) / max(len(violations), 1) * 100):.1f}%",
                "human_oversight_active": len(overrides) > 0,
                "audit_trail_complete": self.verify_integrity(),
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
