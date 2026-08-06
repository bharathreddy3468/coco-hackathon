import React, { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { MetricsOverview } from './components/MetricsOverview';
import { CustomerPortal } from './components/CustomerPortal';
import { AdjusterDashboard } from './components/AdjusterDashboard';
import { SkillExecutor } from './components/SkillExecutor';
import { ClaimDetailModal } from './components/ClaimDetailModal';
import { api } from './services/api';
import { Claim, SkillMeta, SystemReadiness, ClaimDocument, FraudReviewAction } from './types/claim';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'customer' | 'adjuster' | 'skills'>('customer');
  const [readiness, setReadiness] = useState<SystemReadiness | null>(null);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [skills, setSkills] = useState<SkillMeta[]>([]);
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const loadData = async () => {
    try {
      const [readyRes, claimsRes, skillsRes] = await Promise.all([
        api.getReadiness().catch(() => null),
        api.getClaims().catch(() => []),
        api.getSkills().catch(() => []),
      ]);
      setReadiness(readyRes);
      setClaims(claimsRes);
      setSkills(skillsRes);

      if (claimsRes.length === 0) {
        await seedMockClaims();
      }
    } finally {
      setLoading(false);
    }
  };

  const seedMockClaims = async () => {
    const mocks = [
      {
        policy_number: 'POL-2026-1049',
        claimant_name: 'David Miller',
        claim_type: 'Auto',
        claimed_amount: 1850.0,
        incident_description: 'Low-speed rear-end fender bender while stopped at red light. Contact is 555-0192, SSN 000-12-3456.',
        documents: [{ name: 'police_report.pdf', size: '1.2 MB', type: 'application/pdf' }]
      },
      {
        policy_number: 'POL-2026-8820',
        claimant_name: 'Elena Rostova',
        claim_type: 'Property',
        claimed_amount: 14200.0,
        incident_description: 'Water pipe burst unwitnessed during extreme freeze. Cash cleanup fee requested.',
        documents: [{ name: 'water_damage_photo.png', size: '3.1 MB', type: 'image/png' }]
      },
      {
        policy_number: 'EXPIRED-POL-99',
        claimant_name: 'Marcus Vance',
        claim_type: 'Auto',
        claimed_amount: 3200.0,
        incident_description: 'Windshield cracked by flying gravel on interstate 80.',
        documents: [{ name: 'windshield_photo.jpg', size: '1.8 MB', type: 'image/jpeg' }]
      },
    ];

    for (const m of mocks) {
      await api.createClaim(m).catch(() => null);
    }
    const fresh = await api.getClaims().catch(() => []);
    setClaims(fresh);
  };

  useEffect(() => {
    loadData();
    // Auto-refresh poll every 3 seconds to catch background workflow transitions
    const interval = setInterval(() => {
      api.getClaims().then(setClaims).catch(() => null);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleCustomerSubmitClaim = async (data: {
    policy_number: string;
    claimant_name: string;
    claim_type: string;
    claimed_amount: number;
    incident_description: string;
    documents: ClaimDocument[];
  }) => {
    await api.createClaim(data);
    const updatedClaims = await api.getClaims();
    setClaims(updatedClaims);
  };

  const handleAdvanceWorkflow = async (claimId: string) => {
    await api.advanceWorkflow(claimId);
    const updatedClaims = await api.getClaims();
    setClaims(updatedClaims);
    const updatedSelected = updatedClaims.find(c => c.id === claimId);
    if (updatedSelected) {
      setSelectedClaim(updatedSelected);
    }
  };

  const handleSubmitFraudReview = async (claimId: string, action: FraudReviewAction) => {
    await api.submitFraudReview(claimId, action);
    const updatedClaims = await api.getClaims();
    setClaims(updatedClaims);
    const updatedSelected = updatedClaims.find(c => c.id === claimId);
    if (updatedSelected) {
      setSelectedClaim(updatedSelected);
    }
  };

  const handleUpdateClaim = async (claimId: string, updateData: { status?: string; approved_amount?: number; adjuster_notes?: string }) => {
    await api.updateClaim(claimId, updateData);
    const updatedClaims = await api.getClaims();
    setClaims(updatedClaims);
    const updatedSelected = updatedClaims.find(c => c.id === claimId);
    if (updatedSelected) {
      setSelectedClaim(updatedSelected);
    }
  };

  const handleQuickCreateClaim = async () => {
    const claimantNames = ['Sophia Chen', 'James Wilson', 'Amara Patel', 'Lucas Bennett'];
    const types = ['Auto', 'Property', 'Health'];
    const randomName = claimantNames[Math.floor(Math.random() * claimantNames.length)];
    const randomType = types[Math.floor(Math.random() * types.length)];
    const randomAmount = Math.round(1500 + Math.random() * 8500);

    try {
      await api.createClaim({
        policy_number: `POL-2026-${Math.floor(1000 + Math.random() * 9000)}`,
        claimant_name: randomName,
        claim_type: randomType,
        claimed_amount: randomAmount,
        incident_description: `Incident reported by claimant ${randomName}. Minor collision damage. Contact 555-0188.`,
        documents: [{ name: 'incident_photo.jpg', size: '2.1 MB', type: 'image/jpeg' }]
      });
      const updatedClaims = await api.getClaims();
      setClaims(updatedClaims);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="app-container">
      <Navbar
        readiness={readiness}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onNewClaim={handleQuickCreateClaim}
      />

      <main>
        {activeTab === 'customer' && (
          <CustomerPortal
            claims={claims}
            onSubmitClaim={handleCustomerSubmitClaim}
            onSelectClaim={setSelectedClaim}
          />
        )}

        {activeTab === 'adjuster' && (
          <div>
            <MetricsOverview claims={claims} />
            {loading ? (
              <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>Loading async workflow claims data...</div>
            ) : (
              <AdjusterDashboard
                claims={claims}
                onSelectClaim={setSelectedClaim}
                onAdvanceWorkflow={handleAdvanceWorkflow}
                onSubmitFraudReview={handleSubmitFraudReview}
                onUpdateClaim={handleUpdateClaim}
              />
            )}
          </div>
        )}

        {activeTab === 'skills' && (
          <SkillExecutor skills={skills} onExecuteSkill={api.executeSkill} />
        )}
      </main>

      {selectedClaim && activeTab !== 'adjuster' && (
        <ClaimDetailModal
          claim={selectedClaim}
          onClose={() => setSelectedClaim(null)}
          onEvaluate={handleAdvanceWorkflow}
        />
      )}
    </div>
  );
};
