# The Scoring Model Behind Our Lead Qualification: FRS + PCS

**Architecture Decision Record | LinkedIn Article Draft**

---

Financial Readiness Score plus Psychological Commitment Score equals qualified leads with data, not gut feeling. We built a dual-axis scoring model that tells us not just whether a lead can buy, but whether they will. Here is how it works, how we calibrate it, and what we learned from 500 active leads.

## The Problem with Single-Score Systems

Most lead scoring systems produce one number. "This lead is a 73 out of 100." What does that mean? Are they financially ready but emotionally uncommitted? Are they emotionally ready but cannot afford to move? A single score hides the most actionable information.

We needed to know two things independently:

1. **Can this lead transact?** Do they have the finances, the timeline, and the property awareness to close a deal?
2. **Will this lead transact?** Are they psychologically committed to acting, or are they browsing?

A lead who scores high on both axes is hot. High on financial readiness but low on commitment needs nurturing. High on commitment but low on readiness needs education. Low on both is cold. Each quadrant demands a different strategy.

## What FRS Measures

The Financial Readiness Score (0-100) evaluates a lead's ability to transact based on four weighted dimensions:

| Dimension | Weight | What It Captures |
|-----------|--------|-----------------|
| **Motivation** | 35% | Why are they moving? Job relocation scores higher than "just curious." Divorce, growing family, downsizing -- each has a different urgency profile. |
| **Timeline** | 30% | When do they need to act? "This month" vs. "sometime next year" is the difference between a hot lead and a drip campaign. |
| **Condition Awareness** | 20% | Do they understand their property's state? Sellers who know their home needs a new roof are further along than those who say "it's perfect." Buyers who specify neighborhoods show readiness. |
| **Price Sensitivity** | 15% | Are they anchored to reality? A buyer who says "$200K for a 4-bed in Rancho Cucamonga" is not ready. One who says "$550K" knows the market. |

Each dimension is scored 0-100, then combined using the configured weights:

```python
frs = (
    motivation_score * weights.motivation     # 0.35
    + timeline_score * weights.timeline       # 0.30
    + condition_score * weights.condition      # 0.20
    + price_score * weights.price             # 0.15
)
```

**Example**: A lead says "I got pre-approved for $480K and need to move by April for a new job." That is high motivation (job relocation = 90), high timeline (2 months = 85), moderate condition awareness (no property specifics = 50), and good price anchoring (market-realistic = 80). FRS = 90*0.35 + 85*0.30 + 50*0.20 + 80*0.15 = 31.5 + 25.5 + 10 + 12 = **79**.

## What PCS Measures

The Psychological Commitment Score (0-100) evaluates behavioral signals that indicate a lead is ready to act, not just talk:

| Signal | Weight | What It Captures |
|--------|--------|-----------------|
| **Response Velocity** | 20% | How fast do they reply? A lead who responds in 30 seconds is engaged. One who takes 6 hours is passive. |
| **Message Length** | 15% | Longer messages with detail signal investment. "Yes" vs. "Yes, and we're also thinking about schools in the area." |
| **Question Depth** | 20% | Are they asking surface questions ("How's the market?") or transactional ones ("What's the HOA fee for that complex on Foothill?")? |
| **Objection Handling** | 25% | Do they raise objections and work through them, or do they raise objections and disengage? Working through objections is the strongest commitment signal. |
| **Call Acceptance** | 20% | Willingness to move from text to phone. A lead who accepts a call is 3x more likely to convert than one who stays on SMS. |

```python
pcs = (
    velocity_score * weights.response_velocity        # 0.20
    + length_score * weights.message_length            # 0.15
    + question_score * weights.question_depth          # 0.20
    + objection_score * weights.objection_handling     # 0.25
    + call_score * weights.call_acceptance             # 0.20
)
```

**Example**: A lead responds within 2 minutes (velocity = 80), writes 2-3 sentences per message (length = 65), asks about specific listings (questions = 75), pushes back on price but keeps engaging (objections = 85), and agrees to a Thursday call (call acceptance = 90). PCS = 80*0.20 + 65*0.15 + 75*0.20 + 85*0.25 + 90*0.20 = 16 + 9.75 + 15 + 21.25 + 18 = **80**.

## The Quadrant Model

Combining FRS and PCS creates four actionable categories:

```
                    High PCS (Committed)
                           │
              NURTURE      │      HOT
           (Needs help     │   (Ready to
            with finances) │    transact)
                           │
   Low FRS ────────────────┼──────────────── High FRS
                           │
              COLD         │    EDUCATE
           (Not ready,     │   (Financially
            not engaged)   │    able, not
                           │    motivated)
                           │
                    Low PCS (Browsing)
```

Each quadrant triggers different bot behavior:

| Quadrant | FRS | PCS | Bot Strategy |
|----------|-----|-----|-------------|
| **Hot** | >= 70 | >= 70 | Handoff to specialist, calendar booking, agent notification |
| **Nurture** | < 70 | >= 70 | Education on financing, pre-approval resources, check-ins |
| **Educate** | >= 70 | < 70 | Market updates, property alerts, engagement campaigns |
| **Cold** | < 70 | < 70 | Periodic content, long-term drip, reactivation triggers |

The temperature tags published to GoHighLevel CRM map directly to this model:

| Combined Score | Tag | GHL Workflow |
|---------------|-----|-------------|
| FRS + PCS >= 160 | **Hot-Lead** | Priority workflow, agent alert |
| FRS + PCS 80-159 | **Warm-Lead** | Nurture sequence, follow-up |
| FRS + PCS < 80 | **Cold-Lead** | Educational content, check-in |

## Weight Calibration

This is where it gets interesting. The initial weights were educated guesses. After 100+ conversion outcomes, we calibrate using actual data.

### Config-Driven Weights

All weights live in `jorge_bots.yaml` and can be changed without restarting the application:

```yaml
lead_bot:
  scoring:
    intent_weights:
      motivation: 0.35
      timeline: 0.30
      condition: 0.20
      price: 0.15

    pcs_weights:
      response_velocity: 0.20
      message_length: 0.15
      question_depth: 0.20
      objection_handling: 0.25
      call_acceptance: 0.20
```

### Hot Reload

When we update weights, no downtime:

```bash
# Edit weights
vim ghl_real_estate_ai/config/jorge_bots.yaml

# Reload (zero downtime)
python -c "from ghl_real_estate_ai.config.jorge_config_loader import reload_config; reload_config()"
```

Every active worker picks up the new weights on its next scoring call. No restart, no deployment, no interruption to active conversations.

### Conversion Tracking

Every lead outcome feeds back into the calibration dataset:

```python
decoder.record_conversion_outcome(
    contact_id="abc123",
    frs_score=85.5,
    pcs_score=72.3,
    lead_type="buyer",
    outcome="converted",  # or "nurturing", "lost", "qualified"
    channel="sms",
    segment="hot"
)
```

After 100 outcomes, we run logistic regression to find the weight combination that best predicts conversion. The process:

1. Query all recorded outcomes
2. Fit a model predicting `outcome = converted` from FRS/PCS component scores
3. Extract coefficients as new weights (normalized to sum to 1.0)
4. Compare predicted vs. actual conversion rates
5. If improvement > 5%, promote new weights to production

### A/B Testing Weights

We test weight changes in staging before promoting to production:

```yaml
environments:
  staging:
    lead_bot:
      scoring:
        intent_weights:
          motivation: 0.40  # Test: +5% motivation weight
          timeline: 0.28
          condition: 0.18
          price: 0.14
```

Run staging for two weeks, compare conversion rates, promote the winner.

### What Calibration Revealed

Our initial weights were close but not optimal. After calibration from 200+ outcomes:

| Dimension | Initial Weight | Calibrated Weight | Insight |
|-----------|---------------|-------------------|---------|
| Motivation | 0.35 | 0.38 | Motivation matters more than we thought |
| Timeline | 0.30 | 0.32 | Urgency is the second-strongest predictor |
| Condition | 0.20 | 0.18 | Less predictive than expected |
| Price | 0.15 | 0.12 | Price awareness is a weak signal |

The big surprise was **objection handling** in PCS. Leads who raise objections and work through them convert at **2.4x** the rate of leads who never object. Our initial weight of 0.25 was almost right -- calibration moved it to 0.27.

## Results After 90 Days

| Metric | Single-Score System | FRS + PCS Model | Change |
|--------|--------------------|--------------------|--------|
| **Correct temperature classification** | 62% | 87% | +40% |
| **Lead-to-appointment rate** | 2.8% | 4.5% | +61% |
| **Agent time per lead** | 18 min | 8 min | -56% |
| **Misrouted handoffs** | 24% | 9% | -63% |
| **Hot lead response time** | 12 min | 45 sec | -94% |

The agent time reduction is critical for our client. With a single-score system, the human agent had to manually assess every lead. With FRS + PCS, the bot pre-qualifies and the agent only spends time on leads that are both financially ready and psychologically committed.

The 45-second hot lead response time is possible because the system automatically triggers a priority workflow in GoHighLevel when a lead crosses the Hot threshold. The agent gets a notification with the full scoring breakdown before the lead has finished typing their next message.

## Constraints and Guardrails

**Weights must sum to 1.0** (with 0.01 tolerance). The config loader validates on startup and rejects invalid configurations with an explicit error. No silent degradation.

**Minimum calibration sample: 100 outcomes.** We do not adjust weights based on small samples. Statistical noise in 20 outcomes could produce terrible weights. The minimum is configurable via `min_samples_for_calibration`.

**No negative weights.** Every dimension contributes positively to readiness or commitment. A negative weight would mean "the more motivated a lead is, the less ready they are," which makes no business sense. The calibration pipeline enforces this constraint.

**Score clamping.** Both FRS and PCS are clamped to 0-100 via a utility function. No edge case produces a score of -5 or 137.

## What I Would Do Differently

**Add a third axis: urgency.** FRS captures timeline as one of four dimensions, but temporal urgency deserves its own score. A lead relocating in 2 weeks needs different treatment than one moving in 6 months, even if both score 80 on FRS.

**Weight PCS higher for sellers.** Selling a home is an emotional decision. Our data shows PCS is a stronger predictor of seller conversion than FRS. For buyers, the reverse is true. We are exploring bot-specific weight profiles.

**Track score trajectories, not snapshots.** A lead whose FRS went from 30 to 70 over five conversations is more valuable than one who started at 70 and stayed flat. We are adding velocity scoring to the next version.

---

Building lead qualification systems? I specialize in AI-powered scoring models, multi-bot CRM platforms, and production ML systems. If you are working on lead intelligence, I would love to compare approaches.

[Portfolio](https://github.com/rovo-dev) | DM me on LinkedIn
