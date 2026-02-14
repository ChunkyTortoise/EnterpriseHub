#!/bin/bash

# AgentForge Gumroad ZIP Packaging Script
# Creates 3 ZIP files for Gumroad upload
# Usage: bash content/gumroad/package-zips.sh

set -e  # Exit on error

echo "🚀 AgentForge Gumroad ZIP Packaging Script"
echo "=========================================="
echo ""

# Check if ai-orchestrator repo exists
if [ ! -d "../ai-orchestrator" ]; then
    echo "❌ ERROR: ai-orchestrator repo not found at ../ai-orchestrator"
    echo "Expected location: /Users/cave/Documents/GitHub/ai-orchestrator"
    echo ""
    echo "Please ensure ai-orchestrator repo is cloned:"
    echo "  cd /Users/cave/Documents/GitHub"
    echo "  git clone https://github.com/ChunkyTortoise/ai-orchestrator.git"
    exit 1
fi

# Create output directory
OUTPUT_DIR="content/gumroad/zips"
mkdir -p "$OUTPUT_DIR"

echo "✅ Found ai-orchestrator repo"
echo "📁 Output directory: $OUTPUT_DIR"
echo ""

# Get current timestamp for versioning
TIMESTAMP=$(date +%Y%m%d)

# ========================================
# STARTER ZIP
# ========================================

echo "📦 Packaging STARTER tier..."
STARTER_ZIP="$OUTPUT_DIR/agentforge-starter-v1.0-$TIMESTAMP.zip"

cd ../ai-orchestrator

zip -r "../EnterpriseHub/$STARTER_ZIP" \
    README.md \
    LICENSE \
    requirements.txt \
    pyproject.toml \
    Dockerfile \
    docker-compose.yml \
    agentforge/ \
    app.py \
    client.py \
    subagent.py \
    streamlit_app.py \
    services/ \
    utils/ \
    tests/ \
    examples/basic_usage.py \
    examples/multi_provider.py \
    examples/fallback_routing.py \
    examples/streaming.py \
    benchmarks/ \
    Makefile \
    pytest.ini \
    .env.example \
    .gitignore \
    docs/ \
    -x "*.pyc" \
    -x "*/__pycache__/*" \
    -x "*/__pycache__" \
    -x ".git/*" \
    -x ".pytest_cache/*" \
    -x ".mypy_cache/*" \
    -x ".ruff_cache/*" \
    -x "*.egg-info/*"

cd ../EnterpriseHub

echo "✅ Starter ZIP created: $STARTER_ZIP"
echo ""

# ========================================
# PRO ZIP
# ========================================

echo "📦 Packaging PRO tier..."
PRO_ZIP="$OUTPUT_DIR/agentforge-pro-v1.0-$TIMESTAMP.zip"

# Start with Starter ZIP contents
cp "$STARTER_ZIP" "$PRO_ZIP"

# Create temp directory for additional files
TEMP_DIR=$(mktemp -d)

# Copy supporting files
cp content/gumroad/supporting-files/CONSULTATION_BOOKING.txt "$TEMP_DIR/"
cp content/gumroad/supporting-files/PRIORITY_SUPPORT.txt "$TEMP_DIR/"

# Create case-studies directory (placeholder for now)
mkdir -p "$TEMP_DIR/case-studies"
cat > "$TEMP_DIR/case-studies/README.md" << 'EOF'
# AgentForge Pro - Case Studies

## Included Case Studies

### 1. LegalTech Startup: 70% Cost Reduction
**Coming Soon**: Full implementation code showing how to reduce LLM costs from $18.5K to $6.2K/month

**Preview**:
- Provider routing by task type
- 3-tier caching strategy
- Structured output optimization

### 2. Healthcare Platform: HIPAA-Compliant Routing
**Coming Soon**: Production-ready code for HIPAA-compliant multi-provider routing

**Preview**:
- PHI routing to certified providers
- Automatic failover without data exposure
- Audit trail implementation

### 3. Fintech Fraud Detection: 5-Agent Consensus
**Coming Soon**: Multi-agent orchestration with consensus voting

**Preview**:
- Parallel execution (sub-100ms)
- Cost-aware routing escalation
- Confidence score aggregation

**Note**: Full case studies with working code will be delivered within 7 days of purchase.
Contact caymanroden@gmail.com if not received.
EOF

# Create ci-cd directory (placeholder)
mkdir -p "$TEMP_DIR/ci-cd"
cat > "$TEMP_DIR/ci-cd/README.md" << 'EOF'
# CI/CD Templates

## Included Templates

### 1. GitHub Actions Workflow
**Coming Soon**: Production-ready GitHub Actions workflow

**Will Include**:
- Automated testing on push/PR
- Multi-Python version matrix
- Code quality checks (ruff, mypy, black)
- Docker build and push
- Deployment automation

### 2. Docker Deployment Guide
**Coming Soon**: Best practices for containerized deployment

### 3. Environment Configuration
**Coming Soon**: Secure secrets management examples

**Note**: Full CI/CD templates will be delivered within 7 days of purchase.
Contact caymanroden@gmail.com if not received.
EOF

# Add to Pro ZIP
SCRIPT_DIR="$(pwd)"
cd "$TEMP_DIR"
zip -r "$SCRIPT_DIR/$PRO_ZIP" \
    CONSULTATION_BOOKING.txt \
    PRIORITY_SUPPORT.txt \
    case-studies/ \
    ci-cd/

cd "$SCRIPT_DIR"
rm -rf "$TEMP_DIR"

echo "✅ Pro ZIP created: $PRO_ZIP"
echo ""

# ========================================
# ENTERPRISE ZIP
# ========================================

echo "📦 Packaging ENTERPRISE tier..."
ENTERPRISE_ZIP="$OUTPUT_DIR/agentforge-enterprise-v1.0-$TIMESTAMP.zip"

# Start with Pro ZIP contents
cp "$PRO_ZIP" "$ENTERPRISE_ZIP"

# Create temp directory for Enterprise files
TEMP_DIR=$(mktemp -d)

# Copy Enterprise supporting files
cp content/gumroad/supporting-files/ENTERPRISE_KICKOFF.txt "$TEMP_DIR/"
cp content/gumroad/supporting-files/CUSTOM_EXAMPLES_FORM.txt "$TEMP_DIR/"
cp content/gumroad/supporting-files/WHITE_LABEL_LICENSE.txt "$TEMP_DIR/"

# Create enterprise directory (placeholder)
mkdir -p "$TEMP_DIR/enterprise"
cat > "$TEMP_DIR/enterprise/README.md" << 'EOF'
# AgentForge Enterprise - Premium Documentation

## Included Documentation

### 1. Security Hardening Checklist
**Coming Soon**: Production security best practices

### 2. Compliance Documentation
**Coming Soon**: HIPAA, SOC2, GDPR implementation guides

### 3. Multi-Tenant Architecture Patterns
**Coming Soon**: Architecture patterns for multi-tenant deployments

### 4. High-Availability Deployment Guide
**Coming Soon**: HA/DR setup for production

### 5. Monitoring & Observability Setup
**Coming Soon**: Logging, metrics, tracing configuration

**Note**: Full premium documentation will be delivered within 7 days of purchase.
Contact caymanroden@gmail.com if not received.
EOF

# Create Slack invite placeholder
cat > "$TEMP_DIR/SLACK_INVITE.txt" << 'EOF'
# AgentForge Enterprise - Slack Channel Invite

Your private Slack channel will be created within 24 hours of purchase.

## What to Expect

You will receive an email at your Gumroad purchase email with:
- Slack workspace invite link
- Your private channel name: #agentforge-enterprise-[your-name]
- Instructions to get started

## Response SLA

- **Response Time**: 4 hours (business hours, 9am-5pm PST, Mon-Fri)
- **Duration**: 90 days from purchase
- **Extension**: $400/month after 90 days (optional)

## If You Don't Receive Invite

Email: caymanroden@gmail.com
Subject: "Enterprise Slack Invite - [Your Name]"

Include:
- Gumroad order number
- Preferred Slack email address

We'll get you set up within 4 hours!
EOF

# Create team training placeholder
cat > "$TEMP_DIR/TEAM_TRAINING.txt" << 'EOF'
# AgentForge Enterprise - Team Training Session

## Book Your Team Training

**Duration**: 1 hour
**Attendees**: Up to 10 people
**Format**: Live Zoom/Google Meet + Recording

**Booking Link**: https://calendly.com/caymanroden/agentforge-team-training

## What We'll Cover

1. **AgentForge Overview** (15 min)
   - Architecture walkthrough
   - Provider comparison
   - Core features demo

2. **Best Practices** (20 min)
   - Production deployment checklist
   - Cost optimization strategies
   - Error handling patterns
   - Monitoring & observability

3. **Live Q&A** (20 min)
   - Team asks questions
   - Domain-specific guidance

4. **Next Steps** (5 min)
   - Action items
   - Resource links

## Scheduling

Book within 30 days of purchase for best availability.

Questions? Email caymanroden@gmail.com
EOF

# Add to Enterprise ZIP
SCRIPT_DIR="$(pwd)"
cd "$TEMP_DIR"
zip -r "$SCRIPT_DIR/$ENTERPRISE_ZIP" \
    ENTERPRISE_KICKOFF.txt \
    CUSTOM_EXAMPLES_FORM.txt \
    WHITE_LABEL_LICENSE.txt \
    SLACK_INVITE.txt \
    TEAM_TRAINING.txt \
    enterprise/

cd "$SCRIPT_DIR"
rm -rf "$TEMP_DIR"

echo "✅ Enterprise ZIP created: $ENTERPRISE_ZIP"
echo ""

# ========================================
# SUMMARY
# ========================================

echo "=========================================="
echo "✅ All ZIPs created successfully!"
echo "=========================================="
echo ""
echo "📦 STARTER:    $STARTER_ZIP"
echo "   Size: $(du -h "$STARTER_ZIP" | cut -f1)"
echo ""
echo "📦 PRO:        $PRO_ZIP"
echo "   Size: $(du -h "$PRO_ZIP" | cut -f1)"
echo ""
echo "📦 ENTERPRISE: $ENTERPRISE_ZIP"
echo "   Size: $(du -h "$ENTERPRISE_ZIP" | cut -f1)"
echo ""
echo "=========================================="
echo "📋 Next Steps:"
echo "=========================================="
echo ""
echo "1. Review ZIPs to ensure contents are correct:"
echo "   unzip -l $STARTER_ZIP | less"
echo ""
echo "2. Upload to Gumroad following checklist:"
echo "   cat content/gumroad/GUMROAD-UPLOAD-CHECKLIST.md"
echo ""
echo "3. Test download after upload"
echo ""
echo "4. Launch on social media (LinkedIn + Twitter)"
echo ""
echo "🎯 Expected Revenue: \$3,483-\$5,324/month (11x current)"
echo ""
