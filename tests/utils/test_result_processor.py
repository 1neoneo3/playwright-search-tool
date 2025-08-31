"""Tests for utils.result_processor module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from src.playwright_search.core.models import SearchResult
from src.playwright_search.utils.result_processor import ResultProcessor


class TestResultProcessor:
    """Tests for ResultProcessor class."""
    
    def create_sample_results(self):
        """Create sample SearchResult objects for testing."""
        fixed_time = datetime(2024, 8, 31, 12, 0, 0)
        
        results = [
            SearchResult(
                title="Recent Article",
                url="https://example.com/recent",
                snippet="Recent content",
                position=1,
                source="google",
                extracted_date=fixed_time - timedelta(days=1),
                recency_score=1.0
            ),
            SearchResult(
                title="Old Article",
                url="https://example.com/old",
                snippet="Old content",
                position=2,
                source="google", 
                extracted_date=fixed_time - timedelta(days=120),
                recency_score=0.3
            ),
            SearchResult(
                title="Medium Article",
                url="https://example.com/medium",
                snippet="Medium age content",
                position=3,
                source="bing",
                extracted_date=fixed_time - timedelta(days=30),
                recency_score=0.8
            ),
            SearchResult(
                title="No Date Article",
                url="https://example.com/no-date",
                snippet="No date content",
                position=4,
                source="google"
            )
        ]
        return results
    
    def test_filter_and_sort_by_date_all_results(self):
        """Test filter_and_sort_by_date without filtering."""
        results = self.create_sample_results()
        
        scored_results = ResultProcessor.filter_and_sort_by_date(
            results, recent_only=False, months=3
        )
        
        # Should return all results, sorted by recency score
        assert len(scored_results) == 4
        
        # Check sorting (highest recency score first)
        scores = [score for result, score in scored_results]
        assert scores == sorted(scores, reverse=True)
        
        # Check that results with dates come first
        first_result, first_score = scored_results[0]
        assert first_result.title == "Recent Article"
        assert first_score == 1.0
    
    def test_filter_and_sort_by_date_recent_only(self):
        """Test filter_and_sort_by_date with recent_only=True."""
        results = self.create_sample_results()
        
        with patch('src.playwright_search.utils.date_parser.DateParser.is_recent') as mock_is_recent:
            # Mock is_recent to return True for recent and medium, False for old
            def mock_recent_check(date, months):
                if date is None:
                    return False
                days_ago = (datetime(2024, 8, 31, 12, 0, 0) - date).days
                return days_ago <= 90  # 3 months
            
            mock_is_recent.side_effect = mock_recent_check
            
            scored_results = ResultProcessor.filter_and_sort_by_date(
                results, recent_only=True, months=3
            )
            
            # Should filter out old results
            assert len(scored_results) == 2
            
            # Should include recent and medium articles
            titles = [result.title for result, score in scored_results]
            assert "Recent Article" in titles
            assert "Medium Article" in titles
            assert "Old Article" not in titles
            assert "No Date Article" not in titles
    
    def test_deduplicate_results(self):
        """Test deduplicate_results method."""
        # Create duplicate results
        results = [
            SearchResult("Title 1", "https://example.com/1", "Snippet 1", 1, "google"),
            SearchResult("Title 2", "https://example.com/2", "Snippet 2", 2, "google"),
            SearchResult("Different Title", "https://example.com/1", "Different snippet", 3, "bing"),  # Same URL
            SearchResult("Title 3", "https://example.com/3", "Snippet 3", 4, "google"),
        ]
        
        unique_results = ResultProcessor.deduplicate_results(results)
        
        # Should remove the duplicate URL
        assert len(unique_results) == 3
        
        # Should keep the first occurrence
        urls = [result.url for result in unique_results]
        assert urls == ["https://example.com/1", "https://example.com/2", "https://example.com/3"]
        assert unique_results[0].title == "Title 1"  # First occurrence kept
    
    def test_merge_results(self):
        """Test merge_results method."""
        group1 = [
            SearchResult("Title 1", "https://example.com/1", "Snippet 1", 1, "google", recency_score=0.9),
            SearchResult("Title 2", "https://example.com/2", "Snippet 2", 2, "google", recency_score=0.7),
        ]
        
        group2 = [
            SearchResult("Title 3", "https://example.com/3", "Snippet 3", 1, "bing", recency_score=0.8),
            SearchResult("Duplicate", "https://example.com/1", "Different snippet", 2, "bing", recency_score=0.6),  # Duplicate
        ]
        
        merged = ResultProcessor.merge_results([group1, group2], deduplicate=True)
        
        # Should merge and deduplicate
        assert len(merged) == 3
        
        # Should be sorted by recency score and position
        expected_order = ["Title 1", "Title 3", "Title 2"]  # Based on recency_score
        actual_order = [result.title for result in merged]
        assert actual_order == expected_order
    
    def test_merge_results_no_deduplication(self):
        """Test merge_results without deduplication."""
        group1 = [SearchResult("Title 1", "https://example.com/1", "Snippet 1", 1, "google")]
        group2 = [SearchResult("Duplicate", "https://example.com/1", "Different snippet", 2, "bing")]
        
        merged = ResultProcessor.merge_results([group1, group2], deduplicate=False)
        
        # Should include duplicates
        assert len(merged) == 2
        urls = [result.url for result in merged]
        assert urls.count("https://example.com/1") == 2
    
    def test_add_search_context(self):
        """Test add_search_context method."""
        results = [
            SearchResult("Title 1", "https://example.com/1", "Snippet 1", 1, "google"),
            SearchResult("Title 2", "https://example.com/2", "Snippet 2", 2, "google"),
        ]
        
        context = "machine learning tutorials"
        results_with_context = ResultProcessor.add_search_context(results, context)
        
        # Should add context to all results
        assert len(results_with_context) == 2
        for result in results_with_context:
            assert result.search_context == context
        
        # Should return the same results (modified in place)
        assert results_with_context == results
    
    def test_limit_results(self):
        """Test limit_results method."""
        results = [
            SearchResult("Title 1", "https://example.com/1", "Snippet 1", 1, "google"),
            SearchResult("Title 2", "https://example.com/2", "Snippet 2", 2, "google"),
            SearchResult("Title 3", "https://example.com/3", "Snippet 3", 3, "google"),
            SearchResult("Title 4", "https://example.com/4", "Snippet 4", 4, "google"),
        ]
        
        # Test normal limiting
        limited = ResultProcessor.limit_results(results, 2)
        assert len(limited) == 2
        assert limited[0].title == "Title 1"
        assert limited[1].title == "Title 2"
        
        # Test limiting with more than available
        limited = ResultProcessor.limit_results(results, 10)
        assert len(limited) == 4
        
        # Test with empty list
        limited = ResultProcessor.limit_results([], 5)
        assert limited == []
        
        # Test with zero limit
        limited = ResultProcessor.limit_results(results, 0)
        assert limited == []
    
    def test_empty_inputs(self):
        """Test methods with empty inputs."""
        # Empty results list
        empty_scored = ResultProcessor.filter_and_sort_by_date([], False, 3)
        assert empty_scored == []
        
        empty_unique = ResultProcessor.deduplicate_results([])
        assert empty_unique == []
        
        empty_merged = ResultProcessor.merge_results([], True)
        assert empty_merged == []
        
        empty_context = ResultProcessor.add_search_context([], "context")
        assert empty_context == []
    
    def test_sorting_edge_cases(self):
        """Test sorting with edge cases."""
        # Results without recency scores
        results = [
            SearchResult("Title 1", "https://example.com/1", "Snippet 1", 3, "google"),
            SearchResult("Title 2", "https://example.com/2", "Snippet 2", 1, "google"),
            SearchResult("Title 3", "https://example.com/3", "Snippet 3", 2, "google"),
        ]
        
        merged = ResultProcessor.merge_results([results], deduplicate=False)
        
        # Should sort by position when recency_score is the same (0.0)
        positions = [result.position for result in merged]
        # Sorting by (recency_score, -position) reverse=True means better position (lower number) comes first
        assert positions == [1, 2, 3]


if __name__ == "__main__":
    pytest.main([__file__])