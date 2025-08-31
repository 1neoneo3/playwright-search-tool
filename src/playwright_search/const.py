"""Constants and configuration for Playwright Search Tool."""

# Search Engine Configuration
DEFAULT_ENGINES = ["google", "bing"]
ENGINE_ALIASES = {
    "google": "google",
    "bing": "bing",
}

# Timeout Configuration (milliseconds)
DEFAULT_TIMEOUT = 30000
DEFAULT_TIMEOUT_SECONDS = 30
MIN_TIMEOUT = 5000
MAX_TIMEOUT = 120000

# Browser Configuration
DEFAULT_HEADLESS = True
DEFAULT_VIEWPORT = {"width": 1920, "height": 1080}
DEFAULT_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Browser Launch Arguments
BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-blink-features=AutomationControlled",
    "--disable-dev-shm-usage",
    "--disable-extensions",
    "--disable-gpu",
    "--disable-web-security",
    "--allow-running-insecure-content",
]

# Search Configuration
DEFAULT_NUM_RESULTS = 10
MAX_NUM_RESULTS = 50
DEFAULT_RECENT_MONTHS = 3
MAX_RECENT_MONTHS = 24

# Content Extraction Configuration
MAX_CONTENT_LENGTH = 3000
MIN_SNIPPET_LENGTH = 50
MAX_SNIPPET_LINES = 200
CONTENT_EXTRACTION_LIMIT = 3  # Number of results to extract content from

# Parallel Search Configuration
DEFAULT_MAX_CONCURRENT = 5
MIN_MAX_CONCURRENT = 1
MAX_MAX_CONCURRENT = 15
DEFAULT_PARALLEL_RESULTS_PER_SEARCH = 5

# Search Result Selectors
GOOGLE_SELECTORS = {
    "search_containers": "#search div[data-ved], #search .g, #search [jscontroller], .MjjYud",
    "title": "h3",
    "link": "a[href]:has(h3)",
    "snippet": '[data-snf="nke7rc"], .VwiC3b, .s3v9rd, .hgKElc, span, div',
}

BING_SELECTORS = {
    "results": ".b_algo",
    "title_link": "h2 a",
    "snippet": ".b_caption p, .b_descript",
}


# Content Extraction Selectors
CONTENT_SELECTORS = [
    "main article",
    "main",
    "article",
    '[role="main"]',
    ".content-body",
    ".post-body",
    ".entry-content",
    ".article-content",
    ".main-content",
    ".article-body",
    ".post-content",
    ".content",
]

# Elements to remove for content extraction
NOISE_SELECTORS = [
    "nav",
    "header",
    "footer",
    ".ads",
    ".advertisement",
    ".sidebar",
    ".menu",
    ".navigation",
    '[role="banner"]',
    '[role="navigation"]',
    ".cookie",
    ".popup",
    ".modal",
    ".related-posts",
    ".comments",
    ".social-share",
    ".breadcrumb",
]

# Date Patterns for extraction
DATE_PATTERNS = [
    # Relative dates (Japanese)
    (r"(\d+)\s*日前", lambda m: "days_ago", int),
    (r"(\d+)\s*時間前", lambda m: "hours_ago", int),
    (r"(\d+)\s*分前", lambda m: "minutes_ago", int),
    (r"(\d+)\s*週間前", lambda m: "weeks_ago", int),
    (r"(\d+)\s*ヶ月前", lambda m: "months_ago", int),
    (r"(\d+)\s*年前", lambda m: "years_ago", int),
    # Relative dates (English)
    (r"(\d+)\s*days?\s*ago", lambda m: "days_ago", int),
    (r"(\d+)\s*hours?\s*ago", lambda m: "hours_ago", int),
    (r"(\d+)\s*minutes?\s*ago", lambda m: "minutes_ago", int),
    (r"(\d+)\s*weeks?\s*ago", lambda m: "weeks_ago", int),
    (r"(\d+)\s*months?\s*ago", lambda m: "months_ago", int),
    (r"(\d+)\s*years?\s*ago", lambda m: "years_ago", int),
    # Absolute dates
    (r"(\d{4})年(\d{1,2})月(\d{1,2})日", lambda m: "absolute_date", tuple),
    (r"(\d{4})/(\d{1,2})/(\d{1,2})", lambda m: "absolute_date", tuple),
    (r"(\d{4})-(\d{1,2})-(\d{1,2})", lambda m: "absolute_date", tuple),
    (r"(\d{1,2})/(\d{1,2})/(\d{4})", lambda m: "absolute_date_us", tuple),
    (r"(\d{1,2})-(\d{1,2})-(\d{4})", lambda m: "absolute_date_us", tuple),
    # Keywords
    (r"今日|today", lambda m: "today", str),
    (r"昨日|yesterday", lambda m: "yesterday", str),
    (r"一週間前|last week", lambda m: "last_week", str),
    (r"先月|last month", lambda m: "last_month", str),
]

# Search Plan Templates
PLAN_TEMPLATES = {
    "technology": [
        "{topic} 最新情報",
        "{topic} 技術動向",
        "{topic} リリース情報",
        "{topic} tutorial guide",
        "{topic} best practices",
    ],
    "research": [
        "{topic} 研究",
        "{topic} 論文",
        "{topic} analysis report",
        "{topic} case study",
        "{topic} データ分析",
    ],
    "news": [
        "{topic} ニュース",
        "{topic} 最新",
        "{topic} latest news",
        "{topic} updates",
        "{topic} 発表",
    ],
    "comparison": [
        "{topic} 比較",
        "{topic} vs",
        "{topic} comparison",
        "{topic} 選び方",
        "{topic} review",
    ],
    "tutorial": [
        "{topic} 使い方",
        "{topic} 入門",
        "{topic} tutorial",
        "{topic} how to",
        "{topic} ガイド",
    ],
}

# CLI Configuration
DEFAULT_CLI_OUTPUT_JSON = False
DEFAULT_CLI_VERBOSE = False
MAX_DISPLAY_RESULTS = 50

# Error Messages
ERROR_MESSAGES = {
    "invalid_engine": "Invalid search engine. Supported engines: {engines}",
    "timeout_exceeded": "Search timeout exceeded: {timeout}ms",
    "no_results": "No search results found",
    "extraction_failed": "Failed to extract content from: {url}",
    "browser_failed": "Failed to start browser: {error}",
    "search_failed": "Search failed: {error}",
    "invalid_timeout": "Timeout must be between {min}ms and {max}ms",
    "invalid_concurrent": "Max concurrent searches must be between {min} and {max}",
    "plan_execution_failed": "Plan execution failed: {error}",
}

# Success Messages
SUCCESS_MESSAGES = {
    "plan_created": "Search plan created successfully",
    "search_completed": "Search completed successfully",
    "content_extracted": "Content extracted successfully",
    "parallel_search_completed": "Parallel search completed",
}

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# File Extensions
SUPPORTED_OUTPUT_FORMATS = ["json", "csv", "txt"]
DEFAULT_OUTPUT_FORMAT = "json"

# Performance Thresholds
PERFORMANCE_THRESHOLDS = {
    "fast_search": 5.0,  # seconds
    "slow_search": 30.0,  # seconds
    "max_results_warning": 30,
    "low_success_rate": 0.7,  # 70%
}
