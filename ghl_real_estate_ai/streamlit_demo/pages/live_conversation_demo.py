"""
Live Conversation Demo - Shows realistic buyer/seller AI conversations
"""
import streamlit as st

st.set_page_config(page_title="Live AI Demo", page_icon="💬", layout="wide")

st.title("💬 Live AI Conversation Demo")
st.markdown("*See how our AI engages with real estate buyers and sellers*")

# Scenario selector
scenario_type = st.radio(
    "Choose a scenario:",
    ["🏠 Buyer Inquiry", "💰 Seller Valuation", "⚠️ Price Objection", "📅 Showing Request"],
    horizontal=True
)

st.markdown("---")

# Define conversation flows
conversations = {
    "🏠 Buyer Inquiry": [
        {"role": "user", "message": "I'm looking for a 3-bedroom home in Austin under $800K"},
        {"role": "ai", "message": "Great! Austin is a hot market right now. I have 4 properties that match your criteria. The Domain area has 2 new listings at $750K and $780K - both 3bed/2.5bath with modern kitchens and home offices.\n\nThe West Lake area also has 2 options at $775K and $795K with larger yards.\n\nWhen would you like to see them? I can schedule showings as early as tomorrow."},
        {"role": "user", "message": "What about the Domain properties? Tell me more"},
        {"role": "ai", "message": "Perfect choice! Here are the details:\n\n**123 Oak Street** - $750,000\n• 3 bed, 2.5 bath, 2,100 sq ft\n• Built 2020, open floor plan\n• Smart home features, chef's kitchen\n• Walking distance to Domain shops\n• HOA: $150/month\n\n**456 Maple Ave** - $780,000\n• 3 bed, 2.5 bath, 2,300 sq ft  \n• Built 2021, luxury finishes\n• Pool, covered patio, 2-car garage\n• Top-rated schools nearby\n• HOA: $200/month\n\nBoth are move-in ready. Would you like me to send you the full listing details and schedule a showing?"}
    ],
    "💰 Seller Valuation": [
        {"role": "user", "message": "What's my home worth? I'm in Downtown Austin"},
        {"role": "ai", "message": "I'd love to help you! Based on recent sales in Downtown Austin, similar homes have been selling for $650K-$750K depending on size and condition.\n\nTo give you an accurate valuation, can you share:\n• Your address (or cross streets)\n• Square footage\n• Number of bedrooms/bathrooms\n• Any recent upgrades?\n\nI'll run a detailed Comparative Market Analysis (CMA) for you right away."},
        {"role": "user", "message": "789 Congress Ave, 2000 sq ft, 2 bed 2 bath, renovated kitchen last year"},
        {"role": "ai", "message": "Excellent! Based on your details:\n\n**📊 Estimated Home Value: $685,000 - $715,000**\n\nHere's why:\n• Congress Ave location: Premium ($50K+ boost)\n• 2,000 sq ft: Perfect size for downtown\n• Recent kitchen reno: Adds $15-25K value\n• 2/2 layout: High demand for this area\n\n**Recent Comps (last 60 days):**\n• 801 Congress: $695K (1,950 sq ft, no reno)\n• 765 Congress: $720K (2,100 sq ft, full reno)\n• 812 Colorado: $670K (1,900 sq ft, dated)\n\nYour renovated kitchen puts you at the higher end. I'm seeing homes in your area sell in 12-18 days average.\n\nWould you like me to prepare a full CMA report with professional photos and staging recommendations?"}
    ],
    "⚠️ Price Objection": [
        {"role": "user", "message": "That's way too expensive. I saw similar homes for $100K less"},
        {"role": "ai", "message": "I totally understand - pricing is important! Let me explain what you're getting with this property:\n\n**Why the price difference:**\n• This home was renovated in 2021 (new HVAC, roof, appliances)\n• Those $100K cheaper listings are likely 15-20 years older\n• This neighborhood appreciated 8% last year vs 3% city average\n• Schools here are top 10% in Austin (huge value driver)\n\n**Here's what I recommend:**\n1. Let me show you both - you'll see the difference\n2. I can pull comparable sales data to justify the price\n3. If you love it, we can negotiate - sellers just reduced $15K\n\nWhat's your target budget? I want to make sure I'm showing you the best value for your money."},
        {"role": "user", "message": "My max is $700K"},
        {"role": "ai", "message": "Perfect! That's a solid budget. Here's what I can do:\n\n**Option 1:** This property at $750K\n• Offer $710K (seller might counter at $725K)\n• Ask for $10K in seller concessions (closing costs)\n• Final out-of-pocket: ~$715K\n\n**Option 2:** Show you 3 other homes in the $680-$700K range\n• Slightly older but great bones\n• You'd have $20-30K for your own upgrades\n• Build instant equity with improvements\n\n**Option 3:** Wait 30-60 days\n• More inventory coming in spring\n• Potential for better deals\n\nWhich approach feels best? I'm here to find you the right home at the right price, not just any home."}
    ],
    "📅 Showing Request": [
        {"role": "user", "message": "Can I see 123 Oak Street this weekend?"},
        {"role": "ai", "message": "Absolutely! Let me check availability for 123 Oak Street.\n\n**This Weekend Options:**\n• Saturday 10:00 AM ✅ Available\n• Saturday 2:00 PM ✅ Available  \n• Sunday 11:00 AM ✅ Available\n• Sunday 3:00 PM ✅ Available\n\nWhich time works best for you? I'll send you a calendar invite with:\n• Property address and access code\n• What to look for during the showing\n• Neighborhood info and comps\n• Pre-approval tips if you love it\n\nAlso, would you like to see any other properties while we're out? I can bundle 2-3 showings in one trip to save you time."},
        {"role": "user", "message": "Saturday 2pm works. And yes, show me similar homes nearby"},
        {"role": "ai", "message": "Perfect! I've scheduled you for:\n\n**📅 Saturday 2:00 PM - Property Tour**\n\n**Stop 1:** 123 Oak Street (2:00-2:30 PM)\n• Your requested property\n• 3 bed, 2.5 bath, $750K\n• Modern kitchen, home office\n\n**Stop 2:** 456 Maple Ave (2:45-3:15 PM)  \n• 5 minutes away\n• 3 bed, 2.5 bath, $780K\n• Pool, larger lot\n\n**Stop 3:** 789 Cedar Lane (3:30-4:00 PM)\n• 3 minutes from Stop 2\n• 3 bed, 2 bath, $725K\n• Newly listed (just hit market today!)\n\n**✅ You'll receive:**\n• Calendar invite with all addresses\n• Property comparison sheet\n• Financing pre-approval checklist\n• SMS reminders 24 hours before\n\nI'll meet you at the first property. Excited to show you these homes! Any questions before Saturday?"}
    ]
}

# Display selected conversation
selected_conv = conversations[scenario_type]

st.markdown("### 💬 Conversation Flow")

for msg in selected_conv:
    if msg["role"] == "user":
        st.markdown(f"""
        <div style='background: #2563eb; color: white; padding: 1rem 1.5rem; border-radius: 16px 16px 4px 16px; 
                    margin-bottom: 1rem; margin-left: 20%; box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);'>
            <div style='font-size: 0.75rem; opacity: 0.9; margin-bottom: 0.5rem;'>👤 BUYER/SELLER</div>
            <div style='font-size: 0.95rem;'>{msg["message"]}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='background: white; border: 1px solid #e5e7eb; padding: 1rem 1.5rem; border-radius: 16px 16px 16px 4px; 
                    margin-bottom: 1rem; margin-right: 20%; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);'>
            <div style='font-size: 0.75rem; color: #6b7280; margin-bottom: 0.5rem;'>🤖 AI ASSISTANT</div>
            <div style='font-size: 0.95rem; color: #374151; white-space: pre-wrap;'>{msg["message"]}</div>
        </div>
        """, unsafe_allow_html=True)

# Key features showcase
st.markdown("---")
st.markdown("### ✨ AI Capabilities Demonstrated")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **🎯 Lead Qualification**
    - Asks budget, location, timeline
    - Identifies must-have features
    - Pre-qualifies before showing
    """)

with col2:
    st.markdown("""
    **💡 Property Matching**
    - Searches inventory instantly
    - Provides detailed comparisons
    - Schedules bundled showings
    """)

with col3:
    st.markdown("""
    **🔥 Objection Handling**
    - Addresses price concerns
    - Explains value differences
    - Offers multiple solutions
    """)
