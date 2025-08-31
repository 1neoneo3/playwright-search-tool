#!/usr/bin/env python3
"""Simple test runner for core functionality without external dependencies."""

import sys
import os
from pathlib import Path
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_core_models():
    """Test core.models module."""
    print("🧪 Testing core.models...")
    
    # Mock playwright dependency
    with patch.dict('sys.modules', {
        'playwright': Mock(),
        'playwright.async_api': Mock(),
    }):
        from playwright_search.core.models import (
            SearchResult, SearchEngineConfig, SearchTask, SearchPlan, ParallelSearchResult
        )
        
        # Test SearchResult
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
            position=1,
            source="test"
        )
        assert result.title == "Test Title"
        assert result.timestamp is not None
        print("  ✅ SearchResult creation and defaults")
        
        # Test SearchEngineConfig
        config = SearchEngineConfig()
        assert config.headless is True
        assert config.timeout == 30000
        print("  ✅ SearchEngineConfig defaults")
        
        # Test SearchTask
        task = SearchTask("Python", "google")
        assert task.keyword == "Python"
        assert task.engine == "google"
        assert task.num_results == 10  # default
        print("  ✅ SearchTask defaults")
        
        # Test SearchPlan
        plan = SearchPlan("Test Topic", [task], time.time())
        assert plan.topic == "Test Topic"
        assert len(plan.tasks) == 1
        assert plan.created_at is not None
        print("  ✅ SearchPlan creation")

def test_validators():
    """Test validators module."""
    print("🧪 Testing utils.validators...")
    
    with patch.dict('sys.modules', {
        'playwright': Mock(),
        'playwright.async_api': Mock(),
    }):
        from playwright_search.utils.validators import InputValidator, ValidationError
        
        # Test valid engine
        assert InputValidator.validate_engine("google") == "google"
        assert InputValidator.validate_engine("GOOGLE") == "google"
        print("  ✅ Engine validation")
        
        # Test invalid engine
        try:
            InputValidator.validate_engine("invalid")
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass
        print("  ✅ Engine validation error handling")
        
        # Test engines list
        engines = InputValidator.validate_engines(["google", "bing"])
        assert "google" in engines
        assert "bing" in engines
        print("  ✅ Engines list validation")
        
        # Test timeout validation
        assert InputValidator.validate_timeout(30000) == 30000
        try:
            InputValidator.validate_timeout(500)  # Too small
            assert False, "Should have raised ValidationError"
        except ValidationError:
            pass
        print("  ✅ Timeout validation")
        
        # Test query validation
        assert InputValidator.validate_query("Python") == "Python"
        assert InputValidator.validate_query("  Python  ") == "Python"
        try:
            InputValidator.validate_query("")
            assert False, "Should have raised ValidationError" 
        except ValidationError:
            pass
        print("  ✅ Query validation")

def test_date_parser():
    """Test date_parser module."""
    print("🧪 Testing utils.date_parser...")
    
    with patch.dict('sys.modules', {
        'playwright': Mock(),
        'playwright.async_api': Mock(),
    }):
        from playwright_search.utils.date_parser import DateParser
        
        # Test recency score for None
        assert DateParser.calculate_recency_score(None) == 0.0
        print("  ✅ Recency score for None date")
        
        # Test current date recency score
        now = datetime.now()
        assert DateParser.calculate_recency_score(now) == 1.0
        print("  ✅ Current date recency score")
        
        # Test old date recency score
        old_date = now - timedelta(days=365)
        score = DateParser.calculate_recency_score(old_date)
        assert 0.1 <= score <= 0.5
        print("  ✅ Old date recency score")
        
        # Test is_recent
        recent = now - timedelta(days=60)  # 2 months ago
        assert DateParser.is_recent(recent, months=3) is True
        
        old = now - timedelta(days=120)  # 4 months ago  
        assert DateParser.is_recent(old, months=3) is False
        print("  ✅ is_recent functionality")

def test_result_processor():
    """Test result_processor module."""
    print("🧪 Testing utils.result_processor...")
    
    with patch.dict('sys.modules', {
        'playwright': Mock(),
        'playwright.async_api': Mock(),
    }):
        from playwright_search.utils.result_processor import ResultProcessor
        from playwright_search.core.models import SearchResult
        
        # Create test results
        results = [
            SearchResult("Title 1", "https://example.com/1", "Snippet 1", 1, "google"),
            SearchResult("Title 2", "https://example.com/2", "Snippet 2", 2, "google"),
            SearchResult("Duplicate", "https://example.com/1", "Different snippet", 3, "bing"),
        ]
        
        # Test deduplication
        unique = ResultProcessor.deduplicate_results(results)
        assert len(unique) == 2  # Should remove duplicate URL
        print("  ✅ Result deduplication")
        
        # Test limit results
        limited = ResultProcessor.limit_results(results, 2)
        assert len(limited) == 2
        print("  ✅ Result limiting")
        
        # Test add context
        with_context = ResultProcessor.add_search_context(results, "test context")
        assert all(hasattr(r, 'search_context') for r in with_context)
        print("  ✅ Search context addition")

def test_constants():
    """Test constants module."""
    print("🧪 Testing const.py...")
    
    with patch.dict('sys.modules', {
        'playwright': Mock(),
        'playwright.async_api': Mock(),
    }):
        from playwright_search.const import (
            ENGINE_ALIASES, PLAN_TEMPLATES, DEFAULT_MAX_CONCURRENT, 
            MIN_TIMEOUT, MAX_TIMEOUT
        )
        
        # Test engine aliases
        assert "google" in ENGINE_ALIASES
        assert "bing" in ENGINE_ALIASES
        assert "ddg" in ENGINE_ALIASES
        assert ENGINE_ALIASES["ddg"] == "duckduckgo"
        print("  ✅ Engine aliases")
        
        # Test plan templates
        assert "technology" in PLAN_TEMPLATES
        assert "research" in PLAN_TEMPLATES
        assert isinstance(PLAN_TEMPLATES["technology"], list)
        print("  ✅ Plan templates")
        
        # Test constants
        assert isinstance(DEFAULT_MAX_CONCURRENT, int)
        assert MIN_TIMEOUT < MAX_TIMEOUT
        print("  ✅ Timeout constants")

def test_parallel_search_plan_generator():
    """Test SearchPlanGenerator without async operations."""
    print("🧪 Testing SearchPlanGenerator...")
    
    with patch.dict('sys.modules', {
        'playwright': Mock(),
        'playwright.async_api': Mock(),
    }):
        from playwright_search.parallel_search import SearchPlanGenerator
        
        # Test comprehensive plan
        plan = SearchPlanGenerator.create_plan(
            topic="Machine Learning",
            plan_type="comprehensive",
            engines=["google", "bing"]
        )
        
        assert plan.topic == "Machine Learning"
        assert len(plan.tasks) > 0
        assert plan.created_at is not None
        
        # Check that both engines are used
        engines_used = set(task.engine for task in plan.tasks)
        assert "google" in engines_used
        assert "bing" in engines_used
        print("  ✅ Comprehensive plan creation")
        
        # Test custom plan
        custom_plan = SearchPlanGenerator.create_custom_plan(
            topic="Python",
            keywords=["Python tutorial", "Python guide"],
            engines=["google"]
        )
        
        assert custom_plan.topic == "Python"
        assert len(custom_plan.tasks) == 2  # 2 keywords × 1 engine
        
        keywords = set(task.keyword for task in custom_plan.tasks)
        assert "Python tutorial" in keywords
        assert "Python guide" in keywords
        print("  ✅ Custom plan creation")

def run_all_tests():
    """Run all available tests."""
    print("🚀 Running simplified test suite...")
    print(f"📁 Project root: {project_root}")
    print()
    
    test_functions = [
        test_core_models,
        test_validators,
        test_date_parser,
        test_result_processor,
        test_constants,
        test_parallel_search_plan_generator,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
            print(f"✅ {test_func.__name__} passed")
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__} failed: {e}")
            # Print traceback for debugging
            import traceback
            traceback.print_exc()
        print()
    
    # Summary
    print("=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n💥 {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())