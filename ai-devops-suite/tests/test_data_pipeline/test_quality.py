"""Unit tests for DataQualityChecker — validation, range, regex, completeness."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from devops_suite.data_pipeline.quality import DataQualityChecker


@pytest.fixture
def checker():
    return DataQualityChecker()


class TestNotNullCheck:
    def test_passes_for_string(self, checker):
        r = checker.check_not_null("name", "John")
        assert r.passed is True

    def test_fails_for_none(self, checker):
        r = checker.check_not_null("name", None)
        assert r.passed is False

    def test_fails_for_empty_string(self, checker):
        r = checker.check_not_null("name", "")
        assert r.passed is False

    def test_passes_for_zero(self, checker):
        r = checker.check_not_null("count", 0)
        assert r.passed is True


class TestRegexCheck:
    def test_email_pattern_passes(self, checker):
        r = checker.check_regex("email", "user@test.com", r"^[\w.]+@[\w.]+\.\w+$")
        assert r.passed is True

    def test_email_pattern_fails(self, checker):
        r = checker.check_regex("email", "not-an-email", r"^[\w.]+@[\w.]+\.\w+$")
        assert r.passed is False

    def test_null_value_fails(self, checker):
        r = checker.check_regex("email", None, r".*")
        assert r.passed is False


class TestRangeCheck:
    def test_in_range(self, checker):
        r = checker.check_range("price", 50, min_val=0, max_val=100)
        assert r.passed is True

    def test_below_min(self, checker):
        r = checker.check_range("price", -5, min_val=0)
        assert r.passed is False

    def test_above_max(self, checker):
        r = checker.check_range("price", 200, max_val=100)
        assert r.passed is False

    def test_non_numeric(self, checker):
        r = checker.check_range("price", "abc")
        assert r.passed is False

    def test_none_value(self, checker):
        r = checker.check_range("price", None)
        assert r.passed is False

    def test_no_bounds(self, checker):
        r = checker.check_range("price", 9999)
        assert r.passed is True

    def test_string_numeric(self, checker):
        r = checker.check_range("price", "50", min_val=0, max_val=100)
        assert r.passed is True


class TestUniqueCheck:
    def test_all_unique(self, checker):
        r = checker.check_unique("id", [1, 2, 3, 4])
        assert r.passed is True

    def test_has_duplicates(self, checker):
        r = checker.check_unique("id", [1, 2, 2, 3])
        assert r.passed is False
        assert "1 duplicates" in r.message


class TestFreshnessCheck:
    def test_fresh_data(self, checker):
        recent = datetime.utcnow() - timedelta(seconds=30)
        r = checker.check_freshness("ts", recent, timedelta(minutes=5))
        assert r.passed is True

    def test_stale_data(self, checker):
        old = datetime.utcnow() - timedelta(hours=2)
        r = checker.check_freshness("ts", old, timedelta(minutes=5))
        assert r.passed is False


class TestCompleteness:
    def test_all_fields_present(self, checker):
        report = checker.check_completeness({"name": "John", "email": "j@t.com"}, ["name", "email"])
        assert report.score == 1.0
        assert report.failed == 0

    def test_missing_fields(self, checker):
        report = checker.check_completeness({"name": "John"}, ["name", "email", "phone"])
        assert report.score == pytest.approx(1 / 3, abs=0.01)
        assert report.failed == 2


class TestRunChecks:
    def test_mixed_checks(self, checker):
        data = {"name": "John", "age": 25, "email": "bad"}
        checks = [
            {"field": "name", "check": "not_null"},
            {"field": "age", "check": "range", "params": {"min": 0, "max": 120}},
            {"field": "email", "check": "regex", "params": {"pattern": r"^[\w.]+@[\w.]+\.\w+$"}},
        ]
        report = checker.run_checks(data, checks)
        assert report.total_checks == 3
        assert report.passed == 2  # name and age pass
        assert report.failed == 1  # email fails

    def test_unknown_check_type(self, checker):
        report = checker.run_checks({"x": 1}, [{"field": "x", "check": "magic"}])
        assert report.failed == 1
        assert "Unknown check type" in report.results[0].message
