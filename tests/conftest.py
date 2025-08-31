"""Pytest configuration and test fixtures."""

import sys
from pathlib import Path

# Add src to Python path for tests
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import time


@pytest.fixture
def mock_playwright():
    """Create a comprehensive mock for playwright components."""
    mock_playwright = Mock()
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    
    # Setup the mock chain
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    # Mock cleanup methods
    mock_page.close = AsyncMock()
    mock_context.close = AsyncMock()
    mock_browser.close = AsyncMock()
    mock_playwright.stop = AsyncMock()
    
    # Mock page methods
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.query_selector_all = AsyncMock(return_value=[])
    mock_page.evaluate = AsyncMock(return_value="")
    mock_page.set_default_timeout = Mock()
    mock_page.add_init_script = AsyncMock()
    
    return {
        'playwright': mock_playwright,
        'browser': mock_browser,
        'context': mock_context,
        'page': mock_page
    }


@pytest.fixture
def sample_search_results():
    """Create sample SearchResult objects for testing."""
    from src.playwright_search.core.models import SearchResult
    
    return [
        SearchResult(
            title="First Result",
            url="https://example.com/1",
            snippet="First result snippet",
            position=1,
            source="google",
            extracted_date=datetime(2024, 8, 30),
            recency_score=0.9
        ),
        SearchResult(
            title="Second Result",
            url="https://example.com/2", 
            snippet="Second result snippet",
            position=2,
            source="bing",
            extracted_date=datetime(2024, 8, 25),
            recency_score=0.7
        ),
        SearchResult(
            title="Third Result",
            url="https://example.com/3",
            snippet="Third result snippet", 
            position=3,
            source="google"
        )
    ]


@pytest.fixture
def sample_search_plan():
    """Create a sample SearchPlan for testing."""
    from src.playwright_search.core.models import SearchTask, SearchPlan
    
    tasks = [
        SearchTask("Python tutorial", "google", num_results=5),
        SearchTask("Python guide", "bing", num_results=5),
        SearchTask("Python documentation", "duckduckgo", num_results=3)
    ]
    
    return SearchPlan("Python Programming", tasks, time.time())


# Auto-use fixture to mock playwright import globally
@pytest.fixture(autouse=True)
def mock_playwright_import():
    """Automatically mock playwright imports for all tests."""
    with patch.dict('sys.modules', {
        'playwright': Mock(),
        'playwright.async_api': Mock(),
    }):
        yield


# Mark async tests
def pytest_collection_modifyitems(config, items):
    """Auto-mark async tests."""
    for item in items:
        if 'asyncio' in item.keywords or 'async' in item.name:
            item.add_marker(pytest.mark.asyncio)