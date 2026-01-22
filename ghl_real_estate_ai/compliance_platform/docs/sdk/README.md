# Compliance Platform Python SDK

The Compliance SDK provides a Pythonic interface to the AI Compliance Platform, allowing developers to integrate regulatory tracking and risk assessment directly into their AI pipelines.

## Installation

```bash
pip install httpx
```

## Quick Start

### 1. Initialize the Client

```python
import asyncio
from compliance_client import ComplianceClient

async def main():
    client = ComplianceClient(base_url="http://localhost:8000")
    
    # Check health
    health = await client.check_health()
    print(f"System Status: {health['status']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Register and Assess a Model

```python
async def integrate_model():
    client = ComplianceClient()
    
    # Register model
    model = await client.register_model({
        "name": "Market Sentiment Engine",
        "version": "2.0.1",
        "description": "Analyzes social media for real estate trends",
        "model_type": "nlp",
        "provider": "anthropic",
        "deployment_location": "cloud",
        "intended_use": "Market research",
        "applicable_regulations": ["eu_ai_act", "gdpr"]
    })
    
    model_id = model["id"]
    print(f"Registered model: {model_id}")
    
    # Trigger assessment
    assessment = await client.assess_model(model_id)
    print(f"Compliance Score: {assessment['compliance_score']}")
    print(f"Risk Level: {assessment['risk_level']}")

    # Check for violations
    violations = await client.get_violations(model_id)
    for v in violations:
        print(f"Violation: {v['title']} ({v['severity']})")
```

### 3. Generate Reports

```python
async def fetch_audit_report():
    client = ComplianceClient()
    
    # Trigger generation
    result = await client.generate_report(report_type="executive", period_days=90)
    report_id = result["report_id"]
    
    # Poll for completion (simplified)
    import time
    while True:
        report = await client.get_report(report_id)
        if report["status"] == "completed":
            print(f"Report Summary: {report['report']['overall_score']['overall_score']}")
            break
        await asyncio.sleep(2)
```

## Error Handling

The SDK raises `ComplianceAPIError` for network issues or non-2xx API responses.

```python
try:
    await client.get_model("invalid-id")
except ComplianceAPIError as e:
    print(f"Error: {e.message}")
    print(f"Status: {e.status_code}")
```
