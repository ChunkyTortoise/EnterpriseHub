"""
Database Property Repository Implementation

Handles property data from SQL databases using async database connections.
Supports PostgreSQL, MySQL, SQLite with connection pooling and query optimization.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

try:
    import aiomysql  # MySQL
    import aiosqlite  # SQLite
    import asyncpg  # PostgreSQL

    HAS_DB_DRIVERS = True
except ImportError:
    HAS_DB_DRIVERS = False

from .interfaces import (
    IPropertyRepository,
    PropertyQuery,
    QueryOperator,
    RepositoryError,
    RepositoryMetadata,
    RepositoryResult,
    SortOrder,
)


class DatabasePropertyRepository(IPropertyRepository):
    """
    Repository implementation for SQL database property data.

    Features:
    - Multiple database backend support (PostgreSQL, MySQL, SQLite)
    - Connection pooling for performance
    - Query optimization and prepared statements
    - Transaction support
    - Schema flexibility
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize database repository.

        Config options:
        - database_url: Database connection URL
        - database_type: Type of database ('postgresql', 'mysql', 'sqlite')
        - table_name: Property table name (default: 'properties')
        - pool_size: Connection pool size
        - pool_timeout: Pool connection timeout
        - query_timeout: Query execution timeout
        """
        super().__init__("database_repository", config)

        if not HAS_DB_DRIVERS:
            raise RepositoryError(
                "Database repository requires database drivers: asyncpg, aiomysql, aiosqlite",
                repository_type="database",
            )

        # Configuration
        self.database_url = config.get("database_url", "")
        self.database_type = config.get("database_type", "postgresql")
        self.table_name = config.get("table_name", "properties")
        self.pool_size = config.get("pool_size", 10)
        self.pool_timeout = config.get("pool_timeout", 30)
        self.query_timeout = config.get("query_timeout", 30)

        # Schema configuration
        self.schema_config = config.get("schema", {})

        # Internal state
        self._pool: Optional[Any] = None
        self._connection_string_parsed = False

    async def connect(self) -> bool:
        """Establish database connection pool"""
        try:
            if self.database_type == "postgresql":
                await self._connect_postgresql()
            elif self.database_type == "mysql":
                await self._connect_mysql()
            elif self.database_type == "sqlite":
                await self._connect_sqlite()
            else:
                raise RepositoryError(f"Unsupported database type: {self.database_type}")

            self._is_connected = True
            return True

        except Exception as e:
            raise RepositoryError(
                f"Failed to connect to {self.database_type} database: {e}", repository_type="database", original_error=e
            )

    async def disconnect(self):
        """Close database connection pool"""
        if self._pool:
            if self.database_type == "postgresql":
                await self._pool.close()
            elif self.database_type == "mysql":
                self._pool.close()
                await self._pool.wait_closed()
            elif self.database_type == "sqlite":
                await self._pool.close()

        self._pool = None
        self._is_connected = False

    async def health_check(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        health = {
            "status": "healthy",
            "database_type": self.database_type,
            "table_name": self.table_name,
            "pool_size": self.pool_size if self._pool else 0,
            "issues": [],
        }

        try:
            # Test connection with simple query
            start_time = datetime.now()
            async with self._get_connection() as conn:
                if self.database_type == "postgresql":
                    await conn.fetchval("SELECT 1")
                elif self.database_type == "mysql":
                    async with conn.cursor() as cursor:
                        await cursor.execute("SELECT 1")
                elif self.database_type == "sqlite":
                    await conn.execute("SELECT 1")

            query_time = (datetime.now() - start_time).total_seconds() * 1000
            health["query_time_ms"] = query_time

            if query_time > 1000:  # > 1 second is concerning
                health["issues"].append(f"Slow database response: {query_time:.2f}ms")
                health["status"] = "warning"

            # Check table exists
            table_exists = await self._check_table_exists()
            if not table_exists:
                health["issues"].append(f"Table '{self.table_name}' does not exist")
                health["status"] = "degraded"

        except Exception as e:
            health["issues"].append(f"Database connectivity issue: {str(e)}")
            health["status"] = "unhealthy"

        return health

    async def find_properties(self, query: PropertyQuery) -> RepositoryResult:
        """Find properties using SQL query"""
        start_time = datetime.now()

        try:
            # Build SQL query
            sql_query, params = await self._build_sql_query(query)

            # Execute query
            async with self._get_connection() as conn:
                if self.database_type == "postgresql":
                    rows = await conn.fetch(sql_query, *params)
                    total_count = await self._get_total_count(conn, query)
                elif self.database_type == "mysql":
                    async with conn.cursor() as cursor:
                        await cursor.execute(sql_query, params)
                        rows = await cursor.fetchall()
                        total_count = await self._get_total_count_mysql(conn, query)
                elif self.database_type == "sqlite":
                    cursor = await conn.execute(sql_query, params)
                    rows = await cursor.fetchall()
                    total_count = await self._get_total_count_sqlite(conn, query)

            # Convert rows to dictionaries
            properties = [dict(row) for row in rows] if rows else []

            # Create metadata
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            metadata = RepositoryMetadata(
                source=self.name, query_time_ms=execution_time, cache_hit=False, total_scanned=total_count
            )

            return RepositoryResult(
                data=properties,
                total_count=total_count,
                pagination=query.pagination,
                metadata=metadata,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            return RepositoryResult(success=False, errors=[f"Database query failed: {str(e)}"])

    async def get_property_by_id(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Get specific property by ID"""
        sql = f"SELECT * FROM {self.table_name} WHERE id = $1 LIMIT 1"

        async with self._get_connection() as conn:
            if self.database_type == "postgresql":
                row = await conn.fetchrow(sql, property_id)
            elif self.database_type == "mysql":
                async with conn.cursor() as cursor:
                    await cursor.execute(sql.replace("$1", "%s"), (property_id,))
                    row = await cursor.fetchone()
            elif self.database_type == "sqlite":
                cursor = await conn.execute(sql.replace("$1", "?"), (property_id,))
                row = await cursor.fetchone()

            return dict(row) if row else None

    async def count_properties(self, query: PropertyQuery) -> int:
        """Count properties matching query"""
        try:
            async with self._get_connection() as conn:
                return await self._get_total_count(conn, query)
        except Exception:
            return 0

    def get_supported_filters(self) -> List[str]:
        """Get supported filter fields based on schema"""
        default_fields = [
            "id",
            "address",
            "price",
            "bedrooms",
            "bathrooms",
            "sqft",
            "property_type",
            "neighborhood",
            "city",
            "state",
            "zip_code",
            "year_built",
            "days_on_market",
            "listing_date",
            "status",
        ]

        # Add schema-specific fields if configured
        schema_fields = self.schema_config.get("additional_fields", [])
        return default_fields + schema_fields

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics"""
        return {
            "repository_type": "database",
            "database_type": self.database_type,
            "table_name": self.table_name,
            "pool_size": self.pool_size,
            "connected": self._is_connected,
            "pool_active": self._pool is not None,
        }

    # Private methods
    async def _connect_postgresql(self):
        """Connect to PostgreSQL database"""
        import asyncpg

        self._pool = await asyncpg.create_pool(
            self.database_url, min_size=1, max_size=self.pool_size, command_timeout=self.query_timeout
        )

    async def _connect_mysql(self):
        """Connect to MySQL database"""
        from urllib.parse import urlparse

        import aiomysql

        parsed = urlparse(self.database_url)
        self._pool = await aiomysql.create_pool(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=parsed.username,
            password=parsed.password,
            db=parsed.path.lstrip("/"),
            minsize=1,
            maxsize=self.pool_size,
        )

    async def _connect_sqlite(self):
        """Connect to SQLite database"""
        import aiosqlite

        # SQLite doesn't use connection pooling in the same way
        # We'll create a simple connection manager
        self.database_path = self.database_url.replace("sqlite://", "")
        self._pool = {"path": self.database_path}

    def _get_connection(self):
        """Get database connection from pool"""
        if self.database_type == "postgresql":
            return self._pool.acquire()
        elif self.database_type == "mysql":
            return self._pool.acquire()
        elif self.database_type == "sqlite":
            import aiosqlite

            return aiosqlite.connect(self._pool["path"])

    async def _build_sql_query(self, query: PropertyQuery) -> tuple:
        """Build SQL query from PropertyQuery"""
        # Base SELECT
        select_parts = [f"SELECT * FROM {self.table_name}"]
        where_conditions = []
        params = []
        param_counter = 1

        # Build WHERE conditions
        if query.min_price is not None:
            where_conditions.append(f"price >= {self._get_param_placeholder(param_counter)}")
            params.append(query.min_price)
            param_counter += 1

        if query.max_price is not None:
            where_conditions.append(f"price <= {self._get_param_placeholder(param_counter)}")
            params.append(query.max_price)
            param_counter += 1

        if query.min_bedrooms is not None:
            where_conditions.append(f"bedrooms >= {self._get_param_placeholder(param_counter)}")
            params.append(query.min_bedrooms)
            param_counter += 1

        if query.max_bedrooms is not None:
            where_conditions.append(f"bedrooms <= {self._get_param_placeholder(param_counter)}")
            params.append(query.max_bedrooms)
            param_counter += 1

        if query.min_bathrooms is not None:
            where_conditions.append(f"bathrooms >= {self._get_param_placeholder(param_counter)}")
            params.append(query.min_bathrooms)
            param_counter += 1

        if query.max_bathrooms is not None:
            where_conditions.append(f"bathrooms <= {self._get_param_placeholder(param_counter)}")
            params.append(query.max_bathrooms)
            param_counter += 1

        if query.min_sqft is not None:
            where_conditions.append(f"sqft >= {self._get_param_placeholder(param_counter)}")
            params.append(query.min_sqft)
            param_counter += 1

        if query.max_sqft is not None:
            where_conditions.append(f"sqft <= {self._get_param_placeholder(param_counter)}")
            params.append(query.max_sqft)
            param_counter += 1

        if query.property_types:
            placeholders = [self._get_param_placeholder(param_counter + i) for i in range(len(query.property_types))]
            where_conditions.append(f"property_type IN ({','.join(placeholders)})")
            params.extend(query.property_types)
            param_counter += len(query.property_types)

        if query.neighborhoods:
            placeholders = [self._get_param_placeholder(param_counter + i) for i in range(len(query.neighborhoods))]
            where_conditions.append(f"neighborhood IN ({','.join(placeholders)})")
            params.extend(query.neighborhoods)
            param_counter += len(query.neighborhoods)

        if query.zip_codes:
            placeholders = [self._get_param_placeholder(param_counter + i) for i in range(len(query.zip_codes))]
            where_conditions.append(f"zip_code IN ({','.join(placeholders)})")
            params.extend(query.zip_codes)
            param_counter += len(query.zip_codes)

        if query.location:
            where_conditions.append(
                f"(city ILIKE {self._get_param_placeholder(param_counter)} OR neighborhood ILIKE {self._get_param_placeholder(param_counter + 1)})"
            )
            params.extend([f"%{query.location}%", f"%{query.location}%"])
            param_counter += 2

        if query.max_days_on_market is not None:
            where_conditions.append(f"days_on_market <= {self._get_param_placeholder(param_counter)}")
            params.append(query.max_days_on_market)
            param_counter += 1

        # Geographic proximity (if database supports PostGIS or similar)
        if query.latitude and query.longitude and query.radius_miles:
            if self.database_type == "postgresql":
                # Assuming PostGIS is available
                where_conditions.append(f"""
                    ST_DWithin(
                        ST_Point(longitude, latitude)::geography,
                        ST_Point({self._get_param_placeholder(param_counter)}, {self._get_param_placeholder(param_counter + 1)})::geography,
                        {self._get_param_placeholder(param_counter + 2)} * 1609.34
                    )
                """)
                params.extend([query.longitude, query.latitude, query.radius_miles])
                param_counter += 3

        # Add WHERE clause if conditions exist
        if where_conditions:
            select_parts.append("WHERE " + " AND ".join(where_conditions))

        # Add ORDER BY
        if query.sort_by:
            order_direction = "DESC" if query.sort_order == SortOrder.DESC else "ASC"
            select_parts.append(f"ORDER BY {query.sort_by} {order_direction}")

        # Add LIMIT and OFFSET
        select_parts.append(f"LIMIT {query.pagination.limit} OFFSET {query.pagination.offset}")

        sql_query = " ".join(select_parts)
        return sql_query, params

    def _get_param_placeholder(self, param_number: int) -> str:
        """Get parameter placeholder for database type"""
        if self.database_type == "postgresql":
            return f"${param_number}"
        elif self.database_type in ["mysql", "sqlite"]:
            return "?"
        else:
            return "?"

    async def _get_total_count(self, conn, query: PropertyQuery) -> int:
        """Get total count for pagination (PostgreSQL)"""
        count_query, params = await self._build_count_query(query)
        return await conn.fetchval(count_query, *params)

    async def _get_total_count_mysql(self, conn, query: PropertyQuery) -> int:
        """Get total count for pagination (MySQL)"""
        count_query, params = await self._build_count_query(query)
        async with conn.cursor() as cursor:
            await cursor.execute(count_query, params)
            result = await cursor.fetchone()
            return result[0] if result else 0

    async def _get_total_count_sqlite(self, conn, query: PropertyQuery) -> int:
        """Get total count for pagination (SQLite)"""
        count_query, params = await self._build_count_query(query)
        cursor = await conn.execute(count_query, params)
        result = await cursor.fetchone()
        return result[0] if result else 0

    async def _build_count_query(self, query: PropertyQuery) -> tuple:
        """Build COUNT query from PropertyQuery"""
        # Reuse the WHERE conditions from the main query
        full_query, params = await self._build_sql_query(query)

        # Extract WHERE clause
        where_start = full_query.upper().find("WHERE")
        order_start = full_query.upper().find("ORDER BY")
        limit_start = full_query.upper().find("LIMIT")

        where_clause = ""
        if where_start != -1:
            end_pos = order_start if order_start != -1 else (limit_start if limit_start != -1 else len(full_query))
            where_clause = full_query[where_start:end_pos].strip()

        count_query = f"SELECT COUNT(*) FROM {self.table_name}"
        if where_clause:
            count_query += f" {where_clause}"

        # Parameters are the same except we need to remove LIMIT/OFFSET params
        count_params = params[:-2] if len(params) >= 2 else params

        return count_query, count_params

    async def _check_table_exists(self) -> bool:
        """Check if the properties table exists"""
        try:
            async with self._get_connection() as conn:
                if self.database_type == "postgresql":
                    result = await conn.fetchval(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)", self.table_name
                    )
                elif self.database_type == "mysql":
                    async with conn.cursor() as cursor:
                        await cursor.execute(
                            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = %s", (self.table_name,)
                        )
                        result = (await cursor.fetchone())[0] > 0
                elif self.database_type == "sqlite":
                    cursor = await conn.execute(
                        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (self.table_name,)
                    )
                    result = (await cursor.fetchone())[0] > 0

                return bool(result)
        except Exception:
            return False

    # Schema management methods
    async def create_table(self, schema: Optional[Dict[str, Any]] = None):
        """Create properties table with specified schema"""
        if schema is None:
            schema = self._get_default_schema()

        create_sql = self._build_create_table_sql(schema)

        async with self._get_connection() as conn:
            if self.database_type == "postgresql":
                await conn.execute(create_sql)
            elif self.database_type == "mysql":
                async with conn.cursor() as cursor:
                    await cursor.execute(create_sql)
                    await conn.commit()
            elif self.database_type == "sqlite":
                await conn.execute(create_sql)
                await conn.commit()

    def _get_default_schema(self) -> Dict[str, Any]:
        """Get default table schema"""
        return {
            "id": "VARCHAR(255) PRIMARY KEY",
            "address": "TEXT",
            "price": "INTEGER",
            "bedrooms": "INTEGER",
            "bathrooms": "DECIMAL(3,1)",
            "sqft": "INTEGER",
            "property_type": "VARCHAR(100)",
            "neighborhood": "VARCHAR(255)",
            "city": "VARCHAR(255)",
            "state": "VARCHAR(50)",
            "zip_code": "VARCHAR(20)",
            "latitude": "DECIMAL(10,8)",
            "longitude": "DECIMAL(11,8)",
            "year_built": "INTEGER",
            "days_on_market": "INTEGER",
            "listing_date": "DATE",
            "status": "VARCHAR(50)",
            "amenities": "TEXT",  # JSON array as text
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        }

    def _build_create_table_sql(self, schema: Dict[str, Any]) -> str:
        """Build CREATE TABLE SQL from schema"""
        columns = []
        for column_name, column_type in schema.items():
            columns.append(f"{column_name} {column_type}")

        return f"CREATE TABLE IF NOT EXISTS {self.table_name} ({', '.join(columns)})"
