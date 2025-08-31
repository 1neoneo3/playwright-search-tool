"""Date extraction and filtering utilities for search results."""

import re
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)

# Date patterns for various formats
DATE_PATTERNS = [
    # Relative dates
    (r'(\d+)\s*日前', lambda m: datetime.now() - timedelta(days=int(m.group(1)))),
    (r'(\d+)\s*時間前', lambda m: datetime.now() - timedelta(hours=int(m.group(1)))),
    (r'(\d+)\s*分前', lambda m: datetime.now() - timedelta(minutes=int(m.group(1)))),
    (r'(\d+)\s*週間前', lambda m: datetime.now() - timedelta(weeks=int(m.group(1)))),
    (r'(\d+)\s*ヶ月前', lambda m: datetime.now() - timedelta(days=int(m.group(1)) * 30)),
    (r'(\d+)\s*年前', lambda m: datetime.now() - timedelta(days=int(m.group(1)) * 365)),
    
    # English relative dates
    (r'(\d+)\s*days?\s*ago', lambda m: datetime.now() - timedelta(days=int(m.group(1)))),
    (r'(\d+)\s*hours?\s*ago', lambda m: datetime.now() - timedelta(hours=int(m.group(1)))),
    (r'(\d+)\s*minutes?\s*ago', lambda m: datetime.now() - timedelta(minutes=int(m.group(1)))),
    (r'(\d+)\s*weeks?\s*ago', lambda m: datetime.now() - timedelta(weeks=int(m.group(1)))),
    (r'(\d+)\s*months?\s*ago', lambda m: datetime.now() - timedelta(days=int(m.group(1)) * 30)),
    (r'(\d+)\s*years?\s*ago', lambda m: datetime.now() - timedelta(days=int(m.group(1)) * 365)),
    
    # Absolute dates - Japanese
    (r'(\d{4})年(\d{1,2})月(\d{1,2})日', 
     lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
    (r'(\d{4})/(\d{1,2})/(\d{1,2})', 
     lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
    (r'(\d{4})-(\d{1,2})-(\d{1,2})', 
     lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
    
    # Absolute dates - English
    (r'(\d{1,2})/(\d{1,2})/(\d{4})', 
     lambda m: datetime(int(m.group(3)), int(m.group(1)), int(m.group(2)))),
    (r'(\d{1,2})-(\d{1,2})-(\d{4})', 
     lambda m: datetime(int(m.group(3)), int(m.group(1)), int(m.group(2)))),
    
    # Month year patterns
    (r'(\d{4})年(\d{1,2})月', 
     lambda m: datetime(int(m.group(1)), int(m.group(2)), 1)),
    
    # Special keywords
    (r'今日|today', lambda m: datetime.now()),
    (r'昨日|yesterday', lambda m: datetime.now() - timedelta(days=1)),
    (r'一週間前|last week', lambda m: datetime.now() - timedelta(weeks=1)),
    (r'先月|last month', lambda m: datetime.now() - timedelta(days=30)),
]

def extract_date_from_snippet(text: str) -> Optional[datetime]:
    """
    Extract date from search result snippet text.
    
    Args:
        text: The snippet text to analyze
        
    Returns:
        datetime object if date found, None otherwise
    """
    if not text:
        return None
        
    # Clean text for better matching
    text = text.replace('\n', ' ').strip()
    
    for pattern, converter in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                date = converter(match)
                logger.debug(f"Extracted date {date} from text: {text[:100]}...")
                return date
            except (ValueError, OverflowError) as e:
                logger.warning(f"Failed to convert date match '{match.group()}': {e}")
                continue
                
    return None

def is_recent(date: datetime, months: int = 3) -> bool:
    """
    Check if a date is within the specified number of months.
    
    Args:
        date: The date to check
        months: Number of months to consider as "recent" (default: 3)
        
    Returns:
        True if date is within the timeframe, False otherwise
    """
    cutoff_date = datetime.now() - timedelta(days=months * 30)
    return date >= cutoff_date

def calculate_recency_score(date: Optional[datetime]) -> float:
    """
    Calculate a recency score (0-1) for a date.
    
    Args:
        date: The date to score, None if no date found
        
    Returns:
        Float between 0-1, where 1 is most recent
    """
    if date is None:
        return 0.0
        
    days_ago = (datetime.now() - date).days
    
    # Score based on recency
    if days_ago < 0:  # Future date, treat as today
        return 1.0
    elif days_ago <= 7:  # Within a week
        return 1.0
    elif days_ago <= 30:  # Within a month
        return 0.9 - (days_ago - 7) * 0.1 / 23  # Linear decay from 0.9 to 0.8
    elif days_ago <= 90:  # Within 3 months
        return 0.8 - (days_ago - 30) * 0.3 / 60  # Linear decay from 0.8 to 0.5
    elif days_ago <= 365:  # Within a year
        return 0.5 - (days_ago - 90) * 0.3 / 275  # Linear decay from 0.5 to 0.2
    else:  # Older than a year
        return max(0.1, 0.2 - (days_ago - 365) * 0.1 / 365)  # Slow decay to minimum

def filter_and_sort_by_date(results: List[any], 
                           recent_only: bool = False, 
                           months: int = 3) -> List[Tuple[any, float]]:
    """
    Filter and sort search results by date recency.
    
    Args:
        results: List of search results with extracted_date attribute
        recent_only: If True, only return results within the timeframe
        months: Number of months to consider as "recent"
        
    Returns:
        List of (result, recency_score) tuples sorted by recency
    """
    scored_results = []
    
    for result in results:
        date = getattr(result, 'extracted_date', None)
        recency_score = calculate_recency_score(date)
        
        if recent_only and date and not is_recent(date, months):
            continue
            
        scored_results.append((result, recency_score))
    
    # Sort by recency score (highest first)
    scored_results.sort(key=lambda x: x[1], reverse=True)
    
    return scored_results