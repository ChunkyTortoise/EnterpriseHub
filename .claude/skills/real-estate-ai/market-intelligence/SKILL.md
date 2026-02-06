# Market Intelligence Skill

## Overview
Advanced Rancho Cucamonga real estate market analysis and property intelligence using MCP integrations.

## Commands

### `/rancho-market`
Comprehensive Rancho Cucamonga real estate market analysis with trend identification.

**Usage**: `/rancho-market [area] [price_range] [timeframe]`
**Example**: `/rancho-market alta-loma 500k-800k q4-2025`

**Implementation**:
- Uses Firecrawl MCP to scrape current listings
- Analyzes price trends and inventory levels
- Generates market insights with Sequential Thinking
- Stores findings in Memory MCP for trend tracking

### `/property-match`
Match leads from GoHighLevel to Rancho Cucamonga property inventory.

**Usage**: `/property-match [lead_id] [criteria]`
**Example**: `/property-match jorge_lead_123 3br-etiwanda-under-700k`

**Implementation**:
- Queries Jorge's GHL account via MCP
- Extracts lead preferences and budget
- Searches properties using Firecrawl
- Generates match recommendations with reasoning

### `/investment-scan`
Identify undervalued Rancho Cucamonga properties with growth potential.

**Usage**: `/investment-scan [area] [roi_target] [max_price]`
**Example**: `/investment-scan terra-vista 12% 750k`

**Implementation**:
- Scrapes property listings and recent sales
- Calculates appreciation potential and ROI
- Uses Sequential Thinking for investment analysis
- Provides ranked opportunity list

### `/market-report`
Generate comprehensive market intelligence reports.

**Usage**: `/market-report [type] [area] [format]`
**Example**: `/market-report cma alta-loma pdf`

**Implementation**:
- Gathers multi-source property data
- Analyzes comparable sales and trends
- Creates formatted reports (PDF, dashboard)
- Stores report data in PostgreSQL

## Integration Points

- **GoHighLevel MCP**: Lead data and preferences
- **Firecrawl MCP**: Property listings and market data
- **PostgreSQL MCP**: Data storage and analytics
- **Sequential Thinking MCP**: Complex market analysis
- **Memory MCP**: Trend tracking and insights

## Market Specializations

### Rancho Cucamonga Geographic Areas
- Alta Loma (foothills, equestrian properties, premium lots)
- Etiwanda (top-rated schools, family neighborhoods)
- Haven Avenue Corridor (commercial proximity, newer builds)
- Victoria Gardens Area (walkable retail, urban feel)
- Terra Vista / Day Creek (planned communities, HOA-managed)

### Property Types
- Single-family homes (primary market, ~$650K median)
- Luxury properties ($1M+ foothills segment)
- Investment properties (rental opportunities, IE growth)
- New developments (pre-construction in Day Creek)
- Multi-family (duplex/triplex near transit)

## Success Metrics

- Property match accuracy >90%
- Market prediction reliability
- Time-to-insight <60 seconds
- Lead-to-property conversion improvement

---
**Ready for Rancho Cucamonga real estate market intelligence!**
