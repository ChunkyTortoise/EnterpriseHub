"""
Churn Integration Service - Bridge Between Churn Engine and Existing Services

This service provides a unified interface for churn prediction and intervention,
integrating seamlessly with existing services while maintaining clean separation
of concerns and robust error handling.

Key Responsibilities:
- Orchestrate churn prediction workflows
- Coordinate with existing service ecosystem
- Manage data flow between components
- Provide high-level APIs for the application
- Handle service failures gracefully

Integration Points:
- MemoryService: Lead context and conversation history
- LeadLifecycleTracker: Stage progression data
- BehavioralTriggerEngine: Event-driven data
- LeadScorer: Qualification scoring
- ReengagementEngine: Intervention execution
- GHLService: External workflow automation

Author: EnterpriseHub AI
Last Updated: 2026-01-09
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json
import numpy as np

# Internal service imports
from .churn_prediction_engine import (
    ChurnPredictionEngine,
    ChurnPrediction,
    ChurnRiskTier
)
from .churn_intervention_orchestrator import (
    InterventionOrchestrator,
    InterventionExecution,
    InterventionStatus
)
from .memory_service import MemoryService
from .lead_lifecycle import LeadLifecycleTracker
from .behavioral_triggers import BehavioralTriggerEngine
from .lead_scorer import LeadScorer
from .reengagement_engine import ReengagementEngine
from .ghl_service import GHLService

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ChurnPredictionRequest:
    """Request structure for churn predictions"""
    lead_ids: List[str]
    force_refresh: bool = False
    include_recommendations: bool = True
    trigger_interventions: bool = True

@dataclass
class ChurnPredictionResponse:
    """Response structure for churn predictions"""
    predictions: Dict[str, ChurnPrediction]
    high_risk_leads: List[str]
    triggered_interventions: Dict[str, List[InterventionExecution]]
    processing_summary: Dict[str, Any]
    errors: List[str]

@dataclass
class ChurnSystemHealth:
    """System health status for churn prediction components"""
    prediction_engine_status: str
    intervention_orchestrator_status: str
    service_dependencies: Dict[str, str]
    last_prediction_run: Optional[datetime]
    total_predictions_today: int
    intervention_success_rate: float
    system_alerts: List[str]

class ChurnIntegrationService:
    """
    Primary integration service for churn prediction and intervention system

    This service provides a high-level interface for churn prediction while
    managing the complexity of coordinating multiple underlying services.
    """

    def __init__(self,
                 memory_service: MemoryService,
                 lifecycle_tracker: LeadLifecycleTracker,
                 behavioral_engine: BehavioralTriggerEngine,
                 lead_scorer: LeadScorer,
                 reengagement_engine: ReengagementEngine,
                 ghl_service: GHLService,
                 model_path: Optional[str] = None):

        # Store service dependencies
        self.memory_service = memory_service
        self.lifecycle_tracker = lifecycle_tracker
        self.behavioral_engine = behavioral_engine
        self.lead_scorer = lead_scorer
        self.reengagement_engine = reengagement_engine
        self.ghl_service = ghl_service

        # Initialize core churn components
        self.prediction_engine = ChurnPredictionEngine(
            memory_service=memory_service,
            lifecycle_tracker=lifecycle_tracker,
            behavioral_engine=behavioral_engine,
            lead_scorer=lead_scorer,
            model_path=model_path
        )

        self.intervention_orchestrator = InterventionOrchestrator(
            reengagement_engine=reengagement_engine,
            memory_service=memory_service,
            ghl_service=ghl_service
        )

        # Service configuration
        self.config = {
            'batch_size': 50,  # Max leads per batch prediction
            'prediction_cache_ttl_hours': 4,
            'auto_intervention_enabled': True,
            'critical_risk_threshold': 80.0,
            'high_risk_threshold': 60.0,
            'max_daily_predictions': 1000
        }

        # Runtime tracking
        self._daily_prediction_count = 0
        self._last_reset_date = datetime.now().date()
        self._system_health = ChurnSystemHealth(
            prediction_engine_status="initialized",
            intervention_orchestrator_status="initialized",
            service_dependencies={},
            last_prediction_run=None,
            total_predictions_today=0,
            intervention_success_rate=0.0,
            system_alerts=[]
        )

        self.logger = logging.getLogger(__name__ + '.ChurnIntegrationService')
        self.logger.info("ChurnIntegrationService initialized successfully")

    async def predict_churn_risk(self, request: ChurnPredictionRequest) -> ChurnPredictionResponse:
        """
        Main entry point for churn prediction requests

        Args:
            request: ChurnPredictionRequest with lead IDs and options

        Returns:
            ChurnPredictionResponse with predictions and triggered interventions
        """
        start_time = datetime.now()
        self.logger.info(f"Processing churn prediction request for {len(request.lead_ids)} leads")

        try:
            # Validate request
            await self._validate_prediction_request(request)

            # Process predictions in batches if needed
            all_predictions = {}
            all_interventions = {}
            errors = []

            for batch_leads in self._batch_lead_ids(request.lead_ids):
                try:
                    # Generate predictions for batch
                    batch_predictions = await self._process_prediction_batch(batch_leads, request.force_refresh)
                    all_predictions.update(batch_predictions)

                    # Trigger interventions if enabled
                    if request.trigger_interventions and self.config['auto_intervention_enabled']:
                        batch_interventions = await self._trigger_interventions_for_batch(batch_predictions)
                        all_interventions.update(batch_interventions)

                except Exception as e:
                    self.logger.error(f"Error processing batch: {str(e)}")
                    errors.append(f"Batch processing error: {str(e)}")

            # Identify high-risk leads
            high_risk_leads = self._identify_high_risk_leads(all_predictions)

            # Generate processing summary
            processing_summary = await self._generate_processing_summary(
                all_predictions, all_interventions, start_time, errors
            )

            # Update system health
            await self._update_system_health(len(request.lead_ids), len(errors))

            response = ChurnPredictionResponse(
                predictions=all_predictions,
                high_risk_leads=high_risk_leads,
                triggered_interventions=all_interventions,
                processing_summary=processing_summary,
                errors=errors
            )

            self.logger.info(f"Churn prediction completed: {len(all_predictions)} predictions, "
                           f"{len(high_risk_leads)} high-risk leads identified")

            return response

        except Exception as e:
            self.logger.error(f"Critical error in churn prediction: {str(e)}")
            return self._create_error_response(str(e))

    async def get_high_risk_dashboard_data(self, days_back: int = 7) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for high-risk leads

        Args:
            days_back: Number of days to include in analysis

        Returns:
            Dict containing dashboard metrics and visualizations data
        """
        try:
            self.logger.info(f"Generating high-risk dashboard data for {days_back} days")

            # Get recent predictions for active leads
            active_leads = await self._get_active_lead_ids()
            request = ChurnPredictionRequest(
                lead_ids=active_leads[:100],  # Limit for performance
                force_refresh=False,
                trigger_interventions=False
            )

            prediction_response = await self.predict_churn_risk(request)

            # Calculate dashboard metrics
            dashboard_data = {
                'summary_metrics': await self._calculate_summary_metrics(prediction_response.predictions),
                'risk_distribution': self._calculate_risk_distribution(prediction_response.predictions),
                'trend_data': await self._get_trend_data(days_back),
                'intervention_analytics': await self.intervention_orchestrator.get_intervention_analytics(days_back),
                'high_priority_leads': self._get_high_priority_leads(prediction_response.predictions),
                'system_health': asdict(self._system_health),
                'last_updated': datetime.now().isoformat()
            }

            return dashboard_data

        except Exception as e:
            self.logger.error(f"Error generating dashboard data: {str(e)}")
            return self._create_dashboard_error_response(str(e))

    async def execute_manual_intervention(self, lead_id: str, intervention_type: str,
                                        urgency_override: Optional[str] = None) -> Dict[str, Any]:
        """
        Manually trigger intervention for specific lead

        Args:
            lead_id: Target lead ID
            intervention_type: Type of intervention to execute
            urgency_override: Override urgency level

        Returns:
            Dict with execution results
        """
        try:
            self.logger.info(f"Manual intervention requested: {intervention_type} for lead {lead_id}")

            # Get current churn prediction
            prediction_request = ChurnPredictionRequest(
                lead_ids=[lead_id],
                force_refresh=True,
                trigger_interventions=False
            )

            prediction_response = await self.predict_churn_risk(prediction_request)

            if lead_id not in prediction_response.predictions:
                return {'success': False, 'error': 'Could not generate prediction for lead'}

            prediction = prediction_response.predictions[lead_id]

            # Override urgency if specified
            if urgency_override:
                prediction.intervention_urgency = urgency_override

            # Create manual intervention execution
            intervention = InterventionExecution(
                execution_id=f"manual_{lead_id}_{intervention_type}_{int(datetime.now().timestamp())}",
                lead_id=lead_id,
                intervention_type=intervention_type,
                trigger_prediction=prediction,
                scheduled_time=datetime.now(),
                personalization_data=await self.intervention_orchestrator._prepare_personalization_data(lead_id, prediction)
            )

            # Execute intervention
            success = await self.intervention_orchestrator._execute_intervention(intervention)

            result = {
                'success': success,
                'intervention_id': intervention.execution_id,
                'lead_id': lead_id,
                'intervention_type': intervention_type,
                'executed_at': datetime.now().isoformat(),
                'prediction_context': {
                    'risk_score': prediction.risk_score_14d,
                    'risk_tier': prediction.risk_tier.value,
                    'confidence': prediction.confidence
                }
            }

            if success:
                self.logger.info(f"Manual intervention executed successfully: {intervention.execution_id}")
            else:
                self.logger.warning(f"Manual intervention failed: {intervention.execution_id}")

            return result

        except Exception as e:
            self.logger.error(f"Error executing manual intervention: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def update_churn_model_training_data(self, lead_id: str, actual_outcome: str,
                                             outcome_date: datetime) -> Dict[str, bool]:
        """
        Update model training data with actual churn outcomes

        Args:
            lead_id: Lead identifier
            actual_outcome: 'churned' or 'retained'
            outcome_date: When the outcome was observed

        Returns:
            Dict indicating success/failure
        """
        try:
            self.logger.info(f"Recording churn outcome: {lead_id} -> {actual_outcome}")

            # Convert outcome to boolean
            actually_churned = actual_outcome.lower() == 'churned'

            # Update prediction engine training data
            await self.prediction_engine.update_model_training_data(lead_id, actually_churned)

            # Log for analytics
            training_update = {
                'lead_id': lead_id,
                'actual_outcome': actual_outcome,
                'actually_churned': actually_churned,
                'outcome_date': outcome_date.isoformat(),
                'recorded_at': datetime.now().isoformat()
            }

            self.logger.info(f"Training data updated: {json.dumps(training_update)}")

            return {'success': True, 'recorded_outcome': actually_churned}

        except Exception as e:
            self.logger.error(f"Error updating training data: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def get_system_health(self) -> ChurnSystemHealth:
        """Get current system health status"""
        try:
            # Update service dependency status
            service_health = {}

            # Test each service dependency
            services = [
                ('memory_service', self.memory_service),
                ('lifecycle_tracker', self.lifecycle_tracker),
                ('behavioral_engine', self.behavioral_engine),
                ('lead_scorer', self.lead_scorer),
                ('reengagement_engine', self.reengagement_engine),
                ('ghl_service', self.ghl_service)
            ]

            for service_name, service in services:
                try:
                    # Basic health check (method availability)
                    if hasattr(service, 'health_check'):
                        health = await service.health_check()
                        service_health[service_name] = 'healthy' if health else 'unhealthy'
                    else:
                        service_health[service_name] = 'available'
                except Exception as e:
                    service_health[service_name] = f'error: {str(e)[:50]}'

            # Update system health
            self._system_health.service_dependencies = service_health

            # Check for system alerts
            alerts = []
            if self._daily_prediction_count > self.config['max_daily_predictions'] * 0.9:
                alerts.append("Approaching daily prediction limit")

            unhealthy_services = [name for name, status in service_health.items()
                                if 'error' in status or status == 'unhealthy']
            if unhealthy_services:
                alerts.append(f"Service issues: {', '.join(unhealthy_services)}")

            self._system_health.system_alerts = alerts

            return self._system_health

        except Exception as e:
            self.logger.error(f"Error checking system health: {str(e)}")
            return self._system_health

    async def _validate_prediction_request(self, request: ChurnPredictionRequest):
        """Validate prediction request parameters"""
        if not request.lead_ids:
            raise ValueError("Lead IDs list cannot be empty")

        if len(request.lead_ids) > 200:
            raise ValueError("Request exceeds maximum batch size of 200 leads")

        # Check daily limits
        if self._daily_prediction_count + len(request.lead_ids) > self.config['max_daily_predictions']:
            raise ValueError("Request would exceed daily prediction limit")

        # Reset daily counter if needed
        current_date = datetime.now().date()
        if current_date > self._last_reset_date:
            self._daily_prediction_count = 0
            self._last_reset_date = current_date

    def _batch_lead_ids(self, lead_ids: List[str]) -> List[List[str]]:
        """Split lead IDs into processing batches"""
        batch_size = self.config['batch_size']
        return [lead_ids[i:i + batch_size] for i in range(0, len(lead_ids), batch_size)]

    async def _process_prediction_batch(self, lead_ids: List[str], force_refresh: bool) -> Dict[str, ChurnPrediction]:
        """Process churn predictions for a batch of leads"""
        predictions = {}

        for lead_id in lead_ids:
            try:
                prediction = await self.prediction_engine.predict_churn_risk(lead_id, force_refresh)
                predictions[lead_id] = prediction
                self._daily_prediction_count += 1

            except Exception as e:
                self.logger.error(f"Error predicting churn for lead {lead_id}: {str(e)}")
                # Continue processing other leads

        return predictions

    async def _trigger_interventions_for_batch(self, predictions: Dict[str, ChurnPrediction]) -> Dict[str, List[InterventionExecution]]:
        """Trigger interventions for batch predictions"""
        try:
            return await self.intervention_orchestrator.process_churn_predictions(predictions)
        except Exception as e:
            self.logger.error(f"Error triggering interventions: {str(e)}")
            return {}

    def _identify_high_risk_leads(self, predictions: Dict[str, ChurnPrediction]) -> List[str]:
        """Identify high-risk leads from predictions"""
        high_risk_leads = []

        for lead_id, prediction in predictions.items():
            if (prediction.risk_tier in [ChurnRiskTier.CRITICAL, ChurnRiskTier.HIGH] or
                prediction.risk_score_14d >= self.config['high_risk_threshold']):
                high_risk_leads.append(lead_id)

        # Sort by risk score (descending)
        high_risk_leads.sort(key=lambda lid: predictions[lid].risk_score_14d, reverse=True)

        return high_risk_leads

    async def _generate_processing_summary(self, predictions: Dict[str, ChurnPrediction],
                                         interventions: Dict[str, List[InterventionExecution]],
                                         start_time: datetime, errors: List[str]) -> Dict[str, Any]:
        """Generate processing summary statistics"""
        processing_time = (datetime.now() - start_time).total_seconds()

        # Risk distribution
        risk_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        confidence_scores = []

        for prediction in predictions.values():
            risk_counts[prediction.risk_tier.value] += 1
            confidence_scores.append(prediction.confidence)

        # Intervention summary
        total_interventions = sum(len(intervention_list) for intervention_list in interventions.values())

        return {
            'total_predictions': len(predictions),
            'processing_time_seconds': processing_time,
            'risk_distribution': risk_counts,
            'average_confidence': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
            'total_interventions_triggered': total_interventions,
            'leads_with_interventions': len(interventions),
            'error_count': len(errors),
            'success_rate': (len(predictions) / (len(predictions) + len(errors))) * 100 if (len(predictions) + len(errors)) > 0 else 0
        }

    async def _update_system_health(self, predictions_processed: int, error_count: int):
        """Update system health metrics"""
        self._system_health.last_prediction_run = datetime.now()
        self._system_health.total_predictions_today = self._daily_prediction_count

        # Update engine status
        if error_count == 0:
            self._system_health.prediction_engine_status = "healthy"
        elif error_count < predictions_processed * 0.1:  # < 10% error rate
            self._system_health.prediction_engine_status = "warning"
        else:
            self._system_health.prediction_engine_status = "error"

        # Update intervention success rate
        try:
            analytics = await self.intervention_orchestrator.get_intervention_analytics(1)
            self._system_health.intervention_success_rate = analytics.get('success_rate', 0.0)
            self._system_health.intervention_orchestrator_status = "healthy"
        except Exception:
            self._system_health.intervention_orchestrator_status = "error"

    async def _get_active_lead_ids(self) -> List[str]:
        """Get list of active lead IDs from the system"""
        try:
            # This would integrate with your lead management system
            # For demo, generating sample lead IDs
            return [f'LEAD_{i:04d}' for i in range(1, 201)]
        except Exception as e:
            self.logger.error(f"Error getting active leads: {str(e)}")
            return []

    async def _calculate_summary_metrics(self, predictions: Dict[str, ChurnPrediction]) -> Dict[str, Any]:
        """Calculate summary metrics for dashboard"""
        if not predictions:
            return {'total_leads': 0, 'critical_risk': 0, 'high_risk': 0, 'average_risk': 0}

        total_leads = len(predictions)
        critical_risk = len([p for p in predictions.values() if p.risk_tier == ChurnRiskTier.CRITICAL])
        high_risk = len([p for p in predictions.values() if p.risk_tier == ChurnRiskTier.HIGH])
        average_risk = sum(p.risk_score_14d for p in predictions.values()) / total_leads

        return {
            'total_leads': total_leads,
            'critical_risk': critical_risk,
            'high_risk': high_risk,
            'average_risk': average_risk,
            'churn_prevention_target': critical_risk + high_risk
        }

    def _calculate_risk_distribution(self, predictions: Dict[str, ChurnPrediction]) -> Dict[str, int]:
        """Calculate risk distribution for dashboard charts"""
        distribution = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}

        for prediction in predictions.values():
            distribution[prediction.risk_tier.value] += 1

        return distribution

    async def _get_trend_data(self, days_back: int) -> Dict[str, List]:
        """Get trend data for dashboard (sample implementation)"""
        # In production, this would query historical data
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days_back, 0, -1)]

        # Sample trend data
        critical_trend = [np.random.randint(2, 8) for _ in dates]
        high_trend = [np.random.randint(5, 15) for _ in dates]

        return {
            'dates': dates,
            'critical_risk_trend': critical_trend,
            'high_risk_trend': high_trend
        }

    def _get_high_priority_leads(self, predictions: Dict[str, ChurnPrediction]) -> List[Dict[str, Any]]:
        """Get high-priority leads for dashboard queue"""
        high_priority = []

        for lead_id, prediction in predictions.items():
            if prediction.risk_tier in [ChurnRiskTier.CRITICAL, ChurnRiskTier.HIGH]:
                high_priority.append({
                    'lead_id': lead_id,
                    'risk_score': prediction.risk_score_14d,
                    'risk_tier': prediction.risk_tier.value,
                    'confidence': prediction.confidence,
                    'urgency': prediction.intervention_urgency,
                    'top_risk_factor': prediction.top_risk_factors[0][0] if prediction.top_risk_factors else 'unknown',
                    'recommendations': prediction.recommended_actions[:2]
                })

        # Sort by risk score
        high_priority.sort(key=lambda x: x['risk_score'], reverse=True)

        return high_priority[:20]  # Top 20

    def _create_error_response(self, error_message: str) -> ChurnPredictionResponse:
        """Create error response for failed predictions"""
        return ChurnPredictionResponse(
            predictions={},
            high_risk_leads=[],
            triggered_interventions={},
            processing_summary={'error': error_message},
            errors=[error_message]
        )

    def _create_dashboard_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response for dashboard data"""
        return {
            'error': error_message,
            'summary_metrics': {'total_leads': 0, 'critical_risk': 0, 'high_risk': 0, 'average_risk': 0},
            'risk_distribution': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
            'last_updated': datetime.now().isoformat()
        }

    # Public API Methods for External Integration

    async def predict_single_lead_churn(self, lead_id: str) -> Optional[ChurnPrediction]:
        """Simplified API for single lead prediction"""
        try:
            request = ChurnPredictionRequest(
                lead_ids=[lead_id],
                force_refresh=False,
                trigger_interventions=True
            )

            response = await self.predict_churn_risk(request)
            return response.predictions.get(lead_id)

        except Exception as e:
            self.logger.error(f"Error predicting single lead churn: {str(e)}")
            return None

    async def get_intervention_status(self, lead_id: str) -> Dict[str, Any]:
        """Get current intervention status for a lead"""
        try:
            # Get active interventions for lead
            active_interventions = self.intervention_orchestrator._active_interventions.get(lead_id, [])

            status = {
                'lead_id': lead_id,
                'active_interventions': len(active_interventions),
                'pending_interventions': len([i for i in active_interventions if i.status == InterventionStatus.PENDING]),
                'completed_interventions': len([i for i in active_interventions if i.status == InterventionStatus.COMPLETED]),
                'last_intervention': None
            }

            if active_interventions:
                latest = max(active_interventions, key=lambda x: x.scheduled_time)
                status['last_intervention'] = {
                    'type': latest.intervention_type.value,
                    'status': latest.status.value,
                    'scheduled_time': latest.scheduled_time.isoformat()
                }

            return status

        except Exception as e:
            self.logger.error(f"Error getting intervention status: {str(e)}")
            return {'lead_id': lead_id, 'error': str(e)}

# Example usage and testing
if __name__ == "__main__":
    async def test_integration_service():
        """Test the integration service"""
        from unittest.mock import AsyncMock

        # Mock all service dependencies
        memory_service = AsyncMock()
        lifecycle_tracker = AsyncMock()
        behavioral_engine = AsyncMock()
        lead_scorer = AsyncMock()
        reengagement_engine = AsyncMock()
        ghl_service = AsyncMock()

        # Initialize integration service
        integration_service = ChurnIntegrationService(
            memory_service=memory_service,
            lifecycle_tracker=lifecycle_tracker,
            behavioral_engine=behavioral_engine,
            lead_scorer=lead_scorer,
            reengagement_engine=reengagement_engine,
            ghl_service=ghl_service
        )

        # Test prediction request
        request = ChurnPredictionRequest(
            lead_ids=['LEAD_001', 'LEAD_002', 'LEAD_003'],
            force_refresh=True,
            trigger_interventions=True
        )

        response = await integration_service.predict_churn_risk(request)

        print(f"Integration Service Test Results:")
        print(f"Predictions generated: {len(response.predictions)}")
        print(f"High-risk leads: {len(response.high_risk_leads)}")
        print(f"Triggered interventions: {len(response.triggered_interventions)}")
        print(f"Processing summary: {response.processing_summary}")

        # Test system health
        health = await integration_service.get_system_health()
        print(f"System Health: {health.prediction_engine_status}")

    import asyncio
    import numpy as np
    asyncio.run(test_integration_service())