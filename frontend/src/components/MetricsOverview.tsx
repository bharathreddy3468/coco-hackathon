import React from 'react';
import { FileText, CheckCircle2, AlertTriangle, Zap } from 'lucide-react';
import { Claim } from '../types/claim';

interface MetricsOverviewProps {
  claims: Claim[];
}

export const MetricsOverview: React.FC<MetricsOverviewProps> = ({ claims }) => {
  const total = claims.length;
  const autoApproved = claims.filter(c => c.copilot_recommendation === 'AUTO_APPROVE').length;
  const highRisk = claims.filter(c => c.risk_score >= 0.5).length;
  
  const approvalRate = total > 0 ? Math.round((autoApproved / total) * 100) : 0;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
      <div className="glass-panel" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Total Claims Intake</span>
          <div style={{ background: 'rgba(99,102,241,0.15)', padding: '0.4rem', borderRadius: '8px' }}>
            <FileText style={{ width: '18px', height: '18px', color: '#818cf8' }} />
          </div>
        </div>
        <div style={{ fontSize: '1.8rem', fontWeight: '700' }}>{total}</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Active claims queue</div>
      </div>

      <div className="glass-panel" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Auto-Approval Rate</span>
          <div style={{ background: 'rgba(16,185,129,0.15)', padding: '0.4rem', borderRadius: '8px' }}>
            <CheckCircle2 style={{ width: '18px', height: '18px', color: '#34d399' }} />
          </div>
        </div>
        <div style={{ fontSize: '1.8rem', fontWeight: '700', color: '#34d399' }}>{approvalRate}%</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>{autoApproved} claims processed straight-through</div>
      </div>

      <div className="glass-panel" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Fraud & Risk Alerts</span>
          <div style={{ background: 'rgba(239,68,68,0.15)', padding: '0.4rem', borderRadius: '8px' }}>
            <AlertTriangle style={{ width: '18px', height: '18px', color: '#f87171' }} />
          </div>
        </div>
        <div style={{ fontSize: '1.8rem', fontWeight: '700', color: highRisk > 0 ? '#f87171' : 'var(--text-main)' }}>{highRisk}</div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Claims score &ge; 0.50 risk threshold</div>
      </div>

      <div className="glass-panel" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Copilot Triage Latency</span>
          <div style={{ background: 'rgba(56,189,248,0.15)', padding: '0.4rem', borderRadius: '8px' }}>
            <Zap style={{ width: '18px', height: '18px', color: '#38bdf8' }} />
          </div>
        </div>
        <div style={{ fontSize: '1.8rem', fontWeight: '700' }}><span className="text-mono">~12ms</span></div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Parallel skill pipeline execution</div>
      </div>
    </div>
  );
};
