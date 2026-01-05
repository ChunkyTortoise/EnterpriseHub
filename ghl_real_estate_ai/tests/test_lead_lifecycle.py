"""
Tests for Lead Lifecycle Tracking and Visualization.

Tests journey tracking, stage transitions, bottleneck identification, and analytics.
"""
import pytest
import json
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta
from ghl_real_estate_ai.services.lead_lifecycle import LeadLifecycleTracker


@pytest.fixture
def test_location_id():
    """Provide a test location ID."""
    return "test_location_lifecycle"


@pytest.fixture
def lifecycle_tracker(test_location_id):
    """Create a lifecycle tracker instance for testing."""
    tracker = LeadLifecycleTracker(test_location_id)
    yield tracker
    # Cleanup
    lifecycle_dir = Path(__file__).parent.parent / "data" / "lifecycle" / test_location_id
    if lifecycle_dir.exists():
        shutil.rmtree(lifecycle_dir)


class TestJourneyCreation:
    """Test journey initialization and basic tracking."""
    
    def test_start_journey(self, lifecycle_tracker):
        """Test starting a new lead journey."""
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_123",
            contact_name="John Doe",
            source="website"
        )
        
        assert journey_id == "journey_contact_123"
        assert journey_id in lifecycle_tracker.journeys
        
        journey = lifecycle_tracker.journeys[journey_id]
        assert journey["contact_name"] == "John Doe"
        assert journey["source"] == "website"
        assert journey["current_stage"] == "new"
        assert journey["status"] == "active"
        assert len(journey["stages"]) == 1
        assert journey["stages"][0]["stage"] == "new"
    
    def test_start_journey_with_initial_data(self, lifecycle_tracker):
        """Test starting journey with initial metadata."""
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_456",
            contact_name="Jane Smith",
            source="referral",
            initial_data={"budget": 500000, "location": "Austin"}
        )
        
        journey = lifecycle_tracker.journeys[journey_id]
        assert journey["metadata"]["budget"] == 500000
        assert journey["metadata"]["location"] == "Austin"
    
    def test_journey_initial_stage(self, lifecycle_tracker):
        """Test that new journeys start in 'new' stage."""
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_789",
            contact_name="Bob Wilson",
            source="phone"
        )
        
        journey = lifecycle_tracker.journeys[journey_id]
        assert journey["current_stage"] == "new"
        assert journey["stages"][0]["entered_at"] is not None
        assert journey["stages"][0]["exited_at"] is None


class TestEventRecording:
    """Test event tracking within journeys."""
    
    def test_record_simple_event(self, lifecycle_tracker):
        """Test recording a basic event."""
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_event1",
            contact_name="Alice Brown",
            source="website"
        )
        
        lifecycle_tracker.record_event(
            journey_id,
            "message",
            "First contact message",
            {"content": "Looking for a house"}
        )
        
        journey = lifecycle_tracker.journeys[journey_id]
        assert len(journey["events"]) == 1
        assert journey["events"][0]["type"] == "message"
        assert journey["events"][0]["description"] == "First contact message"
        assert journey["metrics"]["total_interactions"] == 1
        assert journey["metrics"]["total_messages"] == 1
    
    def test_record_multiple_events(self, lifecycle_tracker):
        """Test recording multiple events."""
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_event2",
            contact_name="Charlie Davis",
            source="email"
        )
        
        lifecycle_tracker.record_event(journey_id, "message", "Initial inquiry")
        lifecycle_tracker.record_event(journey_id, "call", "Phone conversation")
        lifecycle_tracker.record_event(journey_id, "email", "Follow-up email sent")
        
        journey = lifecycle_tracker.journeys[journey_id]
        assert len(journey["events"]) == 3
        assert journey["metrics"]["total_interactions"] == 3
        assert journey["metrics"]["total_messages"] == 1  # Only one message type
    
    def test_events_added_to_current_stage(self, lifecycle_tracker):
        """Test that events are tracked in the current stage."""
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_event3",
            contact_name="Diana Evans",
            source="website"
        )
        
        lifecycle_tracker.record_event(journey_id, "message", "Event in new stage")
        
        journey = lifecycle_tracker.journeys[journey_id]
        current_stage = journey["stages"][-1]
        assert len(current_stage["events"]) == 1
        assert current_stage["events"][0]["description"] == "Event in new stage"


class TestStageTransitions:
    """Test stage transition logic."""
    
    def test_transition_to_next_stage(self, lifecycle_tracker):
        """Test transitioning to a new stage."""
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_trans1",
            contact_name="Eve Foster",
            source="website"
        )
        
        time.sleep(0.01)  # Small delay to ensure duration calculation
        
        lifecycle_tracker.transition_stage(
            journey_id,
            "contacted",
            "First response sent",
            lead_score=35
        )
        
        journey = lifecycle_tracker.journeys[journey_id]
        assert journey["current_stage"] == "contacted"
        assert len(journey["stages"]) == 2
        assert len(journey["transitions"]) == 1
        
        # Check previous stage was closed
        prev_stage = journey["stages"][0]
        assert prev_stage["exited_at"] is not None
        assert prev_stage["duration_minutes"] is not None
        
        # Check new stage
        new_stage = journey["stages"][1]
        assert new_stage["stage"] == "contacted"
        assert new_stage["lead_score"] == 35
        assert new_stage["exited_at"] is None
    
    def test_multiple_stage_transitions(self, lifecycle_tracker):
        """Test progressing through multiple stages."""
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_trans2",
            contact_name="Frank Green",
            source="referral"
        )
        
        stages_to_visit = [
            ("contacted", "Initial response", 35),
            ("qualified", "Budget confirmed", 58),
            ("engaged", "Active conversation", 72),
            ("hot", "High intent", 85)
        ]
        
        for stage, reason, score in stages_to_visit:
            time.sleep(0.01)
            lifecycle_tracker.transition_stage(journey_id, stage, reason, score)
        
        journey = lifecycle_tracker.journeys[journey_id]
        assert journey["current_stage"] == "hot"
        assert len(journey["stages"]) == 5  # new + 4 transitions
        assert len(journey["transitions"]) == 4
        assert journey["metrics"]["progression_count"] == 4
    
    def test_transition_direction_progression(self, lifecycle_tracker):
        """Test that positive transitions are marked as progression."""
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_trans3",
            contact_name="Grace Hill",
            source="website"
        )
        
        lifecycle_tracker.transition_stage(journey_id, "contacted", "Response sent")
        
        journey = lifecycle_tracker.journeys[journey_id]
        transition = journey["transitions"][0]
        assert transition["direction"] == "progression"
        assert journey["metrics"]["progression_count"] == 1
        assert journey["metrics"]["regression_count"] == 0
    
    def test_transition_direction_regression(self, lifecycle_tracker):
        """Test that negative transitions are marked as regression."""
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_trans4",
            contact_name="Henry Irving",
            source="website"
        )
        
        # Progress to hot
        lifecycle_tracker.transition_stage(journey_id, "contacted")
        time.sleep(0.01)
        lifecycle_tracker.transition_stage(journey_id, "qualified")
        time.sleep(0.01)
        lifecycle_tracker.transition_stage(journey_id, "engaged")
        time.sleep(0.01)
        lifecycle_tracker.transition_stage(journey_id, "hot")
        time.sleep(0.01)
        
        # Now regress back to engaged
        lifecycle_tracker.transition_stage(journey_id, "engaged", "Lost interest")
        
        journey = lifecycle_tracker.journeys[journey_id]
        last_transition = journey["transitions"][-1]
        assert last_transition["direction"] == "regression"
        assert journey["metrics"]["regression_count"] == 1
    
    def test_conversion_to_won(self, lifecycle_tracker):
        """Test that converting to 'converted' marks journey as won."""
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_trans5",
            contact_name="Iris Jones",
            source="website"
        )
        
        lifecycle_tracker.transition_stage(journey_id, "appointment")
        time.sleep(0.01)
        lifecycle_tracker.transition_stage(journey_id, "converted", "Deal closed!")
        
        journey = lifecycle_tracker.journeys[journey_id]
        assert journey["status"] == "won"
        assert journey["current_stage"] == "converted"
    
    def test_marking_as_lost(self, lifecycle_tracker):
        """Test that transitioning to 'lost' updates status."""
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_trans6",
            contact_name="Jack Kelly",
            source="website"
        )
        
        lifecycle_tracker.transition_stage(journey_id, "lost", "Chose competitor")
        
        journey = lifecycle_tracker.journeys[journey_id]
        assert journey["status"] == "lost"


class TestJourneySummary:
    """Test journey summary generation."""
    
    def test_get_journey_summary(self, lifecycle_tracker):
        """Test generating a comprehensive journey summary."""
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_sum1",
            contact_name="Laura Martinez",
            source="website"
        )
        
        lifecycle_tracker.record_event(journey_id, "message", "Initial contact")
        lifecycle_tracker.transition_stage(journey_id, "contacted", lead_score=35)
        time.sleep(0.01)
        lifecycle_tracker.transition_stage(journey_id, "qualified", lead_score=58)
        
        summary = lifecycle_tracker.get_journey_summary(journey_id)
        
        assert "journey_info" in summary
        assert "timeline" in summary
        assert "stage_durations" in summary
        assert "key_moments" in summary
        assert "conversion_metrics" in summary
        
        assert summary["journey_info"]["contact_name"] == "Laura Martinez"
        assert summary["journey_info"]["current_stage"] == "qualified"
    
    def test_key_moments_identification(self, lifecycle_tracker):
        """Test that key moments are identified correctly."""
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_sum2",
            contact_name="Mike Nelson",
            source="referral"
        )
        
        lifecycle_tracker.transition_stage(journey_id, "contacted")
        time.sleep(0.01)
        lifecycle_tracker.transition_stage(journey_id, "qualified")
        time.sleep(0.01)
        lifecycle_tracker.transition_stage(journey_id, "converted")
        
        summary = lifecycle_tracker.get_journey_summary(journey_id)
        key_moments = summary["key_moments"]
        
        # Should have: first contact + 3 progressions + conversion
        assert len(key_moments) >= 4
        
        # Check for conversion moment
        conversion_moments = [m for m in key_moments if m["type"] == "conversion"]
        assert len(conversion_moments) == 1
    
    def test_conversion_metrics_calculation(self, lifecycle_tracker):
        """Test that conversion metrics are calculated."""
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_sum3",
            contact_name="Nancy Owens",
            source="website"
        )
        
        lifecycle_tracker.record_event(journey_id, "message", "Message 1")
        lifecycle_tracker.record_event(journey_id, "message", "Message 2")
        lifecycle_tracker.transition_stage(journey_id, "contacted")
        
        summary = lifecycle_tracker.get_journey_summary(journey_id)
        metrics = summary["conversion_metrics"]
        
        assert "time_to_conversion" in metrics
        assert "total_touchpoints" in metrics
        assert "messages_exchanged" in metrics
        assert metrics["messages_exchanged"] == 2


class TestBottleneckAnalysis:
    """Test bottleneck identification."""
    
    def test_analyze_bottlenecks_with_data(self, test_location_id):
        """Test bottleneck analysis with multiple journeys."""
        # Create fresh tracker
        tracker = LeadLifecycleTracker(test_location_id)
        
        # Create multiple journeys with varying durations
        for i in range(5):
            journey_id = tracker.start_journey(
                contact_id=f"contact_bottle_{i}",
                contact_name=f"Contact {i}",
                source="website"
            )
            
            tracker.transition_stage(journey_id, "contacted")
            time.sleep(0.02)  # Simulate time in stage
            tracker.transition_stage(journey_id, "qualified")
            time.sleep(0.05)  # Longer time in qualified (bottleneck)
            tracker.transition_stage(journey_id, "engaged")
        
        analysis = tracker.analyze_bottlenecks()
        
        assert "slowest_stages" in analysis
        assert "common_drop_off_points" in analysis
        assert "avg_time_per_stage" in analysis
        assert "recommendations" in analysis
        
        # Cleanup
        lifecycle_dir = Path(__file__).parent.parent / "data" / "lifecycle" / test_location_id
        if lifecycle_dir.exists():
            shutil.rmtree(lifecycle_dir)
    
    def test_recommendations_generated(self, lifecycle_tracker):
        """Test that recommendations are generated from analysis."""
        # Create journey with slow progression
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_rec1",
            contact_name="Paul Quinn",
            source="website"
        )
        
        lifecycle_tracker.transition_stage(journey_id, "contacted")
        time.sleep(0.1)  # Long time in contacted
        lifecycle_tracker.transition_stage(journey_id, "qualified")
        
        analysis = lifecycle_tracker.analyze_bottlenecks()
        
        if analysis["recommendations"]:
            rec = analysis["recommendations"][0]
            assert "type" in rec
            assert "priority" in rec
            assert "suggestion" in rec


class TestConversionFunnel:
    """Test conversion funnel generation."""
    
    def test_get_conversion_funnel(self, lifecycle_tracker):
        """Test generating conversion funnel data."""
        # Create journeys at different stages
        for i in range(10):
            journey_id = lifecycle_tracker.start_journey(
                contact_id=f"contact_funnel_{i}",
                contact_name=f"Contact {i}",
                source="website"
            )
            
            # Progress to different stages
            if i < 8:
                lifecycle_tracker.transition_stage(journey_id, "contacted")
            if i < 5:
                lifecycle_tracker.transition_stage(journey_id, "qualified")
            if i < 2:
                lifecycle_tracker.transition_stage(journey_id, "engaged")
        
        funnel = lifecycle_tracker.get_conversion_funnel()
        
        assert "funnel" in funnel
        assert "stage_entries" in funnel
        assert "conversion_rates" in funnel
        assert "total_journeys" in funnel
        
        assert funnel["total_journeys"] == 10
        assert funnel["funnel"]["new"] == 10
        assert funnel["funnel"]["contacted"] >= 8
    
    def test_conversion_rates_calculated(self, lifecycle_tracker):
        """Test that conversion rates between stages are calculated."""
        # Create simple funnel
        for i in range(5):
            journey_id = lifecycle_tracker.start_journey(
                contact_id=f"contact_rate_{i}",
                contact_name=f"Contact {i}",
                source="website"
            )
            
            lifecycle_tracker.transition_stage(journey_id, "contacted")
            
            if i < 3:  # 60% convert to qualified
                lifecycle_tracker.transition_stage(journey_id, "qualified")
        
        funnel = lifecycle_tracker.get_conversion_funnel()
        rates = funnel["conversion_rates"]
        
        assert "contacted_to_qualified" in rates
        assert rates["contacted_to_qualified"] == 60.0


class TestStageAnalytics:
    """Test stage-level analytics."""
    
    def test_get_stage_analytics(self, lifecycle_tracker):
        """Test getting detailed analytics per stage."""
        # Create some journeys
        for i in range(3):
            journey_id = lifecycle_tracker.start_journey(
                contact_id=f"contact_analytics_{i}",
                contact_name=f"Contact {i}",
                source="website"
            )
            
            lifecycle_tracker.transition_stage(journey_id, "contacted", lead_score=30 + i*10)
            time.sleep(0.01)
            lifecycle_tracker.transition_stage(journey_id, "qualified", lead_score=50 + i*10)
        
        analytics = lifecycle_tracker.get_stage_analytics()
        
        assert "new" in analytics
        assert "contacted" in analytics
        assert "qualified" in analytics
        
        # Check contacted stage analytics
        contacted = analytics["contacted"]
        assert contacted["total_entries"] == 3
        assert contacted["total_exits"] == 3
        assert contacted["avg_lead_score"] > 0
    
    def test_progression_rate_calculated(self, lifecycle_tracker):
        """Test that progression rates are calculated for stages."""
        # Create journey that progresses
        journey_id = lifecycle_tracker.start_journey(
            contact_id="contact_prog1",
            contact_name="Quinn Roberts",
            source="website"
        )
        
        lifecycle_tracker.transition_stage(journey_id, "contacted")
        lifecycle_tracker.transition_stage(journey_id, "qualified")
        
        analytics = lifecycle_tracker.get_stage_analytics()
        
        # Contacted stage should show 100% progression (no regressions)
        contacted = analytics["contacted"]
        assert contacted["progression_rate"] == 100.0
        assert contacted["regression_rate"] == 0.0


class TestDataPersistence:
    """Test that journey data persists correctly."""
    
    def test_journey_data_persists(self, test_location_id):
        """Test that journey data is saved and can be reloaded."""
        tracker1 = LeadLifecycleTracker(test_location_id)
        
        journey_id = tracker1.start_journey(
            contact_id="contact_persist",
            contact_name="Rita Sanders",
            source="website"
        )
        
        tracker1.record_event(journey_id, "message", "Test event")
        tracker1.transition_stage(journey_id, "contacted")
        
        # Create new tracker instance (simulates app restart)
        tracker2 = LeadLifecycleTracker(test_location_id)
        
        assert journey_id in tracker2.journeys
        journey = tracker2.journeys[journey_id]
        assert journey["contact_name"] == "Rita Sanders"
        assert journey["current_stage"] == "contacted"
        assert len(journey["events"]) == 1
        
        # Cleanup
        lifecycle_dir = Path(__file__).parent.parent / "data" / "lifecycle" / test_location_id
        if lifecycle_dir.exists():
            shutil.rmtree(lifecycle_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
