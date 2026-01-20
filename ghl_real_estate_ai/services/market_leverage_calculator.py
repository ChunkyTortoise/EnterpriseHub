"""
Market Leverage Calculator

Analyzes market conditions, inventory levels, competitive pressure, and buyer positioning
to quantify negotiating leverage and optimal offer positioning.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
from decimal import Decimal

from ghl_real_estate_ai.api.schemas.negotiation import (
    MarketLeverage,
    MarketCondition,
    ListingHistory
)
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.austin_market_service import AustinMarketService
from ghl_real_estate_ai.services.competitive_data_pipeline import get_competitive_data_pipeline

logger = logging.getLogger(__name__)


class MarketLeverageCalculator:
    """
    Calculates buyer's negotiating leverage based on market dynamics,
    property positioning, competitive pressure, and seasonal factors.
    """
    
    def __init__(self):
        self.cache_service = get_cache_service()
        self.market_service = AustinMarketService()
        self.competitive_pipeline = get_competitive_data_pipeline()
    
    async def calculate_market_leverage(
        self,
        property_id: str,
        property_data: Dict[str, Any],
        buyer_profile: Dict[str, Any],
        listing_history: ListingHistory
    ) -> MarketLeverage:
        """
        Calculate comprehensive market leverage analysis for negotiation strategy.
        """
        cache_key = f"market_leverage:{property_id}:v2"
        cached_result = await self.cache_service.get(cache_key)
        
        if cached_result:
            logger.info(f"Returning cached market leverage for {property_id}")
            return MarketLeverage.model_validate(cached_result)
        
        logger.info(f"Calculating market leverage for property {property_id}")
        
        # Parallel analysis of leverage factors
        market_analysis = await self._analyze_market_conditions(property_data)
        inventory_analysis = await self._analyze_inventory_levels(property_data)
        competitive_analysis = await self._analyze_competitive_pressure(property_id, property_data)
        property_analysis = await self._analyze_property_positioning(property_data, listing_history)
        buyer_advantage_analysis = await self._analyze_buyer_advantages(buyer_profile)
        seasonal_analysis = await self._analyze_seasonal_factors()
        
        # Calculate overall leverage score
        leverage_score = self._calculate_overall_leverage_score(
            market_analysis,
            inventory_analysis,
            competitive_analysis,
            property_analysis,
            buyer_advantage_analysis,
            seasonal_analysis
        )
        
        # Synthesize comprehensive leverage analysis
        market_leverage = MarketLeverage(
            overall_leverage_score=leverage_score,
            market_condition=market_analysis["market_condition"],
            inventory_levels=inventory_analysis["inventory_by_range"],
            competitive_pressure=competitive_analysis["pressure_score"],
            seasonal_advantage=seasonal_analysis["seasonal_advantage"],
            property_uniqueness_score=property_analysis["uniqueness_score"],
            comparable_sales_strength=property_analysis["comps_strength"],
            price_positioning=property_analysis["price_positioning"],
            financing_strength=buyer_advantage_analysis["financing_strength"],
            cash_offer_boost=buyer_advantage_analysis["cash_boost"],
            quick_close_advantage=buyer_advantage_analysis["quick_close_boost"]
        )
        
        # Cache result for 1 hour (market conditions change frequently)
        await self.cache_service.set(
            cache_key, 
            market_leverage.model_dump(), 
            ttl=3600
        )
        
        logger.info(f"Market leverage calculation complete: {leverage_score}% overall leverage")
        return market_leverage
    
    async def _analyze_market_conditions(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall market conditions and trends"""
        
        try:
            # Get market metrics from market service
            market_metrics = await self.market_service.get_market_metrics(
                property_data.get("zip_code", "78701")
            )
            
            # Determine market condition
            avg_days_on_market = market_metrics.get("avg_days_on_market", 30)
            price_trend = market_metrics.get("price_trend_3mo", 0)
            inventory_months = market_metrics.get("months_of_inventory", 6)
            
            if inventory_months > 8 or avg_days_on_market > 60:
                market_condition = MarketCondition.BUYERS_MARKET
                buyer_advantage = 25
            elif inventory_months < 3 or avg_days_on_market < 20:
                market_condition = MarketCondition.SELLERS_MARKET
                buyer_advantage = -15
            else:
                market_condition = MarketCondition.BALANCED
                buyer_advantage = 5
            
            # Price trend adjustments
            if price_trend < -2:  # Declining prices
                buyer_advantage += 15
            elif price_trend > 5:  # Rising prices
                buyer_advantage -= 10
            
            return {
                "market_condition": market_condition,
                "buyer_advantage": buyer_advantage,
                "avg_days_on_market": avg_days_on_market,
                "price_trend": price_trend,
                "inventory_months": inventory_months,
                "market_velocity": market_metrics.get("sales_velocity", "moderate")
            }
            
        except Exception as e:
            logger.error(f"Market condition analysis failed: {e}")
            return {
                "market_condition": MarketCondition.BALANCED,
                "buyer_advantage": 0,
                "avg_days_on_market": 30,
                "price_trend": 0,
                "inventory_months": 6,
                "market_velocity": "moderate"
            }
    
    async def _analyze_inventory_levels(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze inventory levels by price range and property type"""
        
        try:
            property_price = property_data.get("list_price", 500000)
            property_type = property_data.get("property_type", "single_family")
            zip_code = property_data.get("zip_code", "78701")
            
            # Define price ranges relative to property price
            price_ranges = {
                "below_range": (property_price * 0.8, property_price * 0.9),
                "target_range": (property_price * 0.9, property_price * 1.1),
                "above_range": (property_price * 1.1, property_price * 1.3)
            }
            
            inventory_by_range = {}
            
            for range_name, (min_price, max_price) in price_ranges.items():
                # Get inventory count for each range
                inventory_data = await self.market_service.get_inventory_analysis(
                    zip_code=zip_code,
                    property_type=property_type,
                    min_price=int(min_price),
                    max_price=int(max_price)
                )
                
                # Calculate months of inventory
                active_listings = inventory_data.get("active_listings", 10)
                monthly_sales = max(inventory_data.get("monthly_sales", 3), 1)
                months_inventory = active_listings / monthly_sales
                
                inventory_by_range[range_name] = months_inventory
            
            # Calculate inventory advantage
            target_inventory = inventory_by_range["target_range"]
            if target_inventory > 8:
                inventory_advantage = 30
            elif target_inventory > 5:
                inventory_advantage = 15
            elif target_inventory < 2:
                inventory_advantage = -20
            else:
                inventory_advantage = 5
            
            return {
                "inventory_by_range": inventory_by_range,
                "inventory_advantage": inventory_advantage,
                "target_range_inventory": target_inventory,
                "inventory_pressure": "high" if target_inventory > 6 else "moderate" if target_inventory > 3 else "low"
            }
            
        except Exception as e:
            logger.error(f"Inventory analysis failed: {e}")
            return {
                "inventory_by_range": {"below_range": 6, "target_range": 6, "above_range": 6},
                "inventory_advantage": 0,
                "target_range_inventory": 6,
                "inventory_pressure": "moderate"
            }
    
    async def _analyze_competitive_pressure(
        self, 
        property_id: str, 
        property_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze competitive pressure from similar properties"""
        
        try:
            # Get competitive properties
            competitive_data = await self.competitive_pipeline.get_competitive_analysis(
                property_id=property_id,
                radius_miles=2,
                similar_criteria={
                    "price_range_pct": 15,
                    "bed_bath_match": True,
                    "property_type": property_data.get("property_type")
                }
            )
            
            similar_properties = competitive_data.get("similar_properties", [])
            
            # Analyze competitive metrics
            recent_listings = len([p for p in similar_properties 
                                 if (datetime.now() - datetime.fromisoformat(p.get("list_date", "2024-01-01"))).days <= 30])
            
            pending_sales = len([p for p in similar_properties 
                               if p.get("status") == "pending"])
            
            price_reductions = len([p for p in similar_properties 
                                  if p.get("price_drops", 0) > 0])
            
            avg_days_on_market = sum(p.get("days_on_market", 30) for p in similar_properties) / max(len(similar_properties), 1)
            
            # Calculate pressure score
            pressure_score = 50  # Base neutral pressure
            
            if recent_listings > 5:
                pressure_score += 20  # More inventory = more buyer leverage
            elif recent_listings < 2:
                pressure_score -= 15  # Less competition
            
            if pending_sales > 3:
                pressure_score -= 25  # Active market reduces buyer leverage
            
            if price_reductions > (len(similar_properties) * 0.4):
                pressure_score += 15  # Many price drops = buyer leverage
            
            if avg_days_on_market > 60:
                pressure_score += 20  # Slow market = buyer leverage
            elif avg_days_on_market < 20:
                pressure_score -= 15  # Fast market = seller leverage
            
            pressure_score = max(0, min(100, pressure_score))
            
            return {
                "pressure_score": pressure_score,
                "recent_listings": recent_listings,
                "pending_sales": pending_sales,
                "price_reductions": price_reductions,
                "avg_days_on_market": avg_days_on_market,
                "competitive_intensity": "high" if pressure_score < 30 else "moderate" if pressure_score < 70 else "low",
                "similar_properties_count": len(similar_properties)
            }
            
        except Exception as e:
            logger.error(f"Competitive analysis failed: {e}")
            return {
                "pressure_score": 50,
                "recent_listings": 3,
                "pending_sales": 2,
                "price_reductions": 1,
                "avg_days_on_market": 30,
                "competitive_intensity": "moderate",
                "similar_properties_count": 5
            }
    
    async def _analyze_property_positioning(
        self, 
        property_data: Dict[str, Any], 
        listing_history: ListingHistory
    ) -> Dict[str, Any]:
        """Analyze how this property is positioned relative to market"""
        
        try:
            # Get comparable sales data
            property_price = listing_history.current_price
            zip_code = property_data.get("zip_code", "78701")
            
            # Get recent comparable sales
            comps_data = await self.market_service.get_comparable_sales(
                zip_code=zip_code,
                bedrooms=property_data.get("bedrooms", 3),
                bathrooms=property_data.get("bathrooms", 2),
                sqft_range=(
                    property_data.get("sqft", 2000) * 0.8,
                    property_data.get("sqft", 2000) * 1.2
                ),
                days_back=90
            )
            
            comparable_sales = comps_data.get("sales", [])
            
            if comparable_sales:
                avg_sale_price = sum(sale.get("sale_price", 0) for sale in comparable_sales) / len(comparable_sales)
                price_per_sqft_comps = sum(sale.get("price_per_sqft", 0) for sale in comparable_sales) / len(comparable_sales)
                property_price_per_sqft = float(property_price) / property_data.get("sqft", 2000)
                
                # Price positioning analysis
                price_variance = (float(property_price) - avg_sale_price) / avg_sale_price * 100
                
                if price_variance > 10:
                    price_positioning = "overpriced"
                    positioning_advantage = 25
                elif price_variance > 5:
                    price_positioning = "above_market"
                    positioning_advantage = 15
                elif price_variance < -5:
                    price_positioning = "underpriced"
                    positioning_advantage = -10
                else:
                    price_positioning = "fairly_priced"
                    positioning_advantage = 5
                
                # Comparable sales strength
                comps_strength = min(len(comparable_sales) / 5 * 100, 100)  # Strong comps = better negotiation position
                
            else:
                price_positioning = "unknown"
                positioning_advantage = 0
                comps_strength = 25  # Weak comps data
            
            # Property uniqueness analysis
            uniqueness_score = self._calculate_property_uniqueness(property_data)
            
            return {
                "price_positioning": price_positioning,
                "positioning_advantage": positioning_advantage,
                "comps_strength": comps_strength,
                "uniqueness_score": uniqueness_score,
                "price_variance_pct": price_variance if comparable_sales else 0,
                "comparable_sales_count": len(comparable_sales)
            }
            
        except Exception as e:
            logger.error(f"Property positioning analysis failed: {e}")
            return {
                "price_positioning": "fairly_priced",
                "positioning_advantage": 0,
                "comps_strength": 50,
                "uniqueness_score": 50,
                "price_variance_pct": 0,
                "comparable_sales_count": 3
            }
    
    def _calculate_property_uniqueness(self, property_data: Dict[str, Any]) -> float:
        """Calculate how unique/rare this property is in the market"""
        
        uniqueness_score = 50.0  # Base score
        
        # Location uniqueness
        if property_data.get("waterfront"):
            uniqueness_score += 30
        if property_data.get("view_type") in ["lake", "mountain", "city"]:
            uniqueness_score += 20
        
        # Property features
        if property_data.get("sqft", 2000) > 4000:
            uniqueness_score += 15
        if property_data.get("bedrooms", 3) > 5:
            uniqueness_score += 10
        if property_data.get("pool"):
            uniqueness_score += 10
        
        # Property type rarity
        property_type = property_data.get("property_type", "single_family")
        if property_type in ["luxury", "estate", "custom"]:
            uniqueness_score += 25
        elif property_type in ["condo", "townhouse"]:
            uniqueness_score -= 10
        
        # Age and condition
        year_built = property_data.get("year_built", 2000)
        if year_built > 2020:
            uniqueness_score += 15  # New construction
        elif year_built < 1950:
            uniqueness_score += 20  # Historic charm
        
        return max(0, min(100, uniqueness_score))
    
    async def _analyze_buyer_advantages(self, buyer_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze buyer's specific advantages in negotiation"""
        
        financing_strength = 50.0
        cash_boost = 0.0
        quick_close_boost = 0.0
        
        # Financing strength analysis
        credit_score = buyer_profile.get("credit_score", 750)
        debt_to_income = buyer_profile.get("debt_to_income", 0.3)
        down_payment_pct = buyer_profile.get("down_payment_percent", 20)
        
        if credit_score > 800:
            financing_strength += 25
        elif credit_score > 740:
            financing_strength += 15
        elif credit_score < 680:
            financing_strength -= 20
        
        if debt_to_income < 0.25:
            financing_strength += 15
        elif debt_to_income > 0.4:
            financing_strength -= 15
        
        if down_payment_pct > 25:
            financing_strength += 10
        elif down_payment_pct < 10:
            financing_strength -= 15
        
        # Cash offer advantages
        if buyer_profile.get("cash_offer", False):
            cash_boost = 25  # Significant advantage
            quick_close_boost = 15  # Can close faster
        elif buyer_profile.get("pre_approved", False):
            financing_strength += 10
        
        # Quick close advantages
        if buyer_profile.get("flexible_timeline", False):
            quick_close_boost += 5
        if buyer_profile.get("current_rental", False):  # No chain to break
            quick_close_boost += 8
        
        # First-time buyer considerations
        if buyer_profile.get("first_time_buyer", False):
            financing_strength -= 5  # Typically weaker position
        
        return {
            "financing_strength": max(0, min(100, financing_strength)),
            "cash_boost": min(25, cash_boost),
            "quick_close_boost": min(15, quick_close_boost),
            "buyer_type": self._classify_buyer_type(buyer_profile),
            "negotiation_strengths": self._identify_buyer_strengths(buyer_profile)
        }
    
    def _classify_buyer_type(self, buyer_profile: Dict[str, Any]) -> str:
        """Classify buyer type for strategic insights"""
        
        if buyer_profile.get("cash_offer"):
            return "cash_buyer"
        elif buyer_profile.get("investor", False):
            return "investor"
        elif buyer_profile.get("first_time_buyer", False):
            return "first_time_buyer"
        elif buyer_profile.get("move_up_buyer", False):
            return "move_up_buyer"
        else:
            return "traditional_buyer"
    
    def _identify_buyer_strengths(self, buyer_profile: Dict[str, Any]) -> List[str]:
        """Identify specific buyer strengths for negotiation"""
        
        strengths = []
        
        if buyer_profile.get("cash_offer"):
            strengths.append("cash_offer")
        if buyer_profile.get("pre_approved"):
            strengths.append("pre_approved_financing")
        if buyer_profile.get("flexible_timeline"):
            strengths.append("flexible_closing")
        if buyer_profile.get("credit_score", 0) > 800:
            strengths.append("excellent_credit")
        if buyer_profile.get("local_buyer", False):
            strengths.append("local_knowledge")
        if not buyer_profile.get("contingent_sale", True):
            strengths.append("no_sale_contingency")
        
        return strengths
    
    async def _analyze_seasonal_factors(self) -> Dict[str, Any]:
        """Analyze seasonal market factors affecting negotiation"""
        
        current_month = datetime.now().month
        
        # Seasonal advantage mapping (buyer perspective)
        seasonal_advantages = {
            1: 15,   # January - slow season
            2: 10,   # February - still slow
            3: 0,    # March - market warming
            4: -5,   # April - spring market starts
            5: -10,  # May - peak selling season
            6: -15,  # June - peak season
            7: -5,   # July - still active
            8: 0,    # August - moderate
            9: 5,    # September - back to school
            10: 10,  # October - fewer buyers
            11: 15,  # November - slow season
            12: 20   # December - holidays slow market
        }
        
        seasonal_advantage = seasonal_advantages.get(current_month, 0)
        
        # Additional seasonal considerations
        is_holiday_season = current_month in [11, 12, 1]
        is_peak_season = current_month in [4, 5, 6, 7]
        is_school_transition = current_month in [8, 9]
        
        seasonal_insights = []
        if is_holiday_season:
            seasonal_insights.append("holiday_season_advantage")
        if is_peak_season:
            seasonal_insights.append("peak_season_competition")
        if is_school_transition:
            seasonal_insights.append("school_year_timing")
        
        return {
            "seasonal_advantage": seasonal_advantage,
            "current_month": current_month,
            "is_holiday_season": is_holiday_season,
            "is_peak_season": is_peak_season,
            "seasonal_insights": seasonal_insights,
            "market_timing": self._get_market_timing_advice(current_month)
        }
    
    def _get_market_timing_advice(self, month: int) -> str:
        """Get market timing advice based on season"""
        
        if month in [11, 12, 1]:
            return "optimal_buyer_timing"
        elif month in [4, 5, 6]:
            return "competitive_season"
        elif month in [2, 3]:
            return "market_warming"
        else:
            return "moderate_timing"
    
    def _calculate_overall_leverage_score(
        self,
        market_analysis: Dict[str, Any],
        inventory_analysis: Dict[str, Any],
        competitive_analysis: Dict[str, Any],
        property_analysis: Dict[str, Any],
        buyer_advantage_analysis: Dict[str, Any],
        seasonal_analysis: Dict[str, Any]
    ) -> float:
        """Calculate weighted overall leverage score"""
        
        # Base score starts neutral
        leverage_score = 50.0
        
        # Weight different factors
        leverage_score += market_analysis["buyer_advantage"] * 0.25
        leverage_score += inventory_analysis["inventory_advantage"] * 0.2
        leverage_score += (competitive_analysis["pressure_score"] - 50) * 0.2
        leverage_score += property_analysis["positioning_advantage"] * 0.15
        leverage_score += (buyer_advantage_analysis["financing_strength"] - 50) * 0.1
        leverage_score += seasonal_analysis["seasonal_advantage"] * 0.1
        
        # Additional adjustments
        if buyer_advantage_analysis["cash_boost"] > 0:
            leverage_score += buyer_advantage_analysis["cash_boost"] * 0.3
        
        if buyer_advantage_analysis["quick_close_boost"] > 0:
            leverage_score += buyer_advantage_analysis["quick_close_boost"] * 0.2
        
        # Property uniqueness adjustment (rare properties reduce leverage)
        if property_analysis["uniqueness_score"] > 80:
            leverage_score -= 15
        elif property_analysis["uniqueness_score"] < 30:
            leverage_score += 10
        
        return max(0, min(100, leverage_score))


# Singleton instance
_market_leverage_calculator = None

def get_market_leverage_calculator() -> MarketLeverageCalculator:
    """Get singleton instance of MarketLeverageCalculator"""
    global _market_leverage_calculator
    if _market_leverage_calculator is None:
        _market_leverage_calculator = MarketLeverageCalculator()
    return _market_leverage_calculator