import React from 'react';
import { ShieldCheck, AlertCircle, XCircle, CheckCircle2, AlertTriangle } from 'lucide-react';
import { ClaimCopilotEvaluation } from '../types/claim';

interface DecisionSummaryProps {
  evaluation: ClaimCopilotEvaluation;
}

export const DecisionSummary: React.FC<DecisionSummaryProps> = ({ evaluation }) => {
  const { overall_recommendation, confidence_score, fraud_risk_score, suggested_payout, summary_reasoning } = evaluation;

  const getStyle = () => {
    switch (overall_recommendation) {
      case 'AUTO_APPROVE':
        return { color: '#34d399', bg: 'rgba(16, 185, 129, 0.12)', border: 'rgba(16, 185, 129, 0.3)', icon: ShieldCheck, title: 'AUTO APPROVED' };
      case 'MANUAL_REVIEW':
        return { color: '#fbbf24', bg: 'rgba(245, 158, 11, 0.12)', border: 'rgba(245, 158, 11, 0.3)', icon: AlertCircle, title: 'FLAGGED FOR MANUAL REVIEW' };
      case 'REJECT':
        return { color: '#f87171', bg: 'rgba(239, 68, 68, 0.12)', border: 'rgba(239, 68, 68, 0.3)', icon: XCircle, title: 'REJECTED BY POLICY RULES' };
      default:
        return { color: '#cbd5e1', bg: 'rgba(255, 255, 255, 0.05)', border: 'var(--border-color)', icon: AlertCircle, title: 'PENDING' };
    }
  };

  const style = getStyle();
  const Icon = style.icon;

  return (
    <div style={{ background: style.bg, border: `1px solid ${style.border}`, borderRadius: '14px', padding: '1.25rem', marginBottom: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <Icon style={{ width: '24px', height: '24px', color: style.color }} />
          <h3 style={{ color: style.color, fontSize: '1.15rem' }}>{style.title}</h3>
        </div>
        <div className="text-mono" style={{ background: 'rgba(0,0,0,0.3)', padding: '0.3rem 0.75rem', borderRadius: '20px', fontSize: '0.8rem', border: '1px solid var(--border-color)' }}>
          Confidence: <strong style={{ color: '#fff' }}>{(confidence_score * 100).toFixed(0)}%</strong>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem', background: 'rgba(0,0,0,0.2)', padding: '0.85rem', borderRadius: '10px' }}>
        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Recommended Payout</span>
          <strong className="text-mono" style={{ fontSize: '1.25rem', color: suggested_payout > 0 ? '#34d399' : 'var(--text-main)' }}>
            ${suggested_payout.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </strong>
        </div>
        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Fraud Risk Index</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.2rem' }}>
            <strong className="text-mono" style={{ fontSize: '1.25rem', color: fraud_risk_score >= 0.5 ? '#f87171' : '#34d399' }}>
              {fraud_risk_score.toFixed(2)}
            </strong>
            {fraud_risk_score >= 0.5 && <AlertTriangle style={{ width: '16px', height: '16px', color: '#f87171' }} />}
          </div>
        </div>
      </div>

      <div>
        <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Key Audit Trail Reasoning:</h4>
        <ul style={{ listStyle: 'none', paddingLeft: 0, display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
          {summary_reasoning.map((r: string, i: number) => (
            <li key={i} style={{ fontSize: '0.85rem', color: 'var(--text-main)', display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
              <CheckCircle2 style={{ width: '14px', height: '14px', color: style.color, flexShrink: 0, marginTop: '3px' }} />
              <span>{r}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
