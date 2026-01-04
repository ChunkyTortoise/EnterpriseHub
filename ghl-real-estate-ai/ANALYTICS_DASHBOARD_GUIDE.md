# Analytics Dashboard User Guide

## Overview

The GHL Real Estate AI Analytics Dashboard provides comprehensive, real-time insights into multi-tenant performance, lead quality metrics, and system health monitoring. Built with Streamlit and Plotly, the dashboard offers interactive visualizations and drill-down capabilities for data-driven decision making.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Layout](#dashboard-layout)
3. [Overview Tab](#overview-tab)
4. [Tenant Details Tab](#tenant-details-tab)
5. [System Health Tab](#system-health-tab)
6. [Filters and Navigation](#filters-and-navigation)
7. [Performance Metrics Explained](#performance-metrics-explained)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

- Python 3.11+
- Streamlit 1.50.0+
- Plotly 6.5.0+
- Mock data file: `data/mock_analytics.json`

### Running the Dashboard

1. Navigate to the project root:
   ```bash
   cd /path/to/ghl-real-estate-ai
   ```

2. Launch the dashboard:
   ```bash
   streamlit run streamlit_demo/analytics.py
   ```

3. Open your browser to `http://localhost:8501`

### First-Time Setup

The dashboard automatically loads mock data from `data/mock_analytics.json`. This file contains:
- 3 sample tenants (Luxury Estates Group, Metro Realty Partners, Coastal Homes Unlimited)
- 50+ conversations with realistic metrics
- System health data

---

## Dashboard Layout

The dashboard is organized into three main tabs:

1. **Overview** - High-level performance metrics and trends
2. **Tenant Details** - Drill-down analysis by tenant
3. **System Health** - Infrastructure and performance monitoring

### Responsive Design

The dashboard is optimized for:
- Desktop (1920x1080 and above)
- Tablet (768x1024)
- Mobile (375x667 minimum)

All charts and metrics automatically resize for optimal viewing.

---

## Overview Tab

### Top Metrics Row

| Metric | Description | Calculation |
|--------|-------------|-------------|
| **Total Conversations** | Number of conversations in selected date range | Count of all conversations |
| **Avg Lead Score** | Average lead quality score (0-100) | Sum of scores / count |
| **Total Messages** | Total messages exchanged | Sum of message_count |
| **Conversion Rate** | Probability of lead conversion | Average conversion_probability |

Delta values show:
- Unique contact count (for Total Conversations)
- Hot leads count (for Avg Lead Score)
- Messages per conversation (for Total Messages)
- Average response time (for Conversion Rate)

### Lead Breakdown

Quick view of lead classifications:
- **Hot Leads** (Score ≥ 70): Red indicator
- **Warm Leads** (Score 50-69): Orange indicator
- **Cold Leads** (Score < 50): Blue indicator

### Visualization Charts

#### 1. Conversation Volume Over Time
- **Type**: Line chart with area fill
- **Purpose**: Track conversation trends by date
- **Insights**: Identify peak activity periods, weekly patterns

#### 2. Lead Classification Breakdown
- **Type**: Donut pie chart
- **Purpose**: Visualize distribution of lead quality
- **Insights**: Assess overall lead quality, identify improvement areas

#### 3. Lead Score Distribution
- **Type**: Histogram (20 bins)
- **Purpose**: Show score distribution across all leads
- **Insights**: Identify score clusters, outliers

#### 4. Avg Response Time by Lead Type
- **Type**: Bar chart
- **Purpose**: Compare response times across classifications
- **Insights**: Validate faster responses for hot leads

#### 5. Contact Intent Distribution
- **Type**: Bar chart
- **Purpose**: Show buyer vs. seller vs. browsing breakdown
- **Insights**: Understand contact motivation mix

---

## Tenant Details Tab

### Tenant Summary Table

Displays all tenants with key metrics:

| Column | Description |
|--------|-------------|
| Tenant | Tenant business name |
| Region | Geographic location |
| Tier | Subscription tier (Standard, Premium, Enterprise) |
| Conversations | Total conversations in date range |
| Avg Score | Average lead score |
| Hot Leads | Count of hot leads |
| Conversion Rate | Average conversion probability |

### Individual Tenant Analysis

Select a tenant for detailed drill-down:

1. **Tenant Information**
   - Location ID (unique identifier)
   - Region and tier

2. **Metrics Row**
   - Conversations count
   - Average score
   - Hot leads
   - Total messages

3. **Charts**
   - Lead score distribution (tenant-specific)
   - Intent breakdown (tenant-specific)

4. **Recent Conversations Table**
   - Last 10 conversations
   - Shows: Contact name, date, messages, score, classification, intent, budget

### Use Cases

- **Performance Comparison**: Compare metrics across tenants
- **Tenant Health Check**: Identify struggling tenants
- **Resource Allocation**: Prioritize high-performing regions
- **Billing Validation**: Verify usage aligns with tier

---

## System Health Tab

### Top-Level Health Metrics

| Metric | Healthy Range | Warning Threshold |
|--------|---------------|-------------------|
| Uptime | > 99.5% | < 99% |
| Error Rate | < 1% | > 2% |
| API Calls (24h) | Varies | N/A |
| Avg Response Time | < 500ms | > 1000ms |

### Performance Metrics

#### API Performance
- **Anthropic API Latency**: Average time for AI responses
- **Cache Hit Rate**: Percentage of cached responses (target: > 80%)
- **Active Webhooks**: Number of active GHL webhooks

#### Infrastructure
- **CPU Usage**: Server CPU utilization (target: < 70%)
- **Memory Usage**: RAM consumption in MB
- **Disk Usage**: Storage consumption in GB

### Database & Resources

- **Connection Pool**: Visual progress bar showing active/max connections
- **Healthy**: < 70% utilization
- **Warning**: 70-90% utilization
- **Critical**: > 90% utilization

### SMS & Communication

- **SMS Sent (24h)**: Total outbound SMS messages
- **Compliance Rate**: Percentage meeting regulatory requirements (target: > 95%)
- **AI Tokens Used**: Anthropic Claude API token consumption

### Overall System Status

Three-level health indicator:
- **HEALTHY**: All metrics in normal range
- **DEGRADED**: One or more warnings
- **CRITICAL**: Uptime < 95% or error rate > 5%

---

## Filters and Navigation

### Sidebar Filters

#### Tenant Selection
- **All Tenants**: Aggregate view of all locations
- **Individual Tenant**: Select specific tenant by name

#### Date Range

**Quick Select Options:**
- Last 7 Days (default)
- Last 30 Days
- Last 90 Days
- Custom (manual date picker)

**Custom Date Range:**
- Start Date: Select from calendar
- End Date: Select from calendar
- Max range: 1 year

#### Lead Classification Filter

Multi-select filter:
- Hot
- Warm
- Cold

Use cases:
- View only hot leads for sales prioritization
- Exclude cold leads for engagement analysis
- Compare warm vs. hot conversion rates

### Navigation Tips

1. **Filter First**: Set filters before analyzing to reduce data load
2. **Compare Periods**: Use custom date ranges to compare month-over-month
3. **Drill Down**: Start with Overview, then use Tenant Details for specifics
4. **Export Data**: Use browser print (Cmd/Ctrl+P) to save as PDF

---

## Performance Metrics Explained

### Lead Scoring

| Score Range | Classification | Typical Characteristics |
|-------------|----------------|-------------------------|
| 70-100 | Hot | High engagement, clear intent, budget confirmed |
| 50-69 | Warm | Moderate engagement, exploring options |
| 0-49 | Cold | Low engagement, browsing only |

### Response Time

- **Target**: < 15 seconds average
- **Calculation**: Average of all message response times in conversation
- **Impact**: Faster responses correlate with higher conversion rates

### Conversion Probability

- **Range**: 0.0 to 1.0 (0% to 100%)
- **Calculation**: AI-predicted likelihood of lead closing
- **Factors**: Lead score, response time, intent, budget clarity

### Message Count

- **Typical Range**: 5-15 messages per conversation
- **Interpretation**:
  - < 5: Brief inquiry or automated response
  - 5-10: Normal engagement
  - 10-15: High engagement, detailed discussion
  - > 15: Complex inquiry or multiple topics

---

## Troubleshooting

### Dashboard Won't Load

**Problem**: Blank screen or error on startup

**Solutions**:
1. Verify Streamlit installation: `pip install streamlit==1.50.0`
2. Check Python version: `python --version` (must be 3.11+)
3. Verify file path: Ensure running from project root
4. Check console for errors: Look for import errors

### Mock Data Not Found

**Problem**: "No conversations found" message

**Solutions**:
1. Verify `data/mock_analytics.json` exists
2. Check JSON syntax: `python -m json.tool data/mock_analytics.json`
3. Regenerate mock data if corrupted
4. Verify file permissions: `chmod 644 data/mock_analytics.json`

### Charts Not Rendering

**Problem**: Blank spaces where charts should appear

**Solutions**:
1. Install Plotly: `pip install plotly==6.5.0`
2. Clear browser cache (Cmd/Ctrl+Shift+R)
3. Try different browser (Chrome, Firefox recommended)
4. Check JavaScript enabled in browser

### Slow Performance

**Problem**: Dashboard takes > 5 seconds to load

**Solutions**:
1. Reduce date range (use Last 7 Days instead of Last 90 Days)
2. Filter by single tenant instead of "All Tenants"
3. Clear Streamlit cache: Settings > Clear Cache
4. Restart Streamlit server
5. Check system resources (CPU, RAM)

### Date Filter Not Working

**Problem**: No data after changing dates

**Solutions**:
1. Verify date range includes conversation dates
2. Check conversation timestamps in `mock_analytics.json`
3. Ensure start_date < end_date
4. Try "Last 7 Days" preset first

### Metrics Showing Zero

**Problem**: All metrics display 0 despite data existing

**Solutions**:
1. Check lead classification filter (ensure at least one selected)
2. Verify tenant selection matches data
3. Expand date range
4. Reload dashboard (Cmd/Ctrl+R)

---

## Advanced Usage

### Custom Data Integration

To use real data instead of mock data:

1. Modify `load_mock_data()` function in `analytics.py`
2. Point to your analytics database or API
3. Ensure data structure matches mock format
4. Test with small dataset first

### Exporting Reports

**PDF Export:**
1. Navigate to desired view
2. Print page (Cmd/Ctrl+P)
3. Select "Save as PDF"
4. Adjust layout for optimal fit

**Data Export:**
- Use browser DevTools Network tab to intercept API calls
- Export tables by selecting and copying
- Consider adding CSV export functionality (future enhancement)

### Scheduled Reports

Use cron or Task Scheduler to:
1. Launch dashboard at specific times
2. Capture screenshots with headless browser
3. Email reports to stakeholders

Example cron (daily at 8 AM):
```bash
0 8 * * * /usr/local/bin/streamlit run /path/to/analytics.py --server.headless true
```

---

## Best Practices

### Dashboard Usage

1. **Review Daily**: Check Overview tab each morning
2. **Weekly Deep Dive**: Analyze Tenant Details every Monday
3. **Monthly Health Check**: Review System Health on 1st of month
4. **Set Alerts**: Monitor uptime, error rate, compliance

### Data Interpretation

1. **Context Matters**: Consider seasonality, marketing campaigns
2. **Trends Over Absolutes**: Focus on direction, not single values
3. **Segment Analysis**: Compare tenants by tier, region
4. **Correlate Metrics**: Link response time to conversion rate

### Performance Optimization

1. **Use Filters**: Don't load all data at once
2. **Cache Wisely**: Streamlit caches data for 60 seconds
3. **Limit Date Ranges**: 30 days max for detailed analysis
4. **Monitor Load Time**: Should be < 3 seconds consistently

---

## Support and Resources

### Documentation
- [Streamlit Docs](https://docs.streamlit.io/)
- [Plotly Python Docs](https://plotly.com/python/)
- Project README: `streamlit_demo/README.md`

### Testing
Run dashboard tests:
```bash
pytest tests/test_analytics_dashboard.py -v
```

### Contact
For issues, feature requests, or questions:
- File GitHub issue
- Contact: analytics-support@yourcompany.com

---

## Changelog

### Version 1.0.0 (2026-01-04)
- Initial release
- Three-tab layout (Overview, Tenant Details, System Health)
- 50+ mock conversations across 3 tenants
- Mobile-responsive design
- Performance optimized (< 3s load time)
- Comprehensive filtering (date, tenant, classification)
- 5 chart types (timeline, pie, histogram, bar)
- System health monitoring
- Test coverage (95%+)

---

## Appendix: Mock Data Schema

### Tenant Structure
```json
{
  "location_id": "string",
  "name": "string",
  "created_at": "ISO8601 timestamp",
  "tier": "standard|premium|enterprise",
  "region": "string"
}
```

### Conversation Structure
```json
{
  "conversation_id": "string",
  "location_id": "string",
  "contact_id": "string",
  "contact_name": "string",
  "start_time": "ISO8601 timestamp",
  "end_time": "ISO8601 timestamp",
  "message_count": "integer",
  "lead_score": "0-100",
  "classification": "hot|warm|cold",
  "intent": "buyer|seller|browsing",
  "budget": "string",
  "response_time_avg_seconds": "float",
  "sentiment": "very_positive|positive|neutral|negative",
  "conversion_probability": "0.0-1.0"
}
```

### System Health Structure
```json
{
  "total_api_calls_24h": "integer",
  "avg_response_time_ms": "integer",
  "uptime_percentage": "float",
  "error_rate_percentage": "float",
  "active_webhooks": "integer",
  "cache_hit_rate": "0.0-1.0",
  "database_connections_active": "integer",
  "database_connections_max": "integer",
  "memory_usage_mb": "integer",
  "cpu_usage_percentage": "integer",
  "disk_usage_gb": "float",
  "sms_sent_24h": "integer",
  "sms_compliance_rate": "0.0-1.0",
  "anthropic_tokens_used_24h": "integer",
  "anthropic_api_latency_avg_ms": "integer"
}
```

---

**Last Updated**: January 4, 2026
**Version**: 1.0.0
**Author**: GHL Real Estate AI Team
