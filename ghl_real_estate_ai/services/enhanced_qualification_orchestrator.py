"""
Enhanced Qualification Orchestrator - Agent Profile Aware Qualification Flows

Extends the base QualificationOrchestrator with multi-tenant agent profile integration,
role-specific qualification flows, and agent-specialized question templates.

Key Enhancements:
- Agent role-specific qualification areas (buyer/seller/transaction coordinator)
- Agent experience-adapted question complexity
- Specialization-based question prioritization
- Session-based context integration
- Multi-tenant shared agent pool support
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .qualification_orchestrator import QualificationOrchestrator
from .agent_profile_service import AgentProfileService
from .enhanced_claude_agent_service import EnhancedClaudeAgentService
from ..models.agent_profile_models import AgentProfile, AgentSession, AgentRole, ConversationStage

logger = logging.getLogger(__name__)


class EnhancedQualificationOrchestrator:
    """
    Agent profile aware qualification orchestrator with role-specific flows.

    Provides specialized qualification workflows for:
    - Buyer Agents: Budget, timeline, property preferences, financing
    - Seller Agents: Property details, pricing expectations, timeline, motivation
    - Transaction Coordinators: Compliance requirements, documentation, deadlines
    """

    # Role-specific qualification areas
    BUYER_AGENT_QUALIFICATION_AREAS = {
        "budget_financing": {
            "weight": 35,
            "required": True,
            "stage_threshold": "qualified",
            "questions": [
                "budget_range", "financing_status", "down_payment", "monthly_comfort",
                "pre_approval_amount", "financing_type"
            ]
        },
        "timeline_urgency": {
            "weight": 25,
            "required": True,
            "stage_threshold": "qualified",
            "questions": [
                "purchase_timeline", "urgency_factors", "current_housing_situation",
                "flexibility", "decision_timeline"
            ]
        },
        "location_preferences": {
            "weight": 20,
            "required": True,
            "stage_threshold": "qualified",
            "questions": [
                "preferred_areas", "location_flexibility", "commute_requirements",
                "neighborhood_priorities", "school_districts", "amenities"
            ]
        },
        "property_requirements": {
            "weight": 15,
            "required": False,
            "stage_threshold": "engaged",
            "questions": [
                "property_type", "size_requirements", "must_haves", "nice_to_haves",
                "style_preferences", "age_preferences"
            ]
        },
        "lifestyle_motivation": {
            "weight": 5,
            "required": False,
            "stage_threshold": "hot",
            "questions": [
                "buying_reason", "family_situation", "lifestyle_goals", "investment_intent"
            ]
        }
    }

    SELLER_AGENT_QUALIFICATION_AREAS = {
        "property_details": {
            "weight": 30,
            "required": True,
            "stage_threshold": "qualified",
            "questions": [
                "property_type", "size_details", "condition_assessment", "unique_features",
                "recent_improvements", "property_age"
            ]
        },
        "pricing_expectations": {
            "weight": 25,
            "required": True,
            "stage_threshold": "qualified",
            "questions": [
                "pricing_expectations", "market_research", "comparable_sales",
                "price_flexibility", "minimum_acceptable"
            ]
        },
        "selling_timeline": {
            "weight": 20,
            "required": True,
            "stage_threshold": "qualified",
            "questions": [
                "selling_timeline", "urgency_factors", "next_home_plans",
                "flexibility", "contingency_needs"
            ]
        },
        "selling_motivation": {
            "weight": 15,
            "required": True,
            "stage_threshold": "engaged",
            "questions": [
                "selling_reason", "motivation_strength", "alternative_options",
                "decision_drivers", "must_sell_factors"
            ]
        },
        "marketing_preferences": {
            "weight": 10,
            "required": False,
            "stage_threshold": "engaged",
            "questions": [
                "marketing_comfort", "showing_availability", "staging_openness",
                "photography_preferences", "open_house_comfort"
            ]
        }
    }

    TRANSACTION_COORDINATOR_QUALIFICATION_AREAS = {
        "contract_requirements": {
            "weight": 35,
            "required": True,
            "stage_threshold": "qualified",
            "questions": [
                "contract_type", "contingencies", "financing_requirements",
                "inspection_needs", "closing_timeline"
            ]
        },
        "compliance_documentation": {
            "weight": 25,
            "required": True,
            "stage_threshold": "qualified",
            "questions": [
                "disclosure_requirements", "documentation_status", "legal_requirements",
                "regulatory_compliance", "title_concerns"
            ]
        },
        "timeline_coordination": {
            "weight": 20,
            "required": True,
            "stage_threshold": "qualified",
            "questions": [
                "key_deadlines", "milestone_tracking", "coordination_needs",
                "scheduling_requirements", "dependency_management"
            ]
        },
        "party_coordination": {
            "weight": 15,
            "required": False,
            "stage_threshold": "engaged",
            "questions": [
                "party_involvement", "communication_preferences", "decision_makers",
                "coordination_challenges", "escalation_needs"
            ]
        },
        "issue_resolution": {
            "weight": 5,
            "required": False,
            "stage_threshold": "hot",
            "questions": [
                "potential_issues", "resolution_preferences", "risk_tolerance",
                "backup_plans", "contingency_strategies"
            ]
        }
    }

    # Role-specific question templates with experience level adaptation
    ROLE_QUESTION_TEMPLATES = {
        "buyer_agent": {
            "budget_range": {
                "novice": {
                    "base": "What price range are you comfortable with for your home purchase?",
                    "follow_up": "Have you spoken with a lender about what you might qualify for?"
                },
                "experienced": {
                    "base": "What's your target price range, and how does that align with your pre-approval amount?",
                    "follow_up": "Are you considering any specific loan programs or financing strategies?"
                },
                "expert": {
                    "base": "What's your investment criteria - target price range, financing structure, and expected ROI?",
                    "follow_up": "How does this purchase fit into your broader real estate portfolio strategy?"
                }
            },
            "purchase_timeline": {
                "novice": {
                    "base": "When are you hoping to buy your new home?",
                    "follow_up": "Is there anything that's driving this timeline?"
                },
                "experienced": {
                    "base": "What's your ideal purchase timeline, and what factors might affect it?",
                    "follow_up": "Do you have any rate lock considerations or market timing strategies?"
                },
                "expert": {
                    "base": "What's your strategic timeline for this acquisition, considering market conditions and opportunity cost?",
                    "follow_up": "How flexible are you on timing if the right opportunity presents itself?"
                }
            }
        },
        "seller_agent": {
            "pricing_expectations": {
                "novice": {
                    "base": "What do you think your home might be worth?",
                    "follow_up": "Have you looked at any recent sales in your neighborhood?"
                },
                "experienced": {
                    "base": "Based on your market research, what's your pricing strategy and expectations?",
                    "follow_up": "How much flexibility do you have on price based on market feedback?"
                },
                "expert": {
                    "base": "What's your pricing strategy considering current market dynamics, competition, and your net proceeds goals?",
                    "follow_up": "How do you want to position against comparable properties and what's your negotiation strategy?"
                }
            },
            "selling_timeline": {
                "novice": {
                    "base": "When do you need to sell your home?",
                    "follow_up": "Is there anything that's driving this timeline?"
                },
                "experienced": {
                    "base": "What's your optimal selling timeline, and what factors influence it?",
                    "follow_up": "Do you need to coordinate with purchasing another property?"
                },
                "expert": {
                    "base": "What's your strategic timeline for this disposition, considering market cycles and tax implications?",
                    "follow_up": "How does this sale fit into your broader real estate or investment strategy?"
                }
            }
        },
        "transaction_coordinator": {
            "contract_requirements": {
                "novice": {
                    "base": "What type of contract are we working with - purchase, sale, or lease?",
                    "follow_up": "Are there any special requirements or contingencies we need to track?"
                },
                "experienced": {
                    "base": "What are the key contract terms and contingencies that require coordination?",
                    "follow_up": "Which deadlines are most critical, and what dependencies should we monitor?"
                },
                "expert": {
                    "base": "What's the complexity of this transaction, and what risk factors should we prioritize in our coordination strategy?",
                    "follow_up": "Which party relationships and communication protocols need special attention?"
                }
            }
        }
    }

    def __init__(self, location_id: str):
        """
        Initialize enhanced qualification orchestrator with agent profile integration.

        Args:
            location_id: GHL Location ID for multi-tenant support
        """
        # Initialize base orchestrator
        self.base_orchestrator = QualificationOrchestrator(location_id)
        self.location_id = location_id

        # Initialize enhanced services
        self.agent_profile_service = AgentProfileService()
        self.enhanced_claude_service = EnhancedClaudeAgentService()

        # Enhanced data storage
        self.data_dir = Path(__file__).parent.parent / "data" / "enhanced_qualification" / location_id
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.agent_flows_file = self.data_dir / "agent_qualification_flows.json"
        self.role_metrics_file = self.data_dir / "role_metrics.json"

        # Load enhanced data
        self.agent_flows = self._load_agent_flows()
        self.role_metrics = self._load_role_metrics()

        logger.info(f"EnhancedQualificationOrchestrator initialized for location {location_id}")

    def _load_agent_flows(self) -> Dict:
        """Load agent-specific qualification flows."""
        if self.agent_flows_file.exists():
            try:
                with open(self.agent_flows_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading agent flows: {e}")
        return {}

    def _save_agent_flows(self) -> None:
        """Save agent-specific qualification flows."""
        try:
            with open(self.agent_flows_file, 'w') as f:
                json.dump(self.agent_flows, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving agent flows: {e}")

    def _load_role_metrics(self) -> Dict:
        """Load role-specific metrics."""
        if self.role_metrics_file.exists():
            try:
                with open(self.role_metrics_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading role metrics: {e}")

        return {
            "buyer_agent": {"flows_started": 0, "flows_completed": 0, "avg_completion_time": 0},
            "seller_agent": {"flows_started": 0, "flows_completed": 0, "avg_completion_time": 0},
            "transaction_coordinator": {"flows_started": 0, "flows_completed": 0, "avg_completion_time": 0}
        }

    def _save_role_metrics(self) -> None:
        """Save role-specific metrics."""
        try:
            with open(self.role_metrics_file, 'w') as f:
                json.dump(self.role_metrics, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving role metrics: {e}")

    async def start_agent_aware_qualification_flow(
        self,
        contact_id: str,
        contact_name: str,
        agent_id: str,
        agent_session_id: str,
        initial_message: str = "",
        source: str = "website",
        lead_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start an agent profile aware qualification flow.

        Args:
            contact_id: Unique contact identifier
            contact_name: Contact's name
            agent_id: Agent identifier
            agent_session_id: Current agent session ID
            initial_message: Initial message from contact
            source: Lead source
            lead_context: Additional lead context

        Returns:
            Dictionary containing flow initialization with agent specialization
        """
        try:
            # Get agent profile and session
            agent_profile = await self.agent_profile_service.get_agent_profile(
                agent_id=agent_id,
                requester_location_id=self.location_id
            )

            agent_session = await self.agent_profile_service.get_agent_session(agent_session_id)

            if not agent_profile:
                logger.warning(f"Agent profile not found for {agent_id}, falling back to base orchestrator")
                return await self.base_orchestrator.start_qualification_flow(
                    contact_id, contact_name, initial_message, source, agent_id
                )

            flow_id = f"enhanced_qual_{contact_id}_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            now = datetime.now().isoformat()

            # Get role-specific qualification areas
            qualification_areas = self._get_qualification_areas_for_role(agent_profile.primary_role)

            # Analyze initial message with agent context
            initial_analysis = {}
            if initial_message:
                initial_analysis = await self._analyze_initial_message_with_agent_context(
                    initial_message, agent_profile, lead_context
                )

            # Create enhanced qualification flow
            enhanced_flow = {
                "flow_id": flow_id,
                "contact_id": contact_id,
                "contact_name": contact_name,
                "location_id": self.location_id,
                "agent_id": agent_id,
                "agent_session_id": agent_session_id,
                "source": source,
                "started_at": now,
                "updated_at": now,
                "status": "active",

                # Agent profile context
                "agent_profile": {
                    "primary_role": agent_profile.primary_role.value,
                    "secondary_roles": [role.value for role in agent_profile.secondary_roles],
                    "years_experience": agent_profile.years_experience,
                    "specializations": agent_profile.specializations,
                    "communication_style": agent_profile.communication_style.value,
                    "coaching_style": agent_profile.coaching_style_preference.value
                },

                # Session context
                "session_context": {
                    "conversation_stage": agent_session.conversation_stage.value if agent_session else "discovery",
                    "guidance_types": [gt.value for gt in agent_session.active_guidance_types] if agent_session else [],
                    "session_start": agent_session.session_start_time.isoformat() if agent_session else now
                },

                # Role-specific qualification tracking
                "qualification_areas": qualification_areas.keys(),
                "qualification_data": {
                    area: {
                        "completed": False,
                        "confidence": 0,
                        "responses": {},
                        "questions_asked": [],
                        "semantic_signals": [],
                        "role_specific_insights": []
                    }
                    for area in qualification_areas.keys()
                },

                # Enhanced tracking
                "conversation_history": [],
                "role_specific_questions_used": [],
                "experience_adaptations": [],
                "specialization_insights": [],

                # Initial analysis
                "initial_message": initial_message,
                "initial_analysis": initial_analysis,
                "lead_context": lead_context or {},

                # Metrics
                "enhanced_metrics": {
                    "role_specific_completions": {},
                    "question_effectiveness": {},
                    "specialization_relevance": {},
                    "experience_adaptation_score": 0
                }
            }

            # Generate role-specific initial questions
            initial_questions = await self._generate_role_specific_questions(
                enhanced_flow, agent_profile, context="flow_start"
            )
            enhanced_flow["next_recommended_questions"] = initial_questions[:3]

            # Save enhanced flow
            self.agent_flows[flow_id] = enhanced_flow
            self._save_agent_flows()

            # Update role-specific metrics
            role_key = agent_profile.primary_role.value.lower()
            if role_key not in self.role_metrics:
                self.role_metrics[role_key] = {"flows_started": 0, "flows_completed": 0, "avg_completion_time": 0}

            self.role_metrics[role_key]["flows_started"] += 1
            self._save_role_metrics()

            # Update agent session with flow context
            if agent_session:
                await self._update_session_with_qualification_context(
                    agent_session, flow_id, qualification_areas
                )

            logger.info(
                f"Started enhanced qualification flow {flow_id} for {agent_profile.primary_role.value} agent {agent_id}"
            )

            return {
                "flow_id": flow_id,
                "status": "started",
                "agent_role": agent_profile.primary_role.value,
                "qualification_areas": list(qualification_areas.keys()),
                "next_questions": enhanced_flow["next_recommended_questions"],
                "completion_percentage": 0,
                "role_specific_approach": True,
                "experience_level": self._get_experience_level(agent_profile.years_experience),
                "specializations_applied": agent_profile.specializations[:3],
                "initial_analysis": initial_analysis,
                "enhanced_features": True
            }

        except Exception as e:
            logger.error(f"Error starting enhanced qualification flow: {e}")
            return {"error": str(e), "status": "failed", "enhanced_features": False}

    async def process_agent_aware_response(
        self,
        flow_id: str,
        user_message: str,
        agent_response: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process response with agent profile awareness and role-specific analysis.

        Args:
            flow_id: Enhanced qualification flow identifier
            user_message: User's response/message
            agent_response: Agent's response (if any)
            context: Additional context data

        Returns:
            Dictionary containing role-specific analysis and recommendations
        """
        try:
            if flow_id not in self.agent_flows:
                return {"error": "Enhanced flow not found", "status": "failed"}

            flow = self.agent_flows[flow_id]
            now = datetime.now().isoformat()

            # Get agent profile for role-specific processing
            agent_id = flow["agent_id"]
            agent_profile = await self.agent_profile_service.get_agent_profile(agent_id)

            if not agent_profile:
                logger.warning(f"Agent profile not found during processing, using standard analysis")
                # Could fallback to base orchestrator here
                return {"error": "Agent profile unavailable", "status": "fallback_required"}

            # Add to conversation history with agent context
            conversation_entry = {
                "timestamp": now,
                "user_message": user_message,
                "agent_response": agent_response,
                "context": context or {},
                "agent_role": agent_profile.primary_role.value
            }
            flow["conversation_history"].append(conversation_entry)

            # Enhanced semantic analysis with agent context
            enhanced_analysis = await self._analyze_response_with_agent_context(
                flow, user_message, agent_profile
            )

            # Update role-specific qualification data
            role_qualification_updates = await self._update_role_specific_qualification_data(
                flow, user_message, enhanced_analysis, agent_profile
            )

            # Calculate role-specific completion percentage
            completion_percentage = self._calculate_role_specific_completion(flow, agent_profile)
            flow["completion_percentage"] = completion_percentage

            # Generate role-specific next questions
            next_questions = await self._generate_role_specific_questions(
                flow, agent_profile, context="response_processed",
                last_response=user_message, analysis=enhanced_analysis
            )
            flow["next_recommended_questions"] = next_questions

            # Get agent-specific recommendations
            agent_recommendations = await self._get_role_specific_recommendations(
                flow, agent_profile, enhanced_analysis
            )

            # Update enhanced metrics
            self._update_enhanced_metrics(flow, enhanced_analysis, agent_profile)

            # Check if role-specific qualification is complete
            role_specific_complete = self._assess_role_specific_completion(flow, agent_profile)
            if role_specific_complete and flow["status"] == "active":
                await self._complete_enhanced_qualification_flow(flow, agent_profile)

            # Save updates
            flow["updated_at"] = now
            self._save_agent_flows()

            return {
                "flow_id": flow_id,
                "status": flow["status"],
                "agent_role": agent_profile.primary_role.value,
                "completion_percentage": completion_percentage,
                "enhanced_analysis": enhanced_analysis,
                "role_qualification_updates": role_qualification_updates,
                "next_questions": next_questions,
                "agent_recommendations": agent_recommendations,
                "role_specific_complete": role_specific_complete,
                "specialization_insights": enhanced_analysis.get("specialization_insights", []),
                "experience_adaptations": flow.get("experience_adaptations", []),
                "enhanced_features": True
            }

        except Exception as e:
            logger.error(f"Error processing enhanced response for flow {flow_id}: {e}")
            return {"error": str(e), "status": "failed"}

    def _get_qualification_areas_for_role(self, role: AgentRole) -> Dict[str, Any]:
        """Get role-specific qualification areas."""
        if role == AgentRole.BUYER_AGENT:
            return self.BUYER_AGENT_QUALIFICATION_AREAS
        elif role == AgentRole.SELLER_AGENT:
            return self.SELLER_AGENT_QUALIFICATION_AREAS
        elif role == AgentRole.TRANSACTION_COORDINATOR:
            return self.TRANSACTION_COORDINATOR_QUALIFICATION_AREAS
        elif role == AgentRole.DUAL_AGENT:
            # For dual agents, use buyer areas as default (could be context-dependent)
            return self.BUYER_AGENT_QUALIFICATION_AREAS
        else:
            # Fallback to base orchestrator areas
            return self.base_orchestrator.QUALIFICATION_AREAS

    def _get_experience_level(self, years: int) -> str:
        """Determine experience level from years of experience."""
        if years < 2:
            return "novice"
        elif years < 7:
            return "experienced"
        else:
            return "expert"

    async def _analyze_initial_message_with_agent_context(
        self,
        message: str,
        agent_profile: AgentProfile,
        lead_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze initial message with agent profile context."""
        try:
            # Use enhanced Claude service for role-aware analysis
            enhanced_analysis = await self.enhanced_claude_service.get_role_specific_insights(
                agent_profile.agent_id,
                "temp_session",  # Temporary session for analysis
                {"initial_message": message, "lead_context": lead_context or {}},
                "initial_qualification"
            )

            return {
                "claude_analysis": enhanced_analysis,
                "role_context": agent_profile.primary_role.value,
                "specialization_relevance": self._assess_specialization_relevance(
                    message, agent_profile.specializations
                ),
                "experience_adaptation": self._get_experience_level(agent_profile.years_experience)
            }

        except Exception as e:
            logger.warning(f"Enhanced initial analysis failed: {e}")
            return {"error": str(e), "fallback": True}

    def _assess_specialization_relevance(self, message: str, specializations: List[str]) -> Dict[str, Any]:
        """Assess how relevant agent specializations are to the message."""
        relevance_scores = {}
        message_lower = message.lower()

        specialization_keywords = {
            "first_time_buyers": ["first time", "new to", "never bought", "first home"],
            "luxury_homes": ["luxury", "high-end", "premium", "executive", "upscale"],
            "investment_properties": ["investment", "rental", "cash flow", "roi", "portfolio"],
            "commercial_properties": ["commercial", "business", "office", "retail", "warehouse"],
            "condominiums": ["condo", "condominium", "unit", "hoa", "association"],
            "new_construction": ["new", "construction", "builder", "custom", "ground up"],
            "relocation": ["relocating", "moving", "transfer", "new job", "company"],
            "downsizing": ["downsize", "smaller", "empty nest", "retirement", "simplify"],
            "foreclosure": ["foreclosure", "distressed", "short sale", "reo", "bank owned"]
        }

        for specialization in specializations:
            spec_lower = specialization.lower()
            keywords = specialization_keywords.get(spec_lower, [spec_lower])

            relevance_score = sum(1 for keyword in keywords if keyword in message_lower)
            if relevance_score > 0:
                relevance_scores[specialization] = min(100, relevance_score * 25)

        return {
            "scores": relevance_scores,
            "top_relevant": max(relevance_scores.items(), key=lambda x: x[1]) if relevance_scores else None,
            "overall_relevance": sum(relevance_scores.values()) / len(specializations) if specializations else 0
        }

    async def _generate_role_specific_questions(
        self,
        flow: Dict[str, Any],
        agent_profile: AgentProfile,
        context: str = "",
        last_response: Optional[str] = None,
        analysis: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate questions specific to agent role and experience."""
        try:
            role = agent_profile.primary_role
            experience_level = self._get_experience_level(agent_profile.years_experience)
            qualification_areas = self._get_qualification_areas_for_role(role)

            # Identify priority areas for this role
            priority_areas = []
            for area_name, area_config in qualification_areas.items():
                area_data = flow["qualification_data"][area_name]

                if not area_data["completed"]:
                    priority = area_config["weight"] * (100 - area_data["confidence"]) / 100

                    # Boost priority based on specialization relevance
                    if analysis:
                        spec_relevance = analysis.get("specialization_relevance", {})
                        if spec_relevance.get("overall_relevance", 0) > 0:
                            priority *= 1.2

                    priority_areas.append((area_name, priority, area_config))

            # Sort by priority
            priority_areas.sort(key=lambda x: x[1], reverse=True)

            questions = []
            role_key = role.value.lower()

            for area_name, priority, area_config in priority_areas[:3]:
                area_data = flow["qualification_data"][area_name]

                # Get available questions for this area
                available_questions = [
                    q for q in area_config["questions"]
                    if q not in area_data["questions_asked"]
                ]

                if available_questions and role_key in self.ROLE_QUESTION_TEMPLATES:
                    question_id = available_questions[0]
                    role_templates = self.ROLE_QUESTION_TEMPLATES[role_key]

                    if question_id in role_templates:
                        # Get experience-appropriate template
                        template = role_templates[question_id].get(
                            experience_level,
                            role_templates[question_id].get("experienced", {})
                        )

                        question_text = template.get("base", f"Tell me about your {area_name.replace('_', ' ')} preferences")
                        follow_up = template.get("follow_up", "")

                        questions.append({
                            "area": area_name,
                            "question_id": question_id,
                            "question_text": question_text,
                            "follow_up": follow_up,
                            "priority": priority,
                            "role_specific": True,
                            "experience_adapted": True,
                            "experience_level": experience_level,
                            "specializations_relevant": self._get_relevant_specializations(
                                area_name, agent_profile.specializations
                            )
                        })

                        # Mark question as used
                        area_data["questions_asked"].append(question_id)

            return questions

        except Exception as e:
            logger.error(f"Error generating role-specific questions: {e}")
            return []

    def _get_relevant_specializations(self, area_name: str, specializations: List[str]) -> List[str]:
        """Get specializations relevant to a specific qualification area."""
        area_specialization_map = {
            "budget_financing": ["investment_properties", "luxury_homes", "first_time_buyers"],
            "location_preferences": ["relocation", "luxury_homes", "commercial_properties"],
            "property_requirements": ["luxury_homes", "new_construction", "condominiums"],
            "timeline_urgency": ["relocation", "investment_properties"],
            "property_details": ["luxury_homes", "new_construction", "commercial_properties"],
            "pricing_expectations": ["luxury_homes", "investment_properties", "commercial_properties"]
        }

        relevant_specs = area_specialization_map.get(area_name, [])
        return [spec for spec in specializations if spec in relevant_specs]

    async def _analyze_response_with_agent_context(
        self,
        flow: Dict[str, Any],
        user_message: str,
        agent_profile: AgentProfile
    ) -> Dict[str, Any]:
        """Analyze user response with agent profile context."""
        try:
            # Use enhanced Claude service for role-aware analysis
            session_id = flow.get("agent_session_id", "temp_session")

            enhanced_analysis = await self.enhanced_claude_service.get_role_specific_insights(
                agent_profile.agent_id,
                session_id,
                {
                    "user_message": user_message,
                    "conversation_history": flow["conversation_history"][-3:],
                    "qualification_progress": flow["qualification_data"],
                    "flow_context": flow
                },
                "response_analysis"
            )

            # Extract role-specific qualification signals
            role_signals = self._extract_role_specific_signals(
                user_message, agent_profile, enhanced_analysis
            )

            # Assess specialization insights
            specialization_insights = self._generate_specialization_insights(
                user_message, agent_profile, enhanced_analysis
            )

            return {
                "enhanced_claude_analysis": enhanced_analysis,
                "role_specific_signals": role_signals,
                "specialization_insights": specialization_insights,
                "experience_context": self._get_experience_level(agent_profile.years_experience),
                "confidence": enhanced_analysis.get("confidence", 75),
                "role_relevance_score": self._calculate_role_relevance_score(user_message, agent_profile)
            }

        except Exception as e:
            logger.warning(f"Enhanced response analysis failed: {e}")
            return {"error": str(e), "fallback": True}

    def _extract_role_specific_signals(
        self,
        message: str,
        agent_profile: AgentProfile,
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract signals specific to agent role."""
        role = agent_profile.primary_role
        signals = {}

        if role == AgentRole.BUYER_AGENT:
            signals = self._extract_buyer_signals(message, analysis)
        elif role == AgentRole.SELLER_AGENT:
            signals = self._extract_seller_signals(message, analysis)
        elif role == AgentRole.TRANSACTION_COORDINATOR:
            signals = self._extract_transaction_signals(message, analysis)

        return signals

    def _extract_buyer_signals(self, message: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract buyer-specific qualification signals."""
        message_lower = message.lower()
        signals = {}

        # Budget/financing signals
        if any(word in message_lower for word in ["budget", "afford", "financing", "loan", "pre-approval"]):
            signals["budget_financing"] = {
                "mentioned": True,
                "confidence": analysis.get("confidence", 50),
                "financing_details": self._extract_financing_details(message)
            }

        # Property preference signals
        if any(word in message_lower for word in ["bedrooms", "bathrooms", "size", "type", "style"]):
            signals["property_requirements"] = {
                "mentioned": True,
                "specificity": len([word for word in ["bedrooms", "bathrooms", "size", "type"] if word in message_lower]),
                "details": self._extract_property_details(message)
            }

        return signals

    def _extract_seller_signals(self, message: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract seller-specific qualification signals."""
        message_lower = message.lower()
        signals = {}

        # Pricing expectation signals
        if any(word in message_lower for word in ["price", "worth", "value", "market", "appraisal"]):
            signals["pricing_expectations"] = {
                "mentioned": True,
                "confidence": analysis.get("confidence", 50),
                "price_indicators": self._extract_price_indicators(message)
            }

        # Timeline/motivation signals
        if any(word in message_lower for word in ["sell", "move", "relocate", "downsize", "upgrade"]):
            signals["selling_motivation"] = {
                "mentioned": True,
                "urgency_level": self._assess_urgency_level(message),
                "motivation_type": self._identify_motivation_type(message)
            }

        return signals

    def _extract_transaction_signals(self, message: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract transaction coordinator specific signals."""
        message_lower = message.lower()
        signals = {}

        # Compliance/documentation signals
        if any(word in message_lower for word in ["contract", "disclosure", "inspection", "deadline"]):
            signals["compliance_documentation"] = {
                "mentioned": True,
                "complexity": len([word for word in ["contract", "disclosure", "inspection"] if word in message_lower]),
                "urgency_factors": self._identify_urgency_factors(message)
            }

        return signals

    async def _update_session_with_qualification_context(
        self,
        agent_session: AgentSession,
        flow_id: str,
        qualification_areas: Dict[str, Any]
    ):
        """Update agent session with qualification flow context."""
        try:
            # Update workflow context with qualification information
            workflow_context = agent_session.workflow_context or {}
            workflow_context.update({
                "qualification_flow_id": flow_id,
                "qualification_areas": list(qualification_areas.keys()),
                "role_specific_flow": True
            })
            agent_session.workflow_context = workflow_context

            # Save updated session
            await self.agent_profile_service.update_agent_session(agent_session)

        except Exception as e:
            logger.warning(f"Error updating session with qualification context: {e}")

    def _calculate_role_specific_completion(
        self,
        flow: Dict[str, Any],
        agent_profile: AgentProfile
    ) -> float:
        """Calculate completion percentage based on role-specific requirements."""
        qualification_areas = self._get_qualification_areas_for_role(agent_profile.primary_role)
        total_weight = sum(area["weight"] for area in qualification_areas.values())
        completed_weight = 0

        for area_name, area_config in qualification_areas.items():
            area_data = flow["qualification_data"][area_name]

            # Calculate area completion with role-specific weighting
            area_completion = area_data["confidence"] / 100

            # Apply specialization bonus
            if area_name in ["property_requirements", "location_preferences"]:
                specialization_bonus = len(flow.get("specialization_insights", [])) * 0.1
                area_completion = min(1.0, area_completion + specialization_bonus)

            completed_weight += area_completion * area_config["weight"]

        return round((completed_weight / total_weight) * 100, 1)

    async def _get_role_specific_recommendations(
        self,
        flow: Dict[str, Any],
        agent_profile: AgentProfile,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate role-specific recommendations for agents."""
        recommendations = []
        completion = flow["completion_percentage"]
        role = agent_profile.primary_role

        if role == AgentRole.BUYER_AGENT:
            recommendations.extend(self._get_buyer_agent_recommendations(flow, completion, analysis))
        elif role == AgentRole.SELLER_AGENT:
            recommendations.extend(self._get_seller_agent_recommendations(flow, completion, analysis))
        elif role == AgentRole.TRANSACTION_COORDINATOR:
            recommendations.extend(self._get_tc_recommendations(flow, completion, analysis))

        # Add experience-based recommendations
        experience_level = self._get_experience_level(agent_profile.years_experience)
        recommendations.extend(self._get_experience_based_recommendations(experience_level, completion))

        return recommendations

    def _get_buyer_agent_recommendations(
        self,
        flow: Dict[str, Any],
        completion: float,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get buyer agent specific recommendations."""
        recommendations = []

        if completion < 40:
            recommendations.append({
                "type": "buyer_qualification",
                "priority": "high",
                "message": "Focus on budget and financing pre-approval status",
                "action": "verify_financing",
                "role_specific": True
            })

        if completion >= 60:
            recommendations.append({
                "type": "buyer_next_steps",
                "priority": "medium",
                "message": "Start property search and schedule showings",
                "action": "begin_search",
                "role_specific": True
            })

        return recommendations

    def _get_seller_agent_recommendations(
        self,
        flow: Dict[str, Any],
        completion: float,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get seller agent specific recommendations."""
        recommendations = []

        if completion < 50:
            recommendations.append({
                "type": "seller_qualification",
                "priority": "high",
                "message": "Establish pricing expectations and timeline",
                "action": "price_timeline_discussion",
                "role_specific": True
            })

        if completion >= 70:
            recommendations.append({
                "type": "seller_next_steps",
                "priority": "medium",
                "message": "Schedule property assessment and discuss marketing strategy",
                "action": "listing_preparation",
                "role_specific": True
            })

        return recommendations

    def _get_tc_recommendations(
        self,
        flow: Dict[str, Any],
        completion: float,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get transaction coordinator specific recommendations."""
        recommendations = []

        if completion < 60:
            recommendations.append({
                "type": "tc_documentation",
                "priority": "high",
                "message": "Gather required documentation and review deadlines",
                "action": "documentation_checklist",
                "role_specific": True
            })

        if completion >= 80:
            recommendations.append({
                "type": "tc_coordination",
                "priority": "critical",
                "message": "Coordinate with all parties and prepare closing timeline",
                "action": "closing_coordination",
                "role_specific": True
            })

        return recommendations

    def _get_experience_based_recommendations(
        self,
        experience_level: str,
        completion: float
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on agent experience level."""
        recommendations = []

        if experience_level == "novice" and completion > 50:
            recommendations.append({
                "type": "guidance",
                "priority": "medium",
                "message": "Consider involving a more experienced agent for complex aspects",
                "action": "seek_mentorship",
                "experience_based": True
            })
        elif experience_level == "expert" and completion > 70:
            recommendations.append({
                "type": "advanced_strategy",
                "priority": "low",
                "message": "Consider advanced strategies based on market conditions",
                "action": "strategic_analysis",
                "experience_based": True
            })

        return recommendations

    # Helper methods for signal extraction
    def _extract_financing_details(self, message: str) -> Dict[str, Any]:
        """Extract financing-related details from message."""
        # Implementation would parse financing details
        return {"type": "conventional", "status": "unknown"}

    def _extract_property_details(self, message: str) -> Dict[str, Any]:
        """Extract property requirement details from message."""
        # Implementation would parse property details
        return {"bedrooms": None, "bathrooms": None, "type": "unknown"}

    def _extract_price_indicators(self, message: str) -> Dict[str, Any]:
        """Extract pricing expectation indicators."""
        # Implementation would parse pricing signals
        return {"range": "unknown", "flexibility": "unknown"}

    def _assess_urgency_level(self, message: str) -> str:
        """Assess urgency level from message content."""
        urgent_words = ["urgent", "asap", "soon", "quickly", "immediately"]
        if any(word in message.lower() for word in urgent_words):
            return "high"
        return "medium"

    def _identify_motivation_type(self, message: str) -> str:
        """Identify type of selling motivation."""
        if "relocat" in message.lower():
            return "relocation"
        elif any(word in message.lower() for word in ["downsize", "smaller"]):
            return "downsizing"
        elif "upgrade" in message.lower():
            return "upsizing"
        return "other"

    def _identify_urgency_factors(self, message: str) -> List[str]:
        """Identify urgency factors for transaction coordination."""
        factors = []
        if "deadline" in message.lower():
            factors.append("deadline_driven")
        if "inspection" in message.lower():
            factors.append("inspection_dependent")
        return factors

    def _generate_specialization_insights(
        self,
        message: str,
        agent_profile: AgentProfile,
        analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate insights based on agent specializations."""
        insights = []

        for specialization in agent_profile.specializations:
            relevance = self._assess_specialization_relevance(message, [specialization])
            if relevance["scores"].get(specialization, 0) > 50:
                insights.append(f"Specialization '{specialization}' highly relevant to this lead")

        return insights

    def _calculate_role_relevance_score(
        self,
        message: str,
        agent_profile: AgentProfile
    ) -> float:
        """Calculate how relevant the message is to the agent's role."""
        role_keywords = {
            AgentRole.BUYER_AGENT: ["buy", "purchase", "looking", "search", "home"],
            AgentRole.SELLER_AGENT: ["sell", "list", "market", "price", "value"],
            AgentRole.TRANSACTION_COORDINATOR: ["contract", "close", "documentation", "deadline"]
        }

        keywords = role_keywords.get(agent_profile.primary_role, [])
        message_lower = message.lower()

        relevance_score = sum(1 for keyword in keywords if keyword in message_lower)
        return min(100, relevance_score * 20)

    def _update_enhanced_metrics(
        self,
        flow: Dict[str, Any],
        analysis: Dict[str, Any],
        agent_profile: AgentProfile
    ):
        """Update enhanced metrics with role and specialization data."""
        metrics = flow.get("enhanced_metrics", {})

        # Update role-specific completion metrics
        role_key = agent_profile.primary_role.value
        if "role_specific_completions" not in metrics:
            metrics["role_specific_completions"] = {}

        metrics["role_specific_completions"][role_key] = flow.get("completion_percentage", 0)

        # Update specialization relevance
        if "specialization_relevance" not in metrics:
            metrics["specialization_relevance"] = {}

        for specialization in agent_profile.specializations:
            metrics["specialization_relevance"][specialization] = analysis.get("role_relevance_score", 50)

        flow["enhanced_metrics"] = metrics

    def _assess_role_specific_completion(
        self,
        flow: Dict[str, Any],
        agent_profile: AgentProfile
    ) -> bool:
        """Assess if role-specific qualification is complete."""
        completion = flow.get("completion_percentage", 0)
        role = agent_profile.primary_role

        # Role-specific completion thresholds
        completion_thresholds = {
            AgentRole.BUYER_AGENT: 75,  # Need strong budget/timeline/location
            AgentRole.SELLER_AGENT: 70,  # Need pricing/timeline/motivation
            AgentRole.TRANSACTION_COORDINATOR: 80,  # Need detailed compliance info
            AgentRole.DUAL_AGENT: 75
        }

        threshold = completion_thresholds.get(role, 75)
        return completion >= threshold

    async def _complete_enhanced_qualification_flow(
        self,
        flow: Dict[str, Any],
        agent_profile: AgentProfile
    ):
        """Complete enhanced qualification flow with role-specific metrics."""
        flow["status"] = "completed"
        flow["completed_at"] = datetime.now().isoformat()

        # Calculate time to completion
        started_at = datetime.fromisoformat(flow["started_at"])
        completed_at = datetime.fromisoformat(flow["completed_at"])
        time_to_completion = (completed_at - started_at).total_seconds() / 3600

        flow["enhanced_metrics"]["time_to_qualification"] = round(time_to_completion, 2)

        # Update role-specific metrics
        role_key = agent_profile.primary_role.value.lower()
        if role_key in self.role_metrics:
            self.role_metrics[role_key]["flows_completed"] += 1

            # Update average completion time
            current_avg = self.role_metrics[role_key].get("avg_completion_time", 0)
            completed_count = self.role_metrics[role_key]["flows_completed"]

            new_avg = ((current_avg * (completed_count - 1)) + time_to_completion) / completed_count
            self.role_metrics[role_key]["avg_completion_time"] = round(new_avg, 2)

        self._save_role_metrics()

        logger.info(
            f"Enhanced qualification flow {flow['flow_id']} completed for {agent_profile.primary_role.value} "
            f"agent in {time_to_completion:.2f} hours"
        )

    def get_enhanced_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get enhanced flow status with role-specific insights."""
        if flow_id not in self.agent_flows:
            return {"error": "Enhanced flow not found"}

        flow = self.agent_flows[flow_id]

        return {
            "flow_id": flow_id,
            "contact_id": flow["contact_id"],
            "contact_name": flow["contact_name"],
            "agent_id": flow["agent_id"],
            "agent_role": flow["agent_profile"]["primary_role"],
            "status": flow["status"],
            "completion_percentage": flow["completion_percentage"],
            "qualification_areas": flow["qualification_areas"],
            "specializations": flow["agent_profile"]["specializations"],
            "experience_level": self._get_experience_level(flow["agent_profile"]["years_experience"]),
            "next_recommended_questions": flow.get("next_recommended_questions", []),
            "enhanced_metrics": flow.get("enhanced_metrics", {}),
            "role_specific_insights": flow.get("specialization_insights", []),
            "enhanced_features": True
        }

    def get_role_analytics(self) -> Dict[str, Any]:
        """Get analytics broken down by agent roles."""
        analytics = {"role_metrics": self.role_metrics}

        # Calculate role-specific completion rates
        role_completion_rates = {}
        for role_key, metrics in self.role_metrics.items():
            if metrics["flows_started"] > 0:
                completion_rate = (metrics["flows_completed"] / metrics["flows_started"]) * 100
                role_completion_rates[role_key] = round(completion_rate, 1)

        analytics["role_completion_rates"] = role_completion_rates

        # Calculate specialization insights
        specialization_stats = defaultdict(lambda: {"flows": 0, "avg_completion": 0})

        for flow in self.agent_flows.values():
            for specialization in flow.get("agent_profile", {}).get("specializations", []):
                specialization_stats[specialization]["flows"] += 1
                completion = flow.get("completion_percentage", 0)
                current_avg = specialization_stats[specialization]["avg_completion"]
                flow_count = specialization_stats[specialization]["flows"]

                new_avg = ((current_avg * (flow_count - 1)) + completion) / flow_count
                specialization_stats[specialization]["avg_completion"] = round(new_avg, 1)

        analytics["specialization_analytics"] = dict(specialization_stats)

        return analytics


# Global instance for easy access
enhanced_qualification_orchestrator = None


def get_enhanced_qualification_orchestrator(location_id: str) -> EnhancedQualificationOrchestrator:
    """Get or create enhanced qualification orchestrator instance for location."""
    global enhanced_qualification_orchestrator

    if enhanced_qualification_orchestrator is None or enhanced_qualification_orchestrator.location_id != location_id:
        enhanced_qualification_orchestrator = EnhancedQualificationOrchestrator(location_id)

    return enhanced_qualification_orchestrator


async def start_agent_qualification_flow(
    contact_id: str,
    contact_name: str,
    agent_id: str,
    agent_session_id: str,
    location_id: str,
    initial_message: str = "",
    source: str = "website"
) -> Dict[str, Any]:
    """Convenience function for starting agent-aware qualification flows."""
    orchestrator = get_enhanced_qualification_orchestrator(location_id)
    return await orchestrator.start_agent_aware_qualification_flow(
        contact_id, contact_name, agent_id, agent_session_id, initial_message, source
    )