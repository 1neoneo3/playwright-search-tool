"""Google search engine implementation."""

from typing import List
import urllib.parse
import logging

from ..core.base import BaseSearchEngine
from ..core.models import SearchResult
from ..utils.date_parser import DateParser

logger = logging.getLogger(__name__)

class GoogleEngine(BaseSearchEngine):
    """Google search engine implementation."""
    
    def get_search_url(self, query: str) -> str:
        """Get Google search URL."""
        encoded_query = urllib.parse.quote_plus(query)
        return f"https://www.google.com/search?q={encoded_query}&num=20"
        
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Perform Google search."""
        results = []
        
        try:
            search_url = self.get_search_url(query)
            logger.info(f"Searching Google for: {query}")
            
            # Navigate to Google
            await self.page.goto(search_url, wait_until='networkidle')
            await self.random_delay(2.0, 4.0)
            
            # Handle cookie consent if present
            try:
                accept_btn = await self.page.wait_for_selector(
                    'button:has-text("Accept all"), button:has-text("I agree"), button:has-text("同意")', 
                    timeout=3000
                )
                if accept_btn:
                    await accept_btn.click()
                    await self.random_delay(1.0, 2.0)
            except:
                pass
                
            # Wait for search results - updated selectors
            try:
                await self.page.wait_for_selector('#search', timeout=10000)
            except:
                try:
                    await self.page.wait_for_selector('[data-ved]', timeout=8000)
                except:
                    await self.page.wait_for_selector('h3', timeout=5000)
            
            # Extract search results - improved selectors for current Google
            # Try multiple selector patterns to find all results
            search_containers = await self.page.query_selector_all('#search div[data-ved], #search .g, #search [jscontroller], .MjjYud')
            position = 1
            
            for element in search_containers:
                # Skip elements without h3 (not actual results) 
                title_elements = await element.query_selector_all('h3')
                if not title_elements:
                    continue
                    
                if position > num_results:
                    break
                    
                try:
                    # Get title
                    title = await title_elements[0].inner_text()
                    if not title.strip():
                        continue
                        
                    # Find the link containing the h3
                    link_element = await element.query_selector('a[href]:has(h3)')
                    if not link_element:
                        # Fallback: find any link with href
                        link_element = await element.query_selector('a[href]')
                        
                    if not link_element:
                        continue
                        
                    href = await link_element.get_attribute('href')
                    if not href or href.startswith('#'):
                        continue
                        
                    # Clean up URL (Google redirect URLs)
                    if href.startswith('/url?q='):
                        href = urllib.parse.unquote(href.split('/url?q=')[1].split('&')[0])
                    
                    # Get snippet - try multiple selectors for description text
                    snippet_element = None
                    snippet_selectors = ['[data-snf="nke7rc"]', '.VwiC3b', '.s3v9rd', '.hgKElc', 'span', 'div']
                    
                    for selector in snippet_selectors:
                        elements = await element.query_selector_all(selector)
                        for elem in elements:
                            text = await elem.inner_text()
                            # Look for descriptive text (not title, not URL)
                            if text and len(text) > 50 and text != title and not text.startswith('http'):
                                snippet_element = elem
                                break
                        if snippet_element:
                            break
                    
                    snippet = ""
                    if snippet_element:
                        snippet = await snippet_element.inner_text()
                        
                    # Check for duplicates
                    is_duplicate = False
                    for existing_result in results:
                        if existing_result.url == href and existing_result.title == title.strip():
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        # Extract date from snippet
                        extracted_date = DateParser.extract_date_from_snippet(snippet)
                        recency_score = DateParser.calculate_recency_score(extracted_date)
                        
                        result = SearchResult(
                            title=title.strip(),
                            url=href,
                            snippet=snippet.strip(),
                            position=position,
                            source="google",
                            extracted_date=extracted_date,
                            recency_score=recency_score
                        )
                        results.append(result)
                        position += 1
                    
                except Exception as e:
                    logger.debug(f"Error extracting result: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Google search failed: {str(e)}")
            
        return results