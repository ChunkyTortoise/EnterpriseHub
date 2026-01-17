"""
Automation Service for Elite UI Components
Connects elite component actions to real GHL workflows and automation

This service bridges the gap between UI buttons and backend automation:
- Heatmap "Schedule Outreach" → GHL workflow scheduling
- Timeline acceleration tracking → Action logging system
- Gap analysis "Find Contractors" → External service integration
- Gap analysis "Find Alternatives" → Property search automation
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import uuid

# Import GHL services
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.workflow_builder import (
    WorkflowBuilderService, 
    WorkflowTrigger, 
    WorkflowAction,
    TriggerType,
    ActionType
)


@dataclass
class AutomationLog:
    """Log entry for automation actions"""
    log_id: str
    contact_id: str
    automation_type: str  # 'heatmap_schedule', 'timeline_action', 'gap_resolution'
    action_details: Dict[str, Any]
    status: str  # 'pending', 'scheduled', 'completed', 'failed'
    created_at: str
    executed_at: Optional[str] = None
    error_message: Optional[str] = None


class AutomationService:
    """
    Service for managing automation from elite UI components
    """
    
    def __init__(
        self, 
        ghl_client: Optional[GHLClient] = None,
        workflow_service: Optional[WorkflowBuilderService] = None,
        log_dir: str = "data/automation_logs"
    ):
        """
        Initialize automation service
        
        Args:
            ghl_client: GHL API client (creates default if None)
            workflow_service: Workflow builder service (creates default if None)
            log_dir: Directory for automation logs
        """
        self.ghl_client = ghl_client or GHLClient()
        self.workflow_service = workflow_service or WorkflowBuilderService()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def schedule_peak_outreach(
        self, 
        contact_id: str,
        peak_day: str,
        peak_hour: int,
        segment: str = "active",
        message_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Schedule outreach for peak engagement time
        Connected to: render_actionable_heatmap() "Schedule Outreach" button
        
        Args:
            contact_id: GHL contact ID
            peak_day: Day of week (e.g., "Tuesday")
            peak_hour: Hour of day (0-23)
            segment: Lead segment for targeting
            message_template: Optional custom message
            
        Returns:
            Result dict with workflow_id and schedule details
        """
        # Calculate next occurrence of peak day/hour
        next_occurrence = self._calculate_next_occurrence(peak_day, peak_hour)
        
        # Default message based on segment
        if not message_template:
            message_template = self._get_segment_message(segment)
        
        # Create time-based workflow trigger
        trigger = WorkflowTrigger(
            trigger_type=TriggerType.TIME_BASED.value,
            conditions={
                "scheduled_time": next_occurrence.isoformat(),
                "peak_day": peak_day,
                "peak_hour": peak_hour
            }
        )
        
        # Define outreach action
        actions = [
            WorkflowAction(
                action_id=str(uuid.uuid4()),
                action_type=ActionType.SEND_SMS.value,
                config={
                    "message": message_template,
                    "contact_id": contact_id
                },
                conditions=[],
                delay_seconds=0
            ),
            WorkflowAction(
                action_id=str(uuid.uuid4()),
                action_type=ActionType.ADD_TAG.value,
                config={
                    "tag": f"peak_outreach_{peak_day.lower()}"
                },
                conditions=[],
                delay_seconds=0
            )
        ]
        
        # Link actions
        actions[0].next_action_id = actions[1].action_id
        
        # Create workflow
        workflow = self.workflow_service.create_workflow(
            name=f"Peak Outreach - {peak_day} {peak_hour:02d}:00",
            description=f"Automated outreach scheduled for peak engagement: {peak_day}s at {peak_hour}:00",
            trigger=trigger,
            actions=actions,
            created_by="elite_heatmap"
        )
        
        # Log automation
        log_entry = AutomationLog(
            log_id=str(uuid.uuid4()),
            contact_id=contact_id,
            automation_type="heatmap_schedule",
            action_details={
                "workflow_id": workflow.workflow_id,
                "peak_day": peak_day,
                "peak_hour": peak_hour,
                "scheduled_time": next_occurrence.isoformat(),
                "segment": segment
            },
            status="scheduled",
            created_at=datetime.utcnow().isoformat()
        )
        
        self._save_log(log_entry)
        
        return {
            "success": True,
            "workflow_id": workflow.workflow_id,
            "scheduled_time": next_occurrence.isoformat(),
            "peak_day": peak_day,
            "peak_hour": peak_hour,
            "message": f"Outreach scheduled for next {peak_day} at {peak_hour}:00"
        }
    
    def track_timeline_action(
        self,
        contact_id: str,
        action_name: str,
        estimated_days_saved: int = 5
    ) -> Dict[str, Any]:
        """
        Track high-value action completion for timeline acceleration
        Connected to: render_dynamic_timeline() action tracking
        
        Args:
            contact_id: GHL contact ID
            action_name: Name of completed action
            estimated_days_saved: Days saved by this action
            
        Returns:
            Updated timeline metrics
        """
        # Log the action
        log_entry = AutomationLog(
            log_id=str(uuid.uuid4()),
            contact_id=contact_id,
            automation_type="timeline_action",
            action_details={
                "action_name": action_name,
                "days_saved": estimated_days_saved,
                "timestamp": datetime.utcnow().isoformat()
            },
            status="completed",
            created_at=datetime.utcnow().isoformat(),
            executed_at=datetime.utcnow().isoformat()
        )
        
        self._save_log(log_entry)
        
        # Update contact custom field with action count
        # This would integrate with GHL to store timeline metrics
        actions_completed = self._get_contact_actions_completed(contact_id) + 1
        
        # Calculate new timeline
        base_days = 45  # Default cycle time
        accelerated_days = int(base_days * (0.85 ** actions_completed))
        total_savings = base_days - accelerated_days
        
        return {
            "success": True,
            "actions_completed": actions_completed,
            "base_days": base_days,
            "accelerated_days": accelerated_days,
            "total_days_saved": total_savings,
            "latest_action": action_name
        }
    
    def execute_quick_wins(
        self,
        contact_id: str,
        actions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute all quick win actions to accelerate timeline
        Connected to: render_dynamic_timeline() "Execute All Quick Wins" button
        
        Args:
            contact_id: GHL contact ID
            actions: Optional list of specific actions (uses defaults if None)
            
        Returns:
            Execution results
        """
        # Default quick win actions
        if not actions:
            actions = [
                "Schedule property tour within 48 hours",
                "Get pre-approval confirmation",
                "Send personalized property matches",
                "Set up automated showing alerts"
            ]
        
        # Create workflow for each action
        results = []
        
        for action in actions:
            # Determine action type and configuration
            workflow_actions = self._action_to_workflow(action, contact_id)
            
            # Create trigger
            trigger = WorkflowTrigger(
                trigger_type=TriggerType.BEHAVIOR_BASED.value,
                conditions={"source": "quick_wins"}
            )
            
            # Create workflow
            workflow = self.workflow_service.create_workflow(
                name=f"Quick Win: {action[:30]}...",
                description=f"Timeline acceleration action: {action}",
                trigger=trigger,
                actions=workflow_actions,
                created_by="elite_timeline"
            )
            
            results.append({
                "action": action,
                "workflow_id": workflow.workflow_id,
                "status": "queued"
            })
            
            # Track the action
            self.track_timeline_action(contact_id, action, estimated_days_saved=5)
        
        # Log bulk execution
        log_entry = AutomationLog(
            log_id=str(uuid.uuid4()),
            contact_id=contact_id,
            automation_type="quick_wins_bulk",
            action_details={
                "actions": actions,
                "workflows_created": [r["workflow_id"] for r in results],
                "estimated_total_savings": len(actions) * 5
            },
            status="completed",
            created_at=datetime.utcnow().isoformat(),
            executed_at=datetime.utcnow().isoformat()
        )
        
        self._save_log(log_entry)
        
        return {
            "success": True,
            "actions_executed": len(actions),
            "estimated_days_saved": len(actions) * 5,
            "results": results
        }
    
    def find_contractors(
        self,
        contact_id: str,
        feature_needed: str,
        property_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Find contractors for missing property features
        Connected to: render_feature_gap() "Find Contractors" button
        
        Args:
            contact_id: GHL contact ID
            feature_needed: Feature to add (e.g., "pool", "garage")
            property_address: Optional property address for local search
            
        Returns:
            Contractor recommendations and quote requests
        """
        # Mock contractor database (in production, integrate with real services)
        contractor_categories = {
            "pool": ["Pool Installation", "Pool & Spa Contractors"],
            "garage": ["Garage Builders", "General Contractors"],
            "renovation": ["Home Remodeling", "General Contractors"],
            "landscaping": ["Landscaping", "Outdoor Design"]
        }
        
        # Determine category
        category_key = next(
            (k for k in contractor_categories.keys() if k in feature_needed.lower()),
            "renovation"
        )
        
        categories = contractor_categories[category_key]
        
        # Generate mock contractor recommendations
        contractors = []
        for i, category in enumerate(categories, 1):
            contractors.append({
                "name": f"{category} Pro {i}",
                "rating": 4.5 + (i * 0.1),
                "reviews": 120 + (i * 30),
                "estimated_cost": f"${25000 + (i * 5000):,} - ${35000 + (i * 10000):,}",
                "availability": f"{i * 2}-{i * 3} weeks",
                "phone": f"(555) {100 + i}00-{1000 + i}000"
            })
        
        # Create workflow to send contractor info
        trigger = WorkflowTrigger(
            trigger_type=TriggerType.BEHAVIOR_BASED.value,
            conditions={"source": "gap_analysis"}
        )
        
        # Format contractor list message
        contractor_message = f"Great news! I found {len(contractors)} contractors for {feature_needed}:\n\n"
        for contractor in contractors:
            contractor_message += f"• {contractor['name']} - {contractor['rating']}⭐ ({contractor['reviews']} reviews)\n"
            contractor_message += f"  Est: {contractor['estimated_cost']}, Available: {contractor['availability']}\n\n"
        contractor_message += "Would you like me to request quotes from all 3?"
        
        actions = [
            WorkflowAction(
                action_id=str(uuid.uuid4()),
                action_type=ActionType.SEND_SMS.value,
                config={"message": contractor_message},
                conditions=[],
                delay_seconds=0
            )
        ]
        
        workflow = self.workflow_service.create_workflow(
            name=f"Contractor Referrals - {feature_needed}",
            description=f"Send contractor recommendations for {feature_needed}",
            trigger=trigger,
            actions=actions,
            created_by="elite_gap_analysis"
        )
        
        # Log the action
        log_entry = AutomationLog(
            log_id=str(uuid.uuid4()),
            contact_id=contact_id,
            automation_type="gap_resolution",
            action_details={
                "feature_needed": feature_needed,
                "contractors_found": len(contractors),
                "workflow_id": workflow.workflow_id
            },
            status="completed",
            created_at=datetime.utcnow().isoformat(),
            executed_at=datetime.utcnow().isoformat()
        )
        
        self._save_log(log_entry)
        
        return {
            "success": True,
            "feature": feature_needed,
            "contractors": contractors,
            "workflow_id": workflow.workflow_id,
            "message": f"Found {len(contractors)} contractors for {feature_needed}"
        }
    
    def find_alternative_properties(
        self,
        contact_id: str,
        feature_needed: str,
        current_criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Find alternative properties with required features
        Connected to: render_feature_gap() "Find Alternatives" button
        
        Args:
            contact_id: GHL contact ID
            feature_needed: Required feature
            current_criteria: Current search criteria
            
        Returns:
            Alternative property matches
        """
        # Mock property search (in production, integrate with MLS/property database)
        alternative_properties = [
            {
                "address": f"123 {feature_needed.title()} Lane",
                "price": "$425,000",
                "beds": 3,
                "baths": 2,
                "sqft": 1850,
                "features": [feature_needed, "hardwood floors", "updated kitchen"],
                "match_score": 92
            },
            {
                "address": f"456 Perfect St",
                "price": "$445,000",
                "beds": 4,
                "baths": 2.5,
                "sqft": 2100,
                "features": [feature_needed, "large backyard", "modern appliances"],
                "match_score": 88
            },
            {
                "address": f"789 Dream Ave",
                "price": "$410,000",
                "beds": 3,
                "baths": 2,
                "sqft": 1900,
                "features": [feature_needed, "corner lot", "attached garage"],
                "match_score": 85
            }
        ]
        
        # Create workflow to send alternatives
        trigger = WorkflowTrigger(
            trigger_type=TriggerType.BEHAVIOR_BASED.value,
            conditions={"source": "gap_analysis"}
        )
        
        # Format property message
        property_message = f"Found {len(alternative_properties)} properties with {feature_needed}:\n\n"
        for prop in alternative_properties:
            property_message += f"📍 {prop['address']} - {prop['price']}\n"
            property_message += f"   {prop['beds']}bd/{prop['baths']}ba, {prop['sqft']} sqft\n"
            property_message += f"   Match: {prop['match_score']}% ✅ {feature_needed}\n\n"
        property_message += "Would you like to schedule tours?"
        
        actions = [
            WorkflowAction(
                action_id=str(uuid.uuid4()),
                action_type=ActionType.SEND_SMS.value,
                config={"message": property_message},
                conditions=[],
                delay_seconds=0
            ),
            WorkflowAction(
                action_id=str(uuid.uuid4()),
                action_type=ActionType.ADD_TAG.value,
                config={"tag": f"seeking_{feature_needed}"},
                conditions=[],
                delay_seconds=0
            )
        ]
        
        actions[0].next_action_id = actions[1].action_id
        
        workflow = self.workflow_service.create_workflow(
            name=f"Alternative Properties - {feature_needed}",
            description=f"Send properties with {feature_needed}",
            trigger=trigger,
            actions=actions,
            created_by="elite_gap_analysis"
        )
        
        # Log the action
        log_entry = AutomationLog(
            log_id=str(uuid.uuid4()),
            contact_id=contact_id,
            automation_type="gap_resolution",
            action_details={
                "feature_needed": feature_needed,
                "properties_found": len(alternative_properties),
                "workflow_id": workflow.workflow_id
            },
            status="completed",
            created_at=datetime.utcnow().isoformat(),
            executed_at=datetime.utcnow().isoformat()
        )
        
        self._save_log(log_entry)
        
        return {
            "success": True,
            "feature": feature_needed,
            "properties": alternative_properties,
            "workflow_id": workflow.workflow_id,
            "message": f"Found {len(alternative_properties)} properties with {feature_needed}"
        }
    
    # Helper methods
    
    def _calculate_next_occurrence(self, day_name: str, hour: int) -> datetime:
        """Calculate next occurrence of given day/hour"""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        target_day = days.index(day_name)
        
        now = datetime.now()
        current_day = now.weekday()
        
        # Calculate days until target
        days_ahead = target_day - current_day
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_date = now + timedelta(days=days_ahead)
        next_date = next_date.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        return next_date
    
    def _get_segment_message(self, segment: str) -> str:
        """Get default message template for segment"""
        templates = {
            "active": "Hi {name}! I have some exciting new properties that match your criteria. Available for a quick call today?",
            "warming": "Hi {name}, thought you'd be interested in these new listings in your area. Let me know if any catch your eye!",
            "attention": "Hi {name}, checking in! I have some great opportunities to share. Still looking for your perfect property?",
            "dormant": "Hi {name}, it's been a while! The market has some amazing options right now. Want to reconnect?"
        }
        return templates.get(segment, templates["active"])
    
    def _get_contact_actions_completed(self, contact_id: str) -> int:
        """Get count of completed timeline actions for contact"""
        # In production, query from database or GHL custom field
        # For now, count from logs
        log_files = list(self.log_dir.glob(f"*{contact_id}*.json"))
        count = 0
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    log = json.load(f)
                    if log.get('automation_type') == 'timeline_action':
                        count += 1
            except:
                continue
        return count
    
    def _action_to_workflow(self, action_name: str, contact_id: str) -> List[WorkflowAction]:
        """Convert action description to workflow actions"""
        # Simple mapping based on keywords
        actions = []
        
        if "tour" in action_name.lower() or "showing" in action_name.lower():
            actions.append(WorkflowAction(
                action_id=str(uuid.uuid4()),
                action_type=ActionType.SEND_SMS.value,
                config={"message": "I'd love to show you some properties! What times work best for you this week?"},
                conditions=[],
                delay_seconds=0
            ))
        elif "pre-approval" in action_name.lower():
            actions.append(WorkflowAction(
                action_id=str(uuid.uuid4()),
                action_type=ActionType.SEND_SMS.value,
                config={"message": "Getting pre-approved strengthens your offer! I can connect you with our preferred lenders today."},
                conditions=[],
                delay_seconds=0
            ))
        elif "property matches" in action_name.lower():
            actions.append(WorkflowAction(
                action_id=str(uuid.uuid4()),
                action_type=ActionType.SEND_SMS.value,
                config={"message": "I've curated a list of properties perfectly matched to your criteria. Sending them your way now!"},
                conditions=[],
                delay_seconds=0
            ))
        elif "alerts" in action_name.lower():
            actions.append(WorkflowAction(
                action_id=str(uuid.uuid4()),
                action_type=ActionType.ADD_TAG.value,
                config={"tag": "auto_alerts_enabled"},
                conditions=[],
                delay_seconds=0
            ))
        else:
            # Generic action
            actions.append(WorkflowAction(
                action_id=str(uuid.uuid4()),
                action_type=ActionType.CREATE_TASK.value,
                config={"task": action_name},
                conditions=[],
                delay_seconds=0
            ))
        
        return actions
    
    def _save_log(self, log_entry: AutomationLog):
        """Save automation log to disk"""
        log_file = self.log_dir / f"{log_entry.log_id}_{log_entry.contact_id}.json"
        with open(log_file, 'w') as f:
            json.dump(asdict(log_entry), f, indent=2)
    
    def get_automation_history(
        self, 
        contact_id: Optional[str] = None,
        automation_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get automation history with optional filters
        
        Args:
            contact_id: Filter by contact ID
            automation_type: Filter by automation type
            limit: Maximum number of logs to return
            
        Returns:
            List of automation logs
        """
        logs = []
        
        # Read all log files
        for log_file in sorted(self.log_dir.glob("*.json"), reverse=True):
            if len(logs) >= limit:
                break
                
            try:
                with open(log_file, 'r') as f:
                    log = json.load(f)
                    
                    # Apply filters
                    if contact_id and log.get('contact_id') != contact_id:
                        continue
                    if automation_type and log.get('automation_type') != automation_type:
                        continue
                    
                    logs.append(log)
            except Exception as e:
                continue
        
        return logs


# Test function
def demo_automation_service():
    """Demonstrate automation service capabilities"""
    print("🤖 Elite Automation Service Demo\n")
    
    service = AutomationService()
    test_contact_id = "test_contact_123"
    
    # Test 1: Schedule peak outreach
    print("1️⃣ Scheduling peak outreach...")
    result = service.schedule_peak_outreach(
        contact_id=test_contact_id,
        peak_day="Tuesday",
        peak_hour=14,
        segment="active"
    )
    print(f"   ✅ {result['message']}")
    print(f"   📅 Scheduled: {result['scheduled_time']}")
    
    # Test 2: Track timeline action
    print("\n2️⃣ Tracking timeline action...")
    result = service.track_timeline_action(
        contact_id=test_contact_id,
        action_name="Schedule property tour within 48 hours"
    )
    print(f"   ✅ Actions completed: {result['actions_completed']}")
    print(f"   ⏱️ Timeline: {result['base_days']}d → {result['accelerated_days']}d")
    print(f"   💾 Saved: {result['total_days_saved']} days")
    
    # Test 3: Execute quick wins
    print("\n3️⃣ Executing quick wins...")
    result = service.execute_quick_wins(contact_id=test_contact_id)
    print(f"   ✅ Actions executed: {result['actions_executed']}")
    print(f"   ⏱️ Estimated savings: {result['estimated_days_saved']} days")
    
    # Test 4: Find contractors
    print("\n4️⃣ Finding contractors...")
    result = service.find_contractors(
        contact_id=test_contact_id,
        feature_needed="pool"
    )
    print(f"   ✅ {result['message']}")
    print(f"   👷 Contractors: {len(result['contractors'])}")
    
    # Test 5: Find alternatives
    print("\n5️⃣ Finding alternative properties...")
    result = service.find_alternative_properties(
        contact_id=test_contact_id,
        feature_needed="pool"
    )
    print(f"   ✅ {result['message']}")
    print(f"   🏠 Properties: {len(result['properties'])}")
    
    # Test 6: Get automation history
    print("\n6️⃣ Retrieving automation history...")
    history = service.get_automation_history(contact_id=test_contact_id)
    print(f"   ✅ Found {len(history)} automation logs")
    for log in history:
        print(f"   • {log['automation_type']}: {log['status']}")
    
    print("\n✨ Demo complete!")


if __name__ == "__main__":
    demo_automation_service()
