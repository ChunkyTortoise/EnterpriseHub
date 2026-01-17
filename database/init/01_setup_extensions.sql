-- Service 6 Database Initialization - Step 1: Extensions and Types
-- PostgreSQL 15+ compatible
-- Executed first to set up required extensions and custom types

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For JSONB indexing
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- For query performance monitoring

-- Create custom ENUM types for Service 6
CREATE TYPE lead_status AS ENUM (
    'new', 
    'contacted', 
    'qualified', 
    'disqualified', 
    'converted', 
    'lost', 
    'dormant',
    'reactivated'
);

CREATE TYPE lead_temperature AS ENUM (
    'hot',      -- Ready to buy/highly engaged
    'warm',     -- Interested, engaging
    'cold',     -- Low engagement
    'frozen',   -- No engagement for extended period
    'unknown'   -- Initial state
);

CREATE TYPE communication_channel AS ENUM (
    'email', 
    'sms', 
    'call', 
    'voicemail', 
    'linkedin',
    'facebook',
    'instagram', 
    'whatsapp',
    'webhook',
    'api',
    'other'
);

CREATE TYPE communication_direction AS ENUM (
    'inbound',  -- From lead to us
    'outbound'  -- From us to lead
);

CREATE TYPE communication_status AS ENUM (
    'queued',    -- In queue to be sent
    'sent',      -- Successfully sent
    'delivered', -- Delivered to recipient
    'opened',    -- Recipient opened/viewed
    'clicked',   -- Recipient clicked link
    'replied',   -- Recipient replied
    'failed',    -- Failed to send
    'bounced',   -- Email bounced
    'unsubscribed' -- Recipient unsubscribed
);

CREATE TYPE nurture_status AS ENUM (
    'active',    -- Currently running
    'paused',    -- Temporarily paused
    'completed', -- Finished successfully
    'cancelled', -- Manually cancelled
    'failed'     -- Failed due to error
);

CREATE TYPE workflow_status AS ENUM (
    'queued',    -- Waiting to start
    'running',   -- Currently executing
    'completed', -- Finished successfully
    'failed',    -- Failed with error
    'cancelled', -- Manually cancelled
    'timeout'    -- Timed out
);

CREATE TYPE data_quality AS ENUM (
    'basic',     -- Minimum required fields
    'enriched',  -- Apollo/external data added
    'validated', -- Data verified/confirmed
    'premium'    -- Fully enriched with multiple sources
);

CREATE TYPE agent_role AS ENUM (
    'junior',
    'senior', 
    'lead',
    'manager',
    'admin'
);

CREATE TYPE priority_level AS ENUM (
    'low',
    'medium', 
    'high',
    'urgent',
    'critical'
);

-- Create domain types for common fields
CREATE DOMAIN email_address AS VARCHAR(255) 
    CHECK (VALUE ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

CREATE DOMAIN phone_number AS VARCHAR(20)
    CHECK (VALUE IS NULL OR VALUE ~ '^[0-9+\-() ]{10,20}$');

CREATE DOMAIN percentage_score AS INTEGER
    CHECK (VALUE >= 0 AND VALUE <= 100);

-- Log successful setup
INSERT INTO public.setup_log (step, status, details, completed_at) 
VALUES (
    '01_setup_extensions', 
    'SUCCESS', 
    'Extensions and custom types created successfully',
    NOW()
) ON CONFLICT DO NOTHING;

-- Create the setup_log table if it doesn't exist (will be created properly in next script)
CREATE TABLE IF NOT EXISTS setup_log (
    step VARCHAR(50) PRIMARY KEY,
    status VARCHAR(20) NOT NULL,
    details TEXT,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add comment for tracking
COMMENT ON EXTENSION "uuid-ossp" IS 'Service 6: UUID generation functions';
COMMENT ON EXTENSION "pgcrypto" IS 'Service 6: Cryptographic functions for security';
COMMENT ON EXTENSION "btree_gin" IS 'Service 6: GIN indexing for JSONB performance';
COMMENT ON EXTENSION "pg_stat_statements" IS 'Service 6: Query performance monitoring';

-- Schema information
SELECT 
    'Extensions and types setup completed' as status,
    NOW() as timestamp,
    version() as postgresql_version;
