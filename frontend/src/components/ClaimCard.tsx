import React from 'react';
import { ArrowRight, ShieldCheck, AlertCircle, XCircle, Clock } from 'lucide-react';
import { Claim } from '../types/claim';

interface ClaimCardProps {
  claim: Claim;
  onSelect: (claim: Claim) => void;
}

export const ClaimCard: React.FC<ClaimCardProps> = ({ claim, onSelect }) => {
  const getBadge = (rec: string) => {
    switch (rec) {
      case 'AUTO_APPROVE':
        return <span className="badge badge-approve"><ShieldCheck style={{ width: '12px', height: '12px' }} /> Auto Approve</span>;
      case 'MANUAL_REVIEW':
        return <span className="badge badge-review"><AlertCircle style={{ width: '12px', height: '12px' }} /> Manual Review</span>;
      case 'REJECT':
        return <span className="badge badge-reject"><XCircle style={{ width: '12px', height: '12px' }} /> Reject</span>;
      default:
        return <span className="badge badge-pending"><Clock style={{ width: '12px', height: '12px' }} /> Pending Triage</span>;
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', cursor: 'pointer' }} onClick={() => onSelect(claim)}>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
          <div>
            <span className="text-mono" style={{ fontSize: '0.8rem', color: 'var(--primary)', fontWeight: '600' }}>{claim.claim_number}</span>
            <h3 style={{ fontSize: '1.1rem', marginTop: '0.25rem' }}>{claim.claimant_name}</h3>
          </div>
          {getBadge(claim.copilot_recommendation)}
        </div>

        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
          <div>
            <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.75rem' }}>Type</span>
            <strong>{claim.claim_type}</strong>
          </div>
          <div>
            <span style={{ color: 'var(--text-dim)', display: 'block', fontSize: '0.75rem' }}>Claimed Amount</span>
            <strong className="text-mono" style={{ color: '#fff' }}>${claim.claimed_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
          </div>
        </div>

        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', marginBottom: '1rem', background: 'rgba(0,0,0,0.2)', padding: '0.5rem', borderRadius: '6px' }}>
          {claim.incident_description}
        </p>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.75rem', borderTop: '1px solid var(--border-color)', fontSize: '0.8rem' }}>
        <span style={{ color: 'var(--text-dim)' }}>Policy: <span className="text-mono" style={{ color: 'var(--text-muted)' }}>{claim.policy_number}</span></span>
        <span className="btn-secondary" style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}>
          Inspect & Triage <ArrowRight style={{ width: '12px', height: '12px' }} />
        </span>
      </div>
    </div>
  );
};
