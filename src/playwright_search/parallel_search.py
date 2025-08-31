"""Parallel search functionality for efficient multi-keyword searches."""

import asyncio
import time
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging

from .engines import GoogleEngine, BingEngine, DuckDuckGoEngine
from .search_engine import SearchResult
from .date_utils import filter_and_sort_by_date

logger = logging.getLogger(__name__)

@dataclass
class SearchTask:
    """Represents a single search task."""
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

class SearchPlanGenerator:
    """Generates search plans for comprehensive topic research."""
    
    TOPIC_TEMPLATES = {
        'technology': [
            '{topic} 最新情報',
            '{topic} 技術動向',
            '{topic} リリース情報',
            '{topic} tutorial guide',
            '{topic} best practices'
        ],
        'research': [
            '{topic} 研究',
            '{topic} 論文',
            '{topic} analysis report',
            '{topic} case study',
            '{topic} データ分析'
        ],
        'news': [
            '{topic} ニュース',
            '{topic} 最新',
            '{topic} latest news',
            '{topic} updates',
            '{topic} 発表'
        ],
        'comparison': [
            '{topic} 比較',
            '{topic} vs',
            '{topic} comparison',
            '{topic} 選び方',
            '{topic} review'
        ],
        'tutorial': [
            '{topic} 使い方',
            '{topic} 入門',
            '{topic} tutorial',
            '{topic} how to',
            '{topic} ガイド'
        ]
    }
    
    @classmethod
    def create_plan(cls, topic: str, plan_type: str = 'comprehensive', 
                   engines: List[str] = None, num_results: int = 5,
                   recent_only: bool = True, months: int = 3) -> SearchPlan:
        """
        Create a search plan for the given topic.
        
        Args:
            topic: Main topic to search for
            plan_type: Type of plan ('comprehensive', 'technology', 'research', 'news', 'comparison', 'tutorial')
            engines: List of engines to use (default: ['google', 'bing'])
            num_results: Number of results per search
            recent_only: Whether to filter for recent results
            months: Number of months for recent filtering
        """
        if engines is None:
            engines = ['google', 'bing']
            
        tasks = []
        
        if plan_type == 'comprehensive':
            # Use multiple template types for comprehensive coverage
            templates = []
            for template_list in cls.TOPIC_TEMPLATES.values():
                templates.extend(template_list[:2])  # Take first 2 from each category
        else:
            templates = cls.TOPIC_TEMPLATES.get(plan_type, cls.TOPIC_TEMPLATES['technology'])
        
        # Generate search tasks
        for template in templates[:8]:  # Limit to 8 searches to avoid overwhelming
            keyword = template.format(topic=topic)
            for engine in engines:
                tasks.append(SearchTask(
                    keyword=keyword,
                    engine=engine,
                    num_results=num_results,
                    recent_only=recent_only,
                    months=months
                ))
        
        return SearchPlan(
            topic=topic,
            tasks=tasks,
            created_at=time.time()
        )
    
    @classmethod
    def create_custom_plan(cls, topic: str, keywords: List[str], 
                          engines: List[str] = None, num_results: int = 5,
                          recent_only: bool = True, months: int = 3) -> SearchPlan:
        """Create a search plan with custom keywords."""
        if engines is None:
            engines = ['google']
            
        tasks = []
        for keyword in keywords:
            for engine in engines:
                tasks.append(SearchTask(
                    keyword=keyword,
                    engine=engine,
                    num_results=num_results,
                    recent_only=recent_only,
                    months=months
                ))
        
        return SearchPlan(
            topic=topic,
            tasks=tasks,
            created_at=time.time()
        )

class ParallelSearchEngine:
    """Executes search plans with parallel processing."""
    
    ENGINE_CLASSES = {
        'google': GoogleEngine,
        'bing': BingEngine,
        'duckduckgo': DuckDuckGoEngine,
        'ddg': DuckDuckGoEngine
    }
    
    def __init__(self, max_concurrent: int = 5, headless: bool = True, timeout: int = 30):
        """
        Initialize parallel search engine.
        
        Args:
            max_concurrent: Maximum number of concurrent searches
            headless: Whether to run browsers in headless mode
            timeout: Timeout for individual searches in seconds
        """
        self.max_concurrent = max_concurrent
        self.headless = headless
        self.timeout = timeout * 1000  # Convert to milliseconds
        
    async def execute_plan(self, plan: SearchPlan) -> ParallelSearchResult:
        """
        Execute a search plan with parallel processing.
        
        Args:
            plan: SearchPlan to execute
            
        Returns:
            ParallelSearchResult containing all results and execution info
        """
        start_time = time.time()
        results = {}
        errors = {}
        success_count = 0
        error_count = 0
        
        # Create semaphore to limit concurrent searches
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def execute_single_task(task: SearchTask) -> Tuple[str, Optional[List[SearchResult]], Optional[str]]:
            """Execute a single search task."""
            async with semaphore:
                task_key = f"{task.keyword} ({task.engine})"
                try:
                    engine_class = self.ENGINE_CLASSES[task.engine]
                    async with engine_class(headless=self.headless, timeout=self.timeout) as engine:
                        search_results = await engine.search(task.keyword, task.num_results)
                        
                        # Apply date filtering if requested
                        if task.recent_only and search_results:
                            scored_results = filter_and_sort_by_date(search_results, task.recent_only, task.months)
                            search_results = [result for result, score in scored_results]
                        
                        # Extract content if requested (limited to first few results for performance)
                        if task.extract_content and search_results:
                            for i, result in enumerate(search_results[:3]):  # Limit content extraction
                                try:
                                    content = await engine.extract_text_content(result.url)
                                    if content:
                                        result.content = content
                                except Exception as e:
                                    logger.warning(f"Failed to extract content from {result.url}: {e}")
                        
                        return task_key, search_results, None
                        
                except Exception as e:
                    error_msg = f"Search failed: {str(e)}"
                    logger.error(f"Task '{task_key}' failed: {error_msg}")
                    return task_key, None, error_msg
        
        # Execute all tasks in parallel
        tasks_futures = [execute_single_task(task) for task in plan.tasks]
        completed_tasks = await asyncio.gather(*tasks_futures, return_exceptions=True)
        
        # Process results
        for result in completed_tasks:
            if isinstance(result, Exception):
                error_count += 1
                errors[f"Task {error_count}"] = str(result)
            else:
                task_key, search_results, error = result
                if error:
                    error_count += 1
                    errors[task_key] = error
                else:
                    success_count += 1
                    results[task_key] = search_results or []
        
        execution_time = time.time() - start_time
        
        return ParallelSearchResult(
            plan=plan,
            results=results,
            execution_time=execution_time,
            success_count=success_count,
            error_count=error_count,
            errors=errors
        )
    
    def merge_and_deduplicate_results(self, parallel_result: ParallelSearchResult) -> List[SearchResult]:
        """
        Merge results from all searches and remove duplicates.
        
        Args:
            parallel_result: Result from parallel search execution
            
        Returns:
            List of unique SearchResult objects, sorted by relevance
        """
        all_results = []
        seen_urls = set()
        
        # Collect all results
        for task_key, results in parallel_result.results.items():
            for result in results:
                # Use URL as deduplication key
                if result.url not in seen_urls:
                    seen_urls.add(result.url)
                    # Add search context to result
                    result.search_context = task_key
                    all_results.append(result)
        
        # Sort by recency score if available, then by position
        all_results.sort(key=lambda x: (getattr(x, 'recency_score', 0), -x.position), reverse=True)
        
        return all_results
    
    def generate_search_summary(self, parallel_result: ParallelSearchResult) -> Dict[str, Any]:
        """Generate a summary of search results."""
        merged_results = self.merge_and_deduplicate_results(parallel_result)
        
        # Count results by source
        source_counts = {}
        for result in merged_results:
            source_counts[result.source] = source_counts.get(result.source, 0) + 1
        
        # Count results with dates
        dated_results = len([r for r in merged_results if hasattr(r, 'extracted_date') and r.extracted_date])
        
        return {
            'topic': parallel_result.plan.topic,
            'total_searches': len(parallel_result.plan.tasks),
            'successful_searches': parallel_result.success_count,
            'failed_searches': parallel_result.error_count,
            'total_results': sum(len(results) for results in parallel_result.results.values()),
            'unique_results': len(merged_results),
            'results_with_dates': dated_results,
            'execution_time': parallel_result.execution_time,
            'source_distribution': source_counts,
            'keywords_used': list(set(task.keyword for task in parallel_result.plan.tasks)),
            'engines_used': list(set(task.engine for task in parallel_result.plan.tasks))
        }