"""
Claude-Enhanced Qualification Orchestrator (Phase 2 Enhancement)

Manages intelligent qualification flow with adaptive question sequencing based on Claude analysis,
context-aware conversation branching, and real-time completion tracking with semantic understanding.

Integrates with existing 9-stage lead lifecycle system while providing AI-driven qualification logic.

Features:
- Adaptive question sequencing based on Claude semantic analysis
- Context-aware conversation branching
- Real-time qualification completeness tracking
- Integration with existing LeadLifecycleTracker
- Intelligent question prioritization based on lead profile
- Semantic understanding of responses for better qualification
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ghl_real_estate_ai.services.claude_semantic_analyzer import ClaudeSemanticAnalyzer
from ghl_real_estate_ai.services.lead_lifecycle import LeadLifecycleTracker

logger = logging.getLogger(__name__)


class QualificationOrchestrator:
    """
    Orchestrates intelligent qualification flow with Claude AI semantic understanding.

    Manages adaptive question sequencing, context-aware conversation branching,
    and integration with the existing 9-stage lead lifecycle system.
    """

    # Core qualification areas with priority weights
    QUALIFICATION_AREAS = {
        "budget": {
            "weight": 30,
            "required": True,
            "stage_threshold": "qualified",
            "questions": [
                "budget_range", "financing_status", "down_payment", "monthly_comfort"
            ]
        },
        "timeline": {
            "weight": 25,
            "required": True,
            "stage_threshold": "qualified",
            "questions": [
                "purchase_timeline", "urgency_factors", "current_situation", "flexibility"
            ]
        },
        "location": {
            "weight": 20,
            "required": True,
            "stage_threshold": "qualified",
            "questions": [
                "preferred_areas", "location_flexibility", "commute_requirements", "neighborhood_priorities"
            ]
        },
        "property_preferences": {
            "weight": 15,
            "required": False,
            "stage_threshold": "engaged",
            "questions": [
                "property_type", "size_requirements", "must_haves", "nice_to_haves"
            ]
        },
        "motivation": {
            "weight": 10,
            "required": False,
            "stage_threshold": "hot",
            "questions": [
                "buying_reason", "current_housing", "pain_points", "goals"
            ]
        }
    }

    # Question templates organized by type
    QUESTION_TEMPLATES = {
        "budget_range": {
            "base": "What's your budget range for this purchase?",
            "follow_up": "Are you pre-approved for financing, or would you like recommendations for lenders?",
            "semantic_triggers": ["budget", "price", "afford", "financing", "loan", "mortgage"]
        },
        "financing_status": {
            "base": "Do you have pre-approval or financing in place?",
            "follow_up": "What type of financing are you considering - conventional, FHA, VA, or cash?",
            "semantic_triggers": ["pre-approval", "financing", "cash", "loan", "mortgage", "lender"]
        },
        "purchase_timeline": {
            "base": "What's your ideal timeline for finding and purchasing a home?",
            "follow_up": "Is there anything driving this timeline, like a lease ending or job change?",
            "semantic_triggers": ["timeline", "when", "soon", "urgent", "flexible", "deadline"]
        },
        "preferred_areas": {
            "base": "Which neighborhoods or areas are you most interested in?",
            "follow_up": "How important is proximity to work, schools, or family?",
            "semantic_triggers": ["location", "area", "neighborhood", "commute", "school", "work"]
        },
        "property_type": {
            "base": "Are you looking for a specific type of property - single family, condo, townhome?",
            "follow_up": "Any specific size requirements or must-have features?",
            "semantic_triggers": ["house", "condo", "townhouse", "size", "bedrooms", "bathrooms"]
        }
    }

    # Conversation flow states
    FLOW_STATES = [
        "initial_contact",      # First interaction
        "rapport_building",     # Establishing trust
        "needs_discovery",      # Understanding basic needs
        "qualification_deep_dive", # Detailed qualification
        "preference_refinement", # Fine-tuning preferences
        "urgency_assessment",   # Understanding timeline pressure
        "readiness_confirmation", # Confirming readiness to proceed
        "next_steps_planning"   # Planning follow-up actions
    ]

    def __init__(self, location_id: str):
        """
        Initialize qualification orchestrator for a specific GHL location.

        Args:
            location_id: GHL Location ID for multi-tenant support
        """
        self.location_id = location_id
        self.data_dir = Path(__file__).parent.parent / "data" / "qualification" / location_id
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # File storage
        self.flows_file = self.data_dir / "qualification_flows.json"
        self.metrics_file = self.data_dir / "metrics.json"

        # Load existing data
        self.flows = self._load_flows()
        self.metrics = self._load_metrics()

        # Initialize services
        self.claude_analyzer = ClaudeSemanticAnalyzer()
        self.lifecycle_tracker = LeadLifecycleTracker(location_id)

        logger.info(f"QualificationOrchestrator initialized for location {location_id}")

    def _load_flows(self) -> Dict:
        """Load existing qualification flows from file."""
        if self.flows_file.exists():
            try:
                with open(self.flows_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading flows: {e}")
        return {}

    def _save_flows(self) -> None:
        """Save qualification flows to file."""
        try:
            with open(self.flows_file, 'w') as f:
                json.dump(self.flows, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving flows: {e}")

    def _load_metrics(self) -> Dict:
        """Load qualification metrics from file."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metrics: {e}")
        return {"flows_started": 0, "flows_completed": 0, "avg_completion_time": 0}

    def _save_metrics(self) -> None:
        """Save qualification metrics to file."""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

    async def start_qualification_flow(
        self,
        contact_id: str,
        contact_name: str,
        initial_message: str = "",
        source: str = "website",
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a new intelligent qualification flow for a lead.

        Args:
            contact_id: Unique contact identifier
            contact_name: Contact's name
            initial_message: Initial message from contact (if any)
            source: Lead source
            agent_id: Agent handling the lead

        Returns:
            Dictionary containing flow initialization data and next steps
        """
        try:
            flow_id = f"qual_{contact_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            now = datetime.now().isoformat()

            # Analyze initial message if provided
            initial_analysis = {}
            if initial_message:
                try:
                    initial_analysis = await self.claude_analyzer.analyze_lead_intent([{
                        "role": "user",
                        "content": initial_message,
                        "timestamp": now
                    }])
                except Exception as e:
                    logger.warning(f"Initial message analysis failed: {e}")

            # Create qualification flow
            qualification_flow = {
                "flow_id": flow_id,
                "contact_id": contact_id,
                "contact_name": contact_name,
                "location_id": self.location_id,
                "agent_id": agent_id,
                "source": source,
                "started_at": now,
                "updated_at": now,
                "status": "active",
                "current_state": "initial_contact",
                "completion_percentage": 0,

                # Initial analysis
                "initial_message": initial_message,
                "initial_analysis": initial_analysis,

                # Qualification tracking
                "qualification_data": {
                    area: {
                        "completed": False,
                        "confidence": 0,
                        "responses": {},
                        "questions_asked": [],
                        "semantic_signals": []
                    }
                    for area in self.QUALIFICATION_AREAS.keys()
                },

                # Conversation flow
                "conversation_history": [],
                "flow_states": [{
                    "state": "initial_contact",
                    "entered_at": now,
                    "questions_in_state": 0
                }],

                # Dynamic question queue
                "question_queue": [],
                "questions_asked": [],
                "next_recommended_questions": [],

                # Metrics
                "metrics": {
                    "total_questions_asked": 0,
                    "total_responses_received": 0,
                    "qualification_score": 0,
                    "engagement_level": 0,
                    "time_to_qualification": None
                }
            }

            # Generate initial question recommendations
            initial_questions = await self._generate_adaptive_questions(
                qualification_flow,
                context="flow_start"
            )
            qualification_flow["next_recommended_questions"] = initial_questions[:3]

            # Save flow
            self.flows[flow_id] = qualification_flow
            self._save_flows()

            # Update metrics
            self.metrics["flows_started"] += 1
            self._save_metrics()

            # Start journey tracking in lifecycle system
            journey_id = self.lifecycle_tracker.start_journey(
                contact_id=contact_id,
                contact_name=contact_name,
                source=source,
                initial_data={
                    "qualification_flow_id": flow_id,
                    "agent_id": agent_id
                }
            )

            logger.info(f"Started qualification flow {flow_id} for contact {contact_id}")

            return {
                "flow_id": flow_id,
                "journey_id": journey_id,
                "status": "started",
                "current_state": "initial_contact",
                "next_questions": qualification_flow["next_recommended_questions"],
                "completion_percentage": 0,
                "initial_analysis": initial_analysis
            }

        except Exception as e:
            logger.error(f"Error starting qualification flow: {e}")
            return {"error": str(e), "status": "failed"}

    async def process_response(
        self,
        flow_id: str,
        user_message: str,
        agent_response: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user response and provide intelligent next steps.

        Args:
            flow_id: Qualification flow identifier
            user_message: User's response/message
            agent_response: Agent's response (if any)
            context: Additional context data

        Returns:
            Dictionary containing analysis, updated state, and next recommendations
        """
        try:
            if flow_id not in self.flows:
                return {"error": "Flow not found", "status": "failed"}

            flow = self.flows[flow_id]
            now = datetime.now().isoformat()

            # Add to conversation history
            conversation_entry = {
                "timestamp": now,
                "user_message": user_message,
                "agent_response": agent_response,
                "context": context or {}
            }
            flow["conversation_history"].append(conversation_entry)

            # Analyze response with Claude
            semantic_analysis = await self._analyze_response(flow, user_message)

            # Update qualification data based on analysis
            qualification_updates = await self._update_qualification_data(
                flow, user_message, semantic_analysis
            )

            # Calculate completion percentage
            completion_percentage = self._calculate_completion_percentage(flow)
            flow["completion_percentage"] = completion_percentage

            # Determine next flow state
            next_state = await self._determine_next_state(flow, semantic_analysis)
            if next_state != flow["current_state"]:
                await self._transition_flow_state(flow, next_state)

            # Generate next question recommendations
            next_questions = await self._generate_adaptive_questions(
                flow,
                context="response_processed",
                last_response=user_message,
                semantic_analysis=semantic_analysis
            )
            flow["next_recommended_questions"] = next_questions

            # Update metrics
            flow["metrics"]["total_responses_received"] += 1
            flow["metrics"]["qualification_score"] = completion_percentage
            flow["metrics"]["engagement_level"] = semantic_analysis.get("engagement_level", 0)

            # Check if qualification is complete
            qualification_complete = completion_percentage >= 80
            if qualification_complete and flow["status"] == "active":
                await self._complete_qualification_flow(flow)

            # Update lifecycle stage if needed
            await self._update_lifecycle_stage(flow, completion_percentage)

            # Save updates
            flow["updated_at"] = now
            self._save_flows()

            return {
                "flow_id": flow_id,
                "status": flow["status"],
                "current_state": flow["current_state"],
                "completion_percentage": completion_percentage,
                "semantic_analysis": semantic_analysis,
                "qualification_updates": qualification_updates,
                "next_questions": next_questions,
                "qualification_complete": qualification_complete,
                "recommendations": await self._get_agent_recommendations(flow)
            }

        except Exception as e:
            logger.error(f"Error processing response for flow {flow_id}: {e}")
            return {"error": str(e), "status": "failed"}

    async def _analyze_response(
        self,
        flow: Dict[str, Any],
        user_message: str
    ) -> Dict[str, Any]:
        """Analyze user response using Claude semantic analyzer."""
        try:
            # Build conversation context
            conversation_messages = []
            for entry in flow["conversation_history"][-5:]:  # Last 5 exchanges
                if entry.get("user_message"):
                    conversation_messages.append({
                        "role": "user",
                        "content": entry["user_message"],
                        "timestamp": entry["timestamp"]
                    })
                if entry.get("agent_response"):
                    conversation_messages.append({
                        "role": "assistant",
                        "content": entry["agent_response"],
                        "timestamp": entry["timestamp"]
                    })

            # Analyze with Claude
            analysis = await self.claude_analyzer.analyze_lead_intent(conversation_messages)

            # Extract qualification-specific insights
            qualification_signals = await self._extract_qualification_signals(
                user_message, analysis
            )

            # Calculate engagement level
            engagement_level = self._calculate_engagement_level(user_message, analysis)

            return {
                "claude_analysis": analysis,
                "qualification_signals": qualification_signals,
                "engagement_level": engagement_level,
                "sentiment": analysis.get("sentiment", "neutral"),
                "intent_strength": analysis.get("intent_strength", 50),
                "urgency_indicators": analysis.get("urgency_indicators", [])
            }

        except Exception as e:
            logger.error(f"Error analyzing response: {e}")
            return {"error": str(e), "engagement_level": 50}

    async def _extract_qualification_signals(
        self,
        message: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract qualification-relevant signals from message analysis."""
        signals = {}

        # Check for budget signals
        budget_keywords = ["budget", "afford", "price", "cost", "expensive", "cheap", "financing"]
        if any(keyword in message.lower() for keyword in budget_keywords):
            signals["budget"] = {
                "mentioned": True,
                "confidence": analysis.get("confidence", {}).get("budget", 0),
                "specific_amounts": analysis.get("extracted_data", {}).get("budget", None)
            }

        # Check for timeline signals
        timeline_keywords = ["soon", "asap", "urgent", "flexible", "timeline", "when", "time"]
        if any(keyword in message.lower() for keyword in timeline_keywords):
            signals["timeline"] = {
                "mentioned": True,
                "urgency": analysis.get("urgency_score", 50),
                "timeline_mentioned": analysis.get("extracted_data", {}).get("timeline", None)
            }

        # Check for location signals
        location_keywords = ["area", "neighborhood", "location", "commute", "near", "close"]
        if any(keyword in message.lower() for keyword in location_keywords):
            signals["location"] = {
                "mentioned": True,
                "preferences": analysis.get("extracted_data", {}).get("location", [])
            }

        return signals

    def _calculate_engagement_level(
        self,
        message: str,
        analysis: Dict[str, Any]
    ) -> int:
        """Calculate engagement level based on message content and analysis."""
        score = 50  # Base score

        # Length factor
        if len(message) > 100:
            score += 10
        elif len(message) < 20:
            score -= 10

        # Question asking (high engagement)
        if "?" in message:
            score += 15

        # Specificity (detailed responses)
        specific_words = ["specifically", "exactly", "particular", "prefer", "looking for"]
        if any(word in message.lower() for word in specific_words):
            score += 10

        # Enthusiasm indicators
        enthusiasm_words = ["excited", "love", "perfect", "great", "awesome"]
        if any(word in message.lower() for word in enthusiasm_words):
            score += 15

        # Objection indicators (lower engagement)
        objection_words = ["not sure", "maybe", "think about", "hesitant"]
        if any(word in message.lower() for word in objection_words):
            score -= 10

        # Use Claude analysis if available
        if analysis.get("engagement_score"):
            score = (score + analysis["engagement_score"]) // 2

        return max(0, min(100, score))

    async def _update_qualification_data(
        self,
        flow: Dict[str, Any],
        message: str,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update qualification data based on response analysis."""
        updates = {}
        qual_data = flow["qualification_data"]

        for area_name, area_config in self.QUALIFICATION_AREAS.items():
            area_data = qual_data[area_name]

            # Check if this message contains information for this area
            signals = analysis.get("qualification_signals", {}).get(area_name, {})

            if signals.get("mentioned", False):
                # Update responses
                if area_name not in area_data["responses"]:
                    area_data["responses"][area_name] = []

                area_data["responses"][area_name].append({
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                    "confidence": signals.get("confidence", 50),
                    "extracted_data": signals.get("specific_amounts") or signals.get("preferences", [])
                })

                # Update semantic signals
                area_data["semantic_signals"].extend(
                    analysis.get("keywords", [])
                )

                # Calculate confidence based on completeness
                questions_for_area = area_config["questions"]
                responses_count = len(area_data["responses"].get(area_name, []))
                confidence = min(100, (responses_count / len(questions_for_area)) * 100)
                area_data["confidence"] = confidence

                # Mark as completed if confidence is high enough
                if confidence >= 70:
                    area_data["completed"] = True

                updates[area_name] = {
                    "updated": True,
                    "new_confidence": confidence,
                    "newly_completed": area_data["completed"]
                }

        return updates

    def _calculate_completion_percentage(self, flow: Dict[str, Any]) -> float:
        """Calculate overall qualification completion percentage."""
        total_weight = sum(area["weight"] for area in self.QUALIFICATION_AREAS.values())
        completed_weight = 0

        for area_name, area_config in self.QUALIFICATION_AREAS.items():
            area_data = flow["qualification_data"][area_name]

            # Calculate area completion based on confidence
            area_completion = area_data["confidence"] / 100

            # Apply weight
            completed_weight += area_completion * area_config["weight"]

        return round((completed_weight / total_weight) * 100, 1)

    async def _determine_next_state(
        self,
        flow: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> str:
        """Determine next flow state based on qualification progress and analysis."""
        current_state = flow["current_state"]
        completion = flow["completion_percentage"]
        engagement = analysis.get("engagement_level", 50)

        # State progression logic
        if completion < 20:
            return "needs_discovery"
        elif completion < 50:
            return "qualification_deep_dive"
        elif completion < 70:
            return "preference_refinement"
        elif completion < 85:
            return "urgency_assessment"
        elif completion >= 85:
            return "readiness_confirmation"

        return current_state

    async def _transition_flow_state(
        self,
        flow: Dict[str, Any],
        new_state: str
    ) -> None:
        """Transition flow to new state and update tracking."""
        old_state = flow["current_state"]
        now = datetime.now().isoformat()

        # Close previous state
        if flow["flow_states"]:
            last_state = flow["flow_states"][-1]
            if "exited_at" not in last_state:
                last_state["exited_at"] = now

        # Add new state
        flow["flow_states"].append({
            "state": new_state,
            "entered_at": now,
            "questions_in_state": 0
        })

        flow["current_state"] = new_state

        logger.info(f"Flow {flow['flow_id']} transitioned from {old_state} to {new_state}")

    async def _generate_adaptive_questions(
        self,
        flow: Dict[str, Any],
        context: str = "",
        last_response: Optional[str] = None,
        semantic_analysis: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate adaptive questions based on flow state and Claude analysis."""
        try:
            qual_data = flow["qualification_data"]
            current_state = flow["current_state"]
            completion = flow["completion_percentage"]

            # Identify areas that need more information
            priority_areas = []
            for area_name, area_config in self.QUALIFICATION_AREAS.items():
                area_data = qual_data[area_name]

                if not area_data["completed"]:
                    priority = area_config["weight"] * (100 - area_data["confidence"]) / 100
                    priority_areas.append((area_name, priority, area_config))

            # Sort by priority
            priority_areas.sort(key=lambda x: x[1], reverse=True)

            # Generate questions using Claude
            questions = []

            for area_name, priority, area_config in priority_areas[:3]:  # Top 3 areas
                area_data = qual_data[area_name]

                # Get available questions for this area
                available_questions = [
                    q for q in area_config["questions"]
                    if q not in area_data["questions_asked"]
                ]

                if available_questions:
                    # Use Claude to generate contextual questions
                    contextual_question = await self._generate_contextual_question(
                        area_name,
                        available_questions[0],
                        flow,
                        semantic_analysis
                    )

                    questions.append({
                        "area": area_name,
                        "question_id": available_questions[0],
                        "question_text": contextual_question,
                        "priority": priority,
                        "context": context,
                        "follow_up_enabled": True
                    })

            # Add state-specific questions
            if current_state == "urgency_assessment" and completion > 70:
                questions.append({
                    "area": "urgency",
                    "question_id": "timeline_urgency",
                    "question_text": "How quickly are you looking to make a decision and move forward?",
                    "priority": 90,
                    "context": "urgency_check",
                    "follow_up_enabled": True
                })

            return questions[:3]  # Return top 3 questions

        except Exception as e:
            logger.error(f"Error generating adaptive questions: {e}")
            return []

    async def _generate_contextual_question(
        self,
        area_name: str,
        question_id: str,
        flow: Dict[str, Any],
        semantic_analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate contextual question using Claude analysis."""
        try:
            # Get base question template
            base_template = self.QUESTION_TEMPLATES.get(question_id, {})
            base_question = base_template.get("base", f"Could you tell me more about your {area_name} preferences?")

            # Use Claude to make it contextual
            conversation_context = {
                "area": area_name,
                "current_state": flow["current_state"],
                "completion_percentage": flow["completion_percentage"],
                "previous_responses": flow["qualification_data"][area_name]["responses"],
                "semantic_analysis": semantic_analysis
            }

            # For now, return the base question (could be enhanced with Claude generation)
            # In a full implementation, this would call Claude to generate contextual variants

            return base_question

        except Exception as e:
            logger.error(f"Error generating contextual question: {e}")
            return f"Could you tell me more about your {area_name} preferences?"

    async def _complete_qualification_flow(self, flow: Dict[str, Any]) -> None:
        """Complete the qualification flow and update metrics."""
        flow["status"] = "completed"
        flow["completed_at"] = datetime.now().isoformat()

        # Calculate time to completion
        started_at = datetime.fromisoformat(flow["started_at"])
        completed_at = datetime.fromisoformat(flow["completed_at"])
        time_to_completion = (completed_at - started_at).total_seconds() / 3600  # hours

        flow["metrics"]["time_to_qualification"] = round(time_to_completion, 2)

        # Update global metrics
        self.metrics["flows_completed"] += 1
        if self.metrics["flows_completed"] > 0:
            # Update average completion time
            current_avg = self.metrics.get("avg_completion_time", 0)
            new_avg = ((current_avg * (self.metrics["flows_completed"] - 1)) + time_to_completion) / self.metrics["flows_completed"]
            self.metrics["avg_completion_time"] = round(new_avg, 2)

        logger.info(f"Qualification flow {flow['flow_id']} completed in {time_to_completion:.2f} hours")

    async def _update_lifecycle_stage(
        self,
        flow: Dict[str, Any],
        completion_percentage: float
    ) -> None:
        """Update lifecycle stage based on qualification progress."""
        try:
            contact_id = flow["contact_id"]

            # Determine appropriate stage
            if completion_percentage >= 80:
                target_stage = "qualified"
                reason = f"Qualification {completion_percentage}% complete"
                score = 75
            elif completion_percentage >= 50:
                target_stage = "engaged"
                reason = f"Active qualification in progress ({completion_percentage}%)"
                score = 65
            elif completion_percentage >= 20:
                target_stage = "contacted"
                reason = f"Initial qualification started ({completion_percentage}%)"
                score = 45
            else:
                return  # Don't update if minimal progress

            # Update lifecycle if journey exists
            journey_id = f"journey_{contact_id}"
            journey = self.lifecycle_tracker.get_journey(journey_id)

            if journey and journey["current_stage"] != target_stage:
                self.lifecycle_tracker.transition_stage(
                    journey_id=journey_id,
                    new_stage=target_stage,
                    reason=reason,
                    lead_score=score
                )

                logger.info(f"Updated lifecycle stage to {target_stage} for contact {contact_id}")

        except Exception as e:
            logger.error(f"Error updating lifecycle stage: {e}")

    async def _get_agent_recommendations(self, flow: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate agent recommendations based on current flow state."""
        recommendations = []
        completion = flow["completion_percentage"]
        current_state = flow["current_state"]

        # Completion-based recommendations
        if completion < 30:
            recommendations.append({
                "type": "qualification",
                "priority": "high",
                "message": "Focus on understanding basic budget and timeline needs",
                "action": "ask_budget_timeline"
            })
        elif completion < 70:
            recommendations.append({
                "type": "qualification",
                "priority": "medium",
                "message": "Dive deeper into location and property preferences",
                "action": "explore_preferences"
            })
        elif completion >= 80:
            recommendations.append({
                "type": "next_steps",
                "priority": "high",
                "message": "Lead is well qualified - schedule property viewing or send listings",
                "action": "schedule_showing"
            })

        # State-based recommendations
        if current_state == "urgency_assessment":
            recommendations.append({
                "type": "urgency",
                "priority": "critical",
                "message": "Assess timeline urgency and book next meeting",
                "action": "assess_urgency"
            })

        return recommendations

    def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get current status of a qualification flow."""
        if flow_id not in self.flows:
            return {"error": "Flow not found"}

        flow = self.flows[flow_id]

        return {
            "flow_id": flow_id,
            "contact_id": flow["contact_id"],
            "contact_name": flow["contact_name"],
            "status": flow["status"],
            "current_state": flow["current_state"],
            "completion_percentage": flow["completion_percentage"],
            "started_at": flow["started_at"],
            "updated_at": flow["updated_at"],
            "metrics": flow["metrics"],
            "next_recommended_questions": flow.get("next_recommended_questions", []),
            "qualification_summary": self._get_qualification_summary(flow)
        }

    def _get_qualification_summary(self, flow: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of qualification progress."""
        summary = {}

        for area_name, area_config in self.QUALIFICATION_AREAS.items():
            area_data = flow["qualification_data"][area_name]

            summary[area_name] = {
                "completed": area_data["completed"],
                "confidence": area_data["confidence"],
                "required": area_config["required"],
                "weight": area_config["weight"],
                "responses_count": len(area_data["responses"]),
                "semantic_signals": len(area_data["semantic_signals"])
            }

        return summary

    def get_qualification_analytics(self) -> Dict[str, Any]:
        """Get qualification analytics and metrics."""
        # Calculate completion rates by area
        area_completion_rates = {}
        total_flows = len([f for f in self.flows.values() if f["status"] in ["active", "completed"]])

        if total_flows > 0:
            for area_name in self.QUALIFICATION_AREAS.keys():
                completed_count = len([
                    f for f in self.flows.values()
                    if f["qualification_data"][area_name]["completed"]
                ])
                area_completion_rates[area_name] = round((completed_count / total_flows) * 100, 1)

        # Calculate average completion time by state
        state_durations = defaultdict(list)
        for flow in self.flows.values():
            for state_entry in flow.get("flow_states", []):
                if "exited_at" in state_entry:
                    entered = datetime.fromisoformat(state_entry["entered_at"])
                    exited = datetime.fromisoformat(state_entry["exited_at"])
                    duration = (exited - entered).total_seconds() / 60  # minutes
                    state_durations[state_entry["state"]].append(duration)

        avg_state_durations = {
            state: round(sum(durations) / len(durations), 1)
            for state, durations in state_durations.items()
            if durations
        }

        return {
            "total_flows": total_flows,
            "active_flows": len([f for f in self.flows.values() if f["status"] == "active"]),
            "completed_flows": len([f for f in self.flows.values() if f["status"] == "completed"]),
            "avg_completion_percentage": round(
                sum(f["completion_percentage"] for f in self.flows.values()) / max(total_flows, 1),
                1
            ),
            "area_completion_rates": area_completion_rates,
            "avg_state_durations_minutes": avg_state_durations,
            "global_metrics": self.metrics
        }


if __name__ == "__main__":
    # Demo usage
    import asyncio

    async def demo():
        print("Qualification Orchestrator Demo\n")
        print("=" * 70)

        orchestrator = QualificationOrchestrator("demo_location")

        # Start qualification flow
        result = await orchestrator.start_qualification_flow(
            contact_id="contact_456",
            contact_name="Mike Chen",
            initial_message="Hi, I'm looking for a 3-bedroom house in Austin under $500k",
            source="website"
        )

        flow_id = result["flow_id"]
        print(f"Started qualification flow: {flow_id}")
        print(f"Initial completion: {result['completion_percentage']}%")
        print(f"Next questions: {len(result['next_questions'])}")

        # Simulate responses
        responses = [
            "Our budget is around $450k and we're pre-approved",
            "We need to find something within 6 months, preferably sooner",
            "We're looking in Cedar Park or Round Rock area",
            "Looking for a single family home with a good school district"
        ]

        for i, response in enumerate(responses):
            print(f"\nProcessing response {i+1}: {response[:50]}...")
            result = await orchestrator.process_response(flow_id, response)
            print(f"Completion: {result['completion_percentage']}%")
            print(f"Current state: {result['current_state']}")

        # Get final status
        status = orchestrator.get_flow_status(flow_id)
        print(f"\nFinal Status:")
        print(f"Completion: {status['completion_percentage']}%")
        print(f"State: {status['current_state']}")
        print("=" * 70)

    # Run demo
    asyncio.run(demo())