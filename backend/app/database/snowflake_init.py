"""Snowflake DDL initialization — creates all required tables."""

from app.database.session import execute_query

CLAIMS_DDL = """
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
)
"""

CLAIM_WORKFLOW_DDL = """
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
)
"""

WORKFLOW_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS WORKFLOW_EVENTS (
    event_id VARCHAR(36) PRIMARY KEY,
    claim_id VARCHAR(36) NOT NULL,
    from_state VARCHAR(50),
    to_state VARCHAR(50) NOT NULL,
    actor VARCHAR(100) DEFAULT 'SYSTEM',
    timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    metadata VARIANT DEFAULT PARSE_JSON('{}')
)
"""

AUDIT_LOGS_DDL = """
CREATE TABLE IF NOT EXISTS AUDIT_LOGS (
    id VARCHAR(36) PRIMARY KEY,
    claim_id VARCHAR(36) NOT NULL,
    action VARCHAR(100) NOT NULL,
    performed_by VARCHAR(100) DEFAULT 'SYSTEM_COPILOT',
    details VARIANT DEFAULT PARSE_JSON('{}'),
    timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
)
"""


async def init_snowflake_tables() -> None:
    """Run CREATE TABLE IF NOT EXISTS for all application tables."""
    for ddl in [CLAIMS_DDL, CLAIM_WORKFLOW_DDL, WORKFLOW_EVENTS_DDL, AUDIT_LOGS_DDL]:
        await execute_query(ddl)
