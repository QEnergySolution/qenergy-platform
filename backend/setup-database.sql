-- QEnergy Platform Database Setup
-- Run this script as a PostgreSQL superuser (postgres)

-- Create database (if not exists)
-- Note: This must be run as superuser
-- CREATE DATABASE qenergy_platform;

-- Connect to the database
-- \c qenergy_platform;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create report_uploads table (stores file uploads metadata)
CREATE TABLE IF NOT EXISTS report_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(1024) NOT NULL,
    mime_type VARCHAR(255),
    file_size_bytes BIGINT,
    sha256 VARCHAR(64) UNIQUE NOT NULL,
    status VARCHAR(32) NOT NULL,
    cw_label VARCHAR(8),
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    parsed_at TIMESTAMPTZ NULL,
    created_by VARCHAR(255) NOT NULL,
    updated_by VARCHAR(255) NOT NULL
);

-- Useful indexes
CREATE INDEX IF NOT EXISTS idx_report_uploads_sha256 ON report_uploads(sha256);
CREATE INDEX IF NOT EXISTS idx_report_uploads_uploaded_at ON report_uploads(uploaded_at DESC);

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_code VARCHAR(32) UNIQUE NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    portfolio_cluster VARCHAR(128),
    status INTEGER NOT NULL CHECK (status IN (0, 1)),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(255) NOT NULL
);

-- Create project_history table
CREATE TABLE IF NOT EXISTS project_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_code VARCHAR(32) NOT NULL REFERENCES projects(project_code) ON DELETE CASCADE,
    project_name VARCHAR(255),
    category VARCHAR(128),
    entry_type VARCHAR(50) NOT NULL CHECK (entry_type IN ('Report', 'Issue', 'Decision', 'Maintenance', 'Meeting minutes', 'Mid-update')),
    log_date DATE NOT NULL,
    cw_label VARCHAR(8),
    title VARCHAR(255),
    summary TEXT NOT NULL,
    next_actions TEXT,
    owner VARCHAR(255),
    source_text TEXT,
    source_upload_id UUID,
    attachment_url VARCHAR(1024),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(255) NOT NULL,
    UNIQUE(project_code, log_date, category)
);

-- Backfill/upgrade columns for existing installations
ALTER TABLE project_history ADD COLUMN IF NOT EXISTS project_name VARCHAR(255);
ALTER TABLE project_history ADD COLUMN IF NOT EXISTS source_text TEXT;
ALTER TABLE project_history ADD COLUMN IF NOT EXISTS source_upload_id UUID;
DO $$ BEGIN
    ALTER TABLE project_history
        ADD CONSTRAINT fk_project_history_source_upload
        FOREIGN KEY (source_upload_id) REFERENCES report_uploads(id) ON DELETE SET NULL;
EXCEPTION WHEN duplicate_object THEN
    -- constraint already exists
    NULL;
END $$;

-- Create weekly_report_analysis table
CREATE TABLE IF NOT EXISTS weekly_report_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_code VARCHAR(32) NOT NULL REFERENCES projects(project_code) ON DELETE CASCADE,
    category VARCHAR(128),
    cw_label VARCHAR(8) NOT NULL,
    language VARCHAR(2) NOT NULL DEFAULT 'EN',
    risk_lvl DECIMAL(5,2) CHECK (risk_lvl >= 0 AND risk_lvl <= 100),
    risk_desc VARCHAR(500),
    similarity_lvl DECIMAL(5,2) CHECK (similarity_lvl >= 0 AND similarity_lvl <= 100),
    similarity_desc VARCHAR(500),
    negative_words JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL,
    UNIQUE(project_code, cw_label, language, category)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_portfolio ON projects(portfolio_cluster);
CREATE INDEX IF NOT EXISTS idx_projects_created_at ON projects(created_at);
CREATE INDEX IF NOT EXISTS idx_projects_project_code ON projects(project_code);

CREATE INDEX IF NOT EXISTS idx_project_history_project_code ON project_history(project_code);
CREATE INDEX IF NOT EXISTS idx_project_history_log_date ON project_history(log_date);
CREATE INDEX IF NOT EXISTS idx_project_history_cw_label ON project_history(cw_label);
CREATE INDEX IF NOT EXISTS idx_project_history_category ON project_history(category);
CREATE INDEX IF NOT EXISTS idx_project_history_source_upload ON project_history(source_upload_id);

CREATE INDEX IF NOT EXISTS idx_analysis_project_cw ON weekly_report_analysis(project_code, cw_label);
CREATE INDEX IF NOT EXISTS idx_analysis_risk_lvl ON weekly_report_analysis(risk_lvl DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_similarity_lvl ON weekly_report_analysis(similarity_lvl DESC);

-- Insert sample data for testing
INSERT INTO projects (project_code, project_name, portfolio_cluster, status, created_by, updated_by) VALUES
    ('2ES00009', 'Boedo 1', 'Herrera', 1, 'admin@qenergy.eu', 'admin@qenergy.eu'),
    ('2ES00010', 'Boedo 2', 'Herrera', 1, 'admin@qenergy.eu', 'admin@qenergy.eu'),
    ('2DE00001', 'Illmersdorf', 'Illmersdorf', 1, 'admin@qenergy.eu', 'admin@qenergy.eu'),
    ('2DE00002', 'Garwitz', 'Lunaco', 0, 'admin@qenergy.eu', 'admin@qenergy.eu'),
    ('2DE00003', 'Matzlow', 'Lunaco', 1, 'admin@qenergy.eu', 'admin@qenergy.eu')
ON CONFLICT (project_code) DO NOTHING;

-- Create a function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_history_updated_at BEFORE UPDATE ON project_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO qenergy_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO qenergy_user;

-- Verify setup
SELECT 'Database setup completed successfully!' as status;
