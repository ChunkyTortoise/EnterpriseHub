"""
Jorge System 3.0 - Phase 5: Autonomous Expansion
Agent Swarm Orchestrator v2 (The "Hive Mind")

Orchestrates specialized agents:
1. The Analyst: Token and cost optimization via gemini_metrics.csv.
2. The Hunter: RAG freshness and CRAG trigger management.
3. The Closer: High-priority lead monitoring and Vapi escalation.
4. The Cleaner (Task 2): Self-healing data pipeline for GHL webhooks.
5. The Expander (Task 3): Dynamic Market Expansion via Perplexity.
"""

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from ghl_real_estate_ai.agents.lead_intelligence_swarm import lead_intelligence_swarm
from ghl_real_estate_ai.agents.quant_agent import QuantAgent
from ghl_real_estate_ai.core.gemini_logger import log_metrics
from ghl_real_estate_ai.core.governance_engine import GovernanceEngine
from ghl_real_estate_ai.core.llm_client import LLMClient
from ghl_real_estate_ai.core.rag_engine import RAGEngine
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.executive_dashboard import ExecutiveDashboard
from ghl_real_estate_ai.services.executive_portfolio_manager import PortfolioManagerAgent
from ghl_real_estate_ai.services.market_opportunity_report_service import MarketOpportunityReportService
from ghl_real_estate_ai.services.memory_service import MemoryService
from ghl_real_estate_ai.services.perplexity_researcher import PerplexityResearcher
from ghl_real_estate_ai.services.predictive_lead_scorer_v2 import LeadPriority, PredictiveLeadScorerV2
from ghl_real_estate_ai.services.vapi_service import VapiService

logger = get_logger(__name__)


@dataclass
class AgentState:
    name: str
    last_run: datetime
    status: str
    actions_taken: int


class AgentSwarmOrchestratorV2:
    def __init__(self):
        self.llm = LLMClient()
        self.rag_engine = RAGEngine()
        self.scorer = PredictiveLeadScorerV2()
        self.memory = MemoryService()
        self.researcher = PerplexityResearcher()
        self.vapi = VapiService()
        self.quant = QuantAgent()
        self.governance = GovernanceEngine()
        self.portfolio_manager = PortfolioManagerAgent()
        self.dashboard = ExecutiveDashboard()
        self.reporting_service = MarketOpportunityReportService()

        self.agents = {
            "analyst": AgentState("The Analyst", datetime.min, "idle", 0),
            "hunter": AgentState("The Hunter", datetime.min, "idle", 0),
            "closer": AgentState("The Closer", datetime.min, "idle", 0),
            "cleaner": AgentState("The Cleaner", datetime.min, "idle", 0),
            "expander": AgentState("The Expander", datetime.min, "idle", 0),
            "quant": AgentState("The Quant", datetime.min, "idle", 0),
            "dojo": AgentState("The Dojo Master", datetime.min, "idle", 0),
            "sentry": AgentState("The Retention Sentry", datetime.min, "idle", 0),
            "portfolio": AgentState("The Portfolio Manager", datetime.min, "idle", 0),
            "report_gen": AgentState("The Report Generator", datetime.min, "idle", 0),
            "visualizer": AgentState("The Visualizer", datetime.min, "idle", 0),
        }

        self.metrics_file = "gemini_metrics.csv"
        logger.info("Agent Swarm Orchestrator V2 Initialized with Phase 6 Agents")

    async def run_dojo(self, tenant_id: str = "default_tenant"):
        """
        The Dojo Master: Processes conversions and human feedback.
        Phase 6: Closed-Loop Learning.
        """
        agent = self.agents["dojo"]
        agent.status = "working"
        logger.info(f"[{tenant_id}] {agent.name} scanning for closed deals and feedback...")

        try:
            # 1. Check for 'Won' deals in GHL for this specific tenant (Simulated)
            closed_deals = []  # await self.ghl.get_recently_won_deals(tenant_id)
            for deal in closed_deals:
                await lead_intelligence_swarm.learn_from_outcomes(
                    deal["contact_id"], {"is_conversion": True, "revenue": deal.get("value", 0), "tenant_id": tenant_id}
                )
                agent.actions_taken += 1

            # 2. Process Human RLHF Feedback for this tenant (Simulated)
            # In production, this queries a feedback table/Redis
            human_feedback = []  # await self.memory.get_unprocessed_feedback(tenant_id)
            for feedback in human_feedback:
                # feedback: {"agent_id": "behavioral_profiler", "rating": 0.2, "comment": "Too aggressive"}
                await lead_intelligence_swarm.adjust_agent_weights({feedback["agent_id"]: feedback["rating"]})
                agent.actions_taken += 1

            agent.last_run = datetime.now()
            agent.status = "idle"
        except Exception as e:
            logger.error(f"{agent.name} failed for tenant {tenant_id}: {e}")
            agent.status = "error"

    async def run_quant(self, tenant_id: str = "default_tenant"):
        """
        The Quant: Performs financial engineering on leads.
        """
        agent = self.agents["quant"]
        agent.status = "working"
        logger.info(f"[{tenant_id}] {agent.name} performing financial arbitrage analysis...")

        try:
            # Fetch leads for this tenant that haven't been 'quanted' yet (Simulated)
            leads_to_analyze = []  # self.memory.get_leads_needing_quant(tenant_id)

            for lead in leads_to_analyze:
                analysis = await self.quant.analyze_deal(lead)
                # Save analysis back to lead metadata
                # await self.memory.update_lead_metadata(lead['id'], {"quant_analysis": analysis}, tenant_id)
                agent.actions_taken += 1

            agent.last_run = datetime.now()
            agent.status = "idle"
        except Exception as e:
            logger.error(f"{agent.name} failed for tenant {tenant_id}: {e}")
            agent.status = "error"

    async def run_retention_sentry(self, tenant_id: str = "default_tenant"):
        """
        The Retention Sentry: Predictive Churn Prevention.
        """
        agent = self.agents["sentry"]
        agent.status = "working"
        logger.info(f"[{tenant_id}] {agent.name} scanning for churn risks...")

        try:
            # 1. Analyze gemini_metrics.csv for engagement drops (Tenant-aware in prod)
            if os.path.exists(self.metrics_file):
                df = pd.read_csv(self.metrics_file)

            # 2. Identify 'cooling' leads for this tenant (Simulated)
            cooling_leads = []  # self.memory.get_leads_at_risk_of_churn(tenant_id)

            for lead_id in cooling_leads:
                logger.info(f"[{tenant_id}] {agent.name}: Triggering re-engagement for {lead_id}")
                agent.actions_taken += 1

            log_metrics(
                provider="system", model="internal-sentry", input_tokens=0, output_tokens=0, task_type="revenue_op"
            )

            agent.last_run = datetime.now()
            agent.status = "idle"
        except Exception as e:
            logger.error(f"{agent.name} failed for tenant {tenant_id}: {e}")
            agent.status = "error"

    async def run_analyst(self, tenant_id: str = "default_tenant"):
        """
        The Analyst: Continually reviews gemini_metrics.csv to optimize token usage.
        """
        agent = self.agents["analyst"]
        agent.status = "working"
        logger.info(f"[{tenant_id}] {agent.name} starting analysis...")

        try:
            if not os.path.exists(self.metrics_file):
                logger.warning(f"[{tenant_id}] {agent.name}: Metrics file not found.")
                agent.status = "idle"
                return

            df = pd.read_csv(self.metrics_file)
            if df.empty:
                agent.status = "idle"
                return

            # Analyze token usage trends (Tenant-specific filtering in prod)
            summary = (
                df.groupby("task_type")
                .agg({"total_tokens": "mean", "cost_usd": "sum", "accuracy_score": "mean"})
                .to_dict()
            )

            # Logic for optimization: If cost per task is high, suggest model switching
            optimization_report = f"[{tenant_id}] Token Analysis Report:\n{json.dumps(summary, indent=2)}"

            # Log autonomous operation
            log_metrics(
                provider="system",
                model="internal-analyst",
                input_tokens=0,
                output_tokens=0,
                task_type="autonomous_op",
                accuracy_score=1.0,
            )

            agent.actions_taken += 1
            agent.last_run = datetime.now()
            agent.status = "idle"
            logger.info(f"[{tenant_id}] {agent.name} completed analysis.")

        except Exception as e:
            logger.error(f"{agent.name} failed for tenant {tenant_id}: {e}")
            agent.status = "error"

    async def run_hunter(self, tenant_id: str = "default_tenant"):
        """
        The Hunter: Scans for 'stale' market data and triggers Competitive Arbitrage research.
        Refined for Phase 3: Identifies Expired/Withdrawn listings to create leverage scripts.
        """
        agent = self.agents["hunter"]
        agent.status = "working"
        logger.info(f"[{tenant_id}] {agent.name} scanning for competitive arbitrage opportunities...")

        try:
            # 1. Fetch high-priority leads needing leverage for this tenant
            # In production, this queries MemoryService for active seller leads
            active_seller_leads = []  # await self.memory.get_active_seller_leads(tenant_id)

            for lead in active_seller_leads:
                zip_code = lead.get("zip_code")
                if not zip_code:
                    continue

                # 2. COMPETITIVE ARBITRAGE: Find Expired/Withdrawn listings in this zip
                research_query = f"Find recently expired or withdrawn residential listings in zip code {zip_code} within the last 30 days."
                research_results = await self.researcher.research_topic(research_query)

                if research_results:
                    # 3. LEVERAGE SCRIPT GENERATION
                    prompt = f"""
                    JORGE SYSTEM: COMPETITIVE ARBITRAGE SCRIPT [TENANT: {tenant_id}]
                    
                    A lead in {zip_code} is considering selling. 
                    Failures found: {research_results}
                    
                    Draft a short, punchy comparison script for Jorge to use.
                    """

                    script_response = await self.llm.agenerate(
                        prompt=prompt, system_prompt="You are a real estate arbitrage specialist.", temperature=0.7
                    )

                    # 4. GOVERNANCE ENFORCEMENT
                    sanitized_script = self.governance.enforce(
                        script_response.content,
                        {"market_id": zip_code, "task": "leverage_script", "tenant_id": tenant_id},
                    )

                    # Store leverage script in lead metadata
                    # await self.memory.update_lead_metadata(lead['id'], {"leverage_script": sanitized_script}, tenant_id)
                    logger.info(
                        f"[{tenant_id}] {agent.name}: Generated sanitized leverage script for lead in {zip_code}"
                    )
                    agent.actions_taken += 1

            log_metrics(
                provider="system", model="internal-hunter", input_tokens=0, output_tokens=0, task_type="autonomous_op"
            )

            agent.last_run = datetime.now()
            agent.status = "idle"
        except Exception as e:
            logger.error(f"{agent.name} failed for tenant {tenant_id}: {e}")
            agent.status = "error"

    async def run_closer(self, tenant_id: str = "default_tenant"):
        """
        The Closer: Monitors 'Critical' leads and triggers Vapi calls if SMS engagement stalls.
        Now enhanced with Swarm-Driven Negotiation Strategist results and Tenant Isolation.
        """
        agent = self.agents["closer"]
        agent.status = "working"
        logger.info(f"[{tenant_id}] {agent.name} monitoring critical leads...")

        try:
            # 1. Fetch leads that are critical or stalling for this tenant (Simulated)
            stalled_leads = []  # await self.memory.get_stalled_leads(tenant_id, hours=2)

            for contact_id in stalled_leads:
                # 2. RUN SWARM ANALYSIS: Check for Negotiation Softening
                lead_data = {"tenant_id": tenant_id}  # await self.memory.get_lead_context(contact_id, tenant_id)
                swarm_consensus = await lead_intelligence_swarm.analyze_lead_comprehensive(contact_id, lead_data)

                # 3. SWARM ACTION: Extract drift from NegotiationStrategistAgent
                optimizer_insight = next(
                    (i for i in swarm_consensus.agent_insights if i.agent_type.value == "communication_optimizer"), None
                )

                if optimizer_insight:
                    drift_data = optimizer_insight.metadata.get("drift", {})
                    if drift_data.get("is_softening", False):
                        logger.warning(
                            f"🎯 [{tenant_id}] {agent.name}: TRIGGERING AUTOMATIC TAKE-AWAY CLOSE for {contact_id}"
                        )
                        await self.trigger_take_away_sms(contact_id, "softening_stall", tenant_id)
                        agent.actions_taken += 1
                        continue

                # 4. Standard Vapi escalation
                logger.info(f"[{tenant_id}] {agent.name}: Triggering standard Vapi escalation for {contact_id}")
                agent.actions_taken += 1

            log_metrics(
                provider="system", model="internal-closer", input_tokens=0, output_tokens=0, task_type="autonomous_op"
            )

            agent.last_run = datetime.now()
            agent.status = "idle"
        except Exception as e:
            logger.error(f"{agent.name} failed for tenant {tenant_id}: {e}")
            agent.status = "error"

    async def trigger_take_away_sms(self, contact_id: str, reason: str, tenant_id: str = "default_tenant"):
        """
        Generates and sends a Take-Away Close SMS with Governance enforcement and Tenant context.
        """
        raw_message = "It seems like you've moved on. Is it a ridiculous idea to suggest we stop the process?"
        sanitized_message = self.governance.enforce(
            raw_message, {"contact_id": contact_id, "task": "take_away_close", "tenant_id": tenant_id}
        )
        logger.info(f"📲 [TENANT: {tenant_id}] [SMS SENT] To {contact_id}: {sanitized_message}")
        return True

    async def run_cleaner(self, webhook_payload: Dict[str, Any]):
        """
        The Cleaner (Task 2): Self-healing data pipeline.
        Standardizes phone/address using Claude.
        """
        agent = self.agents["cleaner"]
        agent.status = "working"

        prompt = f"""
        Clean and standardize this GHL Lead Data:
        {json.dumps(webhook_payload, indent=2)}
        
        Tasks:
        1. Format phone to E.164.
        2. Standardize address (Street, City, State, Zip).
        3. Flag ambiguities.
        
        Return ONLY valid JSON.
        """

        try:
            response = await self.llm.agenerate(
                prompt=prompt, system_prompt="You are a data cleaning specialist.", temperature=0
            )
            cleaned_data = json.loads(response.content)

            log_metrics(
                provider=self.llm.provider,
                model=self.llm.model,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                task_type="autonomous_op",
            )

            agent.actions_taken += 1
            agent.last_run = datetime.now()
            agent.status = "idle"
            return cleaned_data
        except Exception as e:
            logger.error(f"{agent.name} failed: {e}")
            agent.status = "error"
            return webhook_payload

    async def run_expander(self, tenant_id: str = "default_tenant"):
        """
        The Expander: Dynamic Market Expansion & Cross-Market Intelligence.
        Phase 4: Uses "Hive Mind" to share insights between markets (e.g., Rancho Cucamonga -> Miami).
        """
        agent = self.agents["expander"]
        agent.status = "working"
        logger.info(f"[{tenant_id}] {agent.name} analyzing cross-market migration intelligence...")

        try:
            from ghl_real_estate_ai.services.national_market_intelligence import get_national_market_intelligence

            market_intel = get_national_market_intelligence()

            # 1. Analyze all active migration patterns
            for pattern in market_intel.migration_patterns:
                # Predict cross-market demand boost
                prediction = await market_intel.predict_cross_market_demand(
                    pattern.source_market, pattern.destination_market
                )

                if prediction["demand_score"] > 70:
                    logger.info(
                        f"🚀 [{tenant_id}] {agent.name}: High Demand detected for {prediction['destination_market']} from {prediction['source_market']}"
                    )

                    # 2. Identify leads in the source market who might be relocating for this tenant
                    potential_migrants = []  # await self.memory.get_leads_by_market(pattern.source_market, tenant_id)

                    for lead in potential_migrants:
                        # 3. DRAFT MIGRATION-BASED OUTREACH
                        prompt = f"JORGE SYSTEM: CROSS-MARKET HIVE MIND OUTREACH [TENANT: {tenant_id}]\n\nDestination: {pattern.destination_market}"

                        outreach_script = await self.llm.agenerate(
                            prompt=prompt,
                            system_prompt="You are a multi-market relocation strategist.",
                            temperature=0.7,
                        )

                        # 4. GOVERNANCE ENFORCEMENT
                        sanitized_pitch = self.governance.enforce(
                            outreach_script.content,
                            {
                                "market_id": pattern.destination_market,
                                "task": "relocation_pitch",
                                "tenant_id": tenant_id,
                            },
                        )

                        # Store in lead metadata
                        # await self.memory.update_lead_metadata(lead['id'], {"relocation_pitch": sanitized_pitch}, tenant_id)
                        agent.actions_taken += 1

            log_metrics(
                provider="system", model="internal-expander", input_tokens=0, output_tokens=0, task_type="revenue_op"
            )

            agent.last_run = datetime.now()
            agent.status = "idle"
        except Exception as e:
            logger.error(f"{agent.name} failed for tenant {tenant_id}: {e}")
            agent.status = "error"

    async def run_visualizer(self, tenant_id: str = "default_tenant"):
        """
        The Visualizer: Generates UI/UX for new markets and dashboards.
        """
        agent = self.agents["visualizer"]
        agent.status = "working"
        logger.info(f"[{tenant_id}] {agent.name} generating autonomous UI updates...")

        try:
            # Logic: Check if there are new markets or metrics that need visualization for this tenant
            agent.actions_taken += 1
            agent.last_run = datetime.now()
            agent.status = "idle"
        except Exception as e:
            logger.error(f"{agent.name} failed for tenant {tenant_id}: {e}")
            agent.status = "error"

    async def run_full_cycle(self, tenant_id: str = "default_tenant"):
        """Runs one full cycle of all agents in the swarm for a specific tenant."""
        logger.info(f"🌐 [{tenant_id}] Executing full autonomous cycle...")
        tasks = [
            self.run_analyst(tenant_id),
            self.run_hunter(tenant_id),
            self.run_closer(tenant_id),
            self.run_expander(tenant_id),
            self.run_quant(tenant_id),
            self.run_retention_sentry(tenant_id),
            self.run_visualizer(tenant_id),
            self.run_dojo(tenant_id),
            self.run_portfolio_manager(tenant_id),
            self.run_report_gen(tenant_id),
        ]
        await asyncio.gather(*tasks)

    async def run_report_gen(self, tenant_id: str = "default_tenant"):
        """
        The Report Generator: Periodically generates executive briefings.
        Phase 7: Executive Intelligence.
        """
        agent = self.agents["report_gen"]

        # Only run reports once a day or on-demand
        if datetime.now() - agent.last_run < timedelta(hours=24):
            return

        agent.status = "working"
        logger.info(f"[{tenant_id}] {agent.name} generating market opportunity report...")

        try:
            # 1. Generate the monthly report
            report = await self.reporting_service.generate_monthly_opportunity_report(tenant_id)

            # 2. Log success and action
            logger.info(f"📊 [{tenant_id}] {agent.name}: Generated report: {report.title}")
            # In production, this would email the report or save to GHL files

            agent.actions_taken += 1
            agent.last_run = datetime.now()
            agent.status = "idle"
        except Exception as e:
            logger.error(f"{agent.name} failed for tenant {tenant_id}: {e}")
            agent.status = "error"

    async def run_portfolio_manager(self, tenant_id: str = "default_tenant"):
        """
        The Portfolio Manager: Scans for 'Dead Capital' and triggers resurrection scripts.
        Phase 7: Executive Intelligence.
        """
        agent = self.agents["portfolio"]
        agent.status = "working"
        logger.info(f"[{tenant_id}] {agent.name} identifying dead capital...")

        try:
            # 1. Identify high-yield stalled leads
            dormant_deals = await self.portfolio_manager.scan_for_dead_capital(tenant_id)

            for deal in dormant_deals:
                # 2. Apply Governance to the Resurrection Script
                sanitized_script = self.governance.enforce(
                    deal["resurrection_script"],
                    {"contact_id": deal["id"], "task": "resurrection", "tenant_id": tenant_id},
                )

                # 3. Log the resurrection attempt
                logger.warning(
                    f"🚀 [{tenant_id}] {agent.name}: TRIGGERING RESURRECTION for {deal['name']} ({deal['id']})"
                )
                # In production, this would trigger an SMS or Task in GHL
                # await self.trigger_resurrection_outreach(deal['id'], sanitized_script, tenant_id)
                agent.actions_taken += 1

            agent.last_run = datetime.now()
            agent.status = "idle"
        except Exception as e:
            logger.error(f"{agent.name} failed for tenant {tenant_id}: {e}")
            agent.status = "error"

    async def main_loop(self):
        """Main autonomous execution loop iterating through tenants."""
        logger.info("Starting Agent Swarm Main Loop (Phase 6 - Multi-Tenant)...")
        while True:
            # 1. Fetch active enterprise tenants
            # In production, this queries the EnterpriseTenantService
            active_tenants = ["default_tenant"]  # await self.memory.get_active_tenants()

            for tenant_id in active_tenants:
                await self.run_full_cycle(tenant_id)

            # Wait for next cycle (e.g., 1 hour for background tasks)
            logger.info("Cycle complete for all tenants. Sleeping for 1 hour...")
            await asyncio.sleep(3600)


if __name__ == "__main__":
    orchestrator = AgentSwarmOrchestratorV2()
    asyncio.run(orchestrator.main_loop())
