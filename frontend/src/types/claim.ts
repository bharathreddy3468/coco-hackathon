export type ClaimState =
  | 'SUBMITTED'
  | 'DOCUMENT_INTAKE'
  | 'PRIVACY_GUARD'
  | 'FRAUD_DETECTION'
  | 'FRAUD_REVIEW'
  | 'CLAIM_ANALYSIS'
  | 'ADJUSTER_REVIEW'
  | 'SEMANTIC_BRIDGE'
  | 'CUSTOMER_COMMUNICATION'
  | 'COMPLETED'
  | 'REJECTED';

export interface ClaimDocument {
  name: string;
  size: string;
  type: string;
}

export interface WorkflowTransition {
  from_state: string | null;
  to_state: string;
  timestamp: string;
}

export interface WorkflowStepResult {
  step_name: string;
  status: 'COMPLETED' | 'FAILED' | 'SKIPPED';
  latency_ms: number;
  summary: string;
  details: Record<string, unknown>;
}

export interface ClaimCopilotEvaluation {
  claim_id: string;
  overall_recommendation: 'AUTO_APPROVE' | 'MANUAL_REVIEW' | 'REJECT';
  confidence_score: number;
  fraud_risk_score: number;
  policy_coverage_valid: boolean;
  summary_reasoning: string[];
  suggested_payout: number;
  workflow_steps: WorkflowStepResult[];
}

export interface Claim {
  id: string;
  claim_number: string;
  policy_number: string;
  claimant_name: string;
  claim_type: string;
  claimed_amount: number;
  approved_amount: number;
  status: ClaimState;
  risk_score: number;
  copilot_recommendation: string;
  incident_description: string;
  redacted_description?: string;
  privacy_flags?: string[];
  documents?: ClaimDocument[];
  adjuster_notes?: string;
  customer_explanation?: string;
  customer_communication?: Record<string, unknown>;
  workflow_history?: WorkflowTransition[];
  ai_analysis_result?: ClaimCopilotEvaluation | Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ClaimUpdate {
  status?: string;
  approved_amount?: number;
  copilot_recommendation?: string;
  adjuster_notes?: string;
}

export interface FraudReviewAction {
  fraud_confirmed: boolean;
  investigator_notes: string;
}

export interface SkillMeta {
  id: string;
  name: string;
  description: string;
  version: string;
  category: string;
}

export interface SkillExecutionResult {
  skill_id: string;
  success: boolean;
  execution_time_ms: number;
  confidence_score: number;
  output: Record<string, unknown>;
  reasoning: string[];
  error?: string;
}

export interface SystemHealth {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface SystemReadiness {
  status: string;
  database_connected: boolean;
  skills_loaded: number;
  timestamp: string;
}
