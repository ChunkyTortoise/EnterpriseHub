# Dev.to Articles: Ready to Publish

**Date**: 2026-02-18
**Status**: No `DEV_TO_API_KEY` or `DEVTO_API_KEY` found in environment. Articles prepared for manual publishing.

---

## How to Get a Dev.to API Key

1. Log in to [dev.to](https://dev.to)
2. Go to **Settings** > **Extensions**
3. Under **DEV Community API Keys**, enter a description (e.g., "CLI publishing")
4. Click **Generate API Key**
5. Copy the key and set it in your environment:
   ```bash
   export DEV_TO_API_KEY="your_key_here"
   ```

---

## Selected Articles (4 best, deduplicated)

### Duplicate Analysis

| Topic | Files | Selected | Reason |
|-------|-------|----------|--------|
| RAG + LangChain | `article1-production-rag.md`, `article-4-production-rag.md`, `article-langchain-alternative.md` | `article-langchain-alternative.md` | Most polished: detailed LangChain migration stories, 5 chunking strategies, HybridRetriever class, citation scoring, performance comparison table |
| LangChain replacement | `article2-replaced-langchain.md` | Skipped (covered by langchain-alternative) | The httpx angle is good but too much overlap with the selected RAG article |
| Streamlit dashboard | `article3-csv-dashboard.md`, `article3-csv-to-dashboard.md` | `article3-csv-dashboard.md` | More detailed: step-by-step with timing, real estate lead dashboard example, production tips, common mistakes section |
| LLM cost reduction | `article-5-llm-cost-reduction.md` | `article-5-llm-cost-reduction.md` | Unique topic, excellent benchmarks, 89% cost reduction with implementation details |
| Multi-agent testing | `production-multi-agent-8500-tests.md` | `production-multi-agent-8500-tests.md` | Unique topic, practical patterns (circular handoff prevention, async coordination, observability) |

---

## Article 1: Why I Built a RAG System Without LangChain

- **File**: `article-langchain-alternative.md`
- **Tags**: `python`, `ai`, `rag`, `machinelearning`
- **Notes**: Remove the `canonical_url` placeholder before publishing (or set to actual URL). Change `published: true` to `published: false` in frontmatter for draft mode.

```bash
curl -X POST https://dev.to/api/articles \
  -H "Content-Type: application/json" \
  -H "api-key: $DEV_TO_API_KEY" \
  -d @- <<'CURL_EOF'
{
  "article": {
    "title": "Why I Built a RAG System Without LangChain",
    "body_markdown": "$(cat /Users/cave/Documents/GitHub/EnterpriseHub/content/devto/article-langchain-alternative.md | sed '1,/^---$/{ /^---$/d; /^---$/!d; }' | tail -n +2)",
    "published": false,
    "tags": ["python", "ai", "rag", "machinelearning"]
  }
}
CURL_EOF
```

---

## Article 2: How I Reduced LLM Costs by 89% With 3-Tier Caching

- **File**: `article-5-llm-cost-reduction.md`
- **Tags**: `python`, `ai`, `llm`, `optimization`

```bash
curl -X POST https://dev.to/api/articles \
  -H "Content-Type: application/json" \
  -H "api-key: $DEV_TO_API_KEY" \
  -d @- <<'CURL_EOF'
{
  "article": {
    "title": "How I Reduced LLM Costs by 89% With 3-Tier Caching",
    "body_markdown": "$(cat /Users/cave/Documents/GitHub/EnterpriseHub/content/devto/article-5-llm-cost-reduction.md | sed '1,/^---$/{ /^---$/d; /^---$/!d; }' | tail -n +2)",
    "published": false,
    "tags": ["python", "ai", "llm", "optimization"]
  }
}
CURL_EOF
```

---

## Article 3: CSV to Dashboard in 10 Minutes with Streamlit

- **File**: `article3-csv-dashboard.md`
- **Tags**: `python`, `streamlit`, `datascience`, `tutorial`

```bash
curl -X POST https://dev.to/api/articles \
  -H "Content-Type: application/json" \
  -H "api-key: $DEV_TO_API_KEY" \
  -d @- <<'CURL_EOF'
{
  "article": {
    "title": "CSV to Dashboard in 10 Minutes with Streamlit",
    "body_markdown": "$(cat /Users/cave/Documents/GitHub/EnterpriseHub/content/devto/article3-csv-dashboard.md | sed '1,/^---$/{ /^---$/d; /^---$/!d; }' | tail -n +2)",
    "published": false,
    "tags": ["python", "streamlit", "datascience", "tutorial"]
  }
}
CURL_EOF
```

---

## Article 4: Building Production Multi-Agent Systems: Lessons from 8,500 Tests

- **File**: `production-multi-agent-8500-tests.md`
- **Tags**: `ai`, `python`, `testing`, `architecture`

```bash
curl -X POST https://dev.to/api/articles \
  -H "Content-Type: application/json" \
  -H "api-key: $DEV_TO_API_KEY" \
  -d @- <<'CURL_EOF'
{
  "article": {
    "title": "Building Production Multi-Agent Systems: Lessons from 8,500 Tests",
    "body_markdown": "$(cat /Users/cave/Documents/GitHub/EnterpriseHub/content/devto/production-multi-agent-8500-tests.md | sed '1,/^---$/{ /^---$/d; /^---$/!d; }' | tail -n +2)",
    "published": false,
    "tags": ["ai", "python", "testing", "architecture"]
  }
}
CURL_EOF
```

---

## Recommended Publishing Order

1. **Multi-Agent Systems** (most unique, strongest hook with "8,500 tests")
2. **RAG Without LangChain** (controversial take drives engagement)
3. **LLM Cost Reduction** (practical value, shareable metric "89%")
4. **CSV to Dashboard** (broadest audience, beginner-friendly)

Space articles 2-3 days apart for maximum reach.

## Quick Publish Script

Once you have your API key, use this script to publish all 4 as drafts:

```bash
#!/bin/bash
# Save as publish_devto.sh and run: bash publish_devto.sh

API_KEY="${DEV_TO_API_KEY}"

if [ -z "$API_KEY" ]; then
  echo "ERROR: Set DEV_TO_API_KEY environment variable first"
  echo "  export DEV_TO_API_KEY='your_key_here'"
  exit 1
fi

BASEDIR="/Users/cave/Documents/GitHub/EnterpriseHub/content/devto"

publish_article() {
  local title="$1"
  local file="$2"
  local tags="$3"

  # Strip YAML frontmatter (everything between first pair of ---)
  local body
  body=$(awk 'BEGIN{skip=0} /^---$/{skip++; next} skip>=2{print}' "$file")

  # Build JSON payload using jq for proper escaping
  local payload
  payload=$(jq -n \
    --arg title "$title" \
    --arg body "$body" \
    --argjson tags "$tags" \
    '{article: {title: $title, body_markdown: $body, published: false, tags: $tags}}')

  echo "Publishing: $title"
  response=$(curl -s -X POST https://dev.to/api/articles \
    -H "Content-Type: application/json" \
    -H "api-key: $API_KEY" \
    -d "$payload")

  url=$(echo "$response" | jq -r '.url // "ERROR"')
  if [ "$url" != "ERROR" ] && [ "$url" != "null" ]; then
    echo "  Draft created: $url"
  else
    echo "  FAILED: $(echo "$response" | jq -r '.error // .message // "Unknown error"')"
  fi
  echo ""
}

publish_article \
  "Building Production Multi-Agent Systems: Lessons from 8,500 Tests" \
  "$BASEDIR/production-multi-agent-8500-tests.md" \
  '["ai", "python", "testing", "architecture"]'

publish_article \
  "Why I Built a RAG System Without LangChain" \
  "$BASEDIR/article-langchain-alternative.md" \
  '["python", "ai", "rag", "machinelearning"]'

publish_article \
  "How I Reduced LLM Costs by 89% With 3-Tier Caching" \
  "$BASEDIR/article-5-llm-cost-reduction.md" \
  '["python", "ai", "llm", "optimization"]'

publish_article \
  "CSV to Dashboard in 10 Minutes with Streamlit" \
  "$BASEDIR/article3-csv-dashboard.md" \
  '["python", "streamlit", "datascience", "tutorial"]'

echo "Done! Review drafts at: https://dev.to/dashboard"
```

## Pre-Publish Checklist

- [ ] Remove `canonical_url` placeholder from `article-langchain-alternative.md`
- [ ] Verify all GitHub links point to public repos
- [ ] Verify Streamlit app links are live
- [ ] Verify Gumroad product links are active
- [ ] Review each draft on Dev.to before setting `published: true`
