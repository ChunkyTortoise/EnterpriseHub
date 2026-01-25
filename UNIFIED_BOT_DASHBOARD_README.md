# 🤖 Jorge AI Unified Bot Dashboard

**Elite Command Center for Lead, Buyer & Seller Bots**

## 🎯 Overview

The Unified Bot Dashboard provides dedicated tabs for each of Jorge's AI bots with comprehensive real-time analytics, chat interfaces, and performance monitoring. This addresses the need for bot-specific interfaces with relevant information, KPIs, and insights for each bot type.

## 🚀 Quick Start

### Option 1: Using the Launcher
```bash
python launch_unified_dashboard.py
```

### Option 2: Direct Streamlit
```bash
python -m streamlit run ghl_real_estate_ai/streamlit_demo/jorge_unified_bot_dashboard.py
```

### Option 3: Custom Port
```bash
streamlit run ghl_real_estate_ai/streamlit_demo/jorge_unified_bot_dashboard.py --server.port 8502
```

## 📋 Features

### 🎯 Lead Bot Tab
- **💬 Live Chat**: Interactive conversation simulator with 3-7-30 day sequences
- **📊 KPIs**: Active sequences, re-engagement rates, day-specific success metrics
- **📈 Analytics**: Sequence performance charts, engagement trends
- **🔄 Pipeline**: Real-time view of active lead sequences and status
- **⚙️ Settings**: Timing configuration, response thresholds, channel preferences

### 🏠 Buyer Bot Tab
- **💬 Live Chat**: Property matching conversation interface
- **📊 KPIs**: Buyers qualified, property matches, showing bookings, offers
- **🏠 Properties**: Property matching interface with search and results
- **📈 Analytics**: Conversion funnel, match accuracy metrics
- **⚙️ Settings**: Matching algorithm weights, qualification criteria

### 💼 Seller Bot Tab
- **💬 Live Chat**: Jorge's confrontational qualification in action
- **📊 KPIs**: Qualification rates, stall detection, FRS/PCS scores
- **📈 Analytics**: FRS distribution, stall-breaking effectiveness
- **🧠 Insights**: Recent qualification insights, market psychology patterns
- **⚙️ Settings**: Jorge's personality controls, compliance settings

## 🏗️ Architecture

### Core Components

```
jorge_unified_bot_dashboard.py          # Main dashboard application
├── UnifiedBotManager                   # Central bot coordination
├── Lead Bot Interface                  # 3-7-30 sequences & nurturing
├── Buyer Bot Interface                 # Property matching & qualification
├── Seller Bot Interface                # Jorge's confrontational qualification
└── Analytics & Insights                # Real-time performance metrics
```

### Supporting Components
```
components/bot_analytics_widgets.py     # Reusable analytics components
├── render_bot_performance_gauge()      # Performance gauges
├── render_conversation_flow_chart()    # Conversation flow analysis
├── render_sentiment_timeline()         # Sentiment tracking
├── render_bot_comparison_radar()       # Multi-bot comparison
└── render_kpi_cards()                 # Beautiful KPI displays
```

## 📊 Metrics & KPIs

### Lead Bot Metrics
- **Sequence Performance**: Active sequences, completion rates
- **Engagement**: Day 3/7/14/30 response rates
- **Re-activation**: Ghost recovery rates, hot lead generation
- **Pipeline**: Conversion rates, engagement scores

### Buyer Bot Metrics
- **Qualification**: Buyers qualified, financial readiness
- **Matching**: Property matches sent, accuracy rates
- **Conversion**: Showings booked, offers submitted
- **Satisfaction**: Buyer satisfaction, closed transactions

### Seller Bot Metrics
- **Qualification**: Total qualifications, qualification rate
- **Jorge's Skills**: Stall detection, take-away close success
- **Scoring**: Average FRS/PCS scores, hot lead identification
- **Conversion**: Voice handoffs, listing conversion rates

## 🎨 UI/UX Features

### Interactive Chat Interfaces
- Real-time conversation simulation for each bot
- Message history tracking with timestamps
- Bot response generation with strategy display
- Context-aware responses based on bot personality

### Real-time Analytics
- Live updating metrics and KPIs
- Interactive charts and visualizations
- Performance trends and patterns
- Comparative bot analysis

### Elite Styling
- Obsidian theme integration for premium feel
- Responsive design for all screen sizes
- Dark mode optimized for professional use
- Animated status indicators and progress bars

## ⚙️ Configuration

### Bot Settings
Each bot has dedicated configuration options:

**Lead Bot Configuration:**
- Sequence timing (day 3, 7, 14, 30)
- Response thresholds and scoring
- Channel preferences (SMS, Voice, Email)
- AI behavior and personalization

**Buyer Bot Configuration:**
- Property matching algorithm weights
- Qualification criteria and thresholds
- Communication preferences
- Financial requirements

**Seller Bot Configuration:**
- Jorge's confrontational intensity
- Stall detection sensitivity
- Take-away close triggers
- Compliance controls

### System Health Monitoring
- Real-time bot status monitoring
- Integration health checks (GHL, Claude, Analytics)
- Performance SLA tracking
- Error rate and uptime metrics

## 🔌 Integrations

### Existing Bot Services
- **Jorge Seller Bot**: Full integration with LangGraph workflows
- **Lead Bot Workflow**: 3-7-30 day sequence automation
- **Jorge Buyer Bot**: Property matching and qualification
- **Analytics Service**: Real-time metrics and insights

### Data Sources
- **GHL CRM**: Lead and seller data synchronization
- **MLS Integration**: Property data for buyer matching
- **Claude API**: AI conversation processing
- **Event Publisher**: Real-time activity streaming

## 📱 Usage Examples

### Starting a Lead Bot Conversation
1. Navigate to "🎯 Lead Bot" tab
2. Select "💬 Live Chat"
3. Choose active lead from dropdown
4. Set sequence step (day 3, 7, 14, 30)
5. Type lead message and click "Send to Lead Bot"
6. View bot response and sequence advancement

### Analyzing Seller Bot Performance
1. Navigate to "💼 Seller Bot" tab
2. View "📊 KPIs" for key performance metrics
3. Check "📈 Analytics" for FRS distribution and stall patterns
4. Review "🧠 Insights" for qualification intelligence
5. Adjust "⚙️ Settings" to optimize Jorge's behavior

### Monitoring System Health
1. Check sidebar "🔗 System Health" section
2. View individual bot status indicators
3. Use "🔄 Refresh Data" for latest metrics
4. Monitor global system status at bottom

## 🛠️ Development

### Adding New Bot Features
1. Extend `UnifiedBotManager` class with new methods
2. Add corresponding render functions for UI components
3. Update bot-specific tabs with new functionality
4. Test integration with existing analytics

### Custom Analytics Widgets
1. Use components from `bot_analytics_widgets.py`
2. Create custom visualizations with Plotly
3. Integrate with real-time data streams
4. Add to appropriate bot tabs

## 🚨 Troubleshooting

### Common Issues

**Dashboard won't start:**
- Check Python environment and dependencies
- Verify Streamlit installation: `pip install streamlit`
- Ensure you're in the correct directory

**Bots show as offline:**
- Check bot service imports in console
- Verify database connections
- Review analytics service configuration

**Charts not displaying:**
- Check Plotly installation: `pip install plotly`
- Verify data format in browser console
- Clear Streamlit cache and refresh

**Performance issues:**
- Use `st.cache_resource` for expensive operations
- Implement data pagination for large datasets
- Monitor memory usage in production

## 📈 Performance Optimization

### Caching Strategy
- Bot managers cached with `@st.cache_resource`
- Metrics data cached for 5 minutes
- Conversation history stored in session state

### Real-time Updates
- WebSocket integration for live data
- Event-driven metric updates
- Efficient state management

## 🔮 Future Enhancements

### Planned Features
- **Voice Integration**: Real-time voice call monitoring
- **A/B Testing**: Bot personality experimentation
- **Advanced Analytics**: Predictive modeling and forecasting
- **Mobile Optimization**: Progressive Web App capabilities
- **Multi-tenant Support**: Agency-level deployment

### Integration Roadmap
- **CRM Sync**: Bidirectional data synchronization
- **Webhook Support**: Real-time external integrations
- **API Endpoints**: RESTful API for external access
- **Export Capabilities**: PDF reports and data export

## 📞 Support

For issues, enhancements, or questions:
1. Check troubleshooting section above
2. Review console logs for error details
3. Test with mock data before reporting issues
4. Provide specific reproduction steps

---

**Version**: 1.0.0
**Last Updated**: 2026-01-25
**Status**: Production Ready 🚀