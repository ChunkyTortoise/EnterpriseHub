# Extractable Code Index - Jorge Deployment Package

**Quick reference for code extraction and integration**

---

## 🔴 Priority 0: CRITICAL (Extract First)

### 1. jorge_claude_intelligence.py (722 lines)
**Path**: `~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/jorge_claude_intelligence.py`

**What it does**:
- High-performance lead analysis with <500ms target
- Dual-layer caching (memory + file) for <100ms responses
- Hybrid pattern-matching + Claude AI approach
- Jorge business rules validation
- 5-minute rule enforcement
- Performance metrics tracking

**Key Classes**:
- `PerformanceCache` - Dual-layer caching system
- `JorgeBusinessRules` - Business validation ($200K-$800K, service areas)
- `ClaudeLeadIntelligence` - Main AI intelligence engine
- `PerformanceMetrics` - Performance tracking dataclass

**Extract to**: `bots/shared/` and `bots/lead_bot/services/`

**Integration effort**: Medium (2-3 hours)
**Value**: ⭐⭐⭐⭐⭐ CRITICAL

---

### 2. jorge_kpi_dashboard.py (482 lines)
**Path**: `~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/jorge_kpi_dashboard.py`

**What it does**:
- Real-time KPI dashboard with 7 major sections
- Lead conversion funnel visualization
- 30-day conversion trends
- Response time analytics
- Temperature distribution charts
- Hot leads alert system
- Export capabilities (CSV, PDF)

**Dashboard Sections**:
1. Key Metrics Cards (5 metrics with deltas)
2. Lead Conversion Funnel
3. Conversion Trends (30-day graph)
4. Bot Response Performance
5. Lead Temperature Distribution
6. Recent Activity Log
7. Hot Leads Alerts

**Extract to**: `command_center/dashboard.py`

**Integration effort**: Low (1 hour)
**Value**: ⭐⭐⭐⭐⭐ CRITICAL

---

### 3. jorge_fastapi_lead_bot.py (618 lines)
**Path**: `~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/jorge_fastapi_lead_bot.py`

**What it does**:
- FastAPI microservice with performance monitoring
- 5-minute rule violation alerts
- CORS configuration
- Pydantic request/response validation
- Background task processing
- Comprehensive health checks
- Multiple testing endpoints

**Key Features**:
- Performance monitoring middleware
- 5-minute rule enforcement logging
- Pydantic models: LeadMessage, GHLWebhook, LeadAnalysisResponse
- Async processing throughout
- X-Process-Time headers

**Endpoints**:
- POST /webhook/ghl-contact
- POST /webhook/ghl-sms
- POST /analyze-lead
- POST /test/analyze
- GET /health
- GET /performance

**Extract to**: Merge with `bots/lead_bot/main.py`

**Integration effort**: Medium (2-3 hours)
**Value**: ⭐⭐⭐⭐⭐ CRITICAL

---

## 🟡 Priority 1: HIGH VALUE (Extract Second)

### 4. lead_intelligence_optimized.py (980+ lines)
**Path**: `~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/lead_intelligence_optimized.py`

**What it does**:
- Pattern-based lead scoring (no AI needed)
- Budget detection with regex patterns
- Timeline extraction
- Location matching
- Motivation analysis
- Fast fallback when Claude unavailable

**Key Classes**:
- `PredictiveLeadScorerV2Optimized` - Main pattern scorer
- Budget detection patterns
- Timeline extraction logic
- Location matching algorithms

**Extract to**: `bots/shared/pattern_intelligence.py`

**Integration effort**: Medium (2-3 hours)
**Value**: ⭐⭐⭐⭐ HIGH (reduces API costs)

---

### 5. jorge_seller_bot.py (543 lines)
**Path**: `~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/jorge_seller_bot.py`

**What it does**:
- Seller qualification with Q1-Q4 framework
- State machine conversation flow
- Timeline/Motivation/Condition/Strategy questions
- Intelligent question sequencing
- CMA trigger conditions

**Q1-Q4 Framework**:
- Q1: Timeline (urgency assessment)
- Q2: Motivation (why selling)
- Q3: Condition (property state)
- Q4: Strategy (pricing/flexibility)

**Extract to**: `bots/seller_bot/main.py`

**Integration effort**: Medium (3-4 hours)
**Value**: ⭐⭐⭐⭐ HIGH

---

### 6. ghl_client.py (347 lines)
**Path**: `~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/ghl_client.py`

**What it does**:
- Complete GoHighLevel API wrapper
- Contact management (CRUD)
- Custom field updates
- SMS/Email sending
- Opportunity management
- Rate limiting handling
- Error handling and retries

**Key Methods**:
- get_contact()
- create_contact()
- update_contact()
- send_sms()
- send_email()
- create_opportunity()
- update_custom_fields()

**Extract to**: Replace `bots/shared/ghl_client.py`

**Integration effort**: Low (1 hour)
**Value**: ⭐⭐⭐⭐ HIGH

---

## 🟢 Priority 2: NICE TO HAVE (Extract Later)

### 7. jorge_ml_data_collector.py (567 lines)
**Path**: `~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/jorge_ml_data_collector.py`

**What it does**:
- Conversation data collection for ML
- Lead scoring feedback tracking
- Feature engineering for ML models
- Data validation and cleaning
- Automatic data export

**Extract to**: `bots/shared/ml/data_collector.py`

**Integration effort**: High (4-5 hours)
**Value**: ⭐⭐⭐ MEDIUM (future ML capability)

---

### 8. jorge_ml_model_trainer.py (572 lines)
**Path**: `~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/jorge_ml_model_trainer.py`

**What it does**:
- ML model training pipeline
- Lead scoring model training
- Accuracy validation
- Model versioning
- Automatic model updates

**Extract to**: `bots/shared/ml/model_trainer.py`

**Integration effort**: High (4-5 hours)
**Value**: ⭐⭐⭐ MEDIUM (continuous improvement)

---

### 9. war_room_dashboard.py
**Path**: `~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/war_room_dashboard.py`

**What it does**:
- Real-time multi-location monitoring
- Alert system for critical issues
- Agent performance tracking
- System health monitoring
- Multi-agent coordination

**Extract to**: `command_center/war_room.py`

**Integration effort**: Medium (3-4 hours)
**Value**: ⭐⭐⭐ MEDIUM (for multi-agent ops)

---

### 10. conversation_manager.py (256 lines)
**Path**: `~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/conversation_manager.py`

**What it does**:
- Conversation state tracking
- Context management
- Message history storage
- Multi-turn conversation support

**Extract to**: `bots/shared/conversation_manager.py`

**Integration effort**: Low (1-2 hours)
**Value**: ⭐⭐⭐ MEDIUM

---

### 11. config_settings.py (122 lines)
**Path**: `~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/config_settings.py`

**What it does**:
- Centralized configuration management
- Environment variable management
- API key retrieval functions
- Settings validation

**NOTE**: Has import error - `get_claude_key()` should be `get_claude_api_key()`

**Extract to**: Reference for `bots/shared/config.py` improvements

**Integration effort**: Low (30 min)
**Value**: ⭐⭐⭐ MEDIUM

---

## 🔵 Supporting Files (Reference Only)

### 12. jorge_automation.py
- Automation workflows
- Task scheduling
- Batch processing

### 13. jorge_engines.py
- Legacy engine implementations
- Can skip (optimized version exists)

### 14. jorge_engines_optimized.py
- Optimized processing engines
- May have useful patterns

### 15. Test Files (Multiple)
- test_bot_optimization.py
- test_performance_validation.py
- test_jorge_lead_bot.py
- test_live_apis.py

**Value**: Reference for testing patterns

---

## Quick Extraction Commands

### Extract Core Files (Phase 1)
```bash
cd ~/Documents/GitHub/jorge_real_estate_bots

# Read files first
cat ~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/jorge_claude_intelligence.py
cat ~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/jorge_kpi_dashboard.py
cat ~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/jorge_fastapi_lead_bot.py

# Copy for reference (don't overwrite directly)
cp ~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/jorge_claude_intelligence.py \
   /tmp/ref_claude_intelligence.py

cp ~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/jorge_kpi_dashboard.py \
   /tmp/ref_kpi_dashboard.py

cp ~/Documents/GitHub/EnterpriseHub/jorge_deployment_package/jorge_fastapi_lead_bot.py \
   /tmp/ref_fastapi_server.py

# Then manually integrate - DO NOT JUST COPY/PASTE
```

---

## Integration Checklist

### Before Extracting Each File:
- [ ] Read entire file to understand functionality
- [ ] Identify dependencies and imports
- [ ] Note any environment variables or config needed
- [ ] Check for conflicts with existing code
- [ ] Plan where each class/function should go

### During Extraction:
- [ ] Extract incrementally (one class at a time)
- [ ] Update imports to match target project structure
- [ ] Maintain code style consistency
- [ ] Add comments explaining changes
- [ ] Keep git commits small and focused

### After Extraction:
- [ ] Test extracted functionality independently
- [ ] Run existing tests to ensure no breakage
- [ ] Add new tests for new functionality
- [ ] Update documentation
- [ ] Verify performance metrics

---

## Dependency Notes

### Additional Packages Needed:
```txt
# For KPI Dashboard
plotly>=5.0.0
pandas>=2.0.0
numpy>=1.24.0
streamlit>=1.31.0

# For ML Features (if extracting)
scikit-learn>=1.3.0
joblib>=1.3.0

# Already in MVP
fastapi
uvicorn
anthropic
redis
pydantic
```

---

## File Size Reference

| File | Lines | Complexity | Extract Time |
|------|-------|-----------|--------------|
| jorge_claude_intelligence.py | 722 | High | 2-3h |
| jorge_kpi_dashboard.py | 482 | Medium | 1h |
| jorge_fastapi_lead_bot.py | 618 | High | 2-3h |
| lead_intelligence_optimized.py | 980+ | High | 2-3h |
| jorge_seller_bot.py | 543 | Medium | 3-4h |
| ghl_client.py | 347 | Low | 1h |
| jorge_ml_data_collector.py | 567 | High | 4-5h |
| jorge_ml_model_trainer.py | 572 | High | 4-5h |
| conversation_manager.py | 256 | Low | 1-2h |
| config_settings.py | 122 | Low | 30m |

**Total Phase 1**: ~8 hours
**Total Phase 2**: ~9 hours
**Total Phase 3**: ~14 hours
**Grand Total**: ~31 hours (4-5 days)

---

## Success Metrics

### After Phase 1 (Core Features):
- ✅ <100ms cache hit responses
- ✅ <500ms AI analysis
- ✅ Dashboard with 7 sections working
- ✅ 5-minute rule enforcement
- ✅ Performance metrics tracking

### After Phase 2 (Advanced Features):
- ✅ Pattern-based fallback working
- ✅ Seller Bot Q1-Q4 framework
- ✅ Complete GHL API integration

### After Phase 3 (ML & Monitoring):
- ✅ ML data collection active
- ✅ Model training pipeline
- ✅ War Room dashboard
- ✅ Multi-agent monitoring

---

**Index Created**: 2026-01-23 by Claude Code
**Total Files Analyzed**: 30+ Python files
**Priority Files**: 11 identified with extraction plans
**Estimated Total Integration Time**: 31 hours (4-5 days)

**Next Step**: Start with Priority 0 files (jorge_claude_intelligence.py, jorge_kpi_dashboard.py, jorge_fastapi_lead_bot.py)
