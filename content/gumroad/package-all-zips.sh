#!/bin/bash

# Unified Gumroad ZIP Packaging Script
# Creates 3-tier ZIPs (Starter/Pro/Enterprise) for ALL 7 products
# Usage: bash content/gumroad/package-all-zips.sh
#   or:  bash content/gumroad/package-all-zips.sh docqa agentforge  (specific products)

set -e

GITHUB_DIR="/Users/cave/Documents/GitHub"
ENTERPRISE_HUB="$GITHUB_DIR/EnterpriseHub"
OUTPUT_DIR="$ENTERPRISE_HUB/content/gumroad/zips"
SUPPORT_DIR="$ENTERPRISE_HUB/content/gumroad/supporting-files"
TIMESTAMP=$(date +%Y%m%d)

# Common excludes for all ZIPs
EXCLUDES=(
    -x "*.pyc"
    -x "*/__pycache__/*"
    -x "*/__pycache__"
    -x ".git/*"
    -x ".git"
    -x ".pytest_cache/*"
    -x ".mypy_cache/*"
    -x ".ruff_cache/*"
    -x "*.egg-info/*"
    -x "*.egg-info"
    -x "dist/*"
    -x "dist"
)

mkdir -p "$OUTPUT_DIR"

echo "=========================================="
echo "  Gumroad ZIP Packaging - All Products"
echo "=========================================="
echo ""
echo "Output: $OUTPUT_DIR"
echo "Date:   $TIMESTAMP"
echo ""

# Track results for summary
declare -a BUILT_ZIPS
ERRORS=0

# ──────────────────────────────────────────────
# Helper: Add Pro-tier files to a ZIP
# ──────────────────────────────────────────────
add_pro_files() {
    local zip_path="$1"
    local product_name="$2"

    local temp_dir
    temp_dir=$(mktemp -d)

    # Supporting files
    cp "$SUPPORT_DIR/CONSULTATION_BOOKING.txt" "$temp_dir/"
    cp "$SUPPORT_DIR/PRIORITY_SUPPORT.txt" "$temp_dir/"

    # Case studies placeholder
    mkdir -p "$temp_dir/case-studies"
    cat > "$temp_dir/case-studies/README.md" << EOF
# ${product_name} Pro - Case Studies

Case studies with production-ready code will be delivered within 7 days of purchase.

Contact caymanroden@gmail.com if not received.
EOF

    # CI/CD placeholder
    mkdir -p "$temp_dir/ci-cd"
    cat > "$temp_dir/ci-cd/README.md" << EOF
# ${product_name} Pro - CI/CD Templates

CI/CD templates (GitHub Actions, Docker deployment, secrets management)
will be delivered within 7 days of purchase.

Contact caymanroden@gmail.com if not received.
EOF

    cd "$temp_dir"
    zip -r "$zip_path" \
        CONSULTATION_BOOKING.txt \
        PRIORITY_SUPPORT.txt \
        case-studies/ \
        ci-cd/
    cd "$ENTERPRISE_HUB"
    rm -rf "$temp_dir"
}

# ──────────────────────────────────────────────
# Helper: Add Enterprise-tier files to a ZIP
# ──────────────────────────────────────────────
add_enterprise_files() {
    local zip_path="$1"
    local product_name="$2"

    local temp_dir
    temp_dir=$(mktemp -d)

    # Supporting files from disk
    cp "$SUPPORT_DIR/ENTERPRISE_KICKOFF.txt" "$temp_dir/"
    cp "$SUPPORT_DIR/CUSTOM_EXAMPLES_FORM.txt" "$temp_dir/"
    cp "$SUPPORT_DIR/WHITE_LABEL_LICENSE.txt" "$temp_dir/"

    # Enterprise docs placeholder
    mkdir -p "$temp_dir/enterprise"
    cat > "$temp_dir/enterprise/README.md" << EOF
# ${product_name} Enterprise - Premium Documentation

Includes:
- Security hardening checklist
- Compliance guides (HIPAA, SOC2, GDPR)
- Multi-tenant architecture patterns
- High-availability deployment guide
- Monitoring and observability setup

Full documentation will be delivered within 7 days of purchase.
Contact caymanroden@gmail.com if not received.
EOF

    # Slack invite
    cat > "$temp_dir/SLACK_INVITE.txt" << EOF
# ${product_name} Enterprise - Slack Channel Invite

Your private Slack channel will be created within 24 hours of purchase.

## What to Expect

You will receive an email at your Gumroad purchase email with:
- Slack workspace invite link
- Your private channel name
- Instructions to get started

## Response SLA

- Response Time: 4 hours (business hours, 9am-5pm PST, Mon-Fri)
- Duration: 90 days from purchase
- Extension: \$400/month after 90 days (optional)

## If You Don't Receive Invite

Email: caymanroden@gmail.com
Subject: "Enterprise Slack Invite - [Your Name]"
Include your Gumroad order number.
EOF

    # Team training
    cat > "$temp_dir/TEAM_TRAINING.txt" << EOF
# ${product_name} Enterprise - Team Training Session

Duration: 1 hour | Attendees: Up to 10 | Format: Live Zoom + Recording

Booking Link: https://calendly.com/caymanroden/team-training

## Agenda

1. Architecture walkthrough (15 min)
2. Best practices and production patterns (20 min)
3. Live Q&A (20 min)
4. Next steps and action items (5 min)

Book within 30 days of purchase for best availability.
Questions? Email caymanroden@gmail.com
EOF

    cd "$temp_dir"
    zip -r "$zip_path" \
        ENTERPRISE_KICKOFF.txt \
        CUSTOM_EXAMPLES_FORM.txt \
        WHITE_LABEL_LICENSE.txt \
        SLACK_INVITE.txt \
        TEAM_TRAINING.txt \
        enterprise/
    cd "$ENTERPRISE_HUB"
    rm -rf "$temp_dir"
}

# ──────────────────────────────────────────────
# Helper: Build all 3 tiers for a product
# ──────────────────────────────────────────────
build_product() {
    local product_slug="$1"    # e.g. "docqa"
    local product_name="$2"    # e.g. "DocQA"
    local repo_dir="$3"        # e.g. "/Users/cave/Documents/GitHub/docqa-engine"
    shift 3
    local files=("$@")         # files/dirs to include in Starter

    echo "──────────────────────────────────────────"
    echo "  ${product_name}"
    echo "──────────────────────────────────────────"

    if [ ! -d "$repo_dir" ]; then
        echo "  ERROR: Repo not found at $repo_dir - SKIPPING"
        echo ""
        ERRORS=$((ERRORS + 1))
        return
    fi

    local starter_zip="$OUTPUT_DIR/${product_slug}-starter-v1.0-${TIMESTAMP}.zip"
    local pro_zip="$OUTPUT_DIR/${product_slug}-pro-v1.0-${TIMESTAMP}.zip"
    local enterprise_zip="$OUTPUT_DIR/${product_slug}-enterprise-v1.0-${TIMESTAMP}.zip"

    # Remove old ZIPs for this product (idempotent)
    rm -f "$OUTPUT_DIR/${product_slug}-starter-v1.0-"*.zip
    rm -f "$OUTPUT_DIR/${product_slug}-pro-v1.0-"*.zip
    rm -f "$OUTPUT_DIR/${product_slug}-enterprise-v1.0-"*.zip

    # --- STARTER ---
    echo "  Packaging Starter..."
    cd "$repo_dir"

    # Build file list: only include files that actually exist
    local include_files=()
    for f in "${files[@]}"; do
        if [ -e "$f" ]; then
            include_files+=("$f")
        fi
    done

    zip -r "$starter_zip" "${include_files[@]}" "${EXCLUDES[@]}" -q
    cd "$ENTERPRISE_HUB"
    echo "  -> $(du -h "$starter_zip" | cut -f1)  $starter_zip"
    BUILT_ZIPS+=("$starter_zip")

    # --- PRO ---
    echo "  Packaging Pro..."
    cp "$starter_zip" "$pro_zip"
    add_pro_files "$pro_zip" "$product_name"
    echo "  -> $(du -h "$pro_zip" | cut -f1)  $pro_zip"
    BUILT_ZIPS+=("$pro_zip")

    # --- ENTERPRISE ---
    echo "  Packaging Enterprise..."
    cp "$pro_zip" "$enterprise_zip"
    add_enterprise_files "$enterprise_zip" "$product_name"
    echo "  -> $(du -h "$enterprise_zip" | cut -f1)  $enterprise_zip"
    BUILT_ZIPS+=("$enterprise_zip")

    echo ""
}

# ══════════════════════════════════════════════
# PRODUCT DEFINITIONS
# ══════════════════════════════════════════════

build_docqa() {
    build_product "docqa" "DocQA Engine" "$GITHUB_DIR/docqa-engine" \
        README.md LICENSE requirements.txt requirements-dev.txt \
        pyproject.toml Dockerfile docker-compose.yml Makefile .gitignore \
        app.py \
        docqa_engine/ \
        tests/ \
        docs/ \
        demo_data/ demo_docs/ \
        scripts/ \
        benchmarks/ \
        assets/ \
        BENCHMARKS.md CHANGELOG.md CONTRIBUTING.md CUSTOMIZATION.md \
        DEMO_MODE.md SECURITY.md CODE_OF_CONDUCT.md \
        CASE_STUDY_Document_Intelligence_Legal.md
}

build_insight() {
    build_product "insight" "Insight Engine" "$GITHUB_DIR/insight-engine" \
        README.md LICENSE requirements.txt requirements-dev.txt \
        pyproject.toml Dockerfile docker-compose.yml Makefile .gitignore \
        app.py \
        insight_engine/ \
        tests/ \
        docs/ \
        demo_data/ \
        scripts/ \
        benchmarks/ \
        assets/ \
        BENCHMARKS.md CHANGELOG.md CONTRIBUTING.md SECURITY.md CODE_OF_CONDUCT.md \
        CASE_STUDY_Marketing_Analytics_Attribution.md
}

build_scraper() {
    build_product "scraper" "Scrape & Serve" "$GITHUB_DIR/scrape-and-serve" \
        README.md LICENSE requirements.txt requirements-dev.txt \
        pyproject.toml Dockerfile docker-compose.yml Makefile .gitignore \
        app.py \
        scrape_and_serve/ \
        tests/ \
        docs/ \
        demo_data/ \
        benchmarks/ \
        assets/ \
        BENCHMARKS.md CHANGELOG.md CONTRIBUTING.md CUSTOMIZATION.md \
        DEMO_MODE.md SECURITY.md CODE_OF_CONDUCT.md
}

build_prompt_toolkit() {
    build_product "prompt-toolkit" "Prompt Engineering Toolkit" "$GITHUB_DIR/prompt-engineering-lab" \
        README.md LICENSE requirements.txt requirements-dev.txt \
        pyproject.toml Dockerfile docker-compose.yml Makefile .gitignore \
        app.py \
        prompt_engineering_lab/ \
        prompt_lab/ \
        tests/ \
        docs/ \
        demo_data/ \
        benchmarks/ \
        BENCHMARKS.md CHANGELOG.md CONTRIBUTING.md DEPLOY.md \
        SECURITY.md CODE_OF_CONDUCT.md
}

build_llm_starter() {
    build_product "llm-starter" "LLM Integration Starter" "$GITHUB_DIR/llm-integration-starter" \
        README.md LICENSE requirements.txt requirements-dev.txt \
        pyproject.toml Dockerfile docker-compose.yml Makefile .gitignore \
        app.py \
        llm_integration_starter/ \
        llm_starter/ \
        tests/ \
        docs/ \
        demo_data/ \
        benchmarks/ \
        BENCHMARKS.md CHANGELOG.md CONTRIBUTING.md CUSTOMIZATION.md \
        DEMO_MODE.md DEPLOY.md SECURITY.md CODE_OF_CONDUCT.md
}

build_dashboard() {
    # Dashboard Templates: subset of insight-engine focused on visualization
    local repo_dir="$GITHUB_DIR/insight-engine"

    echo "──────────────────────────────────────────"
    echo "  Dashboard Templates"
    echo "──────────────────────────────────────────"

    if [ ! -d "$repo_dir" ]; then
        echo "  ERROR: Repo not found at $repo_dir - SKIPPING"
        echo ""
        ERRORS=$((ERRORS + 1))
        return
    fi

    local starter_zip="$OUTPUT_DIR/dashboard-starter-v1.0-${TIMESTAMP}.zip"
    local pro_zip="$OUTPUT_DIR/dashboard-pro-v1.0-${TIMESTAMP}.zip"
    local enterprise_zip="$OUTPUT_DIR/dashboard-enterprise-v1.0-${TIMESTAMP}.zip"

    rm -f "$OUTPUT_DIR/dashboard-starter-v1.0-"*.zip
    rm -f "$OUTPUT_DIR/dashboard-pro-v1.0-"*.zip
    rm -f "$OUTPUT_DIR/dashboard-enterprise-v1.0-"*.zip

    # Starter: dashboard-relevant subset
    echo "  Packaging Starter..."
    cd "$repo_dir"

    local include_files=()
    for f in \
        README.md LICENSE requirements.txt pyproject.toml \
        Dockerfile docker-compose.yml Makefile .gitignore \
        app.py \
        insight_engine/__init__.py \
        insight_engine/dashboard_generator.py \
        insight_engine/forecaster.py \
        insight_engine/anomaly_detector.py \
        insight_engine/advanced_anomaly.py \
        insight_engine/profiler.py \
        insight_engine/kpi_framework.py \
        insight_engine/report_generator.py \
        insight_engine/clustering.py \
        insight_engine/statistical_tests.py \
        insight_engine/data_quality.py \
        insight_engine/api/ \
        insight_engine/connectors/ \
        tests/ \
        docs/ \
        demo_data/ \
        assets/ \
        BENCHMARKS.md CHANGELOG.md CONTRIBUTING.md \
        CASE_STUDY_Marketing_Analytics_Attribution.md; do
        if [ -e "$f" ]; then
            include_files+=("$f")
        fi
    done

    zip -r "$starter_zip" "${include_files[@]}" "${EXCLUDES[@]}" -q
    cd "$ENTERPRISE_HUB"
    echo "  -> $(du -h "$starter_zip" | cut -f1)  $starter_zip"
    BUILT_ZIPS+=("$starter_zip")

    # Pro
    echo "  Packaging Pro..."
    cp "$starter_zip" "$pro_zip"
    add_pro_files "$pro_zip" "Dashboard Templates"
    echo "  -> $(du -h "$pro_zip" | cut -f1)  $pro_zip"
    BUILT_ZIPS+=("$pro_zip")

    # Enterprise
    echo "  Packaging Enterprise..."
    cp "$pro_zip" "$enterprise_zip"
    add_enterprise_files "$enterprise_zip" "Dashboard Templates"
    echo "  -> $(du -h "$enterprise_zip" | cut -f1)  $enterprise_zip"
    BUILT_ZIPS+=("$enterprise_zip")

    echo ""
}

build_agentforge() {
    build_product "agentforge" "AgentForge" "$GITHUB_DIR/ai-orchestrator" \
        README.md LICENSE requirements.txt \
        pyproject.toml Dockerfile docker-compose.yml Makefile .gitignore \
        pytest.ini .env.example \
        app.py client.py subagent.py streamlit_app.py \
        agentforge/ \
        services/ \
        utils/ \
        tests/ \
        examples/ \
        docs/ \
        benchmarks/
}

# ══════════════════════════════════════════════
# MAIN: Build requested products or all
# ══════════════════════════════════════════════

ALL_PRODUCTS="docqa insight scraper prompt-toolkit llm-starter dashboard agentforge"

if [ $# -eq 0 ]; then
    PRODUCTS="$ALL_PRODUCTS"
else
    PRODUCTS="$*"
fi

for product in $PRODUCTS; do
    case "$product" in
        docqa)          build_docqa ;;
        insight)        build_insight ;;
        scraper)        build_scraper ;;
        prompt-toolkit) build_prompt_toolkit ;;
        llm-starter)    build_llm_starter ;;
        dashboard)      build_dashboard ;;
        agentforge)     build_agentforge ;;
        *)
            echo "Unknown product: $product"
            echo "Available: $ALL_PRODUCTS"
            ERRORS=$((ERRORS + 1))
            ;;
    esac
done

# ══════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════

echo "=========================================="
echo "  SUMMARY"
echo "=========================================="
echo ""
echo "  ZIPs built: ${#BUILT_ZIPS[@]}"
echo "  Errors:     $ERRORS"
echo ""

if [ ${#BUILT_ZIPS[@]} -gt 0 ]; then
    echo "  Product                Tier        Size"
    echo "  ───────────────────────────────────────────"
    for z in "${BUILT_ZIPS[@]}"; do
        fname=$(basename "$z")
        size=$(du -h "$z" | cut -f1)
        printf "  %-40s %s\n" "$fname" "$size"
    done
    echo ""
    total_size=$(du -sh "$OUTPUT_DIR" | cut -f1)
    echo "  Total output size: $total_size"
fi

echo ""
echo "=========================================="
echo "  Next Steps"
echo "=========================================="
echo ""
echo "  1. Inspect a ZIP:  unzip -l content/gumroad/zips/<file>.zip"
echo "  2. Upload to Gumroad per product listing"
echo "  3. Test download after upload"
echo ""

exit $ERRORS
