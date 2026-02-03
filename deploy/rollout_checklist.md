# Jorge Bot Phased Rollout Checklist

## Phase 1: Seller Bot Only

### Pre-Deploy
- [ ] All 64 seller bot tests passing
- [ ] Compliance guard tests passing
- [ ] GHL API key valid and tested
- [ ] HOT_SELLER_WORKFLOW_ID configured in GHL and .env
- [ ] WARM_SELLER_WORKFLOW_ID configured in GHL and .env
- [ ] NOTIFY_AGENT_WORKFLOW_ID configured in GHL and .env
- [ ] Custom field IDs captured and set in .env
- [ ] Staging dry run completed successfully
- [ ] Webhook endpoint accessible from GHL

### Monitoring (First 7 Days)
- [ ] Seller compliance block rate < 1%
- [ ] Seller p99 response time < 2s
- [ ] Seller qualification completion rate > 50%
- [ ] No critical errors in logs
- [ ] Agent notifications triggering correctly for hot sellers
- [ ] Warm seller nurture sequences activating

---

## Phase 1 → Phase 2 Prerequisites

- [ ] Seller bot running for 7+ days without critical errors
- [ ] Seller compliance block rate < 1%
- [ ] Seller p99 response time < 2s
- [ ] Seller qualification completion rate > 50%
- [ ] All seller GHL workflow IDs verified working
- [ ] Buyer GHL workflow IDs configured and tested
- [ ] Buyer bot staging dry run passed
- [ ] All 50 buyer bot tests passing

---

## Phase 2: Seller + Buyer Bots

### Pre-Deploy
- [ ] Phase 1 prerequisites met
- [ ] HOT_BUYER_WORKFLOW_ID configured in GHL and .env
- [ ] WARM_BUYER_WORKFLOW_ID configured in GHL and .env
- [ ] Buyer custom field IDs set
- [ ] Buyer activation tag "Buyer-Lead" configured in GHL

### Monitoring (First 7 Days)
- [ ] Buyer compliance block rate < 1%
- [ ] Buyer p99 response time < 2s
- [ ] Buyer qualification rate tracking
- [ ] Property matching accuracy > 88%
- [ ] No interference between seller and buyer routing

---

## Phase 2 → Phase 3 Prerequisites

- [ ] Buyer bot running for 7+ days without critical errors
- [ ] Buyer compliance block rate < 1%
- [ ] Buyer p99 response time < 2s
- [ ] Handoff service verified (seller↔buyer)
- [ ] Lead bot staging dry run passed
- [ ] Lead routing priority verified (seller > buyer > lead)
- [ ] All 14 lead bot tests passing

---

## Phase 3: All Three Bots

### Pre-Deploy
- [ ] Phase 2 prerequisites met
- [ ] JORGE_LEAD_MODE=true
- [ ] Lead activation tag routing verified
- [ ] Lead compliance guard integrated

### Monitoring (First 7 Days)
- [ ] All three bots stable
- [ ] Cross-bot handoff working correctly
- [ ] No routing priority conflicts
- [ ] Overall p99 < 2s under mixed load

---

## Post-Phase 3 (Full Operation)

- [ ] All three bots stable for 7+ days
- [ ] Monitoring dashboard operational
- [ ] Alert thresholds configured (Slack/PagerDuty)
- [ ] A/B testing baseline metrics captured
- [ ] Documentation updated
- [ ] Enable ENABLE_MLS_INTEGRATION=true when Attom API key obtained
