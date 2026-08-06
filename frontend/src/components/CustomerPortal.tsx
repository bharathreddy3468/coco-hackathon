import React, { useState } from 'react';
import { UploadCloud, FileText, Trash2, Sparkles, Lock } from 'lucide-react';
import { Claim, ClaimDocument, ClaimState } from '../types/claim';

interface CustomerPortalProps {
  claims: Claim[];
  onSubmitClaim: (data: {
    policy_number: string;
    claimant_name: string;
    claim_type: string;
    claimed_amount: number;
    incident_description: string;
    documents: ClaimDocument[];
  }) => Promise<void>;
  onSelectClaim: (claim: Claim) => void;
}

export const CustomerPortal: React.FC<CustomerPortalProps> = ({ claims, onSubmitClaim, onSelectClaim }) => {
  const [policyNumber, setPolicyNumber] = useState('POL-2026-4491');
  const [claimantName, setClaimantName] = useState('Sarah Jenkins');
  const [claimType, setClaimType] = useState('Auto');
  const [claimedAmount, setClaimedAmount] = useState('2450.00');
  const [incidentDescription, setIncidentDescription] = useState('Vehicle rear-ended while stopped at red light on 5th Ave. Contact number is 555-0192, SSN 000-12-3456.');
  
  const [documents, setDocuments] = useState<ClaimDocument[]>([
    { name: 'police_accident_report.pdf', size: '1.4 MB', type: 'application/pdf' },
    { name: 'vehicle_damage_photo.png', size: '2.8 MB', type: 'image/png' },
  ]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);

  const handleAddDemoFile = () => {
    const fileOptions: ClaimDocument[] = [
      { name: 'repair_estimate_quote.pdf', size: '890 KB', type: 'application/pdf' },
      { name: 'medical_receipt_bill.pdf', size: '1.1 MB', type: 'application/pdf' },
      { name: 'incident_scene_photo.jpg', size: '3.4 MB', type: 'image/jpeg' },
    ];
    const nextFile = fileOptions[documents.length % fileOptions.length];
    setDocuments([...documents, nextFile]);
  };

  const handleRemoveFile = (index: number) => {
    setDocuments(documents.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claimedAmount || parseFloat(claimedAmount) <= 0) return;
    setIsSubmitting(true);
    try {
      await onSubmitClaim({
        policy_number: policyNumber,
        claimant_name: claimantName,
        claim_type: claimType,
        claimed_amount: parseFloat(claimedAmount),
        incident_description: incidentDescription,
        documents,
      });
      setIncidentDescription('');
      setDocuments([]);
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeClaim = claims.find(c => c.id === selectedClaimId) || claims[0];

  const getWorkflowBadge = (status: ClaimState) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="badge badge-approve">COMPLETED</span>;
      case 'REJECTED':
        return <span className="badge badge-reject">REJECTED</span>;
      case 'FRAUD_REVIEW':
        return <span className="badge badge-review">SIU FRAUD REVIEW</span>;
      case 'ADJUSTER_REVIEW':
        return <span className="badge badge-review">ADJUSTER REVIEW</span>;
      default:
        return <span className="badge badge-pending">{status.replace('_', ' ')}</span>;
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: '1.5rem' }}>
      {/* Submit Claim Form */}
      <div className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1.25rem' }}>
          <FileText style={{ width: '22px', height: '22px', color: 'var(--primary)' }} />
          <div>
            <h2 style={{ fontSize: '1.25rem' }}>Submit an Insurance Claim</h2>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Asynchronous workflow dispatch with instant Claim ID response</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>Policy Number</label>
              <input
                type="text"
                value={policyNumber}
                onChange={e => setPolicyNumber(e.target.value)}
                required
                className="text-mono"
                style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', color: '#fff', fontSize: '0.85rem' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>Claimant Full Name</label>
              <input
                type="text"
                value={claimantName}
                onChange={e => setClaimantName(e.target.value)}
                required
                style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', color: '#fff', fontSize: '0.85rem' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>Insurance Line Type</label>
              <select
                value={claimType}
                onChange={e => setClaimType(e.target.value)}
                style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', color: '#fff', fontSize: '0.85rem' }}
              >
                <option value="Auto">Auto Collision</option>
                <option value="Property">Property & Home</option>
                <option value="Health">Medical / Health</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>Claimed Amount ($ USD)</label>
              <input
                type="number"
                step="0.01"
                value={claimedAmount}
                onChange={e => setClaimedAmount(e.target.value)}
                required
                className="text-mono"
                style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', color: '#fff', fontSize: '0.85rem' }}
              />
            </div>
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>Incident Narrative</label>
            <textarea
              value={incidentDescription}
              onChange={e => setIncidentDescription(e.target.value)}
              rows={3}
              required
              placeholder="Describe incident details..."
              style={{ width: '100%', padding: '0.6rem', borderRadius: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', color: '#fff', fontSize: '0.85rem', lineHeight: '1.5' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem' }}>Supporting Evidence Documents</label>
            <div
              onClick={handleAddDemoFile}
              style={{
                border: '2px dashed var(--border-highlight)',
                borderRadius: '10px',
                padding: '1rem',
                textAlign: 'center',
                background: 'rgba(99,102,241,0.04)',
                cursor: 'pointer',
              }}
            >
              <UploadCloud style={{ width: '24px', height: '24px', color: 'var(--primary)', marginBottom: '0.2rem' }} />
              <div style={{ fontSize: '0.85rem', fontWeight: '500' }}>Click to Upload Documents (PDF / Photos)</div>
            </div>

            {documents.length > 0 && (
              <div style={{ marginTop: '0.6rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                {documents.map((doc, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.3)', padding: '0.4rem 0.75rem', borderRadius: '6px', fontSize: '0.8rem', border: '1px solid var(--border-color)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <FileText style={{ width: '14px', height: '14px', color: '#a5b4fc' }} />
                      <span>{doc.name}</span>
                      <span className="text-mono" style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>({doc.size})</span>
                    </div>
                    <button type="button" onClick={() => handleRemoveFile(idx)} style={{ background: 'transparent', border: 'none', color: '#f87171', cursor: 'pointer' }}>
                      <Trash2 style={{ width: '14px', height: '14px' }} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <button type="submit" disabled={isSubmitting} className="btn-primary" style={{ marginTop: '0.5rem', justifyContent: 'center' }}>
            <Sparkles style={{ width: '16px', height: '16px' }} />
            {isSubmitting ? 'Submitting to Workflow Engine...' : 'Submit Claim (Instant Async Intake)'}
          </button>
        </form>
      </div>

      {/* Customer Status & Workflow Stepper View */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>My Claim Workflow Progress</h3>
          {claims.length === 0 ? (
            <div style={{ textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.85rem', padding: '1.5rem' }}>
              No claims submitted yet.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {claims.slice(0, 4).map(c => (
                <div
                  key={c.id}
                  onClick={() => { setSelectedClaimId(c.id); onSelectClaim(c); }}
                  style={{
                    padding: '0.85rem 1rem',
                    borderRadius: '10px',
                    background: activeClaim?.id === c.id ? 'rgba(99,102,241,0.15)' : 'rgba(0,0,0,0.2)',
                    border: `1px solid ${activeClaim?.id === c.id ? 'var(--primary)' : 'var(--border-color)'}`,
                    cursor: 'pointer',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <div>
                    <span className="text-mono" style={{ fontSize: '0.75rem', color: 'var(--primary)' }}>{c.claim_number}</span>
                    <div style={{ fontWeight: '600', fontSize: '0.9rem' }}>{c.claim_type} Insurance</div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Claimed: ${c.claimed_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                  </div>
                  {getWorkflowBadge(c.status)}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Privacy Guard & PII Redaction Card */}
        {activeClaim && activeClaim.redacted_description && (
          <div className="glass-panel" style={{ padding: '1.25rem', background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#34d399', fontSize: '0.85rem', fontWeight: '600', marginBottom: '0.5rem' }}>
              <Lock style={{ width: '15px', height: '15px' }} /> Privacy Guard Skill Active (PII Sanitized)
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-main)', background: 'rgba(0,0,0,0.3)', padding: '0.65rem', borderRadius: '6px', fontFamily: 'var(--font-mono)' }}>
              {activeClaim.redacted_description}
            </p>
          </div>
        )}

        {/* AI Semantic Bridge Customer Explanation */}
        {activeClaim && activeClaim.customer_explanation && (
          <div className="glass-panel" style={{ padding: '1.25rem', background: 'linear-gradient(135deg, rgba(99,102,241,0.12) 0%, rgba(14,165,233,0.06) 100%)', border: '1px solid var(--border-highlight)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <Sparkles style={{ width: '18px', height: '18px', color: 'var(--accent-cyan)' }} />
              <h4 style={{ fontSize: '1rem', color: '#fff' }}>Semantic Bridge AI Explanation</h4>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-main)', lineHeight: '1.6' }}>
              {activeClaim.customer_explanation}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
