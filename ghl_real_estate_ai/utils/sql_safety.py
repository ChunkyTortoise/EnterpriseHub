"""SQL identifier safety utilities.

Prevents SQL injection in DDL statements where parameterized queries
cannot be used (CREATE SCHEMA, VACUUM ANALYZE, PRAGMA, etc.).

PostgreSQL and SQLite do not support $1-style parameter binding for
identifiers (table names, schema names, column names). This module
provides safe identifier quoting and validation as a defense-in-depth
measure for those cases.
"""

import re
from typing import Optional

# PostgreSQL identifier: letter/underscore start, alphanumeric/underscore body, max 63 chars
_PG_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,62}$")

# SQLite identifier: same pattern but max 128 chars
_SQLITE_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,127}$")


def validate_identifier(name: str, dialect: str = "postgresql") -> str:
    """Validate and return a safe SQL identifier.

    Args:
        name: The identifier to validate (table name, schema name, etc.).
        dialect: Database dialect ("postgresql" or "sqlite").

    Returns:
        The validated identifier string.

    Raises:
        ValueError: If the identifier contains unsafe characters.
    """
    pattern = _PG_IDENTIFIER_RE if dialect == "postgresql" else _SQLITE_IDENTIFIER_RE
    if not pattern.match(name):
        raise ValueError(f"Unsafe SQL identifier: {name!r}. Must match {pattern.pattern}")
    return name


def quote_identifier(name: str, dialect: str = "postgresql") -> str:
    """Validate and double-quote a SQL identifier for safe use in DDL.

    Double-quoting prevents interpretation of reserved words and ensures
    the identifier is treated as a literal name by the database engine.

    Args:
        name: The identifier to quote.
        dialect: Database dialect ("postgresql" or "sqlite").

    Returns:
        A safely quoted identifier string, e.g. '"my_table"'.

    Raises:
        ValueError: If the identifier contains unsafe characters.
    """
    validated = validate_identifier(name, dialect)
    # Double-quote escaping: any embedded quote becomes two quotes
    escaped = validated.replace('"', '""')
    return f'"{escaped}"'


def safe_pragma(pragma_name: str, value: Optional[int] = None) -> str:
    """Build a safe SQLite PRAGMA statement.

    PRAGMA values cannot be parameterized in SQLite. This function
    validates the pragma name and ensures the value is an integer.

    Args:
        pragma_name: The PRAGMA name (e.g., "cache_size").
        value: Optional integer value. If None, returns a query PRAGMA.

    Returns:
        A safe PRAGMA SQL string.

    Raises:
        ValueError: If pragma_name is invalid or value is not an integer.
    """
    validate_identifier(pragma_name, dialect="sqlite")
    if value is not None:
        if not isinstance(value, int):
            raise TypeError(f"PRAGMA value must be int, got {type(value).__name__}")
        return f"PRAGMA {pragma_name} = {value}"
    return f"PRAGMA {pragma_name}"
