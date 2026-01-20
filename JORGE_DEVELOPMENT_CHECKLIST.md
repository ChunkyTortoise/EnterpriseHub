# Jorge's Seller Bot - Development Checklist

## 🎯 Quick Reference
**Total Development Time**: ~20 hours
**Code Reuse**: 80% of existing EnterpriseHub components
**Jorge's Requirements**: 4 questions, confrontational tone, 2-3d→14d follow-up

---

## ✅ Phase 1: Foundation Adaptation (4 hours)

### Task 1.1: Create Jorge Seller Engine (2 hours)
- [ ] Create `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`
- [ ] Implement `SellerQuestions` class with Jorge's 4 questions
- [ ] Build `JorgeSellerEngine.process_seller_response()` method
- [ ] Integrate with existing `conversation_manager.py`
- [ ] Test basic question sequencing

**Key Pattern**:
```python
class SellerQuestions:
    MOTIVATION = "What's got you considering wanting to sell, where would you move to?"
    TIMELINE = "If our team sold your home within the next 30 to 45 days, would that pose a problem for you?"
    CONDITION = "How would you describe your home, would you say it's move-in ready or would it need some work?"
    PRICE = "What price would incentivize you to sell?"
```

### Task 1.2: Update System Prompts (1 hour)
- [ ] **Modify** `ghl_real_estate_ai/prompts/system_prompts.py:27-35`
- [ ] Replace 7 buyer questions with Jorge's 4 seller questions
- [ ] Add confrontational tone instructions
- [ ] Update SMS optimization (160 chars, no emojis, no hyphens)

**Critical Update**:
```python
# Replace lines 27-35 with:
SELLER_QUESTIONS = """
Ask these 4 questions in order (one at a time):
1. What's got you considering wanting to sell, where would you move to?
2. If our team sold your home within the next 30 to 45 days, would that pose a problem for you?
3. How would you describe your home, move-in ready or needs work?
4. What price would incentivize you to sell?

Be direct and confrontational. NO emojis. NO hyphens. Under 160 characters.
"""
```

### Task 1.3: Data Schema Updates (1 hour)
- [ ] Create `ghl_real_estate_ai/schemas/seller_data.py`
- [ ] Define `SellerProfile` dataclass with Jorge's fields
- [ ] Add database migration for seller fields
- [ ] **Modify** `conversation_manager.py:180-250` (data extraction)

**Key Schema**:
```python
@dataclass
class SellerProfile:
    motivation: Optional[str] = None
    relocation_destination: Optional[str] = None
    timeline_urgency: Optional[TimelineUrgency] = None
    timeline_acceptable: Optional[bool] = None
    property_condition: Optional[PropertyCondition] = None
    price_expectation: Optional[int] = None
    questions_answered: int = 0
```

**Success Criteria**: ✅ Jorge's 4 questions working ✅ Basic seller data extraction ✅ Database updated

---

## ✅ Phase 2: Temperature Classification (3 hours)

### Task 2.1: Adapt Lead Scorer (2 hours)
- [ ] **Modify** `ghl_real_estate_ai/services/lead_scorer.py`
- [ ] Change scoring from 0-7 (buyer) to 0-4 (seller)
- [ ] Implement Jorge's Hot/Warm/Cold logic:
  - Hot: 4 questions + 30-45 day timeline + high responsiveness
  - Warm: 3+ questions + flexible timeline + some hesitation
  - Cold: <3 questions + vague answers + long timeline

**Key Logic**:
```python
def calculate_seller_temperature(seller_data: SellerProfile) -> str:
    if (seller_data.questions_answered == 4 and
        seller_data.timeline_urgency == TimelineUrgency.URGENT_30_45_DAYS and
        seller_data.responsiveness > 0.7):
        return "hot"
    elif seller_data.questions_answered >= 3:
        return "warm"
    else:
        return "cold"
```

### Task 2.2: Tag Management Integration (1 hour)
- [ ] **Modify** `webhook.py:549-625` (tag application logic)
- [ ] Apply temperature tags: "Hot-Seller", "Warm-Seller", "Cold-Seller"
- [ ] Remove "Needs Qualifying" when qualified
- [ ] Trigger agent notification workflow for hot leads

**Success Criteria**: ✅ Accurate temperature classification ✅ Automatic tag application ✅ Hot lead notifications

---

## ✅ Phase 3: Confrontational Tone Engine (4 hours)

### Task 3.1: Build Tone Engine (2 hours)
- [ ] Create `ghl_real_estate_ai/services/jorge/jorge_tone_engine.py`
- [ ] Implement confrontational prompt templates
- [ ] Build response sanitization (no emojis, hyphens, 160 chars)
- [ ] Add evasive answer escalation logic

**Key Components**:
```python
CONFRONTATIONAL_PROMPTS = {
    "re_engagement": [
        "Are you actually serious about selling or just wasting our time?",
        "Should we close your file or are you still interested?",
        "Last chance, are you ready to get serious about selling?"
    ]
}
```

### Task 3.2: Update Claude System Prompts (1 hour)
- [ ] Add confrontational personality instructions to system prompts
- [ ] Implement direct questioning techniques
- [ ] Add evasive answer detection and escalation

### Task 3.3: Response Quality Assessment (1 hour)
- [ ] Build logic to detect vague/evasive answers (< 10 characters)
- [ ] Implement tone escalation for non-responsive leads
- [ ] Create quality scoring for temperature classification

**Success Criteria**: ✅ Direct confrontational responses ✅ SMS-optimized ✅ Appropriate tone escalation

---

## ✅ Phase 4: Follow-up Automation (5 hours)

### Task 4.1: Active Follow-up Engine (2 hours)
- [ ] Create `ghl_real_estate_ai/services/jorge/jorge_followup_engine.py`
- [ ] Implement 2-3 day intervals for first 30 days
- [ ] Build temperature-appropriate message templates
- [ ] Add re-engagement logic for silent leads

**Key Pattern**:
```python
ACTIVE_FOLLOWUP_DAYS = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29]  # Every 2-3 days
```

### Task 4.2: Long-term Nurture Engine (2 hours)
- [ ] Implement 14-day intervals after 30 days
- [ ] Create persistent but respectful follow-up messages
- [ ] Add opt-out detection and handling

### Task 4.3: Scheduling Integration (1 hour)
- [ ] Integrate with GHL workflow triggers
- [ ] Build background task management
- [ ] Add follow-up tracking and analytics

**Success Criteria**: ✅ Automated follow-up sequences ✅ Proper timing ✅ Lead re-engagement

---

## ✅ Phase 5: Integration & Testing (4 hours)

### Task 5.1: Integration Testing (2 hours)
- [ ] Test end-to-end webhook processing
- [ ] Verify tag management functionality
- [ ] Validate workflow trigger operations
- [ ] Confirm message delivery

### Task 5.2: Conversation Flow Testing (1 hour)
- [ ] Test all 4 question sequences
- [ ] Verify temperature classification accuracy
- [ ] Validate follow-up timing
- [ ] Check tone consistency

### Task 5.3: Edge Case Testing (1 hour)
- [ ] Test silent leads (no response)
- [ ] Test partial responses (incomplete answers)
- [ ] Test opt-out scenarios
- [ ] Validate system error handling

**Success Criteria**: ✅ Complete integration tested ✅ Edge cases handled ✅ Production ready

---

## 🔧 Critical Integration Points

### Files That MUST Be Modified
1. **`webhook.py:103-145`** - Add Jorge seller mode detection
2. **`system_prompts.py:27-35`** - Replace buyer questions with seller questions
3. **`lead_scorer.py`** - Adapt for 4 questions instead of 7
4. **`conversation_manager.py:180-250`** - Update data extraction for seller fields

### New Files to Create
1. **`jorge_seller_engine.py`** - Main processing logic
2. **`jorge_tone_engine.py`** - Confrontational tone generation
3. **`jorge_followup_engine.py`** - Follow-up automation
4. **`seller_data.py`** - Seller data schema
5. **`jorge_config.py`** - Jorge-specific configuration

---

## 🎯 Final Validation Checklist

### Jorge's Requirements ✅
- [ ] All 4 questions asked in correct order
- [ ] Confrontational tone ("direct, almost confrontational")
- [ ] No emojis, no hyphens in responses
- [ ] SMS under 160 characters
- [ ] Hot leads trigger agent notification immediately
- [ ] Follow-up timing: 2-3 days for 30 days → 14 days ongoing
- [ ] Proper opt-out handling

### Technical Requirements ✅
- [ ] 80%+ test coverage on new code
- [ ] <2 second webhook response times
- [ ] >90% classification accuracy (Jorge validation)
- [ ] Zero data loss (persistent conversation state)
- [ ] Security compliance (PII protection)
- [ ] SMS optimization (160 chars, no emojis, no hyphens)

### Business KPIs ✅
- [ ] Qualification completion rate: % completing all 4 questions
- [ ] Temperature distribution: Hot/Warm/Cold percentages
- [ ] Agent handoff rate: % advancing to call stage
- [ ] Follow-up engagement: Response rates by phase
- [ ] Opt-out rate: <5% requesting no contact

---

## 🚨 Quick Command Reference

```bash
# Setup development environment
chmod +x jorge_seller_bot_setup.sh
./jorge_seller_bot_setup.sh

# Run tests
pytest tests/jorge_seller/ --cov=ghl_real_estate_ai.services.jorge --cov-report=html

# Start development server
python -m streamlit run ghl_real_estate_ai/streamlit_demo/app.py

# Validate webhook
curl -X POST http://localhost:8000/webhook/ghl \
  -H "Content-Type: application/json" \
  -d '{"contact_id": "test", "tags": ["Needs Qualifying"]}'
```

**This checklist provides step-by-step guidance for completing Jorge's seller bot in ~20 hours with 80% code reuse!**