"""
Outcome-First Landing Page for Real Estate AI & LLMOps Partner.
Serving as the primary sales tool and showcase for EnterpriseHub (Jorge Bot).
"""

import streamlit as st
from pathlib import Path

def render_landing_page():
    """Render the high-conversion landing page."""
    
    # 1. Hero Section
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 4rem 2rem; border-radius: 20px; text-align: center; margin-bottom: 3rem; box-shadow: 0 20px 50px rgba(0,0,0,0.3);">
        <h1 style="color: white; font-size: 3.5rem; font-weight: 800; margin-bottom: 1.5rem; line-height: 1.1;">
            Automate Your Real Estate Lead Qualification.<br>
            <span style="color: #6366F1;">Stop Losing Revenue to Slow Response Times.</span>
        </h1>
        <p style="color: rgba(255,255,255,0.9); font-size: 1.5rem; max-width: 900px; margin: 0 auto 2.5rem auto; line-height: 1.5;">
            I build production-grade AI systems (Jorge Bot) that qualify leads in &lt; 2 minutes, 
            integrate with GoHighLevel, and increase conversions by 133%.
        </p>
        <div style="display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap;">
            <a href="https://calendly.com/your-link" target="_blank" style="background: #6366F1; color: white; padding: 1.2rem 2.5rem; border-radius: 12px; font-weight: 700; font-size: 1.2rem; text-decoration: none; transition: all 0.3s ease; box-shadow: 0 10px 20px rgba(99, 102, 241, 0.3);">
                Book a Lead Automation Audit
            </a>
            <div style="background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); color: white; padding: 1.2rem 2.5rem; border-radius: 12px; font-weight: 600; font-size: 1.1rem; border: 1px solid rgba(255,255,255,0.2);">
                19+ Certifications: Google, Meta, IBM
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. The "Problem" Section
    col1, col2 = st.columns([1, 1.2])
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 8rem; color: #EF4444; font-weight: 800; line-height: 1;">05:00</div>
            <div style="font-size: 1.5rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.2em;">Minutes</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style="padding: 1rem;">
            <h2 style="font-size: 2.2rem; color: #FFFFFF; margin-bottom: 1.5rem;">The Cost of Speed</h2>
            <p style="font-size: 1.2rem; color: #cbd5e1; line-height: 1.6;">
                If you don't respond to a real estate lead in <b>5 minutes</b>, your chances of qualifying them drop by <b>400%</b>.
            </p>
            <p style="font-size: 1.2rem; color: #cbd5e1; line-height: 1.6;">
                Your agents are busy, and manual review is slow. You are leaving money on the table every night.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # 3. The "Solution" Section
    st.markdown("<h2 style='text-align: center; font-size: 2.5rem; margin-bottom: 3rem;'>The Jorge Bot Ecosystem</h2>", unsafe_allow_html=True)
    
    sol_col1, sol_col2, sol_col3 = st.columns(3)
    
    with sol_col1:
        st.markdown("""
        <div style="background: rgba(99, 102, 241, 0.05); padding: 2.5rem; border-radius: 20px; border: 1px solid rgba(99, 102, 241, 0.2); height: 100%;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🤖</div>
            <h3 style="color: #6366F1; margin-bottom: 1rem;">24/7 Multi-Agent Qualification</h3>
            <p style="color: #94a3b8; line-height: 1.6;">
                Specialized bots for Buyers and Sellers. Qualified leads are delivered directly to your CRM without human intervention.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with sol_col2:
        st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.05); padding: 2.5rem; border-radius: 20px; border: 1px solid rgba(16, 185, 129, 0.2); height: 100%;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🔗</div>
            <h3 style="color: #10B981; margin-bottom: 1rem;">Deep GHL Integration</h3>
            <p style="color: #94a3b8; line-height: 1.6;">
                Automated tagging, scoring, and workflow triggers. No more manual data entry or lost contact info.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with sol_col3:
        st.markdown("""
        <div style="background: rgba(245, 158, 11, 0.05); padding: 2.5rem; border-radius: 20px; border: 1px solid rgba(245, 158, 11, 0.2); height: 100%;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
            <h3 style="color: #F59E0B; margin-bottom: 1rem;">BI Dashboard</h3>
            <p style="color: #94a3b8; line-height: 1.6;">
                Real-time visibility into your lead velocity and bot performance. Know exactly where your revenue is coming from.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # 4. Featured Case Study
    st.markdown("""
    <div style="background: #1e293b; padding: 4rem; border-radius: 24px; border: 1px solid rgba(255,255,255,0.05);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
            <h2 style="font-size: 2.5rem; color: white; margin: 0;">Featured Case Study: CS001</h2>
            <div style="background: #6366F1; color: white; padding: 0.5rem 1.5rem; border-radius: 50px; font-weight: 700;">REAL ESTATE</div>
        </div>
        <h3 style="font-size: 2rem; color: #6366F1; margin-bottom: 2rem;">95% Faster Lead Response</h3>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4rem;">
            <div>
                <h4 style="color: white; margin-bottom: 1rem;">THE CHALLENGE</h4>
                <p style="color: #94a3b8; font-size: 1.1rem; line-height: 1.6;">
                    A scaling brokerage was losing 40% of their digital leads due to an average response time of 45 minutes. Leads went cold before agents could pick up the phone.
                </p>
                <h4 style="color: white; margin-top: 2rem; margin-bottom: 1rem;">THE SOLUTION</h4>
                <p style="color: #94a3b8; font-size: 1.1rem; line-height: 1.6;">
                    Deployment of the EnterpriseHub multi-agent system. Automated qualification through LangGraph and deep integration with GoHighLevel.
                </p>
            </div>
            <div style="background: rgba(255,255,255,0.03); padding: 2rem; border-radius: 20px; border: 1px solid rgba(255,255,255,0.05);">
                <h4 style="color: white; margin-bottom: 1.5rem; text-align: center;">THE OUTCOME</h4>
                <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="font-size: 2rem; color: #10B981;">⚡</div>
                        <div>
                            <div style="font-size: 1.5rem; color: white; font-weight: 700;">95% Faster</div>
                            <div style="color: #94a3b8;">Response time dropped from 45m to 2m</div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="font-size: 2rem; color: #10B981;">💰</div>
                        <div>
                            <div style="font-size: 1.5rem; color: white; font-weight: 700;">$240,000 Saved</div>
                            <div style="color: #94a3b8;">Annual reduction in manual labor costs</div>
                        </div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="font-size: 2rem; color: #10B981;">📈</div>
                        <div>
                            <div style="font-size: 1.5rem; color: white; font-weight: 700;">133% Increase</div>
                            <div style="color: #94a3b8;">Lead-to-appointment conversion rate</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # 5. Technical Infrastructure Section
    st.markdown("<h2 style='text-align: center; font-size: 2.5rem; margin-bottom: 3rem;'>Enterprise-Grade Technical Infrastructure</h2>", unsafe_allow_html=True)
    
    tech_col1, tech_col2 = st.columns(2)
    
    with tech_col1:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.03); padding: 2rem; border-radius: 20px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 1.5rem;">
            <h4 style="color: #6366F1; margin-bottom: 0.5rem;">Multi-Agent Orchestration</h4>
            <p style="color: #94a3b8; font-size: 0.95rem;">Powered by <b>LangGraph</b>, managing complex 3-7-30 day follow-up sequences with autonomous decision logic and 'Ghost-in-the-Machine' re-engagement.</p>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 2rem; border-radius: 20px; border: 1px solid rgba(255,255,255,0.05);">
            <h4 style="color: #6366F1; margin-bottom: 0.5rem;">Behavioral Analytics Engine</h4>
            <p style="color: #94a3b8; font-size: 0.95rem;">Real-time analysis of lead response patterns, engagement velocity, and optimal contact windows for maximized reply rates.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with tech_col2:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.03); padding: 2rem; border-radius: 20px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 1.5rem;">
            <h4 style="color: #6366F1; margin-bottom: 0.5rem;">Dynamic Personality Adaptation</h4>
            <p style="color: #94a3b8; font-size: 0.95rem;">AI automatically adapts tone and style (Analytical, Results, Relationship, Security) to match lead psychology detected from conversation history.</p>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 2rem; border-radius: 20px; border: 1px solid rgba(255,255,255,0.05);">
            <h4 style="color: #6366F1; margin-bottom: 0.5rem;">Track 3.1 ML Intelligence</h4>
            <p style="color: #94a3b8; font-size: 0.95rem;">Advanced predictive analytics for market timing, conversion probability forecasting, and intelligent handoff triggers to human agents.</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # 6. Trust Section (Certifications)
    st.markdown("<h2 style='text-align: center; font-size: 2.2rem; margin-bottom: 3rem;'>1,768+ Hours of Specialized AI/ML Training</h2>", unsafe_allow_html=True)
    
    cert_col1, cert_col2, cert_col3, cert_col4 = st.columns(4)
    with cert_col1:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🎓</div>
            <h4 style="color: white;">Google Data Analytics</h4>
        </div>
        """, unsafe_allow_html=True)
    with cert_col2:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🤖</div>
            <h4 style="color: white;">IBM BI Analyst</h4>
        </div>
        """, unsafe_allow_html=True)
    with cert_col3:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">💡</div>
            <h4 style="color: white;">Vanderbilt GenAI</h4>
        </div>
        """, unsafe_allow_html=True)
    with cert_col4:
        st.markdown("""
        <div style="text-align: center; padding: 1.5rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🧠</div>
            <h4 style="color: white;">DeepLearning.AI</h4>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # 6. Offer Menu
    st.markdown("<h2 style='text-align: center; font-size: 2.5rem; margin-bottom: 3rem;'>Ready to Scale Your Revenue?</h2>", unsafe_allow_html=True)
    
    off_col1, off_col2, off_col3 = st.columns(3)
    
    with off_col1:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.03); padding: 3rem; border-radius: 24px; border: 1px solid rgba(255,255,255,0.05); height: 100%; text-align: center;">
            <div style="font-size: 1.2rem; color: #94a3b8; margin-bottom: 1rem;">STRATEGY</div>
            <h3 style="color: white; font-size: 1.8rem; margin-bottom: 1.5rem;">AI Lead Audit</h3>
            <div style="font-size: 2.5rem; color: #6366F1; font-weight: 800; margin-bottom: 2rem;">$1,500</div>
            <ul style="text-align: left; color: #cbd5e1; margin-bottom: 2.5rem; list-style-type: none; padding: 0;">
                <li style="margin-bottom: 0.8rem;">✅ GHL Setup Review</li>
                <li style="margin-bottom: 0.8rem;">✅ Automation Roadmap</li>
                <li style="margin-bottom: 0.8rem;">✅ Cost/ROI Analysis</li>
                <li style="margin-bottom: 0.8rem;">✅ Technical Feasibility</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with off_col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%); padding: 3rem; border-radius: 24px; border: 2px solid #6366F1; height: 100%; text-align: center; transform: scale(1.05); box-shadow: 0 20px 40px rgba(99, 102, 241, 0.2);">
            <div style="font-size: 1.2rem; color: #6366F1; font-weight: 700; margin-bottom: 1rem;">POPULAR</div>
            <h3 style="color: white; font-size: 1.8rem; margin-bottom: 1.5rem;">Jorge Bot Lite</h3>
            <div style="font-size: 2.5rem; color: #6366F1; font-weight: 800; margin-bottom: 2rem;">$5,000</div>
            <ul style="text-align: left; color: #cbd5e1; margin-bottom: 2.5rem; list-style-type: none; padding: 0;">
                <li style="margin-bottom: 0.8rem;">✅ Custom Lead Qual Bot</li>
                <li style="margin-bottom: 0.8rem;">✅ GHL Integration</li>
                <li style="margin-bottom: 0.8rem;">✅ 30 Days Monitoring</li>
                <li style="margin-bottom: 0.8rem;">✅ Custom Prompt Engineering</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with off_col3:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.03); padding: 3rem; border-radius: 24px; border: 1px solid rgba(255,255,255,0.05); height: 100%; text-align: center;">
            <div style="font-size: 1.2rem; color: #94a3b8; margin-bottom: 1rem;">ENTERPRISE</div>
            <h3 style="color: white; font-size: 1.8rem; margin-bottom: 1.5rem;">Revenue Engine</h3>
            <div style="font-size: 2.5rem; color: #6366F1; font-weight: 800; margin-bottom: 2rem;">$15k+</div>
            <ul style="text-align: left; color: #cbd5e1; margin-bottom: 2.5rem; list-style-type: none; padding: 0;">
                <li style="margin-bottom: 0.8rem;">✅ Multi-Agent Swarm</li>
                <li style="margin-bottom: 0.8rem;">✅ Full BI Dashboard</li>
                <li style="margin-bottom: 0.8rem;">✅ Caching Optimization</li>
                <li style="margin-bottom: 0.8rem;">✅ 24/7 SLA Support</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 7. Footer
    st.markdown("""
    <div style="text-align: center; padding: 4rem 0; border-top: 1px solid rgba(255,255,255,0.05);">
        <p style="color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem;">
            © 2026 EnterpriseHub | 4,937 Tests Passing | Built with LangGraph & GHL
        </p>
        <div style="display: flex; justify-content: center; gap: 2rem;">
            <a href="https://github.com/ChunkyTortoise/EnterpriseHub" style="color: #6366F1; text-decoration: none;">GitHub Repository</a>
            <a href="https://linkedin.com/in/your-profile" style="color: #6366F1; text-decoration: none;">LinkedIn Profile</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
