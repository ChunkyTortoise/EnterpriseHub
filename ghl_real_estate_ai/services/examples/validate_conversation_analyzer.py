#!/usr/bin/env python3
"""
Validation Script for Claude Conversation Analyzer Service

Quick validation to ensure all components are properly installed and configured.
"""

import asyncio
import sys
from datetime import datetime, timedelta


async def validate_imports():
    """Validate all required imports"""
    print("="*80)
    print("STEP 1: Validating Imports")
    print("="*80)

    try:
        from ghl_real_estate_ai.services.claude_conversation_analyzer import (
            ClaudeConversationAnalyzer,
            ConversationData,
            ConversationAnalysis,
            CoachingInsights,
            ImprovementMetrics,
            SkillAssessment,
            QualityScore,
            ExpertiseAssessment,
            CoachingOpportunity,
            ConversationQualityArea,
            RealEstateExpertiseArea,
            CoachingPriority,
            SkillLevel,
            ConversationOutcome,
            get_conversation_analyzer,
            analyze_agent_conversation,
            get_coaching_recommendations,
            track_agent_improvement
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


async def validate_service_initialization():
    """Validate service can be initialized"""
    print("\n" + "="*80)
    print("STEP 2: Validating Service Initialization")
    print("="*80)

    try:
        from ghl_real_estate_ai.services.claude_conversation_analyzer import (
            ClaudeConversationAnalyzer
        )

        # Create analyzer with test configuration
        analyzer = ClaudeConversationAnalyzer(
            anthropic_api_key="test_key_validation"
        )

        print("✅ Service initialization successful")
        print(f"   Model: {analyzer.model}")
        print(f"   Max Tokens: {analyzer.max_tokens}")
        print(f"   Temperature: {analyzer.temperature}")
        print(f"   Timeout: {analyzer.timeout_seconds}s")

        return True
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return False


async def validate_data_models():
    """Validate data models can be created"""
    print("\n" + "="*80)
    print("STEP 3: Validating Data Models")
    print("="*80)

    try:
        from ghl_real_estate_ai.services.claude_conversation_analyzer import (
            ConversationData,
            QualityScore,
            ExpertiseAssessment,
            CoachingOpportunity,
            ConversationQualityArea,
            RealEstateExpertiseArea,
            CoachingPriority,
            SkillLevel
        )

        # Test ConversationData
        conversation = ConversationData(
            conversation_id="test_conv_001",
            agent_id="test_agent_123",
            tenant_id="test_tenant_456",
            lead_id="test_lead_789",
            messages=[
                {"role": "agent", "content": "Test message", "timestamp": datetime.now().isoformat()}
            ],
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(minutes=5)
        )
        print("✅ ConversationData model created")

        # Test QualityScore
        quality_score = QualityScore(
            area="communication_effectiveness",
            score=85.0,
            confidence=0.9,
            strengths=["Clear communication"],
            weaknesses=["Could ask more questions"],
            evidence=["Test evidence"],
            recommendations=["Test recommendation"]
        )
        print("✅ QualityScore model created")

        # Test ExpertiseAssessment
        expertise = ExpertiseAssessment(
            area=RealEstateExpertiseArea.MARKET_KNOWLEDGE,
            skill_level=SkillLevel.PROFICIENT,
            score=78.0,
            confidence=0.85,
            demonstrated_knowledge=["Market trends"],
            knowledge_gaps=["Pricing strategy"],
            improvement_suggestions=["Study CMAs"]
        )
        print("✅ ExpertiseAssessment model created")

        # Test CoachingOpportunity
        opportunity = CoachingOpportunity(
            opportunity_id="test_opp_001",
            priority=CoachingPriority.HIGH,
            category="property_presentation",
            title="Test Opportunity",
            description="Test description",
            impact="Test impact",
            recommended_action="Test action",
            training_modules=["Module 1"],
            confidence=0.85
        )
        print("✅ CoachingOpportunity model created")

        return True
    except Exception as e:
        print(f"❌ Data model validation failed: {e}")
        return False


async def validate_helper_methods():
    """Validate helper methods work correctly"""
    print("\n" + "="*80)
    print("STEP 4: Validating Helper Methods")
    print("="*80)

    try:
        from ghl_real_estate_ai.services.claude_conversation_analyzer import (
            ClaudeConversationAnalyzer,
            ConversationData
        )

        analyzer = ClaudeConversationAnalyzer(anthropic_api_key="test_key")

        # Test message formatting
        messages = [
            {"role": "agent", "content": "Hello", "timestamp": "2024-01-10T10:00:00"},
            {"role": "client", "content": "Hi", "timestamp": "2024-01-10T10:00:30"}
        ]
        formatted = analyzer._format_messages(messages)
        assert "AGENT:" in formatted
        assert "CLIENT:" in formatted
        print("✅ Message formatting works")

        # Test duration calculation
        start = datetime(2024, 1, 10, 10, 0, 0)
        end = datetime(2024, 1, 10, 10, 5, 0)
        duration = analyzer._calculate_duration(start, end)
        assert duration == 5.0
        print("✅ Duration calculation works")

        # Test conversation metrics
        conversation = ConversationData(
            conversation_id="test_001",
            agent_id="agent_001",
            tenant_id="tenant_001",
            lead_id="lead_001",
            messages=messages,
            start_time=start,
            end_time=end
        )
        metrics = analyzer._calculate_conversation_metrics(conversation)
        assert metrics["total_messages"] == 2
        print("✅ Conversation metrics calculation works")

        # Test time period parsing
        time_periods = ["last_7_days", "last_30_days", "last_quarter"]
        for period in time_periods:
            start_date, end_date = analyzer._parse_time_period(period)
            assert start_date < end_date
        print("✅ Time period parsing works")

        return True
    except Exception as e:
        print(f"❌ Helper method validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def validate_templates():
    """Validate analysis templates are properly initialized"""
    print("\n" + "="*80)
    print("STEP 5: Validating Analysis Templates")
    print("="*80)

    try:
        from ghl_real_estate_ai.services.claude_conversation_analyzer import (
            ClaudeConversationAnalyzer
        )

        analyzer = ClaudeConversationAnalyzer(anthropic_api_key="test_key")

        # Check all required templates exist
        required_templates = [
            "conversation_quality",
            "real_estate_expertise",
            "coaching_opportunities",
            "performance_tracking"
        ]

        for template in required_templates:
            assert template in analyzer.templates
            assert len(analyzer.templates[template]) > 0
            print(f"✅ Template '{template}' initialized")

        return True
    except Exception as e:
        print(f"❌ Template validation failed: {e}")
        return False


async def validate_metrics_tracking():
    """Validate metrics tracking functionality"""
    print("\n" + "="*80)
    print("STEP 6: Validating Metrics Tracking")
    print("="*80)

    try:
        from ghl_real_estate_ai.services.claude_conversation_analyzer import (
            ClaudeConversationAnalyzer
        )
        from unittest.mock import Mock

        analyzer = ClaudeConversationAnalyzer(anthropic_api_key="test_key")

        # Test initial metrics
        metrics = analyzer.get_service_metrics()
        assert metrics["total_analyses"] == 0
        print("✅ Initial metrics retrieved")

        # Test metrics update
        mock_analysis = Mock()
        mock_analysis.processing_time_ms = 1500.0
        analyzer._update_metrics(mock_analysis)

        updated_metrics = analyzer.get_service_metrics()
        assert updated_metrics["total_analyses"] == 1
        assert updated_metrics["successful_analyses"] == 1
        print("✅ Metrics update works")

        return True
    except Exception as e:
        print(f"❌ Metrics tracking validation failed: {e}")
        return False


async def run_validation():
    """Run all validation checks"""
    print("\n" + "="*80)
    print("CLAUDE CONVERSATION ANALYZER - VALIDATION SUITE")
    print("="*80)

    results = []

    # Run validation steps
    results.append(("Imports", await validate_imports()))
    results.append(("Service Initialization", await validate_service_initialization()))
    results.append(("Data Models", await validate_data_models()))
    results.append(("Helper Methods", await validate_helper_methods()))
    results.append(("Templates", await validate_templates()))
    results.append(("Metrics Tracking", await validate_metrics_tracking()))

    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for step, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {step}")

    print("\n" + "="*80)
    print(f"Results: {passed}/{total} checks passed")
    print("="*80)

    if passed == total:
        print("\n🎉 All validation checks passed!")
        print("   Claude Conversation Analyzer is ready for use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} validation check(s) failed.")
        print("   Please review errors above and fix issues.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_validation())
    sys.exit(exit_code)
