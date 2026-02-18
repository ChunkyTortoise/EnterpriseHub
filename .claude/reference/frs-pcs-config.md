# FRS/PCS Weight Calibration

**Config file**: `ghl_real_estate_ai/config/jorge_bots.yaml`

## Current Weights

```yaml
lead_bot:
  scoring:
    intent_weights:          # FRS
      motivation: 0.35
      timeline: 0.30
      condition: 0.20
      price: 0.15
    pcs_weights:             # PCS
      response_velocity: 0.20
      message_length: 0.15
      question_depth: 0.20
      objection_handling: 0.25
      call_acceptance: 0.20

environments:
  production:
    lead_bot:
      scoring:
        intent_weights:      # Tuned from conversion data
          motivation: 0.38
          timeline: 0.32
          condition: 0.18
          price: 0.12
```

## Hot Reload (Zero Downtime)

```bash
python -c "from ghl_real_estate_ai.config.jorge_config_loader import reload_config; reload_config()"
python -c "from ghl_real_estate_ai.config.jorge_config_loader import get_config; print(get_config().lead_bot.scoring.intent_weights)"
```

## Conversion Tracking

```python
decoder.record_conversion_outcome(
    contact_id="abc123", frs_score=85.5, pcs_score=72.3,
    lead_type="buyer", outcome="converted",  # or "nurturing", "lost", "qualified"
    channel="sms", segment="hot"
)
```

## Calibration

- Trigger: 100+ conversion outcomes (`min_samples_for_calibration`)
- Method: Logistic regression on outcomes → update production weights → hot reload
- Constraint: All weights must sum to 1.0 (±0.01), validated on startup

## A/B Testing Weights

Use `environments.staging.lead_bot.scoring.intent_weights` to test variants.
Monitor conversion rates in staging vs production before promoting.
