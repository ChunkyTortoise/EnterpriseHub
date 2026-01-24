# Jorge Skill Router - Discovery Phase (103 tokens)
*Progressive Skills Architecture - Always loaded for skill discovery*

## Purpose
Analyze seller interaction and determine which Jorge skill to load (single skill only for maximum efficiency).

## Analysis Context
- **Lead**: {{lead_name}}
- **Last Message**: "{{last_message}}"
- **Interaction Count**: {{interaction_count}}
- **Previous Stalls**: {{stall_history}}
- **Temperature**: {{seller_temperature}}

## Skill Selection Logic

### Priority 1: Stalling Patterns (jorge_stall_breaker)
**Load if detecting:**
- Keywords: "think", "not sure", "maybe", "consider", "decide", "uncertain"
- Phrases: "I'll get back to you", "need time", "have to discuss"
- Pattern: Vague responses to direct questions

### Priority 2: Disqualification Signals (jorge_disqualifier)
**Load if detecting:**
- Multiple previous stalls in conversation history
- "Just exploring", "shopping around", "seeing what's out there"
- Low commitment indicators (lukewarm, cold temperature)
- Won't provide property details or timeline

### Priority 3: Qualified Engagement (jorge_confrontational)
**Load if detecting:**
- Specific timeline mentioned
- Property details readily provided
- Direct answers to Jorge's questions
- Hot or warm temperature classification

### Priority 4: Competition/Value Questions (jorge_value_proposition)
**Load if detecting:**
- "Why should I choose you?"
- Mentions of other agents/competitors
- Questions about Jorge's qualifications/experience
- Comparison shopping indicators

## Jorge's Core Principle
**Default to confrontational qualification** - expose "Lookers", prioritize "Motivated Sellers"

## Output Format (Required)
```json
{
  "skill": "skill_name",
  "confidence": 0.8,
  "reasoning": "Brief explanation for skill choice",
  "detected_pattern": "pattern_type"
}
```

**Single skill only** - Jorge focuses conversations, never overwhelms with multiple approaches.