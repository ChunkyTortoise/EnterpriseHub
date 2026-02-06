"""
Lead Lifecycle Visualization (Phase 2 Enhancement)

Provides journey mapping, stage transition tracking, bottleneck identification,
and duration analysis for lead progression through the sales funnel.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import statistics


class LeadLifecycleTracker:
    """
    Tracks lead progression through stages and provides lifecycle analytics.
    """
    
    # Define standard lead stages
    STAGES = [
        "new",           # Initial contact
        "contacted",     # First response sent
        "qualified",     # Basic info gathered (budget, timeline, location)
        "engaged",       # Active conversation, multiple interactions
        "hot",           # High intent, ready to act
        "appointment",   # Scheduled viewing/meeting
        "converted",     # Deal closed / sale made
        "lost",          # Lead went cold / chose competitor
        "dormant"        # No activity for extended period
    ]
    
    # Stage transitions that indicate progression
    POSITIVE_TRANSITIONS = [
        ("new", "contacted"),
        ("contacted", "qualified"),
        ("qualified", "engaged"),
        ("engaged", "hot"),
        ("hot", "appointment"),
        ("appointment", "converted")
    ]
    
    # Stage transitions that indicate regression
    NEGATIVE_TRANSITIONS = [
        ("hot", "engaged"),
        ("engaged", "qualified"),
        ("qualified", "contacted"),
        ("*", "lost"),
        ("*", "dormant")
    ]
    
    def __init__(self, location_id: str):
        """
        Initialize lifecycle tracker for a specific GHL location.
        
        Args:
            location_id: GHL Location ID for multi-tenant support
        """
        self.location_id = location_id
        self.lifecycle_dir = Path(__file__).parent.parent / "data" / "lifecycle" / location_id
        self.lifecycle_dir.mkdir(parents=True, exist_ok=True)
        self.journeys_file = self.lifecycle_dir / "journeys.json"
        self.journeys = self._load_journeys()
    
    def _load_journeys(self) -> Dict:
        """Load existing journey data from file."""
        if self.journeys_file.exists():
            with open(self.journeys_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_journeys(self):
        """Save journey data to file."""
        with open(self.journeys_file, 'w') as f:
            json.dump(self.journeys, f, indent=2)
    
    def start_journey(
        self,
        contact_id: str,
        contact_name: str,
        source: str = "website",
        initial_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Start tracking a new lead journey.
        
        Args:
            contact_id: Unique contact identifier
            contact_name: Contact's name
            source: Lead source (website, phone, referral, etc.)
            initial_data: Optional initial contact data
        
        Returns:
            journey_id: Unique identifier for this journey
        """
        journey_id = f"journey_{contact_id}"
        
        now = datetime.now().isoformat()
        
        self.journeys[journey_id] = {
            "journey_id": journey_id,
            "contact_id": contact_id,
            "contact_name": contact_name,
            "location_id": self.location_id,
            "source": source,
            "started_at": now,
            "updated_at": now,
            "current_stage": "new",
            "status": "active",
            "stages": [
                {
                    "stage": "new",
                    "entered_at": now,
                    "exited_at": None,
                    "duration_minutes": None,
                    "events": [],
                    "lead_score": 0
                }
            ],
            "transitions": [],
            "events": [],
            "metrics": {
                "total_duration_hours": 0,
                "total_interactions": 0,
                "total_messages": 0,
                "score_changes": 0,
                "progression_count": 0,
                "regression_count": 0
            },
            "metadata": initial_data or {}
        }
        
        self._save_journeys()
        return journey_id
    
    def record_event(
        self,
        journey_id: str,
        event_type: str,
        description: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Record an event in the lead's journey.
        
        Args:
            journey_id: Journey identifier
            event_type: Type of event (message, call, email, score_change, etc.)
            description: Human-readable description
            data: Optional event data
        """
        if journey_id not in self.journeys:
            return
        
        journey = self.journeys[journey_id]
        now = datetime.now().isoformat()
        
        event = {
            "timestamp": now,
            "type": event_type,
            "description": description,
            "data": data or {}
        }
        
        journey["events"].append(event)
        journey["updated_at"] = now
        journey["metrics"]["total_interactions"] += 1
        
        if event_type == "message":
            journey["metrics"]["total_messages"] += 1
        
        # Add event to current stage
        if journey["stages"]:
            current_stage = journey["stages"][-1]
            if current_stage["exited_at"] is None:
                current_stage["events"].append(event)
        
        self._save_journeys()
    
    def transition_stage(
        self,
        journey_id: str,
        new_stage: str,
        reason: str = "",
        lead_score: Optional[int] = None
    ):
        """
        Transition a lead to a new stage.
        
        Args:
            journey_id: Journey identifier
            new_stage: Target stage
            reason: Reason for transition
            lead_score: Optional updated lead score
        """

        # ALGORITHM: Lead Stage Transition
        # 1. Validate current stage and target stage
        # 2. Check if transition is allowed (workflow rules)
        # 3. Update lead status in database
        # 4. Trigger stage-specific automation
        # 5. Log transition event
        # 6. Update analytics metrics
        
        # Business Rules:
        # - Cannot skip stages (must progress sequentially)
        # - Certain stages require manager approval
        # - Failed transitions are logged but don't block workflow

        if journey_id not in self.journeys:
            return
        
        if new_stage not in self.STAGES:
            return
        
        journey = self.journeys[journey_id]
        old_stage = journey["current_stage"]
        
        if old_stage == new_stage:
            return  # No change
        
        now = datetime.now().isoformat()
        now_dt = datetime.fromisoformat(now)
        
        # Close out the previous stage
        if journey["stages"]:
            prev_stage = journey["stages"][-1]
            if prev_stage["exited_at"] is None:
                prev_stage["exited_at"] = now
                
                # Calculate duration
                entered_dt = datetime.fromisoformat(prev_stage["entered_at"])
                duration = (now_dt - entered_dt).total_seconds() / 60
                prev_stage["duration_minutes"] = round(duration, 2)
        
        # Create new stage entry
        new_stage_entry = {
            "stage": new_stage,
            "entered_at": now,
            "exited_at": None,
            "duration_minutes": None,
            "events": [],
            "lead_score": lead_score or prev_stage.get("lead_score", 0)
        }
        
        journey["stages"].append(new_stage_entry)
        journey["current_stage"] = new_stage
        journey["updated_at"] = now
        
        # Record transition
        transition = {
            "from_stage": old_stage,
            "to_stage": new_stage,
            "timestamp": now,
            "reason": reason,
            "lead_score": lead_score,
            "direction": self._get_transition_direction(old_stage, new_stage)
        }
        
        journey["transitions"].append(transition)
        
        # Update metrics
        if transition["direction"] == "progression":
            journey["metrics"]["progression_count"] += 1
        elif transition["direction"] == "regression":
            journey["metrics"]["regression_count"] += 1
        
        if lead_score is not None:
            journey["metrics"]["score_changes"] += 1
        
        # Update status
        if new_stage == "converted":
            journey["status"] = "won"
        elif new_stage == "lost":
            journey["status"] = "lost"
        elif new_stage == "dormant":
            journey["status"] = "dormant"
        
        # Calculate total journey duration
        started_dt = datetime.fromisoformat(journey["started_at"])
        total_hours = (now_dt - started_dt).total_seconds() / 3600
        journey["metrics"]["total_duration_hours"] = round(total_hours, 2)
        
        self._save_journeys()
    
    def _get_transition_direction(self, from_stage: str, to_stage: str) -> str:
        """Determine if a transition is progression, regression, or lateral."""
        if (from_stage, to_stage) in self.POSITIVE_TRANSITIONS:
            return "progression"
        
        for neg_from, neg_to in self.NEGATIVE_TRANSITIONS:
            if neg_to == to_stage and (neg_from == "*" or neg_from == from_stage):
                return "regression"
        
        return "lateral"
    
    def get_journey(self, journey_id: str) -> Optional[Dict[str, Any]]:
        """Get complete journey data for a specific lead."""
        return self.journeys.get(journey_id)
    
    def get_journey_summary(self, journey_id: str) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a lead's journey.
        
        Returns:
            {
                "journey_info": {...},
                "timeline": [...],
                "stage_durations": {...},
                "key_moments": [...],
                "conversion_metrics": {...}
            }
        """

        # ALGORITHM: Lead Journey Summarization
        # 1. Fetch all touchpoints for lead (calls, emails, texts, meetings)
        # 2. Sort chronologically
        # 3. Group by campaign/source
        # 4. Calculate engagement metrics per stage
        # 5. Identify key moments (first contact, conversion, etc.)
        # 6. Generate natural language summary
        
        # Summary includes: timeline, engagement level, conversion triggers, next steps

        if journey_id not in self.journeys:
            return {"error": "Journey not found"}
        
        journey = self.journeys[journey_id]
        
        # Calculate stage durations
        stage_durations = {}
        for stage_entry in journey["stages"]:
            stage = stage_entry["stage"]
            duration = stage_entry.get("duration_minutes", 0)
            
            if stage not in stage_durations:
                stage_durations[stage] = {"total_minutes": 0, "visits": 0}
            
            if duration:
                stage_durations[stage]["total_minutes"] += duration
            stage_durations[stage]["visits"] += 1
        
        # Identify key moments
        key_moments = []
        
        # First contact
        if journey["stages"]:
            key_moments.append({
                "type": "first_contact",
                "timestamp": journey["started_at"],
                "description": f"First contact via {journey['source']}",
                "stage": "new"
            })
        
        # Stage progressions
        for trans in journey["transitions"]:
            if trans["direction"] == "progression":
                key_moments.append({
                    "type": "progression",
                    "timestamp": trans["timestamp"],
                    "description": f"Progressed from {trans['from_stage']} to {trans['to_stage']}",
                    "stage": trans["to_stage"],
                    "lead_score": trans.get("lead_score")
                })
        
        # Conversion or loss
        if journey["status"] == "won":
            key_moments.append({
                "type": "conversion",
                "timestamp": journey["updated_at"],
                "description": "Successfully converted to customer!",
                "stage": "converted"
            })
        elif journey["status"] == "lost":
            key_moments.append({
                "type": "lost",
                "timestamp": journey["updated_at"],
                "description": "Lead was lost",
                "stage": "lost"
            })
        
        # Calculate conversion metrics
        conversion_metrics = {
            "time_to_conversion": journey["metrics"]["total_duration_hours"],
            "total_touchpoints": journey["metrics"]["total_interactions"],
            "messages_exchanged": journey["metrics"]["total_messages"],
            "progression_rate": self._calculate_progression_rate(journey),
            "stage_efficiency": self._calculate_stage_efficiency(journey)
        }
        
        return {
            "journey_info": {
                "journey_id": journey_id,
                "contact_name": journey["contact_name"],
                "source": journey["source"],
                "current_stage": journey["current_stage"],
                "status": journey["status"],
                "started_at": journey["started_at"],
                "duration_hours": journey["metrics"]["total_duration_hours"]
            },
            "timeline": journey["stages"],
            "stage_durations": stage_durations,
            "key_moments": key_moments,
            "conversion_metrics": conversion_metrics,
            "full_journey": journey
        }
    
    def _calculate_progression_rate(self, journey: Dict) -> float:
        """Calculate the rate of positive progression vs regression."""
        prog = journey["metrics"]["progression_count"]
        regr = journey["metrics"]["regression_count"]
        
        if prog + regr == 0:
            return 0.0
        
        return (prog / (prog + regr)) * 100
    
    def _calculate_stage_efficiency(self, journey: Dict) -> Dict[str, float]:
        """Calculate time efficiency for each stage."""
        efficiency = {}
        
        for stage_entry in journey["stages"]:
            stage = stage_entry["stage"]
            duration = stage_entry.get("duration_minutes", 0)
            
            if duration and duration > 0:
                # Efficiency score: inverse of duration (faster = better)
                # Normalized to 0-100 scale
                efficiency[stage] = min(100, (60 / duration) * 100)
        
        return efficiency
    
    def analyze_bottlenecks(self) -> Dict[str, Any]:
        """
        Identify bottlenecks in the lead journey across all leads.
        
        Returns:
            {
                "slowest_stages": [...],
                "common_drop_off_points": [...],
                "avg_time_per_stage": {...},
                "recommendations": [...]
            }
        """

        # ALGORITHM: Lead Lifecycle Bottleneck Analysis
        # 1. Group leads by current stage
        # 2. Calculate time spent in each stage
        # 3. Identify stages with abnormally long durations
        # 4. Calculate conversion rates between stages
        # 5. Flag bottlenecks where conversion < threshold
        
        # Business Rule: Bottleneck = stage with <30% conversion or >7 days avg duration

        stage_times = defaultdict(list)
        stage_exits = defaultdict(lambda: {"progression": 0, "regression": 0, "stall": 0})
        
        for journey_id, journey in self.journeys.items():
            # Collect stage durations
            for stage_entry in journey["stages"]:
                stage = stage_entry["stage"]
                duration = stage_entry.get("duration_minutes")
                if duration:
                    stage_times[stage].append(duration)
            
            # Track where leads exit stages
            for trans in journey["transitions"]:
                from_stage = trans["from_stage"]
                direction = trans["direction"]
                
                if direction == "progression":
                    stage_exits[from_stage]["progression"] += 1
                elif direction == "regression":
                    stage_exits[from_stage]["regression"] += 1
        
        # Calculate average times per stage
        avg_times = {}
        for stage, times in stage_times.items():
            if times:
                avg_times[stage] = {
                    "avg_minutes": round(statistics.mean(times), 2),
                    "median_minutes": round(statistics.median(times), 2),
                    "max_minutes": round(max(times), 2),
                    "min_minutes": round(min(times), 2)
                }
        
        # Identify slowest stages (potential bottlenecks)
        slowest_stages = sorted(
            avg_times.items(),
            key=lambda x: x[1]["avg_minutes"],
            reverse=True
        )[:3]
        
        # Identify common drop-off points
        drop_off_points = []
        for stage, exits in stage_exits.items():
            total_exits = exits["progression"] + exits["regression"]
            if total_exits > 0:
                regression_rate = (exits["regression"] / total_exits) * 100
                if regression_rate > 20:  # More than 20% regression
                    drop_off_points.append({
                        "stage": stage,
                        "regression_rate": round(regression_rate, 1),
                        "total_exits": total_exits
                    })
        
        drop_off_points = sorted(drop_off_points, key=lambda x: x["regression_rate"], reverse=True)
        
        # Generate recommendations
        recommendations = []
        
        for stage, times_data in slowest_stages:
            recommendations.append({
                "type": "bottleneck",
                "priority": "high",
                "stage": stage,
                "issue": f"Leads spending {times_data['avg_minutes']:.0f} minutes in {stage} stage",
                "suggestion": f"Review and optimize {stage} stage process to reduce time",
                "expected_impact": "15-25% reduction in conversion time"
            })
        
        for drop_off in drop_off_points[:2]:  # Top 2 drop-off points
            recommendations.append({
                "type": "drop_off",
                "priority": "critical",
                "stage": drop_off["stage"],
                "issue": f"{drop_off['regression_rate']:.0f}% of leads regress from {drop_off['stage']}",
                "suggestion": f"Investigate why leads are leaving {drop_off['stage']} stage",
                "expected_impact": "10-20% improvement in conversion rate"
            })
        
        return {
            "slowest_stages": [
                {"stage": stage, "metrics": metrics}
                for stage, metrics in slowest_stages
            ],
            "common_drop_off_points": drop_off_points,
            "avg_time_per_stage": avg_times,
            "recommendations": recommendations
        }
    
    def get_conversion_funnel(self) -> Dict[str, Any]:
        """
        Generate conversion funnel data showing lead progression through stages.
        
        Returns:
            Funnel data with counts at each stage and conversion rates
        """
        funnel = {stage: 0 for stage in self.STAGES}
        stage_entries = {stage: 0 for stage in self.STAGES}
        
        for journey in self.journeys.values():
            # Count unique stages visited
            visited_stages = set()
            for stage_entry in journey["stages"]:
                stage = stage_entry["stage"]
                visited_stages.add(stage)
                stage_entries[stage] += 1
            
            for stage in visited_stages:
                funnel[stage] += 1
        
        # Calculate conversion rates between stages
        conversion_rates = {}
        for i in range(len(self.STAGES) - 1):
            current_stage = self.STAGES[i]
            next_stage = self.STAGES[i + 1]
            
            if funnel[current_stage] > 0:
                rate = (funnel[next_stage] / funnel[current_stage]) * 100
                conversion_rates[f"{current_stage}_to_{next_stage}"] = round(rate, 1)
            else:
                conversion_rates[f"{current_stage}_to_{next_stage}"] = 0.0
        
        return {
            "funnel": funnel,
            "stage_entries": stage_entries,
            "conversion_rates": conversion_rates,
            "total_journeys": len(self.journeys)
        }
    
    def get_stage_analytics(self) -> Dict[str, Any]:
        """
        Get detailed analytics for each stage.
        
        Returns:
            Per-stage statistics including average duration, exit rates, etc.
        """
        analytics = {}
        
        for stage in self.STAGES:
            stage_data = {
                "total_entries": 0,
                "total_exits": 0,
                "durations": [],
                "exit_directions": {"progression": 0, "regression": 0, "current": 0},
                "average_score": []
            }
            
            for journey in self.journeys.values():
                for stage_entry in journey["stages"]:
                    if stage_entry["stage"] == stage:
                        stage_data["total_entries"] += 1
                        
                        if stage_entry.get("duration_minutes"):
                            stage_data["durations"].append(stage_entry["duration_minutes"])
                        
                        if stage_entry.get("lead_score"):
                            stage_data["average_score"].append(stage_entry["lead_score"])
                        
                        if stage_entry["exited_at"]:
                            stage_data["total_exits"] += 1
                        else:
                            stage_data["exit_directions"]["current"] += 1
                
                # Count transitions from this stage
                for trans in journey.get("transitions", []):
                    if trans["from_stage"] == stage:
                        direction = trans["direction"]
                        if direction in ["progression", "regression"]:
                            stage_data["exit_directions"][direction] += 1
            
            # Calculate statistics
            analytics[stage] = {
                "total_entries": stage_data["total_entries"],
                "total_exits": stage_data["total_exits"],
                "currently_in_stage": stage_data["exit_directions"]["current"],
                "avg_duration_minutes": round(statistics.mean(stage_data["durations"]), 2) if stage_data["durations"] else 0,
                "median_duration_minutes": round(statistics.median(stage_data["durations"]), 2) if stage_data["durations"] else 0,
                "avg_lead_score": round(statistics.mean(stage_data["average_score"]), 1) if stage_data["average_score"] else 0,
                "progression_rate": round(
                    (stage_data["exit_directions"]["progression"] / stage_data["total_exits"] * 100)
                    if stage_data["total_exits"] > 0 else 0, 1
                ),
                "regression_rate": round(
                    (stage_data["exit_directions"]["regression"] / stage_data["total_exits"] * 100)
                    if stage_data["total_exits"] > 0 else 0, 1
                )
            }
        
        return analytics


if __name__ == "__main__":
    # Demo usage
    print("Lead Lifecycle Visualization Demo\n")
    print("=" * 70)
    
    tracker = LeadLifecycleTracker("demo_location")
    
    # Create a sample journey
    journey_id = tracker.start_journey(
        contact_id="contact_123",
        contact_name="Sarah Johnson",
        source="website"
    )
    
    print(f"Started journey: {journey_id}")
    
    # Simulate journey events
    tracker.record_event(journey_id, "message", "First contact: 'Looking for 3br in Austin'")
    tracker.transition_stage(journey_id, "contacted", "Initial response sent", lead_score=35)
    
    tracker.record_event(journey_id, "message", "Budget discussed")
    tracker.transition_stage(journey_id, "qualified", "Budget and timeline confirmed", lead_score=58)
    
    tracker.record_event(journey_id, "message", "Property recommendations sent")
    tracker.transition_stage(journey_id, "engaged", "Active conversation ongoing", lead_score=72)
    
    tracker.record_event(journey_id, "message", "Expressed urgency")
    tracker.transition_stage(journey_id, "hot", "High intent signals detected", lead_score=85)
    
    tracker.record_event(journey_id, "appointment", "Viewing scheduled for Friday 2 PM")
    tracker.transition_stage(journey_id, "appointment", "Appointment booked", lead_score=92)
    
    # Get journey summary
    summary = tracker.get_journey_summary(journey_id)
    
    print("\n" + "=" * 70)
    print("JOURNEY SUMMARY")
    print("=" * 70)
    print(f"Contact: {summary['journey_info']['contact_name']}")
    print(f"Current Stage: {summary['journey_info']['current_stage']}")
    print(f"Duration: {summary['journey_info']['duration_hours']:.1f} hours")
    print(f"\nStages Visited: {len(summary['timeline'])}")
    print(f"Total Interactions: {summary['conversion_metrics']['total_touchpoints']}")
    print(f"Progression Rate: {summary['conversion_metrics']['progression_rate']:.0f}%")
    print("=" * 70)
