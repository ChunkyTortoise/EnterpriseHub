import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_seller_prep_checklist():
    """Comprehensive seller preparation checklist"""
    st.subheader("📋 Seller Preparation Checklist")

    # Progress overview
    st.markdown("#### 📊 Preparation Progress")

    # Mock completion data
    total_tasks = 25
    completed_tasks = 12
    progress = completed_tasks / total_tasks

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("✅ Tasks Completed", f"{completed_tasks}/{total_tasks}")
    with col2:
        st.metric("📈 Progress", f"{progress*100:.0f}%")
    with col3:
        st.metric("🏠 Market Readiness", "Good")
    with col4:
        st.metric("⏱️ Time to Market", "2-3 weeks")

    # Progress bar
    st.progress(progress)

    # Checklist categories
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Interior Prep", "🌿 Exterior Prep", "📄 Documentation", "📸 Marketing Prep", "🔧 Repairs & Updates"
    ])

    with tab1:
        st.markdown("##### Interior Preparation")

        interior_tasks = [
            {"task": "Deep clean all rooms", "status": "✅", "priority": "High", "notes": "Professional cleaning scheduled"},
            {"task": "Declutter and organize", "status": "✅", "priority": "High", "notes": "Completed last weekend"},
            {"task": "Fresh paint (neutral colors)", "status": "⏳", "priority": "High", "notes": "Painter coming Monday"},
            {"task": "Clean windows inside", "status": "✅", "priority": "Medium", "notes": "Done with deep cleaning"},
            {"task": "Replace burnt-out bulbs", "status": "❌", "priority": "Medium", "notes": "Need LED bulbs"},
            {"task": "Remove personal photos", "status": "✅", "priority": "Medium", "notes": "Stored in garage"},
            {"task": "Stage furniture arrangement", "status": "❌", "priority": "Medium", "notes": "Stager coming Thursday"},
            {"task": "Fix squeaky doors/hinges", "status": "❌", "priority": "Low", "notes": "Need WD-40"},
        ]

        for task in interior_tasks:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 2])

                with col1:
                    st.markdown(f"{task['status']} {task['task']}")
                with col2:
                    priority_color = "red" if task['priority'] == "High" else "orange" if task['priority'] == "Medium" else "green"
                    st.markdown(f"<span style='color: {priority_color};'>{task['priority']}</span>", unsafe_allow_html=True)
                with col3:
                    if task['status'] == "❌":
                        if st.button("Mark Done", key=f"interior_{task['task'][:10]}"):
                            st.success("Task completed!")
                with col4:
                    st.markdown(f"*{task['notes']}*")

    with tab2:
        st.markdown("##### Exterior & Curb Appeal")

        exterior_tasks = [
            {"task": "Mow and edge lawn", "status": "✅", "priority": "High", "notes": "Weekly maintenance"},
            {"task": "Trim bushes and trees", "status": "✅", "priority": "High", "notes": "Landscaper completed"},
            {"task": "Plant seasonal flowers", "status": "⏳", "priority": "Medium", "notes": "Scheduled for weekend"},
            {"task": "Power wash driveway/walkways", "status": "❌", "priority": "High", "notes": "Rent pressure washer"},
            {"task": "Clean exterior windows", "status": "❌", "priority": "Medium", "notes": "Include in window service"},
            {"task": "Touch up exterior paint", "status": "❌", "priority": "Medium", "notes": "Minor spots identified"},
            {"task": "Clean gutters", "status": "✅", "priority": "Low", "notes": "Done in fall"},
            {"task": "Ensure adequate outdoor lighting", "status": "⏳", "priority": "Medium", "notes": "Adding pathway lights"},
        ]

        for task in exterior_tasks:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 2])

                with col1:
                    st.markdown(f"{task['status']} {task['task']}")
                with col2:
                    priority_color = "red" if task['priority'] == "High" else "orange" if task['priority'] == "Medium" else "green"
                    st.markdown(f"<span style='color: {priority_color};'>{task['priority']}</span>", unsafe_allow_html=True)
                with col3:
                    if task['status'] == "❌":
                        if st.button("Mark Done", key=f"exterior_{task['task'][:10]}"):
                            st.success("Task completed!")
                with col4:
                    st.markdown(f"*{task['notes']}*")

    with tab3:
        st.markdown("##### Required Documentation")

        documents = [
            {"doc": "Property deed", "status": "✅", "location": "File cabinet", "notes": "Original in safe"},
            {"doc": "Previous property disclosures", "status": "✅", "location": "With agent", "notes": "From purchase"},
            {"doc": "Recent utility bills", "status": "✅", "location": "Office desk", "notes": "Last 3 months"},
            {"doc": "HOA documents (if applicable)", "status": "N/A", "location": "-", "notes": "No HOA"},
            {"doc": "Survey/plat of property", "status": "⏳", "location": "Searching", "notes": "Request from title company"},
            {"doc": "Warranty information", "status": "❌", "location": "Need to gather", "notes": "HVAC, appliances"},
            {"doc": "Home inspection reports", "status": "✅", "location": "With agent", "notes": "From 2019 purchase"},
            {"doc": "Property tax records", "status": "✅", "location": "Online access", "notes": "Current and paid"},
        ]

        for doc in documents:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 2])

                with col1:
                    st.markdown(f"{doc['status']} {doc['doc']}")
                with col2:
                    st.markdown(doc['location'])
                with col3:
                    if doc['status'] == "❌":
                        if st.button("Found", key=f"doc_{doc['doc'][:8]}"):
                            st.success("Document located!")
                with col4:
                    st.markdown(f"*{doc['notes']}*")

    with tab4:
        st.markdown("##### Marketing Preparation")

        marketing_tasks = [
            {"task": "Professional photography", "status": "⏳", "priority": "High", "notes": "Scheduled for next Tuesday"},
            {"task": "Drone/aerial photos", "status": "❌", "priority": "Medium", "notes": "Include with photography"},
            {"task": "Virtual tour/3D scan", "status": "❌", "priority": "Medium", "notes": "Optional upgrade"},
            {"task": "Write compelling listing description", "status": "⏳", "priority": "High", "notes": "Agent drafting"},
            {"task": "Create property feature list", "status": "✅", "priority": "Medium", "notes": "Completed with agent"},
            {"task": "Gather neighborhood amenities info", "status": "✅", "priority": "Low", "notes": "Schools, shopping, etc."},
            {"task": "Plan open house logistics", "status": "❌", "priority": "Medium", "notes": "After photos complete"},
        ]

        for task in marketing_tasks:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 2])

                with col1:
                    st.markdown(f"{task['status']} {task['task']}")
                with col2:
                    priority_color = "red" if task['priority'] == "High" else "orange" if task['priority'] == "Medium" else "green"
                    st.markdown(f"<span style='color: {priority_color};'>{task['priority']}</span>", unsafe_allow_html=True)
                with col3:
                    if task['status'] == "❌":
                        if st.button("Complete", key=f"marketing_{task['task'][:10]}"):
                            st.success("Task completed!")
                with col4:
                    st.markdown(f"*{task['notes']}*")

    with tab5:
        st.markdown("##### Repairs & Updates")

        repairs = [
            {"item": "Fix leaky kitchen faucet", "priority": "High", "cost": "$150", "status": "⏳", "notes": "Plumber scheduled"},
            {"item": "Replace cracked outlet cover", "priority": "Medium", "cost": "$5", "status": "❌", "notes": "Hardware store trip"},
            {"item": "Caulk around master bathtub", "priority": "Medium", "cost": "$20", "status": "❌", "notes": "DIY project"},
            {"item": "Touch up paint in hallway", "priority": "Low", "cost": "$25", "status": "⏳", "notes": "With main painting"},
            {"item": "Replace air filter", "priority": "Low", "cost": "$15", "status": "✅", "notes": "Done monthly"},
        ]

        total_repair_cost = sum([int(repair['cost'].replace('$', '')) for repair in repairs])

        st.markdown(f"**Total Estimated Repair Cost:** ${total_repair_cost}")

        for repair in repairs:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])

                with col1:
                    st.markdown(f"{repair['status']} {repair['item']}")
                with col2:
                    priority_color = "red" if repair['priority'] == "High" else "orange" if repair['priority'] == "Medium" else "green"
                    st.markdown(f"<span style='color: {priority_color};'>{repair['priority']}</span>", unsafe_allow_html=True)
                with col3:
                    st.markdown(repair['cost'])
                with col4:
                    if repair['status'] == "❌":
                        if st.button("Fixed", key=f"repair_{repair['item'][:8]}"):
                            st.success("Repair completed!")
                with col5:
                    st.markdown(f"*{repair['notes']}*")

    # Action buttons
    st.markdown("#### 🎯 Quick Actions")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📧 Email Checklist"):
            st.success("Checklist emailed to you!")

    with col2:
        if st.button("📱 Share with Agent"):
            st.info("Checklist shared with your agent!")

    with col3:
        if st.button("📅 Schedule Services"):
            st.info("Service scheduling portal opened!")

    with col4:
        if st.button("💰 Get Cost Estimates"):
            st.info("Contractor quotes requested!")

def render_marketing_campaign_dashboard():
    """Marketing campaign performance and management dashboard"""
    st.subheader("📈 Marketing Campaign Dashboard")

    # Campaign overview
    st.markdown("#### 📊 Campaign Performance Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👀 Total Views", "2,847", delta="312 this week")
    with col2:
        st.metric("💕 Favorites", "89", delta="23 new")
    with col3:
        st.metric("📞 Inquiries", "47", delta="12 this week")
    with col4:
        st.metric("📅 Showings Scheduled", "18", delta="5 pending")

    # Detailed analytics tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Performance Analytics", "🌐 Online Listings", "📸 Marketing Materials", "📅 Showing Activity", "📈 Market Feedback"
    ])

    with tab1:
        st.markdown("##### Performance Analytics")

        # Views over time
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Daily Views (Last 14 Days)**")
            days = list(range(1, 15))
            views = [45, 52, 38, 67, 89, 123, 145, 167, 89, 76, 98, 134, 156, 187]

            fig_views = px.line(x=days, y=views, title="Daily Property Views")
            fig_views.update_layout(xaxis_title="Days", yaxis_title="Views")
            st.plotly_chart(fig_views, use_container_width=True)

        with col2:
            st.markdown("**Inquiry Sources**")
            sources = ["Zillow", "Realtor.com", "MLS", "Company Website", "Social Media", "Referral"]
            inquiries = [18, 15, 8, 4, 2, 0]

            fig_sources = px.pie(values=inquiries, names=sources, title="Lead Sources")
            st.plotly_chart(fig_sources, use_container_width=True)

        # Performance metrics
        st.markdown("**Key Performance Indicators**")
        metrics_data = [
            {"Metric": "View-to-Inquiry Rate", "Current": "1.65%", "Goal": "2.0%", "Status": "📈 Improving"},
            {"Metric": "Inquiry-to-Showing Rate", "Current": "38.3%", "Goal": "35%", "Status": "✅ Exceeding"},
            {"Metric": "Days on Market", "Current": "8 days", "Goal": "< 15 days", "Status": "🎯 On Target"},
            {"Metric": "Price per Sq Ft", "Current": "$263", "Goal": "$255", "Status": "💰 Above Market"}
        ]

        metrics_df = pd.DataFrame(metrics_data)
        st.dataframe(metrics_df, use_container_width=True)

    with tab2:
        st.markdown("##### Online Listing Status")

        listings = [
            {
                "platform": "MLS",
                "status": "🟢 Active",
                "views": "1,247",
                "leads": "23",
                "last_updated": "Today",
                "notes": "Primary listing source"
            },
            {
                "platform": "Zillow",
                "status": "🟢 Active",
                "views": "892",
                "leads": "18",
                "last_updated": "2 days ago",
                "notes": "High traffic source"
            },
            {
                "platform": "Realtor.com",
                "status": "🟢 Active",
                "views": "654",
                "leads": "15",
                "last_updated": "Today",
                "notes": "Good conversion rate"
            },
            {
                "platform": "Company Website",
                "status": "🟢 Active",
                "views": "234",
                "leads": "4",
                "last_updated": "1 day ago",
                "notes": "Brand awareness"
            },
            {
                "platform": "Facebook Marketplace",
                "status": "🟡 Pending",
                "views": "0",
                "leads": "0",
                "last_updated": "N/A",
                "notes": "Awaiting approval"
            }
        ]

        for listing in listings:
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1, 1, 1, 1, 2])

                with col1:
                    st.markdown(f"**{listing['platform']}**")
                with col2:
                    st.markdown(listing['status'])
                with col3:
                    st.markdown(listing['views'])
                with col4:
                    st.markdown(listing['leads'])
                with col5:
                    st.markdown(listing['last_updated'])
                with col6:
                    st.markdown(f"*{listing['notes']}*")

                st.markdown("---")

    with tab3:
        st.markdown("##### Marketing Materials")

        # Photo performance
        st.markdown("**Photo Performance Analysis**")

        photos = [
            {"photo": "Front Exterior", "views": "2,847", "saves": "89", "engagement": "3.1%"},
            {"photo": "Living Room", "views": "2,203", "saves": "67", "engagement": "3.0%"},
            {"photo": "Kitchen", "views": "2,156", "saves": "78", "engagement": "3.6%"},
            {"photo": "Master Bedroom", "views": "1,834", "saves": "45", "engagement": "2.5%"},
            {"photo": "Backyard", "views": "1,623", "saves": "52", "engagement": "3.2%"}
        ]

        for photo in photos:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                with col1:
                    st.markdown(f"📸 **{photo['photo']}**")
                with col2:
                    st.markdown(f"👀 {photo['views']}")
                with col3:
                    st.markdown(f"💾 {photo['saves']}")
                with col4:
                    engagement_float = float(photo['engagement'].replace('%', ''))
                    color = "green" if engagement_float >= 3.0 else "orange"
                    st.markdown(f"<span style='color: {color};'>📈 {photo['engagement']}</span>", unsafe_allow_html=True)

        # Marketing materials status
        st.markdown("**Marketing Materials Checklist**")
        materials = [
            {"item": "Professional Photos (25 images)", "status": "✅ Complete"},
            {"item": "Property Description", "status": "✅ Complete"},
            {"item": "Feature Sheet/Flyer", "status": "✅ Complete"},
            {"item": "Virtual Tour", "status": "⏳ In Progress"},
            {"item": "Drone/Aerial Video", "status": "❌ Pending"},
            {"item": "Social Media Posts", "status": "✅ Posted Daily"}
        ]

        for material in materials:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"• {material['item']}")
            with col2:
                st.markdown(material['status'])

    with tab4:
        st.markdown("##### Showing Activity")

        # Upcoming showings
        st.markdown("**Scheduled Showings**")

        showings = [
            {
                "date": "Today",
                "time": "2:00 PM",
                "type": "Private Showing",
                "agent": "Sarah Johnson (Buyer Agent)",
                "notes": "Pre-approved buyer, serious interest"
            },
            {
                "date": "Tomorrow",
                "time": "10:00 AM",
                "type": "Private Showing",
                "agent": "Mike Chen (Buyer Agent)",
                "notes": "First-time homebuyer"
            },
            {
                "date": "Saturday",
                "time": "1:00-4:00 PM",
                "type": "Open House",
                "agent": "Your Listing Agent",
                "notes": "First open house event"
            },
            {
                "date": "Sunday",
                "time": "11:00 AM",
                "type": "Private Showing",
                "agent": "Lisa Rodriguez (Buyer Agent)",
                "notes": "Investor client"
            }
        ]

        for showing in showings:
            with st.container():
                col1, col2, col3, col4 = st.columns([1, 1, 2, 2])

                with col1:
                    st.markdown(f"**📅 {showing['date']}**")
                with col2:
                    st.markdown(f"🕐 {showing['time']}")
                with col3:
                    st.markdown(f"**{showing['type']}**")
                    st.markdown(f"*{showing['agent']}*")
                with col4:
                    st.markdown(showing['notes'])

                st.markdown("---")

        # Showing statistics
        st.markdown("**Showing Statistics (Last 30 Days)**")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Showings", "18")
        with col2:
            st.metric("Private Showings", "14")
        with col3:
            st.metric("Open Houses", "2")
        with col4:
            st.metric("Avg per Week", "4.5")

    with tab5:
        st.markdown("##### Market Feedback & Insights")

        # Feedback from showings
        st.markdown("**Agent & Buyer Feedback**")

        feedback = [
            {
                "source": "Sarah Johnson (Buyer Agent)",
                "date": "2 days ago",
                "rating": "⭐⭐⭐⭐⭐",
                "comment": "Beautiful home, well-maintained. Buyers loved the kitchen updates.",
                "concerns": "Slight concern about backyard size for their dogs."
            },
            {
                "source": "Mike Chen (Buyer Agent)",
                "date": "3 days ago",
                "rating": "⭐⭐⭐⭐",
                "comment": "Great location and condition. Competitive price point.",
                "concerns": "Buyers prefer a larger master bathroom."
            },
            {
                "source": "Lisa Rodriguez (Buyer Agent)",
                "date": "1 week ago",
                "rating": "⭐⭐⭐⭐⭐",
                "comment": "Excellent investment opportunity. Cash buyer interested.",
                "concerns": "None - ready to make offer."
            }
        ]

        for fb in feedback:
            with st.expander(f"{fb['source']} - {fb['rating']} ({fb['date']})"):
                st.markdown(f"**Comment:** {fb['comment']}")
                if fb['concerns']:
                    st.markdown(f"**Concerns:** {fb['concerns']}")

        # Market positioning analysis
        st.markdown("**Competitive Market Analysis**")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Strengths vs Competition:**")
            st.markdown("• ✅ Superior kitchen updates")
            st.markdown("• ✅ Better curb appeal")
            st.markdown("• ✅ Competitive pricing")
            st.markdown("• ✅ Excellent school district")

        with col2:
            st.markdown("**Areas for Improvement:**")
            st.markdown("• 🔸 Smaller master bathroom")
            st.markdown("• 🔸 Limited backyard space")
            st.markdown("• 🔸 Single-car garage only")

        # Recommendations
        st.info("💡 **Agent Recommendations:** Continue current marketing strategy. Consider hosting second open house to capture weekend traffic. Price point is well-positioned for quick sale.")

def render_seller_communication_portal():
    """Communication hub for seller-agent interaction"""
    st.subheader("💬 Seller Communication Portal")

    # Communication overview
    st.markdown("#### 📊 Communication Summary")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📧 Messages Today", "5", delta="2 unread")
    with col2:
        st.metric("📞 Calls This Week", "3", delta="1 scheduled")
    with col3:
        st.metric("📅 Updates Sent", "12", delta="Weekly report due")
    with col4:
        st.metric("🏠 Showing Reports", "8", delta="3 new")

    # Communication tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Messages", "📞 Calls & Meetings", "📊 Reports & Updates", "📅 Showing Feedback", "📋 Documents"
    ])

    with tab1:
        st.markdown("##### Message Center")

        # Quick message composer
        with st.expander("✏️ Send New Message"):
            message_to = st.selectbox("To:", ["Your Listing Agent", "Transaction Coordinator", "Marketing Team"])
            message_subject = st.text_input("Subject:")
            message_body = st.text_area("Message:", height=100)

            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("📤 Send Message"):
                    st.success("Message sent!")

        # Message history
        st.markdown("**Recent Messages**")

        messages = [
            {
                "from": "Your Listing Agent",
                "subject": "Showing Report - Great Feedback!",
                "time": "2 hours ago",
                "preview": "Had two showings today with very positive feedback. The buyers loved...",
                "unread": True
            },
            {
                "from": "Transaction Coordinator",
                "subject": "Document Upload Required",
                "time": "1 day ago",
                "preview": "Please upload the signed property disclosure form to complete...",
                "unread": True
            },
            {
                "from": "Your Listing Agent",
                "subject": "Weekly Market Update",
                "time": "3 days ago",
                "preview": "Market activity remains strong in your neighborhood. Three new...",
                "unread": False
            },
            {
                "from": "Marketing Team",
                "subject": "Photos Ready for Approval",
                "time": "5 days ago",
                "preview": "Professional photography is complete! Please review the gallery...",
                "unread": False
            }
        ]

        for message in messages:
            unread_style = "background-color: #E3F2FD;" if message['unread'] else "background-color: white;"

            with st.container():
                st.markdown(f"""
                <div style="{unread_style} padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #2196F3;">
                    <div style="display: flex; justify-content: between; margin-bottom: 5px;">
                        <strong>{'📧 ' if message['unread'] else '✉️ '}{message['subject']}</strong>
                        <span style="color: #666; font-size: 0.9em; margin-left: auto;">{message['time']}</span>
                    </div>
                    <div style="color: #666; font-size: 0.9em; margin-bottom: 5px;">From: {message['from']}</div>
                    <div style="color: #333;">{message['preview']}</div>
                </div>
                """, unsafe_allow_html=True)

                col1, col2, col3 = st.columns([1, 1, 4])
                with col1:
                    if st.button("📖 Read", key=f"read_{message['subject'][:10]}"):
                        st.info("Opening full message...")
                with col2:
                    if st.button("↩️ Reply", key=f"reply_{message['subject'][:10]}"):
                        st.info("Reply window opened...")

    with tab2:
        st.markdown("##### Calls & Meetings")

        # Upcoming meetings
        st.markdown("**Upcoming Calls & Meetings**")

        meetings = [
            {
                "title": "Weekly Check-in Call",
                "date": "Tomorrow",
                "time": "10:00 AM",
                "type": "Phone Call",
                "agenda": "Discuss showing feedback and next steps"
            },
            {
                "title": "Marketing Strategy Review",
                "date": "Friday",
                "time": "2:00 PM",
                "type": "Video Call",
                "agenda": "Review performance metrics and adjust strategy"
            }
        ]

        for meeting in meetings:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 2])

                with col1:
                    st.markdown(f"**📅 {meeting['title']}**")
                    st.markdown(f"*{meeting['agenda']}*")
                with col2:
                    st.markdown(meeting['date'])
                with col3:
                    st.markdown(meeting['time'])
                with col4:
                    if st.button("📞 Join", key=f"join_{meeting['title'][:8]}"):
                        st.success("Meeting link opened!")

                st.markdown("---")

        # Call history
        st.markdown("**Recent Call History**")

        calls = [
            {
                "date": "Yesterday",
                "duration": "15 minutes",
                "type": "📞 Phone Call",
                "summary": "Discussed pricing strategy and showing feedback"
            },
            {
                "date": "3 days ago",
                "duration": "22 minutes",
                "type": "💻 Video Call",
                "summary": "Reviewed marketing materials and listing photos"
            }
        ]

        for call in calls:
            st.markdown(f"**{call['type']} - {call['date']}** ({call['duration']})")
            st.markdown(f"*{call['summary']}*")
            st.markdown("---")

    with tab3:
        st.markdown("##### Reports & Updates")

        # Report schedule
        st.markdown("**Scheduled Reports**")

        reports = [
            {
                "report": "Weekly Activity Report",
                "frequency": "Every Monday",
                "last_sent": "3 days ago",
                "next_due": "In 4 days"
            },
            {
                "report": "Showing Summary",
                "frequency": "After each showing",
                "last_sent": "Today",
                "next_due": "As needed"
            },
            {
                "report": "Market Analysis Update",
                "frequency": "Bi-weekly",
                "last_sent": "1 week ago",
                "next_due": "Next week"
            }
        ]

        for report in reports:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"**{report['report']}**")
            with col2:
                st.markdown(report['frequency'])
            with col3:
                st.markdown(report['last_sent'])
            with col4:
                st.markdown(report['next_due'])

        # Recent reports
        st.markdown("**Recent Reports**")

        with st.expander("📊 Weekly Activity Report - January 6, 2026"):
            st.markdown("""
            **This Week's Highlights:**
            - 23 new online views (+18% from last week)
            - 5 showing appointments scheduled
            - 2 private showings completed with positive feedback
            - Featured in weekend newsletter to 2,500+ subscribers

            **Marketing Performance:**
            - Zillow: 12 inquiries, 89 favorites
            - Realtor.com: 8 inquiries, 45 favorites
            - MLS: 3 agent inquiries

            **Next Week's Plans:**
            - Schedule professional photography touch-ups
            - Host first open house on Saturday
            - Follow up with interested buyers from this week
            """)

        with st.expander("🏠 Showing Report - Today 2:00 PM"):
            st.markdown("""
            **Showing Details:**
            - Buyer Agent: Sarah Johnson, ABC Realty
            - Showing Duration: 25 minutes
            - Buyer Profile: Pre-approved first-time buyers, $450K budget

            **Feedback:**
            - Overall Impression: Very positive
            - Loved: Updated kitchen, hardwood floors, neighborhood
            - Concerns: Wanted larger master bathroom
            - Interest Level: High - planning second viewing this weekend

            **Agent Comments:**
            "Serious buyers who have been looking for 3 months. Your home checks most of their boxes. They'll likely make an offer after second showing."
            """)

    with tab4:
        st.markdown("##### Showing Feedback")

        # Feedback summary
        st.markdown("**Feedback Summary (Last 30 Days)**")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Overall Rating", "4.6/5", delta="Excellent")
        with col2:
            st.metric("Would Recommend", "92%", delta="Above average")
        with col3:
            st.metric("Serious Interest", "67%", delta="High engagement")

        # Detailed feedback
        st.markdown("**Recent Feedback**")

        detailed_feedback = [
            {
                "date": "Today 2:00 PM",
                "agent": "Sarah Johnson",
                "rating": 5,
                "highlights": "Kitchen updates, hardwood floors, location",
                "concerns": "Master bathroom size",
                "likelihood": "High - second showing planned"
            },
            {
                "date": "Yesterday 11:00 AM",
                "agent": "Mike Chen",
                "rating": 4,
                "highlights": "Move-in ready condition, good value",
                "concerns": "Prefers larger backyard",
                "likelihood": "Medium - still considering options"
            },
            {
                "date": "2 days ago 3:00 PM",
                "agent": "Lisa Rodriguez",
                "rating": 5,
                "highlights": "Investment potential, neighborhood growth",
                "concerns": "None mentioned",
                "likelihood": "Very High - cash buyer ready to offer"
            }
        ]

        for feedback in detailed_feedback:
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    st.markdown(f"**📅 {feedback['date']}**")
                    st.markdown(f"*Agent: {feedback['agent']}*")

                with col2:
                    st.markdown(f"**Rating:** {'⭐' * feedback['rating']}")
                    st.markdown(f"**Highlights:** {feedback['highlights']}")
                    if feedback['concerns'] != "None mentioned":
                        st.markdown(f"**Concerns:** {feedback['concerns']}")

                with col3:
                    likelihood_color = "green" if "High" in feedback['likelihood'] else "orange" if "Medium" in feedback['likelihood'] else "red"
                    st.markdown(f"<span style='color: {likelihood_color};'>**{feedback['likelihood']}**</span>", unsafe_allow_html=True)

                st.markdown("---")

    with tab5:
        st.markdown("##### Document Management")

        # Document categories
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📋 Required Documents**")

            required_docs = [
                {"doc": "Property Disclosure", "status": "✅ Complete"},
                {"doc": "Listing Agreement", "status": "✅ Complete"},
                {"doc": "MLS Listing Form", "status": "✅ Complete"},
                {"doc": "Lead Paint Disclosure", "status": "⏳ Pending"},
                {"doc": "HOA Documents", "status": "N/A"},
                {"doc": "Survey/Plat", "status": "⏳ Requested"}
            ]

            for doc in required_docs:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"• {doc['doc']}")
                with col_b:
                    st.markdown(doc['status'])

        with col2:
            st.markdown("**📁 Shared Documents**")

            shared_docs = [
                {"doc": "Professional Photos", "date": "5 days ago"},
                {"doc": "Marketing Flyer", "date": "4 days ago"},
                {"doc": "CMA Report", "date": "1 week ago"},
                {"doc": "Listing Analytics", "date": "Yesterday"},
                {"doc": "Showing Reports", "date": "Today"}
            ]

            for doc in shared_docs:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"📄 {doc['doc']}")
                with col_b:
                    if st.button("📥", key=f"download_{doc['doc'][:8]}"):
                        st.success("Downloaded!")

        # Document upload
        st.markdown("**📤 Upload Documents**")

        col1, col2 = st.columns([3, 1])
        with col1:
            uploaded_file = st.file_uploader("Choose file", type=['pdf', 'doc', 'docx', 'jpg', 'png'])
        with col2:
            if st.button("Upload"):
                if uploaded_file:
                    st.success("Document uploaded successfully!")
                else:
                    st.warning("Please select a file first.")

def render_transaction_timeline():
    """Transaction timeline and offer management"""
    st.subheader("📅 Transaction Timeline & Offers")

    # Timeline overview
    st.markdown("#### 🎯 Sale Progress")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📅 Days Listed", "8 days")
    with col2:
        st.metric("👀 Total Interest", "High")
    with col3:
        st.metric("🤝 Offers Received", "2")
    with col4:
        st.metric("📊 Current Status", "Active")

    # Main timeline tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Current Offers", "📅 Timeline", "🔄 Next Steps", "📊 Milestones"
    ])

    with tab1:
        st.markdown("##### Active Offers")

        offers = [
            {
                "buyer": "Johnson Family (Sarah Johnson, Buyer Agent)",
                "offer_price": "$492,000",
                "earnest_money": "$10,000",
                "financing": "Conventional - Pre-approved",
                "closing_date": "30 days",
                "contingencies": "Inspection, Financing",
                "status": "🟡 Under Review",
                "expires": "Tomorrow 5:00 PM",
                "notes": "Strong offer, motivated buyers"
            },
            {
                "buyer": "Investment Group (Lisa Rodriguez, Buyer Agent)",
                "offer_price": "$485,000",
                "earnest_money": "$25,000",
                "financing": "Cash Offer",
                "closing_date": "15 days",
                "contingencies": "Inspection Only (7 days)",
                "status": "🟢 Active",
                "expires": "Today 6:00 PM",
                "notes": "Cash offer, quick close, investor buyer"
            }
        ]

        for i, offer in enumerate(offers):
            with st.container():
                st.markdown(f"**Buyer: {offer['buyer']}**")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Offer Price", offer['offer_price'])
                with col2:
                    st.metric("Earnest Money", offer['earnest_money'])
                with col3:
                    st.metric("Closing Date", offer['closing_date'])
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**Financing:** {offer['financing']}")
                    st.markdown(f"**Contingencies:** {offer['contingencies']}")
                with col_b:
                    st.markdown(f"**Status:** {offer['status']}")
                    st.markdown(f"**Expires:** {offer['expires']}")
                
                st.markdown(f"*Notes: {offer['notes']}*")
                
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                with btn_col1:
                    if st.button("✅ Accept Offer", key=f"accept_{i}"):
                        st.success("Offer accepted! Moving to closing...")
                with btn_col2:
                    if st.button("📝 Counter Offer", key=f"counter_{i}"):
                        st.info("Counter offer window opened...")
                with btn_col3:
                    if st.button("❌ Reject Offer", key=f"reject_{i}"):
                        st.warning("Offer rejected.")
                
                st.markdown("---")

    with tab2:
        st.markdown("##### Listing Timeline")

        timeline_events = [
            {"date": "Jan 11", "event": "2nd Offer Received", "status": "Active"},
            {"date": "Jan 9", "event": "1st Offer Received", "status": "Under Review"},
            {"date": "Jan 6", "event": "Price Adjusted to $495K", "status": "Completed"},
            {"date": "Jan 4", "event": "Professional Photography", "status": "Completed"},
            {"date": "Jan 3", "event": "Listing Agreement Signed", "status": "Completed"},
            {"date": "Jan 1", "event": "Initial Consultation", "status": "Completed"}
        ]

        for event in timeline_events:
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                st.markdown(f"**{event['date']}**")
            with col2:
                st.markdown(event['event'])
            with col3:
                st.markdown(event['status'])

    with tab3:
        st.markdown("##### Next Steps in the Process")

        next_steps = [
            {"step": "Review current offers with agent", "priority": "High", "timing": "Today"},
            {"step": "Provide counter offer to Johnson family", "priority": "High", "timing": "Within 24 hours"},
            {"step": "Gather HOA resale certificate", "priority": "Medium", "timing": "Next 3 days"},
            {"step": "Schedule appraisal (once under contract)", "priority": "High", "timing": "TBD"}
        ]

        for step in next_steps:
            with st.container():
                st.markdown(f"**{step['step']}**")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"Priority: {step['priority']}")
                with col2:
                    st.markdown(f"Timing: {step['timing']}")
                st.markdown("---")

    with tab4:
        st.markdown("##### Key Milestones Tracker")

        milestones = [
            {"milestone": "Pre-listing Prep", "status": "100%", "completed": True},
            {"milestone": "Marketing Phase", "status": "100%", "completed": True},
            {"milestone": "Active Listing", "status": "80%", "completed": False},
            {"milestone": "Offer Negotiation", "status": "40%", "completed": False},
            {"milestone": "Under Contract", "status": "0%", "completed": False},
            {"milestone": "Closing Process", "status": "0%", "completed": False}
        ]

        for m in milestones:
            st.markdown(f"**{m['milestone']}**")
            st.progress(int(m['status'].replace('%', '')))

def render_seller_analytics():
    """Comprehensive seller analytics and insights"""
    st.subheader("📊 Seller Analytics & Insights")

    # Analytics overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Projected Net Proceeds", "$462,150", delta="$8,500 vs. initial estimate")
    with col2:
        st.metric("📈 Market Performance", "Above Average", delta="Top 15% in area")
    with col3:
        st.metric("⏱️ Est. Time to Contract", "12 days", delta="3 days faster than average")
    with col4:
        st.metric("🎯 Success Probability", "92%", delta="Strong indicators")

    # Detailed analytics
    tab1, tab2, tab3, tab4 = st.tabs([
        "💰 Financial Analysis", "📊 Market Performance", "🎯 Success Predictors", "📈 Competitive Position"
    ])

    with tab1:
        st.markdown("##### Financial Projection")

        # Net proceeds calculation
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📊 Estimated Sale Proceeds**")

            # Financial breakdown
            sale_price = 492000
            commission = sale_price * 0.06
            closing_costs = sale_price * 0.015
            repairs = 2500
            staging = 1200
            other_costs = 800

            financial_data = [
                {"Item": "Gross Sale Price", "Amount": f"${sale_price:,}"},
                {"Item": "Real Estate Commission (6%)", "Amount": f"-${commission:,.0f}"},
                {"Item": "Closing Costs (~1.5%)", "Amount": f"-${closing_costs:,.0f}"},
                {"Item": "Pre-Sale Repairs", "Amount": f"-${repairs:,}"},
                {"Item": "Staging Costs", "Amount": f"-${staging:,}"},
                {"Item": "Other Selling Costs", "Amount": f"-${other_costs:,}"},
                {"Item": "**Net Proceeds**", "Amount": f"**${sale_price - commission - closing_costs - repairs - staging - other_costs:,.0f}**"}
            ]

            for item in financial_data:
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    if item["Item"].startswith("**"):
                        st.markdown(item["Item"])
                    else:
                        st.markdown(f"• {item['Item']}")
                with col_b:
                    st.markdown(item["Amount"])

        with col2:
            # Visual breakdown
            costs = ["Commission", "Closing Costs", "Repairs", "Other", "Net Proceeds"]
            amounts = [commission, closing_costs, repairs, staging + other_costs, sale_price - commission - closing_costs - repairs - staging - other_costs]

            fig = px.pie(values=amounts, names=costs, title="Sale Proceeds Breakdown")
            st.plotly_chart(fig, use_container_width=True)

        # ROI Analysis
        st.markdown("**🏠 Return on Investment Analysis**")

        original_purchase = 385000
        improvements = 15000
        total_investment = original_purchase + improvements
        total_return = sale_price - commission - closing_costs - repairs - staging - other_costs
        roi = ((total_return - total_investment) / total_investment) * 100

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Original Purchase", f"${original_purchase:,}")
        with col2:
            st.metric("Total Improvements", f"${improvements:,}")
        with col3:
            st.metric("Total Investment", f"${total_investment:,}")
        with col4:
            st.metric("ROI", f"{roi:.1f}%", delta="Excellent return")

    with tab2:
        st.markdown("##### Market Performance Analysis")

        # Comparison metrics
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📊 Your Property vs. Market Average**")

            comparison_data = [
                {"Metric": "Days on Market", "Your Property": "8 days", "Market Average": "22 days", "Performance": "🟢 64% Faster"},
                {"Metric": "List-to-Sale Price", "Your Property": "99.4%", "Market Average": "96.8%", "Performance": "🟢 2.6% Better"},
                {"Metric": "Showings per Week", "Your Property": "9", "Market Average": "4.5", "Performance": "🟢 2x More"},
                {"Metric": "Inquiry Rate", "Your Property": "1.65%", "Market Average": "1.2%", "Performance": "🟢 38% Higher"}
            ]

            for data in comparison_data:
                st.markdown(f"**{data['Metric']}:**")
                col_a, col_b, col_c = st.columns([1, 1, 1])
                with col_a:
                    st.markdown(f"You: {data['Your Property']}")
                with col_b:
                    st.markdown(f"Market: {data['Market Average']}")
                with col_c:
                    st.markdown(data['Performance'])
                st.markdown("---")

        with col2:
            # Performance trends
            st.markdown("**📈 Performance Trends**")

            weeks = ["Week 1", "Week 2"]
            views = [1456, 1391]
            inquiries = [28, 19]

            fig_performance = go.Figure()
            fig_performance.add_trace(go.Scatter(x=weeks, y=views, mode='lines+markers', name='Views', yaxis='y'))
            fig_performance.add_trace(go.Scatter(x=weeks, y=inquiries, mode='lines+markers', name='Inquiries', yaxis='y2'))

            fig_performance.update_layout(
                title="Weekly Performance Trends",
                yaxis=dict(title="Views", side="left"),
                yaxis2=dict(title="Inquiries", side="right", overlaying="y"),
                legend=dict(x=0.7, y=1)
            )
            st.plotly_chart(fig_performance, use_container_width=True)

        # Market conditions impact
        st.markdown("**🌍 Market Conditions Analysis**")

        conditions = [
            {"Factor": "Interest Rates", "Current": "7.25%", "Trend": "📈 Stable", "Impact": "Neutral"},
            {"Factor": "Inventory Levels", "Current": "2.1 months", "Trend": "📉 Low", "Impact": "🟢 Favorable"},
            {"Factor": "Buyer Demand", "Current": "High", "Trend": "📈 Strong", "Impact": "🟢 Favorable"},
            {"Factor": "Seasonal Timing", "Current": "Peak Season", "Trend": "📈 Optimal", "Impact": "🟢 Favorable"}
        ]

        for condition in conditions:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"**{condition['Factor']}**")
            with col2:
                st.markdown(condition['Current'])
            with col3:
                st.markdown(condition['Trend'])
            with col4:
                impact_color = "green" if "Favorable" in condition['Impact'] else "orange" if "Neutral" in condition['Impact'] else "red"
                st.markdown(f"<span style='color: {impact_color};'>{condition['Impact']}</span>", unsafe_allow_html=True)

    with tab3:
        st.markdown("##### Success Probability Indicators")

        # Success factors
        success_factors = [
            {"Factor": "Competitive Pricing", "Score": 95, "Weight": "25%", "Impact": "Very High"},
            {"Factor": "Property Condition", "Score": 88, "Weight": "20%", "Impact": "High"},
            {"Factor": "Market Timing", "Score": 92, "Weight": "20%", "Impact": "Very High"},
            {"Factor": "Marketing Quality", "Score": 90, "Weight": "15%", "Impact": "High"},
            {"Factor": "Agent Performance", "Score": 94, "Weight": "10%", "Impact": "High"},
            {"Factor": "Location Desirability", "Score": 85, "Weight": "10%", "Impact": "Medium-High"}
        ]

        for factor in success_factors:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

            with col1:
                st.markdown(f"**{factor['Factor']}**")
                st.progress(factor['Score'] / 100)

            with col2:
                st.markdown(f"{factor['Score']}/100")

            with col3:
                st.markdown(factor['Weight'])

            with col4:
                impact_color = "green" if "Very High" in factor['Impact'] else "blue" if "High" in factor['Impact'] else "orange"
                st.markdown(f"<span style='color: {impact_color};'>{factor['Impact']}</span>", unsafe_allow_html=True)

        # Overall score calculation
        weighted_score = sum([factor['Score'] * float(factor['Weight'].replace('%', '')) / 100 for factor in success_factors])

        st.markdown(f"**🎯 Overall Success Score: {weighted_score:.1f}/100**")

        if weighted_score >= 90:
            st.success("🟢 **Excellent** - Very high probability of successful sale at or above asking price")
        elif weighted_score >= 80:
            st.info("🔵 **Good** - Strong probability of successful sale within market timeframe")
        elif weighted_score >= 70:
            st.warning("🟡 **Fair** - Moderate probability, may need strategy adjustments")
        else:
            st.error("🔴 **Needs Improvement** - Consider addressing key factors before listing")

    with tab4:
        st.markdown("##### Competitive Market Position")

        # Direct competitors
        st.markdown("**🏠 Direct Competitors Currently Listed**")

        competitors = [
            {
                "address": "1456 Maple Street",
                "price": "$515,000",
                "days_listed": "45 days",
                "beds_baths": "3 bed / 2.5 bath",
                "sqft": "1,920 sqft",
                "advantage": "Better condition, lower price",
                "risk": "Similar features, longer on market"
            },
            {
                "address": "1678 Oak Avenue",
                "price": "$475,000",
                "days_listed": "12 days",
                "beds_baths": "3 bed / 2 bath",
                "sqft": "1,750 sqft",
                "advantage": "Larger, better updates",
                "risk": "Direct competition, similar price"
            },
            {
                "address": "1234 Pine Drive",
                "price": "$525,000",
                "days_listed": "8 days",
                "beds_baths": "4 bed / 2.5 bath",
                "sqft": "2,100 sqft",
                "advantage": "Better value per sqft",
                "risk": "Larger home, higher price point"
            }
        ]

        for competitor in competitors:
            with st.expander(f"{competitor['address']} - {competitor['price']} ({competitor['days_listed']})"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Size:** {competitor['beds_baths']}, {competitor['sqft']}")
                    st.markdown(f"**Your Advantage:** {competitor['advantage']}")

                with col2:
                    st.markdown(f"**Days Listed:** {competitor['days_listed']}")
                    st.markdown(f"**Competitive Risk:** {competitor['risk']}")

        # Market positioning summary
        st.markdown("**🎯 Strategic Positioning Summary**")

        positioning = [
            {"Aspect": "Price Point", "Position": "Competitive", "Strategy": "Priced to move quickly while maximizing value"},
            {"Aspect": "Condition", "Position": "Superior", "Strategy": "Highlight move-in ready status and recent updates"},
            {"Aspect": "Marketing", "Position": "Leading", "Strategy": "Professional presentation generating strong interest"},
            {"Aspect": "Timing", "Position": "Optimal", "Strategy": "Listed during peak buyer activity period"}
        ]

        for pos in positioning:
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                st.markdown(f"**{pos['Aspect']}:**")
            with col2:
                position_color = "green" if pos['Position'] in ["Superior", "Leading", "Optimal"] else "blue" if pos['Position'] == "Competitive" else "orange"
                st.markdown(f"<span style='color: {position_color};'>{pos['Position']}</span>", unsafe_allow_html=True)
            with col3:
                st.markdown(f"*{pos['Strategy']}*")

        # Recommendations
        st.info("""
        💡 **Strategic Recommendations:**
        - Maintain current pricing strategy - well-positioned vs. competition
        - Emphasize move-in ready condition and recent updates in marketing
        - Monitor competitor price changes and adjust strategy if needed
        - Current positioning should result in sale within 2-3 weeks at or near asking price
        """)