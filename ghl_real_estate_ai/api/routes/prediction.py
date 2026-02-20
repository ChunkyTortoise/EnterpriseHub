"""
Prediction API Routes - Jorge's Crystal Ball Technology
FastAPI routes for predictive intelligence and forecasting services

This module provides:
- Market movement prediction endpoints
- Client behavior analysis and prediction
- Deal outcome and closing probability prediction
- Business forecasting and strategic planning
- Real-time prediction updates via WebSocket
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ...prediction.business_forecasting_engine import ForecastTimeframe, GrowthStrategy
from ...prediction.business_forecasting_engine import BusinessForecastingEngine
from ...prediction.client_behavior_analyzer import ClientBehaviorAnalyzer
from ...prediction.deal_success_predictor import DealStage, DealSuccessPredictor
from ...prediction.jorge_prediction_engine import JorgePredictionEngine, PredictionContext, TimeFrame
from ...prediction.market_intelligence_analyzer import MarketIntelligenceAnalyzer
from ...services.auth_service import get_current_user
from ...services.database_service import get_database
from ...services.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/prediction", tags=["prediction"])

# Initialize prediction engines
prediction_engine = JorgePredictionEngine()
market_analyzer = MarketIntelligenceAnalyzer()
client_analyzer = ClientBehaviorAnalyzer()
deal_predictor = DealSuccessPredictor()
business_forecaster = BusinessForecastingEngine()

# WebSocket manager for real-time updates
ws_manager = WebSocketManager()


# Request/Response Models
class LocationRequest(BaseModel):
    lat: float
    lng: float


class MarketMovementRequest(BaseModel):
    location: LocationRequest
    timeframe: str = "medium_term"
    context: Optional[Dict[str, Any]] = None


class ClientBehaviorRequest(BaseModel):
    client_id: str
    scenario: str = "purchase_timing"
    context: Optional[Dict[str, Any]] = None


class DealOutcomeRequest(BaseModel):
    deal_id: str
    current_stage: str = "negotiation"
    context: Optional[Dict[str, Any]] = None


class BusinessForecastRequest(BaseModel):
    metric_type: str = "revenue"
    timeframe: str = "quarterly"
    context: Optional[Dict[str, Any]] = None


class BulkPredictionRequest(BaseModel):
    requests: List[Dict[str, Any]]


class PredictionAccuracyRequest(BaseModel):
    prediction_id: str
    actual_outcome: Dict[str, Any]


def _normalize_string_list(value: Any, fallback: List[str]) -> List[str]:
    if isinstance(value, list):
        parsed = [str(item).strip() for item in value if str(item).strip()]
        return parsed or fallback
    if isinstance(value, str):
        parsed = [item.strip() for item in value.split(",") if item.strip()]
        return parsed or fallback
    return fallback


async def _fetch_client_interaction_history(client_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch recent interaction history for a client from the repository layer."""
    try:
        db = await get_database()
        async with db.get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    interaction_type,
                    content,
                    metadata,
                    created_at
                FROM interaction_history
                WHERE client_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                client_id,
                limit,
            )
        return [dict(row) for row in rows]
    except Exception as exc:
        logger.warning("Failed to fetch interaction history for %s: %s", client_id, exc)
        return []


async def _fetch_deal_data(deal_id: str, current_stage: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Fetch deal row from repository and normalize for predictor input."""
    fallback = {
        "deal_id": deal_id,
        "property_value": float((context or {}).get("property_value", 500000)),
        "offer_amount": float((context or {}).get("offer_amount", 485000)),
        "commission_rate": float((context or {}).get("commission_rate", 0.06)),
        "current_stage": current_stage,
    }
    try:
        db = await get_database()
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    deal_id,
                    property_value,
                    offer_amount,
                    commission_rate,
                    current_stage
                FROM deals
                WHERE deal_id = $1
                LIMIT 1
                """,
                deal_id,
            )
        if not row:
            return fallback

        record = dict(row)
        return {
            "deal_id": record.get("deal_id", deal_id),
            "property_value": float(record.get("property_value") or fallback["property_value"]),
            "offer_amount": float(record.get("offer_amount") or fallback["offer_amount"]),
            "commission_rate": float(record.get("commission_rate") or fallback["commission_rate"]),
            "current_stage": str(record.get("current_stage") or current_stage),
        }
    except Exception as exc:
        logger.warning("Failed to fetch deal data for %s: %s", deal_id, exc)
        return fallback


async def _fetch_business_profile(user_id: str) -> Dict[str, Any]:
    """Fetch target markets/team/expansion preferences for business forecasting."""
    profile = {
        "target_markets": ["NYC", "LA", "Chicago"],
        "team_size": 8,
        "expansion_territories": ["Miami", "Rancho Cucamonga", "Seattle"],
    }
    try:
        db = await get_database()
        async with db.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT
                    target_markets,
                    team_size,
                    expansion_territories
                FROM user_settings
                WHERE user_id = $1
                LIMIT 1
                """,
                user_id,
            )
        if not row:
            return profile

        record = dict(row)
        profile["target_markets"] = _normalize_string_list(record.get("target_markets"), profile["target_markets"])
        profile["team_size"] = int(record.get("team_size") or profile["team_size"])
        profile["expansion_territories"] = _normalize_string_list(
            record.get("expansion_territories"), profile["expansion_territories"]
        )
    except Exception as exc:
        logger.warning("Failed to fetch business profile for %s: %s", user_id, exc)

    return profile


# Market Movement Prediction
@router.post("/market-movement")
async def predict_market_movement(request: MarketMovementRequest, current_user: Dict = Depends(get_current_user)):
    """
    Predict market movement for specific location and timeframe
    """
    try:
        logger.info(f"Market movement prediction requested by user: {current_user.get('user_id')}")

        # Convert request to internal format
        location = {"lat": request.location.lat, "lng": request.location.lng}
        timeframe = TimeFrame(request.timeframe)
        context = PredictionContext(**request.context) if request.context else None

        # Generate market prediction
        prediction = await prediction_engine.predict_market_movement(location, timeframe, context)

        # Broadcast update to connected WebSocket clients
        await ws_manager.broadcast_to_group(
            "market_predictions",
            {
                "type": "market_prediction_update",
                "location": location,
                "prediction": prediction.__dict__,
                "timestamp": datetime.now().isoformat(),
            },
        )

        return prediction.__dict__

    except Exception as e:
        logger.error(f"Market movement prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Client Behavior Prediction
@router.post("/client-behavior")
async def predict_client_behavior(request: ClientBehaviorRequest, current_user: Dict = Depends(get_current_user)):
    """
    Predict client behavior patterns and purchase timing
    """
    try:
        logger.info(f"Client behavior prediction requested for: {request.client_id}")

        interaction_history = await _fetch_client_interaction_history(request.client_id)

        # Generate behavioral predictions
        psychology_profile = await client_analyzer.analyze_client_psychology(
            request.client_id, interaction_history, request.context
        )

        purchase_prediction = await client_analyzer.predict_purchase_behavior(
            request.client_id, "active", request.context
        )

        behavioral_patterns = await client_analyzer.assess_behavioral_patterns(request.client_id, 30)

        financial_profile = await client_analyzer.evaluate_financial_readiness(request.client_id, request.context)

        client_value = await client_analyzer.predict_client_value(
            request.client_id, behavioral_patterns, financial_profile
        )

        engagement_strategy = await client_analyzer.determine_optimal_engagement_strategy(
            request.client_id, psychology_profile, purchase_prediction
        )

        # Comprehensive client prediction response
        response = {
            "client_id": request.client_id,
            "psychology_profile": psychology_profile.__dict__,
            "purchase_prediction": purchase_prediction.__dict__,
            "behavioral_patterns": behavioral_patterns.__dict__,
            "financial_profile": financial_profile.__dict__,
            "client_value_assessment": client_value.__dict__,
            "optimal_engagement_strategy": engagement_strategy,
        }

        # Broadcast update to WebSocket clients
        await ws_manager.broadcast_to_group(
            "client_predictions",
            {
                "type": "client_behavior_update",
                "client_id": request.client_id,
                "purchase_probability": purchase_prediction.purchase_probability,
                "jorge_methodology_fit": engagement_strategy.get("jorge_methodology_fit_score", 0),
                "timestamp": datetime.now().isoformat(),
            },
        )

        return response

    except Exception as e:
        logger.error(f"Client behavior prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Deal Outcome Prediction
@router.post("/deal-outcome")
async def predict_deal_outcome(request: DealOutcomeRequest, current_user: Dict = Depends(get_current_user)):
    """
    Predict deal outcome and closing probability
    """
    try:
        logger.info(f"Deal outcome prediction requested for: {request.deal_id}")

        deal_data = await _fetch_deal_data(request.deal_id, request.current_stage, request.context)

        # Generate deal predictions
        deal_forecast = await deal_predictor.predict_deal_success(
            request.deal_id, deal_data, DealStage(request.current_stage), request.context
        )

        deal_risks = await deal_predictor.assess_deal_risks(
            request.deal_id, deal_data, DealStage(request.current_stage)
        )

        success_accelerators = await deal_predictor.identify_success_accelerators(
            request.deal_id, deal_data, DealStage(request.current_stage)
        )

        negotiation_intelligence = await deal_predictor.generate_negotiation_intelligence(
            request.deal_id, deal_data, request.context or {}
        )

        commission_optimization = await deal_predictor.predict_commission_optimization(
            request.deal_id, deal_data, request.context or {}
        )

        # Comprehensive deal prediction response
        response = {
            "deal_id": request.deal_id,
            "deal_forecast": deal_forecast.__dict__,
            "risk_assessment": [risk.__dict__ for risk in deal_risks],
            "success_accelerators": [acc.__dict__ for acc in success_accelerators],
            "negotiation_intelligence": negotiation_intelligence.__dict__,
            "commission_optimization": commission_optimization,
        }

        # Broadcast update to WebSocket clients
        await ws_manager.broadcast_to_group(
            "deal_predictions",
            {
                "type": "deal_outcome_update",
                "deal_id": request.deal_id,
                "closing_probability": deal_forecast.closing_probability,
                "commission_probability_6_percent": deal_forecast.commission_probability_6_percent,
                "timestamp": datetime.now().isoformat(),
            },
        )

        return response

    except Exception as e:
        logger.error(f"Deal outcome prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Business Forecasting
@router.post("/business-forecast")
async def generate_business_forecast(request: BusinessForecastRequest, current_user: Dict = Depends(get_current_user)):
    """
    Generate comprehensive business forecasting and strategic planning
    """
    try:
        logger.info(f"Business forecast requested: {request.metric_type} - {request.timeframe}")

        # Generate comprehensive business forecasts
        revenue_forecast = await business_forecaster.forecast_revenue(
            ForecastTimeframe(request.timeframe), request.context or {}, request.context or {}
        )

        user_id = str(current_user.get("user_id") or current_user.get("id") or "anonymous")
        business_profile = await _fetch_business_profile(user_id)

        target_markets = business_profile["target_markets"]
        market_share_projection = await business_forecaster.project_market_share_growth(
            target_markets,
            GrowthStrategy.STEADY_GROWTH,
        )

        team_data = {"team_size": business_profile["team_size"]}
        team_projection = await business_forecaster.forecast_team_performance(
            team_data,
            {"growth_targets": {}},
            ForecastTimeframe(request.timeframe),
        )

        expansion_territories = business_profile["expansion_territories"]
        territory_analysis = await business_forecaster.analyze_territory_expansion(
            expansion_territories
        )

        business_opportunities = await business_forecaster.identify_business_opportunities(
            ["market_expansion", "service_enhancement", "technology_leverage"]
        )

        # Strategic business plan
        strategic_plan = await business_forecaster.generate_strategic_business_plan(
            ForecastTimeframe(request.timeframe),
            {
                "revenue_data": request.context or {},
                "target_markets": target_markets,
                "growth_strategy": "steady_growth",
                "team_data": team_data,
                "team_growth_plans": {},
                "potential_territories": expansion_territories,
                "opportunity_types": ["market_expansion", "service_enhancement"],
            },
        )

        # Comprehensive business forecast response
        response = {
            "metric_type": request.metric_type,
            "timeframe": request.timeframe,
            "revenue_forecast": revenue_forecast.__dict__,
            "market_share_projection": market_share_projection.__dict__,
            "team_performance_projection": team_projection.__dict__,
            "territory_expansion_analysis": territory_analysis.__dict__,
            "business_opportunities": [opp.__dict__ for opp in business_opportunities],
            "strategic_plan": strategic_plan,
        }

        # Broadcast update to WebSocket clients
        await ws_manager.broadcast_to_group(
            "business_forecasts",
            {
                "type": "business_forecast_update",
                "metric_type": request.metric_type,
                "timeframe": request.timeframe,
                "revenue_base": float(revenue_forecast.base_forecast),
                "growth_rate": revenue_forecast.growth_rate,
                "timestamp": datetime.now().isoformat(),
            },
        )

        return response

    except Exception as e:
        logger.error(f"Business forecast generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Bulk Predictions
@router.post("/bulk")
async def process_bulk_predictions(
    request: BulkPredictionRequest, background_tasks: BackgroundTasks, current_user: Dict = Depends(get_current_user)
):
    """
    Process multiple prediction requests in bulk
    """
    try:
        logger.info(f"Bulk predictions requested: {len(request.requests)} requests")

        results = []
        for req in request.requests:
            try:
                prediction_type = req.get("type")
                parameters = req.get("parameters", {})

                if prediction_type == "market_movement":
                    prediction = await predict_market_movement(MarketMovementRequest(**parameters), current_user)
                elif prediction_type == "client_behavior":
                    prediction = await predict_client_behavior(ClientBehaviorRequest(**parameters), current_user)
                elif prediction_type == "deal_outcome":
                    prediction = await predict_deal_outcome(DealOutcomeRequest(**parameters), current_user)
                elif prediction_type == "business_forecast":
                    prediction = await generate_business_forecast(BusinessForecastRequest(**parameters), current_user)
                else:
                    raise ValueError(f"Unknown prediction type: {prediction_type}")

                results.append({"type": prediction_type, "status": "success", "result": prediction})

            except Exception as e:
                results.append({"type": req.get("type", "unknown"), "status": "error", "error": str(e)})

        return {
            "total_requests": len(request.requests),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"]),
            "results": results,
        }

    except Exception as e:
        logger.error(f"Bulk predictions failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Prediction Explanation
@router.get("/explain/{prediction_id}")
async def explain_prediction(prediction_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Get detailed explanation of how a prediction was made
    """
    try:
        explanation = await prediction_engine.explain_prediction(prediction_id)
        return explanation

    except Exception as e:
        logger.error(f"Prediction explanation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Update Prediction Accuracy
@router.post("/accuracy")
async def update_prediction_accuracy(
    request: PredictionAccuracyRequest, current_user: Dict = Depends(get_current_user)
):
    """
    Update prediction accuracy based on actual outcomes
    """
    try:
        logger.info(f"Updating prediction accuracy for: {request.prediction_id}")

        await prediction_engine.update_prediction_accuracy(request.prediction_id, request.actual_outcome)

        return {"status": "success", "message": "Prediction accuracy updated"}

    except Exception as e:
        logger.error(f"Prediction accuracy update failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Real-time Prediction Updates WebSocket
@router.websocket("/ws/updates")
async def prediction_updates_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time prediction updates
    """
    await ws_manager.connect(websocket, "prediction_updates")

    try:
        while True:
            # Send periodic prediction updates
            await asyncio.sleep(30)  # 30 seconds

            # Send heartbeat
            await websocket.send_json({"type": "heartbeat", "timestamp": datetime.now().isoformat()})

    except WebSocketDisconnect:
        logger.info("Client disconnected from prediction updates WebSocket")
        await ws_manager.disconnect(websocket, "prediction_updates")


# Market Alerts WebSocket
@router.websocket("/ws/market-alerts")
async def market_alerts_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time market alerts
    """
    await ws_manager.connect(websocket, "market_alerts")

    try:
        while True:
            # Monitor for market changes and send alerts
            await asyncio.sleep(60)  # 1 minute

            await websocket.send_json(
                {
                    "type": "market_alert_summary",
                    "severity": "info",
                    "message": "Market monitor heartbeat",
                    "active_connections": ws_manager.get_connection_count(),
                    "timestamp": datetime.now().isoformat(),
                }
            )

    except WebSocketDisconnect:
        logger.info("Client disconnected from market alerts WebSocket")
        await ws_manager.disconnect(websocket, "market_alerts")


# Background task for continuous prediction updates
async def continuous_prediction_monitoring():
    """
    Background task to continuously monitor and update predictions
    """
    while True:
        try:
            health_status = await prediction_health_check()
            await ws_manager.broadcast_to_group(
                "prediction_updates",
                {
                    "type": "monitoring_tick",
                    "status": health_status.get("engine_status", "unknown"),
                    "websocket_connections": health_status.get("websocket_connections", 0),
                    "timestamp": datetime.now().isoformat(),
                },
            )

            await asyncio.sleep(900)  # 15 minutes

        except Exception as e:
            logger.error(f"Continuous prediction monitoring error: {str(e)}")
            await asyncio.sleep(60)  # Wait 1 minute before retry


# Health check endpoint
@router.get("/health")
async def prediction_health_check():
    """
    Health check for prediction services
    """
    try:
        # Check all prediction engine components
        engine_status = "healthy"
        component_errors = []
        
        # Verify prediction engines are initialized
        if not prediction_engine:
            component_errors.append("prediction_engine not initialized")
        if not market_analyzer:
            component_errors.append("market_analyzer not initialized")
        if not client_analyzer:
            component_errors.append("client_analyzer not initialized")
        if not deal_predictor:
            component_errors.append("deal_predictor not initialized")
        if not business_forecaster:
            component_errors.append("business_forecaster not initialized")
        
        if component_errors:
            engine_status = "degraded"
            logger.warning(f"Prediction health check: {', '.join(component_errors)}")

        # Check model performance (mock data for now - to be replaced with real metrics)
        model_performance = {"market": 87.5, "client": 91.2, "deals": 93.8, "business": 95.1}

        # Check WebSocket connections
        ws_connections = ws_manager.get_connection_count()

        return {
            "status": "healthy",
            "engine_status": engine_status,
            "model_performance": model_performance,
            "websocket_connections": ws_connections,
            "last_update": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Prediction health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")


# Initialize background monitoring
@router.on_event("startup")
async def startup_prediction_monitoring():
    """
    Start background prediction monitoring on startup
    """
    asyncio.create_task(continuous_prediction_monitoring())
    logger.info("Prediction monitoring started")


@router.on_event("shutdown")
async def shutdown_prediction_services():
    """
    Clean up prediction services on shutdown
    """
    await prediction_engine.cleanup()
    await market_analyzer.cleanup()
    await client_analyzer.cleanup()
    await deal_predictor.cleanup()
    await business_forecaster.cleanup()
    logger.info("Prediction services cleaned up")
