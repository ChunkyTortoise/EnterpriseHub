# Gumroad Product Tagging - Complete Automation Prompt

**Task**: Add category and tags to 14 existing Gumroad products via browser automation.

**Login**: Already authenticated at gumroad.com (session active)

---

## Instructions

For each product below:

1. Navigate to the product's Share URL
2. Set **Category** to: `Software > Developer Tools`
3. Add all **Tags** (type each tag and press Enter after each)
4. Click **Save changes**
5. Verify "Changes saved!" confirmation appears
6. Move to next product

---

## Products to Tag (14 total)

### 1. Data Intelligence Dashboard Enterprise
- **Product ID**: `fnlyf`
- **Share URL**: `https://gumroad.com/products/fnlyf/edit/share`
- **Tags**: `data-dashboard`, `enterprise`, `white-label`, `consulting`, `custom-development`, `slack-support`, `sla`, `production-grade`, `team-training`, `resale-rights`, `agency`, `business-intelligence`, `real-time`, `streaming`, `bigquery`

### 2. Data Intelligence Dashboard Pro
- **Product ID**: `yktghj`
- **Share URL**: `https://gumroad.com/products/yktghj/edit/share`
- **Tags**: `data-dashboard`, `business-intelligence`, `streamlit`, `advanced-analytics`, `cohort-analysis`, `rfm`, `ltv`, `ab-testing`, `funnel-analysis`, `case-studies`, `pdf-reports`, `database-connectors`, `postgresql`, `bigquery`, `snowflake`

### 3. Web Scraper & Price Monitor Enterprise
- **Product ID**: `haoudw`
- **Share URL**: `https://gumroad.com/products/haoudw/edit/share`
- **Tags**: `web-scraping`, `enterprise`, `proxy-rotation`, `anti-detection`, `white-label`, `custom-scrapers`, `priority-support`, `commercial-license`, `resale-rights`, `headless-browser`, `python`, `production-ready`, `selenium`, `playwright`

### 4. Web Scraper & Price Monitor Pro
- **Product ID**: `hqprrr`
- **Share URL**: `https://gumroad.com/products/hqprrr/edit/share`
- **Tags**: `web-scraping`, `price-monitoring`, `proxy-rotation`, `anti-detection`, `headless-browser`, `selenium`, `playwright`, `yaml-config`, `change-detection`, `price-tracker`, `seo`, `python`, `async`, `production-ready`

### 5. DocQA Engine Enterprise
- **Product ID**: `ryothv`
- **Share URL**: `https://gumroad.com/products/ryothv/edit/share`
- **Tags**: `rag`, `enterprise`, `document-qa`, `custom-rag`, `white-label`, `slack-support`, `commercial-license`, `resale-rights`, `vector-database`, `llm`, `ai`, `chatbot`, `knowledge-base`, `production-grade`

### 6. DocQA Engine Pro
- **Product ID**: `akggr`
- **Share URL**: `https://gumroad.com/products/akggr/edit/share`
- **Tags**: `rag`, `document-qa`, `vector-database`, `hybrid-search`, `llm`, `chatbot`, `ai`, `knowledge-base`, `citation-scoring`, `chunking`, `embeddings`, `fastapi`, `streamlit`, `production-ready`, `python`

### 7. AgentForge Enterprise
- **Product ID**: `vfxqj`
- **Share URL**: `https://gumroad.com/products/vfxqj/edit/share`
- **Tags**: `llm-orchestrator`, `enterprise`, `multi-provider`, `white-label`, `commercial-license`, `claude`, `gpt-4`, `gemini`, `priority-support`, `production-grade`, `ai-agents`, `chatbot`, `python`, `async`

### 8. AgentForge Pro
- **Product ID**: `nvsyaa`
- **Share URL**: `https://gumroad.com/products/nvsyaa/edit/share`
- **Tags**: `llm-orchestrator`, `multi-provider`, `claude`, `gpt-4`, `gemini`, `production-ready`, `rate-limiting`, `cost-tracking`, `function-calling`, `streaming`, `python`, `async`, `ai-agents`, `chatbot`, `developer-tools`

### 9. AI Integration Starter Kit (Starter)
- **Product ID**: `tghyec`
- **Share URL**: `https://gumroad.com/products/tghyec/edit/share`
- **Tags**: `llm-integration`, `claude`, `gpt`, `gemini`, `streaming`, `function-calling`, `rag`, `cost-tracker`, `python`, `starter-kit`, `ai-development`, `developer-tools`, `production-ready`, `examples`, `mit-license`

### 10. Prompt Engineering Toolkit (Starter)
- **Product ID**: `dlaoh`
- **Share URL**: `https://gumroad.com/products/dlaoh/edit/share`
- **Tags**: `prompt-engineering`, `llm-prompts`, `chatgpt-prompts`, `claude-prompts`, `ai-prompts`, `prompt-templates`, `prompt-optimization`, `token-counting`, `ai-cost-reduction`, `prompt-patterns`, `python`, `template-manager`, `developer-tools`, `ai-development`

### 11. Data Intelligence Dashboard (Insight Starter)
- **Product ID**: `lknrrt`
- **Share URL**: `https://gumroad.com/products/lknrrt/edit/share`
- **Tags**: `data-dashboard`, `business-intelligence`, `streamlit`, `csv-analysis`, `data-visualization`, `forecasting`, `clustering`, `anomaly-detection`, `pdf-reports`, `python`, `starter-kit`, `developer-tools`, `analytics`, `production-ready`, `mit-license`

### 12. Web Scraper & Price Monitor Toolkit (Scraper Starter)
- **Product ID**: `aixma`
- **Share URL**: `https://gumroad.com/products/aixma/edit/share`
- **Tags**: `web-scraping`, `price-monitoring`, `yaml-config`, `change-detection`, `sha256`, `seo`, `price-tracker`, `async`, `python`, `starter-kit`, `developer-tools`, `production-ready`, `mit-license`, `headless-browser`

### 13. AgentForge Starter - Multi-LLM Orchestration Framework
- **Product ID**: `ssqhvi`
- **Share URL**: `https://gumroad.com/products/ssqhvi/edit/share`
- **Tags**: `llm-orchestrator`, `multi-provider`, `claude`, `gemini`, `openai`, `python`, `async`, `rate-limiting`, `cost-tracking`, `production-ready`, `ai-api`, `chatbot`, `agent-framework`, `starter-kit`, `mit-license`

### 14. AI Document Q&A Engine (DocQA Starter)
- **Product ID**: `cvgam`
- **Share URL**: `https://gumroad.com/products/cvgam/edit/share`
- **Tags**: `rag`, `document-qa`, `vector-database`, `llm`, `ai`, `chatbot`, `knowledge-base`, `embeddings`, `chunking`, `fastapi`, `streamlit`, `python`, `starter-kit`, `production-ready`, `mit-license`

---

## Category Dropdown Instructions

The category field is a **combobox/select** dropdown. To set it:

1. Click on the Category field (shows "Other" by default)
2. Type: `Software`
3. Wait for dropdown to show "Software > Developer Tools"
4. Click or press Enter to select "Software > Developer Tools"
5. Field should now show: `Software > Developer Tools`

## Tags Field Instructions

The tags field is a **multi-select tag input**. To add tags:

1. Click on the Tags field (shows "Begin typing to add a tag...")
2. Type the first tag (e.g., `data-dashboard`)
3. Press **Enter** to add the tag
4. Tag should appear as a chip/bubble
5. Repeat for all remaining tags
6. Each tag is added individually by typing + Enter

## Save Instructions

1. After adding category and all tags, scroll to top of page
2. Click **Save changes** button (top right, purple)
3. Wait for confirmation: "Changes saved!" toast message
4. If you see "Changes saved!", proceed to next product
5. If category/tags disappeared after save, they did NOT save - retry

---

## Verification Checklist (Per Product)

- [ ] Category set to "Software > Developer Tools"
- [ ] All tags added (count matches list above)
- [ ] "Save changes" clicked
- [ ] "Changes saved!" confirmation appeared
- [ ] Category and tags still visible after save (if they disappeared, retry)

---

## Troubleshooting

**Category reverts to "Other" after save:**
- The dropdown selection didn't register
- Solution: Click dropdown, wait for options to load, then select with mouse click (not just typing)

**Tags field empty after save:**
- Tags didn't register (Enter key after each tag is required)
- Solution: Type tag, press Enter, verify chip appears, then type next tag

**Can't find "Software > Developer Tools":**
- Dropdown may need time to populate
- Solution: Type "Software", wait 1-2 seconds, then arrow down or mouse select

---

## Success Criteria

All 14 products should have:
- ✅ Category: "Software > Developer Tools"
- ✅ 10-15 tags each (from lists above)
- ✅ "Changes saved!" confirmation shown
- ✅ Changes persist after refresh

---

## Estimated Time

- ~3-5 minutes per product
- Total: **42-70 minutes** for all 14 products

---

## Additional Context

- User already authenticated at gumroad.com
- These are existing published products
- Goal: Improve Gumroad Discover visibility with proper categorization and tags
- No other changes needed (pricing, descriptions, content are already set)
