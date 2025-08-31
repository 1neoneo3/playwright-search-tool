"""DuckDuckGo search engine implementation."""

from typing import List
import urllib.parse
import logging

from ..core.base import BaseSearchEngine
from ..core.models import SearchResult
from ..utils.date_parser import DateParser

logger = logging.getLogger(__name__)

class DuckDuckGoEngine(BaseSearchEngine):
    """DuckDuckGo search engine implementation."""
    
    def get_search_url(self, query: str) -> str:
        """Get DuckDuckGo search URL.""" 
        encoded_query = urllib.parse.quote_plus(query)
        return f"https://duckduckgo.com/?q={encoded_query}"
        
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Perform DuckDuckGo search."""
        results = []
        
        try:
            search_url = self.get_search_url(query)
            logger.info(f"Searching DuckDuckGo for: {query}")
            
            await self.page.goto(search_url, wait_until='networkidle')
            await self.random_delay(2.0, 3.0)
            
            # Wait for search results - try multiple selectors
            try:
                await self.page.wait_for_selector('[data-testid="result"]', timeout=8000)
                search_elements = await self.page.query_selector_all('[data-testid="result"]')
            except:
                await self.page.wait_for_selector('article', timeout=5000)
                search_elements = await self.page.query_selector_all('article')
            position = 1
            
            for element in search_elements[:num_results]:
                try:
                    # Get title and URL
                    title_link = await element.query_selector('h2 a, [data-testid="result-title-a"]')
                    if not title_link:
                        continue
                        
                    title = await title_link.inner_text() 
                    href = await title_link.get_attribute('href')
                    
                    if not title.strip() or not href:
                        continue
                        
                    # Get snippet
                    snippet_element = await element.query_selector('[data-result="snippet"]')
                    snippet = ""
                    if snippet_element:
                        snippet = await snippet_element.inner_text()
                        
                    # Extract date from snippet
                    extracted_date = DateParser.extract_date_from_snippet(snippet)
                    recency_score = DateParser.calculate_recency_score(extracted_date)
                    
                    result = SearchResult(
                        title=title.strip(),
                        url=href,
                        snippet=snippet.strip(),
                        position=position,
                        source="duckduckgo",
                        extracted_date=extracted_date,
                        recency_score=recency_score
                    )
                    results.append(result)
                    position += 1
                    
                except Exception as e:
                    logger.debug(f"Error extracting DDG result: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {str(e)}")
            
        return results