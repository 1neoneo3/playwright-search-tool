"""Tests for core.models module."""

import pytest
from datetime import datetime
import time
from unittest.mock import patch

from src.playwright_search.core.models import (
    SearchResult, SearchEngineConfig, SearchTask, SearchPlan, ParallelSearchResult
)


class TestSearchResult:
    """Tests for SearchResult dataclass."""
    
    def test_basic_creation(self):
        """Test basic SearchResult creation."""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
            position=1,
            source="test"
        )
        
        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.snippet == "Test snippet"
        assert result.position == 1
        assert result.source == "test"
        assert result.timestamp is not None
        assert isinstance(result.timestamp, float)
    
    def test_timestamp_auto_generation(self):
        """Test that timestamp is automatically generated."""
        with patch('time.time', return_value=12345.678):
            result = SearchResult(
                title="Test",
                url="https://example.com", 
                snippet="Test",
                position=1
            )
            assert result.timestamp == 12345.678
    
    def test_with_extracted_date(self):
        """Test SearchResult with extracted date."""
        test_date = datetime(2024, 8, 31, 12, 0, 0)
        result = SearchResult(
            title="Test",
            url="https://example.com",
            snippet="Test",
            position=1,
            extracted_date=test_date,
            recency_score=0.85
        )
        
        assert result.extracted_date == test_date
        assert result.recency_score == 0.85
    
    def test_optional_fields(self):
        """Test SearchResult with all optional fields."""
        result = SearchResult(
            title="Test",
            url="https://example.com",
            snippet="Test",
            position=1,
            source="google",
            content="Full page content",
            search_context="machine learning tutorials"
        )
        
        assert result.content == "Full page content"
        assert result.search_context == "machine learning tutorials"


class TestSearchEngineConfig:
    """Tests for SearchEngineConfig dataclass."""
    
    def test_default_values(self):
        """Test SearchEngineConfig with default values."""
        config = SearchEngineConfig()
        
        assert config.headless is True
        assert config.timeout == 30000
        assert config.viewport == {"width": 1920, "height": 1080}
        assert "Mozilla/5.0" in config.user_agent
    
    def test_custom_values(self):
        """Test SearchEngineConfig with custom values."""
        custom_viewport = {"width": 1366, "height": 768}
        custom_user_agent = "Custom User Agent"
        
        config = SearchEngineConfig(
            headless=False,
            timeout=60000,
            viewport=custom_viewport,
            user_agent=custom_user_agent
        )
        
        assert config.headless is False
        assert config.timeout == 60000
        assert config.viewport == custom_viewport
        assert config.user_agent == custom_user_agent


class TestSearchTask:
    """Tests for SearchTask dataclass."""
    
    def test_basic_creation(self):
        """Test basic SearchTask creation."""
        task = SearchTask(
            keyword="Python programming",
            engine="google"
        )
        
        assert task.keyword == "Python programming"
        assert task.engine == "google"
        assert task.num_results == 10  # default
        assert task.extract_content is False  # default
        assert task.recent_only is False  # default
        assert task.months == 3  # default
    
    def test_custom_values(self):
        """Test SearchTask with custom values."""
        task = SearchTask(
            keyword="Machine learning",
            engine="bing",
            num_results=20,
            extract_content=True,
            recent_only=True,
            months=6
        )
        
        assert task.keyword == "Machine learning"
        assert task.engine == "bing"
        assert task.num_results == 20
        assert task.extract_content is True
        assert task.recent_only is True
        assert task.months == 6


class TestSearchPlan:
    """Tests for SearchPlan dataclass."""
    
    def test_basic_creation(self):
        """Test basic SearchPlan creation."""
        tasks = [
            SearchTask("Python", "google"),
            SearchTask("Machine learning", "bing")
        ]
        
        with patch('time.time', return_value=12345.678):
            plan = SearchPlan(
                topic="Programming",
                tasks=tasks,
                created_at=12345.678
            )
        
        assert plan.topic == "Programming"
        assert len(plan.tasks) == 2
        assert plan.created_at == 12345.678
    
    def test_auto_timestamp(self):
        """Test that created_at is automatically set."""
        tasks = [SearchTask("test", "google")]
        plan = SearchPlan("Test Topic", tasks, time.time())
        
        assert plan.created_at is not None
        assert isinstance(plan.created_at, float)
        # Should be close to current time
        assert abs(plan.created_at - time.time()) < 1.0


class TestParallelSearchResult:
    """Tests for ParallelSearchResult dataclass."""
    
    def test_creation(self):
        """Test ParallelSearchResult creation."""
        plan = SearchPlan("Test", [SearchTask("test", "google")], time.time())
        results = {"test (google)": [
            SearchResult("Title", "https://example.com", "Snippet", 1)
        ]}
        errors = {"failed_task": "Connection error"}
        
        result = ParallelSearchResult(
            plan=plan,
            results=results,
            execution_time=5.5,
            success_count=1,
            error_count=1,
            errors=errors
        )
        
        assert result.plan == plan
        assert result.results == results
        assert result.execution_time == 5.5
        assert result.success_count == 1
        assert result.error_count == 1
        assert result.errors == errors


if __name__ == "__main__":
    pytest.main([__file__])