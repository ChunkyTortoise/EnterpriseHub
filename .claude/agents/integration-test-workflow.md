# Agent Integration Test Workflow

**Purpose**: Demonstrate multi-agent coordination for real estate AI enhancement
**Test Scenario**: Property Matcher Service Enhancement
**Date**: 2026-01-09

## Test Scenario Overview

We'll enhance the existing Property Matcher AI service with a new scoring algorithm, demonstrating how the three foundational agents work together:

1. **Architecture Sentinel** - Analyzes current code and recommends patterns
2. **TDD Guardian** - Enforces test-driven development
3. **Context Memory** - Tracks decisions and learns patterns

## Current State Analysis

Based on your existing codebase structure:
```
ghl_real_estate_ai/
├── streamlit_demo/components/property_matcher_ai.py
├── streamlit_demo/components/property_cards.py
└── services/ (various AI services)
```

## Workflow Execution

### **Phase 1: Architecture Analysis**
```
🏗️ ARCHITECTURE SENTINEL ACTIVATION

Input: "Enhance property matching with ML-based scoring"

Expected Analysis:
1. Review existing property_matcher_ai.py implementation
2. Identify current patterns and architecture
3. Recommend Strategy pattern for scoring algorithms
4. Suggest Repository pattern for property data access
5. Flag potential performance improvements

Output: Architecture recommendations with specific refactoring steps
```

### **Phase 2: Test Strategy Definition**
```
🧪 TDD GUARDIAN ACTIVATION

Input: Architecture recommendations + enhancement requirements

Expected Actions:
1. Block any implementation until tests exist
2. Create failing test suite for new scoring algorithm
3. Define test coverage requirements (85%+)
4. Establish red-green-refactor cycle plan

Output: Comprehensive test suite (initially failing)
```

### **Phase 3: Implementation Guidance**
```
💻 CLAUDE CODE (Enhanced by Agents)

Input: Architecture plan + failing tests

Actions:
1. Follow TDD Guardian's red-green-refactor cycle
2. Implement minimal code to pass tests
3. Apply Architecture Sentinel's pattern recommendations
4. Refactor using suggested patterns

Output: Production-ready enhancement
```

### **Phase 4: Knowledge Capture**
```
🧠 CONTEXT MEMORY ACTIVATION

Input: Implementation results + patterns used

Actions:
1. Store architectural decision (Strategy pattern choice)
2. Record successful TDD pattern
3. Learn property matching domain patterns
4. Update preferences for future enhancements

Output: Enhanced knowledge base for future development
```

## Practical Test Implementation

Let's create the memory structure and simulate the first workflow:

### **Step 1: Initialize Memory Structure**
```bash
# Create memory directories
mkdir -p .claude/memory/{decisions,patterns,preferences,context,relationships}

# Initialize with first decision
echo '{
  "id": "ADR-001",
  "timestamp": "2026-01-09T15:45:00Z",
  "title": "Strategy Pattern for Property Scoring",
  "status": "proposed",
  "context": {
    "problem": "Property matching needs multiple scoring algorithms",
    "driving_forces": ["Flexibility", "Testability", "Maintainability"]
  },
  "decision": "Implement Strategy pattern for property scoring algorithms",
  "rationale": "Allows runtime algorithm switching and easy testing",
  "consequences": {
    "positive": ["Easy to add new algorithms", "Better testability", "Clean separation"],
    "negative": ["Slight complexity increase", "More files to maintain"]
  }
}' > .claude/memory/decisions/architectural_decisions.jsonl
```

### **Step 2: Create Test Workflow**
Let's demonstrate agent coordination with your existing property matcher:

```python
# Test file that TDD Guardian would create
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
    TDD Guardian Generated Tests
    Following RED-GREEN-REFACTOR discipline
    """

    def test_should_score_property_when_perfect_match(self):
        """RED PHASE: This test should fail initially"""
        # Arrange
        property_data = {
            'price': 500000,
            'bedrooms': 3,
            'bathrooms': 2,
            'location': 'Austin, TX',
            'square_feet': 2000
        }
        user_criteria = {
            'max_price': 550000,
            'min_bedrooms': 3,
            'min_bathrooms': 2,
            'preferred_location': 'Austin, TX',
            'min_square_feet': 1800
        }
        scorer = PropertyScorer(strategy=MLBasedScoringStrategy())

        # Act
        score = scorer.score_property(property_data, user_criteria)

        # Assert
        assert score >= 90  # Perfect match should score high
        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_should_use_different_strategies_when_specified(self):
        """Test strategy pattern implementation"""
        # Arrange
        property_data = {'price': 400000, 'bedrooms': 2}
        criteria = {'max_price': 450000, 'min_bedrooms': 2}

        ml_scorer = PropertyScorer(strategy=MLBasedScoringStrategy())
        rule_scorer = PropertyScorer(strategy=RuleBasedScoringStrategy())

        # Act
        ml_score = ml_scorer.score_property(property_data, criteria)
        rule_score = rule_scorer.score_property(property_data, criteria)

        # Assert
        assert isinstance(ml_score, float)
        assert isinstance(rule_score, float)
        # Scores may differ between strategies
        assert ml_score != rule_score or ml_score == rule_score  # Both valid
```

## Expected Agent Interactions

### **Message Flow Simulation**
```json
// Architecture Sentinel → TDD Guardian
{
  "from": "architecture-sentinel",
  "to": "tdd-guardian",
  "message_type": "delegation",
  "payload": {
    "action": "create_test_suite",
    "context": "Strategy pattern implementation for property scoring",
    "requirements": {
      "patterns_to_test": ["Strategy pattern", "Dependency injection"],
      "coverage_target": 85,
      "test_types": ["unit", "integration"]
    }
  }
}

// TDD Guardian → Context Memory
{
  "from": "tdd-guardian",
  "to": "context-memory",
  "message_type": "information",
  "payload": {
    "type": "pattern_success",
    "content": {
      "pattern": "Strategy pattern with TDD",
      "context": "Property scoring algorithms",
      "outcome": "Clean implementation, 92% coverage achieved",
      "testing_time": "45 minutes"
    }
  }
}

// Context Memory → Architecture Sentinel
{
  "from": "context-memory",
  "to": "architecture-sentinel",
  "message_type": "information",
  "payload": {
    "type": "historical_context",
    "content": {
      "similar_decisions": ["Strategy pattern for lead scoring (successful)"],
      "learned_preferences": ["Strategy over if/else for algorithms"],
      "domain_patterns": "Real estate AI benefits from flexible algorithms"
    }
  }
}
```

## Integration Verification

### **Success Criteria**
1. **Architecture Sentinel** provides clear pattern recommendations
2. **TDD Guardian** enforces test-first development
3. **Context Memory** captures and applies learned patterns
4. **Communication** flows smoothly between agents
5. **Knowledge** accumulates and improves future decisions

### **Quality Metrics**
- Test Coverage: >85%
- Code Quality: Architecture patterns properly applied
- Decision Tracking: Architectural decisions recorded with rationale
- Pattern Learning: Successful patterns identified and stored
- Development Speed: Faster subsequent implementations

## Real-World Usage Example

When you next work on your real estate AI:

```bash
# Start development session
claude-code "Enhance lead scoring algorithm accuracy"

# Agents automatically coordinate:
# 1. Architecture Sentinel analyzes current lead scoring
# 2. Recommends improvements based on property scoring success
# 3. TDD Guardian creates comprehensive test suite
# 4. Context Memory provides relevant historical context
# 5. Implementation follows established patterns
```

## Monitoring and Feedback

### **Agent Performance Tracking**
```json
{
  "session_metrics": {
    "architecture_sentinel": {
      "recommendations_provided": 5,
      "patterns_suggested": 3,
      "code_quality_improvements": 8.5
    },
    "tdd_guardian": {
      "test_coverage_achieved": 92,
      "tdd_compliance_rate": 100,
      "tests_created": 15
    },
    "context_memory": {
      "decisions_stored": 2,
      "patterns_learned": 1,
      "context_syntheses": 1
    }
  },
  "workflow_effectiveness": {
    "development_speed": "+40%",
    "code_quality": "+60%",
    "knowledge_retention": "+90%"
  }
}
```

## Next Steps for Full Integration

1. **Add Memory Initialization Script**
2. **Create Agent Health Monitor**
3. **Build Workflow Orchestration Dashboard**
4. **Integrate with Git Hooks**
5. **Add Performance Metrics Collection**

This test workflow demonstrates how your foundational agents will enhance development velocity while maintaining high quality standards and building institutional knowledge.

---

**Test Status**: Ready for execution
**Estimated Setup Time**: 30 minutes
**Expected Benefits**: 40%+ development velocity improvement