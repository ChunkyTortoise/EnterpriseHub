# Stripe Payment Links & Embed HTML for Portfolio Store

**Generated**: 2026-02-18
**Target Site**: `chunkytortoise.github.io/store.html`
**Status**: AWAITING STRIPE API EXECUTION

---

## How to Use

1. Run the creation script with your live Stripe key:
   ```bash
   cd /Users/cave/Documents/GitHub/EnterpriseHub
   STRIPE_SECRET_KEY=sk_live_YOUR_KEY bash content/stripe-create-products.sh
   ```
2. The script outputs all payment link URLs and saves them to `content/stripe-product-ids.json`
3. Replace the `PAYMENT_LINK_URL` placeholders below with the real URLs from the script output
4. Copy the relevant HTML sections into `store.html`

---

## Product Mapping (fill after running script)

| Product | Tier | Price | Stripe Product ID | Stripe Price ID | Payment Link URL |
|---------|------|-------|-------------------|-----------------|------------------|
| AgentForge AI Starter Kit | Starter | $49 | `prod_XXX` | `price_XXX` | `https://buy.stripe.com/XXX` |
| AgentForge AI Starter Kit | Pro | $199 | (same product) | `price_XXX` | `https://buy.stripe.com/XXX` |
| AgentForge AI Starter Kit | Enterprise | $999 | (same product) | `price_XXX` | `https://buy.stripe.com/XXX` |
| DocQA Engine | Starter | $59 | `prod_XXX` | `price_XXX` | `https://buy.stripe.com/XXX` |
| DocQA Engine | Pro | $249 | (same product) | `price_XXX` | `https://buy.stripe.com/XXX` |
| DocQA Engine | Enterprise | $1,499 | (same product) | `price_XXX` | `https://buy.stripe.com/XXX` |
| Prompt Engineering Toolkit | Starter | $29 | `prod_XXX` | `price_XXX` | `https://buy.stripe.com/XXX` |
| Prompt Engineering Toolkit | Pro | $79 | (same product) | `price_XXX` | `https://buy.stripe.com/XXX` |
| Prompt Engineering Toolkit | Enterprise | $199 | (same product) | `price_XXX` | `https://buy.stripe.com/XXX` |

---

## Embed HTML: 3-Tier Pricing Cards

This replaces the "Choose Your Plan" section in `store.html` and adds per-product tier selectors. Copy and adapt as needed.

### Option A: Inline Tier Selector (Per-Product Card)

Replace the existing product cards in the `<!-- Product Grid -->` section. Each card gets a tier dropdown and the "Buy Now" button updates accordingly.

```html
<!-- ============================================ -->
<!-- AgentForge AI Starter Kit — 3-Tier Card      -->
<!-- ============================================ -->
<div class="product-card">
    <div class="px-6 pt-6 pb-4">
        <div class="text-sm text-indigo-600 font-medium mb-1">Multi-Agent AI</div>
        <h3 class="text-xl font-bold mb-2">AgentForge AI Starter Kit</h3>
        <p class="text-gray-600 text-sm mb-4">Production-ready Python framework for Claude, GPT-4, Gemini orchestration. 550+ tests, Docker ready, MIT licensed. Unified async interface with cost tracking and streaming.</p>

        <!-- Tier Selector -->
        <div class="flex gap-2 mb-4" id="af-tiers">
            <button onclick="selectTier('af','starter')" class="tier-tab active text-xs font-semibold px-3 py-1.5 rounded-full bg-indigo-600 text-white" id="af-tab-starter">Starter</button>
            <button onclick="selectTier('af','pro')" class="tier-tab text-xs font-semibold px-3 py-1.5 rounded-full bg-gray-200 text-gray-700 hover:bg-gray-300" id="af-tab-pro">Pro</button>
            <button onclick="selectTier('af','enterprise')" class="tier-tab text-xs font-semibold px-3 py-1.5 rounded-full bg-gray-200 text-gray-700 hover:bg-gray-300" id="af-tab-enterprise">Enterprise</button>
        </div>

        <!-- Tier: Starter -->
        <div id="af-starter" class="tier-content">
            <div class="price mb-3">
                <span class="text-3xl font-bold text-gray-900">$49</span>
            </div>
            <ul class="text-sm text-gray-600 space-y-2 mb-6">
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 550+ tests, 80%+ coverage</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 4 LLM providers unified API</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Docker + CLI + Streamlit demo</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> MIT License, 4 examples</li>
            </ul>
        </div>

        <!-- Tier: Pro -->
        <div id="af-pro" class="tier-content hidden">
            <div class="price mb-3">
                <span class="text-3xl font-bold text-gray-900">$199</span>
                <span class="text-sm text-gray-500 ml-1">save $349</span>
            </div>
            <ul class="text-sm text-gray-600 space-y-2 mb-6">
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Everything in Starter</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 3 production case studies ($147K savings)</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 30-min architecture consultation</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Priority support (48hr SLA)</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 9 advanced examples + CI/CD templates</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Lifetime updates</li>
            </ul>
        </div>

        <!-- Tier: Enterprise -->
        <div id="af-enterprise" class="tier-content hidden">
            <div class="price mb-3">
                <span class="text-3xl font-bold text-gray-900">$999</span>
                <span class="text-sm text-gray-500 ml-1">save $4,100</span>
            </div>
            <ul class="text-sm text-gray-600 space-y-2 mb-6">
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Everything in Pro</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 60-min architecture deep-dive</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 2-3 custom code examples for your domain</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 90-day private Slack (4hr SLA)</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> White-label & resale rights</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Team training (up to 10 people)</li>
            </ul>
        </div>
    </div>
    <div class="px-6 pb-6 mt-auto">
        <!-- REPLACE THESE URLs after running stripe-create-products.sh -->
        <a href="PAYMENT_LINK_URL_AF_STARTER" class="buy-btn" id="af-buy">Buy Starter — $49</a>
        <a href="https://ct-agentforge.streamlit.app" class="demo-btn" target="_blank" rel="noopener noreferrer">View Demo</a>
    </div>
</div>


<!-- ============================================ -->
<!-- DocQA Engine — 3-Tier Card                   -->
<!-- ============================================ -->
<div class="product-card">
    <div class="px-6 pt-6 pb-4">
        <div class="text-sm text-indigo-600 font-medium mb-1">RAG / LLM</div>
        <h3 class="text-xl font-bold mb-2">DocQA Engine</h3>
        <p class="text-gray-600 text-sm mb-4">Document Q&A pipeline with hybrid retrieval (BM25 + semantic vectors), 5 chunking strategies, citation scoring, REST API, and Streamlit UI. 500+ tests, self-hosted, zero external APIs.</p>

        <!-- Tier Selector -->
        <div class="flex gap-2 mb-4" id="dq-tiers">
            <button onclick="selectTier('dq','starter')" class="tier-tab active text-xs font-semibold px-3 py-1.5 rounded-full bg-indigo-600 text-white" id="dq-tab-starter">Starter</button>
            <button onclick="selectTier('dq','pro')" class="tier-tab text-xs font-semibold px-3 py-1.5 rounded-full bg-gray-200 text-gray-700 hover:bg-gray-300" id="dq-tab-pro">Pro</button>
            <button onclick="selectTier('dq','enterprise')" class="tier-tab text-xs font-semibold px-3 py-1.5 rounded-full bg-gray-200 text-gray-700 hover:bg-gray-300" id="dq-tab-enterprise">Enterprise</button>
        </div>

        <!-- Tier: Starter -->
        <div id="dq-starter" class="tier-content">
            <div class="price mb-3">
                <span class="text-3xl font-bold text-gray-900">$59</span>
            </div>
            <ul class="text-sm text-gray-600 space-y-2 mb-6">
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Hybrid search (BM25 + dense vectors)</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 5 chunking strategies</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Citation scoring with confidence</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> FastAPI + Streamlit + Docker</li>
            </ul>
        </div>

        <!-- Tier: Pro -->
        <div id="dq-pro" class="tier-content hidden">
            <div class="price mb-3">
                <span class="text-3xl font-bold text-gray-900">$249</span>
                <span class="text-sm text-gray-500 ml-1">save $508</span>
            </div>
            <ul class="text-sm text-gray-600 space-y-2 mb-6">
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Everything in Starter</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 30-page RAG optimization guide</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 3 case studies (legal, healthcare, finance)</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 30-min expert RAG consultation</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Priority support (48hr SLA)</li>
            </ul>
        </div>

        <!-- Tier: Enterprise -->
        <div id="dq-enterprise" class="tier-content hidden">
            <div class="price mb-3">
                <span class="text-3xl font-bold text-gray-900">$1,499</span>
                <span class="text-sm text-gray-500 ml-1">save $4,850</span>
            </div>
            <ul class="text-sm text-gray-600 space-y-2 mb-6">
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Everything in Pro</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 60-min architecture deep-dive</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Custom domain tuning for your docs</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 90-day Slack support (4hr SLA)</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> White-label & resale rights</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Vector DB migration guides</li>
            </ul>
        </div>
    </div>
    <div class="px-6 pb-6 mt-auto">
        <!-- REPLACE THESE URLs after running stripe-create-products.sh -->
        <a href="PAYMENT_LINK_URL_DQ_STARTER" class="buy-btn" id="dq-buy">Buy Starter — $59</a>
        <a href="https://ct-document-engine.streamlit.app" class="demo-btn" target="_blank" rel="noopener noreferrer">View Demo</a>
    </div>
</div>


<!-- ============================================ -->
<!-- Prompt Engineering Toolkit — 3-Tier Card     -->
<!-- ============================================ -->
<div class="product-card">
    <div class="px-6 pt-6 pb-4">
        <div class="text-sm text-indigo-600 font-medium mb-1">Tools / Prompts</div>
        <h3 class="text-xl font-bold mb-2">Prompt Engineering Toolkit</h3>
        <p class="text-gray-600 text-sm mb-4">8 battle-tested prompt patterns with template management, token counting, A/B testing, cost optimization, and evaluation metrics. 190 tests. Works with Claude, GPT, Gemini.</p>

        <!-- Tier Selector -->
        <div class="flex gap-2 mb-4" id="pt-tiers">
            <button onclick="selectTier('pt','starter')" class="tier-tab active text-xs font-semibold px-3 py-1.5 rounded-full bg-indigo-600 text-white" id="pt-tab-starter">Starter</button>
            <button onclick="selectTier('pt','pro')" class="tier-tab text-xs font-semibold px-3 py-1.5 rounded-full bg-gray-200 text-gray-700 hover:bg-gray-300" id="pt-tab-pro">Pro</button>
            <button onclick="selectTier('pt','enterprise')" class="tier-tab text-xs font-semibold px-3 py-1.5 rounded-full bg-gray-200 text-gray-700 hover:bg-gray-300" id="pt-tab-enterprise">Enterprise</button>
        </div>

        <!-- Tier: Starter -->
        <div id="pt-starter" class="tier-content">
            <div class="price mb-3">
                <span class="text-3xl font-bold text-gray-900">$29</span>
            </div>
            <ul class="text-sm text-gray-600 space-y-2 mb-6">
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 8 production-ready prompt patterns</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Template manager with variables</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Token counter for cost estimation</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 10 example templates, quick-start guide</li>
            </ul>
        </div>

        <!-- Tier: Pro -->
        <div id="pt-pro" class="tier-content hidden">
            <div class="price mb-3">
                <span class="text-3xl font-bold text-gray-900">$79</span>
            </div>
            <ul class="text-sm text-gray-600 space-y-2 mb-6">
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Everything in Starter</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> A/B testing framework</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Cost calculator (per-model pricing)</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Prompt versioning with rollback</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Safety checker (injection detection)</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> CLI tool for terminal workflows</li>
            </ul>
        </div>

        <!-- Tier: Enterprise -->
        <div id="pt-enterprise" class="tier-content hidden">
            <div class="price mb-3">
                <span class="text-3xl font-bold text-gray-900">$199</span>
            </div>
            <ul class="text-sm text-gray-600 space-y-2 mb-6">
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Everything in Pro</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Benchmark runner for evaluation</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Report generator (Markdown/PDF)</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Docker + CI/CD templates</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> Commercial license (unlimited team)</li>
                <li class="flex items-start gap-2"><span class="text-green-500 mt-0.5">&#10003;</span> 30-min consultation + 30-day priority support</li>
            </ul>
        </div>
    </div>
    <div class="px-6 pb-6 mt-auto">
        <!-- REPLACE THESE URLs after running stripe-create-products.sh -->
        <a href="PAYMENT_LINK_URL_PT_STARTER" class="buy-btn" id="pt-buy">Buy Starter — $29</a>
        <a href="https://github.com/ChunkyTortoise/prompt-engineering-lab" class="demo-btn" target="_blank" rel="noopener noreferrer">View on GitHub</a>
    </div>
</div>
```

---

## JavaScript: Tier Switcher

Add this `<script>` tag just before `</body>` in `store.html`:

```html
<script>
// Payment link URLs — replace after running stripe-create-products.sh
const paymentLinks = {
    af: {
        starter:    'PAYMENT_LINK_URL_AF_STARTER',
        pro:        'PAYMENT_LINK_URL_AF_PRO',
        enterprise: 'PAYMENT_LINK_URL_AF_ENTERPRISE'
    },
    dq: {
        starter:    'PAYMENT_LINK_URL_DQ_STARTER',
        pro:        'PAYMENT_LINK_URL_DQ_PRO',
        enterprise: 'PAYMENT_LINK_URL_DQ_ENTERPRISE'
    },
    pt: {
        starter:    'PAYMENT_LINK_URL_PT_STARTER',
        pro:        'PAYMENT_LINK_URL_PT_PRO',
        enterprise: 'PAYMENT_LINK_URL_PT_ENTERPRISE'
    }
};

const prices = {
    af: { starter: '$49', pro: '$199', enterprise: '$999' },
    dq: { starter: '$59', pro: '$249', enterprise: '$1,499' },
    pt: { starter: '$29', pro: '$79', enterprise: '$199' }
};

const tierNames = { starter: 'Starter', pro: 'Pro', enterprise: 'Enterprise' };

function selectTier(product, tier) {
    // Hide all tier content for this product
    ['starter', 'pro', 'enterprise'].forEach(t => {
        const content = document.getElementById(product + '-' + t);
        const tab = document.getElementById(product + '-tab-' + t);
        if (content) content.classList.add('hidden');
        if (tab) {
            tab.classList.remove('bg-indigo-600', 'text-white');
            tab.classList.add('bg-gray-200', 'text-gray-700');
        }
    });

    // Show selected tier
    const selected = document.getElementById(product + '-' + tier);
    const selectedTab = document.getElementById(product + '-tab-' + tier);
    if (selected) selected.classList.remove('hidden');
    if (selectedTab) {
        selectedTab.classList.remove('bg-gray-200', 'text-gray-700');
        selectedTab.classList.add('bg-indigo-600', 'text-white');
    }

    // Update buy button
    const buyBtn = document.getElementById(product + '-buy');
    if (buyBtn && paymentLinks[product] && paymentLinks[product][tier]) {
        buyBtn.href = paymentLinks[product][tier];
        buyBtn.textContent = 'Buy ' + tierNames[tier] + ' \u2014 ' + prices[product][tier];
    }
}
</script>
```

---

## CSS Addition

Add to `style.css`:

```css
/* Tier content toggle */
.tier-content.hidden {
    display: none;
}

/* Tier tab hover */
.tier-tab {
    cursor: pointer;
    transition: background-color 0.15s, color 0.15s;
}
```

---

## Option B: Simple Direct Links (No Tier Selector)

If you prefer separate "Buy Now" links without the interactive tier selector, use these standalone buttons wherever needed:

### AgentForge AI Starter Kit
```html
<a href="PAYMENT_LINK_URL_AF_STARTER" class="buy-btn">Buy Starter — $49</a>
<a href="PAYMENT_LINK_URL_AF_PRO" class="buy-btn">Buy Pro — $199</a>
<a href="PAYMENT_LINK_URL_AF_ENTERPRISE" class="buy-btn">Buy Enterprise — $999</a>
```

### DocQA Engine
```html
<a href="PAYMENT_LINK_URL_DQ_STARTER" class="buy-btn">Buy Starter — $59</a>
<a href="PAYMENT_LINK_URL_DQ_PRO" class="buy-btn">Buy Pro — $249</a>
<a href="PAYMENT_LINK_URL_DQ_ENTERPRISE" class="buy-btn">Buy Enterprise — $1,499</a>
```

### Prompt Engineering Toolkit
```html
<a href="PAYMENT_LINK_URL_PT_STARTER" class="buy-btn">Buy Starter — $29</a>
<a href="PAYMENT_LINK_URL_PT_PRO" class="buy-btn">Buy Pro — $79</a>
<a href="PAYMENT_LINK_URL_PT_ENTERPRISE" class="buy-btn">Buy Enterprise — $199</a>
```

---

## Option C: Updated "Choose Your Plan" Section

Replace the existing 3-tier section (Individual / Pro Bundle / Enterprise) in `store.html` with a product-aware pricing grid:

```html
<!-- Pricing Tiers — 3 Products x 3 Tiers -->
<section class="bg-gray-900 py-20">
    <div class="max-w-6xl mx-auto px-4">
        <h2 class="text-3xl font-bold text-center text-white mb-4">Choose Your Plan</h2>
        <p class="text-gray-400 text-center mb-12 max-w-2xl mx-auto">Every tier includes source code, tests, and documentation. Higher tiers add case studies, consulting, and support.</p>

        <!-- Tier Comparison -->
        <div class="overflow-x-auto">
            <table class="w-full text-sm text-left text-gray-300">
                <thead>
                    <tr class="border-b border-gray-700">
                        <th class="px-4 py-3 text-gray-400 font-medium">Feature</th>
                        <th class="px-4 py-3 text-center text-white font-bold">Starter</th>
                        <th class="px-4 py-3 text-center text-indigo-400 font-bold">Pro</th>
                        <th class="px-4 py-3 text-center text-yellow-400 font-bold">Enterprise</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="border-b border-gray-800">
                        <td class="px-4 py-3 font-medium text-white">Full source code + tests</td>
                        <td class="px-4 py-3 text-center text-green-400">&#10003;</td>
                        <td class="px-4 py-3 text-center text-green-400">&#10003;</td>
                        <td class="px-4 py-3 text-center text-green-400">&#10003;</td>
                    </tr>
                    <tr class="border-b border-gray-800">
                        <td class="px-4 py-3 font-medium text-white">Docker + documentation</td>
                        <td class="px-4 py-3 text-center text-green-400">&#10003;</td>
                        <td class="px-4 py-3 text-center text-green-400">&#10003;</td>
                        <td class="px-4 py-3 text-center text-green-400">&#10003;</td>
                    </tr>
                    <tr class="border-b border-gray-800">
                        <td class="px-4 py-3 font-medium text-white">Production case studies</td>
                        <td class="px-4 py-3 text-center text-gray-600">&mdash;</td>
                        <td class="px-4 py-3 text-center text-green-400">&#10003; (3)</td>
                        <td class="px-4 py-3 text-center text-green-400">&#10003; (3)</td>
                    </tr>
                    <tr class="border-b border-gray-800">
                        <td class="px-4 py-3 font-medium text-white">Expert consultation</td>
                        <td class="px-4 py-3 text-center text-gray-600">&mdash;</td>
                        <td class="px-4 py-3 text-center text-green-400">30 min</td>
                        <td class="px-4 py-3 text-center text-green-400">60 min</td>
                    </tr>
                    <tr class="border-b border-gray-800">
                        <td class="px-4 py-3 font-medium text-white">Priority support</td>
                        <td class="px-4 py-3 text-center text-gray-600">&mdash;</td>
                        <td class="px-4 py-3 text-center text-green-400">48hr email</td>
                        <td class="px-4 py-3 text-center text-green-400">4hr Slack</td>
                    </tr>
                    <tr class="border-b border-gray-800">
                        <td class="px-4 py-3 font-medium text-white">Custom code examples</td>
                        <td class="px-4 py-3 text-center text-gray-600">&mdash;</td>
                        <td class="px-4 py-3 text-center text-gray-600">&mdash;</td>
                        <td class="px-4 py-3 text-center text-green-400">2-3 custom</td>
                    </tr>
                    <tr class="border-b border-gray-800">
                        <td class="px-4 py-3 font-medium text-white">White-label rights</td>
                        <td class="px-4 py-3 text-center text-gray-600">&mdash;</td>
                        <td class="px-4 py-3 text-center text-gray-600">&mdash;</td>
                        <td class="px-4 py-3 text-center text-green-400">&#10003;</td>
                    </tr>
                    <tr class="border-b border-gray-800">
                        <td class="px-4 py-3 font-medium text-white">Team training</td>
                        <td class="px-4 py-3 text-center text-gray-600">&mdash;</td>
                        <td class="px-4 py-3 text-center text-gray-600">&mdash;</td>
                        <td class="px-4 py-3 text-center text-green-400">Up to 10</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Product Price Cards -->
        <div class="grid md:grid-cols-3 gap-6 mt-12">
            <!-- AgentForge -->
            <div class="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <h3 class="text-lg font-bold text-white mb-4">AgentForge AI Starter Kit</h3>
                <div class="space-y-3">
                    <a href="PAYMENT_LINK_URL_AF_STARTER" class="block text-center bg-gray-700 text-white px-4 py-2.5 rounded-lg font-semibold hover:bg-gray-600 transition text-sm">Starter — $49</a>
                    <a href="PAYMENT_LINK_URL_AF_PRO" class="block text-center bg-indigo-600 text-white px-4 py-2.5 rounded-lg font-semibold hover:bg-indigo-700 transition text-sm">Pro — $199</a>
                    <a href="PAYMENT_LINK_URL_AF_ENTERPRISE" class="block text-center bg-yellow-600 text-white px-4 py-2.5 rounded-lg font-semibold hover:bg-yellow-700 transition text-sm">Enterprise — $999</a>
                </div>
            </div>

            <!-- DocQA -->
            <div class="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <h3 class="text-lg font-bold text-white mb-4">DocQA Engine</h3>
                <div class="space-y-3">
                    <a href="PAYMENT_LINK_URL_DQ_STARTER" class="block text-center bg-gray-700 text-white px-4 py-2.5 rounded-lg font-semibold hover:bg-gray-600 transition text-sm">Starter — $59</a>
                    <a href="PAYMENT_LINK_URL_DQ_PRO" class="block text-center bg-indigo-600 text-white px-4 py-2.5 rounded-lg font-semibold hover:bg-indigo-700 transition text-sm">Pro — $249</a>
                    <a href="PAYMENT_LINK_URL_DQ_ENTERPRISE" class="block text-center bg-yellow-600 text-white px-4 py-2.5 rounded-lg font-semibold hover:bg-yellow-700 transition text-sm">Enterprise — $1,499</a>
                </div>
            </div>

            <!-- Prompt Toolkit -->
            <div class="bg-gray-800 rounded-xl p-6 border border-gray-700">
                <h3 class="text-lg font-bold text-white mb-4">Prompt Engineering Toolkit</h3>
                <div class="space-y-3">
                    <a href="PAYMENT_LINK_URL_PT_STARTER" class="block text-center bg-gray-700 text-white px-4 py-2.5 rounded-lg font-semibold hover:bg-gray-600 transition text-sm">Starter — $29</a>
                    <a href="PAYMENT_LINK_URL_PT_PRO" class="block text-center bg-indigo-600 text-white px-4 py-2.5 rounded-lg font-semibold hover:bg-indigo-700 transition text-sm">Pro — $79</a>
                    <a href="PAYMENT_LINK_URL_PT_ENTERPRISE" class="block text-center bg-yellow-600 text-white px-4 py-2.5 rounded-lg font-semibold hover:bg-yellow-700 transition text-sm">Enterprise — $199</a>
                </div>
            </div>
        </div>
    </div>
</section>
```

---

## Stripe Product Details Reference

### 1. AgentForge AI Starter Kit

**Description**: Production-ready Python framework for Claude, GPT-4, Gemini orchestration. 550+ tests, Docker ready, MIT licensed. Multi-LLM orchestration with unified async interface, token-aware rate limiting, exponential backoff, function calling, structured JSON output, cost tracking, and streaming support. 15KB core -- 3x smaller than LangChain.

| Tier | Price | Includes |
|------|-------|----------|
| Starter | $49 | Framework + 4 examples + Docker + MIT license |
| Pro | $199 | + 3 case studies + 30-min consult + 9 examples + CI/CD + priority support + lifetime updates |
| Enterprise | $999 | + 60-min deep-dive + custom code + 90-day Slack + white-label + team training |

### 2. DocQA Engine

**Description**: Production-ready RAG pipeline with hybrid retrieval (BM25 + semantic vectors), 5 chunking strategies, cross-encoder re-ranking, citation scoring with confidence levels, FastAPI REST API with JWT auth and rate limiting, and Streamlit demo UI. 500+ tests, Docker ready, zero external API dependencies. Self-hosted document Q&A. MIT licensed.

| Tier | Price | Includes |
|------|-------|----------|
| Starter | $59 | Full RAG pipeline + 5 chunking strategies + API + UI + Docker |
| Pro | $249 | + 30-page optimization guide + 3 case studies + 30-min consult + priority support |
| Enterprise | $1,499 | + 60-min deep-dive + custom domain tuning + 90-day Slack + white-label + vector DB migration |

### 3. Prompt Engineering Toolkit

**Description**: 8 battle-tested prompt patterns (Chain-of-Thought, Few-Shot, Role-Playing, Socratic, Tree-of-Thought, Constraint-Based, Iterative Refinement, Multi-Perspective) with template management, token counting, A/B testing, cost optimization, prompt versioning, safety checker, and evaluation metrics. 190 automated tests. Works with Claude, GPT, Gemini, or any LLM.

| Tier | Price | Includes |
|------|-------|----------|
| Starter | $29 | 8 patterns + template manager + token counter + 10 templates |
| Pro | $79 | + A/B testing + cost calculator + versioning + safety checker + CLI |
| Enterprise | $199 | + benchmark runner + report generator + Docker + CI/CD + commercial license + 30-min consult |

---

## Quick URL Replacement Guide

After running `stripe-create-products.sh`, do a find-and-replace in this file and in `store.html`:

| Placeholder | Replace with |
|-------------|-------------|
| `PAYMENT_LINK_URL_AF_STARTER` | AgentForge Starter payment link |
| `PAYMENT_LINK_URL_AF_PRO` | AgentForge Pro payment link |
| `PAYMENT_LINK_URL_AF_ENTERPRISE` | AgentForge Enterprise payment link |
| `PAYMENT_LINK_URL_DQ_STARTER` | DocQA Starter payment link |
| `PAYMENT_LINK_URL_DQ_PRO` | DocQA Pro payment link |
| `PAYMENT_LINK_URL_DQ_ENTERPRISE` | DocQA Enterprise payment link |
| `PAYMENT_LINK_URL_PT_STARTER` | Prompt Toolkit Starter payment link |
| `PAYMENT_LINK_URL_PT_PRO` | Prompt Toolkit Pro payment link |
| `PAYMENT_LINK_URL_PT_ENTERPRISE` | Prompt Toolkit Enterprise payment link |

The script also outputs a `content/stripe-product-ids.json` file with the full mapping for programmatic use.
