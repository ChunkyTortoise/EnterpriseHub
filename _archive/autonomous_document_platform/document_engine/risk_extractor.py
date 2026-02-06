"""
Risk Extractor - Contract Risk Identification and Scoring

Identify and score contractual risks using AI-powered analysis.
Leverages EnterpriseHub patterns:
- ClaudeAssistant for contextual risk analysis
- LLMClient for multi-turn analysis with routing
- SemanticResponseCache for risk assessment caching
- Analytics tracking patterns

Key Features:
- Risk taxonomy (financial, operational, compliance, reputational)
- Clause-level risk scoring with confidence intervals
- Red flag detection (unlimited liability, auto-renewal, unusual indemnity)
- Missing clause detection (force majeure, limitation of liability)
- Risk comparison against industry standards
- Executive risk summary generation
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter

# EnterpriseHub reused components
import sys
sys.path.append('/Users/cave/Documents/GitHub/EnterpriseHub')

from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.core.llm_client import LLMClient, TaskComplexity
from ghl_real_estate_ai.services.cache_service import CacheService
from autonomous_document_platform.document_engine.legal_analyzer import LegalClause, ClauseType, ContractType, ContractAnalysis
from autonomous_document_platform.document_engine.intelligent_parser import ParsedDocument
from autonomous_document_platform.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RiskCategory(str, Enum):
    """Categories of contractual risks"""
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    REPUTATIONAL = "reputational"
    LEGAL = "legal"
    STRATEGIC = "strategic"
    TECHNICAL = "technical"


class RiskSeverity(str, Enum):
    """Risk severity levels"""
    CRITICAL = "critical"  # Immediate attention required
    HIGH = "high"         # Significant risk
    MEDIUM = "medium"     # Moderate risk
    LOW = "low"          # Minor risk
    MINIMAL = "minimal"   # Negligible risk


class RedFlagType(str, Enum):
    """Types of red flag patterns"""
    UNLIMITED_LIABILITY = "unlimited_liability"
    AUTO_RENEWAL = "auto_renewal"
    UNUSUAL_INDEMNITY = "unusual_indemnity"
    MISSING_TERMINATION = "missing_termination"
    BROAD_IP_ASSIGNMENT = "broad_ip_assignment"
    ONEROUS_PENALTIES = "onerous_penalties"
    VAGUE_OBLIGATIONS = "vague_obligations"
    UNFAIR_DISPUTE_RESOLUTION = "unfair_dispute_resolution"
    EXCESSIVE_CONFIDENTIALITY = "excessive_confidentiality"
    WEAK_DATA_PROTECTION = "weak_data_protection"


@dataclass
class Risk:
    """Single identified risk with detailed metadata"""
    risk_id: str
    category: RiskCategory
    severity: RiskSeverity
    confidence: float  # 0.0 to 1.0
    title: str
    description: str
    affected_clauses: List[str] = field(default_factory=list)  # Citation IDs
    mitigation_suggestions: List[str] = field(default_factory=list)
    industry_comparison: Optional[str] = None
    financial_impact_estimate: Optional[str] = None
    likelihood_estimate: Optional[float] = None  # 0.0 to 1.0
    regulatory_implications: List[str] = field(default_factory=list)
    precedent_cases: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.utcnow)

    def get_risk_score(self) -> float:
        """Calculate composite risk score"""
        severity_weights = {
            RiskSeverity.CRITICAL: 1.0,
            RiskSeverity.HIGH: 0.8,
            RiskSeverity.MEDIUM: 0.6,
            RiskSeverity.LOW: 0.4,
            RiskSeverity.MINIMAL: 0.2
        }

        base_score = severity_weights.get(self.severity, 0.5)
        confidence_adjusted = base_score * self.confidence

        # Adjust for likelihood if available
        if self.likelihood_estimate:
            confidence_adjusted *= self.likelihood_estimate

        return min(1.0, confidence_adjusted)


@dataclass
class RedFlag:
    """Red flag pattern detected in contract"""
    flag_id: str
    flag_type: RedFlagType
    severity: RiskSeverity
    description: str
    evidence_text: str
    clause_reference: Optional[str] = None
    confidence: float = 0.0
    immediate_action_required: bool = False
    legal_precedents: List[str] = field(default_factory=list)
    mitigation_priority: int = 1  # 1 = highest priority
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RiskAssessment:
    """Complete risk assessment for a contract"""
    document_id: str
    contract_type: ContractType
    overall_risk_score: float  # 0.0 to 1.0
    risk_level: str  # "Low", "Medium", "High", "Critical"
    risks: List[Risk] = field(default_factory=list)
    red_flags: List[RedFlag] = field(default_factory=list)
    missing_protections: List[str] = field(default_factory=list)
    industry_benchmark_comparison: Dict[str, Any] = field(default_factory=dict)
    executive_summary: str = ""
    key_concerns: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    risk_distribution: Dict[RiskCategory, int] = field(default_factory=dict)
    assessment_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class RedFlagDetector:
    """Detect known high-risk patterns in contracts"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._setup_patterns()

    def _setup_patterns(self):
        """Setup regex patterns for red flag detection"""
        self.patterns = {
            RedFlagType.UNLIMITED_LIABILITY: [
                r'unlimited liability',
                r'without limitation',
                r'liability.*unlimited',
                r'no limit.*liability',
                r'liability.*cap.*shall not apply'
            ],
            RedFlagType.AUTO_RENEWAL: [
                r'automatically.*renew',
                r'auto.*renew',
                r'evergreen',
                r'successive.*periods?.*unless.*notice',
                r'renew.*automatically'
            ],
            RedFlagType.UNUSUAL_INDEMNITY: [
                r'indemnify.*harmless.*all.*claims',
                r'defend.*hold harmless.*any.*claim',
                r'broad.*indemnification',
                r'indemnify.*gross negligence',
                r'indemnify.*willful misconduct'
            ],
            RedFlagType.BROAD_IP_ASSIGNMENT: [
                r'all.*intellectual property.*assign',
                r'work.*hire.*belongs.*company',
                r'inventions.*discoveries.*assign',
                r'ideas.*concepts.*property.*company'
            ],
            RedFlagType.ONEROUS_PENALTIES: [
                r'liquidated damages.*\$[\d,]+',
                r'penalty.*breach.*\$[\d,]+',
                r'damages.*not.*less than.*\$[\d,]+',
                r'minimum.*damages.*\$[\d,]+'
            ],
            RedFlagType.VAGUE_OBLIGATIONS: [
                r'reasonable efforts',
                r'best efforts(?!\s+(?:commercially|industry))',
                r'as.*reasonably.*determined',
                r'subject to.*discretion'
            ],
            RedFlagType.UNFAIR_DISPUTE_RESOLUTION: [
                r'arbitration.*binding.*final',
                r'waive.*jury.*trial',
                r'disputes.*resolved.*[A-Z][a-z]+.*only',
                r'exclusive.*jurisdiction.*[A-Z][a-z]+'
            ]
        }

    async def detect_red_flags(
        self,
        contract_text: str,
        contract_analysis: ContractAnalysis
    ) -> List[RedFlag]:
        """Detect red flag patterns in contract text"""

        red_flags = []

        for flag_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, contract_text, re.IGNORECASE | re.MULTILINE)

                for match in matches:
                    # Get context around the match
                    context_start = max(0, match.start() - 100)
                    context_end = min(len(contract_text), match.end() + 100)
                    context = contract_text[context_start:context_end]

                    # Calculate confidence based on pattern specificity and context
                    confidence = self._calculate_pattern_confidence(
                        flag_type, pattern, context, contract_analysis
                    )

                    if confidence >= 0.6:  # Only include high-confidence matches
                        red_flag = RedFlag(
                            flag_id=f"flag_{flag_type.value}_{match.start()}",
                            flag_type=flag_type,
                            severity=self._determine_flag_severity(flag_type, context),
                            description=self._generate_flag_description(flag_type, context),
                            evidence_text=match.group(),
                            confidence=confidence,
                            immediate_action_required=flag_type in [
                                RedFlagType.UNLIMITED_LIABILITY,
                                RedFlagType.ONEROUS_PENALTIES
                            ],
                            mitigation_priority=self._get_mitigation_priority(flag_type)
                        )

                        red_flags.append(red_flag)

        # Remove duplicate flags (same type, similar position)
        red_flags = self._deduplicate_red_flags(red_flags)

        self.logger.info(f"Detected {len(red_flags)} red flags in contract")
        return red_flags

    def _calculate_pattern_confidence(
        self,
        flag_type: RedFlagType,
        pattern: str,
        context: str,
        contract_analysis: ContractAnalysis
    ) -> float:
        """Calculate confidence score for a pattern match"""

        # Base confidence from pattern specificity
        base_confidence = 0.7

        # Boost confidence for legal contract context
        legal_indicators = ['clause', 'section', 'party', 'agreement', 'contract']
        context_lower = context.lower()
        legal_context_boost = sum(0.05 for indicator in legal_indicators if indicator in context_lower)

        # Adjust for contract type relevance
        type_relevance = {
            ContractType.EMPLOYMENT: {
                RedFlagType.BROAD_IP_ASSIGNMENT: 0.2,
                RedFlagType.UNLIMITED_LIABILITY: 0.1
            },
            ContractType.NDA: {
                RedFlagType.EXCESSIVE_CONFIDENTIALITY: 0.15
            },
            ContractType.SERVICE: {
                RedFlagType.UNLIMITED_LIABILITY: 0.2,
                RedFlagType.ONEROUS_PENALTIES: 0.15
            }
        }

        relevance_boost = type_relevance.get(contract_analysis.contract_type, {}).get(flag_type, 0)

        total_confidence = min(1.0, base_confidence + legal_context_boost + relevance_boost)
        return total_confidence

    def _determine_flag_severity(self, flag_type: RedFlagType, context: str) -> RiskSeverity:
        """Determine severity level for a red flag"""

        severity_map = {
            RedFlagType.UNLIMITED_LIABILITY: RiskSeverity.CRITICAL,
            RedFlagType.ONEROUS_PENALTIES: RiskSeverity.HIGH,
            RedFlagType.BROAD_IP_ASSIGNMENT: RiskSeverity.HIGH,
            RedFlagType.AUTO_RENEWAL: RiskSeverity.MEDIUM,
            RedFlagType.UNUSUAL_INDEMNITY: RiskSeverity.HIGH,
            RedFlagType.VAGUE_OBLIGATIONS: RiskSeverity.MEDIUM,
            RedFlagType.UNFAIR_DISPUTE_RESOLUTION: RiskSeverity.MEDIUM
        }

        base_severity = severity_map.get(flag_type, RiskSeverity.MEDIUM)

        # Check for aggravating factors in context
        aggravating_terms = ['gross negligence', 'willful misconduct', 'criminal', 'unlimited']
        if any(term in context.lower() for term in aggravating_terms):
            if base_severity == RiskSeverity.HIGH:
                return RiskSeverity.CRITICAL
            elif base_severity == RiskSeverity.MEDIUM:
                return RiskSeverity.HIGH

        return base_severity

    def _generate_flag_description(self, flag_type: RedFlagType, context: str) -> str:
        """Generate human-readable description for a red flag"""

        descriptions = {
            RedFlagType.UNLIMITED_LIABILITY: "Contract contains unlimited liability provisions that could expose the company to significant financial risk.",
            RedFlagType.AUTO_RENEWAL: "Contract automatically renews without explicit consent, potentially creating unintended long-term obligations.",
            RedFlagType.UNUSUAL_INDEMNITY: "Broad indemnification clause may require covering costs beyond reasonable business risks.",
            RedFlagType.BROAD_IP_ASSIGNMENT: "Overly broad intellectual property assignment could transfer valuable company assets.",
            RedFlagType.ONEROUS_PENALTIES: "Contract includes severe penalty clauses that may be disproportionate to potential damages.",
            RedFlagType.VAGUE_OBLIGATIONS: "Contract contains vague or subjective performance standards that could lead to disputes.",
            RedFlagType.UNFAIR_DISPUTE_RESOLUTION: "Dispute resolution terms may be heavily biased toward the counterparty."
        }

        return descriptions.get(flag_type, "Potential contractual risk identified.")

    def _get_mitigation_priority(self, flag_type: RedFlagType) -> int:
        """Get mitigation priority (1 = highest)"""

        priorities = {
            RedFlagType.UNLIMITED_LIABILITY: 1,
            RedFlagType.ONEROUS_PENALTIES: 1,
            RedFlagType.BROAD_IP_ASSIGNMENT: 2,
            RedFlagType.UNUSUAL_INDEMNITY: 2,
            RedFlagType.AUTO_RENEWAL: 3,
            RedFlagType.UNFAIR_DISPUTE_RESOLUTION: 3,
            RedFlagType.VAGUE_OBLIGATIONS: 4
        }

        return priorities.get(flag_type, 5)

    def _deduplicate_red_flags(self, red_flags: List[RedFlag]) -> List[RedFlag]:
        """Remove duplicate red flags"""

        # Group by flag type and keep highest confidence
        flag_groups = defaultdict(list)
        for flag in red_flags:
            flag_groups[flag.flag_type].append(flag)

        deduplicated = []
        for flag_type, flags in flag_groups.items():
            # Keep the highest confidence flag of each type
            best_flag = max(flags, key=lambda f: f.confidence)
            deduplicated.append(best_flag)

        return deduplicated


class RiskScorer:
    """Score and prioritize risks using AI-powered analysis"""

    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or CacheService()
        self.claude_assistant = ClaudeAssistant(context_type="risk_analysis")
        self.llm_client = LLMClient(provider="claude")

    async def score_clause_risk(
        self,
        clause: LegalClause,
        contract_type: ContractType,
        industry_context: Optional[str] = None
    ) -> List[Risk]:
        """Score risks for a specific clause"""

        # Generate semantic cache key
        clause_fingerprint = f"{clause.clause_type.value}_{contract_type.value}_{len(clause.text)}_{clause.confidence:.2f}"
        cache_key = f"clause_risk:{clause_fingerprint}"

        # Check cache first
        cached_risks = await self.cache_service.get(cache_key)
        if cached_risks:
            logger.info(f"Retrieved clause risk assessment from cache")
            return [Risk(**risk) for risk in cached_risks]

        try:
            risks = []

            # Use LLM to analyze clause-specific risks
            context_info = {
                "clause_type": clause.clause_type.value,
                "contract_type": contract_type.value,
                "industry": industry_context or "general",
                "clause_length": len(clause.text),
                "obligations_count": len(clause.obligations),
                "rights_count": len(clause.rights)
            }

            prompt = f"""
            Analyze this {clause.clause_type.value} clause from a {contract_type.value} contract for potential risks.

            Clause text:
            {clause.text}

            Obligations: {clause.obligations}
            Rights: {clause.rights}
            Conditions: {clause.conditions}

            Identify and assess risks in this JSON format:
            {{
                "risks": [
                    {{
                        "category": "financial|operational|compliance|reputational|legal",
                        "severity": "critical|high|medium|low|minimal",
                        "title": "Short risk title",
                        "description": "Detailed risk description",
                        "confidence": 0.0-1.0,
                        "likelihood_estimate": 0.0-1.0,
                        "financial_impact_estimate": "low|medium|high|critical or dollar range",
                        "mitigation_suggestions": ["suggestion1", "suggestion2"],
                        "regulatory_implications": ["implication1", "implication2"]
                    }}
                ]
            }}

            Focus on risks that could materially impact the business. Consider:
            - Financial exposure and liability
            - Operational constraints or obligations
            - Compliance and regulatory issues
            - Reputational risks
            - Enforceability concerns
            """

            response = await self.claude_assistant.analyze_with_context(
                prompt=prompt,
                context=context_info
            )

            # Parse LLM response
            response_text = response.get('content', '').strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            risk_analysis = json.loads(response_text)

            for risk_data in risk_analysis.get('risks', []):
                risk = Risk(
                    risk_id=f"risk_{clause.clause_id}_{risk_data['category']}_{int(datetime.utcnow().timestamp())}",
                    category=RiskCategory(risk_data['category']),
                    severity=RiskSeverity(risk_data['severity']),
                    confidence=float(risk_data['confidence']),
                    title=risk_data['title'],
                    description=risk_data['description'],
                    affected_clauses=[clause.clause_id],
                    mitigation_suggestions=risk_data.get('mitigation_suggestions', []),
                    financial_impact_estimate=risk_data.get('financial_impact_estimate'),
                    likelihood_estimate=float(risk_data.get('likelihood_estimate', 0.5)),
                    regulatory_implications=risk_data.get('regulatory_implications', []),
                    metadata={
                        "analysis_method": "llm_clause_analysis",
                        "clause_type": clause.clause_type.value,
                        "contract_type": contract_type.value,
                        "industry_context": industry_context
                    }
                )
                risks.append(risk)

            # Cache results for 4 hours
            cached_data = [risk.__dict__ for risk in risks]
            await self.cache_service.set(cache_key, cached_data, ttl=14400)

            logger.info(f"Identified {len(risks)} risks for {clause.clause_type.value} clause")
            return risks

        except Exception as e:
            logger.error(f"Clause risk scoring failed: {e}")
            return []

    async def aggregate_document_risk(
        self,
        all_risks: List[Risk],
        red_flags: List[RedFlag],
        contract_analysis: ContractAnalysis
    ) -> Tuple[float, str]:
        """Calculate overall document risk score and level"""

        if not all_risks and not red_flags:
            return 0.1, "Low"

        # Calculate weighted risk score
        total_weighted_score = 0.0
        total_weight = 0.0

        # Weight risks by severity and confidence
        severity_weights = {
            RiskSeverity.CRITICAL: 5.0,
            RiskSeverity.HIGH: 4.0,
            RiskSeverity.MEDIUM: 3.0,
            RiskSeverity.LOW: 2.0,
            RiskSeverity.MINIMAL: 1.0
        }

        for risk in all_risks:
            weight = severity_weights.get(risk.severity, 3.0) * risk.confidence
            score = risk.get_risk_score()
            total_weighted_score += score * weight
            total_weight += weight

        # Add red flag impact
        red_flag_impact = 0.0
        for flag in red_flags:
            flag_weight = severity_weights.get(flag.severity, 3.0) * flag.confidence
            red_flag_impact += flag_weight * 0.2  # Red flags add 20% boost

        if total_weight > 0:
            base_score = total_weighted_score / total_weight
        else:
            base_score = 0.0

        # Apply red flag boost
        overall_score = min(1.0, base_score + red_flag_impact)

        # Determine risk level
        if overall_score >= 0.8:
            risk_level = "Critical"
        elif overall_score >= 0.6:
            risk_level = "High"
        elif overall_score >= 0.4:
            risk_level = "Medium"
        elif overall_score >= 0.2:
            risk_level = "Low"
        else:
            risk_level = "Minimal"

        return overall_score, risk_level

    async def compare_to_benchmark(
        self,
        contract_type: ContractType,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compare risk profile to industry benchmarks"""

        # This would integrate with industry risk databases
        # For now, return simulated benchmark comparison

        benchmarks = {
            ContractType.NDA: {
                "average_risk_score": 0.3,
                "common_risks": ["excessive_confidentiality", "broad_scope"],
                "typical_red_flags": 1.2
            },
            ContractType.SERVICE: {
                "average_risk_score": 0.5,
                "common_risks": ["liability_exposure", "performance_obligations"],
                "typical_red_flags": 2.1
            },
            ContractType.EMPLOYMENT: {
                "average_risk_score": 0.4,
                "common_risks": ["ip_assignment", "non_compete"],
                "typical_red_flags": 1.8
            }
        }

        return benchmarks.get(contract_type, {
            "average_risk_score": 0.4,
            "common_risks": ["standard_commercial_risks"],
            "typical_red_flags": 2.0
        })


class RiskExtractor:
    """
    Main orchestrator for contract risk analysis
    Coordinates red flag detection, risk scoring, and assessment generation
    """

    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or CacheService()
        self.red_flag_detector = RedFlagDetector()
        self.risk_scorer = RiskScorer(cache_service)
        self.claude_assistant = ClaudeAssistant(context_type="executive_risk_summary")

    async def extract_risks(
        self,
        parsed_doc: ParsedDocument,
        contract_analysis: ContractAnalysis,
        industry_context: Optional[str] = None
    ) -> RiskAssessment:
        """Perform comprehensive risk extraction and assessment"""

        logger.info(f"Starting risk extraction for {parsed_doc.document_id}")

        # Generate cache key
        assessment_key = f"risk_assessment:{parsed_doc.document_id}_{contract_analysis.contract_type.value}_{len(contract_analysis.clauses)}"

        # Check cache
        cached_assessment = await self.cache_service.get(assessment_key)
        if cached_assessment:
            logger.info(f"Retrieved risk assessment from cache")
            return RiskAssessment(**cached_assessment)

        start_time = datetime.utcnow()

        # Step 1: Detect red flags
        red_flags = await self.red_flag_detector.detect_red_flags(
            parsed_doc.text,
            contract_analysis
        )

        # Step 2: Score risks for each clause
        all_risks = []
        for clause in contract_analysis.clauses:
            clause_risks = await self.risk_scorer.score_clause_risk(
                clause,
                contract_analysis.contract_type,
                industry_context
            )
            all_risks.extend(clause_risks)

        # Step 3: Identify missing protections
        missing_protections = await self._identify_missing_protections(
            contract_analysis.clauses,
            contract_analysis.contract_type
        )

        # Step 4: Calculate overall risk score
        overall_score, risk_level = await self.risk_scorer.aggregate_document_risk(
            all_risks,
            red_flags,
            contract_analysis
        )

        # Step 5: Get industry benchmark comparison
        benchmark_comparison = await self.risk_scorer.compare_to_benchmark(
            contract_analysis.contract_type,
            industry_context
        )

        # Step 6: Generate executive summary and recommendations
        executive_summary = await self._generate_executive_summary(
            contract_analysis,
            all_risks,
            red_flags,
            overall_score,
            risk_level
        )

        # Step 7: Extract key concerns and recommendations
        key_concerns = self._extract_key_concerns(all_risks, red_flags)
        recommendations = await self._generate_recommendations(all_risks, red_flags, missing_protections)

        # Step 8: Calculate risk distribution
        risk_distribution = self._calculate_risk_distribution(all_risks)

        # Create assessment
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        assessment = RiskAssessment(
            document_id=parsed_doc.document_id,
            contract_type=contract_analysis.contract_type,
            overall_risk_score=overall_score,
            risk_level=risk_level,
            risks=all_risks,
            red_flags=red_flags,
            missing_protections=missing_protections,
            industry_benchmark_comparison=benchmark_comparison,
            executive_summary=executive_summary,
            key_concerns=key_concerns,
            recommended_actions=recommendations,
            risk_distribution=risk_distribution,
            assessment_metadata={
                "total_risks_identified": len(all_risks),
                "red_flags_count": len(red_flags),
                "analysis_duration_ms": duration_ms,
                "industry_context": industry_context,
                "confidence_distribution": self._calculate_confidence_distribution(all_risks)
            }
        )

        # Cache assessment for 6 hours
        await self.cache_service.set(assessment_key, assessment.__dict__, ttl=21600)

        logger.info(
            f"Risk extraction completed for {parsed_doc.document_id}: "
            f"{risk_level} risk level with {len(all_risks)} risks, {len(red_flags)} red flags"
        )

        return assessment

    async def _identify_missing_protections(
        self,
        clauses: List[LegalClause],
        contract_type: ContractType
    ) -> List[str]:
        """Identify missing protective clauses"""

        present_clause_types = {clause.clause_type for clause in clauses}

        # Expected protections by contract type
        expected_protections = {
            ContractType.SERVICE: [
                ClauseType.LIABILITY,
                ClauseType.INDEMNITY,
                ClauseType.FORCE_MAJEURE,
                ClauseType.TERMINATION
            ],
            ContractType.NDA: [
                ClauseType.TERMINATION,
                ClauseType.SEVERABILITY
            ],
            ContractType.EMPLOYMENT: [
                ClauseType.TERMINATION,
                ClauseType.CONFIDENTIALITY
            ]
        }

        expected = expected_protections.get(contract_type, [])
        missing = []

        for expected_clause in expected:
            if expected_clause not in present_clause_types:
                missing.append(f"Missing {expected_clause.value} clause")

        # Check for specific protective language
        contract_text = " ".join(clause.text for clause in clauses).lower()

        if "limitation of liability" not in contract_text:
            missing.append("Missing liability limitation provisions")

        if "force majeure" not in contract_text:
            missing.append("Missing force majeure protection")

        return missing

    async def _generate_executive_summary(
        self,
        contract_analysis: ContractAnalysis,
        risks: List[Risk],
        red_flags: List[RedFlag],
        overall_score: float,
        risk_level: str
    ) -> str:
        """Generate executive summary of risks"""

        try:
            context_info = {
                "contract_type": contract_analysis.contract_type.value,
                "overall_risk_score": overall_score,
                "risk_level": risk_level,
                "total_risks": len(risks),
                "red_flags_count": len(red_flags),
                "critical_risks": len([r for r in risks if r.severity == RiskSeverity.CRITICAL]),
                "high_risks": len([r for r in risks if r.severity == RiskSeverity.HIGH])
            }

            # Get top 3 risks for summary
            top_risks = sorted(risks, key=lambda r: r.get_risk_score(), reverse=True)[:3]
            top_risk_descriptions = [f"{r.category.value}: {r.title}" for r in top_risks]

            prompt = f"""
            Generate a concise executive summary for this contract risk assessment.

            Contract: {contract_analysis.contract_type.value}
            Risk Level: {risk_level} (Score: {overall_score:.2f})
            Total Risks: {len(risks)}
            Red Flags: {len(red_flags)}

            Top Risks:
            {chr(10).join(top_risk_descriptions)}

            Red Flags Present: {len(red_flags) > 0}

            Write a 2-3 paragraph executive summary that:
            1. States the overall risk assessment
            2. Highlights the most critical concerns
            3. Provides clear actionable guidance

            Keep it executive-level (non-technical) and focused on business impact.
            """

            response = await self.claude_assistant.analyze_with_context(
                prompt=prompt,
                context=context_info
            )

            return response.get('content', 'Risk assessment completed.')

        except Exception as e:
            logger.error(f"Executive summary generation failed: {e}")
            return f"Risk assessment completed for {contract_analysis.contract_type.value} contract with {risk_level.lower()} risk level."

    def _extract_key_concerns(self, risks: List[Risk], red_flags: List[RedFlag]) -> List[str]:
        """Extract top key concerns from risks and red flags"""

        concerns = []

        # Add critical and high risks
        high_priority_risks = [r for r in risks if r.severity in [RiskSeverity.CRITICAL, RiskSeverity.HIGH]]
        for risk in sorted(high_priority_risks, key=lambda r: r.get_risk_score(), reverse=True)[:5]:
            concerns.append(f"{risk.category.value.title()} Risk: {risk.title}")

        # Add high-priority red flags
        priority_flags = [f for f in red_flags if f.mitigation_priority <= 2]
        for flag in priority_flags:
            concerns.append(f"Red Flag: {flag.description}")

        return concerns[:10]  # Top 10 concerns

    async def _generate_recommendations(
        self,
        risks: List[Risk],
        red_flags: List[RedFlag],
        missing_protections: List[str]
    ) -> List[str]:
        """Generate actionable recommendations"""

        recommendations = []

        # Recommendations from risks
        for risk in sorted(risks, key=lambda r: r.get_risk_score(), reverse=True)[:5]:
            if risk.mitigation_suggestions:
                recommendations.extend(risk.mitigation_suggestions[:2])  # Top 2 suggestions per risk

        # Recommendations from red flags
        red_flag_recommendations = {
            RedFlagType.UNLIMITED_LIABILITY: "Add liability limitation clause to cap financial exposure",
            RedFlagType.AUTO_RENEWAL: "Require explicit consent for contract renewals",
            RedFlagType.UNUSUAL_INDEMNITY: "Limit indemnification scope to standard business risks",
            RedFlagType.ONEROUS_PENALTIES: "Negotiate reasonable penalty amounts or liquidated damages caps"
        }

        for flag in red_flags:
            if flag.flag_type in red_flag_recommendations:
                recommendations.append(red_flag_recommendations[flag.flag_type])

        # Recommendations for missing protections
        for protection in missing_protections[:3]:  # Top 3 missing protections
            if "liability" in protection.lower():
                recommendations.append("Add comprehensive liability limitation clause")
            elif "termination" in protection.lower():
                recommendations.append("Include clear termination provisions and notice requirements")
            elif "force majeure" in protection.lower():
                recommendations.append("Add force majeure clause to protect against unforeseeable events")

        # Deduplicate and prioritize
        unique_recommendations = list(dict.fromkeys(recommendations))  # Preserve order while removing duplicates
        return unique_recommendations[:10]  # Top 10 recommendations

    def _calculate_risk_distribution(self, risks: List[Risk]) -> Dict[RiskCategory, int]:
        """Calculate distribution of risks by category"""

        distribution = {category: 0 for category in RiskCategory}
        for risk in risks:
            distribution[risk.category] += 1

        return distribution

    def _calculate_confidence_distribution(self, risks: List[Risk]) -> Dict[str, int]:
        """Calculate distribution of confidence scores"""

        buckets = {"high": 0, "medium": 0, "low": 0}
        for risk in risks:
            if risk.confidence >= 0.8:
                buckets["high"] += 1
            elif risk.confidence >= 0.5:
                buckets["medium"] += 1
            else:
                buckets["low"] += 1

        return buckets

    async def generate_risk_comparison_report(
        self,
        assessments: List[RiskAssessment]
    ) -> Dict[str, Any]:
        """Generate comparative risk analysis across multiple contracts"""

        if not assessments:
            return {"error": "No assessments provided"}

        report = {
            "total_contracts": len(assessments),
            "average_risk_score": sum(a.overall_risk_score for a in assessments) / len(assessments),
            "risk_level_distribution": Counter(a.risk_level for a in assessments),
            "common_risk_categories": {},
            "red_flag_patterns": {},
            "recommendations": [],
            "generated_at": datetime.utcnow().isoformat()
        }

        # Analyze common risk categories
        all_risks = []
        for assessment in assessments:
            all_risks.extend(assessment.risks)

        risk_categories = Counter(risk.category for risk in all_risks)
        report["common_risk_categories"] = dict(risk_categories.most_common())

        # Analyze red flag patterns
        all_red_flags = []
        for assessment in assessments:
            all_red_flags.extend(assessment.red_flags)

        red_flag_types = Counter(flag.flag_type for flag in all_red_flags)
        report["red_flag_patterns"] = dict(red_flag_types.most_common())

        # Generate portfolio-level recommendations
        if risk_categories.most_common(1):
            top_risk_category = risk_categories.most_common(1)[0][0]
            report["recommendations"].append(
                f"Focus on {top_risk_category.value} risk management across contract portfolio"
            )

        if red_flag_types.most_common(1):
            top_red_flag = red_flag_types.most_common(1)[0][0]
            report["recommendations"].append(
                f"Address recurring {top_red_flag.value} issues in contract templates"
            )

        logger.info(f"Generated risk comparison report for {len(assessments)} contracts")
        return report