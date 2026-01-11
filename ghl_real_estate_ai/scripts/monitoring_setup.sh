#!/bin/bash
# Enterprise Monitoring Stack Setup Script
# Deploys Prometheus, Grafana, and predictive alerting for EnterpriseHub Phase 4

set -e

echo "🚀 EnterpriseHub Enterprise Monitoring Stack Setup"
echo "=================================================="

# Configuration
MONITORING_DIR="/opt/enterprisehub/monitoring"
PROMETHEUS_VERSION="2.45.0"
GRAFANA_VERSION="10.1.0"
ALERTMANAGER_VERSION="0.26.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root or with sudo"
    exit 1
fi

# Step 1: Create monitoring directories
log_info "Creating monitoring directories..."
mkdir -p "$MONITORING_DIR"/{prometheus,grafana,alertmanager}/{data,config,dashboards,rules}
chmod -R 755 "$MONITORING_DIR"

# Step 2: Install Prometheus
log_info "Installing Prometheus v$PROMETHEUS_VERSION..."
if ! command -v prometheus &> /dev/null; then
    cd /tmp
    wget "https://github.com/prometheus/prometheus/releases/download/v${PROMETHEUS_VERSION}/prometheus-${PROMETHEUS_VERSION}.linux-amd64.tar.gz"
    tar xzf "prometheus-${PROMETHEUS_VERSION}.linux-amd64.tar.gz"
    cd "prometheus-${PROMETHEUS_VERSION}.linux-amd64"
    cp prometheus promtool /usr/local/bin/
    cp -r consoles console_libraries "$MONITORING_DIR/prometheus/"
    log_info "Prometheus installed successfully"
else
    log_info "Prometheus already installed"
fi

# Step 3: Install Grafana
log_info "Installing Grafana v$GRAFANA_VERSION..."
if ! command -v grafana-server &> /dev/null; then
    apt-get update
    apt-get install -y adduser libfontconfig1
    wget "https://dl.grafana.com/oss/release/grafana_${GRAFANA_VERSION}_amd64.deb"
    dpkg -i "grafana_${GRAFANA_VERSION}_amd64.deb"
    systemctl daemon-reload
    systemctl enable grafana-server
    log_info "Grafana installed successfully"
else
    log_info "Grafana already installed"
fi

# Step 4: Install Alertmanager
log_info "Installing Alertmanager v$ALERTMANAGER_VERSION..."
if ! command -v alertmanager &> /dev/null; then
    cd /tmp
    wget "https://github.com/prometheus/alertmanager/releases/download/v${ALERTMANAGER_VERSION}/alertmanager-${ALERTMANAGER_VERSION}.linux-amd64.tar.gz"
    tar xzf "alertmanager-${ALERTMANAGER_VERSION}.linux-amd64.tar.gz"
    cd "alertmanager-${ALERTMANAGER_VERSION}.linux-amd64"
    cp alertmanager amtool /usr/local/bin/
    log_info "Alertmanager installed successfully"
else
    log_info "Alertmanager already installed"
fi

# Step 5: Install exporters
log_info "Installing Prometheus exporters..."

# Node Exporter
if ! command -v node_exporter &> /dev/null; then
    NODE_EXPORTER_VERSION="1.6.1"
    cd /tmp
    wget "https://github.com/prometheus/node_exporter/releases/download/v${NODE_EXPORTER_VERSION}/node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz"
    tar xzf "node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64.tar.gz"
    cp "node_exporter-${NODE_EXPORTER_VERSION}.linux-amd64/node_exporter" /usr/local/bin/
    log_info "Node Exporter installed"
fi

# PostgreSQL Exporter
if ! command -v postgres_exporter &> /dev/null; then
    POSTGRES_EXPORTER_VERSION="0.13.2"
    cd /tmp
    wget "https://github.com/prometheus-community/postgres_exporter/releases/download/v${POSTGRES_EXPORTER_VERSION}/postgres_exporter-${POSTGRES_EXPORTER_VERSION}.linux-amd64.tar.gz"
    tar xzf "postgres_exporter-${POSTGRES_EXPORTER_VERSION}.linux-amd64.tar.gz"
    cp "postgres_exporter-${POSTGRES_EXPORTER_VERSION}.linux-amd64/postgres_exporter" /usr/local/bin/
    log_info "PostgreSQL Exporter installed"
fi

# Redis Exporter
if ! command -v redis_exporter &> /dev/null; then
    REDIS_EXPORTER_VERSION="1.52.0"
    cd /tmp
    wget "https://github.com/oliver006/redis_exporter/releases/download/v${REDIS_EXPORTER_VERSION}/redis_exporter-v${REDIS_EXPORTER_VERSION}.linux-amd64.tar.gz"
    tar xzf "redis_exporter-v${REDIS_EXPORTER_VERSION}.linux-amd64.tar.gz"
    cp "redis_exporter-v${REDIS_EXPORTER_VERSION}.linux-amd64/redis_exporter" /usr/local/bin/
    log_info "Redis Exporter installed"
fi

# Step 6: Copy configuration files
log_info "Copying configuration files..."
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Prometheus configuration
cp "$PROJECT_ROOT/infrastructure/prometheus_config.yml" "$MONITORING_DIR/prometheus/config/prometheus.yml"
cp "$PROJECT_ROOT/infrastructure/prometheus/alert_rules.yml" "$MONITORING_DIR/prometheus/rules/"

# Grafana dashboards
cp "$PROJECT_ROOT/infrastructure/grafana_dashboards/"*.json "$MONITORING_DIR/grafana/dashboards/"

log_info "Configuration files copied"

# Step 7: Create systemd service files
log_info "Creating systemd service files..."

# Prometheus service
cat > /etc/systemd/system/prometheus.service <<EOF
[Unit]
Description=Prometheus Monitoring System
Documentation=https://prometheus.io/docs/introduction/overview/
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/bin/prometheus \\
  --config.file=$MONITORING_DIR/prometheus/config/prometheus.yml \\
  --storage.tsdb.path=$MONITORING_DIR/prometheus/data \\
  --storage.tsdb.retention.time=90d \\
  --storage.tsdb.retention.size=50GB \\
  --web.console.templates=$MONITORING_DIR/prometheus/consoles \\
  --web.console.libraries=$MONITORING_DIR/prometheus/console_libraries \\
  --web.enable-lifecycle

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Node Exporter service
cat > /etc/systemd/system/node_exporter.service <<EOF
[Unit]
Description=Prometheus Node Exporter
After=network.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/bin/node_exporter \\
  --collector.filesystem.mount-points-exclude='^/(sys|proc|dev|host|etc)($$|/)' \\
  --collector.netclass.ignored-devices='^(veth.*|docker.*|br-.*)$$'

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Alertmanager service
cat > /etc/systemd/system/alertmanager.service <<EOF
[Unit]
Description=Prometheus Alertmanager
After=network-online.target

[Service]
Type=simple
User=prometheus
Group=prometheus
ExecStart=/usr/local/bin/alertmanager \\
  --config.file=$MONITORING_DIR/alertmanager/config/alertmanager.yml \\
  --storage.path=$MONITORING_DIR/alertmanager/data

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create prometheus user
if ! id -u prometheus > /dev/null 2>&1; then
    useradd --no-create-home --shell /bin/false prometheus
fi

chown -R prometheus:prometheus "$MONITORING_DIR"

# Step 8: Configure Alertmanager
log_info "Configuring Alertmanager..."
cat > "$MONITORING_DIR/alertmanager/config/alertmanager.yml" <<EOF
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true
    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://localhost:8000/alerts/webhook'

  - name: 'slack'
    slack_configs:
      - api_url: '\${SLACK_WEBHOOK_URL}'
        channel: '#alerts'
        title: 'EnterpriseHub Alert'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '\${PAGERDUTY_SERVICE_KEY}'
        description: '{{ .CommonAnnotations.summary }}'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'service']
EOF

# Step 9: Install Python dependencies for predictive alerting
log_info "Installing Python dependencies for ML-based alerting..."
pip3 install prometheus_client scikit-learn scipy statsmodels psutil numpy pandas

# Step 10: Start services
log_info "Starting monitoring services..."
systemctl daemon-reload

systemctl enable prometheus
systemctl start prometheus
log_info "Prometheus started on port 9090"

systemctl enable node_exporter
systemctl start node_exporter
log_info "Node Exporter started on port 9100"

systemctl enable alertmanager
systemctl start alertmanager
log_info "Alertmanager started on port 9093"

systemctl start grafana-server
log_info "Grafana started on port 3000"

# Step 11: Configure Grafana
log_info "Configuring Grafana..."
sleep 5  # Wait for Grafana to start

# Add Prometheus data source
GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="admin"

curl -X POST -H "Content-Type: application/json" -d '{
  "name": "Prometheus",
  "type": "prometheus",
  "url": "http://localhost:9090",
  "access": "proxy",
  "isDefault": true
}' "$GRAFANA_URL/api/datasources" -u "$GRAFANA_USER:$GRAFANA_PASSWORD" || log_warn "Grafana datasource may already exist"

# Import dashboards
for dashboard_file in "$MONITORING_DIR/grafana/dashboards/"*.json; do
    log_info "Importing dashboard: $(basename $dashboard_file)"
    curl -X POST -H "Content-Type: application/json" \
        -d @"$dashboard_file" \
        "$GRAFANA_URL/api/dashboards/db" \
        -u "$GRAFANA_USER:$GRAFANA_PASSWORD" || log_warn "Dashboard import may have failed"
done

# Step 12: Verification
log_info "Verifying installation..."
sleep 3

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    log_info "✅ Prometheus is healthy"
else
    log_error "❌ Prometheus health check failed"
fi

# Check Grafana
if curl -s http://localhost:3000/api/health > /dev/null; then
    log_info "✅ Grafana is healthy"
else
    log_error "❌ Grafana health check failed"
fi

# Check Node Exporter
if curl -s http://localhost:9100/metrics > /dev/null; then
    log_info "✅ Node Exporter is healthy"
else
    log_error "❌ Node Exporter health check failed"
fi

# Step 13: Display access information
echo ""
echo "========================================"
echo "✅ Enterprise Monitoring Stack Installed"
echo "========================================"
echo ""
echo "Access URLs:"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana:    http://localhost:3000 (admin/admin)"
echo "  Alertmanager: http://localhost:9093"
echo ""
echo "Metrics Endpoints:"
echo "  Node Exporter: http://localhost:9100/metrics"
echo ""
echo "Configuration:"
echo "  Prometheus Config: $MONITORING_DIR/prometheus/config/prometheus.yml"
echo "  Alert Rules: $MONITORING_DIR/prometheus/rules/alert_rules.yml"
echo "  Grafana Dashboards: $MONITORING_DIR/grafana/dashboards/"
echo ""
echo "Next Steps:"
echo "  1. Change Grafana admin password"
echo "  2. Configure Slack webhook URL in alertmanager config"
echo "  3. Configure PagerDuty service key"
echo "  4. Start EnterpriseHub services with metrics endpoints"
echo "  5. Run: python3 $PROJECT_ROOT/infrastructure/enterprise_monitoring.py"
echo ""
echo "For predictive alerting, run:"
echo "  python3 $PROJECT_ROOT/services/predictive_alerting_engine.py"
echo ""

log_info "Setup complete!"
