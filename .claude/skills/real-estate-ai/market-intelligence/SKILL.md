# Market Intelligence Skill

## Overview
Advanced Austin real estate market analysis and property intelligence using MCP integrations.

## Commands

### `/austin-market`
Comprehensive Austin real estate market analysis with trend identification.

**Usage**: `/austin-market [area] [price_range] [timeframe]`
**Example**: `/austin-market west-lake-hills 500k-1m q4-2025`

**Implementation**:
- Uses Firecrawl MCP to scrape current listings
- Analyzes price trends and inventory levels
- Generates market insights with Sequential Thinking
- Stores findings in Memory MCP for trend tracking

### `/property-match`
Match leads from GoHighLevel to Austin property inventory.

**Usage**: `/property-match [lead_id] [criteria]`
**Example**: `/property-match jorge_lead_123 3br-cedar-park-under-600k`

**Implementation**:
- Queries Jorge's GHL account via MCP
- Extracts lead preferences and budget
- Searches properties using Firecrawl
- Generates match recommendations with reasoning

### `/investment-scan`
Identify undervalued Austin properties with growth potential.

**Usage**: `/investment-scan [area] [roi_target] [max_price]`
**Example**: `/investment-scan downtown 15% 800k`

**Implementation**:
- Scrapes property listings and recent sales
- Calculates appreciation potential and ROI
- Uses Sequential Thinking for investment analysis
- Provides ranked opportunity list

### `/market-report`
Generate comprehensive market intelligence reports.

**Usage**: `/market-report [type] [area] [format]`
**Example**: `/market-report cma west-lake-hills pdf`

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

### Austin Geographic Areas
- Downtown Austin (condos, urban living)
- West Lake Hills (luxury, waterfront)
- Cedar Park/Round Rock (family suburbs)
- South Austin (emerging neighborhoods)
- East Austin (gentrification zones)

### Property Types
- Single-family homes (suburban market)
- Luxury properties ($1M+ segment)
- Investment properties (rental opportunities)
- New developments (pre-construction)
- Distressed properties (fix-and-flip)

## Success Metrics

- Property match accuracy >90%
- Market prediction reliability
- Time-to-insight <60 seconds
- Lead-to-property conversion improvement

---
**Ready for Austin real estate market domination!**