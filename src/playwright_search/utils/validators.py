"""Input validation utilities."""

from typing import List
from ..const import (
    ENGINE_ALIASES,
    MIN_TIMEOUT,
    MAX_TIMEOUT,
    MIN_MAX_CONCURRENT,
    MAX_MAX_CONCURRENT,
    MAX_NUM_RESULTS,
    MAX_RECENT_MONTHS,
    ERROR_MESSAGES,
)


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


class InputValidator:
    """Validator for user inputs and configuration."""

    @staticmethod
    def validate_engine(engine: str) -> str:
        """
        Validate and normalize engine name.

        Args:
            engine: Engine name to validate

        Returns:
            Normalized engine name

        Raises:
            ValidationError: If engine is invalid
        """
        if not engine:
            raise ValidationError("Engine name cannot be empty")

        engine = engine.lower()

        if engine in ENGINE_ALIASES:
            return ENGINE_ALIASES[engine]

        raise ValidationError(
            ERROR_MESSAGES["invalid_engine"].format(
                engines=", ".join(ENGINE_ALIASES.keys())
            )
        )

    @staticmethod
    def validate_engines(engines: List[str]) -> List[str]:
        """
        Validate and normalize a list of engine names.

        Args:
            engines: List of engine names

        Returns:
            List of normalized engine names
        """
        if not engines:
            raise ValidationError("At least one engine must be specified")

        validated_engines = []
        for engine in engines:
            validated_engines.append(InputValidator.validate_engine(engine))

        return list(set(validated_engines))  # Remove duplicates

    @staticmethod
    def validate_timeout(timeout: int) -> int:
        """
        Validate timeout value.

        Args:
            timeout: Timeout value in milliseconds

        Returns:
            Validated timeout value

        Raises:
            ValidationError: If timeout is invalid
        """
        if (
            not isinstance(timeout, int)
            or timeout < MIN_TIMEOUT
            or timeout > MAX_TIMEOUT
        ):
            raise ValidationError(
                ERROR_MESSAGES["invalid_timeout"].format(
                    min=MIN_TIMEOUT, max=MAX_TIMEOUT
                )
            )

        return timeout

    @staticmethod
    def validate_concurrent_limit(max_concurrent: int) -> int:
        """
        Validate max concurrent limit.

        Args:
            max_concurrent: Maximum concurrent searches

        Returns:
            Validated concurrent limit

        Raises:
            ValidationError: If limit is invalid
        """
        if (
            not isinstance(max_concurrent, int)
            or max_concurrent < MIN_MAX_CONCURRENT
            or max_concurrent > MAX_MAX_CONCURRENT
        ):
            raise ValidationError(
                ERROR_MESSAGES["invalid_concurrent"].format(
                    min=MIN_MAX_CONCURRENT, max=MAX_MAX_CONCURRENT
                )
            )

        return max_concurrent

    @staticmethod
    def validate_num_results(num_results: int) -> int:
        """
        Validate number of results.

        Args:
            num_results: Number of results to fetch

        Returns:
            Validated number of results

        Raises:
            ValidationError: If number is invalid
        """
        if (
            not isinstance(num_results, int)
            or num_results <= 0
            or num_results > MAX_NUM_RESULTS
        ):
            raise ValidationError(
                f"Number of results must be between 1 and {MAX_NUM_RESULTS}"
            )

        return num_results

    @staticmethod
    def validate_months(months: int) -> int:
        """
        Validate months value for date filtering.

        Args:
            months: Number of months

        Returns:
            Validated months value

        Raises:
            ValidationError: If months is invalid
        """
        if not isinstance(months, int) or months <= 0 or months > MAX_RECENT_MONTHS:
            raise ValidationError(f"Months must be between 1 and {MAX_RECENT_MONTHS}")

        return months

    @staticmethod
    def validate_query(query: str) -> str:
        """
        Validate search query.

        Args:
            query: Search query string

        Returns:
            Validated query string

        Raises:
            ValidationError: If query is invalid
        """
        if not query or not query.strip():
            raise ValidationError("Search query cannot be empty")

        query = query.strip()

        if len(query) > 1000:
            raise ValidationError("Search query is too long (max 1000 characters)")

        return query

    @staticmethod
    def validate_keywords(keywords: List[str]) -> List[str]:
        """
        Validate list of keywords.

        Args:
            keywords: List of keyword strings

        Returns:
            Validated list of keywords

        Raises:
            ValidationError: If keywords are invalid
        """
        if not keywords:
            raise ValidationError("At least one keyword must be provided")

        validated_keywords = []
        for keyword in keywords:
            validated_keyword = InputValidator.validate_query(keyword)
            if validated_keyword:
                validated_keywords.append(validated_keyword)

        if not validated_keywords:
            raise ValidationError("No valid keywords provided")

        return validated_keywords

    @staticmethod
    def validate_plan_type(plan_type: str) -> str:
        """
        Validate plan type.

        Args:
            plan_type: Plan type string

        Returns:
            Validated plan type

        Raises:
            ValidationError: If plan type is invalid
        """
        from ..const import PLAN_TEMPLATES

        valid_types = list(PLAN_TEMPLATES.keys()) + ["comprehensive"]

        if plan_type not in valid_types:
            raise ValidationError(
                f"Invalid plan type. Valid types: {', '.join(valid_types)}"
            )

        return plan_type
