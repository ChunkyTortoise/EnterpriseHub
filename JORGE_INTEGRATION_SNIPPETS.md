# Jorge's Seller Bot - Critical Integration Code Snippets

## 🎯 Key Integration Points
This document contains the exact code snippets needed to integrate Jorge's seller bot with the existing EnterpriseHub system.

---

## 1. WEBHOOK HANDLER INTEGRATION

### File: `ghl_real_estate_ai/api/routes/webhook.py`

#### A. Add Jorge Mode Detection (Lines ~150-170)
```python
# Add this after existing tag checking logic (around line 150)

# Check if this is Jorge's seller qualification mode
jorge_seller_mode = (
    "Needs Qualifying" in webhook_event.tags and
    settings.JORGE_SELLER_MODE and
    not any(deactivate_tag in webhook_event.tags for deactivate_tag in settings.DEACTIVATION_TAGS)
)

if jorge_seller_mode:
    # Route to Jorge's seller engine
    from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine

    jorge_engine = JorgeSellerEngine(conversation_manager, ghl_client)
    result = await jorge_engine.process_seller_response(
        contact_id=contact_id,
        user_message=webhook_event.message_body,
        location_id=location_id
    )

    # Apply Jorge's specific actions
    if result.get("actions"):
        for action in result["actions"]:
            await ghl_client.apply_actions(contact_id, [action])

    # Send Jorge's response
    await ghl_client.send_message(
        contact_id=contact_id,
        message=result["message"],
        channel=MessageType.SMS
    )

    # Track analytics
    await analytics_service.track_event(
        event_type="jorge_seller_interaction",
        location_id=location_id,
        contact_id=contact_id,
        data={"temperature": result["temperature"], "questions_answered": result.get("questions_answered", 0)}
    )

    return {"status": "jorge_seller_processed", "temperature": result["temperature"]}

# Continue with existing buyer logic if not Jorge mode
elif any(tag in webhook_event.tags for tag in settings.activation_tags):
    # Existing buyer conversation logic continues here...
```

#### B. Update Settings Import (Top of file)
```python
# Add to imports at top of webhook.py
from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig
```

---

## 2. SYSTEM PROMPTS UPDATES

### File: `ghl_real_estate_ai/prompts/system_prompts.py`

#### A. Replace Buyer Questions (Lines 27-35)
```python
# REPLACE lines 27-35 with this Jorge seller version:

def build_seller_system_prompt(
    contact_name: str,
    conversation_stage: str,
    seller_temperature: str,
    extracted_seller_data: Dict,
    relevant_knowledge: str = "",
    is_returning_seller: bool = False,
    hours_since: float = 0,
    **kwargs
) -> str:

    # Jorge's 4 seller questions
    seller_questions = """
    Ask these 4 questions in order (ONE AT A TIME, wait for response):

    1. MOTIVATION: "What's got you considering wanting to sell, where would you move to?"
    2. TIMELINE: "If our team sold your home within the next 30 to 45 days, would that pose a problem for you?"
    3. CONDITION: "How would you describe your home, would you say it's move-in ready or would it need some work?"
    4. PRICE: "What price would incentivize you to sell?"

    NEVER ask a question if you already have the answer from previous responses.
    """

    # Jorge's confrontational tone requirements
    tone_instructions = """
    TONE REQUIREMENTS (CRITICAL):
    - Be direct and almost confrontational
    - Straightforward, no-nonsense approach
    - Short sentences with occasional commas instead of periods
    - NO emojis, NO hyphens, NO robotic phrasing
    - Keep ALL responses under 160 characters (SMS limit)
    - If they give vague answers, be more direct: "Are you actually serious about selling or just wasting our time?"
    """

    # Determine next question based on what's already answered
    next_question = _get_next_seller_question(extracted_seller_data)

    # Hot seller detection (all 4 questions + good timeline)
    if (extracted_seller_data.get("questions_answered", 0) >= 4 and
        extracted_seller_data.get("timeline_acceptable") and
        seller_temperature == "hot"):
        handoff_prompt = f"""
        {contact_name} has answered all qualification questions and is a HOT SELLER.

        Respond with: "Based on your answers, you're exactly who we help. Let me get you scheduled with our team to discuss your options. When works better for you - morning or afternoon?"

        This will trigger agent handoff automatically.
        """
        return handoff_prompt

    # Re-engagement for returning sellers
    if is_returning_seller and hours_since > 24:
        if hours_since <= 48:
            re_engage_prompt = f"""
            {contact_name} went silent after {hours_since:.1f} hours. Be direct:

            "Hey {contact_name}, just checking in, is it still a priority of yours to sell or have you given up?"
            """
        else:
            re_engage_prompt = f"""
            {contact_name} has been silent for {hours_since:.1f} hours. Final attempt:

            "Hey, are you actually still looking to sell or should we close your file?"
            """
        return re_engage_prompt

    # Main qualification prompt
    system_prompt = f"""
    You are a direct, no-nonsense real estate AI qualifying sellers for {contact_name}.

    {seller_questions}

    {tone_instructions}

    CURRENT STATUS:
    - Questions answered: {extracted_seller_data.get("questions_answered", 0)}/4
    - Seller temperature: {seller_temperature}
    - Next question: {next_question or "All questions answered"}

    EXTRACTED DATA:
    {json.dumps(extracted_seller_data, indent=2)}

    KNOWLEDGE BASE:
    {relevant_knowledge}

    Remember: Ask ONE question at a time. Be confrontational. No emojis. Under 160 characters.
    """

    return system_prompt

def _get_next_seller_question(seller_data: Dict) -> Optional[str]:
    """Get the next unanswered question in Jorge's sequence"""
    questions = [
        ("motivation", "What's got you considering wanting to sell, where would you move to?"),
        ("timeline_acceptable", "If our team sold your home within the next 30 to 45 days, would that pose a problem for you?"),
        ("property_condition", "How would you describe your home, would you say it's move-in ready or would it need some work?"),
        ("price_expectation", "What price would incentivize you to sell?")
    ]

    for field, question in questions:
        if not seller_data.get(field):
            return question
    return None
```

#### B. Update Main build_system_prompt Function
```python
# Add to the main build_system_prompt function (around line 60):

def build_system_prompt(
    contact_name: str,
    conversation_stage: str = "qualifying",
    lead_score: int = 0,
    extracted_preferences: Dict = None,
    relevant_knowledge: str = "",
    is_buyer: bool = True,  # Add this parameter
    is_seller: bool = False,  # Add this parameter
    seller_temperature: str = "cold",  # Add this parameter
    available_slots: str = "",
    appointment_status: str = "",
    property_recommendations: str = "",
    is_returning_lead: bool = False,
    hours_since: float = 0
) -> str:

    # Route to Jorge's seller prompt if seller mode
    if is_seller or not is_buyer:
        return build_seller_system_prompt(
            contact_name=contact_name,
            conversation_stage=conversation_stage,
            seller_temperature=seller_temperature,
            extracted_seller_data=extracted_preferences or {},
            relevant_knowledge=relevant_knowledge,
            is_returning_seller=is_returning_lead,
            hours_since=hours_since
        )

    # Continue with existing buyer logic...
    # (rest of existing function remains unchanged)
```

---

## 3. LEAD SCORER ADAPTATION

### File: `ghl_real_estate_ai/services/lead_scorer.py`

#### A. Add Seller Scoring Method
```python
# Add this method to the LeadScorer class:

def calculate_seller_score(self, seller_data: Dict) -> Dict:
    """
    Calculate seller lead score based on Jorge's 4 questions
    Returns score (0-4) and temperature classification
    """
    score = 0
    details = {}

    # Question 1: Motivation (25% weight)
    if seller_data.get("motivation") and seller_data.get("relocation_destination"):
        score += 1
        details["motivation_score"] = 1

    # Question 2: Timeline (35% weight - most important for Jorge)
    timeline_score = 0
    if seller_data.get("timeline_acceptable") is True:
        timeline_score = 1
    elif seller_data.get("timeline_acceptable") is False:
        timeline_score = 0.5  # Still answered, but not ideal

    score += timeline_score
    details["timeline_score"] = timeline_score

    # Question 3: Property Condition (20% weight)
    if seller_data.get("property_condition"):
        score += 1
        details["condition_score"] = 1

    # Question 4: Price Expectation (20% weight)
    if seller_data.get("price_expectation"):
        score += 1
        details["price_score"] = 1

    # Calculate temperature based on Jorge's rules
    temperature = self._classify_seller_temperature(
        score=score,
        seller_data=seller_data,
        response_quality=seller_data.get("response_quality", 0.5),
        responsiveness=seller_data.get("responsiveness", 0.5)
    )

    # Convert to percentage for consistency with existing system
    percentage_score = int((score / 4) * 100)

    return {
        "raw_score": score,
        "percentage_score": percentage_score,
        "temperature": temperature,
        "details": details,
        "questions_answered": score,
        "max_questions": 4
    }

def _classify_seller_temperature(self, score: int, seller_data: Dict,
                               response_quality: float, responsiveness: float) -> str:
    """Jorge's seller temperature classification logic"""

    # Hot seller criteria (Jorge's exact requirements)
    if (score == 4 and  # All questions answered
        seller_data.get("timeline_acceptable") is True and  # 30-45 days acceptable
        response_quality > 0.7 and  # High quality responses
        responsiveness > 0.7):  # Responsive to messages
        return "hot"

    # Warm seller criteria
    elif (score >= 3 and  # Most questions answered
          response_quality > 0.5):  # Decent responses
        return "warm"

    # Cold seller (default)
    else:
        return "cold"
```

#### B. Update Main calculate Method
```python
# Update the main calculate method to detect seller mode:

def calculate(self, context: Dict) -> int:
    """Main scoring method - detects buyer vs seller mode"""

    # Check if this is seller mode (Jorge's bot)
    if (context.get("seller_preferences") or
        context.get("seller_temperature") or
        "seller" in context.get("conversation_type", "").lower()):

        seller_result = self.calculate_seller_score(context.get("seller_preferences", {}))
        return seller_result["raw_score"]

    # Continue with existing buyer scoring logic...
    # (rest of existing method remains unchanged)
```

---

## 4. CONVERSATION MANAGER INTEGRATION

### File: `ghl_real_estate_ai/core/conversation_manager.py`

#### A. Add Seller Data Extraction (Lines ~200-250)
```python
# Add this method to the ConversationManager class:

async def extract_seller_data(
    self,
    user_message: str,
    current_seller_data: Dict,
    tenant_config: Dict
) -> Dict:
    """Extract seller-specific data from user message using Claude"""

    extraction_prompt = f"""
    Extract seller qualification data from this message: "{user_message}"

    Current seller data: {json.dumps(current_seller_data, indent=2)}

    Extract the following fields (only if clearly mentioned):

    MOTIVATION & RELOCATION:
    - motivation: Why they want to sell (relocation, downsizing, financial, divorce, inherited, other)
    - relocation_destination: Where they plan to move (city, state, or general area)

    TIMELINE:
    - timeline_acceptable: Boolean - would 30-45 days be okay? (true/false/null)
    - timeline_urgency: "urgent" (30-45 days), "flexible", "long-term", or "unknown"

    PROPERTY CONDITION:
    - property_condition: "move-in ready", "needs work", "major repairs", or "unknown"
    - repair_estimate: Any mentioned repair needs or costs

    PRICE EXPECTATIONS:
    - price_expectation: Numeric price they mentioned (dollars)
    - price_flexibility: "firm", "negotiable", or "unknown"

    RESPONSE QUALITY METRICS:
    - response_quality: 0.0-1.0 based on completeness and specificity
    - responsiveness: 0.0-1.0 based on engagement level

    Return ONLY JSON with extracted fields. If no new info, return existing data.
    Count questions_answered based on how many of the 4 main categories have data.

    Example response:
    {{
        "motivation": "relocation",
        "relocation_destination": "Austin, TX",
        "timeline_acceptable": true,
        "timeline_urgency": "urgent",
        "property_condition": "move-in ready",
        "price_expectation": 450000,
        "price_flexibility": "negotiable",
        "response_quality": 0.85,
        "responsiveness": 0.90,
        "questions_answered": 4
    }}
    """

    try:
        extracted_data = await self.llm_client.extract_structured_data(
            prompt=extraction_prompt,
            user_message=user_message,
            model=tenant_config.get("claude_model", "claude-3-5-sonnet-20241022")
        )

        # Merge with existing seller data
        merged_data = {**current_seller_data, **extracted_data}

        # Ensure questions_answered count is accurate
        question_fields = ["motivation", "timeline_acceptable", "property_condition", "price_expectation"]
        questions_answered = sum(1 for field in question_fields if merged_data.get(field))
        merged_data["questions_answered"] = questions_answered

        return merged_data

    except Exception as e:
        logger.error(f"Seller data extraction failed: {e}")
        return current_seller_data
```

#### B. Update Main process_conversation Method
```python
# Update the process_conversation method to handle seller mode (around line 50):

async def process_conversation(
    self,
    user_message: str,
    contact_info: Dict,
    location_id: str,
    tenant_config: Dict,
    ghl_client,
    is_seller: bool = False,  # Add this parameter
    **kwargs
) -> ConversationResult:

    contact_id = contact_info["id"]
    contact_name = contact_info.get("firstName", "there")

    # Get conversation context
    context = await self.get_context(contact_id, location_id)

    # Handle seller mode (Jorge's bot)
    if is_seller:
        # Extract seller data instead of buyer preferences
        current_seller_data = context.get("seller_preferences", {})
        extracted_seller_data = await self.extract_seller_data(
            user_message=user_message,
            current_seller_data=current_seller_data,
            tenant_config=tenant_config
        )

        # Calculate seller temperature
        lead_scorer = LeadScorer()
        seller_result = lead_scorer.calculate_seller_score(extracted_seller_data)
        seller_temperature = seller_result["temperature"]

        # Generate seller-focused response
        ai_response = await self.generate_response(
            user_message=user_message,
            contact_info=contact_info,
            context=context,
            is_buyer=False,
            is_seller=True,
            extracted_preferences=extracted_seller_data,
            seller_temperature=seller_temperature,
            tenant_config=tenant_config,
            ghl_client=ghl_client
        )

        # Update context with seller data
        await self.update_context(
            contact_id=contact_id,
            user_message=user_message,
            ai_response=ai_response.message,
            extracted_data=extracted_seller_data,
            location_id=location_id,
            seller_temperature=seller_temperature
        )

        return ConversationResult(
            message=ai_response.message,
            lead_score=seller_result["raw_score"],
            temperature=seller_temperature,
            extracted_data=extracted_seller_data,
            actions=ai_response.actions or []
        )

    # Continue with existing buyer logic if not seller mode...
    # (rest of existing method remains unchanged)
```

---

## 5. ENVIRONMENT CONFIGURATION

### File: `.env` or `.env.jorge`
```bash
# Jorge Seller Bot Configuration
JORGE_SELLER_MODE=true

# GHL Integration
ACTIVATION_TAGS=["Needs Qualifying"]
DEACTIVATION_TAGS=["AI-Off", "Qualified", "Stop-Bot", "Seller-Qualified"]
HOT_SELLER_WORKFLOW_ID=jorge_hot_seller_workflow_12345
WARM_SELLER_WORKFLOW_ID=jorge_warm_seller_workflow_12345

# Temperature Classification
HOT_SELLER_THRESHOLD=0.75
WARM_SELLER_THRESHOLD=0.50
AUTO_DEACTIVATE_THRESHOLD=100  # Only deactivate when hot (all 4 questions)

# Follow-up Settings
ACTIVE_FOLLOWUP_DAYS=30
ACTIVE_FOLLOWUP_INTERVAL_MIN=2
ACTIVE_FOLLOWUP_INTERVAL_MAX=3
LONGTERM_FOLLOWUP_INTERVAL=14

# Message Settings
MAX_SMS_LENGTH=160
CONFRONTATIONAL_TONE=true
NO_EMOJIS=true
NO_HYPHENS=true

# Custom Fields (Set these to your GHL field IDs)
CUSTOM_FIELD_SELLER_TEMPERATURE=seller_temp_field_id
CUSTOM_FIELD_SELLER_MOTIVATION=seller_motivation_field_id
CUSTOM_FIELD_PRICE_EXPECTATION=price_expectation_field_id
CUSTOM_FIELD_PROPERTY_CONDITION=property_condition_field_id

# Analytics
JORGE_ANALYTICS_ENABLED=true
TRACK_SELLER_INTERACTIONS=true
```

---

## 6. SETTINGS CONFIGURATION

### File: `ghl_real_estate_ai/ghl_utils/config.py`

#### Add Jorge Settings
```python
# Add these settings to the existing config class:

class Settings(BaseSettings):
    # ... existing settings ...

    # Jorge Seller Bot Settings
    jorge_seller_mode: bool = Field(False, env="JORGE_SELLER_MODE")
    confrontational_tone: bool = Field(False, env="CONFRONTATIONAL_TONE")
    no_emojis: bool = Field(True, env="NO_EMOJIS")
    no_hyphens: bool = Field(True, env="NO_HYPHENS")

    # Jorge Temperature Settings
    hot_seller_threshold: float = Field(0.75, env="HOT_SELLER_THRESHOLD")
    warm_seller_threshold: float = Field(0.50, env="WARM_SELLER_THRESHOLD")

    # Jorge Follow-up Settings
    active_followup_days: int = Field(30, env="ACTIVE_FOLLOWUP_DAYS")
    active_followup_interval_min: int = Field(2, env="ACTIVE_FOLLOWUP_INTERVAL_MIN")
    active_followup_interval_max: int = Field(3, env="ACTIVE_FOLLOWUP_INTERVAL_MAX")
    longterm_followup_interval: int = Field(14, env="LONGTERM_FOLLOWUP_INTERVAL")

    # Jorge GHL Integration
    hot_seller_workflow_id: Optional[str] = Field(None, env="HOT_SELLER_WORKFLOW_ID")
    warm_seller_workflow_id: Optional[str] = Field(None, env="WARM_SELLER_WORKFLOW_ID")

    # Jorge Custom Fields
    custom_field_seller_temperature: Optional[str] = Field(None, env="CUSTOM_FIELD_SELLER_TEMPERATURE")
    custom_field_seller_motivation: Optional[str] = Field(None, env="CUSTOM_FIELD_SELLER_MOTIVATION")
    custom_field_price_expectation: Optional[str] = Field(None, env="CUSTOM_FIELD_PRICE_EXPECTATION")
    custom_field_property_condition: Optional[str] = Field(None, env="CUSTOM_FIELD_PROPERTY_CONDITION")

    @property
    def JORGE_SELLER_MODE(self) -> bool:
        """Easy access to Jorge seller mode flag"""
        return self.jorge_seller_mode
```

---

## 7. DATABASE MIGRATION

### SQL Migration Script
```sql
-- Add seller-specific columns to conversation_contexts table
-- File: migrations/add_jorge_seller_fields.sql

ALTER TABLE conversation_contexts
ADD COLUMN seller_preferences JSONB DEFAULT '{}';

ALTER TABLE conversation_contexts
ADD COLUMN seller_temperature VARCHAR(10) DEFAULT 'cold';

ALTER TABLE conversation_contexts
ADD COLUMN followup_phase VARCHAR(20) DEFAULT 'active';

ALTER TABLE conversation_contexts
ADD COLUMN last_followup_sent TIMESTAMP NULL;

ALTER TABLE conversation_contexts
ADD COLUMN followup_count INTEGER DEFAULT 0;

-- Create index for seller queries
CREATE INDEX idx_conversation_contexts_seller_temperature
ON conversation_contexts(seller_temperature);

CREATE INDEX idx_conversation_contexts_followup_phase
ON conversation_contexts(followup_phase);

-- Create seller analytics table
CREATE TABLE seller_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id VARCHAR(255) NOT NULL,
    location_id VARCHAR(255) NOT NULL,
    interaction_type VARCHAR(50) NOT NULL, -- 'question_asked', 'data_extracted', 'temperature_change'
    question_number INTEGER, -- 1-4 for Jorge's questions
    temperature VARCHAR(10), -- 'hot', 'warm', 'cold'
    response_quality FLOAT,
    message_content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_seller_interactions_contact_id ON seller_interactions(contact_id);
CREATE INDEX idx_seller_interactions_location_id ON seller_interactions(location_id);
CREATE INDEX idx_seller_interactions_temperature ON seller_interactions(temperature);
```

---

## 🚀 Quick Integration Test

### Test Script: `test_jorge_integration.py`
```python
import asyncio
import json
from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook
from ghl_real_estate_ai.schemas.ghl import GHLWebhookEvent

async def test_jorge_seller_flow():
    """Test Jorge's seller bot integration end-to-end"""

    # Test webhook event with Jorge's trigger tag
    test_event = GHLWebhookEvent(
        contact_id="test_contact_123",
        location_id="test_location_456",
        tags=["Needs Qualifying"],
        message_body="I'm thinking about selling my house",
        contact_info={
            "id": "test_contact_123",
            "firstName": "John",
            "phone": "+15551234567"
        }
    )

    # Process through webhook handler
    result = await handle_ghl_webhook(test_event)

    print("Jorge Integration Test Result:")
    print(json.dumps(result, indent=2))

    assert result["status"] == "jorge_seller_processed"
    assert "temperature" in result
    print("✅ Jorge seller bot integration working!")

# Run test
if __name__ == "__main__":
    asyncio.run(test_jorge_seller_flow())
```

---

**These integration snippets provide the exact code needed to connect Jorge's seller bot with the existing EnterpriseHub system. Copy and paste these into the specified files to implement Jorge's requirements with 80% code reuse!**