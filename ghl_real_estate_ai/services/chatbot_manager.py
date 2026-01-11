"""
Unified Chatbot Manager for Real Estate AI Platform

Handles conversations for leads, buyers, and sellers with cross-session tracking,
behavioral learning integration, and tenant-specific context management.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
from dataclasses import dataclass, field
import json

from ghl_real_estate_ai.services.learning.interfaces import (
    BehavioralEvent, EventType, LearningContext,
    IBehaviorTracker, IFeatureEngineer, IPersonalizationEngine
)

logger = logging.getLogger(__name__)


class UserType(Enum):
    """Types of users in the system"""
    LEAD = "lead"
    BUYER = "buyer"
    SELLER = "seller"
    AGENT = "agent"


class ConversationStage(Enum):
    """Stages in conversation flow"""
    INITIAL_CONTACT = "initial_contact"
    QUALIFICATION = "qualification"
    NEEDS_ASSESSMENT = "needs_assessment"
    PROPERTY_DISCUSSION = "property_discussion"
    SCHEDULING = "scheduling"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    POST_SALE = "post_sale"


class MessageType(Enum):
    """Types of messages in conversation"""
    USER_MESSAGE = "user"
    ASSISTANT_MESSAGE = "assistant"
    SYSTEM_MESSAGE = "system"
    PROPERTY_SHARE = "property_share"
    DOCUMENT_SHARE = "document_share"


@dataclass
class ChatMessage:
    """Individual chat message"""
    message_id: str
    user_id: str
    tenant_id: str
    message_type: MessageType
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Metadata
    session_id: Optional[str] = None
    conversation_stage: Optional[ConversationStage] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ML context
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    sentiment_score: Optional[float] = None
    intent: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "message_id": self.message_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "message_type": self.message_type.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "conversation_stage": self.conversation_stage.value if self.conversation_stage else None,
            "metadata": self.metadata,
            "extracted_entities": self.extracted_entities,
            "sentiment_score": self.sentiment_score,
            "intent": self.intent
        }


@dataclass
class ConversationContext:
    """Context for ongoing conversation"""
    conversation_id: str
    user_id: str
    tenant_id: str
    user_type: UserType
    current_stage: ConversationStage

    # User profile
    user_profile: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)

    # Conversation state
    messages: List[ChatMessage] = field(default_factory=list)
    active_session_id: Optional[str] = None
    last_interaction: datetime = field(default_factory=datetime.now)

    # ML insights
    behavioral_insights: Dict[str, Any] = field(default_factory=dict)
    personalization_data: Dict[str, Any] = field(default_factory=dict)

    # Business context
    lead_score: Optional[float] = None
    conversion_probability: Optional[float] = None
    priority_level: str = "medium"


class ChatbotManager:
    """
    Unified chatbot manager for all user types with behavioral learning integration.

    Features:
    - Cross-session conversation tracking
    - Tenant-specific context isolation
    - Behavioral learning integration
    - Intelligent response generation
    - Real-time personalization
    """

    def __init__(
        self,
        behavior_tracker: Optional[IBehaviorTracker] = None,
        feature_engineer: Optional[IFeatureEngineer] = None,
        personalization_engine: Optional[IPersonalizationEngine] = None
    ):
        """Initialize chatbot manager with ML components"""
        self.behavior_tracker = behavior_tracker
        self.feature_engineer = feature_engineer
        self.personalization_engine = personalization_engine

        # In-memory storage (in production, use persistent storage)
        self.conversations: Dict[str, ConversationContext] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> session_ids
        self.tenant_data: Dict[str, Dict[str, Any]] = {}  # tenant_id -> data

        # Response templates by user type and stage
        self.response_templates = self._initialize_response_templates()

        # Entity extraction patterns
        self.entity_patterns = self._initialize_entity_patterns()

        logger.info("ChatbotManager initialized with ML integration")

    async def start_conversation(
        self,
        user_id: str,
        tenant_id: str,
        user_type: UserType,
        session_id: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> ConversationContext:
        """Start a new conversation or resume existing one"""

        # Check for existing conversation
        conversation_key = f"{tenant_id}:{user_id}"

        if conversation_key in self.conversations:
            # Resume existing conversation
            context = self.conversations[conversation_key]
            context.active_session_id = session_id or str(uuid.uuid4())
            context.last_interaction = datetime.now()

            logger.info(f"Resumed conversation for {user_type.value} {user_id} in tenant {tenant_id}")
        else:
            # Create new conversation
            conversation_id = str(uuid.uuid4())
            context = ConversationContext(
                conversation_id=conversation_id,
                user_id=user_id,
                tenant_id=tenant_id,
                user_type=user_type,
                current_stage=ConversationStage.INITIAL_CONTACT,
                active_session_id=session_id or str(uuid.uuid4()),
                user_profile=initial_context or {}
            )

            self.conversations[conversation_key] = context

            # Track session
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = []
            self.user_sessions[user_id].append(context.active_session_id)

            logger.info(f"Started new conversation for {user_type.value} {user_id} in tenant {tenant_id}")

        return context

    async def process_message(
        self,
        user_id: str,
        tenant_id: str,
        message_content: str,
        session_id: Optional[str] = None,
        user_type: Optional[UserType] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Process incoming message and generate response"""

        try:
            # Get or create conversation context
            conversation_key = f"{tenant_id}:{user_id}"

            if conversation_key not in self.conversations:
                # Auto-detect user type or use provided
                detected_user_type = user_type or await self._detect_user_type(message_content)
                await self.start_conversation(user_id, tenant_id, detected_user_type, session_id)

            context = self.conversations[conversation_key]
            context.active_session_id = session_id or context.active_session_id

            # Create user message
            user_message = ChatMessage(
                message_id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                message_type=MessageType.USER_MESSAGE,
                content=message_content,
                session_id=context.active_session_id,
                conversation_stage=context.current_stage
            )

            # Extract entities and analyze intent
            await self._analyze_message(user_message, context)

            # Add to conversation
            context.messages.append(user_message)
            context.last_interaction = datetime.now()

            # Track behavioral event
            if self.behavior_tracker:
                await self._track_conversation_event(user_message, context)

            # Generate response
            response_content, response_metadata = await self._generate_response(
                user_message, context
            )

            # Create assistant message
            assistant_message = ChatMessage(
                message_id=str(uuid.uuid4()),
                user_id=user_id,
                tenant_id=tenant_id,
                message_type=MessageType.ASSISTANT_MESSAGE,
                content=response_content,
                session_id=context.active_session_id,
                conversation_stage=context.current_stage,
                metadata=response_metadata
            )

            context.messages.append(assistant_message)

            # Update conversation stage if needed
            await self._update_conversation_stage(context)

            # Update ML insights
            if self.feature_engineer:
                await self._update_behavioral_insights(context)

            return response_content, response_metadata

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return "I apologize, but I'm having trouble processing your message right now. Could you please try again?", {}

    async def get_conversation_history(
        self,
        user_id: str,
        tenant_id: str,
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """Get conversation history for user"""

        conversation_key = f"{tenant_id}:{user_id}"

        if conversation_key not in self.conversations:
            return []

        messages = self.conversations[conversation_key].messages

        if limit:
            return messages[-limit:]

        return messages

    async def get_user_insights(
        self,
        user_id: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """Get behavioral insights for user"""

        conversation_key = f"{tenant_id}:{user_id}"

        if conversation_key not in self.conversations:
            return {}

        context = self.conversations[conversation_key]

        insights = {
            "conversation_summary": {
                "total_messages": len(context.messages),
                "conversation_duration": (datetime.now() - context.messages[0].timestamp).total_seconds() / 3600 if context.messages else 0,
                "current_stage": context.current_stage.value,
                "last_interaction": context.last_interaction.isoformat(),
                "session_count": len(self.user_sessions.get(user_id, []))
            },
            "behavioral_insights": context.behavioral_insights,
            "personalization_data": context.personalization_data,
            "lead_scoring": {
                "lead_score": context.lead_score,
                "conversion_probability": context.conversion_probability,
                "priority_level": context.priority_level
            }
        }

        # Add ML insights if available
        if self.personalization_engine and context.messages:
            try:
                # Get recent behavioral events
                if self.behavior_tracker:
                    events = await self.behavior_tracker.get_events(
                        entity_id=user_id,
                        entity_type=context.user_type.value
                    )

                    if events and self.feature_engineer:
                        # Extract features
                        features = await self.feature_engineer.extract_features(
                            user_id, context.user_type.value, events
                        )

                        # Get recommendations
                        recommendations = await self.personalization_engine.get_recommendations(
                            entity_id=user_id,
                            entity_type=context.user_type.value,
                            max_results=5
                        )

                        insights["ml_insights"] = {
                            "feature_count": len(features.numerical_features) + len(features.categorical_features),
                            "recommendations_available": len(recommendations),
                            "personalization_confidence": np.mean([r.confidence for r in recommendations]) if recommendations else 0
                        }

            except Exception as e:
                logger.warning(f"Failed to generate ML insights: {str(e)}")

        return insights

    # Helper methods

    async def _detect_user_type(self, message_content: str) -> UserType:
        """Detect user type from initial message"""
        content_lower = message_content.lower()

        # Simple keyword-based detection
        if any(word in content_lower for word in ["sell", "selling", "list", "listing", "market my"]):
            return UserType.SELLER
        elif any(word in content_lower for word in ["buy", "buying", "purchase", "looking for", "find me"]):
            return UserType.BUYER
        else:
            return UserType.LEAD

    async def _analyze_message(self, message: ChatMessage, context: ConversationContext):
        """Analyze message for entities and intent"""
        content_lower = message.content.lower()

        # Extract common real estate entities
        entities = {}

        # Budget/Price extraction
        import re
        price_patterns = [
            r'\$([0-9,]+)k?',
            r'([0-9,]+)\s*k',
            r'([0-9,]+)\s*thousand',
            r'([0-9,]+)\s*million'
        ]

        for pattern in price_patterns:
            matches = re.findall(pattern, content_lower)
            if matches:
                try:
                    price = int(matches[0].replace(',', ''))
                    if 'k' in content_lower or 'thousand' in content_lower:
                        price *= 1000
                    elif 'million' in content_lower:
                        price *= 1000000
                    entities['budget'] = price
                    break
                except ValueError:
                    pass

        # Bedroom/bathroom extraction
        bedroom_match = re.search(r'([0-9]+)\s*(bed|bedroom)', content_lower)
        if bedroom_match:
            entities['bedrooms'] = int(bedroom_match.group(1))

        bathroom_match = re.search(r'([0-9]+)\s*(bath|bathroom)', content_lower)
        if bathroom_match:
            entities['bathrooms'] = int(bathroom_match.group(1))

        # Location extraction (simple)
        location_keywords = ['downtown', 'suburb', 'city', 'neighborhood', 'area', 'district']
        for keyword in location_keywords:
            if keyword in content_lower:
                # Extract surrounding context
                words = content_lower.split()
                for i, word in enumerate(words):
                    if keyword in word:
                        # Get surrounding words for location context
                        start = max(0, i-2)
                        end = min(len(words), i+3)
                        entities['location_mention'] = ' '.join(words[start:end])
                        break

        # Intent detection
        intent = "general_inquiry"

        if any(word in content_lower for word in ["schedule", "appointment", "meeting", "show", "tour"]):
            intent = "scheduling"
        elif any(word in content_lower for word in ["price", "cost", "budget", "afford"]):
            intent = "pricing_inquiry"
        elif any(word in content_lower for word in ["location", "neighborhood", "area", "where"]):
            intent = "location_inquiry"
        elif any(word in content_lower for word in ["features", "amenities", "specs", "details"]):
            intent = "feature_inquiry"

        # Sentiment analysis (simple)
        positive_words = ['great', 'excellent', 'perfect', 'love', 'interested', 'excited']
        negative_words = ['not', 'dont', 'cant', 'wont', 'no', 'never']

        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)

        sentiment_score = (positive_count - negative_count) / max(1, positive_count + negative_count)

        message.extracted_entities = entities
        message.intent = intent
        message.sentiment_score = sentiment_score

    async def _generate_response(
        self,
        user_message: ChatMessage,
        context: ConversationContext
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate appropriate response based on context"""

        user_type = context.user_type
        stage = context.current_stage
        intent = user_message.intent
        entities = user_message.extracted_entities

        # Get base response template
        response_template = self._get_response_template(user_type, stage, intent)

        # Personalize response based on extracted entities
        response = self._personalize_response(response_template, entities, context)

        # Add intelligent follow-up questions
        follow_ups = self._generate_follow_up_questions(user_type, stage, entities)

        if follow_ups:
            response += "\n\n" + follow_ups

        # Metadata for response tracking
        metadata = {
            "template_used": f"{user_type.value}_{stage.value}_{intent}",
            "entities_detected": list(entities.keys()),
            "personalization_applied": bool(entities),
            "follow_up_generated": bool(follow_ups)
        }

        return response, metadata

    async def _track_conversation_event(self, message: ChatMessage, context: ConversationContext):
        """Track conversation as behavioral event"""

        if not self.behavior_tracker:
            return

        # Create behavioral event
        event = BehavioralEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LEAD_INTERACTION,
            timestamp=message.timestamp,
            lead_id=message.user_id,
            session_id=message.session_id,
            event_data={
                "message_content": message.content,
                "conversation_stage": context.current_stage.value,
                "user_type": context.user_type.value,
                "intent": message.intent,
                "entities": message.extracted_entities,
                "sentiment": message.sentiment_score
            },
            metadata={
                "tenant_id": message.tenant_id,
                "conversation_id": context.conversation_id,
                "message_type": message.message_type.value
            }
        )

        await self.behavior_tracker.track_event(event)

    async def _update_conversation_stage(self, context: ConversationContext):
        """Update conversation stage based on recent messages"""

        # Analyze recent messages to determine stage progression
        recent_messages = context.messages[-3:] if len(context.messages) >= 3 else context.messages

        # Simple stage progression logic
        recent_intents = [msg.intent for msg in recent_messages if msg.intent]
        recent_entities = {}

        for msg in recent_messages:
            recent_entities.update(msg.extracted_entities)

        current_stage = context.current_stage

        # Stage progression rules
        if current_stage == ConversationStage.INITIAL_CONTACT:
            if recent_entities.get('budget') or 'pricing_inquiry' in recent_intents:
                context.current_stage = ConversationStage.QUALIFICATION

        elif current_stage == ConversationStage.QUALIFICATION:
            if len(recent_entities) >= 3:  # Sufficient qualification data
                context.current_stage = ConversationStage.NEEDS_ASSESSMENT

        elif current_stage == ConversationStage.NEEDS_ASSESSMENT:
            if 'scheduling' in recent_intents:
                context.current_stage = ConversationStage.SCHEDULING

        # Update user profile with extracted entities
        context.user_profile.update(recent_entities)

    async def _update_behavioral_insights(self, context: ConversationContext):
        """Update behavioral insights using feature engineering"""

        if not self.feature_engineer or not self.behavior_tracker:
            return

        try:
            # Get recent events for the user
            events = await self.behavior_tracker.get_events(
                entity_id=context.user_id,
                entity_type=context.user_type.value
            )

            if events:
                # Extract features
                features = await self.feature_engineer.extract_features(
                    context.user_id, context.user_type.value, events
                )

                # Update behavioral insights
                context.behavioral_insights = {
                    "engagement_score": features.numerical_features.get('engagement_score', 0.5),
                    "interaction_velocity": features.numerical_features.get('interaction_velocity', 0.0),
                    "session_consistency": features.numerical_features.get('session_consistency', 0.0),
                    "feature_count": len(features.numerical_features),
                    "last_updated": datetime.now().isoformat()
                }

                # Update lead scoring (simple implementation)
                engagement = features.numerical_features.get('engagement_score', 0.5)
                message_count = len(context.messages)
                recency_hours = (datetime.now() - context.last_interaction).total_seconds() / 3600

                # Simple lead scoring formula
                lead_score = min(100, (engagement * 50) + (message_count * 2) + max(0, 10 - recency_hours))
                context.lead_score = lead_score

                # Conversion probability (mockup)
                context.conversion_probability = min(1.0, lead_score / 100 * 0.8 + engagement * 0.2)

                # Priority level
                if lead_score >= 80:
                    context.priority_level = "high"
                elif lead_score >= 50:
                    context.priority_level = "medium"
                else:
                    context.priority_level = "low"

        except Exception as e:
            logger.warning(f"Failed to update behavioral insights: {str(e)}")

    def _initialize_response_templates(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Initialize response templates by user type and stage"""
        return {
            "lead": {
                "initial_contact": {
                    "general_inquiry": "Hi! Thanks for reaching out. I'm here to help you with your real estate needs. What are you looking for today?",
                    "pricing_inquiry": "I'd be happy to help you understand pricing in your area. Could you tell me which neighborhoods you're considering?",
                    "location_inquiry": "Great question about the area! I can provide detailed information about different neighborhoods. What's most important to you in a location?"
                },
                "qualification": {
                    "general_inquiry": "To help you find the perfect property, could you share your budget range and preferred number of bedrooms?",
                    "pricing_inquiry": "Understanding your budget helps me show you the best options. Are you pre-approved for financing?",
                    "feature_inquiry": "What features are most important to you? For example, updated kitchen, home office, or outdoor space?"
                }
            },
            "buyer": {
                "initial_contact": {
                    "general_inquiry": "Welcome! I'm excited to help you find your next home. Let's start by understanding what you're looking for.",
                    "scheduling": "I'd love to show you some properties! When works best for your schedule?"
                },
                "needs_assessment": {
                    "feature_inquiry": "Let me find properties that match your criteria. What's your timeline for purchasing?",
                    "location_inquiry": "I know some great options in that area. Would you like to see properties this week?"
                }
            },
            "seller": {
                "initial_contact": {
                    "general_inquiry": "Hi! I understand you're thinking about selling. I'd love to help you get the best value for your property.",
                    "pricing_inquiry": "I can provide a free market analysis. When did you purchase your home, and have you made any major improvements?"
                },
                "qualification": {
                    "general_inquiry": "To give you an accurate valuation, could you tell me about your property's condition and any recent updates?",
                    "scheduling": "I'd like to schedule a time to see your property in person. What works best for you this week?"
                }
            }
        }

    def _initialize_entity_patterns(self) -> Dict[str, Any]:
        """Initialize entity extraction patterns"""
        return {
            "budget_keywords": ["budget", "price", "cost", "afford", "$", "k", "thousand", "million"],
            "bedroom_keywords": ["bed", "bedroom", "br"],
            "bathroom_keywords": ["bath", "bathroom", "ba"],
            "location_keywords": ["downtown", "suburb", "neighborhood", "area", "district", "near"],
            "scheduling_keywords": ["schedule", "appointment", "meeting", "show", "tour", "visit"],
            "urgency_keywords": ["asap", "urgent", "soon", "now", "immediately"]
        }

    def _get_response_template(self, user_type: UserType, stage: ConversationStage, intent: str) -> str:
        """Get appropriate response template"""
        templates = self.response_templates.get(user_type.value, {})
        stage_templates = templates.get(stage.value, {})
        return stage_templates.get(intent, stage_templates.get("general_inquiry",
            "I understand. How can I help you with your real estate needs?"))

    def _personalize_response(self, template: str, entities: Dict[str, Any], context: ConversationContext) -> str:
        """Personalize response based on extracted entities"""
        response = template

        # Add budget-specific responses
        if "budget" in entities:
            budget = entities["budget"]
            if budget < 300000:
                response += f" With a budget around ${budget:,}, I can show you some excellent starter homes and condos."
            elif budget < 700000:
                response += f" With a budget of ${budget:,}, you have great options in both established and up-and-coming neighborhoods."
            else:
                response += f" With a budget of ${budget:,}, I can show you some premium properties with luxury features."

        # Add bedroom-specific responses
        if "bedrooms" in entities:
            bedrooms = entities["bedrooms"]
            if bedrooms >= 4:
                response += f" Looking for {bedrooms} bedrooms gives you plenty of space for a growing family or home office."
            elif bedrooms == 3:
                response += f" A {bedrooms}-bedroom home is perfect for flexibility - great for families or having a home office."

        return response

    def _generate_follow_up_questions(self, user_type: UserType, stage: ConversationStage, entities: Dict[str, Any]) -> str:
        """Generate intelligent follow-up questions"""
        follow_ups = []

        if user_type == UserType.BUYER or user_type == UserType.LEAD:
            if stage == ConversationStage.QUALIFICATION:
                if "budget" not in entities:
                    follow_ups.append("What's your budget range for this purchase?")
                if "bedrooms" not in entities:
                    follow_ups.append("How many bedrooms are you looking for?")
                if "location_mention" not in entities:
                    follow_ups.append("Do you have preferred neighborhoods or areas?")

            elif stage == ConversationStage.NEEDS_ASSESSMENT:
                follow_ups.append("Would you like me to send you some listings that match your criteria?")

        elif user_type == UserType.SELLER:
            if stage == ConversationStage.QUALIFICATION:
                follow_ups.append("What's prompting you to sell at this time?")
                follow_ups.append("What's your ideal timeline for selling?")

        return " ".join(follow_ups)

    def get_active_conversations(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all active conversations for a tenant"""
        active = []

        for key, context in self.conversations.items():
            if context.tenant_id == tenant_id:
                # Consider conversation active if last interaction was within 24 hours
                hours_since_last = (datetime.now() - context.last_interaction).total_seconds() / 3600

                if hours_since_last < 24:
                    active.append({
                        "user_id": context.user_id,
                        "user_type": context.user_type.value,
                        "current_stage": context.current_stage.value,
                        "message_count": len(context.messages),
                        "last_interaction": context.last_interaction.isoformat(),
                        "lead_score": context.lead_score,
                        "priority_level": context.priority_level
                    })

        return sorted(active, key=lambda x: x["last_interaction"], reverse=True)

    async def export_conversation_data(self, tenant_id: str) -> Dict[str, Any]:
        """Export conversation data for analytics"""
        tenant_conversations = []

        for key, context in self.conversations.items():
            if context.tenant_id == tenant_id:
                conversation_data = {
                    "conversation_id": context.conversation_id,
                    "user_id": context.user_id,
                    "user_type": context.user_type.value,
                    "current_stage": context.current_stage.value,
                    "message_count": len(context.messages),
                    "duration_hours": (datetime.now() - context.messages[0].timestamp).total_seconds() / 3600 if context.messages else 0,
                    "lead_score": context.lead_score,
                    "conversion_probability": context.conversion_probability,
                    "user_profile": context.user_profile,
                    "behavioral_insights": context.behavioral_insights,
                    "messages": [msg.to_dict() for msg in context.messages]
                }
                tenant_conversations.append(conversation_data)

        return {
            "tenant_id": tenant_id,
            "export_timestamp": datetime.now().isoformat(),
            "total_conversations": len(tenant_conversations),
            "conversations": tenant_conversations
        }