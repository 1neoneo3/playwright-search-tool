"""Test helpers to handle dependency injection and mocking."""

import sys
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def setup_mock_playwright():
    """Set up comprehensive playwright mocking for tests."""
    # Mock all playwright-related modules
    mock_modules = {
        'playwright': Mock(),
        'playwright.async_api': Mock(),
    }
    
    # Create mock playwright components
    mock_playwright = Mock()
    mock_browser = Mock()
    mock_context = Mock()
    mock_page = Mock()
    
    # Configure async methods
    mock_playwright.chromium.launch = Mock(return_value=mock_browser)
    mock_browser.new_context = Mock(return_value=mock_context)
    mock_context.new_page = Mock(return_value=mock_page)
    
    # Configure cleanup methods
    mock_page.close = Mock()
    mock_context.close = Mock()  
    mock_browser.close = Mock()
    mock_playwright.stop = Mock()
    
    # Configure page interaction methods
    mock_page.goto = Mock()
    mock_page.wait_for_selector = Mock()
    mock_page.query_selector_all = Mock(return_value=[])
    mock_page.evaluate = Mock(return_value="")
    mock_page.set_default_timeout = Mock()
    mock_page.add_init_script = Mock()
    
    # Mock the async_playwright function
    mock_modules['playwright.async_api'].async_playwright = Mock(return_value=Mock(start=Mock(return_value=mock_playwright)))
    
    return mock_modules

def mock_dependencies():
    """Context manager to mock all external dependencies."""
    mock_modules = setup_mock_playwright()
    
    return patch.dict('sys.modules', mock_modules)

class MockSearchResult:
    """Mock SearchResult for testing without imports."""
    def __init__(self, title, url, snippet, position, source="test", **kwargs):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.position = position
        self.source = source
        self.timestamp = kwargs.get('timestamp', 1234567890.0)
        self.extracted_date = kwargs.get('extracted_date')
        self.recency_score = kwargs.get('recency_score', 0.0)
        self.content = kwargs.get('content')
        self.search_context = kwargs.get('search_context')

class MockSearchEngineConfig:
    """Mock SearchEngineConfig for testing without imports."""
    def __init__(self, headless=True, timeout=30000, viewport=None, user_agent=None):
        self.headless = headless
        self.timeout = timeout
        self.viewport = viewport or {"width": 1920, "height": 1080}
        self.user_agent = user_agent or "Mozilla/5.0 (test)"