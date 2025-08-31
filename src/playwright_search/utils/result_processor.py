"""Result processing utilities."""

from typing import List, Tuple
from ..core.models import SearchResult
from .date_parser import DateParser


class ResultProcessor:
    """Processor for search results with filtering and sorting capabilities."""

    @staticmethod
    def filter_and_sort_by_date(
        results: List[SearchResult], recent_only: bool = False, months: int = 3
    ) -> List[Tuple[SearchResult, float]]:
        """
        Filter and sort search results by date recency.

        Args:
            results: List of search results with extracted_date attribute
            recent_only: If True, only return results within the timeframe
            months: Number of months to consider as "recent"

        Returns:
            List of (result, recency_score) tuples sorted by recency
        """
        scored_results = []

        for result in results:
            date = getattr(result, "extracted_date", None)
            recency_score = DateParser.calculate_recency_score(date)

            if recent_only and date and not DateParser.is_recent(date, months):
                continue

            scored_results.append((result, recency_score))

        # Sort by recency score (highest first)
        scored_results.sort(key=lambda x: x[1], reverse=True)

        return scored_results

    @staticmethod
    def deduplicate_results(results: List[SearchResult]) -> List[SearchResult]:
        """
        Remove duplicate results based on URL.

        Args:
            results: List of search results

        Returns:
            List of unique search results
        """
        seen_urls = set()
        unique_results = []

        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        return unique_results

    @staticmethod
    def merge_results(
        result_groups: List[List[SearchResult]], deduplicate: bool = True
    ) -> List[SearchResult]:
        """
        Merge multiple result groups into a single list.

        Args:
            result_groups: List of result groups to merge
            deduplicate: Whether to remove duplicates

        Returns:
            Merged list of search results
        """
        all_results = []
        for group in result_groups:
            all_results.extend(group)

        if deduplicate:
            all_results = ResultProcessor.deduplicate_results(all_results)

        # Sort by recency score if available, then by position
        all_results.sort(
            key=lambda x: (getattr(x, "recency_score", 0), -x.position), reverse=True
        )

        return all_results

    @staticmethod
    def add_search_context(
        results: List[SearchResult], context: str
    ) -> List[SearchResult]:
        """
        Add search context information to results.

        Args:
            results: List of search results
            context: Context information to add

        Returns:
            Results with search context added
        """
        for result in results:
            result.search_context = context
        return results

    @staticmethod
    def limit_results(results: List[SearchResult], limit: int) -> List[SearchResult]:
        """
        Limit the number of results.

        Args:
            results: List of search results
            limit: Maximum number of results to return

        Returns:
            Limited list of search results
        """
        return results[:limit] if results else []
