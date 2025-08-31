"""Base search engine classes and data structures."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser
import asyncio
import time
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    url: str
    snippet: str
    position: int
    source: str = "unknown"
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class SearchEngine(ABC):
    """Abstract base class for search engines."""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
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
            headless=self.headless,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--disable-gpu',
                '--disable-web-security',
                '--allow-running-insecure-content'
            ]
        )
        
        # Create context with realistic settings
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.timeout)
        
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
        if hasattr(self, 'playwright'):
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
            await self.page.goto(url, wait_until='networkidle', timeout=self.timeout)
            await self.random_delay(0.5, 1.5)
            
            # Remove ads, navigation, and other non-content elements
            await self.page.evaluate("""
                // Remove common non-content elements
                const selectors = [
                    'nav', 'header', 'footer', '.ads', '.advertisement', 
                    '.sidebar', '.menu', '.navigation', '[role="banner"]',
                    '[role="navigation"]', '.cookie', '.popup', '.modal',
                    '.related-posts', '.comments', '.social-share', '.breadcrumb'
                ];
                selectors.forEach(sel => {
                    document.querySelectorAll(sel).forEach(el => el.remove());
                });
            """)
            
            # Try to find main content with priority order
            content_selectors = [
                'main article',
                'main',
                'article', 
                '[role="main"]', 
                '.content-body',
                '.post-body',
                '.entry-content',
                '.article-content',
                '.main-content', 
                '.article-body', 
                '.post-content',
                '.content'
            ]
            
            content = None
            for selector in content_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        text = await element.inner_text()
                        # Check if we got meaningful content (not just whitespace/short text)
                        if text and len(text.strip()) > 100:
                            content = text
                            break
                except:
                    continue
                    
            # Fallback to body if no main content found
            if not content:
                content = await self.page.evaluate('document.body.innerText')
            
            if content:
                # Clean up the content
                lines = content.split('\n')
                # Remove empty lines and very short lines that are likely navigation
                cleaned_lines = [line.strip() for line in lines if line.strip() and len(line.strip()) > 10]
                content = '\n'.join(cleaned_lines[:200])  # Limit to first 200 meaningful lines
                
            return content[:3000] if content else None  # Increased limit but still reasonable
            
        except Exception as e:
            logger.error(f"Failed to extract content from {url}: {str(e)}")
            return None