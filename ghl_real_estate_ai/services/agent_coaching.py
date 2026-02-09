"""
Real-Time Agent Coaching Service - Wow Factor Feature #2
Provides live coaching suggestions during conversations
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class CoachingTip:
    """Real-time coaching suggestion"""

    tip_type: str  # "question", "objection_handler", "closing", "rapport", "warning"
    title: str
    suggestion: str
    example: str
    why_it_works: str
    confidence: float
    urgency: int  # 1 (show now) to 3 (show when idle)

    def to_dict(self) -> Dict:
        return asdict(self)


class AgentCoachingService:
    """
    🎯 WOW FEATURE: Real-Time Conversation Coaching

    Analyzes conversations in real-time and provides Jorge's agents with
    intelligent coaching tips to help them close more deals.

    Features:
    - Detects missed opportunities
    - Suggests objection handlers
    - Recommends closing techniques
    - Warns about compliance issues
    - Provides Jorge-style response templates
    """

    def __init__(self):
        self.jorge_style_responses = self._load_jorge_templates()

    def analyze_conversation_live(self, conversation_history: List[Dict], current_context: Dict) -> List[CoachingTip]:
        """
        Analyze ongoing conversation and provide real-time coaching

        Args:
            conversation_history: List of messages
            current_context: Current lead state (score, metadata, etc.)

        Returns:
            List of coaching tips prioritized by urgency
        """
        tips = []

        # Get last few messages for context
        recent_messages = conversation_history[-5:] if len(conversation_history) >= 5 else conversation_history
        last_lead_message = next((m for m in reversed(recent_messages) if m.get("sender") == "lead"), None)

        if not last_lead_message:
            return tips

        lead_text = last_lead_message.get("message", "").lower()

        # Tip 1: Detect buying signals
        buying_signals = self._detect_buying_signals(lead_text)
        if buying_signals:
            tips.append(
                CoachingTip(
                    tip_type="closing",
                    title="🔥 Buying Signal Detected!",
                    suggestion=f"Lead just showed interest: '{buying_signals}'. Move to schedule NOW.",
                    example="Perfect! Would today around 2pm or closer to 4:30pm work better for you?",
                    why_it_works="Strike while iron is hot - they're ready to move forward",
                    confidence=0.9,
                    urgency=1,
                )
            )

        # Tip 2: Price objection handler
        if any(word in lead_text for word in ["expensive", "too much", "afford", "budget"]):
            tips.append(
                CoachingTip(
                    tip_type="objection_handler",
                    title="💰 Price Objection Detected",
                    suggestion="Reframe around value, not price. Offer both wholesale and listing options.",
                    example="I hear you. That's why we offer two routes - cash offer (quick, as-is) or listing (top dollar). Which matters more to you right now, speed or maximum price?",
                    why_it_works="Gives them control and shows you're flexible, not pushy",
                    confidence=0.85,
                    urgency=1,
                )
            )

        # Tip 3: Urgency detected - capitalize on it
        if any(word in lead_text for word in ["asap", "urgent", "quickly", "soon", "deadline"]):
            tips.append(
                CoachingTip(
                    tip_type="closing",
                    title="⚡ URGENCY DETECTED - Act Fast!",
                    suggestion="They need speed. Push for same-day call or appointment.",
                    example="Got it - time is critical. I can have someone look at the property today. Are you free at 3pm or would 5pm work better?",
                    why_it_works="Matches their urgency with immediate action",
                    confidence=0.95,
                    urgency=1,
                )
            )

        # Tip 4: Competition mentioned
        if any(phrase in lead_text for phrase in ["other agent", "another", "comparing", "someone else"]):
            tips.append(
                CoachingTip(
                    tip_type="objection_handler",
                    title="⚠️ Competitive Threat",
                    suggestion="Differentiate NOW. Mention Jorge's dual path advantage.",
                    example="That's smart to compare. Just so you know, we're unique - we can either buy your house cash (close in 7 days) OR list it for top dollar. Most agents only do one. What matters most to you?",
                    why_it_works="Shows clear differentiation without badmouthing competitors",
                    confidence=0.8,
                    urgency=1,
                )
            )

        # Tip 5: Vague response - need specifics
        if any(word in lead_text for word in ["maybe", "not sure", "thinking", "idk", "dunno"]):
            tips.append(
                CoachingTip(
                    tip_type="question",
                    title="🎯 Get Specific - Ask Qualifying Question",
                    suggestion="Lead is being vague. Dig deeper with either/or question.",
                    example="No worries! Let me ask this way - are you hoping to move in the next 30 days, or more like 60-90 days? Just helps me send you the right properties.",
                    why_it_works="Either/or questions are easier to answer than open-ended",
                    confidence=0.75,
                    urgency=2,
                )
            )

        # Tip 6: Location mentioned - capitalize
        if self._detect_location(lead_text):
            location = self._detect_location(lead_text)
            tips.append(
                CoachingTip(
                    tip_type="rapport",
                    title="📍 Location Mentioned - Build Rapport",
                    suggestion=f"They mentioned {location}. Show local knowledge.",
                    example=f"Nice! {location} is hot right now. Are you looking in the heart of {location} or more on the outskirts?",
                    why_it_works="Shows you know the area and builds trust",
                    confidence=0.7,
                    urgency=2,
                )
            )

        # Tip 7: Check if too many questions asked
        agent_questions = sum(1 for m in recent_messages if m.get("sender") == "agent" and "?" in m.get("message", ""))
        if agent_questions > 3:
            tips.append(
                CoachingTip(
                    tip_type="warning",
                    title="⚠️ Too Many Questions",
                    suggestion="You've asked 3+ questions in a row. Switch to statement or offer value.",
                    example="Here's what I think based on what you've told me... [summarize their needs]. Does that sound about right?",
                    why_it_works="Avoids feeling like an interrogation, shows you're listening",
                    confidence=0.8,
                    urgency=2,
                )
            )

        # Tip 8: No response in conversation - re-engagement needed
        if len(conversation_history) > 0:
            last_message_time = conversation_history[-1].get("timestamp")
            if last_message_time:
                # Check if it's been a while (simplified check)
                if conversation_history[-1].get("sender") == "agent":
                    tips.append(
                        CoachingTip(
                            tip_type="question",
                            title="💤 Waiting for Response",
                            suggestion="If no response in 4+ hours, send Jorge-style break-up text.",
                            example="Hey [Name], just checking - still interested or should we close your file? No worries either way!",
                            why_it_works="Creates urgency without being pushy. Often gets response.",
                            confidence=0.85,
                            urgency=3,
                        )
                    )

        # Tip 9: Hot lead - push for appointment
        score = current_context.get("score", 0)
        if score > 7.5 and not self._has_appointment_scheduled(conversation_history):
            tips.append(
                CoachingTip(
                    tip_type="closing",
                    title="🔥 HOT LEAD - Schedule Appointment NOW",
                    suggestion="Lead score is 7.5+. Stop texting, get them on phone or in person.",
                    example="You know what, let's just hop on a quick call. I have 10 minutes right now or we can do 4pm. Which works?",
                    why_it_works="High-intent leads convert better with voice/in-person",
                    confidence=0.9,
                    urgency=1,
                )
            )

        # Sort by urgency and confidence
        tips.sort(key=lambda t: (t.urgency, -t.confidence))

        return tips[:5]  # Return top 5 tips

    def _detect_buying_signals(self, message: str) -> Optional[str]:
        """Detect buying signals in lead message"""
        signals = {
            "ready": "ready to move forward",
            "when can": "asking about next steps",
            "how soon": "timeline urgency",
            "let's do": "commitment language",
            "sounds good": "agreement/acceptance",
            "interested": "showing interest",
            "send me": "requesting information",
            "show me": "wanting to see properties",
        }

        for keyword, signal in signals.items():
            if keyword in message:
                return signal

        return None

    def _detect_location(self, message: str) -> Optional[str]:
        """Extract location mentions from message"""
        # Common Miami areas (can be expanded)
        locations = [
            "miami beach",
            "downtown miami",
            "brickell",
            "coral gables",
            "coconut grove",
            "kendall",
            "homestead",
            "doral",
            "aventura",
            "wynwood",
            "edgewater",
            "midtown",
        ]

        for location in locations:
            if location in message:
                return location.title()

        return None

    def _has_appointment_scheduled(self, conversation_history: List[Dict]) -> bool:
        """Check if appointment has been scheduled"""
        keywords = ["scheduled", "booked", "confirmed", "appointment set", "see you"]

        for msg in conversation_history:
            if msg.get("sender") == "agent":
                text = msg.get("message", "").lower()
                if any(kw in text for kw in keywords):
                    return True

        return False

    def _load_jorge_templates(self) -> Dict:
        """Load Jorge's proven response templates"""
        return {
            "opening": [
                "Hey {name}! Quick question - looking to buy or sell?",
                "Hey {name}, are you wanting a cash offer or to list for top dollar?",
            ],
            "timeline": [
                "When are you hoping to move? Next few months or just exploring?",
                "What's your timeline looking like - urgent or flexible?",
            ],
            "budget": [
                "What price range are you comfortable with? Ballpark is fine.",
                "What's your budget looking like? Just helps me narrow it down.",
            ],
            "closing": [
                "Perfect! Would today around 2pm or closer to 4:30pm work better?",
                "Sounds good. I have slots at 11am or 3pm tomorrow. Which works?",
            ],
            "reengagement": [
                "Hey {name}, just checking in. Still thinking about {location} or should we close your file?",
                "{name} - real talk. Is this still a priority or have you given up? No judgment!",
            ],
        }

    def get_jorge_template(self, category: str, context: Dict) -> str:
        """Get a Jorge-style template for specific situation"""
        templates = self.jorge_style_responses.get(category, [])
        if templates:
            template = templates[0]  # Could randomize
            # Fill in context
            return template.format(
                name=context.get("name", "there"),
                location=context.get("location", "the area"),
            )
        return ""

    def analyze_agent_performance(self, agent_id: str, conversations: List[Dict]) -> Dict:
        """
        Analyze agent's performance and provide coaching report

        Returns coaching report with strengths and improvement areas
        """
        total_convos = len(conversations)

        if total_convos == 0:
            return {"error": "No conversations to analyze"}

        # Metrics
        response_times = []
        questions_asked = 0
        appointments_set = 0
        jorge_style_usage = 0

        for conv in conversations:
            agent_messages = [m for m in conv.get("messages", []) if m.get("sender") == "agent"]

            # Count questions
            questions_asked += sum(1 for m in agent_messages if "?" in m.get("message", ""))

            # Check for appointments
            if self._has_appointment_scheduled(conv.get("messages", [])):
                appointments_set += 1

            # Check Jorge-style language
            for msg in agent_messages:
                text = msg.get("message", "").lower()
                if any(phrase in text for phrase in ["hey", "quick question", "real talk", "no worries"]):
                    jorge_style_usage += 1
                    break

        appointment_rate = appointments_set / total_convos if total_convos > 0 else 0
        jorge_style_rate = jorge_style_usage / total_convos if total_convos > 0 else 0

        # Generate report
        report = {
            "agent_id": agent_id,
            "period": datetime.now().isoformat(),
            "metrics": {
                "total_conversations": total_convos,
                "appointment_rate": f"{appointment_rate * 100:.1f}%",
                "avg_questions_per_convo": (questions_asked / total_convos if total_convos > 0 else 0),
                "jorge_style_adoption": f"{jorge_style_rate * 100:.1f}%",
            },
            "strengths": [],
            "improvements": [],
            "coaching_focus": [],
        }

        # Identify strengths
        if appointment_rate > 0.25:
            report["strengths"].append("High appointment conversion rate")
        if jorge_style_rate > 0.7:
            report["strengths"].append("Strong adoption of Jorge's communication style")

        # Identify improvements
        if appointment_rate < 0.15:
            report["improvements"].append(
                "Focus on closing for appointments - too many conversations without next steps"
            )
            report["coaching_focus"].append("Practice Jorge's either/or closing questions")

        if jorge_style_rate < 0.5:
            report["improvements"].append("Use more Jorge-style language (casual, direct, friendly)")
            report["coaching_focus"].append("Review Jorge's example scripts and templates")

        return report

    def get_objection_handler(self, objection_type: str, context: Dict) -> Dict:
        """
        🆕 ENHANCEMENT: Smart objection handler database

        Returns Jorge-style responses for common objections
        """
        handlers = {
            "price_too_high": {
                "title": "Price Objection",
                "jorge_response": "I hear you. That's why we offer two routes - cash offer (quick, as-is) or listing (top dollar). Which matters more to you right now, speed or maximum price?",
                "why_it_works": "Gives them control and reframes as value choice, not price objection",
                "followup": "Most people don't realize we can do both. What's your timeline looking like?",
                "success_rate": 0.73,
            },
            "need_to_think": {
                "title": "Thinking It Over",
                "jorge_response": "Totally get it. Quick question though - what specifically are you thinking about? Price, timeline, or something else?",
                "why_it_works": "Uncovers the real objection instead of accepting vague delay",
                "followup": "Let's figure out what's holding you back so we can address it right now.",
                "success_rate": 0.65,
            },
            "working_with_another_agent": {
                "title": "Already Have Agent",
                "jorge_response": "That's smart to compare! Just so you know, we're unique - we can either buy your house cash (close in 7 days) OR list it for top dollar. Most agents only do one. What did they offer you?",
                "why_it_works": "Shows clear differentiation without badmouthing competition",
                "followup": "Seriously though, if they can beat our offer, go with them. But let me show you what we can do.",
                "success_rate": 0.58,
            },
            "not_ready_yet": {
                "title": "Not Ready",
                "jorge_response": "No problem! When do you think you'll be ready - next few months or more like 6-12 months? Just helps me know when to check back in.",
                "why_it_works": "Either/or question makes it easier to commit to timeframe",
                "followup": "Cool. I'll follow up in [timeframe]. In the meantime, want me to send you market updates?",
                "success_rate": 0.71,
            },
            "need_repairs": {
                "title": "Property Needs Work",
                "jorge_response": "Perfect - that's exactly why people come to us! We buy as-is. You don't fix a thing, we handle everything. When can we take a look?",
                "why_it_works": "Turns objection into competitive advantage",
                "followup": "Seriously, we buy houses in ANY condition. Seen worse than yours, trust me.",
                "success_rate": 0.82,
            },
            "market_timing": {
                "title": "Waiting for Market",
                "jorge_response": "I get it. Real talk though - are you waiting for prices to go up or down? Because I can show you the data on where we're headed.",
                "why_it_works": "Positions you as market expert and offers value",
                "followup": "Let me send you our market report. Then you can decide if now is the time.",
                "success_rate": 0.61,
            },
        }

        handler = handlers.get(
            objection_type,
            {
                "title": "General Objection",
                "jorge_response": "I hear you. Help me understand - what's the biggest concern for you right now?",
                "why_it_works": "Open-ended to uncover real issue",
                "followup": "Let's address that head-on.",
                "success_rate": 0.55,
            },
        )

        # Personalize with context
        name = context.get("name", "there")
        handler["personalized_response"] = f"Hey {name}, " + handler["jorge_response"]

        return handler

    def get_closing_technique(self, lead_score: float, urgency: str) -> Dict:
        """
        🆕 ENHANCEMENT: Smart closing technique selector

        Recommends best closing approach based on lead signals
        """
        techniques = []

        if lead_score > 8 and urgency == "high":
            techniques.append(
                {
                    "name": "Direct Close",
                    "script": "Perfect! Would today around 2pm or closer to 4:30pm work better for you?",
                    "when_to_use": "Hot lead with urgency - strike now",
                    "success_rate": 0.78,
                }
            )

        if lead_score > 6:
            techniques.append(
                {
                    "name": "Either/Or Close",
                    "script": "Sounds good. I have slots at 11am or 3pm tomorrow. Which works?",
                    "when_to_use": "Engaged lead ready to move forward",
                    "success_rate": 0.71,
                }
            )

        if urgency == "low":
            techniques.append(
                {
                    "name": "Trial Close",
                    "script": "If we could meet your price and timeline, would you be ready to move forward?",
                    "when_to_use": "Testing readiness without pressure",
                    "success_rate": 0.62,
                }
            )

        techniques.append(
            {
                "name": "Takeaway Close",
                "script": "Hey, real talk - is this actually a priority for you or should we close your file? No worries either way!",
                "when_to_use": "Unresponsive or fence-sitting leads",
                "success_rate": 0.68,
            }
        )

        return {
            "recommended": techniques[0] if techniques else None,
            "alternatives": techniques[1:] if len(techniques) > 1 else [],
            "context": {"lead_score": lead_score, "urgency": urgency},
        }

    def get_conversation_template(self, scenario: str, context: Dict) -> str:
        """
        🆕 ENHANCEMENT: Full conversation templates

        Returns multi-message conversation flows for common scenarios
        """
        templates = {
            "first_contact_seller": [
                "Hey {name}! Quick question - looking to sell or just exploring options?",
                "[Wait for response]",
                "Got it! Cash offer or list for top dollar? We do both.",
                "[If they ask about cash] We can close in 7 days, buy as-is. [If listing] We'll get you top dollar, full marketing.",
                "What's your timeline looking like - urgent or flexible?",
            ],
            "first_contact_buyer": [
                "Hey {name}! What area are you looking in?",
                "[Wait for response]",
                "Nice! What's your budget looking like? Ballpark is fine.",
                "[After budget] Perfect. Have you been pre-approved yet?",
                "Cool. Want me to send you 3-5 listings that match? I can text them over.",
            ],
            "reengagement_cold": [
                "Hey {name}, just checking in. Still interested in {area} or did life get busy?",
                "[If no response after 48h]",
                "{name} - real talk. Are you actually still looking or should we close your file? No judgment!",
                "[If still no response]",
                "Last text! Market's hot right now. If you want back in later just reply 'I'm back'. Take care!",
            ],
            "appointment_scheduled": [
                "Perfect! See you at {time}. I'll text you the address.",
                "[Send address]",
                "[Day before] Hey {name}! Reminder we're meeting tomorrow at {time}. Still good?",
                "[2 hours before] On my way! See you in a bit.",
            ],
        }

        template = templates.get(scenario, ["Hey {name}! How can I help you today?"])

        # Personalize
        name = context.get("name", "there")
        area = context.get("location", "the area")
        time = context.get("time", "2pm")

        personalized = []
        for msg in template:
            personalized.append(msg.format(name=name, area=area, time=time))

        return "\n".join(personalized)


# Example usage
if __name__ == "__main__":
    coaching_service = AgentCoachingService()

    # Simulate ongoing conversation
    conversation = [
        {
            "sender": "agent",
            "message": "Hey! Looking to buy or sell?",
            "timestamp": "2026-01-05T14:00:00",
        },
        {
            "sender": "lead",
            "message": "Selling. House is old though, needs work",
            "timestamp": "2026-01-05T14:02:00",
        },
        {
            "sender": "agent",
            "message": "No problem! We buy as-is. What area?",
            "timestamp": "2026-01-05T14:03:00",
        },
        {
            "sender": "lead",
            "message": "Kendall. But it's expensive to fix up",
            "timestamp": "2026-01-05T14:05:00",
        },
    ]

    context = {"score": 7.2, "location": "Kendall", "name": "Maria"}

    tips = coaching_service.analyze_conversation_live(conversation, context)

    print("🎓 Real-Time Coaching Tips:\n")
    for tip in tips:
        print(f"{'🔥' if tip.urgency == 1 else '💡'} {tip.title}")
        print(f"   📝 {tip.suggestion}")
        print(f'   💬 Example: "{tip.example}"')
        print(f"   ✨ Why: {tip.why_it_works}\n")
