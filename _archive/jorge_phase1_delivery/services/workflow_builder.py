"""
Smart Workflow Builder Service
Visual drag-and-drop workflow automation creator

Feature 9: Smart Workflow Builder
Allows Jorge's team to create custom automation sequences without code.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class TriggerType(Enum):
    """Types of workflow triggers"""
    LEAD_CREATED = "lead_created"
    STATUS_CHANGED = "status_changed"
    MESSAGE_RECEIVED = "message_received"
    TIME_BASED = "time_based"
    BEHAVIOR_BASED = "behavior_based"
    TAG_ADDED = "tag_added"
    SCORE_THRESHOLD = "score_threshold"
    NO_RESPONSE = "no_response"


class ActionType(Enum):
    """Types of workflow actions"""
    SEND_SMS = "send_sms"
    SEND_EMAIL = "send_email"
    UPDATE_STATUS = "update_status"
    ASSIGN_AGENT = "assign_agent"
    ADD_TAG = "add_tag"
    REMOVE_TAG = "remove_tag"
    CREATE_TASK = "create_task"
    WAIT = "wait"
    WEBHOOK = "webhook"
    UPDATE_FIELD = "update_field"


class ConditionOperator(Enum):
    """Condition operators for if/then logic"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"


@dataclass
class WorkflowTrigger:
    """Workflow trigger configuration"""
    trigger_type: str
    conditions: Dict[str, Any]
    enabled: bool = True


@dataclass
class WorkflowCondition:
    """Conditional logic for workflow branching"""
    field: str
    operator: str
    value: Any
    next_action_id: Optional[str] = None


@dataclass
class WorkflowAction:
    """Individual workflow action"""
    action_id: str
    action_type: str
    config: Dict[str, Any]
    conditions: List[WorkflowCondition]
    next_action_id: Optional[str] = None
    delay_seconds: int = 0


@dataclass
class Workflow:
    """Complete workflow definition"""
    workflow_id: str
    name: str
    description: str
    trigger: WorkflowTrigger
    actions: List[WorkflowAction]
    enabled: bool = True
    created_at: str = None
    updated_at: str = None
    created_by: str = "system"
    execution_count: int = 0
    success_count: int = 0
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.utcnow().isoformat()


class WorkflowBuilderService:
    """Service for creating and managing workflows"""
    
    def __init__(self, data_dir: str = "data/workflows"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.workflows: Dict[str, Workflow] = {}
        self._load_workflows()
    
    def _load_workflows(self):
        """Load existing workflows from disk"""
        for workflow_file in self.data_dir.glob("*.json"):
            try:
                with open(workflow_file, 'r') as f:
                    data = json.load(f)
                    workflow = self._dict_to_workflow(data)
                    self.workflows[workflow.workflow_id] = workflow
            except Exception as e:
                print(f"Error loading workflow {workflow_file}: {e}")
    
    def _dict_to_workflow(self, data: Dict) -> Workflow:
        """Convert dictionary to Workflow object"""
        trigger = WorkflowTrigger(**data['trigger'])
        actions = [
            WorkflowAction(
                action_id=a['action_id'],
                action_type=a['action_type'],
                config=a['config'],
                conditions=[WorkflowCondition(**c) for c in a.get('conditions', [])],
                next_action_id=a.get('next_action_id'),
                delay_seconds=a.get('delay_seconds', 0)
            )
            for a in data['actions']
        ]
        return Workflow(
            workflow_id=data['workflow_id'],
            name=data['name'],
            description=data['description'],
            trigger=trigger,
            actions=actions,
            enabled=data.get('enabled', True),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            created_by=data.get('created_by', 'system'),
            execution_count=data.get('execution_count', 0),
            success_count=data.get('success_count', 0)
        )
    
    def _workflow_to_dict(self, workflow: Workflow) -> Dict:
        """Convert Workflow object to dictionary"""
        return {
            'workflow_id': workflow.workflow_id,
            'name': workflow.name,
            'description': workflow.description,
            'trigger': asdict(workflow.trigger),
            'actions': [
                {
                    'action_id': a.action_id,
                    'action_type': a.action_type,
                    'config': a.config,
                    'conditions': [asdict(c) for c in a.conditions],
                    'next_action_id': a.next_action_id,
                    'delay_seconds': a.delay_seconds
                }
                for a in workflow.actions
            ],
            'enabled': workflow.enabled,
            'created_at': workflow.created_at,
            'updated_at': workflow.updated_at,
            'created_by': workflow.created_by,
            'execution_count': workflow.execution_count,
            'success_count': workflow.success_count
        }
    
    def create_workflow(
        self,
        name: str,
        description: str,
        trigger: WorkflowTrigger,
        actions: List[WorkflowAction],
        created_by: str = "user"
    ) -> Workflow:
        """Create a new workflow"""
        workflow = Workflow(
            workflow_id=str(uuid.uuid4()),
            name=name,
            description=description,
            trigger=trigger,
            actions=actions,
            created_by=created_by
        )
        
        self.workflows[workflow.workflow_id] = workflow
        self._save_workflow(workflow)
        return workflow
    
    def _save_workflow(self, workflow: Workflow):
        """Save workflow to disk"""
        workflow.updated_at = datetime.utcnow().isoformat()
        workflow_file = self.data_dir / f"{workflow.workflow_id}.json"
        with open(workflow_file, 'w') as f:
            json.dump(self._workflow_to_dict(workflow), f, indent=2)
    
    def update_workflow(self, workflow_id: str, **updates) -> Optional[Workflow]:
        """Update an existing workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        for key, value in updates.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)
        
        self._save_workflow(workflow)
        return workflow
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow"""
        if workflow_id not in self.workflows:
            return False
        
        del self.workflows[workflow_id]
        workflow_file = self.data_dir / f"{workflow_id}.json"
        if workflow_file.exists():
            workflow_file.unlink()
        return True
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a specific workflow"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self, enabled_only: bool = False) -> List[Workflow]:
        """List all workflows"""
        workflows = list(self.workflows.values())
        if enabled_only:
            workflows = [w for w in workflows if w.enabled]
        return sorted(workflows, key=lambda w: w.created_at, reverse=True)
    
    def execute_workflow(self, workflow_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow with given context"""
        workflow = self.workflows.get(workflow_id)
        if not workflow or not workflow.enabled:
            return {"success": False, "error": "Workflow not found or disabled"}
        
        workflow.execution_count += 1
        results = []
        
        try:
            # Execute actions in sequence
            current_action_id = workflow.actions[0].action_id if workflow.actions else None
            
            while current_action_id:
                action = next((a for a in workflow.actions if a.action_id == current_action_id), None)
                if not action:
                    break
                
                # Check conditions
                if action.conditions:
                    condition_met = self._evaluate_conditions(action.conditions, context)
                    if not condition_met:
                        current_action_id = action.next_action_id
                        continue
                
                # Execute action
                action_result = self._execute_action(action, context)
                results.append(action_result)
                
                # Move to next action
                current_action_id = action.next_action_id
            
            workflow.success_count += 1
            self._save_workflow(workflow)
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "actions_executed": len(results),
                "results": results
            }
        
        except Exception as e:
            return {
                "success": False,
                "workflow_id": workflow_id,
                "error": str(e)
            }
    
    def _evaluate_conditions(self, conditions: List[WorkflowCondition], context: Dict) -> bool:
        """Evaluate if conditions are met"""
        for condition in conditions:
            field_value = context.get(condition.field)
            
            if condition.operator == ConditionOperator.EQUALS.value:
                if field_value != condition.value:
                    return False
            elif condition.operator == ConditionOperator.GREATER_THAN.value:
                if not (field_value and field_value > condition.value):
                    return False
            elif condition.operator == ConditionOperator.CONTAINS.value:
                if not (field_value and condition.value in str(field_value)):
                    return False
            # Add more operators as needed
        
        return True
    
    def _execute_action(self, action: WorkflowAction, context: Dict) -> Dict:
        """Execute a single action"""
        # This is a mock implementation
        # In production, this would call actual GHL API, send SMS, etc.
        
        action_type = action.action_type
        config = action.config
        
        if action_type == ActionType.SEND_SMS.value:
            return {
                "action": "send_sms",
                "to": context.get('phone'),
                "message": config.get('message', ''),
                "status": "sent"
            }
        elif action_type == ActionType.SEND_EMAIL.value:
            return {
                "action": "send_email",
                "to": context.get('email'),
                "subject": config.get('subject', ''),
                "status": "sent"
            }
        elif action_type == ActionType.UPDATE_STATUS.value:
            return {
                "action": "update_status",
                "new_status": config.get('status'),
                "status": "updated"
            }
        elif action_type == ActionType.WAIT.value:
            return {
                "action": "wait",
                "delay_seconds": action.delay_seconds,
                "status": "waiting"
            }
        else:
            return {
                "action": action_type,
                "status": "executed"
            }
    
    def get_workflow_templates(self) -> List[Dict]:
        """Get pre-built workflow templates"""
        return [
            {
                "name": "New Lead Auto-Response",
                "description": "Instantly respond to new leads within 60 seconds",
                "template_id": "new_lead_response",
                "category": "lead_management"
            },
            {
                "name": "Re-engagement Sequence",
                "description": "Win back cold leads with 5-message sequence",
                "template_id": "reengagement",
                "category": "nurture"
            },
            {
                "name": "Appointment Reminder",
                "description": "Send reminders 24h, 2h, and 30min before appointments",
                "template_id": "appointment_reminder",
                "category": "appointments"
            },
            {
                "name": "Hot Lead Fast Track",
                "description": "Priority handling for high-score leads",
                "template_id": "hot_lead",
                "category": "lead_management"
            },
            {
                "name": "No-Response Follow-up",
                "description": "Automatic follow-up after 48h of no response",
                "template_id": "no_response",
                "category": "follow_up"
            }
        ]
    
    def create_from_template(self, template_id: str, customizations: Dict = None) -> Optional[Workflow]:
        """Create a workflow from a template"""
        templates = {
            "new_lead_response": self._template_new_lead_response,
            "reengagement": self._template_reengagement,
            "hot_lead": self._template_hot_lead
        }
        
        template_func = templates.get(template_id)
        if not template_func:
            return None
        
        return template_func(customizations or {})
    
    def _template_new_lead_response(self, customizations: Dict) -> Workflow:
        """Template: New Lead Auto-Response"""
        trigger = WorkflowTrigger(
            trigger_type=TriggerType.LEAD_CREATED.value,
            conditions={}
        )
        
        actions = [
            WorkflowAction(
                action_id="action_1",
                action_type=ActionType.SEND_SMS.value,
                config={
                    "message": customizations.get('message', 
                        "Hi {name}! Thanks for your interest. I'm {agent_name} and I'll help you find your perfect property. What brings you here today?")
                },
                conditions=[],
                delay_seconds=60  # Wait 60 seconds
            ),
            WorkflowAction(
                action_id="action_2",
                action_type=ActionType.UPDATE_STATUS.value,
                config={
                    "status": "contacted"
                },
                conditions=[],
                next_action_id=None
            )
        ]
        
        actions[0].next_action_id = "action_2"
        
        return self.create_workflow(
            name="New Lead Auto-Response",
            description="Instantly respond to new leads",
            trigger=trigger,
            actions=actions,
            created_by="template"
        )
    
    def _template_reengagement(self, customizations: Dict) -> Workflow:
        """Template: Re-engagement Sequence"""
        trigger = WorkflowTrigger(
            trigger_type=TriggerType.NO_RESPONSE.value,
            conditions={"days": 30}
        )
        
        actions = [
            WorkflowAction(
                action_id="action_1",
                action_type=ActionType.SEND_SMS.value,
                config={
                    "message": "Hi {name}, checking in! Still interested in finding your dream property?"
                },
                conditions=[],
                delay_seconds=0
            ),
            WorkflowAction(
                action_id="action_2",
                action_type=ActionType.WAIT.value,
                config={},
                conditions=[],
                delay_seconds=86400 * 3  # 3 days
            ),
            WorkflowAction(
                action_id="action_3",
                action_type=ActionType.SEND_EMAIL.value,
                config={
                    "subject": "New properties that match your criteria",
                    "message": "Thought you might be interested in these..."
                },
                conditions=[],
                delay_seconds=0
            )
        ]
        
        # Link actions
        actions[0].next_action_id = "action_2"
        actions[1].next_action_id = "action_3"
        
        return self.create_workflow(
            name="Re-engagement Sequence",
            description="Win back cold leads",
            trigger=trigger,
            actions=actions,
            created_by="template"
        )
    
    def _template_hot_lead(self, customizations: Dict) -> Workflow:
        """Template: Hot Lead Fast Track"""
        trigger = WorkflowTrigger(
            trigger_type=TriggerType.SCORE_THRESHOLD.value,
            conditions={"score": 80}
        )
        
        actions = [
            WorkflowAction(
                action_id="action_1",
                action_type=ActionType.ASSIGN_AGENT.value,
                config={
                    "priority": "high",
                    "agent_type": "senior"
                },
                conditions=[],
                delay_seconds=0
            ),
            WorkflowAction(
                action_id="action_2",
                action_type=ActionType.SEND_SMS.value,
                config={
                    "message": "Great news! I have some perfect properties for you. Can we schedule a call today?"
                },
                conditions=[],
                delay_seconds=300  # 5 minutes
            )
        ]
        
        actions[0].next_action_id = "action_2"
        
        return self.create_workflow(
            name="Hot Lead Fast Track",
            description="Priority handling for hot leads",
            trigger=trigger,
            actions=actions,
            created_by="template"
        )


# Demo/Test functions
def demo_workflow_builder():
    """Demonstrate workflow builder capabilities"""
    service = WorkflowBuilderService()
    
    print("🏗️  Smart Workflow Builder Demo\n")
    
    # Create a simple workflow
    trigger = WorkflowTrigger(
        trigger_type=TriggerType.LEAD_CREATED.value,
        conditions={}
    )
    
    actions = [
        WorkflowAction(
            action_id="send_welcome",
            action_type=ActionType.SEND_SMS.value,
            config={"message": "Welcome! Thanks for reaching out."},
            conditions=[],
            next_action_id="update_status"
        ),
        WorkflowAction(
            action_id="update_status",
            action_type=ActionType.UPDATE_STATUS.value,
            config={"status": "contacted"},
            conditions=[],
            next_action_id=None
        )
    ]
    
    workflow = service.create_workflow(
        name="Simple Welcome Workflow",
        description="Send welcome message to new leads",
        trigger=trigger,
        actions=actions
    )
    
    print(f"✅ Created workflow: {workflow.name}")
    print(f"   ID: {workflow.workflow_id}")
    print(f"   Actions: {len(workflow.actions)}")
    
    # Execute workflow
    context = {
        "lead_id": "123",
        "name": "John Doe",
        "phone": "+1234567890",
        "email": "john@example.com"
    }
    
    result = service.execute_workflow(workflow.workflow_id, context)
    print(f"\n🚀 Execution result: {result['success']}")
    print(f"   Actions executed: {result.get('actions_executed', 0)}")
    
    # List templates
    templates = service.get_workflow_templates()
    print(f"\n📋 Available templates: {len(templates)}")
    for template in templates:
        print(f"   • {template['name']}: {template['description']}")
    
    return service


if __name__ == "__main__":
    demo_workflow_builder()
