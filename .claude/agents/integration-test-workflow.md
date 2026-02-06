# Agent Integration Test Workflow

**Purpose**: Demonstrate multi-agent coordination for real estate AI enhancement
**Test Scenario**: Property Matcher Service Enhancement
**Version**: 2.0.0

## Test Scenario Overview

We'll enhance the existing Property Matcher AI service with a new scoring algorithm, demonstrating how agents coordinate:

1. **Architecture Sentinel** - Analyzes current code and recommends patterns
2. **Database Migration** - Validates schema changes for new scoring data
3. **ML Pipeline** - Evaluates scoring model quality and feature engineering
4. **API Consistency** - Ensures new endpoints follow standards

## Current State Analysis

Based on your existing codebase structure:
```
ghl_real_estate_ai/
├── streamlit_demo/components/property_matcher_ai.py
├── streamlit_demo/components/property_cards.py
├── services/advanced_property_matching_engine.py
├── services/predictive_analytics_engine.py
└── agents/property_intelligence_agent.py
```

## Workflow Execution

### **Phase 1: Architecture Analysis**
```
ARCHITECTURE SENTINEL ACTIVATION

Input: "Enhance property matching with ML-based scoring"

Expected Analysis:
1. Review existing property_matcher_ai.py implementation
2. Identify current patterns and architecture
3. Recommend Strategy pattern for scoring algorithms
4. Suggest Repository pattern for property data access
5. Flag potential performance improvements

Output: Architecture recommendations with specific refactoring steps
```

### **Phase 2: Schema Validation**
```
DATABASE MIGRATION ACTIVATION

Input: Architecture recommendations requiring new data storage

Expected Actions:
1. Review existing property and scoring models
2. Propose Alembic migration for new scoring columns/tables
3. Validate index strategy for scoring queries (<50ms target)
4. Ensure pgvector dimensions match embedding model
5. Generate reversible migration with downgrade

Output: Reviewed migration file ready for application
```

### **Phase 3: ML Model Validation**
```
ML PIPELINE ACTIVATION

Input: New scoring algorithm implementation

Expected Actions:
1. Evaluate feature engineering for property scoring
2. Validate score range (0-100) and calibration
3. Check for data leakage in training features
4. Benchmark accuracy against rule-based baseline
5. Verify inference latency (<25ms target)

Output: Model quality report with metrics
```

### **Phase 4: API Integration**
```
API CONSISTENCY ACTIVATION

Input: New property scoring endpoints

Expected Actions:
1. Validate URL naming conventions (plural nouns, snake_case)
2. Verify response envelope format (success/data/meta)
3. Check auth decorators and rate limiting
4. Ensure pagination on list endpoints
5. Validate OpenAPI metadata

Output: Compliance report for new endpoints
```

### **Phase 5: Test-Driven Implementation**
```
CLAUDE CODE (Enhanced by Agents)

Input: Architecture plan + migration + model validation

Actions:
1. Write failing tests for new scoring algorithm
2. Implement minimal code to pass tests
3. Apply Architecture Sentinel's pattern recommendations
4. Run ML Pipeline validation on results
5. Verify API Consistency compliance
6. Refactor for clean architecture

Output: Production-ready enhancement with full test coverage
```

## Practical Test Implementation

### **Step 1: Test Suite Creation**
```python
# test_property_scoring_strategy.py

import pytest
from unittest.mock import Mock, patch
from ghl_real_estate_ai.services.property_scorer import (
    PropertyScorer,
    MLBasedScoringStrategy,
    RuleBasedScoringStrategy
)

class TestPropertyScoringStrategy:
    """
    TDD-first test suite for property scoring enhancement.
    Following RED-GREEN-REFACTOR discipline.
    """

    def test_should_score_property_when_perfect_match(self):
        """RED PHASE: This test should fail initially"""
        property_data = {
            'price': 500000,
            'bedrooms': 3,
            'bathrooms': 2,
            'location': 'Rancho Cucamonga, CA',
            'square_feet': 2000
        }
        user_criteria = {
            'max_price': 550000,
            'min_bedrooms': 3,
            'min_bathrooms': 2,
            'preferred_location': 'Rancho Cucamonga, CA',
            'min_square_feet': 1800
        }
        scorer = PropertyScorer(strategy=MLBasedScoringStrategy())

        score = scorer.score_property(property_data, user_criteria)

        assert score >= 90
        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_should_use_different_strategies_when_specified(self):
        """Test strategy pattern implementation"""
        property_data = {'price': 400000, 'bedrooms': 2}
        criteria = {'max_price': 450000, 'min_bedrooms': 2}

        ml_scorer = PropertyScorer(strategy=MLBasedScoringStrategy())
        rule_scorer = PropertyScorer(strategy=RuleBasedScoringStrategy())

        ml_score = ml_scorer.score_property(property_data, criteria)
        rule_score = rule_scorer.score_property(property_data, criteria)

        assert isinstance(ml_score, float)
        assert isinstance(rule_score, float)
```

### **Step 2: Migration Validation**
```python
# Alembic migration review checklist
# Database Migration agent validates:
assert migration.has_downgrade()        # Reversible
assert migration.no_table_locks(">5s")  # Non-blocking
assert migration.indexes_on_fks()       # Performance
assert migration.handles_existing_data() # Data safety
```

## Expected Agent Interactions

### **Message Flow**
```
Architecture Sentinel
    ├──► Database Migration: "New scoring tables needed"
    ├──► ML Pipeline: "Validate scoring algorithm quality"
    └──► API Consistency: "Review new /api/v1/properties/scores endpoint"

Database Migration
    └──► Performance Optimizer: "Verify query plans for new indexes"

ML Pipeline
    └──► Cost Token Optimization: "Evaluate ML vs LLM cost for scoring"

API Consistency
    └──► Security Auditor: "Verify auth on new endpoints"
```

## Integration Verification

### **Success Criteria**
1. **Architecture Sentinel** provides clear pattern recommendations
2. **Database Migration** produces safe, reversible migration
3. **ML Pipeline** validates model accuracy >85%
4. **API Consistency** confirms endpoint compliance
5. **All tests** pass with >85% coverage

### **Quality Metrics**
- Test Coverage: >85%
- Code Quality: Architecture patterns properly applied
- Migration Safety: Fully reversible with downgrade tested
- Model Accuracy: >85% on validation set
- API Compliance: 10/10 consistency score
- Inference Latency: <25ms per scoring call

## Real-World Usage Example

```bash
# Start development session
claude "Enhance lead scoring algorithm accuracy"

# Agents coordinate automatically:
# 1. Architecture Sentinel analyzes current scoring implementation
# 2. Database Migration validates any schema changes
# 3. ML Pipeline evaluates model quality
# 4. API Consistency reviews new endpoints
# 5. Security Auditor checks auth coverage
# 6. Cost Token Optimization evaluates cost impact
```

---

**Test Status**: Ready for execution
**Last Updated**: 2026-02-05
**Compatible with**: Claude Code v2.0+
**Dependencies**: Architecture Sentinel, Database Migration, ML Pipeline, API Consistency, Security Auditor
