"""Tests for WebScraper: httpx + BeautifulSoup, rate limiting, robots.txt."""

import pytest

from devops_suite.data_pipeline.scraper import RobotsPolicy, WebScraper


@pytest.fixture
def scraper():
    return WebScraper(rate_limit=10.0, respect_robots=False, timeout=5.0)


class TestWebScraper:
    @pytest.mark.asyncio
    async def test_scrape_basic_html(self, scraper, httpx_mock):
        html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Hello World</h1>
            <a href="/page1">Page 1</a>
            <a href="https://example.com/page2">Page 2</a>
        </body>
        </html>
        """
        httpx_mock.add_response(url="https://example.com/test", text=html, status_code=200)

        result = await scraper.scrape("https://example.com/test")
        assert result.status_code == 200
        assert result.title == "Test Page"
        assert "Hello World" in result.text
        assert len(result.links) == 2
        assert result.elapsed_ms > 0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_scrape_extracts_text(self, scraper, httpx_mock):
        html = "<html><body><p>First paragraph</p><p>Second paragraph</p></body></html>"
        httpx_mock.add_response(url="https://example.com/", text=html)

        result = await scraper.scrape("https://example.com/")
        assert "First paragraph" in result.text
        assert "Second paragraph" in result.text

    @pytest.mark.asyncio
    async def test_scrape_no_title(self, scraper, httpx_mock):
        html = "<html><body>No title here</body></html>"
        httpx_mock.add_response(url="https://example.com/", text=html)

        result = await scraper.scrape("https://example.com/")
        assert result.title is None

    @pytest.mark.asyncio
    async def test_scrape_http_error(self, scraper, httpx_mock):
        httpx_mock.add_response(url="https://example.com/404", status_code=404)

        result = await scraper.scrape("https://example.com/404")
        assert result.status_code == 404

    @pytest.mark.asyncio
    async def test_scrape_network_error(self, scraper, httpx_mock):
        import httpx
        httpx_mock.add_exception(httpx.ConnectError("Connection failed"))

        result = await scraper.scrape("https://example.com/")
        assert result.status_code == 0
        assert result.error is not None
        assert "Connection failed" in result.error

    @pytest.mark.asyncio
    async def test_scrape_batch(self, scraper, httpx_mock):
        httpx_mock.add_response(url="https://example.com/1", text="<html><title>Page 1</title></html>")
        httpx_mock.add_response(url="https://example.com/2", text="<html><title>Page 2</title></html>")
        httpx_mock.add_response(url="https://example.com/3", text="<html><title>Page 3</title></html>")

        urls = ["https://example.com/1", "https://example.com/2", "https://example.com/3"]
        results = await scraper.scrape_batch(urls)

        assert len(results) == 3
        assert results[0].title == "Page 1"
        assert results[1].title == "Page 2"
        assert results[2].title == "Page 3"

    @pytest.mark.asyncio
    async def test_rate_limiting(self, scraper, httpx_mock):
        import time
        httpx_mock.add_response(url="https://example.com/", text="<html></html>")

        scraper.rate_limit = 2.0  # 2 requests per second
        start = time.monotonic()
        await scraper.scrape("https://example.com/")
        await scraper.scrape("https://example.com/")
        elapsed = time.monotonic() - start

        # Second request should wait ~0.5s
        assert elapsed >= 0.4  # Allow some tolerance

    @pytest.mark.asyncio
    async def test_robots_txt_allowed(self, scraper, httpx_mock):
        scraper.respect_robots = True
        robots = "User-agent: *\nAllow: /"
        httpx_mock.add_response(url="https://example.com/robots.txt", text=robots)
        httpx_mock.add_response(url="https://example.com/page", text="<html></html>")

        result = await scraper.scrape("https://example.com/page")
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_robots_txt_disallowed(self, scraper, httpx_mock):
        scraper.respect_robots = True
        robots = "User-agent: *\nDisallow: /admin"
        httpx_mock.add_response(url="https://example.com/robots.txt", text=robots)

        result = await scraper.scrape("https://example.com/admin")
        assert result.status_code == 403
        assert result.error == "Blocked by robots.txt"

    @pytest.mark.asyncio
    async def test_robots_txt_cache(self, scraper, httpx_mock):
        scraper.respect_robots = True
        robots = "User-agent: *\nAllow: /"
        httpx_mock.add_response(url="https://example.com/robots.txt", text=robots)
        httpx_mock.add_response(url="https://example.com/page1", text="<html></html>")
        httpx_mock.add_response(url="https://example.com/page2", text="<html></html>")

        await scraper.scrape("https://example.com/page1")
        await scraper.scrape("https://example.com/page2")

        # robots.txt should only be fetched once
        robots_requests = [req for req in httpx_mock.get_requests() if "robots.txt" in str(req.url)]
        assert len(robots_requests) == 1

    @pytest.mark.asyncio
    async def test_robots_txt_not_found(self, scraper, httpx_mock):
        scraper.respect_robots = True
        httpx_mock.add_response(url="https://example.com/robots.txt", status_code=404)
        httpx_mock.add_response(url="https://example.com/page", text="<html></html>")

        # Should allow scraping if robots.txt not found
        result = await scraper.scrape("https://example.com/page")
        assert result.status_code == 200

    def test_parse_robots_disallow(self, scraper):
        robots_txt = """
        User-agent: *
        Disallow: /private
        Disallow: /admin
        """
        policy = scraper._parse_robots(robots_txt, "/private/page")
        assert policy.allowed is False

    def test_parse_robots_allow(self, scraper):
        robots_txt = """
        User-agent: *
        Disallow: /private
        """
        policy = scraper._parse_robots(robots_txt, "/public/page")
        assert policy.allowed is True

    def test_parse_robots_crawl_delay(self, scraper):
        robots_txt = """
        User-agent: *
        Crawl-delay: 2.5
        """
        policy = scraper._parse_robots(robots_txt, "/page")
        assert policy.crawl_delay == 2.5

    def test_parse_robots_specific_agent(self, scraper):
        robots_txt = """
        User-agent: BadBot
        Disallow: /

        User-agent: *
        Disallow: /admin
        """
        # Should match wildcard, not BadBot
        policy = scraper._parse_robots(robots_txt, "/page")
        assert policy.allowed is True

    def test_parse_robots_aidevops_agent(self, scraper):
        robots_txt = """
        User-agent: AIDevOpsSuite
        Disallow: /restricted
        """
        policy = scraper._parse_robots(robots_txt, "/restricted/page")
        assert policy.allowed is False

    @pytest.mark.asyncio
    async def test_link_extraction_absolute_urls(self, scraper, httpx_mock):
        html = """
        <html><body>
        <a href="https://example.com/page1">Link 1</a>
        <a href="https://example.com/page2">Link 2</a>
        </body></html>
        """
        httpx_mock.add_response(url="https://example.com/", text=html)

        result = await scraper.scrape("https://example.com/")
        assert "https://example.com/page1" in result.links
        assert "https://example.com/page2" in result.links

    @pytest.mark.asyncio
    async def test_link_extraction_relative_urls(self, scraper, httpx_mock):
        html = """
        <html><body>
        <a href="/page1">Link 1</a>
        <a href="page2">Link 2</a>
        </body></html>
        """
        httpx_mock.add_response(url="https://example.com/base/", text=html)

        result = await scraper.scrape("https://example.com/base/")
        assert "https://example.com/page1" in result.links
        assert "https://example.com/base/page2" in result.links

    @pytest.mark.asyncio
    async def test_custom_user_agent(self, scraper, httpx_mock):
        scraper.user_agent = "CustomBot/1.0"
        httpx_mock.add_response(url="https://example.com/", text="<html></html>")

        await scraper.scrape("https://example.com/")

        requests = httpx_mock.get_requests()
        assert requests[0].headers["User-Agent"] == "CustomBot/1.0"
