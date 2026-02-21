"""
Example: Integrating GHL Webhooks with EnterpriseHub Bots

This file demonstrates how to wire up the GHL integration to existing FastAPI apps.
"""

# ============================================================================
# Option 1: Add to existing app.py
# ============================================================================


def integrate_with_main_app():
    """
    Add this to your app.py or main FastAPI application file:
    """
    from fastapi import FastAPI

    from ghl_integration import ghl_router, initialize_ghl_integration

    app = FastAPI()

    # Include GHL webhook router
    app.include_router(ghl_router, prefix="/ghl")

    @app.on_event("startup")
    async def startup_event():
        # Initialize GHL integration (registers handlers, starts retry worker)
        result = await initialize_ghl_integration()
        if not result.get("success"):
            print(f"⚠️ GHL Integration warning: {result.get('error')}")
        else:
            print("✅ GHL Integration initialized")
            print(f"   Handlers registered: {result.get('handlers_registered')}")


# ============================================================================
# Option 2: Per-bot integration (if bots run separately)
# ============================================================================


def integrate_with_lead_bot():
    """
    For lead_bot/main.py - if running as separate service
    """
    from fastapi import FastAPI

    from ghl_integration.integration import _register_lead_handlers
    from ghl_integration.router import router as ghl_router

    app = FastAPI()

    # Mount only lead bot webhooks
    app.include_router(ghl_router, prefix="/ghl")

    @app.on_event("startup")
    async def startup():
        _register_lead_handlers()
        print("✅ Lead Bot GHL handlers registered")


def integrate_with_seller_bot():
    """
    For seller_bot/main.py - if running as separate service
    """
    from fastapi import FastAPI

    from ghl_integration.integration import _register_seller_handlers
    from ghl_integration.router import router as ghl_router

    app = FastAPI()

    app.include_router(ghl_router, prefix="/ghl")

    @app.on_event("startup")
    async def startup():
        _register_seller_handlers()
        print("✅ Seller Bot GHL handlers registered")


def integrate_with_buyer_bot():
    """
    For buyer_bot/main.py - if running as separate service
    """
    from fastapi import FastAPI

    from ghl_integration.integration import _register_buyer_handlers
    from ghl_integration.router import router as ghl_router

    app = FastAPI()

    app.include_router(ghl_router, prefix="/ghl")

    @app.on_event("startup")
    async def startup():
        _register_buyer_handlers()
        print("✅ Buyer Bot GHL handlers registered")


# ============================================================================
# Option 3: Using lifespan (FastAPI 0.100+ recommended approach)
# ============================================================================


def integrate_with_lifespan():
    """
    Modern FastAPI approach using lifespan context manager
    """
    from contextlib import asynccontextmanager

    from fastapi import FastAPI

    from ghl_integration import ghl_router, initialize_ghl_integration, shutdown_ghl_integration

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Startup
        result = await initialize_ghl_integration()
        if result.get("success"):
            print("✅ GHL Integration ready")
        else:
            print(f"⚠️ GHL Integration issue: {result.get('error')}")

        yield

        # Shutdown
        await shutdown_ghl_integration()
        print("🛑 GHL Integration shutdown")

    app = FastAPI(lifespan=lifespan)
    app.include_router(ghl_router, prefix="/ghl")

    return app


# ============================================================================
# Environment Configuration Helper
# ============================================================================


def check_environment():
    """
    Run this to verify environment is configured correctly
    """
    from ghl_integration.integration import get_webhook_urls, verify_environment

    print("🔍 Checking GHL Integration Environment...\n")

    # Verify env vars
    results = verify_environment()

    print("Required Variables:")
    for var, present in results["required"].items():
        status = "✅" if present else "❌"
        print(f"  {status} {var}")

    print("\nOptional Variables:")
    for var, present in results["optional"].items():
        status = "✅" if present else "⚪"
        print(f"  {status} {var}")

    if results["missing_required"]:
        print(f"\n❌ Missing required: {', '.join(results['missing_required'])}")
    else:
        print("\n✅ All required variables present!")

    # Show webhook URLs
    import os

    base_url = os.getenv("APP_BASE_URL", "https://api.example.com")
    urls = get_webhook_urls(base_url)

    print(f"\n📡 Webhook URLs (base: {base_url}):")
    for bot_type, endpoints in urls.items():
        print(f"\n  {bot_type}:")
        for name, url in endpoints.items():
            print(f"    - {name}: {url}")

    return results["ready"]


# ============================================================================
# Manual Webhook Testing
# ============================================================================


async def test_webhook_locally():
    """
    Test webhooks locally using the fixtures
    """
    import json

    import httpx

    # Load fixture
    with open("tests/ghl_integration/fixtures/ghl_webhooks/contact_create.json") as f:
        payload = json.load(f)

    # Send to local server
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/ghl/webhook/lead/new-lead",
            json=payload,
            headers={"X-GHL-Signature": "test-signature"},
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")


# ============================================================================
# GHL Configuration Helper
# ============================================================================


def generate_ghl_webhook_config():
    """
    Generate YAML configuration for GHL webhook setup
    """
    import os

    base_url = os.getenv("APP_BASE_URL", "https://api.yourdomain.com")

    config = f"""
# GHL Webhook Configuration
# Add these to your GoHighLevel webhook settings

webhooks:
  # Lead Bot Webhooks
  - name: "Lead Bot - New Lead"
    url: "{base_url}/ghl/webhook/lead/new-lead"
    events:
      - "ContactCreate"
    filters:
      tags: ["lead"]
    
  - name: "Lead Bot - Lead Response"
    url: "{base_url}/ghl/webhook/lead/lead-response"
    events:
      - "ConversationMessageCreate"
    filters:
      direction: "inbound"
    
  # Seller Bot Webhooks  
  - name: "Seller Bot - Seller Inquiry"
    url: "{base_url}/ghl/webhook/seller/seller-inquiry"
    events:
      - "ContactCreate"
    filters:
      tags: ["seller", "listing_inquiry"]
    
  - name: "Seller Bot - Listing Created"
    url: "{base_url}/ghl/webhook/seller/listing-created"
    events:
      - "OpportunityCreate"
    filters:
      pipeline_id: "${{GHL_SELLER_PIPELINE_ID}}"
    
  - name: "Seller Bot - Seller Response"
    url: "{base_url}/ghl/webhook/seller/seller-response"
    events:
      - "ConversationMessageCreate"
    filters:
      tags: ["seller"]
      direction: "inbound"
    
  # Buyer Bot Webhooks
  - name: "Buyer Bot - Buyer Inquiry"
    url: "{base_url}/ghl/webhook/buyer/buyer-inquiry"
    events:
      - "ContactCreate"
    filters:
      tags: ["buyer", "home_buyer"]
    
  - name: "Buyer Bot - Buyer Response"
    url: "{base_url}/ghl/webhook/buyer/buyer-response"
    events:
      - "ConversationMessageCreate"
    filters:
      tags: ["buyer"]
      direction: "inbound"
    
  - name: "Buyer Bot - Pipeline Change"
    url: "{base_url}/ghl/webhook/buyer/pipeline-change"
    events:
      - "PipelineStageChange"
    filters:
      pipeline_id: "${{GHL_BUYER_PIPELINE_ID}}"
"""

    print(config)
    return config


if __name__ == "__main__":
    # Run environment check
    check_environment()

    print("\n" + "=" * 60)
    print("GHL Integration Examples")
    print("=" * 60)

    print("\nTo integrate:")
    print("1. Copy one of the integration functions above")
    print("2. Add to your main app.py file")
    print("3. Set environment variables in .env")
    print("4. Configure webhooks in GHL using the generated config")

    print("\nGenerate GHL config:")
    generate_ghl_webhook_config()
