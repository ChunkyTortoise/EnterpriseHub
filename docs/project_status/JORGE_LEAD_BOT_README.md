# 🤖 Jorge's AI Lead Bot System - Complete Setup Guide

**Automated Lead Generation & Qualification for GoHighLevel**

---

## 🚀 Quick Start (5 Minutes)

### Option 1: Simple Dashboard Launch
```bash
# Install requirements (one-time setup)
pip install streamlit fastapi uvicorn requests

# Launch Jorge's dashboard
python jorge_lead_bot_launcher.py
```
🌐 **Dashboard opens at**: http://localhost:8501

### Option 2: Full System (API + Dashboard)
```bash
# Terminal 1 - Start API Server
python jorge_lead_bot_launcher.py --api

# Terminal 2 - Start Dashboard  
python jorge_lead_bot_launcher.py
```

---

## 🎯 What Jorge Gets

### 📞 **Voice AI Phone Integration**
- **Automatic lead qualification calls**
- Real-time conversation processing with Claude AI
- Intelligent call scoring and qualification
- Automatic transfer to Jorge for high-quality leads
- Complete call analytics and reporting

### 🎯 **Automated Marketing Campaigns**
- **AI-powered campaign generation** based on triggers
- Smart audience targeting and segmentation
- Multi-channel campaigns (Email, SMS, Social, Direct Mail)
- A/B testing and optimization
- ROI tracking and performance analytics

### 🤝 **Client Retention & Referral System**
- **Automatic lifecycle tracking** for all clients
- Smart referral opportunity detection
- Engagement scoring and retention prediction
- Automated follow-up sequences
- Lifetime value calculation

### 📈 **Market Prediction Analytics**
- **AI-powered market trend analysis**
- Investment opportunity identification
- Price appreciation predictions
- Market velocity and risk assessment
- Competitive landscape insights

---

## 🎛️ Dashboard Overview

### **Command Center** - Main Dashboard
- Real-time system health monitoring
- Key performance metrics across all modules
- Quick action buttons for emergency overrides
- Live data from GHL integration

### **Voice AI Tab**
- Start new qualification calls instantly
- Monitor call performance and outcomes
- View qualification scores and analytics
- Review successful lead transfers

### **Marketing Tab** 
- Create AI-powered campaigns in minutes
- Monitor active campaign performance
- Launch blast campaigns for opportunities
- Track ROI and conversion metrics

### **Retention Tab**
- Update client lifecycle events
- Track referral opportunities
- Monitor engagement scores
- View top referral sources

### **Market Intelligence Tab**
- Request market analysis for any area
- Generate investment opportunity reports
- View prediction accuracy metrics
- Access historical trend data

---

## 🔧 Technical Setup

### **Requirements**
```bash
Python 3.11+
streamlit >= 1.31.0
fastapi >= 0.104.0
uvicorn >= 0.24.0
requests >= 2.31.0
```

### **Environment Variables**
Create `.env` file:
```bash
# Claude AI Configuration
ANTHROPIC_API_KEY=your_claude_api_key_here

# GoHighLevel Integration  
GHL_API_KEY=your_ghl_api_key_here
GHL_WEBHOOK_SECRET=your_webhook_secret_here

# Redis Cache (Optional)
REDIS_URL=redis://localhost:6379

# Database (Optional - uses SQLite by default)
DATABASE_URL=postgresql://user:pass@localhost/jorge_leads
```

### **GHL Webhook Setup**
1. In GHL, go to Settings → Integrations → Webhooks
2. Add new webhook: `http://your-server:8000/webhooks/ghl`
3. Select events: Contact Created, Contact Updated, Opportunity Created
4. Use the webhook secret from your `.env` file

---

## 📊 API Endpoints

### **Voice AI Endpoints**
```bash
POST /jorge-advanced/voice/start-call      # Start AI qualification call
POST /jorge-advanced/voice/process-input   # Process voice input
POST /jorge-advanced/voice/end-call        # End call and get analytics
GET  /jorge-advanced/voice/analytics       # Get voice system analytics
```

### **Marketing Automation**
```bash
POST /jorge-advanced/marketing/create-campaign     # Create AI campaign
GET  /jorge-advanced/marketing/campaigns/{id}/content    # Get campaign content
GET  /jorge-advanced/marketing/campaigns/{id}/performance # Campaign metrics
POST /jorge-advanced/marketing/ab-test/{id}        # Start A/B test
```

### **Client Retention**
```bash
POST /jorge-advanced/retention/update-lifecycle    # Update client lifecycle
POST /jorge-advanced/retention/track-referral      # Track new referral
GET  /jorge-advanced/retention/client/{id}/engagement # Client engagement summary
GET  /jorge-advanced/retention/analytics           # Retention system analytics
```

### **Market Predictions**
```bash
POST /jorge-advanced/market/analyze                # Market trend analysis
POST /jorge-advanced/market/investment-opportunities # Find investment properties
GET  /jorge-advanced/market/trends/{neighborhood}   # Get market trends
```

### **System Health**
```bash
GET /jorge-advanced/dashboard/metrics      # Unified dashboard metrics
GET /jorge-advanced/health/modules         # Module health status
GET /jorge-advanced/health                 # System health check
```

---

## 🎮 How to Use

### **Daily Workflow**

1. **Morning Check** - Open dashboard, review overnight activity
2. **Call Management** - Monitor Voice AI call handling
3. **Campaign Review** - Check marketing campaign performance
4. **Lead Follow-up** - Process qualified leads from Voice AI
5. **Market Opportunities** - Review new investment opportunities
6. **Client Touch-points** - Update lifecycle events, track referrals

### **Emergency Situations**

- **High-Volume Calls**: Use "Emergency Call Override" to route all calls to Jorge directly
- **Market Opportunities**: Use "Launch Blast Campaign" for urgent market opportunities
- **System Issues**: Check Module Health status for troubleshooting

### **Weekly/Monthly Tasks**

- Export performance reports
- Review and optimize campaign performance
- Update market prediction models
- Analyze client retention metrics
- Plan new marketing campaigns

---

## 🛡️ Security & Compliance

### **Data Protection**
- All client data encrypted at rest
- Redis cache with TTL expiration
- No PII in logs or error messages
- Webhook signature verification

### **API Security**
- Rate limiting on all endpoints
- Input validation with Pydantic models
- Error handling without data exposure
- HTTPS enforcement in production

### **GHL Integration Security**
- Webhook signature verification
- API key rotation support
- Audit logging for all actions
- Compliance with GHL terms

---

## 🚨 Troubleshooting

### **Common Issues**

**Dashboard won't start:**
```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall requirements
pip install --upgrade streamlit fastapi uvicorn requests
```

**API connection failed:**
```bash
# Check if API server is running
curl http://localhost:8000/jorge-advanced/health

# Start API server
python jorge_lead_bot_launcher.py --api
```

**GHL webhook errors:**
- Verify webhook URL is accessible from internet
- Check webhook secret matches `.env` file
- Review GHL webhook logs in their dashboard

**Claude AI errors:**
- Verify `ANTHROPIC_API_KEY` in `.env` file
- Check API key has sufficient credits
- Monitor rate limiting in logs

### **Performance Optimization**

- **Redis Cache**: Enable for faster response times
- **Database**: Use PostgreSQL for production (vs SQLite)
- **Load Balancing**: Use multiple API instances for high volume
- **CDN**: Serve dashboard assets through CDN

---

## 📈 Scaling for Growth

### **High-Volume Setup**
- Deploy API to cloud (AWS, GCP, Azure)
- Use managed Redis (ElastiCache, Google Memory Store)
- Set up load balancer for API instances
- Enable auto-scaling based on call volume

### **Multi-Market Expansion**
- Configure market-specific prediction models
- Set up regional API deployments
- Customize campaigns by market
- Enable multi-timezone support

### **Team Integration**
- Add user authentication
- Role-based access control
- Team performance dashboards
- Lead assignment automation

---

## 🎉 Success Metrics

Jorge's system tracks these key performance indicators:

### **Voice AI Performance**
- Call qualification rate: **Target 50%+**
- Average call duration: **Target 4-6 minutes**
- Transfer rate to Jorge: **Target 15%+**
- Lead quality score: **Target 80%+**

### **Marketing ROI**
- Campaign conversion rate: **Target 3%+**
- Cost per lead: **Target <$20**
- Email open rates: **Target 25%+**
- Overall ROI: **Target 300%+**

### **Client Retention**
- Client retention rate: **Target 90%+**
- Referrals per month: **Target 10+**
- Lifetime value growth: **Target 15%+ annually**
- Engagement score: **Target 80%+**

### **Market Intelligence**
- Prediction accuracy: **Target 85%+**
- Opportunities identified: **Target 10+ monthly**
- Market trend alerts: **Target 5+ weekly**
- Investment ROI potential: **Target 20%+**

---

## 📞 Support & Contact

For technical support or questions about Jorge's Lead Bot System:

1. **Check the logs** in the dashboard Module Health section
2. **Review this README** for common solutions
3. **Test individual components** using the API endpoints
4. **Check GHL webhook logs** for integration issues

**System developed specifically for Jorge's Rancho Cucamonga real estate business**

---

## 🔄 Updates & Maintenance

The system includes:
- **Automatic error recovery** for API failures
- **Health monitoring** for all components  
- **Performance analytics** for optimization
- **Backup and recovery** procedures
- **Version control** for configuration changes

Jorge's Lead Bot System is designed to run 24/7 with minimal maintenance required.

**Ready to automate your lead generation? Launch the system and start converting more leads!** 🚀