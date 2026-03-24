"""Tests for SQL identifier safety utilities."""

import pytest

from ghl_real_estate_ai.utils.sql_safety import (
    quote_identifier,
    safe_pragma,
    validate_identifier,
)


class TestValidateIdentifier:
    """Tests for validate_identifier."""

    def test_valid_simple_name(self):
        assert validate_identifier("users") == "users"

    def test_valid_with_underscores(self):
        assert validate_identifier("follow_up_tasks") == "follow_up_tasks"

    def test_valid_starts_with_underscore(self):
        assert validate_identifier("_private_table") == "_private_table"

    def test_valid_mixed_case(self):
        assert validate_identifier("LeadScoring") == "LeadScoring"

    def test_valid_with_numbers(self):
        assert validate_identifier("table_v2") == "table_v2"

    def test_rejects_starts_with_number(self):
        with pytest.raises(ValueError, match="Unsafe SQL identifier"):
            validate_identifier("2table")

    def test_rejects_semicolon(self):
        with pytest.raises(ValueError, match="Unsafe SQL identifier"):
            validate_identifier("users; DROP TABLE users")

    def test_rejects_spaces(self):
        with pytest.raises(ValueError, match="Unsafe SQL identifier"):
            validate_identifier("my table")

    def test_rejects_quotes(self):
        with pytest.raises(ValueError, match="Unsafe SQL identifier"):
            validate_identifier('users"')

    def test_rejects_hyphen(self):
        with pytest.raises(ValueError, match="Unsafe SQL identifier"):
            validate_identifier("my-table")

    def test_rejects_empty(self):
        with pytest.raises(ValueError, match="Unsafe SQL identifier"):
            validate_identifier("")

    def test_rejects_too_long_postgresql(self):
        with pytest.raises(ValueError, match="Unsafe SQL identifier"):
            validate_identifier("a" * 64, dialect="postgresql")

    def test_accepts_max_length_postgresql(self):
        name = "a" * 63
        assert validate_identifier(name, dialect="postgresql") == name

    def test_sqlite_allows_longer_names(self):
        name = "a" * 128
        assert validate_identifier(name, dialect="sqlite") == name


class TestQuoteIdentifier:
    """Tests for quote_identifier."""

    def test_simple_quoting(self):
        assert quote_identifier("users") == '"users"'

    def test_underscore_quoting(self):
        assert quote_identifier("follow_up_tasks") == '"follow_up_tasks"'

    def test_rejects_unsafe_input(self):
        with pytest.raises(ValueError):
            quote_identifier("users; DROP TABLE users")

    def test_tenant_schema_pattern(self):
        """Test the pattern used in multi_tenant_enterprise_architecture.py."""
        schema = "tenant_abc123_def"
        assert quote_identifier(schema) == '"tenant_abc123_def"'

    def test_rejects_sql_injection_attempt(self):
        with pytest.raises(ValueError):
            quote_identifier('"; DROP SCHEMA public; --')


class TestSafePragma:
    """Tests for safe_pragma."""

    def test_cache_size(self):
        assert safe_pragma("cache_size", 2000) == "PRAGMA cache_size = 2000"

    def test_query_only(self):
        assert safe_pragma("journal_mode") == "PRAGMA journal_mode"

    def test_negative_value(self):
        assert safe_pragma("cache_size", -2000) == "PRAGMA cache_size = -2000"

    def test_rejects_unsafe_pragma_name(self):
        with pytest.raises(ValueError):
            safe_pragma("cache_size; DROP TABLE users")

    def test_rejects_non_int_value(self):
        with pytest.raises(TypeError, match="PRAGMA value must be int"):
            safe_pragma("cache_size", "2000")  # type: ignore[arg-type]

    def test_rejects_float_value(self):
        with pytest.raises(TypeError, match="PRAGMA value must be int"):
            safe_pragma("cache_size", 20.5)  # type: ignore[arg-type]
