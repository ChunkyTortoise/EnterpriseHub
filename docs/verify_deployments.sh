#!/bin/bash
# Streamlit Deployment Verification Script

echo "=== Streamlit App Deployment Status ==="
echo ""

urls=(
    "https://ct-agentforge.streamlit.app"
    "https://ct-prompt-lab.streamlit.app"
    "https://ct-llm-starter.streamlit.app"
)

names=(
    "AgentForge"
    "Prompt Lab"
    "LLM Starter"
)

for i in "${!urls[@]}"; do
    url="${urls[$i]}"
    name="${names[$i]}"
    
    echo "[$name]"
    echo "URL: $url"
    
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>&1)
    
    if [ "$status" = "200" ]; then
        echo "✅ Status: $status OK - App is live!"
    elif [ "$status" = "303" ]; then
        echo "⚠️  Status: $status - App needs deployment/activation"
    else
        echo "❌ Status: $status - Check deployment"
    fi
    
    echo ""
done

echo "=== Verification Complete ==="
echo ""
echo "Next steps if apps are not live:"
echo "1. Visit https://share.streamlit.io/"
echo "2. Deploy apps following docs/STREAMLIT_DEPLOY_GUIDE.md"
echo "3. Run this script again to verify"
