"""
Agent Collaboration Service

Team collaboration features for real estate agents including lead sharing,
deal collaboration, team insights, and Claude-powered team optimization.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from .claude_agent_service import claude_agent_service
from .agent_workflow_automation import agent_workflow_automation, TaskPriority
from ..ghl_utils.config import settings

logger = logging.getLogger(__name__)


class CollaborationType(Enum):
    """Types of agent collaboration"""
    LEAD_REFERRAL = "lead_referral"
    DEAL_PARTNERSHIP = "deal_partnership"
    KNOWLEDGE_SHARE = "knowledge_share"
    MENTORSHIP = "mentorship"
    TEAM_PROJECT = "team_project"
    COVERAGE_REQUEST = "coverage_request"


class CollaborationStatus(Enum):
    """Status of collaboration requests"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TeamRole(Enum):
    """Team roles for agents"""
    AGENT = "agent"
    SENIOR_AGENT = "senior_agent"
    TEAM_LEAD = "team_lead"
    BROKER = "broker"
    MANAGER = "manager"


@dataclass
class CollaborationRequest:
    """Collaboration request between agents"""
    id: str
    requesting_agent_id: str
    target_agent_id: str
    collaboration_type: CollaborationType
    status: CollaborationStatus
    title: str
    description: str
    lead_id: Optional[str] = None
    property_id: Optional[str] = None
    expected_value: Optional[float] = None
    commission_split: Optional[Dict[str, float]] = None
    deadline: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    accepted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Team:
    """Real estate team structure"""
    id: str
    name: str
    lead_agent_id: str
    member_agent_ids: Set[str]
    territory: Optional[str] = None
    specializations: List[str] = field(default_factory=list)
    commission_structure: Dict[str, Any] = field(default_factory=dict)
    goals: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    active: bool = True


@dataclass
class AgentProfile:
    """Extended agent profile for collaboration"""
    agent_id: str
    name: str
    role: TeamRole
    team_id: Optional[str] = None
    specializations: List[str] = field(default_factory=list)
    territory: Optional[str] = None
    experience_years: int = 0
    preferred_collaboration_types: List[CollaborationType] = field(default_factory=list)
    availability_status: str = "available"  # available, busy, away
    performance_rating: float = 0.0
    collaboration_rating: float = 0.0
    mentor_status: str = "none"  # mentor, mentee, none
    skills: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)


@dataclass
class TeamInsight:
    """Team performance and collaboration insights"""
    team_id: str
    period_start: datetime
    period_end: datetime
    total_deals: int = 0
    total_volume: float = 0.0
    collaboration_count: int = 0
    member_performance: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    top_collaborators: List[str] = field(default_factory=list)
    bottlenecks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class AgentCollaborationService:
    """
    Comprehensive agent collaboration and team management service.

    Enables agents to collaborate effectively on deals, share knowledge,
    and optimize team performance with AI insights.
    """

    def __init__(self):
        self.agent_profiles: Dict[str, AgentProfile] = {}
        self.teams: Dict[str, Team] = {}
        self.collaboration_requests: Dict[str, CollaborationRequest] = {}
        self.active_collaborations: Dict[str, List[str]] = {}  # agent_id -> collaboration_ids
        self.team_insights: Dict[str, List[TeamInsight]] = {}

    async def create_agent_profile(
        self,
        agent_id: str,
        name: str,
        role: TeamRole,
        specializations: Optional[List[str]] = None,
        territory: Optional[str] = None,
        experience_years: int = 0,
        skills: Optional[List[str]] = None,
        languages: Optional[List[str]] = None
    ) -> AgentProfile:
        """Create or update an agent's collaboration profile"""

        profile = AgentProfile(
            agent_id=agent_id,
            name=name,
            role=role,
            specializations=specializations or [],
            territory=territory,
            experience_years=experience_years,
            skills=skills or [],
            languages=languages or ["English"]
        )

        self.agent_profiles[agent_id] = profile
        self.active_collaborations[agent_id] = []

        logger.info(f"Created collaboration profile for agent {agent_id}")
        return profile

    async def create_team(
        self,
        team_name: str,
        lead_agent_id: str,
        member_agent_ids: List[str],
        territory: Optional[str] = None,
        specializations: Optional[List[str]] = None
    ) -> Team:
        """Create a new real estate team"""

        team_id = f"team_{int(datetime.now().timestamp())}"

        team = Team(
            id=team_id,
            name=team_name,
            lead_agent_id=lead_agent_id,
            member_agent_ids=set(member_agent_ids),
            territory=territory,
            specializations=specializations or []
        )

        # Update agent profiles with team assignment
        for agent_id in [lead_agent_id] + member_agent_ids:
            if agent_id in self.agent_profiles:
                self.agent_profiles[agent_id].team_id = team_id

        self.teams[team_id] = team
        self.team_insights[team_id] = []

        logger.info(f"Created team {team_name} with {len(member_agent_ids) + 1} members")
        return team

    async def request_collaboration(
        self,
        requesting_agent_id: str,
        target_agent_id: str,
        collaboration_type: CollaborationType,
        title: str,
        description: str,
        lead_id: Optional[str] = None,
        property_id: Optional[str] = None,
        expected_value: Optional[float] = None,
        commission_split: Optional[Dict[str, float]] = None,
        deadline: Optional[datetime] = None
    ) -> CollaborationRequest:
        """Create a collaboration request between agents"""

        request_id = f"collab_{requesting_agent_id}_{int(datetime.now().timestamp())}"

        # Validate agents exist
        if requesting_agent_id not in self.agent_profiles:
            raise ValueError(f"Requesting agent {requesting_agent_id} not found")
        if target_agent_id not in self.agent_profiles:
            raise ValueError(f"Target agent {target_agent_id} not found")

        request = CollaborationRequest(
            id=request_id,
            requesting_agent_id=requesting_agent_id,
            target_agent_id=target_agent_id,
            collaboration_type=collaboration_type,
            status=CollaborationStatus.PENDING,
            title=title,
            description=description,
            lead_id=lead_id,
            property_id=property_id,
            expected_value=expected_value,
            commission_split=commission_split,
            deadline=deadline
        )

        self.collaboration_requests[request_id] = request

        # Notify target agent (would integrate with notification system)
        await self._notify_collaboration_request(request)

        logger.info(f"Created collaboration request {request_id} from {requesting_agent_id} to {target_agent_id}")
        return request

    async def respond_to_collaboration(
        self,
        request_id: str,
        response: CollaborationStatus,
        responding_agent_id: str,
        notes: Optional[str] = None
    ) -> bool:
        """Respond to a collaboration request"""

        if request_id not in self.collaboration_requests:
            return False

        request = self.collaboration_requests[request_id]

        if request.target_agent_id != responding_agent_id:
            return False

        if request.status != CollaborationStatus.PENDING:
            return False

        request.status = response
        request.updated_at = datetime.now()

        if response == CollaborationStatus.ACCEPTED:
            request.accepted_at = datetime.now()

            # Add to active collaborations
            if responding_agent_id not in self.active_collaborations:
                self.active_collaborations[responding_agent_id] = []
            self.active_collaborations[responding_agent_id].append(request_id)

            if request.requesting_agent_id not in self.active_collaborations:
                self.active_collaborations[request.requesting_agent_id] = []
            self.active_collaborations[request.requesting_agent_id].append(request_id)

            # Create shared tasks if applicable
            await self._create_collaboration_tasks(request)

        # Notify requesting agent
        await self._notify_collaboration_response(request, notes)

        logger.info(f"Collaboration request {request_id} {response.value} by {responding_agent_id}")
        return True

    async def find_collaboration_partners(
        self,
        requesting_agent_id: str,
        collaboration_type: CollaborationType,
        criteria: Optional[Dict[str, Any]] = None
    ) -> List[AgentProfile]:
        """Find potential collaboration partners using AI matching"""

        requesting_profile = self.agent_profiles.get(requesting_agent_id)
        if not requesting_profile:
            return []

        # Get all potential partners
        potential_partners = [
            profile for profile in self.agent_profiles.values()
            if profile.agent_id != requesting_agent_id and profile.availability_status == "available"
        ]

        # Apply basic filtering
        if criteria:
            potential_partners = self._apply_partner_criteria(potential_partners, criteria)

        # Use AI for intelligent matching
        if claude_agent_service and potential_partners:
            enhanced_matches = await self._ai_enhanced_partner_matching(
                requesting_profile, potential_partners, collaboration_type, criteria
            )
            return enhanced_matches

        # Fallback to basic scoring
        return self._basic_partner_scoring(requesting_profile, potential_partners, collaboration_type)

    async def get_team_performance(self, team_id: str, days: int = 30) -> Optional[TeamInsight]:
        """Get comprehensive team performance analytics"""

        if team_id not in self.teams:
            return None

        team = self.teams[team_id]
        period_start = datetime.now() - timedelta(days=days)
        period_end = datetime.now()

        # Calculate team metrics
        team_collaborations = [
            req for req in self.collaboration_requests.values()
            if (req.requesting_agent_id in team.member_agent_ids or
                req.target_agent_id in team.member_agent_ids) and
               req.created_at >= period_start
        ]

        # Get AI insights for team optimization
        team_insight = TeamInsight(
            team_id=team_id,
            period_start=period_start,
            period_end=period_end,
            collaboration_count=len(team_collaborations),
            member_performance=await self._calculate_member_performance(team, period_start)
        )

        # Add AI-powered recommendations
        if claude_agent_service:
            team_insight.recommendations = await self._get_ai_team_recommendations(team, team_insight)

        return team_insight

    async def get_collaboration_insights(self, agent_id: str) -> Dict[str, Any]:
        """Get AI-powered collaboration insights for an agent"""

        if agent_id not in self.agent_profiles:
            return {"error": "Agent not found"}

        profile = self.agent_profiles[agent_id]
        active_collabs = self.active_collaborations.get(agent_id, [])

        # Get collaboration history
        collaboration_history = [
            req for req in self.collaboration_requests.values()
            if req.requesting_agent_id == agent_id or req.target_agent_id == agent_id
        ]

        # Generate AI insights
        insights = {
            "collaboration_score": self._calculate_collaboration_score(agent_id),
            "active_collaborations": len(active_collabs),
            "total_collaborations": len(collaboration_history),
            "success_rate": self._calculate_success_rate(collaboration_history),
            "preferred_partners": self._get_preferred_partners(collaboration_history),
            "collaboration_types": self._analyze_collaboration_types(collaboration_history)
        }

        # Add AI recommendations
        if claude_agent_service:
            ai_recommendations = await self._get_ai_collaboration_recommendations(agent_id, insights)
            insights["ai_recommendations"] = ai_recommendations

        return insights

    async def suggest_lead_referral(
        self,
        agent_id: str,
        lead_id: str,
        lead_criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """AI-powered lead referral suggestions"""

        # Find best agents for this lead type
        potential_agents = await self.find_collaboration_partners(
            agent_id,
            CollaborationType.LEAD_REFERRAL,
            {
                "specializations": lead_criteria.get("property_type", []),
                "territory": lead_criteria.get("location"),
                "price_range": lead_criteria.get("budget")
            }
        )

        suggestions = []
        for agent_profile in potential_agents[:5]:  # Top 5 suggestions
            # Calculate referral potential using AI
            if claude_agent_service:
                potential_score = await self._calculate_referral_potential(
                    agent_profile, lead_criteria
                )
            else:
                potential_score = self._basic_referral_scoring(agent_profile, lead_criteria)

            suggestions.append({
                "agent_id": agent_profile.agent_id,
                "agent_name": agent_profile.name,
                "specializations": agent_profile.specializations,
                "experience": agent_profile.experience_years,
                "collaboration_rating": agent_profile.collaboration_rating,
                "potential_score": potential_score,
                "reasoning": f"Strong match for {lead_criteria.get('property_type', 'this lead type')}"
            })

        return sorted(suggestions, key=lambda x: x["potential_score"], reverse=True)

    async def create_team_workspace(self, team_id: str) -> Dict[str, Any]:
        """Create a collaborative workspace for a team"""

        if team_id not in self.teams:
            return {"error": "Team not found"}

        team = self.teams[team_id]

        workspace = {
            "team_id": team_id,
            "team_name": team.name,
            "shared_leads": await self._get_shared_team_leads(team_id),
            "active_deals": await self._get_active_team_deals(team_id),
            "team_calendar": await self._get_team_calendar(team_id),
            "knowledge_base": await self._get_team_knowledge_base(team_id),
            "communication_channels": self._setup_team_communication(team_id),
            "performance_dashboard": await self.get_team_performance(team_id),
            "ai_insights": await self._get_team_ai_insights(team_id)
        }

        return workspace

    # Helper methods

    def _apply_partner_criteria(
        self,
        partners: List[AgentProfile],
        criteria: Dict[str, Any]
    ) -> List[AgentProfile]:
        """Apply filtering criteria to potential partners"""

        filtered_partners = partners

        if "specializations" in criteria and criteria["specializations"]:
            target_specializations = criteria["specializations"]
            if isinstance(target_specializations, str):
                target_specializations = [target_specializations]

            filtered_partners = [
                p for p in filtered_partners
                if any(spec in p.specializations for spec in target_specializations)
            ]

        if "territory" in criteria and criteria["territory"]:
            filtered_partners = [
                p for p in filtered_partners
                if p.territory == criteria["territory"]
            ]

        if "min_experience" in criteria:
            filtered_partners = [
                p for p in filtered_partners
                if p.experience_years >= criteria["min_experience"]
            ]

        if "min_rating" in criteria:
            filtered_partners = [
                p for p in filtered_partners
                if p.collaboration_rating >= criteria["min_rating"]
            ]

        return filtered_partners

    async def _ai_enhanced_partner_matching(
        self,
        requesting_profile: AgentProfile,
        potential_partners: List[AgentProfile],
        collaboration_type: CollaborationType,
        criteria: Optional[Dict[str, Any]]
    ) -> List[AgentProfile]:
        """Use AI to enhance partner matching"""

        try:
            # Build context for AI
            context = {
                "requesting_agent": {
                    "specializations": requesting_profile.specializations,
                    "territory": requesting_profile.territory,
                    "experience": requesting_profile.experience_years,
                    "collaboration_type": collaboration_type.value
                },
                "potential_partners": [
                    {
                        "agent_id": p.agent_id,
                        "name": p.name,
                        "specializations": p.specializations,
                        "territory": p.territory,
                        "experience": p.experience_years,
                        "rating": p.collaboration_rating
                    }
                    for p in potential_partners
                ],
                "criteria": criteria or {}
            }

            query = f"Help me find the best collaboration partners for {collaboration_type.value}. Rank the potential partners by compatibility and effectiveness."

            response = await claude_agent_service.chat_with_agent(
                requesting_profile.agent_id, query, context=context
            )

            # Parse AI recommendations and reorder partners
            # In a real implementation, this would parse the AI response
            # For now, return the partners with basic scoring
            return self._basic_partner_scoring(requesting_profile, potential_partners, collaboration_type)

        except Exception as e:
            logger.warning(f"AI partner matching failed: {str(e)}")
            return self._basic_partner_scoring(requesting_profile, potential_partners, collaboration_type)

    def _basic_partner_scoring(
        self,
        requesting_profile: AgentProfile,
        potential_partners: List[AgentProfile],
        collaboration_type: CollaborationType
    ) -> List[AgentProfile]:
        """Basic scoring algorithm for partner matching"""

        scored_partners = []

        for partner in potential_partners:
            score = 0

            # Specialization match
            common_specs = set(requesting_profile.specializations) & set(partner.specializations)
            score += len(common_specs) * 10

            # Territory compatibility
            if partner.territory == requesting_profile.territory:
                score += 15

            # Experience factor
            if collaboration_type == CollaborationType.MENTORSHIP:
                if partner.experience_years > requesting_profile.experience_years:
                    score += (partner.experience_years - requesting_profile.experience_years) * 2
            else:
                # For other collaborations, closer experience is better
                exp_diff = abs(partner.experience_years - requesting_profile.experience_years)
                score += max(0, 10 - exp_diff)

            # Collaboration rating
            score += partner.collaboration_rating * 5

            # Role compatibility
            if partner.role in [TeamRole.SENIOR_AGENT, TeamRole.TEAM_LEAD]:
                score += 5

            scored_partners.append((partner, score))

        # Sort by score and return partners
        scored_partners.sort(key=lambda x: x[1], reverse=True)
        return [partner for partner, score in scored_partners]

    def _calculate_collaboration_score(self, agent_id: str) -> float:
        """Calculate overall collaboration effectiveness score"""

        history = [
            req for req in self.collaboration_requests.values()
            if req.requesting_agent_id == agent_id or req.target_agent_id == agent_id
        ]

        if not history:
            return 0.0

        # Calculate success rate
        completed = len([req for req in history if req.status == CollaborationStatus.COMPLETED])
        success_rate = completed / len(history)

        # Calculate response rate (for incoming requests)
        incoming = [req for req in history if req.target_agent_id == agent_id]
        if incoming:
            responded = len([req for req in incoming if req.status != CollaborationStatus.PENDING])
            response_rate = responded / len(incoming)
        else:
            response_rate = 1.0

        # Combine scores
        return (success_rate * 0.7 + response_rate * 0.3) * 100

    def _calculate_success_rate(self, collaboration_history: List[CollaborationRequest]) -> float:
        """Calculate collaboration success rate"""
        if not collaboration_history:
            return 0.0

        completed = len([req for req in collaboration_history if req.status == CollaborationStatus.COMPLETED])
        return (completed / len(collaboration_history)) * 100

    def _get_preferred_partners(self, collaboration_history: List[CollaborationRequest]) -> List[str]:
        """Get list of most frequently collaborated agents"""

        partner_counts = {}
        for req in collaboration_history:
            if req.status == CollaborationStatus.COMPLETED:
                # Count both directions
                other_agent = (req.target_agent_id if req.requesting_agent_id != req.requesting_agent_id
                              else req.requesting_agent_id)
                partner_counts[other_agent] = partner_counts.get(other_agent, 0) + 1

        # Sort by count and return top partners
        sorted_partners = sorted(partner_counts.items(), key=lambda x: x[1], reverse=True)
        return [agent_id for agent_id, count in sorted_partners[:5]]

    def _analyze_collaboration_types(self, collaboration_history: List[CollaborationRequest]) -> Dict[str, int]:
        """Analyze distribution of collaboration types"""

        type_counts = {}
        for req in collaboration_history:
            type_name = req.collaboration_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        return type_counts

    async def _notify_collaboration_request(self, request: CollaborationRequest):
        """Send notification about new collaboration request"""
        # In a real implementation, this would integrate with notification system
        logger.info(f"Notification: New collaboration request {request.id} for {request.target_agent_id}")

    async def _notify_collaboration_response(
        self,
        request: CollaborationRequest,
        notes: Optional[str] = None
    ):
        """Send notification about collaboration response"""
        logger.info(f"Notification: Collaboration response {request.status.value} for request {request.id}")

    async def _create_collaboration_tasks(self, request: CollaborationRequest):
        """Create shared tasks for accepted collaboration"""

        if not agent_workflow_automation:
            return

        # Create tasks for both agents
        task_templates = self._get_collaboration_task_templates(request.collaboration_type)

        for template in task_templates:
            # Task for requesting agent
            await agent_workflow_automation.create_task(
                agent_id=request.requesting_agent_id,
                title=template["title"].format(partner_name="Partner"),
                description=template["description"],
                priority=TaskPriority(template["priority"]),
                workflow_id=request.id,
                auto_generated=True,
                metadata={"collaboration_id": request.id, "partner_id": request.target_agent_id}
            )

            # Task for target agent
            await agent_workflow_automation.create_task(
                agent_id=request.target_agent_id,
                title=template["title"].format(partner_name="Partner"),
                description=template["description"],
                priority=TaskPriority(template["priority"]),
                workflow_id=request.id,
                auto_generated=True,
                metadata={"collaboration_id": request.id, "partner_id": request.requesting_agent_id}
            )

    def _get_collaboration_task_templates(self, collaboration_type: CollaborationType) -> List[Dict[str, str]]:
        """Get task templates for different collaboration types"""

        templates = {
            CollaborationType.LEAD_REFERRAL: [
                {
                    "title": "Handover lead details to {partner_name}",
                    "description": "Provide comprehensive lead information and warm introduction",
                    "priority": "high"
                },
                {
                    "title": "Follow up on referral outcome",
                    "description": "Check on lead progress and gather feedback",
                    "priority": "medium"
                }
            ],
            CollaborationType.DEAL_PARTNERSHIP: [
                {
                    "title": "Establish partnership roles with {partner_name}",
                    "description": "Define responsibilities and commission split",
                    "priority": "urgent"
                },
                {
                    "title": "Schedule joint client meeting",
                    "description": "Coordinate schedules for collaborative client presentation",
                    "priority": "high"
                }
            ],
            CollaborationType.MENTORSHIP: [
                {
                    "title": "Schedule mentoring session",
                    "description": "Set up regular mentoring meetings and goals",
                    "priority": "medium"
                }
            ]
        }

        return templates.get(collaboration_type, [])

    async def _calculate_member_performance(
        self,
        team: Team,
        period_start: datetime
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate performance metrics for team members"""

        member_performance = {}

        for agent_id in team.member_agent_ids:
            if agent_workflow_automation:
                tasks = await agent_workflow_automation.get_agent_tasks(agent_id, limit=100)
                recent_tasks = [t for t in tasks if getattr(t, 'created_at', datetime.min) >= period_start]

                member_performance[agent_id] = {
                    "tasks_completed": len([t for t in recent_tasks if getattr(t, 'status', '') == 'completed']),
                    "collaboration_requests": len([
                        req for req in self.collaboration_requests.values()
                        if req.requesting_agent_id == agent_id and req.created_at >= period_start
                    ]),
                    "collaboration_score": self._calculate_collaboration_score(agent_id)
                }
            else:
                # Demo data
                member_performance[agent_id] = {
                    "tasks_completed": 15,
                    "collaboration_requests": 3,
                    "collaboration_score": 85.5
                }

        return member_performance

    async def _get_ai_team_recommendations(
        self,
        team: Team,
        team_insight: TeamInsight
    ) -> List[str]:
        """Get AI-powered team optimization recommendations"""

        try:
            if not claude_agent_service:
                return ["Increase collaboration frequency", "Focus on lead sharing", "Improve communication"]

            context = {
                "team_size": len(team.member_agent_ids),
                "collaboration_count": team_insight.collaboration_count,
                "member_performance": team_insight.member_performance
            }

            query = "Analyze our team performance and provide specific recommendations for improving collaboration and productivity."

            response = await claude_agent_service.chat_with_agent(
                team.lead_agent_id, query, context=context
            )

            return response.recommendations[:5]

        except Exception as e:
            logger.warning(f"Failed to get AI team recommendations: {str(e)}")
            return ["Increase collaboration frequency", "Focus on lead sharing", "Improve communication"]

    async def _get_ai_collaboration_recommendations(
        self,
        agent_id: str,
        insights: Dict[str, Any]
    ) -> List[str]:
        """Get AI recommendations for improving collaboration"""

        try:
            if not claude_agent_service:
                return ["Increase collaboration frequency", "Focus on knowledge sharing"]

            query = f"Based on my collaboration metrics, how can I improve my teamwork and partnership effectiveness?"

            response = await claude_agent_service.chat_with_agent(
                agent_id, query, context=insights
            )

            return response.recommendations[:3]

        except Exception as e:
            logger.warning(f"Failed to get AI collaboration recommendations: {str(e)}")
            return ["Increase collaboration frequency", "Focus on knowledge sharing"]

    async def _calculate_referral_potential(
        self,
        agent_profile: AgentProfile,
        lead_criteria: Dict[str, Any]
    ) -> float:
        """Calculate AI-enhanced referral potential score"""

        # This would use AI to calculate match potential
        # For now, use basic scoring
        return self._basic_referral_scoring(agent_profile, lead_criteria)

    def _basic_referral_scoring(
        self,
        agent_profile: AgentProfile,
        lead_criteria: Dict[str, Any]
    ) -> float:
        """Basic referral potential scoring"""

        score = 0.0

        # Specialization match
        lead_property_type = lead_criteria.get("property_type", "")
        if lead_property_type in agent_profile.specializations:
            score += 30

        # Territory match
        if agent_profile.territory == lead_criteria.get("location"):
            score += 25

        # Experience factor
        score += min(agent_profile.experience_years * 2, 20)

        # Collaboration rating
        score += agent_profile.collaboration_rating / 100 * 25

        return min(score, 100.0)

    # Demo/placeholder methods for workspace features
    async def _get_shared_team_leads(self, team_id: str) -> List[Dict[str, Any]]:
        """Get leads shared within the team"""
        return []  # Placeholder

    async def _get_active_team_deals(self, team_id: str) -> List[Dict[str, Any]]:
        """Get active deals involving team members"""
        return []  # Placeholder

    async def _get_team_calendar(self, team_id: str) -> Dict[str, Any]:
        """Get team calendar and shared events"""
        return {"events": []}  # Placeholder

    async def _get_team_knowledge_base(self, team_id: str) -> Dict[str, Any]:
        """Get team knowledge base and shared resources"""
        return {"articles": [], "templates": []}  # Placeholder

    def _setup_team_communication(self, team_id: str) -> Dict[str, Any]:
        """Setup team communication channels"""
        return {"channels": []}  # Placeholder

    async def _get_team_ai_insights(self, team_id: str) -> List[str]:
        """Get AI insights for team optimization"""
        return ["Focus on lead sharing", "Improve response times", "Coordinate schedules better"]


# Global instance
agent_collaboration_service = AgentCollaborationService()


# Convenience functions
async def create_collaboration_request(
    requesting_agent_id: str,
    target_agent_id: str,
    collaboration_type: str,
    title: str,
    description: str,
    **kwargs
) -> CollaborationRequest:
    """Create a collaboration request"""
    return await agent_collaboration_service.request_collaboration(
        requesting_agent_id,
        target_agent_id,
        CollaborationType(collaboration_type),
        title,
        description,
        **kwargs
    )


async def find_collaboration_partners(
    agent_id: str,
    collaboration_type: str,
    criteria: Optional[Dict[str, Any]] = None
) -> List[AgentProfile]:
    """Find collaboration partners"""
    return await agent_collaboration_service.find_collaboration_partners(
        agent_id, CollaborationType(collaboration_type), criteria
    )


async def get_collaboration_insights(agent_id: str) -> Dict[str, Any]:
    """Get collaboration insights for an agent"""
    return await agent_collaboration_service.get_collaboration_insights(agent_id)