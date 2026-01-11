"""
Claude Multi-Modal Intelligence Engine - Phase 2 Enhancement

Advanced document and image analysis capabilities using Claude's vision features
for comprehensive real estate document processing and intelligence.

Features:
- Property document analysis (MLS listings, inspections, reports)
- Financial document processing (pre-approvals, income verification)
- Legal document review (contracts, disclosures, agreements)
- Real-time document coaching and insights
- Automated data extraction and CRM integration
"""

import asyncio
import base64
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import hashlib
from pathlib import Path
import mimetypes

from anthropic import AsyncAnthropic
import redis.asyncio as redis
from PIL import Image
import io

from ..ghl_utils.config import settings
from .websocket_manager import get_websocket_manager, IntelligenceEventType

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Types of real estate documents that can be analyzed."""
    MLS_LISTING = "mls_listing"
    PROPERTY_REPORT = "property_report"
    INSPECTION_REPORT = "inspection_report"
    APPRAISAL = "appraisal"
    FINANCIAL_PREAPPROVAL = "financial_preapproval"
    INCOME_VERIFICATION = "income_verification"
    BANK_STATEMENT = "bank_statement"
    PURCHASE_CONTRACT = "purchase_contract"
    LISTING_AGREEMENT = "listing_agreement"
    DISCLOSURE_FORM = "disclosure_form"
    INSURANCE_DOCUMENT = "insurance_document"
    TITLE_DOCUMENT = "title_document"
    FLOOR_PLAN = "floor_plan"
    PROPERTY_PHOTO = "property_photo"
    UNKNOWN = "unknown"


class AnalysisComplexity(Enum):
    """Analysis complexity levels for processing optimization."""
    QUICK_SCAN = "quick_scan"          # 5-10 seconds
    STANDARD_ANALYSIS = "standard_analysis"  # 15-30 seconds
    DEEP_ANALYSIS = "deep_analysis"    # 30-60 seconds
    COMPREHENSIVE_REVIEW = "comprehensive_review"  # 60+ seconds


class DocumentProcessingStatus(Enum):
    """Document processing status states."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"


@dataclass
class DocumentMetadata:
    """Metadata for uploaded document."""
    document_id: str
    original_filename: str
    file_size: int
    mime_type: str
    upload_timestamp: datetime
    uploaded_by: str
    document_type: DocumentType
    confidence_score: float
    processing_status: DocumentProcessingStatus


@dataclass
class DocumentAnalysisResult:
    """Result of document analysis."""
    document_id: str
    document_type: DocumentType
    analysis_summary: str
    key_insights: List[str]
    extracted_data: Dict[str, Any]
    risk_flags: List[str]
    opportunities: List[str]
    coaching_suggestions: List[str]
    compliance_notes: List[str]
    confidence_score: float
    processing_time_ms: float
    analysis_timestamp: datetime
    requires_human_review: bool = False


@dataclass
class PropertyDocumentInsights:
    """Specific insights for property-related documents."""
    property_address: Optional[str]
    listing_price: Optional[float]
    property_type: Optional[str]
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    square_footage: Optional[int]
    lot_size: Optional[str]
    year_built: Optional[int]
    key_features: List[str]
    condition_notes: List[str]
    market_analysis: Dict[str, Any]
    investment_potential: Optional[str]


@dataclass
class FinancialDocumentInsights:
    """Specific insights for financial documents."""
    income_amount: Optional[float]
    credit_score: Optional[int]
    debt_to_income_ratio: Optional[float]
    employment_status: Optional[str]
    pre_approval_amount: Optional[float]
    down_payment_amount: Optional[float]
    loan_type: Optional[str]
    financial_strength: str  # "strong", "moderate", "weak"
    risk_factors: List[str]
    qualification_notes: List[str]


@dataclass
class LegalDocumentInsights:
    """Specific insights for legal documents."""
    contract_type: Optional[str]
    parties_involved: List[str]
    key_terms: Dict[str, Any]
    contingencies: List[str]
    deadlines: List[Dict[str, Any]]
    risks_identified: List[str]
    compliance_requirements: List[str]
    recommended_actions: List[str]


class ClaudeMultiModalIntelligence:
    """
    Advanced multi-modal intelligence engine using Claude's vision capabilities.

    Provides comprehensive document analysis, real-time insights, and automated
    data extraction for real estate transactions and lead management.
    """

    def __init__(self):
        self.claude_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.websocket_manager = get_websocket_manager()
        self.redis_client = None

        # Document type classification prompts
        self.classification_prompts = self._initialize_classification_prompts()

        # Analysis templates for different document types
        self.analysis_templates = self._initialize_analysis_templates()

        # Initialize Redis for caching and session management
        self._init_redis()

    async def _init_redis(self):
        """Initialize Redis connection for caching."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Multi-modal intelligence Redis connection established")
        except Exception as e:
            logger.warning(f"Redis unavailable for multi-modal intelligence: {e}")
            self.redis_client = None

    def _initialize_classification_prompts(self) -> Dict[DocumentType, str]:
        """Initialize document type classification prompts."""
        return {
            DocumentType.MLS_LISTING: "This document contains property listing information with photos, price, features, and market details",
            DocumentType.PROPERTY_REPORT: "This document contains comprehensive property analysis including condition, valuation, and recommendations",
            DocumentType.INSPECTION_REPORT: "This document contains property inspection findings with condition assessments and repair recommendations",
            DocumentType.FINANCIAL_PREAPPROVAL: "This document contains loan pre-approval information including approved amount and terms",
            DocumentType.PURCHASE_CONTRACT: "This document contains purchase agreement terms including price, contingencies, and closing details",
            # Add more classifications as needed
        }

    def _initialize_analysis_templates(self) -> Dict[DocumentType, str]:
        """Initialize analysis templates for different document types."""
        return {
            DocumentType.MLS_LISTING: """
            Analyze this MLS listing and provide:
            1. Property summary with key details (address, price, features)
            2. Market positioning analysis (pricing competitiveness, unique selling points)
            3. Investment potential assessment
            4. Buyer appeal factors
            5. Potential concerns or risks
            6. Negotiation insights and strategies
            """,

            DocumentType.FINANCIAL_PREAPPROVAL: """
            Analyze this financial pre-approval document and provide:
            1. Buyer financial strength assessment
            2. Loan terms and conditions analysis
            3. Purchase power evaluation
            4. Risk factors identification
            5. Qualification completeness check
            6. Recommendations for next steps
            """,

            DocumentType.PURCHASE_CONTRACT: """
            Analyze this purchase contract and provide:
            1. Key contract terms summary
            2. Contingency analysis and timeline
            3. Risk assessment for all parties
            4. Compliance requirements check
            5. Deadline tracking and critical dates
            6. Negotiation opportunities and concerns
            """,

            DocumentType.INSPECTION_REPORT: """
            Analyze this property inspection report and provide:
            1. Overall property condition assessment
            2. Critical issues requiring immediate attention
            3. Maintenance and repair cost estimates
            4. Safety and code compliance concerns
            5. Impact on property value and marketability
            6. Negotiation strategies based on findings
            """
        }

    async def analyze_document(
        self,
        document_data: Union[str, bytes],
        document_type: Optional[DocumentType] = None,
        analysis_complexity: AnalysisComplexity = AnalysisComplexity.STANDARD_ANALYSIS,
        agent_id: Optional[str] = None,
        lead_context: Optional[Dict[str, Any]] = None
    ) -> DocumentAnalysisResult:
        """
        Analyze a document using Claude's vision capabilities.

        Args:
            document_data: Base64 encoded image data or file path
            document_type: Type of document (auto-detected if None)
            analysis_complexity: Level of analysis detail required
            agent_id: Agent requesting analysis
            lead_context: Additional context about the lead/transaction

        Returns:
            Comprehensive document analysis results
        """
        start_time = datetime.now()

        try:
            # Generate document ID
            document_id = self._generate_document_id(document_data)

            # Check cache for recent analysis
            cached_result = await self._get_cached_analysis(document_id)
            if cached_result:
                return cached_result

            # Classify document type if not provided
            if document_type is None:
                document_type = await self._classify_document_type(document_data)

            # Prepare image data for Claude
            image_data = await self._prepare_image_data(document_data)

            # Generate analysis prompt based on document type
            analysis_prompt = self._generate_analysis_prompt(
                document_type, analysis_complexity, lead_context
            )

            # Call Claude API with vision
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # Vision-capable model
                max_tokens=1500 if analysis_complexity == AnalysisComplexity.COMPREHENSIVE_REVIEW else 1000,
                temperature=0.3,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": analysis_prompt
                        }
                    ]
                }]
            )

            # Parse Claude's analysis
            analysis_text = response.content[0].text
            analysis_result = await self._parse_document_analysis(
                document_id, document_type, analysis_text, start_time
            )

            # Cache successful analysis
            await self._cache_analysis_result(document_id, analysis_result)

            # Broadcast analysis completion
            if agent_id:
                await self._broadcast_analysis_completion(agent_id, analysis_result)

            logger.info(f"Document analysis completed for {document_id} in {analysis_result.processing_time_ms}ms")
            return analysis_result

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Error analyzing document: {e}")

            return DocumentAnalysisResult(
                document_id=document_id if 'document_id' in locals() else "error",
                document_type=document_type or DocumentType.UNKNOWN,
                analysis_summary=f"Analysis failed: {str(e)}",
                key_insights=["Error occurred during document analysis"],
                extracted_data={},
                risk_flags=["Analysis failure"],
                opportunities=[],
                coaching_suggestions=["Manual review required"],
                compliance_notes=["Unable to verify compliance due to analysis error"],
                confidence_score=0.0,
                processing_time_ms=processing_time,
                analysis_timestamp=datetime.now(),
                requires_human_review=True
            )

    async def _classify_document_type(self, document_data: Union[str, bytes]) -> DocumentType:
        """Classify document type using Claude's vision capabilities."""
        try:
            image_data = await self._prepare_image_data(document_data)

            classification_prompt = """
            Analyze this document image and classify it as one of the following real estate document types:

            1. MLS_LISTING - Property listing with photos and details
            2. PROPERTY_REPORT - Comprehensive property analysis report
            3. INSPECTION_REPORT - Property inspection findings
            4. APPRAISAL - Property valuation document
            5. FINANCIAL_PREAPPROVAL - Loan pre-approval letter
            6. INCOME_VERIFICATION - Income/employment verification
            7. BANK_STATEMENT - Financial account statement
            8. PURCHASE_CONTRACT - Purchase agreement or contract
            9. LISTING_AGREEMENT - Property listing contract
            10. DISCLOSURE_FORM - Property disclosure document
            11. INSURANCE_DOCUMENT - Insurance policy or claim
            12. TITLE_DOCUMENT - Title report or deed
            13. FLOOR_PLAN - Property layout diagram
            14. PROPERTY_PHOTO - Property photograph
            15. UNKNOWN - Cannot determine type

            Respond with only the classification name and a confidence score (0-100%).
            Format: DOCUMENT_TYPE: confidence%
            """

            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=50,
                temperature=0.1,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": classification_prompt
                        }
                    ]
                }]
            )

            classification_text = response.content[0].text.strip()

            # Parse classification result
            if ":" in classification_text:
                doc_type_str = classification_text.split(":")[0].strip()
                try:
                    return DocumentType(doc_type_str.lower())
                except ValueError:
                    return DocumentType.UNKNOWN

            return DocumentType.UNKNOWN

        except Exception as e:
            logger.warning(f"Error classifying document type: {e}")
            return DocumentType.UNKNOWN

    async def _prepare_image_data(self, document_data: Union[str, bytes]) -> str:
        """Prepare image data for Claude API."""
        try:
            if isinstance(document_data, str):
                # Assume it's base64 encoded
                if document_data.startswith('data:'):
                    # Remove data URL prefix
                    document_data = document_data.split(',')[1]
                return document_data

            elif isinstance(document_data, bytes):
                # Convert bytes to base64
                return base64.b64encode(document_data).decode('utf-8')

            else:
                raise ValueError(f"Unsupported document data type: {type(document_data)}")

        except Exception as e:
            logger.error(f"Error preparing image data: {e}")
            raise

    def _generate_analysis_prompt(
        self,
        document_type: DocumentType,
        analysis_complexity: AnalysisComplexity,
        lead_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate analysis prompt based on document type and complexity."""

        base_template = self.analysis_templates.get(
            document_type,
            "Analyze this document and provide key insights relevant to real estate transactions."
        )

        # Add complexity-specific instructions
        if analysis_complexity == AnalysisComplexity.QUICK_SCAN:
            complexity_instruction = "Provide a brief summary focusing on the most critical points only."
        elif analysis_complexity == AnalysisComplexity.COMPREHENSIVE_REVIEW:
            complexity_instruction = "Provide an extremely detailed analysis covering all aspects, potential issues, and strategic recommendations."
        else:
            complexity_instruction = "Provide a balanced analysis covering key points and actionable insights."

        # Add lead context if available
        context_instruction = ""
        if lead_context:
            context_instruction = f"\n\nLead Context: {json.dumps(lead_context, indent=2)}\nConsider this context when providing insights and recommendations."

        # Combine all elements
        full_prompt = f"""
        You are an expert real estate analyst with deep knowledge of property transactions, financing, and market dynamics.

        Document Type: {document_type.value.replace('_', ' ').title()}

        {base_template}

        Analysis Level: {complexity_instruction}

        Please structure your response with the following sections:
        1. **Executive Summary**: Brief overview of document contents
        2. **Key Insights**: Most important findings (3-5 bullet points)
        3. **Risk Factors**: Potential concerns or issues identified
        4. **Opportunities**: Positive aspects or advantages identified
        5. **Coaching Suggestions**: Recommendations for real estate agents
        6. **Compliance Notes**: Regulatory or legal considerations
        7. **Next Steps**: Recommended actions based on analysis

        Provide specific, actionable insights that will help real estate professionals make informed decisions.
        {context_instruction}
        """

        return full_prompt

    async def _parse_document_analysis(
        self,
        document_id: str,
        document_type: DocumentType,
        analysis_text: str,
        start_time: datetime
    ) -> DocumentAnalysisResult:
        """Parse Claude's document analysis into structured format."""

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        try:
            # Extract sections from Claude's response
            sections = self._extract_analysis_sections(analysis_text)

            # Extract specific data based on document type
            extracted_data = await self._extract_structured_data(document_type, analysis_text)

            # Determine if human review is required
            requires_review = self._assess_review_requirement(sections)

            # Calculate confidence score based on analysis quality
            confidence_score = self._calculate_confidence_score(sections, analysis_text)

            return DocumentAnalysisResult(
                document_id=document_id,
                document_type=document_type,
                analysis_summary=sections.get("executive_summary", analysis_text[:200] + "..."),
                key_insights=sections.get("key_insights", []),
                extracted_data=extracted_data,
                risk_flags=sections.get("risk_factors", []),
                opportunities=sections.get("opportunities", []),
                coaching_suggestions=sections.get("coaching_suggestions", []),
                compliance_notes=sections.get("compliance_notes", []),
                confidence_score=confidence_score,
                processing_time_ms=processing_time,
                analysis_timestamp=datetime.now(),
                requires_human_review=requires_review
            )

        except Exception as e:
            logger.warning(f"Error parsing document analysis: {e}")
            return DocumentAnalysisResult(
                document_id=document_id,
                document_type=document_type,
                analysis_summary=analysis_text[:200] + "..." if len(analysis_text) > 200 else analysis_text,
                key_insights=["Analysis completed - see summary for details"],
                extracted_data={},
                risk_flags=["Parsing error - manual review recommended"],
                opportunities=[],
                coaching_suggestions=["Review analysis manually for specific recommendations"],
                compliance_notes=["Unable to extract compliance notes"],
                confidence_score=0.5,
                processing_time_ms=processing_time,
                analysis_timestamp=datetime.now(),
                requires_human_review=True
            )

    def _extract_analysis_sections(self, analysis_text: str) -> Dict[str, List[str]]:
        """Extract structured sections from Claude's analysis."""
        sections = {
            "executive_summary": "",
            "key_insights": [],
            "risk_factors": [],
            "opportunities": [],
            "coaching_suggestions": [],
            "compliance_notes": [],
            "next_steps": []
        }

        current_section = None
        lines = analysis_text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect section headers
            line_lower = line.lower()
            if "executive summary" in line_lower or "summary" in line_lower:
                current_section = "executive_summary"
                continue
            elif "key insights" in line_lower or "insights" in line_lower:
                current_section = "key_insights"
                continue
            elif "risk factors" in line_lower or "risks" in line_lower:
                current_section = "risk_factors"
                continue
            elif "opportunities" in line_lower:
                current_section = "opportunities"
                continue
            elif "coaching" in line_lower:
                current_section = "coaching_suggestions"
                continue
            elif "compliance" in line_lower:
                current_section = "compliance_notes"
                continue
            elif "next steps" in line_lower:
                current_section = "next_steps"
                continue

            # Extract content based on current section
            if current_section == "executive_summary":
                if not line.startswith('**') and not line.startswith('#'):
                    sections["executive_summary"] += line + " "
            elif current_section and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                content = line.lstrip('-•* ').strip()
                if content:
                    sections[current_section].append(content)

        return sections

    async def _extract_structured_data(self, document_type: DocumentType, analysis_text: str) -> Dict[str, Any]:
        """Extract structured data based on document type."""
        extracted_data = {}

        try:
            # Property-specific data extraction
            if document_type in [DocumentType.MLS_LISTING, DocumentType.PROPERTY_REPORT]:
                extracted_data.update(self._extract_property_data(analysis_text))

            # Financial document data extraction
            elif document_type in [DocumentType.FINANCIAL_PREAPPROVAL, DocumentType.INCOME_VERIFICATION]:
                extracted_data.update(self._extract_financial_data(analysis_text))

            # Contract data extraction
            elif document_type == DocumentType.PURCHASE_CONTRACT:
                extracted_data.update(self._extract_contract_data(analysis_text))

        except Exception as e:
            logger.warning(f"Error extracting structured data: {e}")

        return extracted_data

    def _extract_property_data(self, analysis_text: str) -> Dict[str, Any]:
        """Extract property-specific data from analysis."""
        import re

        property_data = {}
        text_lower = analysis_text.lower()

        # Extract price
        price_patterns = [
            r'\$[\d,]+',
            r'price[:\s]+\$?[\d,]+',
            r'listed[:\s]+\$?[\d,]+'
        ]
        for pattern in price_patterns:
            match = re.search(pattern, text_lower)
            if match:
                price_str = match.group().replace('$', '').replace(',', '')
                try:
                    property_data['listing_price'] = float(price_str)
                    break
                except ValueError:
                    continue

        # Extract bedroom/bathroom counts
        bed_match = re.search(r'(\d+)[:\s]*bed', text_lower)
        if bed_match:
            property_data['bedrooms'] = int(bed_match.group(1))

        bath_match = re.search(r'(\d+(?:\.\d+)?)[:\s]*bath', text_lower)
        if bath_match:
            property_data['bathrooms'] = float(bath_match.group(1))

        # Extract square footage
        sqft_patterns = [
            r'(\d{1,4}(?:,\d{3})*)[:\s]*sq\.?\s*ft',
            r'(\d{1,4}(?:,\d{3})*)[:\s]*square\s*feet'
        ]
        for pattern in sqft_patterns:
            match = re.search(pattern, text_lower)
            if match:
                sqft_str = match.group(1).replace(',', '')
                try:
                    property_data['square_footage'] = int(sqft_str)
                    break
                except ValueError:
                    continue

        return property_data

    def _extract_financial_data(self, analysis_text: str) -> Dict[str, Any]:
        """Extract financial-specific data from analysis."""
        import re

        financial_data = {}
        text_lower = analysis_text.lower()

        # Extract income
        income_patterns = [
            r'income[:\s]+\$?[\d,]+',
            r'annual[:\s]+\$?[\d,]+',
            r'salary[:\s]+\$?[\d,]+'
        ]
        for pattern in income_patterns:
            match = re.search(pattern, text_lower)
            if match:
                amount_str = re.search(r'[\d,]+', match.group()).group().replace(',', '')
                try:
                    financial_data['income_amount'] = float(amount_str)
                    break
                except ValueError:
                    continue

        # Extract credit score
        credit_match = re.search(r'credit[:\s]*score[:\s]*(\d+)', text_lower)
        if credit_match:
            financial_data['credit_score'] = int(credit_match.group(1))

        # Extract pre-approval amount
        preapproval_patterns = [
            r'pre.?approval[:\s]+\$?[\d,]+',
            r'approved[:\s]*for[:\s]+\$?[\d,]+'
        ]
        for pattern in preapproval_patterns:
            match = re.search(pattern, text_lower)
            if match:
                amount_str = re.search(r'[\d,]+', match.group()).group().replace(',', '')
                try:
                    financial_data['pre_approval_amount'] = float(amount_str)
                    break
                except ValueError:
                    continue

        return financial_data

    def _extract_contract_data(self, analysis_text: str) -> Dict[str, Any]:
        """Extract contract-specific data from analysis."""
        contract_data = {}

        # This would include more sophisticated contract parsing
        # For now, basic pattern matching
        if 'contingency' in analysis_text.lower():
            contract_data['has_contingencies'] = True

        if 'closing' in analysis_text.lower():
            contract_data['mentions_closing'] = True

        return contract_data

    def _assess_review_requirement(self, sections: Dict[str, List[str]]) -> bool:
        """Assess if human review is required based on analysis content."""
        risk_factors = sections.get("risk_factors", [])
        compliance_notes = sections.get("compliance_notes", [])

        # Require review if significant risks identified
        high_risk_keywords = ['legal', 'compliance', 'violation', 'concern', 'error', 'missing', 'invalid']

        for risk in risk_factors:
            if any(keyword in risk.lower() for keyword in high_risk_keywords):
                return True

        for note in compliance_notes:
            if any(keyword in note.lower() for keyword in high_risk_keywords):
                return True

        return False

    def _calculate_confidence_score(self, sections: Dict[str, List[str]], analysis_text: str) -> float:
        """Calculate confidence score based on analysis quality."""
        score = 0.5  # Base score

        # Increase score for comprehensive sections
        if sections.get("key_insights"):
            score += 0.15
        if sections.get("coaching_suggestions"):
            score += 0.15
        if sections.get("executive_summary"):
            score += 0.1

        # Increase score for detailed analysis
        if len(analysis_text) > 500:
            score += 0.1

        return min(score, 0.95)  # Cap at 95%

    def _generate_document_id(self, document_data: Union[str, bytes]) -> str:
        """Generate unique document ID based on content hash."""
        if isinstance(document_data, str):
            content_bytes = document_data.encode('utf-8')
        else:
            content_bytes = document_data

        hash_obj = hashlib.sha256(content_bytes)
        return f"doc_{hash_obj.hexdigest()[:12]}_{int(datetime.now().timestamp())}"

    async def _get_cached_analysis(self, document_id: str) -> Optional[DocumentAnalysisResult]:
        """Get cached analysis result if available."""
        if not self.redis_client:
            return None

        try:
            cached_data = await self.redis_client.get(f"doc_analysis:{document_id}")
            if cached_data:
                data = json.loads(cached_data)
                return DocumentAnalysisResult(**data)
        except Exception as e:
            logger.warning(f"Error retrieving cached analysis: {e}")

        return None

    async def _cache_analysis_result(self, document_id: str, result: DocumentAnalysisResult, ttl_seconds: int = 3600):
        """Cache analysis result for future use."""
        if not self.redis_client:
            return

        try:
            result_data = asdict(result)
            # Convert datetime objects to strings
            result_data['analysis_timestamp'] = result_data['analysis_timestamp'].isoformat()

            await self.redis_client.setex(
                f"doc_analysis:{document_id}",
                ttl_seconds,
                json.dumps(result_data, default=str)
            )
        except Exception as e:
            logger.warning(f"Error caching analysis result: {e}")

    async def _broadcast_analysis_completion(self, agent_id: str, result: DocumentAnalysisResult):
        """Broadcast analysis completion to WebSocket clients."""
        try:
            await self.websocket_manager.broadcast_intelligence_update(
                IntelligenceEventType.DOCUMENT_ANALYSIS,
                {
                    "type": "document_analysis_complete",
                    "agent_id": agent_id,
                    "document_id": result.document_id,
                    "document_type": result.document_type.value,
                    "analysis_summary": result.analysis_summary,
                    "key_insights": result.key_insights[:3],  # Top 3 insights
                    "confidence_score": result.confidence_score,
                    "processing_time_ms": result.processing_time_ms,
                    "requires_review": result.requires_human_review,
                    "timestamp": result.analysis_timestamp.isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast analysis completion: {e}")

    # Additional methods for batch processing, document comparison, etc.

    async def batch_analyze_documents(
        self,
        documents: List[Dict[str, Any]],
        agent_id: str
    ) -> List[DocumentAnalysisResult]:
        """Analyze multiple documents in batch."""
        results = []

        for doc in documents:
            try:
                result = await self.analyze_document(
                    document_data=doc['data'],
                    document_type=doc.get('type'),
                    analysis_complexity=doc.get('complexity', AnalysisComplexity.STANDARD_ANALYSIS),
                    agent_id=agent_id,
                    lead_context=doc.get('context')
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error in batch analysis: {e}")
                # Continue with other documents

        return results

    async def compare_documents(
        self,
        document_1_id: str,
        document_2_id: str,
        comparison_focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compare two analyzed documents."""
        # Implementation for document comparison
        # This would retrieve cached analyses and perform comparison
        pass

    async def get_document_insights_summary(
        self,
        document_ids: List[str],
        summary_type: str = "transaction"
    ) -> Dict[str, Any]:
        """Generate insights summary across multiple documents."""
        # Implementation for multi-document insights
        pass


# Global instance
claude_multimodal_intelligence = ClaudeMultiModalIntelligence()


async def get_multimodal_intelligence() -> ClaudeMultiModalIntelligence:
    """Get global multi-modal intelligence service."""
    return claude_multimodal_intelligence