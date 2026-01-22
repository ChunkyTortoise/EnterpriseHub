
import json
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.getcwd())

from fastapi.openapi.utils import get_openapi
from ghl_real_estate_ai.api.main import app

def generate_schema():
    """Generates and saves the OpenAPI schema for the hardening routes."""
    print("🎨 Generating JSON Schema for Next.js Export...")
    
    schema = get_openapi(
        title="Lyrio.io Hardened AI API",
        version="1.0.0",
        description="JSON/OpenAPI schema for hardened /matches and /analyze routes.",
        routes=app.routes,
    )
    
    # Ensure export directory exists
    export_dir = Path("ghl_real_estate_ai/schemas/export")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = export_dir / "api_schema.json"
    
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)
        
    print(f"✨ Schema successfully exported to {output_path}")
    print("🚀 Ready for React/Next.js frontend consumption.")

if __name__ == "__main__":
    generate_schema()
