"""
Production Database Service for Service 6 Lead Recovery & Nurture Engine.

Replaces all mock database implementations with production PostgreSQL.
Features:
- Connection pooling for high-volume processing
- Transaction management with proper rollback
- Database migrations and version control
- Optimized indexing for performance
- Health checks and monitoring
"""

import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import asyncpg
from asyncpg import Pool, Connection
from pydantic import BaseModel

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.database.connection_manager import DatabaseConnectionManager

logger = get_logger(__name__)


class LeadStatus(Enum):
    """Lead status enumeration."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NURTURING = "nurturing"
    HOT = "hot"
    CONVERTED = "converted"
    LOST = "lost"
    SILENT = "silent"


class CommunicationChannel(Enum):
    """Communication channel types."""
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    WEBHOOK = "webhook"


class CampaignStatus(Enum):
    """Nurture campaign status."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ============================================================================
# Database Models
# ============================================================================

class Lead(BaseModel):
    """Lead data model."""
    id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    source: str
    status: LeadStatus
    score: int = 0
    temperature: str = "cold"  # hot, warm, cold
    assigned_agent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_interaction_at: Optional[datetime] = None
    enrichment_data: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    tags: List[str] = []
    
    class Config:
        use_enum_values = True


class CommunicationLog(BaseModel):
    """Communication log model."""
    id: str
    lead_id: str
    channel: CommunicationChannel
    direction: str  # inbound, outbound
    content: str
    status: str  # sent, delivered, failed, opened, clicked
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    campaign_id: Optional[str] = None
    template_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class NurtureCampaign(BaseModel):
    """Nurture campaign model."""
    id: str
    name: str
    description: str
    status: CampaignStatus
    trigger_conditions: Dict[str, Any]
    steps: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    active_leads_count: int = 0
    completed_leads_count: int = 0
    conversion_rate: float = 0.0
    
    class Config:
        use_enum_values = True


class LeadCampaignStatus(BaseModel):
    """Lead's status within a specific campaign."""
    id: str
    lead_id: str
    campaign_id: str
    current_step: int
    status: str  # enrolled, active, completed, cancelled
    enrolled_at: datetime
    completed_at: Optional[datetime] = None
    next_action_at: Optional[datetime] = None


class DatabaseService:
    """
    Production database service for Service 6.

    Enhanced with enterprise-grade DatabaseConnectionManager for:
    - Advanced connection pooling with health monitoring
    - Query performance tracking and optimization
    - Transaction management with circuit breaker pattern
    - Real-time performance metrics and alerting
    - Automated failover and recovery
    """

    def __init__(self, database_url: str = None):
        """Initialize database service with enterprise connection manager."""
        self.database_url = database_url or settings.database_url
        self.pool: Optional[Pool] = None
        self._initialized = False

        # Initialize enterprise connection manager
        self.connection_manager = DatabaseConnectionManager(
            connection_string=self.database_url,
            min_connections=5,
            max_connections=20,
            pool_name="service6_lead_engine"
        )
    
    async def initialize(self) -> None:
        """Initialize database connection pool with enterprise manager."""
        if self._initialized:
            return

        try:
            # Initialize enterprise connection manager
            await self.connection_manager.initialize()

            # Get the pool from connection manager for backwards compatibility
            self.pool = self.connection_manager.pool

            # Run database migrations
            await self._run_migrations()

            # Create indexes for performance
            await self._create_indexes()

            self._initialized = True
            logger.info("Database service initialized with enterprise connection manager")

        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise
    
    async def close(self) -> None:
        """Close database connections via enterprise connection manager."""
        if self.connection_manager:
            await self.connection_manager.cleanup()
            self.pool = None
            self._initialized = False
            logger.info("Enterprise database connections closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from enterprise pool with monitoring."""
        if not self._initialized:
            await self.initialize()

        async with self.connection_manager.get_connection() as connection:
            yield connection
    
    @asynccontextmanager
    async def transaction(self):
        """Execute database operations within a transaction."""
        async with self.get_connection() as conn:
            async with conn.transaction():
                yield conn
    
    # ============================================================================
    # Database Schema Migrations
    # ============================================================================
    
    async def _run_migrations(self) -> None:
        """Run database migrations."""
        async with self.get_connection() as conn:
            # Create migrations tracking table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) UNIQUE NOT NULL,
                    applied_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Define migrations
            migrations = [
                ("001_create_leads_table", self._migration_001_create_leads_table),
                ("002_create_communication_logs", self._migration_002_create_communication_logs),
                ("003_create_nurture_campaigns", self._migration_003_create_nurture_campaigns),
                ("004_create_lead_campaign_status", self._migration_004_create_lead_campaign_status),
                ("005_add_audit_fields", self._migration_005_add_audit_fields)
            ]
            
            # Check and apply migrations
            for version, migration_func in migrations:
                exists = await conn.fetchval(
                    "SELECT 1 FROM migrations WHERE version = $1", version
                )
                
                if not exists:
                    logger.info(f"Applying migration: {version}")
                    await migration_func(conn)
                    await conn.execute(
                        "INSERT INTO migrations (version) VALUES ($1)", version
                    )
    
    async def _migration_001_create_leads_table(self, conn: Connection) -> None:
        """Create leads table."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20),
                source VARCHAR(100) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'new',
                score INTEGER DEFAULT 0,
                temperature VARCHAR(10) DEFAULT 'cold',
                assigned_agent_id UUID,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                last_interaction_at TIMESTAMP,
                enrichment_data JSONB DEFAULT '{}',
                preferences JSONB DEFAULT '{}',
                tags TEXT[] DEFAULT '{}',
                
                CONSTRAINT valid_status CHECK (status IN ('new', 'contacted', 'qualified', 'nurturing', 'hot', 'converted', 'lost', 'silent')),
                CONSTRAINT valid_temperature CHECK (temperature IN ('hot', 'warm', 'cold')),
                CONSTRAINT valid_score CHECK (score >= 0 AND score <= 100)
            )
        """)
    
    async def _migration_002_create_communication_logs(self, conn: Connection) -> None:
        """Create communication logs table."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS communication_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
                channel VARCHAR(20) NOT NULL,
                direction VARCHAR(10) NOT NULL,
                content TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'sent',
                sent_at TIMESTAMP DEFAULT NOW(),
                delivered_at TIMESTAMP,
                campaign_id UUID,
                template_id UUID,
                metadata JSONB DEFAULT '{}',
                
                CONSTRAINT valid_channel CHECK (channel IN ('email', 'sms', 'phone', 'webhook')),
                CONSTRAINT valid_direction CHECK (direction IN ('inbound', 'outbound'))
            )
        """)
    
    async def _migration_003_create_nurture_campaigns(self, conn: Connection) -> None:
        """Create nurture campaigns table."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS nurture_campaigns (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(200) NOT NULL,
                description TEXT,
                status VARCHAR(20) DEFAULT 'active',
                trigger_conditions JSONB NOT NULL DEFAULT '{}',
                steps JSONB NOT NULL DEFAULT '[]',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                active_leads_count INTEGER DEFAULT 0,
                completed_leads_count INTEGER DEFAULT 0,
                conversion_rate DECIMAL(5,4) DEFAULT 0.0,
                
                CONSTRAINT valid_campaign_status CHECK (status IN ('active', 'paused', 'completed', 'cancelled'))
            )
        """)
    
    async def _migration_004_create_lead_campaign_status(self, conn: Connection) -> None:
        """Create lead campaign status table."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS lead_campaign_status (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
                campaign_id UUID NOT NULL REFERENCES nurture_campaigns(id) ON DELETE CASCADE,
                current_step INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'enrolled',
                enrolled_at TIMESTAMP DEFAULT NOW(),
                completed_at TIMESTAMP,
                next_action_at TIMESTAMP,
                
                CONSTRAINT valid_lead_campaign_status CHECK (status IN ('enrolled', 'active', 'completed', 'cancelled')),
                UNIQUE(lead_id, campaign_id)
            )
        """)
    
    async def _migration_005_add_audit_fields(self, conn: Connection) -> None:
        """Add audit fields to existing tables."""
        # Add audit fields to leads
        await conn.execute("""
            ALTER TABLE leads 
            ADD COLUMN IF NOT EXISTS created_by UUID,
            ADD COLUMN IF NOT EXISTS updated_by UUID
        """)
        
        # Add audit fields to campaigns
        await conn.execute("""
            ALTER TABLE nurture_campaigns 
            ADD COLUMN IF NOT EXISTS created_by UUID,
            ADD COLUMN IF NOT EXISTS updated_by UUID
        """)
    
    async def _create_indexes(self) -> None:
        """Create database indexes for performance."""
        async with self.get_connection() as conn:
            indexes = [
                # Leads table indexes
                "CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email)",
                "CREATE INDEX IF NOT EXISTS idx_leads_phone ON leads(phone)",
                "CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)",
                "CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score DESC)",
                "CREATE INDEX IF NOT EXISTS idx_leads_temperature ON leads(temperature)",
                "CREATE INDEX IF NOT EXISTS idx_leads_assigned_agent ON leads(assigned_agent_id)",
                "CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_leads_last_interaction ON leads(last_interaction_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_leads_source ON leads(source)",
                
                # Communication logs indexes
                "CREATE INDEX IF NOT EXISTS idx_comm_lead_id ON communication_logs(lead_id)",
                "CREATE INDEX IF NOT EXISTS idx_comm_sent_at ON communication_logs(sent_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_comm_channel ON communication_logs(channel)",
                "CREATE INDEX IF NOT EXISTS idx_comm_status ON communication_logs(status)",
                "CREATE INDEX IF NOT EXISTS idx_comm_campaign_id ON communication_logs(campaign_id)",
                
                # Nurture campaigns indexes
                "CREATE INDEX IF NOT EXISTS idx_campaigns_status ON nurture_campaigns(status)",
                "CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON nurture_campaigns(created_at DESC)",
                
                # Lead campaign status indexes
                "CREATE INDEX IF NOT EXISTS idx_lead_campaign_lead_id ON lead_campaign_status(lead_id)",
                "CREATE INDEX IF NOT EXISTS idx_lead_campaign_campaign_id ON lead_campaign_status(campaign_id)",
                "CREATE INDEX IF NOT EXISTS idx_lead_campaign_next_action ON lead_campaign_status(next_action_at)",
                "CREATE INDEX IF NOT EXISTS idx_lead_campaign_status ON lead_campaign_status(status)",
                
                # Composite indexes for common queries
                "CREATE INDEX IF NOT EXISTS idx_leads_status_score ON leads(status, score DESC)",
                "CREATE INDEX IF NOT EXISTS idx_leads_temperature_last_interaction ON leads(temperature, last_interaction_at)",
                "CREATE INDEX IF NOT EXISTS idx_comm_lead_sent ON communication_logs(lead_id, sent_at DESC)"
            ]
            
            for index_sql in indexes:
                try:
                    await conn.execute(index_sql)
                except Exception as e:
                    logger.warning(f"Index creation failed (may already exist): {e}")
    
    # ============================================================================
    # Lead Management
    # ============================================================================
    
    async def create_lead(self, lead_data: Dict[str, Any], created_by: str = None) -> str:
        """Create a new lead record."""
        async with self.transaction() as conn:
            lead_id = str(uuid.uuid4())
            
            await conn.execute("""
                INSERT INTO leads (
                    id, first_name, last_name, email, phone, source, 
                    status, score, temperature, assigned_agent_id,
                    enrichment_data, preferences, tags, created_by
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """, 
                lead_id,
                lead_data.get("first_name"),
                lead_data.get("last_name"),
                lead_data.get("email"),
                lead_data.get("phone"),
                lead_data.get("source"),
                lead_data.get("status", "new"),
                lead_data.get("score", 0),
                lead_data.get("temperature", "cold"),
                lead_data.get("assigned_agent_id"),
                json.dumps(lead_data.get("enrichment_data", {})),
                json.dumps(lead_data.get("preferences", {})),
                lead_data.get("tags", []),
                created_by
            )
            
            logger.info(f"Created lead {lead_id} for {lead_data.get('email')}")
            return lead_id
    
    async def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get lead by ID."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow("SELECT * FROM leads WHERE id = $1", lead_id)
            
            if row:
                return dict(row)
            return None
    
    async def get_lead_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get lead by email address."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow("SELECT * FROM leads WHERE email = $1", email)
            
            if row:
                return dict(row)
            return None
    
    async def update_lead(self, lead_id: str, updates: Dict[str, Any], updated_by: str = None) -> bool:
        """Update lead record."""
        async with self.transaction() as conn:
            # Build dynamic update query
            set_clauses = ["updated_at = NOW()"]
            values = []
            param_count = 1
            
            for field, value in updates.items():
                if field in ["enrichment_data", "preferences"]:
                    set_clauses.append(f"{field} = ${param_count}")
                    values.append(json.dumps(value))
                elif field == "tags":
                    set_clauses.append(f"{field} = ${param_count}")
                    values.append(value)
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
                SET {', '.join(set_clauses)}
                WHERE id = ${param_count}
            """
            
            result = await conn.execute(query, *values)
            
            # Check if any rows were affected
            rows_affected = int(result.split()[-1])
            
            if rows_affected > 0:
                logger.info(f"Updated lead {lead_id} with fields: {list(updates.keys())}")
                return True
            else:
                logger.warning(f"No lead found with ID {lead_id}")
                return False
    
    async def search_leads(self, filters: Dict[str, Any] = None, 
                          limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Search leads with filters."""
        async with self.get_connection() as conn:
            where_clauses = []
            values = []
            param_count = 1
            
            if filters:
                for field, value in filters.items():
                    if field == "status":
                        where_clauses.append(f"status = ${param_count}")
                        values.append(value)
                    elif field == "temperature":
                        where_clauses.append(f"temperature = ${param_count}")
                        values.append(value)
                    elif field == "score_min":
                        where_clauses.append(f"score >= ${param_count}")
                        values.append(value)
                    elif field == "score_max":
                        where_clauses.append(f"score <= ${param_count}")
                        values.append(value)
                    elif field == "created_after":
                        where_clauses.append(f"created_at >= ${param_count}")
                        values.append(value)
                    elif field == "created_before":
                        where_clauses.append(f"created_at <= ${param_count}")
                        values.append(value)
                    elif field == "assigned_agent_id":
                        where_clauses.append(f"assigned_agent_id = ${param_count}")
                        values.append(value)
                    elif field == "source":
                        where_clauses.append(f"source = ${param_count}")
                        values.append(value)
                    param_count += 1
            
            # Add limit and offset
            values.extend([limit, offset])
            limit_param = param_count
            offset_param = param_count + 1
            
            where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            query = f"""
                SELECT * FROM leads 
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ${limit_param} OFFSET ${offset_param}
            """
            
            rows = await conn.fetch(query, *values)
            return [dict(row) for row in rows]
    
    async def get_silent_leads(self, silence_threshold_hours: int = 24) -> List[Dict[str, Any]]:
        """Get leads that have gone silent."""
        cutoff_time = datetime.utcnow() - timedelta(hours=silence_threshold_hours)
        
        async with self.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM leads 
                WHERE status IN ('contacted', 'qualified', 'nurturing')
                  AND last_interaction_at < $1
                  AND last_interaction_at IS NOT NULL
                ORDER BY last_interaction_at ASC
            """, cutoff_time)
            
            return [dict(row) for row in rows]
    
    # ============================================================================
    # Communication Logs
    # ============================================================================
    
    async def log_communication(self, comm_data: Dict[str, Any]) -> str:
        """Log communication event."""
        async with self.transaction() as conn:
            comm_id = str(uuid.uuid4())
            
            await conn.execute("""
                INSERT INTO communication_logs (
                    id, lead_id, channel, direction, content, status,
                    campaign_id, template_id, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
                comm_id,
                comm_data["lead_id"],
                comm_data["channel"],
                comm_data["direction"],
                comm_data["content"],
                comm_data.get("status", "sent"),
                comm_data.get("campaign_id"),
                comm_data.get("template_id"),
                json.dumps(comm_data.get("metadata", {}))
            )
            
            # Update lead's last interaction time for outbound messages
            if comm_data["direction"] == "outbound":
                await conn.execute("""
                    UPDATE leads 
                    SET last_interaction_at = NOW(), updated_at = NOW()
                    WHERE id = $1
                """, comm_data["lead_id"])
            
            return comm_id
    
    async def get_lead_communications(self, lead_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get communication history for a lead."""
        async with self.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM communication_logs 
                WHERE lead_id = $1
                ORDER BY sent_at DESC
                LIMIT $2
            """, lead_id, limit)
            
            return [dict(row) for row in rows]
    
    async def update_communication_status(self, comm_id: str, status: str, 
                                        delivered_at: datetime = None) -> bool:
        """Update communication delivery status."""
        async with self.transaction() as conn:
            if delivered_at:
                result = await conn.execute("""
                    UPDATE communication_logs 
                    SET status = $1, delivered_at = $2
                    WHERE id = $3
                """, status, delivered_at, comm_id)
            else:
                result = await conn.execute("""
                    UPDATE communication_logs 
                    SET status = $1
                    WHERE id = $2
                """, status, comm_id)
            
            rows_affected = int(result.split()[-1])
            return rows_affected > 0
    
    # ============================================================================
    # Nurture Campaigns
    # ============================================================================
    
    async def create_nurture_campaign(self, campaign_data: Dict[str, Any], 
                                    created_by: str = None) -> str:
        """Create a new nurture campaign."""
        async with self.transaction() as conn:
            campaign_id = str(uuid.uuid4())
            
            await conn.execute("""
                INSERT INTO nurture_campaigns (
                    id, name, description, status, trigger_conditions, 
                    steps, created_by
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
                campaign_id,
                campaign_data["name"],
                campaign_data.get("description"),
                campaign_data.get("status", "active"),
                json.dumps(campaign_data["trigger_conditions"]),
                json.dumps(campaign_data["steps"]),
                created_by
            )
            
            return campaign_id
    
    async def get_active_campaigns(self) -> List[Dict[str, Any]]:
        """Get all active nurture campaigns."""
        async with self.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM nurture_campaigns 
                WHERE status = 'active'
                ORDER BY created_at DESC
            """)
            
            return [dict(row) for row in rows]
    
    async def enroll_lead_in_campaign(self, lead_id: str, campaign_id: str,
                                    next_action_at: datetime = None) -> str:
        """Enroll a lead in a nurture campaign."""
        async with self.transaction() as conn:
            enrollment_id = str(uuid.uuid4())
            
            await conn.execute("""
                INSERT INTO lead_campaign_status (
                    id, lead_id, campaign_id, status, next_action_at
                )
                VALUES ($1, $2, $3, 'enrolled', $4)
                ON CONFLICT (lead_id, campaign_id) DO NOTHING
            """,
                enrollment_id, lead_id, campaign_id, next_action_at
            )
            
            # Update campaign active leads count
            await conn.execute("""
                UPDATE nurture_campaigns 
                SET active_leads_count = active_leads_count + 1
                WHERE id = $1
            """, campaign_id)
            
            return enrollment_id
    
    async def get_due_campaign_actions(self) -> List[Dict[str, Any]]:
        """Get campaign actions that are due for execution."""
        async with self.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT lcs.*, l.email, l.first_name, l.last_name, 
                       nc.name as campaign_name, nc.steps
                FROM lead_campaign_status lcs
                JOIN leads l ON lcs.lead_id = l.id
                JOIN nurture_campaigns nc ON lcs.campaign_id = nc.id
                WHERE lcs.status = 'active' 
                  AND lcs.next_action_at <= NOW()
                  AND nc.status = 'active'
                ORDER BY lcs.next_action_at ASC
            """)
            
            return [dict(row) for row in rows]
    
    # ============================================================================
    # Health Checks & Monitoring
    # ============================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            start_time = datetime.utcnow()
            
            async with self.get_connection() as conn:
                # Test basic connectivity
                result = await conn.fetchval("SELECT 1")
                
                # Check table counts
                leads_count = await conn.fetchval("SELECT COUNT(*) FROM leads")
                comms_count = await conn.fetchval("SELECT COUNT(*) FROM communication_logs")
                campaigns_count = await conn.fetchval("SELECT COUNT(*) FROM nurture_campaigns")
                
                # Check recent activity
                recent_leads = await conn.fetchval("""
                    SELECT COUNT(*) FROM leads 
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """)
                
                response_time = (datetime.utcnow() - start_time).total_seconds()
                
                return {
                    "status": "healthy",
                    "response_time_seconds": response_time,
                    "database_connected": result == 1,
                    "stats": {
                        "total_leads": leads_count,
                        "total_communications": comms_count,
                        "total_campaigns": campaigns_count,
                        "leads_today": recent_leads
                    },
                    "pool_stats": {
                        "size": self.pool.get_size() if self.pool else 0,
                        "idle": self.pool.get_idle_size() if self.pool else 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_seconds": None
            }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive database performance metrics via enterprise connection manager."""
        async with self.get_connection() as conn:
            metrics = {}

            # Get enterprise connection manager metrics
            connection_metrics = await self.connection_manager.get_pool_metrics()
            metrics["connection_pool"] = connection_metrics

            # Get query performance metrics
            query_metrics = await self.connection_manager.get_query_performance_summary()
            metrics["query_performance"] = query_metrics

            # Table sizes
            table_sizes = await conn.fetch("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as bytes
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """)

            metrics["table_sizes"] = [dict(row) for row in table_sizes]

            # Recent activity
            activity = await conn.fetchrow("""
                SELECT
                    (SELECT COUNT(*) FROM leads WHERE created_at >= NOW() - INTERVAL '1 hour') as leads_last_hour,
                    (SELECT COUNT(*) FROM communication_logs WHERE sent_at >= NOW() - INTERVAL '1 hour') as comms_last_hour,
                    (SELECT COUNT(*) FROM leads WHERE status = 'new') as new_leads,
                    (SELECT COUNT(*) FROM leads WHERE status = 'hot') as hot_leads
            """)

            metrics["activity"] = dict(activity) if activity else {}

            return metrics

    async def execute_optimized_query(self, sql: str, *args, timeout: Optional[float] = None) -> Any:
        """Execute query with enterprise connection manager's optimization and monitoring."""
        return await self.connection_manager.execute_query(
            sql, *args, timeout=timeout, record_execution=True
        )

    async def get_connection_health(self) -> Dict[str, Any]:
        """Get detailed connection health metrics."""
        health = await self.connection_manager.health_check()
        return {
            "enterprise_connection_manager": health,
            "database_specific": await self.health_check()
        }


# ============================================================================
# Database Factory & Connection Management
# ============================================================================

class DatabaseManager:
    """Database connection manager singleton."""
    
    _instance = None
    _service = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_service(self) -> DatabaseService:
        """Get database service instance."""
        if self._service is None:
            self._service = DatabaseService()
            await self._service.initialize()
        return self._service
    
    async def close(self):
        """Close database service."""
        if self._service:
            await self._service.close()
            self._service = None


# Global database manager instance
db_manager = DatabaseManager()


# ============================================================================
# Convenience Functions
# ============================================================================

async def get_database() -> DatabaseService:
    """Get database service instance."""
    return await db_manager.get_service()


async def create_lead(lead_data: Dict[str, Any]) -> str:
    """Convenience function to create a lead."""
    db = await get_database()
    return await db.create_lead(lead_data)


async def get_lead(lead_id: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get a lead."""
    db = await get_database()
    return await db.get_lead(lead_id)


async def log_communication(comm_data: Dict[str, Any]) -> str:
    """Convenience function to log communication."""
    db = await get_database()
    return await db.log_communication(comm_data)


# ============================================================================
# Example Usage & Testing
# ============================================================================

if __name__ == "__main__":
    async def test_database_service():
        """Test database service functionality."""
        db = DatabaseService()
        await db.initialize()
        
        try:
            # Test lead creation
            lead_data = {
                "first_name": "John",
                "last_name": "Doe", 
                "email": "john.doe@example.com",
                "phone": "+1234567890",
                "source": "website",
                "status": "new"
            }
            
            lead_id = await db.create_lead(lead_data, created_by="test-system")
            print(f"Created lead: {lead_id}")
            
            # Test lead retrieval
            lead = await db.get_lead(lead_id)
            print(f"Retrieved lead: {lead['email']}")
            
            # Test communication logging
            comm_data = {
                "lead_id": lead_id,
                "channel": "email",
                "direction": "outbound",
                "content": "Welcome to our service!",
                "status": "sent"
            }
            
            comm_id = await db.log_communication(comm_data)
            print(f"Logged communication: {comm_id}")
            
            # Test health check
            health = await db.health_check()
            print(f"Health check: {health}")
            
        finally:
            await db.close()
    
    # Run test
    asyncio.run(test_database_service())