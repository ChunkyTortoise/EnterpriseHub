"""Temporal Processing for time-aware retrieval and recency boosting.

This module provides advanced temporal understanding capabilities including:
- Time-aware retrieval with temporal constraint extraction
- Recency boosting for ranking recent documents higher
- Temporal constraint extraction from natural language queries
- Integration with retrieval systems for time-based filtering
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime, timedelta
from collections import defaultdict
import math

import numpy as np

from src.core.exceptions import RetrievalError


class TemporalConstraintType(Enum):
    """Types of temporal constraints that can be extracted from queries."""

    ABSOLUTE_DATE = "absolute_date"  # Specific date: "January 15, 2024"
    ABSOLUTE_RANGE = "absolute_range"  # Date range: "from Jan 1 to Jan 31"
    RELATIVE = "relative"  # Relative time: "last week", "past 3 days"
    RECENCY = "recency"  # Recency preference: "recent", "latest", "new"
    DURATION = "duration"  # Duration: "for 2 weeks", "within 5 days"
    PERIODIC = "periodic"  # Periodic: "monthly", "weekly", "yearly"
    SEASONAL = "seasonal"  # Seasonal: "summer", "winter", "Q4"
    ONGOING = "ongoing"  # Ongoing/current: "current", "ongoing", "now"
    FUTURE = "future"  # Future-looking: "next week", "upcoming", "soon"
    HISTORICAL = "historical"  # Historical: "all time", "historical", "archive"


@dataclass
class TemporalConstraint:
    """Represents a temporal constraint extracted from a query.

    Attributes:
        constraint_type: Type of temporal constraint
        start_date: Start of temporal range (if applicable)
        end_date: End of temporal range (if applicable)
        raw_text: Original text that triggered this constraint
        confidence: Confidence score (0.0-1.0)
        granularity: Time granularity (day, week, month, year)
        is_exact: Whether the dates are exact or approximate
    """

    constraint_type: TemporalConstraintType
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    raw_text: str = ""
    confidence: float = 1.0
    granularity: str = "day"
    is_exact: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert constraint to dictionary."""
        return {
            "constraint_type": self.constraint_type.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "raw_text": self.raw_text,
            "confidence": self.confidence,
            "granularity": self.granularity,
            "is_exact": self.is_exact,
        }

    def is_satisfied_by(self, document_date: datetime) -> bool:
        """Check if a document date satisfies this constraint.

        Args:
            document_date: Date of the document to check

        Returns:
            True if document satisfies the constraint
        """
        if self.start_date and document_date < self.start_date:
            return False
        if self.end_date and document_date > self.end_date:
            return False
        return True


@dataclass
class RecencyBoostConfig:
    """Configuration for recency boosting.

    Attributes:
        enabled: Whether recency boosting is enabled
        decay_function: Decay function type ('exponential', 'linear', 'gaussian')
        half_life_days: Half-life for exponential decay (days)
        max_boost: Maximum boost multiplier for most recent documents
        min_boost: Minimum boost for oldest documents
        reference_date: Date to use as "now" (defaults to current time)
        time_field: Document field containing timestamp
    """

    enabled: bool = True
    decay_function: str = "exponential"  # 'exponential', 'linear', 'gaussian'
    half_life_days: float = 30.0
    max_boost: float = 2.0
    min_boost: float = 0.5
    reference_date: Optional[datetime] = None
    time_field: str = "created_at"

    def get_reference_date(self) -> datetime:
        """Get the reference date for recency calculation."""
        return self.reference_date or datetime.now()


@dataclass
class TemporalContext:
    """Complete temporal context extracted from a query.

    Attributes:
        constraints: List of temporal constraints
        primary_constraint: Main temporal constraint
        recency_preference: Whether user prefers recent results
        temporal_focus: Overall temporal focus (past, present, future)
        extracted_dates: All dates mentioned in query
        time_keywords: Keywords indicating temporal intent
    """

    constraints: List[TemporalConstraint] = field(default_factory=list)
    primary_constraint: Optional[TemporalConstraint] = None
    recency_preference: float = 0.5  # 0 = historical, 1 = recent
    temporal_focus: str = "present"  # 'past', 'present', 'future', 'any'
    extracted_dates: List[datetime] = field(default_factory=list)
    time_keywords: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "constraints": [c.to_dict() for c in self.constraints],
            "primary_constraint": self.primary_constraint.to_dict() if self.primary_constraint else None,
            "recency_preference": self.recency_preference,
            "temporal_focus": self.temporal_focus,
            "extracted_dates": [d.isoformat() for d in self.extracted_dates],
            "time_keywords": self.time_keywords,
        }


class TemporalProcessor:
    """Extract and process temporal constraints from queries.

    Provides comprehensive temporal understanding including absolute dates,
    relative time expressions, and recency preferences.

    Example:
        ```python
        processor = TemporalProcessor()

        # Extract temporal constraints
        context = processor.extract_temporal_context(
            "Show me houses listed in Rancho Cucamonga last week"
        )

        print(context.primary_constraint.constraint_type)
        # TemporalConstraintType.RELATIVE

        print(context.primary_constraint.start_date)
        # datetime object for 7 days ago
        ```
    """

    def __init__(self, reference_date: Optional[datetime] = None):
        """Initialize temporal processor.

        Args:
            reference_date: Date to use as "now" (defaults to current time)
        """
        self.reference_date = reference_date or datetime.now()
        self._patterns = self._build_patterns()
        self._relative_expressions = self._build_relative_expressions()
        self._seasonal_expressions = self._build_seasonal_expressions()

    def _build_patterns(self) -> Dict[str, re.Pattern]:
        """Build regex patterns for temporal extraction."""
        return {
            # Absolute dates
            "date_us": re.compile(
                r"\b(0?[1-9]|1[0-2])[/-](0?[1-9]|[12]\d|3[01])[/-](\d{4}|\d{2})\b",
                re.IGNORECASE,
            ),
            "date_iso": re.compile(r"\b(\d{4})[/-](0?[1-9]|1[0-2])[/-](0?[1-9]|[12]\d|3[01])\b"),
            "date_written": re.compile(
                r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
                r"(\d{1,2})(?:st|nd|rd|th)?(?:,\s*(\d{4}))?\b",
                re.IGNORECASE,
            ),
            "month_year": re.compile(
                r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
                r"(\d{4})\b",
                re.IGNORECASE,
            ),
            # Relative expressions
            "last_period": re.compile(
                r"\b(last|past|previous)\s+(\d+\s+)?(day|week|month|year|quarter)s?\b",
                re.IGNORECASE,
            ),
            "next_period": re.compile(
                r"\b(next|coming|upcoming)\s+(\d+\s+)?(day|week|month|year|quarter)s?\b",
                re.IGNORECASE,
            ),
            "ago": re.compile(r"\b(\d+)\s+(day|week|month|year)s?\s+ago\b", re.IGNORECASE),
            "from_now": re.compile(r"\b(in\s+)?(\d+)\s+(day|week|month|year)s?(\s+from\s+now)?\b", re.IGNORECASE),
            # Recency indicators
            "recent": re.compile(
                r"\b(recent|recently|latest|new|newest|current|fresh|just|lately)\b", re.IGNORECASE
            ),
            "historical": re.compile(
                r"\b(historical|archive|all\s+time|old|older|past\s+data)\b", re.IGNORECASE
            ),
            # Duration
            "within": re.compile(r"\bwithin\s+(the\s+)?(last\s+)?(\d+)\s+(day|week|month|year)s?\b", re.IGNORECASE),
            "for_duration": re.compile(r"\bfor\s+(the\s+)?(last\s+)?(\d+)\s+(day|week|month|year)s?\b", re.IGNORECASE),
            # Periodic
            "periodic": re.compile(r"\b(daily|weekly|monthly|yearly|quarterly|annually)\b", re.IGNORECASE),
            # Seasonal
            "season": re.compile(
                r"\b(spring|summer|fall|autumn|winter)\s+(of\s+)?(\d{4})?\b", re.IGNORECASE
            ),
            "quarter": re.compile(r"\b(Q[1-4]|quarter\s+[1-4])(\s+(of\s+)?(\d{4}))?\b", re.IGNORECASE),
            # Ongoing
            "ongoing": re.compile(r"\b(current|ongoing|present|now|today|active)\b", re.IGNORECASE),
            # Ranges
            "since": re.compile(r"\bsince\s+(\w+)\b", re.IGNORECASE),
            "between": re.compile(
                r"\b(between|from)\s+(.+?)\s+(and|to)\s+(.+?)\b", re.IGNORECASE
            ),
        }

    def _build_relative_expressions(self) -> Dict[str, Tuple[int, str]]:
        """Build mapping of relative time expressions to (amount, unit)."""
        return {
            # Days
            "today": (0, "day"),
            "yesterday": (1, "day"),
            "tomorrow": (-1, "day"),  # Negative for future
            # Weeks
            "this week": (0, "week"),
            "last week": (1, "week"),
            "next week": (-1, "week"),
            "past week": (1, "week"),
            # Months
            "this month": (0, "month"),
            "last month": (1, "month"),
            "next month": (-1, "month"),
            "past month": (1, "month"),
            # Years
            "this year": (0, "year"),
            "last year": (1, "year"),
            "next year": (-1, "year"),
            "past year": (1, "year"),
        }

    def _build_seasonal_expressions(self) -> Dict[str, Tuple[int, int]]:
        """Build mapping of seasons to (start_month, end_month)."""
        return {
            "spring": (3, 5),
            "summer": (6, 8),
            "fall": (9, 11),
            "autumn": (9, 11),
            "winter": (12, 2),
        }

    def extract_temporal_context(self, query: str) -> TemporalContext:
        """Extract complete temporal context from a query.

        Args:
            query: Input query string

        Returns:
            TemporalContext with all extracted temporal information
        """
        context = TemporalContext()

        # Extract various constraint types
        constraints = []
        constraints.extend(self._extract_absolute_dates(query))
        constraints.extend(self._extract_relative_expressions(query))
        constraints.extend(self._extract_recency_indicators(query))
        constraints.extend(self._extract_duration_constraints(query))
        constraints.extend(self._extract_seasonal_constraints(query))
        constraints.extend(self._extract_periodic_constraints(query))
        constraints.extend(self._extract_range_constraints(query))

        context.constraints = constraints

        # Determine primary constraint
        if constraints:
            # Prefer absolute dates, then relative, then recency
            priority_order = [
                TemporalConstraintType.ABSOLUTE_DATE,
                TemporalConstraintType.ABSOLUTE_RANGE,
                TemporalConstraintType.RELATIVE,
                TemporalConstraintType.RECENCY,
                TemporalConstraintType.DURATION,
            ]
            for priority in priority_order:
                for constraint in constraints:
                    if constraint.constraint_type == priority:
                        context.primary_constraint = constraint
                        break
                if context.primary_constraint:
                    break

            if not context.primary_constraint:
                context.primary_constraint = constraints[0]

        # Determine temporal focus
        context.temporal_focus = self._determine_temporal_focus(query, constraints)

        # Calculate recency preference
        context.recency_preference = self._calculate_recency_preference(query, constraints)

        # Extract time keywords
        context.time_keywords = self._extract_time_keywords(query)

        return context

    def _extract_absolute_dates(self, query: str) -> List[TemporalConstraint]:
        """Extract absolute date constraints."""
        constraints = []

        # US format: MM/DD/YYYY or MM-DD-YYYY
        for match in self._patterns["date_us"].finditer(query):
            month, day, year = match.groups()
            year = int(year)
            if year < 100:
                year += 2000 if year < 50 else 1900
            try:
                date = datetime(year, int(month), int(day))
                constraints.append(
                    TemporalConstraint(
                        constraint_type=TemporalConstraintType.ABSOLUTE_DATE,
                        start_date=date,
                        end_date=date,
                        raw_text=match.group(),
                        confidence=0.95,
                        granularity="day",
                        is_exact=True,
                    )
                )
            except ValueError:
                continue

        # ISO format: YYYY-MM-DD
        for match in self._patterns["date_iso"].finditer(query):
            year, month, day = match.groups()
            try:
                date = datetime(int(year), int(month), int(day))
                constraints.append(
                    TemporalConstraint(
                        constraint_type=TemporalConstraintType.ABSOLUTE_DATE,
                        start_date=date,
                        end_date=date,
                        raw_text=match.group(),
                        confidence=0.95,
                        granularity="day",
                        is_exact=True,
                    )
                )
            except ValueError:
                continue

        # Written format: "January 15, 2024"
        months = {
            "january": 1,
            "february": 2,
            "march": 3,
            "april": 4,
            "may": 5,
            "june": 6,
            "july": 7,
            "august": 8,
            "september": 9,
            "october": 10,
            "november": 11,
            "december": 12,
        }

        for match in self._patterns["date_written"].finditer(query):
            month_str, day, year = match.groups()
            month = months.get(month_str.lower())
            if month:
                year = int(year) if year else self.reference_date.year
                try:
                    date = datetime(year, month, int(day))
                    constraints.append(
                        TemporalConstraint(
                            constraint_type=TemporalConstraintType.ABSOLUTE_DATE,
                            start_date=date,
                            end_date=date,
                            raw_text=match.group(),
                            confidence=0.90,
                            granularity="day",
                            is_exact=True,
                        )
                    )
                except ValueError:
                    continue

        return constraints

    def _extract_relative_expressions(self, query: str) -> List[TemporalConstraint]:
        """Extract relative time expressions."""
        constraints = []
        query_lower = query.lower()

        # Check for known expressions
        for expr, (amount, unit) in self._relative_expressions.items():
            if expr in query_lower:
                start_date, end_date = self._calculate_relative_range(amount, unit)
                is_future = amount < 0

                constraints.append(
                    TemporalConstraint(
                        constraint_type=TemporalConstraintType.FUTURE
                        if is_future
                        else TemporalConstraintType.RELATIVE,
                        start_date=start_date,
                        end_date=end_date,
                        raw_text=expr,
                        confidence=0.85,
                        granularity=unit,
                        is_exact=False,
                    )
                )

        # Pattern-based extraction: "last 3 days", "past 2 weeks"
        for match in self._patterns["last_period"].finditer(query):
            _, num, unit = match.groups()
            amount = int(num) if num else 1
            start_date, end_date = self._calculate_relative_range(amount, unit)

            constraints.append(
                TemporalConstraint(
                    constraint_type=TemporalConstraintType.RELATIVE,
                    start_date=start_date,
                    end_date=end_date,
                    raw_text=match.group(),
                    confidence=0.80,
                    granularity=unit,
                    is_exact=False,
                )
            )

        # "X days ago"
        for match in self._patterns["ago"].finditer(query):
            num, unit = match.groups()
            start_date, end_date = self._calculate_relative_range(int(num), unit)

            constraints.append(
                TemporalConstraint(
                    constraint_type=TemporalConstraintType.RELATIVE,
                    start_date=start_date,
                    end_date=end_date,
                    raw_text=match.group(),
                    confidence=0.85,
                    granularity=unit,
                    is_exact=False,
                )
            )

        return constraints

    def _extract_recency_indicators(self, query: str) -> List[TemporalConstraint]:
        """Extract recency preference indicators."""
        constraints = []

        if self._patterns["recent"].search(query):
            # Recent = last 30 days by default
            start_date = self.reference_date - timedelta(days=30)
            constraints.append(
                TemporalConstraint(
                    constraint_type=TemporalConstraintType.RECENCY,
                    start_date=start_date,
                    end_date=self.reference_date,
                    raw_text="recent",
                    confidence=0.75,
                    granularity="day",
                    is_exact=False,
                )
            )

        if self._patterns["historical"].search(query):
            # Historical = all time, no date constraints
            constraints.append(
                TemporalConstraint(
                    constraint_type=TemporalConstraintType.HISTORICAL,
                    raw_text="historical",
                    confidence=0.70,
                    granularity="year",
                    is_exact=False,
                )
            )

        return constraints

    def _extract_duration_constraints(self, query: str) -> List[TemporalConstraint]:
        """Extract duration-based constraints."""
        constraints = []

        for match in self._patterns["within"].finditer(query):
            _, _, num, unit = match.groups()
            start_date = self._calculate_relative_range(int(num), unit)[0]

            constraints.append(
                TemporalConstraint(
                    constraint_type=TemporalConstraintType.DURATION,
                    start_date=start_date,
                    end_date=self.reference_date,
                    raw_text=match.group(),
                    confidence=0.80,
                    granularity=unit,
                    is_exact=False,
                )
            )

        return constraints

    def _extract_seasonal_constraints(self, query: str) -> List[TemporalConstraint]:
        """Extract seasonal constraints."""
        constraints = []

        for match in self._patterns["season"].finditer(query):
            season, _, year = match.groups()
            year = int(year) if year else self.reference_date.year

            if season.lower() in self._seasonal_expressions:
                start_month, end_month = self._seasonal_expressions[season.lower()]
                start_date = datetime(year, start_month, 1)
                if end_month < start_month:  # Winter spans years
                    end_date = datetime(year + 1, end_month, 28)
                else:
                    end_date = datetime(year, end_month, 28)

                constraints.append(
                    TemporalConstraint(
                        constraint_type=TemporalConstraintType.SEASONAL,
                        start_date=start_date,
                        end_date=end_date,
                        raw_text=match.group(),
                        confidence=0.80,
                        granularity="month",
                        is_exact=False,
                    )
                )

        return constraints

    def _extract_periodic_constraints(self, query: str) -> List[TemporalConstraint]:
        """Extract periodic constraints."""
        constraints = []

        for match in self._patterns["periodic"].finditer(query):
            period = match.group().lower()
            granularity = period.replace("ly", "")

            constraints.append(
                TemporalConstraint(
                    constraint_type=TemporalConstraintType.PERIODIC,
                    raw_text=match.group(),
                    confidence=0.70,
                    granularity=granularity,
                    is_exact=False,
                )
            )

        return constraints

    def _extract_range_constraints(self, query: str) -> List[TemporalConstraint]:
        """Extract date range constraints."""
        constraints = []

        for match in self._patterns["between"].finditer(query):
            constraints.append(
                TemporalConstraint(
                    constraint_type=TemporalConstraintType.ABSOLUTE_RANGE,
                    raw_text=match.group(),
                    confidence=0.60,
                    granularity="day",
                    is_exact=False,
                )
            )

        return constraints

    def _calculate_relative_range(
        self, amount: int, unit: str
    ) -> Tuple[datetime, datetime]:
        """Calculate date range from relative expression.

        Args:
            amount: Number of units
            unit: Time unit (day, week, month, year)

        Returns:
            Tuple of (start_date, end_date)
        """
        end_date = self.reference_date

        if unit == "day":
            start_date = end_date - timedelta(days=amount)
        elif unit == "week":
            start_date = end_date - timedelta(weeks=amount)
        elif unit == "month":
            # Approximate months
            start_date = end_date - timedelta(days=amount * 30)
        elif unit == "year":
            start_date = end_date - timedelta(days=amount * 365)
        elif unit == "quarter":
            start_date = end_date - timedelta(days=amount * 90)
        else:
            start_date = end_date - timedelta(days=amount)

        return start_date, end_date

    def _determine_temporal_focus(
        self, query: str, constraints: List[TemporalConstraint]
    ) -> str:
        """Determine overall temporal focus of query."""
        query_lower = query.lower()

        # Check for future indicators
        future_words = ["next", "upcoming", "coming", "future", "will", "plan", "schedule"]
        if any(w in query_lower for w in future_words):
            return "future"

        # Check for past/historical indicators
        past_words = ["past", "previous", "last", "ago", "history", "historical", "archive"]
        if any(w in query_lower for w in past_words):
            return "past"

        # Check constraint types
        future_types = {TemporalConstraintType.FUTURE}
        past_types = {
            TemporalConstraintType.RELATIVE,
            TemporalConstraintType.HISTORICAL,
        }

        type_counts = defaultdict(int)
        for c in constraints:
            type_counts[c.constraint_type] += 1

        if any(t in future_types for t in type_counts):
            return "future"
        if any(t in past_types for t in type_counts):
            return "past"

        return "present"

    def _calculate_recency_preference(
        self, query: str, constraints: List[TemporalConstraint]
    ) -> float:
        """Calculate recency preference score (0-1)."""
        query_lower = query.lower()

        # Strong recency indicators
        recent_words = ["recent", "latest", "new", "current", "fresh", "just", "today"]
        if any(w in query_lower for w in recent_words):
            return 0.9

        # Historical indicators
        historical_words = ["historical", "archive", "all time", "old", "past data"]
        if any(w in query_lower for w in historical_words):
            return 0.1

        # Check constraints
        for constraint in constraints:
            if constraint.constraint_type == TemporalConstraintType.RECENCY:
                return 0.8
            if constraint.constraint_type == TemporalConstraintType.HISTORICAL:
                return 0.2
            if constraint.constraint_type == TemporalConstraintType.RELATIVE:
                # More recent relative constraints = higher preference
                if constraint.start_date:
                    days_ago = (self.reference_date - constraint.start_date).days
                    if days_ago <= 7:
                        return 0.85
                    elif days_ago <= 30:
                        return 0.75
                    elif days_ago <= 90:
                        return 0.6

        return 0.5  # Neutral

    def _extract_time_keywords(self, query: str) -> List[str]:
        """Extract temporal keywords from query."""
        time_words = [
            "today",
            "yesterday",
            "tomorrow",
            "week",
            "month",
            "year",
            "day",
            "recent",
            "latest",
            "new",
            "current",
            "past",
            "future",
            "upcoming",
            "previous",
            "last",
            "next",
            "ago",
            "since",
            "until",
            "before",
            "after",
            "during",
            "while",
            "when",
        ]

        query_lower = query.lower()
        found = [word for word in time_words if word in query_lower]
        return found

    def update_reference_date(self, new_date: datetime) -> None:
        """Update the reference date for relative calculations.

        Args:
            new_date: New reference date
        """
        self.reference_date = new_date


class TimeAwareRetriever:
    """Apply temporal awareness to document retrieval.

    Provides recency boosting and temporal filtering for search results.

    Example:
        ```python
        retriever = TimeAwareRetriever()

        # Apply recency boost to search results
        boosted_results = retriever.apply_recency_boost(
            results,
            RecencyBoostConfig(half_life_days=30, max_boost=2.0)
        )

        # Filter by temporal constraints
        filtered = retriever.filter_by_constraints(
            results,
            context.constraints
        )
        ```
    """

    def __init__(self):
        """Initialize time-aware retriever."""
        self.config = RecencyBoostConfig()

    def apply_recency_boost(
        self,
        documents: List[Dict[str, Any]],
        config: Optional[RecencyBoostConfig] = None,
    ) -> List[Dict[str, Any]]:
        """Apply recency boosting to document scores.

        Args:
            documents: List of documents with scores and timestamps
            config: Recency boost configuration

        Returns:
            Documents with boosted scores
        """
        config = config or self.config

        if not config.enabled:
            return documents

        reference_date = config.get_reference_date()
        boosted = []

        for doc in documents:
            # Get document timestamp
            time_field = config.time_field
            if time_field not in doc:
                boosted.append(doc)
                continue

            doc_date = doc[time_field]
            if isinstance(doc_date, str):
                try:
                    doc_date = datetime.fromisoformat(doc_date.replace("Z", "+00:00"))
                except ValueError:
                    boosted.append(doc)
                    continue

            # Calculate age in days
            age_days = (reference_date - doc_date).total_seconds() / (24 * 3600)

            # Calculate boost factor
            boost = self._calculate_boost(age_days, config)

            # Apply boost to score
            boosted_doc = doc.copy()
            original_score = doc.get("score", 1.0)
            boosted_doc["original_score"] = original_score
            boosted_doc["recency_boost"] = boost
            boosted_doc["score"] = original_score * boost
            boosted_doc["age_days"] = age_days

            boosted.append(boosted_doc)

        # Re-sort by boosted score
        boosted.sort(key=lambda x: x.get("score", 0), reverse=True)

        return boosted

    def _calculate_boost(self, age_days: float, config: RecencyBoostConfig) -> float:
        """Calculate recency boost factor.

        Args:
            age_days: Age of document in days
            config: Boost configuration

        Returns:
            Boost multiplier
        """
        if config.decay_function == "exponential":
            # Exponential decay: boost = max_boost * (0.5 ^ (age / half_life))
            decay = 0.5 ** (age_days / config.half_life_days)
            boost = config.min_boost + (config.max_boost - config.min_boost) * decay

        elif config.decay_function == "linear":
            # Linear decay
            max_age = config.half_life_days * 3  # Effective cutoff
            if age_days >= max_age:
                boost = config.min_boost
            else:
                decay = 1 - (age_days / max_age)
                boost = config.min_boost + (config.max_boost - config.min_boost) * decay

        elif config.decay_function == "gaussian":
            # Gaussian decay
            sigma = config.half_life_days / 1.177  # Convert half-life to sigma
            decay = math.exp(-(age_days**2) / (2 * sigma**2))
            boost = config.min_boost + (config.max_boost - config.min_boost) * decay

        else:
            boost = 1.0

        return max(config.min_boost, min(config.max_boost, boost))

    def filter_by_constraints(
        self,
        documents: List[Dict[str, Any]],
        constraints: List[TemporalConstraint],
        time_field: str = "created_at",
    ) -> List[Dict[str, Any]]:
        """Filter documents by temporal constraints.

        Args:
            documents: List of documents
            constraints: Temporal constraints to apply
            time_field: Field containing document timestamp

        Returns:
            Filtered documents
        """
        if not constraints:
            return documents

        filtered = []
        for doc in documents:
            if time_field not in doc:
                filtered.append(doc)
                continue

            doc_date = doc[time_field]
            if isinstance(doc_date, str):
                try:
                    doc_date = datetime.fromisoformat(doc_date.replace("Z", "+00:00"))
                except ValueError:
                    filtered.append(doc)
                    continue

            # Check all constraints
            satisfies_all = all(
                constraint.is_satisfied_by(doc_date) for constraint in constraints
            )

            if satisfies_all:
                filtered.append(doc)

        return filtered

    def get_temporal_stats(
        self, documents: List[Dict[str, Any]], time_field: str = "created_at"
    ) -> Dict[str, Any]:
        """Get temporal statistics for a document set.

        Args:
            documents: List of documents
            time_field: Field containing timestamps

        Returns:
            Dictionary with temporal statistics
        """
        dates = []
        for doc in documents:
            if time_field in doc:
                date = doc[time_field]
                if isinstance(date, str):
                    try:
                        date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                dates.append(date)

        if not dates:
            return {"count": 0}

        dates.sort()
        now = datetime.now()
        ages = [(now - d).total_seconds() / (24 * 3600) for d in dates]

        return {
            "count": len(dates),
            "oldest": dates[0].isoformat(),
            "newest": dates[-1].isoformat(),
            "median_age_days": np.median(ages) if ages else 0,
            "mean_age_days": np.mean(ages) if ages else 0,
            "time_span_days": (dates[-1] - dates[0]).total_seconds() / (24 * 3600)
            if len(dates) > 1
            else 0,
        }
