"""Web scraper with httpx, BeautifulSoup, robots.txt respect, and rate limiting."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


@dataclass
class ScrapeResult:
    url: str
    status_code: int
    html: str
    text: str
    title: str | None
    links: list[str]
    elapsed_ms: float
    error: str | None = None


@dataclass
class RobotsPolicy:
    allowed: bool = True
    crawl_delay: float | None = None


class WebScraper:
    """Configurable web scraper with rate limiting and robots.txt support."""

    def __init__(
        self,
        rate_limit: float = 1.0,  # requests per second
        respect_robots: bool = True,
        timeout: float = 30.0,
        user_agent: str = "AIDevOpsSuite/0.1 (+https://devops-suite.example.com/bot)",
    ):
        self.rate_limit = rate_limit
        self.respect_robots = respect_robots
        self.timeout = timeout
        self.user_agent = user_agent
        self._last_request: dict[str, float] = {}  # domain -> timestamp
        self._robots_cache: dict[str, RobotsPolicy] = {}

    async def scrape(self, url: str, client: httpx.AsyncClient | None = None) -> ScrapeResult:
        domain = urlparse(url).netloc
        await self._rate_limit_wait(domain)

        if self.respect_robots:
            policy = await self._check_robots(url, client)
            if not policy.allowed:
                return ScrapeResult(
                    url=url,
                    status_code=403,
                    html="",
                    text="",
                    title=None,
                    links=[],
                    elapsed_ms=0,
                    error="Blocked by robots.txt",
                )

        should_close = client is None
        if client is None:
            client = httpx.AsyncClient(timeout=self.timeout)

        try:
            start = time.monotonic()
            response = await client.get(url, headers={"User-Agent": self.user_agent})
            elapsed = (time.monotonic() - start) * 1000

            self._last_request[domain] = time.monotonic()
            soup = BeautifulSoup(response.text, "html.parser")
            title_tag = soup.find("title")

            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                links.append(urljoin(url, href))

            return ScrapeResult(
                url=url,
                status_code=response.status_code,
                html=response.text,
                text=soup.get_text(separator="\n", strip=True),
                title=title_tag.string if title_tag else None,
                links=links,
                elapsed_ms=elapsed,
            )
        except httpx.HTTPError as e:
            return ScrapeResult(
                url=url,
                status_code=0,
                html="",
                text="",
                title=None,
                links=[],
                elapsed_ms=0,
                error=str(e),
            )
        finally:
            if should_close:
                await client.aclose()

    async def scrape_batch(self, urls: list[str]) -> list[ScrapeResult]:
        results = []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for url in urls:
                result = await self.scrape(url, client)
                results.append(result)
        return results

    async def _rate_limit_wait(self, domain: str) -> None:
        if self.rate_limit <= 0:
            return
        last = self._last_request.get(domain, 0)
        interval = 1.0 / self.rate_limit
        elapsed = time.monotonic() - last
        if elapsed < interval:
            await asyncio.sleep(interval - elapsed)

    async def _check_robots(
        self, url: str, client: httpx.AsyncClient | None = None
    ) -> RobotsPolicy:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        if robots_url in self._robots_cache:
            return self._robots_cache[robots_url]

        should_close = client is None
        if client is None:
            client = httpx.AsyncClient(timeout=10)

        try:
            resp = await client.get(robots_url, headers={"User-Agent": self.user_agent})
            if resp.status_code != 200:
                policy = RobotsPolicy(allowed=True)
            else:
                policy = self._parse_robots(resp.text, parsed.path)
            self._robots_cache[robots_url] = policy
            return policy
        except httpx.HTTPError:
            policy = RobotsPolicy(allowed=True)
            self._robots_cache[robots_url] = policy
            return policy
        finally:
            if should_close:
                await client.aclose()

    def _parse_robots(self, robots_txt: str, path: str) -> RobotsPolicy:
        allowed = True
        crawl_delay = None
        in_relevant_block = False

        for line in robots_txt.splitlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            key, _, value = line.partition(":")
            key = key.strip().lower()
            value = value.strip()

            if key == "user-agent":
                in_relevant_block = value == "*" or "aidevops" in value.lower()
            elif in_relevant_block and key == "disallow" and value:
                if path.startswith(value):
                    allowed = False
            elif in_relevant_block and key == "crawl-delay":
                try:
                    crawl_delay = float(value)
                except ValueError:
                    pass

        return RobotsPolicy(allowed=allowed, crawl_delay=crawl_delay)
