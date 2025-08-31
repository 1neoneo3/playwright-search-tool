"""Base classes for search engines and components."""

from abc import ABC, abstractmethod
from typing import List, Optional
from playwright.async_api import async_playwright, Page, Browser
import asyncio
import random
import logging

from .models import SearchResult, SearchEngineConfig
from ..const import BROWSER_ARGS, NOISE_SELECTORS, CONTENT_SELECTORS

logger = logging.getLogger(__name__)


class BaseSearchEngine(ABC):
    """Abstract base class for search engines."""

    def __init__(self, config: Optional[SearchEngineConfig] = None):
        """Initialize search engine with configuration."""
        self.config = config or SearchEngineConfig()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.context = None
        self.playwright = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self):
        """Start the browser and page."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.config.headless, args=BROWSER_ARGS
        )

        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport=self.config.viewport, user_agent=self.config.user_agent
        )

        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.config.timeout)

        # Add stealth features
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)

    async def close(self):
        """Close the browser."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def random_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """Add random delay to simulate human behavior."""
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)

    @abstractmethod
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Perform a search and return results."""
        pass

    @abstractmethod
    def get_search_url(self, query: str) -> str:
        """Get the search URL for the given query."""
        pass

    async def extract_text_content(self, url: str) -> Optional[str]:
        """Extract text content from a webpage with improved content detection."""
        try:
            await self.page.goto(
                url, wait_until="networkidle", timeout=self.config.timeout
            )
            await self.random_delay(0.5, 1.5)

            # Remove ads, navigation, and other non-content elements
            await self._remove_noise_elements()

            # Try to find main content with priority order
            content = await self._extract_main_content()

            if content:
                # Clean up the content
                content = self._clean_content(content)

            return content

        except Exception as e:
            logger.error(f"Failed to extract content from {url}: {str(e)}")
            return None

    async def _remove_noise_elements(self):
        """Remove noise elements from the page."""
        script = f"""
            const selectors = {NOISE_SELECTORS};
            selectors.forEach(sel => {{
                document.querySelectorAll(sel).forEach(el => el.remove());
            }});
        """
        await self.page.evaluate(script)

    async def _extract_main_content(self) -> Optional[str]:
        """Extract main content from the page."""
        content = None

        for selector in CONTENT_SELECTORS:
            try:
                element = await self.page.wait_for_selector(selector, timeout=2000)
                if element:
                    text = await element.inner_text()
                    # Check if we got meaningful content (not just whitespace/short text)
                    if text and len(text.strip()) > 100:
                        content = text
                        break
            except Exception:
                continue

        # Fallback to body if no main content found
        if not content:
            content = await self.page.evaluate("document.body.innerText")

        return content

    def _clean_content(self, content: str) -> str:
        """Clean and format content."""
        from ..const import MAX_CONTENT_LENGTH, MAX_SNIPPET_LINES

        lines = content.split("\n")
        # Remove empty lines and very short lines that are likely navigation
        cleaned_lines = [
            line.strip() for line in lines if line.strip() and len(line.strip()) > 10
        ]
        content = "\n".join(cleaned_lines[:MAX_SNIPPET_LINES])

        return content[:MAX_CONTENT_LENGTH] if content else None
