import React from 'react';
import { Shield, Cpu, Activity, CheckCircle, AlertCircle, User, ShieldAlert } from 'lucide-react';
import { SystemReadiness } from '../types/claim';

interface NavbarProps {
  readiness: SystemReadiness | null;
  activeTab: 'customer' | 'adjuster' | 'skills';
  setActiveTab: (tab: 'customer' | 'adjuster' | 'skills') => void;
  onNewClaim: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ readiness, activeTab, setActiveTab, onNewClaim }) => {
  return (
    <header className="glass-panel" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)', padding: '0.65rem', borderRadius: '12px', display: 'flex', boxShadow: '0 0 15px rgba(99,102,241,0.4)' }}>
          <Shield style={{ width: '24px', height: '24px', color: '#fff' }} />
        </div>
        <div>
          <h1 className="text-gradient" style={{ fontSize: '1.35rem', lineHeight: '1.2' }}>Insurance Claims Copilot</h1>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Autonomous Insurance Triage & AI Skill Engine</p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {/* Persona & View Switcher */}
        <nav style={{ display: 'flex', gap: '0.35rem', background: 'rgba(0,0,0,0.3)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
          <button
            onClick={() => setActiveTab('customer')}
            className={`tab-btn ${activeTab === 'customer' ? 'active' : ''}`}
            style={{ padding: '0.45rem 0.9rem', borderRadius: '6px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <User style={{ width: '15px', height: '15px' }} />
            Customer Portal
          </button>
          <button
            onClick={() => setActiveTab('adjuster')}
            className={`tab-btn ${activeTab === 'adjuster' ? 'active' : ''}`}
            style={{ padding: '0.45rem 0.9rem', borderRadius: '6px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <ShieldAlert style={{ width: '15px', height: '15px' }} />
            Adjuster Workbench
          </button>
          <button
            onClick={() => setActiveTab('skills')}
            className={`tab-btn ${activeTab === 'skills' ? 'active' : ''}`}
            style={{ padding: '0.45rem 0.9rem', borderRadius: '6px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}
          >
            <Cpu style={{ width: '15px', height: '15px' }} />
            AI Skills Lab
          </button>
        </nav>

        {readiness && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', background: 'rgba(255,255,255,0.03)', padding: '0.4rem 0.8rem', borderRadius: '20px', border: '1px solid var(--border-color)' }}>
            <Activity style={{ width: '14px', height: '14px', color: 'var(--accent-cyan)' }} />
            <span>Skills: <strong style={{ color: '#fff' }}>{readiness.skills_loaded} Active</strong></span>
            <span style={{ color: 'var(--text-dim)' }}>|</span>
            <span style={{ color: '#818cf8', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Shield style={{ width: '12px', height: '12px' }} /> PII Guard Active
            </span>
            <span style={{ color: 'var(--text-dim)' }}>|</span>
            {readiness.database_connected ? (
              <span style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <CheckCircle style={{ width: '12px', height: '12px' }} /> DB Ready
              </span>
            ) : (
              <span style={{ color: '#f87171', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <AlertCircle style={{ width: '12px', height: '12px' }} /> DB Degraded
              </span>
            )}
          </div>
        )}

        {activeTab === 'adjuster' && (
          <button onClick={onNewClaim} className="btn-primary" style={{ fontSize: '0.85rem' }}>
            + Quick Claim
          </button>
        )}
      </div>
    </header>
  );
};
