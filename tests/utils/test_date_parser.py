"""Tests for utils.date_parser module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from src.playwright_search.utils.date_parser import DateParser


class TestDateParser:
    """Tests for DateParser class."""
    
    def test_extract_date_from_snippet_relative_dates(self):
        """Test extraction of relative dates."""
        # Mock current time for consistent testing
        fixed_time = datetime(2024, 8, 31, 12, 0, 0)
        
        with patch('src.playwright_search.utils.date_parser.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            
            # Test days ago
            result = DateParser.extract_date_from_snippet("Posted 3 days ago")
            expected = fixed_time - timedelta(days=3)
            assert result.date() == expected.date()
            
            # Test hours ago
            result = DateParser.extract_date_from_snippet("Updated 5 hours ago")
            expected = fixed_time - timedelta(hours=5)
            assert result.date() == expected.date()
            
            # Test minutes ago
            result = DateParser.extract_date_from_snippet("Published 30 minutes ago")
            expected = fixed_time - timedelta(minutes=30)
            assert result.date() == expected.date()
            
            # Test weeks ago
            result = DateParser.extract_date_from_snippet("Created 2 weeks ago")
            expected = fixed_time - timedelta(weeks=2)
            assert result.date() == expected.date()
    
    def test_extract_date_from_snippet_absolute_dates(self):
        """Test extraction of absolute dates."""
        # Test ISO format
        result = DateParser.extract_date_from_snippet("Date: 2024-08-31")
        assert result == datetime(2024, 8, 31)
        
        # Test US format (MM/DD/YYYY)
        result = DateParser.extract_date_from_snippet("Published on 08/31/2024")
        assert result == datetime(2024, 8, 31)
        
        # Test different formats
        result = DateParser.extract_date_from_snippet("2024/08/31 update")
        assert result == datetime(2024, 8, 31)
    
    def test_extract_date_from_snippet_special_keywords(self):
        """Test extraction of special date keywords."""
        fixed_time = datetime(2024, 8, 31, 12, 0, 0)
        
        with patch('src.playwright_search.utils.date_parser.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            
            # Test today
            result = DateParser.extract_date_from_snippet("Published today")
            assert result.date() == fixed_time.date()
            
            # Test yesterday
            result = DateParser.extract_date_from_snippet("Updated yesterday")
            expected = fixed_time - timedelta(days=1)
            assert result.date() == expected.date()
            
            # Test last week
            result = DateParser.extract_date_from_snippet("From last week")
            expected = fixed_time - timedelta(weeks=1)
            assert result.date() == expected.date()
            
            # Test last month
            result = DateParser.extract_date_from_snippet("Last month's report")
            expected = fixed_time - timedelta(days=30)
            assert result.date() == expected.date()
    
    def test_extract_date_from_snippet_no_date(self):
        """Test when no date is found in snippet."""
        result = DateParser.extract_date_from_snippet("No date information here")
        assert result is None
        
        result = DateParser.extract_date_from_snippet("")
        assert result is None
        
        result = DateParser.extract_date_from_snippet(None)
        assert result is None
    
    def test_extract_date_from_snippet_japanese_dates(self):
        """Test extraction of Japanese date formats."""
        fixed_time = datetime(2024, 8, 31, 12, 0, 0)
        
        with patch('src.playwright_search.utils.date_parser.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            
            # Test Japanese relative dates
            result = DateParser.extract_date_from_snippet("3日前")
            expected = fixed_time - timedelta(days=3)
            assert result.date() == expected.date()
            
            result = DateParser.extract_date_from_snippet("1週間前")
            expected = fixed_time - timedelta(weeks=1)
            assert result.date() == expected.date()
    
    def test_is_recent(self):
        """Test is_recent method."""
        fixed_time = datetime(2024, 8, 31, 12, 0, 0)
        
        with patch('src.playwright_search.utils.date_parser.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            
            # Test recent dates (within 3 months)
            recent_date = fixed_time - timedelta(days=60)  # 2 months ago
            assert DateParser.is_recent(recent_date, months=3) is True
            
            # Test old dates (beyond 3 months)
            old_date = fixed_time - timedelta(days=120)  # 4 months ago
            assert DateParser.is_recent(old_date, months=3) is False
            
            # Test exact boundary
            boundary_date = fixed_time - timedelta(days=90)  # Exactly 3 months
            assert DateParser.is_recent(boundary_date, months=3) is True
            
            # Test custom months parameter
            assert DateParser.is_recent(old_date, months=6) is True
    
    def test_calculate_recency_score(self):
        """Test calculate_recency_score method."""
        fixed_time = datetime(2024, 8, 31, 12, 0, 0)
        
        with patch('src.playwright_search.utils.date_parser.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            
            # Test None date
            assert DateParser.calculate_recency_score(None) == 0.0
            
            # Test current date
            assert DateParser.calculate_recency_score(fixed_time) == 1.0
            
            # Test future date (should be treated as today)
            future_date = fixed_time + timedelta(days=1)
            assert DateParser.calculate_recency_score(future_date) == 1.0
            
            # Test recent dates (within a week)
            recent = fixed_time - timedelta(days=3)
            assert DateParser.calculate_recency_score(recent) == 1.0
            
            # Test dates within a month (should be between 0.8 and 0.9)
            month_old = fixed_time - timedelta(days=20)
            score = DateParser.calculate_recency_score(month_old)
            assert 0.8 <= score <= 0.9
            
            # Test dates within 3 months (should be between 0.5 and 0.8)
            three_month_old = fixed_time - timedelta(days=60)
            score = DateParser.calculate_recency_score(three_month_old)
            assert 0.5 <= score <= 0.8
            
            # Test dates within a year (should be between 0.2 and 0.5)
            year_old = fixed_time - timedelta(days=200)
            score = DateParser.calculate_recency_score(year_old)
            assert 0.2 <= score <= 0.5
            
            # Test very old dates (should be 0.1 or higher)
            very_old = fixed_time - timedelta(days=500)
            score = DateParser.calculate_recency_score(very_old)
            assert score >= 0.1
    
    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # Test malformed dates that might cause errors
        result = DateParser.extract_date_from_snippet("Posted 999999 days ago")
        assert result is None or isinstance(result, datetime)
        
        # Test mixed content
        result = DateParser.extract_date_from_snippet("Some text with 2 days ago and more text")
        assert result is not None
        
        # Test multiple dates (should return the first valid one)
        result = DateParser.extract_date_from_snippet("Posted 1 day ago, updated 2 hours ago")
        assert result is not None
    
    def test_text_cleaning(self):
        """Test that text is properly cleaned before parsing."""
        # Test with newlines and extra whitespace
        text_with_newlines = "Some content\n\nPosted 2 days ago\n\nMore content"
        result = DateParser.extract_date_from_snippet(text_with_newlines)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__])