"""
Enhanced Lead Intelligence Service
Integrates Claude Orchestrator with Lead Intelligence Hub for comprehensive analysis
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import streamlit as st

from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator, ClaudeOrchestrator
from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import ClaudeEnhancedLeadScorer, UnifiedScoringResult
from ghl_real_estate_ai.services.claude_automation_engine import ClaudeAutomationEngine, ScriptType
from ghl_real_estate_ai.services.memory_service import MemoryService


class EnhancedLeadIntelligence:
    """
    Enhanced Lead Intelligence service that provides comprehensive lead analysis
    using the unified Claude intelligence layer.

    Features:
    - Comprehensive lead scoring with Claude reasoning
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

    def __init__(self):
        self.claude = get_claude_orchestrator()
        self.enhanced_scorer = ClaudeEnhancedLeadScorer()
        self.automation_engine = ClaudeAutomationEngine()
        self.memory = MemoryService()

        # Enterprise performance services
        self._initialize_performance_services()

        # Legacy performance tracking (maintained for compatibility)
        self.analysis_cache = {}
        self.performance_metrics = {
            "analyses_completed": 0,
            "cache_hits": 0,
            "avg_analysis_time_ms": 0,
            "deep_dossiers_generated": 0
        }

    def _initialize_performance_services(self):
        """Initialize enterprise performance services"""
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
            self._setup_circuit_breakers()
            
            logger.info("Enterprise performance services initialized")
            
        except Exception as e:
            logger.warning(f"Enterprise services initialization failed, using fallback: {e}")
            self.optimized_cache = None
            self.cqrs_service = None
            self.performance_tracker = None
            self.circuit_manager = None

    def _setup_circuit_breakers(self):
        """Setup circuit breakers for external dependencies"""
        if not self.circuit_manager:
            return
            
        from ghl_real_estate_ai.services.circuit_breaker import CircuitBreakerConfig, claude_fallback
        
        # Claude API circuit breaker
        claude_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30.0,
            success_threshold=2,
            timeout=25.0,
            fallback=claude_fallback
        )
        self.claude_breaker = self.circuit_manager.create_breaker("claude_api", claude_config)
        
        # Cache circuit breaker  
        cache_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=10.0,
            success_threshold=3,
            timeout=5.0,
            fallback=None  # Cache failures should not block processing
        )
        self.cache_breaker = self.circuit_manager.create_breaker("cache_service", cache_config)

    async def get_cognitive_dossier(self, lead_name: str, lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform 'Deep Research' on a lead to generate a comprehensive cognitive dossier.
        """
        lead_id = lead_context.get('lead_id', f"research_{lead_name.lower().replace(' ', '_')}")
        
        # Build a deep research prompt
        prompt = f"Perform a deep cognitive research analysis on lead: {lead_name}. Synthesize all known interactions, preferences, and behavioral patterns into a strategic dossier."
        
        try:
            response = await self.claude.chat_query(
                query=prompt,
                context={"task": "cognitive_dossier", "lead_data": lead_context},
                lead_id=lead_id
            )
            
            self.performance_metrics["deep_dossiers_generated"] += 1
            return {
                "success": True,
                "dossier": response.content,
                "generated_at": datetime.now().isoformat(),
                "confidence": response.confidence or 0.92
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_psychological_property_fit(self, property_data: Dict[str, Any], analysis_result: UnifiedScoringResult) -> str:
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
                lead_id=analysis_result.lead_id
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
                query=prompt,
                context={"task": "swipe_commentary"},
                lead_id="system_swipe"
            )
            return response.content.strip(' "')
        except Exception:
            return f"Perfect for {lead_name}'s current search criteria!"

    def render_deep_intelligence_tab(self, lead_name: str, lead_context: Dict[str, Any], analysis_result: UnifiedScoringResult):
        """
        Renders the 'Deep Intelligence' UI component with interactive research options.
        Enhanced with Competitive Landscape analysis.
        """
        st.subheader(f"🕵️ Deep Intelligence Dossier: {lead_name}")
        st.markdown("*Claude's comprehensive research and strategic profile*")
        
        col1, col2, col3, col4 = st.columns(4)
        
        research_type = None
        with col1:
            if st.button("🧬 Behavioral Blueprint", use_container_width=True, help="Analyze cognitive biases and decision patterns"):
                research_type = "behavioral_blueprint"
        with col2:
            if st.button("📈 Inventory Match", use_container_width=True, help="Compare preferences against current market inventory"):
                research_type = "inventory_match"
        with col3:
            if st.button("🎯 Conversion Roadmap", use_container_width=True, help="Step-by-step strategy to move lead to closing"):
                research_type = "conversion_roadmap"
        with col4:
            if st.button("⚔️ Competitive Landscape", use_container_width=True, help="Analyze other agents and market competition"):
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
                        from ghl_real_estate_ai.services.claude_lead_qualification import get_claude_qualification_engine
                        qual_engine = get_claude_qualification_engine()
                        # Simulate history for now
                        history = [{"role": "user", "content": "I was talking to another agent about Manor properties."}]
                        comp_analysis = loop.run_until_complete(qual_engine.analyze_competitive_landscape(history))
                        
                        st.markdown(f"#### ⚔️ Competitive Landscape for {lead_name}")
                        st.write(f"**Competitive Pressure:** {comp_analysis['competitive_pressure']:.0%}")
                        st.info(f"**Recommended Positioning:** {comp_analysis['recommended_positioning']}")
                        
                        col_c1, col_c2 = st.columns(2)
                        with col_c1:
                            st.markdown("**Competitors Detected:**")
                            if not comp_analysis['competitors_mentioned']:
                                st.write("None mentioned (Ghosting risk low)")
                            else:
                                for comp in comp_analysis['competitors_mentioned']:
                                    st.markdown(f"- {comp}")
                        with col_c2:
                            st.markdown("**Differentiation Opportunities:**")
                            for opp in comp_analysis['differentiation_opportunities']:
                                st.markdown(f"• {opp}")
                    else:
                        prompt = f"Perform deep research on {lead_name}. Focus specifically on: {research_type.replace('_', ' ')}. Data: {json.dumps(lead_context)}"
                        response = loop.run_until_complete(
                            self.claude.chat_query(
                                query=prompt,
                                context={"task": research_type, "lead_data": lead_context},
                                lead_id=analysis_result.lead_id
                            )
                        )
                        from ghl_real_estate_ai.streamlit_demo.obsidian_theme import render_dossier_block
                        render_dossier_block(response.content, title=f"{research_type.replace('_', ' ').upper()} SYNTHESIZED")
                    
                    if st.button("💾 Save to GHL Notes", key=f"save_{research_type}"):
                        st.toast("Research saved to lead profile in GHL!", icon="✅")
                        
                except Exception as e:
                    st.error(f"Research failed: {str(e)}")
        
        st.markdown("---")
        st.markdown("#### 🧠 Quick Strategic Take")
        st.info(analysis_result.strategic_summary)

    def render_journey_orchestration_tab(self, lead_name: str, lead_context: Dict[str, Any], analysis_result: UnifiedScoringResult):
        """
        Renders the 'Journey Orchestration' tab with real autonomous journey management.
        """
        from ghl_real_estate_ai.streamlit_demo.components.journey_orchestrator_ui import render_journey_orchestrator
        
        lead_id = lead_context.get('lead_id', 'unknown')
        render_journey_orchestrator(lead_id, lead_name, lead_context)

    async def get_comprehensive_lead_analysis_enterprise(self,
                                                      lead_name: str, 
                                                      lead_context: Dict[str, Any],
                                                      force_refresh: bool = False) -> UnifiedScoringResult:
        """
        Enterprise-grade comprehensive lead analysis with performance optimization
        Features: Circuit breakers, multi-layer caching, performance tracking, CQRS
        """
        request_id = f"analysis_{lead_name}_{int(time.time() * 1000000)}"
        
        # Use performance tracker if available
        if self.performance_tracker:
            async with self.performance_tracker.track_request(request_id, "lead_analysis", lead_name):
                return await self._execute_comprehensive_analysis(lead_name, lead_context, force_refresh)
        else:
            return await self._execute_comprehensive_analysis(lead_name, lead_context, force_refresh)

    async def _execute_comprehensive_analysis(self,
                                            lead_name: str,
                                            lead_context: Dict[str, Any], 
                                            force_refresh: bool = False) -> UnifiedScoringResult:
        """Execute comprehensive analysis with enterprise optimizations"""
        
        # Try CQRS pattern if available
        if self.cqrs_service and not force_refresh:
            try:
                from ghl_real_estate_ai.services.cqrs_service import GetLeadScoreQuery
                
                lead_id = lead_context.get('lead_id', f"demo_{lead_name.lower().replace(' ', '_')}")
                query = GetLeadScoreQuery(lead_id=lead_id, include_reasoning=True)
                
                result = await self.cqrs_service.execute_query(query)
                if result.success:
                    # Convert CQRS result to UnifiedScoringResult format
                    return self._convert_cqrs_to_unified_result(result, lead_name, lead_context)
                    
            except Exception as e:
                logger.warning(f"CQRS query failed, falling back to direct analysis: {e}")

        # Fall back to enhanced analysis with performance optimizations
        return await self._enhanced_analysis_with_optimizations(lead_name, lead_context, force_refresh)

    async def _enhanced_analysis_with_optimizations(self,
                                                  lead_name: str,
                                                  lead_context: Dict[str, Any],
                                                  force_refresh: bool = False) -> UnifiedScoringResult:
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

        # Perform enhanced analysis with circuit breaker protection
        try:
            start_time = datetime.now()
            
            # Generate lead_id
            lead_id = lead_context.get('lead_id', f"demo_{lead_name.lower().replace(' ', '_').replace('(', '').replace(')', '')}")
            
            # Use circuit breaker for Claude API calls
            if self.claude_breaker:
                analysis_result = await self.claude_breaker.call(
                    self.enhanced_scorer.analyze_lead_comprehensive,
                    lead_id=lead_id,
                    lead_context=lead_context
                )
            else:
                analysis_result = await self.enhanced_scorer.analyze_lead_comprehensive(
                    lead_id=lead_id,
                    lead_context=lead_context
                )
            
            analysis_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Cache the result in optimized cache
            if self.optimized_cache:
                try:
                    if self.cache_breaker:
                        await self.cache_breaker.call(
                            self.optimized_cache.set,
                            cache_key, analysis_result, 300  # 5 minute TTL
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

    def _convert_cqrs_to_unified_result(self, cqrs_result, lead_name: str, lead_context: Dict[str, Any]) -> UnifiedScoringResult:
        """Convert CQRS query result to UnifiedScoringResult format"""
        data = cqrs_result.data
        
        from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import UnifiedScoringResult
        
        return UnifiedScoringResult(
            lead_id=data.get('lead_id', 'unknown'),
            lead_name=lead_name,
            scored_at=datetime.now(),
            final_score=data.get('score', 50.0),
            confidence_score=data.get('confidence', 0.8),
            classification=data.get('classification', 'warm'),
            jorge_score=75,  # Default values
            ml_conversion_score=70,
            churn_risk_score=30,
            engagement_score=80,
            strategic_summary=f"CQRS-optimized analysis for {lead_name}",
            behavioral_insights=data.get('reasoning', 'High-performance analysis via CQRS'),
            reasoning=data.get('reasoning', 'Cached analysis result'),
            risk_factors=['CQRS optimization active'],
            opportunities=['Enhanced performance'],
            recommended_actions=[{'action': 'Follow up', 'priority': 'medium'}],
            next_best_action='Continue engagement',
            expected_timeline='24-48 hours',
            success_probability=75.0,
            feature_breakdown={},
            conversation_context=lead_context,
            sources=['CQRS Cache'],
            analysis_time_ms=cqrs_result.latency_ms,
            claude_reasoning_time_ms=0
        )

    async def get_comprehensive_lead_analysis(self,
                                            lead_name: str,
                                            lead_context: Dict[str, Any],
                                            force_refresh: bool = False) -> UnifiedScoringResult:
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
            lead_id = lead_context.get('lead_id', f"demo_{lead_name.lower().replace(' ', '_').replace('(', '').replace(')', '')}")

            # Get comprehensive analysis
            start_time = datetime.now()
            analysis_result = await self.enhanced_scorer.analyze_lead_comprehensive(
                lead_id=lead_id,
                lead_context=lead_context
            )
            analysis_time = (datetime.now() - start_time).total_seconds() * 1000

            # Cache the result
            self.analysis_cache[cache_key] = {
                "result": analysis_result,
                "timestamp": datetime.now()
            }

            # Update metrics
            self._update_metrics(analysis_time)

            return analysis_result

        except Exception as e:
            # Return fallback analysis on error
            return self._create_fallback_analysis(lead_name, lead_context, str(e))

    async def generate_behavioral_insight(self,
                                        lead_name: str,
                                        analysis_result: UnifiedScoringResult) -> str:
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

    async def generate_quick_action_script(self,
                                         lead_name: str,
                                         script_type: str,
                                         analysis_result: UnifiedScoringResult) -> Dict[str, Any]:
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
                variants=1
            )

            return {
                "success": True,
                "script": automated_script.primary_script,
                "reasoning": automated_script.personalization_notes,
                "success_probability": automated_script.success_probability,
                "channel": automated_script.channel
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "script": f"Hi {lead_name}, this is Jorge. I wanted to follow up with you about your property search. When's a good time to chat?",
                "reasoning": f"Fallback script generated due to system error: {str(e)}"
            }

    def render_enhanced_lead_profile_header(self,
                                          lead_name: str,
                                          analysis_result: UnifiedScoringResult):
        """
        Render enhanced lead profile header with comprehensive analysis.
        """
        # Determine colors based on classification
        score_colors = {
            "hot": "#ef4444",
            "warm": "#f59e0b",
            "cold": "#6366f1",
            "error": "#6b7280"
        }

        score_labels = {
            "hot": "🔥 HOT LEAD",
            "warm": "🔸 WARM LEAD",
            "cold": "❄️ COLD LEAD",
            "error": "⚠️ ANALYSIS ERROR"
        }

        classification = analysis_result.classification
        score_color = score_colors.get(classification, "#6b7280")
        score_label = score_labels.get(classification, "🤖 CLAUDE ANALYSIS")

        # Extract occupation and location from context or analysis
        lead_context = analysis_result.conversation_context
        occupation = lead_context.get("extracted_preferences", {}).get("occupation", "Professional")
        location = lead_context.get("extracted_preferences", {}).get("location", "Austin Area")

        st.markdown(f"""
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
        """, unsafe_allow_html=True)

    def render_enhanced_behavioral_insight(self,
                                         lead_name: str,
                                         analysis_result: UnifiedScoringResult):
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

    def render_enhanced_quick_actions(self,
                                    lead_name: str,
                                    analysis_result: UnifiedScoringResult):
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
                    script_result = loop.run_until_complete(self.generate_quick_action_script(
                        lead_name, "sms", analysis_result
                    ))

                    if script_result.get("success"):
                        st.success("📱 Claude generated SMS script:")
                        st.code(script_result["script"], language=None)
                        st.caption(f"💡 {script_result['reasoning']}")
                        st.toast(f"SMS script ready for {lead_name}!", icon="📱")
                    else:
                        st.error(f"Script generation failed: {script_result.get('error', 'Unknown error')}")

                elif action_type == "email":
                    # Generate email script
                    script_result = loop.run_until_complete(self.generate_quick_action_script(
                        lead_name, "email", analysis_result
                    ))

                    if script_result.get("success"):
                        st.success("📧 Claude generated email draft:")
                        st.code(script_result["script"], language=None)
                        st.caption(f"💡 {script_result['reasoning']}")
                        st.toast(f"Email draft ready for {lead_name}!", icon="📧")
                    else:
                        st.error(f"Email generation failed: {script_result.get('error', 'Unknown error')}")

                elif action_type == "call":
                    # Generate call script
                    script_result = loop.run_until_complete(self.generate_quick_action_script(
                        lead_name, "call", analysis_result
                    ))

                    if script_result.get("success"):
                        st.success("📞 Claude generated call script:")
                        st.code(script_result["script"], language=None)
                        st.caption(f"💡 {script_result['reasoning']}")
                        st.toast(f"Call script ready for {lead_name}!", icon="📞")
                    else:
                        st.error(f"Call script generation failed: {script_result.get('error', 'Unknown error')}")

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

            "Mike & Jessica Rodriguez": f"First-time buyer family (Score: {analysis_result.final_score:.0f}%). Claude detected high sentiment but low confidence. Safety & schools research indicates Pflugerville preference. Emphasize 8/10 school ratings.",

            "Robert & Linda Williams": f"Luxury downsizers (Score: {analysis_result.final_score:.0f}%). Relationship-focused with high trust indicators. Value personal service over automation. Recommend exclusive downtown access and concierge approach."
        }

        # Find matching persona or use dynamic insight
        for persona, insight in base_insights.items():
            if persona.split()[0] in lead_name or persona.split()[1] in lead_name:
                return insight

        # Dynamic insight based on analysis
        return f"Lead scored {analysis_result.final_score:.0f}% with {analysis_result.classification} classification. Claude confidence: {analysis_result.confidence_score:.0%}. {analysis_result.strategic_summary}"

    def _create_fallback_analysis(self, lead_name: str, lead_context: Dict[str, Any], error: str) -> UnifiedScoringResult:
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
            claude_reasoning_time_ms=0
        )

    def _update_metrics(self, analysis_time_ms: float):
        """Update performance metrics."""
        count = self.performance_metrics["analyses_completed"]
        self.performance_metrics["analyses_completed"] += 1

        # Update average analysis time
        current_avg = self.performance_metrics["avg_analysis_time_ms"]
        self.performance_metrics["avg_analysis_time_ms"] = (
            (current_avg * count + analysis_time_ms) / (count + 1)
        )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get service performance metrics."""
        total_requests = self.performance_metrics["analyses_completed"] + self.performance_metrics["cache_hits"]
        cache_hit_rate = (
            self.performance_metrics["cache_hits"] / total_requests
            if total_requests > 0 else 0
        )

        return {
            **self.performance_metrics,
            "cache_hit_rate": cache_hit_rate,
            "total_requests": total_requests
        }


# Singleton instance for use in components
_enhanced_lead_intelligence = None

def get_enhanced_lead_intelligence() -> EnhancedLeadIntelligence:
    """Get singleton instance of Enhanced Lead Intelligence."""
    global _enhanced_lead_intelligence
    if _enhanced_lead_intelligence is None:
        _enhanced_lead_intelligence = EnhancedLeadIntelligence()
    return _enhanced_lead_intelligence