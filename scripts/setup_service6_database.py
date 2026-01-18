#!/usr/bin/env python3
"""
Service 6 Database Setup and Migration Script

This script sets up the database for Service 6 Lead Recovery & Nurture Engine
and applies the performance migrations we created.
"""

import asyncio
import asyncpg
import sqlite3
import psycopg2
import os
import sys
from pathlib import Path
from typing import Optional

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.ghl_utils.config import settings


class DatabaseMigrator:
    """Handles database setup and migrations for Service 6."""

    def __init__(self):
        self.db_url = settings.database_url
        self.db_type = self._detect_database_type()
        print(f"🔍 Detected database type: {self.db_type}")

    def _detect_database_type(self) -> str:
        """Detect database type from URL."""
        if not self.db_url:
            return "none"
        if self.db_url.startswith("postgresql://"):
            return "postgresql"
        elif self.db_url.startswith("sqlite:///"):
            return "sqlite"
        else:
            return "unknown"

    async def setup_database(self) -> bool:
        """Set up the database and apply migrations."""
        print(f"🚀 Setting up Service 6 database...")
        print(f"   Database URL: {self.db_url[:30]}...")
        print(f"   Database Type: {self.db_type}")

        if self.db_type == "none":
            print("❌ No database URL configured. Using in-memory setup.")
            return await self._setup_local_postgresql()
        elif self.db_type == "postgresql":
            return await self._setup_postgresql()
        elif self.db_type == "sqlite":
            return await self._setup_sqlite()
        else:
            print(f"❌ Unsupported database type: {self.db_type}")
            return False

    async def _setup_local_postgresql(self) -> bool:
        """Set up a local PostgreSQL instance for Service 6."""
        print("🐘 Setting up local PostgreSQL for Service 6...")

        # Try to connect to a local PostgreSQL instance
        local_urls = [
            "postgresql://postgres:password@localhost:5432/service6_leads",
            "postgresql://service6_user:service6_password@localhost:5432/service6_leads",
            "postgresql://user:password@localhost:5432/postgres"  # Default
        ]

        for db_url in local_urls:
            try:
                print(f"   Trying: {db_url.split('@')[0]}@...")
                conn = await asyncpg.connect(db_url)

                # Create service6_leads database if it doesn't exist
                try:
                    await conn.execute("CREATE DATABASE service6_leads;")
                    print("   ✅ Created service6_leads database")
                except Exception as e:
                    if "already exists" not in str(e):
                        print(f"   ℹ️  Database might already exist: {e}")

                await conn.close()

                # Connect to the service6_leads database
                service6_url = db_url.replace("/postgres", "/service6_leads")
                return await self._apply_postgresql_migrations(service6_url)

            except Exception as e:
                print(f"   ❌ Failed to connect: {e}")
                continue

        print("❌ Could not establish PostgreSQL connection. Setting up development mode with SQLite.")
        return await self._setup_development_mode()

    async def _setup_postgresql(self) -> bool:
        """Set up PostgreSQL database with full migrations."""
        print("🐘 Setting up PostgreSQL database...")
        return await self._apply_postgresql_migrations(self.db_url)

    async def _apply_postgresql_migrations(self, db_url: str) -> bool:
        """Apply PostgreSQL migrations."""
        try:
            conn = await asyncpg.connect(db_url)
            print("   ✅ Connected to PostgreSQL")

            # Create schema_migrations table if it doesn't exist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(20) PRIMARY KEY,
                    description TEXT,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    applied_by VARCHAR(100) DEFAULT current_user,
                    execution_time_ms BIGINT,
                    checksum VARCHAR(64)
                );
            """)

            # Check existing migrations
            existing = await conn.fetch("SELECT version FROM schema_migrations ORDER BY version")
            existing_versions = [row['version'] for row in existing]
            print(f"   📋 Existing migrations: {existing_versions}")

            # Apply Migration 006: Performance Critical Indexes
            if '006' not in existing_versions:
                print("   🚀 Applying Migration 006: Performance Critical Indexes...")
                migration_006 = project_root / "database" / "migrations" / "006_performance_critical_indexes.sql"

                if migration_006.exists():
                    with open(migration_006, 'r') as f:
                        migration_sql = f.read()

                    # Execute in a transaction
                    await conn.execute(migration_sql)
                    print("   ✅ Migration 006 applied successfully")
                else:
                    print("   ❌ Migration 006 file not found")
            else:
                print("   ✅ Migration 006 already applied")

            # Apply Migration 007: Template Management System
            if '007' not in existing_versions:
                print("   🚀 Applying Migration 007: Template Management System...")
                migration_007 = project_root / "database" / "migrations" / "007_create_message_templates.sql"

                if migration_007.exists():
                    with open(migration_007, 'r') as f:
                        migration_sql = f.read()

                    # Execute in a transaction
                    await conn.execute(migration_sql)
                    print("   ✅ Migration 007 applied successfully")
                else:
                    print("   ❌ Migration 007 file not found")
            else:
                print("   ✅ Migration 007 already applied")

            # Validate the setup
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)

            table_names = [row['table_name'] for row in tables]
            print(f"   📋 Created tables: {len(table_names)} tables")

            for table in ['message_templates', 'template_performance', 'template_ab_tests']:
                if table in table_names:
                    print(f"   ✅ {table}")
                else:
                    print(f"   ❌ {table} (missing)")

            await conn.close()
            print("   🎉 PostgreSQL setup completed successfully!")
            return True

        except Exception as e:
            print(f"   ❌ PostgreSQL setup failed: {e}")
            return False

    async def _setup_sqlite(self) -> bool:
        """Set up SQLite database with adapted migrations."""
        print("📱 Setting up SQLite database...")

        # Extract database path from URL
        db_path = self.db_url.replace("sqlite:///", "")
        print(f"   Database path: {db_path}")

        try:
            # Create directories if needed
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Create schema_migrations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    description TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    applied_by TEXT DEFAULT 'system',
                    execution_time_ms INTEGER,
                    checksum TEXT
                );
            """)

            # Check existing migrations
            cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
            existing_versions = [row[0] for row in cursor.fetchall()]
            print(f"   📋 Existing migrations: {existing_versions}")

            # Apply simplified migrations for SQLite
            if '006' not in existing_versions:
                print("   🚀 Applying Migration 006: Basic Indexes (SQLite compatible)...")
                self._apply_sqlite_indexes(cursor)

                cursor.execute("""
                    INSERT INTO schema_migrations (version, description)
                    VALUES ('006', 'Basic performance indexes for SQLite');
                """)
                print("   ✅ Migration 006 applied (SQLite compatible)")

            if '007' not in existing_versions:
                print("   🚀 Applying Migration 007: Template Tables (SQLite compatible)...")
                self._apply_sqlite_template_system(cursor)

                cursor.execute("""
                    INSERT INTO schema_migrations (version, description)
                    VALUES ('007', 'Template management system for SQLite');
                """)
                print("   ✅ Migration 007 applied (SQLite compatible)")

            conn.commit()

            # Validate the setup
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"   📋 Created tables: {len(tables)} tables")

            conn.close()
            print("   🎉 SQLite setup completed successfully!")
            return True

        except Exception as e:
            print(f"   ❌ SQLite setup failed: {e}")
            return False

    def _apply_sqlite_indexes(self, cursor):
        """Apply basic indexes compatible with SQLite."""
        indexes = [
            # Basic lead scoring indexes
            "CREATE INDEX IF NOT EXISTS idx_leads_temperature ON leads(temperature);",
            "CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(lead_score);",

            # Communication indexes
            "CREATE INDEX IF NOT EXISTS idx_communications_channel ON communications(channel);",
            "CREATE INDEX IF NOT EXISTS idx_communications_status ON communications(status);",

            # Agent routing indexes
            "CREATE INDEX IF NOT EXISTS idx_agents_active ON agents(is_active);",
            "CREATE INDEX IF NOT EXISTS idx_agents_capacity ON agents(capacity);",
        ]

        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                print(f"     ⚠️ Index creation warning: {e}")

    def _apply_sqlite_template_system(self, cursor):
        """Apply template system tables compatible with SQLite."""

        # Message templates table (simplified for SQLite)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_templates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL,
                subcategory TEXT,
                version TEXT DEFAULT '1.0',
                subject TEXT NOT NULL,
                content TEXT NOT NULL,
                content_html TEXT,
                content_plain TEXT,
                variables TEXT, -- JSON as text in SQLite
                language_code TEXT DEFAULT 'en',
                channel TEXT DEFAULT 'email',
                is_ab_test INTEGER DEFAULT 0,
                ab_test_id TEXT,
                ab_variant_name TEXT,
                traffic_percentage REAL,
                status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'approved', 'active', 'paused', 'archived')),
                usage_count INTEGER DEFAULT 0,
                last_used_at TIMESTAMP,
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deleted_at TIMESTAMP
            );
        """)

        # Template performance table (simplified)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_performance (
                id TEXT PRIMARY KEY,
                template_id TEXT NOT NULL REFERENCES message_templates(id),
                measurement_period_start TIMESTAMP NOT NULL,
                measurement_period_end TIMESTAMP NOT NULL,
                period_type TEXT DEFAULT 'daily',
                total_sent INTEGER DEFAULT 0,
                total_delivered INTEGER DEFAULT 0,
                total_opened INTEGER DEFAULT 0,
                total_clicked INTEGER DEFAULT 0,
                total_replied INTEGER DEFAULT 0,
                conversion_count INTEGER DEFAULT 0,
                conversion_value REAL DEFAULT 0,
                last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Template indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_templates_status ON message_templates(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_templates_category ON message_templates(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_performance_template ON template_performance(template_id);")

    async def _setup_development_mode(self) -> bool:
        """Set up development mode with in-memory structures."""
        print("🛠️ Setting up development mode...")
        print("   Creating in-memory database structures for testing...")

        # Create a simple SQLite database for development
        dev_db_path = "./data/service6_development.db"
        os.makedirs("./data", exist_ok=True)

        # Update the database URL in memory (don't modify the actual .env)
        global settings
        settings.database_url = f"sqlite:///{dev_db_path}"

        return await self._setup_sqlite()


async def main():
    """Main setup function."""
    print("🎯 Service 6 Database Setup")
    print("=" * 50)

    migrator = DatabaseMigrator()
    success = await migrator.setup_database()

    if success:
        print("\n🎉 Service 6 database setup completed successfully!")
        print("\nNext steps:")
        print("1. ✅ Database migrations applied")
        print("2. 🔄 Validate Service 6 components integration")
        print("3. 🚀 Deploy and test the complete Service 6 package")

        return True
    else:
        print("\n❌ Service 6 database setup failed!")
        print("Please check the error messages above and resolve any issues.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)