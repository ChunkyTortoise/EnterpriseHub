"""
Test Script for Claude Cost Tracking Dashboard
Standalone test to verify dashboard functionality before integration

Run this to test the dashboard independently:
python test_cost_dashboard.py

Or as a Streamlit app:
streamlit run test_cost_dashboard.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import streamlit as st
    from ghl_real_estate_ai.streamlit_demo.components.claude_cost_tracking_dashboard import (
        render_claude_cost_tracking_dashboard,
        CostTrackingDashboard
    )
    
    # Configure Streamlit page
    st.set_page_config(
        page_title="Claude Cost Dashboard Test",
        page_icon="💰",
        layout="wide"
    )
    
    async def test_dashboard():
        """Test the cost tracking dashboard"""
        st.title("🧪 Claude Cost Dashboard Test")
        st.markdown("Testing the cost optimization dashboard functionality...")
        
        # Test dashboard initialization
        st.subheader("1. Dashboard Initialization Test")
        try:
            dashboard = CostTrackingDashboard()
            st.success("✅ Dashboard initialized successfully")
        except Exception as e:
            st.error(f"❌ Dashboard initialization failed: {str(e)}")
            return
        
        # Test metrics collection
        st.subheader("2. Metrics Collection Test")
        try:
            metrics = await dashboard.get_real_time_metrics()
            st.success("✅ Metrics collection working")
            st.json({
                "total_tokens_saved": metrics.total_tokens_saved,
                "total_cost_saved": metrics.total_cost_saved,
                "cache_hit_rate": metrics.cache_hit_rate,
                "optimization_score": metrics.optimization_score
            })
        except Exception as e:
            st.error(f"❌ Metrics collection failed: {str(e)}")
            return
        
        # Test insights generation
        st.subheader("3. Insights Generation Test")
        try:
            insights = await dashboard.get_optimization_insights()
            st.success("✅ Insights generation working")
            st.write("Top Cost Savings:")
            for saving in insights.top_cost_savings:
                st.write(f"- {saving}")
        except Exception as e:
            st.error(f"❌ Insights generation failed: {str(e)}")
        
        st.markdown("---")
        st.subheader("4. Full Dashboard Render Test")
        
        # Render the full dashboard
        await render_claude_cost_tracking_dashboard()
    
    def run_test():
        """Run the async test function"""
        try:
            asyncio.run(test_dashboard())
        except Exception as e:
            st.error(f"Test failed: {str(e)}")
            st.info("This is normal if optimization services aren't fully deployed yet.")
    
    if __name__ == "__main__":
        if len(sys.argv) > 1 and sys.argv[1] == "--streamlit":
            # Running as Streamlit app
            run_test()
        else:
            # Running as Python script
            print("Claude Cost Tracking Dashboard Test")
            print("=" * 40)
            
            # Test basic imports
            print("Testing imports...")
            try:
                from ghl_real_estate_ai.streamlit_demo.components.claude_cost_tracking_dashboard import CostTrackingDashboard
                print("✅ CostTrackingDashboard import successful")
            except ImportError as e:
                print(f"❌ Import failed: {e}")
                sys.exit(1)
            
            # Test dashboard initialization
            print("Testing dashboard initialization...")
            try:
                dashboard = CostTrackingDashboard()
                print("✅ Dashboard initialization successful")
            except Exception as e:
                print(f"❌ Dashboard initialization failed: {e}")
                sys.exit(1)
            
            # Test async metrics (simplified)
            print("Testing metrics collection...")
            try:
                async def test_metrics():
                    metrics = await dashboard.get_real_time_metrics()
                    return metrics
                
                metrics = asyncio.run(test_metrics())
                print(f"✅ Metrics collection successful")
                print(f"   - Tokens saved: {metrics.total_tokens_saved:,}")
                print(f"   - Cost saved: ${metrics.total_cost_saved:.2f}")
                print(f"   - Cache hit rate: {metrics.cache_hit_rate:.1f}%")
                print(f"   - Optimization score: {metrics.optimization_score:.1f}")
            except Exception as e:
                print(f"❌ Metrics collection failed: {e}")
            
            print("\n" + "=" * 40)
            print("Basic tests completed!")
            print("To test the full UI, run:")
            print("streamlit run test_cost_dashboard.py --streamlit")

except ImportError as e:
    print(f"Import Error: {e}")
    print("Make sure you're running from the project root and have all dependencies installed.")
    print("Required: streamlit, plotly, pandas, numpy")
    
if __name__ == "__main__" and "--streamlit" in sys.argv:
    # This runs when called as: streamlit run test_cost_dashboard.py --streamlit
    run_test()