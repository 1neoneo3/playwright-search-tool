"""Parallel search functionality for efficient multi-keyword searches."""

import asyncio
import time
from typing import List, Dict, Optional, Tuple, Any
import logging

from .engines import GoogleEngine, BingEngine, DuckDuckGoEngine
from .core.models import SearchResult, SearchTask, SearchPlan, ParallelSearchResult, SearchEngineConfig
from .utils.result_processor import ResultProcessor
from .const import PLAN_TEMPLATES

logger = logging.getLogger(__name__)

class SearchPlanGenerator:
    """Generates search plans for comprehensive topic research."""
    
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
            for template_list in PLAN_TEMPLATES.values():
                templates.extend(template_list[:2])  # Take first 2 from each category
        else:
            templates = PLAN_TEMPLATES.get(plan_type, PLAN_TEMPLATES['technology'])
        
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
    
    def __init__(self, max_concurrent: int = 5, config: Optional[SearchEngineConfig] = None):
        """
        Initialize parallel search engine.
        
        Args:
            max_concurrent: Maximum number of concurrent searches
            config: Optional SearchEngineConfig to use for engines
        """
        self.max_concurrent = max_concurrent
        self.config = config or SearchEngineConfig()
        
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
                    async with engine_class(config=self.config) as engine:
                        search_results = await engine.search(task.keyword, task.num_results)
                        
                        # Apply date filtering if requested
                        if task.recent_only and search_results:
                            scored_results = ResultProcessor.filter_and_sort_by_date(search_results, task.recent_only, task.months)
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
        
        # Collect all results and add search context
        for task_key, results in parallel_result.results.items():
            results_with_context = ResultProcessor.add_search_context(results, task_key)
            all_results.extend(results_with_context)
        
        # Deduplicate and merge
        return ResultProcessor.merge_results([all_results], deduplicate=True)
    
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