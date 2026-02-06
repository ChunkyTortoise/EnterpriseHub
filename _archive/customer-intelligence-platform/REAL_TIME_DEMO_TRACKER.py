#!/usr/bin/env python3
"""
Customer Intelligence Platform - Real-Time Demo Performance Tracker

Advanced demo execution toolkit with real-time performance tracking:
- Live engagement monitoring during demos
- Automated performance scoring and success prediction
- Real-time recommendations for demo optimization
- Instant follow-up action suggestions
- Integration with client acquisition pipeline
"""

import asyncio
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import sqlite3
import uuid
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading
import time
import websocket
import requests

class RealTimeDemoTracker:
    """Real-time demo performance tracking and optimization system."""
    
    def __init__(self):
        self.db_path = Path(__file__).parent / "demo_campaigns.db"
        self.current_demo = None
        self.engagement_data = []
        self.real_time_metrics = {
            "start_time": None,
            "duration_minutes": 0,
            "questions_asked": 0,
            "engagement_score": 0.0,
            "completion_percentage": 0.0,
            "success_probability": 0.0,
            "attendee_count": 1,
            "interaction_events": []
        }
        self.demo_phases = [
            {"name": "Opening Hook", "duration": 2, "weight": 0.15},
            {"name": "Discovery", "duration": 5, "weight": 0.20},
            {"name": "Core Demo", "duration": 18, "weight": 0.45},
            {"name": "Validation & ROI", "duration": 8, "weight": 0.15},
            {"name": "Close & Next Steps", "duration": 5, "weight": 0.05}
        ]
    
    def initialize_demo_tracking(self, lead_id: str, demo_config: Dict[str, Any]) -> str:
        """Initialize a new demo tracking session."""
        demo_id = str(uuid.uuid4())
        
        self.current_demo = {
            "demo_id": demo_id,
            "lead_id": lead_id,
            "company_name": demo_config.get("company_name", ""),
            "industry": demo_config.get("industry", ""),
            "attendees": demo_config.get("attendees", []),
            "demo_type": demo_config.get("demo_type", "standard"),
            "expected_duration": demo_config.get("duration", 30),
            "objectives": demo_config.get("objectives", [])
        }
        
        self.real_time_metrics["start_time"] = datetime.now()
        self.engagement_data = []
        
        # Store in database
        self._save_demo_session()
        
        return demo_id
    
    def track_engagement_event(self, event_type: str, details: Dict[str, Any] = None):
        """Track real-time engagement events during demo."""
        if not self.current_demo:
            return
        
        timestamp = datetime.now()
        event = {
            "timestamp": timestamp,
            "type": event_type,
            "details": details or {},
            "demo_phase": self._get_current_phase(),
            "elapsed_minutes": self._get_elapsed_minutes()
        }
        
        self.real_time_metrics["interaction_events"].append(event)
        
        # Update specific metrics based on event type
        if event_type == "question_asked":
            self.real_time_metrics["questions_asked"] += 1
            self._update_engagement_score("question", 0.1)
            
        elif event_type == "technical_question":
            self.real_time_metrics["questions_asked"] += 1
            self._update_engagement_score("technical_interest", 0.15)
            
        elif event_type == "pricing_question":
            self._update_engagement_score("buying_signal", 0.2)
            
        elif event_type == "implementation_question":
            self._update_engagement_score("implementation_interest", 0.18)
            
        elif event_type == "demo_interaction":
            self._update_engagement_score("interaction", 0.05)
            
        elif event_type == "objection_raised":
            self._update_engagement_score("objection", -0.1)
            
        elif event_type == "positive_feedback":
            self._update_engagement_score("positive", 0.12)
            
        elif event_type == "competitor_mentioned":
            self._update_engagement_score("competitive_concern", -0.05)
            
        elif event_type == "follow_up_requested":
            self._update_engagement_score("follow_up_interest", 0.25)
        
        # Recalculate success probability
        self._calculate_success_probability()
        
        # Save updated metrics
        self._update_demo_metrics()
    
    def get_real_time_dashboard(self) -> Dict[str, Any]:
        """Get real-time dashboard data for current demo."""
        if not self.current_demo:
            return {"error": "No active demo session"}
        
        current_phase = self._get_current_phase()
        elapsed = self._get_elapsed_minutes()
        completion_pct = min((elapsed / self.current_demo["expected_duration"]) * 100, 100)
        
        dashboard_data = {
            "demo_info": {
                "demo_id": self.current_demo["demo_id"],
                "company": self.current_demo["company_name"],
                "industry": self.current_demo["industry"],
                "start_time": self.real_time_metrics["start_time"].isoformat(),
                "elapsed_minutes": elapsed,
                "completion_percentage": completion_pct,
                "current_phase": current_phase["name"] if current_phase else "Unknown"
            },
            "engagement_metrics": {
                "total_questions": self.real_time_metrics["questions_asked"],
                "engagement_score": round(self.real_time_metrics["engagement_score"], 2),
                "success_probability": round(self.real_time_metrics["success_probability"], 2),
                "attendee_count": len(self.current_demo["attendees"])
            },
            "phase_progress": self._get_phase_progress(),
            "recent_events": self.real_time_metrics["interaction_events"][-10:],
            "recommendations": self._get_real_time_recommendations(),
            "alerts": self._get_performance_alerts()
        }
        
        return dashboard_data
    
    def complete_demo(self, completion_details: Dict[str, Any]) -> Dict[str, Any]:
        """Complete demo session and calculate final metrics."""
        if not self.current_demo:
            return {"error": "No active demo session"}
        
        end_time = datetime.now()
        duration_minutes = (end_time - self.real_time_metrics["start_time"]).total_seconds() / 60
        
        # Calculate final performance metrics
        final_metrics = {
            "demo_id": self.current_demo["demo_id"],
            "lead_id": self.current_demo["lead_id"],
            "industry": self.current_demo["industry"],
            "duration_minutes": round(duration_minutes, 1),
            "attendee_count": len(self.current_demo["attendees"]),
            "engagement_score": round(self.real_time_metrics["engagement_score"], 3),
            "questions_asked": self.real_time_metrics["questions_asked"],
            "technical_questions": len([e for e in self.real_time_metrics["interaction_events"] 
                                      if e["type"] == "technical_question"]),
            "business_questions": len([e for e in self.real_time_metrics["interaction_events"] 
                                     if e["type"] == "question_asked"]),
            "pricing_questions": len([e for e in self.real_time_metrics["interaction_events"] 
                                    if e["type"] == "pricing_question"]),
            "implementation_questions": len([e for e in self.real_time_metrics["interaction_events"] 
                                           if e["type"] == "implementation_question"]),
            "completion_rate": min(duration_minutes / self.current_demo["expected_duration"], 1.0),
            "follow_up_requested": completion_details.get("follow_up_requested", False),
            "pilot_requested": completion_details.get("pilot_requested", False),
            "proposal_requested": completion_details.get("proposal_requested", False),
            "reference_requested": completion_details.get("reference_requested", False),
            "competitive_mentions": completion_details.get("competitive_mentions", []),
            "objections_raised": completion_details.get("objections_raised", []),
            "success_probability": round(self.real_time_metrics["success_probability"], 3),
            "recommended_follow_up": self._generate_follow_up_recommendation(),
            "recorded_at": end_time
        }
        
        # Store final performance data
        self._save_demo_performance(final_metrics)
        
        # Update lead conversion stage
        self._update_lead_conversion_stage(final_metrics)
        
        # Generate insights and recommendations
        insights = self._generate_demo_insights(final_metrics)
        
        # Reset current session
        self.current_demo = None
        self.real_time_metrics = {
            "start_time": None,
            "duration_minutes": 0,
            "questions_asked": 0,
            "engagement_score": 0.0,
            "completion_percentage": 0.0,
            "success_probability": 0.0,
            "attendee_count": 1,
            "interaction_events": []
        }
        
        return {
            "final_metrics": final_metrics,
            "insights": insights,
            "recommended_actions": self._get_recommended_actions(final_metrics)
        }
    
    def _get_current_phase(self) -> Optional[Dict[str, Any]]:
        """Determine current demo phase based on elapsed time."""
        if not self.current_demo:
            return None
        
        elapsed = self._get_elapsed_minutes()
        current_time = 0
        
        for phase in self.demo_phases:
            if elapsed <= current_time + phase["duration"]:
                return {
                    "name": phase["name"],
                    "duration": phase["duration"],
                    "weight": phase["weight"],
                    "time_remaining": current_time + phase["duration"] - elapsed
                }
            current_time += phase["duration"]
        
        return {"name": "Overtime", "duration": 0, "weight": 0, "time_remaining": 0}
    
    def _get_elapsed_minutes(self) -> float:
        """Get elapsed minutes since demo start."""
        if not self.real_time_metrics["start_time"]:
            return 0
        return (datetime.now() - self.real_time_metrics["start_time"]).total_seconds() / 60
    
    def _update_engagement_score(self, event_type: str, score_delta: float):
        """Update engagement score based on event type."""
        current_score = self.real_time_metrics["engagement_score"]
        new_score = max(0, min(1.0, current_score + score_delta))
        self.real_time_metrics["engagement_score"] = new_score
    
    def _calculate_success_probability(self):
        """Calculate current success probability based on engagement and events."""
        base_score = 0.3  # Base probability
        
        # Engagement score contribution (40%)
        engagement_contribution = self.real_time_metrics["engagement_score"] * 0.4
        
        # Questions asked contribution (25%)
        questions_score = min(self.real_time_metrics["questions_asked"] / 8.0, 1.0) * 0.25
        
        # Event quality contribution (25%)
        high_value_events = [
            "pricing_question", "implementation_question", "follow_up_requested",
            "pilot_requested", "proposal_requested", "positive_feedback"
        ]
        
        high_value_count = len([e for e in self.real_time_metrics["interaction_events"] 
                              if e["type"] in high_value_events])
        event_score = min(high_value_count / 5.0, 1.0) * 0.25
        
        # Phase progress contribution (10%)
        elapsed = self._get_elapsed_minutes()
        expected = self.current_demo["expected_duration"] if self.current_demo else 30
        progress_score = min(elapsed / expected, 1.0) * 0.1
        
        total_score = base_score + engagement_contribution + questions_score + event_score + progress_score
        self.real_time_metrics["success_probability"] = min(total_score, 1.0)
    
    def _get_phase_progress(self) -> List[Dict[str, Any]]:
        """Get progress through demo phases."""
        elapsed = self._get_elapsed_minutes()
        current_time = 0
        phases_progress = []
        
        for phase in self.demo_phases:
            phase_start = current_time
            phase_end = current_time + phase["duration"]
            
            if elapsed >= phase_end:
                status = "completed"
                progress = 100
            elif elapsed >= phase_start:
                status = "active"
                progress = ((elapsed - phase_start) / phase["duration"]) * 100
            else:
                status = "pending"
                progress = 0
            
            phases_progress.append({
                "name": phase["name"],
                "status": status,
                "progress": round(progress, 1),
                "duration": phase["duration"],
                "weight": phase["weight"]
            })
            
            current_time += phase["duration"]
        
        return phases_progress
    
    def _get_real_time_recommendations(self) -> List[str]:
        """Get real-time recommendations for demo optimization."""
        recommendations = []
        elapsed = self._get_elapsed_minutes()
        current_phase = self._get_current_phase()
        
        # Engagement-based recommendations
        if self.real_time_metrics["engagement_score"] < 0.5:
            recommendations.append("🔥 Low engagement detected - ask more questions and involve attendees")
        
        # Question-based recommendations
        if elapsed > 10 and self.real_time_metrics["questions_asked"] < 3:
            recommendations.append("❓ Few questions asked - pause and check for understanding")
        
        # Phase-based recommendations
        if current_phase and current_phase["name"] == "Core Demo":
            if self.real_time_metrics["questions_asked"] < 5:
                recommendations.append("🎯 Core demo phase - encourage technical questions")
        
        # Time-based recommendations
        if elapsed > 25 and not any(e["type"] in ["pricing_question", "implementation_question"] 
                                   for e in self.real_time_metrics["interaction_events"]):
            recommendations.append("💰 Time to introduce pricing and implementation timeline")
        
        # Success probability recommendations
        if self.real_time_metrics["success_probability"] > 0.7:
            recommendations.append("🚀 High success probability - consider asking for next steps")
        elif self.real_time_metrics["success_probability"] < 0.4:
            recommendations.append("⚠️ Low success probability - address concerns and show more value")
        
        return recommendations
    
    def _get_performance_alerts(self) -> List[Dict[str, str]]:
        """Get performance alerts for demo monitoring."""
        alerts = []
        elapsed = self._get_elapsed_minutes()
        expected = self.current_demo["expected_duration"] if self.current_demo else 30
        
        # Time alerts
        if elapsed > expected * 1.1:
            alerts.append({
                "type": "warning",
                "message": "Demo running over expected time - consider wrapping up"
            })
        
        # Engagement alerts
        if self.real_time_metrics["engagement_score"] < 0.3:
            alerts.append({
                "type": "critical",
                "message": "Critical: Very low engagement - immediate intervention needed"
            })
        elif self.real_time_metrics["engagement_score"] < 0.5:
            alerts.append({
                "type": "warning", 
                "message": "Low engagement - increase interactivity"
            })
        
        # Success probability alerts
        if self.real_time_metrics["success_probability"] > 0.8:
            alerts.append({
                "type": "success",
                "message": "Excellent demo performance - high conversion probability"
            })
        
        return alerts
    
    def _generate_follow_up_recommendation(self) -> str:
        """Generate follow-up recommendation based on demo performance."""
        success_prob = self.real_time_metrics["success_probability"]
        
        high_value_events = [
            "pricing_question", "implementation_question", "follow_up_requested",
            "pilot_requested", "proposal_requested"
        ]
        
        has_high_value_events = any(e["type"] in high_value_events 
                                   for e in self.real_time_metrics["interaction_events"])
        
        if success_prob >= 0.8 and has_high_value_events:
            return "immediate_proposal"
        elif success_prob >= 0.6:
            return "technical_deep_dive"
        elif success_prob >= 0.4:
            return "reference_call"
        else:
            return "nurturing_sequence"
    
    def _generate_demo_insights(self, final_metrics: Dict[str, Any]) -> List[str]:
        """Generate insights about demo performance."""
        insights = []
        
        # Engagement insights
        if final_metrics["engagement_score"] > 0.7:
            insights.append("High engagement throughout demo - audience was actively involved")
        elif final_metrics["engagement_score"] < 0.4:
            insights.append("Low engagement - consider more interactive approach next time")
        
        # Question insights
        total_questions = final_metrics["questions_asked"]
        if total_questions > 10:
            insights.append("Excellent question engagement - shows strong interest")
        elif total_questions < 3:
            insights.append("Few questions asked - audience may need more encouragement to participate")
        
        # Technical interest insights
        if final_metrics["technical_questions"] > 5:
            insights.append("Strong technical interest - detailed implementation discussion likely needed")
        
        # Timing insights
        if final_metrics["completion_rate"] < 0.8:
            insights.append("Demo ended early - may indicate disengagement or scheduling conflict")
        elif final_metrics["completion_rate"] > 1.2:
            insights.append("Demo ran long - consider tightening timeline for future presentations")
        
        return insights
    
    def _get_recommended_actions(self, final_metrics: Dict[str, Any]) -> List[str]:
        """Get recommended next actions based on demo performance."""
        actions = []
        
        success_prob = final_metrics["success_probability"]
        
        if success_prob >= 0.8:
            actions.append("Send proposal within 24 hours")
            actions.append("Schedule follow-up call with decision makers")
            
        elif success_prob >= 0.6:
            actions.append("Arrange technical deep-dive session")
            actions.append("Provide additional case studies from similar companies")
            
        elif success_prob >= 0.4:
            actions.append("Set up reference call with existing customer")
            actions.append("Send personalized follow-up addressing specific questions")
            
        else:
            actions.append("Add to nurturing campaign")
            actions.append("Provide educational content about industry use cases")
        
        # Add specific actions based on demo events
        if final_metrics.get("pricing_questions", 0) > 0:
            actions.append("Provide detailed pricing breakdown and ROI analysis")
        
        if final_metrics.get("competitive_mentions"):
            actions.append("Send competitive comparison document")
        
        return actions
    
    def _save_demo_session(self):
        """Save demo session data to database."""
        # Implementation would save to database
        pass
    
    def _update_demo_metrics(self):
        """Update demo metrics in database."""
        # Implementation would update database
        pass
    
    def _save_demo_performance(self, final_metrics: Dict[str, Any]):
        """Save final demo performance to database."""
        if not self.db_path.exists():
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO demo_performance (
                    id, demo_id, industry, attendee_count, demo_duration_minutes,
                    engagement_score, technical_questions, business_questions,
                    pricing_questions, implementation_questions, demo_completion_rate,
                    follow_up_requested, pilot_requested, proposal_requested,
                    reference_requested, competitive_mentions, objections_raised,
                    success_probability, recommended_follow_up, recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), final_metrics["demo_id"], final_metrics["industry"],
                final_metrics["attendee_count"], final_metrics["duration_minutes"],
                final_metrics["engagement_score"], final_metrics["technical_questions"],
                final_metrics["business_questions"], final_metrics["pricing_questions"],
                final_metrics["implementation_questions"], final_metrics["completion_rate"],
                final_metrics["follow_up_requested"], final_metrics["pilot_requested"],
                final_metrics["proposal_requested"], final_metrics["reference_requested"],
                json.dumps(final_metrics["competitive_mentions"]),
                json.dumps(final_metrics["objections_raised"]),
                final_metrics["success_probability"], final_metrics["recommended_follow_up"],
                final_metrics["recorded_at"]
            ))
            
            conn.commit()
        except Exception as e:
            print(f"Error saving demo performance: {e}")
        finally:
            conn.close()
    
    def _update_lead_conversion_stage(self, final_metrics: Dict[str, Any]):
        """Update lead conversion stage based on demo performance."""
        if not self.db_path.exists():
            return
        
        success_prob = final_metrics["success_probability"]
        
        if final_metrics.get("proposal_requested", False):
            new_stage = "proposal_requested"
        elif success_prob >= 0.7:
            new_stage = "high_interest"
        elif success_prob >= 0.4:
            new_stage = "medium_interest"
        else:
            new_stage = "low_interest"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE demo_leads 
                SET conversion_stage = ?, demo_status = 'completed', updated_at = ?
                WHERE id = ?
            """, (new_stage, datetime.now(), final_metrics["lead_id"]))
            
            conn.commit()
        except Exception as e:
            print(f"Error updating lead stage: {e}")
        finally:
            conn.close()


def render_real_time_tracking_interface():
    """Render Streamlit interface for real-time demo tracking."""
    st.title("🎬 Real-Time Demo Performance Tracker")
    st.markdown("### Live engagement monitoring and success prediction")
    
    # Initialize tracker
    if 'demo_tracker' not in st.session_state:
        st.session_state.demo_tracker = RealTimeDemoTracker()
    
    tracker = st.session_state.demo_tracker
    
    # Demo session management
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if not tracker.current_demo:
            st.markdown("#### 🚀 Start New Demo Session")
            
            with st.form("start_demo"):
                company_name = st.text_input("Company Name", value="Premier Realty Group")
                industry = st.selectbox("Industry", 
                    ["real_estate", "saas", "ecommerce", "financial_services"],
                    format_func=lambda x: x.replace('_', ' ').title()
                )
                attendees = st.text_area("Attendees (one per line)", 
                    value="Sarah Chen - VP Sales\nMike Rodriguez - IT Director")
                duration = st.number_input("Expected Duration (minutes)", value=30, min_value=15, max_value=60)
                
                if st.form_submit_button("🎯 Start Demo Tracking", type="primary"):
                    demo_config = {
                        "company_name": company_name,
                        "industry": industry,
                        "attendees": attendees.split('\n'),
                        "duration": duration
                    }
                    
                    demo_id = tracker.initialize_demo_tracking("demo_lead_123", demo_config)
                    st.success(f"✅ Demo tracking started! ID: {demo_id[:8]}...")
                    st.rerun()
        
        else:
            # Live demo tracking interface
            dashboard_data = tracker.get_real_time_dashboard()
            
            st.markdown("#### 📊 Live Demo Dashboard")
            
            # Current demo info
            demo_info = dashboard_data["demo_info"]
            metrics = dashboard_data["engagement_metrics"]
            
            col_a, col_b, col_c, col_d = st.columns(4)
            
            with col_a:
                st.metric("🏢 Company", demo_info["company"])
                st.metric("⏱️ Elapsed", f"{demo_info['elapsed_minutes']:.1f} min")
            
            with col_b:
                st.metric("🎯 Industry", demo_info["industry"].replace('_', ' ').title())
                st.metric("📈 Completion", f"{demo_info['completion_percentage']:.1f}%")
            
            with col_c:
                st.metric("🤝 Engagement", f"{metrics['engagement_score']:.2f}")
                st.metric("❓ Questions", metrics["total_questions"])
            
            with col_d:
                st.metric("🎯 Success Probability", f"{metrics['success_probability']:.1%}")
                st.metric("👥 Attendees", metrics["attendee_count"])
            
            # Phase progress
            st.markdown("#### 📋 Demo Phase Progress")
            phases = dashboard_data["phase_progress"]
            
            for phase in phases:
                if phase["status"] == "completed":
                    st.progress(1.0, f"✅ {phase['name']} ({phase['duration']} min)")
                elif phase["status"] == "active":
                    st.progress(phase["progress"]/100, f"🔄 {phase['name']} ({phase['progress']:.1f}%)")
                else:
                    st.progress(0.0, f"⏳ {phase['name']} (Pending)")
            
            # Real-time recommendations
            st.markdown("#### 💡 Live Recommendations")
            recommendations = dashboard_data["recommendations"]
            
            if recommendations:
                for rec in recommendations:
                    st.info(rec)
            else:
                st.success("🎯 Demo is progressing well - no immediate actions needed!")
            
            # Performance alerts
            alerts = dashboard_data["alerts"]
            for alert in alerts:
                if alert["type"] == "critical":
                    st.error(alert["message"])
                elif alert["type"] == "warning":
                    st.warning(alert["message"])
                elif alert["type"] == "success":
                    st.success(alert["message"])
    
    with col2:
        if tracker.current_demo:
            st.markdown("#### 🎛️ Event Tracking")
            
            # Quick event buttons
            if st.button("❓ Question Asked"):
                tracker.track_engagement_event("question_asked")
                st.rerun()
            
            if st.button("🔧 Technical Question"):
                tracker.track_engagement_event("technical_question")
                st.rerun()
            
            if st.button("💰 Pricing Question"):
                tracker.track_engagement_event("pricing_question")
                st.rerun()
            
            if st.button("📋 Implementation Question"):
                tracker.track_engagement_event("implementation_question")
                st.rerun()
            
            if st.button("👍 Positive Feedback"):
                tracker.track_engagement_event("positive_feedback")
                st.rerun()
            
            if st.button("⚠️ Objection Raised"):
                tracker.track_engagement_event("objection_raised")
                st.rerun()
            
            if st.button("🤝 Follow-up Requested"):
                tracker.track_engagement_event("follow_up_requested")
                st.rerun()
            
            st.markdown("---")
            
            # Complete demo
            if st.button("🏁 Complete Demo", type="primary"):
                completion_details = {
                    "follow_up_requested": True,
                    "pilot_requested": False,
                    "proposal_requested": True,
                    "reference_requested": False,
                    "competitive_mentions": ["Salesforce"],
                    "objections_raised": ["Price concerns"]
                }
                
                results = tracker.complete_demo(completion_details)
                
                st.success("✅ Demo completed successfully!")
                
                with st.expander("📊 Final Results"):
                    st.json(results["final_metrics"])
                
                with st.expander("💡 Insights"):
                    for insight in results["insights"]:
                        st.write(f"• {insight}")
                
                with st.expander("🚀 Recommended Actions"):
                    for action in results["recommended_actions"]:
                        st.write(f"• {action}")
                
                st.rerun()
    
    # Recent events timeline
    if tracker.current_demo:
        st.markdown("#### 📋 Event Timeline")
        
        events = tracker.real_time_metrics["interaction_events"][-10:]
        
        if events:
            for event in reversed(events):
                timestamp = event["timestamp"].strftime("%H:%M:%S")
                event_type = event["type"].replace("_", " ").title()
                phase = event["details"].get("phase", "Unknown") if event["details"] else "Demo"
                
                st.text(f"{timestamp} | {event_type} | {phase}")
        else:
            st.info("No events tracked yet. Use the buttons above to track engagement.")


if __name__ == "__main__":
    render_real_time_tracking_interface()