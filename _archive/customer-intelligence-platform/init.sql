-- Customer Intelligence Platform - Database Initialization
-- PostgreSQL schema for production deployment

-- Create database if not exists (handled by Docker)
-- CREATE DATABASE IF NOT EXISTS customer_intelligence;

-- Use the database
-- \c customer_intelligence;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- Core Tables
-- =============================================================================

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(255),
    industry VARCHAR(100),
    department VARCHAR(100) DEFAULT 'General',
    status VARCHAR(50) DEFAULT 'new',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_interaction_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB,
    tags TEXT[]
);

-- Customer scores table
CREATE TABLE IF NOT EXISTS customer_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    score_type VARCHAR(50) NOT NULL,
    score DECIMAL(5,4) NOT NULL CHECK (score >= 0 AND score <= 1),
    confidence DECIMAL(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    model_version VARCHAR(50) NOT NULL,
    features JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Conversation messages table
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Knowledge documents table
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- =============================================================================
-- Indexes for Performance
-- =============================================================================

-- Customer indexes
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_department ON customers(department);
CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);
CREATE INDEX IF NOT EXISTS idx_customers_created_at ON customers(created_at);
CREATE INDEX IF NOT EXISTS idx_customers_last_interaction ON customers(last_interaction_at);

-- Customer scores indexes
CREATE INDEX IF NOT EXISTS idx_customer_scores_customer_id ON customer_scores(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_scores_type ON customer_scores(score_type);
CREATE INDEX IF NOT EXISTS idx_customer_scores_created_at ON customer_scores(created_at);
CREATE INDEX IF NOT EXISTS idx_customer_scores_composite ON customer_scores(customer_id, score_type, created_at DESC);

-- Conversation indexes
CREATE INDEX IF NOT EXISTS idx_conversations_customer_id ON conversations(customer_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);

-- Conversation messages indexes
CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation_id ON conversation_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_customer_id ON conversation_messages(customer_id);
CREATE INDEX IF NOT EXISTS idx_conversation_messages_timestamp ON conversation_messages(timestamp);

-- Knowledge documents indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_type ON knowledge_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_department ON knowledge_documents(department);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_created_at ON knowledge_documents(created_at);

-- GIN indexes for JSONB and arrays
CREATE INDEX IF NOT EXISTS idx_customers_metadata_gin ON customers USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_customers_tags_gin ON customers USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_customer_scores_features_gin ON customer_scores USING GIN(features);
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_tags_gin ON knowledge_documents USING GIN(tags);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_content_fts ON knowledge_documents USING GIN(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_title_fts ON knowledge_documents USING GIN(to_tsvector('english', title));

-- =============================================================================
-- Triggers and Functions
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_customers_updated_at 
    BEFORE UPDATE ON customers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at 
    BEFORE UPDATE ON conversations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_documents_updated_at 
    BEFORE UPDATE ON knowledge_documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Sample Data (Optional)
-- =============================================================================

-- Insert sample customers
INSERT INTO customers (name, email, company, industry, department, status) VALUES 
    ('Acme Corporation', 'contact@acme.com', 'Acme Corp', 'Technology', 'Sales', 'qualified'),
    ('TechStart Inc', 'hello@techstart.com', 'TechStart Inc', 'Software', 'Marketing', 'hot'),
    ('Global Solutions', 'info@globalsol.com', 'Global Solutions Ltd', 'Consulting', 'Customer Success', 'new')
ON CONFLICT DO NOTHING;

-- Insert sample knowledge documents
INSERT INTO knowledge_documents (title, content, document_type, department, tags) VALUES 
    (
        'Platform Overview',
        'Customer Intelligence Platform provides AI-powered insights for business growth. It includes lead scoring, conversation intelligence, and predictive analytics.',
        'product_info',
        'General',
        ARRAY['platform', 'overview', 'ai', 'intelligence']
    ),
    (
        'Lead Scoring Guide',
        'Lead scoring uses machine learning to predict customer conversion probability. Features include engagement score, company size, industry type, and behavioral patterns.',
        'feature_guide',
        'Sales',
        ARRAY['lead', 'scoring', 'machine learning', 'conversion']
    ),
    (
        'Conversation Intelligence',
        'The conversation intelligence feature analyzes customer interactions to provide insights and recommendations. It supports multiple channels including chat, email, and phone.',
        'feature_guide',
        'Customer Success',
        ARRAY['conversation', 'intelligence', 'analysis', 'insights']
    )
ON CONFLICT DO NOTHING;

-- =============================================================================
-- Views for Analytics
-- =============================================================================

-- Customer analytics view
CREATE OR REPLACE VIEW customer_analytics AS
SELECT 
    department,
    status,
    COUNT(*) as customer_count,
    AVG(
        CASE 
            WHEN cs.score IS NOT NULL THEN cs.score 
            ELSE 0.5 
        END
    ) as avg_score,
    COUNT(cs.id) as scored_customers,
    MAX(c.created_at) as latest_customer,
    COUNT(CASE WHEN c.last_interaction_at > CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END) as recent_interactions
FROM customers c
LEFT JOIN (
    SELECT DISTINCT ON (customer_id) 
        customer_id, score, created_at
    FROM customer_scores 
    ORDER BY customer_id, created_at DESC
) cs ON c.id = cs.customer_id
GROUP BY department, status;

-- Scoring performance view
CREATE OR REPLACE VIEW scoring_performance AS
SELECT 
    score_type,
    model_version,
    COUNT(*) as prediction_count,
    AVG(score) as avg_score,
    AVG(confidence) as avg_confidence,
    MIN(created_at) as first_prediction,
    MAX(created_at) as latest_prediction
FROM customer_scores 
GROUP BY score_type, model_version
ORDER BY latest_prediction DESC;

-- =============================================================================
-- Permissions and Security
-- =============================================================================

-- Create application user (if needed)
-- CREATE USER customer_intelligence_app WITH PASSWORD 'secure_password_here';

-- Grant permissions
-- GRANT CONNECT ON DATABASE customer_intelligence TO customer_intelligence_app;
-- GRANT USAGE ON SCHEMA public TO customer_intelligence_app;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO customer_intelligence_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO customer_intelligence_app;

-- Row-level security (example for multi-tenant)
-- ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY customer_policy ON customers FOR ALL USING (department = current_setting('app.current_department'));

-- =============================================================================
-- Completion Message
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Customer Intelligence Platform database initialized successfully!';
    RAISE NOTICE 'Created tables: customers, customer_scores, conversations, conversation_messages, knowledge_documents';
    RAISE NOTICE 'Created indexes for optimal performance';
    RAISE NOTICE 'Created triggers for automatic timestamp updates';
    RAISE NOTICE 'Created analytical views for reporting';
    RAISE NOTICE 'Inserted sample data for demonstration';
END $$;