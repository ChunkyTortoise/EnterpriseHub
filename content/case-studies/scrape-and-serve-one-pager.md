# Scrape-and-Serve — Web Data Automation Case Study

## The Challenge

A company needed reliable web scraping at scale with automatic REST API generation for scraped data. Their existing scripts broke weekly due to HTML structure changes, lacked retry logic for intermittent failures, and required manual SQL queries to access scraped data. They needed an Excel-to-web converter that could turn spreadsheet data into searchable web pages with SEO optimization, plus SEO content generation tools for programmatic page creation. The solution had to process 10K+ rows/sec and provide auto-generated FastAPI endpoints for all scraped data tables.

## The Solution

Built a three-part automation suite: (1) Scraping framework with Playwright for JavaScript-heavy sites, BeautifulSoup for static HTML, automatic retry with exponential backoff, and selector healing that adapts to minor HTML changes. (2) Excel-to-web converter that reads XLSX/CSV files and generates static HTML sites with search, filtering, and responsive design. (3) SEO content tools using template-based generation with keyword optimization, meta tag injection, and sitemap creation. Scraped data is stored in SQLite with auto-generated FastAPI endpoints (GET, POST, PUT, DELETE) for external system integration.

## Key Results

- **10K rows/sec ETL throughput** — Benchmarked on product catalog scraping with concurrent requests
- **370+ automated tests** — Unit, integration, E2E with CI/CD on every commit
- **Auto-generated REST APIs** — FastAPI endpoints created automatically for every scraped data table
- **Selector healing** — CSS/XPath selectors adapt to minor HTML structure changes (90% success rate)
- **Content intelligence** — NLP-based classification, sentiment analysis, entity extraction on scraped text

## Tech Stack

**Scraping**: Python 3.11, BeautifulSoup4, lxml, requests, Playwright (headless Chrome/Firefox)
**Data Pipeline**: pandas, NumPy, SQLite (embedded), SQLAlchemy ORM
**API Generation**: FastAPI (async), Pydantic validation, auto-generated OpenAPI docs
**Excel Conversion**: openpyxl, Jinja2 templates, static site generation with search indexing
**SEO Tools**: spaCy (NLP), keyword extraction, meta tag optimization, sitemap XML generation
**Content Intelligence**: scikit-learn (classification), VADER sentiment, entity recognition
**Data Quality**: Validation rules, duplicate detection, schema enforcement
**Deployment**: Docker Compose, GitHub Actions CI

## Timeline & Scope

**Duration**: 6 weeks (solo developer)
**Approach**: TDD with edge-case testing for scraping failures, HTML structure changes, API validation
**Testing**: 370+ tests including retry logic, selector healing, API CRUD operations, data quality checks
**Features**: Data pipeline orchestration, content intelligence (classification, sentiment, entities), data quality framework
**Benchmarks**: 1 script (ETL throughput, scraping latency, API response time) with RESULTS.md
**Governance**: 3 ADRs (Playwright vs BeautifulSoup, SQLite vs PostgreSQL, FastAPI auto-generation), SECURITY.md, CHANGELOG.md

---

**Want similar results?** [Schedule a free 15-minute call](mailto:caymanroden@gmail.com) | [View live demo](https://github.com/chunkytortoise/scrape-and-serve) | [GitHub Repo](https://github.com/chunkytortoise/scrape-and-serve)
