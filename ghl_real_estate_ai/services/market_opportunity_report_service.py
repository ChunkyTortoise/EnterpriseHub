"""
Market Opportunity Reporting Service - Phase 7
Generates elite-level reports on cross-market trends and high-yield opportunities.

Leverages:
- NationalMarketIntelligence (Hive Mind)
- BusinessIntelligenceReportingEngine
- LLM for narrative generation
"""

from datetime import datetime
from typing import Dict, List

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.business_intelligence_reporting_engine import (
    BusinessReport,
    ReportType,
    get_business_intelligence_engine,
)
from ghl_real_estate_ai.services.national_market_intelligence import get_national_market_intelligence

logger = get_logger(__name__)


class MarketOpportunityReportService:
    """
    Automated reporting service for high-yield market opportunities.
    """

    def __init__(self):
        self.market_intel = get_national_market_intelligence()
        self.bi_engine = get_business_intelligence_engine()

    async def generate_monthly_opportunity_report(self, tenant_id: str) -> BusinessReport:
        """
        Generates a comprehensive report on the top 3 national opportunities
        specifically relevant to the tenant's current lead pool.
        """
        logger.info(f"[{tenant_id}] Generating Monthly Market Opportunity Report...")

        # 1. Fetch top national opportunities
        overview = await self.market_intel.get_national_market_overview()
        top_opps = overview.get("top_opportunities", [])[:3]

        # 2. Get cross-market demand predictions for tenant's primary market
        # (Assuming 'rancho_cucamonga' as primary for now)
        source_market = "rancho_cucamonga"
        hive_mind_insights = []
        for opp in top_opps:
            prediction = await self.market_intel.predict_cross_market_demand(source_market, opp["market_id"])
            if prediction["demand_score"] > 50:
                hive_mind_insights.append(prediction)

        # 3. Use BI Engine to structure the report
        report = BusinessReport(
            template_id="monthly_market_opp",
            report_type=ReportType.MARKET_OPPORTUNITY,
            title=f"Monthly Market Opportunity Analysis - {datetime.now().strftime('%B %Y')}",
            data_summary={
                "top_opportunities": top_opps,
                "hive_mind_insights": hive_mind_insights,
                "tenant_id": tenant_id,
            },
        )

        # 4. Generate AI Narrative
        report.executive_summary = await self._generate_report_narrative(top_opps, hive_mind_insights)

        return report

    async def _generate_report_narrative(self, opportunities: List[Dict], insights: List[Dict]) -> str:
        """
        Uses LLM to turn data points into a visionary executive narrative.
        """
        from ghl_real_estate_ai.core.llm_client import LLMClient

        llm = LLMClient()

        prompt = f"""
        JORGE SYSTEM: EXECUTIVE MARKET BRIEFING
        
        Top Opportunities: {opportunities}
        Hive Mind Insights: {insights}
        
        Draft a high-level executive summary for Jorge. 
        Focus on WHERE the capital should flow this month and WHY. 
        Highlight the tech-migration trends if applicable.
        
        Tone: Visionary, strategic, elite.
        """

        response = await llm.agenerate(
            prompt=prompt,
            system_prompt="You are a Chief Investment Officer for a real estate private equity firm.",
            temperature=0.4,
        )
        return response.content
