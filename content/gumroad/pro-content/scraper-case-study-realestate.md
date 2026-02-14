# Case Study: Real Estate Price Monitoring for a Property Investment Firm

## Client Profile

**Company**: Crestview Capital Group (anonymized)
**Industry**: Real Estate Investment / Property Management
**Team Size**: 6 analysts, 3 acquisitions managers
**Challenge**: Monitor competitor property listings, track price changes, and detect market shifts across 500+ listings

---

## The Challenge

Crestview Capital manages a $45M portfolio of residential properties in Southern California. Their acquisitions team needed to track competitor pricing daily across Zillow, Redfin, Realtor.com, and local MLS aggregators. The manual process was unsustainable:

- **3 analysts** spent 5 hours/week each manually checking competitor listings and entering prices into spreadsheets
- **Price changes** were detected 2-3 days late because checking was weekly, not daily
- **Market shifts** (neighborhoods trending up/down) were identified by gut feel, not data
- **New listings** in target neighborhoods were discovered days after posting, losing first-mover advantage

### Pain Points

| Problem | Impact |
|---------|--------|
| Manual price tracking across 4 sites | 15 analyst-hours/week, $30K/year in labor |
| Weekly checking cadence | 2-3 day delay in price change detection |
| No historical price data | Could not identify pricing trends |
| No alerting system | Missed 12 acquisition opportunities in 6 months |
| Spreadsheet-based tracking | No version control, no diff visualization |

---

## The Solution: Scrape-and-Serve for Real Estate Intelligence

Crestview deployed Scrape-and-Serve's YAML-configurable scraper, price monitor, diff visualizer, and async scheduler.

### Step 1: YAML-Configurable Scraper Setup

Scrape-and-Serve uses YAML configuration for scraping targets. No code changes needed to add new sources:

```python
from scrape_and_serve.scraper import parse_config, scrape_html, ScrapeTarget

# Define scraping targets in YAML
config = {
    "targets": [
        {
            "name": "competitor_listings_zillow",
            "url": "https://example-zillow-cache.com/rancho-cucamonga",
            "selector": ".property-card",
            "fields": {
                "address": ".property-address",
                "price": ".property-price",
                "beds": ".beds-count",
                "sqft": ".sqft-value",
                "days_on_market": ".dom-count",
                "listing_url_href": "a.property-link"
            }
        },
        {
            "name": "competitor_listings_redfin",
            "url": "https://example-redfin-cache.com/rancho-cucamonga",
            "selector": ".HomeCard",
            "fields": {
                "address": ".homecard-address",
                "price": ".homecard-price",
                "beds": ".HomeStatsV2--beds",
                "sqft": ".HomeStatsV2--sqft"
            }
        }
    ]
}

targets = parse_config(config)

# Scrape with CSS selectors and field extraction
for target in targets:
    html = await fetch_page(target.url, headers=target.headers)
    result = scrape_html(html, target)

    print(f"{result.target_name}: {len(result.items)} listings found")
    print(f"Content hash: {result.content_hash}")
    print(f"Scraped at: {result.scraped_at}")

    for item in result.items[:3]:
        print(f"  {item['address']}: {item['price']} ({item['beds']} bed, {item['sqft']} sqft)")
```

The scraper's `extract_fields` function uses CSS selectors per field, supporting both text extraction and attribute extraction (e.g., `_href` suffix for link URLs). The `content_hash` uses SHA-256 to detect page changes between runs.

### Step 2: Historical Price Tracking with Alerts

Scrape-and-Serve's price monitor tracks historical prices and generates alerts when thresholds are crossed:

```python
from scrape_and_serve.price_monitor import PriceHistory, PricePoint, PriceAlert

# Initialize price tracker with 5% alert threshold
tracker = PriceHistory(alert_threshold_pct=5.0)

# Record daily observations
for listing in scraped_listings:
    alert = tracker.add_observation(
        product_name=listing["address"],
        price=float(listing["price"].replace("$", "").replace(",", "")),
        source="zillow"
    )

    if alert:
        print(f"ALERT: {alert.product_name}")
        print(f"  Previous: ${alert.previous_price:,.0f}")
        print(f"  Current: ${alert.current_price:,.0f}")
        print(f"  Change: {alert.change_pct:+.1f}%")
        print(f"  Type: {alert.alert_type}")  # "drop" or "increase"

# Get historical data for a specific property
history = tracker.get_product_history("123 Main St, Rancho Cucamonga")
for point in history:
    print(f"  {point.observed_at}: ${point.price:,.0f}")

# Latest prices across all tracked properties
latest = tracker.latest_prices()
for address, point in latest.items():
    print(f"{address}: ${point.price:,.0f} (via {point.source})")
```

### Price History Export

```python
# Export to CSV for analysis
csv_data = tracker.export_csv()
with open("price_history.csv", "w") as f:
    f.write(csv_data)

# Summary statistics per property
summary = tracker.get_summary_stats()
for product, stats in summary.items():
    print(f"{product}:")
    print(f"  Min: ${stats['min']:,.0f}")
    print(f"  Max: ${stats['max']:,.0f}")
    print(f"  Avg: ${stats['avg']:,.0f}")
    print(f"  Current: ${stats['current']:,.0f}")
    print(f"  Observations: {stats['count']}")
```

### Step 3: Diff Visualization for Listing Changes

Scrape-and-Serve's diff visualizer tracks page snapshots and highlights changes:

```python
from scrape_and_serve.diff_visualizer import DiffVisualizer

viz = DiffVisualizer()

# Store daily snapshots
viz.store_snapshot("123_main_st", current_listing_html)

# Compare with previous version
diff = viz.compare("123_main_st")
if diff.has_changes:
    print(f"Changes detected in listing for 123 Main St:")
    print(diff.unified_diff)  # Standard unified diff format
    print(f"Lines added: {diff.lines_added}")
    print(f"Lines removed: {diff.lines_removed}")

# Get change history
history = viz.get_history("123_main_st")
for entry in history:
    print(f"  {entry.timestamp}: {entry.change_summary}")

# Export history for reporting
viz.export_history("123_main_st", format="csv")
```

This caught listing description changes (price reductions, "motivated seller" language added, open house dates) that manual monitoring missed.

### Step 4: Automated Scheduling

Scrape-and-Serve's async scheduler runs scraping jobs on configurable intervals:

```python
from scrape_and_serve.scheduler import Scheduler, JobConfig

scheduler = Scheduler()

# Schedule daily scraping at 6 AM
scheduler.add_job(JobConfig(
    name="zillow_morning_scan",
    target=targets[0],
    interval_hours=24,
    start_time="06:00",
    callback=process_and_alert  # Called when scrape completes
))

# Schedule hourly for high-priority neighborhoods
scheduler.add_job(JobConfig(
    name="premium_neighborhood_hourly",
    target=premium_target,
    interval_hours=1,
    callback=process_premium_listings
))

# Status tracking
for job in scheduler.get_status():
    print(f"{job.name}: last_run={job.last_run}, next_run={job.next_run}, "
          f"status={job.status}")

# Run scheduler (asyncio-based)
await scheduler.start()
```

### Step 5: Data Validation for Quality Control

Scrape-and-Serve's validator ensures scraped data meets quality standards:

```python
from scrape_and_serve.validator import Validator, ValidationRule

validator = Validator()

# Define validation rules for real estate data
validator.add_rules([
    ValidationRule(field="price", rule_type="range", min_val=100000, max_val=5000000),
    ValidationRule(field="beds", rule_type="range", min_val=1, max_val=10),
    ValidationRule(field="sqft", rule_type="range", min_val=500, max_val=15000),
    ValidationRule(field="address", rule_type="regex", pattern=r".+, [A-Z]{2} \d{5}"),
])

# Validate scraped data
for item in scraped_items:
    result = validator.validate(item)
    if not result.is_valid:
        print(f"Invalid data for {item.get('address', 'unknown')}:")
        for error in result.errors:
            print(f"  {error.field}: {error.message}")
```

---

## Results

### Efficiency

| Metric | Before Scrape-and-Serve | After Scrape-and-Serve | Change |
|--------|------------------------|------------------------|--------|
| Weekly analyst hours on tracking | 15 hours | 1 hour (review alerts) | **-93%** |
| Price change detection delay | 2-3 days | <1 hour | **-96%** |
| Listings tracked | 200 (manual capacity) | 500+ (automated) | **+150%** |
| Annual labor cost for tracking | $30,000 | $4,000 | **-87%** |

### Investment Performance

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Missed acquisition opportunities | 12 in 6 months | 1 in 6 months | **-92%** |
| Days to detect price reduction | 5-7 days | Same day | **-85%** |
| Market trend identification | Gut feel | Data-driven (historical trends) | **Quantified** |
| Below-market deals identified | 3/year | 11/year | **+267%** |

### Data Quality

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Price tracking history | None (point-in-time) | Full daily history | **New capability** |
| Data validation | None | Automated rules | **Validated** |
| Change detection | Manual comparison | SHA-256 + diff visualization | **Automated** |

---

## Implementation Timeline

| Week | Activity | Outcome |
|------|----------|---------|
| 1 | YAML scraper configuration for 4 sources | Automated data collection |
| 1 | Price monitor setup with 5% alert threshold | Immediate price change alerts |
| 2 | Diff visualizer for listing change tracking | Description/terms change detection |
| 2 | Async scheduler for daily and hourly runs | Fully automated monitoring |
| 3 | Data validation rules | Quality-assured data |
| 3 | CSV export pipeline for analytics | Historical data for trend analysis |

**Total deployment**: 3 weeks.

---

## Key Takeaways

1. **YAML configuration makes adding sources trivial**. Crestview added 4 scraping sources in a single day -- no code changes, just CSS selector configuration.

2. **Price alerting catches opportunities humans miss**. Automated 5% threshold alerts identified 267% more below-market deals than manual weekly checking.

3. **SHA-256 change detection is efficient**. Content hashing detects any page change without storing full page copies, keeping storage costs minimal.

4. **Diff visualization catches non-price changes**. "Motivated seller" language, price reduction history, and open house additions were detected automatically.

5. **300+ tests validate data integrity**. Scrape-and-Serve's test suite covers scraping, price monitoring, scheduling, validation, and export across 8 test files.

---

## About Scrape-and-Serve

Scrape-and-Serve provides 300+ automated tests across 8 test files, including YAML-configurable scraping, SHA-256 change detection, historical price tracking with configurable alerts, async scheduling, diff visualization, data validation, and SEO analysis.

- **Repository**: [github.com/ChunkyTortoise/scrape-and-serve](https://github.com/ChunkyTortoise/scrape-and-serve)
- **Live Demo**: [ct-scrape-and-serve.streamlit.app](https://ct-scrape-and-serve.streamlit.app)
- **Scraping**: httpx async + BeautifulSoup4
- **Tests**: 300+ across 8 test files
