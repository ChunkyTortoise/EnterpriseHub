#!/bin/bash
# Phase 3 Monitoring Validation Script
# Validates that all monitoring components are properly configured
# Created: January 10, 2026

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

echo "================================================================================"
echo "  Phase 3 Production Monitoring - Validation Script"
echo "  Validating $265K-440K annual value monitoring infrastructure"
echo "================================================================================"
echo ""

# Function to print test result
print_result() {
    local test_name=$1
    local result=$2
    local message=$3

    if [ "$result" == "PASS" ]; then
        echo -e "${GREEN}✓${NC} $test_name"
        ((PASSED++))
    elif [ "$result" == "FAIL" ]; then
        echo -e "${RED}✗${NC} $test_name"
        if [ ! -z "$message" ]; then
            echo "  → $message"
        fi
        ((FAILED++))
    elif [ "$result" == "WARN" ]; then
        echo -e "${YELLOW}⚠${NC} $test_name"
        if [ ! -z "$message" ]; then
            echo "  → $message"
        fi
        ((WARNINGS++))
    fi
}

echo "1. CONFIGURATION FILES"
echo "------------------------------------------------------------"

# Check Phase 3 alert rules exist
if [ -f "config/monitoring/phase3_alerts.yml" ]; then
    print_result "Phase 3 alert rules file exists" "PASS"
else
    print_result "Phase 3 alert rules file exists" "FAIL" "File not found: config/monitoring/phase3_alerts.yml"
fi

# Check Grafana dashboard exists
if [ -f "config/monitoring/grafana/dashboards/phase3_production_monitoring.json" ]; then
    print_result "Grafana dashboard file exists" "PASS"
else
    print_result "Grafana dashboard file exists" "FAIL" "File not found: config/monitoring/grafana/dashboards/phase3_production_monitoring.json"
fi

# Check metrics exporter exists
if [ -f "ghl_real_estate_ai/services/monitoring/phase3_metrics_exporter.py" ]; then
    print_result "Phase 3 metrics exporter exists" "PASS"
else
    print_result "Phase 3 metrics exporter exists" "FAIL" "File not found: ghl_real_estate_ai/services/monitoring/phase3_metrics_exporter.py"
fi

# Check impact tracker exists
if [ -f "scripts/monitoring/track_phase3_impact.py" ]; then
    print_result "Impact tracking script exists" "PASS"
else
    print_result "Impact tracking script exists" "FAIL" "File not found: scripts/monitoring/track_phase3_impact.py"
fi

# Check impact tracker is executable
if [ -x "scripts/monitoring/track_phase3_impact.py" ]; then
    print_result "Impact tracker is executable" "PASS"
else
    print_result "Impact tracker is executable" "WARN" "File exists but is not executable. Run: chmod +x scripts/monitoring/track_phase3_impact.py"
fi

# Check documentation exists
if [ -f "docs/PHASE_3_MONITORING_SETUP.md" ]; then
    print_result "Monitoring setup guide exists" "PASS"
else
    print_result "Monitoring setup guide exists" "WARN" "Documentation file missing"
fi

echo ""
echo "2. PROMETHEUS CONFIGURATION"
echo "------------------------------------------------------------"

# Check if prometheus.yml is updated with phase3_alerts.yml
if grep -q "phase3_alerts.yml" config/monitoring/prometheus.yml; then
    print_result "Prometheus includes Phase 3 alert rules" "PASS"
else
    print_result "Prometheus includes Phase 3 alert rules" "FAIL" "phase3_alerts.yml not in prometheus.yml rule_files"
fi

# Check if Phase 3 scrape job is configured
if grep -q "phase3-metrics" config/monitoring/prometheus.yml; then
    print_result "Prometheus configured to scrape Phase 3 metrics" "PASS"
else
    print_result "Prometheus configured to scrape Phase 3 metrics" "FAIL" "phase3-metrics job not found in prometheus.yml"
fi

# Validate prometheus.yml syntax if promtool is available
if command -v promtool &> /dev/null; then
    if promtool check config config/monitoring/prometheus.yml &> /dev/null; then
        print_result "Prometheus configuration is valid" "PASS"
    else
        print_result "Prometheus configuration is valid" "FAIL" "Run: promtool check config config/monitoring/prometheus.yml"
    fi
else
    print_result "Prometheus configuration validation" "WARN" "promtool not found, skipping syntax check"
fi

# Validate alert rules if promtool is available
if command -v promtool &> /dev/null; then
    if promtool check rules config/monitoring/phase3_alerts.yml &> /dev/null; then
        print_result "Phase 3 alert rules are valid" "PASS"
    else
        print_result "Phase 3 alert rules are valid" "FAIL" "Run: promtool check rules config/monitoring/phase3_alerts.yml"
    fi
else
    print_result "Phase 3 alert rules validation" "WARN" "promtool not found, skipping syntax check"
fi

echo ""
echo "3. ALERT RULES COVERAGE"
echo "------------------------------------------------------------"

# Count alert rules in phase3_alerts.yml
if [ -f "config/monitoring/phase3_alerts.yml" ]; then
    alert_count=$(grep -c "alert:" config/monitoring/phase3_alerts.yml || true)
    if [ "$alert_count" -ge 90 ]; then
        print_result "Alert coverage (${alert_count} alerts)" "PASS"
    elif [ "$alert_count" -ge 50 ]; then
        print_result "Alert coverage (${alert_count} alerts)" "WARN" "Expected 95+ alerts"
    else
        print_result "Alert coverage (${alert_count} alerts)" "FAIL" "Expected 95+ alerts"
    fi

    # Check for feature-specific alerts
    for feature in "realtime_intelligence" "property_intelligence" "churn_prevention" "ai_coaching"; do
        if grep -q "$feature" config/monitoring/phase3_alerts.yml; then
            print_result "Alerts for $feature" "PASS"
        else
            print_result "Alerts for $feature" "FAIL" "No alerts found for $feature"
        fi
    done
fi

echo ""
echo "4. PYTHON DEPENDENCIES"
echo "------------------------------------------------------------"

# Check for required Python packages
required_packages=("prometheus_client" "redis" "pandas")

for package in "${required_packages[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        print_result "Python package: $package" "PASS"
    else
        print_result "Python package: $package" "FAIL" "Run: pip install $package"
    fi
done

# Check for prometheus-api-client
if python3 -c "import prometheus_api_client" 2>/dev/null; then
    print_result "Python package: prometheus_api_client" "PASS"
else
    print_result "Python package: prometheus_api_client" "WARN" "Required for impact tracking. Run: pip install prometheus-api-client"
fi

echo ""
echo "5. SERVICE AVAILABILITY (if running)"
echo "------------------------------------------------------------"

# Check if Prometheus is running
if curl -s http://localhost:9090/-/healthy &> /dev/null; then
    print_result "Prometheus service is running" "PASS"
else
    print_result "Prometheus service is running" "WARN" "Not running or not accessible at localhost:9090"
fi

# Check if Grafana is running
if curl -s http://localhost:3000/api/health &> /dev/null; then
    print_result "Grafana service is running" "PASS"
else
    print_result "Grafana service is running" "WARN" "Not running or not accessible at localhost:3000"
fi

# Check if AlertManager is running
if curl -s http://localhost:9093/-/healthy &> /dev/null; then
    print_result "AlertManager service is running" "PASS"
else
    print_result "AlertManager service is running" "WARN" "Not running or not accessible at localhost:9093"
fi

# Check if Phase 3 metrics exporter is running
if curl -s http://localhost:8009/metrics &> /dev/null; then
    print_result "Phase 3 metrics exporter is running" "PASS"

    # Check if metrics are actually being exported
    if curl -s http://localhost:8009/metrics | grep -q "phase3_revenue_impact_dollars"; then
        print_result "Phase 3 metrics are being exported" "PASS"
    else
        print_result "Phase 3 metrics are being exported" "WARN" "Exporter running but no Phase 3 metrics found"
    fi
else
    print_result "Phase 3 metrics exporter is running" "WARN" "Not running or not accessible at localhost:8009"
fi

echo ""
echo "6. PROMETHEUS SCRAPING (if Prometheus is running)"
echo "------------------------------------------------------------"

if curl -s http://localhost:9090/-/healthy &> /dev/null; then
    # Check if Prometheus is scraping Phase 3 metrics
    if curl -s http://localhost:9090/api/v1/targets | grep -q "phase3-metrics"; then
        print_result "Prometheus scraping Phase 3 metrics" "PASS"

        # Check scrape status
        scrape_health=$(curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | select(.labels.job=="phase3-metrics") | .health' 2>/dev/null || echo "unknown")

        if [ "$scrape_health" == "up" ]; then
            print_result "Phase 3 metrics scrape status: $scrape_health" "PASS"
        else
            print_result "Phase 3 metrics scrape status: $scrape_health" "WARN" "Scrape target configured but not healthy"
        fi
    else
        print_result "Prometheus scraping Phase 3 metrics" "WARN" "phase3-metrics job not found in targets"
    fi

    # Check if alert rules are loaded
    alert_groups=$(curl -s http://localhost:9090/api/v1/rules | jq -r '.data.groups[] | select(.file | contains("phase3_alerts")) | .name' 2>/dev/null | wc -l)

    if [ "$alert_groups" -gt 0 ]; then
        print_result "Phase 3 alert rules loaded ($alert_groups groups)" "PASS"
    else
        print_result "Phase 3 alert rules loaded" "WARN" "No Phase 3 alert groups found. Reload Prometheus config."
    fi
fi

echo ""
echo "7. GRAFANA DASHBOARD (if Grafana is running)"
echo "------------------------------------------------------------"

if curl -s http://localhost:3000/api/health &> /dev/null; then
    # Note: Dashboard check requires authentication, so we'll just check if the file exists
    if [ -f "config/monitoring/grafana/dashboards/phase3_production_monitoring.json" ]; then
        print_result "Phase 3 dashboard file ready for import" "PASS"
        echo "  → Import at: http://localhost:3000/dashboard/import"
    fi
else
    print_result "Grafana dashboard deployment" "WARN" "Grafana not running, cannot verify dashboard deployment"
fi

echo ""
echo "8. REDIS CONNECTIVITY (if Redis is required)"
echo "------------------------------------------------------------"

# Check if Redis is accessible
if command -v redis-cli &> /dev/null; then
    if redis-cli -n 3 ping &> /dev/null; then
        print_result "Redis connectivity (database 3)" "PASS"
    else
        print_result "Redis connectivity (database 3)" "WARN" "Cannot connect to Redis database 3"
    fi
else
    print_result "Redis CLI available" "WARN" "redis-cli not found, cannot test connectivity"
fi

echo ""
echo "9. IMPACT TRACKING SCRIPT"
echo "------------------------------------------------------------"

# Test if impact tracking script can run
if python3 scripts/monitoring/track_phase3_impact.py --help &> /dev/null; then
    print_result "Impact tracking script is runnable" "PASS"
else
    print_result "Impact tracking script is runnable" "FAIL" "Script has errors. Check dependencies."
fi

echo ""
echo "================================================================================"
echo "  VALIDATION SUMMARY"
echo "================================================================================"
echo ""
echo -e "Passed:   ${GREEN}${PASSED}${NC}"
echo -e "Warnings: ${YELLOW}${WARNINGS}${NC}"
echo -e "Failed:   ${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical validations passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start monitoring stack:    python scripts/monitoring/manage_monitoring.py start"
    echo "2. Start metrics exporter:    python -m ghl_real_estate_ai.services.monitoring.phase3_metrics_exporter"
    echo "3. Deploy Grafana dashboard:  python scripts/monitoring/manage_monitoring.py deploy-dashboards"
    echo "4. Generate impact report:    python scripts/monitoring/track_phase3_impact.py --daily"
    echo ""
    exit 0
elif [ $WARNINGS -gt 0 ] && [ $FAILED -eq 0 ]; then
    echo -e "${YELLOW}⚠ Validation passed with warnings${NC}"
    echo ""
    echo "Review warnings above before production deployment."
    echo ""
    exit 0
else
    echo -e "${RED}✗ Validation failed${NC}"
    echo ""
    echo "Fix the errors above before proceeding."
    echo ""
    exit 1
fi
