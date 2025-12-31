# Changelog

All notable changes to EnterpriseHub will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Reorganized test structure into `tests/unit/` and `tests/integration/`
- Archived historical reports to `_archive/` directory
- Created professional archive structure with README

## [0.2.0] - 2025-12-31

### Added
- **Margin Hunter**:
  - Goal Seek Calculator for reverse-engineering profit targets
  - Monte Carlo Simulation for stochastic profit risk analysis
  - Interactive Sensitivity Heatmaps for price vs. cost modeling
- **Financial Analyst**:
  - 10-year Discounted Cash Flow (DCF) Valuation Model
  - Professional PDF Statement Export with matplotlib formatting
  - Multi-variable Sensitivity Tables for intrinsic value
- **Market Pulse**:
  - Multi-Ticker Comparison for relative performance analysis
  - Advanced Indicators: Bollinger Bands and Average True Range (ATR)
- **Content Engine**:
  - Multi-Platform Adapter (LinkedIn, X, FB, Instagram, Email)
  - A/B Variant Generator (3 versions per post)
  - ML-powered Engagement Prediction scoring
- **Testing**:
  - Added 22 comprehensive unit tests for new financial and modeling features
  - Fixed Streamlit mocking issues in existing test suite

### Changed
- Updated design system with improved contrast and accessibility
- Refactored CVP calculations for high-performance vectorization

### Fixed
- Line length violations across all core modules
- Type hint violations in Margin Hunter
- Nested f-string syntax for Python < 3.12 compatibility
- Streamlit `st.columns` and `st.tabs` mocking in unit tests

## [0.1.0] - 2025-12-06

### Added
- **Priority 4 Completion**: All Tier 2 module enhancements
  - Financial Analyst: Claude-powered AI insights (health, risks, opportunities)
  - Market Pulse: Predictive indicators (trend prediction, support/resistance levels)
  - Agent Logic: Dual-mode sentiment analysis (TextBlob + Claude)
- **Code Quality Improvements**:
  - Retry logic with exponential backoff for API calls
  - 100% type hints across all modules
  - Comprehensive error handling
  - Strategic logging throughout
- **Testing Expansion**:
  - Expanded from 31 to 220+ tests (over 600% increase)
  - Edge case testing (rate limits, network failures)
  - Integration tests for API clients
- **Documentation**:
  - Added 116KB of new documentation
  - Module-specific READMEs (7 files, ~100 KB)
  - DEMO.md with 28 screenshot specifications
  - VIDEO-SCRIPT.md with 5 demo narrations
  - PORTFOLIO.md (34 KB job application showcase)
  - TESTIMONIALS.md template
- **Repository Cleanup** (176MB freed):
  - Removed cache directories (`.mypy_cache/`, `.pytest_cache/`, etc.)
  - Removed obsolete planning templates
  - Removed redundant reports

### Changed
- Updated Content Engine with retry logic and type hints
- Enhanced all modules with production-grade error handling
- Improved test organization and coverage

### Fixed
- API rate limit handling across all AI-integrated modules
- Graceful fallbacks when API keys are unavailable
- Consistent error messaging across modules

## [0.0.1] - 2025-11-30

### Added
- Initial release with 7 business modules:
  - Margin Hunter: CVP analysis with break-even calculations
  - Content Engine: AI-powered LinkedIn post generator
  - Data Detective: Statistical analysis and data profiling
  - Financial Analyst: Stock analysis with real-time data
  - Market Pulse: Technical analysis and charting
  - Marketing Analytics: Campaign performance tracking
  - Agent Logic: Sentiment analysis
- Streamlit web application with modular navigation
- Industry scenario templates (SaaS, E-commerce, Manufacturing)
- CI/CD pipeline with GitHub Actions
- Pre-commit hooks (Black, isort, flake8, mypy, bandit)
- Comprehensive documentation (README, CONTRIBUTING, SECURITY)
- MIT License

---

## Release Notes

### Version 0.1.0 Highlights

**Major Features:**
- AI-powered insights across 4 modules (Claude 3.5 Sonnet integration)
- Dual-mode architecture (free fallback + premium features)
- Production-grade testing (220+ tests, 85%+ coverage)
- Professional documentation (10,000+ words)

**Technical Improvements:**
- Type safety (100% type hints in new code)
- Retry logic (exponential backoff: 1s → 2s → 4s)
- Error handling (comprehensive, user-friendly)
- Logging (strategic, actionable)

**Repository Health:**
- Test coverage: 31 → 220+ tests (over 600% increase)
- Code quality: Production-ready
- Documentation: Portfolio-ready
- Clean codebase: 176MB cache removed

---

## Versioning Strategy

- **Major version (X.0.0)**: Breaking changes, major new features
- **Minor version (0.X.0)**: New features, backward compatible
- **Patch version (0.0.X)**: Bug fixes, minor improvements

## Links

- [Repository](https://github.com/ChunkyTortoise/enterprise-hub)
- [Issues](https://github.com/ChunkyTortoise/enterprise-hub/issues)
- [Latest Release](https://github.com/ChunkyTortoise/enterprise-hub/releases)

---

Last Updated: December 6, 2025
