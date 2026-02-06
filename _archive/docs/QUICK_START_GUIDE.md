# 🚀 GHL Real Estate AI - Quick Start Guide

**Get your AI-powered real estate platform running in 5 minutes!**

---

## ⚡ **FASTEST START (2 Minutes)**

### **Option 1: Automated Setup**
```bash
# Run the automated setup script
./setup_demo.sh

# Follow the prompts, then start the demo
source venv/bin/activate
cd ghl_real_estate_ai/streamlit_demo
streamlit run app.py
```

**Open your browser to:** http://localhost:8501

---

### **Option 2: Manual Setup**
```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env

# 4. Start the demo
cd ghl_real_estate_ai/streamlit_demo
streamlit run app.py
```

---

## 🎯 **DEMO FEATURES (Ready to Test)**

### **🏢 Executive Command Center**
- **$2.4M Active Pipeline** - Realistic Austin market data
- **Real-time Metrics** - Conversion rates, deal sizes, revenue tracking
- **Business Intelligence** - Performance analytics and insights
- **System Health** - API status and performance monitoring

### **🧠 Lead Intelligence Hub (MAIN ATTRACTION)**
- **AI Lead Scoring** - 0-100% conversion probability
- **Behavioral Analytics** - Property engagement tracking
- **Property Swipe Interface** - Tinder-style matching experience
- **Real-time Telemetry** - Live activity monitoring
- **Strategic Recommendations** - AI-generated next actions

### **🤖 Automation Studio**
- **Visual Workflow Builder** - Drag-and-drop automation
- **Pre-built Campaigns** - Ready-to-use lead nurturing
- **24/7 AI Responder** - Intelligent lead engagement
- **Performance Tracking** - Conversion and engagement analytics

### **💰 Sales Copilot**
- **Document Generator** - Instant CMAs and listing descriptions
- **Deal Pipeline** - Visual deal tracking and management
- **Meeting Prep** - AI briefings for appointments
- **Commission Calculator** - Real-time earnings tracking

### **📈 Operations & Optimization**
- **Quality Assurance** - Interaction scoring and optimization
- **Revenue Attribution** - Marketing channel ROI analysis
- **Competitive Intelligence** - Market insights and positioning
- **Performance Analytics** - Comprehensive business metrics

---

## 🔑 **API KEYS SETUP (For Full Functionality)**

### **Required for AI Features:**

#### **1. Claude AI (Anthropic)**
```bash
# Get key from: https://console.anthropic.com/
# Add to .env file:
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

#### **2. GoHighLevel CRM**
```bash
# Get from: GHL Settings → API
# Add to .env file:
GHL_API_KEY=your-ghl-api-key
LOCATION_ID=your-location-id
```

### **What Works WITHOUT API Keys:**
- ✅ Full UI demonstration
- ✅ Demo data exploration ($2.4M pipeline)
- ✅ All component interactions
- ✅ Performance analytics
- ✅ Document templates
- ✅ Workflow visualizations

### **What Requires API Keys:**
- 🔑 Live AI chat responses
- 🔑 Real-time lead scoring
- 🔑 GHL CRM synchronization
- 🔑 Dynamic content generation

---

## 🎬 **DEMO WALKTHROUGH (15 Minutes)**

### **Step 1: Executive Overview (3 min)**
1. Open http://localhost:8501
2. Click "Executive Command Center"
3. Explore the $2.4M pipeline visualization
4. Review key performance metrics

### **Step 2: Lead Intelligence (5 min)**
1. Navigate to "Lead Intelligence Hub"
2. Select "Sarah Chen" (high-scoring tech lead)
3. Review AI insights and behavioral data
4. Test the property swipe interface
5. Check real-time telemetry

### **Step 3: AI Chat Interface (3 min)**
1. Open chat panel in Lead Intelligence
2. Try queries like:
   - "What's the best strategy for Sarah?"
   - "Which leads are ready to buy?"
   - "Show me high-value opportunities"

### **Step 4: Automation Studio (2 min)**
1. Explore pre-built workflows
2. View campaign performance metrics
3. Test workflow builder interface

### **Step 5: Document Generation (2 min)**
1. Go to "Sales Copilot"
2. Generate a CMA for Austin property
3. Create listing description with AI
4. Review quality and time savings

---

**🚀 Ready to see the future of real estate AI? Start your demo now!**

```bash
./setup_demo.sh
```

**Last Updated:** January 13, 2026
**Status:** ✅ Demo Environment Ready
