#!/bin/bash
# Deploy API documentation to GitHub Pages

set -e

echo "🚀 Deploying API Documentation to GitHub Pages"

# Generate docs
python3 scripts/generate_api_docs.py

# Check if gh-pages branch exists
if ! git show-ref --verify --quiet refs/heads/gh-pages; then
    echo "Creating gh-pages branch..."
    git checkout --orphan gh-pages
    git rm -rf .
    git commit --allow-empty -m "Initialize gh-pages"
    git checkout main
fi

# Deploy using git subtree
echo "Pushing to gh-pages..."
git subtree push --prefix api-docs origin gh-pages

echo "✅ Deployed!"
echo "🔗 https://chunkytortoise.github.io/EnterpriseHub/"
