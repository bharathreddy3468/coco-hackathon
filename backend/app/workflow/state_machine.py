from enum import Enum

class ClaimState(str, Enum):
    SUBMITTED = "SUBMITTED"
    DOCUMENT_INTAKE = "DOCUMENT_INTAKE"
    PRIVACY_GUARD = "PRIVACY_GUARD"
    FRAUD_DETECTION = "FRAUD_DETECTION"
    FRAUD_REVIEW = "FRAUD_REVIEW"  # Paused for Human Fraud Investigator Review
    CLAIM_ANALYSIS = "CLAIM_ANALYSIS"
    ADJUSTER_REVIEW = "ADJUSTER_REVIEW"  # Paused for Human Adjuster Review
    SEMANTIC_BRIDGE = "SEMANTIC_BRIDGE"
    CUSTOMER_COMMUNICATION = "CUSTOMER_COMMUNICATION"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"

# Human review states where automatic workflow engine pauses
HUMAN_REVIEW_STATES = {ClaimState.FRAUD_REVIEW, ClaimState.ADJUSTER_REVIEW}

# Terminal states where workflow ends
TERMINAL_STATES = {ClaimState.COMPLETED, ClaimState.REJECTED}
