import React, { useState } from 'react';
import { X, Play, Code2, Sparkles, FileText } from 'lucide-react';
import { Claim, ClaimCopilotEvaluation } from '../types/claim';
import { DecisionSummary } from './DecisionSummary';
import { WorkflowVisualizer } from './WorkflowVisualizer';

interface ClaimDetailModalProps {
  claim: Claim;
  onClose: () => void;
  onEvaluate: (claimId: string) => Promise<void>;
}

export const ClaimDetailModal: React.FC<ClaimDetailModalProps> = ({ claim, onClose, onEvaluate }) => {
  const [evaluating, setEvaluating] = useState(false);
  const [activeTab, setActiveTab] = useState<'decision' | 'json'>('decision');

  const evaluation = claim.ai_analysis_result && 'overall_recommendation' in claim.ai_analysis_result
    ? (claim.ai_analysis_result as unknown as ClaimCopilotEvaluation)
    : null;

  const handleRunEvaluation = async () => {
    setEvaluating(true);
    try {
      await onEvaluate(claim.id);
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '850px', maxHeight: '90vh', overflowY: 'auto', padding: '1.75rem', position: 'relative' }} onClick={e => e.stopPropagation()}>
        <button onClick={onClose} style={{ position: 'absolute', top: '1.25rem', right: '1.25rem', background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
          <X style={{ width: '22px', height: '22px' }} />
        </button>

        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.25rem' }}>
            <span className="text-mono" style={{ color: 'var(--primary)', fontWeight: '600', fontSize: '0.85rem' }}>{claim.claim_number}</span>
            <span className="badge badge-pending">{claim.claim_type}</span>
          </div>
          <h2 style={{ fontSize: '1.5rem' }}>{claim.claimant_name}</h2>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Policy Number: <strong className="text-mono">{claim.policy_number}</strong></span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', background: 'rgba(0,0,0,0.25)', padding: '1rem', borderRadius: '12px', marginBottom: '1.5rem' }}>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'block' }}>Claimed Amount</span>
            <strong className="text-mono" style={{ fontSize: '1.3rem', color: '#fff' }}>${claim.claimed_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'block' }}>Copilot Status</span>
            <strong style={{ fontSize: '1.1rem', color: 'var(--primary)' }}>{claim.copilot_recommendation}</strong>
          </div>
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <h4 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <FileText style={{ width: '16px', height: '16px' }} /> Incident Narrative Description
          </h4>
          <p style={{ background: 'rgba(255,255,255,0.03)', padding: '0.85rem', borderRadius: '8px', fontSize: '0.9rem', lineHeight: '1.6', border: '1px solid var(--border-color)' }}>
            {claim.incident_description}
          </p>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.75rem' }}>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button className={`tab-btn ${activeTab === 'decision' ? 'active' : ''}`} onClick={() => setActiveTab('decision')}>
              <Sparkles style={{ width: '14px', height: '14px', display: 'inline', marginRight: '4px' }} /> Copilot Evaluation
            </button>
            <button className={`tab-btn ${activeTab === 'json' ? 'active' : ''}`} onClick={() => setActiveTab('json')}>
              <Code2 style={{ width: '14px', height: '14px', display: 'inline', marginRight: '4px' }} /> Raw Skills Payload
            </button>
          </div>

          <button onClick={handleRunEvaluation} disabled={evaluating} className="btn-primary" style={{ fontSize: '0.85rem' }}>
            <Play style={{ width: '14px', height: '14px' }} /> {evaluating ? 'Running Copilot Skills...' : 'Run Copilot Triage Pipeline'}
          </button>
        </div>

        {activeTab === 'decision' ? (
          <div>
            {evaluation && <DecisionSummary evaluation={evaluation} />}
            <WorkflowVisualizer steps={evaluation ? evaluation.workflow_steps : []} evaluating={evaluating} />
          </div>
        ) : (
          <pre className="text-mono" style={{ background: '#0b0f19', padding: '1rem', borderRadius: '10px', fontSize: '0.8rem', overflowX: 'auto', border: '1px solid var(--border-color)', color: '#38bdf8' }}>
            {JSON.stringify(claim, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
};
