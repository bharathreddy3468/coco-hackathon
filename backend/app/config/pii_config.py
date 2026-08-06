"""Configurable PII field definitions for the privacy masking guardrail.

This module is the single source of truth for which structured claim fields
are considered Personally Identifiable Information (PII).  The masking
service reads this list to decide what to redact before sending data to any
LLM (including Snowflake Cortex).

To add or remove PII fields, edit the ``PII_FIELDS`` list below — no other
code changes are required.
"""

# ---------------------------------------------------------------------------
# Configurable PII fields — add / remove as business policy evolves.
# Field names are matched **case-insensitively** by the masking service.
# ---------------------------------------------------------------------------
PII_FIELDS: list[str] = [
    "patient_name",
    "claimant_name",
    "phone",
    "email",
    "address",
    "aadhaar",
    "passport",
    "insurance_id",
    "policy_number",
    "claim_number",
]

# The placeholder value that replaces every detected PII field.
PII_REDACTED_VALUE: str = "[REDACTED]"
