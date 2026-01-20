"""
Competitive Intelligence Engine - FastAPI Application

REST API for enterprise competitive intelligence and monitoring.

Endpoints:
- /competitors: Manage competitor monitoring
- /intelligence: Get competitive intelligence reports
- /sentiment: Social sentiment analysis
- /alerts: Crisis detection and alerting
- /predictions: Competitive forecasting

Author: Claude Code Agent - Competitive Intelligence Specialist
Created: 2026-01-19
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import logging

# Import our competitive intelligence modules
from src.intelligence.competitor_monitor import CompetitiveIntelligenceHub
from src.data.web_scraper import CompetitorWebScraper, CompetitorWebsite, ScrapingMethod
from src.data.social_monitor import SocialMediaMonitor, Platform, SentimentType

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Competitive Intelligence Engine",
    description="Enterprise-grade real-time competitive monitoring & predictive intelligence",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (in production, use dependency injection)
web_scraper = CompetitorWebScraper()
social_monitor = None  # Will be initialized with config

# Pydantic models for API
class CompetitorWebsiteRequest(BaseModel):
    name: str
    domain: str
    pricing_page_url: str
    features_page_url: Optional[str] = None
    scraping_method: str = "requests"
    rate_limit_delay: int = 5

class MonitoringConfigRequest(BaseModel):
    brand: str
    competitors: List[str]
    keywords: List[str]
    platforms: List[str] = ["reddit", "twitter", "news_rss"]

class AlertConfigRequest(BaseModel):
    negative_sentiment_threshold: float = 0.7
    volume_spike_threshold: float = 5.0
    notification_webhook: Optional[str] = None

# === COMPETITOR MONITORING ENDPOINTS ===

@app.post("/competitors/websites")
async def add_competitor_website(website: CompetitorWebsiteRequest):
    """Add a competitor website for monitoring."""
    try:
        competitor_site = CompetitorWebsite(
            name=website.name,
            domain=website.domain,
            pricing_page_url=website.pricing_page_url,
            features_page_url=website.features_page_url,
            scraping_method=ScrapingMethod(website.scraping_method),
            rate_limit_delay=website.rate_limit_delay
        )

        web_scraper.add_competitor(competitor_site)

        return {
            "status": "success",
            "message": f"Added competitor website: {website.name}",
            "competitor": website.name
        }
    except Exception as e:
        logger.error(f"Error adding competitor website: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/competitors/websites")
async def list_competitor_websites():
    """List all monitored competitor websites."""
    try:
        competitors = []
        for name, website in web_scraper.monitored_websites.items():
            summary = web_scraper.get_competitor_summary(name)
            competitors.append({
                "name": name,
                "domain": website.domain,
                "last_scraped": website.last_scraped.isoformat() if website.last_scraped else None,
                "scraping_method": website.scraping_method.value,
                "summary": summary
            })

        return {
            "total_competitors": len(competitors),
            "competitors": competitors
        }
    except Exception as e:
        logger.error(f"Error listing competitors: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/competitors/scrape")
async def scrape_all_competitors(background_tasks: BackgroundTasks):
    """Trigger scraping of all competitor websites."""
    try:
        # Run scraping in background
        background_tasks.add_task(run_competitor_scraping)

        return {
            "status": "started",
            "message": "Competitor scraping initiated in background",
            "total_competitors": len(web_scraper.monitored_websites)
        }
    except Exception as e:
        logger.error(f"Error triggering scraping: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_competitor_scraping():
    """Background task for competitor scraping."""
    try:
        results = await web_scraper.scrape_all_competitors()
        logger.info(f"Completed scraping {len(results)} competitors")

        # Process results for alerts
        for result in results:
            if result.success and result.changes_detected:
                logger.warning(f"Changes detected for {result.website}: {len(result.changes_detected)} changes")
                # TODO: Send alerts

    except Exception as e:
        logger.error(f"Error in background scraping: {str(e)}")

@app.get("/competitors/{competitor_name}/summary")
async def get_competitor_summary(competitor_name: str):
    """Get detailed summary for a specific competitor."""
    try:
        summary = web_scraper.get_competitor_summary(competitor_name)
        if not summary:
            raise HTTPException(status_code=404, detail=f"Competitor {competitor_name} not found")

        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting competitor summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# === SOCIAL MEDIA MONITORING ENDPOINTS ===

@app.post("/social/configure")
async def configure_social_monitoring(config: MonitoringConfigRequest):
    """Configure social media monitoring."""
    global social_monitor

    try:
        # Initialize social monitor with config
        social_config = {
            "reddit": {
                "client_id": "demo_client_id",
                "client_secret": "demo_client_secret",
                "user_agent": "competitive_intelligence_monitor"
            }
        }

        social_monitor = SocialMediaMonitor(social_config)

        # Add brand and competitors
        social_monitor.add_monitored_brand(config.brand, config.keywords)
        for competitor in config.competitors:
            social_monitor.add_competitor(competitor, config.keywords)

        return {
            "status": "success",
            "message": "Social media monitoring configured",
            "brand": config.brand,
            "competitors": config.competitors,
            "platforms": config.platforms
        }
    except Exception as e:
        logger.error(f"Error configuring social monitoring: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/social/monitor")
async def monitor_social_platforms(background_tasks: BackgroundTasks):
    """Trigger social media monitoring across all platforms."""
    if not social_monitor:
        raise HTTPException(status_code=400, detail="Social monitoring not configured")

    try:
        background_tasks.add_task(run_social_monitoring)

        return {
            "status": "started",
            "message": "Social media monitoring initiated",
            "monitored_brands": len(social_monitor.monitored_brands),
            "monitored_competitors": len(social_monitor.monitored_competitors)
        }
    except Exception as e:
        logger.error(f"Error triggering social monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_social_monitoring():
    """Background task for social media monitoring."""
    try:
        results = await social_monitor.monitor_all_platforms()
        total_mentions = sum(len(mentions) for mentions in results.values())
        logger.info(f"Social monitoring completed: {total_mentions} mentions found")

        # Check for crisis signals
        for brand in social_monitor.monitored_brands:
            crisis = social_monitor.detect_crisis_signals(brand)
            if crisis['crisis_detected']:
                logger.critical(f"Crisis detected for {brand}: {crisis['signals']}")
                # TODO: Send crisis alerts

    except Exception as e:
        logger.error(f"Error in social monitoring: {str(e)}")

@app.get("/social/sentiment/{brand}")
async def get_sentiment_analysis(brand: str, days: int = 7):
    """Get sentiment analysis for a brand."""
    if not social_monitor:
        raise HTTPException(status_code=400, detail="Social monitoring not configured")

    try:
        trend = social_monitor.analyze_sentiment_trends(brand, days)
        if not trend:
            raise HTTPException(status_code=404, detail=f"No data found for brand: {brand}")

        return {
            "brand": brand,
            "time_period": f"{days} days",
            "sentiment_breakdown": {
                "positive": trend.positive_mentions,
                "negative": trend.negative_mentions,
                "neutral": trend.neutral_mentions,
                "total": trend.total_mentions
            },
            "average_sentiment": trend.average_sentiment,
            "alert_level": trend.alert_level.value,
            "top_keywords": trend.top_keywords,
            "crisis_indicators": trend.crisis_indicators
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sentiment analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/social/crisis/{brand}")
async def check_crisis_signals(brand: str):
    """Check for crisis signals for a specific brand."""
    if not social_monitor:
        raise HTTPException(status_code=400, detail="Social monitoring not configured")

    try:
        crisis_analysis = social_monitor.detect_crisis_signals(brand)
        return crisis_analysis
    except Exception as e:
        logger.error(f"Error checking crisis signals: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# === ANALYTICS & REPORTING ENDPOINTS ===

@app.get("/intelligence/dashboard")
async def get_intelligence_dashboard():
    """Get comprehensive competitive intelligence dashboard data."""
    try:
        dashboard_data = {
            "competitor_monitoring": {
                "total_websites": len(web_scraper.monitored_websites),
                "active_monitoring": True,
                "recent_changes": []
            },
            "social_intelligence": {
                "monitoring_active": social_monitor is not None,
                "monitored_brands": len(social_monitor.monitored_brands) if social_monitor else 0,
                "monitored_competitors": len(social_monitor.monitored_competitors) if social_monitor else 0
            },
            "alerts": {
                "active_crises": 0,
                "pending_alerts": 0
            },
            "system_health": {
                "web_scraper": "online",
                "social_monitor": "online" if social_monitor else "offline",
                "last_update": datetime.now().isoformat()
            }
        }

        # Add recent changes from competitor websites
        for name, website in web_scraper.monitored_websites.items():
            summary = web_scraper.get_competitor_summary(name)
            if summary and summary.get('recent_changes'):
                dashboard_data["competitor_monitoring"]["recent_changes"].extend(
                    summary['recent_changes']
                )

        return dashboard_data
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "web_scraper": "online",
            "social_monitor": "online" if social_monitor else "offline"
        }
    }

# === STARTUP EVENTS ===

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Competitive Intelligence Engine API...")

    # Initialize with demo data
    demo_competitors = [
        CompetitorWebsite(
            name="demo_competitor_saas",
            domain="demo-saas.com",
            pricing_page_url="https://demo-saas.com/pricing",
            features_page_url="https://demo-saas.com/features",
            scraping_method=ScrapingMethod.REQUESTS
        )
    ]

    # Add demo competitors
    for competitor in demo_competitors:
        web_scraper.add_competitor(competitor)

    logger.info("Competitive Intelligence Engine API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Competitive Intelligence Engine API...")


if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )