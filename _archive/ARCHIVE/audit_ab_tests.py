import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
sys.path.append(str(Path.cwd()))

from ghl_real_estate_ai.services.autonomous_ab_testing import get_autonomous_ab_testing

async def main():
    print("🧪 JORGE'S BOT EVOLUTION: A/B TEST PERFORMANCE AUDIT")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    ab_engine = get_autonomous_ab_testing()
    summary = ab_engine.get_testing_performance_summary()
    
    print(f"📊 Overall Engine Status: {'🟢 ACTIVE' if summary['monitoring_status'] else '⚪ IDLE'}")
    print(f"📈 Average Lift Achieved: {summary['testing_metrics']['average_lift_achieved']:.1f}%")
    print(f"🧪 Active Tests: {len(summary['active_tests'])}\n")
    
    if not summary['active_tests']:
        print("No active tests found. Initializing Follow-up Optimization test...")
        # Triggering a dummy allocation to ensure the test is created if it hasn't run yet
        from ghl_real_estate_ai.services.jorge.jorge_followup_scheduler import JorgeFollowUpScheduler
        scheduler = JorgeFollowUpScheduler()
        await scheduler._get_or_create_follow_up_test()
        summary = ab_engine.get_testing_performance_summary()

    for test_id, data in summary['active_tests'].items():
        print(f"--- Test: {data['name']} [{test_id}] ---")
        print(f"  Status: {data['status'].upper()}")
        print(f"  Participants: {data['participants']}")
        print(f"  Conversions: {data['conversions']}")
        print(f"  Conv. Rate: {data['conversion_rate']:.1%}")
        
        # In a real scenario, we'd list variant breakdowns here
        print(f"  Variants: {data['variants']}")
        print(f"  Insights Generated: {summary['total_insights_generated']}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
