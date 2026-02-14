# Buying Signal Detection Reference

Comprehensive guide to identifying and weighting buying signals in real estate conversations.

## Signal Categories

### 1. High-Intent Signals (Weight: 0.8-1.0)

#### Financial Readiness
- **Pre-approval mention**: "I'm pre-approved for $X"
- **Budget confirmation**: "We can go up to $X"
- **Down payment discussion**: "We have $X saved"
- **Financing questions**: "What's the interest rate looking like?"

#### Timeline Urgency
- **Lease expiration**: "Our lease ends in X months"
- **Life events**: "We're expecting a baby", "Just got married"
- **Job relocation**: "Starting new job in X weeks"
- **Must-move dates**: "Need to be settled by X"

#### Commitment Language
- **Possession questions**: "When could we move in?"
- **Exclusivity requests**: "Can you show us this before others?"
- **Offer inquiries**: "What would it take to secure this?"
- **Next steps**: "What's the process from here?"

### 2. Medium-Intent Signals (Weight: 0.5-0.7)

#### Active Engagement
- **Multiple property requests**: "Can you show me X, Y, and Z?"
- **Detailed questions**: "What's the HOA cover?", "School district ratings?"
- **Comparison inquiries**: "How does this compare to X?"
- **Return visits**: "Can we see that one again?"

#### Research Behavior
- **Market questions**: "How's the market in X area?"
- **Investment inquiries**: "What's the appreciation rate?"
- **Neighborhood deep-dive**: "What about the commute?", "Crime statistics?"
- **Future planning**: "How's the resale value?"

#### Emotional Investment
- **Vision language**: "I can see us living here"
- **Family planning**: "The kids would love this"
- **Lifestyle fit**: "This would be perfect for our needs"
- **Positive exclamations**: "This is exactly what we wanted!"

### 3. Low-Intent Signals (Weight: 0.2-0.4)

#### Early Stage
- **General inquiries**: "Just starting to look"
- **Educational questions**: "How does buying work?"
- **Timeline uncertainty**: "Maybe in the next year or so"
- **Broad criteria**: "Somewhere in the Rancho Cucamonga area"

#### Hesitation Indicators
- **Need to consult**: "I need to talk to my spouse"
- **Financial uncertainty**: "We're not sure about budget yet"
- **Timeline delays**: "Not in a rush"
- **Comparison shopping**: "Still looking at other areas"

## Signal Combinations

### Hot Lead Pattern (Score: 85-100)
```
+ Pre-approval confirmed
+ Timeline under 90 days
+ Specific property interest
+ Asking about offers/next steps
```

### Warm Lead Pattern (Score: 60-84)
```
+ Budget discussed
+ Timeline within 6 months
+ Engaged with multiple listings
+ Asking comparison questions
```

### Cold Lead Pattern (Score: 0-59)
```
- Vague timeline
- No budget discussed
- General/educational questions
- Infrequent responses
```

## Conversation Analysis Patterns

### Question Progression (Positive)
```
Early: "What areas do you cover?"
Middle: "What's available in Teravista?"
Late: "Can we see 123 Main St tomorrow?"
```

### Response Timing Signals
- **< 5 minutes**: High engagement (weight: 1.0)
- **< 1 hour**: Good engagement (weight: 0.8)
- **Same day**: Moderate engagement (weight: 0.6)
- **Next day**: Low engagement (weight: 0.4)
- **> 2 days**: Declining interest (weight: 0.2)

### Message Length Signals
- **Detailed responses**: High investment
- **Brief answers**: Moderate interest
- **Single word**: Possible declining interest
- **Questions back**: Active engagement

## Real Estate Specific Signals

### Buyer Type Indicators

#### First-Time Buyer Signals
- Process questions
- Nervousness about decisions
- Seeking guidance/hand-holding
- Budget sensitivity

#### Investor Signals
- ROI questions
- Rental income inquiries
- Multiple property interest
- Market timing focus

#### Luxury Buyer Signals
- Amenity focus
- Privacy concerns
- Quality over price
- Lifestyle integration

#### Relocation Signals
- Area unfamiliarity
- Timeline pressure
- Remote viewing requests
- Community questions

## Detection Algorithm

```python
def calculate_buying_signal_strength(signals: List[str], context: Dict) -> float:
    """
    Calculate aggregate buying signal strength.

    Args:
        signals: List of detected signal identifiers
        context: Lead context including timeline, budget, etc.

    Returns:
        Signal strength score 0-100
    """
    weights = {
        "pre_approval": 0.95,
        "timeline_urgent": 0.90,
        "offer_inquiry": 0.85,
        "budget_confirmed": 0.80,
        "specific_property": 0.75,
        "multiple_showings": 0.70,
        "detailed_questions": 0.65,
        "emotional_language": 0.60,
        "comparison_questions": 0.55,
        "general_inquiry": 0.30,
    }

    total_weight = sum(weights.get(s, 0.5) for s in signals)
    max_possible = len(signals) * 1.0

    base_score = (total_weight / max_possible) * 100 if max_possible > 0 else 0

    # Apply context multipliers
    if context.get("timeline_days", 365) < 90:
        base_score *= 1.15
    if context.get("pre_approved"):
        base_score *= 1.10
    if context.get("repeat_engagement"):
        base_score *= 1.05

    return min(base_score, 100)
```

## Integration with Jorge's Question Framework

### 7 Qualification Questions → Signal Mapping
1. **Budget** → Financial readiness signals
2. **Location** → Specificity indicators
3. **Bedrooms** → Family planning signals
4. **Timeline** → Urgency indicators
5. **Pre-approval** → Financial commitment signals
6. **Motivation** → Emotional investment signals
7. **Seller condition** → Investment sophistication signals

### Scoring Alignment
- **Hot (3+ answers)** → Signal strength 70-100
- **Warm (2 answers)** → Signal strength 40-69
- **Cold (0-1 answers)** → Signal strength 0-39
