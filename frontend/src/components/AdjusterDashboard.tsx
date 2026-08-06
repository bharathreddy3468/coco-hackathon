import React, { useState } from 'react';
import { XCircle, CheckCircle2, Play, Edit3, MessageSquare, ShieldAlert, AlertTriangle, Lock } from 'lucide-react';
import { Claim, FraudReviewAction } from '../types/claim';
import { WorkflowVisualizer } from './WorkflowVisualizer';

interface AdjusterDashboardProps {
  claims: Claim[];
  onSelectClaim: (claim: Claim) => void;
  onAdvanceWorkflow: (claimId: string) => Promise<void>;
  onSubmitFraudReview: (claimId: string, action: FraudReviewAction) => Promise<void>;
  onUpdateClaim: (claimId: string, updateData: { status?: string; approved_amount?: number; adjuster_notes?: string }) => Promise<void>;
}

export const AdjusterDashboard: React.FC<AdjusterDashboardProps> = ({
  claims,
  onSelectClaim,
  onAdvanceWorkflow,
  onSubmitFraudReview,
  onUpdateClaim
}) => {
  const [activeQueueTab, setActiveQueueTab] = useState<'FRAUD_REVIEW' | 'ADJUSTER_REVIEW' | 'ALL'>('FRAUD_REVIEW');
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(claims[0]?.id || null);
  
  // Modals state
  const [fraudModalOpen, setFraudModalOpen] = useState(false);
  const [fraudConfirmed, setFraudConfirmed] = useState(false);
  const [investigatorNotes, setInvestigatorNotes] = useState('');

  const [adjusterModalOpen, setAdjusterModalOpen] = useState(false);
  const [adjusterActionType, setAdjusterActionType] = useState<'APPROVE' | 'MODIFY' | 'REJECT'>('APPROVE');
  const [modifiedPayout, setModifiedPayout] = useState<string>('');
  const [adjusterNotes, setAdjusterNotes] = useState<string>('');
  
  const [processing, setProcessing] = useState(false);
  const [advancing, setAdvancing] = useState(false);

  const fraudQueue = claims.filter(c => c.status === 'FRAUD_REVIEW' || c.risk_score >= 0.5);
  const adjusterQueue = claims.filter(c => c.status === 'ADJUSTER_REVIEW' || c.status === 'CLAIM_ANALYSIS');

  const currentList = activeQueueTab === 'FRAUD_REVIEW' ? fraudQueue : (activeQueueTab === 'ADJUSTER_REVIEW' ? adjusterQueue : claims);
  const selectedClaim = claims.find(c => c.id === selectedClaimId) || currentList[0] || claims[0];

  const handleOpenFraudAction = (confirmed: boolean) => {
    setFraudConfirmed(confirmed);
    setInvestigatorNotes(confirmed ? 'Confirmed suspicious synthetic identity pattern and staged collision evidence.' : 'Verified identity proofs; cleared anomaly risk flags.');
    setFraudModalOpen(true);
  };

  const handleConfirmFraudAction = async () => {
    if (!selectedClaim) return;
    setProcessing(true);
    try {
      await onSubmitFraudReview(selectedClaim.id, {
        fraud_confirmed: fraudConfirmed,
        investigator_notes: investigatorNotes,
      });
      setFraudModalOpen(false);
    } finally {
      setProcessing(false);
    }
  };

  const handleOpenAdjusterAction = (type: 'APPROVE' | 'MODIFY' | 'REJECT') => {
    if (!selectedClaim) return;
    setAdjusterActionType(type);
    setModifiedPayout((selectedClaim.approved_amount || selectedClaim.claimed_amount).toString());
    setAdjusterNotes(selectedClaim.adjuster_notes || '');
    setAdjusterModalOpen(true);
  };

  const handleConfirmAdjusterAction = async () => {
    if (!selectedClaim) return;
    setProcessing(true);
    try {
      let newStatus = 'APPROVED';
      let finalPayout = parseFloat(modifiedPayout) || 0;

      if (adjusterActionType === 'REJECT') {
        newStatus = 'REJECTED';
        finalPayout = 0;
      }

      await onUpdateClaim(selectedClaim.id, {
        status: newStatus,
        approved_amount: finalPayout,
        adjuster_notes: adjusterNotes,
      });
      setAdjusterModalOpen(false);
    } finally {
      setProcessing(false);
    }
  };

  const handleAdvanceStep = async () => {
    if (!selectedClaim) return;
    setAdvancing(true);
    try {
      await onAdvanceWorkflow(selectedClaim.id);
    } finally {
      setAdvancing(false);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '1.5rem' }}>
      {/* Left Queue View */}
      <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column' }}>
        <div style={{ marginBottom: '1rem' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '0.6rem' }}>Human Workflow Queues</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <button
              className={`tab-btn ${activeQueueTab === 'FRAUD_REVIEW' ? 'active' : ''}`}
              onClick={() => setActiveQueueTab('FRAUD_REVIEW')}
              style={{ textAlign: 'left', padding: '0.5rem 0.75rem', borderRadius: '8px', fontSize: '0.85rem', display: 'flex', justifyContent: 'space-between' }}
            >
              <span><ShieldAlert style={{ width: '14px', height: '14px', display: 'inline', marginRight: '6px' }} /> SIU Fraud Queue</span>
              <strong className="text-mono" style={{ color: '#f87171' }}>{fraudQueue.length}</strong>
            </button>
            <button
              className={`tab-btn ${activeQueueTab === 'ADJUSTER_REVIEW' ? 'active' : ''}`}
              onClick={() => setActiveQueueTab('ADJUSTER_REVIEW')}
              style={{ textAlign: 'left', padding: '0.5rem 0.75rem', borderRadius: '8px', fontSize: '0.85rem', display: 'flex', justifyContent: 'space-between' }}
            >
              <span><Edit3 style={{ width: '14px', height: '14px', display: 'inline', marginRight: '6px' }} /> Adjuster Review</span>
              <strong className="text-mono" style={{ color: '#fbbf24' }}>{adjusterQueue.length}</strong>
            </button>
            <button
              className={`tab-btn ${activeQueueTab === 'ALL' ? 'active' : ''}`}
              onClick={() => setActiveQueueTab('ALL')}
              style={{ textAlign: 'left', padding: '0.5rem 0.75rem', borderRadius: '8px', fontSize: '0.85rem', display: 'flex', justifyContent: 'space-between' }}
            >
              <span>All Claims Database</span>
              <strong className="text-mono">{claims.length}</strong>
            </button>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          {currentList.map(claim => {
            const isSelected = selectedClaim?.id === claim.id;
            return (
              <div
                key={claim.id}
                onClick={() => { setSelectedClaimId(claim.id); onSelectClaim(claim); }}
                style={{
                  padding: '0.85rem',
                  borderRadius: '10px',
                  background: isSelected ? 'rgba(99,102,241,0.18)' : 'rgba(0,0,0,0.2)',
                  border: `1px solid ${isSelected ? 'var(--primary)' : 'var(--border-color)'}`,
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.35rem' }}>
                  <span className="text-mono" style={{ fontSize: '0.75rem', color: 'var(--primary)', fontWeight: '600' }}>{claim.claim_number}</span>
                  <span className={`badge ${claim.status === 'COMPLETED' ? 'badge-approve' : (claim.status === 'FRAUD_REVIEW' || claim.status === 'REJECTED' ? 'badge-reject' : 'badge-review')}`} style={{ fontSize: '0.65rem' }}>
                    {claim.status}
                  </span>
                </div>
                <div style={{ fontWeight: '600', fontSize: '0.9rem' }}>{claim.claimant_name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between', marginTop: '0.35rem' }}>
                  <span>Risk Score: <strong className="text-mono" style={{ color: claim.risk_score >= 0.5 ? '#f87171' : '#34d399' }}>{claim.risk_score.toFixed(2)}</strong></span>
                  <strong className="text-mono">${claim.claimed_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right Detailed Workbench Panel */}
      {selectedClaim ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Header Card */}
          <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                <span className="text-mono" style={{ color: 'var(--primary)', fontWeight: '700', fontSize: '0.9rem' }}>{selectedClaim.claim_number}</span>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>| Policy: <strong className="text-mono">{selectedClaim.policy_number}</strong></span>
              </div>
              <h2 style={{ fontSize: '1.4rem' }}>{selectedClaim.claimant_name} ({selectedClaim.claim_type} Insurance)</h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>{selectedClaim.incident_description}</p>
            </div>

            {/* Persona Action Buttons */}
            {selectedClaim.status === 'FRAUD_REVIEW' ? (
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button onClick={() => handleOpenFraudAction(false)} className="btn-primary" style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', boxShadow: 'none' }}>
                  <CheckCircle2 style={{ width: '16px', height: '16px' }} /> Clear Fraud Flags
                </button>
                <button onClick={() => handleOpenFraudAction(true)} className="btn-secondary" style={{ color: '#f87171', borderColor: 'rgba(239,68,68,0.4)' }}>
                  <AlertTriangle style={{ width: '16px', height: '16px' }} /> Confirm Fraud (Reject)
                </button>
              </div>
            ) : selectedClaim.status === 'ADJUSTER_REVIEW' ? (
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button onClick={() => handleOpenAdjusterAction('APPROVE')} className="btn-primary" style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', boxShadow: 'none' }}>
                  <CheckCircle2 style={{ width: '16px', height: '16px' }} /> Approve Payout
                </button>
                <button onClick={() => handleOpenAdjusterAction('MODIFY')} className="btn-secondary">
                  <Edit3 style={{ width: '16px', height: '16px' }} /> Modify Payout
                </button>
                <button onClick={() => handleOpenAdjusterAction('REJECT')} className="btn-secondary" style={{ color: '#f87171' }}>
                  <XCircle style={{ width: '16px', height: '16px' }} /> Reject
                </button>
              </div>
            ) : (
              <button onClick={handleAdvanceStep} disabled={advancing} className="btn-primary" style={{ fontSize: '0.85rem' }}>
                <Play style={{ width: '14px', height: '14px' }} /> {advancing ? 'Advancing Workflow...' : 'Advance Workflow Engine Step'}
              </button>
            )}
          </div>

          {/* Privacy & PII Redaction Audit Card */}
          {selectedClaim.redacted_description && (
            <div className="glass-panel" style={{ padding: '1rem 1.25rem', background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.2)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#34d399', fontSize: '0.85rem', fontWeight: '600', marginBottom: '0.35rem' }}>
                <Lock style={{ width: '15px', height: '15px' }} /> Privacy Guard Sanitized Narrative (PII Flags: {selectedClaim.privacy_flags?.join(', ') || 'None'})
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-main)', fontFamily: 'var(--font-mono)', background: 'rgba(0,0,0,0.3)', padding: '0.65rem', borderRadius: '6px' }}>
                {selectedClaim.redacted_description}
              </div>
            </div>
          )}

          {/* Adjuster Notes History */}
          {selectedClaim.adjuster_notes && (
            <div className="glass-panel" style={{ padding: '1rem 1.25rem', background: 'rgba(99,102,241,0.06)', border: '1px dashed var(--border-highlight)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem', color: 'var(--primary)', fontWeight: '600', fontSize: '0.85rem' }}>
                <MessageSquare style={{ width: '15px', height: '15px' }} /> Adjuster Audit Notes:
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-main)', fontStyle: 'italic' }}>
                "{selectedClaim.adjuster_notes}"
              </p>
            </div>
          )}

          {/* Workflow Execution Timeline */}
          <div className="glass-panel" style={{ padding: '1.25rem' }}>
            <WorkflowVisualizer steps={[]} evaluating={false} claimHistory={selectedClaim.workflow_history} currentStatus={selectedClaim.status} />
          </div>
        </div>
      ) : (
        <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-dim)' }}>
          Select a claim from the queue to inspect.
        </div>
      )}

      {/* SIU Fraud Review Modal */}
      {fraudModalOpen && (
        <div className="modal-overlay">
          <div className="glass-panel" style={{ width: '100%', maxWidth: '500px', padding: '1.75rem' }}>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem', color: fraudConfirmed ? '#f87171' : '#34d399' }}>
              {fraudConfirmed ? 'Confirm SIU Fraud Determination (Reject)' : 'Clear Fraud Flags (Proceed to Claim Analysis)'}
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Record SIU investigation finding for claim <strong className="text-mono">{selectedClaim?.claim_number}</strong>.
            </p>

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>SIU Investigator Findings & Notes</label>
              <textarea
                value={investigatorNotes}
                onChange={e => setInvestigatorNotes(e.target.value)}
                rows={4}
                required
                style={{ width: '100%', padding: '0.65rem', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', color: '#fff', fontSize: '0.85rem', lineHeight: '1.5' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button onClick={() => setFraudModalOpen(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleConfirmFraudAction} disabled={processing} className="btn-primary">
                {processing ? 'Saving...' : 'Confirm SIU Finding'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Adjuster Payout Review Modal */}
      {adjusterModalOpen && (
        <div className="modal-overlay">
          <div className="glass-panel" style={{ width: '100%', maxWidth: '500px', padding: '1.75rem' }}>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>
              {adjusterActionType === 'APPROVE' && 'Approve Claim Payout'}
              {adjusterActionType === 'MODIFY' && 'Modify Payout Amount'}
              {adjusterActionType === 'REJECT' && 'Reject Claim'}
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
              Record final adjuster determination for claim <strong className="text-mono">{selectedClaim?.claim_number}</strong>.
            </p>

            {adjusterActionType !== 'REJECT' && (
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>Authorized Payout Amount ($ USD)</label>
                <input
                  type="number"
                  step="0.01"
                  value={modifiedPayout}
                  onChange={e => setModifiedPayout(e.target.value)}
                  className="text-mono"
                  style={{ width: '100%', padding: '0.65rem', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', color: '#fff', fontSize: '0.9rem' }}
                />
              </div>
            )}

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>Adjuster Reasoning / Feedback Notes</label>
              <textarea
                value={adjusterNotes}
                onChange={e => setAdjusterNotes(e.target.value)}
                rows={4}
                placeholder="Enter justification for audit trail..."
                style={{ width: '100%', padding: '0.65rem', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', color: '#fff', fontSize: '0.85rem', lineHeight: '1.5' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button onClick={() => setAdjusterModalOpen(false)} className="btn-secondary">Cancel</button>
              <button onClick={handleConfirmAdjusterAction} disabled={processing} className="btn-primary">
                {processing ? 'Saving...' : 'Save & Trigger Semantic Bridge'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
