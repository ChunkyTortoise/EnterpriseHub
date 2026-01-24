
# GoHighLevel Unified Integration Guide

## 🎯 Complete Setup for Enhanced Jorge Bot Platform

### Components Integration:
1. **Enhanced Seller Bot FastAPI** (Port 8002)
2. **Enhanced Lead Bot FastAPI** (Port 8001)
3. **Unified Command Center Dashboard** (Port 8501)
4. **Performance Monitoring** (Port 8503)

### 1. Webhook Configuration

#### Primary Webhooks:
- Lead Bot: `https://your-domain.com:8001/webhook/ghl`
- Seller Bot: `https://your-domain.com:8002/webhook/ghl`

#### Events to Subscribe:
- contact.created
- contact.updated
- message.received
- conversation.new
- appointment.scheduled

### 2. Required Custom Fields

Navigate to: Settings → Custom Fields → Contact Fields

**Lead Bot Fields:**
- ai_lead_score (Number, 0-100)
- lead_temperature (Dropdown: Hot, Warm, Cold)
- jorge_priority (Dropdown: high, normal, review_required)

**Seller Bot Fields:**
- seller_qualification_stage (Number, 1-4)
- seller_motivation_score (Number, 0-100)
- seller_timeline_urgency (Dropdown: immediate, 30_days, 60_days, flexible)
- seller_confrontation_response (Text)

**Business Fields:**
- estimated_commission (Number)
- meets_jorge_criteria (Checkbox)
- last_ai_analysis (Date/Time)

### 3. Automation Workflows

#### High Priority Lead → Seller Transition:
- Trigger: Lead score > 90 AND tagged "Priority-High"
- Actions:
  * Move to Seller Bot pipeline
  * Assign to Jorge immediately
  * Send internal notification
  * Schedule qualification call

#### Seller Qualification Complete:
- Trigger: seller_qualification_stage = 4
- Actions:
  * Calculate estimated commission
  * Create listing appointment task
  * Send contract preparation checklist

### 4. Performance Monitoring Integration

Set up webhook events to track:
- Response times for 5-minute rule compliance
- Lead-to-seller conversion rates
- Jorge's business metrics
- Commission pipeline value

### 5. Testing Commands

```bash
# Test Lead Bot webhook
curl -X POST https://your-domain.com:8001/webhook/ghl \
  -H "Content-Type: application/json" \
  -d '{"type": "contact.created", "contact_id": "test_lead_001"}'

# Test Seller Bot webhook
curl -X POST https://your-domain.com:8002/webhook/ghl \
  -H "Content-Type: application/json" \
  -d '{"type": "message.received", "message": "I want to sell my house"}'
```

## 🚀 Go Live Checklist

- [ ] All webhook URLs updated to production domain
- [ ] Custom fields created in GHL
- [ ] Automation workflows configured
- [ ] Test webhooks successful
- [ ] Performance monitoring active
- [ ] Jorge's business rules validated

## 📊 Success Metrics (24hr target)

- Response time: <500ms average
- 5-minute rule: >99% compliance
- Lead qualification: >80% automated
- Seller qualification: >75% to stage 4
- Estimated commissions: $25,000+ pipeline

