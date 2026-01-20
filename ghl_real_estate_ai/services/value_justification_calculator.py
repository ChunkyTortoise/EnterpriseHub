"""
Value Justification Calculator Service

Calculates and demonstrates the ROI and value delivered by premium real estate services
compared to discount brokers, FSBO, and market averages. Provides dynamic pricing
recommendations based on verified performance metrics.

Key Features:
- ROI calculation on agent fees vs. value delivered
- Financial benefit tracking (negotiation savings, market timing, risk prevention)
- Time value quantification (efficiency advantages)
- Outcome optimization measurement (result improvements vs. baseline)
- Competitive advantage demonstration (vs. discount brokers, FSBO)
- Dynamic pricing recommendations based on demonstrated value
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import json

logger = logging.getLogger(__name__)

class ServiceTier(Enum):
    """Service tier types"""
    PREMIUM = "premium"
    STANDARD = "standard"
    BASIC = "basic"

class CompetitorType(Enum):
    """Types of competitors for comparison"""
    DISCOUNT_BROKER = "discount_broker"
    TRADITIONAL_AGENT = "traditional_agent"
    FSBO = "fsbo"
    ONLINE_PLATFORM = "online_platform"

@dataclass
class ValueCalculation:
    """Individual value calculation result"""
    calculation_type: str
    description: str
    value_amount: float
    confidence_score: float
    supporting_data: Dict[str, Any]
    calculation_method: str
    timestamp: datetime

@dataclass
class CompetitiveAnalysis:
    """Competitive analysis against different service types"""
    competitor_type: CompetitorType
    cost_difference: float
    value_difference: float
    net_benefit: float
    risk_factors: List[str]
    success_rate_difference: float
    time_difference_days: float

@dataclass
class ServiceTierRecommendation:
    """Service tier and pricing recommendation"""
    recommended_tier: ServiceTier
    recommended_rate: float
    confidence_level: float
    justification_factors: List[str]
    expected_client_roi: float
    competitive_positioning: str
    risk_assessment: str

@dataclass
class ValueJustificationReport:
    """Comprehensive value justification report"""
    agent_id: str
    client_id: Optional[str]
    property_value: float
    current_commission_rate: float
    recommended_commission_rate: float
    
    # Value calculations
    negotiation_value: ValueCalculation
    time_value: ValueCalculation
    risk_prevention_value: ValueCalculation
    market_timing_value: ValueCalculation
    expertise_value: ValueCalculation
    
    # Total calculations
    total_value_delivered: float
    total_fees: float
    net_client_benefit: float
    roi_percentage: float
    
    # Competitive analysis
    competitive_comparisons: List[CompetitiveAnalysis]
    
    # Recommendations
    service_recommendation: ServiceTierRecommendation
    
    # Supporting data
    calculation_details: Dict[str, Any]
    confidence_metrics: Dict[str, float]
    report_generated_at: datetime

class ValueJustificationCalculator:
    """
    Value Justification Calculator
    
    Calculates and demonstrates the ROI and value delivered by premium
    real estate services with competitive analysis and pricing recommendations.
    """
    
    def __init__(self):
        # Market baseline data (would be updated from real market sources)
        self.market_baselines = {
            "average_commission_rate": 0.03,  # 3%
            "discount_broker_rate": 0.015,    # 1.5%
            "fsbo_success_rate": 0.65,        # 65% successful sales
            "agent_success_rate": 0.95,       # 95% successful sales
            "average_days_on_market": 24,
            "average_negotiation_percentage": 0.94,  # 94% of asking
            "average_transaction_issues": 0.35,      # 35% have issues
        }
        
        # Value calculation parameters
        self.value_parameters = {
            "time_value_per_day": 150,        # Value of time savings per day
            "stress_reduction_value": 2000,   # Value of stress reduction
            "legal_issue_prevention": 5000,   # Avg cost of legal issues
            "financing_optimization": 3000,   # Avg financing optimization value
            "marketing_effectiveness": 1.15,  # 15% better marketing reach
            "negotiation_expertise": 1.03,    # 3% better negotiation outcomes
        }
        
        # Risk factors and their typical costs
        self.risk_factors = {
            "contract_errors": 3500,
            "disclosure_issues": 8000,
            "financing_problems": 2500,
            "inspection_disputes": 1800,
            "title_issues": 4200,
            "appraisal_challenges": 2000,
            "closing_delays": 500,  # per day
        }

    async def calculate_comprehensive_value_justification(
        self,
        agent_id: str,
        agent_performance_metrics: Dict[str, float],
        property_value: float,
        proposed_commission_rate: float,
        client_id: Optional[str] = None,
        market_conditions: Optional[Dict[str, float]] = None
    ) -> ValueJustificationReport:
        """
        Calculate comprehensive value justification with ROI analysis
        
        Args:
            agent_id: Agent identifier
            agent_performance_metrics: Agent's verified performance data
            property_value: Property value for calculation
            proposed_commission_rate: Proposed commission rate
            client_id: Optional client identifier
            market_conditions: Optional current market condition data
            
        Returns:
            ValueJustificationReport: Comprehensive value analysis
        """
        try:
            # Calculate individual value components
            negotiation_value = await self._calculate_negotiation_value(
                agent_performance_metrics, property_value
            )
            
            time_value = await self._calculate_time_value(
                agent_performance_metrics, property_value
            )
            
            risk_prevention_value = await self._calculate_risk_prevention_value(
                agent_performance_metrics, property_value
            )
            
            market_timing_value = await self._calculate_market_timing_value(
                agent_performance_metrics, property_value, market_conditions
            )
            
            expertise_value = await self._calculate_expertise_value(
                agent_performance_metrics, property_value
            )
            
            # Calculate totals
            total_value_delivered = sum([
                negotiation_value.value_amount,
                time_value.value_amount,
                risk_prevention_value.value_amount,
                market_timing_value.value_amount,
                expertise_value.value_amount
            ])
            
            total_fees = property_value * proposed_commission_rate
            net_client_benefit = total_value_delivered - total_fees
            roi_percentage = (net_client_benefit / total_fees * 100) if total_fees > 0 else 0
            
            # Competitive analysis
            competitive_comparisons = await self._perform_competitive_analysis(
                agent_performance_metrics, property_value, proposed_commission_rate
            )
            
            # Service recommendation
            service_recommendation = await self._generate_service_recommendation(
                agent_performance_metrics, total_value_delivered, total_fees, roi_percentage
            )
            
            # Calculate confidence metrics
            confidence_metrics = await self._calculate_confidence_metrics(
                agent_performance_metrics, [
                    negotiation_value, time_value, risk_prevention_value,
                    market_timing_value, expertise_value
                ]
            )
            
            # Recommended commission rate
            recommended_rate = await self._calculate_recommended_commission_rate(
                agent_performance_metrics, total_value_delivered, property_value
            )
            
            report = ValueJustificationReport(
                agent_id=agent_id,
                client_id=client_id,
                property_value=property_value,
                current_commission_rate=proposed_commission_rate,
                recommended_commission_rate=recommended_rate,
                negotiation_value=negotiation_value,
                time_value=time_value,
                risk_prevention_value=risk_prevention_value,
                market_timing_value=market_timing_value,
                expertise_value=expertise_value,
                total_value_delivered=total_value_delivered,
                total_fees=total_fees,
                net_client_benefit=net_client_benefit,
                roi_percentage=roi_percentage,
                competitive_comparisons=competitive_comparisons,
                service_recommendation=service_recommendation,
                calculation_details=await self._get_calculation_details(agent_performance_metrics),
                confidence_metrics=confidence_metrics,
                report_generated_at=datetime.now()
            )
            
            logger.info(f"Generated value justification report for agent {agent_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error calculating value justification: {e}")
            raise

    async def compare_service_tiers(
        self,
        agent_performance_metrics: Dict[str, float],
        property_value: float
    ) -> Dict[ServiceTier, Dict[str, Any]]:
        """
        Compare different service tiers with value propositions
        
        Args:
            agent_performance_metrics: Agent's performance data
            property_value: Property value for calculations
            
        Returns:
            Dict: Service tier comparisons with value propositions
        """
        try:
            tier_comparisons = {}
            
            # Define service tier characteristics
            tier_configs = {
                ServiceTier.PREMIUM: {
                    "commission_rate": 0.035,
                    "service_level": 1.0,
                    "performance_multiplier": 1.0,
                    "features": [
                        "Full-service professional representation",
                        "AI-powered market analysis",
                        "Professional photography & marketing",
                        "Negotiation expertise & strategy",
                        "Transaction management & support",
                        "24/7 client communication",
                        "Risk mitigation & legal protection"
                    ]
                },
                ServiceTier.STANDARD: {
                    "commission_rate": 0.025,
                    "service_level": 0.75,
                    "performance_multiplier": 0.85,
                    "features": [
                        "Professional representation",
                        "Basic market analysis",
                        "Standard marketing package",
                        "Negotiation support",
                        "Basic transaction management"
                    ]
                },
                ServiceTier.BASIC: {
                    "commission_rate": 0.015,
                    "service_level": 0.5,
                    "performance_multiplier": 0.65,
                    "features": [
                        "MLS listing",
                        "Basic marketing",
                        "Limited support",
                        "Standard contracts"
                    ]
                }
            }
            
            for tier, config in tier_configs.items():
                # Calculate adjusted performance metrics for tier
                adjusted_metrics = {
                    key: value * config["performance_multiplier"]
                    for key, value in agent_performance_metrics.items()
                }
                
                # Calculate value for this tier
                report = await self.calculate_comprehensive_value_justification(
                    "tier_comparison",
                    adjusted_metrics,
                    property_value,
                    config["commission_rate"]
                )
                
                tier_comparisons[tier] = {
                    "commission_rate": config["commission_rate"],
                    "commission_amount": property_value * config["commission_rate"],
                    "total_value_delivered": report.total_value_delivered,
                    "net_client_benefit": report.net_client_benefit,
                    "roi_percentage": report.roi_percentage,
                    "service_level": config["service_level"],
                    "features": config["features"],
                    "value_per_dollar": report.total_value_delivered / (property_value * config["commission_rate"]) if config["commission_rate"] > 0 else 0
                }
            
            return tier_comparisons
            
        except Exception as e:
            logger.error(f"Error comparing service tiers: {e}")
            raise

    async def calculate_competitive_roi(
        self,
        agent_performance_metrics: Dict[str, float],
        property_value: float,
        competitor_type: CompetitorType
    ) -> Dict[str, Any]:
        """
        Calculate ROI comparison against specific competitor type
        
        Args:
            agent_performance_metrics: Agent's performance metrics
            property_value: Property value
            competitor_type: Type of competitor for comparison
            
        Returns:
            Dict: Detailed competitive ROI analysis
        """
        try:
            # Define competitor characteristics
            competitor_configs = {
                CompetitorType.DISCOUNT_BROKER: {
                    "commission_rate": 0.015,
                    "success_rate": 0.85,
                    "avg_days_market": 35,
                    "negotiation_performance": 0.91,
                    "service_quality": 0.6,
                    "risk_level": 0.4  # Higher risk
                },
                CompetitorType.TRADITIONAL_AGENT: {
                    "commission_rate": 0.03,
                    "success_rate": 0.92,
                    "avg_days_market": 24,
                    "negotiation_performance": 0.94,
                    "service_quality": 0.8,
                    "risk_level": 0.2
                },
                CompetitorType.FSBO: {
                    "commission_rate": 0.0,
                    "success_rate": 0.65,
                    "avg_days_market": 45,
                    "negotiation_performance": 0.87,
                    "service_quality": 0.3,
                    "risk_level": 0.7  # Highest risk
                },
                CompetitorType.ONLINE_PLATFORM: {
                    "commission_rate": 0.01,
                    "success_rate": 0.78,
                    "avg_days_market": 40,
                    "negotiation_performance": 0.89,
                    "service_quality": 0.5,
                    "risk_level": 0.5
                }
            }
            
            if competitor_type not in competitor_configs:
                raise ValueError(f"Unknown competitor type: {competitor_type}")
                
            competitor = competitor_configs[competitor_type]
            
            # Calculate agent value
            agent_commission = property_value * agent_performance_metrics.get("commission_rate", 0.035)
            agent_value = await self._calculate_total_agent_value(agent_performance_metrics, property_value)
            
            # Calculate competitor costs and outcomes
            competitor_commission = property_value * competitor["commission_rate"]
            
            # Calculate outcome differences
            negotiation_diff = (
                agent_performance_metrics.get("negotiation_performance", 0.97) - 
                competitor["negotiation_performance"]
            ) * property_value
            
            time_diff_days = competitor["avg_days_market"] - agent_performance_metrics.get("avg_days_market", 18)
            time_value_diff = time_diff_days * self.value_parameters["time_value_per_day"]
            
            # Calculate risk differences
            agent_risk_cost = self._calculate_expected_risk_cost(0.1)  # Agent has low risk
            competitor_risk_cost = self._calculate_expected_risk_cost(competitor["risk_level"])
            risk_value_diff = competitor_risk_cost - agent_risk_cost
            
            # Calculate success rate impact
            success_rate_diff = agent_performance_metrics.get("success_rate", 0.95) - competitor["success_rate"]
            success_value_diff = success_rate_diff * property_value * 0.1  # Cost of failed sale
            
            # Total comparison
            total_value_difference = negotiation_diff + time_value_diff + risk_value_diff + success_value_diff
            cost_difference = agent_commission - competitor_commission
            net_benefit = total_value_difference - cost_difference
            
            roi_analysis = {
                "competitor_type": competitor_type.value,
                "cost_comparison": {
                    "agent_commission": agent_commission,
                    "competitor_commission": competitor_commission,
                    "cost_difference": cost_difference,
                    "cost_difference_percentage": (cost_difference / competitor_commission * 100) if competitor_commission > 0 else float('inf')
                },
                "value_comparison": {
                    "negotiation_value_diff": negotiation_diff,
                    "time_value_diff": time_value_diff,
                    "risk_value_diff": risk_value_diff,
                    "success_rate_value_diff": success_value_diff,
                    "total_value_difference": total_value_difference
                },
                "net_analysis": {
                    "net_benefit": net_benefit,
                    "roi_percentage": (net_benefit / cost_difference * 100) if cost_difference > 0 else float('inf'),
                    "break_even_commission_rate": (total_value_difference + competitor_commission) / property_value,
                    "value_justification": net_benefit > 0
                },
                "risk_analysis": {
                    "agent_risk_level": 0.1,
                    "competitor_risk_level": competitor["risk_level"],
                    "risk_difference": competitor["risk_level"] - 0.1,
                    "expected_risk_cost_difference": risk_value_diff
                },
                "service_comparison": {
                    "agent_service_quality": agent_performance_metrics.get("service_quality", 0.95),
                    "competitor_service_quality": competitor["service_quality"],
                    "service_advantage": agent_performance_metrics.get("service_quality", 0.95) - competitor["service_quality"]
                }
            }
            
            return roi_analysis
            
        except Exception as e:
            logger.error(f"Error calculating competitive ROI: {e}")
            raise

    # Private helper methods
    
    async def _calculate_negotiation_value(
        self,
        metrics: Dict[str, float],
        property_value: float
    ) -> ValueCalculation:
        """Calculate value from superior negotiation performance"""
        
        agent_negotiation = metrics.get("negotiation_performance", 0.97)
        market_average = self.market_baselines["average_negotiation_percentage"]
        
        negotiation_advantage = agent_negotiation - market_average
        value_amount = negotiation_advantage * property_value
        
        # Confidence based on data quality and sample size
        confidence_score = min(0.95, 0.7 + (metrics.get("transaction_count", 0) * 0.05))
        
        return ValueCalculation(
            calculation_type="negotiation_value",
            description="Additional value achieved through superior negotiation performance",
            value_amount=value_amount,
            confidence_score=confidence_score,
            supporting_data={
                "agent_performance": agent_negotiation,
                "market_average": market_average,
                "performance_advantage": negotiation_advantage,
                "property_value": property_value
            },
            calculation_method="performance_differential_analysis",
            timestamp=datetime.now()
        )

    async def _calculate_time_value(
        self,
        metrics: Dict[str, float],
        property_value: float
    ) -> ValueCalculation:
        """Calculate value from time savings"""
        
        agent_days = metrics.get("avg_days_market", 18)
        market_average_days = self.market_baselines["average_days_on_market"]
        
        days_saved = max(0, market_average_days - agent_days)
        value_amount = days_saved * self.value_parameters["time_value_per_day"]
        
        # Add stress reduction value for faster sales
        if days_saved > 5:
            value_amount += self.value_parameters["stress_reduction_value"]
        
        confidence_score = 0.9  # Time data is typically very reliable
        
        return ValueCalculation(
            calculation_type="time_value",
            description="Value of time savings through efficient process and faster sales",
            value_amount=value_amount,
            confidence_score=confidence_score,
            supporting_data={
                "agent_avg_days": agent_days,
                "market_avg_days": market_average_days,
                "days_saved": days_saved,
                "daily_value": self.value_parameters["time_value_per_day"]
            },
            calculation_method="time_differential_analysis",
            timestamp=datetime.now()
        )

    async def _calculate_risk_prevention_value(
        self,
        metrics: Dict[str, float],
        property_value: float
    ) -> ValueCalculation:
        """Calculate value from risk prevention and issue avoidance"""
        
        agent_issue_rate = metrics.get("transaction_issue_rate", 0.05)  # 5% issue rate
        market_issue_rate = self.market_baselines["average_transaction_issues"]  # 35% issue rate
        
        issue_rate_reduction = market_issue_rate - agent_issue_rate
        
        # Calculate expected cost savings from avoided issues
        avg_issue_cost = statistics.mean(self.risk_factors.values())
        value_amount = issue_rate_reduction * avg_issue_cost
        
        # Add specific high-value risk prevention
        value_amount += self.value_parameters["legal_issue_prevention"] * (issue_rate_reduction * 0.3)
        
        confidence_score = 0.8  # Risk data can be harder to quantify
        
        return ValueCalculation(
            calculation_type="risk_prevention_value",
            description="Value from preventing legal issues, contract problems, and transaction failures",
            value_amount=value_amount,
            confidence_score=confidence_score,
            supporting_data={
                "agent_issue_rate": agent_issue_rate,
                "market_issue_rate": market_issue_rate,
                "risk_reduction": issue_rate_reduction,
                "avg_issue_cost": avg_issue_cost,
                "risk_factors": list(self.risk_factors.keys())
            },
            calculation_method="risk_analysis_actuarial",
            timestamp=datetime.now()
        )

    async def _calculate_market_timing_value(
        self,
        metrics: Dict[str, float],
        property_value: float,
        market_conditions: Optional[Dict[str, float]] = None
    ) -> ValueCalculation:
        """Calculate value from market timing and pricing strategy"""
        
        # Base value from optimal market timing
        timing_advantage = metrics.get("market_timing_accuracy", 0.85)
        market_volatility = 0.02 if not market_conditions else market_conditions.get("volatility", 0.02)
        
        # Value from avoiding poor timing
        value_amount = timing_advantage * market_volatility * property_value
        
        # Add value from pricing strategy optimization
        pricing_optimization = metrics.get("pricing_accuracy", 0.9)
        value_amount += (pricing_optimization - 0.8) * property_value * 0.01
        
        confidence_score = 0.75  # Market timing is inherently uncertain
        
        return ValueCalculation(
            calculation_type="market_timing_value",
            description="Value from optimal market timing and pricing strategy",
            value_amount=value_amount,
            confidence_score=confidence_score,
            supporting_data={
                "timing_advantage": timing_advantage,
                "market_volatility": market_volatility,
                "pricing_optimization": pricing_optimization,
                "market_conditions": market_conditions or {}
            },
            calculation_method="market_analysis_optimization",
            timestamp=datetime.now()
        )

    async def _calculate_expertise_value(
        self,
        metrics: Dict[str, float],
        property_value: float
    ) -> ValueCalculation:
        """Calculate value from professional expertise and services"""
        
        # Marketing effectiveness value
        marketing_effectiveness = metrics.get("marketing_reach_multiplier", 1.15)
        marketing_value = (marketing_effectiveness - 1.0) * property_value * 0.02
        
        # Financing optimization value
        financing_success_rate = metrics.get("financing_success_rate", 0.95)
        financing_value = (financing_success_rate - 0.85) * self.value_parameters["financing_optimization"]
        
        # Professional network value
        network_advantage = metrics.get("professional_network_score", 0.8)
        network_value = network_advantage * property_value * 0.005
        
        value_amount = marketing_value + financing_value + network_value
        confidence_score = 0.85
        
        return ValueCalculation(
            calculation_type="expertise_value",
            description="Value from professional expertise, marketing, and industry connections",
            value_amount=value_amount,
            confidence_score=confidence_score,
            supporting_data={
                "marketing_effectiveness": marketing_effectiveness,
                "financing_success_rate": financing_success_rate,
                "network_advantage": network_advantage,
                "marketing_value": marketing_value,
                "financing_value": financing_value,
                "network_value": network_value
            },
            calculation_method="expertise_analysis_composite",
            timestamp=datetime.now()
        )

    async def _perform_competitive_analysis(
        self,
        metrics: Dict[str, float],
        property_value: float,
        commission_rate: float
    ) -> List[CompetitiveAnalysis]:
        """Perform competitive analysis against different service types"""
        
        analyses = []
        
        for competitor_type in CompetitorType:
            roi_analysis = await self.calculate_competitive_roi(metrics, property_value, competitor_type)
            
            analysis = CompetitiveAnalysis(
                competitor_type=competitor_type,
                cost_difference=roi_analysis["cost_comparison"]["cost_difference"],
                value_difference=roi_analysis["value_comparison"]["total_value_difference"],
                net_benefit=roi_analysis["net_analysis"]["net_benefit"],
                risk_factors=await self._get_competitor_risk_factors(competitor_type),
                success_rate_difference=roi_analysis["service_comparison"]["service_advantage"],
                time_difference_days=roi_analysis["value_comparison"]["time_value_diff"] / self.value_parameters["time_value_per_day"]
            )
            
            analyses.append(analysis)
        
        return analyses

    async def _generate_service_recommendation(
        self,
        metrics: Dict[str, float],
        total_value: float,
        total_fees: float,
        roi_percentage: float
    ) -> ServiceTierRecommendation:
        """Generate service tier and pricing recommendation"""
        
        # Determine recommended tier based on performance and value
        performance_score = metrics.get("overall_performance_score", 85)
        
        if performance_score >= 90 and roi_percentage >= 200:
            recommended_tier = ServiceTier.PREMIUM
            justified_rate = 0.035
            positioning = "Ultra-premium service with verified exceptional results"
        elif performance_score >= 80 and roi_percentage >= 150:
            recommended_tier = ServiceTier.PREMIUM
            justified_rate = 0.032
            positioning = "Premium service with strong value demonstration"
        elif performance_score >= 70 and roi_percentage >= 100:
            recommended_tier = ServiceTier.STANDARD
            justified_rate = 0.025
            positioning = "Professional service with solid value proposition"
        else:
            recommended_tier = ServiceTier.BASIC
            justified_rate = 0.02
            positioning = "Competitive service at market rates"
        
        # Calculate confidence level
        confidence_level = min(0.95, 0.5 + (roi_percentage / 400))  # Higher ROI = higher confidence
        
        # Generate justification factors
        justification_factors = []
        if roi_percentage > 200:
            justification_factors.append("Exceptional ROI demonstrates clear value superiority")
        if metrics.get("client_satisfaction", 4.5) > 4.7:
            justification_factors.append("Superior client satisfaction ratings")
        if metrics.get("negotiation_performance", 0.94) > 0.96:
            justification_factors.append("Proven superior negotiation outcomes")
        if metrics.get("avg_days_market", 24) < 20:
            justification_factors.append("Significantly faster transaction times")
        
        # Risk assessment
        if roi_percentage < 100:
            risk_assessment = "Medium risk - ROI below optimal threshold"
        elif roi_percentage < 150:
            risk_assessment = "Low risk - Solid value proposition"
        else:
            risk_assessment = "Very low risk - Strong value demonstration"
        
        return ServiceTierRecommendation(
            recommended_tier=recommended_tier,
            recommended_rate=justified_rate,
            confidence_level=confidence_level,
            justification_factors=justification_factors,
            expected_client_roi=roi_percentage,
            competitive_positioning=positioning,
            risk_assessment=risk_assessment
        )

    async def _calculate_confidence_metrics(
        self,
        metrics: Dict[str, float],
        value_calculations: List[ValueCalculation]
    ) -> Dict[str, float]:
        """Calculate confidence metrics for the value calculations"""
        
        # Overall confidence based on data quality and volume
        data_quality = metrics.get("data_verification_rate", 0.85)
        sample_size_factor = min(1.0, metrics.get("transaction_count", 0) / 20)  # 20+ transactions = full confidence
        
        overall_confidence = (data_quality + sample_size_factor) / 2
        
        # Individual calculation confidence
        calculation_confidence = {
            calc.calculation_type: calc.confidence_score
            for calc in value_calculations
        }
        
        # Weighted average confidence
        total_value = sum(calc.value_amount for calc in value_calculations)
        if total_value > 0:
            weighted_confidence = sum(
                calc.confidence_score * (calc.value_amount / total_value)
                for calc in value_calculations
            )
        else:
            weighted_confidence = overall_confidence
        
        return {
            "overall_confidence": overall_confidence,
            "data_quality_score": data_quality,
            "sample_size_factor": sample_size_factor,
            "weighted_calculation_confidence": weighted_confidence,
            **calculation_confidence
        }

    async def _calculate_recommended_commission_rate(
        self,
        metrics: Dict[str, float],
        total_value: float,
        property_value: float
    ) -> float:
        """Calculate recommended commission rate based on value delivered"""
        
        # Base rate calculation: value-based pricing
        value_based_rate = (total_value * 0.3) / property_value  # 30% of value as commission
        
        # Performance-based adjustment
        performance_multiplier = metrics.get("overall_performance_score", 85) / 85
        performance_adjusted_rate = self.market_baselines["average_commission_rate"] * performance_multiplier
        
        # Take the average of value-based and performance-based rates
        recommended_rate = (value_based_rate + performance_adjusted_rate) / 2
        
        # Ensure within reasonable bounds
        min_rate = 0.02  # 2% minimum
        max_rate = 0.05  # 5% maximum
        
        return max(min_rate, min(max_rate, recommended_rate))

    async def _calculate_total_agent_value(
        self,
        metrics: Dict[str, float],
        property_value: float
    ) -> float:
        """Calculate total value delivered by agent"""
        
        # This would call all the individual value calculation methods
        # and sum them up. Simplified for brevity.
        return property_value * 0.08  # 8% total value

    def _calculate_expected_risk_cost(self, risk_level: float) -> float:
        """Calculate expected cost from risk level"""
        
        total_risk_cost = sum(self.risk_factors.values())
        return risk_level * total_risk_cost

    async def _get_competitor_risk_factors(self, competitor_type: CompetitorType) -> List[str]:
        """Get risk factors for competitor type"""
        
        risk_factors = {
            CompetitorType.DISCOUNT_BROKER: [
                "Limited support and guidance",
                "Potential contract errors",
                "Reduced marketing exposure",
                "Higher transaction failure risk"
            ],
            CompetitorType.FSBO: [
                "Legal liability exposure",
                "Pricing and negotiation inexperience",
                "Limited marketing reach",
                "Contract and disclosure errors",
                "Financing complications"
            ],
            CompetitorType.ONLINE_PLATFORM: [
                "Automated processes may miss issues",
                "Limited local market knowledge",
                "Reduced personal attention",
                "Technology dependencies"
            ],
            CompetitorType.TRADITIONAL_AGENT: [
                "Variable service quality",
                "Potential technology gaps",
                "Standard market approaches"
            ]
        }
        
        return risk_factors.get(competitor_type, [])

    async def _get_calculation_details(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Get detailed calculation methodology and assumptions"""
        
        return {
            "methodology": "Multi-factor value analysis with competitive benchmarking",
            "data_sources": ["Transaction records", "Market analysis", "Client feedback"],
            "assumptions": {
                "time_value_per_day": self.value_parameters["time_value_per_day"],
                "market_baselines": self.market_baselines,
                "risk_factors": self.risk_factors
            },
            "calculation_date": datetime.now().isoformat(),
            "version": "1.0"
        }

# Global instance
_value_justification_calculator = None

def get_value_justification_calculator() -> ValueJustificationCalculator:
    """Get global value justification calculator instance"""
    global _value_justification_calculator
    if _value_justification_calculator is None:
        _value_justification_calculator = ValueJustificationCalculator()
    return _value_justification_calculator