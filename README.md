# Playwright Search Tool

A powerful, reliable web search tool using Playwright for browser automation. This tool bypasses many of the limitations of traditional web scraping by using a real browser engine.

## Features

- **Multiple Search Engines**: Google, Bing, DuckDuckGo support
- **Browser Automation**: Uses Playwright for reliable, JavaScript-enabled searches
- **Content Extraction**: Extract full page content from search results
- **Date Filtering**: Filter results by recency and sort by date
- **Parallel Search**: Execute multiple searches concurrently with intelligent planning
- **Rich CLI Interface**: Beautiful terminal output with progress indicators
- **JSON Output**: Machine-readable output for automation
- **Stealth Mode**: Avoids detection with realistic browser behavior
- **Fast & Concurrent**: Parallel processing for multiple engines and keywords

## Installation

### Using uv (Recommended)

```bash
# Clone or download the project
cd search-tool

# Install dependencies and build
uv sync
uv run playwright install chromium

# Install globally
uv tool install .
```

### Using pip

```bash
cd search-tool
pip install -e .
playwright install chromium
```

## Quick Start

### Basic Search
```bash
# Simple search
psearch "Python programming tutorials"

# Specify number of results
psearch "machine learning" -n 5

# Use different search engine
psearch "web scraping" -e bing

# Search all engines
psearch "AI news" -e all -n 3
```

### Advanced Usage
```bash
# Extract full content from result pages
psearch "data science" --extract-content

# Output in JSON format
psearch "web development" --json

# Verbose logging
psearch "debugging tips" --verbose

# Non-headless mode (show browser)
psearch "automation testing" --no-headless

# Filter to recent results only (last 3 months)
psearch "Python news" --recent-only

# Sort results by date (most recent first)
psearch "AI developments" --sort-by-date

# Custom recency window (last 6 months)
psearch "tech trends" --recent-only --months 6

# Parallel search with automatic keyword planning
psearch plan "AI agents" --type technology --execute

# Custom keywords with parallel execution
psearch plan "Claude Code" --keywords "Claude Code 使い方,Claude Code MCP" --execute

# Create search plan without executing
psearch plan "machine learning" --type research
```

### Content Extraction
```bash
# Extract content from specific URL
psearch extract https://example.com/article

# Extract with JSON output
psearch extract https://example.com/article --json
```

## CLI Reference

### Main Search Command

```
psearch search [OPTIONS] QUERY

Options:
  -n, --num-results INTEGER      Number of search results (default: 10)
  -e, --engine [google|bing|duckduckgo|ddg|all]  
                                 Search engine to use (default: google)
  --headless / --no-headless     Run browser in headless mode (default: headless)
  --timeout INTEGER              Timeout in seconds (default: 30)
  -c, --extract-content          Extract full content from result pages
  -r, --recent-only              Only show results from the last 3 months
  -s, --sort-by-date             Sort results by date (most recent first)
  --months INTEGER               Number of months to consider as recent (default: 3)
  --json                         Output results in JSON format
  -v, --verbose                  Enable verbose logging
```

### Parallel Search Planning Command

```
psearch plan [OPTIONS] TOPIC

Options:
  --type [comprehensive|technology|research|news|comparison|tutorial]
                                 Type of search plan (default: comprehensive)
  --engines TEXT                 Comma-separated list of engines (default: google,bing)
  --keywords TEXT                Custom keywords (overrides plan type)
  -n, --num-results INTEGER     Number of results per search (default: 5)
  --recent-only                  Filter for recent results only
  --months INTEGER               Number of months for recent filtering (default: 3)
  --execute                      Execute the plan immediately
  --max-concurrent INTEGER       Maximum concurrent searches (default: 5)
  --headless / --no-headless     Run browser in headless mode (default: headless)
  --timeout INTEGER              Timeout per search in seconds (default: 30)
  --json                         Output results in JSON format
  -v, --verbose                  Enable verbose logging
```

### Content Extraction Command

```
psearch extract [OPTIONS] URL

Options:
  --headless / --no-headless     Run browser in headless mode (default: headless)
  --timeout INTEGER              Timeout in seconds (default: 30)
  --json                         Output in JSON format
```

## Usage Examples

### 1. Simple Web Search
```bash
psearch "best Python libraries 2024"
```

### 2. Multi-Engine Search
```bash
psearch "machine learning frameworks" -e all -n 5
```

### 3. Content Extraction
```bash
psearch "Django tutorial" -n 3 --extract-content
```

### 4. JSON Output for Automation
```bash
psearch "API documentation" --json > results.json
```

### 5. Specific Engine Search
```bash
psearch "privacy-focused search" -e duckduckgo -n 10
```

## API Usage

You can also use the search engines programmatically:

```python
import asyncio
from playwright_search import GoogleEngine, SearchResult

async def main():
    async with GoogleEngine(headless=True) as engine:
        results = await engine.search("Python tutorials", num_results=5)
        
        for result in results:
            print(f"Title: {result.title}")
            print(f"URL: {result.url}")
            print(f"Snippet: {result.snippet}")
            print("---")

if __name__ == "__main__":
    asyncio.run(main())
```

## Supported Search Engines

| Engine | Identifier | Features |
|--------|------------|----------|
| Google | `google` | Most comprehensive results |
| Bing | `bing` | Good alternative with different ranking |
| DuckDuckGo | `duckduckgo`, `ddg` | Privacy-focused, no tracking |

## Configuration

### Environment Variables

- `PLAYWRIGHT_HEADLESS`: Set to `false` to run in non-headless mode
- `PLAYWRIGHT_TIMEOUT`: Default timeout in milliseconds (default: 30000)
- `PLAYWRIGHT_SLOW_MO`: Slow down operations by N milliseconds

### Browser Settings

The tool automatically configures the browser with:
- Realistic user agent strings
- Standard viewport size (1920x1080)
- Disabled automation detection
- Random delays between actions

## Troubleshooting

### Common Issues

1. **Browser Installation**
   ```bash
   playwright install chromium
   ```

2. **Permission Errors**
   ```bash
   # Make sure you have proper permissions
   chmod +x ~/.local/bin/psearch
   ```

3. **Network Issues**
   - Check your internet connection
   - Try different search engines with `-e` flag
   - Increase timeout with `--timeout 60`

4. **JavaScript/Content Issues**
   - Use `--no-headless` to see what's happening
   - Enable verbose logging with `--verbose`

### Performance Tips

- Use headless mode (default) for better performance
- Adjust timeout based on your network speed
- Use specific engines instead of `all` for faster results
- Limit the number of results with `-n` flag

## Development

### Setting up Development Environment

```bash
git clone <repository>
cd search-tool

# Install in development mode
uv sync
uv run playwright install

# Run tests
uv run pytest

# Run linting
uv run ruff check src/
```

### Adding New Search Engines

1. Create a new class inheriting from `SearchEngine`
2. Implement `search()` and `get_search_url()` methods
3. Add to `ENGINES` dict in `cli.py`

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Changelog

### v0.1.0
- Initial release
- Google, Bing, DuckDuckGo support
- Content extraction
- Rich CLI interface
- JSON output support