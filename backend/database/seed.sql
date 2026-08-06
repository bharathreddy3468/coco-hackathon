-- Seed data for Insurance Claims Decision Copilot

-- 1. Demo Claim 1: David Miller
INSERT INTO CLAIMS (
    id, claim_number, policy_number, claimant_name, claim_type,
    claimed_amount, approved_amount, status, risk_score, copilot_recommendation,
    incident_description, redacted_description, privacy_flags, documents,
    adjuster_notes, customer_explanation, customer_communication,
    workflow_history, ai_analysis_result, created_at, updated_at
)
SELECT
    'claim-demo-001', 'CLM-DM001001', 'POL-2026-1049', 'David Miller', 'Auto',
    1850.00, 0.00, 'SUBMITTED', 0.00, 'PENDING',
    'Low-speed rear-end fender bender while stopped at red light. Contact is 555-0192, SSN 000-12-3456.',
    '', PARSE_JSON('[]'), PARSE_JSON('[{"name": "police_report.pdf", "size": "1.2 MB", "type": "application/pdf"}]'),
    '', '', PARSE_JSON('{}'),
    PARSE_JSON('[{"from_state": null, "to_state": "SUBMITTED", "timestamp": "2026-08-06T10:00:00Z"}]'),
    PARSE_JSON('{}'), CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP();

INSERT INTO CLAIM_WORKFLOW (
    claim_id, current_state, previous_state, current_skill, workflow_status, retry_count, started_at, updated_at
)
VALUES (
    'claim-demo-001', 'SUBMITTED', NULL, NULL, 'ACTIVE', 0, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
);

INSERT INTO WORKFLOW_EVENTS (
    event_id, claim_id, event_type, from_state, to_state, actor, timestamp, metadata
)
SELECT
    'evt-demo-001', 'claim-demo-001', 'STATE_TRANSITION', NULL, 'SUBMITTED', 'CUSTOMER_PORTAL', CURRENT_TIMESTAMP(), PARSE_JSON('{"source": "seed"}');


-- 2. Demo Claim 2: Elena Rostova
INSERT INTO CLAIMS (
    id, claim_number, policy_number, claimant_name, claim_type,
    claimed_amount, approved_amount, status, risk_score, copilot_recommendation,
    incident_description, redacted_description, privacy_flags, documents,
    adjuster_notes, customer_explanation, customer_communication,
    workflow_history, ai_analysis_result, created_at, updated_at
)
SELECT
    'claim-demo-002', 'CLM-ER002002', 'POL-2026-8820', 'Elena Rostova', 'Property',
    14200.00, 0.00, 'SUBMITTED', 0.00, 'PENDING',
    'Water pipe burst unwitnessed during extreme freeze. Cash cleanup fee requested.',
    '', PARSE_JSON('[]'), PARSE_JSON('[{"name": "water_damage_photo.png", "size": "3.1 MB", "type": "image/png"}]'),
    '', '', PARSE_JSON('{}'),
    PARSE_JSON('[{"from_state": null, "to_state": "SUBMITTED", "timestamp": "2026-08-06T10:05:00Z"}]'),
    PARSE_JSON('{}'), CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP();

INSERT INTO CLAIM_WORKFLOW (
    claim_id, current_state, previous_state, current_skill, workflow_status, retry_count, started_at, updated_at
)
VALUES (
    'claim-demo-002', 'SUBMITTED', NULL, NULL, 'ACTIVE', 0, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
);

INSERT INTO WORKFLOW_EVENTS (
    event_id, claim_id, event_type, from_state, to_state, actor, timestamp, metadata
)
SELECT
    'evt-demo-002', 'claim-demo-002', 'STATE_TRANSITION', NULL, 'SUBMITTED', 'CUSTOMER_PORTAL', CURRENT_TIMESTAMP(), PARSE_JSON('{"source": "seed"}');


-- 3. Demo Claim 3: Marcus Vance
INSERT INTO CLAIMS (
    id, claim_number, policy_number, claimant_name, claim_type,
    claimed_amount, approved_amount, status, risk_score, copilot_recommendation,
    incident_description, redacted_description, privacy_flags, documents,
    adjuster_notes, customer_explanation, customer_communication,
    workflow_history, ai_analysis_result, created_at, updated_at
)
SELECT
    'claim-demo-003', 'CLM-MV003003', 'EXPIRED-POL-99', 'Marcus Vance', 'Auto',
    3200.00, 0.00, 'SUBMITTED', 0.00, 'PENDING',
    'Windshield cracked by flying gravel on interstate 80.',
    '', PARSE_JSON('[]'), PARSE_JSON('[{"name": "windshield_photo.jpg", "size": "1.8 MB", "type": "image/jpeg"}]'),
    '', '', PARSE_JSON('{}'),
    PARSE_JSON('[{"from_state": null, "to_state": "SUBMITTED", "timestamp": "2026-08-06T10:10:00Z"}]'),
    PARSE_JSON('{}'), CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP();

INSERT INTO CLAIM_WORKFLOW (
    claim_id, current_state, previous_state, current_skill, workflow_status, retry_count, started_at, updated_at
)
VALUES (
    'claim-demo-003', 'SUBMITTED', NULL, NULL, 'ACTIVE', 0, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP()
);

INSERT INTO WORKFLOW_EVENTS (
    event_id, claim_id, event_type, from_state, to_state, actor, timestamp, metadata
)
SELECT
    'evt-demo-003', 'claim-demo-003', 'STATE_TRANSITION', NULL, 'SUBMITTED', 'CUSTOMER_PORTAL', CURRENT_TIMESTAMP(), PARSE_JSON('{"source": "seed"}');
