#!/usr/bin/env python3
"""
Enhanced Database Security Service - Critical Security Fixes for Service 6
Addresses SQL injection vulnerabilities and silent failure points identified by security audit.

Critical Security Enhancements:
1. Field whitelisting to prevent SQL injection
2. Enhanced error handling with specific error IDs
3. Circuit breaker pattern for database operations
4. Comprehensive logging with security monitoring
5. Input validation and sanitization
"""

import asyncio
import json
import time
import uuid
from enum import Enum
from typing import Any, Dict, List

import asyncpg

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseOperationError(Exception):
    """Specific database operation error for proper error handling"""

    def __init__(self, message: str, error_id: str = None):
        super().__init__(message)
        self.error_id = error_id


class CircuitBreakerState(Enum):
    """Circuit breaker states for database operations"""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class DatabaseCircuitBreaker:
    """Circuit breaker for database operations to prevent cascading failures"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0, success_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.last_failure_time = None

    async def call(self, operation, *args, **kwargs):
        """Execute operation with circuit breaker protection"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
            else:
                logger.error(
                    "CIRCUIT_BREAKER_OPEN: Database operation blocked",
                    extra={
                        "error_id": "CIRCUIT_BREAKER_OPEN_001",
                        "operation": operation.__name__,
                        "state": self.state.value,
                        "failure_count": self.failure_count,
                    },
                )
                raise DatabaseOperationError(
                    "Database circuit breaker is OPEN - service temporarily unavailable",
                    error_id="CIRCUIT_BREAKER_OPEN_001",
                )

        try:
            result = await operation(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure(e)
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout

    async def _on_success(self):
        """Handle successful operation"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                logger.info(
                    "CIRCUIT_BREAKER_CLOSED: Database circuit breaker reset to CLOSED",
                    extra={"error_id": "CIRCUIT_BREAKER_CLOSED_001", "state": self.state.value},
                )
        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on successful operation
            self.failure_count = max(0, self.failure_count - 1)

    async def _on_failure(self, error: Exception):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitBreakerState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.error(
                    "CIRCUIT_BREAKER_OPEN: Database circuit breaker OPENED due to failures",
                    extra={
                        "error_id": "CIRCUIT_BREAKER_OPENED_001",
                        "failure_count": self.failure_count,
                        "threshold": self.failure_threshold,
                        "error": str(error),
                    },
                )
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            logger.warning(
                "CIRCUIT_BREAKER_REOPEN: Database circuit breaker reopened after failed recovery",
                extra={"error_id": "CIRCUIT_BREAKER_REOPEN_001", "error": str(error)},
            )


class EnhancedDatabaseService:
    """Enhanced database service with comprehensive security and error handling"""

    # SECURITY: Comprehensive field whitelist for all tables
    LEAD_ALLOWED_FIELDS = {
        "first_name",
        "last_name",
        "email",
        "phone",
        "company",
        "status",
        "source",
        "score",
        "temperature",
        "last_interaction_at",
        "assigned_agent_id",
        "notes",
        "budget_min",
        "budget_max",
        "property_type",
        "location",
        "timeline",
        "enrichment_data",
        "preferences",
        "tags",
        "priority",
        "lead_type",
    }

    AGENT_ALLOWED_FIELDS = {
        "first_name",
        "last_name",
        "email",
        "phone",
        "is_active",
        "is_available",
        "current_load",
        "capacity",
        "conversion_rate",
        "avg_response_time_minutes",
        "expertise_areas",
        "territory",
    }

    COMMUNICATION_ALLOWED_FIELDS = {
        "lead_id",
        "channel",
        "direction",
        "content",
        "status",
        "sent_at",
        "response_received_at",
        "sentiment_score",
        "metadata",
    }

    def __init__(self):
        self.circuit_breaker = DatabaseCircuitBreaker()
        self.connection_manager = None  # Will be injected

    async def secure_update_lead(self, lead_id: str, updates: Dict[str, Any], updated_by: str = None) -> bool:
        """
        Secure lead update with SQL injection prevention and comprehensive error handling

        Args:
            lead_id: Lead UUID
            updates: Field updates (validated against whitelist)
            updated_by: User performing the update

        Returns:
            bool: Success status

        Raises:
            ValueError: Invalid field names or data
            DatabaseOperationError: Database operation failed
        """

        async def _perform_update():
            # SECURITY: Validate lead_id format
            try:
                uuid.UUID(lead_id)
            except ValueError:
                error_msg = f"Invalid lead ID format: {lead_id}"
                logger.error(
                    f"SECURITY_VIOLATION: {error_msg}",
                    extra={"error_id": "INVALID_LEAD_ID_001", "lead_id": lead_id, "source": "secure_update_lead"},
                )
                raise ValueError(error_msg)

            # SECURITY: Validate all fields are whitelisted
            invalid_fields = set(updates.keys()) - self.LEAD_ALLOWED_FIELDS
            if invalid_fields:
                error_msg = f"Invalid field(s) in update: {invalid_fields}. Allowed: {self.LEAD_ALLOWED_FIELDS}"
                logger.error(
                    f"SECURITY_VIOLATION: {error_msg}",
                    extra={
                        "error_id": "SQL_INJECTION_ATTEMPT_001",
                        "lead_id": lead_id,
                        "invalid_fields": list(invalid_fields),
                        "attempted_fields": list(updates.keys()),
                    },
                )
                raise ValueError(error_msg)

            if not updates:
                logger.warning(
                    f"EMPTY_UPDATE: No data provided for lead {lead_id}",
                    extra={"error_id": "EMPTY_UPDATE_001", "lead_id": lead_id},
                )
                return True

            # SECURITY: Sanitize input data
            sanitized_updates = self._sanitize_lead_data(updates)

            try:
                async with self.connection_manager.transaction() as conn:
                    # Build secure parameterized query
                    set_clauses = ["updated_at = NOW()"]
                    values = []
                    param_count = 1

                    for field, value in sanitized_updates.items():
                        if field in ["enrichment_data", "preferences"]:
                            set_clauses.append(f"{field} = ${param_count}")
                            values.append(json.dumps(value))
                        elif field == "tags":
                            set_clauses.append(f"{field} = ${param_count}")
                            values.append(value if isinstance(value, list) else [value])
                        else:
                            set_clauses.append(f"{field} = ${param_count}")
                            values.append(value)
                        param_count += 1

                    if updated_by:
                        set_clauses.append(f"updated_by = ${param_count}")
                        values.append(updated_by)
                        param_count += 1

                    # Add lead_id as final parameter
                    values.append(lead_id)

                    query = f"""
                        UPDATE leads
                        SET {", ".join(set_clauses)}
                        WHERE id = ${param_count} AND deleted_at IS NULL
                    """

                    result = await conn.execute(query, *values)

                    # Check if any rows were affected
                    rows_affected = int(result.split()[-1]) if result else 0

                    if rows_affected > 0:
                        logger.info(
                            f"LEAD_UPDATED: Successfully updated lead {lead_id}",
                            extra={
                                "error_id": "LEAD_UPDATED_001",
                                "lead_id": lead_id,
                                "fields_updated": list(sanitized_updates.keys()),
                                "updated_by": updated_by,
                            },
                        )
                        return True
                    else:
                        logger.warning(
                            f"DB_UPDATE_NO_ROWS: Lead {lead_id} not found or no changes made",
                            extra={
                                "error_id": "DB_UPDATE_NO_ROWS_001",
                                "lead_id": lead_id,
                                "attempted_fields": list(updates.keys()),
                            },
                        )
                        return False

            except asyncpg.PostgresError as e:
                logger.error(
                    f"DB_FAILURE: Database error updating lead {lead_id}",
                    extra={
                        "error_id": "DB_FAILURE_002",
                        "lead_id": lead_id,
                        "postgres_error": str(e),
                        "error_code": e.sqlstate if hasattr(e, "sqlstate") else None,
                    },
                )
                raise DatabaseOperationError(f"Failed to update lead: {e}", error_id="DB_FAILURE_002")

            except Exception as e:
                logger.error(
                    f"UNEXPECTED_ERROR: Unexpected error updating lead {lead_id}",
                    extra={
                        "error_id": "UNEXPECTED_ERROR_002",
                        "lead_id": lead_id,
                        "error_type": type(e).__name__,
                        "error": str(e),
                    },
                )
                raise

        # Execute with circuit breaker protection
        return await self.circuit_breaker.call(_perform_update)

    def _sanitize_lead_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize lead data for secure database operations"""
        sanitized = {}

        for field, value in data.items():
            if field in self.LEAD_ALLOWED_FIELDS:
                if field in ["first_name", "last_name", "company", "notes"]:
                    # Sanitize text fields
                    if isinstance(value, str):
                        # Remove potential XSS/SQL injection characters
                        sanitized_value = value.strip()[:255]  # Limit length
                        # Remove dangerous characters but keep apostrophes for names
                        dangerous_chars = ["<", ">", '"', "&", ";", "--", "/*", "*/", "script"]
                        for char in dangerous_chars:
                            if char in sanitized_value.lower():
                                logger.warning(
                                    f"SUSPICIOUS_INPUT: Removed dangerous character from {field}",
                                    extra={
                                        "error_id": "SUSPICIOUS_INPUT_001",
                                        "field": field,
                                        "original_length": len(value),
                                        "sanitized_length": len(sanitized_value),
                                    },
                                )
                                sanitized_value = sanitized_value.replace(char, "")
                        sanitized[field] = sanitized_value
                    else:
                        sanitized[field] = value
                elif field == "email":
                    # Basic email validation
                    if isinstance(value, str) and "@" in value and "." in value:
                        sanitized[field] = value.lower().strip()
                    else:
                        logger.warning(
                            f"INVALID_EMAIL: Invalid email format",
                            extra={"error_id": "INVALID_EMAIL_001", "field": field},
                        )
                        continue
                elif field in ["score", "budget_min", "budget_max"]:
                    # Validate numeric fields
                    if isinstance(value, (int, float)) and value >= 0:
                        sanitized[field] = value
                    else:
                        logger.warning(
                            f"INVALID_NUMERIC: Invalid numeric value",
                            extra={"error_id": "INVALID_NUMERIC_001", "field": field, "value": value},
                        )
                        continue
                else:
                    sanitized[field] = value

        return sanitized

    async def secure_get_lead_follow_up_history(self, lead_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Secure retrieval of lead follow-up history with comprehensive error handling

        Args:
            lead_id: Lead UUID
            limit: Maximum number of records

        Returns:
            List of follow-up history records

        Raises:
            ValueError: Invalid parameters
            DatabaseOperationError: Database operation failed
        """

        async def _get_history():
            # Validate lead_id format
            try:
                uuid.UUID(lead_id)
            except ValueError:
                error_msg = f"Invalid lead ID format: {lead_id}"
                logger.error(
                    f"INVALID_LEAD_ID: {error_msg}", extra={"error_id": "INVALID_LEAD_ID_002", "lead_id": lead_id}
                )
                raise ValueError(error_msg)

            # Validate limit
            if not isinstance(limit, int) or limit <= 0 or limit > 1000:
                limit = min(max(1, limit), 1000)
                logger.warning(
                    f"LIMIT_ADJUSTED: Adjusted limit to safe range",
                    extra={"error_id": "LIMIT_ADJUSTED_001", "original_limit": limit, "adjusted_limit": limit},
                )

            try:
                async with self.connection_manager.get_connection() as conn:
                    query = """
                        SELECT
                            id, lead_id, channel, direction, content, status,
                            sent_at, response_received_at, sentiment_score, metadata,
                            created_at
                        FROM communication_logs
                        WHERE lead_id = $1
                        AND direction = 'outbound'
                        AND deleted_at IS NULL
                        ORDER BY sent_at DESC
                        LIMIT $2
                    """

                    rows = await conn.fetch(query, lead_id, limit)
                    result = [dict(row) for row in rows]

                    # Log successful but empty results for monitoring
                    if not result:
                        logger.warning(
                            f"DB_EMPTY_RESULT: No follow-up history found for lead {lead_id}",
                            extra={
                                "error_id": "DB_EMPTY_RESULT_001",
                                "lead_id": lead_id,
                                "table": "communication_logs",
                                "query_type": "follow_up_history",
                            },
                        )
                    else:
                        logger.debug(
                            f"FOLLOW_UP_HISTORY_RETRIEVED: Found {len(result)} records",
                            extra={
                                "error_id": "FOLLOW_UP_HISTORY_RETRIEVED_001",
                                "lead_id": lead_id,
                                "record_count": len(result),
                            },
                        )

                    return result

            except asyncpg.PostgresError as e:
                logger.error(
                    f"DB_FAILURE: Database error getting follow-up history for lead {lead_id}",
                    extra={
                        "error_id": "DB_FAILURE_001",
                        "lead_id": lead_id,
                        "postgres_error": str(e),
                        "error_code": e.sqlstate if hasattr(e, "sqlstate") else None,
                    },
                )
                # Don't return empty list - re-raise to force proper error handling
                raise DatabaseOperationError(f"Failed to get lead follow-up history: {e}", error_id="DB_FAILURE_001")

            except Exception as e:
                logger.error(
                    f"UNEXPECTED_DB_ERROR: Unexpected error in get_lead_follow_up_history",
                    extra={
                        "error_id": "UNEXPECTED_DB_ERROR_001",
                        "lead_id": lead_id,
                        "error_type": type(e).__name__,
                        "error": str(e),
                    },
                )
                raise

        # Execute with circuit breaker protection
        return await self.circuit_breaker.call(_get_history)

    async def secure_bulk_update_leads(self, updates: List[Dict[str, Any]], updated_by: str = None) -> Dict[str, int]:
        """
        Secure bulk lead updates for performance optimization

        Args:
            updates: List of update dictionaries with 'lead_id' and update fields
            updated_by: User performing the updates

        Returns:
            Dict with success/failure counts

        Raises:
            ValueError: Invalid input data
            DatabaseOperationError: Database operation failed
        """

        async def _bulk_update():
            if not updates:
                return {"success": 0, "failed": 0, "total": 0}

            success_count = 0
            failed_count = 0

            # Process in smaller batches to avoid memory issues
            batch_size = 50
            for i in range(0, len(updates), batch_size):
                batch = updates[i : i + batch_size]

                for update_data in batch:
                    if "lead_id" not in update_data:
                        logger.error(
                            "BULK_UPDATE_ERROR: Missing lead_id in update data",
                            extra={"error_id": "BULK_UPDATE_ERROR_001", "update_data": update_data},
                        )
                        failed_count += 1
                        continue

                    lead_id = update_data.pop("lead_id")

                    try:
                        success = await self.secure_update_lead(lead_id, update_data, updated_by)
                        if success:
                            success_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error(
                            f"BULK_UPDATE_ITEM_FAILED: Failed to update lead {lead_id}",
                            extra={"error_id": "BULK_UPDATE_ITEM_FAILED_001", "lead_id": lead_id, "error": str(e)},
                        )
                        failed_count += 1

                # Small delay between batches to prevent overwhelming database
                if i + batch_size < len(updates):
                    await asyncio.sleep(0.01)

            logger.info(
                f"BULK_UPDATE_COMPLETED: Processed {len(updates)} updates",
                extra={
                    "error_id": "BULK_UPDATE_COMPLETED_001",
                    "total": len(updates),
                    "success": success_count,
                    "failed": failed_count,
                    "success_rate": success_count / len(updates) if updates else 0,
                },
            )

            return {"success": success_count, "failed": failed_count, "total": len(updates)}

        # Execute with circuit breaker protection
        return await self.circuit_breaker.call(_bulk_update)


# Export enhanced service
__all__ = ["EnhancedDatabaseService", "DatabaseOperationError", "DatabaseCircuitBreaker", "CircuitBreakerState"]
