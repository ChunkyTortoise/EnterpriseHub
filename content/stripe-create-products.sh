#!/bin/bash
# =============================================================================
# Stripe Product + Price + Payment Link Creator
# =============================================================================
# Creates 3 products with 3 tiers each (9 prices, 9 payment links)
# Run: STRIPE_SECRET_KEY=sk_live_xxx bash content/stripe-create-products.sh
#
# Products:
#   1. AgentForge AI Starter Kit — $49 / $199 / $999
#   2. DocQA Engine             — $59 / $249 / $1,499
#   3. Prompt Engineering Toolkit — $29 / $79 / $199
# =============================================================================

set -euo pipefail

if [ -z "${STRIPE_SECRET_KEY:-}" ]; then
  echo "ERROR: STRIPE_SECRET_KEY env var is required."
  echo "Usage: STRIPE_SECRET_KEY=sk_live_xxx bash $0"
  exit 1
fi

SK="$STRIPE_SECRET_KEY"
OUTPUT_FILE="content/stripe-product-ids.json"

# Helper: create product, return product ID
create_product() {
  local name="$1"
  local description="$2"
  local category="$3"

  local result
  result=$(curl -s https://api.stripe.com/v1/products \
    -u "$SK:" \
    -d "name=$name" \
    --data-urlencode "description=$description" \
    -d "metadata[category]=$category" \
    -d "metadata[tier]=multi")

  echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])"
}

# Helper: create price, return price ID
create_price() {
  local product_id="$1"
  local amount_cents="$2"
  local nickname="$3"

  local result
  result=$(curl -s https://api.stripe.com/v1/prices \
    -u "$SK:" \
    -d "product=$product_id" \
    -d "unit_amount=$amount_cents" \
    -d "currency=usd" \
    -d "nickname=$nickname")

  echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])"
}

# Helper: create payment link, return URL
create_payment_link() {
  local price_id="$1"

  local result
  result=$(curl -s https://api.stripe.com/v1/payment_links \
    -u "$SK:" \
    -d "line_items[0][price]=$price_id" \
    -d "line_items[0][quantity]=1" \
    -d "after_completion[type]=redirect" \
    -d "after_completion[redirect][url]=https://chunkytortoise.github.io/thank-you.html")

  echo "$result" | python3 -c "import sys,json; print(json.load(sys.stdin)['url'])"
}

echo "============================================"
echo "Creating Stripe Products + Prices + Links"
echo "============================================"
echo ""

# -----------------------------------------------
# 1. AgentForge AI Starter Kit
# -----------------------------------------------
echo "[1/3] Creating AgentForge AI Starter Kit..."
AF_PRODUCT=$(create_product \
  "AgentForge AI Starter Kit" \
  "Production-ready Python framework for Claude, GPT-4, Gemini orchestration. 550+ tests, Docker ready, MIT licensed. Multi-LLM orchestration with unified async interface, token-aware rate limiting, exponential backoff, function calling, structured JSON output, cost tracking, and streaming support. 15KB core — 3x smaller than LangChain." \
  "multi-agent-ai")
echo "  Product ID: $AF_PRODUCT"

echo "  Creating Starter price ($49)..."
AF_STARTER_PRICE=$(create_price "$AF_PRODUCT" 4900 "AgentForge Starter")
echo "  Price ID: $AF_STARTER_PRICE"

echo "  Creating Pro price ($199)..."
AF_PRO_PRICE=$(create_price "$AF_PRODUCT" 19900 "AgentForge Pro")
echo "  Price ID: $AF_PRO_PRICE"

echo "  Creating Enterprise price ($999)..."
AF_ENT_PRICE=$(create_price "$AF_PRODUCT" 99900 "AgentForge Enterprise")
echo "  Price ID: $AF_ENT_PRICE"

echo "  Creating payment links..."
AF_STARTER_LINK=$(create_payment_link "$AF_STARTER_PRICE")
AF_PRO_LINK=$(create_payment_link "$AF_PRO_PRICE")
AF_ENT_LINK=$(create_payment_link "$AF_ENT_PRICE")
echo "  Starter: $AF_STARTER_LINK"
echo "  Pro:     $AF_PRO_LINK"
echo "  Enterprise: $AF_ENT_LINK"
echo ""

# -----------------------------------------------
# 2. DocQA Engine
# -----------------------------------------------
echo "[2/3] Creating DocQA Engine..."
DQ_PRODUCT=$(create_product \
  "DocQA Engine" \
  "Production-ready RAG pipeline with hybrid retrieval (BM25 + semantic vectors), 5 chunking strategies, cross-encoder re-ranking, citation scoring with confidence levels, FastAPI REST API with JWT auth and rate limiting, and Streamlit demo UI. 500+ tests, Docker ready, zero external API dependencies. Self-hosted document Q&A. MIT licensed." \
  "rag-llm")
echo "  Product ID: $DQ_PRODUCT"

echo "  Creating Starter price ($59)..."
DQ_STARTER_PRICE=$(create_price "$DQ_PRODUCT" 5900 "DocQA Starter")
echo "  Price ID: $DQ_STARTER_PRICE"

echo "  Creating Pro price ($249)..."
DQ_PRO_PRICE=$(create_price "$DQ_PRODUCT" 24900 "DocQA Pro")
echo "  Price ID: $DQ_PRO_PRICE"

echo "  Creating Enterprise price ($1499)..."
DQ_ENT_PRICE=$(create_price "$DQ_PRODUCT" 149900 "DocQA Enterprise")
echo "  Price ID: $DQ_ENT_PRICE"

echo "  Creating payment links..."
DQ_STARTER_LINK=$(create_payment_link "$DQ_STARTER_PRICE")
DQ_PRO_LINK=$(create_payment_link "$DQ_PRO_PRICE")
DQ_ENT_LINK=$(create_payment_link "$DQ_ENT_PRICE")
echo "  Starter: $DQ_STARTER_LINK"
echo "  Pro:     $DQ_PRO_LINK"
echo "  Enterprise: $DQ_ENT_LINK"
echo ""

# -----------------------------------------------
# 3. Prompt Engineering Toolkit
# -----------------------------------------------
echo "[3/3] Creating Prompt Engineering Toolkit..."
PT_PRODUCT=$(create_product \
  "Prompt Engineering Toolkit" \
  "8 battle-tested prompt patterns (Chain-of-Thought, Few-Shot, Role-Playing, Socratic, Tree-of-Thought, Constraint-Based, Iterative Refinement, Multi-Perspective) with template management, token counting, A/B testing, cost optimization, prompt versioning, safety checker, and evaluation metrics. 190 automated tests. Works with Claude, GPT, Gemini, or any LLM." \
  "tools-prompts")
echo "  Product ID: $PT_PRODUCT"

echo "  Creating Starter price ($29)..."
PT_STARTER_PRICE=$(create_price "$PT_PRODUCT" 2900 "Prompt Toolkit Starter")
echo "  Price ID: $PT_STARTER_PRICE"

echo "  Creating Pro price ($79)..."
PT_PRO_PRICE=$(create_price "$PT_PRODUCT" 7900 "Prompt Toolkit Pro")
echo "  Price ID: $PT_PRO_PRICE"

echo "  Creating Enterprise price ($199)..."
PT_ENT_PRICE=$(create_price "$PT_PRODUCT" 19900 "Prompt Toolkit Enterprise")
echo "  Price ID: $PT_ENT_PRICE"

echo "  Creating payment links..."
PT_STARTER_LINK=$(create_payment_link "$PT_STARTER_PRICE")
PT_PRO_LINK=$(create_payment_link "$PT_PRO_PRICE")
PT_ENT_LINK=$(create_payment_link "$PT_ENT_PRICE")
echo "  Starter: $PT_STARTER_LINK"
echo "  Pro:     $PT_PRO_LINK"
echo "  Enterprise: $PT_ENT_LINK"
echo ""

# -----------------------------------------------
# Output JSON mapping
# -----------------------------------------------
echo "============================================"
echo "Writing product mapping to $OUTPUT_FILE"
echo "============================================"

cat > "$OUTPUT_FILE" <<JSONEOF
{
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "mode": "$(echo $SK | grep -q 'sk_live' && echo 'live' || echo 'test')",
  "products": {
    "agentforge": {
      "product_id": "$AF_PRODUCT",
      "tiers": {
        "starter": { "price_id": "$AF_STARTER_PRICE", "amount": 4900, "payment_link": "$AF_STARTER_LINK" },
        "pro":     { "price_id": "$AF_PRO_PRICE",     "amount": 19900, "payment_link": "$AF_PRO_LINK" },
        "enterprise": { "price_id": "$AF_ENT_PRICE",  "amount": 99900, "payment_link": "$AF_ENT_LINK" }
      }
    },
    "docqa": {
      "product_id": "$DQ_PRODUCT",
      "tiers": {
        "starter": { "price_id": "$DQ_STARTER_PRICE", "amount": 5900, "payment_link": "$DQ_STARTER_LINK" },
        "pro":     { "price_id": "$DQ_PRO_PRICE",     "amount": 24900, "payment_link": "$DQ_PRO_LINK" },
        "enterprise": { "price_id": "$DQ_ENT_PRICE",  "amount": 149900, "payment_link": "$DQ_ENT_LINK" }
      }
    },
    "prompt_toolkit": {
      "product_id": "$PT_PRODUCT",
      "tiers": {
        "starter": { "price_id": "$PT_STARTER_PRICE", "amount": 2900, "payment_link": "$PT_STARTER_LINK" },
        "pro":     { "price_id": "$PT_PRO_PRICE",     "amount": 7900, "payment_link": "$PT_PRO_LINK" },
        "enterprise": { "price_id": "$PT_ENT_PRICE",  "amount": 19900, "payment_link": "$PT_ENT_LINK" }
      }
    }
  }
}
JSONEOF

echo ""
echo "Done! Product IDs and payment links saved to: $OUTPUT_FILE"
echo ""
echo "============================================"
echo "PAYMENT LINK SUMMARY"
echo "============================================"
echo ""
echo "AgentForge AI Starter Kit:"
echo "  Starter  ($49):   $AF_STARTER_LINK"
echo "  Pro      ($199):  $AF_PRO_LINK"
echo "  Enterprise ($999): $AF_ENT_LINK"
echo ""
echo "DocQA Engine:"
echo "  Starter  ($59):    $DQ_STARTER_LINK"
echo "  Pro      ($249):   $DQ_PRO_LINK"
echo "  Enterprise ($1,499): $DQ_ENT_LINK"
echo ""
echo "Prompt Engineering Toolkit:"
echo "  Starter  ($29):   $PT_STARTER_LINK"
echo "  Pro      ($79):   $PT_PRO_LINK"
echo "  Enterprise ($199): $PT_ENT_LINK"
echo ""
echo "Next: paste these URLs into content/stripe-embed-html.md"
echo "      or update store.html directly."
