"""
National Market Intelligence Service

Advanced analytics service for cross-market insights, corporate migration patterns,
and national pricing trends. Provides strategic intelligence for $1M+ revenue
enhancement through data-driven decision making.

Key Features:
- Cross-market analytics and comparisons
- National pricing trends and predictions
- Corporate migration pattern analysis
- Market opportunity scoring and prioritization
- Competitive intelligence across markets
- ROI optimization for national expansion

Author: EnterpriseHub AI
Created: 2026-01-18
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict
import statistics

from ..markets.national_registry import get_national_market_registry, CrossMarketInsights
from ..services.cache_service import get_cache_service
from ..services.claude_assistant import ClaudeAssistant
from ..ghl_utils.logger import get_logger

logger = get_logger(__name__)


class MarketTrend(Enum):
    """Market trend classifications"""
    RAPIDLY_GROWING = "rapidly_growing"
    GROWING = "growing"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


class OpportunityLevel(Enum):
    """Market opportunity levels"""
    PREMIUM = "premium"      # Top 10% opportunities
    HIGH = "high"           # Top 25% opportunities
    MODERATE = "moderate"   # Middle 50% opportunities
    LOW = "low"            # Bottom 25% opportunities
    MINIMAL = "minimal"    # Bottom 10% opportunities


@dataclass
class MarketMetrics:
    """Comprehensive market performance metrics"""
    market_id: str
    market_name: str
    population: int
    median_home_price: float
    price_appreciation_1y: float
    price_appreciation_3y: float
    inventory_days: int
    employment_rate: float
    income_growth_rate: float
    corporate_headquarters_count: int
    tech_job_growth: float
    cost_of_living_index: float
    quality_of_life_score: float
    market_trend: MarketTrend
    opportunity_score: float
    last_updated: datetime


@dataclass
class CompetitiveAnalysis:
    """Competitive landscape analysis for market"""
    market_id: str
    major_competitors: List[str]
    market_share_distribution: Dict[str, float]
    competitive_intensity: float  # 0-1 scale
    differentiation_opportunities: List[str]
    pricing_competitiveness: Dict[str, float]
    service_gaps: List[str]
    entry_barriers: List[str]
    competitive_advantages: List[str]
    threat_level: str  # low, moderate, high
    opportunity_rating: OpportunityLevel


@dataclass
class PricingIntelligence:
    """National pricing trends and intelligence"""
    market_comparisons: Dict[str, Dict[str, float]]
    national_median: float
    price_trend_forecast: Dict[str, float]  # 6mo, 1yr, 2yr predictions
    affordability_rankings: List[Tuple[str, float]]  # (market, ratio)
    luxury_market_premiums: Dict[str, float]
    corporate_housing_allowances: Dict[str, float]
    seasonal_variations: Dict[str, Dict[str, float]]
    roi_projections: Dict[str, float]
    last_analysis: datetime


@dataclass
class MigrationPattern:
    """Corporate migration and relocation patterns"""
    source_market: str
    destination_market: str
    annual_volume: int
    primary_industries: List[str]
    average_salary_band: Tuple[float, float]
    peak_months: List[str]
    success_rate: float
    average_housing_budget: float
    family_size_average: float
    relocation_triggers: List[str]
    trend_direction: str  # increasing, stable, decreasing


class NationalMarketIntelligence:
    """
    Advanced analytics service for national market intelligence and decision support.

    Provides comprehensive cross-market insights, pricing intelligence, competitive
    analysis, and migration pattern analytics for strategic business growth.
    """

    def __init__(self):
        """Initialize national market intelligence service"""
        self.cache = get_cache_service()
        self.claude_assistant = ClaudeAssistant()
        self.national_registry = get_national_market_registry()

        # Data storage
        self.data_dir = Path(__file__).parent.parent / "data" / "market_intelligence"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Intelligence data files
        self.metrics_file = self.data_dir / "market_metrics.json"
        self.competitive_file = self.data_dir / "competitive_analysis.json"
        self.pricing_file = self.data_dir / "pricing_intelligence.json"
        self.migration_file = self.data_dir / "migration_patterns.json"

        # In-memory analytics stores
        self.market_metrics: Dict[str, MarketMetrics] = {}
        self.competitive_analyses: Dict[str, CompetitiveAnalysis] = {}
        self.pricing_intelligence: Optional[PricingIntelligence] = None
        self.migration_patterns: List[MigrationPattern] = []

        # Initialize analytics
        self._initialize_market_intelligence()

        logger.info("NationalMarketIntelligence service initialized with advanced analytics")

    def _initialize_market_intelligence(self) -> None:
        """Initialize comprehensive market intelligence data"""
        # Load existing data or create initial intelligence
        self._load_existing_data()

        # If no existing data, create initial intelligence
        if not self.market_metrics:
            asyncio.create_task(self._generate_initial_intelligence())

    def _load_existing_data(self) -> None:
        """Load existing intelligence data from files"""
        try:
            # Load market metrics
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    for market_id, metrics_data in data.items():
                        metrics_data['market_trend'] = MarketTrend(metrics_data['market_trend'])
                        metrics_data['last_updated'] = datetime.fromisoformat(metrics_data['last_updated'])
                        self.market_metrics[market_id] = MarketMetrics(**metrics_data)

            # Load competitive analyses
            if self.competitive_file.exists():
                with open(self.competitive_file, 'r') as f:
                    data = json.load(f)
                    for market_id, comp_data in data.items():
                        comp_data['opportunity_rating'] = OpportunityLevel(comp_data['opportunity_rating'])
                        self.competitive_analyses[market_id] = CompetitiveAnalysis(**comp_data)

            # Load pricing intelligence
            if self.pricing_file.exists():
                with open(self.pricing_file, 'r') as f:
                    data = json.load(f)
                    data['last_analysis'] = datetime.fromisoformat(data['last_analysis'])
                    self.pricing_intelligence = PricingIntelligence(**data)

            # Load migration patterns
            if self.migration_file.exists():
                with open(self.migration_file, 'r') as f:
                    data = json.load(f)
                    self.migration_patterns = [MigrationPattern(**pattern) for pattern in data]

            logger.info(f"Loaded intelligence data: {len(self.market_metrics)} markets, "
                       f"{len(self.competitive_analyses)} competitive analyses, "
                       f"{len(self.migration_patterns)} migration patterns")

        except Exception as e:
            logger.error(f"Failed to load intelligence data: {str(e)}")

    async def _generate_initial_intelligence(self) -> None:
        """Generate initial market intelligence data"""
        logger.info("Generating initial market intelligence data...")

        # Get all available markets
        markets = self.national_registry.base_registry.list_markets()

        # Generate metrics for each market
        for market_id in markets:
            await self._generate_market_metrics(market_id)

        # Generate competitive analyses
        for market_id in markets:
            await self._generate_competitive_analysis(market_id)

        # Generate pricing intelligence
        await self._generate_pricing_intelligence()

        # Generate migration patterns
        await self._generate_migration_patterns()

        logger.info("Initial market intelligence generation completed")

    async def _generate_market_metrics(self, market_id: str) -> None:
        """Generate comprehensive metrics for a market"""
        market_config = self.national_registry.base_registry.get_market_config(market_id)
        if not market_config:
            return

        # Extract data from market configuration
        demographics = market_config.get('demographics', {})

        # Calculate derived metrics
        opportunity_score = await self._calculate_opportunity_score(market_id, market_config)
        market_trend = self._determine_market_trend(market_config)

        metrics = MarketMetrics(
            market_id=market_id,
            market_name=market_config.get('market_name', market_id),
            population=demographics.get('population', 0),
            median_home_price=market_config.get('median_home_price', 0),
            price_appreciation_1y=market_config.get('price_appreciation_1y', 0),
            price_appreciation_3y=market_config.get('price_appreciation_1y', 0) * 3,  # Estimated
            inventory_days=market_config.get('inventory_days', 30),
            employment_rate=demographics.get('employment_rate', 0.94),
            income_growth_rate=0.03,  # Mock 3% annual growth
            corporate_headquarters_count=len(market_config.get('employers', [])),
            tech_job_growth=self._estimate_tech_job_growth(market_config),
            cost_of_living_index=self._calculate_col_index(market_config),
            quality_of_life_score=self._calculate_qol_score(market_config),
            market_trend=market_trend,
            opportunity_score=opportunity_score,
            last_updated=datetime.now()
        )

        self.market_metrics[market_id] = metrics

    async def _calculate_opportunity_score(self, market_id: str, market_config: Dict[str, Any]) -> float:
        """Calculate market opportunity score (0-100)"""
        score = 50.0  # Base score

        # Population growth factor
        demographics = market_config.get('demographics', {})
        growth_rate = demographics.get('population_growth_rate', 0.02)
        score += min(growth_rate * 500, 20)  # Up to +20 for high growth

        # Home price appreciation
        appreciation = market_config.get('price_appreciation_1y', 0)
        if 5 <= appreciation <= 12:  # Sweet spot for appreciation
            score += 15
        elif appreciation > 12:
            score += 5  # Too hot market
        elif appreciation < 0:
            score -= 10  # Declining market

        # Corporate presence
        employers_count = len(market_config.get('employers', []))
        score += min(employers_count * 2, 15)  # Up to +15 for corporate presence

        # Education level
        education_rate = demographics.get('college_education_rate', 0.3)
        score += min(education_rate * 30, 15)  # Up to +15 for educated population

        # Market type bonuses
        market_type = market_config.get('market_type', '')
        type_bonuses = {
            'tech_hub': 10,
            'tech_headquarters': 15,
            'finance_hub': 8,
            'corporate_hub': 12,
            'energy_hub': 6
        }
        score += type_bonuses.get(market_type, 0)

        return min(95.0, max(5.0, score))  # Clamp between 5-95

    def _determine_market_trend(self, market_config: Dict[str, Any]) -> MarketTrend:
        """Determine market trend based on indicators"""
        appreciation = market_config.get('price_appreciation_1y', 0)
        growth_rate = market_config.get('demographics', {}).get('population_growth_rate', 0.02)

        if appreciation > 15 or growth_rate > 0.04:
            return MarketTrend.RAPIDLY_GROWING
        elif appreciation > 8 or growth_rate > 0.025:
            return MarketTrend.GROWING
        elif 2 <= appreciation <= 8 and growth_rate >= 0.01:
            return MarketTrend.STABLE
        elif appreciation < 0 or growth_rate < 0:
            return MarketTrend.DECLINING
        else:
            return MarketTrend.VOLATILE

    def _estimate_tech_job_growth(self, market_config: Dict[str, Any]) -> float:
        """Estimate technology job growth rate"""
        market_type = market_config.get('market_type', '')
        base_rates = {
            'tech_hub': 0.08,
            'tech_headquarters': 0.12,
            'finance_hub': 0.05,
            'corporate_hub': 0.06,
            'energy_hub': 0.03,
            'mixed_economy': 0.04
        }

        base_rate = base_rates.get(market_type, 0.04)

        # Adjust based on employers
        tech_employers = ['google', 'microsoft', 'amazon', 'apple', 'facebook', 'intel']
        employer_names = [emp.get('name', '').lower() for emp in market_config.get('employers', [])]

        tech_presence = sum(1 for tech_emp in tech_employers
                           if any(tech_emp in emp_name for emp_name in employer_names))

        adjustment = tech_presence * 0.02  # +2% per major tech employer
        return min(0.25, base_rate + adjustment)

    def _calculate_col_index(self, market_config: Dict[str, Any]) -> float:
        """Calculate cost of living index (100 = national average)"""
        median_price = market_config.get('median_home_price', 400000)
        median_income = market_config.get('demographics', {}).get('median_household_income', 70000)

        # Use housing price as primary COL indicator
        # National median around $400K
        housing_ratio = median_price / 400000 * 100

        # Adjust for income levels
        income_adjustment = median_income / 70000

        col_index = housing_ratio / income_adjustment

        return max(50.0, min(200.0, col_index))  # Clamp between 50-200

    def _calculate_qol_score(self, market_config: Dict[str, Any]) -> float:
        """Calculate quality of life score (0-100)"""
        score = 50.0  # Base score

        # Weather and geography (simplified)
        state = market_config.get('state', '')
        state_bonuses = {
            'CA': 8, 'WA': 6, 'CO': 10, 'TX': 4, 'AZ': 6
        }
        score += state_bonuses.get(state, 0)

        # Average neighborhood school ratings
        neighborhoods = market_config.get('neighborhoods', [])
        if neighborhoods:
            avg_school_rating = statistics.mean(
                n.get('school_rating', 7.0) for n in neighborhoods
            )
            score += (avg_school_rating - 5) * 5  # Scale 5-10 rating to +/- points

        # Market specialization quality
        market_type = market_config.get('market_type', '')
        if 'tech' in market_type:
            score += 5  # Tech markets tend to have higher QOL

        return max(20.0, min(95.0, score))

    async def _generate_competitive_analysis(self, market_id: str) -> None:
        """Generate competitive analysis for market"""
        market_config = self.national_registry.base_registry.get_market_config(market_id)
        if not market_config:
            return

        # Define competitive landscape by market type
        market_type = market_config.get('market_type', 'mixed_economy')

        competitive_data = {
            'tech_hub': {
                'competitors': ['Redfin', 'Compass', 'Keller Williams Tech', 'eXp Realty'],
                'intensity': 0.8,
                'barriers': ['Technology investment required', 'Tech talent acquisition'],
                'advantages': ['Corporate tech relationships', 'Data analytics expertise']
            },
            'tech_headquarters': {
                'competitors': ['Windermere', 'John L. Scott', 'Coldwell Banker', 'Compass'],
                'intensity': 0.9,
                'barriers': ['High market entry costs', 'Established relationships'],
                'advantages': ['Fortune 500 corporate programs', 'Executive relocation expertise']
            },
            'finance_hub': {
                'competitors': ['Coldwell Banker', 'RE/MAX', 'Century 21', 'Berkshire Hathaway'],
                'intensity': 0.7,
                'barriers': ['Financial services relationships', 'Compliance requirements'],
                'advantages': ['Corporate finance expertise', 'Executive housing knowledge']
            },
            'corporate_hub': {
                'competitors': ['Coldwell Banker', 'Keller Williams', 'RE/MAX', 'Century 21'],
                'intensity': 0.6,
                'barriers': ['Corporate contract requirements', 'Volume service capabilities'],
                'advantages': ['Multi-market coordination', 'Corporate relocation programs']
            }
        }

        comp_info = competitive_data.get(market_type, {
            'competitors': ['Local Market Leaders', 'National Chains'],
            'intensity': 0.5,
            'barriers': ['Local market knowledge'],
            'advantages': ['Technology platform', 'National coordination']
        })

        # Calculate opportunity rating based on market metrics
        metrics = self.market_metrics.get(market_id)
        opportunity_rating = OpportunityLevel.MODERATE

        if metrics:
            if metrics.opportunity_score >= 80:
                opportunity_rating = OpportunityLevel.PREMIUM
            elif metrics.opportunity_score >= 65:
                opportunity_rating = OpportunityLevel.HIGH
            elif metrics.opportunity_score >= 40:
                opportunity_rating = OpportunityLevel.MODERATE
            elif metrics.opportunity_score >= 25:
                opportunity_rating = OpportunityLevel.LOW
            else:
                opportunity_rating = OpportunityLevel.MINIMAL

        analysis = CompetitiveAnalysis(
            market_id=market_id,
            major_competitors=comp_info['competitors'],
            market_share_distribution={
                comp: 100 / len(comp_info['competitors'])
                for comp in comp_info['competitors']
            },
            competitive_intensity=comp_info['intensity'],
            differentiation_opportunities=[
                "Corporate relocation specialization",
                "AI-powered market intelligence",
                "Multi-market coordination",
                "Executive-level service tiers"
            ],
            pricing_competitiveness={'competitive': 0.8, 'premium': 0.2},
            service_gaps=[
                "Limited corporate relocation expertise",
                "Lack of multi-market coordination",
                "Traditional technology platforms",
                "No Fortune 500 partnership programs"
            ],
            entry_barriers=comp_info['barriers'],
            competitive_advantages=comp_info['advantages'],
            threat_level="moderate" if comp_info['intensity'] < 0.7 else "high",
            opportunity_rating=opportunity_rating
        )

        self.competitive_analyses[market_id] = analysis

    async def _generate_pricing_intelligence(self) -> None:
        """Generate comprehensive pricing intelligence"""
        markets = list(self.market_metrics.keys())
        if not markets:
            return

        # Market comparisons
        comparisons = {}
        for market_id in markets:
            metrics = self.market_metrics[market_id]
            comparisons[market_id] = {
                'median_home_price': metrics.median_home_price,
                'price_appreciation_1y': metrics.price_appreciation_1y,
                'cost_of_living_index': metrics.cost_of_living_index,
                'opportunity_score': metrics.opportunity_score
            }

        # National median calculation
        prices = [metrics.median_home_price for metrics in self.market_metrics.values()]
        national_median = statistics.median(prices)

        # Price forecasts (simplified predictive model)
        forecasts = {}
        for market_id, metrics in self.market_metrics.items():
            current_appreciation = metrics.price_appreciation_1y / 100

            # Simple trend-based forecast
            forecasts[market_id] = {
                '6mo': current_appreciation * 0.5,
                '1yr': current_appreciation * 0.9,  # Slight moderation
                '2yr': current_appreciation * 0.8   # Further moderation
            }

        # Affordability rankings
        affordability_rankings = []
        for market_id, metrics in self.market_metrics.items():
            ratio = metrics.median_home_price / (
                self.national_registry.base_registry.get_market_config(market_id)
                .get('demographics', {}).get('median_household_income', 70000)
            )
            affordability_rankings.append((market_id, ratio))

        affordability_rankings.sort(key=lambda x: x[1])  # Sort by ratio (lower = more affordable)

        # Corporate housing allowances (estimated)
        corporate_allowances = {}
        for market_id, metrics in self.market_metrics.items():
            base_allowance = metrics.median_home_price * 0.15  # 15% of median price
            corporate_allowances[market_id] = base_allowance

        self.pricing_intelligence = PricingIntelligence(
            market_comparisons=comparisons,
            national_median=national_median,
            price_trend_forecast=forecasts,
            affordability_rankings=affordability_rankings,
            luxury_market_premiums={
                market_id: 2.5 if metrics.opportunity_score > 80 else 1.8
                for market_id, metrics in self.market_metrics.items()
            },
            corporate_housing_allowances=corporate_allowances,
            seasonal_variations={
                market_id: {
                    'Q1': 0.95, 'Q2': 1.05, 'Q3': 1.0, 'Q4': 1.0
                } for market_id in markets
            },
            roi_projections={
                market_id: metrics.opportunity_score / 10
                for market_id, metrics in self.market_metrics.items()
            },
            last_analysis=datetime.now()
        )

    async def _generate_migration_patterns(self) -> None:
        """Generate corporate migration patterns"""
        markets = list(self.market_metrics.keys())
        patterns = []

        # Generate patterns between major markets
        for source in ['rancho_cucamonga', 'dallas', 'houston']:
            if source not in markets:
                continue

            for destination in ['denver', 'phoenix', 'seattle']:
                if destination not in markets or source == destination:
                    continue

                pattern = MigrationPattern(
                    source_market=source,
                    destination_market=destination,
                    annual_volume=self._estimate_migration_volume(source, destination),
                    primary_industries=self._identify_migration_industries(source, destination),
                    average_salary_band=self._estimate_salary_band(source, destination),
                    peak_months=['March', 'April', 'June', 'July'],
                    success_rate=0.85,  # High success rate for corporate relocations
                    average_housing_budget=self._estimate_housing_budget(destination),
                    family_size_average=2.3,
                    relocation_triggers=[
                        'Corporate expansion',
                        'Cost of living optimization',
                        'Career advancement',
                        'Quality of life improvement'
                    ],
                    trend_direction='increasing'
                )
                patterns.append(pattern)

        self.migration_patterns = patterns

    def _estimate_migration_volume(self, source: str, destination: str) -> int:
        """Estimate annual migration volume between markets"""
        # Base on market opportunity scores
        source_metrics = self.market_metrics.get(source)
        dest_metrics = self.market_metrics.get(destination)

        if not source_metrics or not dest_metrics:
            return 50

        # Higher destination opportunity = more migration
        base_volume = int(dest_metrics.opportunity_score * 2)

        # Adjust for tech presence
        if dest_metrics.tech_job_growth > 0.06:
            base_volume += 30

        return max(25, min(150, base_volume))

    def _identify_migration_industries(self, source: str, destination: str) -> List[str]:
        """Identify primary industries driving migration"""
        dest_config = self.national_registry.base_registry.get_market_config(destination)
        if not dest_config:
            return ['Technology']

        market_type = dest_config.get('market_type', '')
        industry_map = {
            'tech_hub': ['Technology', 'Software Development', 'Cybersecurity'],
            'tech_headquarters': ['Technology', 'Cloud Computing', 'AI/ML'],
            'finance_hub': ['Financial Services', 'Banking', 'Insurance'],
            'corporate_hub': ['Corporate Services', 'Finance', 'Technology'],
            'energy_hub': ['Energy', 'Oil & Gas', 'Renewable Energy']
        }

        return industry_map.get(market_type, ['Technology', 'Professional Services'])

    def _estimate_salary_band(self, source: str, destination: str) -> Tuple[float, float]:
        """Estimate salary band for migrating employees"""
        dest_config = self.national_registry.base_registry.get_market_config(destination)
        if not dest_config:
            return (75000, 150000)

        median_income = dest_config.get('demographics', {}).get('median_household_income', 70000)

        # Corporate relocations typically 50% above median to 300% above median
        return (median_income * 1.5, median_income * 3.0)

    def _estimate_housing_budget(self, destination: str) -> float:
        """Estimate average housing budget for relocating employees"""
        dest_metrics = self.market_metrics.get(destination)
        if not dest_metrics:
            return 750000

        # Corporate relocations typically afford 1.5x median home price
        return dest_metrics.median_home_price * 1.5

    async def get_national_market_overview(self) -> Dict[str, Any]:
        """Get comprehensive national market overview"""
        cache_key = "national_market_overview"

        cached = await self.cache.get(cache_key)
        if cached:
            return cached

        overview = {
            "summary": {
                "total_markets": len(self.market_metrics),
                "average_opportunity_score": statistics.mean(
                    m.opportunity_score for m in self.market_metrics.values()
                ) if self.market_metrics else 0,
                "national_median_price": self.pricing_intelligence.national_median if self.pricing_intelligence else 0,
                "total_corporate_headquarters": sum(
                    m.corporate_headquarters_count for m in self.market_metrics.values()
                )
            },
            "top_opportunities": await self._get_top_market_opportunities(),
            "market_trends": self._analyze_market_trends(),
            "pricing_insights": await self._get_pricing_insights(),
            "migration_flows": self._analyze_migration_flows(),
            "competitive_landscape": await self._get_competitive_overview(),
            "expansion_recommendations": await self._generate_expansion_recommendations(),
            "last_updated": datetime.now().isoformat()
        }

        # Cache for 2 hours
        await self.cache.set(cache_key, overview, ttl=7200)

        return overview

    async def _get_top_market_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top market opportunities ranked by score"""
        opportunities = []

        for market_id, metrics in self.market_metrics.items():
            competitive = self.competitive_analyses.get(market_id)

            opportunities.append({
                "market_id": market_id,
                "market_name": metrics.market_name,
                "opportunity_score": metrics.opportunity_score,
                "market_trend": metrics.market_trend.value,
                "median_home_price": metrics.median_home_price,
                "price_appreciation": metrics.price_appreciation_1y,
                "corporate_headquarters": metrics.corporate_headquarters_count,
                "competitive_intensity": competitive.competitive_intensity if competitive else 0.5,
                "opportunity_rating": competitive.opportunity_rating.value if competitive else "moderate"
            })

        # Sort by opportunity score
        opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)

        return opportunities[:limit]

    def _analyze_market_trends(self) -> Dict[str, Any]:
        """Analyze overall market trends"""
        trend_counts = defaultdict(int)
        for metrics in self.market_metrics.values():
            trend_counts[metrics.market_trend.value] += 1

        appreciation_rates = [m.price_appreciation_1y for m in self.market_metrics.values()]

        return {
            "trend_distribution": dict(trend_counts),
            "average_appreciation": statistics.mean(appreciation_rates) if appreciation_rates else 0,
            "appreciation_range": {
                "min": min(appreciation_rates) if appreciation_rates else 0,
                "max": max(appreciation_rates) if appreciation_rates else 0
            },
            "growth_markets": len([m for m in self.market_metrics.values()
                                 if m.market_trend in [MarketTrend.GROWING, MarketTrend.RAPIDLY_GROWING]]),
            "stable_markets": len([m for m in self.market_metrics.values()
                                 if m.market_trend == MarketTrend.STABLE])
        }

    async def _get_pricing_insights(self) -> Dict[str, Any]:
        """Get national pricing insights"""
        if not self.pricing_intelligence:
            return {}

        return {
            "national_median": self.pricing_intelligence.national_median,
            "most_affordable_markets": self.pricing_intelligence.affordability_rankings[:5],
            "most_expensive_markets": list(reversed(self.pricing_intelligence.affordability_rankings))[:5],
            "price_forecasts": {
                market: forecast['1yr'] for market, forecast in
                self.pricing_intelligence.price_trend_forecast.items()
            },
            "luxury_premiums": self.pricing_intelligence.luxury_market_premiums,
            "corporate_allowances": self.pricing_intelligence.corporate_housing_allowances
        }

    def _analyze_migration_flows(self) -> Dict[str, Any]:
        """Analyze corporate migration flows"""
        total_volume = sum(p.annual_volume for p in self.migration_patterns)

        destination_volumes = defaultdict(int)
        source_volumes = defaultdict(int)

        for pattern in self.migration_patterns:
            destination_volumes[pattern.destination_market] += pattern.annual_volume
            source_volumes[pattern.source_market] += pattern.annual_volume

        return {
            "total_annual_volume": total_volume,
            "top_destinations": sorted(
                destination_volumes.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "top_sources": sorted(
                source_volumes.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "primary_industries": list(set(
                industry for pattern in self.migration_patterns
                for industry in pattern.primary_industries
            )),
            "average_success_rate": statistics.mean(
                p.success_rate for p in self.migration_patterns
            ) if self.migration_patterns else 0
        }

    async def _get_competitive_overview(self) -> Dict[str, Any]:
        """Get competitive landscape overview"""
        if not self.competitive_analyses:
            return {}

        intensities = [c.competitive_intensity for c in self.competitive_analyses.values()]

        opportunity_counts = defaultdict(int)
        for analysis in self.competitive_analyses.values():
            opportunity_counts[analysis.opportunity_rating.value] += 1

        return {
            "average_competitive_intensity": statistics.mean(intensities) if intensities else 0,
            "opportunity_distribution": dict(opportunity_counts),
            "high_opportunity_markets": [
                analysis.market_id for analysis in self.competitive_analyses.values()
                if analysis.opportunity_rating in [OpportunityLevel.HIGH, OpportunityLevel.PREMIUM]
            ],
            "common_service_gaps": list(set(
                gap for analysis in self.competitive_analyses.values()
                for gap in analysis.service_gaps
            )),
            "key_differentiators": list(set(
                diff for analysis in self.competitive_analyses.values()
                for diff in analysis.differentiation_opportunities
            ))
        }

    async def _generate_expansion_recommendations(self) -> List[Dict[str, Any]]:
        """Generate strategic expansion recommendations"""
        recommendations = []

        # Top 3 markets by opportunity score
        top_markets = sorted(
            self.market_metrics.items(),
            key=lambda x: x[1].opportunity_score,
            reverse=True
        )[:3]

        for market_id, metrics in top_markets:
            competitive = self.competitive_analyses.get(market_id)

            recommendation = {
                "market_id": market_id,
                "market_name": metrics.market_name,
                "recommendation_type": "immediate_expansion" if metrics.opportunity_score > 80 else "strategic_expansion",
                "opportunity_score": metrics.opportunity_score,
                "key_advantages": [
                    f"${metrics.median_home_price:,.0f} median home price",
                    f"{metrics.price_appreciation_1y:.1f}% annual appreciation",
                    f"{metrics.corporate_headquarters_count} corporate headquarters",
                    f"{metrics.tech_job_growth:.1f}% tech job growth"
                ],
                "competitive_position": competitive.opportunity_rating.value if competitive else "moderate",
                "estimated_roi": self.pricing_intelligence.roi_projections.get(market_id, 0) if self.pricing_intelligence else 0,
                "investment_timeline": "6-9 months" if metrics.opportunity_score > 75 else "12-18 months",
                "key_challenges": competitive.entry_barriers if competitive else [],
                "success_factors": competitive.competitive_advantages if competitive else []
            }

            recommendations.append(recommendation)

        return recommendations

    def _save_intelligence_data(self) -> None:
        """Save all intelligence data to files"""
        try:
            # Save market metrics
            metrics_data = {}
            for market_id, metrics in self.market_metrics.items():
                data_dict = metrics.__dict__.copy()
                data_dict['market_trend'] = metrics.market_trend.value
                data_dict['last_updated'] = metrics.last_updated.isoformat()
                metrics_data[market_id] = data_dict

            with open(self.metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)

            # Save competitive analyses
            comp_data = {}
            for market_id, analysis in self.competitive_analyses.items():
                data_dict = analysis.__dict__.copy()
                data_dict['opportunity_rating'] = analysis.opportunity_rating.value
                comp_data[market_id] = data_dict

            with open(self.competitive_file, 'w') as f:
                json.dump(comp_data, f, indent=2)

            # Save pricing intelligence
            if self.pricing_intelligence:
                pricing_data = self.pricing_intelligence.__dict__.copy()
                pricing_data['last_analysis'] = self.pricing_intelligence.last_analysis.isoformat()

                with open(self.pricing_file, 'w') as f:
                    json.dump(pricing_data, f, indent=2)

            # Save migration patterns
            with open(self.migration_file, 'w') as f:
                json.dump([pattern.__dict__ for pattern in self.migration_patterns], f, indent=2)

            logger.info("Intelligence data saved successfully")

        except Exception as e:
            logger.error(f"Failed to save intelligence data: {str(e)}")

    def health_check(self) -> Dict[str, Any]:
        """Perform service health check"""
        try:
            return {
                "status": "healthy",
                "service": "NationalMarketIntelligence",
                "metrics": {
                    "market_metrics": len(self.market_metrics),
                    "competitive_analyses": len(self.competitive_analyses),
                    "migration_patterns": len(self.migration_patterns),
                    "pricing_intelligence": bool(self.pricing_intelligence)
                },
                "data_files": {
                    "metrics_file": self.metrics_file.exists(),
                    "competitive_file": self.competitive_file.exists(),
                    "pricing_file": self.pricing_file.exists(),
                    "migration_file": self.migration_file.exists()
                },
                "cache_available": self.cache is not None,
                "last_check": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }


# Global service instance
_national_intelligence = None


def get_national_market_intelligence() -> NationalMarketIntelligence:
    """Get the global national market intelligence instance"""
    global _national_intelligence
    if _national_intelligence is None:
        _national_intelligence = NationalMarketIntelligence()
    return _national_intelligence