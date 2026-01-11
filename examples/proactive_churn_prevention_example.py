"""
Proactive Churn Prevention - Integration Example

Demonstrates the 3-Stage Intervention Framework in action with real-world scenarios:
1. Early warning detection and subtle re-engagement
2. Active risk intervention with multi-channel delivery
3. Critical risk escalation to manager

Author: EnterpriseHub AI Platform
Last Updated: 2026-01-10
"""

import asyncio
from datetime import datetime
from typing import List

from ghl_real_estate_ai.services.proactive_churn_prevention_orchestrator import (
    get_proactive_churn_orchestrator,
    monitor_lead_churn_risk,
    trigger_churn_intervention,
    escalate_critical_churn,
    InterventionStage,
    InterventionOutcome
)


async def example_1_basic_monitoring():
    """Example 1: Basic churn monitoring and intervention"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Churn Monitoring and Intervention")
    print("="*70 + "\n")

    orchestrator = await get_proactive_churn_orchestrator()

    # Monitor a lead's churn risk
    print("📊 Monitoring churn risk for lead...")
    assessment = await orchestrator.monitor_churn_risk(
        lead_id="lead_demo_001",
        tenant_id="demo_tenant"
    )

    print(f"\n✅ Risk Assessment Complete:")
    print(f"   Lead ID: {assessment.lead_id}")
    print(f"   Churn Probability: {assessment.churn_probability:.1%}")
    print(f"   Risk Level: {assessment.risk_level.value}")
    print(f"   Intervention Stage: {assessment.intervention_stage.value}")
    print(f"   Time to Churn: {assessment.time_to_churn_days} days")
    print(f"   Detection Latency: {assessment.detection_latency_ms:.1f}ms")
    print(f"   Assessment Time: {assessment.assessment_time_ms:.1f}ms")

    # Trigger intervention based on stage
    if assessment.churn_probability > 0.3:
        print(f"\n🎯 Triggering {assessment.intervention_stage.value} intervention...")

        result = await orchestrator.trigger_intervention(
            lead_id=assessment.lead_id,
            tenant_id=assessment.tenant_id,
            stage=assessment.intervention_stage
        )

        print(f"\n✅ Intervention Executed:")
        print(f"   Action ID: {result.action_id}")
        print(f"   Outcome: {result.outcome.value}")
        print(f"   Delivery Time: {result.delivery_time_ms:.1f}ms")
        print(f"   Total Latency: {result.total_latency_ms:.1f}ms")
        print(f"   Status: {result.delivery_status}")


async def example_2_batch_portfolio_monitoring():
    """Example 2: Batch monitoring for entire lead portfolio"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Batch Portfolio Monitoring")
    print("="*70 + "\n")

    orchestrator = await get_proactive_churn_orchestrator()

    # Simulate portfolio of leads
    lead_ids = [f"portfolio_lead_{i:03d}" for i in range(1, 11)]
    tenant_id = "demo_tenant"

    print(f"📊 Monitoring {len(lead_ids)} leads in parallel...")

    # Monitor all leads concurrently
    start_time = asyncio.get_event_loop().time()

    tasks = [
        orchestrator.monitor_churn_risk(lead_id, tenant_id)
        for lead_id in lead_ids
    ]

    assessments = await asyncio.gather(*tasks)

    total_time = asyncio.get_event_loop().time() - start_time

    print(f"\n✅ Portfolio Assessment Complete in {total_time:.2f}s")
    print(f"   Average time per lead: {(total_time / len(lead_ids)) * 1000:.1f}ms")

    # Categorize by risk stage
    early_warning = [a for a in assessments if a.intervention_stage == InterventionStage.EARLY_WARNING]
    active_risk = [a for a in assessments if a.intervention_stage == InterventionStage.ACTIVE_RISK]
    critical_risk = [a for a in assessments if a.intervention_stage == InterventionStage.CRITICAL_RISK]

    print(f"\n📈 Risk Distribution:")
    print(f"   Early Warning: {len(early_warning)} leads ({len(early_warning)/len(assessments)*100:.1f}%)")
    print(f"   Active Risk: {len(active_risk)} leads ({len(active_risk)/len(assessments)*100:.1f}%)")
    print(f"   Critical Risk: {len(critical_risk)} leads ({len(critical_risk)/len(assessments)*100:.1f}%)")

    # Trigger interventions for high-risk leads
    intervention_count = 0
    for assessment in active_risk + critical_risk:
        result = await orchestrator.trigger_intervention(
            lead_id=assessment.lead_id,
            tenant_id=tenant_id,
            stage=assessment.intervention_stage
        )
        if result.outcome == InterventionOutcome.DELIVERED:
            intervention_count += 1

    print(f"\n🎯 Interventions Triggered: {intervention_count}/{len(active_risk) + len(critical_risk)}")


async def example_3_critical_risk_escalation():
    """Example 3: Critical risk detection and manager escalation"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Critical Risk Detection and Manager Escalation")
    print("="*70 + "\n")

    orchestrator = await get_proactive_churn_orchestrator()

    # Monitor high-risk lead
    print("📊 Monitoring high-value lead with suspected churn risk...")

    assessment = await orchestrator.monitor_churn_risk(
        lead_id="high_value_lead_001",
        tenant_id="demo_tenant"
    )

    print(f"\n⚠️  Risk Assessment:")
    print(f"   Churn Probability: {assessment.churn_probability:.1%}")
    print(f"   Risk Level: {assessment.risk_level.value}")
    print(f"   Time to Churn: {assessment.time_to_churn_days} days")

    # If critical risk, execute emergency protocol
    if assessment.intervention_stage == InterventionStage.CRITICAL_RISK:
        print(f"\n🚨 CRITICAL RISK DETECTED - Initiating Emergency Protocol")

        # Step 1: Immediate intervention
        print("\n🎯 Step 1: Triggering immediate intervention...")
        intervention = await orchestrator.trigger_intervention(
            lead_id=assessment.lead_id,
            tenant_id=assessment.tenant_id,
            stage=InterventionStage.CRITICAL_RISK
        )

        print(f"   Intervention: {intervention.outcome.value}")
        print(f"   Latency: {intervention.total_latency_ms:.1f}ms")

        # Step 2: Escalate to manager
        print("\n🚀 Step 2: Escalating to manager...")
        escalation = await orchestrator.escalate_to_manager(
            lead_id=assessment.lead_id,
            tenant_id=assessment.tenant_id,
            context={
                "reason": "critical_churn_risk",
                "urgency": "immediate",
                "churn_probability": assessment.churn_probability,
                "days_to_churn": assessment.time_to_churn_days,
                "intervention_attempted": True
            }
        )

        print(f"\n✅ Escalation Created:")
        print(f"   Escalation ID: {escalation.escalation_id}")
        print(f"   Assigned To: {escalation.escalated_to}")
        print(f"   Urgency Level: {escalation.urgency_level}")
        print(f"   Status: {escalation.resolution_status}")

        print(f"\n📋 Recommended Actions for Manager:")
        for idx, action in enumerate(escalation.recommended_actions, 1):
            print(f"   {idx}. {action}")

        print(f"\n📊 Churn Context Provided:")
        print(f"   Risk Factors: {len(escalation.churn_context.get('top_risk_factors', []))}")
        print(f"   Intervention History: {len(escalation.intervention_history)}")
        print(f"   Behavioral Signals: {len(escalation.churn_context.get('behavioral_signals', {}))}")


async def example_4_performance_dashboard():
    """Example 4: Performance metrics and dashboard"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Performance Metrics Dashboard")
    print("="*70 + "\n")

    orchestrator = await get_proactive_churn_orchestrator()

    # Simulate some activity
    print("📊 Simulating prevention activity...")

    # Monitor several leads
    for i in range(5):
        await orchestrator.monitor_churn_risk(f"metrics_lead_{i}", "demo_tenant")

    # Trigger some interventions
    for i in range(3):
        await orchestrator.trigger_intervention(
            f"metrics_lead_{i}",
            "demo_tenant",
            InterventionStage.EARLY_WARNING
        )

    # Get comprehensive metrics
    metrics = await orchestrator.get_prevention_metrics()

    print(f"\n📈 Proactive Churn Prevention Dashboard")
    print(f"\n{'─'*70}")
    print(f"VOLUME METRICS")
    print(f"{'─'*70}")
    print(f"   Total Assessments: {metrics.total_assessments}")
    print(f"   Early Warning: {metrics.early_warning_count}")
    print(f"   Active Risk: {metrics.active_risk_count}")
    print(f"   Critical Risk: {metrics.critical_risk_count}")

    print(f"\n{'─'*70}")
    print(f"INTERVENTION METRICS")
    print(f"{'─'*70}")
    print(f"   Total Interventions: {metrics.total_interventions}")
    print(f"   Successful: {metrics.successful_interventions}")
    print(f"   Failed: {metrics.failed_interventions}")
    print(f"   Success Rate: {metrics.avg_success_rate:.1%}")
    print(f"   Escalations: {metrics.escalations_count}")

    print(f"\n{'─'*70}")
    print(f"PERFORMANCE METRICS")
    print(f"{'─'*70}")
    print(f"   Avg Detection Latency: {metrics.avg_detection_latency_ms:.1f}ms")
    print(f"   Avg Intervention Latency: {metrics.avg_intervention_latency_ms:.1f}ms")
    print(f"   Meets <30s Target: {'✅ YES' if metrics.avg_intervention_latency_ms < 30000 else '❌ NO'}")

    print(f"\n{'─'*70}")
    print(f"BUSINESS IMPACT")
    print(f"{'─'*70}")
    print(f"   Churn Prevented: {metrics.churn_prevented_count} leads")
    print(f"   Revenue Saved: ${metrics.estimated_revenue_saved:,.2f}")
    print(f"   Intervention ROI: {metrics.intervention_roi:.1f}x")

    print(f"\n{'─'*70}")
    print(f"REAL-TIME STATUS")
    print(f"{'─'*70}")
    print(f"   Active Monitoring: {metrics.active_monitoring_count} leads")
    print(f"   Pending Interventions: {metrics.pending_interventions}")
    print(f"   In Progress: {metrics.in_progress_interventions}")

    print(f"\n{'─'*70}")
    print(f"TIME WINDOW")
    print(f"{'─'*70}")
    print(f"   Start: {metrics.metrics_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   End: {metrics.metrics_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    duration = (metrics.metrics_end_time - metrics.metrics_start_time).total_seconds()
    print(f"   Duration: {duration:.1f} seconds")


async def example_5_real_world_scenario():
    """Example 5: Real-world scenario - Lead going cold"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Real-World Scenario - Re-engaging Cold Lead")
    print("="*70 + "\n")

    orchestrator = await get_proactive_churn_orchestrator()

    print("📖 Scenario: Sarah Johnson hasn't engaged in 12 days")
    print("   - Last property view: 12 days ago")
    print("   - Email open rate: Declining (60% → 20%)")
    print("   - No responses to last 3 emails")
    print("   - Budget: $400K-$500K")
    print("   - Location: Austin, TX suburbs")

    print("\n📊 Phase 1: Churn Risk Detection")
    print("   Running ML-powered churn prediction...")

    assessment = await monitor_lead_churn_risk(
        lead_id="sarah_johnson_12345",
        tenant_id="austin_realty_001"
    )

    print(f"\n   ✅ Risk Detected:")
    print(f"      Churn Probability: {assessment.churn_probability:.1%}")
    print(f"      Stage: {assessment.intervention_stage.value}")
    print(f"      Estimated Time to Churn: {assessment.time_to_churn_days} days")
    print(f"      Detection Time: {assessment.detection_latency_ms:.1f}ms")

    print("\n🎯 Phase 2: Intervention Strategy")

    if assessment.intervention_stage == InterventionStage.EARLY_WARNING:
        print("   Strategy: Subtle re-engagement campaign")
        print("   - Send personalized market update (Austin suburbs)")
        print("   - Share 3 new properties matching criteria ($400K-$500K)")
        print("   - Educational content: 'Best time to buy in Austin'")

    elif assessment.intervention_stage == InterventionStage.ACTIVE_RISK:
        print("   Strategy: Direct personal outreach")
        print("   - Personal call from agent within 24 hours")
        print("   - SMS with exclusive property preview")
        print("   - Offer private showing of top-matched properties")

    elif assessment.intervention_stage == InterventionStage.CRITICAL_RISK:
        print("   Strategy: Emergency retention protocol")
        print("   - Immediate call from senior agent")
        print("   - Manager escalation for VIP treatment")
        print("   - Special offer: Closing cost assistance ($2,500)")

    print("\n🚀 Phase 3: Executing Intervention")

    result = await trigger_churn_intervention(
        lead_id="sarah_johnson_12345",
        tenant_id="austin_realty_001",
        stage=assessment.intervention_stage
    )

    print(f"   ✅ Intervention Delivered:")
    print(f"      Channel: {result.channel_metadata.get('channel', 'multi-channel')}")
    print(f"      Outcome: {result.outcome.value}")
    print(f"      Delivery Time: {result.delivery_time_ms:.1f}ms")
    print(f"      Total Latency: {result.total_latency_ms:.1f}ms")

    print("\n📈 Phase 4: Expected Outcomes")

    if assessment.intervention_stage == InterventionStage.EARLY_WARNING:
        print("   Expected Re-engagement: 40-50%")
        print("   Follow-up: Monitor for 7 days")
    elif assessment.intervention_stage == InterventionStage.ACTIVE_RISK:
        print("   Expected Re-engagement: 55-65%")
        print("   Follow-up: Schedule showing within 48 hours")
    elif assessment.intervention_stage == InterventionStage.CRITICAL_RISK:
        print("   Expected Retention: 60-70%")
        print("   Follow-up: Manager personal involvement")

    print(f"\n💰 Business Impact:")
    print(f"   Lead Value: $50,000 (estimated commission)")
    print(f"   Intervention Cost: ~$5")
    print(f"   Expected ROI: {(50000 * 0.65) / 5:.0f}x (assuming 65% success)")


async def run_all_examples():
    """Run all examples sequentially"""
    print("\n" + "="*70)
    print("  PROACTIVE CHURN PREVENTION - INTEGRATION EXAMPLES")
    print("="*70)

    try:
        await example_1_basic_monitoring()
        await asyncio.sleep(1)

        await example_2_batch_portfolio_monitoring()
        await asyncio.sleep(1)

        await example_3_critical_risk_escalation()
        await asyncio.sleep(1)

        await example_4_performance_dashboard()
        await asyncio.sleep(1)

        await example_5_real_world_scenario()

        print("\n" + "="*70)
        print("  ✅ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run all examples
    asyncio.run(run_all_examples())
