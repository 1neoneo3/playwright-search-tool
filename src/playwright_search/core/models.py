"""Data models for Playwright Search Tool."""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime
import time

@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    url: str
    snippet: str
    position: int
    source: str = "unknown"
    timestamp: Optional[float] = None
    extracted_date: Optional[datetime] = None
    recency_score: float = 0.0
    content: Optional[str] = None
    search_context: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class SearchTask:
    """Represents a single search task for parallel execution."""
    keyword: str
    engine: str = "google"
    num_results: int = 10
    extract_content: bool = False
    recent_only: bool = False
    months: int = 3

@dataclass
class SearchPlan:
    """Represents a complete search plan with multiple tasks."""
    topic: str
    tasks: List[SearchTask]
    created_at: float
    
    def __post_init__(self):
        if not hasattr(self, 'created_at') or self.created_at is None:
            self.created_at = time.time()

@dataclass
class ParallelSearchResult:
    """Results from parallel search execution."""
    plan: SearchPlan
    results: Dict[str, List[SearchResult]]
    execution_time: float
    success_count: int
    error_count: int
    errors: Dict[str, str]

@dataclass
class SearchEngineConfig:
    """Configuration for search engine."""
    headless: bool = True
    timeout: int = 30000
    viewport: Dict[str, int] = None
    user_agent: str = None
    
    def __post_init__(self):
        if self.viewport is None:
            from ..const import DEFAULT_VIEWPORT
            self.viewport = DEFAULT_VIEWPORT.copy()
        if self.user_agent is None:
            from ..const import DEFAULT_USER_AGENT
            self.user_agent = DEFAULT_USER_AGENT