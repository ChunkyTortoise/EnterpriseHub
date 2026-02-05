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
from pydantic import BaseModel, ConfigDict

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


class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""
    pass


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
    
    model_config = ConfigDict(use_enum_values=True)


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
    
    model_config = ConfigDict(use_enum_values=True)


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
    
    model_config = ConfigDict(use_enum_values=True)


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
        async with self.connection_manager.get_connection() as conn:
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
                ("005_add_audit_fields", self._migration_005_add_audit_fields),
                ("006_create_clv_predictions", self._migration_006_create_clv_predictions),
                ("007_create_behavioral_signals", self._migration_007_create_behavioral_signals),
                ("008_create_billing_tables", self._migration_008_create_billing_tables),
                ("009_create_lead_activity_tables", self._migration_009_create_lead_activity_tables),
                ("010_create_lead_journey_state", self._migration_010_create_lead_journey_state),
                ("011_create_model_outcomes", self._migration_011_create_model_outcomes),
                ("012_create_users_table", self._migration_012_create_users_table),
                ("013_create_follow_up_tasks", self._migration_013_create_follow_up_tasks),
                ("014_create_market_intelligence_tables", self._migration_014_create_market_intelligence_tables),
                ("015_create_agents_table", self._migration_015_create_agents_table),
                ("016_create_notifications_table", self._migration_016_create_notifications_table),
                ("017_create_sessions_table", self._migration_017_create_sessions_table),
                ("018_add_currency_to_subscriptions", self._migration_018_add_currency_to_subscriptions)
            ]
            
            # Check and apply migrations
            applied = await conn.fetch("SELECT version FROM migrations")
            applied_versions = {row["version"] for row in applied}
            
            for version, migration_func in migrations:
                if version not in applied_versions:
                    logger.info(f"Applying migration: {version}")
                    await migration_func(conn)
                    await conn.execute("INSERT INTO migrations (version) VALUES ($1)", version)

    async def _migration_016_create_notifications_table(self, conn: Connection) -> None:
        """Create table for notifications."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL,
                location_id VARCHAR(100) NOT NULL,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                type VARCHAR(50) DEFAULT 'info',
                is_read BOOLEAN DEFAULT FALSE,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                read_at TIMESTAMP WITH TIME ZONE
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = FALSE")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_notifications_location ON notifications(location_id)")

    async def _migration_017_create_sessions_table(self, conn: Connection) -> None:
        """Create table for persistent sessions (Implementation 11)."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                user_id UUID NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                status VARCHAR(20) DEFAULT 'active',
                risk_score DECIMAL(3, 2) DEFAULT 0.0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                metadata JSONB DEFAULT '{}'
            )
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)")

    async def _migration_018_add_currency_to_subscriptions(self, conn: Connection) -> None:
        """Add currency column to subscriptions table (Phase 7)."""
        await conn.execute("""
            ALTER TABLE subscriptions 
            ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'usd'
        """)

    async def _migration_011_create_model_outcomes(self, conn: Connection) -> None:
        """Create table for feedback loop retraining data."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS model_outcomes (
                id SERIAL PRIMARY KEY,
                lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
                outcome VARCHAR(50) NOT NULL, -- 'won', 'lost', 'no_show', etc.
                monetary_value DECIMAL(12, 2) DEFAULT 0.0,
                recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

    async def _migration_012_create_users_table(self, conn: Connection) -> None:
        """Create users table for authentication and RBAC."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                roles TEXT[] DEFAULT '{user}',
                provider VARCHAR(50) DEFAULT 'local',
                is_active BOOLEAN DEFAULT TRUE,
                is_verified BOOLEAN DEFAULT FALSE,
                is_admin BOOLEAN DEFAULT FALSE,
                mfa_enabled BOOLEAN DEFAULT FALSE,
                mfa_secret VARCHAR(100),
                failed_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP WITH TIME ZONE,
                password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_login TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

    async def _migration_013_create_follow_up_tasks(self, conn: Connection) -> None:
        """Create table for autonomous follow-up tasks."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS follow_up_tasks (
                id VARCHAR(100) PRIMARY KEY,
                lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
                contact_id VARCHAR(100) NOT NULL,
                channel VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                priority INTEGER DEFAULT 1,
                intent_level VARCHAR(20),
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                executed_at TIMESTAMP WITH TIME ZONE,
                result JSONB DEFAULT '{}'
            )
        """)
        
        # Add indexes for task queue performance
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_follow_up_tasks_status_time ON follow_up_tasks(status, scheduled_time ASC);
            CREATE INDEX IF NOT EXISTS idx_follow_up_tasks_lead_id ON follow_up_tasks(lead_id);
            CREATE INDEX IF NOT EXISTS idx_follow_up_tasks_priority ON follow_up_tasks(priority DESC);
        """)

    async def _migration_014_create_market_intelligence_tables(self, conn: Connection) -> None:
        """Create tables for market intelligence and competitive analysis."""
        # Market data table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                market_area VARCHAR(100) NOT NULL,
                analysis_period VARCHAR(50) NOT NULL,
                avg_pricing JSONB NOT NULL,
                market_velocity VARCHAR(50),
                inventory_levels VARCHAR(50),
                market_share JSONB,
                competitor_pricing JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(market_area, analysis_period)
            )
        """)

        # Competitor profiles table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS competitor_profiles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                competitor_id VARCHAR(100) UNIQUE NOT NULL,
                name VARCHAR(200) NOT NULL,
                website VARCHAR(255),
                market_areas TEXT[] DEFAULT '{}',
                specialties TEXT[] DEFAULT '{}',
                team_size INTEGER,
                threat_level VARCHAR(20),
                social_media_handles JSONB DEFAULT '{}',
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Add indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_data_area ON market_data(market_area);
            CREATE INDEX IF NOT EXISTS idx_competitor_profiles_threat ON competitor_profiles(threat_level);
        """)

    async def _migration_015_create_agents_table(self, conn: Connection) -> None:
        """Create table for agents and team members."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(20),
                role VARCHAR(50) DEFAULT 'agent',
                is_active BOOLEAN DEFAULT true,
                specializations JSONB DEFAULT '[]',
                territory JSONB DEFAULT '{}',
                capacity INTEGER DEFAULT 100,
                current_load INTEGER DEFAULT 0,
                avg_response_time_minutes INTEGER DEFAULT 60,
                conversion_rate DECIMAL(5,2) DEFAULT 0.0,
                total_leads_handled INTEGER DEFAULT 0,
                total_conversions INTEGER DEFAULT 0,
                customer_satisfaction DECIMAL(3,2) DEFAULT 0.0,
                working_hours JSONB DEFAULT '{}',
                timezone VARCHAR(50) DEFAULT 'America/Los_Angeles',
                is_available BOOLEAN DEFAULT true,
                last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Add indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_agents_email ON agents(email);
            CREATE INDEX IF NOT EXISTS idx_agents_availability ON agents(is_available, is_active);
            CREATE INDEX IF NOT EXISTS idx_agents_load ON agents(current_load, capacity);
        """)
    
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
    
    async def _migration_006_create_clv_predictions(self, conn: Connection) -> None:
        """Create CLV prediction tables for Predictive CLV Engine."""
        
        # CLV predictions main table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS lead_clv_predictions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                lead_id VARCHAR(255) NOT NULL,
                prediction_id VARCHAR(255) UNIQUE NOT NULL,
                
                -- Core predictions
                predicted_clv_12_month DECIMAL(12,2) NOT NULL,
                predicted_clv_lifetime DECIMAL(12,2) NOT NULL,
                confidence_interval_lower DECIMAL(12,2) NOT NULL,
                confidence_interval_upper DECIMAL(12,2) NOT NULL,
                prediction_confidence DECIMAL(4,3) NOT NULL CHECK (prediction_confidence >= 0 AND prediction_confidence <= 1),
                
                -- Risk assessment
                risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
                volatility_score DECIMAL(8,2) DEFAULT 0.0,
                uncertainty_factors TEXT[], -- Array of uncertainty factor strings
                
                -- Revenue breakdown
                monthly_revenue_forecast DECIMAL(12,2)[] NOT NULL, -- 12-month forecast array
                probability_of_conversion DECIMAL(4,3) NOT NULL CHECK (probability_of_conversion >= 0 AND probability_of_conversion <= 1),
                expected_transaction_value DECIMAL(12,2) NOT NULL,
                expected_commission DECIMAL(12,2) NOT NULL,
                
                -- Behavioral insights
                engagement_trend VARCHAR(20) DEFAULT 'stable' CHECK (engagement_trend IN ('increasing', 'stable', 'declining')),
                buying_readiness_score DECIMAL(5,2) NOT NULL CHECK (buying_readiness_score >= 0 AND buying_readiness_score <= 100),
                
                -- Model metadata
                models_used TEXT[] NOT NULL,
                feature_count INTEGER NOT NULL,
                training_data_size INTEGER DEFAULT 0,
                model_last_updated TIMESTAMP NOT NULL,
                
                -- Benchmarking
                percentile_rank DECIMAL(5,2) NOT NULL CHECK (percentile_rank >= 0 AND percentile_rank <= 100),
                similar_lead_comparison TEXT,
                
                -- Audit fields
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                created_by UUID,
                updated_by UUID
            )
        """)
        
        # Behavioral signals table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS behavioral_signals (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                lead_id VARCHAR(255) NOT NULL,
                prediction_id VARCHAR(255) NOT NULL REFERENCES lead_clv_predictions(prediction_id) ON DELETE CASCADE,
                
                -- Signal data
                signal_name VARCHAR(100) NOT NULL,
                signal_value DECIMAL(5,2) NOT NULL CHECK (signal_value >= 0 AND signal_value <= 100),
                raw_value TEXT, -- Store original value as text for flexibility
                category VARCHAR(50) NOT NULL CHECK (category IN ('engagement', 'communication', 'property_interaction', 'financial', 'behavioral_patterns', 'market_context')),
                
                -- Quality metrics
                importance_score DECIMAL(4,3) NOT NULL CHECK (importance_score >= 0 AND importance_score <= 1),
                confidence DECIMAL(4,3) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
                strength VARCHAR(20) NOT NULL CHECK (strength IN ('weak', 'moderate', 'strong', 'critical')),
                
                -- Temporal data
                signal_timestamp TIMESTAMP NOT NULL,
                trend_direction VARCHAR(20) CHECK (trend_direction IN ('declining', 'stable', 'increasing', 'volatile')),
                trend_velocity DECIMAL(6,3), -- Rate of change
                
                -- Context
                description TEXT NOT NULL,
                extraction_method VARCHAR(100) NOT NULL,
                data_source VARCHAR(100) NOT NULL,
                sample_size INTEGER DEFAULT 1,
                
                -- Anomaly detection
                is_anomaly BOOLEAN DEFAULT FALSE,
                anomaly_score DECIMAL(6,3),
                baseline_comparison DECIMAL(8,2),
                
                -- Audit fields
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Revenue opportunities table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS revenue_opportunities (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                opportunity_id VARCHAR(255) UNIQUE NOT NULL,
                lead_id VARCHAR(255) NOT NULL,
                prediction_id VARCHAR(255) REFERENCES lead_clv_predictions(prediction_id) ON DELETE CASCADE,
                
                -- Opportunity details
                opportunity_type VARCHAR(30) NOT NULL CHECK (opportunity_type IN ('upsell', 'cross_sell', 'retention', 'acceleration', 'referral', 'repeat_business', 'portfolio_expansion')),
                opportunity_score DECIMAL(5,2) NOT NULL CHECK (opportunity_score >= 0 AND opportunity_score <= 100),
                estimated_value DECIMAL(12,2) NOT NULL,
                confidence DECIMAL(4,3) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
                
                -- Urgency and timing
                urgency_level VARCHAR(20) NOT NULL CHECK (urgency_level IN ('low', 'medium', 'high', 'critical')),
                recommended_action TEXT NOT NULL,
                optimal_timing TEXT NOT NULL,
                expiration_date TIMESTAMP,
                
                -- Supporting data
                supporting_evidence TEXT[] NOT NULL,
                
                -- Status tracking
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'pursued', 'completed', 'expired', 'cancelled')),
                pursued_at TIMESTAMP,
                completed_at TIMESTAMP,
                actual_value DECIMAL(12,2), -- Actual value if opportunity was realized
                
                -- Audit fields
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                created_by UUID,
                updated_by UUID
            )
        """)
        
        # Signal baselines table for anomaly detection
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS signal_baselines (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                signal_name VARCHAR(100) NOT NULL,
                
                -- Statistical baselines
                median_value DECIMAL(8,2) NOT NULL,
                mean_value DECIMAL(8,2) NOT NULL,
                std_deviation DECIMAL(8,2) NOT NULL,
                min_value DECIMAL(8,2) NOT NULL,
                max_value DECIMAL(8,2) NOT NULL,
                
                -- Percentiles
                percentile_25 DECIMAL(8,2) NOT NULL,
                percentile_75 DECIMAL(8,2) NOT NULL,
                percentile_95 DECIMAL(8,2) NOT NULL,
                
                -- Sample info
                sample_size INTEGER NOT NULL,
                last_updated TIMESTAMP DEFAULT NOW(),
                
                UNIQUE(signal_name)
            )
        """)
    
    async def _migration_007_create_behavioral_signals(self, conn: Connection) -> None:
        """Create additional behavioral signal tracking tables."""
        
        # Signal extraction results table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS signal_extraction_results (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                extraction_id VARCHAR(255) UNIQUE NOT NULL,
                lead_id VARCHAR(255) NOT NULL,
                
                -- Summary statistics
                total_signals INTEGER NOT NULL,
                strong_signals_count INTEGER NOT NULL,
                average_confidence DECIMAL(4,3) NOT NULL CHECK (average_confidence >= 0 AND average_confidence <= 1),
                extraction_time_ms DECIMAL(10,2) NOT NULL,
                
                -- Quality indicators
                data_completeness_score DECIMAL(5,2) NOT NULL CHECK (data_completeness_score >= 0 AND data_completeness_score <= 100),
                signal_reliability_score DECIMAL(4,3) NOT NULL CHECK (signal_reliability_score >= 0 AND signal_reliability_score <= 1),
                anomalies_detected INTEGER DEFAULT 0,
                
                -- Analysis results
                signal_correlations JSONB, -- Store correlation analysis as JSON
                dominant_trends TEXT[], -- Array of dominant trend directions
                behavioral_profile_summary TEXT NOT NULL,
                
                -- Audit fields
                extraction_timestamp TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Signal correlations table for cross-signal analysis
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS signal_correlations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                lead_id VARCHAR(255) NOT NULL,
                signal_1_name VARCHAR(100) NOT NULL,
                signal_2_name VARCHAR(100) NOT NULL,
                correlation_coefficient DECIMAL(6,3) NOT NULL CHECK (correlation_coefficient >= -1 AND correlation_coefficient <= 1),
                correlation_strength VARCHAR(20) NOT NULL CHECK (correlation_strength IN ('weak', 'moderate', 'strong')),
                significance_level DECIMAL(4,3) NOT NULL,
                sample_size INTEGER NOT NULL,
                analysis_date TIMESTAMP DEFAULT NOW(),
                
                UNIQUE(lead_id, signal_1_name, signal_2_name)
            )
        """)
        
        # Add indexes for CLV prediction tables
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_clv_predictions_lead_id ON lead_clv_predictions(lead_id);
            CREATE INDEX IF NOT EXISTS idx_clv_predictions_confidence ON lead_clv_predictions(prediction_confidence DESC);
            CREATE INDEX IF NOT EXISTS idx_clv_predictions_value ON lead_clv_predictions(predicted_clv_12_month DESC);
            CREATE INDEX IF NOT EXISTS idx_clv_predictions_risk ON lead_clv_predictions(risk_level);
            CREATE INDEX IF NOT EXISTS idx_clv_predictions_created ON lead_clv_predictions(created_at DESC);
        """)
        
        # Behavioral signals indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_behavioral_signals_lead_id ON behavioral_signals(lead_id);
            CREATE INDEX IF NOT EXISTS idx_behavioral_signals_prediction_id ON behavioral_signals(prediction_id);
            CREATE INDEX IF NOT EXISTS idx_behavioral_signals_category ON behavioral_signals(category);
            CREATE INDEX IF NOT EXISTS idx_behavioral_signals_strength ON behavioral_signals(strength);
            CREATE INDEX IF NOT EXISTS idx_behavioral_signals_anomaly ON behavioral_signals(is_anomaly) WHERE is_anomaly = TRUE;
            CREATE INDEX IF NOT EXISTS idx_behavioral_signals_timestamp ON behavioral_signals(signal_timestamp DESC);
        """)
        
        # Revenue opportunities indexes  
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_revenue_opportunities_lead_id ON revenue_opportunities(lead_id);
            CREATE INDEX IF NOT EXISTS idx_revenue_opportunities_type ON revenue_opportunities(opportunity_type);
            CREATE INDEX IF NOT EXISTS idx_revenue_opportunities_score ON revenue_opportunities(opportunity_score DESC);
            CREATE INDEX IF NOT EXISTS idx_revenue_opportunities_urgency ON revenue_opportunities(urgency_level);
            CREATE INDEX IF NOT EXISTS idx_revenue_opportunities_status ON revenue_opportunities(status);
            CREATE INDEX IF NOT EXISTS idx_revenue_opportunities_expiration ON revenue_opportunities(expiration_date) WHERE expiration_date IS NOT NULL;
        """)
        
        # Signal extraction results indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_signal_extraction_lead_id ON signal_extraction_results(lead_id);
            CREATE INDEX IF NOT EXISTS idx_signal_extraction_timestamp ON signal_extraction_results(extraction_timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_signal_extraction_quality ON signal_extraction_results(signal_reliability_score DESC);
        """)
        
        # Signal correlations indexes
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_signal_correlations_lead_id ON signal_correlations(lead_id);
            CREATE INDEX IF NOT EXISTS idx_signal_correlations_signals ON signal_correlations(signal_1_name, signal_2_name);
            CREATE INDEX IF NOT EXISTS idx_signal_correlations_strength ON signal_correlations(correlation_strength);
        """)
    
    async def _migration_008_create_billing_tables(self, conn: Connection) -> None:
        """Create billing and subscription management tables."""
        # Subscriptions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id SERIAL PRIMARY KEY,
                location_id VARCHAR(255) UNIQUE NOT NULL,
                stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
                stripe_customer_id VARCHAR(255) NOT NULL,
                tier VARCHAR(50) NOT NULL,
                status VARCHAR(50) NOT NULL,
                current_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
                current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
                usage_allowance INTEGER NOT NULL,
                usage_current INTEGER DEFAULT 0,
                overage_rate DECIMAL(10, 2) NOT NULL,
                base_price DECIMAL(10, 2) NOT NULL,
                trial_end TIMESTAMP WITH TIME ZONE,
                cancel_at_period_end BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

        # Stripe customers mapping
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS stripe_customers (
                id SERIAL PRIMARY KEY,
                location_id VARCHAR(255) UNIQUE NOT NULL,
                stripe_customer_id VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255),
                name VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

        # Usage records for overage billing
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_records (
                id SERIAL PRIMARY KEY,
                subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE CASCADE,
                stripe_usage_record_id VARCHAR(255) UNIQUE,
                lead_id VARCHAR(255) NOT NULL,
                contact_id VARCHAR(255) NOT NULL,
                quantity INTEGER DEFAULT 1,
                amount DECIMAL(10, 2) NOT NULL,
                tier VARCHAR(50),
                billing_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
                billing_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

    async def _migration_009_create_lead_activity_tables(self, conn: Connection) -> None:
        """Create extended lead activity tracking tables."""
        # Property searches
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS property_searches (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
                search_query JSONB NOT NULL,
                results_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

        # Pricing tool usage
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS pricing_tool_uses (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
                property_details JSONB NOT NULL,
                valuation_result JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

        # Agent inquiries
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_inquiries (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
                agent_id UUID,
                inquiry_text TEXT,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

    async def _migration_010_create_lead_journey_state(self, conn: Connection) -> None:
        """Create lead journey state table for omnichannel persistence."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS lead_journey_state (
                lead_id UUID PRIMARY KEY REFERENCES leads(id) ON DELETE CASCADE,
                current_stage VARCHAR(50) NOT NULL,
                last_channel VARCHAR(20),
                last_interaction_summary TEXT,
                pending_actions JSONB DEFAULT '[]',
                context_data JSONB DEFAULT '{}',
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)

    async def _create_indexes(self) -> None:
        """Create database indexes for performance including Service 6 critical optimizations."""
        async with self.connection_manager.get_connection() as conn:
            # Service 6 Critical Performance Indexes (90%+ improvement potential)
            critical_indexes = [
                # *** CRITICAL PRIORITY - Lead scoring optimization (eliminates full table scans) ***
                "CREATE INDEX IF NOT EXISTS idx_leads_score_status_created ON leads(score DESC, status, created_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_leads_temperature_interaction ON leads(temperature, last_interaction_at DESC, status)",
                "CREATE INDEX IF NOT EXISTS idx_leads_high_intent_routing ON leads(score DESC, status, assigned_agent_id) WHERE score >= 50 AND status IN ('new', 'contacted', 'qualified', 'nurturing', 'hot')",

                # *** COMMUNICATION PERFORMANCE (70%+ improvement) ***
                "CREATE INDEX IF NOT EXISTS idx_comm_followup_history ON communication_logs(lead_id, direction, sent_at DESC) WHERE direction = 'outbound'",
                "CREATE INDEX IF NOT EXISTS idx_comm_response_tracking ON communication_logs(lead_id, direction, sent_at DESC) WHERE direction = 'inbound'",
                "CREATE INDEX IF NOT EXISTS idx_comm_recent_activity ON communication_logs(lead_id, sent_at DESC, channel, status)",

                # *** COVERING INDEXES (90% I/O reduction) ***
                "CREATE INDEX IF NOT EXISTS idx_leads_profile_covering ON leads(id, first_name, last_name, email, phone, status, score, temperature, created_at, last_interaction_at)",
                "CREATE INDEX IF NOT EXISTS idx_comm_history_covering ON communication_logs(lead_id, channel, direction, sent_at, status, content)"
            ]

            # Standard performance indexes
            standard_indexes = [
                # Basic leads table indexes
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

            # Apply critical indexes first (highest impact)
            logger.info("🚀 Applying Service 6 critical performance indexes...")
            for index_sql in critical_indexes:
                try:
                    await conn.execute(index_sql)
                    logger.debug(f"✅ Critical index created: {index_sql.split(' ON ')[1].split('(')[0] if ' ON ' in index_sql else 'index'}")
                except Exception as e:
                    # Only catch "already exists" errors, raise everything else
                    if "already exists" in str(e).lower():
                        logger.debug(f"ℹ️ Critical index already exists: {index_sql.split(' ON ')[1].split('(')[0] if ' ON ' in index_sql else 'index'}")
                    else:
                        logger.error(f"❌ Failed to create critical index: {e}")
                        raise

            # Apply standard indexes
            logger.info("📊 Applying standard performance indexes...")
            for index_sql in standard_indexes:
                try:
                    await conn.execute(index_sql)
                except Exception as e:
                    # Only catch "already exists" errors, raise everything else
                    if "already exists" in str(e).lower():
                        continue
                    else:
                        logger.error(f"❌ Failed to create standard index: {e}")
                        raise

            # Update statistics for query optimizer
            logger.info("📈 Updating database statistics for optimal query planning...")
            try:
                await conn.execute("ANALYZE leads")
                await conn.execute("ANALYZE communication_logs")
                await conn.execute("ANALYZE nurture_campaigns")
                await conn.execute("ANALYZE lead_campaign_status")
                logger.info("✅ Database statistics updated for Service 6 performance optimization")
            except Exception as e:
                logger.error(f"❌ Statistics update failed: {e}")
                raise

            logger.info("🎯 Service 6 performance optimization complete - expecting 90%+ query improvement")
    
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
    # Service 6 Specific Operations
    # ============================================================================

    async def get_lead_follow_up_history(self, lead_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get follow-up communication history for a lead (outbound messages only)."""
        async with self.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT
                    id, channel, content, status, sent_at, delivered_at,
                    campaign_id, template_id, metadata
                FROM communication_logs
                WHERE lead_id = $1 AND direction = 'outbound'
                ORDER BY sent_at DESC
                LIMIT $2
            """, lead_id, limit)

            return [dict(row) for row in rows]

    async def get_lead_response_data(self, lead_id: str) -> Dict[str, Any]:
        """Get response data for lead including inbound messages and sentiment analysis."""
        async with self.get_connection() as conn:
            try:
                # First try with sentiment_score column
                responses = await conn.fetch("""
                    SELECT
                        id, channel, content, sent_at as response_time,
                        sentiment_score, metadata
                    FROM communication_logs
                    WHERE lead_id = $1 AND direction = 'inbound'
                    ORDER BY sent_at DESC
                """, lead_id)
            except Exception as e:
                # Fallback query without sentiment_score if column doesn't exist
                if "sentiment_score" in str(e).lower() or "column" in str(e).lower():
                    logger.warning(f"sentiment_score column not found, using fallback query: {e}")
                    responses = await conn.fetch("""
                        SELECT
                            id, channel, content, sent_at as response_time,
                            NULL::float as sentiment_score, metadata
                        FROM communication_logs
                        WHERE lead_id = $1 AND direction = 'inbound'
                        ORDER BY sent_at DESC
                    """, lead_id)
                else:
                    # Re-raise if it's not a schema issue
                    logger.error(f"Failed to get lead response data: {e}")
                    raise e

            # Calculate response metrics
            response_list = [dict(row) for row in responses]

            # Check for negative sentiment (handle None sentiment scores)
            negative_sentiment = any(
                row.get('sentiment_score') is not None and row.get('sentiment_score', 0) < -0.3
                for row in response_list
            )

            # Get last response time
            last_response_time = response_list[0]['response_time'] if response_list else None

            # Calculate average sentiment, handling None values
            valid_sentiments = [r.get('sentiment_score', 0) for r in response_list if r.get('sentiment_score') is not None]
            avg_sentiment = sum(valid_sentiments) / len(valid_sentiments) if valid_sentiments else 0

            return {
                'responses': response_list,
                'negative_sentiment': negative_sentiment,
                'last_response_time': last_response_time,
                'total_responses': len(response_list),
                'avg_sentiment': avg_sentiment
            }

    async def get_lead_profile_data(self, lead_id: str) -> Dict[str, Any]:
        """Get comprehensive lead profile data."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT
                    id, first_name, last_name, email, phone, company,
                    source, status, score, temperature,
                    city, state, country, timezone,
                    job_title, seniority, company_industry, company_size,
                    preferences, enrichment_data, tags,
                    created_at, last_interaction_at
                FROM leads
                WHERE id = $1
            """, lead_id)

            if not row:
                return {
                    'name': 'Unknown Lead',
                    'contacts': [],
                    'preferences': {},
                    'demographics': {}
                }

            lead_dict = dict(row)

            # Format for Service 6 compatibility
            return {
                'name': f"{lead_dict.get('first_name', '')} {lead_dict.get('last_name', '')}".strip(),
                'email': lead_dict.get('email'),
                'phone': lead_dict.get('phone'),
                'company': lead_dict.get('company'),
                'contacts': [
                    {'type': 'email', 'value': lead_dict.get('email')},
                    {'type': 'phone', 'value': lead_dict.get('phone')} if lead_dict.get('phone') else None
                ],
                'preferences': lead_dict.get('preferences', {}),
                'demographics': {
                    'job_title': lead_dict.get('job_title'),
                    'seniority': lead_dict.get('seniority'),
                    'company_industry': lead_dict.get('company_industry'),
                    'company_size': lead_dict.get('company_size'),
                    'city': lead_dict.get('city'),
                    'state': lead_dict.get('state'),
                    'country': lead_dict.get('country'),
                    'timezone': lead_dict.get('timezone')
                },
                'source': lead_dict.get('source'),
                'status': lead_dict.get('status'),
                'temperature': lead_dict.get('temperature'),
                'score': lead_dict.get('score'),
                'tags': lead_dict.get('tags', []),
                'created_at': lead_dict.get('created_at'),
                'last_interaction_at': lead_dict.get('last_interaction_at')
            }

    async def get_lead_activity_data(self, lead_id: str) -> Dict[str, Any]:
        """Get lead activity and behavioral data."""
        async with self.get_connection() as conn:
            # Get lead behavioral metrics
            lead_row = await conn.fetchrow("""
                SELECT
                    website_visits, email_opens, email_clicks,
                    form_submissions, call_attempts, social_engagement
                FROM leads
                WHERE id = $1
            """, lead_id)

            if not lead_row:
                return {
                    "property_searches": [],
                    "email_interactions": [],
                    "website_visits": [],
                    "pricing_tool_uses": [],
                    "agent_inquiries": [],
                }

            lead_metrics = dict(lead_row)

            # Get recent communications for interaction patterns
            recent_comms = await conn.fetch("""
                SELECT channel, direction, sent_at, status
                FROM communication_logs
                WHERE lead_id = $1 AND sent_at >= NOW() - INTERVAL '30 days'
                ORDER BY sent_at DESC
                LIMIT 100
            """, lead_id)

            # Get property searches
            property_searches = await conn.fetch("""
                SELECT search_query, results_count, created_at
                FROM property_searches
                WHERE lead_id = $1
                ORDER BY created_at DESC
                LIMIT 50
            """, lead_id)

            # Get pricing tool uses
            pricing_tool_uses = await conn.fetch("""
                SELECT property_details, valuation_result, created_at
                FROM pricing_tool_uses
                WHERE lead_id = $1
                ORDER BY created_at DESC
                LIMIT 50
            """, lead_id)

            # Get agent inquiries
            agent_inquiries = await conn.fetch("""
                SELECT agent_id, inquiry_text, status, created_at
                FROM agent_inquiries
                WHERE lead_id = $1
                ORDER BY created_at DESC
                LIMIT 50
            """, lead_id)

            # Process communications by type
            email_interactions = []
            sms_responses = []
            call_history = []

            for comm in recent_comms:
                comm_dict = dict(comm)
                if comm_dict['channel'] == 'email':
                    email_interactions.append({
                        'type': comm_dict['direction'],
                        'timestamp': comm_dict['sent_at'],
                        'status': comm_dict['status']
                    })
                elif comm_dict['channel'] == 'sms' and comm_dict['direction'] == 'inbound':
                    sms_responses.append({
                        'timestamp': comm_dict['sent_at'],
                        'status': comm_dict['status']
                    })
                elif comm_dict['channel'] == 'phone':
                    call_history.append({
                        'type': comm_dict['direction'],
                        'timestamp': comm_dict['sent_at'],
                        'status': comm_dict['status']
                    })

            return {
                "property_searches": [dict(r) for r in property_searches],
                "email_interactions": email_interactions,
                "sms_responses": sms_responses,
                "call_history": call_history,
                "website_visits": [{'count': lead_metrics.get('website_visits', 0)}],
                "pricing_tool_uses": [dict(r) for r in pricing_tool_uses],
                "agent_inquiries": [dict(r) for r in agent_inquiries],
                "behavioral_metrics": {
                    "website_visits": lead_metrics.get('website_visits', 0),
                    "email_opens": lead_metrics.get('email_opens', 0),
                    "email_clicks": lead_metrics.get('email_clicks', 0),
                    "form_submissions": lead_metrics.get('form_submissions', 0),
                    "call_attempts": lead_metrics.get('call_attempts', 0),
                    "social_engagement": lead_metrics.get('social_engagement', 0)
                }
            }

    async def get_lead_journey_state(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """Get lead journey state for omnichannel context."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow("SELECT * FROM lead_journey_state WHERE lead_id = $1", lead_id)
            return dict(row) if row else None

    async def update_lead_journey_state(self, lead_id: str, state_data: Dict[str, Any]) -> None:
        """Update or create lead journey state."""
        async with self.transaction() as conn:
            await conn.execute("""
                INSERT INTO lead_journey_state (
                    lead_id, current_stage, last_channel, last_interaction_summary, 
                    pending_actions, context_data, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                ON CONFLICT (lead_id) DO UPDATE SET
                    current_stage = EXCLUDED.current_stage,
                    last_channel = EXCLUDED.last_channel,
                    last_interaction_summary = EXCLUDED.last_interaction_summary,
                    pending_actions = EXCLUDED.pending_actions,
                    context_data = lead_journey_state.context_data || EXCLUDED.context_data,
                    updated_at = NOW()
            """,
                lead_id,
                state_data.get("current_stage", "initial"),
                state_data.get("last_channel"),
                state_data.get("last_interaction_summary"),
                json.dumps(state_data.get("pending_actions", [])),
                json.dumps(state_data.get("context_data", {}))
            )

    async def get_available_agents(self, limit: int = 50, include_unavailable: bool = False) -> List[Dict[str, Any]]:
        """Get available agents for lead routing."""
        async with self.get_connection() as conn:
            where_clause = "WHERE is_active = true"
            if not include_unavailable:
                where_clause += " AND is_available = true AND current_load < capacity"

            rows = await conn.fetch(f"""
                SELECT
                    id, first_name, last_name, email, role,
                    specializations, territory, capacity, current_load,
                    avg_response_time_minutes, conversion_rate,
                    total_leads_handled, customer_satisfaction,
                    working_hours, timezone, is_available
                FROM agents
                {where_clause}
                ORDER BY
                    (CASE WHEN is_available THEN 0 ELSE 1 END),
                    (current_load::float / capacity::float),
                    conversion_rate DESC
                LIMIT $1
            """, limit)

            return [dict(row) for row in rows]

    async def get_high_intent_leads(self, min_score: int = 50, limit: int = 100) -> List[str]:
        """Get leads with high intent/behavioral scores."""
        async with self.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT id
                FROM leads
                WHERE score >= $1
                  AND status IN ('new', 'contacted', 'qualified', 'nurturing', 'hot')
                  AND deleted_at IS NULL
                ORDER BY score DESC, last_interaction_at ASC
                LIMIT $2
            """, min_score, limit)

            return [str(row['id']) for row in rows]

    # ============================================================================
    # Market Intelligence Operations
    # ============================================================================

    async def get_market_data(self, market_area: str, analysis_period: str = "30_days") -> Optional[Dict[str, Any]]:
        """Get market data for a specific area and period."""
        async with self.get_connection() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM market_data 
                WHERE market_area = $1 AND analysis_period = $2
            """, market_area, analysis_period)
            
            if row:
                return dict(row)
            return None

    async def get_competitor_profiles(self, market_areas: List[str]) -> List[Dict[str, Any]]:
        """Get competitor profiles active in specific market areas."""
        async with self.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM competitor_profiles 
                WHERE market_areas && $1
            """, market_areas)
            
            return [dict(row) for row in rows]

    async def get_personalization_lead_data(self, lead_id: str) -> Dict[str, Any]:
        """Get lead data for content personalization."""
        async with self.get_connection() as conn:
            # Get comprehensive lead data
            lead_row = await conn.fetchrow("""
                SELECT
                    l.*,
                    li.behavioral_data, li.enrichment_data as intelligence_data,
                    li.behavior_score, li.intent_score, li.engagement_score
                FROM leads l
                LEFT JOIN lead_intelligence li ON l.id = li.lead_id
                WHERE l.id = $1
                ORDER BY li.enriched_at DESC
                LIMIT 1
            """, lead_id)

            if not lead_row:
                return {}

            lead_dict = dict(lead_row)

            # Get recent communication history for context
            recent_comms = await conn.fetch("""
                SELECT channel, direction, content, sent_at
                FROM communication_logs
                WHERE lead_id = $1
                ORDER BY sent_at DESC
                LIMIT 10
            """, lead_id)

            return {
                'lead_profile': {
                    'name': f"{lead_dict.get('first_name', '')} {lead_dict.get('last_name', '')}".strip(),
                    'email': lead_dict.get('email'),
                    'company': lead_dict.get('company'),
                    'job_title': lead_dict.get('job_title'),
                    'industry': lead_dict.get('company_industry'),
                    'location': f"{lead_dict.get('city', '')}, {lead_dict.get('state', '')}".strip(', '),
                    'preferences': lead_dict.get('preferences', {}),
                    'tags': lead_dict.get('tags', [])
                },
                'behavioral_data': lead_dict.get('behavioral_data', {}),
                'intelligence_data': lead_dict.get('intelligence_data', {}),
                'scores': {
                    'overall': lead_dict.get('score', 0),
                    'behavior': lead_dict.get('behavior_score', 0),
                    'intent': lead_dict.get('intent_score', 0),
                    'engagement': lead_dict.get('engagement_score', 0)
                },
                'recent_communications': [dict(comm) for comm in recent_comms],
                'source': lead_dict.get('source'),
                'status': lead_dict.get('status'),
                'temperature': lead_dict.get('temperature')
            }

    # ============================================================================
    # Lead Activity Tracking
    # ============================================================================

    async def log_property_search(self, lead_id: str, search_query: Dict[str, Any], results_count: int = 0) -> str:
        """Log a property search event."""
        async with self.transaction() as conn:
            search_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO property_searches (id, lead_id, search_query, results_count)
                VALUES ($1, $2, $3, $4)
            """, search_id, uuid.UUID(lead_id), json.dumps(search_query), results_count)
            return search_id

    async def log_pricing_tool_use(self, lead_id: str, property_details: Dict[str, Any], valuation_result: Optional[Dict[str, Any]] = None) -> str:
        """Log usage of the pricing tool."""
        async with self.transaction() as conn:
            usage_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO pricing_tool_uses (id, lead_id, property_details, valuation_result)
                VALUES ($1, $2, $3, $4)
            """, usage_id, uuid.UUID(lead_id), json.dumps(property_details), json.dumps(valuation_result) if valuation_result else None)
            return usage_id

    async def log_agent_inquiry(self, lead_id: str, agent_id: Optional[str], inquiry_text: str) -> str:
        """Log a direct agent inquiry."""
        async with self.transaction() as conn:
            inquiry_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO agent_inquiries (id, lead_id, agent_id, inquiry_text)
                VALUES ($1, $2, $3, $4)
            """, inquiry_id, uuid.UUID(lead_id), uuid.UUID(agent_id) if agent_id else None, inquiry_text)
            return inquiry_id

    # ============================================================================
    # Follow-up Task Management (Service 6 State Persistence)
    # ============================================================================

    async def save_follow_up_task(self, task_data: Dict[str, Any]) -> str:
        """
        Save a follow-up task to the database for persistence.
        Ensures state is not lost on service restart.
        """
        async with self.transaction() as conn:
            # Check if task already exists
            existing = await conn.fetchval("SELECT id FROM follow_up_tasks WHERE id = $1", task_data["task_id"])
            
            if existing:
                await self.update_follow_up_task(task_data["task_id"], task_data)
                return task_data["task_id"]

            await conn.execute("""
                INSERT INTO follow_up_tasks (
                    id, lead_id, contact_id, channel, message, scheduled_time,
                    status, priority, intent_level, metadata
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """,
                task_data["task_id"],
                uuid.UUID(task_data["lead_id"]) if isinstance(task_data["lead_id"], str) else task_data["lead_id"],
                task_data["contact_id"],
                task_data["channel"],
                task_data["message"],
                task_data["scheduled_time"],
                task_data.get("status", "pending"),
                task_data.get("priority", 1),
                task_data.get("intent_level"),
                json.dumps(task_data.get("metadata", {}))
            )
            
            logger.info(f"Persisted follow-up task {task_data['task_id']} for lead {task_data['lead_id']}")
            return task_data["task_id"]

    async def get_pending_follow_up_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get pending follow-up tasks that are ready for execution."""
        async with self.get_connection() as conn:
            rows = await conn.fetch("""
                SELECT * FROM follow_up_tasks
                WHERE status IN ('pending', 'scheduled')
                  AND scheduled_time <= NOW()
                ORDER BY priority DESC, scheduled_time ASC
                LIMIT $1
            """, limit)
            
            return [dict(row) for row in rows]

    async def update_follow_up_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update follow-up task status and result."""
        async with self.transaction() as conn:
            set_clauses = []
            values = []
            param_count = 1
            
            for field, value in updates.items():
                if field == "id": continue # Cannot update ID
                
                if field == "metadata" or field == "result":
                    set_clauses.append(f"{field} = ${param_count}")
                    values.append(json.dumps(value))
                elif field == "lead_id" and isinstance(value, str):
                    set_clauses.append(f"{field} = ${param_count}")
                    values.append(uuid.UUID(value))
                else:
                    set_clauses.append(f"{field} = ${param_count}")
                    values.append(value)
                param_count += 1
            
            if not set_clauses:
                return True
                
            values.append(task_id)
            query = f"UPDATE follow_up_tasks SET {', '.join(set_clauses)} WHERE id = ${param_count}"
            
            result = await conn.execute(query, *values)
            rows_affected = int(result.split()[-1])
            return rows_affected > 0

    # ============================================================================
    # Health Checks & Monitoring
    # ============================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check. Raises DatabaseConnectionError on critical failure."""
        try:
            start_time = datetime.utcnow()
            
            async with self.get_connection() as conn:
                # Test basic connectivity
                result = await conn.fetchval("SELECT 1")
                
                if result != 1:
                    raise DatabaseConnectionError("Database connectivity test failed")
                
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
                    "database_connected": True,
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
            # Re-raise to ensure calling layer knows about the failure
            raise e
    
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


async def log_property_search(lead_id: str, search_query: Dict[str, Any], results_count: int = 0) -> str:
    """Convenience function to log property search."""
    db = await get_database()
    return await db.log_property_search(lead_id, search_query, results_count)


async def log_pricing_tool_use(lead_id: str, property_details: Dict[str, Any], valuation_result: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function to log pricing tool use."""
    db = await get_database()
    return await db.log_pricing_tool_use(lead_id, property_details, valuation_result)


async def log_agent_inquiry(lead_id: str, agent_id: Optional[str], inquiry_text: str) -> str:
    """Convenience function to log agent inquiry."""
    db = await get_database()
    return await db.log_agent_inquiry(lead_id, agent_id, inquiry_text)


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
