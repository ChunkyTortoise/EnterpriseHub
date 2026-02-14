# GHL MCP Server Usage Examples

Real-world usage examples demonstrating integration with existing EnterpriseHub services.

## Table of Contents
- [Natural Language Operations](#natural-language-operations)
- [Integration with Predictive Lead Scorer](#integration-with-predictive-lead-scorer)
- [Integration with Claude Enhanced Scorer](#integration-with-claude-enhanced-scorer)
- [Integration with GHL Sync Service](#integration-with-ghl-sync-service)
- [Automation Scripts](#automation-scripts)
- [CLI Usage](#cli-usage)

---

## Natural Language Operations

### Basic Contact Management

**Create Contact with Natural Language:**

```
User: "Create a contact for John Smith with email john@example.com and phone +15125551234. Tag him as Hot Lead and Buyer."

MCP Response:
{
  "id": "contact_abc123",
  "name": "John Smith",
  "email": "john@example.com",
  "phone": "+15125551234",
  "tags": ["Hot Lead", "Buyer"],
  "locationId": "loc_xyz789"
}
```

**Search Contacts:**

```
User: "Find all contacts tagged as Hot Lead who were created this week"

MCP Response:
[
  {"id": "abc123", "name": "John Smith", "tags": ["Hot Lead"]},
  {"id": "def456", "name": "Jane Doe", "tags": ["Hot Lead", "Seller"]},
  ...
]
```

**Update Lead Score:**

```
User: "Update lead score for contact abc123 to 87 based on high engagement and qualified budget"

MCP Response:
{
  "id": "abc123",
  "score": 87,
  "tags": ["Hot Lead", "AI_Scored_Hot"],
  "custom_fields": {
    "lead_score": "87",
    "budget": "qualified",
    "engagement_level": "high"
  },
  "workflow_triggered": "high_value_lead_workflow"
}
```

---

## Integration with Predictive Lead Scorer

### Example: ML-Powered Lead Scoring Pipeline

```python
#!/usr/bin/env python3
"""
ML-powered lead scoring with automatic GHL sync.

Demonstrates integration between:
- services/predictive_lead_scorer.py (ML scoring)
- .claude/mcp-servers/ghl/server.py (GHL sync)
"""

import asyncio
from ghl_real_estate_ai.services.predictive_lead_scorer import PredictiveLeadScorer
from ghl_real_estate_ai.services.ghl_client import GHLClient

# MCP server import
import sys
sys.path.insert(0, '.claude/mcp-servers/ghl/')
from server import GHLMCPServer


async def score_and_sync_lead(contact_id: str, lead_context: dict):
    """
    Score lead with ML and sync to GHL via MCP server.

    Args:
        contact_id: GHL contact ID
        lead_context: Lead data for scoring

    Returns:
        Combined ML score + GHL sync result
    """
    # Step 1: Run ML predictive scoring
    ml_scorer = PredictiveLeadScorer()
    ml_score = ml_scorer.score_lead(contact_id, lead_context)

    print(f"ML Score: {ml_score.score}/100")
    print(f"Tier: {ml_score.tier}")
    print(f"Confidence: {ml_score.confidence}")
    print(f"Reasoning: {ml_score.reasoning[:100]}...")

    # Step 2: Sync score to GHL via MCP
    mcp_server = GHLMCPServer()

    sync_result = await mcp_server.update_lead_score(
        contact_id=contact_id,
        score=ml_score.score,
        factors={
            "ml_tier": ml_score.tier,
            "ml_confidence": ml_score.confidence,
            "ml_reasoning": ml_score.reasoning,
            "prediction_timestamp": ml_score.timestamp.isoformat()
        },
        notes=f"ML Predicted Conversion: {ml_score.score}% ({ml_score.tier})"
    )

    print(f"\nGHL Sync Result: {sync_result}")

    return {
        "ml_score": ml_score,
        "ghl_sync": sync_result
    }


async def batch_score_pipeline():
    """Batch score all unscored leads"""

    mcp_server = GHLMCPServer()

    # Find unscored leads
    unscored = await mcp_server.search_ghl_contacts(
        tags=["Need to Qualify", "Unscored"],
        limit=50
    )

    print(f"Found {len(unscored)} unscored leads")

    results = []
    for contact in unscored:
        try:
            # Build lead context from GHL custom fields
            lead_context = {
                "name": contact["name"],
                "email": contact.get("email"),
                "phone": contact.get("phone"),
                "tags": contact.get("tags", []),
                "custom_fields": contact.get("customFields", {})
            }

            # Score and sync
            result = await score_and_sync_lead(contact["id"], lead_context)
            results.append(result)

            print(f"✓ Scored {contact['name']}: {result['ml_score'].score}/100")

        except Exception as e:
            print(f"✗ Failed to score {contact['id']}: {e}")

    return results


if __name__ == "__main__":
    # Example 1: Single lead scoring
    print("=== Single Lead Scoring ===")
    lead_data = {
        "budget": 500000,
        "timeline": "3-6 months",
        "location": "downtown rancho_cucamonga",
        "property_type": "condo",
        "engagement_level": "high"
    }

    result = asyncio.run(score_and_sync_lead("contact_abc123", lead_data))

    # Example 2: Batch scoring
    print("\n=== Batch Lead Scoring ===")
    batch_results = asyncio.run(batch_score_pipeline())
    print(f"\nScored {len(batch_results)} leads")
```

**Output:**

```
=== Single Lead Scoring ===
ML Score: 82/100
Tier: hot
Confidence: 0.87
Reasoning: High engagement with qualified budget and near-term timeline. Strong conversion indicators...

GHL Sync Result: {
  "id": "contact_abc123",
  "score": 82,
  "tags": ["Hot Lead", "AI_Scored_Hot"],
  "workflow_triggered": "high_value_lead_workflow"
}

=== Batch Lead Scoring ===
Found 23 unscored leads
✓ Scored John Smith: 87/100
✓ Scored Jane Doe: 65/100
✓ Scored Bob Johnson: 42/100
...
Scored 23 leads
```

---

## Integration with Claude Enhanced Scorer

### Example: Comprehensive AI Analysis with GHL Sync

```python
#!/usr/bin/env python3
"""
Comprehensive Claude AI analysis with GHL DNA sync.

Demonstrates integration between:
- services/claude_enhanced_lead_scorer.py (AI analysis)
- services/ghl_sync_service.py (DNA payload sync)
- .claude/mcp-servers/ghl/server.py (MCP operations)
"""

import asyncio
from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import (
    ClaudeEnhancedLeadScorer,
    analyze_lead_with_claude
)
from ghl_real_estate_ai.services.ghl_sync_service import GHLSyncService

import sys
sys.path.insert(0, '.claude/mcp-servers/ghl/')
from server import GHLMCPServer


async def comprehensive_lead_analysis(contact_id: str, lead_context: dict):
    """
    Run comprehensive Claude AI analysis and sync all intelligence to GHL.

    This combines:
    1. Jorge's question-based scoring (0-7)
    2. ML predictive scoring (0-100)
    3. Churn risk assessment (0-100)
    4. Claude strategic reasoning
    5. Full DNA payload sync to GHL custom fields

    Args:
        contact_id: GHL contact ID
        lead_context: Complete lead data

    Returns:
        Unified analysis result
    """
    print(f"Starting comprehensive analysis for {contact_id}...")

    # Step 1: Run Claude Enhanced Scorer
    analysis = await analyze_lead_with_claude(contact_id, lead_context)

    print(f"\n=== Analysis Results ===")
    print(f"Final Score: {analysis.final_score}/100")
    print(f"Classification: {analysis.classification}")
    print(f"Confidence: {analysis.confidence_score}")
    print(f"\nComponent Scores:")
    print(f"  Jorge: {analysis.jorge_score}/7")
    print(f"  ML Conversion: {analysis.ml_conversion_score}/100")
    print(f"  Churn Risk: {analysis.churn_risk_score}/100")
    print(f"  Engagement: {analysis.engagement_score}/100")
    print(f"\nStrategic Summary:")
    print(f"  {analysis.strategic_summary}")
    print(f"\nNext Best Action:")
    print(f"  {analysis.next_best_action}")
    print(f"\nSuccess Probability: {analysis.success_probability}%")

    # Step 2: Sync basic score via MCP
    mcp_server = GHLMCPServer()

    score_sync = await mcp_server.update_lead_score(
        contact_id=contact_id,
        score=analysis.final_score,
        factors={
            "jorge_score": analysis.jorge_score,
            "ml_score": analysis.ml_conversion_score,
            "churn_risk": analysis.churn_risk_score,
            "engagement": analysis.engagement_score,
            "confidence": analysis.confidence_score,
            "classification": analysis.classification,
            "strategic_summary": analysis.strategic_summary,
            "next_action": analysis.next_best_action,
            "success_probability": analysis.success_probability
        },
        notes=analysis.reasoning
    )

    print(f"\n✓ Score synced to GHL: {score_sync.get('id')}")

    # Step 3: Sync full DNA payload
    sync_service = GHLSyncService()

    dna_payload = {
        "factors": {
            "intent_level": analysis.engagement_score / 100,
            "financial_readiness": 0.8 if analysis.ml_conversion_score >= 70 else 0.5,
            "timeline_urgency": 0.9 if "immediate" in analysis.expected_timeline.lower() else 0.6,
            "emotional_investment": analysis.confidence_score
        },
        "dimensions": {
            "status": lead_context.get("status_priority", 0.5),
            "convenience": lead_context.get("convenience_priority", 0.5),
            "investment": lead_context.get("investment_priority", 0.5)
        }
    }

    dna_sync = await sync_service.sync_dna_to_ghl(contact_id, dna_payload)

    print(f"✓ DNA payload synced: {dna_sync['fields_updated']} fields")

    # Step 4: Trigger appropriate workflow based on score
    if analysis.final_score >= 85:
        workflow_result = await mcp_server.trigger_ghl_workflow(
            contact_id,
            "wf_hot_lead_handoff",
            custom_values={
                "score": analysis.final_score,
                "next_action": analysis.next_best_action,
                "success_probability": analysis.success_probability
            }
        )
        print(f"✓ Triggered hot lead handoff workflow")

        # Send SMS to agent
        await mcp_server.send_ghl_sms(
            contact_id="jorge_admin_id",
            message=f"🔥 HOT LEAD: {lead_context['name']} scored {analysis.final_score}/100. {analysis.next_best_action}",
            message_type="transactional"
        )
        print(f"✓ Notified agent via SMS")

    return {
        "analysis": analysis,
        "score_sync": score_sync,
        "dna_sync": dna_sync
    }


async def real_time_lead_monitoring():
    """Monitor new leads and auto-analyze with Claude"""

    mcp_server = GHLMCPServer()

    print("Monitoring for new leads...")

    while True:
        # Search for new unanalyzed leads
        new_leads = await mcp_server.search_ghl_contacts(
            tags=["New Lead", "Needs Analysis"],
            limit=10
        )

        for lead in new_leads:
            print(f"\n📬 New lead detected: {lead['name']}")

            # Build context from GHL data
            lead_context = {
                "name": lead["name"],
                "email": lead.get("email"),
                "phone": lead.get("phone"),
                "tags": lead.get("tags", []),
                "custom_fields": lead.get("customFields", {})
            }

            # Run comprehensive analysis
            result = await comprehensive_lead_analysis(lead["id"], lead_context)

            print(f"✓ Analysis complete for {lead['name']}")

        # Wait before next check
        await asyncio.sleep(60)


if __name__ == "__main__":
    # Example 1: Single comprehensive analysis
    print("=== Comprehensive Lead Analysis ===")

    lead_data = {
        "name": "Sarah Martinez",
        "email": "sarah@example.com",
        "phone": "+15125559999",
        "budget": 750000,
        "timeline": "immediate",
        "location": "downtown rancho_cucamonga",
        "property_type": "luxury condo",
        "jorge_questions_answered": 6,
        "engagement_history": ["property_view", "property_view", "email_open", "sms_reply"],
        "status_priority": 0.8,
        "investment_priority": 0.9
    }

    result = asyncio.run(
        comprehensive_lead_analysis("contact_xyz789", lead_data)
    )

    # Example 2: Real-time monitoring (uncomment to run)
    # asyncio.run(real_time_lead_monitoring())
```

**Output:**

```
=== Comprehensive Lead Analysis ===
Starting comprehensive analysis for contact_xyz789...

=== Analysis Results ===
Final Score: 91/100
Classification: hot
Confidence: 0.89

Component Scores:
  Jorge: 6/7
  ML Conversion: 88/100
  Churn Risk: 12/100
  Engagement: 85/100

Strategic Summary:
  High-intent luxury buyer with immediate timeline and qualified budget. Strong engagement signals and minimal churn risk. Excellent conversion candidate.

Next Best Action:
  Schedule immediate property viewing for top 3 luxury condos matching criteria. Follow up within 4 hours.

Success Probability: 87%

✓ Score synced to GHL: contact_xyz789
✓ DNA payload synced: 28 fields
✓ Triggered hot lead handoff workflow
✓ Notified agent via SMS
```

---

## Integration with GHL Sync Service

### Example: DNA Payload Synchronization

```python
#!/usr/bin/env python3
"""
Sync comprehensive lead DNA to GHL custom fields.

Demonstrates:
- 25+ qualification factors
- 16+ lifestyle dimensions
- Automatic field mapping
- High-readiness handoff triggers
"""

import asyncio
from ghl_real_estate_ai.services.ghl_sync_service import GHLSyncService

import sys
sys.path.insert(0, '.claude/mcp-servers/ghl/')
from server import GHLMCPServer


async def sync_lead_dna_comprehensive(contact_id: str):
    """Sync full DNA payload to GHL"""

    # Complete DNA payload with all factors and dimensions
    dna_payload = {
        # 25 Qualification Factors
        "intent_level": 0.92,
        "financial_readiness": 0.88,
        "timeline_urgency": 0.95,
        "emotional_investment": 0.85,
        "decision_authority": 0.90,
        "market_knowledge": 0.75,
        "property_urgency": 0.88,
        "referral_likelihood": 0.82,
        "communication_preference": "sms",
        "negotiation_style": "collaborative",
        "research_depth": 0.80,
        "price_anchoring": 0.70,
        "location_flexibility": 0.60,
        "financing_sophistication": 0.85,
        "renovation_readiness": 0.45,
        "investment_mindset": 0.90,
        "lifestyle_alignment": 0.88,
        "trust_building": 0.85,
        "objection_handling": 0.78,
        "follow_through": 0.92,
        "competitive_awareness": 0.75,
        "social_influence": 0.65,
        "stress_tolerance": 0.80,
        "technology_comfort": 0.90,
        "local_market_fit": 0.85,

        # 16+ Lifestyle Dimensions
        "status": 0.85,
        "convenience": 0.90,
        "security": 0.75,
        "investment": 0.92,
        "family": 0.70,
        "career": 0.85,
        "lifestyle": 0.88,
        "privacy": 0.80,
        "social_connectivity": 0.75,
        "cultural_fit": 0.85,
        "commute_optimization": 0.70,
        "future_family_planning": 0.60,
        "aging_in_place": 0.40,
        "environmental_values": 0.75,
        "technology_integration": 0.90,
        "health_wellness": 0.80
    }

    # Sync to GHL
    sync_service = GHLSyncService()
    result = await sync_service.sync_dna_to_ghl(contact_id, dna_payload)

    print(f"DNA Sync Result:")
    print(f"  Status: {result['status']}")
    print(f"  Fields Updated: {result['fields_updated']}")
    print(f"  Timestamp: {result['timestamp']}")

    # Check for high readiness trigger
    readiness_score = (
        dna_payload["intent_level"] +
        dna_payload["financial_readiness"] +
        dna_payload["timeline_urgency"]
    ) / 3

    if readiness_score >= 0.85:
        print(f"\n🚀 HIGH READINESS: {readiness_score:.2%}")
        await sync_service.trigger_high_readiness_handoff(
            contact_id,
            "Sarah Martinez",
            readiness_score
        )
        print(f"✓ Triggered high-readiness handoff workflow")

    return result


if __name__ == "__main__":
    result = asyncio.run(sync_lead_dna_comprehensive("contact_xyz789"))
```

---

## Automation Scripts

### Example: Automated Lead Nurture Campaign

```python
#!/usr/bin/env python3
"""
Automated lead nurture based on AI scoring and engagement.
"""

import asyncio
from datetime import datetime, timedelta

import sys
sys.path.insert(0, '.claude/mcp-servers/ghl/')
from server import GHLMCPServer


async def automated_nurture_campaign():
    """Run automated nurture campaign for warm leads"""

    mcp_server = GHLMCPServer()

    # Find warm leads (score 40-69)
    warm_leads = await mcp_server.search_ghl_contacts(
        tags=["AI_Scored_Warm"],
        limit=100
    )

    print(f"Found {len(warm_leads)} warm leads for nurture")

    for lead in warm_leads:
        try:
            # Check last contact date
            last_contact = lead.get("lastContactedDate")
            days_since_contact = (
                (datetime.now() - datetime.fromisoformat(last_contact)).days
                if last_contact else 999
            )

            # Nurture based on time since last contact
            if days_since_contact >= 7:
                # Re-engagement SMS
                await mcp_server.send_ghl_sms(
                    contact_id=lead["id"],
                    message=f"Hi {lead['name']}! Just checking in. Any questions about properties in your area? We have some new listings you might love!",
                    message_type="marketing"
                )
                print(f"✓ Sent re-engagement SMS to {lead['name']}")

            elif days_since_contact >= 3:
                # Value-add content workflow
                await mcp_server.trigger_ghl_workflow(
                    lead["id"],
                    "wf_value_content_sequence"
                )
                print(f"✓ Triggered content workflow for {lead['name']}")

        except Exception as e:
            print(f"✗ Failed to nurture {lead['id']}: {e}")

        # Rate limit pause
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(automated_nurture_campaign())
```

---

## CLI Usage

### Command-Line Interface Examples

```bash
# Set environment
export CLAUDE_PROFILE=backend-services

# Example 1: Create contact via natural language
claude "Create a contact named Emily Chen with email emily@example.com, phone +15125558888, tagged as Buyer and Hot Lead, with custom field budget set to 600000"

# Example 2: Search and score leads
claude "Find all contacts tagged as Needs Qualifying, then score each one using the ML predictor and update their scores in GHL"

# Example 3: High-value lead workflow
claude "Search for all contacts with score >= 85 and last contact > 2 days ago. Send them a priority follow-up SMS and notify the agent."

# Example 4: Batch opportunity creation
claude "For each Hot Lead contact without an existing opportunity, create one in the Sales pipeline at Initial Contact stage"

# Example 5: Comprehensive analysis
claude "Run comprehensive Claude AI analysis on contact abc123 and sync all DNA factors to GHL custom fields"
```

---

**Version**: 1.0.0
**Last Updated**: January 16, 2026
**Integration Services**:
- `services/predictive_lead_scorer.py`
- `services/claude_enhanced_lead_scorer.py`
- `services/ghl_sync_service.py`
- `services/ghl_client.py`
