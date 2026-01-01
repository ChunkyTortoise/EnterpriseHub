import streamlit as st
import pandas as pd
import utils.ui as ui
from modules.arete_brain import workflow
from utils.github_tools import GitHubManager
import os

def render():
    """
    Renders the ARETE DevOps Control Dashboard.
    """
    # 1. Header Section
    ui.section_header("🏗️ ARETE Self-Evolution Console", "Technical Co-Founder Control Plane")

    # 2. Status & Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ui.card_metric("Agent Status", "Idle", "Waiting for input")
    with col2:
        ui.card_metric("Active Branch", "main", "Protected")
    with col3:
        ui.card_metric("Test Coverage", "85%", "+2% (Last Build)")
    with col4:
        ui.card_metric("Memory Usage", "124MB", "Optimal")
    
    ui.spacer(20)

    # 3. Main Control Interface
    main_col, side_col = st.columns([2, 1])

    with main_col:
        st.markdown("### 🤖 Active Agent Workflows")
        
        # Chat Interface
        with st.container():
            st.info("🟢 **System Ready:** Neural engine initialized. Connected to GitHub API.")
            
            task = st.chat_input("Instruct ARETE to modify the codebase (e.g., 'Add a new feature to the pricing module')...")
            
            if task:
                # 1. User Message
                with st.chat_message("user"):
                    st.write(task)
                
                # 2. Agent Thinking (Simulated connection to LangGraph)
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing codebase architecture..."):
                        # In a real app, we would invoke the graph here:
                        # result = workflow.invoke({"messages": [HumanMessage(content=task)]})
                        
                        st.markdown("**Plan Proposed:**")
                        st.code("""
                        1. SEARCH: 'pricing_module.py' and 'test_pricing.py'
                        2. ANALYSIS: Identify extension points for requested feature
                        3. BRANCH: Create 'feature/pricing-update-v2'
                        4. ACTION: Implement changes
                        5. VERIFY: Run unit tests
                        """, language="yaml")
                        
                        st.success("✅ **Execution Complete:** PR #42 Created")
                        st.markdown("[View Pull Request](https://github.com/ChunkyTortoise/enterprise-hub/pulls)")

        ui.spacer(20)
        
        # Activity Log (Mock Data for Demo)
        st.markdown("### 📜 Recent Agent Actions")
        activity_data = pd.DataFrame({
            "Timestamp": ["10:42 AM", "09:15 AM", "Yesterday"],
            "Action": ["Code Commit", "Test Run", "Self-Correction"],
            "Details": ["Updated utils/ui.py", "Passed 220 tests", "Fixed import error in modules/auth.py"],
            "Status": ["Success", "Success", "Resolved"]
        })
        st.dataframe(activity_data, use_container_width=True, hide_index=True)

    with side_col:
        st.markdown("### 🧠 System Memory")
        
        # Business Context Card
        ui.glassmorphic_card(
            title="Business Context",
            content="""
            **Goal:** Build self-maintaining AI<br>
            **Stack:** Claude 3.5, LangGraph, Flask<br>
            **Deploy:** AWS Lambda / Streamlit Cloud
            """,
            icon="🏢"
        )
        
        ui.spacer(10)
        
        # Tech Stack Card
        ui.glassmorphic_card(
            title="Capabilities",
            content="""
            ✅ **File I/O:** Read/Write Access<br>
            ✅ **Git:** Commit, Push, PR<br>
            ✅ **Tests:** Run pytest suite<br>
            ✅ **Deploy:** Trigger CI/CD
            """,
            icon="🛠️"
        )

    # 4. Footer Credentials
    ui.spacer(40)
    st.caption("🔒 Authenticated as Root Admin. All actions are logged and version-controlled.")
