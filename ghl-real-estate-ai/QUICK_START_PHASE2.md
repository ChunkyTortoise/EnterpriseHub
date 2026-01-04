# Phase 2 Quick Start Guide

Get started with Phase 2 features in 5 minutes.

## 🚀 Quick Test Commands

### 1. Start the Server
```bash
cd ghl-real-estate-ai
uvicorn api.main:app --reload --port 8000
```

### 2. View API Documentation
Open browser: `http://localhost:8000/docs`

### 3. Test Analytics Dashboard
```bash
curl "http://localhost:8000/api/analytics/dashboard?location_id=demo_location&days=7"
```

### 4. Create an A/B Test
```bash
curl -X POST "http://localhost:8000/api/analytics/experiments?location_id=demo_location" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Opening Message Test",
    "variant_a": {"message": "Hi! Looking for a home?"},
    "variant_b": {"message": "Hey! Ready to find your dream home?"},
    "metric": "conversion_rate"
  }'
```

### 5. Test Bulk SMS (Demo)
```bash
curl -X POST "http://localhost:8000/api/bulk/sms/campaign?location_id=demo_location" \
  -H "Content-Type: application/json" \
  -d '{
    "contact_ids": ["contact1", "contact2"],
    "message": "New property alert! 123 Main St just listed."
  }'
```

### 6. Check Lead Health
```bash
curl "http://localhost:8000/api/lifecycle/health/demo_location/contact_123"
```

## 📊 Run All Tests
```bash
# Run Phase 2 tests only
pytest tests/test_advanced_analytics.py tests/test_campaign_analytics.py tests/test_lead_lifecycle.py -v

# All 63 tests should pass ✅
```

## 🎯 Common Use Cases

### Use Case 1: Import Leads from CSV
```bash
curl -X POST "http://localhost:8000/api/bulk/import/csv?location_id=demo_location&tags=Q1-Campaign,Imported" \
  -F "file=@leads.csv"
```

### Use Case 2: Find At-Risk Leads
```bash
curl "http://localhost:8000/api/lifecycle/health/demo_location/at-risk?threshold=0.3"
```

### Use Case 3: Get Campaign ROI
```bash
curl "http://localhost:8000/api/analytics/campaigns/demo_location?days=30"
```

### Use Case 4: Export Hot Leads
```bash
curl -X POST "http://localhost:8000/api/bulk/export/csv?location_id=demo_location" \
  -H "Content-Type: application/json" \
  -d '{"filters": {"tags": ["Hot-Lead"]}}' \
  --output hot_leads.csv
```

## 🔧 Integration Examples

### Python Integration
```python
import requests

BASE_URL = "http://localhost:8000/api"
LOCATION_ID = "your_location_id"

# Get dashboard metrics
response = requests.get(
    f"{BASE_URL}/analytics/dashboard",
    params={"location_id": LOCATION_ID, "days": 7}
)
metrics = response.json()
print(f"Hot Leads: {metrics['hot_leads']}")

# Create re-engagement campaign
response = requests.post(
    f"{BASE_URL}/lifecycle/reengage/campaign",
    params={"location_id": LOCATION_ID},
    json={
        "filters": {"days_inactive": 30},
        "template": "Hi {first_name}, still looking for a home?"
    }
)
campaign = response.json()
print(f"Campaign ID: {campaign['campaign_id']}")
```

### JavaScript Integration
```javascript
const BASE_URL = 'http://localhost:8000/api';
const LOCATION_ID = 'your_location_id';

// Get lifecycle metrics
async function getMetrics() {
  const response = await fetch(
    `${BASE_URL}/lifecycle/metrics/${LOCATION_ID}?days=30`
  );
  const metrics = await response.json();
  console.log('Conversion Rate:', metrics.conversion_rate);
}

// Start nurture sequence
async function startNurture(contactId) {
  const response = await fetch(
    `${BASE_URL}/lifecycle/nurture/start?location_id=${LOCATION_ID}&contact_id=${contactId}&sequence_type=warm_lead_nurture`,
    { method: 'POST' }
  );
  const result = await response.json();
  console.log('Sequence ID:', result.sequence_id);
}
```

## 📚 Next Steps

1. **Read the API Reference:** `PHASE2_API_REFERENCE.md`
2. **Review Handoff Document:** `SESSION_HANDOFF_2026-01-04_PHASE2_COMPLETE.md`
3. **Deploy to Railway:** Follow Railway deployment guide
4. **Set Environment Variables:**
   ```
   ANTHROPIC_API_KEY=your_key
   GHL_API_KEY=your_key
   ENVIRONMENT=production
   ```

## 💡 Tips

- All endpoints support multi-tenancy via `location_id`
- Bulk operations return `operation_id` for status tracking
- Use `/docs` endpoint for interactive API testing
- Phase 2 works alongside Phase 1 webhook seamlessly

## 🆘 Troubleshooting

**Issue:** Tests failing  
**Solution:** Run `pytest tests/test_advanced_analytics.py -v` to see specific failures

**Issue:** API not responding  
**Solution:** Check server is running: `curl http://localhost:8000/health`

**Issue:** Import failing  
**Solution:** Verify CSV format matches expected columns

---

**Need Help?** Check the full documentation or create an issue.
