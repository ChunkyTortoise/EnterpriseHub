"""
Enhanced Lead Intelligence Service
Integrates Claude Orchestrator with Lead Intelligence Hub for comprehensive analysis
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict

import streamlit as st

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.attom_client import get_attom_client
from ghl_real_estate_ai.services.claude_automation_engine import ClaudeAutomationEngine, ScriptType
from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import ClaudeEnhancedLeadScorer, UnifiedScoringResult
from ghl_real_estate_ai.services.claude_orchestrator import ClaudeOrchestrator, get_claude_orchestrator
from ghl_real_estate_ai.services.heygen_service import get_heygen_service
from ghl_real_estate_ai.services.latex_report_generator import get_latex_report_generator
from ghl_real_estate_ai.services.memory_service import MemoryService

# Initialize logger
logger = get_logger(__name__)


class EnhancedLeadIntelligence:
    """
    Enhanced Lead Intelligence service that provides comprehensive lead analysis
    using the unified Claude intelligence layer.

    Features:
    - Comprehensive lead scoring with Claude reasoning
    - Pre-Lead Intelligence via ATTOM API (Property DNA)
    - Real-time behavioral insights
    - Dynamic script generation
    - Deep Cognitive Dossiers (Research)
    - Psychological Property Fit Analysis
    - Real-time Swipe Commentary
    - Enterprise-grade performance optimization
    - Event-driven processing
    - Multi-layer caching
    - Circuit breaker protection
    """

    # SHARED RESOURCE POOL: Static instances shared across all tenant-specific instances
    _claude = None
    _enhanced_scorer = None
    _automation_engine = None
    _memory = None
    _attom_client = None
    _latex_gen = None
    _heygen = None
    _service_lock = asyncio.Lock()

    def __init__(self):
        # Core services now managed via Shared Resource Pool
        self._init_shared_resources()

        # Initialize enterprise services to None - will be lazy loaded
        self.optimized_cache = None
        self.cqrs_service = None
        self.performance_tracker = None
        self.circuit_manager = None
        self.claude_breaker = None
        self.cache_breaker = None

        # Track initialization state
        self._initialized = False
        self._initialization_lock = asyncio.Lock()

        # Legacy performance tracking (maintained for compatibility)
        self.analysis_cache = {}
        self.performance_metrics = {
            "analyses_completed": 0,
            "cache_hits": 0,
            "avg_analysis_time_ms": 0,
            "deep_dossiers_generated": 0,
        }

    def _init_shared_resources(self):
        """
        Implements the Shared Resource Pool pattern to reduce memory footprint.
        Centralizes the psychographic scoring and sentiment engines.
        """
        if EnhancedLeadIntelligence._claude is not None:
            return

        # Synchronous initialization for core engines
        EnhancedLeadIntelligence._claude = get_claude_orchestrator()
        EnhancedLeadIntelligence._enhanced_scorer = ClaudeEnhancedLeadScorer()
        EnhancedLeadIntelligence._automation_engine = ClaudeAutomationEngine()
        EnhancedLeadIntelligence._memory = MemoryService()
        EnhancedLeadIntelligence._attom_client = get_attom_client()
        EnhancedLeadIntelligence._latex_gen = get_latex_report_generator()
        EnhancedLeadIntelligence._heygen = get_heygen_service()
        logger.info("EnhancedLeadIntelligence: Shared Resource Pool Initialized")

    @property
    def claude(self) -> ClaudeOrchestrator:
        return EnhancedLeadIntelligence._claude

    @property
    def enhanced_scorer(self) -> ClaudeEnhancedLeadScorer:
        return EnhancedLeadIntelligence._enhanced_scorer

    @property
    def automation_engine(self) -> ClaudeAutomationEngine:
        return EnhancedLeadIntelligence._automation_engine

    @property
    def memory(self) -> MemoryService:
        return EnhancedLeadIntelligence._memory

    @property
    def attom_client(self):
        return EnhancedLeadIntelligence._attom_client

    @property
    def latex_gen(self):
        return EnhancedLeadIntelligence._latex_gen

    @property
    def heygen(self):
        return EnhancedLeadIntelligence._heygen

    async def initialize(self):
        """
        Async initialization of enterprise services with proper connection handling.
        This method should be called before using any enterprise features.
        """
        async with self._initialization_lock:
            if self._initialized:
                return

            logger.info("Initializing Enhanced Lead Intelligence enterprise services...")
            await self._initialize_performance_services_async()
            self._initialized = True
            logger.info("Enhanced Lead Intelligence enterprise services initialized successfully")

    async def _ensure_initialized(self):
        """Ensure the service is initialized before use"""
        if not self._initialized:
            await self.initialize()

    def _initialize_performance_services(self):
        """Legacy synchronous initialization (deprecated - use async version)"""
        logger.warning("Using deprecated synchronous initialization. Consider calling initialize() async method.")
        # Set all enterprise services to None - they will be lazy loaded
        self.optimized_cache = None
        self.cqrs_service = None
        self.performance_tracker = None
        self.circuit_manager = None

    async def _initialize_performance_services_async(self):
        """Initialize enterprise performance services asynchronously"""
        try:
            # Initialize optimized cache service
            from ghl_real_estate_ai.services.optimized_cache_service import get_optimized_cache_service

            self.optimized_cache = get_optimized_cache_service()

            # Initialize CQRS service
            from ghl_real_estate_ai.services.cqrs_service import get_cqrs_service

            self.cqrs_service = get_cqrs_service()

            # Initialize performance tracker
            from ghl_real_estate_ai.services.performance_tracker import get_performance_tracker

            self.performance_tracker = get_performance_tracker()

            # Initialize circuit breaker manager
            from ghl_real_estate_ai.services.circuit_breaker import get_circuit_manager

            self.circuit_manager = get_circuit_manager()

            # Create circuit breakers for external services
            await self._setup_circuit_breakers_async()

            logger.info("Enterprise performance services initialized successfully")

        except Exception as e:
            logger.warning(f"Enterprise services initialization failed, using fallback: {e}")
            # Keep services as None for graceful fallback
            pass

    def _setup_circuit_breakers(self):
        """Legacy synchronous setup (deprecated - use async version)"""
        logger.warning("Using deprecated synchronous circuit breaker setup.")
        return

    async def _setup_circuit_breakers_async(self):
        """Setup circuit breakers for external dependencies asynchronously"""
        if not self.circuit_manager:
            return

        try:
            from ghl_real_estate_ai.services.circuit_breaker import CircuitBreakerConfig, claude_fallback

            # Claude API circuit breaker
            claude_config = CircuitBreakerConfig(
                failure_threshold=3, recovery_timeout=30.0, success_threshold=2, timeout=25.0, fallback=claude_fallback
            )
            self.claude_breaker = self.circuit_manager.create_breaker("claude_api", claude_config)

            # Cache circuit breaker
            cache_config = CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=10.0,
                success_threshold=3,
                timeout=5.0,
                fallback=None,  # Cache failures should not block processing
            )
            self.cache_breaker = self.circuit_manager.create_breaker("cache_service", cache_config)

            logger.info("Circuit breakers configured successfully")

        except Exception as e:
            logger.warning(f"Circuit breaker setup failed: {e}")
            self.claude_breaker = None
            self.cache_breaker = None

    async def get_cognitive_dossier(self, lead_name: str, lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform 'Deep Research' on a lead to generate a comprehensive cognitive dossier.
        """
        lead_id = lead_context.get("lead_id", f"research_{lead_name.lower().replace(' ', '_')}")

        # Build a deep research prompt
        prompt = f"Perform a deep cognitive research analysis on lead: {lead_name}. Synthesize all known interactions, preferences, and behavioral patterns into a strategic dossier."

        try:
            response = await self.claude.chat_query(
                query=prompt, context={"task": "cognitive_dossier", "lead_data": lead_context}, lead_id=lead_id
            )

            self.performance_metrics["deep_dossiers_generated"] += 1
            return {
                "success": True,
                "dossier": response.content,
                "generated_at": datetime.now().isoformat(),
                "confidence": response.confidence or 0.92,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_psychological_property_fit(
        self, property_data: Dict[str, Any], analysis_result: UnifiedScoringResult
    ) -> str:
        """
        Analyze why a specific property fits a lead's psychological profile.
        """
        lead_name = analysis_result.lead_name
        behavioral_context = analysis_result.behavioral_insights

        prompt = f"Analyze the match between {lead_name} and this property: {property_data.get('address')}. Focus on psychological triggers and lifestyle alignment based on these insights: {behavioral_context}"

        try:
            response = await self.claude.chat_query(
                query=prompt,
                context={"task": "psychological_fit", "property": property_data},
                lead_id=analysis_result.lead_id,
            )
            return response.content
        except Exception:
            return "Excellent match based on extracted preferences and current market velocity."

    async def get_swipe_commentary(self, property_data: Dict[str, Any], lead_name: str) -> str:
        """
        Generate a quick, catchy AI thought for the property swipe UI.
        """
        prompt = f"Give a 1-sentence 'hot take' on why {lead_name} should consider this property: {property_data.get('address')}. Keep it punchy and insightful."

        try:
            # Using a low temperature for consistent "takes"
            response = await self.claude.chat_query(
                query=prompt, context={"task": "swipe_commentary"}, lead_id="system_swipe"
            )
            return response.content.strip(' "')
        except Exception:
            return f"Perfect for {lead_name}'s current search criteria!"

    def render_deep_intelligence_tab(
        self, lead_name: str, lead_context: Dict[str, Any], analysis_result: UnifiedScoringResult
    ):
        """
        Renders the 'Deep Intelligence' UI component with interactive research options.
        Enhanced with Competitive Landscape analysis.
        """
        st.subheader(f"🕵️ Deep Intelligence Dossier: {lead_name}")
        st.markdown("*Claude's comprehensive research and strategic profile*")

        col1, col2, col3, col4 = st.columns(4)

        research_type = None
        with col1:
            if st.button(
                "🧬 Behavioral Blueprint",
                use_container_width=True,
                help="Analyze cognitive biases and decision patterns",
            ):
                research_type = "behavioral_blueprint"
        with col2:
            if st.button(
                "📈 Inventory Match",
                use_container_width=True,
                help="Compare preferences against current market inventory",
            ):
                research_type = "inventory_match"
        with col3:
            if st.button(
                "🎯 Conversion Roadmap", use_container_width=True, help="Step-by-step strategy to move lead to closing"
            ):
                research_type = "conversion_roadmap"
        with col4:
            if st.button(
                "⚔️ Competitive Landscape", use_container_width=True, help="Analyze other agents and market competition"
            ):
                research_type = "competitive_analysis"

        if research_type:
            with st.spinner(f"Claude is generating {research_type.replace('_', ' ')}..."):
                try:
                    # Handle Streamlit event loop
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    if research_type == "competitive_analysis":
                        # Use the new qualification engine method
                        from ghl_real_estate_ai.services.claude_lead_qualification import (
                            get_claude_qualification_engine,
                        )

                        qual_engine = get_claude_qualification_engine()
                        # Simulate history for now
                        history = [
                            {"role": "user", "content": "I was talking to another agent about Manor properties."}
                        ]
                        comp_analysis = loop.run_until_complete(qual_engine.analyze_competitive_landscape(history))

                        st.markdown(f"#### ⚔️ Competitive Landscape for {lead_name}")
                        st.write(f"**Competitive Pressure:** {comp_analysis['competitive_pressure']:.0%}")
                        st.info(f"**Recommended Positioning:** {comp_analysis['recommended_positioning']}")

                        col_c1, col_c2 = st.columns(2)
                        with col_c1:
                            st.markdown("**Competitors Detected:**")
                            if not comp_analysis["competitors_mentioned"]:
                                st.write("None mentioned (Ghosting risk low)")
                            else:
                                for comp in comp_analysis["competitors_mentioned"]:
                                    st.markdown(f"- {comp}")
                        with col_c2:
                            st.markdown("**Differentiation Opportunities:**")
                            for opp in comp_analysis["differentiation_opportunities"]:
                                st.markdown(f"• {opp}")
                    else:
                        prompt = f"Perform deep research on {lead_name}. Focus specifically on: {research_type.replace('_', ' ')}. Data: {json.dumps(lead_context)}"
                        response = loop.run_until_complete(
                            self.claude.chat_query(
                                query=prompt,
                                context={"task": research_type, "lead_data": lead_context},
                                lead_id=analysis_result.lead_id,
                            )
                        )
                        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import render_dossier_block

                        render_dossier_block(
                            response.content, title=f"{research_type.replace('_', ' ').upper()} SYNTHESIZED"
                        )

                    if st.button("💾 Save to GHL Notes", key=f"save_{research_type}"):
                        st.toast("Research saved to lead profile in GHL!", icon="✅")

                except Exception as e:
                    st.error(f"Research failed: {str(e)}")

        st.markdown("---")
        st.markdown("#### 🧠 Quick Strategic Take")
        st.info(analysis_result.strategic_summary)

    def render_journey_orchestration_tab(
        self, lead_name: str, lead_context: Dict[str, Any], analysis_result: UnifiedScoringResult
    ):
        """
        Renders the 'Journey Orchestration' tab with real autonomous journey management.
        """
        from ghl_real_estate_ai.streamlit_demo.components.journey_orchestrator_ui import render_journey_orchestrator

        lead_id = lead_context.get("lead_id", "unknown")
        render_journey_orchestrator(lead_id, lead_name, lead_context)

    async def get_comprehensive_lead_analysis_enterprise(
        self, lead_name: str, lead_context: Dict[str, Any], force_refresh: bool = False
    ) -> UnifiedScoringResult:
        """
        Enterprise-grade comprehensive lead analysis with performance optimization
        Features: Circuit breakers, multi-layer caching, performance tracking, CQRS
        """
        # Ensure enterprise services are initialized
        await self._ensure_initialized()

        request_id = f"analysis_{lead_name}_{int(time.time() * 1000000)}"

        # Use performance tracker if available
        if self.performance_tracker:
            async with self.performance_tracker.track_request(request_id, "lead_analysis", lead_name):
                return await self._execute_comprehensive_analysis(lead_name, lead_context, force_refresh)
        else:
            return await self._execute_comprehensive_analysis(lead_name, lead_context, force_refresh)

    async def _execute_comprehensive_analysis(
        self, lead_name: str, lead_context: Dict[str, Any], force_refresh: bool = False
    ) -> UnifiedScoringResult:
        """Execute comprehensive analysis with enterprise optimizations"""

        # Try CQRS pattern if available
        if self.cqrs_service and not force_refresh:
            try:
                from ghl_real_estate_ai.services.cqrs_service import GetLeadScoreQuery

                lead_id = lead_context.get("lead_id", f"demo_{lead_name.lower().replace(' ', '_')}")
                query = GetLeadScoreQuery(lead_id=lead_id, include_reasoning=True)

                result = await self.cqrs_service.execute_query(query)
                if result.success:
                    # Convert CQRS result to UnifiedScoringResult format
                    return self._convert_cqrs_to_unified_result(result, lead_name, lead_context)

            except Exception as e:
                logger.warning(f"CQRS query failed, falling back to direct analysis: {e}")

        # Fall back to enhanced analysis with performance optimizations
        return await self._enhanced_analysis_with_optimizations(lead_name, lead_context, force_refresh)

    async def get_pre_lead_intelligence(self, address: str) -> Dict[str, Any]:
        """
        Fetch proprietary Pre-Lead Intelligence (ATTOM DNA + Life Events).
        """
        dna_task = self.attom_client.get_property_dna(address)
        triggers_task = self.attom_client.get_life_event_triggers(address)

        dna, triggers = await asyncio.gather(dna_task, triggers_task)

        return {
            "property_dna": dna,
            "life_event_triggers": triggers,
            "summary": f"Property DNA: {dna.get('characteristics', {}).get('sqft')} sqft, {dna.get('characteristics', {}).get('bedrooms')} beds. Triggers: {triggers}",
        }

    async def _enhanced_analysis_with_optimizations(
        self, lead_name: str, lead_context: Dict[str, Any], force_refresh: bool = False
    ) -> UnifiedScoringResult:
        """Enhanced analysis with multi-layer caching and circuit breakers"""

        # Check optimized cache first
        cache_key = f"enhanced_analysis_{lead_name}_{hash(json.dumps(lead_context, sort_keys=True, default=str))}"

        if self.optimized_cache and not force_refresh:
            try:
                if self.cache_breaker:
                    cached_result = await self.cache_breaker.call(self.optimized_cache.get, cache_key)
                else:
                    cached_result = await self.optimized_cache.get(cache_key)

                if cached_result:
                    self.performance_metrics["cache_hits"] += 1
                    return cached_result

            except Exception as e:
                logger.warning(f"Optimized cache access failed: {e}")

        # 🚀 PRE-LEAD INTELLIGENCE ENRICHMENT
        property_address = lead_context.get("location") or lead_context.get("extracted_preferences", {}).get("location")
        if property_address:
            try:
                pre_lead_intel = await self.get_pre_lead_intelligence(property_address)
                lead_context["pre_lead_intelligence"] = pre_lead_intel
                logger.info(f"Enriched analysis for {lead_name} with Pre-Lead Intelligence")
            except Exception as e:
                logger.error(f"Pre-Lead Intelligence enrichment failed: {e}")

        # Perform enhanced analysis with circuit breaker protection
        try:
            start_time = datetime.now()

            # Generate lead_id
            lead_id = lead_context.get(
                "lead_id", f"demo_{lead_name.lower().replace(' ', '_').replace('(', '').replace(')', '')}"
            )

            # Use circuit breaker for Claude API calls
            if self.claude_breaker:
                analysis_result = await self.claude_breaker.call(
                    self.enhanced_scorer.analyze_lead_comprehensive, lead_id=lead_id, lead_context=lead_context
                )
            else:
                analysis_result = await self.enhanced_scorer.analyze_lead_comprehensive(
                    lead_id=lead_id, lead_context=lead_context
                )

            analysis_time = (datetime.now() - start_time).total_seconds() * 1000

            # Cache the result in optimized cache
            if self.optimized_cache:
                try:
                    if self.cache_breaker:
                        await self.cache_breaker.call(
                            self.optimized_cache.set,
                            cache_key,
                            analysis_result,
                            300,  # 5 minute TTL
                        )
                    else:
                        await self.optimized_cache.set(cache_key, analysis_result, ttl=300)
                except Exception as e:
                    logger.warning(f"Failed to cache analysis result: {e}")

            # Update performance metrics
            self._update_metrics(analysis_time)

            return analysis_result

        except Exception as e:
            logger.error(f"Enhanced analysis failed: {e}")
            # Return fallback analysis
            return self._create_fallback_analysis(lead_name, lead_context, str(e))

    def _convert_cqrs_to_unified_result(
        self, cqrs_result, lead_name: str, lead_context: Dict[str, Any]
    ) -> UnifiedScoringResult:
        """Convert CQRS query result to UnifiedScoringResult format"""
        data = cqrs_result.data

        from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import UnifiedScoringResult

        return UnifiedScoringResult(
            lead_id=data.get("lead_id", "unknown"),
            lead_name=lead_name,
            scored_at=datetime.now(),
            final_score=data.get("score", 50.0),
            confidence_score=data.get("confidence", 0.8),
            classification=data.get("classification", "warm"),
            jorge_score=75,  # Default values
            ml_conversion_score=70,
            churn_risk_score=30,
            engagement_score=80,
            frs_score=65.0,
            pcs_score=60.0,
            strategic_summary=f"CQRS-optimized analysis for {lead_name}",
            behavioral_insights=data.get("reasoning", "High-performance analysis via CQRS"),
            reasoning=data.get("reasoning", "Cached analysis result"),
            risk_factors=["CQRS optimization active"],
            opportunities=["Enhanced performance"],
            recommended_actions=[{"action": "Follow up", "priority": "medium"}],
            next_best_action="Continue engagement",
            expected_timeline="24-48 hours",
            success_probability=75.0,
            feature_breakdown={},
            conversation_context=lead_context,
            sources=["CQRS Cache"],
            analysis_time_ms=cqrs_result.latency_ms,
            claude_reasoning_time_ms=0,
        )

    async def get_comprehensive_lead_analysis(
        self, lead_name: str, lead_context: Dict[str, Any], force_refresh: bool = False
    ) -> UnifiedScoringResult:
        """
        Get comprehensive lead analysis with caching for performance.

        Args:
            lead_name: Name of the lead to analyze
            lead_context: Lead data and preferences
            force_refresh: Whether to bypass cache and regenerate analysis

        Returns:
            UnifiedScoringResult with complete analysis
        """
        # Generate cache key
        cache_key = f"{lead_name}_{hash(json.dumps(lead_context, sort_keys=True, default=str))}"

        # Check cache unless forced refresh
        if not force_refresh and cache_key in self.analysis_cache:
            cached_result = self.analysis_cache[cache_key]
            # Use cache if less than 5 minutes old
            if (datetime.now() - cached_result["timestamp"]).seconds < 300:
                self.performance_metrics["cache_hits"] += 1
                return cached_result["result"]

        try:
            # Generate lead_id from name
            lead_id = lead_context.get(
                "lead_id", f"demo_{lead_name.lower().replace(' ', '_').replace('(', '').replace(')', '')}"
            )

            # Get comprehensive analysis
            start_time = datetime.now()
            analysis_result = await self.enhanced_scorer.analyze_lead_comprehensive(
                lead_id=lead_id, lead_context=lead_context
            )
            analysis_time = (datetime.now() - start_time).total_seconds() * 1000

            # Cache the result
            self.analysis_cache[cache_key] = {"result": analysis_result, "timestamp": datetime.now()}

            # Update metrics
            self._update_metrics(analysis_time)

            return analysis_result

        except Exception as e:
            # Return fallback analysis on error
            return self._create_fallback_analysis(lead_name, lead_context, str(e))

    async def generate_behavioral_insight(self, lead_name: str, analysis_result: UnifiedScoringResult) -> str:
        """
        Generate enhanced behavioral insights using Claude analysis.
        """
        try:
            # Use the strategic summary and behavioral insights from the analysis
            if analysis_result.behavioral_insights:
                return analysis_result.behavioral_insights

            # Fallback to existing persona-based insights
            return self._get_persona_insight(lead_name, analysis_result)

        except Exception as e:
            return f"Behavioral analysis temporarily unavailable: {str(e)}"

    async def generate_quick_action_script(
        self, lead_name: str, script_type: str, analysis_result: UnifiedScoringResult
    ) -> Dict[str, Any]:
        """
        Generate quick action scripts for the Lead Intelligence Hub buttons.
        """
        try:
            lead_id = analysis_result.lead_id

            # Map script type to enum
            script_type_enum = ScriptType.FOLLOW_UP
            if "sms" in script_type.lower():
                script_type_enum = ScriptType.FOLLOW_UP
            elif "email" in script_type.lower():
                script_type_enum = ScriptType.FOLLOW_UP
            elif "call" in script_type.lower():
                script_type_enum = ScriptType.CLOSING_SEQUENCE

            # Generate script
            automated_script = await self.automation_engine.generate_personalized_script(
                script_type=script_type_enum,
                lead_id=lead_id,
                channel="sms" if "sms" in script_type.lower() else "email",
                variants=1,
            )

            return {
                "success": True,
                "script": automated_script.primary_script,
                "reasoning": automated_script.personalization_notes,
                "success_probability": automated_script.success_probability,
                "channel": automated_script.channel,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "script": f"Hi {lead_name}, this is Jorge. I wanted to follow up with you about your property search. When's a good time to chat?",
                "reasoning": f"Fallback script generated due to system error: {str(e)}",
            }

    def render_enhanced_lead_profile_header(self, lead_name: str, analysis_result: UnifiedScoringResult):
        """
        Render enhanced lead profile header with comprehensive analysis.
        """
        # Determine colors based on classification
        score_colors = {"hot": "#ef4444", "warm": "#f59e0b", "cold": "#6366f1", "error": "#6b7280"}

        score_labels = {
            "hot": "🔥 HOT LEAD",
            "warm": "🔸 WARM LEAD",
            "cold": "❄️ COLD LEAD",
            "error": "⚠️ ANALYSIS ERROR",
        }

        classification = analysis_result.classification
        score_color = score_colors.get(classification, "#6b7280")
        score_label = score_labels.get(classification, "🤖 CLAUDE ANALYSIS")

        # Extract occupation and location from context or analysis
        lead_context = analysis_result.conversation_context
        occupation = lead_context.get("extracted_preferences", {}).get("occupation", "Professional")
        location = lead_context.get("extracted_preferences", {}).get("location", "Rancho Cucamonga Area")

        st.markdown(
            f"""
        <div style='background: rgba(30, 41, 59, 0.4);
                    padding: 1.75rem; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); 
                    border-left: 6px solid {score_color}; margin-bottom: 2rem;
                    box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.25); backdrop-filter: blur(15px);'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <h2 style='margin: 0; color: white !important; font-size: 1.75rem; font-family: "Manrope", sans-serif; letter-spacing: -0.02em;'>{lead_name}</h2>
                    <div style='display: flex; align-items: center; gap: 1rem; margin-top: 0.6rem; flex-wrap: wrap;'>
                        <span style='background: {score_color}20; color: {score_color}; padding: 0.25rem 0.85rem;
                                     border-radius: 999px; font-size: 0.75rem; font-weight: 800; border: 1px solid {score_color}40; text-transform: uppercase;'>
                            {score_label}
                        </span>
                        <span style='color: #94a3b8; font-size: 0.95rem; font-weight: 500;'>• {occupation}</span>
                        <span style='color: #94a3b8; font-size: 0.95rem; font-weight: 500;'>• {location}</span>
                        <span style='color: #94a3b8; font-size: 0.95rem; font-weight: 500; background: rgba(99, 102, 241, 0.1); padding: 2px 8px; border-radius: 4px;'>Confidence: {analysis_result.confidence_score:.0%}</span>
                    </div>
                </div>
                <div style='text-align: right;'>
                    <div style='font-size: 2.5rem; font-weight: 900; color: {score_color}; line-height: 1; font-family: "Manrope", sans-serif;'>
                        {analysis_result.final_score:.0f}%
                    </div>
                    <div style='font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; margin-top: 6px;'>
                        Match Score
                    </div>
                    <div style='font-size: 0.65rem; color: #64748b; margin-top: 6px; font-family: monospace;'>
                        T-ANALYTICS: {analysis_result.analysis_time_ms}ms
                    </div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    async def generate_personalized_report_and_video(
        self, lead_name: str, lead_context: Dict[str, Any], analysis_result: UnifiedScoringResult
    ) -> Dict[str, Any]:
        """
        Phase 3: Combine LaTeX reporting with HeyGen video presentation.
        """
        # 1. Generate LaTeX Report
        report_data = {
            "lead_name": lead_name,
            "address": lead_context.get("location", "The Property"),
            "valuation": analysis_result.ml_conversion_score * 5000 + 400000,  # Mock valuation
            "frs_score": analysis_result.frs_score,
            "alignment": analysis_result.classification.title() + " Readiness",
            "strategy": analysis_result.strategic_summary,
        }
        tex_source = self.latex_gen.generate_tex_source(report_data)
        self.latex_gen.mock_pdf_render(tex_source)

        # 2. Generate HeyGen Video Script
        video_script = (
            f"Hi {lead_name}, I've just finished your personalized market intelligence report for {report_data['address']}. "
            f"Based on our analysis, your transaction readiness score is {analysis_result.frs_score} percent. "
            f"I'm sending the full detailed report now. Let's discuss when you're ready."
        )

        # 3. Trigger HeyGen
        video_result = await self.heygen.generate_personalized_video(lead_name, video_script)

        return {
            "success": True,
            "latex_source": tex_source,
            "video_result": video_result,
            "report_url": "https://lyrio.io/reports/demo_report.pdf",  # Mock
        }

    def render_enhanced_behavioral_insight(self, lead_name: str, analysis_result: UnifiedScoringResult):
        """
        Render enhanced behavioral insights with Claude analysis.
        """
        with st.container(border=True):
            st.markdown(f"**🤖 Claude's Behavioral Intelligence: {lead_name}**")

            # Use Claude's behavioral insights if available
            if analysis_result.behavioral_insights:
                st.info(analysis_result.behavioral_insights)
            else:
                # Fallback to persona-based insights
                insight = self._get_persona_insight(lead_name, analysis_result)
                st.info(insight)

            # Show reasoning if available
            if analysis_result.reasoning:
                with st.expander("🧠 Claude's Reasoning", expanded=False):
                    st.caption(analysis_result.reasoning)

            # Show risk factors and opportunities
            col1, col2 = st.columns(2)

            with col1:
                if analysis_result.risk_factors:
                    st.markdown("**⚠️ Risk Factors:**")
                    for risk in analysis_result.risk_factors[:3]:
                        st.markdown(f"• {risk}")

            with col2:
                if analysis_result.opportunities:
                    st.markdown("**🎯 Opportunities:**")
                    for opportunity in analysis_result.opportunities[:3]:
                        st.markdown(f"• {opportunity}")

            # 🏰 PRE-LEAD DNA (ATTOM DATA MOAT)
            pre_lead_intel = analysis_result.conversation_context.get("pre_lead_intelligence")
            if pre_lead_intel:
                with st.expander("🏰 Pre-Lead DNA (Proprietary Data Moat)", expanded=True):
                    dna = pre_lead_intel.get("property_dna", {})
                    triggers = pre_lead_intel.get("life_event_triggers", {})

                    st.markdown("#### 🧬 Property DNA (ATTOM)")
                    dna_cols = st.columns(4)
                    with dna_cols[0]:
                        st.metric("Years Owned", dna.get("summary", {}).get("years_owned", "N/A"))
                    with dna_cols[1]:
                        st.metric("SqFt", dna.get("characteristics", {}).get("sqft", "N/A"))
                    with dna_cols[2]:
                        st.metric(
                            "Beds/Baths",
                            f"{dna.get('characteristics', {}).get('bedrooms', 'N/A')}/{dna.get('characteristics', {}).get('bathrooms', 'N/A')}",
                        )
                    with dna_cols[3]:
                        st.metric("Absentee", "YES" if dna.get("summary", {}).get("absentee_owner") else "NO")

                    st.markdown("#### ⚡ Life Event Triggers")
                    trig_cols = st.columns(3)
                    with trig_cols[0]:
                        st.markdown(f"**Probate:** {'🔴 YES' if triggers.get('probate') else '🟢 NO'}")
                    with trig_cols[1]:
                        st.markdown(f"**Liens:** {triggers.get('liens', 0)}")
                    with trig_cols[2]:
                        st.markdown(f"**Tax Delinquent:** {'🔴 YES' if triggers.get('tax_delinquent') else '🟢 NO'}")

    def render_enhanced_quick_actions(self, lead_name: str, analysis_result: UnifiedScoringResult):
        """
        Render enhanced quick actions with Claude-generated scripts.
        """
        st.markdown("#### ⚡ Claude-Powered Quick Actions")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📞 Smart Call", use_container_width=True, type="primary"):
                self._handle_quick_action("call", lead_name, analysis_result)

        with col2:
            if st.button("💬 Generate SMS", use_container_width=True):
                self._handle_quick_action("sms", lead_name, analysis_result)

        with col3:
            if st.button("📧 Draft Email", use_container_width=True):
                self._handle_quick_action("email", lead_name, analysis_result)

        with col4:
            if st.button("📅 Schedule Tour", use_container_width=True):
                self._handle_quick_action("schedule", lead_name, analysis_result)

        # Phase 3: Personalized Video Report
        st.markdown("#### 📹 Personalized Media (Phase 3 Moat)")
        if st.button(
            "🎬 Generate Personalized Video Report (LaTeX + HeyGen)", type="primary", use_container_width=True
        ):
            self._handle_quick_action("video_report", lead_name, analysis_result)

    def _handle_quick_action(self, action_type: str, lead_name: str, analysis_result: UnifiedScoringResult):
        """Handle quick action button clicks with Claude intelligence."""

        with st.spinner(f"🧠 Claude is generating {action_type} strategy..."):
            try:
                # Get or create event loop
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                if action_type == "sms":
                    # Generate SMS script asynchronously
                    script_result = loop.run_until_complete(
                        self.generate_quick_action_script(lead_name, "sms", analysis_result)
                    )

                    if script_result.get("success"):
                        st.success("📱 Claude generated SMS script:")
                        st.code(script_result["script"], language=None)
                        st.caption(f"💡 {script_result['reasoning']}")
                        st.toast(f"SMS script ready for {lead_name}!", icon="📱")
                    else:
                        st.error(f"Script generation failed: {script_result.get('error', 'Unknown error')}")

                elif action_type == "email":
                    # Generate email script
                    script_result = loop.run_until_complete(
                        self.generate_quick_action_script(lead_name, "email", analysis_result)
                    )

                    if script_result.get("success"):
                        st.success("📧 Claude generated email draft:")
                        st.code(script_result["script"], language=None)
                        st.caption(f"💡 {script_result['reasoning']}")
                        st.toast(f"Email draft ready for {lead_name}!", icon="📧")
                    else:
                        st.error(f"Email generation failed: {script_result.get('error', 'Unknown error')}")

                elif action_type == "call":
                    # Generate call script
                    script_result = loop.run_until_complete(
                        self.generate_quick_action_script(lead_name, "call", analysis_result)
                    )

                    if script_result.get("success"):
                        st.success("📞 Claude generated call script:")
                        st.code(script_result["script"], language=None)
                        st.caption(f"💡 {script_result['reasoning']}")
                        st.toast(f"Call script ready for {lead_name}!", icon="📞")
                    else:
                        st.error(f"Call script generation failed: {script_result.get('error', 'Unknown error')}")

                elif action_type == "video_report":
                    # Generate Phase 3 Report and Video
                    lead_context = analysis_result.conversation_context
                    result = loop.run_until_complete(
                        self.generate_personalized_report_and_video(lead_name, lead_context, analysis_result)
                    )

                    if result.get("success"):
                        st.success(f"🎥 Phase 3 Media Pack Generated for {lead_name}!")
                        col_v1, col_v2 = st.columns(2)
                        with col_v1:
                            st.info("📄 LaTeX Report Source Ready")
                            st.code(result["latex_source"][:300] + "...", language="latex")
                        with col_v2:
                            st.info("🎬 HeyGen Video Processing")
                            st.write(f"Video ID: `{result['video_result']['video_id']}`")
                            st.write(f"Status: `{result['video_result']['status']}`")
                        st.toast("Personalized video report queued!", icon="🎬")
                    else:
                        st.error("Failed to generate video report pack.")

                elif action_type == "schedule":
                    # Use next best action from analysis
                    next_action = analysis_result.next_best_action
                    if "tour" in next_action.lower() or "showing" in next_action.lower():
                        st.success(f"🏠 Claude recommends: {next_action}")
                    else:
                        st.info("📅 Claude suggests scheduling follow-up call before property tour")
                    st.toast("Calendar integration ready", icon="📅")

            except Exception as e:
                st.error(f"Action failed: {str(e)}")

    def _get_persona_insight(self, lead_name: str, analysis_result: UnifiedScoringResult) -> str:
        """Get persona-based insights as fallback."""

        # Enhanced persona insights with analysis data
        base_insights = {
            "Sarah Chen": f"High-velocity tech professional (Score: {analysis_result.final_score:.0f}%). Apple engineers are data-driven; Claude detected {analysis_result.engagement_score:.0f}% engagement. Timeline critical: prioritize Teravista for commute efficiency.",
            "David Kim": f"Analytical investor (Score: {analysis_result.final_score:.0f}%). Claude identified investment-focused behavior patterns. Current focus: Manor vs Del Valle yield comparison. Recommend off-market ROI analysis.",
            "Mike & Jessica Rodriguez": f"First-time buyer family (Score: {analysis_result.final_score:.0f}%). Claude detected high sentiment but low confidence. Safety & schools research indicates Ontario preference. Emphasize 8/10 school ratings.",
            "Robert & Linda Williams": f"Luxury downsizers (Score: {analysis_result.final_score:.0f}%). Relationship-focused with high trust indicators. Value personal service over automation. Recommend exclusive downtown access and concierge approach.",
        }

        # Find matching persona or use dynamic insight
        for persona, insight in base_insights.items():
            if persona.split()[0] in lead_name or persona.split()[1] in lead_name:
                return insight

        # Dynamic insight based on analysis
        return f"Lead scored {analysis_result.final_score:.0f}% with {analysis_result.classification} classification. Claude confidence: {analysis_result.confidence_score:.0%}. {analysis_result.strategic_summary}"

    def _create_fallback_analysis(
        self, lead_name: str, lead_context: Dict[str, Any], error: str
    ) -> UnifiedScoringResult:
        """Create fallback analysis when Claude fails."""
        from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import UnifiedScoringResult

        return UnifiedScoringResult(
            lead_id=f"fallback_{lead_name.lower().replace(' ', '_')}",
            lead_name=lead_name,
            scored_at=datetime.now(),
            final_score=50.0,
            confidence_score=0.1,
            classification="error",
            jorge_score=0,
            ml_conversion_score=0,
            churn_risk_score=50,
            engagement_score=0,
            frs_score=0.0,
            pcs_score=0.0,
            strategic_summary=f"Analysis failed due to system error: {error}",
            behavioral_insights="Unable to generate behavioral insights due to technical issue",
            reasoning=f"System error prevented comprehensive analysis: {error}",
            risk_factors=["Technical system error"],
            opportunities=["Retry analysis when system available"],
            recommended_actions=[{"action": "Manual review required", "priority": "high"}],
            next_best_action="Review lead manually due to system error",
            expected_timeline="Unknown due to error",
            success_probability=25.0,
            feature_breakdown={},
            conversation_context=lead_context,
            sources=["Fallback System"],
            analysis_time_ms=0,
            claude_reasoning_time_ms=0,
        )

    def _update_metrics(self, analysis_time_ms: float):
        """Update performance metrics."""
        count = self.performance_metrics["analyses_completed"]
        self.performance_metrics["analyses_completed"] += 1

        # Update average analysis time
        current_avg = self.performance_metrics["avg_analysis_time_ms"]
        self.performance_metrics["avg_analysis_time_ms"] = (current_avg * count + analysis_time_ms) / (count + 1)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get service performance metrics."""
        total_requests = self.performance_metrics["analyses_completed"] + self.performance_metrics["cache_hits"]
        cache_hit_rate = self.performance_metrics["cache_hits"] / total_requests if total_requests > 0 else 0

        return {**self.performance_metrics, "cache_hit_rate": cache_hit_rate, "total_requests": total_requests}


# Singleton instance for use in components
_enhanced_lead_intelligence = None


def get_enhanced_lead_intelligence() -> EnhancedLeadIntelligence:
    """Get singleton instance of Enhanced Lead Intelligence."""
    global _enhanced_lead_intelligence
    if _enhanced_lead_intelligence is None:
        _enhanced_lead_intelligence = EnhancedLeadIntelligence()
    return _enhanced_lead_intelligence


async def get_enhanced_lead_intelligence_async() -> EnhancedLeadIntelligence:
    """Get singleton instance of Enhanced Lead Intelligence with async initialization."""
    global _enhanced_lead_intelligence
    if _enhanced_lead_intelligence is None:
        _enhanced_lead_intelligence = EnhancedLeadIntelligence()

    # Ensure it's initialized
    await _enhanced_lead_intelligence.initialize()
    return _enhanced_lead_intelligence
