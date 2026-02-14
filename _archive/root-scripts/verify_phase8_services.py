
import asyncio
import sys
import os
from datetime import datetime

# Add the project root to sys.path
sys.path.append(os.getcwd())

from ghl_real_estate_ai.services.autonomous_deal_orchestrator import AutonomousDealOrchestrator
from ghl_real_estate_ai.services.luxury_market_data_integration import LuxuryMarketDataIntegrator
from ghl_real_estate_ai.services.transaction_service import TransactionCreate

async def verify_services():
    print("🚀 Verifying Critical Services...")
    
    # 1. Verify AutonomousDealOrchestrator
    print("\n--- AutonomousDealOrchestrator ---")
    try:
        orchestrator = AutonomousDealOrchestrator()
        status = orchestrator.get_orchestration_status()
        print(f"✅ Orchestrator instantiated. Status: {status['is_running']}")
        
        # Test workflow generation (internal method but good for verification)
        mock_transaction = TransactionCreate(
            ghl_lead_id="test_lead_123",
            property_id="test_prop_456",
            buyer_name="Test Buyer",
            buyer_email="test@example.com",
            property_address="123 Test St, Rancho Cucamonga, CA",
            purchase_price=500000.0,
            contract_date=datetime.now(),
            expected_closing_date=datetime.now(),
            agent_name="Test Agent"
        )
        tasks = await orchestrator._generate_workflow_tasks("test_id", mock_transaction)
        print(f"✅ Workflow generation successful. Generated {len(tasks)} tasks.")
    except Exception as e:
        print(f"❌ Orchestrator verification failed: {e}")
        import traceback
        traceback.print_exc()

    # 2. Verify LuxuryMarketDataIntegrator
    print("\n--- LuxuryMarketDataIntegrator ---")
    try:
        integrator = LuxuryMarketDataIntegrator()
        print("✅ Integrator instantiated.")
        
        # Test inventory summary (mocked but tests the data structure)
        inventory = await integrator.get_luxury_inventory_summary()
        print(f"✅ Inventory summary successful. Total properties: {inventory['total_luxury_properties']}")
        
        # Test market report
        report = await integrator.generate_luxury_market_report()
        print(f"✅ Market report generation successful. Report date: {report['report_date']}")
    except Exception as e:
        print(f"❌ Integrator verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_services())
