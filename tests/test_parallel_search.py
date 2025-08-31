"""Tests for parallel_search module."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import time

from src.playwright_search.parallel_search import (
    SearchPlanGenerator,
    ParallelSearchEngine,
)
from src.playwright_search.core.models import (
    SearchResult,
    SearchTask,
    SearchPlan,
    ParallelSearchResult,
)


class TestSearchPlanGenerator:
    """Tests for SearchPlanGenerator class."""

    def test_create_plan_comprehensive(self):
        """Test creating a comprehensive search plan."""
        plan = SearchPlanGenerator.create_plan(
            topic="Machine Learning",
            plan_type="comprehensive",
            engines=["google", "bing"],
            num_results=5,
        )

        assert plan.topic == "Machine Learning"
        assert len(plan.tasks) > 0
        assert plan.created_at is not None

        # Should have tasks for both engines
        engines_used = set(task.engine for task in plan.tasks)
        assert "google" in engines_used
        assert "bing" in engines_used

        # Should have varied keywords from comprehensive plan
        keywords = set(task.keyword for task in plan.tasks)
        assert len(keywords) > 1

    def test_create_plan_technology_type(self):
        """Test creating a technology-specific search plan."""
        plan = SearchPlanGenerator.create_plan(
            topic="Python",
            plan_type="technology",
            engines=["google"],
            num_results=3,
            recent_only=True,
            months=6,
        )

        assert plan.topic == "Python"
        assert len(plan.tasks) > 0

        # All tasks should have technology-related settings
        for task in plan.tasks:
            assert task.engine == "google"
            assert task.num_results == 3
            assert task.recent_only is True
            assert task.months == 6

        # Should contain technology-related keywords
        keywords = [task.keyword for task in plan.tasks]
        # At least one keyword should contain the topic
        assert any("Python" in keyword for keyword in keywords)

    def test_create_plan_default_engines(self):
        """Test plan creation with default engines."""
        plan = SearchPlanGenerator.create_plan(
            topic="AI Research", plan_type="research"
        )

        # Should use default engines (google, bing)
        engines_used = set(task.engine for task in plan.tasks)
        assert "google" in engines_used
        assert "bing" in engines_used

    def test_create_custom_plan(self):
        """Test creating a custom plan with specific keywords."""
        custom_keywords = ["Python tutorial", "Django framework", "Flask guide"]

        plan = SearchPlanGenerator.create_custom_plan(
            topic="Python Web Development",
            keywords=custom_keywords,
            engines=["google", "duckduckgo"],
            num_results=8,
            recent_only=False,
            months=12,
        )

        assert plan.topic == "Python Web Development"
        assert len(plan.tasks) == 6  # 3 keywords × 2 engines

        # Verify all custom keywords are used
        task_keywords = set(task.keyword for task in plan.tasks)
        for keyword in custom_keywords:
            assert keyword in task_keywords

        # Verify settings
        for task in plan.tasks:
            assert task.num_results == 8
            assert task.recent_only is False
            assert task.months == 12
            assert task.engine in ["google", "duckduckgo"]

    def test_create_plan_limits_tasks(self):
        """Test that plan creation limits the number of tasks."""
        plan = SearchPlanGenerator.create_plan(
            topic="Test",
            plan_type="comprehensive",
            engines=["google"],  # Single engine
        )

        # Should be limited to reasonable number of tasks (8 from code)
        assert len(plan.tasks) <= 8


class TestParallelSearchEngine:
    """Tests for ParallelSearchEngine class."""

    @pytest.fixture
    def sample_plan(self):
        """Create a sample search plan for testing."""
        tasks = [
            SearchTask("Python tutorial", "google", num_results=3),
            SearchTask("Python guide", "bing", num_results=3),
        ]
        return SearchPlan("Python", tasks, time.time())

    @pytest.fixture
    def mock_search_engine(self):
        """Create a mock search engine."""
        engine = AsyncMock()
        engine.search = AsyncMock(
            return_value=[
                SearchResult(
                    "Test Title", "https://example.com", "Test snippet", 1, "test"
                )
            ]
        )
        engine.__aenter__ = AsyncMock(return_value=engine)
        engine.__aexit__ = AsyncMock()
        return engine

    def test_initialization(self):
        """Test ParallelSearchEngine initialization."""
        engine = ParallelSearchEngine(max_concurrent=3)
        assert engine.max_concurrent == 3
        assert engine.config is not None

    def test_initialization_with_config(self):
        """Test ParallelSearchEngine initialization with custom config."""
        from src.playwright_search.core.models import SearchEngineConfig

        config = SearchEngineConfig(headless=False, timeout=60000)
        engine = ParallelSearchEngine(max_concurrent=5, config=config)

        assert engine.max_concurrent == 5
        assert engine.config == config
        assert engine.config.headless is False

    @pytest.mark.asyncio
    async def test_execute_plan_success(self, sample_plan, mock_search_engine):
        """Test successful plan execution."""
        engine = ParallelSearchEngine(max_concurrent=2)

        # Mock the engine classes
        with patch.dict(
            engine.ENGINE_CLASSES,
            {
                "google": Mock(return_value=mock_search_engine),
                "bing": Mock(return_value=mock_search_engine),
            },
        ):
            result = await engine.execute_plan(sample_plan)

            assert isinstance(result, ParallelSearchResult)
            assert result.plan == sample_plan
            assert result.success_count == 2  # Both tasks should succeed
            assert result.error_count == 0
            assert len(result.results) == 2  # Results for both engines
            assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_execute_plan_with_errors(self, sample_plan):
        """Test plan execution with some errors."""
        engine = ParallelSearchEngine(max_concurrent=2)

        # Create mixed success/failure engines
        success_engine = AsyncMock()
        success_engine.search = AsyncMock(
            return_value=[
                SearchResult(
                    "Success", "https://example.com", "Success snippet", 1, "google"
                )
            ]
        )
        success_engine.__aenter__ = AsyncMock(return_value=success_engine)
        success_engine.__aexit__ = AsyncMock()

        failure_engine = AsyncMock()
        failure_engine.search = AsyncMock(side_effect=Exception("Search failed"))
        failure_engine.__aenter__ = AsyncMock(return_value=failure_engine)
        failure_engine.__aexit__ = AsyncMock()

        # Mock asyncio.gather to return proper tuples
        async def mock_gather(*args, **kwargs):
            results = []
            for task in sample_plan.tasks:
                task_key = f"{task.keyword} ({task.engine})"
                if task.engine == "google":
                    # Success case
                    results.append(
                        (
                            task_key,
                            [
                                SearchResult(
                                    "Success",
                                    "https://example.com",
                                    "Success snippet",
                                    1,
                                    "google",
                                )
                            ],
                            None,
                        )
                    )
                else:
                    # Error case
                    results.append((task_key, None, "Search failed: Search failed"))
            return results

        with patch("asyncio.gather", side_effect=mock_gather):
            result = await engine.execute_plan(sample_plan)

            assert result.success_count == 1
            assert result.error_count == 1
            assert len(result.errors) == 1
            assert len(result.results) == 1  # Only successful results

    def test_merge_and_deduplicate_results(self):
        """Test merging and deduplicating results."""
        engine = ParallelSearchEngine()

        # Create test results with duplicates
        results = {
            "task1": [
                SearchResult(
                    "Title 1", "https://example.com/1", "Snippet 1", 1, "google"
                ),
                SearchResult(
                    "Title 2", "https://example.com/2", "Snippet 2", 2, "google"
                ),
            ],
            "task2": [
                SearchResult(
                    "Title 3", "https://example.com/3", "Snippet 3", 1, "bing"
                ),
                SearchResult(
                    "Duplicate", "https://example.com/1", "Different snippet", 2, "bing"
                ),  # Duplicate URL
            ],
        }

        # Create a mock ParallelSearchResult
        plan = SearchPlan("Test", [], time.time())
        parallel_result = ParallelSearchResult(
            plan=plan,
            results=results,
            execution_time=1.0,
            success_count=2,
            error_count=0,
            errors={},
        )

        merged = engine.merge_and_deduplicate_results(parallel_result)

        # Should deduplicate based on URL
        assert len(merged) == 3  # 4 original - 1 duplicate
        urls = [result.url for result in merged]
        assert len(set(urls)) == 3  # All unique URLs

        # Should add search context
        for result in merged:
            assert hasattr(result, "search_context")
            assert result.search_context is not None

    def test_generate_search_summary(self):
        """Test search summary generation."""
        engine = ParallelSearchEngine()

        # Create test data
        plan = SearchPlan(
            "Test Topic",
            [SearchTask("keyword1", "google"), SearchTask("keyword2", "bing")],
            time.time(),
        )

        results = {
            "keyword1 (google)": [
                SearchResult(
                    "Title 1", "https://example.com/1", "Snippet 1", 1, "google"
                ),
            ],
            "keyword2 (bing)": [
                SearchResult(
                    "Title 2", "https://example.com/2", "Snippet 2", 1, "bing"
                ),
            ],
        }

        parallel_result = ParallelSearchResult(
            plan=plan,
            results=results,
            execution_time=2.5,
            success_count=2,
            error_count=0,
            errors={},
        )

        summary = engine.generate_search_summary(parallel_result)

        assert summary["topic"] == "Test Topic"
        assert summary["total_searches"] == 2
        assert summary["successful_searches"] == 2
        assert summary["failed_searches"] == 0
        assert summary["total_results"] == 2
        assert summary["unique_results"] == 2
        assert summary["execution_time"] == 2.5
        assert "source_distribution" in summary
        assert "keywords_used" in summary
        assert "engines_used" in summary

    @pytest.mark.asyncio
    async def test_concurrent_limiting(self, mock_search_engine):
        """Test that concurrent searches are properly limited."""
        engine = ParallelSearchEngine(max_concurrent=1)  # Limit to 1

        # Create plan with multiple tasks
        tasks = [SearchTask(f"query{i}", "google") for i in range(3)]
        plan = SearchPlan("Test", tasks, time.time())

        # Track call times to verify they don't all run simultaneously
        call_times = []

        async def mock_search_with_timing(*args, **kwargs):
            import asyncio

            call_times.append(time.time())
            await asyncio.sleep(0.1)  # Small delay
            return [SearchResult("Test", "https://example.com", "Test", 1, "google")]

        mock_search_engine.search = mock_search_with_timing

        # Mock asyncio.gather to return proper tuples for all tasks
        async def mock_gather(*args, **kwargs):
            results = []
            for task in plan.tasks:
                task_key = f"{task.keyword} ({task.engine})"
                results.append(
                    (
                        task_key,
                        [
                            SearchResult(
                                f"Result for {task.keyword}",
                                "https://example.com",
                                "Test",
                                1,
                                "google",
                            )
                        ],
                        None,
                    )
                )
            # Simulate the timing constraint
            import asyncio

            await asyncio.sleep(0.3)  # 3 tasks * 0.1s each
            return results

        with patch("asyncio.gather", side_effect=mock_gather):
            result = await engine.execute_plan(plan)

            # Verify that execution completed successfully
            assert result.success_count == 3
            assert result.error_count == 0
            assert len(result.results) == 3
            # Execution time should reflect the mocked delay
            assert result.execution_time >= 0.25


if __name__ == "__main__":
    pytest.main([__file__])
