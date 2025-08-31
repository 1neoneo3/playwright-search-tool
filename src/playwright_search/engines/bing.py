"""Bing search engine implementation."""

from typing import List
import urllib.parse
import logging

from ..core.base import BaseSearchEngine
from ..core.models import SearchResult
from ..utils.date_parser import DateParser

logger = logging.getLogger(__name__)


class BingEngine(BaseSearchEngine):
    """Bing search engine implementation."""

    def get_search_url(self, query: str) -> str:
        """Get Bing search URL."""
        encoded_query = urllib.parse.quote_plus(query)
        return f"https://www.bing.com/search?q={encoded_query}&count=20"

    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """Perform Bing search."""
        results = []

        try:
            search_url = self.get_search_url(query)
            logger.info(f"Searching Bing for: {query}")

            await self.page.goto(search_url, wait_until="networkidle")
            await self.random_delay(1.0, 2.0)

            # Wait for search results
            await self.page.wait_for_selector(".b_algo", timeout=10000)

            # Extract search results
            search_elements = await self.page.query_selector_all(".b_algo")
            position = 1

            for element in search_elements[:num_results]:
                try:
                    # Get title and URL
                    title_link = await element.query_selector("h2 a")
                    if not title_link:
                        continue

                    title = await title_link.inner_text()
                    href = await title_link.get_attribute("href")

                    if not title.strip() or not href:
                        continue

                    # Get snippet
                    snippet_element = await element.query_selector(
                        ".b_caption p, .b_descript"
                    )
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
                        source="bing",
                        extracted_date=extracted_date,
                        recency_score=recency_score,
                    )
                    results.append(result)
                    position += 1

                except Exception as e:
                    logger.debug(f"Error extracting Bing result: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Bing search failed: {str(e)}")

        return results
