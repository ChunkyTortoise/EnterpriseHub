"""
Quote Request Form Component
Professional service quote request form for portfolio showcase
"""

import streamlit as st
from datetime import datetime, timedelta
import re


def render_quote_request_form():
    """Render the quote request form."""
    st.markdown("## 📋 Request a Quote")
    st.markdown("Fill out the form below and I'll get back to you within 24 hours.")
    st.markdown("---")
    
    with st.form("quote_request_form"):
        # Contact Information
        st.markdown("### Contact Information")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name *", placeholder="John Smith")
            email = st.text_input("Email *", placeholder="john@company.com")
            phone = st.text_input("Phone", placeholder="+1 (555) 123-4567")
        
        with col2:
            company = st.text_input("Company", placeholder="Acme Inc.")
            website = st.text_input("Website", placeholder="https://company.com")
            preferred_contact = st.selectbox(
                "Preferred Contact Method",
                ["Email", "Phone", "Video Call"]
            )
        
        st.markdown("---")
        
        # Project Details
        st.markdown("### Project Details")
        
        service_category = st.selectbox(
            "Service Category *",
            [
                "Select a category...",
                "AI Intelligent Automation",
                "Data & Business Intelligence",
                "Infrastructure & MLOps",
                "Marketing & Growth",
                "Ops & Governance",
                "Strategic Services",
                "Not sure - need consultation"
            ]
        )
        
        # Show relevant services based on category
        if service_category == "AI Intelligent Automation":
            specific_service = st.multiselect(
                "Specific Services of Interest",
                [
                    "Custom RAG Conversational Agents",
                    "Multi-Agent Workflows",
                    "Prompt Engineering & Optimization",
                    "Automation & Workflow Engineering"
                ]
            )
        elif service_category == "Data & Business Intelligence":
            specific_service = st.multiselect(
                "Specific Services of Interest",
                [
                    "Deep Learning & Custom ML Models",
                    "Interactive BI Dashboards",
                    "Automated Reporting Pipelines",
                    "Predictive Analytics & Lead Scoring",
                    "Data Engineering & Pipelines"
                ]
            )
        elif service_category == "Marketing & Growth":
            specific_service = st.multiselect(
                "Specific Services of Interest",
                [
                    "Programmatic SEO Content Engine",
                    "Email & Outreach Automation",
                    "Social Media Content Automation",
                    "Marketing Attribution Analysis",
                    "Competitor Intelligence & Monitoring"
                ]
            )
        else:
            specific_service = []
        
        project_description = st.text_area(
            "Project Description *",
            placeholder="Describe your project, goals, and any specific requirements...",
            height=150
        )
        
        # Timeline & Budget
        col3, col4 = st.columns(2)
        
        with col3:
            timeline = st.selectbox(
                "Desired Timeline",
                [
                    "ASAP (1-2 weeks)",
                    "Standard (3-5 weeks)",
                    "Flexible (6+ weeks)",
                    "Ongoing retainer"
                ]
            )
        
        with col4:
            budget_range = st.selectbox(
                "Budget Range",
                [
                    "$3,000 - $5,000",
                    "$5,000 - $10,000",
                    "$10,000 - $20,000",
                    "$20,000+",
                    "Not sure - need consultation"
                ]
            )
        
        st.markdown("---")
        
        # Additional Information
        st.markdown("### Additional Information")
        
        has_existing_data = st.radio(
            "Do you have existing data/systems to integrate?",
            ["Yes", "No", "Not sure"]
        )
        
        team_size = st.selectbox(
            "Expected users/team size",
            ["Just me", "2-10 people", "11-50 people", "50+ people"]
        )
        
        discovery_call = st.checkbox(
            "I'd like to schedule a 30-minute discovery call",
            value=True
        )
        
        if discovery_call:
            call_dates = []
            for i in range(5):
                date = datetime.now() + timedelta(days=i+1)
                if date.weekday() < 5:  # Monday = 0, Friday = 4
                    call_dates.append(date.strftime("%A, %B %d"))
            
            preferred_date = st.selectbox("Preferred date for call", call_dates)
            preferred_time = st.selectbox(
                "Preferred time (Pacific)",
                ["9:00 AM", "10:00 AM", "11:00 AM", "1:00 PM", "2:00 PM", "3:00 PM", "4:00 PM"]
            )
        
        # Submit button
        st.markdown("---")
        submitted = st.form_submit_button("Submit Quote Request", type="primary")
        
        if submitted:
            # Validation
            errors = []
            if not name:
                errors.append("Name is required")
            if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                errors.append("Valid email is required")
            if service_category == "Select a category...":
                errors.append("Please select a service category")
            if not project_description:
                errors.append("Project description is required")
            
            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Success message
                st.success("✅ Quote request submitted successfully!")
                st.balloons()
                
                st.markdown("""
                **What happens next:**
                1. I'll review your request within 24 hours
                2. I'll send a detailed proposal with timeline and pricing
                3. We'll schedule a call to discuss (if requested)
                
                **Contact:** caymanroden@gmail.com
                """)
                
                # In production, this would save to database and send email
                # For now, just show the data that would be saved
                with st.expander("📊 Request Summary (Internal)"):
                    st.json({
                        "timestamp": datetime.now().isoformat(),
                        "contact": {
                            "name": name,
                            "email": email,
                            "phone": phone,
                            "company": company,
                            "website": website,
                            "preferred_contact": preferred_contact
                        },
                        "project": {
                            "category": service_category,
                            "specific_services": specific_service,
                            "description": project_description[:100] + "...",
                            "timeline": timeline,
                            "budget": budget_range
                        },
                        "details": {
                            "existing_data": has_existing_data,
                            "team_size": team_size,
                            "discovery_call": discovery_call,
                            "call_preference": f"{preferred_date} at {preferred_time}" if discovery_call else None
                        }
                    })


if __name__ == "__main__":
    st.set_page_config(page_title="Request a Quote", page_icon="📋")
    render_quote_request_form()
