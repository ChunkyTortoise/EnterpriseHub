# Case Study: E-Commerce Competitive Intelligence with Automated Price Monitoring

## Client Profile

**Company**: PrimeShelf (anonymized)
**Industry**: E-Commerce / Consumer Electronics
**Team Size**: 2 data analysts, 4 category managers
**Challenge**: Monitor competitor pricing across 2,000 SKUs daily and optimize pricing strategy with real-time intelligence

---

## The Challenge

PrimeShelf sells consumer electronics through their own website and Amazon. With 2,000 active SKUs and 8 direct competitors, their pricing team was drowning in manual work:

- **Category managers** manually checked 3 competitor sites daily for their top 200 products (the other 1,800 went unmonitored)
- **Price changes** by competitors triggered reactive responses 2-3 days late
- **No historical data** meant they could not distinguish temporary promotions from permanent price drops
- **SEO rankings** for product pages were declining but no one had time to diagnose why
- **Excel-based pricing** spreadsheets were the source of truth, with no version control or audit trail

### Pain Points

| Problem | Impact |
|---------|--------|
| Only 10% of SKUs monitored | 1,800 SKUs had zero competitive intelligence |
| 2-3 day price reaction time | Lost 15% of competitive bids to faster-reacting competitors |
| No historical pricing data | Could not distinguish sales from permanent repricing |
| Declining SEO rankings | 23% traffic drop in 6 months with no diagnosis |
| Excel as source of truth | Version conflicts, no audit trail |

---

## The Solution: Scrape-and-Serve for Competitive Intelligence

PrimeShelf deployed the full Scrape-and-Serve toolkit: scraper, price monitor, SEO analyzer, and Excel converter.

### Step 1: YAML-Configurable Multi-Competitor Scraping

Scrape-and-Serve's YAML configuration made it trivial to add all 8 competitors:

```python
from scrape_and_serve.scraper import parse_config, scrape_html, ScrapeTarget, ScrapeResult

config = {
    "targets": [
        {
            "name": "competitor_a_electronics",
            "url": "https://competitor-a.example.com/electronics",
            "selector": ".product-item",
            "fields": {
                "name": ".product-name",
                "price": ".product-price",
                "sku": ".product-sku",
                "stock_status": ".stock-indicator",
                "rating": ".star-rating",
                "review_count": ".review-count"
            },
            "headers": {
                "User-Agent": "Mozilla/5.0 (compatible; PriceBot/1.0)"
            }
        },
        # ... 7 more competitor targets
    ]
}

targets = parse_config(config)

# Scrape all competitors
results = {}
for target in targets:
    html = await fetch_page(target.url, headers=target.headers)
    result = scrape_html(html, target)
    results[target.name] = result

    print(f"{target.name}: {len(result.items)} products, hash={result.content_hash[:12]}")
```

The field extraction supports CSS selectors per field. For price fields, Scrape-and-Serve automatically handles currency symbols, commas, and whitespace through the `clean_price` utility:

```python
from scrape_and_serve.scraper import clean_price

# Handles various price formats
assert clean_price("$1,299.99") == 1299.99
assert clean_price("USD 1299.99") == 1299.99
assert clean_price("1,299") == 1299.0
```

### Step 2: Automated Price Monitoring with Tiered Alerts

PrimeShelf configured different alert thresholds for different product categories:

```python
from scrape_and_serve.price_monitor import PriceHistory, PriceAlert

# Premium products: alert on 3% change
premium_tracker = PriceHistory(alert_threshold_pct=3.0)

# Budget products: alert on 8% change (more volatile)
budget_tracker = PriceHistory(alert_threshold_pct=8.0)

# Process scraped data
for result in results.values():
    for item in result.items:
        price = clean_price(item["price"])
        category = categorize_product(item["sku"])

        tracker = premium_tracker if category == "premium" else budget_tracker

        alert = tracker.add_observation(
            product_name=item["sku"],
            price=price,
            source=result.target_name
        )

        if alert:
            # Immediate notification to category manager
            notify_category_manager(
                sku=alert.product_name,
                competitor=alert.source,
                old_price=alert.previous_price,
                new_price=alert.current_price,
                change_pct=alert.change_pct,
                alert_type=alert.alert_type
            )
```

### Cross-Competitor Price Comparison

```python
# Get latest prices across all competitors for a SKU
def price_comparison(sku: str, trackers: dict) -> dict:
    """Compare current prices for a SKU across all competitors."""
    prices = {}
    for source, tracker in trackers.items():
        history = tracker.get_product_history(sku)
        if history:
            latest = history[-1]
            prices[source] = {
                "price": latest.price,
                "observed_at": latest.observed_at,
            }

    # Calculate position
    sorted_prices = sorted(prices.items(), key=lambda x: x[1]["price"])
    for rank, (source, data) in enumerate(sorted_prices, 1):
        data["rank"] = rank
        data["vs_cheapest"] = (
            (data["price"] - sorted_prices[0][1]["price"])
            / sorted_prices[0][1]["price"] * 100
        )

    return prices
```

### Step 3: SEO Analysis for Product Pages

PrimeShelf's traffic had dropped 23% in 6 months. Scrape-and-Serve's SEO analyzer diagnosed the issues:

```python
from scrape_and_serve.seo_content import score_content, analyze_keyword, ContentOutline

# Score existing product page
page_content = fetch_product_page("widget-pro-x")

score = score_content(
    content=page_content,
    keywords=["wireless headphones", "noise cancelling", "bluetooth"],
    meta_description="Buy the WidgetPro X - premium wireless headphones"
)

print(f"SEO Score: {score.total_score}/100")
print(f"Word count: {score.word_count}")
print(f"Heading count: {score.heading_count}")
print(f"Readability grade: {score.readability_grade:.1f}")

print("\nKeyword Analysis:")
for kw in score.keyword_scores:
    print(f"  '{kw.keyword}': density={kw.density:.2f}%, "
          f"in_title={kw.in_title}, in_first_para={kw.in_first_paragraph}")

print("\nIssues:")
for issue in score.issues:
    print(f"  - {issue}")

print("\nSuggestions:")
for suggestion in score.suggestions:
    print(f"  + {suggestion}")
```

### Advanced SEO Analysis

```python
from scrape_and_serve.seo_analyzer import SEOAnalyzer

analyzer = SEOAnalyzer()

# Compare our page against top competitor
comparison = analyzer.compare_content(
    our_content=our_page_html,
    competitor_content=competitor_page_html,
    keywords=["wireless headphones"]
)

print(f"Our SEO score: {comparison.our_score}")
print(f"Competitor SEO score: {comparison.competitor_score}")
print(f"Gap areas: {comparison.gaps}")

# Get keyword suggestions
suggestions = analyzer.suggest_keywords(page_content)
for kw in suggestions:
    print(f"  Suggested: '{kw.keyword}' (relevance: {kw.score:.2f})")

# Technical SEO issues
issues = analyzer.technical_audit(page_html)
for issue in issues:
    print(f"  Technical issue: {issue.description} (severity: {issue.severity})")
```

The SEO analysis revealed that PrimeShelf's product pages had thin content (avg 120 words vs competitor avg 800 words), missing meta descriptions on 40% of pages, and keyword density below 0.5% for target terms.

### Step 4: Excel-to-Web Migration

PrimeShelf's pricing spreadsheet was replaced with a web application:

```python
from scrape_and_serve.excel_converter import ExcelConverter

converter = ExcelConverter()

# Convert pricing spreadsheet to web app
result = converter.convert(
    file_path="pricing_master.xlsx",
    output_db="pricing.db"  # SQLite database
)

print(f"Detected schema: {result.schema}")
print(f"Rows imported: {result.row_count}")
print(f"Columns: {result.column_count}")
print(f"SQLite database: {result.db_path}")

# Auto-generated Streamlit CRUD app
crud_code = converter.generate_streamlit_app(result.schema)
# Produces a complete Streamlit app with:
# - Data table with sorting/filtering
# - Add/edit/delete forms
# - Search functionality
# - CSV export
```

### Step 5: Scheduled Monitoring Pipeline

```python
from scrape_and_serve.scheduler import Scheduler, JobConfig

scheduler = Scheduler()

# Morning scan: all competitors, all categories
scheduler.add_job(JobConfig(
    name="morning_full_scan",
    target=all_competitor_targets,
    interval_hours=24,
    start_time="06:00",
    callback=process_morning_results
))

# Midday check: premium products only (more volatile)
scheduler.add_job(JobConfig(
    name="midday_premium_check",
    target=premium_targets,
    interval_hours=12,
    start_time="12:00",
    callback=process_premium_alerts
))

# Hourly check: flash sale detection
scheduler.add_job(JobConfig(
    name="flash_sale_detection",
    target=flash_sale_targets,
    interval_hours=1,
    callback=detect_flash_sales
))

await scheduler.start()
```

---

## Results

### Competitive Intelligence

| Metric | Before Scrape-and-Serve | After Scrape-and-Serve | Change |
|--------|------------------------|------------------------|--------|
| SKUs monitored | 200 (10%) | 2,000 (100%) | **+900%** |
| Competitors tracked | 3 (manual) | 8 (automated) | **+167%** |
| Price reaction time | 2-3 days | <2 hours | **-96%** |
| Analyst hours/week on tracking | 20 hours | 3 hours | **-85%** |

### Revenue Impact

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Competitive bid win rate | 42% | 58% | **+38%** |
| Price-match response rate | 35% within 24h | 95% within 2h | **+171%** |
| Revenue from price optimization | Baseline | +$340K/year | **Significant** |
| Flash sale detection | 0% (missed) | 90% caught same-hour | **New capability** |

### SEO Recovery

| Metric | Before | After (3 months) | Change |
|--------|--------|-------------------|--------|
| Average page SEO score | 32/100 | 74/100 | **+131%** |
| Organic traffic | -23% (declining) | +18% (recovering) | **+41% swing** |
| Pages with meta descriptions | 60% | 98% | **+63%** |
| Average content word count | 120 words | 650 words | **+442%** |

---

## Implementation Timeline

| Week | Activity | Outcome |
|------|----------|---------|
| 1 | YAML configuration for 8 competitors | Automated scraping active |
| 1 | Price monitor with tiered alert thresholds | Real-time price change alerts |
| 2 | SEO analysis for top 50 product pages | Issues diagnosed, fix plan created |
| 2 | Excel converter for pricing spreadsheet | Web-based pricing management |
| 3 | Scheduler configuration (daily + hourly) | Fully automated monitoring |
| 3 | Data validation and CSV export pipeline | Quality-assured data feeds |

**Total deployment**: 3 weeks.

---

## Key Takeaways

1. **YAML configuration scales to any number of competitors**. Adding a new competitor takes 10 minutes of CSS selector configuration, not days of development.

2. **Tiered alert thresholds reduce noise**. Premium products at 3% vs budget products at 8% prevented alert fatigue while catching meaningful changes.

3. **SEO analysis reveals invisible traffic losses**. The 23% traffic drop was caused by thin content and missing meta descriptions -- issues invisible without systematic analysis.

4. **Excel-to-web migration eliminates version conflicts**. A single source of truth with CRUD interface replaced emailed spreadsheet chaos.

5. **300+ tests ensure scraping reliability**. Validation rules catch malformed data before it enters the pricing system, preventing bad decisions from bad data.

---

## About Scrape-and-Serve

Scrape-and-Serve provides 300+ automated tests across 8 test files, with YAML-configurable scraping, SHA-256 change detection, historical price tracking, async scheduling, SEO analysis (5-dimension scoring), diff visualization, Excel-to-web conversion, and data validation.

- **Repository**: [github.com/ChunkyTortoise/scrape-and-serve](https://github.com/ChunkyTortoise/scrape-and-serve)
- **Live Demo**: [ct-scrape-and-serve.streamlit.app](https://ct-scrape-and-serve.streamlit.app)
- **Scraping**: httpx (async) + BeautifulSoup4
- **Config**: YAML-based, no code changes needed
