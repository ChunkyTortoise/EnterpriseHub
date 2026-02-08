"""
Enterprise ML Governance and Audit Trail System
Demonstrates compliance, lineage tracking, and governance for production ML
"""

import hashlib
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of audit events"""

    MODEL_REGISTRATION = "model_registration"
    MODEL_PROMOTION = "model_promotion"
    MODEL_DEPLOYMENT = "model_deployment"
    MODEL_ROLLBACK = "model_rollback"
    MODEL_RETIREMENT = "model_retirement"
    DATA_ACCESS = "data_access"
    PREDICTION_REQUEST = "prediction_request"
    PERFORMANCE_ALERT = "performance_alert"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_CHECK = "compliance_check"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"


class ComplianceFramework(Enum):
    """Supported compliance frameworks"""

    GDPR = "gdpr"
    CCPA = "ccpa"
    SOX = "sox"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"
    ISO27001 = "iso27001"


class RiskLevel(Enum):
    """Risk assessment levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Comprehensive audit event record"""

    # Core identification
    event_id: str
    timestamp: datetime
    event_type: EventType
    actor_id: str
    actor_type: str  # human, system, api_client
    session_id: Optional[str] = None

    # Event details
    resource_type: str = ""  # model, dataset, pipeline, deployment
    resource_id: str = ""
    resource_version: Optional[str] = None
    action: str = ""
    description: str = ""

    # Context and metadata
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    # Compliance and governance
    compliance_frameworks: List[ComplianceFramework] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    approval_required: bool = False
    approved_by: Optional[str] = None
    approval_timestamp: Optional[datetime] = None

    # Technical details
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    api_endpoint: Optional[str] = None
    request_id: Optional[str] = None
    response_status: Optional[int] = None

    # Data lineage
    input_datasets: List[str] = field(default_factory=list)
    output_datasets: List[str] = field(default_factory=list)
    parent_models: List[str] = field(default_factory=list)
    child_models: List[str] = field(default_factory=list)

    # Performance and impact
    processing_time_ms: Optional[float] = None
    data_volume_bytes: Optional[int] = None
    prediction_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["event_type"] = self.event_type.value
        data["risk_level"] = self.risk_level.value
        data["compliance_frameworks"] = [f.value for f in self.compliance_frameworks]
        if self.approval_timestamp:
            data["approval_timestamp"] = self.approval_timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEvent":
        """Create from dictionary"""
        # Convert back from serialized format
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["event_type"] = EventType(data["event_type"])
        data["risk_level"] = RiskLevel(data["risk_level"])
        data["compliance_frameworks"] = [ComplianceFramework(f) for f in data.get("compliance_frameworks", [])]
        if data.get("approval_timestamp"):
            data["approval_timestamp"] = datetime.fromisoformat(data["approval_timestamp"])
        return cls(**data)


class LineageNode:
    """Data/Model lineage node for tracking relationships"""

    def __init__(
        self,
        node_id: str,
        node_type: str,
        name: str,
        version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize lineage node"""
        self.node_id = node_id
        self.node_type = node_type  # dataset, model, pipeline, feature
        self.name = name
        self.version = version
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()

        # Relationships
        self.parents: List[str] = []  # upstream dependencies
        self.children: List[str] = []  # downstream dependencies

    def add_parent(self, parent_id: str) -> None:
        """Add parent dependency"""
        if parent_id not in self.parents:
            self.parents.append(parent_id)

    def add_child(self, child_id: str) -> None:
        """Add child dependency"""
        if child_id not in self.children:
            self.children.append(child_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "name": self.name,
            "version": self.version,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "parents": self.parents,
            "children": self.children,
        }


class AuditEventHandler(ABC):
    """Abstract base class for audit event handlers"""

    @abstractmethod
    async def handle_event(self, event: AuditEvent) -> bool:
        """Handle audit event"""
        pass


class FileAuditHandler(AuditEventHandler):
    """File-based audit event handler"""

    def __init__(self, audit_dir: str = "audit_logs"):
        """Initialize file audit handler"""
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    async def handle_event(self, event: AuditEvent) -> bool:
        """Write event to file"""
        try:
            # Organize by date
            date_dir = self.audit_dir / event.timestamp.strftime("%Y/%m/%d")
            date_dir.mkdir(parents=True, exist_ok=True)

            # Write event to hourly file
            hour_file = date_dir / f"audit_{event.timestamp.strftime('%H')}.jsonl"

            with open(hour_file, "a") as f:
                json.dump(event.to_dict(), f)
                f.write("\n")

            return True
        except Exception as e:
            logger.error(f"Failed to write audit event to file: {e}")
            return False


class ComplianceChecker:
    """
    Compliance checking and validation system

    Validates actions against various compliance frameworks
    """

    def __init__(self):
        """Initialize compliance checker"""
        self.rules: Dict[ComplianceFramework, List[Dict[str, Any]]] = {}
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load default compliance rules"""
        # GDPR rules
        self.rules[ComplianceFramework.GDPR] = [
            {
                "name": "data_retention",
                "description": "Data must not be retained beyond necessary period",
                "applies_to": ["data_access", "prediction_request"],
                "validation": self._validate_data_retention,
            },
            {
                "name": "consent_tracking",
                "description": "User consent must be tracked for data processing",
                "applies_to": ["data_access", "model_deployment"],
                "validation": self._validate_consent,
            },
            {
                "name": "right_to_explanation",
                "description": "ML predictions must be explainable",
                "applies_to": ["model_deployment", "prediction_request"],
                "validation": self._validate_explainability,
            },
        ]

        # SOC2 rules
        self.rules[ComplianceFramework.SOC2] = [
            {
                "name": "access_control",
                "description": "Access must be properly authorized",
                "applies_to": ["model_registration", "model_deployment", "data_access"],
                "validation": self._validate_access_control,
            },
            {
                "name": "change_management",
                "description": "Changes must follow approval process",
                "applies_to": ["model_promotion", "model_deployment"],
                "validation": self._validate_change_management,
            },
        ]

    def check_compliance(self, event: AuditEvent, frameworks: List[ComplianceFramework]) -> Dict[str, Any]:
        """
        Check event against compliance frameworks

        Returns compliance validation results
        """
        results = {"compliant": True, "violations": [], "warnings": [], "framework_results": {}}

        for framework in frameworks:
            framework_result = self._check_framework_compliance(event, framework)
            results["framework_results"][framework.value] = framework_result

            if not framework_result["compliant"]:
                results["compliant"] = False
                results["violations"].extend(framework_result["violations"])

            results["warnings"].extend(framework_result.get("warnings", []))

        return results

    def _check_framework_compliance(self, event: AuditEvent, framework: ComplianceFramework) -> Dict[str, Any]:
        """Check compliance for specific framework"""
        result = {"framework": framework.value, "compliant": True, "violations": [], "warnings": []}

        if framework not in self.rules:
            result["warnings"].append(f"No rules defined for {framework.value}")
            return result

        for rule in self.rules[framework]:
            if event.event_type.value in rule["applies_to"]:
                try:
                    rule_result = rule["validation"](event, rule)
                    if not rule_result["compliant"]:
                        result["compliant"] = False
                        result["violations"].append(
                            {
                                "rule": rule["name"],
                                "description": rule["description"],
                                "details": rule_result.get("details", ""),
                            }
                        )
                except Exception as e:
                    result["warnings"].append(f"Rule validation failed for {rule['name']}: {e}")

        return result

    def _validate_data_retention(self, event: AuditEvent, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data retention compliance"""
        # Example validation - in practice, this would check against data retention policies
        retention_period_days = event.metadata.get("retention_period_days", 0)
        max_retention_days = 365  # Example limit

        if retention_period_days > max_retention_days:
            return {
                "compliant": False,
                "details": f"Retention period {retention_period_days} days exceeds limit {max_retention_days}",
            }

        return {"compliant": True}

    def _validate_consent(self, event: AuditEvent, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Validate consent tracking"""
        consent_id = event.metadata.get("consent_id")
        if not consent_id:
            return {"compliant": False, "details": "Missing consent tracking for data processing"}

        return {"compliant": True}

    def _validate_explainability(self, event: AuditEvent, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Validate model explainability"""
        explainable = event.metadata.get("explainable", False)
        if not explainable:
            return {"compliant": False, "details": "Model predictions must be explainable"}

        return {"compliant": True}

    def _validate_access_control(self, event: AuditEvent, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Validate access control"""
        if event.actor_type == "human" and not event.metadata.get("authenticated"):
            return {"compliant": False, "details": "Human actor must be authenticated"}

        return {"compliant": True}

    def _validate_change_management(self, event: AuditEvent, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Validate change management process"""
        if event.approval_required and not event.approved_by:
            return {"compliant": False, "details": "Change requires approval but none provided"}

        return {"compliant": True}


class GovernanceEngine:
    """
    Main ML governance engine

    Provides comprehensive governance, audit, and compliance management
    """

    def __init__(
        self,
        event_handlers: Optional[List[AuditEventHandler]] = None,
        compliance_frameworks: Optional[List[ComplianceFramework]] = None,
    ):
        """Initialize governance engine"""
        self.event_handlers = event_handlers or [FileAuditHandler()]
        self.compliance_frameworks = compliance_frameworks or [ComplianceFramework.GDPR, ComplianceFramework.SOC2]

        self.compliance_checker = ComplianceChecker()
        self.lineage_graph: Dict[str, LineageNode] = {}
        self.audit_cache: List[AuditEvent] = []

        # Statistics
        self.stats = {"total_events": 0, "events_by_type": {}, "compliance_violations": 0, "high_risk_events": 0}

    async def record_event(
        self,
        event_type: EventType,
        actor_id: str,
        actor_type: str = "system",
        resource_type: str = "",
        resource_id: str = "",
        action: str = "",
        description: str = "",
        **kwargs,
    ) -> AuditEvent:
        """
        Record a new audit event

        Args:
            event_type: Type of event
            actor_id: ID of the actor performing the action
            actor_type: Type of actor (human, system, api_client)
            resource_type: Type of resource affected
            resource_id: ID of resource
            action: Action performed
            description: Human-readable description
            **kwargs: Additional event properties

        Returns:
            Created AuditEvent
        """
        # Create event
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type=event_type,
            actor_id=actor_id,
            actor_type=actor_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            description=description,
            **kwargs,
        )

        # Check compliance
        compliance_result = self.compliance_checker.check_compliance(event, self.compliance_frameworks)

        if not compliance_result["compliant"]:
            event.risk_level = RiskLevel.HIGH
            self.stats["compliance_violations"] += 1
            logger.warning(f"Compliance violation detected: {compliance_result['violations']}")

        # Update statistics
        self._update_statistics(event)

        # Store in cache
        self.audit_cache.append(event)
        if len(self.audit_cache) > 1000:  # Keep cache size manageable
            self.audit_cache = self.audit_cache[-500:]

        # Handle event
        for handler in self.event_handlers:
            try:
                success = await handler.handle_event(event)
                if not success:
                    logger.error(f"Event handler {handler.__class__.__name__} failed")
            except Exception as e:
                logger.error(f"Event handler {handler.__class__.__name__} error: {e}")

        logger.info(f"Recorded audit event: {event_type.value} by {actor_id}")
        return event

    def _update_statistics(self, event: AuditEvent) -> None:
        """Update governance statistics"""
        self.stats["total_events"] += 1

        event_type_str = event.event_type.value
        self.stats["events_by_type"][event_type_str] = self.stats["events_by_type"].get(event_type_str, 0) + 1

        if event.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self.stats["high_risk_events"] += 1

    def add_lineage_node(
        self,
        node_id: str,
        node_type: str,
        name: str,
        version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LineageNode:
        """Add node to lineage graph"""
        node = LineageNode(node_id, node_type, name, version, metadata)
        self.lineage_graph[node_id] = node

        # Record lineage event
        asyncio.create_task(
            self.record_event(
                event_type=EventType.MODEL_REGISTRATION if node_type == "model" else EventType.DATA_ACCESS,
                actor_id="system",
                resource_type=node_type,
                resource_id=node_id,
                action="create_lineage_node",
                description=f"Added {node_type} {name} to lineage graph",
                metadata=metadata or {},
            )
        )

        return node

    def add_lineage_relationship(self, parent_id: str, child_id: str) -> None:
        """Add relationship in lineage graph"""
        if parent_id in self.lineage_graph and child_id in self.lineage_graph:
            self.lineage_graph[parent_id].add_child(child_id)
            self.lineage_graph[child_id].add_parent(parent_id)

            logger.info(f"Added lineage relationship: {parent_id} -> {child_id}")

    def get_lineage_upstream(self, node_id: str, max_depth: int = 10) -> List[LineageNode]:
        """Get upstream lineage (parents) for a node"""
        visited = set()
        result = []

        def traverse_upstream(current_id: str, depth: int):
            if depth >= max_depth or current_id in visited:
                return

            visited.add(current_id)
            if current_id in self.lineage_graph:
                node = self.lineage_graph[current_id]
                result.append(node)

                for parent_id in node.parents:
                    traverse_upstream(parent_id, depth + 1)

        if node_id in self.lineage_graph:
            for parent_id in self.lineage_graph[node_id].parents:
                traverse_upstream(parent_id, 0)

        return result

    def get_lineage_downstream(self, node_id: str, max_depth: int = 10) -> List[LineageNode]:
        """Get downstream lineage (children) for a node"""
        visited = set()
        result = []

        def traverse_downstream(current_id: str, depth: int):
            if depth >= max_depth or current_id in visited:
                return

            visited.add(current_id)
            if current_id in self.lineage_graph:
                node = self.lineage_graph[current_id]
                result.append(node)

                for child_id in node.children:
                    traverse_downstream(child_id, depth + 1)

        if node_id in self.lineage_graph:
            for child_id in self.lineage_graph[node_id].children:
                traverse_downstream(child_id, 0)

        return result

    def query_audit_events(
        self,
        event_type: Optional[EventType] = None,
        actor_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        risk_level: Optional[RiskLevel] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Query audit events with filters"""
        results = []

        for event in reversed(self.audit_cache):  # Most recent first
            if len(results) >= limit:
                break

            # Apply filters
            if event_type and event.event_type != event_type:
                continue
            if actor_id and event.actor_id != actor_id:
                continue
            if resource_id and event.resource_id != resource_id:
                continue
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            if risk_level and event.risk_level != risk_level:
                continue

            results.append(event)

        return results

    def generate_compliance_report(self, time_period: timedelta = timedelta(days=30)) -> Dict[str, Any]:
        """Generate compliance report"""
        start_time = datetime.utcnow() - time_period
        recent_events = self.query_audit_events(start_time=start_time)

        report = {
            "report_period": {
                "start_time": start_time.isoformat(),
                "end_time": datetime.utcnow().isoformat(),
                "duration_days": time_period.days,
            },
            "summary": {"total_events": len(recent_events), "compliance_violations": 0, "high_risk_events": 0},
            "violations_by_framework": {},
            "event_types": {},
            "recommendations": [],
        }

        # Analyze events
        for event in recent_events:
            # Count event types
            event_type = event.event_type.value
            report["event_types"][event_type] = report["event_types"].get(event_type, 0) + 1

            # Count risk levels
            if event.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                report["summary"]["high_risk_events"] += 1

        # Add recommendations
        if report["summary"]["high_risk_events"] > 10:
            report["recommendations"].append(
                "High number of high-risk events detected. Review access controls and approval processes."
            )

        if report["summary"]["compliance_violations"] > 0:
            report["recommendations"].append("Compliance violations detected. Review and update compliance procedures.")

        return report

    def get_governance_dashboard(self) -> Dict[str, Any]:
        """Get governance dashboard data"""
        recent_events = self.query_audit_events(start_time=datetime.utcnow() - timedelta(hours=24), limit=50)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "statistics": self.stats.copy(),
            "recent_events": [event.to_dict() for event in recent_events[:10]],
            "lineage_nodes": len(self.lineage_graph),
            "compliance_frameworks": [f.value for f in self.compliance_frameworks],
            "risk_distribution": self._calculate_risk_distribution(recent_events),
        }

    def _calculate_risk_distribution(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Calculate risk level distribution"""
        distribution = {level.value: 0 for level in RiskLevel}

        for event in events:
            distribution[event.risk_level.value] += 1

        return distribution


# Example usage for RAG system governance
async def create_rag_governance_system():
    """Create governance system for RAG models"""
    # Initialize governance engine
    governance = GovernanceEngine(
        compliance_frameworks=[ComplianceFramework.GDPR, ComplianceFramework.SOC2, ComplianceFramework.ISO27001]
    )

    # Add lineage nodes for RAG system
    embedding_model = governance.add_lineage_node(
        node_id="text-embedding-3-large-v1.0.0",
        node_type="model",
        name="text-embedding-3-large",
        version="1.0.0",
        metadata={"model_type": "embedding", "parameters": 3072, "context_length": 8192},
    )

    vector_store = governance.add_lineage_node(
        node_id="rag-vector-store-v1",
        node_type="dataset",
        name="rag-vector-store",
        version="1.0",
        metadata={"storage_type": "chromadb", "document_count": 10000, "embedding_dimension": 3072},
    )

    # Add relationship
    governance.add_lineage_relationship(parent_id=embedding_model.node_id, child_id=vector_store.node_id)

    # Record model deployment event
    await governance.record_event(
        event_type=EventType.MODEL_DEPLOYMENT,
        actor_id="ai-engineer",
        actor_type="human",
        resource_type="model",
        resource_id="rag-api-v2.1.0",
        action="deploy_production",
        description="Deployed RAG API v2.1.0 to production environment",
        approval_required=True,
        approved_by="senior-engineer",
        approval_timestamp=datetime.utcnow(),
        metadata={
            "environment": "production",
            "deployment_type": "canary",
            "traffic_percentage": 5.0,
            "explainable": True,
            "authenticated": True,
        },
    )

    return governance


# Import asyncio for async usage
import asyncio
