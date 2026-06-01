# Layer 3: Database Security Layer

## Complete Implementation Reference

This layer prevents SQL injection, implements secure queries, and validates database operations.

### SQL Injection Prevention

```python
"""
Database security layer with SQL injection prevention.
"""

from typing import Any, Dict, List, Optional, Union
import re
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, insert, update, delete


class DatabaseSecurityLayer:
    """Secure database operations with SQL injection prevention."""

    def __init__(self, session: Session):
        self.session = session
        self.query_log = []

    def safe_query(
        self,
        model: Any,
        filters: Dict[str, Any],
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> ValidationResult:
        """Execute safe parameterized query."""
        errors = []
        warnings = []

        try:
            # Layer 1: Validate filter inputs
            filter_result = self._validate_filters(filters, model)
            if not filter_result.is_valid:
                return filter_result

            # Layer 2: Build parameterized query
            query = select(model)

            # Layer 3: Apply filters safely
            for field, value in filters.items():
                if hasattr(model, field):
                    query = query.where(getattr(model, field) == value)
                else:
                    warnings.append(f"Field '{field}' not found in model")

            # Layer 4: Apply order by if specified
            if order_by:
                order_result = self._validate_order_by(order_by, model)
                if order_result.is_valid:
                    if order_by.startswith('-'):
                        query = query.order_by(getattr(model, order_by[1:]).desc())
                    else:
                        query = query.order_by(getattr(model, order_by))
                else:
                    warnings.extend(order_result.warnings)

            # Layer 5: Apply limit safely
            if limit:
                if not isinstance(limit, int) or limit < 0:
                    warnings.append("Invalid limit value")
                else:
                    query = query.limit(min(limit, 1000))  # Max 1000 results

            # Execute query
            results = self.session.execute(query).scalars().all()

            # Log query for audit
            self._log_query('SELECT', model.__tablename__, filters)

            return ValidationResult(
                is_valid=True,
                errors=errors,
                warnings=warnings,
                sanitized_data=results
            )

        except Exception as e:
            errors.append(f"Database query error: {str(e)}")
            return ValidationResult(False, errors, warnings)

    def _validate_filters(self, filters: Dict[str, Any], model: Any) -> ValidationResult:
        """Validate filter dictionary for SQL injection attempts."""
        errors = []
        warnings = []

        # Layer 1: Check for SQL injection patterns
        sql_injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|\#|\/\*|\*\/)",
            r"(\bOR\b.*=.*)",
            r"(';\s*(DROP|DELETE|UPDATE))",
            r"(1\s*=\s*1)",
            r"(SLEEP\(|BENCHMARK\()",
        ]

        for key, value in filters.items():
            str_value = str(value)
            for pattern in sql_injection_patterns:
                if re.search(pattern, str_value, re.IGNORECASE):
                    errors.append(
                        f"Potential SQL injection detected in filter '{key}': {pattern}"
                    )

        # Layer 2: Validate field names
        for key in filters.keys():
            if not key.replace('_', '').isalnum():
                errors.append(f"Invalid field name: {key}")

        # Layer 3: Check for excessive filter complexity
        if len(filters) > 20:
            warnings.append("Excessive number of filters may impact performance")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def _validate_order_by(self, order_by: str, model: Any) -> ValidationResult:
        """Validate order_by parameter."""
        errors = []
        warnings = []

        # Remove DESC prefix if exists
        field_name = order_by.lstrip('-')

        # Layer 1: Check field name is alphanumeric
        if not field_name.replace('_', '').isalnum():
            errors.append(f"Invalid order_by field: {order_by}")

        # Layer 2: Check field exists in model
        if not hasattr(model, field_name):
            warnings.append(f"Order field '{field_name}' not found in model")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def safe_insert(
        self,
        model: Any,
        data: Dict[str, Any]
    ) -> ValidationResult:
        """Safely insert data into database."""
        errors = []
        warnings = []

        try:
            # Layer 1: Validate data inputs
            validation_result = self._validate_insert_data(data, model)
            if not validation_result.is_valid:
                return validation_result

            # Layer 2: Create model instance
            instance = model(**data)

            # Layer 3: Add and commit
            self.session.add(instance)
            self.session.commit()

            # Log operation
            self._log_query('INSERT', model.__tablename__, data)

            return ValidationResult(
                is_valid=True,
                errors=errors,
                warnings=warnings,
                sanitized_data=instance
            )

        except Exception as e:
            self.session.rollback()
            errors.append(f"Database insert error: {str(e)}")
            return ValidationResult(False, errors, warnings)

    def _validate_insert_data(self, data: Dict[str, Any], model: Any) -> ValidationResult:
        """Validate data for safe insertion."""
        errors = []
        warnings = []

        # Layer 1: Check for required fields
        # This would be model-specific
        if not data:
            errors.append("No data provided for insertion")

        # Layer 2: Validate data types
        for key, value in data.items():
            if not hasattr(model, key):
                warnings.append(f"Field '{key}' not in model schema")

            # Check for dangerous values
            if isinstance(value, str):
                if len(value) > 10000:
                    warnings.append(f"Very large string value for field '{key}'")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def safe_update(
        self,
        model: Any,
        filters: Dict[str, Any],
        updates: Dict[str, Any]
    ) -> ValidationResult:
        """Safely update database records."""
        errors = []
        warnings = []

        try:
            # Layer 1: Validate filters
            filter_result = self._validate_filters(filters, model)
            if not filter_result.is_valid:
                return filter_result

            # Layer 2: Validate updates
            update_result = self._validate_updates(updates, model)
            if not update_result.is_valid:
                return update_result

            # Layer 3: Build update query
            query = update(model)
            for field, value in filters.items():
                if hasattr(model, field):
                    query = query.where(getattr(model, field) == value)

            query = query.values(**updates)

            # Layer 4: Execute update
            result = self.session.execute(query)
            self.session.commit()

            # Log operation
            self._log_query('UPDATE', model.__tablename__, {'filters': filters, 'updates': updates})

            return ValidationResult(
                is_valid=True,
                errors=errors,
                warnings=warnings,
                sanitized_data={'rows_updated': result.rowcount}
            )

        except Exception as e:
            self.session.rollback()
            errors.append(f"Database update error: {str(e)}")
            return ValidationResult(False, errors, warnings)

    def _validate_updates(self, updates: Dict[str, Any], model: Any) -> ValidationResult:
        """Validate update data."""
        errors = []
        warnings = []

        if not updates:
            errors.append("No update data provided")

        # Check for protected fields
        protected_fields = ['id', 'created_at']
        for field in protected_fields:
            if field in updates:
                errors.append(f"Cannot update protected field: {field}")

        return ValidationResult(len(errors) == 0, errors, warnings)

    def safe_delete(
        self,
        model: Any,
        filters: Dict[str, Any],
        require_filters: bool = True
    ) -> ValidationResult:
        """Safely delete database records."""
        errors = []
        warnings = []

        try:
            # Layer 1: Prevent accidental mass deletion
            if require_filters and not filters:
                errors.append("Delete operation requires filters to prevent mass deletion")
                return ValidationResult(False, errors, warnings)

            # Layer 2: Validate filters
            filter_result = self._validate_filters(filters, model)
            if not filter_result.is_valid:
                return filter_result

            # Layer 3: Build delete query
            query = delete(model)
            for field, value in filters.items():
                if hasattr(model, field):
                    query = query.where(getattr(model, field) == value)

            # Layer 4: Execute delete
            result = self.session.execute(query)
            self.session.commit()

            # Log operation
            self._log_query('DELETE', model.__tablename__, filters)

            if result.rowcount > 100:
                warnings.append(f"Large deletion: {result.rowcount} rows deleted")

            return ValidationResult(
                is_valid=True,
                errors=errors,
                warnings=warnings,
                sanitized_data={'rows_deleted': result.rowcount}
            )

        except Exception as e:
            self.session.rollback()
            errors.append(f"Database delete error: {str(e)}")
            return ValidationResult(False, errors, warnings)

    def _log_query(self, operation: str, table: str, params: Dict):
        """Log database operations for audit trail."""
        self.query_log.append({
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'table': table,
            'params': params
        })
```

### Raw SQL Safety Wrapper

```python
def execute_raw_sql(
    self,
    query_template: str,
    params: Dict[str, Any]
) -> ValidationResult:
    """Execute raw SQL with strict validation (use sparingly)."""
    errors = []
    warnings = []

    try:
        # Layer 1: Validate query template
        if not self._is_safe_query_template(query_template):
            errors.append("Unsafe SQL query template detected")
            return ValidationResult(False, errors, warnings)

        # Layer 2: Validate parameters
        param_result = self._validate_sql_params(params)
        if not param_result.is_valid:
            return param_result

        # Layer 3: Execute with parameters (never string interpolation!)
        stmt = text(query_template)
        result = self.session.execute(stmt, params)

        # Log operation
        self._log_query('RAW_SQL', 'custom', {'template': query_template, 'params': params})

        return ValidationResult(
            is_valid=True,
            errors=errors,
            warnings=warnings,
            sanitized_data=result.fetchall()
        )

    except Exception as e:
        errors.append(f"Raw SQL execution error: {str(e)}")
        return ValidationResult(False, errors, warnings)

def _is_safe_query_template(self, template: str) -> bool:
    """Verify SQL template is safe."""
    # Must use parameterized placeholders
    if '%s' in template or f'{' in template:
        return False  # String interpolation detected

    # Should use :param_name format
    if ':' not in template and 'SELECT' in template.upper():
        return False  # No parameters in query

    return True

def _validate_sql_params(self, params: Dict[str, Any]) -> ValidationResult:
    """Validate SQL parameters."""
    errors = []
    warnings = []

    for key, value in params.items():
        # Check parameter names
        if not key.replace('_', '').isalnum():
            errors.append(f"Invalid parameter name: {key}")

        # Check for SQL injection in values
        if isinstance(value, str):
            dangerous_patterns = ['--', ';', 'DROP', 'DELETE', 'UPDATE', 'INSERT']
            if any(pattern in value.upper() for pattern in dangerous_patterns):
                warnings.append(f"Potentially dangerous value in parameter '{key}'")

    return ValidationResult(len(errors) == 0, errors, warnings)
```

## Best Practices

1. **Always use parameterized queries** - never string concatenation
2. **Use ORM methods** when possible (safer than raw SQL)
3. **Validate all filter inputs** before query construction
4. **Implement query logging** for audit trails
5. **Use transactions** for data consistency
6. **Limit query results** to prevent resource exhaustion
7. **Validate field names** against model schema
8. **Never trust user input** in SQL queries
