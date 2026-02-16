"""Data quality checking: schema validation, completeness, freshness."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class QualityCheckResult:
    field_name: str
    check_type: str
    passed: bool
    message: str


@dataclass
class QualityReport:
    total_checks: int
    passed: int
    failed: int
    score: float  # 0.0-1.0
    results: list[QualityCheckResult]


class DataQualityChecker:
    """Validates extracted data for completeness, format, and freshness."""

    def check_not_null(self, field_name: str, value: Any) -> QualityCheckResult:
        passed = value is not None and value != ""
        return QualityCheckResult(
            field_name=field_name, check_type="not_null",
            passed=passed,
            message=f"{field_name} is present" if passed else f"{field_name} is null or empty",
        )

    def check_regex(self, field_name: str, value: Any, pattern: str) -> QualityCheckResult:
        if value is None:
            return QualityCheckResult(
                field_name=field_name, check_type="regex",
                passed=False, message=f"{field_name} is null",
            )
        passed = bool(re.match(pattern, str(value)))
        return QualityCheckResult(
            field_name=field_name, check_type="regex",
            passed=passed,
            message=f"{field_name} matches pattern" if passed else f"{field_name} does not match {pattern}",
        )

    def check_range(self, field_name: str, value: Any, min_val: float | None = None,
                    max_val: float | None = None) -> QualityCheckResult:
        try:
            num = float(value)
        except (TypeError, ValueError):
            return QualityCheckResult(
                field_name=field_name, check_type="range",
                passed=False, message=f"{field_name} is not numeric",
            )
        if min_val is not None and num < min_val:
            return QualityCheckResult(
                field_name=field_name, check_type="range",
                passed=False, message=f"{field_name}={num} < min {min_val}",
            )
        if max_val is not None and num > max_val:
            return QualityCheckResult(
                field_name=field_name, check_type="range",
                passed=False, message=f"{field_name}={num} > max {max_val}",
            )
        return QualityCheckResult(
            field_name=field_name, check_type="range",
            passed=True, message=f"{field_name}={num} in range",
        )

    def check_unique(self, field_name: str, values: list[Any]) -> QualityCheckResult:
        unique_count = len(set(values))
        total = len(values)
        passed = unique_count == total
        return QualityCheckResult(
            field_name=field_name, check_type="unique",
            passed=passed,
            message=f"{field_name}: {unique_count}/{total} unique" if passed
            else f"{field_name}: {total - unique_count} duplicates found",
        )

    def check_freshness(self, field_name: str, timestamp: datetime,
                        max_age: timedelta) -> QualityCheckResult:
        age = datetime.utcnow() - timestamp
        passed = age <= max_age
        return QualityCheckResult(
            field_name=field_name, check_type="freshness",
            passed=passed,
            message=f"{field_name} is {age.total_seconds():.0f}s old (max: {max_age.total_seconds():.0f}s)",
        )

    def check_completeness(self, data: dict[str, Any], required_fields: list[str]) -> QualityReport:
        results = []
        for fld in required_fields:
            results.append(self.check_not_null(fld, data.get(fld)))
        passed = sum(1 for r in results if r.passed)
        total = len(results)
        return QualityReport(
            total_checks=total, passed=passed, failed=total - passed,
            score=passed / max(total, 1), results=results,
        )

    def run_checks(self, data: dict[str, Any],
                   checks: list[dict]) -> QualityReport:
        results = []
        for check in checks:
            field_name = check["field"]
            check_type = check["check"]
            params = check.get("params", {})

            if check_type == "not_null":
                results.append(self.check_not_null(field_name, data.get(field_name)))
            elif check_type == "regex":
                results.append(self.check_regex(field_name, data.get(field_name), params["pattern"]))
            elif check_type == "range":
                results.append(self.check_range(
                    field_name, data.get(field_name),
                    params.get("min"), params.get("max"),
                ))
            else:
                results.append(QualityCheckResult(
                    field_name=field_name, check_type=check_type,
                    passed=False, message=f"Unknown check type: {check_type}",
                ))

        passed = sum(1 for r in results if r.passed)
        total = len(results)
        return QualityReport(
            total_checks=total, passed=passed, failed=total - passed,
            score=passed / max(total, 1), results=results,
        )
