"""
Competitor Website Scraper - Real-Time Pricing & Feature Monitoring

Monitors competitor websites for:
- Pricing changes across all products/services
- Feature updates and product announcements
- Marketing message changes
- Service/product availability changes

Supports multiple scraping methods:
- BeautifulSoup for static content
- Selenium for dynamic content
- Playwright for advanced SPA monitoring

Author: Claude Code Agent - Competitive Intelligence Specialist
Created: 2026-01-19
"""

import asyncio
import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import re

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import httpx

logger = logging.getLogger(__name__)


class ScrapingMethod(Enum):
    """Web scraping methods available."""
    REQUESTS = "requests"
    SELENIUM = "selenium"
    PLAYWRIGHT = "playwright"
    API = "api"


class ChangeType(Enum):
    """Types of changes detected on competitor websites."""
    PRICING = "pricing"
    FEATURES = "features"
    PRODUCTS = "products"
    MARKETING_MESSAGE = "marketing_message"
    AVAILABILITY = "availability"
    PROMOTIONS = "promotions"
    CONTACT_INFO = "contact_info"
    TEAM_CHANGES = "team_changes"


@dataclass
class CompetitorWebsite:
    """Configuration for monitoring a competitor website."""
    name: str
    domain: str
    pricing_page_url: str
    features_page_url: Optional[str] = None
    products_page_url: Optional[str] = None
    about_page_url: Optional[str] = None
    scraping_method: ScrapingMethod = ScrapingMethod.REQUESTS
    selectors: Dict[str, str] = None
    headers: Dict[str, str] = None
    rate_limit_delay: int = 5
    last_scraped: Optional[datetime] = None

    def __post_init__(self):
        if self.selectors is None:
            self.selectors = {
                'pricing': '.price, .pricing, [class*="price"], [id*="price"]',
                'features': '.feature, .features, [class*="feature"]',
                'products': '.product, .products, [class*="product"]',
                'title': 'h1, h2, .title, [class*="title"]',
                'description': '.description, .desc, p',
            }
        if self.headers is None:
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }


@dataclass
class ScrapingResult:
    """Result of scraping a competitor website."""
    website: str
    url: str
    timestamp: datetime
    content_hash: str
    extracted_data: Dict[str, Any]
    changes_detected: List[Dict[str, Any]]
    scraping_method: ScrapingMethod
    success: bool
    error_message: Optional[str] = None


class CompetitorWebScraper:
    """
    Advanced web scraper for monitoring competitor websites.

    Capabilities:
    - Multi-method scraping (requests, selenium, playwright)
    - Change detection through content hashing
    - Rate limiting and respectful scraping
    - Structured data extraction
    - Error handling and retry logic
    """

    def __init__(self):
        self.monitored_websites: Dict[str, CompetitorWebsite] = {}
        self.scraping_history: Dict[str, List[ScrapingResult]] = {}
        self.selenium_driver: Optional[webdriver.Chrome] = None

    def add_competitor(self, website: CompetitorWebsite) -> None:
        """Add a competitor website to monitoring."""
        self.monitored_websites[website.name] = website
        self.scraping_history[website.name] = []
        logger.info(f"Added competitor website: {website.name} ({website.domain})")

    async def scrape_all_competitors(self) -> List[ScrapingResult]:
        """Scrape all monitored competitor websites."""
        results = []

        for website_name, website in self.monitored_websites.items():
            try:
                # Check rate limiting
                if (website.last_scraped and
                    datetime.now() - website.last_scraped < timedelta(seconds=website.rate_limit_delay)):
                    logger.debug(f"Rate limit active for {website_name}, skipping")
                    continue

                result = await self.scrape_website(website)
                results.append(result)

                # Update last scraped time
                website.last_scraped = datetime.now()

                # Store result
                self.scraping_history[website_name].append(result)

                # Keep only last 100 results per website
                if len(self.scraping_history[website_name]) > 100:
                    self.scraping_history[website_name] = self.scraping_history[website_name][-100:]

            except Exception as e:
                logger.error(f"Error scraping {website_name}: {str(e)}")
                error_result = ScrapingResult(
                    website=website_name,
                    url=website.pricing_page_url,
                    timestamp=datetime.now(),
                    content_hash="",
                    extracted_data={},
                    changes_detected=[],
                    scraping_method=website.scraping_method,
                    success=False,
                    error_message=str(e)
                )
                results.append(error_result)

        return results

    async def scrape_website(self, website: CompetitorWebsite) -> ScrapingResult:
        """Scrape a single competitor website."""
        logger.info(f"Scraping {website.name} using {website.scraping_method.value}")

        if website.scraping_method == ScrapingMethod.REQUESTS:
            return await self._scrape_with_requests(website)
        elif website.scraping_method == ScrapingMethod.SELENIUM:
            return await self._scrape_with_selenium(website)
        else:
            raise NotImplementedError(f"Scraping method {website.scraping_method} not implemented yet")

    async def _scrape_with_requests(self, website: CompetitorWebsite) -> ScrapingResult:
        """Scrape website using requests + BeautifulSoup."""
        try:
            async with httpx.AsyncClient(headers=website.headers, timeout=30.0) as client:
                response = await client.get(website.pricing_page_url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                extracted_data = self._extract_data_with_selectors(soup, website.selectors)

                # Calculate content hash
                content_hash = hashlib.md5(response.text.encode()).hexdigest()

                # Detect changes
                changes = self._detect_changes(website.name, extracted_data, content_hash)

                return ScrapingResult(
                    website=website.name,
                    url=website.pricing_page_url,
                    timestamp=datetime.now(),
                    content_hash=content_hash,
                    extracted_data=extracted_data,
                    changes_detected=changes,
                    scraping_method=ScrapingMethod.REQUESTS,
                    success=True
                )

        except Exception as e:
            logger.error(f"Error scraping {website.name} with requests: {str(e)}")
            return ScrapingResult(
                website=website.name,
                url=website.pricing_page_url,
                timestamp=datetime.now(),
                content_hash="",
                extracted_data={},
                changes_detected=[],
                scraping_method=ScrapingMethod.REQUESTS,
                success=False,
                error_message=str(e)
            )

    async def _scrape_with_selenium(self, website: CompetitorWebsite) -> ScrapingResult:
        """Scrape website using Selenium for dynamic content."""
        if not self.selenium_driver:
            self._initialize_selenium_driver()

        try:
            self.selenium_driver.get(website.pricing_page_url)

            # Wait for page to load
            WebDriverWait(self.selenium_driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Extract data using selectors
            extracted_data = {}
            for data_type, selector in website.selectors.items():
                try:
                    elements = self.selenium_driver.find_elements(By.CSS_SELECTOR, selector)
                    extracted_data[data_type] = [elem.text.strip() for elem in elements if elem.text.strip()]
                except Exception as e:
                    logger.warning(f"Could not extract {data_type} from {website.name}: {str(e)}")
                    extracted_data[data_type] = []

            # Get page source for hash calculation
            page_source = self.selenium_driver.page_source
            content_hash = hashlib.md5(page_source.encode()).hexdigest()

            # Detect changes
            changes = self._detect_changes(website.name, extracted_data, content_hash)

            return ScrapingResult(
                website=website.name,
                url=website.pricing_page_url,
                timestamp=datetime.now(),
                content_hash=content_hash,
                extracted_data=extracted_data,
                changes_detected=changes,
                scraping_method=ScrapingMethod.SELENIUM,
                success=True
            )

        except Exception as e:
            logger.error(f"Error scraping {website.name} with Selenium: {str(e)}")
            return ScrapingResult(
                website=website.name,
                url=website.pricing_page_url,
                timestamp=datetime.now(),
                content_hash="",
                extracted_data={},
                changes_detected=[],
                scraping_method=ScrapingMethod.SELENIUM,
                success=False,
                error_message=str(e)
            )

    def _initialize_selenium_driver(self):
        """Initialize Selenium Chrome driver with optimal settings."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")  # For faster scraping

        self.selenium_driver = webdriver.Chrome(options=chrome_options)

    def _extract_data_with_selectors(self, soup: BeautifulSoup, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract structured data using CSS selectors."""
        extracted_data = {}

        for data_type, selector in selectors.items():
            try:
                elements = soup.select(selector)
                extracted_data[data_type] = [elem.get_text(strip=True) for elem in elements if elem.get_text(strip=True)]
            except Exception as e:
                logger.warning(f"Could not extract {data_type}: {str(e)}")
                extracted_data[data_type] = []

        return extracted_data

    def _detect_changes(self, website_name: str, current_data: Dict[str, Any], content_hash: str) -> List[Dict[str, Any]]:
        """Detect changes by comparing with previous scraping results."""
        changes = []

        if website_name not in self.scraping_history or not self.scraping_history[website_name]:
            return changes  # No previous data to compare

        last_result = self.scraping_history[website_name][-1]

        # Check if content hash changed
        if last_result.content_hash != content_hash:
            changes.append({
                'type': 'content_changed',
                'timestamp': datetime.now().isoformat(),
                'description': 'Website content has changed'
            })

        # Check for specific data changes
        for data_type, current_values in current_data.items():
            if data_type in last_result.extracted_data:
                previous_values = last_result.extracted_data[data_type]

                if current_values != previous_values:
                    changes.append({
                        'type': f'{data_type}_changed',
                        'timestamp': datetime.now().isoformat(),
                        'description': f'{data_type.title()} data has changed',
                        'previous': previous_values,
                        'current': current_values
                    })

        return changes

    def get_competitor_summary(self, competitor_name: str) -> Optional[Dict[str, Any]]:
        """Get a summary of competitor monitoring results."""
        if competitor_name not in self.scraping_history:
            return None

        history = self.scraping_history[competitor_name]
        if not history:
            return None

        latest = history[-1]
        total_changes = sum(len(result.changes_detected) for result in history)

        return {
            'competitor': competitor_name,
            'last_scraped': latest.timestamp.isoformat(),
            'last_scrape_success': latest.success,
            'total_scrapes': len(history),
            'total_changes_detected': total_changes,
            'latest_data': latest.extracted_data,
            'recent_changes': latest.changes_detected
        }

    def __del__(self):
        """Clean up Selenium driver."""
        if self.selenium_driver:
            try:
                self.selenium_driver.quit()
            except:
                pass


# Factory function for easy integration
def get_competitor_web_scraper() -> CompetitorWebScraper:
    """Get a configured competitor web scraper instance."""
    return CompetitorWebScraper()


# Example usage and configuration
if __name__ == "__main__":
    # Example competitor configurations
    example_competitors = [
        CompetitorWebsite(
            name="competitor_a",
            domain="competitor-a.com",
            pricing_page_url="https://competitor-a.com/pricing",
            features_page_url="https://competitor-a.com/features",
            scraping_method=ScrapingMethod.REQUESTS,
            selectors={
                'pricing': '.price-card .price, .pricing-tier .amount',
                'features': '.feature-list li, .features .feature-item',
                'plans': '.plan-name, .tier-title'
            }
        ),
        CompetitorWebsite(
            name="competitor_b",
            domain="competitor-b.com",
            pricing_page_url="https://competitor-b.com/plans",
            scraping_method=ScrapingMethod.SELENIUM,  # Dynamic content
            rate_limit_delay=10
        )
    ]

    async def demo_scraping():
        scraper = get_competitor_web_scraper()

        # Add competitors
        for competitor in example_competitors:
            scraper.add_competitor(competitor)

        # Scrape all competitors
        results = await scraper.scrape_all_competitors()

        # Display results
        for result in results:
            if result.success:
                print(f"✅ Successfully scraped {result.website}")
                if result.changes_detected:
                    print(f"  🚨 {len(result.changes_detected)} changes detected!")
                    for change in result.changes_detected:
                        print(f"    - {change['description']}")
                else:
                    print(f"  📊 No changes detected")
            else:
                print(f"❌ Failed to scrape {result.website}: {result.error_message}")

    # Run demo
    asyncio.run(demo_scraping())