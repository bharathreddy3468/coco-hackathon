import React, { useState } from 'react';
import { Cpu, Play, Terminal } from 'lucide-react';
import { SkillMeta, SkillExecutionResult } from '../types/claim';

interface SkillExecutorProps {
  skills: SkillMeta[];
  onExecuteSkill: (skillId: string, inputData: Record<string, unknown>) => Promise<SkillExecutionResult>;
}

export const SkillExecutor: React.FC<SkillExecutorProps> = ({ skills, onExecuteSkill }) => {
  const [selectedSkillId, setSelectedSkillId] = useState<string>(skills[0]?.id || 'skill_claim_extractor');
  const [inputJson, setInputJson] = useState<string>(
    JSON.stringify({
      policy_number: 'POL-2026-9921',
      claimed_amount: 4500.0,
      incident_description: 'Vehicle collided with deer on highway 101. Front bumper damaged.',
      claim_type: 'Auto'
    }, null, 2)
  );
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SkillExecutionResult | null>(null);

  const activeSkill = skills.find(s => s.id === selectedSkillId);

  const handleRun = async () => {
    setLoading(true);
    setResult(null);
    try {
      const parsed = JSON.parse(inputJson);
      const res = await onExecuteSkill(selectedSkillId, parsed);
      setResult(res);
    } catch (e) {
      alert(`Invalid JSON or execution error: ${e}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
      <div className="glass-panel" style={{ padding: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1rem' }}>
          <Cpu style={{ width: '22px', height: '22px', color: 'var(--primary)' }} />
          <h3 style={{ fontSize: '1.2rem' }}>AI Skills Registry Sandbox</h3>
        </div>

        <div style={{ marginBottom: '1.25rem' }}>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem' }}>Select Skill Target</label>
          <select
            value={selectedSkillId}
            onChange={e => setSelectedSkillId(e.target.value)}
            style={{ width: '100%', padding: '0.65rem', borderRadius: '8px', background: 'rgba(0,0,0,0.4)', color: '#fff', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}
          >
            {skills.map(skill => (
              <option key={skill.id} value={skill.id}>
                {skill.name} ({skill.category})
              </option>
            ))}
          </select>
        </div>

        {activeSkill && (
          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '0.85rem', borderRadius: '8px', border: '1px solid var(--border-color)', marginBottom: '1.25rem' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--primary)' }}>{activeSkill.name} (v{activeSkill.version})</div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>{activeSkill.description}</p>
          </div>
        )}

        <div style={{ marginBottom: '1.25rem' }}>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.4rem' }}>Skill Input JSON Payload</label>
          <textarea
            value={inputJson}
            onChange={e => setInputJson(e.target.value)}
            rows={10}
            className="text-mono"
            style={{ width: '100%', padding: '0.75rem', borderRadius: '8px', background: '#090d16', color: '#a5b4fc', border: '1px solid var(--border-color)', fontSize: '0.85rem', lineHeight: '1.5' }}
          />
        </div>

        <button onClick={handleRun} disabled={loading} className="btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
          <Play style={{ width: '16px', height: '16px' }} /> {loading ? 'Executing Skill...' : 'Trigger Skill Execution'}
        </button>
      </div>

      <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1rem' }}>
          <Terminal style={{ width: '22px', height: '22px', color: 'var(--accent-cyan)' }} />
          <h3 style={{ fontSize: '1.2rem' }}>Skill Execution Result</h3>
        </div>

        {result ? (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(0,0,0,0.3)', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'block' }}>Status</span>
                <span style={{ color: result.success ? '#34d399' : '#f87171', fontWeight: '600', fontSize: '0.9rem' }}>
                  {result.success ? 'SUCCESS 200' : 'FAILED'}
                </span>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'block' }}>Latency</span>
                <span className="text-mono" style={{ color: '#fff', fontSize: '0.9rem' }}>{result.execution_time_ms} ms</span>
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', display: 'block' }}>Confidence Score</span>
                <span className="text-mono" style={{ color: '#38bdf8', fontWeight: '600', fontSize: '0.9rem' }}>{(result.confidence_score * 100).toFixed(0)}%</span>
              </div>
            </div>

            <div>
              <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>Reasoning Steps:</h4>
              <ul style={{ paddingLeft: '1.25rem', fontSize: '0.85rem', color: 'var(--text-main)', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                {result.reasoning.map((r, idx) => (
                  <li key={idx}>{r}</li>
                ))}
              </ul>
            </div>

            <div style={{ flex: 1 }}>
              <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.4rem' }}>Output Data Payload:</h4>
              <pre className="text-mono" style={{ background: '#0b0f19', padding: '0.85rem', borderRadius: '8px', fontSize: '0.8rem', color: '#34d399', border: '1px solid var(--border-color)', height: '220px', overflowY: 'auto' }}>
                {JSON.stringify(result.output, null, 2)}
              </pre>
            </div>
          </div>
        ) : (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)', fontSize: '0.875rem' }}>
            Select a skill on the left and click trigger to see isolated output.
          </div>
        )}
      </div>
    </div>
  );
};
