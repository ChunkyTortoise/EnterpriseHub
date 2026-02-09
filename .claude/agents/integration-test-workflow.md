---
name: integration-test-workflow
description: Multi-agent coordination testing, cross-module integration verification, and workflow validation
tools: Read, Grep, Glob, Bash
model: sonnet
---

# Agent Integration Test Workflow

**Purpose**: Demonstrate multi-agent coordination for feature enhancement
**Test Scenario**: User Recommendation Service Enhancement
**Version**: 2.0.0

## Project-Specific Guidance

Adapts to the active project's domain via CLAUDE.md and reference files.

## Test Scenario Overview

We'll enhance the existing Recommendation Service with a new scoring algorithm, demonstrating how agents coordinate:

1. **Architecture Sentinel** - Analyzes current code and recommends patterns
2. **Database Migration** - Validates schema changes for new scoring data
3. **ML Pipeline** - Evaluates scoring model quality and feature engineering
4. **API Consistency** - Ensures new endpoints follow standards

## Current State Analysis

Based on your existing codebase structure:
```
src/
├── components/recommendation_engine.py
├── components/result_cards.py
├── services/advanced_matching_engine.py
├── services/predictive_analytics_engine.py
└── agents/intelligence_agent.py
```

## Workflow Execution

### **Phase 1: Architecture Analysis**
```
ARCHITECTURE SENTINEL ACTIVATION

Input: "Enhance recommendation matching with ML-based scoring"

Expected Analysis:
1. Review existing recommendation_engine.py implementation
2. Identify current patterns and architecture
3. Recommend Strategy pattern for scoring algorithms
4. Suggest Repository pattern for data access
5. Flag potential performance improvements

Output: Architecture recommendations with specific refactoring steps
```

### **Phase 2: Schema Validation**
```
DATABASE MIGRATION ACTIVATION

Input: Architecture recommendations requiring new data storage

Expected Actions:
1. Review existing data and scoring models
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
1. Evaluate feature engineering for recommendation scoring
2. Validate score range (0-100) and calibration
3. Check for data leakage in training features
4. Benchmark accuracy against rule-based baseline
5. Verify inference latency (<25ms target)

Output: Model quality report with metrics
```

### **Phase 4: API Integration**
```
API CONSISTENCY ACTIVATION

Input: New recommendation scoring endpoints

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
# test_recommendation_scoring_strategy.py

import pytest
from unittest.mock import Mock, patch
from src.services.recommendation_scorer import (
    RecommendationScorer,
    MLBasedScoringStrategy,
    RuleBasedScoringStrategy
)

class TestRecommendationScoringStrategy:
    """
    TDD-first test suite for recommendation scoring enhancement.
    Following RED-GREEN-REFACTOR discipline.
    """

    def test_should_score_item_when_perfect_match(self):
        """RED PHASE: This test should fail initially"""
        item_data = {
            'category': 'premium',
            'features': ['feature_a', 'feature_b', 'feature_c'],
            'rating': 4.8,
            'region': 'us-west',
            'tier': 'enterprise'
        }
        user_criteria = {
            'preferred_category': 'premium',
            'required_features': ['feature_a', 'feature_b'],
            'min_rating': 4.5,
            'preferred_region': 'us-west',
            'tier': 'enterprise'
        }
        scorer = RecommendationScorer(strategy=MLBasedScoringStrategy())

        score = scorer.score_item(item_data, user_criteria)

        assert score >= 90
        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_should_use_different_strategies_when_specified(self):
        """Test strategy pattern implementation"""
        item_data = {'category': 'standard', 'rating': 4.0}
        criteria = {'preferred_category': 'standard', 'min_rating': 3.5}

        ml_scorer = RecommendationScorer(strategy=MLBasedScoringStrategy())
        rule_scorer = RecommendationScorer(strategy=RuleBasedScoringStrategy())

        ml_score = ml_scorer.score_item(item_data, criteria)
        rule_score = rule_scorer.score_item(item_data, criteria)

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
    └──► API Consistency: "Review new /api/v1/recommendations/scores endpoint"

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
claude "Enhance recommendation scoring algorithm accuracy"

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
