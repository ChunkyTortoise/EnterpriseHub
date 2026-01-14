"""
Claude Lead Qualification Engine - Autonomous Real-time Qualification
Provides intelligent, real-time lead qualification using Claude AI and conversation analysis.
"""
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import streamlit as st

# Import Claude services
from services.claude_conversation_intelligence import get_conversation_intelligence, ConversationAnalysis, IntentSignals
from services.claude_semantic_property_matcher import get_semantic_property_matcher
from services.memory_service import MemoryService
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class QualificationResult:
    """Complete qualification result with Claude analysis."""
    lead_id: str
    qualification_score: float  # 0.0-1.0
    qualification_tier: str  # "hot", "warm", "cold", "nurture"
    conversation_analysis: ConversationAnalysis
    intent_signals: IntentSignals
    financial_readiness: float  # 0.0-1.0
    timeline_assessment: str  # "immediate", "short_term", "long_term", "exploring"
    decision_authority: str  # "primary", "influencer", "information_gatherer"
    property_readiness: str  # "ready", "needs_education", "researching"
    recommended_actions: List[str]
    next_conversation_strategy: str
    qualification_timestamp: datetime
    confidence_level: float  # 0.0-1.0

@dataclass
class AutomatedActions:
    """Actions that can be automated based on qualification."""
    send_property_suggestions: bool
    schedule_follow_up: bool
    assign_to_agent: bool
    trigger_nurture_sequence: bool
    priority_level: str  # "urgent", "high", "medium", "low"
    suggested_response: str
    optimal_contact_time: str

class ClaudeLeadQualificationEngine:
    """
    Autonomous lead qualification using Claude AI for conversation analysis,
    behavioral psychology, and predictive qualification.
    """

    def __init__(self):
        self.conversation_intelligence = get_conversation_intelligence()
        self.semantic_matcher = get_semantic_property_matcher()
        self.memory_service = MemoryService()

        # Qualification thresholds
        self.qualification_thresholds = {
            "hot": 0.75,     # High intent, ready to buy
            "warm": 0.50,    # Moderate intent, needs nurturing
            "cold": 0.25,    # Low intent, long-term nurturing
            "nurture": 0.0   # Very low intent, automated nurturing
        }

        # Initialize Claude client
        try:
            from ghl_real_estate_ai.core.llm_client import LLMClient
            from ghl_real_estate_ai.ghl_utils.config import settings

            self.claude_client = LLMClient(
                provider="claude",
                model=settings.claude_model
            )
            self.enabled = True
            logger.info("ClaudeLeadQualificationEngine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Claude client: {e}")
            self.claude_client = None
            self.enabled = False

    async def qualify_lead_comprehensive(self, lead_data: Dict, conversation_history: List[Dict] = None) -> QualificationResult:
        """
        Comprehensive lead qualification using Claude intelligence.

        Args:
            lead_data: Complete lead profile and context
            conversation_history: Recent conversation messages

        Returns:
            QualificationResult with detailed analysis and recommendations
        """
        if not self.enabled:
            return self._get_fallback_qualification(lead_data)

        lead_id = lead_data.get('lead_id', 'unknown')
        logger.info(f"Starting comprehensive qualification for lead: {lead_id}")

        try:
            # Step 1: Analyze conversation if available
            conversation_analysis = None
            if conversation_history:
                conversation_analysis = await self.conversation_intelligence.analyze_conversation_realtime(
                    conversation_history, lead_data
                )

            # Step 2: Extract deep intent signals
            intent_signals = await self._extract_comprehensive_intent(lead_data, conversation_history)

            # Step 3: Assess financial readiness
            financial_readiness = await self._assess_financial_readiness(lead_data, intent_signals)

            # Step 4: Determine timeline and decision authority
            timeline_assessment = await self._assess_timeline_urgency(lead_data, intent_signals)
            decision_authority = await self._assess_decision_authority(lead_data, conversation_analysis)

            # Step 5: Calculate overall qualification score
            qualification_score = await self._calculate_qualification_score(
                conversation_analysis, intent_signals, financial_readiness, timeline_assessment
            )

            # Step 6: Determine qualification tier
            qualification_tier = self._determine_qualification_tier(qualification_score)

            # Step 7: Generate recommended actions
            recommended_actions = await self._generate_recommended_actions(
                qualification_score, qualification_tier, intent_signals, conversation_analysis
            )

            # Step 8: Create next conversation strategy
            next_strategy = await self._create_conversation_strategy(
                lead_data, qualification_tier, intent_signals, conversation_analysis
            )

            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(
                conversation_analysis, intent_signals, len(conversation_history or [])
            )

            result = QualificationResult(
                lead_id=lead_id,
                qualification_score=qualification_score,
                qualification_tier=qualification_tier,
                conversation_analysis=conversation_analysis,
                intent_signals=intent_signals,
                financial_readiness=financial_readiness,
                timeline_assessment=timeline_assessment,
                decision_authority=decision_authority,
                property_readiness=self._assess_property_readiness(intent_signals),
                recommended_actions=recommended_actions,
                next_conversation_strategy=next_strategy,
                qualification_timestamp=datetime.now(),
                confidence_level=confidence_level
            )

            logger.info(f"Qualification complete: {lead_id} -> {qualification_tier} ({qualification_score:.2f})")
            return result

        except Exception as e:
            logger.error(f"Error in comprehensive qualification: {e}")
            return self._get_fallback_qualification(lead_data)

    async def generate_automated_actions(self, qualification_result: QualificationResult) -> AutomatedActions:
        """
        Generate automated actions based on qualification results.

        Args:
            qualification_result: Complete qualification analysis

        Returns:
            AutomatedActions with specific recommendations
        """
        if not self.enabled:
            return self._get_fallback_actions()

        try:
            actions_prompt = self._build_actions_prompt(qualification_result)

            response = await self.claude_client.chat(
                messages=[{"role": "user", "content": actions_prompt}],
                temperature=0.4
            )

            actions_data = self._parse_automated_actions(response.content)

            return AutomatedActions(
                send_property_suggestions=actions_data.get('send_property_suggestions', False),
                schedule_follow_up=actions_data.get('schedule_follow_up', True),
                assign_to_agent=actions_data.get('assign_to_agent', False),
                trigger_nurture_sequence=actions_data.get('trigger_nurture_sequence', False),
                priority_level=actions_data.get('priority_level', 'medium'),
                suggested_response=actions_data.get('suggested_response', 'Thank you for your interest'),
                optimal_contact_time=actions_data.get('optimal_contact_time', 'business_hours')
            )

        except Exception as e:
            logger.error(f"Error generating automated actions: {e}")
            return self._get_fallback_actions()

    async def monitor_qualification_changes(self, lead_id: str, new_activity: Dict) -> Optional[QualificationResult]:
        """
        Monitor for qualification changes based on new lead activity.

        Args:
            lead_id: Lead identifier
            new_activity: New lead activity (message, property view, etc.)

        Returns:
            Updated qualification if significant changes detected
        """
        if not self.enabled:
            return None

        try:
            # Get previous qualification from memory
            previous_context = await self.memory_service.get_context(lead_id)
            previous_qualification = previous_context.get('last_qualification')

            if not previous_qualification:
                return None

            # Assess if requalification is needed
            requalification_needed = await self._assess_requalification_need(
                previous_qualification, new_activity
            )

            if requalification_needed:
                logger.info(f"Requalification triggered for lead: {lead_id}")
                # Get updated lead data and requali
                # Note: This would need integration with the broader lead management system
                return await self.qualify_lead_comprehensive({"lead_id": lead_id})

        except Exception as e:
            logger.error(f"Error monitoring qualification changes: {e}")
            return None

    async def _extract_comprehensive_intent(self, lead_data: Dict, conversation_history: List[Dict]) -> IntentSignals:
        """Extract comprehensive intent signals using Claude."""
        if conversation_history:
            # Use conversation history for intent extraction
            conversation_text = [msg.get('content', '') for msg in conversation_history]
            return await self.conversation_intelligence.extract_intent_signals(
                conversation_text, lead_data
            )
        else:
            # Use lead profile data for intent signals
            return await self._analyze_profile_intent(lead_data)

    async def _analyze_profile_intent(self, lead_data: Dict) -> IntentSignals:
        """Analyze intent signals from lead profile data."""
        try:
            profile_prompt = self._build_profile_intent_prompt(lead_data)

            response = await self.claude_client.chat(
                messages=[{"role": "user", "content": profile_prompt}],
                temperature=0.3
            )

            return self._parse_intent_from_profile(response.content)

        except Exception as e:
            logger.error(f"Error analyzing profile intent: {e}")
            return self._get_fallback_intent_signals()

    async def _assess_financial_readiness(self, lead_data: Dict, intent_signals: IntentSignals) -> float:
        """Assess financial readiness using Claude analysis."""
        try:
            financial_prompt = self._build_financial_assessment_prompt(lead_data, intent_signals)

            response = await self.claude_client.chat(
                messages=[{"role": "user", "content": financial_prompt}],
                temperature=0.2
            )

            return self._parse_financial_readiness(response.content)

        except Exception as e:
            logger.error(f"Error assessing financial readiness: {e}")
            return 0.5

    async def _assess_timeline_urgency(self, lead_data: Dict, intent_signals: IntentSignals) -> str:
        """Assess timeline urgency."""
        urgency_score = intent_signals.timeline_urgency

        if urgency_score >= 0.8:
            return "immediate"
        elif urgency_score >= 0.6:
            return "short_term"
        elif urgency_score >= 0.3:
            return "long_term"
        else:
            return "exploring"

    async def _assess_decision_authority(self, lead_data: Dict, conversation_analysis: ConversationAnalysis) -> str:
        """Assess decision-making authority."""
        if conversation_analysis:
            authority_score = getattr(conversation_analysis, 'decision_authority', 0.5)
        else:
            authority_score = 0.5

        if authority_score >= 0.7:
            return "primary"
        elif authority_score >= 0.4:
            return "influencer"
        else:
            return "information_gatherer"

    def _assess_property_readiness(self, intent_signals: IntentSignals) -> str:
        """Assess property viewing readiness."""
        emotional_investment = intent_signals.emotional_investment

        if emotional_investment >= 0.7:
            return "ready"
        elif emotional_investment >= 0.4:
            return "needs_education"
        else:
            return "researching"

    async def _calculate_qualification_score(self, conversation_analysis: ConversationAnalysis,
                                           intent_signals: IntentSignals, financial_readiness: float,
                                           timeline_assessment: str) -> float:
        """Calculate comprehensive qualification score."""
        # Weight different factors
        weights = {
            "intent_level": 0.25,
            "financial_readiness": 0.25,
            "timeline_urgency": 0.20,
            "emotional_investment": 0.15,
            "decision_authority": 0.15
        }

        # Get scores
        intent_level = conversation_analysis.intent_level if conversation_analysis else 0.5
        timeline_score = self._timeline_to_score(timeline_assessment)

        # Calculate weighted score
        qualification_score = (
            intent_level * weights["intent_level"] +
            financial_readiness * weights["financial_readiness"] +
            intent_signals.timeline_urgency * weights["timeline_urgency"] +
            intent_signals.emotional_investment * weights["emotional_investment"] +
            intent_signals.decision_authority * weights["decision_authority"]
        )

        return min(1.0, max(0.0, qualification_score))

    def _timeline_to_score(self, timeline_assessment: str) -> float:
        """Convert timeline assessment to score."""
        timeline_scores = {
            "immediate": 1.0,
            "short_term": 0.8,
            "long_term": 0.4,
            "exploring": 0.2
        }
        return timeline_scores.get(timeline_assessment, 0.5)

    def _determine_qualification_tier(self, qualification_score: float) -> str:
        """Determine qualification tier based on score."""
        if qualification_score >= self.qualification_thresholds["hot"]:
            return "hot"
        elif qualification_score >= self.qualification_thresholds["warm"]:
            return "warm"
        elif qualification_score >= self.qualification_thresholds["cold"]:
            return "cold"
        else:
            return "nurture"

    async def _generate_recommended_actions(self, qualification_score: float, qualification_tier: str,
                                          intent_signals: IntentSignals, conversation_analysis: ConversationAnalysis) -> List[str]:
        """Generate recommended actions based on qualification."""
        actions = []

        if qualification_tier == "hot":
            actions.extend([
                "Schedule immediate property viewing",
                "Prepare pre-approval documentation",
                "Assign to senior agent",
                "Send best matching properties",
                "Follow up within 24 hours"
            ])
        elif qualification_tier == "warm":
            actions.extend([
                "Send property recommendations",
                "Schedule consultation call",
                "Provide market analysis",
                "Educational content series",
                "Follow up within 48 hours"
            ])
        elif qualification_tier == "cold":
            actions.extend([
                "Add to nurture campaign",
                "Provide market insights",
                "Educational webinar invitation",
                "Monthly market updates",
                "Follow up in 1 week"
            ])
        else:  # nurture
            actions.extend([
                "Automated nurture sequence",
                "General market updates",
                "Community event invitations",
                "Follow up in 1 month"
            ])

        return actions

    async def _create_conversation_strategy(self, lead_data: Dict, qualification_tier: str,
                                          intent_signals: IntentSignals, conversation_analysis: ConversationAnalysis) -> str:
        """Create next conversation strategy."""
        try:
            strategy_prompt = self._build_strategy_prompt(
                lead_data, qualification_tier, intent_signals, conversation_analysis
            )

            response = await self.claude_client.chat(
                messages=[{"role": "user", "content": strategy_prompt}],
                temperature=0.5
            )

            return response.content.strip()

        except Exception as e:
            logger.error(f"Error creating conversation strategy: {e}")
            return "Continue building rapport and gathering information"

    def _calculate_confidence_level(self, conversation_analysis: ConversationAnalysis,
                                   intent_signals: IntentSignals, conversation_length: int) -> float:
        """Calculate confidence in qualification results."""
        confidence_factors = []

        # Conversation analysis confidence
        if conversation_analysis:
            confidence_factors.append(conversation_analysis.confidence)

        # Data completeness
        data_completeness = min(1.0, conversation_length / 5.0)  # 5+ messages = full confidence
        confidence_factors.append(data_completeness)

        # Intent signal strength
        intent_strength = (intent_signals.financial_readiness + intent_signals.emotional_investment) / 2
        confidence_factors.append(intent_strength)

        # Return average confidence
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.5

    def _build_profile_intent_prompt(self, lead_data: Dict) -> str:
        """Build prompt for profile-based intent analysis."""
        return f"""
Analyze this lead profile for buying intent signals without conversation history.

Lead Profile:
{json.dumps(lead_data, indent=2)}

Extract intent signals in JSON format:
{{
    "financial_readiness": float (0.0-1.0),
    "timeline_urgency": float (0.0-1.0),
    "decision_authority": float (0.0-1.0),
    "emotional_investment": float (0.0-1.0),
    "hidden_concerns": [list of potential concerns],
    "lifestyle_indicators": {{
        "family_focused": float,
        "career_driven": float,
        "investment_minded": float,
        "status_conscious": float,
        "security_focused": float,
        "convenience_seeking": float
    }}
}}

Base analysis on:
- Contact information and source
- Stated preferences and requirements
- Budget and financing information
- Timeline indicators
- Property types of interest
- Location preferences
"""

    def _build_financial_assessment_prompt(self, lead_data: Dict, intent_signals: IntentSignals) -> str:
        """Build prompt for financial readiness assessment."""
        return f"""
Assess financial readiness for real estate purchase.

Lead Data:
{json.dumps(lead_data, indent=2)}

Intent Signals:
- Financial Readiness: {intent_signals.financial_readiness:.2f}
- Timeline Urgency: {intent_signals.timeline_urgency:.2f}

Return a single float (0.0-1.0) representing financial readiness based on:
- Budget information and pre-approval status
- Income indicators and employment stability
- Down payment readiness
- Financing knowledge and preparation
- Investment capacity and reserves
"""

    def _build_actions_prompt(self, qualification_result: QualificationResult) -> str:
        """Build prompt for automated actions generation."""
        return f"""
Generate automated actions for this qualified lead.

Qualification Results:
- Score: {qualification_result.qualification_score:.2f}
- Tier: {qualification_result.qualification_tier}
- Financial Readiness: {qualification_result.financial_readiness:.2f}
- Timeline: {qualification_result.timeline_assessment}
- Property Readiness: {qualification_result.property_readiness}

Return JSON with automated actions:
{{
    "send_property_suggestions": boolean,
    "schedule_follow_up": boolean,
    "assign_to_agent": boolean,
    "trigger_nurture_sequence": boolean,
    "priority_level": "urgent|high|medium|low",
    "suggested_response": "Specific response text",
    "optimal_contact_time": "immediate|business_hours|evening|weekend"
}}

Consider qualification tier and readiness levels for appropriate automation.
"""

    def _build_strategy_prompt(self, lead_data: Dict, qualification_tier: str,
                              intent_signals: IntentSignals, conversation_analysis: ConversationAnalysis) -> str:
        """Build prompt for conversation strategy."""
        analysis_summary = ""
        if conversation_analysis:
            analysis_summary = f"""
Conversation Analysis:
- Intent Level: {conversation_analysis.intent_level:.2f}
- Urgency Score: {conversation_analysis.urgency_score:.2f}
- Objection Type: {conversation_analysis.objection_type}
- Next Best Action: {conversation_analysis.next_best_action}
"""

        return f"""
Create next conversation strategy for this lead.

Lead Profile:
{json.dumps(lead_data, indent=2)}

Qualification Results:
- Tier: {qualification_tier}
- Timeline Urgency: {intent_signals.timeline_urgency:.2f}
- Emotional Investment: {intent_signals.emotional_investment:.2f}
{analysis_summary}

Provide a specific conversation strategy that:
1. Addresses their current stage and concerns
2. Moves them toward the next qualification level
3. Matches their communication style and preferences
4. Provides value and builds trust
5. Creates momentum toward property viewing/purchase

Keep strategy concise and actionable (2-3 sentences).
"""

    # Parsing and fallback methods
    def _parse_intent_from_profile(self, response_content: str) -> IntentSignals:
        """Parse intent signals from profile analysis."""
        # Similar to conversation intelligence parsing
        return self.conversation_intelligence._parse_intent_signals(response_content)

    def _parse_financial_readiness(self, response_content: str) -> float:
        """Parse financial readiness score."""
        try:
            import re
            float_match = re.search(r'(0\\.\\d+|1\\.0|0|1)', response_content)
            if float_match:
                return float(float_match.group())
        except Exception:
            pass
        return 0.5

    def _parse_automated_actions(self, response_content: str) -> Dict:
        """Parse automated actions from Claude response."""
        try:
            import re
            json_match = re.search(r'\\{.*\\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        return {}

    def _get_fallback_qualification(self, lead_data: Dict) -> QualificationResult:
        """Get fallback qualification when Claude is unavailable."""
        return QualificationResult(
            lead_id=lead_data.get('lead_id', 'unknown'),
            qualification_score=0.5,
            qualification_tier="warm",
            conversation_analysis=None,
            intent_signals=self.conversation_intelligence._get_fallback_intent_signals(),
            financial_readiness=0.5,
            timeline_assessment="long_term",
            decision_authority="information_gatherer",
            property_readiness="researching",
            recommended_actions=["Gather more information", "Follow up in 48 hours"],
            next_conversation_strategy="Continue building rapport and qualifying needs",
            qualification_timestamp=datetime.now(),
            confidence_level=0.5
        )

    def _get_fallback_actions(self) -> AutomatedActions:
        """Get fallback automated actions."""
        return AutomatedActions(
            send_property_suggestions=False,
            schedule_follow_up=True,
            assign_to_agent=False,
            trigger_nurture_sequence=True,
            priority_level="medium",
            suggested_response="Thank you for your interest. I'll follow up with some information.",
            optimal_contact_time="business_hours"
        )

    def _get_fallback_intent_signals(self) -> IntentSignals:
        """Get fallback intent signals."""
        return self.conversation_intelligence._get_fallback_intent_signals()

    def render_qualification_dashboard(self, lead_data: Dict, conversation_history: List[Dict] = None) -> None:
        """
        Render comprehensive qualification dashboard in Streamlit.

        Args:
            lead_data: Lead profile and context
            conversation_history: Recent conversation messages
        """
        st.markdown("### 🎯 Claude Lead Qualification")

        if not lead_data:
            st.info("Select a lead to see qualification analysis")
            return

        if st.button("🚀 Qualify Lead with Claude", key="qualify_lead"):
            with st.spinner("🧠 Analyzing lead qualification..."):
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                # Run comprehensive qualification
                qualification_result = loop.run_until_complete(
                    self.qualify_lead_comprehensive(lead_data, conversation_history)
                )

                # Display results
                st.markdown("### 📊 Qualification Results")

                # Key metrics
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    tier_emoji = {"hot": "🔥", "warm": "🔸", "cold": "❄️", "nurture": "🌱"}
                    st.metric(
                        "Qualification Tier",
                        f"{tier_emoji[qualification_result.qualification_tier]} {qualification_result.qualification_tier.title()}",
                        delta=f"{qualification_result.qualification_score:.0%}"
                    )

                with col2:
                    st.metric("Financial Readiness", f"{qualification_result.financial_readiness:.0%}")

                with col3:
                    st.metric("Timeline", qualification_result.timeline_assessment.replace('_', ' ').title())

                with col4:
                    st.metric("Confidence", f"{qualification_result.confidence_level:.0%}")

                # Detailed analysis
                st.markdown("### 🎯 Recommended Actions")
                for action in qualification_result.recommended_actions:
                    st.markdown(f"• {action}")

                st.markdown("### 💬 Next Conversation Strategy")
                st.info(qualification_result.next_conversation_strategy)

                # Generate automated actions
                if st.button("🤖 Generate Automated Actions", key="generate_actions"):
                    with st.spinner("Generating automated actions..."):
                        automated_actions = loop.run_until_complete(
                            self.generate_automated_actions(qualification_result)
                        )

                        st.markdown("### ⚡ Automated Actions")

                        action_col1, action_col2 = st.columns(2)

                        with action_col1:
                            if automated_actions.send_property_suggestions:
                                st.success("✅ Send Property Suggestions")
                            if automated_actions.schedule_follow_up:
                                st.success("✅ Schedule Follow-up")

                        with action_col2:
                            if automated_actions.assign_to_agent:
                                st.success("✅ Assign to Agent")
                            if automated_actions.trigger_nurture_sequence:
                                st.success("✅ Trigger Nurture Sequence")

                        st.markdown(f"**Priority Level:** {automated_actions.priority_level.title()}")
                        st.markdown(f"**Suggested Response:** {automated_actions.suggested_response}")
                        st.markdown(f"**Optimal Contact Time:** {automated_actions.optimal_contact_time.replace('_', ' ').title()}")

# Global instance for easy access
_claude_qualification_engine = None

def get_claude_qualification_engine() -> ClaudeLeadQualificationEngine:
    """Get global Claude qualification engine instance."""
    global _claude_qualification_engine
    if _claude_qualification_engine is None:
        _claude_qualification_engine = ClaudeLeadQualificationEngine()
    return _claude_qualification_engine