import React, { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { MetricsOverview } from './components/MetricsOverview';
import { CustomerPortal } from './components/CustomerPortal';
import { AdjusterDashboard } from './components/AdjusterDashboard';
import { SkillExecutor } from './components/SkillExecutor';
import { api } from './services/api';
import { Claim, SkillMeta, SystemReadiness, ClaimDocument, FraudReviewAction } from './types/claim';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'customer' | 'adjuster' | 'skills'>('customer');
  const [readiness, setReadiness] = useState<SystemReadiness | null>(null);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [skills, setSkills] = useState<SkillMeta[]>([]);
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
    } finally {
      setLoading(false);
    }
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

  const handleSubmitFraudReview = async (claimId: string, action: FraudReviewAction) => {
    await api.submitFraudReview(claimId, action);
    const updatedClaims = await api.getClaims();
    setClaims(updatedClaims);
  };

  const handleUpdateClaim = async (claimId: string, updateData: { status?: string; approved_amount?: number; adjuster_notes?: string }) => {
    await api.updateClaim(claimId, updateData);
    const updatedClaims = await api.getClaims();
    setClaims(updatedClaims);
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
    </div>
  );
};
