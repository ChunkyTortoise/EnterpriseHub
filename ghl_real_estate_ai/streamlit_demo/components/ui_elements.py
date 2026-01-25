import streamlit as st

def render_action_card(title, description, icon, key_suffix=""):

    """

    Render a consistent premium action card with GHL trigger simulation.

    """

    st.markdown(f"""

        <div style="

            border: 1px solid rgba(255,255,255,0.08); 

            border-top: 1px solid rgba(255,255,255,0.15);

            border-radius: 16px; 

            padding: 24px; 

            margin-bottom: 20px; 

            border-left: 4px solid #6366f1; 

            background: rgba(13, 17, 23, 0.8); 

            backdrop-filter: blur(20px); 

            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.6);

        ">

            <div style="display: flex; align-items: center; gap: 15px;">

                <span style="font-size: 1.8rem; filter: drop-shadow(0 0 12px rgba(99, 102, 241, 0.5));">{icon}</span>

                <b style="color: #FFFFFF; font-size: 1.2rem; font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.02em;">{title}</b>

            </div>

            <p style="font-size: 15px; color: #E6EDF3; margin-top: 12px; line-height: 1.6; font-family: 'Inter', sans-serif;">{description}</p>

        </div>

    """, unsafe_allow_html=True)

    

    col1, col2 = st.columns([3, 1])

    with col2:

        if st.button("Run Action", key=f"run_action_{key_suffix}_{title.lower().replace(' ', '_')}", use_container_width=True):

            with st.spinner("Executing GHL trigger..."):

                import time

                time.sleep(1)

                st.toast(f"Success: {title} triggered", icon="⚡")



def render_insight_card(title, value, description, status='info', action_label=None, action_key=None):

    """

    Renders a high-fidelity AI insight card with optional hub redirection.

    """

    colors = {

        'success': 'rgba(16, 185, 129, 0.08)', 

        'warning': 'rgba(245, 158, 11, 0.08)', 

        'info': 'rgba(99, 102, 241, 0.08)',

        'danger': 'rgba(239, 68, 68, 0.08)'

    }

    border_colors = {

        'success': '#10B981', 

        'warning': '#F59E0B', 

        'info': '#6366f1',

        'danger': '#EF4444'

    }

    

    st.markdown(f"""

        <div style="

            background-color: {colors.get(status, colors['info'])}; 

            padding: 2.5rem; 

            border-radius: 20px; 

            margin-bottom: 2rem; 

            border: 1px solid rgba(255,255,255,0.08); 

            border-top: 1px solid rgba(255,255,255,0.15);

            border-left: 6px solid {border_colors.get(status, border_colors['info'])}; 

            backdrop-filter: blur(25px); 

            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.7);

        ">

            <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 1rem;">

                <b style="color: #FFFFFF; font-size: 1.5rem; font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.03em;">{title}</b>

            </div>

            <div style="font-size: 3rem; font-weight: 700; color: #FFFFFF; margin: 0.5rem 0; font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.05em; text-shadow: 0 0 30px {border_colors.get(status, border_colors['info'])}40;">{value}</div>

            <p style="font-size: 1.15rem; color: #E6EDF3; margin: 0; line-height: 1.7; font-family: 'Inter', sans-serif;">{description}</p>

        </div>

    """, unsafe_allow_html=True)

    if action_label and action_key:
        if st.button(action_label, key=action_key, use_container_width=True):
            st.session_state.current_hub = "🧠 Lead Intelligence Hub"
            st.rerun()


    
    


    
    def apply_page_transitions():


    
        """


    
        Injects custom CSS for smooth page transitions and micro-interactions.


    
        """


    
        st.markdown("""


    
            <style>


    
                /* Smooth Fade-in Animation for the entire app container */


    
                .stApp {


    
                    animation: fadeIn 0.8s ease-out;


    
                }


    
                


    
                @keyframes fadeIn {


    
                    0% { opacity: 0; transform: translateY(10px); }


    
                    100% { opacity: 1; transform: translateY(0); }


    
                }


    
                


    
                /* Micro-interactions for buttons */


    
                .stButton > button {


    
                    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;


    
                }


    
                .stButton > button:hover {


    
                    transform: translateY(-2px);


    
                    box-shadow: 0 5px 15px rgba(99, 102, 241, 0.4) !important;


    
                    border-color: #6366f1 !important;


    
                }


    
                


    
                /* Glossy card hover effect */


    
                [data-testid="stExpander"] {


    
                    transition: all 0.3s ease;


    
                    border: 1px solid rgba(255,255,255,0.05) !important;


    
                }


    
                [data-testid="stExpander"]:hover {


    
                    border-color: rgba(99, 102, 241, 0.3) !important;


    
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);


    
                }


    
            </style>


    
        """, unsafe_allow_html=True)


    
    


    
    def render_loading_animation():


    
        """Renders a sleek pulse animation for AI operations."""


    
        st.markdown("""


    
            <div style="display: flex; justify-content: center; align-items: center; padding: 2rem;">


    
                <div style="


    
                    width: 60px; height: 60px; 


    
                    border-radius: 50%; 


    
                    background: #6366f1; 


    
                    box-shadow: 0 0 0 rgba(99, 102, 241, 0.4);


    
                    animation: pulse 1.5s infinite;


    
                "></div>


    
            </div>


    
            <style>


    
                @keyframes pulse {


    
                    0% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.7); }


    
                    70% { transform: scale(1); box-shadow: 0 0 0 20px rgba(99, 102, 241, 0); }


    
                    100% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(99, 102, 241, 0); }


    
                }


    
            </style>


    
        """, unsafe_allow_html=True)


    
    