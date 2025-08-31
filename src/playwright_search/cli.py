"""Command Line Interface for Playwright Search Tool."""

import asyncio
import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from typing import List, Optional
import sys
import time
import logging

from .engines import GoogleEngine, BingEngine, DuckDuckGoEngine
from .search_engine import SearchResult
from .content_extractor import ContentExtractor
from .date_utils import filter_and_sort_by_date

console = Console()
logger = logging.getLogger(__name__)

ENGINES = {
    'google': GoogleEngine,
    'bing': BingEngine, 
    'duckduckgo': DuckDuckGoEngine,
    'ddg': DuckDuckGoEngine,
    'all': None  # Special case for all engines
}


async def search_with_engine(engine_class, query: str, num_results: int, 
                           headless: bool, timeout: int, extract_content: bool) -> List[SearchResult]:
    """Perform search with a specific engine."""
    
    results = []
    engine_name = engine_class.__name__.replace('Engine', '')
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]Searching with {task.fields[engine]}..."),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("search", engine=engine_name)
        
        async with engine_class(headless=headless, timeout=timeout) as engine:
            results = await engine.search(query, num_results)
            
            if extract_content and results:
                progress.update(task, description=f"[bold green]Extracting content...")
                
                # Extract content with better error handling
                successful_extractions = 0
                for i, result in enumerate(results):
                    try:
                        progress.update(task, 
                                      description=f"[bold green]Extracting from {result.title[:30]}...")
                        content = await engine.extract_text_content(result.url)
                        if content:
                            result.content = content
                            successful_extractions += 1
                        progress.update(task, 
                                      description=f"[bold green]Extracted {i+1}/{len(results)} pages ({successful_extractions} successful)...")
                    except Exception as e:
                        console.print(f"[yellow]Warning: Failed to extract content from {result.url}: {str(e)}")
                
                if successful_extractions < len(results):
                    console.print(f"[yellow]Note: Successfully extracted content from {successful_extractions}/{len(results)} pages[/yellow]")
                        
    return results

def display_results(results: List[SearchResult], query: str, extract_content: bool, show_dates: bool = False):
    """Display search results in a formatted table."""
    
    if not results:
        console.print("[red]No search results found.")
        return
        
    # Group results by source
    by_source = {}
    for result in results:
        if result.source not in by_source:
            by_source[result.source] = []
        by_source[result.source].append(result)
        
    console.print(f"\n[bold green]Search Results for: [white]{query}[/white][/bold green]")
    console.print(f"[dim]Found {len(results)} results\n")
    
    for source, source_results in by_source.items():
        table = Table(
            title=f"{source.title()} Results",
            show_header=True,
            header_style="bold magenta",
            border_style="blue"
        )
        
        table.add_column("Pos", style="dim", width=4)
        table.add_column("Title", style="bold blue", min_width=30)
        table.add_column("URL", style="cyan", min_width=30)
        table.add_column("Snippet", min_width=40)
        if show_dates:
            table.add_column("Date", style="green", width=12)
        
        for result in source_results:
            # Truncate long text
            title = result.title[:80] + "..." if len(result.title) > 80 else result.title
            url = result.url[:60] + "..." if len(result.url) > 60 else result.url
            snippet = result.snippet[:100] + "..." if len(result.snippet) > 100 else result.snippet
            
            # Format date if available
            date_str = ""
            if show_dates and hasattr(result, 'extracted_date') and result.extracted_date:
                date_str = result.extracted_date.strftime("%Y-%m-%d")
            elif show_dates:
                date_str = "No date"
            
            if show_dates:
                table.add_row(
                    str(result.position),
                    title,
                    url,
                    snippet,
                    date_str
                )
            else:
                table.add_row(
                    str(result.position),
                    title,
                    url,
                    snippet
                )
            
            # Show extracted content if available
            if extract_content and hasattr(result, 'content') and result.content:
                # Split content into paragraphs for better display
                content_lines = result.content.split('\n')
                meaningful_lines = [line.strip() for line in content_lines if line.strip()][:3]  # First 3 paragraphs
                content_preview = '\n'.join(meaningful_lines)
                if len(result.content) > 500:
                    content_preview += "\n[dim]...(content truncated)[/dim]"
                
                table.add_row(
                    "",
                    "[dim]Content:[/dim]",
                    "",
                    f"[italic green]{content_preview}[/italic green]"
                )
                table.add_row("", "", "", "")  # Add spacing
                
        console.print(table)
        console.print()

def output_json_results(results: List[SearchResult]):
    """Output results in JSON format."""
    
    json_results = []
    for result in results:
        result_dict = {
            "title": result.title,
            "url": result.url,
            "snippet": result.snippet,
            "position": result.position,
            "source": result.source,
            "timestamp": result.timestamp
        }
        
        if hasattr(result, 'content'):
            result_dict["content"] = result.content
            
        if hasattr(result, 'extracted_date') and result.extracted_date:
            result_dict["extracted_date"] = result.extracted_date.isoformat()
            
        if hasattr(result, 'recency_score'):
            result_dict["recency_score"] = result.recency_score
            
        json_results.append(result_dict)
        
    print(json.dumps(json_results, indent=2, ensure_ascii=False))

@click.group()
def main():
    """Playwright Search Tool - Reliable web search using browser automation."""
    pass

@main.command()
@click.argument('query', type=str)  
@click.option('-n', '--num-results', default=10, help='Number of search results')
@click.option('-e', '--engine', default='google', type=click.Choice(['google', 'bing', 'duckduckgo', 'ddg', 'all']))
@click.option('--headless/--no-headless', default=True)
@click.option('--timeout', default=30)
@click.option('--extract-content', '-c', is_flag=True)
@click.option('--recent-only', '-r', is_flag=True, help='Only show results from the last 3 months')
@click.option('--sort-by-date', '-s', is_flag=True, help='Sort results by date (most recent first)')
@click.option('--months', default=3, help='Number of months to consider as recent (default: 3)')
@click.option('--json', 'output_json', is_flag=True)
@click.option('--verbose', '-v', is_flag=True)
def search(query: str, num_results: int, engine: str, headless: bool, 
           timeout: int, extract_content: bool, recent_only: bool, sort_by_date: bool, 
           months: int, output_json: bool, verbose: bool):
    """Search the web using Playwright."""
    
    if verbose:
        import logging
        logging.basicConfig(level=logging.INFO)
        
    if engine == 'all':
        engines = ['google', 'bing', 'duckduckgo']
    else:
        engines = [engine]
        
    all_results = []
    
    for engine_name in engines:
        engine_class = ENGINES[engine_name]
        results = asyncio.run(
            search_with_engine(engine_class, query, num_results, headless, timeout * 1000, extract_content)
        )
        all_results.extend(results)
        
    # Apply date filtering and sorting
    if recent_only or sort_by_date:
        scored_results = filter_and_sort_by_date(all_results, recent_only, months)
        filtered_results = [result for result, score in scored_results]
        
        # Show filtering stats
        if recent_only and len(filtered_results) < len(all_results):
            console.print(f"[yellow]Filtered to {len(filtered_results)} recent results (last {months} months) from {len(all_results)} total results[/yellow]\n")
        elif sort_by_date:
            console.print(f"[dim]Sorted {len(all_results)} results by date (most recent first)[/dim]\n")
            
        all_results = filtered_results
        
    if output_json:
        output_json_results(all_results)
    else:
        display_results(all_results, query, extract_content, recent_only or sort_by_date)

@main.command()
@click.argument('url', type=str)
@click.option('--headless/--no-headless', default=True)
@click.option('--timeout', default=30)
@click.option('--json', 'output_json', is_flag=True)
@click.option('--verbose', '-v', is_flag=True)
def extract(url: str, headless: bool, timeout: int, output_json: bool, verbose: bool):
    """Extract text content from a specific URL with improved content detection."""
    
    if verbose:
        import logging
        logging.basicConfig(level=logging.INFO)
    
    async def extract_content():
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Extracting content..."),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("extract", total=None)
            
            async with GoogleEngine(headless=headless, timeout=timeout * 1000) as engine:
                progress.update(task, description=f"[bold blue]Loading {url[:50]}...")
                content = await engine.extract_text_content(url)
                progress.update(task, description=f"[bold green]Content extracted!")
                return content
            
    content = asyncio.run(extract_content())
    
    if output_json:
        result = {
            "url": url,
            "content": content,
            "timestamp": time.time(),
            "word_count": len(content.split()) if content else 0,
            "character_count": len(content) if content else 0
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        if content:
            word_count = len(content.split())
            char_count = len(content)
            console.print(f"[bold green]Content extracted from: [cyan]{url}[/cyan][/bold green]")
            console.print(f"[dim]Words: {word_count} | Characters: {char_count}[/dim]\n")
            console.print(Panel(content, border_style="green", title="[bold]Extracted Content[/bold]"))
        else:
            console.print(f"[red]Failed to extract content from: {url}[/red]")
            console.print("[yellow]Try using --verbose flag to see detailed error information[/yellow]")

if __name__ == "__main__":
    main()