# Scrape-and-Serve Proxy Rotation and Anti-Detection Guide

## Building Reliable, Respectful Web Scrapers

This guide covers proxy rotation strategies, anti-detection techniques, and best practices for building production scrapers that run reliably without getting blocked. Based on Scrape-and-Serve's architecture (300+ tests, 8 test files) with real configuration examples.

---

## Table of Contents

1. [Scraping Architecture Overview](#1-scraping-architecture-overview)
2. [YAML Configuration for Multi-Target Scraping](#2-yaml-configuration-for-multi-target-scraping)
3. [Proxy Rotation Strategies](#3-proxy-rotation-strategies)
4. [Anti-Detection Techniques](#4-anti-detection-techniques)
5. [Rate Limiting and Politeness](#5-rate-limiting-and-politeness)
6. [Change Detection with SHA-256](#6-change-detection-with-sha-256)
7. [Data Validation and Quality](#7-data-validation-and-quality)
8. [Error Handling and Resilience](#8-error-handling-and-resilience)
9. [Scheduling and Automation](#9-scheduling-and-automation)
10. [SEO Intelligence Extraction](#10-seo-intelligence-extraction)

---

## 1. Scraping Architecture Overview

Scrape-and-Serve uses an async architecture built on httpx and BeautifulSoup4:

```
YAML Config -> Target Parser -> Async HTTP Client (httpx) -> HTML Parser (BS4)
                                        |
                                        v
                                 CSS Selector Extraction -> Data Validation
                                        |
                                        v
                                 Change Detection (SHA-256) -> Price Monitor
                                        |
                                        v
                                 Scheduler (asyncio) -> Alerts + Export
```

### Core Components

```python
from scrape_and_serve.scraper import (
    ScrapeTarget,      # Single scraping target definition
    ScrapeResult,      # Result with items, hash, timestamp
    parse_config,      # YAML config -> ScrapeTarget list
    scrape_html,       # HTML + target -> structured data
    extract_fields,    # CSS selector -> field values
    clean_price,       # Price string -> float
)
```

---

## 2. YAML Configuration for Multi-Target Scraping

### Basic Configuration

```python
from scrape_and_serve.scraper import parse_config, ScrapeTarget

config = {
    "targets": [
        {
            "name": "product_catalog",
            "url": "https://example.com/products",
            "selector": ".product-card",  # CSS selector for items
            "fields": {
                "title": "h3.product-title",
                "price": ".price-current",
                "original_price": ".price-original",
                "rating": ".star-rating",
                "review_count": ".review-count",
                "image_href": "img.product-image",  # _href suffix extracts href/src
                "link_href": "a.product-link"
            },
            "headers": {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "Accept-Language": "en-US,en;q=0.9"
            }
        }
    ]
}

targets = parse_config(config)
```

### Multi-Page Configuration

```python
# Configure pagination
config = {
    "targets": [
        {
            "name": "paginated_catalog",
            "url": "https://example.com/products?page={page}",
            "selector": ".product-item",
            "fields": {
                "name": ".product-name",
                "price": ".product-price",
                "sku": "[data-sku]"
            }
        }
    ]
}

# Scrape across pages
all_items = []
for page in range(1, 20):
    target = targets[0]
    target_url = target.url.format(page=page)
    modified_target = ScrapeTarget(
        name=target.name,
        url=target_url,
        selector=target.selector,
        fields=target.fields,
        headers=target.headers
    )

    html = await fetch_page(modified_target.url, headers=modified_target.headers)
    result = scrape_html(html, modified_target)

    if not result.items:
        break  # No more pages

    all_items.extend(result.items)
    await asyncio.sleep(2)  # Polite delay between pages
```

### Field Extraction Patterns

```python
from scrape_and_serve.scraper import extract_fields
from bs4 import BeautifulSoup

# extract_fields handles two modes:
# 1. Text extraction (default): gets inner text
# 2. Attribute extraction: field names ending in _href get href attribute

fields = {
    "title": "h3.title",              # Gets text content
    "price": ".price",                 # Gets text content
    "link_href": "a.product-link",     # Gets href attribute
    "image_href": "img.thumb",         # Gets href (or src for images)
}

html = '<div><h3 class="title">Widget</h3><span class="price">$29.99</span></div>'
soup = BeautifulSoup(html, "html.parser")
element = soup.select_one("div")
result = extract_fields(element, fields)
# {"title": "Widget", "price": "$29.99", "link_href": "", "image_href": ""}
```

---

## 3. Proxy Rotation Strategies

### Round-Robin Proxy Pool

```python
import httpx
from itertools import cycle

class ProxyRotator:
    """Round-robin proxy rotation for distributed scraping."""

    def __init__(self, proxies: list[str]):
        self.proxy_cycle = cycle(proxies)
        self.proxies = proxies
        self.failures = {p: 0 for p in proxies}

    def get_next(self) -> str:
        """Get next proxy in rotation, skip failed proxies."""
        for _ in range(len(self.proxies)):
            proxy = next(self.proxy_cycle)
            if self.failures[proxy] < 3:  # Max 3 failures before skip
                return proxy
        raise RuntimeError("All proxies exhausted")

    def mark_failed(self, proxy: str):
        self.failures[proxy] += 1

    def mark_success(self, proxy: str):
        self.failures[proxy] = 0

# Usage with httpx
rotator = ProxyRotator([
    "http://proxy1.example.com:8080",
    "http://proxy2.example.com:8080",
    "http://proxy3.example.com:8080",
])

async def fetch_with_proxy(url: str, headers: dict) -> str:
    proxy = rotator.get_next()
    try:
        async with httpx.AsyncClient(proxy=proxy, timeout=30.0) as client:
            response = await client.get(url, headers=headers)
            rotator.mark_success(proxy)
            return response.text
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        rotator.mark_failed(proxy)
        raise
```

### Weighted Proxy Selection

```python
import random

class WeightedProxyPool:
    """Proxy selection weighted by success rate."""

    def __init__(self, proxies: list[str]):
        self.proxies = proxies
        self.success_count = {p: 1 for p in proxies}  # Start at 1 (Laplace smoothing)
        self.total_count = {p: 1 for p in proxies}

    def get_proxy(self) -> str:
        """Select proxy weighted by historical success rate."""
        weights = [
            self.success_count[p] / self.total_count[p]
            for p in self.proxies
        ]
        return random.choices(self.proxies, weights=weights, k=1)[0]

    def record_result(self, proxy: str, success: bool):
        self.total_count[proxy] += 1
        if success:
            self.success_count[proxy] += 1
```

### Proxy Provider Recommendations

| Provider Type | Cost | Speed | Reliability | Best For |
|--------------|------|-------|-------------|----------|
| Datacenter proxies | Low ($2-5/GB) | Fast | Medium | High-volume, non-sensitive |
| Residential proxies | Medium ($10-15/GB) | Medium | High | Anti-detection critical |
| ISP proxies | High ($20-30/GB) | Fast | Very High | Premium targets |
| Free proxies | Free | Slow | Very Low | Testing only |

---

## 4. Anti-Detection Techniques

### User-Agent Rotation

```python
import random

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

def random_headers() -> dict:
    """Generate realistic browser headers."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
```

### Request Timing Patterns

```python
import asyncio
import random

async def human_delay():
    """Simulate human browsing patterns with variable delays."""
    # Base delay: 2-5 seconds (human reading time)
    base = random.uniform(2.0, 5.0)

    # Occasional longer pause (thinking/distraction): 10% chance
    if random.random() < 0.10:
        base += random.uniform(5.0, 15.0)

    await asyncio.sleep(base)

async def scrape_with_human_timing(targets, fetch_fn):
    """Scrape targets with human-like timing."""
    results = []
    for target in targets:
        result = await fetch_fn(target)
        results.append(result)
        await human_delay()
    return results
```

### Session Management

```python
async def session_scrape(targets: list, max_per_session: int = 20):
    """Rotate sessions to avoid tracking."""
    session_count = 0

    async with httpx.AsyncClient(headers=random_headers()) as client:
        for i, target in enumerate(targets):
            if session_count >= max_per_session:
                # Start new session with new headers
                session_count = 0
                await asyncio.sleep(random.uniform(30, 60))  # Session gap

            response = await client.get(target.url)
            session_count += 1
            await human_delay()
```

### Fingerprint Diversification Checklist

| Technique | Implementation | Priority |
|-----------|----------------|----------|
| User-Agent rotation | Random from pool per session | High |
| Header order variation | Randomize non-critical headers | Medium |
| Request timing | 2-5s base + random variation | High |
| Session rotation | New client every 15-25 requests | Medium |
| Referer headers | Set realistic referer chains | Low |
| Cookie management | Accept cookies, clear per session | Medium |
| TLS fingerprint | Use different httpx configurations | Low |

---

## 5. Rate Limiting and Politeness

### Respectful Scraping Policy

```python
import asyncio
from dataclasses import dataclass

@dataclass
class PolitenessPolicy:
    """Configure polite scraping behavior per domain."""
    requests_per_minute: int = 10
    concurrent_requests: int = 2
    respect_robots_txt: bool = True
    retry_after_429: bool = True
    max_retries: int = 3

class PoliteClient:
    """Rate-limited, robots.txt-respecting HTTP client."""

    def __init__(self, policy: PolitenessPolicy):
        self.policy = policy
        self.semaphore = asyncio.Semaphore(policy.concurrent_requests)
        self.request_interval = 60.0 / policy.requests_per_minute
        self.last_request_time = 0

    async def fetch(self, url: str, headers: dict = None) -> str:
        async with self.semaphore:
            # Enforce rate limit
            elapsed = asyncio.get_event_loop().time() - self.last_request_time
            if elapsed < self.request_interval:
                await asyncio.sleep(self.request_interval - elapsed)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers or random_headers())

                if response.status_code == 429 and self.policy.retry_after_429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    await asyncio.sleep(retry_after)
                    response = await client.get(url, headers=headers or random_headers())

                self.last_request_time = asyncio.get_event_loop().time()
                return response.text
```

### Robots.txt Compliance

```python
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

class RobotsChecker:
    """Check robots.txt before scraping."""

    def __init__(self):
        self._parsers = {}

    def can_fetch(self, url: str, user_agent: str = "*") -> bool:
        domain = urlparse(url).netloc

        if domain not in self._parsers:
            parser = RobotFileParser()
            parser.set_url(f"https://{domain}/robots.txt")
            try:
                parser.read()
            except Exception:
                return True  # If we cannot read robots.txt, proceed
            self._parsers[domain] = parser

        return self._parsers[domain].can_fetch(user_agent, url)

# Usage
robots = RobotsChecker()
if robots.can_fetch(target.url):
    result = await scrape(target)
else:
    print(f"Blocked by robots.txt: {target.url}")
```

---

## 6. Change Detection with SHA-256

### How Scrape-and-Serve Detects Changes

```python
from scrape_and_serve.scraper import scrape_html

# Every ScrapeResult includes a content_hash
result = scrape_html(html, target)
print(result.content_hash)  # SHA-256 of extracted items

# Compare hashes between runs
previous_hash = load_previous_hash(target.name)
if result.content_hash != previous_hash:
    print("Page content changed!")
    process_changes(result)
    save_hash(target.name, result.content_hash)
else:
    print("No changes detected")
```

### Granular Change Detection

```python
import hashlib
import json

def detect_item_changes(current_items, previous_items):
    """Detect which specific items changed, were added, or removed."""

    # Hash each item individually
    def item_hash(item):
        return hashlib.sha256(json.dumps(item, sort_keys=True).encode()).hexdigest()

    current_hashes = {item_hash(i): i for i in current_items}
    previous_hashes = {item_hash(i): i for i in previous_items}

    added = {h: current_hashes[h] for h in current_hashes if h not in previous_hashes}
    removed = {h: previous_hashes[h] for h in previous_hashes if h not in current_hashes}
    unchanged = {h: current_hashes[h] for h in current_hashes if h in previous_hashes}

    return {
        "added": list(added.values()),
        "removed": list(removed.values()),
        "unchanged": list(unchanged.values()),
        "changed": len(added) > 0 or len(removed) > 0
    }
```

---

## 7. Data Validation and Quality

### Validation Rules

```python
from scrape_and_serve.validator import Validator, ValidationRule

validator = Validator()

# Type checking
validator.add_rules([
    ValidationRule(field="price", rule_type="type", expected_type="float"),
    ValidationRule(field="title", rule_type="type", expected_type="str"),
])

# Range validation
validator.add_rules([
    ValidationRule(field="price", rule_type="range", min_val=0.01, max_val=100000),
    ValidationRule(field="rating", rule_type="range", min_val=0, max_val=5),
])

# Regex validation
validator.add_rules([
    ValidationRule(field="sku", rule_type="regex", pattern=r"^[A-Z]{2}\d{6}$"),
    ValidationRule(field="url", rule_type="regex", pattern=r"^https?://"),
])

# Custom validation
validator.add_rules([
    ValidationRule(
        field="price",
        rule_type="custom",
        custom_fn=lambda v: v > 0 and v == round(v, 2)
    ),
])

# Validate all scraped items
for item in scraped_items:
    result = validator.validate(item)
    if not result.is_valid:
        log_validation_error(item, result.errors)
```

---

## 8. Error Handling and Resilience

### Retry with Exponential Backoff

```python
import asyncio
import random

async def fetch_with_retry(url, headers, max_retries=3):
    """Fetch URL with exponential backoff retry."""

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    return response.text
                elif response.status_code == 429:
                    wait = int(response.headers.get("Retry-After", 2 ** attempt * 10))
                    await asyncio.sleep(wait)
                elif response.status_code >= 500:
                    await asyncio.sleep(2 ** attempt + random.random())
                else:
                    return None  # 404, 403, etc.

        except (httpx.TimeoutException, httpx.ConnectError):
            await asyncio.sleep(2 ** attempt + random.random())

    return None  # All retries exhausted
```

---

## 9. Scheduling and Automation

### Production Scheduling with Scrape-and-Serve

```python
from scrape_and_serve.scheduler import Scheduler, JobConfig

scheduler = Scheduler()

# Configure jobs with different intervals
jobs = [
    JobConfig(name="price_monitor", target=price_targets,
             interval_hours=6, callback=process_prices),
    JobConfig(name="new_listings", target=listing_targets,
             interval_hours=1, callback=process_listings),
    JobConfig(name="seo_audit", target=seo_targets,
             interval_hours=168, callback=process_seo),  # Weekly
]

for job in jobs:
    scheduler.add_job(job)

# Monitor job status
for status in scheduler.get_status():
    print(f"{status.name}: runs={status.run_count}, "
          f"last={status.last_run}, errors={status.error_count}")

# Start scheduler
await scheduler.start()
```

---

## 10. SEO Intelligence Extraction

### Competitive SEO Analysis

```python
from scrape_and_serve.seo_content import score_content, analyze_keyword, keyword_density
from scrape_and_serve.seo_analyzer import SEOAnalyzer

# Analyze competitor content
for competitor_page in competitor_pages:
    score = score_content(
        content=competitor_page.text,
        keywords=target_keywords,
        meta_description=competitor_page.meta
    )

    print(f"Competitor: {competitor_page.url}")
    print(f"  SEO Score: {score.total_score}/100")
    print(f"  Word Count: {score.word_count}")
    print(f"  Readability: {score.readability_grade}")
    print(f"  Keyword Density:")
    for kw in score.keyword_scores:
        print(f"    '{kw.keyword}': {kw.density:.2f}%")
```

### Content Gap Analysis

```python
analyzer = SEOAnalyzer()

# Find keywords competitors rank for that we do not
gaps = analyzer.content_gap_analysis(
    our_content=our_page,
    competitor_contents=[comp1, comp2, comp3],
    keywords=industry_keywords
)

for gap in gaps:
    print(f"Missing keyword: '{gap.keyword}' "
          f"(competitors avg density: {gap.competitor_avg:.2f}%, ours: {gap.our_density:.2f}%)")
```

---

## Production Checklist

- [ ] **Proxy rotation**: Configure pool with at least 5 proxies
- [ ] **User-Agent rotation**: Pool of 5+ current browser UAs
- [ ] **Rate limiting**: 10-30 req/min per domain
- [ ] **Robots.txt**: Check before scraping any new domain
- [ ] **Error handling**: Retry with exponential backoff
- [ ] **Data validation**: Rules for every extracted field
- [ ] **Change detection**: SHA-256 hashing to avoid re-processing
- [ ] **Scheduling**: Asyncio scheduler with status tracking
- [ ] **Alerting**: Price change and error alerts configured
- [ ] **Export**: CSV/JSON export for downstream analytics

---

## About Scrape-and-Serve

Scrape-and-Serve provides 300+ automated tests across 8 test files (scraper, price monitor, Excel converter, SEO content, SEO analyzer, diff visualizer, scheduler, validator). All tests run without network access using mock HTTP responses.

- **Repository**: [github.com/ChunkyTortoise/scrape-and-serve](https://github.com/ChunkyTortoise/scrape-and-serve)
- **Live Demo**: [ct-scrape-and-serve.streamlit.app](https://ct-scrape-and-serve.streamlit.app)
- **HTTP Client**: httpx (async)
- **Parser**: BeautifulSoup4
- **Config**: YAML-based target definitions
- **Tests**: 300+ (all mocked, no network access)
