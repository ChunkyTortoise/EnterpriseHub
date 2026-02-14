#!/usr/bin/env python3
"""
Generate static API documentation from OpenAPI schema.
Deploys to GitHub Pages branch.
"""

import json
import shutil
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
    
    print("\n📋 Next Steps:")
    print("1. git add api-docs/")
    print("2. git commit -m 'Update API documentation'")
    print("3. git subtree push --prefix api-docs origin gh-pages")
    print("   OR use: scripts/deploy_api_docs.sh")
    print(f"\n🔗 URL: https://chunkytortoise.github.io/EnterpriseHub/")

if __name__ == "__main__":
    main()
