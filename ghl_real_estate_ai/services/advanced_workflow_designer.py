"""
Advanced Visual Workflow Designer

Interactive workflow builder with drag-and-drop interface, real-time validation,
and intelligent suggestions. Supports conditional logic, multi-channel sequencing,
and advanced automation rules.

Features:
- Visual workflow builder
- Real-time validation and suggestions
- Template-based workflow creation
- Advanced condition builder
- Multi-channel coordination
- Performance simulation
"""

import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of workflow nodes"""

    START = "start"
    ACTION = "action"
    CONDITION = "condition"
    DELAY = "delay"
    SPLIT = "split"
    MERGE = "merge"
    END = "end"
    TRIGGER = "trigger"


class ValidationType(Enum):
    """Validation rule types"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


@dataclass
class WorkflowNode:
    """Visual workflow node representation"""

    node_id: str
    node_type: NodeType
    name: str
    description: str
    position: Dict[str, float]  # {x, y} coordinates
    config: Dict[str, Any] = field(default_factory=dict)
    connections: List[str] = field(default_factory=list)  # Connected node IDs
    validation_status: str = "pending"
    validation_messages: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class WorkflowConnection:
    """Connection between workflow nodes"""

    connection_id: str
    source_node_id: str
    target_node_id: str
    condition: Optional[Dict[str, Any]] = None
    label: str = ""


@dataclass
class ValidationResult:
    """Workflow validation result"""

    is_valid: bool
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class WorkflowDesign:
    """Complete workflow design"""

    design_id: str
    name: str
    description: str
    nodes: Dict[str, WorkflowNode]
    connections: Dict[str, WorkflowConnection]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1


class AdvancedWorkflowDesigner:
    """Advanced visual workflow designer"""

    def __init__(self, template_library=None, action_registry=None):
        self.designs: Dict[str, WorkflowDesign] = {}
        self.template_library = template_library
        self.action_registry = action_registry

        # Node templates for quick creation
        self.node_templates = self._initialize_node_templates()

        # Validation rules
        self.validation_rules = self._initialize_validation_rules()

    def _initialize_node_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize node templates for common actions"""

        return {
            "smart_email": {
                "name": "Smart Email",
                "description": "Send personalized email with intelligent timing",
                "node_type": NodeType.ACTION,
                "icon": "email",
                "color": "#3b82f6",
                "config_schema": {
                    "subject": {"type": "string", "required": True, "placeholder": "Email subject"},
                    "template_id": {"type": "select", "options": ["welcome", "follow_up", "nurture"]},
                    "personalization_level": {"type": "select", "options": ["basic", "advanced", "premium"]},
                    "timing_optimization": {"type": "boolean", "default": True},
                },
            },
            "smart_sms": {
                "name": "Smart SMS",
                "description": "Send personalized SMS with timing optimization",
                "node_type": NodeType.ACTION,
                "icon": "message-circle",
                "color": "#10b981",
                "config_schema": {
                    "message": {"type": "textarea", "required": True, "placeholder": "SMS message"},
                    "timing_check": {"type": "boolean", "default": True},
                    "character_limit": {"type": "number", "default": 160},
                },
            },
            "lead_scoring": {
                "name": "Lead Scoring",
                "description": "Update lead score based on behavior",
                "node_type": NodeType.ACTION,
                "icon": "trending-up",
                "color": "#8b5cf6",
                "config_schema": {
                    "scoring_factors": {"type": "multi-select", "options": ["behavioral", "demographic", "engagement"]},
                    "weight_adjustment": {"type": "number", "min": 0, "max": 100},
                },
            },
            "property_matching": {
                "name": "Property Matching",
                "description": "Find and send matching properties",
                "node_type": NodeType.ACTION,
                "icon": "home",
                "color": "#f59e0b",
                "config_schema": {
                    "max_properties": {"type": "number", "default": 5, "min": 1, "max": 20},
                    "match_criteria": {"type": "json", "placeholder": "Matching criteria"},
                    "include_new_listings": {"type": "boolean", "default": True},
                },
            },
            "wait_delay": {
                "name": "Wait/Delay",
                "description": "Add delay between actions",
                "node_type": NodeType.DELAY,
                "icon": "clock",
                "color": "#6b7280",
                "config_schema": {
                    "delay_type": {"type": "select", "options": ["fixed", "smart_timing", "business_hours"]},
                    "delay_amount": {"type": "number", "required": True},
                    "delay_unit": {"type": "select", "options": ["minutes", "hours", "days"]},
                },
            },
            "condition_check": {
                "name": "Condition Check",
                "description": "Branch workflow based on conditions",
                "node_type": NodeType.CONDITION,
                "icon": "git-branch",
                "color": "#ef4444",
                "config_schema": {
                    "conditions": {"type": "condition_builder"},
                    "logic_operator": {"type": "select", "options": ["AND", "OR"]},
                    "true_path": {"type": "string", "placeholder": "True condition path"},
                    "false_path": {"type": "string", "placeholder": "False condition path"},
                },
            },
        }

    def _initialize_validation_rules(self) -> List[Dict[str, Any]]:
        """Initialize workflow validation rules"""

        return [
            {
                "rule_id": "start_node_required",
                "type": ValidationType.ERROR,
                "message": "Workflow must have exactly one start node",
                "check": lambda design: len([n for n in design.nodes.values() if n.node_type == NodeType.START]) == 1,
            },
            {
                "rule_id": "no_orphaned_nodes",
                "type": ValidationType.WARNING,
                "message": "Some nodes are not connected to the main workflow",
                "check": self._check_orphaned_nodes,
            },
            {
                "rule_id": "condition_branches",
                "type": ValidationType.ERROR,
                "message": "Condition nodes must have exactly 2 outgoing connections",
                "check": self._check_condition_branches,
            },
            {
                "rule_id": "circular_references",
                "type": ValidationType.ERROR,
                "message": "Workflow contains circular references",
                "check": self._check_circular_references,
            },
            {
                "rule_id": "unreachable_nodes",
                "type": ValidationType.WARNING,
                "message": "Some nodes are unreachable from start",
                "check": self._check_unreachable_nodes,
            },
        ]

    async def create_new_design(
        self, name: str, description: str = "", template_id: Optional[str] = None
    ) -> WorkflowDesign:
        """Create a new workflow design"""

        design_id = f"design_{datetime.now().timestamp()}"

        if template_id and self.template_library:
            # Create from template
            template = self.template_library.get_template(template_id)
            if template:
                nodes, connections = await self._convert_template_to_visual(template)
            else:
                nodes, connections = self._create_empty_workflow()
        else:
            # Create empty workflow
            nodes, connections = self._create_empty_workflow()

        design = WorkflowDesign(
            design_id=design_id,
            name=name,
            description=description,
            nodes=nodes,
            connections=connections,
            metadata={"source_template": template_id, "created_by": "designer", "auto_layout": True},
        )

        self.designs[design_id] = design
        logger.info(f"Created new workflow design: {name} (ID: {design_id})")

        return design

    def _create_empty_workflow(self) -> Tuple[Dict[str, WorkflowNode], Dict[str, WorkflowConnection]]:
        """Create empty workflow with just start and end nodes"""

        start_node = WorkflowNode(
            node_id="start_1",
            node_type=NodeType.START,
            name="Start",
            description="Workflow entry point",
            position={"x": 100, "y": 100},
            config={"triggers": []},
        )

        end_node = WorkflowNode(
            node_id="end_1",
            node_type=NodeType.END,
            name="End",
            description="Workflow completion",
            position={"x": 400, "y": 100},
            config={},
        )

        connection = WorkflowConnection(
            connection_id="conn_1", source_node_id="start_1", target_node_id="end_1", label="Default path"
        )

        nodes = {"start_1": start_node, "end_1": end_node}

        connections = {"conn_1": connection}

        return nodes, connections

    async def _convert_template_to_visual(
        self, template
    ) -> Tuple[Dict[str, WorkflowNode], Dict[str, WorkflowConnection]]:
        """Convert workflow template to visual design"""

        nodes = {}
        connections = {}
        y_position = 100
        x_spacing = 200

        # Create start node
        start_node = WorkflowNode(
            node_id="start_1",
            node_type=NodeType.START,
            name="Start",
            description="Workflow entry point",
            position={"x": 100, "y": y_position},
            config={"triggers": template.triggers},
        )
        nodes["start_1"] = start_node

        # Convert template steps to visual nodes
        previous_node_id = "start_1"

        for i, step in enumerate(template.steps):
            node_id = f"node_{i + 1}"
            x_position = 100 + (i + 1) * x_spacing

            # Determine node type from step type
            if step.get("type") in ["smart_email", "smart_sms", "property_matching", "lead_scoring"]:
                node_type = NodeType.ACTION
            elif "condition" in step.get("type", "").lower():
                node_type = NodeType.CONDITION
            elif step.get("type") == "wait":
                node_type = NodeType.DELAY
            else:
                node_type = NodeType.ACTION

            node = WorkflowNode(
                node_id=node_id,
                node_type=node_type,
                name=step.get("name", f"Step {i + 1}"),
                description=step.get("description", ""),
                position={"x": x_position, "y": y_position},
                config=step.get("config", {}),
                connections=[],
            )
            nodes[node_id] = node

            # Create connection from previous node
            conn_id = f"conn_{i + 1}"
            connection = WorkflowConnection(
                connection_id=conn_id, source_node_id=previous_node_id, target_node_id=node_id, label=""
            )
            connections[conn_id] = connection

            previous_node_id = node_id

        # Create end node
        end_node = WorkflowNode(
            node_id="end_1",
            node_type=NodeType.END,
            name="End",
            description="Workflow completion",
            position={"x": 100 + (len(template.steps) + 1) * x_spacing, "y": y_position},
            config={},
        )
        nodes["end_1"] = end_node

        # Connect last step to end
        if template.steps:
            final_conn = WorkflowConnection(
                connection_id=f"conn_final", source_node_id=previous_node_id, target_node_id="end_1", label=""
            )
            connections["conn_final"] = final_conn

        return nodes, connections

    async def add_node(
        self,
        design_id: str,
        node_type: str,
        position: Dict[str, float],
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Optional[WorkflowNode]:
        """Add new node to workflow design"""

        design = self.designs.get(design_id)
        if not design:
            return None

        # Generate unique node ID
        node_id = f"{node_type}_{len(design.nodes) + 1}"

        # Get node template
        template = self.node_templates.get(node_type, {})

        node = WorkflowNode(
            node_id=node_id,
            node_type=NodeType(template.get("node_type", NodeType.ACTION)),
            name=name or template.get("name", node_type.title()),
            description=template.get("description", ""),
            position=position,
            config=config or {},
            connections=[],
        )

        design.nodes[node_id] = node
        design.updated_at = datetime.now()

        # Auto-validate
        await self._auto_validate_design(design)

        logger.debug(f"Added node {node_id} to design {design_id}")
        return node

    async def connect_nodes(
        self,
        design_id: str,
        source_node_id: str,
        target_node_id: str,
        condition: Optional[Dict[str, Any]] = None,
        label: str = "",
    ) -> Optional[WorkflowConnection]:
        """Create connection between two nodes"""

        design = self.designs.get(design_id)
        if not design:
            return None

        # Validate nodes exist
        if source_node_id not in design.nodes or target_node_id not in design.nodes:
            return None

        # Generate connection ID
        conn_id = f"conn_{source_node_id}_{target_node_id}"

        connection = WorkflowConnection(
            connection_id=conn_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            condition=condition,
            label=label,
        )

        design.connections[conn_id] = connection

        # Update node connections
        design.nodes[source_node_id].connections.append(target_node_id)

        design.updated_at = datetime.now()

        # Auto-validate
        await self._auto_validate_design(design)

        logger.debug(f"Connected {source_node_id} -> {target_node_id} in design {design_id}")
        return connection

    async def update_node_config(self, design_id: str, node_id: str, config: Dict[str, Any]) -> bool:
        """Update node configuration"""

        design = self.designs.get(design_id)
        if not design or node_id not in design.nodes:
            return False

        node = design.nodes[node_id]
        node.config.update(config)
        design.updated_at = datetime.now()

        # Validate updated configuration
        validation_result = await self._validate_node_config(node)
        node.validation_messages = validation_result

        logger.debug(f"Updated config for node {node_id} in design {design_id}")
        return True

    async def delete_node(self, design_id: str, node_id: str) -> bool:
        """Delete node and its connections"""

        design = self.designs.get(design_id)
        if not design or node_id not in design.nodes:
            return False

        # Cannot delete start or end nodes
        node = design.nodes[node_id]
        if node.node_type in [NodeType.START, NodeType.END]:
            return False

        # Remove connections involving this node
        connections_to_remove = []
        for conn_id, connection in design.connections.items():
            if connection.source_node_id == node_id or connection.target_node_id == node_id:
                connections_to_remove.append(conn_id)

        for conn_id in connections_to_remove:
            del design.connections[conn_id]

        # Remove node
        del design.nodes[node_id]

        # Update other nodes' connection lists
        for other_node in design.nodes.values():
            if node_id in other_node.connections:
                other_node.connections.remove(node_id)

        design.updated_at = datetime.now()
        await self._auto_validate_design(design)

        logger.debug(f"Deleted node {node_id} from design {design_id}")
        return True

    async def validate_design(self, design_id: str) -> ValidationResult:
        """Comprehensive validation of workflow design"""

        design = self.designs.get(design_id)
        if not design:
            return ValidationResult(is_valid=False, errors=[{"message": "Design not found", "type": "critical"}])

        errors = []
        warnings = []
        suggestions = []

        # Run all validation rules
        for rule in self.validation_rules:
            try:
                if not rule["check"](design):
                    validation_item = {
                        "rule_id": rule["rule_id"],
                        "message": rule["message"],
                        "type": rule["type"].value,
                    }

                    if rule["type"] == ValidationType.ERROR:
                        errors.append(validation_item)
                    elif rule["type"] == ValidationType.WARNING:
                        warnings.append(validation_item)
                    elif rule["type"] == ValidationType.INFO:
                        suggestions.append(validation_item)

            except Exception as e:
                logger.error(f"Validation rule {rule['rule_id']} failed: {e}")

        # Additional intelligent suggestions
        suggestions.extend(await self._generate_suggestions(design))

        is_valid = len(errors) == 0

        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings, suggestions=suggestions)

    async def _auto_validate_design(self, design: WorkflowDesign):
        """Auto-validate design and update node status"""

        validation = await self.validate_design(design.design_id)

        # Update overall design validation status
        design.metadata["validation_status"] = "valid" if validation.is_valid else "invalid"
        design.metadata["last_validation"] = datetime.now().isoformat()

        # Update individual node validation status
        for node in design.nodes.values():
            node_validation = await self._validate_node(node, design)
            if node_validation:
                node.validation_status = "valid" if len(node_validation) == 0 else "warning"
                node.validation_messages = node_validation

    async def _validate_node(self, node: WorkflowNode, design: WorkflowDesign) -> List[Dict[str, str]]:
        """Validate individual node"""

        messages = []

        # Check required config fields
        if node.node_type == NodeType.ACTION:
            template = self.node_templates.get(node.name.lower().replace(" ", "_"), {})
            config_schema = template.get("config_schema", {})

            for field, schema in config_schema.items():
                if schema.get("required", False) and field not in node.config:
                    messages.append(
                        {"type": "error", "field": field, "message": f"Required field '{field}' is missing"}
                    )

        # Check connection requirements
        if node.node_type == NodeType.CONDITION and len(node.connections) != 2:
            messages.append(
                {
                    "type": "error",
                    "field": "connections",
                    "message": "Condition nodes must have exactly 2 outgoing connections",
                }
            )

        return messages

    async def _validate_node_config(self, node: WorkflowNode) -> List[Dict[str, str]]:
        """Validate node configuration against schema"""

        messages = []

        # Get template schema
        template = self.node_templates.get(node.name.lower().replace(" ", "_"), {})
        config_schema = template.get("config_schema", {})

        for field, schema in config_schema.items():
            value = node.config.get(field)

            # Required field check
            if schema.get("required", False) and (value is None or value == ""):
                messages.append({"type": "error", "field": field, "message": f"Field '{field}' is required"})
                continue

            if value is not None:
                # Type validation
                field_type = schema.get("type")
                if field_type == "number" and not isinstance(value, (int, float)):
                    messages.append({"type": "error", "field": field, "message": f"Field '{field}' must be a number"})

                # Range validation
                if field_type == "number":
                    min_val = schema.get("min")
                    max_val = schema.get("max")
                    if min_val is not None and value < min_val:
                        messages.append(
                            {"type": "warning", "field": field, "message": f"Value should be at least {min_val}"}
                        )
                    if max_val is not None and value > max_val:
                        messages.append(
                            {"type": "warning", "field": field, "message": f"Value should be at most {max_val}"}
                        )

        return messages

    def _check_orphaned_nodes(self, design: WorkflowDesign) -> bool:
        """Check for orphaned nodes not connected to main flow"""

        # Get all nodes in connections
        connected_nodes = set()
        for connection in design.connections.values():
            connected_nodes.add(connection.source_node_id)
            connected_nodes.add(connection.target_node_id)

        # Check if all nodes are connected
        all_nodes = set(design.nodes.keys())
        return len(all_nodes - connected_nodes) == 0

    def _check_condition_branches(self, design: WorkflowDesign) -> bool:
        """Check condition nodes have correct number of branches"""

        for node in design.nodes.values():
            if node.node_type == NodeType.CONDITION:
                outgoing_connections = len([c for c in design.connections.values() if c.source_node_id == node.node_id])
                if outgoing_connections != 2:
                    return False
        return True

    def _check_circular_references(self, design: WorkflowDesign) -> bool:
        """Check for circular references using DFS"""

        def has_cycle(node_id, visited, rec_stack):
            visited.add(node_id)
            rec_stack.add(node_id)

            # Check all connected nodes
            connected_nodes = [c.target_node_id for c in design.connections.values() if c.source_node_id == node_id]

            for connected_node in connected_nodes:
                if connected_node not in visited:
                    if has_cycle(connected_node, visited, rec_stack):
                        return True
                elif connected_node in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        visited = set()
        rec_stack = set()

        for node_id in design.nodes.keys():
            if node_id not in visited:
                if has_cycle(node_id, visited, rec_stack):
                    return False

        return True

    def _check_unreachable_nodes(self, design: WorkflowDesign) -> bool:
        """Check if all nodes are reachable from start"""

        # Find start node
        start_nodes = [n for n in design.nodes.values() if n.node_type == NodeType.START]
        if not start_nodes:
            return False

        start_node_id = start_nodes[0].node_id

        # BFS to find all reachable nodes
        visited = set()
        queue = [start_node_id]

        while queue:
            current_node = queue.pop(0)
            if current_node in visited:
                continue

            visited.add(current_node)

            # Add connected nodes to queue
            connected_nodes = [
                c.target_node_id for c in design.connections.values() if c.source_node_id == current_node
            ]
            queue.extend(connected_nodes)

        # Check if all nodes are reachable
        return len(visited) == len(design.nodes)

    async def _generate_suggestions(self, design: WorkflowDesign) -> List[Dict[str, Any]]:
        """Generate intelligent suggestions for workflow improvement"""

        suggestions = []

        # Suggest adding delays between actions
        action_nodes = [n for n in design.nodes.values() if n.node_type == NodeType.ACTION]
        consecutive_actions = 0

        for node in action_nodes:
            # Check if next node is also an action
            next_nodes = [
                design.nodes[c.target_node_id] for c in design.connections.values() if c.source_node_id == node.node_id
            ]

            if any(n.node_type == NodeType.ACTION for n in next_nodes):
                consecutive_actions += 1

        if consecutive_actions > 0:
            suggestions.append(
                {
                    "type": "optimization",
                    "message": f"Consider adding delays between {consecutive_actions} consecutive actions",
                    "action": "add_delays",
                    "priority": "medium",
                }
            )

        # Suggest lead scoring updates
        has_scoring = any("scoring" in n.name.lower() for n in design.nodes.values())
        if not has_scoring and len(action_nodes) > 2:
            suggestions.append(
                {
                    "type": "enhancement",
                    "message": "Consider adding lead scoring to track engagement",
                    "action": "add_lead_scoring",
                    "priority": "medium",
                }
            )

        # Suggest A/B testing for email nodes
        email_nodes = [n for n in design.nodes.values() if "email" in n.name.lower()]
        if len(email_nodes) > 0:
            suggestions.append(
                {
                    "type": "optimization",
                    "message": "Consider A/B testing your email content and timing",
                    "action": "enable_ab_testing",
                    "priority": "low",
                }
            )

        return suggestions

    async def auto_layout_design(self, design_id: str) -> bool:
        """Auto-arrange nodes in optimal layout"""

        design = self.designs.get(design_id)
        if not design:
            return False

        # Simple layered layout algorithm
        layers = self._calculate_node_layers(design)

        layer_width = 200
        node_height = 80
        layer_spacing = 150

        for layer_index, nodes_in_layer in enumerate(layers):
            y_position = 100 + layer_index * layer_spacing

            for node_index, node_id in enumerate(nodes_in_layer):
                x_position = 100 + node_index * layer_width
                design.nodes[node_id].position = {"x": x_position, "y": y_position}

        design.metadata["auto_layout_applied"] = datetime.now().isoformat()
        design.updated_at = datetime.now()

        logger.debug(f"Applied auto-layout to design {design_id}")
        return True

    def _calculate_node_layers(self, design: WorkflowDesign) -> List[List[str]]:
        """Calculate node layers for layout"""

        # Find start node
        start_nodes = [n.node_id for n in design.nodes.values() if n.node_type == NodeType.START]
        if not start_nodes:
            return []

        layers = []
        visited = set()
        current_layer = start_nodes

        while current_layer:
            layers.append(current_layer.copy())
            visited.update(current_layer)

            next_layer = []
            for node_id in current_layer:
                # Find connected nodes
                connected_nodes = [
                    c.target_node_id
                    for c in design.connections.values()
                    if c.source_node_id == node_id and c.target_node_id not in visited
                ]
                next_layer.extend(connected_nodes)

            current_layer = list(set(next_layer))  # Remove duplicates

        return layers

    async def export_to_engine_format(self, design_id: str) -> Optional[Dict[str, Any]]:
        """Export visual design to workflow engine format"""

        design = self.designs.get(design_id)
        if not design:
            return None

        # Validate before export
        validation = await self.validate_design(design_id)
        if not validation.is_valid:
            return None

        # Convert visual design to engine format
        engine_workflow = {
            "id": f"workflow_{design.design_id}",
            "name": design.name,
            "description": design.description,
            "steps": [],
            "triggers": [],
            "global_config": design.metadata,
        }

        # Get execution order
        execution_order = self._get_execution_order(design)

        for node_id in execution_order:
            node = design.nodes[node_id]

            if node.node_type in [NodeType.START, NodeType.END]:
                continue

            # Convert node to step
            step = {
                "id": node_id,
                "name": node.name,
                "type": self._map_node_type_to_action(node),
                "config": node.config.copy(),
                "branches": [],
                "default_next_step_id": None,
            }

            # Handle connections and conditions
            outgoing_connections = [c for c in design.connections.values() if c.source_node_id == node_id]

            if len(outgoing_connections) == 1:
                # Single connection
                step["default_next_step_id"] = outgoing_connections[0].target_node_id
            elif len(outgoing_connections) > 1:
                # Multiple connections (branching)
                for conn in outgoing_connections:
                    if conn.condition:
                        branch = {
                            "name": conn.label or "Branch",
                            "conditions": [conn.condition],
                            "next_step_id": conn.target_node_id,
                        }
                        step["branches"].append(branch)
                    else:
                        step["default_next_step_id"] = conn.target_node_id

            engine_workflow["steps"].append(step)

        return engine_workflow

    def _get_execution_order(self, design: WorkflowDesign) -> List[str]:
        """Get node execution order using topological sort"""

        # Simple topological sort
        in_degree = defaultdict(int)

        # Calculate in-degrees
        for connection in design.connections.values():
            in_degree[connection.target_node_id] += 1

        # Find start nodes (in-degree 0)
        queue = [node_id for node_id in design.nodes.keys() if in_degree[node_id] == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # Find connected nodes and reduce their in-degree
            connected = [c.target_node_id for c in design.connections.values() if c.source_node_id == current]

            for node_id in connected:
                in_degree[node_id] -= 1
                if in_degree[node_id] == 0:
                    queue.append(node_id)

        return result

    def _map_node_type_to_action(self, node: WorkflowNode) -> str:
        """Map visual node type to engine action type"""

        mapping = {
            "Smart Email": "smart_email",
            "Smart SMS": "smart_sms",
            "Lead Scoring": "lead_scoring",
            "Property Matching": "property_matching",
            "Wait/Delay": "wait",
            "Condition Check": "conditional_split",
        }

        return mapping.get(node.name, "generic_action")

    async def save_design(self, design_id: str) -> bool:
        """Save design to persistent storage"""

        design = self.designs.get(design_id)
        if not design:
            return False

        # In production, this would save to database
        design.version += 1
        design.updated_at = datetime.now()

        logger.info(f"Saved workflow design: {design.name} (version {design.version})")
        return True

    async def load_design(self, design_id: str) -> Optional[WorkflowDesign]:
        """Load design from persistent storage"""

        # In production, this would load from database
        return self.designs.get(design_id)

    def get_node_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available node templates for UI"""

        return self.node_templates

    def get_design_summary(self, design_id: str) -> Optional[Dict[str, Any]]:
        """Get design summary for UI"""

        design = self.designs.get(design_id)
        if not design:
            return None

        return {
            "design_id": design_id,
            "name": design.name,
            "description": design.description,
            "node_count": len(design.nodes),
            "connection_count": len(design.connections),
            "validation_status": design.metadata.get("validation_status", "pending"),
            "created_at": design.created_at.isoformat(),
            "updated_at": design.updated_at.isoformat(),
            "version": design.version,
        }

    async def duplicate_design(self, design_id: str, new_name: str) -> Optional[WorkflowDesign]:
        """Create a copy of existing design"""

        original = self.designs.get(design_id)
        if not original:
            return None

        new_design_id = f"design_{datetime.now().timestamp()}"

        # Deep copy nodes and connections with new IDs
        new_nodes = {}
        new_connections = {}
        node_id_mapping = {}

        # Create new nodes with new IDs
        for old_node_id, node in original.nodes.items():
            new_node_id = f"{node.node_type.value}_{len(new_nodes) + 1}"
            node_id_mapping[old_node_id] = new_node_id

            new_node = WorkflowNode(
                node_id=new_node_id,
                node_type=node.node_type,
                name=node.name,
                description=node.description,
                position=node.position.copy(),
                config=node.config.copy(),
                connections=[],
                validation_status="pending",
                validation_messages=[],
            )
            new_nodes[new_node_id] = new_node

        # Create new connections with updated node IDs
        for old_conn_id, connection in original.connections.items():
            new_conn_id = f"conn_{len(new_connections) + 1}"
            new_source_id = node_id_mapping[connection.source_node_id]
            new_target_id = node_id_mapping[connection.target_node_id]

            new_connection = WorkflowConnection(
                connection_id=new_conn_id,
                source_node_id=new_source_id,
                target_node_id=new_target_id,
                condition=connection.condition.copy() if connection.condition else None,
                label=connection.label,
            )
            new_connections[new_conn_id] = new_connection

            # Update node connections
            new_nodes[new_source_id].connections.append(new_target_id)

        duplicated_design = WorkflowDesign(
            design_id=new_design_id,
            name=new_name,
            description=f"Copy of {original.description}",
            nodes=new_nodes,
            connections=new_connections,
            metadata=original.metadata.copy(),
            version=1,
        )

        self.designs[new_design_id] = duplicated_design

        logger.info(f"Duplicated design {design_id} as {new_design_id}")
        return duplicated_design
