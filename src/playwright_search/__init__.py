"""Playwright Search Tool - A powerful web search tool using Playwright."""

__version__ = "0.4.0"
__author__ = "Assistant"
__email__ = "assistant@example.com"

from .core.base import BaseSearchEngine
from .core.models import SearchResult, SearchEngineConfig
from .engines import GoogleEngine, BingEngine, DuckDuckGoEngine
from .parallel_search import SearchPlanGenerator, ParallelSearchEngine
from .cli import main

__all__ = [
    "BaseSearchEngine",
    "SearchResult",
    "SearchEngineConfig",
    "GoogleEngine",
    "BingEngine",
    "DuckDuckGoEngine",
    "SearchPlanGenerator",
    "ParallelSearchEngine",
    "main",
]
