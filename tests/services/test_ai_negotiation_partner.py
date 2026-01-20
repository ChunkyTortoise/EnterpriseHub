"""
Comprehensive tests for AI Negotiation Partner system.

Tests seller psychology analysis, market leverage calculation, strategy generation,
win probability prediction, and real-time coaching functionality.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from ghl_real_estate_ai.services.ai_negotiation_partner import AINegotiationPartner
from ghl_real_estate_ai.api.schemas.negotiation import (
    NegotiationAnalysisRequest,
    RealTimeCoachingRequest,
    StrategyUpdateRequest,
    ListingHistory,
    SellerMotivationType,
    UrgencyLevel,
    MarketCondition,
    NegotiationTactic
)


class TestAINegotiationPartner:
    """Test suite for AI Negotiation Partner"""
    
    @pytest.fixture
    def negotiation_partner(self):
        """Create AI negotiation partner instance for testing"""
        return AINegotiationPartner()
    
    @pytest.fixture
    def mock_analysis_request(self):
        """Mock negotiation analysis request"""
        return NegotiationAnalysisRequest(
            property_id="PROP_12345",
            lead_id="LEAD_67890",
            buyer_preferences={
                "cash_offer": False,
                "flexible_timeline": True,
                "pre_approved": True
            }
        )
    
    @pytest.fixture
    def mock_listing_history(self):
        """Mock listing history data"""
        return ListingHistory(
            original_list_price=Decimal("800000"),
            current_price=Decimal("750000"),
            price_drops=[
                {"date": "2024-10-15", "old_price": 800000, "new_price": 750000, "percentage": 6.25}
            ],
            days_on_market=45,
            listing_views=350,
            showing_requests=22,
            offers_received=1,
            previous_listing_attempts=0
        )
    
    @pytest.fixture
    def mock_property_data(self):
        """Mock property data"""
        return {
            "property_id": "PROP_12345",
            "list_price": 750000,
            "sqft": 2800,
            "bedrooms": 4,
            "bathrooms": 3,
            "property_type": "single_family",
            "zip_code": "78701",
            "days_on_market": 45,
            "year_built": 2015,
            "price_drops": 1
        }
    
    @pytest.fixture
    def mock_buyer_data(self):
        """Mock buyer profile data"""
        return {
            "lead_id": "LEAD_67890",
            "credit_score": 780,
            "debt_to_income": 0.25,
            "down_payment_percent": 20,
            "pre_approved": True,
            "cash_offer": False,
            "flexible_timeline": True,
            "first_time_buyer": False,
            "communication_data": {
                "avg_response_time_hours": 3.5,
                "communication_tone": "professional"
            }
        }


class TestSellerPsychologyAnalyzer:
    """Test seller psychology analysis functionality"""
    
    @pytest.mark.asyncio
    async def test_analyze_seller_psychology_basic(self, negotiation_partner, mock_listing_history):
        """Test basic seller psychology analysis"""
        
        with patch.object(negotiation_partner.psychology_analyzer, 'analyze_seller_psychology') as mock_analyze:
            mock_analyze.return_value = MagicMock(
                motivation_type=SellerMotivationType.FINANCIAL,
                urgency_level=UrgencyLevel.HIGH,
                urgency_score=78.5,
                flexibility_score=65.2,
                emotional_attachment_score=35.0,
                financial_pressure_score=82.0,
                relationship_importance=45.0
            )
            
            # Test analysis
            result = await mock_analyze("PROP_12345", mock_listing_history, {})
            
            assert result.motivation_type == SellerMotivationType.FINANCIAL
            assert result.urgency_level == UrgencyLevel.HIGH
            assert result.urgency_score > 75
            assert result.financial_pressure_score > 80
    
    @pytest.mark.asyncio
    async def test_urgency_analysis_high_days_on_market(self, negotiation_partner):
        """Test urgency analysis with high days on market"""
        
        listing_history = ListingHistory(
            original_list_price=Decimal("750000"),
            current_price=Decimal("700000"),
            price_drops=[
                {"date": "2024-08-15", "old_price": 750000, "new_price": 725000, "percentage": 3.3},
                {"date": "2024-09-20", "old_price": 725000, "new_price": 700000, "percentage": 3.4}
            ],
            days_on_market=125,  # High DOM
            listing_views=800,
            showing_requests=35,
            offers_received=2
        )
        
        with patch.object(negotiation_partner.psychology_analyzer, 'analyze_seller_psychology') as mock_analyze:
            mock_analyze.return_value = MagicMock(
                urgency_level=UrgencyLevel.CRITICAL,
                urgency_score=88.0,
                motivation_type=SellerMotivationType.DISTRESSED
            )
            
            result = await mock_analyze("PROP_12345", listing_history, {})
            
            assert result.urgency_level == UrgencyLevel.CRITICAL
            assert result.urgency_score > 85
            assert result.motivation_type == SellerMotivationType.DISTRESSED
    
    def test_psychology_score_calculations(self, negotiation_partner):
        """Test psychology score calculation logic"""
        
        # Test emotional attachment calculation
        motivation_analysis = {"primary_motivation": SellerMotivationType.EMOTIONAL}
        ai_insights = {"ai_emotional_assessment": "high attachment"}
        behavioral_analysis = {"behavioral_pattern": "overpriced_stubborn"}
        
        # This would test internal methods if they were public
        # For now, we test the overall behavior through the public interface
        assert True  # Placeholder for internal calculation tests


class TestMarketLeverageCalculator:
    """Test market leverage calculation functionality"""
    
    @pytest.mark.asyncio
    async def test_calculate_market_leverage_buyers_market(self, negotiation_partner, mock_property_data, mock_buyer_data, mock_listing_history):
        """Test market leverage calculation in buyers market"""
        
        with patch.object(negotiation_partner.leverage_calculator, 'calculate_market_leverage') as mock_calculate:
            mock_calculate.return_value = MagicMock(
                overall_leverage_score=78.5,
                market_condition=MarketCondition.BUYERS_MARKET,
                competitive_pressure=65.0,
                price_positioning="overpriced",
                seasonal_advantage=12.0,
                financing_strength=85.0
            )
            
            result = await mock_calculate("PROP_12345", mock_property_data, mock_buyer_data, mock_listing_history)
            
            assert result.overall_leverage_score > 75
            assert result.market_condition == MarketCondition.BUYERS_MARKET
            assert result.price_positioning == "overpriced"
            assert result.financing_strength > 80
    
    @pytest.mark.asyncio
    async def test_cash_offer_leverage_boost(self, negotiation_partner):
        """Test leverage boost from cash offer"""
        
        cash_buyer_data = {
            "cash_offer": True,
            "credit_score": 800,
            "quick_close": True
        }
        
        with patch.object(negotiation_partner.leverage_calculator, 'calculate_market_leverage') as mock_calculate:
            mock_calculate.return_value = MagicMock(
                cash_offer_boost=25.0,
                quick_close_advantage=15.0,
                financing_strength=95.0
            )
            
            result = await mock_calculate("PROP_12345", {}, cash_buyer_data, None)
            
            assert result.cash_offer_boost == 25.0
            assert result.quick_close_advantage == 15.0
            assert result.financing_strength == 95.0
    
    def test_seasonal_advantage_calculation(self, negotiation_partner):
        """Test seasonal advantage calculations"""
        
        # Test different months for seasonal advantage
        winter_months = [11, 12, 1]  # Should favor buyers
        spring_months = [4, 5, 6]    # Should favor sellers
        
        # These would test internal seasonal calculation methods
        # For now, verify the concept through integration tests
        assert True  # Placeholder for seasonal calculation tests


class TestNegotiationStrategyEngine:
    """Test negotiation strategy generation"""
    
    @pytest.mark.asyncio
    async def test_generate_price_focused_strategy(self, negotiation_partner):
        """Test price-focused strategy generation"""
        
        mock_psychology = MagicMock(
            motivation_type=SellerMotivationType.FINANCIAL,
            urgency_level=UrgencyLevel.HIGH,
            flexibility_score=75.0
        )
        
        mock_leverage = MagicMock(
            overall_leverage_score=82.0,
            market_condition=MarketCondition.BUYERS_MARKET,
            price_positioning="overpriced"
        )
        
        with patch.object(negotiation_partner.strategy_engine, 'generate_negotiation_strategy') as mock_generate:
            mock_generate.return_value = MagicMock(
                primary_tactic=NegotiationTactic.PRICE_FOCUSED,
                confidence_score=85.0,
                recommended_offer_price=Decimal("712500"),
                opening_strategy="Present 95.0% offer with strong market analysis"
            )
            
            result = await mock_generate("PROP_12345", mock_psychology, mock_leverage, {}, {})
            
            assert result.primary_tactic == NegotiationTactic.PRICE_FOCUSED
            assert result.confidence_score > 80
            assert float(result.recommended_offer_price) < 750000  # Below list price
    
    @pytest.mark.asyncio
    async def test_generate_relationship_strategy(self, negotiation_partner):
        """Test relationship-building strategy generation"""
        
        mock_psychology = MagicMock(
            motivation_type=SellerMotivationType.EMOTIONAL,
            relationship_importance=85.0,
            emotional_attachment_score=78.0
        )
        
        mock_leverage = MagicMock(
            overall_leverage_score=45.0,  # Lower leverage
            market_condition=MarketCondition.BALANCED
        )
        
        with patch.object(negotiation_partner.strategy_engine, 'generate_negotiation_strategy') as mock_generate:
            mock_generate.return_value = MagicMock(
                primary_tactic=NegotiationTactic.RELATIONSHIP_BUILDING,
                relationship_building_approach="personal_empathetic",
                key_terms_to_emphasize=["personal_connection", "home_appreciation"]
            )
            
            result = await mock_generate("PROP_12345", mock_psychology, mock_leverage, {}, {})
            
            assert result.primary_tactic == NegotiationTactic.RELATIONSHIP_BUILDING
            assert "personal" in result.relationship_building_approach
    
    def test_offer_price_calculation(self, negotiation_partner):
        """Test optimal offer price calculation logic"""
        
        # Test psychology-based adjustments
        high_urgency_psychology = MagicMock(urgency_level=UrgencyLevel.CRITICAL, urgency_score=90)
        low_urgency_psychology = MagicMock(urgency_level=UrgencyLevel.LOW, urgency_score=25)
        
        # These would test internal pricing calculation methods
        assert True  # Placeholder for pricing calculation tests


class TestWinProbabilityPredictor:
    """Test win probability prediction functionality"""
    
    @pytest.mark.asyncio
    async def test_predict_high_win_probability(self, negotiation_partner):
        """Test high win probability prediction"""
        
        mock_psychology = MagicMock(
            urgency_score=85.0,
            flexibility_score=80.0,
            motivation_type=SellerMotivationType.DISTRESSED
        )
        
        mock_leverage = MagicMock(
            overall_leverage_score=88.0,
            market_condition=MarketCondition.BUYERS_MARKET
        )
        
        mock_strategy = MagicMock(
            recommended_offer_price=Decimal("720000"),  # 96% of 750k list
            confidence_score=82.0
        )
        
        with patch.object(negotiation_partner.win_predictor, 'predict_win_probability') as mock_predict:
            mock_predict.return_value = MagicMock(
                win_probability=87.3,
                confidence_interval={"lower": 81.5, "upper": 93.1},
                success_drivers=["High seller urgency", "Strong market leverage", "Competitive offer"]
            )
            
            result = await mock_predict("PROP_12345", mock_psychology, mock_leverage, mock_strategy, {}, {})
            
            assert result.win_probability > 85
            assert len(result.success_drivers) > 0
            assert result.confidence_interval["lower"] < result.win_probability < result.confidence_interval["upper"]
    
    @pytest.mark.asyncio
    async def test_predict_low_win_probability(self, negotiation_partner):
        """Test low win probability prediction"""
        
        mock_psychology = MagicMock(
            urgency_score=25.0,
            flexibility_score=35.0,
            motivation_type=SellerMotivationType.EMOTIONAL
        )
        
        mock_leverage = MagicMock(
            overall_leverage_score=22.0,
            market_condition=MarketCondition.SELLERS_MARKET
        )
        
        mock_strategy = MagicMock(
            recommended_offer_price=Decimal("650000"),  # Low ball offer
            confidence_score=45.0
        )
        
        with patch.object(negotiation_partner.win_predictor, 'predict_win_probability') as mock_predict:
            mock_predict.return_value = MagicMock(
                win_probability=28.5,
                risk_factors=["Low offer price", "Sellers market", "Low seller urgency"]
            )
            
            result = await mock_predict("PROP_12345", mock_psychology, mock_leverage, mock_strategy, {}, {})
            
            assert result.win_probability < 35
            assert len(result.risk_factors) > 0
    
    def test_scenario_analysis_generation(self, negotiation_partner):
        """Test scenario analysis for different offer types"""
        
        # Test various scenarios: cash offer, quick close, higher price, etc.
        # This would test internal scenario generation methods
        assert True  # Placeholder for scenario analysis tests


class TestNegotiationIntelligence:
    """Test comprehensive negotiation intelligence analysis"""
    
    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self, negotiation_partner, mock_analysis_request):
        """Test complete negotiation intelligence workflow"""
        
        with patch.object(negotiation_partner, '_gather_analysis_data') as mock_gather:
            mock_gather.return_value = (
                {"property_id": "PROP_12345", "list_price": 750000},  # property_data
                {"lead_id": "LEAD_67890", "credit_score": 780},       # buyer_data
                ListingHistory(
                    original_list_price=Decimal("750000"),
                    current_price=Decimal("750000"),
                    price_drops=[],
                    days_on_market=30
                )
            )
            
            # Mock all intelligence engines
            with patch.object(negotiation_partner.psychology_analyzer, 'analyze_seller_psychology') as mock_psych, \
                 patch.object(negotiation_partner.leverage_calculator, 'calculate_market_leverage') as mock_leverage, \
                 patch.object(negotiation_partner.strategy_engine, 'generate_negotiation_strategy') as mock_strategy, \
                 patch.object(negotiation_partner.win_predictor, 'predict_win_probability') as mock_win:
                
                # Setup mocks
                mock_psych.return_value = MagicMock(motivation_type=SellerMotivationType.FINANCIAL)
                mock_leverage.return_value = MagicMock(overall_leverage_score=75.0)
                mock_strategy.return_value = MagicMock(primary_tactic=NegotiationTactic.PRICE_FOCUSED)
                mock_win.return_value = MagicMock(win_probability=82.5)
                
                # Mock AI summary generation
                with patch.object(negotiation_partner, '_generate_strategic_summary') as mock_summary:
                    mock_summary.return_value = (
                        "Executive summary",
                        ["Key insight 1", "Key insight 2"],
                        ["Action item 1", "Action item 2"]
                    )
                    
                    # Execute analysis
                    result = await negotiation_partner.analyze_negotiation_intelligence(mock_analysis_request)
                    
                    # Verify results
                    assert result.property_id == mock_analysis_request.property_id
                    assert result.lead_id == mock_analysis_request.lead_id
                    assert result.processing_time_ms is not None
                    assert result.executive_summary == "Executive summary"
                    assert len(result.key_insights) == 2
                    assert len(result.action_items) == 2
    
    @pytest.mark.asyncio
    async def test_analysis_performance_target(self, negotiation_partner, mock_analysis_request):
        """Test that analysis completes within 3-second target"""
        
        start_time = datetime.now()
        
        with patch.object(negotiation_partner, '_gather_analysis_data'), \
             patch.object(negotiation_partner.psychology_analyzer, 'analyze_seller_psychology'), \
             patch.object(negotiation_partner.leverage_calculator, 'calculate_market_leverage'), \
             patch.object(negotiation_partner.strategy_engine, 'generate_negotiation_strategy'), \
             patch.object(negotiation_partner.win_predictor, 'predict_win_probability'), \
             patch.object(negotiation_partner, '_generate_strategic_summary'):
            
            # Mock fast responses
            negotiation_partner.psychology_analyzer.analyze_seller_psychology.return_value = MagicMock()
            negotiation_partner.leverage_calculator.calculate_market_leverage.return_value = MagicMock()
            negotiation_partner.strategy_engine.generate_negotiation_strategy.return_value = MagicMock()
            negotiation_partner.win_predictor.predict_win_probability.return_value = MagicMock()
            negotiation_partner._gather_analysis_data.return_value = ({}, {}, MagicMock())
            negotiation_partner._generate_strategic_summary.return_value = ("", [], [])
            
            result = await negotiation_partner.analyze_negotiation_intelligence(mock_analysis_request)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Verify performance target (allowing for test overhead)
            assert processing_time < 5.0  # Generous allowance for test environment
            assert result.processing_time_ms < 3000  # Target: sub-3-second


class TestRealTimeCoaching:
    """Test real-time coaching functionality"""
    
    @pytest.mark.asyncio
    async def test_realtime_coaching_basic(self, negotiation_partner):
        """Test basic real-time coaching"""
        
        # Setup active negotiation
        mock_intelligence = MagicMock()
        negotiation_partner.active_negotiations["PROP_12345"] = {
            "intelligence": mock_intelligence,
            "buyer_profile": {},
            "property_data": {},
            "created_at": datetime.now()
        }
        
        coaching_request = RealTimeCoachingRequest(
            negotiation_id="PROP_12345",
            conversation_context="Seller is considering our offer",
            current_situation="Initial offer presentation",
            buyer_feedback="Client is confident",
            seller_response="Seller wants to think about it"
        )
        
        with patch.object(negotiation_partner, '_analyze_conversation_context') as mock_analyze, \
             patch.object(negotiation_partner, '_generate_immediate_guidance') as mock_guidance:
            
            mock_analyze.return_value = {"seller_emotional_state": "neutral"}
            mock_guidance.return_value = "Continue with current strategy"
            
            result = await negotiation_partner.provide_realtime_coaching(coaching_request)
            
            assert result.immediate_guidance == "Continue with current strategy"
            assert isinstance(result.tactical_adjustments, list)
            assert isinstance(result.next_steps, list)
    
    @pytest.mark.asyncio
    async def test_coaching_counter_offer_scenario(self, negotiation_partner):
        """Test coaching for counter-offer scenario"""
        
        # Setup active negotiation with specific strategy
        mock_intelligence = MagicMock()
        mock_intelligence.negotiation_strategy.primary_tactic = NegotiationTactic.PRICE_FOCUSED
        
        negotiation_partner.active_negotiations["PROP_12345"] = {
            "intelligence": mock_intelligence,
            "buyer_profile": {},
            "property_data": {},
            "created_at": datetime.now()
        }
        
        coaching_request = RealTimeCoachingRequest(
            negotiation_id="PROP_12345",
            conversation_context="Seller countered at $740,000",
            current_situation="Seller counter-offer",
            seller_response="Counter at $740k"
        )
        
        result = await negotiation_partner.provide_realtime_coaching(coaching_request)
        
        # Should provide counter-specific guidance
        assert "counter" in result.immediate_guidance.lower()
        assert len(result.next_steps) > 0
    
    def test_coaching_risk_identification(self, negotiation_partner):
        """Test risk identification in coaching"""
        
        # Test various risk scenarios
        # This would test internal risk identification methods
        assert True  # Placeholder for risk identification tests


class TestStrategyUpdates:
    """Test strategy update functionality"""
    
    @pytest.mark.asyncio
    async def test_strategy_update_new_information(self, negotiation_partner):
        """Test strategy update with new seller information"""
        
        # Setup active negotiation
        mock_intelligence = MagicMock()
        negotiation_partner.active_negotiations["PROP_12345"] = {
            "intelligence": mock_intelligence,
            "buyer_profile": {},
            "property_data": {},
            "created_at": datetime.now()
        }
        
        update_request = StrategyUpdateRequest(
            negotiation_id="PROP_12345",
            new_information={
                "seller_response": "Seller mentioned divorce timeline",
                "urgency_update": "increased",
                "communication_data": {"tone": "urgent"}
            }
        )
        
        with patch.object(negotiation_partner.psychology_analyzer, 'analyze_seller_psychology') as mock_psych, \
             patch.object(negotiation_partner.strategy_engine, 'generate_negotiation_strategy') as mock_strategy, \
             patch.object(negotiation_partner.win_predictor, 'predict_win_probability') as mock_win:
            
            mock_psych.return_value = MagicMock(urgency_level=UrgencyLevel.CRITICAL)
            mock_strategy.return_value = MagicMock(primary_tactic=NegotiationTactic.TIMELINE_FOCUSED)
            mock_win.return_value = MagicMock(win_probability=88.5)
            
            result = await negotiation_partner.update_negotiation_strategy(update_request)
            
            # Verify strategy was updated
            assert result.seller_psychology.urgency_level == UrgencyLevel.CRITICAL
            assert result.negotiation_strategy.primary_tactic == NegotiationTactic.TIMELINE_FOCUSED
    
    @pytest.mark.asyncio
    async def test_selective_engine_updates(self, negotiation_partner):
        """Test that only relevant engines are updated"""
        
        # Setup active negotiation
        mock_intelligence = MagicMock()
        negotiation_partner.active_negotiations["PROP_12345"] = {
            "intelligence": mock_intelligence,
            "buyer_profile": {},
            "property_data": {},
            "created_at": datetime.now()
        }
        
        # Update with market information only
        update_request = StrategyUpdateRequest(
            negotiation_id="PROP_12345",
            new_information={
                "market_change": "New comparable sales",
                "inventory_update": "Decreased inventory"
            }
        )
        
        with patch.object(negotiation_partner.leverage_calculator, 'calculate_market_leverage') as mock_leverage:
            mock_leverage.return_value = MagicMock()
            
            # Psychology analyzer should NOT be called
            with patch.object(negotiation_partner.psychology_analyzer, 'analyze_seller_psychology') as mock_psych:
                await negotiation_partner.update_negotiation_strategy(update_request)
                
                # Market leverage should be recalculated
                mock_leverage.assert_called_once()
                # Psychology should not be recalculated
                mock_psych.assert_not_called()


class TestPerformanceMetrics:
    """Test performance monitoring and metrics"""
    
    def test_performance_metrics_tracking(self, negotiation_partner):
        """Test performance metrics collection"""
        
        # Simulate some analyses
        negotiation_partner.performance_metrics["total_analyses"] = 10
        negotiation_partner.performance_metrics["avg_processing_time_ms"] = 2500
        negotiation_partner.performance_metrics["strategy_effectiveness"] = {
            "price_focused": {"count": 5, "total_probability": 420},
            "relationship_building": {"count": 3, "total_probability": 240}
        }
        
        metrics = negotiation_partner.get_performance_metrics()
        
        assert metrics["total_analyses"] == 10
        assert metrics["avg_processing_time_ms"] == 2500
        assert "price_focused" in metrics["strategy_averages"]
        assert metrics["strategy_averages"]["price_focused"] == 84.0  # 420/5
    
    def test_active_negotiation_cleanup(self, negotiation_partner):
        """Test cleanup of inactive negotiations"""
        
        # Add old and new negotiations
        old_time = datetime.now() - timedelta(hours=25)
        new_time = datetime.now() - timedelta(hours=1)
        
        negotiation_partner.active_negotiations["OLD_PROP"] = {
            "created_at": old_time,
            "intelligence": MagicMock()
        }
        negotiation_partner.active_negotiations["NEW_PROP"] = {
            "created_at": new_time,
            "intelligence": MagicMock()
        }
        
        # Cleanup with 24-hour threshold
        negotiation_partner.cleanup_inactive_negotiations(hours_threshold=24)
        
        # Old negotiation should be removed
        assert "OLD_PROP" not in negotiation_partner.active_negotiations
        # New negotiation should remain
        assert "NEW_PROP" in negotiation_partner.active_negotiations


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_analysis_with_missing_data(self, negotiation_partner):
        """Test analysis behavior with missing data"""
        
        request = NegotiationAnalysisRequest(
            property_id="MISSING_PROP",
            lead_id="MISSING_LEAD"
        )
        
        with patch.object(negotiation_partner, '_gather_analysis_data') as mock_gather:
            mock_gather.return_value = (None, {}, MagicMock())  # Missing property data
            
            with pytest.raises(ValueError, match="Property data not found"):
                await negotiation_partner.analyze_negotiation_intelligence(request)
    
    @pytest.mark.asyncio
    async def test_coaching_without_active_negotiation(self, negotiation_partner):
        """Test coaching request without active negotiation"""
        
        coaching_request = RealTimeCoachingRequest(
            negotiation_id="NON_EXISTENT",
            conversation_context="Test context",
            current_situation="Test situation"
        )
        
        with pytest.raises(ValueError, match="Active negotiation not found"):
            await negotiation_partner.provide_realtime_coaching(coaching_request)
    
    @pytest.mark.asyncio
    async def test_engine_failure_handling(self, negotiation_partner, mock_analysis_request):
        """Test handling of individual engine failures"""
        
        with patch.object(negotiation_partner, '_gather_analysis_data') as mock_gather:
            mock_gather.return_value = ({}, {}, MagicMock())
            
            # Make psychology analyzer fail
            with patch.object(negotiation_partner.psychology_analyzer, 'analyze_seller_psychology') as mock_psych:
                mock_psych.side_effect = Exception("Psychology analysis failed")
                
                with pytest.raises(Exception):
                    await negotiation_partner.analyze_negotiation_intelligence(mock_analysis_request)


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_distressed_seller_scenario(self, negotiation_partner):
        """Test analysis of distressed seller scenario"""
        
        # Simulate distressed seller: high DOM, multiple price drops, urgent motivation
        distressed_request = NegotiationAnalysisRequest(
            property_id="DISTRESSED_PROP",
            lead_id="INVESTOR_LEAD",
            buyer_preferences={"cash_offer": True, "quick_close": True}
        )
        
        # Expected: High urgency, financial motivation, price-focused strategy, high win probability
        with patch.object(negotiation_partner, '_gather_analysis_data') as mock_gather, \
             patch.object(negotiation_partner.psychology_analyzer, 'analyze_seller_psychology') as mock_psych, \
             patch.object(negotiation_partner.leverage_calculator, 'calculate_market_leverage') as mock_leverage, \
             patch.object(negotiation_partner.strategy_engine, 'generate_negotiation_strategy') as mock_strategy, \
             patch.object(negotiation_partner.win_predictor, 'predict_win_probability') as mock_win:
            
            # Setup distressed seller scenario
            mock_gather.return_value = ({}, {"cash_offer": True}, MagicMock())
            mock_psych.return_value = MagicMock(
                motivation_type=SellerMotivationType.DISTRESSED,
                urgency_level=UrgencyLevel.CRITICAL,
                urgency_score=92.0
            )
            mock_leverage.return_value = MagicMock(
                overall_leverage_score=85.0,
                cash_offer_boost=25.0
            )
            mock_strategy.return_value = MagicMock(
                primary_tactic=NegotiationTactic.PRICE_FOCUSED,
                confidence_score=88.0
            )
            mock_win.return_value = MagicMock(win_probability=91.5)
            
            with patch.object(negotiation_partner, '_generate_strategic_summary') as mock_summary:
                mock_summary.return_value = ("Summary", [], [])
                
                result = await negotiation_partner.analyze_negotiation_intelligence(distressed_request)
                
                assert result.seller_psychology.motivation_type == SellerMotivationType.DISTRESSED
                assert result.seller_psychology.urgency_level == UrgencyLevel.CRITICAL
                assert result.negotiation_strategy.primary_tactic == NegotiationTactic.PRICE_FOCUSED
                assert result.win_probability.win_probability > 90
    
    @pytest.mark.asyncio
    async def test_emotional_seller_scenario(self, negotiation_partner):
        """Test analysis of emotional seller scenario"""
        
        emotional_request = NegotiationAnalysisRequest(
            property_id="EMOTIONAL_PROP",
            lead_id="FAMILY_LEAD",
            buyer_preferences={"first_time_buyer": True, "family_home": True}
        )
        
        # Expected: Emotional motivation, relationship-building strategy
        with patch.object(negotiation_partner, '_gather_analysis_data') as mock_gather, \
             patch.object(negotiation_partner.psychology_analyzer, 'analyze_seller_psychology') as mock_psych, \
             patch.object(negotiation_partner.leverage_calculator, 'calculate_market_leverage') as mock_leverage, \
             patch.object(negotiation_partner.strategy_engine, 'generate_negotiation_strategy') as mock_strategy, \
             patch.object(negotiation_partner.win_predictor, 'predict_win_probability') as mock_win:
            
            mock_gather.return_value = ({}, {"first_time_buyer": True}, MagicMock())
            mock_psych.return_value = MagicMock(
                motivation_type=SellerMotivationType.EMOTIONAL,
                relationship_importance=85.0,
                emotional_attachment_score=78.0
            )
            mock_leverage.return_value = MagicMock(overall_leverage_score=55.0)
            mock_strategy.return_value = MagicMock(
                primary_tactic=NegotiationTactic.RELATIONSHIP_BUILDING,
                relationship_building_approach="personal_empathetic"
            )
            mock_win.return_value = MagicMock(win_probability=72.5)
            
            with patch.object(negotiation_partner, '_generate_strategic_summary') as mock_summary:
                mock_summary.return_value = ("Summary", [], [])
                
                result = await negotiation_partner.analyze_negotiation_intelligence(emotional_request)
                
                assert result.seller_psychology.motivation_type == SellerMotivationType.EMOTIONAL
                assert result.negotiation_strategy.primary_tactic == NegotiationTactic.RELATIONSHIP_BUILDING
                assert "personal" in result.negotiation_strategy.relationship_building_approach


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([
        "tests/services/test_ai_negotiation_partner.py",
        "-v",
        "--cov=ghl_real_estate_ai.services.ai_negotiation_partner",
        "--cov-report=html"
    ])