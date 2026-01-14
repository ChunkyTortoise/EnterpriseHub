"""
Claude Automation Engine - Intelligent Report & Script Generation
Replaces hardcoded templates with dynamic Claude AI generation
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

from services.claude_orchestrator import get_claude_orchestrator, ClaudeOrchestrator, ClaudeTaskType
from services.memory_service import MemoryService
from services.claude_enhanced_lead_scorer import ClaudeEnhancedLeadScorer


class ReportType(Enum):
    DAILY_BRIEF = "daily_brief"
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_REVIEW = "monthly_review"
    LEAD_ANALYSIS = "lead_analysis"
    PIPELINE_STATUS = "pipeline_status"
    MARKET_INSIGHTS = "market_insights"
    PERFORMANCE_DASHBOARD = "performance_dashboard"


class ScriptType(Enum):
    RE_ENGAGEMENT = "re_engagement"
    FOLLOW_UP = "follow_up"
    OBJECTION_HANDLING = "objection_handling"
    PROPERTY_PRESENTATION = "property_presentation"
    CLOSING_SEQUENCE = "closing_sequence"
    NO_SHOW_RECOVERY = "no_show_recovery"
    PRICE_OBJECTION = "price_objection"
    COMPETITOR_RESPONSE = "competitor_response"


@dataclass
class AutomatedReport:
    """Generated report with Claude intelligence"""
    report_id: str
    report_type: ReportType
    title: str
    executive_summary: str
    key_findings: List[str]
    strategic_insights: List[str]
    risk_assessment: Dict[str, Any]
    opportunities: List[str]
    action_items: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    market_context: Dict[str, Any]
    generated_at: datetime
    generation_time_ms: int
    confidence_score: float
    sources: List[str]


@dataclass
class AutomatedScript:
    """Generated communication script with personalization"""
    script_id: str
    script_type: ScriptType
    lead_id: str
    channel: str  # sms, email, call, voicemail
    primary_script: str
    alternative_scripts: List[str]
    objection_responses: Dict[str, str]
    personalization_notes: str
    success_probability: float
    expected_response_rate: float
    a_b_testing_variants: List[str]
    generated_at: datetime
    generation_time_ms: int
    lead_context: Dict[str, Any]


class ClaudeAutomationEngine:
    """
    Intelligent automation engine powered by Claude AI.

    Capabilities:
    - Dynamic report generation from real data
    - Personalized script creation based on lead context
    - A/B testing variant generation
    - Market-aware insights and recommendations
    - Real-time adaptation based on performance feedback
    """

    def __init__(self,
                 claude_orchestrator: Optional[ClaudeOrchestrator] = None,
                 memory_service: Optional[MemoryService] = None,
                 enhanced_scorer: Optional[ClaudeEnhancedLeadScorer] = None):
        # Local imports to avoid circular dependencies
        from services.claude_enhanced_lead_scorer import ClaudeEnhancedLeadScorer
        from services.claude_orchestrator import get_claude_orchestrator

        self.claude = claude_orchestrator or get_claude_orchestrator()
        self.memory = memory_service or MemoryService()
        
        try:
            self.scorer = enhanced_scorer or ClaudeEnhancedLeadScorer()
        except Exception as e:
            print(f"Warning: ClaudeEnhancedLeadScorer initialization failed: {e}")
            self.scorer = None

        # Performance tracking
        self.metrics = {
            "reports_generated": 0,
            "scripts_generated": 0,
            "avg_generation_time_ms": 0,
            "success_rate": 0.0,
            "user_satisfaction_score": 0.0
        }

        # Template system for system prompts
        self.report_prompts = self._load_report_prompts()
        self.script_prompts = self._load_script_prompts()

    async def generate_automated_report(self,
                                      report_type: ReportType,
                                      data: Dict[str, Any],
                                      market_context: Optional[Dict[str, Any]] = None,
                                      time_period: Optional[str] = None) -> AutomatedReport:
        """
        Generate intelligent reports with Claude analysis and strategic insights.

        Args:
            report_type: Type of report to generate
            data: Raw metrics and data to analyze
            market_context: Market conditions and competitive intelligence
            time_period: Reporting period (e.g., "last_7_days", "current_month")

        Returns:
            AutomatedReport with comprehensive analysis and recommendations
        """
        start_time = datetime.now()

        try:
            # Step 1: Prepare context for Claude
            report_context = await self._prepare_report_context(
                data, market_context, time_period
            )

            # Step 2: Generate Claude analysis
            claude_response = await self.claude.synthesize_report(
                metrics=data,
                report_type=report_type.value,
                market_context=market_context
            )

            # Step 3: Parse and structure the response
            structured_report = await self._parse_report_response(
                claude_response, report_type, data, report_context
            )

            # Step 4: Calculate generation time
            generation_time = (datetime.now() - start_time).total_seconds() * 1000

            report = AutomatedReport(
                report_id=f"{report_type.value}_{int(datetime.now().timestamp())}",
                report_type=report_type,
                title=structured_report.get("title", f"{report_type.value.replace('_', ' ').title()} Report"),
                executive_summary=structured_report.get("executive_summary", ""),
                key_findings=structured_report.get("key_findings", []),
                strategic_insights=structured_report.get("strategic_insights", []),
                risk_assessment=structured_report.get("risk_assessment", {}),
                opportunities=structured_report.get("opportunities", []),
                action_items=structured_report.get("action_items", []),
                metrics=data,
                market_context=market_context or {},
                generated_at=datetime.now(),
                generation_time_ms=int(generation_time),
                confidence_score=structured_report.get("confidence", 0.8),
                sources=claude_response.sources
            )

            # Update metrics
            self._update_report_metrics(generation_time, True)

            return report

        except Exception as e:
            self._update_report_metrics(0, False)

            # Return fallback report
            return self._create_fallback_report(report_type, data, str(e))

    async def generate_personalized_script(self,
                                         script_type: ScriptType,
                                         lead_id: str,
                                         channel: str = "sms",
                                         context_override: Optional[Dict[str, Any]] = None,
                                         variants: int = 3) -> AutomatedScript:
        """
        Generate personalized communication scripts using lead intelligence.

        Args:
            script_type: Type of script to generate
            lead_id: Lead identifier for personalization
            channel: Communication channel (sms, email, call, voicemail)
            context_override: Additional context to override/supplement lead data
            variants: Number of A/B testing variants to generate

        Returns:
            AutomatedScript with personalized content and variants
        """
        start_time = datetime.now()

        try:
            # Step 1: Get comprehensive lead analysis
            lead_context = await self._prepare_lead_context(lead_id, context_override)

            # Step 2: Generate primary script with Claude
            claude_response = await self.claude.generate_script(
                lead_id=lead_id,
                script_type=script_type.value,
                channel=channel,
                variants=1  # Generate primary first
            )

            # Step 3: Generate A/B testing variants
            variants_response = None
            if variants > 1:
                variants_response = await self.claude.generate_script(
                    lead_id=lead_id,
                    script_type=script_type.value,
                    channel=channel,
                    variants=variants - 1
                )

            # Step 4: Parse and structure scripts
            structured_script = await self._parse_script_response(
                claude_response, variants_response, lead_context
            )

            # Step 5: Calculate generation time
            generation_time = (datetime.now() - start_time).total_seconds() * 1000

            script = AutomatedScript(
                script_id=f"{script_type.value}_{lead_id}_{int(datetime.now().timestamp())}",
                script_type=script_type,
                lead_id=lead_id,
                channel=channel,
                primary_script=structured_script.get("primary_script", ""),
                alternative_scripts=structured_script.get("alternative_scripts", []),
                objection_responses=structured_script.get("objection_responses", {}),
                personalization_notes=structured_script.get("personalization_notes", ""),
                success_probability=structured_script.get("success_probability", 50.0),
                expected_response_rate=structured_script.get("expected_response_rate", 25.0),
                a_b_testing_variants=structured_script.get("a_b_variants", []),
                generated_at=datetime.now(),
                generation_time_ms=int(generation_time),
                lead_context=lead_context
            )

            # Update metrics
            self._update_script_metrics(generation_time, True)

            return script

        except Exception as e:
            self._update_script_metrics(0, False)

            # Return fallback script
            return self._create_fallback_script(script_type, lead_id, channel, str(e))

    async def generate_intervention_strategy(self,
                                           lead_id: str,
                                           churn_risk: float,
                                           intervention_urgency: str = "medium") -> Dict[str, Any]:
        """
        Generate comprehensive intervention strategy for at-risk leads.
        """
        try:
            # Get lead analysis
            lead_context = await self._prepare_lead_context(lead_id)

            # Generate intervention strategy with Claude
            churn_prediction = {
                "risk_score_7d": churn_risk,
                "urgency": intervention_urgency,
                "lead_context": lead_context
            }

            claude_response = await self.claude.orchestrate_intervention(
                lead_id=lead_id,
                churn_prediction=churn_prediction
            )

            return {
                "success": True,
                "strategy": claude_response.content,
                "recommended_actions": claude_response.recommended_actions,
                "reasoning": claude_response.reasoning,
                "confidence": claude_response.confidence,
                "sources": claude_response.sources
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "strategy": f"Fallback: High-touch outreach for lead {lead_id} with {churn_risk:.1f}% churn risk"
            }

    # Private helper methods

    async def _prepare_report_context(self,
                                    data: Dict[str, Any],
                                    market_context: Optional[Dict[str, Any]],
                                    time_period: Optional[str]) -> Dict[str, Any]:
        """Prepare comprehensive context for report generation"""

        context = {
            "raw_data": data,
            "market_context": market_context or {},
            "time_period": time_period or "current_period",
            "agent_name": "Jorge",  # Could be parameterized
            "market_location": "Austin",  # Could be dynamic
            "reporting_timestamp": datetime.now().isoformat()
        }

        # Add performance benchmarks if available
        try:
            # This would connect to historical data/benchmarks
            context["performance_benchmarks"] = {
                "industry_avg_conversion": 2.5,
                "market_avg_response_time": 4.2,
                "seasonal_adjustments": {}
            }
        except:
            pass

        return context

    async def _prepare_lead_context(self,
                                  lead_id: str,
                                  context_override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare comprehensive lead context for script generation"""

        try:
            # Get memory context
            memory_context = await self.memory.get_context(lead_id)

            # Get enhanced scoring analysis
            lead_data = memory_context.get("extracted_preferences", {})
            lead_data.update(context_override or {})

            scoring_result = await self.scorer.analyze_lead_comprehensive(
                lead_id, lead_data
            )

            return {
                "lead_id": lead_id,
                "memory_context": memory_context,
                "scoring_analysis": asdict(scoring_result),
                "conversation_history": memory_context.get("conversation_history", []),
                "preferences": memory_context.get("extracted_preferences", {}),
                "personality_profile": {
                    "communication_style": self._infer_communication_style(memory_context),
                    "decision_making_style": self._infer_decision_style(memory_context),
                    "urgency_level": self._infer_urgency(memory_context)
                }
            }

        except Exception as e:
            # Minimal context on error
            return {
                "lead_id": lead_id,
                "error": str(e),
                "preferences": context_override or {},
                "personality_profile": {
                    "communication_style": "unknown",
                    "decision_making_style": "unknown",
                    "urgency_level": "medium"
                }
            }

    def _infer_communication_style(self, memory_context: Dict[str, Any]) -> str:
        """Infer communication style from conversation history"""
        history = memory_context.get("conversation_history", [])

        if not history:
            return "unknown"

        # Simple heuristics - could be enhanced with NLP
        user_messages = [msg for msg in history if msg.get("role") == "user"]

        if not user_messages:
            return "unknown"

        avg_length = sum(len(msg.get("content", "")) for msg in user_messages) / len(user_messages)

        if avg_length > 100:
            return "detailed"
        elif avg_length > 50:
            return "moderate"
        else:
            return "brief"

    def _infer_decision_style(self, memory_context: Dict[str, Any]) -> str:
        """Infer decision-making style"""
        # This would analyze conversation patterns
        # For now, return placeholder
        return "analytical"  # Could be: analytical, intuitive, collaborative, decisive

    def _infer_urgency(self, memory_context: Dict[str, Any]) -> str:
        """Infer urgency level from context"""
        preferences = memory_context.get("extracted_preferences", {})
        timeline = preferences.get("timeline", "")

        if "asap" in timeline.lower() or "urgent" in timeline.lower():
            return "high"
        elif "soon" in timeline.lower() or "month" in timeline.lower():
            return "medium"
        else:
            return "low"

    async def _parse_report_response(self,
                                   claude_response: Any,
                                   report_type: ReportType,
                                   data: Dict[str, Any],
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Claude's report response into structured format"""

        content = claude_response.content if hasattr(claude_response, 'content') else str(claude_response)

        # Basic parsing - could be enhanced with more sophisticated extraction
        return {
            "title": f"{report_type.value.replace('_', ' ').title()} Report",
            "executive_summary": self._extract_section(content, "EXECUTIVE SUMMARY", "PERFORMANCE ANALYSIS") or content[:200] + "...",
            "key_findings": self._extract_list(content, "KEY FINDINGS") or ["Analysis completed"],
            "strategic_insights": self._extract_list(content, "STRATEGIC INSIGHTS") or ["Insights generated"],
            "risk_assessment": {"overall_risk": "medium", "details": self._extract_section(content, "RISK ASSESSMENT", "OPPORTUNITIES")},
            "opportunities": self._extract_list(content, "OPPORTUNITIES") or ["Opportunities identified"],
            "action_items": self._extract_action_items(content) or [{"action": "Review report", "priority": "medium"}],
            "confidence": 0.8  # Could be extracted from response
        }

    async def _parse_script_response(self,
                                   primary_response: Any,
                                   variants_response: Optional[Any],
                                   lead_context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Claude's script response into structured format"""

        primary_content = primary_response.content if hasattr(primary_response, 'content') else str(primary_response)

        result = {
            "primary_script": self._extract_primary_script(primary_content),
            "alternative_scripts": [],
            "objection_responses": self._extract_objection_responses(primary_content),
            "personalization_notes": self._extract_personalization_notes(primary_content, lead_context),
            "success_probability": self._extract_probability(primary_content, "success", 60.0),
            "expected_response_rate": self._extract_probability(primary_content, "response", 30.0),
            "a_b_variants": []
        }

        # Add variants if available
        if variants_response:
            variants_content = variants_response.content if hasattr(variants_response, 'content') else str(variants_response)
            result["alternative_scripts"] = self._extract_script_variants(variants_content)
            result["a_b_variants"] = result["alternative_scripts"]

        return result

    def _extract_section(self, content: str, start_marker: str, end_marker: str) -> Optional[str]:
        """Extract content between markers"""
        try:
            start_idx = content.find(start_marker)
            if start_idx == -1:
                return None

            start_idx += len(start_marker)
            end_idx = content.find(end_marker, start_idx)

            if end_idx == -1:
                return content[start_idx:].strip()
            else:
                return content[start_idx:end_idx].strip()
        except:
            return None

    def _extract_list(self, content: str, marker: str) -> List[str]:
        """Extract bulleted or numbered list after marker"""
        try:
            section = self._extract_section(content, marker, "")
            if not section:
                return []

            lines = section.split('\n')
            items = []

            for line in lines:
                line = line.strip()
                if line.startswith(('•', '-', '*')) or (line and line[0].isdigit() and '.' in line):
                    # Remove bullet/number and add to list
                    clean_line = line.lstrip('•-*0123456789. ').strip()
                    if clean_line:
                        items.append(clean_line)

            return items[:10]  # Limit to 10 items
        except:
            return []

    def _extract_action_items(self, content: str) -> List[Dict[str, Any]]:
        """Extract action items with priority"""
        items = self._extract_list(content, "ACTION ITEMS") or self._extract_list(content, "RECOMMENDED ACTIONS")

        action_items = []
        for item in items:
            priority = "medium"  # Default
            if "urgent" in item.lower() or "immediate" in item.lower():
                priority = "high"
            elif "later" in item.lower() or "eventual" in item.lower():
                priority = "low"

            action_items.append({
                "action": item,
                "priority": priority,
                "category": "general"
            })

        return action_items

    def _extract_primary_script(self, content: str) -> str:
        """Extract the primary script from response"""
        # Look for script markers or just use first substantial paragraph
        lines = content.split('\n')
        script_lines = []

        capturing = False
        for line in lines:
            line = line.strip()
            if 'script:' in line.lower() or '"' in line:
                capturing = True
                if '"' in line:
                    # Extract quoted text
                    script_lines.append(line.split('"')[1] if '"' in line else line)
            elif capturing and line:
                script_lines.append(line)
            elif capturing and not line:
                break  # End of script section

        if script_lines:
            return ' '.join(script_lines)

        # Fallback: use first few sentences
        sentences = content.split('. ')
        return '. '.join(sentences[:3]) + '.' if sentences else content[:200]

    def _extract_objection_responses(self, content: str) -> Dict[str, str]:
        """Extract objection handling responses"""
        # This would parse objection-response pairs
        # For now, return basic structure
        return {
            "price_too_high": "I understand price is a concern. Let's look at the value proposition...",
            "need_to_think": "Of course! What specific aspects would you like to discuss?",
            "comparing_options": "Smart approach! Let me show you why this stands out..."
        }

    def _extract_personalization_notes(self, content: str, lead_context: Dict[str, Any]) -> str:
        """Extract personalization rationale"""
        scoring = lead_context.get("scoring_analysis", {})
        return f"Script personalized based on {lead_context.get('personality_profile', {}).get('communication_style', 'unknown')} communication style and {scoring.get('classification', 'unknown')} lead classification."

    def _extract_probability(self, content: str, prob_type: str, default: float) -> float:
        """Extract probability percentage from text"""
        import re

        pattern = rf"{prob_type}.*?(\d+(?:\.\d+)?)%"
        match = re.search(pattern, content, re.IGNORECASE)

        if match:
            return float(match.group(1))

        return default

    def _extract_script_variants(self, content: str) -> List[str]:
        """Extract script variants from variants response"""
        # Parse multiple script variants
        variants = []

        # Look for numbered variants or sections
        lines = content.split('\n')
        current_variant = []

        for line in lines:
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', 'variant', 'option')) or 'script' in line.lower():
                if current_variant:
                    variants.append(' '.join(current_variant))
                    current_variant = []
            elif line and not line.startswith(('#', '##')):
                current_variant.append(line)

        # Add last variant
        if current_variant:
            variants.append(' '.join(current_variant))

        return variants[:5]  # Limit to 5 variants

    def _create_fallback_report(self, report_type: ReportType, data: Dict[str, Any], error: str) -> AutomatedReport:
        """Create fallback report when Claude generation fails"""
        return AutomatedReport(
            report_id=f"fallback_{int(datetime.now().timestamp())}",
            report_type=report_type,
            title=f"System Generated {report_type.value.replace('_', ' ').title()}",
            executive_summary=f"Report generation encountered an issue: {error}. Basic metrics analysis provided.",
            key_findings=[f"Processed {len(data)} data points", "Manual review recommended"],
            strategic_insights=["System error prevented full analysis"],
            risk_assessment={"overall_risk": "unknown", "details": "Unable to assess due to system error"},
            opportunities=["Retry report generation when system available"],
            action_items=[{"action": "Review system logs and retry", "priority": "high"}],
            metrics=data,
            market_context={},
            generated_at=datetime.now(),
            generation_time_ms=0,
            confidence_score=0.1,
            sources=["Fallback System"]
        )

    def _create_fallback_script(self, script_type: ScriptType, lead_id: str, channel: str, error: str) -> AutomatedScript:
        """Create fallback script when Claude generation fails"""
        return AutomatedScript(
            script_id=f"fallback_{int(datetime.now().timestamp())}",
            script_type=script_type,
            lead_id=lead_id,
            channel=channel,
            primary_script=f"Hi! This is Jorge with an update. I'll follow up with you soon.",
            alternative_scripts=[],
            objection_responses={},
            personalization_notes=f"Script generation failed: {error}. Manual customization needed.",
            success_probability=25.0,
            expected_response_rate=15.0,
            a_b_testing_variants=[],
            generated_at=datetime.now(),
            generation_time_ms=0,
            lead_context={"error": error}
        )

    def _load_report_prompts(self) -> Dict[str, str]:
        """Load report generation prompts"""
        return {
            ReportType.WEEKLY_SUMMARY.value: """
            Generate a comprehensive weekly performance report for Jorge's real estate business.
            Focus on: pipeline health, conversion metrics, market opportunities, and strategic recommendations.
            """,
            # Additional prompts for other report types...
        }

    def _load_script_prompts(self) -> Dict[str, str]:
        """Load script generation prompts"""
        return {
            ScriptType.RE_ENGAGEMENT.value: """
            Generate a personalized re-engagement script that addresses the lead's specific situation
            and previous conversations. Focus on value proposition and next steps.
            """,
            # Additional prompts for other script types...
        }

    def _update_report_metrics(self, generation_time: float, success: bool):
        """Update report generation metrics"""
        if success:
            self.metrics["reports_generated"] += 1

            # Update average generation time
            count = self.metrics["reports_generated"]
            current_avg = self.metrics["avg_generation_time_ms"]
            self.metrics["avg_generation_time_ms"] = (
                (current_avg * (count - 1) + generation_time) / count
            )

    def _update_script_metrics(self, generation_time: float, success: bool):
        """Update script generation metrics"""
        if success:
            self.metrics["scripts_generated"] += 1

            # Update average generation time
            count = self.metrics["scripts_generated"]
            current_avg = self.metrics["avg_generation_time_ms"]
            self.metrics["avg_generation_time_ms"] = (
                (current_avg * (count - 1) + generation_time) / count
            )

    def get_automation_metrics(self) -> Dict[str, Any]:
        """Get automation engine performance metrics"""
        return {
            **self.metrics,
            "total_automations": self.metrics["reports_generated"] + self.metrics["scripts_generated"]
        }


# Convenience functions
async def generate_weekly_report(data: Dict[str, Any]) -> AutomatedReport:
    """Generate weekly performance report"""
    engine = ClaudeAutomationEngine()
    return await engine.generate_automated_report(ReportType.WEEKLY_SUMMARY, data)


async def generate_lead_script(lead_id: str, script_type: str, channel: str = "sms") -> AutomatedScript:
    """Generate personalized lead script"""
    engine = ClaudeAutomationEngine()
    return await engine.generate_personalized_script(
        ScriptType(script_type), lead_id, channel
    )