"""Tests for engines base functionality."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from src.playwright_search.core.base import BaseSearchEngine
from src.playwright_search.core.models import SearchEngineConfig, SearchResult


class TestSearchEngine(BaseSearchEngine):
    """Test implementation of BaseSearchEngine."""

    def get_search_url(self, query: str) -> str:
        return f"https://example.com/search?q={query}"

    async def search(self, query: str, num_results: int = 10):
        # Simple mock implementation
        return [
            SearchResult(
                title=f"Result for {query}",
                url="https://example.com/result",
                snippet=f"Snippet for {query}",
                position=1,
                source="test",
            )
        ]


class TestBaseSearchEngine:
    """Tests for BaseSearchEngine abstract class."""

    @pytest.fixture
    def mock_playwright(self):
        """Create mock playwright components."""
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

        return {
            "playwright": mock_playwright,
            "browser": mock_browser,
            "context": mock_context,
            "page": mock_page,
        }

    def test_config_initialization(self):
        """Test SearchEngine initialization with config."""
        config = SearchEngineConfig(
            headless=False, timeout=60000, viewport={"width": 1366, "height": 768}
        )

        engine = TestSearchEngine(config=config)
        assert engine.config == config
        assert engine.browser is None
        assert engine.page is None

    def test_default_config(self):
        """Test SearchEngine initialization with default config."""
        engine = TestSearchEngine()
        assert engine.config.headless is True
        assert engine.config.timeout == 30000

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_playwright):
        """Test async context manager functionality."""
        with patch(
            "src.playwright_search.core.base.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright["playwright"]
            )

            async with TestSearchEngine() as engine:
                assert engine.playwright == mock_playwright["playwright"]
                assert engine.browser == mock_playwright["browser"]
                assert engine.page == mock_playwright["page"]

                # Verify initialization sequence
                mock_playwright["playwright"].chromium.launch.assert_called_once()
                mock_playwright["browser"].new_context.assert_called_once()
                mock_playwright["context"].new_page.assert_called_once()

            # Verify cleanup sequence
            mock_playwright["page"].close.assert_called_once()
            mock_playwright["context"].close.assert_called_once()
            mock_playwright["browser"].close.assert_called_once()
            mock_playwright["playwright"].stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_method(self, mock_playwright):
        """Test start method functionality."""
        engine = TestSearchEngine()

        with patch(
            "src.playwright_search.core.base.async_playwright"
        ) as mock_async_playwright:
            mock_async_playwright.return_value.start = AsyncMock(
                return_value=mock_playwright["playwright"]
            )

            await engine.start()

            # Verify browser launch with correct config
            mock_playwright["playwright"].chromium.launch.assert_called_once()
            launch_args = mock_playwright["playwright"].chromium.launch.call_args
            assert launch_args[1]["headless"] is True  # Default config

            # Verify context creation
            mock_playwright["browser"].new_context.assert_called_once()
            context_args = mock_playwright["browser"].new_context.call_args
            assert "viewport" in context_args[1]
            assert "user_agent" in context_args[1]

    @pytest.mark.asyncio
    async def test_close_method(self, mock_playwright):
        """Test close method functionality."""
        engine = TestSearchEngine()

        # Set up engine with mock components
        engine.playwright = mock_playwright["playwright"]
        engine.browser = mock_playwright["browser"]
        engine.context = mock_playwright["context"]
        engine.page = mock_playwright["page"]

        await engine.close()

        # Verify cleanup sequence
        mock_playwright["page"].close.assert_called_once()
        mock_playwright["context"].close.assert_called_once()
        mock_playwright["browser"].close.assert_called_once()
        mock_playwright["playwright"].stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_method_partial_cleanup(self, mock_playwright):
        """Test close method with partial initialization."""
        engine = TestSearchEngine()

        # Only set some components (simulating partial initialization)
        engine.browser = mock_playwright["browser"]
        engine.playwright = mock_playwright["playwright"]

        await engine.close()

        # Should handle missing components gracefully
        mock_playwright["browser"].close.assert_called_once()
        mock_playwright["playwright"].stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_random_delay(self):
        """Test random_delay method."""
        engine = TestSearchEngine()

        with patch("asyncio.sleep") as mock_sleep:
            await engine.random_delay(1.0, 2.0)

            # Should have called sleep with a value between 1.0 and 2.0
            mock_sleep.assert_called_once()
            sleep_value = mock_sleep.call_args[0][0]
            assert 1.0 <= sleep_value <= 2.0

    @pytest.mark.asyncio
    async def test_extract_text_content(self, mock_playwright):
        """Test extract_text_content method."""
        engine = TestSearchEngine()
        engine.page = mock_playwright["page"]
        engine.config = SearchEngineConfig()

        # Mock page responses
        mock_playwright["page"].goto = AsyncMock()
        mock_playwright["page"].evaluate = AsyncMock(
            return_value="Removed noise elements"
        )
        mock_playwright["page"].wait_for_selector = AsyncMock()
        mock_element = AsyncMock()
        mock_element.inner_text = AsyncMock(return_value="Main content text here")
        mock_playwright["page"].wait_for_selector.return_value = mock_element

        url = "https://example.com/article"
        content = await engine.extract_text_content(url)

        # Verify navigation and content extraction
        mock_playwright["page"].goto.assert_called_once_with(
            url, wait_until="networkidle", timeout=engine.config.timeout
        )
        assert content is not None
        assert len(content) > 0

    @pytest.mark.asyncio
    async def test_extract_text_content_fallback(self, mock_playwright):
        """Test extract_text_content with fallback to body."""
        engine = TestSearchEngine()
        engine.page = mock_playwright["page"]
        engine.config = SearchEngineConfig()

        # Mock page responses - main selectors fail, fallback succeeds
        mock_playwright["page"].goto = AsyncMock()
        mock_playwright["page"].evaluate = AsyncMock(
            side_effect=[
                None,  # Noise removal
                "Fallback body content",  # Body fallback
            ]
        )
        mock_playwright["page"].wait_for_selector = AsyncMock(
            side_effect=Exception("No main content")
        )

        url = "https://example.com/article"
        content = await engine.extract_text_content(url)

        assert content == "Fallback body content"

    @pytest.mark.asyncio
    async def test_extract_text_content_error_handling(self, mock_playwright):
        """Test extract_text_content error handling."""
        engine = TestSearchEngine()
        engine.page = mock_playwright["page"]
        engine.config = SearchEngineConfig()

        # Mock page navigation failure
        mock_playwright["page"].goto = AsyncMock(
            side_effect=Exception("Navigation failed")
        )

        url = "https://example.com/article"
        content = await engine.extract_text_content(url)

        assert content is None

    def test_clean_content(self):
        """Test _clean_content method."""
        engine = TestSearchEngine()

        # Test with normal content
        content = "Line 1\nLine 2 with enough content\nLine 3 is also long enough\nShort\nLine 5"
        cleaned = engine._clean_content(content)

        assert "Line 1" not in cleaned  # Too short, should be removed
        assert "Line 2 with enough content" in cleaned
        assert "Line 3 is also long enough" in cleaned
        assert "Short" not in cleaned  # Too short
        assert "Line 5" not in cleaned  # Too short

    def test_clean_content_max_length(self):
        """Test _clean_content with max length limit."""
        engine = TestSearchEngine()

        # Create content longer than MAX_CONTENT_LENGTH
        long_content = "A" * 10000 + "\n" + "B" * 10000  # 20k+ chars
        cleaned = engine._clean_content(long_content)

        # Should be truncated to MAX_CONTENT_LENGTH (8000 from const.py)
        assert len(cleaned) <= 8000

    def test_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError."""
        # This is implicitly tested by using TestSearchEngine which implements them
        # The abstract base class cannot be instantiated without implementing these methods

        # Verify our test implementation works
        engine = TestSearchEngine()
        assert engine.get_search_url("test") == "https://example.com/search?q=test"

    def test_get_search_url_abstract(self):
        """Test that BaseSearchEngine cannot be instantiated without implementing abstract methods."""
        with pytest.raises(TypeError):
            # Should raise TypeError because BaseSearchEngine has abstract methods
            BaseSearchEngine()


if __name__ == "__main__":
    pytest.main([__file__])
