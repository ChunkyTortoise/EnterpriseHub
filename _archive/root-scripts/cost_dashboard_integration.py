"""
Cost Dashboard Integration Guide
How to integrate the Claude Cost Tracking Dashboard into the main Streamlit app

This file shows the integration points and code changes needed.
"""

# ============================================================================
# STEP 1: Add import to app.py (around line 170 where other components are imported)
# ============================================================================

# ADD THIS IMPORT:
"""
from ghl_real_estate_ai.streamlit_demo.components.claude_cost_tracking_dashboard import render_claude_cost_tracking_dashboard
"""

# ============================================================================
# STEP 2: Add the dashboard to the hub navigation
# This code should be added to the sidebar navigation section of app.py
# ============================================================================

SIDEBAR_NAVIGATION_ADDITION = """
# In the sidebar navigation section, add:

with st.sidebar:
    st.markdown("### 💰 Cost Optimization")
    if st.button("📊 Claude Cost Dashboard", use_container_width=True):
        st.session_state.current_hub = "Claude Cost Tracking"
"""

# ============================================================================
# STEP 3: Add the dashboard to the main hub dispatcher
# This should be added to the main content area where other hubs are rendered
# ============================================================================

HUB_DISPATCHER_ADDITION = """
# In the main hub dispatcher section, add this elif block:

elif st.session_state.current_hub == "Claude Cost Tracking":
    st.markdown("---")
    
    # Add async wrapper since we need to call async function
    import asyncio
    
    # Run the async dashboard
    try:
        # Use asyncio.run for the async dashboard function
        if hasattr(asyncio, 'run'):
            asyncio.run(render_claude_cost_tracking_dashboard())
        else:
            # Fallback for older Python versions
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(render_claude_cost_tracking_dashboard())
            finally:
                loop.close()
    except Exception as e:
        st.error(f"Error loading cost dashboard: {str(e)}")
        st.info("Cost tracking dashboard is currently being optimized. Please check back soon.")
"""

# ============================================================================
# STEP 4: Enhanced Integration with Async Utils
# For better integration with the existing async patterns in the app
# ============================================================================

ENHANCED_ASYNC_INTEGRATION = """
# Alternative approach using the existing async_utils.py pattern:

# 1. First, check if async_utils.py has a run_async function:
try:
    from ghl_real_estate_ai.streamlit_demo.async_utils import run_async
    ASYNC_UTILS_AVAILABLE = True
except ImportError:
    ASYNC_UTILS_AVAILABLE = False

# 2. Then in the hub dispatcher:
elif st.session_state.current_hub == "Claude Cost Tracking":
    if ASYNC_UTILS_AVAILABLE:
        # Use the project's async utilities
        run_async(render_claude_cost_tracking_dashboard())
    else:
        # Fallback to standard asyncio
        import asyncio
        asyncio.run(render_claude_cost_tracking_dashboard())
"""

# ============================================================================
# STEP 5: Optional - Add to main navigation tabs
# If you want to add it to the main navigation instead of sidebar
# ============================================================================

MAIN_TAB_INTEGRATION = """
# In the main tab selector, add:

hub_options = [
    "Executive Command Center",
    "Lead Intelligence Hub", 
    "Property Matching Engine",
    "Deal Closer AI",
    "Agent Performance Dashboard",
    "Claude Cost Tracking",  # ADD THIS
    "Jorge Analytics Hub"
]

# Then the existing hub dispatcher will work with the addition above
"""

# ============================================================================
# STEP 6: Quick Integration Script (Copy-Paste Ready)
# ============================================================================

print("=== QUICK INTEGRATION FOR app.py ===")
print()
print("1. Add this import after the existing component imports (around line 170):")
print("from ghl_real_estate_ai.streamlit_demo.components.claude_cost_tracking_dashboard import render_claude_cost_tracking_dashboard")
print()
print("2. Add this to the sidebar navigation:")
print('''
with st.sidebar:
    st.markdown("### 💰 Cost Optimization")
    if st.button("📊 Claude Cost Dashboard", use_container_width=True):
        st.session_state.current_hub = "Claude Cost Tracking"
''')
print()
print("3. Add this to the main hub dispatcher:")
print('''
elif st.session_state.current_hub == "Claude Cost Tracking":
    import asyncio
    try:
        asyncio.run(render_claude_cost_tracking_dashboard())
    except Exception as e:
        st.error(f"Error loading cost dashboard: {str(e)}")
        st.info("Cost tracking dashboard is optimizing. Please try again.")
''')
print()
print("=== END INTEGRATION ===")

# ============================================================================
# STEP 7: Testing the Integration
# ============================================================================

TESTING_NOTES = """
After integration, test:

1. Dashboard loads without errors
2. Real-time metrics display correctly
3. Charts and visualizations render properly
4. Async functions work with the existing app structure
5. No conflicts with existing navigation
6. Performance remains optimal

Expected load time: <2 seconds
Expected memory usage: Minimal additional overhead
Expected user experience: Seamless integration with existing UI
"""

if __name__ == "__main__":
    print(__doc__)
    print("\nIntegration steps above show how to add the Claude Cost Tracking Dashboard to the main app.")
    print("Copy the relevant code sections to app.py as indicated.")