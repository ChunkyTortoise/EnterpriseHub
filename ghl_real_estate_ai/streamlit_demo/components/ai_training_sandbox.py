"""
AI Training Sandbox Component
Interactive chat interface for testing AI prompts and personas in real-time
"""
import streamlit as st
from typing import List, Dict


def render_ai_training_sandbox(ai_tone: str = "Natural"):
    """
    Render the interactive AI Training Sandbox with:
    - Live system prompt editor
    - Chat-based conversation simulator
    - Roleplay scenarios for testing objection handling
    
    Args:
        ai_tone: Current AI tone setting (Professional, Natural, Direct/Casual)
    """
    
    st.markdown("### 🧪 AI Training Lab")
    st.markdown("*Test and refine your AI assistant's personality before going live*")
    
    col_prompt, col_sandbox = st.columns([1, 1])
    
    with col_prompt:
        st.markdown("#### 📝 System Prompt Configuration")
        
        # Dynamic prompt based on tone
        base_prompts = {
            "Professional": "You are a senior real estate advisor representing Jorge Salas. Use formal language, emphasize market data and ROI, and maintain a polite, consultative approach. Always confirm details and provide comprehensive market insights.",
            "Natural": "You are a helpful assistant on Jorge's real estate team. Be friendly and approachable, use first names, and keep sentences concise but informative. Balance professionalism with warmth.",
            "Direct/Casual": "You are Jorge speaking directly. Be extremely direct and casual. Skip unnecessary pleasantries. Your goal is to get the budget and location ASAP so you don't waste anyone's time. Use short sentences."
        }
        
        # Use session state for prompt if available (from templates)
        if 'active_prompt' not in st.session_state:
            st.session_state.active_prompt = base_prompts.get(ai_tone, base_prompts["Natural"])
        
        current_prompt = st.text_area(
            "Edit System Prompt:",
            value=st.session_state.active_prompt,
            height=180,
            help="This is what the AI 'thinks' - it defines the personality and behavior",
            key="system_prompt_editor"
        )
        
        # Update session state when manually edited
        if current_prompt != st.session_state.active_prompt:
            st.session_state.active_prompt = current_prompt
        
        st.markdown("#### 🎭 Quick Persona Templates")
        st.caption("Click to auto-populate the System Prompt above")
        
        template_col1, template_col2 = st.columns(2)
        
        with template_col1:
            if st.button("🤝 Consultative Closer", width='stretch', key="template_consultative"):
                consultative_prompt = "You are a senior real estate advisor with 15+ years experience. Use consultative selling techniques: ask open-ended questions, listen actively, and provide comprehensive market analysis. Build trust through expertise. Always offer 3 options and explain pros/cons. Your goal is to guide, not push."
                st.session_state.active_prompt = consultative_prompt
                st.toast("✅ Consultative Closer prompt loaded!", icon="🤝")
                st.rerun()
        
        with template_col2:
            if st.button("⚡ Speed Qualifier", width='stretch', key="template_speed"):
                speed_prompt = "You are a direct, time-efficient real estate assistant. Get to the point fast: Ask budget, location, timeline in the first 3 messages. Skip small talk. If the lead doesn't match criteria, politely redirect. Your goal is to qualify or disqualify within 2 minutes."
                st.session_state.active_prompt = speed_prompt
                st.toast("✅ Speed Qualifier prompt loaded!", icon="⚡")
                st.rerun()
        
        # More templates
        template_col3, template_col4 = st.columns(2)
        
        with template_col3:
            if st.button("🏡 Luxury Specialist", width='stretch', key="template_luxury"):
                luxury_prompt = "You are an exclusive luxury real estate specialist. Use sophisticated language, emphasize investment value and lifestyle benefits. Reference high-end amenities, architectural features, and neighborhood prestige. Your clients expect white-glove service and discretion."
                st.session_state.active_prompt = luxury_prompt
                st.toast("✅ Luxury Specialist prompt loaded!", icon="🏡")
                st.rerun()
        
        with template_col4:
            if st.button("🏠 First-Time Buyer Helper", width='stretch', key="template_firsttime"):
                firsttime_prompt = "You are a patient, educational real estate guide for first-time home buyers. Explain the process step-by-step, define industry terms, and address common fears (mortgage, closing costs, inspection). Use encouraging language. Your goal is to make buying feel achievable and exciting."
                st.session_state.active_prompt = firsttime_prompt
                st.toast("✅ First-Time Buyer Helper prompt loaded!", icon="🏠")
                st.rerun()
        
        st.markdown("---")
        st.markdown("#### 💡 Testing Tips")
        st.info("""
        **Test these scenarios:**
        - 🔴 **Price objection**: "That's too expensive"
        - 🟡 **Timeline hesitation**: "I need to think about it"
        - 🟢 **Feature request**: "Do you have anything with a pool?"
        - 🔵 **Competitor mention**: "Another agent offered me a better deal"
        """)
    
    with col_sandbox:
        st.markdown("#### 💬 Live Conversation Simulator")
        st.markdown(f"*Currently testing in **{ai_tone}** mode*")
        
        # Initialize chat history
        if 'sandbox_chat' not in st.session_state:
            st.session_state.sandbox_chat = [
                {"role": "assistant", "content": f"Hello! I'm your AI assistant in {ai_tone} mode. Try asking me about properties or raising objections to test my responses."}
            ]
        
        # Split into chat and thought trace
        col_chat, col_trace = st.columns([2, 1])
        
        with col_chat:
            st.markdown("##### 💬 Conversation")
            # Chat container with custom styling
            chat_container = st.container(height=400, border=True)
            
            with chat_container:
                for message in st.session_state.sandbox_chat:
                    if message["role"] == "user":
                        st.markdown(f"""
                        <div style='display: flex; justify-content: flex-end; margin-bottom: 1rem;'>
                            <div style='max-width: 75%; background: #2563eb; color: white; padding: 0.75rem 1rem; 
                                        border-radius: 16px 16px 4px 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                                <div style='font-size: 0.875rem;'>{message["content"]}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='display: flex; justify-content: flex-start; margin-bottom: 1rem;'>
                            <div style='max-width: 75%; background: white; border: 1px solid #e5e7eb; padding: 0.75rem 1rem; 
                                        border-radius: 16px 16px 16px 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
                                <div style='font-size: 0.875rem; color: #374151;'>{message["content"]}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        
        with col_trace:
            st.markdown("##### 🧠 AI Thinking (Chain-of-Thought)")
            
            # Initialize thought trace
            if 'thought_trace' not in st.session_state:
                st.session_state.thought_trace = []
            
            # Thought trace container
            trace_container = st.container(height=400, border=True)
            
            with trace_container:
                if st.session_state.thought_trace:
                    for thought in st.session_state.thought_trace:
                        st.markdown(f"""
                        <div style='background: #f8fafc; border-left: 2px dashed #cbd5e1; padding: 0.75rem; 
                                    margin-bottom: 0.5rem; border-radius: 4px;'>
                            <div style='font-family: monospace; font-size: 0.75rem; color: #64748b; line-height: 1.5;'>
                                {thought}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style='text-align: center; padding: 2rem; color: #94a3b8; font-size: 0.875rem;'>
                        <div style='font-size: 2rem; margin-bottom: 0.5rem;'>🧠</div>
                        Send a message to see AI's internal reasoning
                    </div>
                    """, unsafe_allow_html=True)
        
        # Input area
        user_input = st.text_input(
            "Type a lead's message:",
            placeholder="Ex: 'The price is too high' or 'I'm looking for a 3-bed home'",
            key="sandbox_input",
            label_visibility="collapsed"
        )
        
        col_send, col_reset = st.columns([3, 1])
        
        with col_send:
            if st.button("🚀 Send", width='stretch', type="primary") and user_input:
                # Add user message
                st.session_state.sandbox_chat.append({"role": "user", "content": user_input})
                
                # Generate thought trace BEFORE response
                thought_trace = generate_thought_trace(user_input, ai_tone)
                st.session_state.thought_trace.append(thought_trace)
                
                # Generate AI response based on tone and input
                ai_response = generate_sandbox_response(user_input, ai_tone, current_prompt)
                st.session_state.sandbox_chat.append({"role": "assistant", "content": ai_response})
                
                st.rerun()
        
        with col_reset:
            if st.button("🗑️", width='stretch', help="Clear conversation"):
                st.session_state.sandbox_chat = [
                    {"role": "assistant", "content": f"Conversation cleared. I'm ready to test in {ai_tone} mode!"}
                ]
                st.session_state.thought_trace = []
                st.rerun()
        
        # Response analytics
        if len(st.session_state.sandbox_chat) > 2:
            st.markdown("---")
            st.markdown("#### 📊 Response Analytics")
            
            total_exchanges = (len(st.session_state.sandbox_chat) - 1) // 2
            
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                st.metric("Exchanges", total_exchanges)
            
            with metric_col2:
                # Calculate avg response length
                ai_messages = [m for m in st.session_state.sandbox_chat if m["role"] == "assistant"]
                avg_length = sum(len(m["content"].split()) for m in ai_messages) / len(ai_messages) if ai_messages else 0
                st.metric("Avg Words", f"{avg_length:.0f}")
            
            with metric_col3:
                # Determine if responses match tone
                tone_match = "✅" if avg_length < 30 and ai_tone == "Direct/Casual" else "✅"
                st.metric("Tone Match", tone_match)


def generate_thought_trace(user_input: str, tone: str) -> str:
    """
    Generate Chain-of-Thought internal reasoning trace
    Shows what the AI is "thinking" before it responds
    """
    
    user_lower = user_input.lower()
    
    # Detect intent
    if any(word in user_lower for word in ["expensive", "too much", "too high", "price", "cost"]):
        intent = "PRICE_OBJECTION"
    elif any(word in user_lower for word in ["think about", "not sure", "maybe", "hesitant"]):
        intent = "TIMELINE_HESITATION"
    elif any(word in user_lower for word in ["pool", "garage", "bedroom", "bathroom", "feature"]):
        intent = "FEATURE_REQUEST"
    elif any(word in user_lower for word in ["other agent", "another", "competitor", "better deal"]):
        intent = "COMPETITOR_MENTION"
    elif any(word in user_lower for word in ["area", "neighborhood", "location", "where"]):
        intent = "LOCATION_QUERY"
    else:
        intent = "GENERAL_INQUIRY"
    
    # Build thought trace
    trace_steps = []
    
    trace_steps.append(f"[1] 🔍 ANALYZING INPUT: '{user_input[:50]}{'...' if len(user_input) > 50 else ''}'")
    trace_steps.append(f"[2] 🎯 DETECTED INTENT: {intent}")
    trace_steps.append(f"[3] 🎨 ACTIVE TONE: {tone}")
    
    # Knowledge retrieval simulation
    if intent == "PRICE_OBJECTION":
        trace_steps.append("[4] 📊 RETRIEVING: Market comps, ROI data")
        trace_steps.append("[5] 🧮 CALCULATING: Budget constraints vs property value")
    elif intent == "FEATURE_REQUEST":
        trace_steps.append("[4] 🔎 SEARCHING: MLS database for matching features")
        trace_steps.append("[5] 📍 FILTERING: By location + budget constraints")
    elif intent == "LOCATION_QUERY":
        trace_steps.append("[4] 🗺️  ACCESSING: Neighborhood insights database")
        trace_steps.append("[5] 📈 PULLING: School ratings, appreciation trends")
    else:
        trace_steps.append("[4] 🤔 FORMULATING: Qualification questions")
        trace_steps.append("[5] 🎯 PRIORITIZING: Budget + Location + Timeline")
    
    # Response strategy
    if tone == "Professional":
        trace_steps.append("[6] ✍️  STRATEGY: Formal language, comprehensive data")
    elif tone == "Direct/Casual":
        trace_steps.append("[6] ✍️  STRATEGY: Direct questions, skip pleasantries")
    else:
        trace_steps.append("[6] ✍️  STRATEGY: Friendly tone, balanced information")
    
    trace_steps.append("[7] ✅ GENERATING RESPONSE...")
    
    return "<br>".join(trace_steps)


def generate_sandbox_response(user_input: str, tone: str, system_prompt: str) -> str:
    """
    Generate AI response based on user input, tone, and system prompt
    
    This is a rule-based simulator for demo purposes.
    In production, this would call your actual LLM with the system prompt.
    """
    user_lower = user_input.lower()
    
    # Objection handling
    if any(word in user_lower for word in ["expensive", "too much", "too high", "price", "cost"]):
        if tone == "Professional":
            return "I understand your concern about pricing. In the current market, properties in this area have appreciated 12% year-over-year. I'd be happy to provide a comparative market analysis showing similar properties and their ROI potential. What's your target investment range?"
        elif tone == "Natural":
            return "I totally get it - pricing is important! Here's the thing: this property is actually priced competitively for the area. I can show you comps if you'd like. What budget are you most comfortable with?"
        else:  # Direct/Casual
            return "Fair. What's your max budget? I'll find you something in that range. No point looking at stuff you can't afford."
    
    # Timeline hesitation
    elif any(word in user_lower for word in ["think about", "not sure", "maybe", "hesitant"]):
        if tone == "Professional":
            return "I completely respect your need for due diligence. May I ask what specific factors you'd like to evaluate? I can provide additional market data, neighborhood insights, or arrange a second viewing at your convenience."
        elif tone == "Natural":
            return "No pressure at all! Take your time. Is there anything specific you're unsure about? Happy to answer questions or get you more info."
        else:  # Direct/Casual
            return "Cool. What's holding you back? If it's the property, I got others. If it's timing, lemme know when you're ready."
    
    # Feature requests
    elif any(word in user_lower for word in ["pool", "garage", "bedroom", "bathroom", "feature"]):
        if tone == "Professional":
            return f"Excellent question. I'm noting your preference for {user_input.split()[-1]}. This specific amenity can significantly impact property valuation. Let me query our MLS database for properties matching this criterion in your target area."
        elif tone == "Natural":
            return f"Great! I'll definitely look for properties with {user_input.split()[-1]}. That's pretty popular in this area. What else is on your must-have list?"
        else:  # Direct/Casual
            return f"Got it. {user_input.split()[-1].title()}. What else? And what's your budget?"
    
    # Competitor mention
    elif any(word in user_lower for word in ["other agent", "another", "competitor", "better deal"]):
        if tone == "Professional":
            return "I appreciate you being transparent. Jorge's team focuses on long-term client relationships and market expertise. We offer comprehensive market analysis, post-sale support, and exclusive off-market listings. May I ask what specific terms were offered so I can ensure we're providing maximum value?"
        elif tone == "Natural":
            return "That's fair - you should definitely explore your options! I'd love to know what they're offering so I can make sure we're competitive. We also have some exclusive listings that aren't public yet. Want to see those?"
        else:  # Direct/Casual
            return "Cool. What'd they offer? If it's legit better, take it. If not, I'll beat it. Your call."
    
    # Location queries
    elif any(word in user_lower for word in ["area", "neighborhood", "location", "where"]):
        if tone == "Professional":
            return "Location is indeed the cornerstone of real estate value. Which specific neighborhoods or zip codes are you targeting? I can provide detailed market reports including school ratings, appreciation trends, and demographic data."
        elif tone == "Natural":
            return "Location is key! Which areas are you interested in? I can give you the inside scoop on different neighborhoods - what's hot, what's quiet, schools, all that good stuff."
        else:  # Direct/Casual
            return "Where you wanna be? Give me a neighborhood or zip code and I'll show you what we got."
    
    # Default response
    else:
        if tone == "Professional":
            return "Thank you for that information. I'm documenting your preferences to ensure we find the optimal property match. Could you please elaborate on your primary requirements: budget range, preferred location, and timeline?"
        elif tone == "Natural":
            return "Thanks for sharing that! To help you better, what's your budget looking like? And which area are you most interested in?"
        else:  # Direct/Casual
            return "Got it. Budget? Location? Timeline? Hit me with the basics so I can find you something."
