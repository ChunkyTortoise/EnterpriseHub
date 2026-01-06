#!/bin/bash
# Quick Setup Script for Multiple Freelance Platforms
# Opens all registration pages in your browser

echo "🚀 Multi-Platform Freelance Setup"
echo "=================================="
echo ""
echo "This script will open registration pages for 6 freelance platforms."
echo "Your profile template is copied to clipboard for easy paste."
echo ""
read -p "Press ENTER to continue..."

# Profile template (will be copied to clipboard)
PROFILE_TEXT="Python & AI Engineer | IBM-Certified | 311+ Production Tests

I build production-grade Python applications specializing in:
• Interactive Streamlit dashboards
• AI automation (Claude 3.5, GPT-4)
• Web scraping & data pipelines
• API integrations

Recent Work:
EnterpriseHub - 7-module BI platform with 311 automated tests
https://github.com/ChunkyTortoise/EnterpriseHub

Tech Stack: Python, Streamlit, Plotly, pandas, Anthropic API, pytest

Certifications:
• IBM Generative AI Engineering (Professional)
• Google Business Intelligence (Professional)
• 1,700+ hours specialized training

Availability: 20-30 hrs/week
Rate: \$50-75/hr"

# Copy to clipboard (macOS)
echo "$PROFILE_TEXT" | pbcopy
echo "✅ Profile template copied to clipboard!"
echo ""

# Platform URLs
declare -a PLATFORMS=(
    "https://www.fiverr.com/start_selling|Fiverr (Gig Platform)"
    "https://www.freelancer.com/get-started|Freelancer.com"
    "https://www.peopleperhour.com/join|PeoplePerHour"
    "https://www.toptal.com/developers|Toptal (Vetted Platform)"
    "https://contra.com/signup|Contra (0% Commission)"
    "https://www.gun.io/signup|Gun.io (Developer-Focused)"
)

echo "Opening platforms in browser..."
echo ""

for platform in "${PLATFORMS[@]}"; do
    IFS='|' read -r url name <<< "$platform"
    echo "📍 Opening: $name"
    open "$url"
    sleep 2
done

echo ""
echo "✅ All platforms opened!"
echo ""
echo "📋 Next steps:"
echo "1. Fill in registration forms (profile template is in your clipboard)"
echo "2. Upload profile photo (professional headshot)"
echo "3. Link to GitHub: https://github.com/ChunkyTortoise/EnterpriseHub"
echo "4. Set rates: \$50/hr minimum"
echo "5. Complete verification (ID, payment method)"
echo ""
echo "⏱️  Estimated time: 2-3 hours total for all platforms"
echo ""
echo "💡 Tip: Use the same profile bio everywhere (just paste from clipboard)"
echo ""
