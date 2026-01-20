# Jorge's Seller Bot - Complete Development Reference

## 🎯 PROJECT OVERVIEW
**Objective**: Develop AI seller qualification bot for Jorge's GHL Real Estate System
**Foundation**: EnterpriseHub GHL Real Estate AI Platform (80% reusable)
**Timeline**: ~20 hours development
**Production Ready**: Yes, leveraging existing production-tested components

---

## 📋 JORGE'S REQUIREMENTS SUMMARY

### Core Functionality
- **Trigger**: "Needs Qualifying" tag applied to lead
- **Questions**: 4 specific seller questions (asked one at a time)
- **Classification**: Hot/Warm/Cold temperature based on responses
- **Follow-up**: 2-3 days for 30 days → 14-day intervals ongoing
- **Tone**: Direct, confrontational, no emojis, no hyphens
- **SMS**: 160 character limit enforcement

### Jorge's 4 Questions (In Order)
1. "What's got you considering wanting to sell, where would you move to?"
2. "If our team sold your home within the next 30 to 45 days, would that pose a problem for you?"
3. "How would you describe your home, would you say it's move-in ready or would it need some work?"
4. "What price would incentivize you to sell?"

### Temperature Classification Logic
- **Hot**: Answered all 4 questions + timeline within 30-45 days + high responsiveness
- **Warm**: Answered most questions + timeline beyond 45 days + some hesitation
- **Cold**: Vague answers or stops responding + long timeline or exploring

---

## 🏗️ KEY FILES TO REFERENCE/MODIFY

### Core Components (Existing - to Adapt)

#### 1. Webhook Handler
**File**: `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/api/routes/webhook.py`
- **Lines 103-145**: Tag-triggered activation (already supports "Needs Qualifying")
- **Lines 497-501**: Tag management actions
- **Lines 504-511**: Workflow triggering for agent handoff
- **Lines 490-511**: Auto-deactivation logic (currently 70% threshold)

**Key Pattern**:
```python
# Check activation tags
if any(tag in webhook_event.tags for tag in settings.activation_tags):
    # Process the conversation
    result = await conversation_manager.process_conversation(...)
```

#### 2. Conversation Manager (Core Brain)
**File**: `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/core/conversation_manager.py`
- **Lines 180-250**: Data extraction logic (adapt for seller fields)
- **Lines 100-110**: Smart resume for returning leads
- **Line 84**: One-question-at-a-time enforcement in system prompt

**Key Pattern**:
```python
# Get context and extract data
context = await self.get_context(contact_id, location_id)
extracted_data = await self.extract_data(user_message, current_preferences, tenant_config)

# Generate response
ai_response = await self.generate_response(
    user_message=user_message,
    contact_info=contact_info,
    context=context,
    is_buyer=False,  # Set to False for sellers
    tenant_config=tenant_config
)
```

#### 3. System Prompts (Needs Major Updates)
**File**: `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/prompts/system_prompts.py`
- **Lines 27-35**: Current 7 buyer questions (replace with Jorge's 4 seller questions)
- **Line 37**: Hot lead detection logic (adapt for 4 questions)
- **Lines 48-50**: One-question enforcement
- **Lines 53-57**: Re-engagement templates (adapt tone to confrontational)
- **Line 19**: SMS length control

**Critical Update Needed**:
```python
# Replace buyer questions with Jorge's seller questions
SELLER_QUESTIONS = [
    "What's got you considering wanting to sell, where would you move to?",
    "If our team sold your home within the next 30 to 45 days, would that pose a problem for you?",
    "How would you describe your home, would you say it's move-in ready or would it need some work?",
    "What price would incentivize you to sell?"
]

# Add confrontational tone instructions
CONFRONTATIONAL_TONE = """
You are direct and almost confrontational in your approach.
Ask tough questions. Don't be overly polite.
Be straightforward and no-nonsense.
NO emojis. NO hyphens. Keep responses under 160 characters.
"""
```

#### 4. Lead Scorer (Adapt for 4 Questions)
**File**: `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/services/lead_scorer.py`
- **Current**: Scores 0-7 based on buyer questions
- **Needed**: Score 0-4 based on Jorge's seller questions

**Key Pattern**:
```python
def calculate_seller_score(seller_data: Dict) -> int:
    """Score based on Jorge's 4 questions"""
    score = 0
    if seller_data.get('motivation'): score += 1
    if seller_data.get('timeline_acceptable'): score += 1
    if seller_data.get('property_condition'): score += 1
    if seller_data.get('price_expectation'): score += 1
    return score

# Classification thresholds
def get_seller_temperature(score: int) -> str:
    if score == 4: return "hot"      # All questions answered
    elif score >= 2: return "warm"   # Most questions answered
    else: return "cold"              # Few/no questions answered
```

#### 5. GHL Client (Ready to Use)
**File**: `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/services/ghl_client.py`
- **All methods ready**: send_message, add_tags, remove_tags, trigger_workflow

#### 6. Memory Service (Ready to Use)
**File**: `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/services/memory_service.py`
- **Context structure**: Ready for seller data
- **Persistence**: File-based or Redis

---

## 🆕 NEW FILES TO CREATE

### 1. Jorge Seller Engine (Main Logic)
**File**: `ghl_real_estate_ai/services/jorge_seller_engine.py`

```python
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class SellerQuestionType(Enum):
    MOTIVATION = "motivation"
    TIMELINE = "timeline"
    CONDITION = "condition"
    PRICE = "price"

@dataclass
class SellerQuestions:
    MOTIVATION = "What's got you considering wanting to sell, where would you move to?"
    TIMELINE = "If our team sold your home within the next 30 to 45 days, would that pose a problem for you?"
    CONDITION = "How would you describe your home, would you say it's move-in ready or would it need some work?"
    PRICE = "What price would incentivize you to sell?"

    @classmethod
    def get_question_order(cls) -> List[SellerQuestionType]:
        return [SellerQuestionType.MOTIVATION, SellerQuestionType.TIMELINE,
                SellerQuestionType.CONDITION, SellerQuestionType.PRICE]

    @classmethod
    def get_next_question(cls, answered_questions: Dict) -> Optional[str]:
        for q_type in cls.get_question_order():
            if q_type.value not in answered_questions:
                return getattr(cls, q_type.name)
        return None

class JorgeSellerEngine:
    def __init__(self, conversation_manager, ghl_client):
        self.conversation_manager = conversation_manager
        self.ghl_client = ghl_client

    async def process_seller_response(self, contact_id: str, user_message: str, location_id: str) -> Dict:
        # 1. Get conversation context
        context = await self.conversation_manager.get_context(contact_id, location_id)

        # 2. Extract seller data
        seller_data = await self._extract_seller_data(user_message, context.get("seller_preferences", {}))

        # 3. Calculate temperature
        temperature = self._calculate_seller_temperature(seller_data)

        # 4. Generate response
        if temperature == "hot":
            response = await self._generate_handoff_message(seller_data)
            actions = await self._create_hot_seller_actions(contact_id, location_id)
        else:
            next_question = SellerQuestions.get_next_question(seller_data)
            if next_question:
                response = await self._generate_confrontational_response(next_question, seller_data)
            else:
                response = await self._generate_nurture_transition(seller_data)
                actions = await self._create_nurture_actions(contact_id, temperature)

        # 5. Update context
        await self.conversation_manager.update_context(
            contact_id=contact_id, user_message=user_message, ai_response=response,
            extracted_data=seller_data, location_id=location_id, seller_temperature=temperature
        )

        return {"message": response, "actions": actions, "temperature": temperature}
```

### 2. Confrontational Tone Engine
**File**: `ghl_real_estate_ai/services/jorge_tone_engine.py`

```python
import re
import random

class JorgeToneEngine:
    CONFRONTATIONAL_PROMPTS = {
        "motivation": [
            "What's really driving this decision to sell?",
            "Where exactly are you planning to move?",
            "Are you serious about selling or just testing the waters?"
        ],
        "timeline": [
            "Can you actually close in 30-45 days or not?",
            "Is this timeline realistic for your situation?",
            "Are you ready to move that quickly?"
        ],
        "condition": [
            "Be honest, what kind of shape is your house really in?",
            "Would a buyer walk in and be ready to move in tomorrow?",
            "How much work are we talking about here?"
        ],
        "price": [
            "What's the absolute minimum you'd accept?",
            "Are you being realistic about the price?",
            "What number would make you say yes today?"
        ],
        "re_engagement": [
            "Are you actually serious about selling or just wasting our time?",
            "Should we close your file or are you still interested?",
            "Last chance, are you ready to get serious about selling?"
        ]
    }

    @staticmethod
    def generate_confrontational_response(question_type: str, seller_data: dict, previous_response: str) -> str:
        if len(previous_response.strip()) < 10:
            return random.choice(JorgeToneEngine.CONFRONTATIONAL_PROMPTS["re_engagement"])

        base_prompts = JorgeToneEngine.CONFRONTATIONAL_PROMPTS.get(question_type, [])
        selected_prompt = random.choice(base_prompts)
        return JorgeToneEngine.sanitize_for_sms(selected_prompt)

    @staticmethod
    def sanitize_for_sms(message: str) -> str:
        # Remove emojis
        message = re.sub(r'[^\w\s,.!?]', '', message)
        # Remove hyphens (Jorge's requirement)
        message = message.replace('-', ' ')
        # Ensure under 160 characters
        if len(message) > 160:
            message = message[:157] + "..."
        return message.strip()
```

### 3. Follow-up Automation Engine
**File**: `ghl_real_estate_ai/services/jorge_followup_engine.py`

```python
from datetime import datetime, timedelta

class JorgeFollowupEngine:
    ACTIVE_FOLLOWUP_DAYS = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29]  # Every 2-3 days
    LONGTERM_FOLLOWUP_INTERVAL = 14  # Every 14 days after 30 days

    def __init__(self, ghl_client, conversation_manager):
        self.ghl_client = ghl_client
        self.conversation_manager = conversation_manager

    async def schedule_followup(self, contact_id: str, location_id: str,
                              seller_temperature: str, last_interaction: datetime):
        days_since_last = (datetime.now() - last_interaction).days

        if days_since_last <= 30:
            next_followup_day = self._get_next_active_followup_day(days_since_last)
            if next_followup_day:
                await self._schedule_active_followup(contact_id, location_id, seller_temperature, next_followup_day)
        else:
            await self._schedule_longterm_followup(contact_id, location_id, seller_temperature)

    def _get_next_active_followup_day(self, days_since: int) -> Optional[int]:
        for day in self.ACTIVE_FOLLOWUP_DAYS:
            if day > days_since:
                return day
        return None

    async def _schedule_active_followup(self, contact_id: str, location_id: str, temperature: str, followup_day: int):
        if temperature == "hot":
            message = "Ready to move forward with selling? Let's get you scheduled."
        elif temperature == "warm":
            message = "Still thinking about selling? What questions do you have?"
        else:  # cold
            message = "Are you actually serious about selling or should we close your file?"

        await self.ghl_client.send_message(
            contact_id=contact_id,
            message=JorgeToneEngine.sanitize_for_sms(message),
            channel=MessageType.SMS
        )
```

### 4. Seller Data Schema
**File**: `ghl_real_estate_ai/schemas/seller_data.py`

```python
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class TimelineUrgency(Enum):
    URGENT_30_45_DAYS = "30-45 days"
    FLEXIBLE = "flexible"
    LONG_TERM = "long-term"
    UNKNOWN = "unknown"

class PropertyCondition(Enum):
    MOVE_IN_READY = "move-in ready"
    NEEDS_WORK = "needs work"
    MAJOR_REPAIRS = "major repairs"
    UNKNOWN = "unknown"

@dataclass
class SellerProfile:
    # Question 1: Motivation
    motivation: Optional[str] = None
    relocation_destination: Optional[str] = None

    # Question 2: Timeline
    timeline_urgency: Optional[TimelineUrgency] = None
    timeline_acceptable: Optional[bool] = None

    # Question 3: Condition
    property_condition: Optional[PropertyCondition] = None
    repair_estimate: Optional[str] = None

    # Question 4: Price
    price_expectation: Optional[int] = None
    price_flexibility: Optional[str] = None

    # Metrics
    questions_answered: int = 0
    response_quality: float = 0.0
    responsiveness: float = 0.0

    @property
    def completion_percentage(self) -> float:
        return (self.questions_answered / 4) * 100
```

### 5. Jorge Configuration
**File**: `ghl_real_estate_ai/ghl_utils/jorge_config.py`

```python
class JorgeSellerConfig:
    # Activation/Deactivation Tags
    ACTIVATION_TAGS = ["Needs Qualifying"]
    DEACTIVATION_TAGS = ["AI-Off", "Qualified", "Stop-Bot", "Seller-Qualified"]

    # Temperature Tags
    HOT_SELLER_TAG = "Hot-Seller"
    WARM_SELLER_TAG = "Warm-Seller"
    COLD_SELLER_TAG = "Cold-Seller"

    # Classification Thresholds
    HOT_SELLER_THRESHOLD = 0.75  # Must answer all 4 questions
    WARM_SELLER_THRESHOLD = 0.50  # Must answer 3+ questions

    # Follow-up Settings
    ACTIVE_FOLLOWUP_DAYS = 30
    ACTIVE_FOLLOWUP_INTERVAL_MIN = 2
    ACTIVE_FOLLOWUP_INTERVAL_MAX = 3
    LONGTERM_FOLLOWUP_INTERVAL = 14

    # GHL Integration
    HOT_SELLER_WORKFLOW_ID = "jorge_hot_seller_workflow"
    AGENT_NOTIFICATION_FIELD = "seller_lead_score"

    # Message Settings
    MAX_SMS_LENGTH = 160
    CONFRONTATIONAL_TONE = True
    NO_EMOJIS = True
    NO_HYPHENS = True

    # Jorge's 4 Questions
    SELLER_QUESTIONS = {
        1: "What's got you considering wanting to sell, where would you move to?",
        2: "If our team sold your home within the next 30 to 45 days, would that pose a problem for you?",
        3: "How would you describe your home, would you say it's move-in ready or would it need some work?",
        4: "What price would incentivize you to sell?"
    }
```

---

## 🔧 CONFIGURATION FILES

### Environment Variables (.env updates)
```bash
# Jorge Seller Bot Configuration
JORGE_SELLER_MODE=true
ACTIVATION_TAGS=["Needs Qualifying"]
DEACTIVATION_TAGS=["AI-Off", "Qualified", "Stop-Bot", "Seller-Qualified"]
HOT_SELLER_WORKFLOW_ID=jorge_workflow_12345
CONFRONTATIONAL_TONE=true
MAX_SMS_LENGTH=160
HOT_SELLER_THRESHOLD=0.75
WARM_SELLER_THRESHOLD=0.50
ACTIVE_FOLLOWUP_DAYS=30
LONGTERM_FOLLOWUP_INTERVAL=14
```

### Database Schema Updates
```sql
-- Add seller-specific fields to existing conversation context table
ALTER TABLE conversation_contexts ADD COLUMN seller_preferences JSONB;
ALTER TABLE conversation_contexts ADD COLUMN seller_temperature VARCHAR(10);
ALTER TABLE conversation_contexts ADD COLUMN followup_phase VARCHAR(20);

-- Seller preferences JSONB structure:
{
    "motivation": "relocation",
    "relocation_destination": "Austin, TX",
    "timeline_urgency": "30-45 days",
    "timeline_acceptable": true,
    "property_condition": "move-in ready",
    "price_expectation": 450000,
    "price_flexibility": "negotiable",
    "questions_answered": 4,
    "response_quality": 0.85,
    "responsiveness": 0.92,
    "last_followup_sent": "2026-01-20T10:00:00Z",
    "followup_count": 3
}
```

---

## 🚀 DEVELOPMENT PHASES

### Phase 1: Foundation Adaptation (4 hours)
1. **Create Jorge Seller Engine** (2 hours)
   - Build `jorge_seller_engine.py`
   - Integrate with existing conversation_manager
   - Test basic question flow

2. **Update System Prompts** (1 hour)
   - Replace buyer questions with seller questions in `system_prompts.py:27-35`
   - Add confrontational tone instructions
   - Update SMS optimization rules

3. **Data Schema Updates** (1 hour)
   - Create `SellerProfile` dataclass in `schemas/seller_data.py`
   - Update database schema for seller fields
   - Modify extraction logic in conversation_manager

**Success Criteria**: Jorge's 4 questions working, basic seller data extraction, database updated

### Phase 2: Temperature Classification (3 hours)
1. **Seller Temperature Classifier** (2 hours)
   - Adapt `lead_scorer.py` for 4 questions vs 7
   - Implement Jorge's Hot/Warm/Cold logic
   - Question completion + timeline urgency weighting

2. **Tag Management Integration** (1 hour)
   - Apply Hot-Seller, Warm-Seller, Cold-Seller tags
   - Remove "Needs Qualifying" when qualified
   - Trigger agent notification workflow for hot leads

**Success Criteria**: Accurate temperature classification, automatic tag application, hot lead notifications

### Phase 3: Confrontational Tone Engine (4 hours)
1. **Tone Engine Development** (2 hours)
   - Build `jorge_tone_engine.py`
   - Confrontational prompt templates
   - Response sanitization (no emojis, hyphens, 160 chars)

2. **Claude System Prompt Updates** (1 hour)
   - Add confrontational personality to system prompts
   - Direct questioning techniques
   - Evasive answer escalation

3. **Response Quality Assessment** (1 hour)
   - Detect vague/evasive answers
   - Escalate confrontational tone
   - Quality scoring for temperature classification

**Success Criteria**: Direct confrontational responses, SMS-optimized, appropriate tone escalation

### Phase 4: Follow-up Automation (5 hours)
1. **Active Follow-up Engine** (2 hours)
   - Build `jorge_followup_engine.py`
   - 2-3 day intervals for first 30 days
   - Temperature-appropriate messages

2. **Long-term Nurture Engine** (2 hours)
   - 14-day intervals after 30 days
   - Re-engagement logic for silent leads
   - Opt-out detection and handling

3. **Scheduling Integration** (1 hour)
   - GHL workflow triggers
   - Background task management
   - Follow-up tracking

**Success Criteria**: Automated follow-up sequences, proper timing, lead re-engagement

### Phase 5: Integration & Testing (4 hours)
1. **Integration Testing** (2 hours)
   - End-to-end webhook processing
   - Tag management verification
   - Workflow trigger validation

2. **Conversation Flow Testing** (1 hour)
   - All 4 question sequences
   - Temperature classification accuracy
   - Follow-up timing verification

3. **Edge Case Testing** (1 hour)
   - Silent leads, partial responses
   - Opt-out scenarios
   - System error handling

**Success Criteria**: Complete integration tested, edge cases handled, production ready

---

## ✅ TESTING CHECKLIST

### Unit Tests
```bash
# Create test files
tests/jorge_seller/
├── test_seller_engine.py
├── test_temperature_classifier.py
├── test_tone_engine.py
├── test_followup_engine.py
└── test_data_extraction.py

# Run tests
pytest tests/jorge_seller/ --cov=ghl_real_estate_ai.services.jorge --cov-report=html
```

### Integration Tests
- [ ] Complete 4-question sequence with hot lead outcome
- [ ] Cold lead follow-up sequence (2-3 days → 14 days)
- [ ] Tag management (add/remove Hot-Seller, etc.)
- [ ] Workflow triggering for agent handoff
- [ ] SMS length validation (all under 160 chars)
- [ ] Confrontational tone consistency

### User Acceptance Testing
- [ ] Jorge reviews conversation samples
- [ ] Tone validation ("confrontational enough?")
- [ ] Question sequence approval
- [ ] Follow-up timing confirmation

---

## 🎯 SUCCESS METRICS

### Technical KPIs
- Webhook response time: <2 seconds
- Message delivery: >99% success rate
- Classification accuracy: >90% (Jorge validation)
- Follow-up timing: Within 5 minutes of scheduled

### Business KPIs
- Qualification completion rate: % completing all 4 questions
- Temperature distribution: Hot/Warm/Cold percentages
- Agent handoff rate: % advancing to call stage
- Follow-up engagement: Response rates by phase
- Opt-out rate: <5% requesting no contact

---

## 🚨 CRITICAL INTEGRATION POINTS

### Webhook Handler Updates
**File**: `webhook.py`
**Lines to modify**: 103-145 (tag checking), 490-511 (auto-deactivation)

```python
# Add Jorge seller mode detection
if "Needs Qualifying" in webhook_event.tags and settings.JORGE_SELLER_MODE:
    # Route to Jorge seller engine instead of buyer engine
    result = await jorge_seller_engine.process_seller_response(...)
```

### System Prompt Integration
**File**: `system_prompts.py`
**Critical update**: Replace lines 27-35 with Jorge's questions

```python
# OLD (lines 27-35): 7 buyer questions
# NEW: Jorge's 4 seller questions
if is_seller_mode:
    questions_prompt = f"""
    Ask these 4 questions in order (one at a time):
    1. What's got you considering wanting to sell, where would you move to?
    2. If our team sold your home within the next 30 to 45 days, would that pose a problem for you?
    3. How would you describe your home, would you say it's move-in ready or would it need some work?
    4. What price would incentivize you to sell?

    Be direct and confrontational. No emojis. No hyphens. Under 160 characters.
    """
```

---

## 📞 DEPLOYMENT CHECKLIST

### GHL Sub-account Setup
- [ ] Create custom fields: seller_temperature, seller_motivation, price_expectation, property_condition
- [ ] Create workflow: Hot Seller Notification workflow
- [ ] Create tags: Hot-Seller, Warm-Seller, Cold-Seller
- [ ] Configure: Needs Qualifying trigger tag
- [ ] Set up: AI-Off, Qualified deactivation tags

### Environment Configuration
- [ ] Set JORGE_SELLER_MODE=true
- [ ] Configure activation/deactivation tags
- [ ] Set workflow IDs for agent handoff
- [ ] Configure confrontational tone settings
- [ ] Set SMS length limits

### Production Deployment
```bash
git checkout main
git pull origin main
docker build -t jorge-seller-bot:v2.0 .
docker-compose up -d
python manage.py migrate
cp .env.jorge .env
```

### Monitoring & Validation
- [ ] Webhook endpoint responding (<2s)
- [ ] Message delivery working (>99%)
- [ ] Tag management functioning
- [ ] Follow-up scheduling active
- [ ] Analytics tracking enabled

---

## 🎉 FINAL SUCCESS CRITERIA

### Jorge Approval Requirements
- [ ] All 4 questions asked in correct order
- [ ] Confrontational tone ("direct, almost confrontational")
- [ ] No emojis, no hyphens in responses
- [ ] SMS under 160 characters
- [ ] Hot leads trigger agent notification
- [ ] Follow-up timing: 2-3 days → 14 days
- [ ] Proper opt-out handling

### Technical Requirements
- [ ] 80%+ test coverage on new code
- [ ] <2 second webhook response times
- [ ] >90% classification accuracy
- [ ] Zero data loss (persistent conversation state)
- [ ] Security compliance (PII protection)

This reference provides everything needed to continue Jorge's seller bot development in a new chat session. The foundation is solid with 80% code reuse possible!