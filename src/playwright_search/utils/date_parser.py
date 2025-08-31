"""Date parsing utilities."""

import re
from datetime import datetime, timedelta
from typing import Optional
import logging

from ..const import DATE_PATTERNS

logger = logging.getLogger(__name__)


class DateParser:
    """Parser for extracting dates from text snippets."""

    @staticmethod
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
        text = text.replace("\n", " ").strip()

        for pattern, date_type_func, converter in DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    date_type = date_type_func(match)
                    date = DateParser._convert_to_datetime(match, date_type, converter)
                    if date:
                        logger.debug(
                            f"Extracted date {date} from text: {text[:100]}..."
                        )
                        return date
                except (ValueError, OverflowError) as e:
                    logger.warning(
                        f"Failed to convert date match '{match.group()}': {e}"
                    )
                    continue

        return None

    @staticmethod
    def _convert_to_datetime(
        match: re.Match, date_type: str, converter: type
    ) -> Optional[datetime]:
        """Convert regex match to datetime based on date type."""
        now = datetime.now()

        if date_type == "days_ago":
            days = int(match.group(1))
            return now - timedelta(days=days)
        elif date_type == "hours_ago":
            hours = int(match.group(1))
            return now - timedelta(hours=hours)
        elif date_type == "minutes_ago":
            minutes = int(match.group(1))
            return now - timedelta(minutes=minutes)
        elif date_type == "weeks_ago":
            weeks = int(match.group(1))
            return now - timedelta(weeks=weeks)
        elif date_type == "months_ago":
            months = int(match.group(1))
            return now - timedelta(days=months * 30)
        elif date_type == "years_ago":
            years = int(match.group(1))
            return now - timedelta(days=years * 365)
        elif date_type == "absolute_date":
            year, month, day = (
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
            )
            return datetime(year, month, day)
        elif date_type == "absolute_date_us":
            month, day, year = (
                int(match.group(1)),
                int(match.group(2)),
                int(match.group(3)),
            )
            return datetime(year, month, day)
        elif date_type == "today":
            return now
        elif date_type == "yesterday":
            return now - timedelta(days=1)
        elif date_type == "last_week":
            return now - timedelta(weeks=1)
        elif date_type == "last_month":
            return now - timedelta(days=30)

        return None

    @staticmethod
    def is_recent(date: datetime, months: int = 3) -> bool:
        """
        Check if a date is within the specified number of months.

        Args:
            date: The date to check
            months: Number of months to consider as "recent"

        Returns:
            True if date is within the timeframe, False otherwise
        """
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        return date >= cutoff_date

    @staticmethod
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
