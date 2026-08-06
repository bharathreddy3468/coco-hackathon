from app.skills.base import BaseSkill
from app.skills.document_intake import DocumentIntakeSkill
from app.skills.privacy_guard import PrivacyGuardSkill
from app.skills.fraud_detector import FraudDetectorSkill
from app.skills.claim_analysis import ClaimAnalysisSkill
from app.skills.semantic_bridge import SemanticBridgeSkill
from app.skills.customer_comm import CustomerCommunicationSkill
from app.workflow.state_machine import ClaimState

skills_registry: dict[str, BaseSkill] = {
    "skill_document_intake": DocumentIntakeSkill(),
    "skill_privacy_guard": PrivacyGuardSkill(),
    "skill_fraud_detector": FraudDetectorSkill(),
    "skill_claim_analysis": ClaimAnalysisSkill(),
    "skill_semantic_bridge": SemanticBridgeSkill(),
    "skill_customer_comm": CustomerCommunicationSkill(),
}

# State to Skill mapping
STATE_SKILL_MAPPING = {
    ClaimState.DOCUMENT_INTAKE: skills_registry["skill_document_intake"],
    ClaimState.PRIVACY_GUARD: skills_registry["skill_privacy_guard"],
    ClaimState.FRAUD_DETECTION: skills_registry["skill_fraud_detector"],
    ClaimState.CLAIM_ANALYSIS: skills_registry["skill_claim_analysis"],
    ClaimState.SEMANTIC_BRIDGE: skills_registry["skill_semantic_bridge"],
    ClaimState.CUSTOMER_COMMUNICATION: skills_registry["skill_customer_comm"],
}

__all__ = [
    "BaseSkill",
    "DocumentIntakeSkill",
    "PrivacyGuardSkill",
    "FraudDetectorSkill",
    "ClaimAnalysisSkill",
    "SemanticBridgeSkill",
    "CustomerCommunicationSkill",
    "skills_registry",
    "STATE_SKILL_MAPPING",
]
