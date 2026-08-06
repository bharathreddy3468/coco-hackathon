import { Claim, ClaimUpdate, FraudReviewAction, SkillMeta, SkillExecutionResult, SystemHealth, SystemReadiness, ClaimDocument } from '../types/claim';

const API_BASE = '/api/v1';

export const api = {
  async getHealth(): Promise<SystemHealth> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  },

  async getReadiness(): Promise<SystemReadiness> {
    const res = await fetch(`${API_BASE}/ready`);
    if (!res.ok) throw new Error('Readiness check failed');
    return res.json();
  },

  async getClaims(): Promise<Claim[]> {
    const res = await fetch(`${API_BASE}/claims`);
    if (!res.ok) throw new Error('Failed to fetch claims');
    return res.json();
  },

  async createClaim(data: {
    policy_number: string;
    claimant_name: string;
    claim_type: string;
    claimed_amount: number;
    incident_description: string;
    documents?: ClaimDocument[];
  }): Promise<Claim> {
    const res = await fetch(`${API_BASE}/claims`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create claim');
    return res.json();
  },

  async submitFraudReview(claimId: string, action: FraudReviewAction): Promise<Claim> {
    const res = await fetch(`${API_BASE}/claims/${claimId}/fraud-review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(action),
    });
    if (!res.ok) throw new Error('Failed to submit fraud review');
    return res.json();
  },

  async updateClaim(claimId: string, updateData: ClaimUpdate): Promise<Claim> {
    const res = await fetch(`${API_BASE}/claims/${claimId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updateData),
    });
    if (!res.ok) throw new Error('Failed to update claim');
    return res.json();
  },

  async getSkills(): Promise<SkillMeta[]> {
    const res = await fetch(`${API_BASE}/skills`);
    if (!res.ok) throw new Error('Failed to fetch skills');
    return res.json();
  },

  async executeSkill(skillId: string, inputData: Record<string, unknown>): Promise<SkillExecutionResult> {
    const res = await fetch(`${API_BASE}/skills/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ skill_id: skillId, input_data: inputData }),
    });
    if (!res.ok) throw new Error('Failed to execute skill');
    return res.json();
  },
};
