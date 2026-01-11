# PHASE 2: Performance Foundation - Core Optimization

## Context
You are implementing Phase 2 of the EnterpriseHub optimization roadmap. Agent analysis identified specific performance bottlenecks and optimization opportunities that can deliver 25-35% infrastructure cost reduction while achieving <200ms API responses and <500ms ML inference targets.

## Your Mission
Implement core performance optimizations across caching, database, API connections, and ML inference to establish the performance foundation for high-value features.

**Timeline:** Weeks 3-4 | **Priority:** HIGH | **Value:** $145K/year infrastructure savings + user experience

## Performance Optimization Tasks

### ⚡ Quick Wins (8 hours - Week 3)
**Files to modify:**
- `/ghl_real_estate_ai/services/advanced_cache_optimization.py` (Line 182)
- `/ghl_real_estate_ai/services/database_optimization.py` (Lines 404-432)
- `/ghl_real_estate_ai/services/enhanced_api_performance.py` (Lines 742-785)

**Specific Actions:**
1. **L1 Cache Optimization:**
   ```python
   # advanced_cache_optimization.py Line 182
   l1_max_size: 5000 → 50000  # 10x increase for 90%+ hit rate
   ```

2. **Connection Pool Tuning:**
   ```python
   # database_optimization.py
   master_pool_size: 20 → 50
   replica_pool_size: 30 → 100

   # enhanced_api_performance.py
   GHL max_concurrent: 5 → 20
   OpenAI max_concurrent: 10 → 50
   Real Estate max_concurrent: 15 → 30
   ```

3. **Database Query Optimization:**
   ```sql
   -- Add performance indexes
   CREATE INDEX CONCURRENTLY idx_leads_created_scored
     ON leads(created_at DESC, ml_score DESC) WHERE status = 'active';
   CREATE INDEX CONCURRENTLY idx_properties_location_price
     ON properties USING GiST (location, price_range);
   ```

### 🤖 ML Inference Optimization (1 week - Week 4)
**Files to modify:**
- `/ghl_real_estate_ai/services/optimization/production_performance_optimizer.py` (Lines 315-337)
- `/scripts/enhanced_ml_performance_benchmarks.py`

**Specific Actions:**
1. **Model Quantization (INT8):**
   - Implement FP32 → INT8 conversion for neural networks
   - Expected: 60% inference time reduction, 40% cost reduction
   - Target: <500ms per prediction (from current ~400-450ms)

2. **Batch Processing Implementation:**
   - Collect requests for 10-50ms windows
   - Process 10-50 predictions simultaneously
   - Expected: 5-10x throughput improvement

3. **Model Pre-loading Strategy:**
   - Warm up top 10 models during startup
   - Implement prediction-based pre-loading
   - Add GPU acceleration path for neural networks

4. **Caching Enhancement:**
   - Cache model predictions for 5 minutes (Redis)
   - Implement aggressive eviction of cold data
   - Add compression for large model outputs

## Success Criteria
- [ ] API response time: <200ms P95 (maintain current 145ms)
- [ ] ML inference: <500ms per prediction
- [ ] Database queries: <50ms P90 with new indexes
- [ ] Cache hit rate: >95% (L1+L2+L3 combined)
- [ ] Connection pool efficiency: >90%
- [ ] Infrastructure cost reduction: 25-35%
- [ ] Throughput: 5-10x improvement for ML inference

## Skills to Leverage
```bash
invoke cost-optimization-analyzer --scope="ml-services,ghl-api-costs"
invoke workflow-automation-builder --ci-cd="performance-testing"
invoke systematic-debugging --performance-bottlenecks
```

## Performance Benchmarking
**Before/After Validation Required:**
- Load test with 100+ concurrent users
- ML inference batch vs individual timing
- Database connection pool stress testing
- Cache performance under load
- Cost tracking for 30-day baseline

## Expected Deliverables
1. Optimized caching layer (50,000 L1 items, 95%+ hit rate)
2. Enhanced database performance (<50ms P90 queries)
3. ML inference optimization (<500ms target achieved)
4. API connection optimization (proper pool sizing)
5. Performance benchmarking suite
6. Cost optimization documentation ($145K/year savings validated)