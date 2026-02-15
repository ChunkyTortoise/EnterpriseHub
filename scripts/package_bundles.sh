#!/bin/bash

# Script to package Gumroad bundles from existing individual product ZIPs
# Usage: bash scripts/package_bundles.sh

set -e

GITHUB_DIR="/Users/cave/Documents/GitHub"
ENTERPRISE_HUB="$GITHUB_DIR/EnterpriseHub"
ZIPS_DIR="$ENTERPRISE_HUB/content/gumroad/zips"
TIMESTAMP=$(date +%Y%m%d)

echo "=========================================="
echo "  Gumroad Bundle Packaging"
echo "=========================================="

mkdir -p "$ZIPS_DIR"

package_bundle() {
    local bundle_name="$1"
    local bundle_slug="$2"
    shift 2
    local source_zips=("$@")

    echo "Packaging $bundle_name..."
    
    local temp_dir
    temp_dir=$(mktemp -d)
    
    for zip_file in "${source_zips[@]}"; do
        # Find the latest zip file matching the pattern
        local latest_zip=$(ls -t "$ZIPS_DIR/${zip_file}-v1.0-"*.zip | head -n 1)
        if [ -f "$latest_zip" ]; then
            echo "  Adding $(basename "$latest_zip")..."
            mkdir -p "$temp_dir/${zip_file}"
            unzip -q "$latest_zip" -d "$temp_dir/${zip_file}"
        else
            echo "  WARNING: No ZIP found for ${zip_file} - SKIPPING"
        fi
    done

    local output_zip="$ZIPS_DIR/${bundle_slug}-v1.0-${TIMESTAMP}.zip"
    cd "$temp_dir"
    zip -r "$output_zip" . -q
    cd "$ENTERPRISE_HUB"
    
    echo "  -> $(du -h "$output_zip" | cut -f1)  $output_zip"
    rm -rf "$temp_dir"
}

# 1. All Starters Bundle
package_bundle "All Starters Bundle" "all-starters-bundle" \
    "agentforge-starter" "docqa-starter" "scraper-starter" "insight-starter"

# 2. All Pro Bundle
package_bundle "All Pro Bundle" "all-pro-bundle" \
    "agentforge-pro" "docqa-pro" "scraper-pro" "insight-pro"

# 3. Revenue-Sprint Bundle
package_bundle "Revenue-Sprint Bundle" "revenue-sprint-bundle" \
    "prompt-toolkit-starter" "llm-starter-starter" "dashboard-starter"

echo ""
echo "Done! All bundles packaged in $ZIPS_DIR"
