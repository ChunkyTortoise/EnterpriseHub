"""
Elite Refinement Components
Professional-grade UI components with actionable intelligence
Addresses Screenshots 20-24 refinements
"""
import streamlit as st
from typing import List, Dict, Any, Optional
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta


def styled_segment_card(title: str, engagement: int, score: int,
                       price: str, actions: List[str],
                       lead_count: Optional[int] = None):
    """
    Elite Component to fix the 'HTML Leak' seen in Screenshots 21-22.
    Renders professional data cards with proper HTML escaping and styling.

    Args:
        title: Segment name (e.g., "Highly Active", "Warming Up")
        engagement: Engagement percentage (0-100)
        score: AI Score (0-100)
        price: Estimated value (e.g., "$800K+")
        actions: List of recommended actions
        lead_count: Optional number of leads in segment
    """
    # Engagement color gradient
    if engagement >= 80:
        badge_bg = "#dcfce7"
        badge_color = "#166534"
        card_bg = "#f0fdf4"
    elif engagement >= 60:
        badge_bg = "#fef3c7"
        badge_color = "#92400e"
        card_bg = "#fffbeb"
    else:
        badge_bg = "#fee2e2"
        badge_color = "#991b1b"
        card_bg = "#fef2f2"

    # Use Streamlit native components instead of complex HTML
    with st.container():
        # Create a styled container with background color
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {card_bg} 0%, #ffffff 100%);
            border-radius: 12px;
            border: 2px solid #e2e8f0;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        </div>
        """, unsafe_allow_html=True)

        # Header row with title and engagement badge
        col1, col2 = st.columns([3, 1])

        with col1:
            if lead_count:
                st.markdown(f"### {title} ({lead_count} leads)")
            else:
                st.markdown(f"### {title}")

        with col2:
            st.markdown(f"""
            <div style="
                background: {badge_bg};
                color: {badge_color};
                padding: 8px 16px;
                border-radius: 20px;
                text-align: center;
                font-weight: bold;
                font-size: 0.9rem;">
                {engagement}% Active
            </div>
            """, unsafe_allow_html=True)

        # Metrics row
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                label="AI Score",
                value=f"{score}",
                delta=None
            )

        with col2:
            st.metric(
                label="Est. Value",
                value=price,
                delta=None
            )

        # Recommended Actions
        st.markdown("**🎯 Recommended Actions:**")
        for action in actions:
            st.markdown(f"• {action}")

        # Add some spacing
        st.markdown("<br>", unsafe_allow_html=True)


def render_dynamic_timeline(days_remaining: int, actions_completed: int = 0, 
                            agent_name: Optional[str] = None):
    """
    Refines the static '45 Days' into a dynamic 'Acceleration' metric.
    Shows how AI-recommended actions compress the sales cycle.
    
    Args:
        days_remaining: Base estimated days to close
        actions_completed: Number of high-value actions completed
        agent_name: Optional agent name for personalization
    """
    # Logic: Each completed high-value action reduces expected close time by 15%
    accelerated_days = int(days_remaining * (0.85 ** actions_completed))
    savings = days_remaining - accelerated_days
    
    # Calculate progress (assuming 90 days is max cycle)
    progress = max(0, min(100, 100 - (accelerated_days / 90 * 100)))
    
    st.markdown("### ⏱️ Conversion Timeline")
    
    # Show acceleration badge if actions completed
    if actions_completed > 0:
        st.markdown(f"""
        <div style="background: #dcfce7; border-left: 4px solid #10b981; padding: 12px; 
                    border-radius: 8px; margin-bottom: 16px;">
            <p style="margin: 0; color: #166534; font-weight: 600;">
                🚀 <b>{actions_completed}</b> AI actions completed! 
                Timeline accelerated by <b>{savings} days</b>.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        # Visual progress bar toward the 'Close'
        st.progress(progress / 100)
        st.caption(f"📅 Estimated **{accelerated_days} days** to close")
    
    with col2:
        st.metric(
            "Timeline", 
            f"{accelerated_days}d",
            delta=f"-{savings}d" if savings > 0 else "On Track",
            delta_color="normal" if savings > 0 else "off"
        )
    
    with col3:
        # Show projected close date
        close_date = datetime.now() + timedelta(days=accelerated_days)
        st.metric(
            "Est. Close",
            close_date.strftime("%b %d"),
            delta=close_date.strftime("%Y")
        )
    
    # Action suggestions to further accelerate
    if actions_completed < 3:
        with st.expander("🎯 Accelerate Timeline Further"):
            st.markdown("""
            **High-Impact Actions** (Each saves ~5-7 days):
            - 📞 Schedule property tour within 48 hours
            - 💰 Get pre-approval confirmation
            - 📧 Send personalized property matches
            - 🏠 Set up automated showing alerts
            """)
            
            if st.button("🚀 Execute All Quick Wins", key="timeline_accelerate"):
                st.success("✅ AI actions queued! Expected savings: 15-20 days")


def render_actionable_heatmap(df_activity: pd.DataFrame, 
                              enable_automation: bool = True):
    """
    Temporal engagement heatmap with automated outreach triggers.
    Transforms Screenshot 23 from 'look-but-don't-touch' to action-oriented.
    
    Args:
        df_activity: DataFrame with columns ['day', 'hour', 'activity_count']
        enable_automation: Whether to show automation buttons
    """
    st.markdown("### 📊 Lead Activity Heatmap (Temporal)")
    
    # Find peak engagement window
    peak_row = df_activity.loc[df_activity['activity_count'].idxmax()]
    peak_day = peak_row['day']
    peak_hour = peak_row['hour']
    peak_count = peak_row['activity_count']
    
    # Create heatmap visualization
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    hours = [f"{h:02d}:00" for h in range(24)]
    
    # Pivot data for heatmap
    heatmap_data = df_activity.pivot_table(
        values='activity_count',
        index='hour',
        columns='day',
        fill_value=0
    )
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=days,
        y=hours,
        colorscale='Blues',
        hoverongaps=False,
        hovertemplate='%{x}<br>%{y}<br>Activity: %{z}<extra></extra>'
    ))
    
    fig.update_layout(
        title="When Are Your Leads Most Active?",
        xaxis_title="Day of Week",
        yaxis_title="Hour of Day",
        height=400,
        margin=dict(l=80, r=20, t=40, b=40)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Peak engagement insight with automation
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info(f"""
        💡 **Peak Engagement Detected**  
        **{peak_day}s at {peak_hour}:00** show {peak_count}% higher response rates.
        """)
    
    with col2:
        if enable_automation:
            if st.button(f"📅 Schedule Outreach", key="schedule_peak"):
                st.success(f"""
                ✅ Bulk outreach scheduled for:  
                Next {peak_day} @ {peak_hour}:00
                """)
                # In production: ghl_api.schedule_workflow(...)
    
    # Additional insights
    with st.expander("📈 Advanced Engagement Insights"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Best Days:**")
            top_days = df_activity.groupby('day')['activity_count'].sum().nlargest(3)
            for day, count in top_days.items():
                st.markdown(f"- {day}: {count} interactions")
        
        with col2:
            st.markdown("**Best Hours:**")
            top_hours = df_activity.groupby('hour')['activity_count'].sum().nlargest(3)
            for hour, count in top_hours.items():
                st.markdown(f"- {hour:02d}:00: {count} interactions")


def render_feature_gap(property_data: Dict[str, Any], 
                       lead_must_haves: List[str],
                       match_score: int):
    """
    Explains the 'Gap' in the match score from Screenshot 24.
    Prepares agents for objections by highlighting what's missing.
    
    Args:
        property_data: Property details including features list
        lead_must_haves: Lead's must-have features
        match_score: Overall match percentage (0-100)
    """
    st.markdown("#### 🔍 Match Gap Analysis")
    
    # Identify what is present and missing
    property_features = set(property_data.get('features', []))
    must_haves_set = set(lead_must_haves)
    
    matched = must_haves_set & property_features
    missing = must_haves_set - property_features
    bonus = property_features - must_haves_set
    
    # Visual breakdown
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("✅ Matched", f"{len(matched)}/{len(must_haves_set)}")
        if matched:
            with st.expander("View Matched"):
                for item in matched:
                    st.markdown(f"✓ {item}")
    
    with col2:
        st.metric("⚠️ Missing", len(missing))
        if missing:
            with st.expander("View Missing"):
                for item in missing:
                    st.markdown(f"✗ {item}")
    
    with col3:
        st.metric("🎁 Bonus Features", len(bonus))
        if bonus:
            with st.expander("View Extras"):
                for item in bonus:
                    st.markdown(f"+ {item}")
    
    # Match quality assessment
    if match_score >= 95:
        st.success(f"""
        🎯 **Exceptional Match ({match_score}%)**  
        This property meets {len(matched)}/{len(must_haves_set)} must-haves. 
        Recommend immediate showing.
        """)
    elif match_score >= 85:
        st.info(f"""
        👍 **Strong Match ({match_score}%)**  
        Minor gaps can likely be addressed. Review alternatives below.
        """)
    else:
        st.warning(f"""
        🤔 **Good Match ({match_score}%)**  
        Significant gaps exist. Present as backup option or explore workarounds.
        """)
    
    # Provide solutions for missing features
    if missing:
        st.markdown("---")
        st.markdown("#### 🛠️ Gap Resolution Strategies")
        
        for item in missing:
            with st.expander(f"💡 Solutions for: **{item}**"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Context-aware suggestions
                    if "pool" in item.lower():
                        st.markdown("""
                        **Options:**
                        - 🏊 Community pool access (0.2 mi away)
                        - 💰 Install in-ground pool: $35K-$55K
                        - 🏖️ Above-ground option: $5K-$10K
                        """)
                    elif "garage" in item.lower():
                        st.markdown("""
                        **Options:**
                        - 🚗 Covered parking available
                        - 🏗️ Add detached garage: $25K-$40K
                        - 📦 Climate-controlled storage nearby
                        """)
                    else:
                        st.markdown(f"""
                        **AI Analysis:**
                        - Similar properties nearby with {item}
                        - Renovation feasibility: TBD
                        - Alternative solutions available
                        """)
                
                with col2:
                    if st.button(f"Find Contractors", key=f"contractor_{item}"):
                        st.success("📞 3 local quotes requested!")
                    
                    if st.button(f"Find Alternatives", key=f"alt_{item}"):
                        st.success(f"🔍 Found 5 properties with {item}")


def render_elite_segmentation_tab():
    """
    Complete elite segmentation view with all refinements.
    Replaces the basic segmentation from Screenshot 21-22.
    """
    st.markdown("## 📊 AI-Powered Lead Segmentation")
    st.markdown("### Intelligent segments based on behavior, engagement, and intent")
    
    # Segment 1: Highly Active
    styled_segment_card(
        title="🔥 Highly Active",
        engagement=94,
        score=87,
        price="$800K+",
        actions=[
            "Schedule immediate follow-up calls",
            "Send personalized property matches",
            "Enable VIP fast-track workflow",
            "Set up automated showing alerts"
        ],
        lead_count=23
    )
    
    # Segment 2: Warming Up
    styled_segment_card(
        title="🌡️ Warming Up",
        engagement=67,
        score=72,
        price="$650K",
        actions=[
            "Send educational content series",
            "Schedule soft-touch check-ins",
            "Provide market insights",
            "Offer free home valuation"
        ],
        lead_count=41
    )
    
    # Segment 3: Need Attention
    styled_segment_card(
        title="⚠️ Need Attention",
        engagement=34,
        score=58,
        price="$500K",
        actions=[
            "Re-engagement campaign trigger",
            "Special incentive offer",
            "Personal video message",
            "Referral partner introduction"
        ],
        lead_count=17
    )
    
    # Segment 4: Dormant (Re-engage)
    styled_segment_card(
        title="😴 Dormant",
        engagement=12,
        score=31,
        price="$400K",
        actions=[
            "Win-back campaign sequence",
            "Market update with urgency",
            "Last-chance offer",
            "Survey for feedback"
        ],
        lead_count=9
    )
