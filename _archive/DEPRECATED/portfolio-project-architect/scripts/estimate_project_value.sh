#!/bin/bash
# Calculate revenue potential for portfolio projects
# Zero-context execution - only output consumes tokens

set -e

PROJECT_TYPE=${1:-"saas"}
DEVELOPMENT_WEEKS=${2:-4}
CURRENT_RATE=${3:-150}

echo "💰 Portfolio Project Value Calculator"
echo "====================================="
echo "Project Type: ${PROJECT_TYPE}"
echo "Development Time: ${DEVELOPMENT_WEEKS} weeks"
echo "Current Hourly Rate: \$${CURRENT_RATE}"
echo ""

# Calculate base investment
DEVELOPMENT_HOURS=$((DEVELOPMENT_WEEKS * 40))
BASE_INVESTMENT=$((DEVELOPMENT_HOURS * CURRENT_RATE))

echo "📊 Investment Analysis:"
echo "  Development Hours: ${DEVELOPMENT_HOURS}"
echo "  Base Investment: \$$(printf "%'d" $BASE_INVESTMENT)"
echo ""

case $PROJECT_TYPE in
  "saas")
    MIN_PROJECT_VALUE=50000
    MAX_PROJECT_VALUE=500000
    TYPICAL_PROJECTS_YEAR=4
    RATE_MULTIPLIER=3
    ;;
  "enterprise")
    MIN_PROJECT_VALUE=100000
    MAX_PROJECT_VALUE=1000000
    TYPICAL_PROJECTS_YEAR=3
    RATE_MULTIPLIER=4
    ;;
  "consulting")
    MIN_PROJECT_VALUE=75000
    MAX_PROJECT_VALUE=300000
    TYPICAL_PROJECTS_YEAR=5
    RATE_MULTIPLIER=2.5
    ;;
esac

# Calculate potential returns
ANNUAL_MIN_REVENUE=$((MIN_PROJECT_VALUE * TYPICAL_PROJECTS_YEAR))
ANNUAL_MAX_REVENUE=$((MAX_PROJECT_VALUE * TYPICAL_PROJECTS_YEAR))
TWO_YEAR_MIN=$((ANNUAL_MIN_REVENUE * 2))
TWO_YEAR_MAX=$((ANNUAL_MAX_REVENUE * 2))

# ROI Calculations
MIN_ROI=$(echo "scale=0; (($TWO_YEAR_MIN - $BASE_INVESTMENT) * 100) / $BASE_INVESTMENT" | bc)
MAX_ROI=$(echo "scale=0; (($TWO_YEAR_MAX - $BASE_INVESTMENT) * 100) / $BASE_INVESTMENT" | bc)

# Payback period (months)
MONTHLY_REVENUE_INCREASE=$((MIN_PROJECT_VALUE / 12))
PAYBACK_MONTHS=$(echo "scale=1; $BASE_INVESTMENT / $MONTHLY_REVENUE_INCREASE" | bc)

echo "🎯 Revenue Potential (2-Year Projection):"
echo "  Min Annual Revenue: \$$(printf "%'d" $ANNUAL_MIN_REVENUE)"
echo "  Max Annual Revenue: \$$(printf "%'d" $ANNUAL_MAX_REVENUE)"
echo "  Min 2-Year Total: \$$(printf "%'d" $TWO_YEAR_MIN)"
echo "  Max 2-Year Total: \$$(printf "%'d" $TWO_YEAR_MAX)"
echo ""

echo "📈 ROI Analysis:"
echo "  Minimum ROI: ${MIN_ROI}%"
echo "  Maximum ROI: ${MAX_ROI}%"
echo "  Payback Period: ${PAYBACK_MONTHS} months"
echo ""

# Rate increase potential
NEW_HOURLY_RATE=$(echo "scale=0; $CURRENT_RATE * $RATE_MULTIPLIER" | bc)
ANNUAL_RATE_INCREASE=$(($(echo "scale=0; ($NEW_HOURLY_RATE - $CURRENT_RATE) * 2000" | bc)))

echo "💼 Rate Improvement Potential:"
echo "  Current Rate: \$${CURRENT_RATE}/hour"
echo "  Portfolio-Enabled Rate: \$${NEW_HOURLY_RATE}/hour"
echo "  Annual Rate Increase Value: \$$(printf "%'d" $ANNUAL_RATE_INCREASE)"
echo ""

# Total business impact
TOTAL_TWO_YEAR_IMPACT=$((TWO_YEAR_MIN + ANNUAL_RATE_INCREASE * 2))
NET_IMPACT=$((TOTAL_TWO_YEAR_IMPACT - BASE_INVESTMENT))

echo "🚀 Total Business Impact (2 Years):"
echo "  Project Value Increase: \$$(printf "%'d" $TWO_YEAR_MIN)"
echo "  Rate Increase Value: \$$(printf "%'d" $((ANNUAL_RATE_INCREASE * 2)))"
echo "  Total Revenue Impact: \$$(printf "%'d" $TOTAL_TWO_YEAR_IMPACT)"
echo "  Net Profit Impact: \$$(printf "%'d" $NET_IMPACT)"
echo "  Total ROI: $(echo "scale=0; ($NET_IMPACT * 100) / $BASE_INVESTMENT" | bc)%"
echo ""

echo "📋 Success Scenarios:"
echo ""
echo "Conservative (Bottom 25%):"
echo "  • 2 projects/year at \$$(printf "%'d" $MIN_PROJECT_VALUE) avg"
echo "  • Rate increase to \$$(echo "scale=0; $CURRENT_RATE * 1.5" | bc)/hour"
echo "  • ROI: $(echo "scale=0; ((($MIN_PROJECT_VALUE * 4) + ($CURRENT_RATE * 1000)) * 100) / $BASE_INVESTMENT" | bc)%"
echo ""
echo "Moderate (Median):"
echo "  • ${TYPICAL_PROJECTS_YEAR} projects/year at \$$(printf "%'d" $(((MIN_PROJECT_VALUE + MAX_PROJECT_VALUE) / 2))) avg"
echo "  • Rate increase to \$$(echo "scale=0; $CURRENT_RATE * 2" | bc)/hour"
echo "  • ROI: $(echo "scale=0; (((($MIN_PROJECT_VALUE + $MAX_PROJECT_VALUE) / 2) * $TYPICAL_PROJECTS_YEAR * 2) * 100) / $BASE_INVESTMENT" | bc)%"
echo ""
echo "Optimistic (Top 25%):"
echo "  • $((TYPICAL_PROJECTS_YEAR + 2)) projects/year at \$$(printf "%'d" $MAX_PROJECT_VALUE) avg"
echo "  • Rate increase to \$${NEW_HOURLY_RATE}/hour"
echo "  • ROI: ${MAX_ROI}%"
echo ""

echo "⚡ Key Success Factors:"
echo "  1. Portfolio quality enables premium positioning"
echo "  2. Technical credibility reduces sales friction"
echo "  3. Demonstrated expertise commands higher rates"
echo "  4. Case studies accelerate business development"
echo "  5. Competitive differentiation creates pricing power"