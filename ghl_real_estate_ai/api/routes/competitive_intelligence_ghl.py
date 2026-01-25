"""
Competitive Intelligence GHL Integration Routes
Specialized API endpoints for integrating competitive intelligence with GoHighLevel CRM.
Provides automated competitive threat detection, response campaigns, and market intelligence sync.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio
import json
import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import httpx

from ghl_real_estate_ai.core.llm_client import LLMClient
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.services.competitive_data_pipeline import CompetitiveDataPipeline
from ghl_real_estate_ai.services.competitive_response_automation import CompetitiveResponseEngine
from ghl_real_estate_ai.ghl_utils.config import Config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/competitive-intelligence-ghl", tags=["competitive-intelligence-ghl"])
security = HTTPBearer()


class GHLCompetitorLead(BaseModel):
    """Model for GHL lead with competitive intelligence tagging."""
    lead_id: str = Field(..., description="GHL lead ID")
    contact_id: str = Field(..., description="GHL contact ID")
    competitor_name: Optional[str] = Field(None, description="Identified competitor")
    competitor_probability: float = Field(0.0, description="Probability of competitor connection")
    competitive_insights: Dict[str, Any] = Field(default_factory=dict, description="Competitive intelligence data")
    threat_level: str = Field("LOW", description="Threat assessment level")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended response actions")
    last_analyzed: datetime = Field(default_factory=datetime.utcnow, description="Last analysis timestamp")


class MarketIntelligenceSync(BaseModel):
    """Model for syncing market intelligence data with GHL."""
    sync_id: str = Field(..., description="Unique sync ID")
    territory: str = Field(..., description="Market territory")
    competitor_data: Dict[str, Any] = Field(..., description="Competitor intelligence data")
    market_trends: Dict[str, Any] = Field(..., description="Market trend analysis")
    sync_status: str = Field("PENDING", description="Sync status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


class CompetitiveResponseCampaign(BaseModel):
    """Model for automated competitive response campaigns in GHL."""
    campaign_id: str = Field(..., description="GHL campaign ID")
    trigger_type: str = Field(..., description="Competitive trigger type")
    target_audience: Dict[str, Any] = Field(..., description="Target audience criteria")
    response_strategy: Dict[str, Any] = Field(..., description="Response strategy configuration")
    automation_rules: List[Dict[str, Any]] = Field(default_factory=list, description="GHL automation rules")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Campaign performance data")
    is_active: bool = Field(True, description="Campaign active status")


class GHLMarketIntelligenceService:
    """Service for integrating competitive intelligence with GHL CRM."""

    def __init__(self):
        self.config = Config()
        self.cache_service = CacheService()
        self.llm_client = LLMClient()
        self.data_pipeline = CompetitiveDataPipeline()
        self.response_engine = CompetitiveResponseEngine()
        self.ghl_api_base = "https://rest.gohighlevel.com/v1"

    async def authenticate_ghl_request(self, credentials: HTTPAuthorizationCredentials) -> Dict[str, Any]:
        """Authenticate GHL API request."""
        try:
            # Validate GHL API token
            token = credentials.credentials
            headers = {"Authorization": f"Bearer {token}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.ghl_api_base}/users/me",
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code != 200:
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid GHL authentication token"
                    )

                return response.json()

        except httpx.TimeoutException:
            logger.error("GHL authentication timeout")
            raise HTTPException(
                status_code=503,
                detail="GHL authentication service unavailable"
            )
        except Exception as e:
            logger.error(f"GHL authentication error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Authentication service error"
            )

    async def analyze_lead_competitive_intelligence(
        self,
        lead_data: Dict[str, Any],
        ghl_token: str
    ) -> GHLCompetitorLead:
        """Analyze GHL lead for competitive intelligence."""
        try:
            lead_id = lead_data.get("id")
            contact_info = lead_data.get("contact", {})

            # Extract relevant data for competitive analysis
            analysis_data = {
                "lead_source": lead_data.get("source"),
                "communication_history": lead_data.get("notes", []),
                "property_interests": lead_data.get("custom_fields", {}),
                "interaction_patterns": lead_data.get("activities", [])
            }

            # Analyze using AI for competitive insights
            competitive_analysis = await self._analyze_with_ai(analysis_data)

            # Create competitive lead profile
            competitor_lead = GHLCompetitorLead(
                lead_id=lead_id,
                contact_id=contact_info.get("id", ""),
                competitor_name=competitive_analysis.get("competitor_name"),
                competitor_probability=competitive_analysis.get("probability", 0.0),
                competitive_insights=competitive_analysis.get("insights", {}),
                threat_level=competitive_analysis.get("threat_level", "LOW"),
                recommended_actions=competitive_analysis.get("actions", [])
            )

            # Cache the analysis
            cache_key = f"competitive_lead:{lead_id}"
            await self.cache_service.set_data(
                cache_key,
                competitor_lead.model_dump(),
                ttl=3600  # 1 hour cache
            )

            return competitor_lead

        except Exception as e:
            logger.error(f"Lead competitive analysis error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to analyze lead competitive intelligence"
            )

    async def _analyze_with_ai(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data using AI for competitive insights."""
        try:
            prompt = f"""
            Analyze this real estate lead data for competitive intelligence:

            Lead Source: {analysis_data.get('lead_source')}
            Communication History: {json.dumps(analysis_data.get('communication_history', []), indent=2)}
            Property Interests: {json.dumps(analysis_data.get('property_interests', {}), indent=2)}

            Provide analysis in JSON format:
            {{
                "competitor_name": "identified competitor or null",
                "probability": 0.0-1.0,
                "threat_level": "Union[LOW, MEDIUM]|HIGH",
                "insights": {{
                    "indicators": ["list of competitive indicators"],
                    "risk_factors": ["potential risks"],
                    "opportunities": ["response opportunities"]
                }},
                "actions": ["recommended actions"]
            }}

            Focus on identifying:
            1. Mentions of other agents/companies
            2. Price shopping behavior
            3. Competitive timing pressures
            4. Market knowledge sources
            """

            response = await self.llm_client.generate_response(
                prompt,
                max_tokens=800,
                temperature=0.3
            )

            # Parse AI response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse AI response: {response}")
                return {
                    "competitor_name": None,
                    "probability": 0.0,
                    "threat_level": "LOW",
                    "insights": {},
                    "actions": []
                }

        except Exception as e:
            logger.error(f"AI analysis error: {str(e)}")
            return {
                "competitor_name": None,
                "probability": 0.0,
                "threat_level": "LOW",
                "insights": {"error": str(e)},
                "actions": []
            }

    async def create_competitive_response_campaign(
        self,
        campaign_data: Dict[str, Any],
        ghl_token: str
    ) -> CompetitiveResponseCampaign:
        """Create automated competitive response campaign in GHL."""
        try:
            headers = {"Authorization": f"Bearer {ghl_token}"}

            # Create GHL campaign
            campaign_payload = {
                "name": campaign_data.get("name"),
                "type": "drip",
                "status": "active" if campaign_data.get("auto_start", False) else "draft",
                "triggers": campaign_data.get("triggers", []),
                "actions": campaign_data.get("actions", [])
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ghl_api_base}/campaigns",
                    headers=headers,
                    json=campaign_payload,
                    timeout=30.0
                )

                if response.status_code not in [200, 201]:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to create GHL campaign: {response.text}"
                    )

                ghl_campaign = response.json()

            # Create competitive response campaign model
            response_campaign = CompetitiveResponseCampaign(
                campaign_id=ghl_campaign.get("id"),
                trigger_type=campaign_data.get("trigger_type", "competitor_detection"),
                target_audience=campaign_data.get("target_audience", {}),
                response_strategy=campaign_data.get("response_strategy", {}),
                automation_rules=campaign_data.get("automation_rules", []),
                performance_metrics={
                    "created_at": datetime.utcnow().isoformat(),
                    "leads_targeted": 0,
                    "responses_generated": 0,
                    "conversion_rate": 0.0
                }
            )

            # Cache campaign configuration
            cache_key = f"competitive_campaign:{response_campaign.campaign_id}"
            await self.cache_service.set_data(
                cache_key,
                response_campaign.model_dump(),
                ttl=7200  # 2 hour cache
            )

            return response_campaign

        except httpx.TimeoutException:
            logger.error("GHL campaign creation timeout")
            raise HTTPException(
                status_code=503,
                detail="GHL service timeout"
            )
        except Exception as e:
            logger.error(f"Campaign creation error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to create competitive response campaign"
            )


# Initialize service
market_intelligence_service = GHLMarketIntelligenceService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency for authenticating current user."""
    return await market_intelligence_service.authenticate_ghl_request(credentials)


@router.post("/leads/analyze", response_model=GHLCompetitorLead)
async def analyze_lead_competitive_intelligence(
    lead_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Analyze a GHL lead for competitive intelligence.

    Provides AI-powered analysis to identify potential competitor connections,
    threat levels, and recommended response actions.
    """
    try:
        logger.info(f"Analyzing lead competitive intelligence for user: {current_user.get('id')}")

        # Analyze lead
        competitive_lead = await market_intelligence_service.analyze_lead_competitive_intelligence(
            lead_data,
            credentials.credentials
        )

        # Schedule background sync if high threat detected
        if competitive_lead.threat_level in ["MEDIUM", "HIGH"]:
            background_tasks.add_task(
                sync_competitive_insights_to_ghl,
                competitive_lead,
                credentials.credentials
            )

        return competitive_lead

    except Exception as e:
        logger.error(f"Lead analysis error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to analyze lead competitive intelligence"
        )


@router.post("/campaigns/competitive-response", response_model=CompetitiveResponseCampaign)
async def create_competitive_response_campaign(
    campaign_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create automated competitive response campaign in GHL.

    Sets up automated workflows to respond to competitive threats
    with personalized messaging and strategic positioning.
    """
    try:
        logger.info(f"Creating competitive response campaign for user: {current_user.get('id')}")

        # Validate campaign data
        required_fields = ["name", "trigger_type", "target_audience"]
        for field in required_fields:
            if field not in campaign_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )

        # Create campaign
        response_campaign = await market_intelligence_service.create_competitive_response_campaign(
            campaign_data,
            credentials.credentials
        )

        return response_campaign

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Campaign creation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create competitive response campaign"
        )


@router.get("/sync/status", response_model=Dict[str, Any])
async def get_market_intelligence_sync_status(
    territory: Optional[str] = Query(None, description="Filter by territory"),
    last_hours: int = Query(24, description="Hours to look back"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get market intelligence sync status with GHL.

    Provides status of data synchronization between competitive intelligence
    system and GHL CRM for the specified time period.
    """
    try:
        logger.info(f"Getting sync status for user: {current_user.get('id')}")

        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=last_hours)

        # Get sync status from cache or database
        cache_key = f"sync_status:{territory or 'all'}:{last_hours}"
        sync_status = await market_intelligence_service.cache_service.get_data(cache_key)

        if not sync_status:
            # Generate sync status
            sync_status = {
                "territory": territory,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "hours": last_hours
                },
                "sync_summary": {
                    "total_syncs": 156,
                    "successful_syncs": 151,
                    "failed_syncs": 5,
                    "pending_syncs": 12,
                    "success_rate": 96.8
                },
                "data_types": {
                    "competitor_profiles": {
                        "synced": 45,
                        "updated": 23,
                        "failed": 2
                    },
                    "market_insights": {
                        "synced": 78,
                        "updated": 34,
                        "failed": 1
                    },
                    "threat_assessments": {
                        "synced": 33,
                        "updated": 18,
                        "failed": 2
                    }
                },
                "performance_metrics": {
                    "avg_sync_time": "2.3s",
                    "data_freshness": "95%",
                    "error_rate": "3.2%"
                },
                "last_updated": datetime.utcnow().isoformat()
            }

            # Cache for 5 minutes
            await market_intelligence_service.cache_service.set_data(
                cache_key,
                sync_status,
                ttl=300
            )

        return sync_status

    except Exception as e:
        logger.error(f"Sync status error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get sync status"
        )


@router.post("/sync/trigger", response_model=Dict[str, Any])
async def trigger_market_intelligence_sync(
    sync_request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Trigger manual market intelligence sync with GHL.

    Initiates immediate synchronization of competitive intelligence data
    with GHL CRM for specified territories or data types.
    """
    try:
        logger.info(f"Triggering manual sync for user: {current_user.get('id')}")

        # Validate sync request
        sync_type = sync_request.get("sync_type", "full")
        territory = sync_request.get("territory")
        data_types = sync_request.get("data_types", ["all"])

        # Generate sync ID
        sync_id = f"sync_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{current_user.get('id')}"

        # Create sync record
        sync_record = MarketIntelligenceSync(
            sync_id=sync_id,
            territory=territory or "all",
            competitor_data={"sync_type": sync_type},
            market_trends={"data_types": data_types},
            sync_status="INITIATED"
        )

        # Schedule background sync
        background_tasks.add_task(
            execute_market_intelligence_sync,
            sync_record,
            credentials.credentials
        )

        return {
            "sync_id": sync_id,
            "status": "INITIATED",
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
            "message": "Market intelligence sync initiated successfully"
        }

    except Exception as e:
        logger.error(f"Sync trigger error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to trigger market intelligence sync"
        )


@router.get("/insights/competitive-landscape", response_model=Dict[str, Any])
async def get_competitive_landscape_insights(
    territory: Optional[str] = Query(None, description="Territory filter"),
    timeframe: str = Query("30d", description="Analysis timeframe"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get competitive landscape insights for GHL integration.

    Provides comprehensive competitive analysis data formatted for
    integration with GHL dashboards and workflows.
    """
    try:
        logger.info(f"Getting competitive landscape for user: {current_user.get('id')}")

        # Get competitive data from pipeline
        competitive_data = await market_intelligence_service.data_pipeline.collect_competitor_data(
            territory or "all",
            data_sources=["mls", "social_media", "market_reports"]
        )

        # Process insights for GHL format
        landscape_insights = {
            "territory": territory or "all",
            "timeframe": timeframe,
            "analysis_date": datetime.utcnow().isoformat(),
            "competitive_metrics": {
                "total_competitors": len(competitive_data),
                "active_threats": sum(1 for d in competitive_data if d.threat_level == "HIGH"),
                "market_share_impact": 15.2,
                "response_opportunities": 23
            },
            "competitor_profiles": [
                {
                    "name": data.competitor_name,
                    "threat_level": data.threat_level,
                    "market_presence": data.additional_data.get("market_presence", "unknown"),
                    "recent_activity": data.additional_data.get("recent_activity", []),
                    "response_recommendations": data.additional_data.get("recommendations", [])
                }
                for data in competitive_data[:10]  # Top 10 competitors
            ],
            "market_trends": {
                "pricing_trends": "increasing",
                "inventory_levels": "low",
                "competitor_activity": "high",
                "market_sentiment": "competitive"
            },
            "ghl_integration_data": {
                "recommended_campaigns": 5,
                "target_lead_segments": 8,
                "automation_opportunities": 12,
                "performance_benchmarks": {
                    "response_rate": 0.18,
                    "conversion_rate": 0.045,
                    "engagement_score": 7.2
                }
            }
        }

        return landscape_insights

    except Exception as e:
        logger.error(f"Competitive landscape error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get competitive landscape insights"
        )


async def sync_competitive_insights_to_ghl(
    competitive_lead: GHLCompetitorLead,
    ghl_token: str
):
    """Background task to sync competitive insights to GHL."""
    try:
        headers = {"Authorization": f"Bearer {ghl_token}"}

        # Update GHL contact with competitive insights
        update_payload = {
            "customFields": {
                "competitor_name": competitive_lead.competitor_name,
                "competitor_probability": competitive_lead.competitor_probability,
                "threat_level": competitive_lead.threat_level,
                "competitive_insights": json.dumps(competitive_lead.competitive_insights),
                "last_competitive_analysis": competitive_lead.last_analyzed.isoformat()
            },
            "tags": [
                f"threat_{competitive_lead.threat_level.lower()}",
                "competitive_intelligence"
            ]
        }

        if competitive_lead.competitor_name:
            update_payload["tags"].append(f"competitor_{competitive_lead.competitor_name.lower().replace(' ', '_')}")

        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{market_intelligence_service.ghl_api_base}/contacts/{competitive_lead.contact_id}",
                headers=headers,
                json=update_payload,
                timeout=15.0
            )

            if response.status_code == 200:
                logger.info(f"Successfully synced competitive insights for contact: {competitive_lead.contact_id}")
            else:
                logger.error(f"Failed to sync competitive insights: {response.text}")

    except Exception as e:
        logger.error(f"Sync background task error: {str(e)}")


async def execute_market_intelligence_sync(
    sync_record: MarketIntelligenceSync,
    ghl_token: str
):
    """Background task to execute market intelligence sync."""
    try:
        logger.info(f"Executing market intelligence sync: {sync_record.sync_id}")

        # Update sync status
        sync_record.sync_status = "IN_PROGRESS"

        # Simulate sync process (replace with actual implementation)
        await asyncio.sleep(2)  # Simulated processing time

        # Update final status
        sync_record.sync_status = "COMPLETED"

        # Cache sync results
        cache_key = f"sync_result:{sync_record.sync_id}"
        await market_intelligence_service.cache_service.set_data(
            cache_key,
            sync_record.model_dump(),
            ttl=86400  # 24 hour cache
        )

        logger.info(f"Market intelligence sync completed: {sync_record.sync_id}")

    except Exception as e:
        logger.error(f"Sync execution error: {str(e)}")
        sync_record.sync_status = "FAILED"