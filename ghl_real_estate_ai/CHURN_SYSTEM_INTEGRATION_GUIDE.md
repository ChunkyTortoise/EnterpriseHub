# Churn Prediction System - Integration Guide

## Overview

The Lead Churn Prediction & Early Warning System provides comprehensive churn risk assessment and automated intervention capabilities for real estate lead management. This guide covers integration, configuration, and operational procedures.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Churn Prediction System                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌──────────────────────────────────┐   │
│  │ Feature         │    │ Prediction Engine                │   │
│  │ Extractor       │───▶│ • Multi-horizon ML models       │   │
│  │ • 26 features   │    │ • Risk scoring (0-100)          │   │
│  │ • Real-time     │    │ • Confidence estimation         │   │
│  └─────────────────┘    └──────────────────────────────────┘   │
│           │                            │                       │
│           ▼                            ▼                       │
│  ┌─────────────────┐    ┌──────────────────────────────────┐   │
│  │ Risk            │    │ Intervention Orchestrator        │   │
│  │ Stratifier      │───▶│ • 8 intervention types          │   │
│  │ • 4 risk tiers  │    │ • Multi-channel execution       │   │
│  │ • Urgency calc  │    │ • Rate limiting & scheduling    │   │
│  └─────────────────┘    └──────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Integration Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  Memory    │ Lifecycle  │ Behavioral │ Lead      │ GHL         │
│  Service   │ Tracker    │ Engine     │ Scorer    │ Service     │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install scikit-learn pandas numpy plotly streamlit

# Ensure all existing services are available
# - MemoryService
# - LeadLifecycleTracker
# - BehavioralTriggerEngine
# - LeadScorer
# - ReengagementEngine
# - GHLService
```

### 2. Basic Integration

```python
from services.churn_integration_service import ChurnIntegrationService, ChurnPredictionRequest

# Initialize with existing services
churn_service = ChurnIntegrationService(
    memory_service=your_memory_service,
    lifecycle_tracker=your_lifecycle_tracker,
    behavioral_engine=your_behavioral_engine,
    lead_scorer=your_lead_scorer,
    reengagement_engine=your_reengagement_engine,
    ghl_service=your_ghl_service
)

# Generate predictions for leads
request = ChurnPredictionRequest(
    lead_ids=['LEAD_001', 'LEAD_002'],
    trigger_interventions=True
)

response = await churn_service.predict_churn_risk(request)
print(f"High-risk leads: {response.high_risk_leads}")
```

### 3. Dashboard Integration

```python
# Add to your Streamlit app
from streamlit_demo.components.churn_early_warning_dashboard import ChurnEarlyWarningDashboard

# In your main app
if st.sidebar.selectbox("Choose Dashboard", options=["Main", "Churn Early Warning"]) == "Churn Early Warning":
    dashboard = ChurnEarlyWarningDashboard()
    dashboard.render_dashboard()
```

## Core Components

### 1. ChurnPredictionEngine

**Purpose**: Multi-horizon churn risk prediction with explainable AI

**Key Features**:
- 26 behavioral features extracted in real-time
- ML models for 7, 14, and 30-day predictions
- Confidence scoring and feature importance
- Graceful degradation when data unavailable

**Configuration**:
```python
# Optional: Provide trained model path
engine = ChurnPredictionEngine(
    memory_service=memory_service,
    lifecycle_tracker=lifecycle_tracker,
    behavioral_engine=behavioral_engine,
    lead_scorer=lead_scorer,
    model_path="/path/to/trained_models.pkl"  # Optional
)
```

### 2. InterventionOrchestrator

**Purpose**: Automated intervention execution with multi-channel support

**Key Features**:
- 8 intervention types with escalation logic
- Rate limiting (max 3 per lead per day)
- Multi-channel execution (email, SMS, phone, GHL workflows)
- A/B testing support
- Comprehensive tracking

**Configuration**:
```python
# Intervention configurations are predefined but can be customized
orchestrator._intervention_configs[InterventionType.EMAIL_REENGAGEMENT].max_frequency = timedelta(hours=12)
```

### 3. ChurnIntegrationService

**Purpose**: Unified API for churn prediction and intervention management

**Key Features**:
- Batch processing (up to 200 leads)
- System health monitoring
- Manual intervention triggers
- Dashboard data aggregation
- Error handling and resilience

## Integration Points

### Required Service Interfaces

Your existing services must implement these methods:

#### MemoryService
```python
async def get_lead_context(self, lead_id: str) -> Dict[str, Any]
async def get_conversation_history(self, lead_id: str, days: int) -> List[Dict]
async def get_last_interaction(self, lead_id: str) -> Dict[str, Any]
```

#### LeadLifecycleTracker
```python
async def get_current_stage(self, lead_id: str) -> str
async def get_stage_history(self, lead_id: str) -> List[Dict]
async def get_progression_metrics(self, lead_id: str) -> Dict[str, float]
```

#### BehavioralTriggerEngine
```python
async def get_recent_events(self, lead_id: str, days: int) -> List[Dict]
async def calculate_engagement_metrics(self, lead_id: str) -> Dict[str, float]
async def analyze_patterns(self, lead_id: str) -> Dict[str, Any]
```

#### LeadScorer
```python
async def get_current_score(self, lead_id: str) -> float
async def get_score_history(self, lead_id: str, days: int) -> List[Dict]
async def get_qualification_factors(self, lead_id: str) -> Dict[str, Any]
```

#### ReengagementEngine
```python
async def trigger_reengagement_campaign(self, lead_id: str, campaign_type: str,
                                       personalization_data: Dict, urgency_level: str) -> Dict[str, Any]
```

#### GHLService
```python
async def trigger_workflow(self, contact_id: str, workflow_id: str,
                         custom_data: Dict) -> Dict[str, Any]
```

### Service Adapter Pattern

If your services have different interfaces, create adapters:

```python
class MyMemoryServiceAdapter:
    def __init__(self, my_existing_service):
        self.service = my_existing_service

    async def get_lead_context(self, lead_id: str):
        # Adapt your service's interface
        raw_data = await self.service.fetch_lead_data(lead_id)
        return {
            'name': raw_data['contact_name'],
            'preferences': raw_data['search_criteria']
        }
```

## Configuration

### Environment Variables

```bash
# Optional: Configure prediction limits
CHURN_MAX_DAILY_PREDICTIONS=1000
CHURN_BATCH_SIZE=50
CHURN_CACHE_TTL_HOURS=4

# Optional: Configure intervention limits
CHURN_MAX_DAILY_INTERVENTIONS_PER_LEAD=3
CHURN_AUTO_INTERVENTIONS_ENABLED=true

# Optional: Risk thresholds
CHURN_CRITICAL_THRESHOLD=80.0
CHURN_HIGH_THRESHOLD=60.0
```

### Risk Thresholds

Customize risk tier thresholds based on your business requirements:

```python
churn_service.config.update({
    'critical_risk_threshold': 85.0,  # Default: 80.0
    'high_risk_threshold': 65.0,      # Default: 60.0
    'max_daily_predictions': 2000     # Default: 1000
})
```

## API Reference

### Core Prediction API

```python
# Single lead prediction
prediction = await churn_service.predict_single_lead_churn('LEAD_123')
print(f"Risk Score: {prediction.risk_score_14d}%")
print(f"Risk Tier: {prediction.risk_tier.value}")

# Batch prediction
request = ChurnPredictionRequest(
    lead_ids=['LEAD_001', 'LEAD_002', 'LEAD_003'],
    force_refresh=False,
    trigger_interventions=True
)
response = await churn_service.predict_churn_risk(request)

# Dashboard data
dashboard_data = await churn_service.get_high_risk_dashboard_data(days_back=7)
```

### Manual Interventions

```python
# Trigger manual intervention
result = await churn_service.execute_manual_intervention(
    lead_id='LEAD_123',
    intervention_type='phone_callback',
    urgency_override='immediate'
)

# Check intervention status
status = await churn_service.get_intervention_status('LEAD_123')
print(f"Active interventions: {status['active_interventions']}")
```

### System Monitoring

```python
# Check system health
health = await churn_service.get_system_health()
print(f"Prediction engine: {health.prediction_engine_status}")
print(f"Daily predictions: {health.total_predictions_today}")

# Record actual outcomes for model improvement
await churn_service.update_churn_model_training_data(
    lead_id='LEAD_123',
    actual_outcome='retained',  # or 'churned'
    outcome_date=datetime.now()
)
```

## Operational Procedures

### Daily Operations

1. **Morning Health Check**
   ```bash
   python scripts/churn_health_check.py
   ```

2. **High-Risk Lead Review**
   - Check Early Warning Dashboard
   - Review critical alerts
   - Manually trigger interventions if needed

3. **Performance Monitoring**
   - Monitor intervention success rates
   - Review agent workload distribution
   - Check prediction accuracy

### Weekly Operations

1. **Model Performance Review**
   - Analyze prediction accuracy
   - Review false positive/negative rates
   - Update risk thresholds if needed

2. **Intervention Optimization**
   - A/B test new templates
   - Analyze channel effectiveness
   - Adjust timing and frequency

3. **System Optimization**
   - Review batch processing performance
   - Optimize feature extraction
   - Clean up prediction cache

### Monthly Operations

1. **Model Retraining**
   - Collect actual churn outcomes
   - Retrain prediction models
   - Deploy updated models

2. **Business Impact Analysis**
   - Calculate churn prevention ROI
   - Measure revenue impact
   - Report to stakeholders

## Troubleshooting

### Common Issues

#### 1. High False Positive Rate

**Symptoms**: Too many leads marked as high-risk who don't actually churn

**Solutions**:
- Increase risk thresholds
- Review feature importance
- Check data quality
- Retrain models with more recent data

```python
# Adjust thresholds
churn_service.config['critical_risk_threshold'] = 85.0
churn_service.config['high_risk_threshold'] = 65.0
```

#### 2. Service Integration Failures

**Symptoms**: Errors in feature extraction or intervention execution

**Solutions**:
- Check service health
- Verify API interfaces
- Review error logs
- Implement circuit breakers

```python
# Check service health
health = await churn_service.get_system_health()
print("Service Status:")
for service, status in health.service_dependencies.items():
    print(f"  {service}: {status}")
```

#### 3. Performance Issues

**Symptoms**: Slow prediction generation or timeouts

**Solutions**:
- Reduce batch sizes
- Implement async processing
- Add caching layers
- Optimize feature extraction

```python
# Reduce batch size
churn_service.config['batch_size'] = 25  # Default: 50

# Enable prediction caching
# Predictions are automatically cached for 4 hours
```

#### 4. Intervention Rate Limiting

**Symptoms**: Important interventions not being triggered

**Solutions**:
- Review rate limiting rules
- Adjust intervention priorities
- Implement manual override capability

```python
# Check intervention status
status = await churn_service.get_intervention_status('LEAD_123')
if status['pending_interventions'] == 0:
    # Manually trigger if needed
    await churn_service.execute_manual_intervention('LEAD_123', 'phone_callback')
```

### Error Handling

The system includes comprehensive error handling:

- **Service Failures**: Graceful degradation with default values
- **Model Errors**: Fallback to rule-based predictions
- **Rate Limiting**: Queue management and prioritization
- **Data Quality**: Validation and sanitization

### Monitoring and Alerts

Set up monitoring for:

- Prediction accuracy drift
- Intervention success rates
- System performance metrics
- Service dependency health

```python
# Custom health checks
async def custom_health_check():
    health = await churn_service.get_system_health()

    if health.prediction_engine_status == "error":
        # Alert operations team
        send_alert("Churn prediction engine failure")

    if health.intervention_success_rate < 0.5:
        # Alert business team
        send_alert("Low intervention success rate")
```

## Best Practices

### 1. Data Quality

- Ensure consistent data formats across services
- Implement data validation at ingestion points
- Monitor for missing or anomalous data
- Regular data quality audits

### 2. Model Management

- Version control for model artifacts
- A/B testing for model updates
- Gradual rollout of new models
- Rollback procedures for failed deployments

### 3. Intervention Strategy

- Start with conservative intervention rules
- Test templates with small user groups
- Monitor for user fatigue and unsubscribes
- Personalize based on lead characteristics

### 4. Performance Optimization

- Use async processing for all I/O operations
- Implement caching at multiple levels
- Monitor and optimize database queries
- Regular performance profiling

### 5. Security and Privacy

- Encrypt prediction data in transit and at rest
- Implement access controls for intervention data
- Regular security audits
- Compliance with data protection regulations

## Support

### Documentation

- [API Reference](./api_reference.md)
- [Model Documentation](./model_docs.md)
- [Intervention Guide](./intervention_guide.md)
- [Dashboard Manual](./dashboard_manual.md)

### Monitoring Dashboards

- System Health: `/dashboard/churn/health`
- Performance Metrics: `/dashboard/churn/performance`
- Business Impact: `/dashboard/churn/business`

### Team Contacts

- **Technical Issues**: DevOps Team
- **Model Performance**: Data Science Team
- **Business Rules**: Product Team
- **Emergency Escalation**: On-call Engineer

---

*Last Updated: 2026-01-09*
*Version: 1.0.0*
*Status: Production Ready*