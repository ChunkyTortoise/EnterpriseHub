"""
M&A Intelligence Event Coordination

This module provides event coordination for M&A intelligence with other enhancement engines,
enabling ultra-high-value cross-engine coordination and enterprise-wide response orchestration.

Key Integration Capabilities:
- Event bus integration for M&A threat and opportunity coordination
- Cross-enhancement engine coordination with autonomous strategy, regulatory, and customer engines  
- Real-time dashboard updates for M&A intelligence
- CRM integration for stakeholder communication
- Enterprise-wide response coordination

Business Value: Enables seamless coordination of $100M-$1B M&A intelligence with other engines
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from ..core.event_bus import (
    EventBus, 
    EventHandler,
    EventType,
    EventPriority,
    publish_ma_threat_event,
    publish_ma_defense_event,
    publish_ma_opportunity_event,
    publish_enterprise_coordination_event
)
from .acquisition_threat_detector import (
    AcquisitionThreatDetector,
    AcquisitionThreat,
    AcquisitionOpportunity,
    MarketValuationAnalysis
)

logger = logging.getLogger(__name__)

class MAEventCoordinator(EventHandler):
    """
    M&A Intelligence Event Coordinator
    
    Coordinates M&A intelligence events with other enhancement engines and enterprise systems
    to deliver ultra-high-value integrated competitive intelligence responses.
    """

    def __init__(
        self,
        ma_threat_detector: AcquisitionThreatDetector,
        event_bus: EventBus
    ):
        super().__init__(
            name="ma_event_coordinator",
            event_types=[
                # Listen for events that require M&A intelligence coordination
                EventType.COMPETITOR_ACTIVITY_DETECTED,
                EventType.STRATEGIC_PATTERN_IDENTIFIED,
                EventType.THREAT_LEVEL_CHANGED,
                EventType.ENTERPRISE_RESPONSE_COORDINATED,
                EventType.MULTI_ENGINE_COORDINATION_REQUIRED,
                
                # Internal M&A events for coordination
                EventType.MA_THREAT_DETECTED,
                EventType.MA_DEFENSE_EXECUTED,
                EventType.MA_OPPORTUNITY_IDENTIFIED,
                EventType.MA_VALUATION_ANALYSIS_COMPLETED,
                EventType.MA_ACQUISITION_APPROACH_PREDICTED,
            ]
        )
        
        self.ma_threat_detector = ma_threat_detector
        self.event_bus = event_bus
        
        # Event coordination metrics
        self.events_coordinated = 0
        self.cross_engine_responses = 0
        self.enterprise_responses_triggered = 0
        
    async def handle(self, event) -> bool:
        """Handle events and coordinate M&A intelligence responses"""
        try:
            if event.type == EventType.COMPETITOR_ACTIVITY_DETECTED:
                await self._handle_competitor_activity_for_ma(event)
            elif event.type == EventType.STRATEGIC_PATTERN_IDENTIFIED:
                await self._handle_strategic_pattern_for_ma(event)
            elif event.type == EventType.THREAT_LEVEL_CHANGED:
                await self._handle_threat_level_change_for_ma(event)
            elif event.type == EventType.MA_THREAT_DETECTED:
                await self._coordinate_ma_threat_response(event)
            elif event.type == EventType.MA_OPPORTUNITY_IDENTIFIED:
                await self._coordinate_ma_opportunity_response(event)
            elif event.type == EventType.MULTI_ENGINE_COORDINATION_REQUIRED:
                await self._handle_multi_engine_coordination(event)
            elif event.type == EventType.ENTERPRISE_RESPONSE_COORDINATED:
                await self._handle_enterprise_response_coordination(event)
                
            self.events_coordinated += 1
            return True
            
        except Exception as e:
            logger.error(f"Error in M&A event coordination: {e}")
            return False

    async def trigger_ma_threat_analysis(
        self, 
        company_profile: Dict, 
        market_context: Dict,
        correlation_id: Optional[str] = None
    ) -> List[AcquisitionThreat]:
        """Trigger M&A threat analysis and publish results"""
        
        # Execute threat detection
        threats = await self.ma_threat_detector.detect_acquisition_threats(
            company_profile,
            market_context,
            monitoring_horizon_months=6
        )
        
        # Publish threat events for high-confidence threats
        for threat in threats:
            if threat.detection_confidence > 0.75:
                await publish_ma_threat_event(
                    threat_data={
                        "threat_id": threat.threat_id,
                        "potential_acquirer": threat.potential_acquirer,
                        "threat_level": threat.threat_level.value,
                        "detection_confidence": threat.detection_confidence,
                        "estimated_approach_date": threat.estimated_approach_date.isoformat(),
                        "predicted_offer_value": float(threat.predicted_offer_value),
                        "financial_capability_score": threat.financial_capability_score,
                        "business_disruption_risk": threat.business_disruption_risk
                    },
                    source_system="ma_intelligence",
                    priority=EventPriority.CRITICAL if threat.detection_confidence > 0.85 else EventPriority.HIGH,
                    correlation_id=correlation_id
                )
        
        return threats

    async def trigger_ma_opportunity_analysis(
        self,
        strategic_objectives: Dict,
        financial_capacity: Dict,
        correlation_id: Optional[str] = None
    ) -> List[AcquisitionOpportunity]:
        """Trigger M&A opportunity analysis and publish results"""
        
        # Execute opportunity identification
        opportunities = await self.ma_threat_detector.identify_strategic_acquisition_opportunities(
            strategic_objectives,
            financial_capacity,
            strategic_objectives.get("target_markets", [])
        )
        
        # Publish opportunity events for high-value opportunities
        for opportunity in opportunities:
            if opportunity.strategic_value_score > 0.70:
                await publish_ma_opportunity_event(
                    opportunity_data={
                        "opportunity_id": opportunity.opportunity_id,
                        "target_company": opportunity.target_company,
                        "opportunity_type": opportunity.opportunity_type,
                        "estimated_target_value": float(opportunity.estimated_target_value),
                        "synergy_value_potential": float(opportunity.synergy_value_potential),
                        "strategic_value_score": opportunity.strategic_value_score,
                        "acquisition_difficulty_score": opportunity.acquisition_difficulty_score,
                        "recommended_approach_strategy": opportunity.recommended_approach_strategy
                    },
                    source_system="ma_intelligence", 
                    priority=EventPriority.HIGH,
                    correlation_id=correlation_id
                )
        
        return opportunities

    async def _handle_competitor_activity_for_ma(self, event):
        """Handle competitor activity that may indicate M&A intentions"""
        try:
            activity_data = event.data
            competitor_id = activity_data.get("competitor_id")
            activity_type = activity_data.get("activity_type")
            
            # Check if activity indicates potential M&A interest
            ma_indicators = [
                "executive_hiring_spree",
                "large_capital_raising",
                "strategic_consultant_engagement",
                "due_diligence_activity",
                "unusual_financial_activity"
            ]
            
            if activity_type in ma_indicators:
                # Trigger focused M&A threat analysis
                company_profile = {
                    "company_name": "current_company",
                    "enterprise_value": 2000000000,  # Would be actual company data
                    "market_segment": activity_data.get("market_segment", "technology")
                }
                
                market_context = {
                    "competitor_activity_detected": True,
                    "competitor_id": competitor_id,
                    "activity_indicators": ma_indicators
                }
                
                threats = await self.trigger_ma_threat_analysis(
                    company_profile,
                    market_context,
                    correlation_id=event.correlation_id
                )
                
                logger.info(f"M&A threat analysis triggered by competitor activity: {competitor_id}")
                
        except Exception as e:
            logger.error(f"Error handling competitor activity for M&A: {e}")

    async def _coordinate_ma_threat_response(self, event):
        """Coordinate enterprise-wide response to M&A threats"""
        try:
            threat_data = event.data
            threat_level = threat_data.get("threat_level")
            confidence = threat_data.get("detection_confidence", 0.0)
            
            # For critical threats, coordinate enterprise-wide response
            if confidence > 0.85 or threat_level in ["hostile_approach", "imminent_takeover"]:
                
                # Coordinate with autonomous strategy engine
                await publish_enterprise_coordination_event(
                    coordination_data={
                        "coordination_type": "ma_threat_response",
                        "threat_id": threat_data.get("threat_id"),
                        "departments_involved": ["legal", "finance", "communications", "operations"],
                        "response_timeline": "<4_hours",
                        "coordination_priority": "critical",
                        "business_impact": {
                            "estimated_value_at_risk": threat_data.get("predicted_offer_value"),
                            "stakeholder_impact": "critical",
                            "response_urgency": "immediate"
                        }
                    },
                    source_system="ma_intelligence",
                    priority=EventPriority.CRITICAL,
                    correlation_id=event.correlation_id
                )
                
                self.enterprise_responses_triggered += 1
                logger.info(f"Enterprise-wide M&A threat response coordinated: {threat_data.get('threat_id')}")
                
        except Exception as e:
            logger.error(f"Error coordinating M&A threat response: {e}")

    async def _coordinate_ma_opportunity_response(self, event):
        """Coordinate evaluation response for M&A opportunities"""
        try:
            opportunity_data = event.data
            strategic_value = opportunity_data.get("strategic_value_score", 0.0)
            estimated_value = opportunity_data.get("estimated_target_value", 0)
            
            # For high-value opportunities, coordinate evaluation process
            if strategic_value > 0.80 or estimated_value > 100000000:  # >$100M
                
                await publish_enterprise_coordination_event(
                    coordination_data={
                        "coordination_type": "ma_opportunity_evaluation",
                        "opportunity_id": opportunity_data.get("opportunity_id"),
                        "departments_involved": ["strategy", "finance", "legal", "operations"],
                        "evaluation_timeline": "30_days",
                        "coordination_priority": "high",
                        "business_impact": {
                            "estimated_acquisition_value": estimated_value,
                            "strategic_value_score": strategic_value,
                            "synergy_potential": opportunity_data.get("synergy_value_potential")
                        }
                    },
                    source_system="ma_intelligence",
                    priority=EventPriority.HIGH,
                    correlation_id=event.correlation_id
                )
                
                logger.info(f"M&A opportunity evaluation coordinated: {opportunity_data.get('opportunity_id')}")
                
        except Exception as e:
            logger.error(f"Error coordinating M&A opportunity response: {e}")

    async def _handle_multi_engine_coordination(self, event):
        """Handle requests for multi-engine coordination involving M&A intelligence"""
        try:
            coordination_data = event.data
            coordination_type = coordination_data.get("coordination_type")
            
            if coordination_type == "ma_defense":
                # Coordinate M&A defense with other engines
                await self._coordinate_ma_defense_with_engines(coordination_data, event.correlation_id)
            elif coordination_type == "ma_opportunity_evaluation":
                # Coordinate M&A opportunity evaluation
                await self._coordinate_ma_opportunity_evaluation(coordination_data, event.correlation_id)
                
            self.cross_engine_responses += 1
            
        except Exception as e:
            logger.error(f"Error in multi-engine coordination: {e}")

    async def _coordinate_ma_defense_with_engines(self, coordination_data: Dict, correlation_id: str):
        """Coordinate M&A defense across enhancement engines"""
        
        # Publish M&A defense execution event
        await publish_ma_defense_event(
            defense_data={
                "threat_id": coordination_data.get("threat_id"),
                "defense_type": "multi_engine_coordination",
                "engines_involved": ["ma_intelligence", "autonomous_strategy", "regulatory_intelligence"],
                "coordination_timeline": coordination_data.get("coordination_deadline"),
                "estimated_value_protection": coordination_data.get("estimated_value_protection", 50000000),
                "defense_strategies_count": 6
            },
            source_system="ma_intelligence",
            priority=EventPriority.CRITICAL,
            correlation_id=correlation_id
        )
        
        logger.info("M&A defense coordinated across enhancement engines")

    async def _coordinate_ma_opportunity_evaluation(self, coordination_data: Dict, correlation_id: str):
        """Coordinate M&A opportunity evaluation process"""
        
        opportunity_data = coordination_data.get("opportunity_data", {})
        
        # Coordinate evaluation across departments and engines
        evaluation_coordination = {
            "coordination_type": "ma_opportunity_due_diligence",
            "opportunity_id": opportunity_data.get("opportunity_id"),
            "evaluation_phases": [
                "financial_analysis",
                "strategic_fit_assessment", 
                "regulatory_impact_analysis",
                "integration_complexity_evaluation"
            ],
            "timeline": "45_days",
            "business_impact": {
                "estimated_opportunity_value": opportunity_data.get("estimated_target_value"),
                "strategic_value_score": opportunity_data.get("strategic_value_score")
            }
        }
        
        await publish_enterprise_coordination_event(
            coordination_data=evaluation_coordination,
            source_system="ma_intelligence",
            priority=EventPriority.HIGH,
            correlation_id=correlation_id
        )
        
        logger.info(f"M&A opportunity evaluation coordinated: {opportunity_data.get('opportunity_id')}")

    async def _handle_strategic_pattern_for_ma(self, event):
        """Handle strategic patterns that may indicate M&A activity"""
        try:
            pattern_data = event.data
            pattern_type = pattern_data.get("pattern_type")
            confidence = pattern_data.get("confidence_score", 0.0)
            
            # Patterns that may indicate M&A activity
            ma_relevant_patterns = [
                "market_consolidation_trend",
                "competitor_expansion_pattern", 
                "industry_transformation_signal",
                "regulatory_change_impact"
            ]
            
            if pattern_type in ma_relevant_patterns and confidence > 0.80:
                # Trigger M&A landscape analysis
                logger.info(f"M&A-relevant strategic pattern detected: {pattern_type}")
                
                # Would trigger appropriate M&A analysis based on pattern type
                
        except Exception as e:
            logger.error(f"Error handling strategic pattern for M&A: {e}")

    async def _handle_threat_level_change_for_ma(self, event):
        """Handle threat level changes that may require M&A analysis"""
        try:
            threat_data = event.data
            new_threat_level = threat_data.get("new_threat_level")
            threat_type = threat_data.get("threat_type")
            
            # If threat level escalates to critical, check for M&A implications
            if new_threat_level in ["critical", "high"] and threat_type == "competitive":
                logger.info("Critical competitive threat detected - evaluating M&A implications")
                
                # Would trigger M&A threat analysis
                
        except Exception as e:
            logger.error(f"Error handling threat level change for M&A: {e}")

    async def _handle_enterprise_response_coordination(self, event):
        """Handle enterprise response coordination that involves M&A intelligence"""
        try:
            coordination_data = event.data
            coordination_type = coordination_data.get("coordination_type")
            
            if "ma_" in coordination_type:
                logger.info(f"Participating in enterprise coordination: {coordination_type}")
                
                # M&A intelligence participation in enterprise response
                
        except Exception as e:
            logger.error(f"Error in enterprise response coordination: {e}")

    def get_coordination_metrics(self) -> Dict:
        """Get M&A event coordination metrics"""
        return {
            "events_coordinated": self.events_coordinated,
            "cross_engine_responses": self.cross_engine_responses,
            "enterprise_responses_triggered": self.enterprise_responses_triggered,
            "is_running": self.is_running
        }

__all__ = [
    "MAEventCoordinator"
]