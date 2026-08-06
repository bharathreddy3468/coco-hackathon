import React from 'react';
import { CheckCircle, FileSearch, ShieldCheck, AlertTriangle, Sparkles, Lock, MessageSquare } from 'lucide-react';
import { WorkflowStepResult, WorkflowTransition } from '../types/claim';

interface WorkflowVisualizerProps {
  steps?: WorkflowStepResult[];
  evaluating?: boolean;
  claimHistory?: WorkflowTransition[];
  currentStatus?: string;
}

export const WorkflowVisualizer: React.FC<WorkflowVisualizerProps> = ({
  claimHistory = [],
  currentStatus = 'SUBMITTED'
}) => {
  const workflowPipeline = [
    { state: 'SUBMITTED', label: 'Claim Intake', icon: FileSearch, desc: 'Instant Async Queue' },
    { state: 'DOCUMENT_INTAKE', label: 'Doc Intake Skill', icon: FileSearch, desc: 'Attachment & Entity Extraction' },
    { state: 'PRIVACY_GUARD', label: 'Privacy Guard Skill', icon: Lock, desc: 'PII Masking & Redaction' },
    { state: 'FRAUD_DETECTION', label: 'Fraud Risk Skill', icon: AlertTriangle, desc: 'Anomaly Risk Scoring' },
    { state: 'CLAIM_ANALYSIS', label: 'Claim Analysis Skill', icon: ShieldCheck, desc: 'Coverage & Policy Limits' },
    { state: 'SEMANTIC_BRIDGE', label: 'Semantic Bridge Skill', icon: Sparkles, desc: 'Plain-Language Translation' },
    { state: 'CUSTOMER_COMMUNICATION', label: 'Customer Comm Skill', icon: MessageSquare, desc: 'Multi-channel Dispatch' },
  ];

  const historyStates = new Set((claimHistory || []).map(h => h.to_state));

  const isStateDone = (state: string) => {
    if (historyStates.has(state)) return true;
    if (currentStatus === 'COMPLETED') return true;
    return false;
  };

  const isStateCurrent = (state: string) => currentStatus === state;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
        <h4 style={{ fontSize: '0.95rem', color: 'var(--text-muted)' }}>Asynchronous State-Driven Workflow Stepper</h4>
        <span className="badge badge-pending">Current State: {currentStatus}</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.5rem' }}>
        {workflowPipeline.map((step, idx) => {
          const Icon = step.icon;
          const done = isStateDone(step.state);
          const active = isStateCurrent(step.state);

          return (
            <div
              key={idx}
              className="glass-panel"
              style={{
                padding: '0.75rem 0.5rem',
                textAlign: 'center',
                background: active ? 'rgba(99,102,241,0.2)' : (done ? 'rgba(16,185,129,0.08)' : 'rgba(0,0,0,0.2)'),
                border: `1px solid ${active ? 'var(--primary)' : (done ? 'rgba(16,185,129,0.3)' : 'var(--border-color)')}`,
                borderRadius: '10px',
              }}
            >
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', margin: '0 auto 0.35rem auto', background: active ? 'var(--primary)' : (done ? '#10b981' : 'rgba(255,255,255,0.08)'), color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {done ? <CheckCircle style={{ width: '16px', height: '16px' }} /> : <Icon style={{ width: '14px', height: '14px' }} />}
              </div>
              <div style={{ fontSize: '0.75rem', fontWeight: '600', color: active ? 'var(--primary)' : (done ? '#34d399' : 'var(--text-muted)') }}>{step.label}</div>
              <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginTop: '0.2rem' }}>{step.desc}</div>
            </div>
          );
        })}
      </div>

      {claimHistory && claimHistory.length > 0 && (
        <div style={{ marginTop: '0.5rem' }}>
          <h5 style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '0.35rem' }}>Workflow State Audit Log History:</h5>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.75rem', background: '#090d16', padding: '0.6rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
            {claimHistory.map((h, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span>Transition: <strong style={{ color: '#a5b4fc' }}>{h.from_state || 'INTAKE'}</strong> &rarr; <strong style={{ color: '#34d399' }}>{h.to_state}</strong></span>
                <span className="text-mono" style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>{h.timestamp.split('T')[1]?.slice(0, 8) || ''}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
