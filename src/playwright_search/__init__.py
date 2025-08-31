"""Playwright Search Tool - A powerful web search tool using Playwright."""

__version__ = "0.1.0"
__author__ = "Assistant"
__email__ = "assistant@example.com"

from .search_engine import SearchEngine, SearchResult
from .engines import GoogleEngine, BingEngine, DuckDuckGoEngine
from .cli import main

__all__ = [
    "SearchEngine",
    "SearchResult", 
    "GoogleEngine",
    "BingEngine",
    "DuckDuckGoEngine",
    "main"
]