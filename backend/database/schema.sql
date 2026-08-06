-- Snowflake DDL for Insurance Claims Decision Copilot
-- Tables: CLAIMS, CLAIM_WORKFLOW, WORKFLOW_EVENTS

CREATE TABLE IF NOT EXISTS CLAIMS (
    id VARCHAR(36) PRIMARY KEY,
    claim_number VARCHAR(50) NOT NULL,
    policy_number VARCHAR(50) NOT NULL,
    claimant_name VARCHAR(100) NOT NULL,
    claim_type VARCHAR(50) NOT NULL,
    claimed_amount FLOAT NOT NULL,
    approved_amount FLOAT DEFAULT 0.0,
    status VARCHAR(50) DEFAULT 'SUBMITTED',
    risk_score FLOAT DEFAULT 0.0,
    copilot_recommendation VARCHAR(50) DEFAULT 'PENDING',
    incident_description TEXT,
    redacted_description TEXT DEFAULT '',
    privacy_flags VARIANT DEFAULT PARSE_JSON('[]'),
    documents VARIANT DEFAULT PARSE_JSON('[]'),
    adjuster_notes TEXT DEFAULT '',
    customer_explanation TEXT DEFAULT '',
    customer_communication VARIANT DEFAULT PARSE_JSON('{}'),
    workflow_history VARIANT DEFAULT PARSE_JSON('[]'),
    ai_analysis_result VARIANT DEFAULT PARSE_JSON('{}'),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS CLAIM_WORKFLOW (
    claim_id VARCHAR(36) PRIMARY KEY,
    current_state VARCHAR(50) NOT NULL,
    previous_state VARCHAR(50),
    current_skill VARCHAR(100),
    workflow_status VARCHAR(20) DEFAULT 'ACTIVE',
    retry_count INTEGER DEFAULT 0,
    started_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    completed_at TIMESTAMP_NTZ,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS WORKFLOW_EVENTS (
    event_id VARCHAR(36) PRIMARY KEY,
    claim_id VARCHAR(36) NOT NULL,
    event_type VARCHAR(50) DEFAULT 'STATE_TRANSITION',
    from_state VARCHAR(50),
    to_state VARCHAR(50),
    actor VARCHAR(100) DEFAULT 'SYSTEM',
    timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    metadata VARIANT DEFAULT PARSE_JSON('{}')
);
