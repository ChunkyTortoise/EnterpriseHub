# API Documentation Deployment Guide
## Deploy Swagger UI to GitHub Pages

**Purpose:** Host interactive API documentation for potential clients and technical evaluators  
**Estimated Time:** 30 minutes  
**Result:** Public API docs at `https://chunkytortoise.github.io/EnterpriseHub/`

---

## Overview

EnterpriseHub has a comprehensive OpenAPI schema. This guide deploys it as interactive documentation using Swagger UI on GitHub Pages.

**Benefits:**
- Clients can explore API without cloning
- Technical evaluators see contract definitions immediately
- Always in sync with code (auto-deploy on push)
- Professional appearance for enterprise clients

---

## Prerequisites

- [ ] GitHub repository access
- [ ] OpenAPI schema exists at `portal_api/tests/openapi_snapshot.json`
- [ ] GitHub Pages enabled (Settings > Pages)

---

## Deployment Steps

### Step 1: Create GitHub Pages Branch

```bash
# Create orphan branch for GitHub Pages
git checkout --orphan gh-pages
git rm -rf .

# Create initial structure
mkdir -p api-docs
touch api-docs/.gitkeep

git add api-docs/
git commit -m "Initialize GitHub Pages for API docs"
git push origin gh-pages

# Return to main
git checkout main
```

### Step 2: Create Swagger UI Setup

Create file: `scripts/generate_api_docs.py`

```python
#!/usr/bin/env python3
"""
Generate static API documentation from OpenAPI schema.
Deploys to GitHub Pages branch.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

# Configuration
REPO_ROOT = Path(__file__).parent.parent
OPENAPI_SCHEMA = REPO_ROOT / "portal_api" / "tests" / "openapi_snapshot.json"
DOCS_DIR = REPO_ROOT / "api-docs"
SWAGGER_UI_VERSION = "5.10.3"

SWAGGER_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>EnterpriseHub API Documentation</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@{version}/swagger-ui.css">
    <link rel="icon" type="image/png" href="https://unpkg.com/swagger-ui-dist@{version}/favicon-32x32.png">
    <style>
        html {{ box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }}
        *, *:before, *:after {{ box-sizing: inherit; }}
        body {{ margin: 0; background: #fafafa; }}
        .topbar {{ display: none; }}
        .info {{ margin: 20px 0; }}
        .info .title {{ color: #6366F1; }}
        .scheme-container {{ margin: 20px 0; padding: 20px; background: #fff; border-radius: 8px; }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@{version}/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@{version}/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: './openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                validatorUrl: null,
                docExpansion: 'list',
                defaultModelsExpandDepth: 1,
                defaultModelExpandDepth: 1,
                displayOperationId: true,
                filter: true,
                showExtensions: true,
                showCommonExtensions: true,
                tryItOutEnabled: true,
                supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
                oauth2RedirectUrl: window.location.origin + '/oauth2-redirect.html'
            }});
        }}
    </script>
</body>
</html>
'''

def main():
    """Generate API documentation."""
    print("🔧 EnterpriseHub API Documentation Generator")
    print("=" * 50)
    
    # Check OpenAPI schema exists
    if not OPENAPI_SCHEMA.exists():
        print(f"❌ OpenAPI schema not found: {OPENAPI_SCHEMA}")
        print("Run: python scripts/refresh_portal_openapi_snapshot.py")
        sys.exit(1)
    
    # Clean/create docs directory
    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir(parents=True)
    
    # Copy OpenAPI schema
    schema_dest = DOCS_DIR / "openapi.json"
    shutil.copy(OPENAPI_SCHEMA, schema_dest)
    print(f"✅ Copied OpenAPI schema: {schema_dest}")
    
    # Generate index.html
    html_content = SWAGGER_HTML.format(version=SWAGGER_UI_VERSION)
    index_path = DOCS_DIR / "index.html"
    index_path.write_text(html_content)
    print(f"✅ Generated Swagger UI: {index_path}")
    
    # Create CNAME (optional, for custom domain)
    # cname_path = DOCS_DIR / "CNAME"
    # cname_path.write_text("api.yourdomain.com")
    
    print("\n📋 Next Steps:")
    print("1. git add api-docs/")
    print("2. git commit -m 'Update API documentation'")
    print("3. git subtree push --prefix api-docs origin gh-pages")
    print("   OR use: scripts/deploy_api_docs.sh")
    print(f"\n🔗 URL: https://chunkytortoise.github.io/EnterpriseHub/")

if __name__ == "__main__":
    main()
```

Make it executable:
```bash
chmod +x scripts/generate_api_docs.py
```

### Step 3: Create Deployment Script

Create file: `scripts/deploy_api_docs.sh`

```bash
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
```

Make it executable:
```bash
chmod +x scripts/deploy_api_docs.sh
```

### Step 4: Generate and Deploy

```bash
# Generate docs
python3 scripts/generate_api_docs.py

# Add to git
git add scripts/generate_api_docs.py scripts/deploy_api_docs.sh
git commit -m "Add API documentation generator and deployment"

# Deploy to GitHub Pages
bash scripts/deploy_api_docs.sh
```

### Step 5: Configure GitHub Pages

1. Go to: `https://github.com/ChunkyTortoise/EnterpriseHub/settings/pages`
2. Source: Deploy from a branch
3. Branch: `gh-pages` / `root`
4. Click Save
5. Wait 2-5 minutes for deployment
6. Visit: `https://chunkytortoise.github.io/EnterpriseHub/`

---

## Automation (CI/CD)

Add to `.github/workflows/deploy-api-docs.yml`:

```yaml
name: Deploy API Documentation

on:
  push:
    branches: [ main ]
    paths:
      - 'portal_api/tests/openapi_snapshot.json'
      - 'scripts/generate_api_docs.py'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Generate API docs
        run: python scripts/generate_api_docs.py
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./api-docs
```

---

## Post-Deployment Verification

### Checklist

- [ ] URL loads without errors: `https://chunkytortoise.github.io/EnterpriseHub/`
- [ ] Swagger UI renders correctly
- [ ] All endpoints are listed
- [ ] Schemas display properly
- [ ] Try-it-out feature works (for demo endpoints)
- [ ] No console errors in browser dev tools

### Add Badge to README

Add to README.md:
```markdown
[![API Docs](https://img.shields.io/badge/API%20Docs-Swagger-green)](https://chunkytortoise.github.io/EnterpriseHub/)
```

---

## Custom Domain (Optional)

If you own a domain:

1. Add CNAME file:
   ```bash
   echo "api.chunkytortoise.io" > api-docs/CNAME
   ```

2. Update DNS:
   - Type: CNAME
   - Name: api
   - Value: chunkytortoise.github.io

3. Enable HTTPS in GitHub Pages settings

---

## Maintenance

### When to Regenerate

- [ ] After adding new API endpoints
- [ ] After changing request/response schemas
- [ ] After OpenAPI snapshot refresh
- [ ] Monthly (to update Swagger UI version)

### Quick Regenerate

```bash
python3 scripts/generate_api_docs.py && bash scripts/deploy_api_docs.sh
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| 404 error | Wait 5 minutes for GitHub Pages to propagate |
| CORS errors | Schema loaded from relative path (./openapi.json) |
| Broken styling | Check Swagger UI CDN version |
| Old version cached | Hard refresh (Cmd+Shift+R) |
| Deployment fails | Ensure gh-pages branch exists |

---

## Marketing Integration

### Add to Portfolio Site

Add this section to `chunkytortoise.github.io`:

```html
<div class="api-docs-cta">
    <h3>Explore the API</h3>
    <p>Interactive documentation with live examples</p>
    <a href="https://chunkytortoise.github.io/EnterpriseHub/" 
       class="btn btn-primary" target="_blank">
       View API Docs →
    </a>
</div>
```

### Include in Proposals

Add to client proposals:
> "Full API documentation available at: https://chunkytortoise.github.io/EnterpriseHub/"

---

## Result

After deployment, you'll have:
- ✅ Public API documentation
- ✅ Interactive Swagger UI
- ✅ Auto-deploy on schema changes
- ✅ Professional appearance for technical evaluators
- ✅ Reduced barrier to entry for potential clients

---

**Status:** Ready to deploy  
**Estimated Time:** 30 minutes  
**Created:** February 11, 2026
