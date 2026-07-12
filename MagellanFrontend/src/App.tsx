import React, { useState, useCallback, useEffect } from 'react';
import type { Runbook, AuditRow, QueryClusterRow } from './types';
import { api, API_BASE_URL, type TemporalDetails } from './api';
import { Sidebar } from './components/Sidebar';
import { Overview } from './components/Overview';
import { Console } from './components/Console';
import { Registry } from './components/Registry';
import { QueryClusters } from './components/QueryClusters';
import { AuditTrail } from './components/AuditTrail';
import { LiveTest } from './components/LiveTest';
import { ShadowTestReport } from './components/ShadowTestReport';
import { OpsFactory } from './components/OpsFactory';
import { LocalAdminAuth } from './components/LocalAdminAuth';
import { Bell, User, LogOut } from 'lucide-react';

/* ── Runbook data is loaded from FastAPI only. ── */
const initialRunbooks: Runbook[] = [];

/* ── Tab title / description mapping ── */
const tabMeta: Record<string, { title: string; subtitle: string }> = {
  overview: {
    title: 'Operations Overview',
    subtitle: 'Real-time health & performance across all AI Search surfaces.',
  },
  factory: {
    title: 'Automated Ops Factory',
    subtitle: 'Observe dynamic self-healing data flows and automated agent assembly lines in real-time.',
  },
  queue: {
    title: 'Ops Runbook Queue',
    subtitle: 'Active incidents triaged by Magellan\'s agent automation skills.',
  },
  registry: {
    title: 'Runbook Registry & Policies',
    subtitle: 'Manage automated agent skills and global release gates.',
  },
  clusters: {
    title: 'Query Cluster Analytics',
    subtitle: 'Semantic clustering of failed search logs, exits, and revenue loss.',
  },
  audit: {
    title: 'Audit Trail & Evidence Ledger',
    subtitle: 'Tamper-proof log of every canary, approval, and rollback.',
  },
  'live-test': {
    title: 'Live Workflow Test',
    subtitle: 'Trigger a new workflow run with a custom JSON input signal.',
  },
  'shadow-reports': {
    title: 'Shadow Test Reports',
    subtitle: 'View the results of simulated shadow tests.',
  },
};

const getRunbookProgress = (status: Runbook['status']) => {
  switch (status) {
    case 'Shadow Test':
      return 0.35;
    case 'Canary 5%':
      return 0.5;
    case 'Canary 25%':
      return 0.7;
    case 'Canary 100%':
      return 0.9;
    case 'Released':
      return 1;
    case 'Rolled Back':
      return 0;
    default:
      return 0;
  }
};

const App: React.FC = () => {
  /* ── Auth State ── */
  const [currentUser, setCurrentUser] = useState<string | null>(() => {
    return localStorage.getItem('magellan_auth_user');
  });

  /* ── Header Interaction States ── */
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  /* ── Navigation ── */
  const [currentTab, setCurrentTab] = useState('overview');

  /* ── Runbook state ── */
  const [runbooks, setRunbooks] = useState(initialRunbooks);
  const [selectedRunbookId, setSelectedRunbookId] = useState('');
  // @ts-ignore
  const [activeWorkflow, setActiveWorkflow] = useState<{ workflow_id: string } | null>(null);

  /* ── Simulation state ── */
  const [isSimulating, setIsSimulating] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  /* ── Registry skills ── */
  const [skills, setSkills] = useState({
    catalogEnrichment: true,
    semanticIndex: true,
    autocompleteTuning: true,
    mxpGovernance: true,
    multimodalQa: false,
  });

  /* ── Policy thresholds ── */
  const [ndcgFloor, setNdcgFloor] = useState('0.84');
  const [latencyCeiling, setLatencyCeiling] = useState('150ms');
  const [canaryTraffic, setCanaryTraffic] = useState('5%');

  /* ── Metrics (derived from live runbook values) ── */
  const totalQueryVolume = runbooks.reduce((sum, r) => sum + r.liveMetrics.queryVolume, 0) || 1;
  const metrics = {
    ndcg:
      runbooks.reduce((sum, r) => {
        const progress = getRunbookProgress(r.status);
        const currentNdcg =
          r.liveMetrics.baselineNdcg +
          (r.liveMetrics.proposedNdcg - r.liveMetrics.baselineNdcg) * progress;
        return sum + currentNdcg * r.liveMetrics.queryVolume;
      }, 0) / totalQueryVolume,
    zeroResultRate:
      runbooks.reduce((sum, r) => {
        const progress = getRunbookProgress(r.status);
        const currentExitRate = r.liveMetrics.exitRate * (1 - (r.businessImpact / 100) * progress);
        return sum + currentExitRate * r.liveMetrics.queryVolume;
      }, 0) / totalQueryVolume,
    latency: Math.round(
      runbooks.reduce((sum, r) => sum + r.liveMetrics.p95Latency * r.liveMetrics.queryVolume, 0) /
        totalQueryVolume
    ),
    completedRunbooks: runbooks.filter(
      (r) => r.status === 'Released' || r.status === 'Rolled Back'
    ).length,
  };

  /* ── Audit history ── */
  const [auditHistory, setAuditHistory] = useState<AuditRow[]>([]);
  const [queryClusters, setQueryClusters] = useState<QueryClusterRow[]>([]);
  const [backendStatus, setBackendStatus] = useState<'loading' | 'connected' | 'offline'>('loading');
  const [temporalDetails, setTemporalDetails] = useState<TemporalDetails | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timerId: NodeJS.Timeout;

    const loadBackendData = async () => {
      try {
        const [backendRunbooks, backendAudit, backendClusters, backendTemporal] = await Promise.all([
          api.getRunbooks(),
          api.getAudit(),
          api.getQueryClusters(),
          api.getTemporalDetails(),
        ]);

        if (cancelled) return;

        setRunbooks(backendRunbooks);
        setSelectedRunbookId((currentId) => {
          if (backendRunbooks.length === 0) return '';
          const stillExists = backendRunbooks.some((runbook) => runbook.id === currentId);
          return stillExists ? currentId : backendRunbooks[0].id;
        });

        setAuditHistory(backendAudit);
        setQueryClusters(backendClusters);
        setTemporalDetails(backendTemporal);
        setBackendStatus('connected');
      } catch (error) {
        if (!cancelled) setBackendStatus('offline');
        console.warn('FastAPI data load failed; no local mock fallback is used.', error);
      }
    };

    // Initial load
    loadBackendData();

    // Start background synchronization polling loop every 4 seconds to sync runbooks, audits and active workflows
    const startPolling = () => {
      timerId = setTimeout(async () => {
        await loadBackendData();
        if (!cancelled) {
          startPolling();
        }
      }, 4000);
    };
    startPolling();

    return () => {
      cancelled = true;
      clearTimeout(timerId);
    };
  }, []);

  const handleActionTriggered = useCallback(
    (action: string) => {
      const selected = runbooks.find((r) => r.id === selectedRunbookId);
      if (!selected) return;
      const now = new Date().toLocaleTimeString();
      const hashSuffix = Math.random().toString(36).substring(2, 10);

      let auditAction = '';
      let approver = 'system:auto-approve';
      let isRollback = false;
      let recordType: AuditRow['recordType'] = 'monitoring';
      let approvalGate = selected.humanApproval.record;

      switch (action) {
        case 'evaluate_pass':
          auditAction = 'Offline eval passed → Shadow test queued';
          approver = selected.humanApproval.mode === 'required'
            ? `pending:${selected.humanApproval.owner}`
            : 'system:auto-approve';
          approvalGate = selected.humanApproval.mode === 'required'
            ? `Human approval required before production canary: ${selected.humanApproval.owner}`
            : `Approval not requested: ${selected.humanApproval.reason}`;
          recordType = 'evaluation';
          break;
        case 'evaluate_block':
          auditAction = 'Offline eval blocked — NDCG below policy floor';
          approver = 'BLOCKED (manual override required)';
          approvalGate = `Manual override required: ${selected.humanApproval.owner}`;
          recordType = 'evaluation';
          break;
        case 'human_approval_recorded':
          auditAction = 'Human approval recorded → Canary gate unlocked';
          approver = `operator:${selected.humanApproval.owner}`;
          approvalGate = `Signed approval saved for ${selected.humanApproval.owner}`;
          recordType = 'approval';
          break;
        case 'release_success':
          auditAction = 'Canary promoted to 100% → Released';
          approver = 'system:temporal-workflow';
          approvalGate = selected.humanApproval.mode === 'required'
            ? `Manual approval satisfied: ${selected.humanApproval.owner}`
            : `Approval not requested: ${selected.humanApproval.reason}`;
          recordType = 'release';
          break;
        case 'rollback':
          auditAction = 'Emergency rollback → Adaptors reset to baseline';
          approver = 'operator:manual-override';
          isRollback = true;
          approvalGate = 'Manual override permitted for emergency rollback.';
          recordType = 'rollback';
          break;
        default:
          auditAction = action;
      }

      const monitoringSummary = selected.monitoringSignals
        .map((signal) => `${signal.label}: ${signal.value} (${signal.status})`)
        .join('; ');

      setAuditHistory((prev) => [
        {
          time: now,
          runbookId: selected.id,
          title: selected.title,
          action: auditAction,
          approver,
          agentName: selected.agent.name,
          agentBehavior: selected.agent.behaviors[0],
          temporalWorkflowId: selected.temporal.workflowId,
          approvalGate,
          monitoringSummary,
          feedbackRecord: selected.feedbackLoop,
          recordType,
          hash: `sha256:${hashSuffix}`,
          isRollback,
        },
        ...prev,
      ]);
    },
    [runbooks, selectedRunbookId]
  );

  const openIncidentsCount = runbooks.filter(
    (r) => r.status !== 'Released' && r.status !== 'Rolled Back'
  ).length;

  const meta = tabMeta[currentTab] || tabMeta.overview;

  /* ── Render the active view ── */
  const renderView = () => {
    switch (currentTab) {
      case 'overview':
        return (
          <Overview
            metrics={metrics}
            runbooks={runbooks}
            auditCount={auditHistory.length}
            queryClusterCount={queryClusters.length}
            backendStatus={backendStatus}
            apiBaseUrl={API_BASE_URL}
            temporalDetails={temporalDetails}
            onNavigateToQueue={() => setCurrentTab('queue')}
          />
        );
      case 'factory':
        return <OpsFactory />;
      case 'queue':
        return (
          <Console
            runbooks={runbooks}
            setRunbooks={setRunbooks}
            selectedRunbookId={selectedRunbookId}
            setSelectedRunbookId={setSelectedRunbookId}
            isSimulating={isSimulating}
            setIsSimulating={setIsSimulating}
            logs={logs}
            setLogs={setLogs}
            ndcgFloor={ndcgFloor}
            canaryTraffic={canaryTraffic}
            onActionTriggered={handleActionTriggered}
            skills={skills}
            appBackendStatus={backendStatus}
            apiBaseUrl={API_BASE_URL}
          />
        );
      case 'registry':
        return (
          <Registry
            skills={skills}
            setSkills={setSkills}
            ndcgFloor={ndcgFloor}
            setNdcgFloor={setNdcgFloor}
            latencyCeiling={latencyCeiling}
            setLatencyCeiling={setLatencyCeiling}
            canaryTraffic={canaryTraffic}
            setCanaryTraffic={setCanaryTraffic}
          />
        );
      case 'clusters':
        return <QueryClusters clusters={queryClusters} />;
      case 'audit':
        return <AuditTrail history={auditHistory} />;
      case 'live-test':
        return <LiveTest setCurrentTab={setCurrentTab} />;
      case 'shadow-reports':
        return <ShadowTestReport />;
      default:
        return null;
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('magellan_auth_user');
    setCurrentUser(null);
    setShowLogoutConfirm(false);
  };

  const handleNotificationClick = (runbookId: string) => {
    setSelectedRunbookId(runbookId);
    setCurrentTab('queue');
    setShowNotifications(false);
  };

  if (!currentUser) {
    return <LocalAdminAuth onLoginSuccess={(username) => setCurrentUser(username)} />;
  }

  const activeIncidents = runbooks.filter(
    (r) => r.status !== 'Released' && r.status !== 'Rolled Back'
  );

  return (
    <div className="app-container">
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        openIncidentsCount={openIncidentsCount}
        backendStatus={backendStatus}
        temporalConnected={temporalDetails?.backend_connected ?? false}
      />

      <main className="content-area">
        {/* Header bar */}
        <div className="content-header" style={{ position: 'relative', zIndex: 100 }}>
          <div className="header-title">
            <h1>{meta.title}</h1>
            <p>{meta.subtitle}</p>
          </div>
          <div className="header-actions" style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            
            {/* Button 1: Notifications (Bell) */}
            <div style={{ position: 'relative' }}>
              <button 
                className="header-icon-btn" 
                type="button" 
                aria-label="Notifications"
                onClick={() => {
                  setShowNotifications(!showNotifications);
                  setShowProfile(false);
                  setShowLogoutConfirm(false);
                }}
                style={{ borderColor: showNotifications ? 'var(--primary)' : 'var(--border-color)', background: showNotifications ? 'rgba(255,255,255,0.95)' : 'rgba(255,255,255,0.72)' }}
              >
                <Bell size={18} />
                {openIncidentsCount > 0 && (
                  <span className="header-notification-dot" />
                )}
              </button>

              {/* Notifications Dropdown card */}
              {showNotifications && (
                <div style={{
                  position: 'absolute',
                  top: '110%',
                  right: 0,
                  width: '320px',
                  background: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(20px)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '12px',
                  boxShadow: '0 12px 28px rgba(30, 41, 59, 0.15)',
                  padding: '1rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  animation: 'viewFadeIn 0.2s ease-out',
                  zIndex: 200
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                    <strong style={{ fontSize: '0.82rem', color: 'var(--text-dark)' }}>Active Incidents ({openIncidentsCount})</strong>
                    {openIncidentsCount > 0 && (
                      <span style={{ fontSize: '0.65rem', background: 'rgba(139, 58, 43, 0.1)', color: 'var(--primary)', padding: '0.15rem 0.45rem', borderRadius: '99px', fontWeight: 'bold' }}>Alerts</span>
                    )}
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '240px', overflowY: 'auto' }}>
                    {activeIncidents.length === 0 ? (
                      <div style={{ padding: '1rem 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                        🎉 Zero unresolved incidents active.
                      </div>
                    ) : (
                      activeIncidents.map((r) => (
                        <button
                          key={r.id}
                          type="button"
                          onClick={() => handleNotificationClick(r.id)}
                          style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'flex-start',
                            gap: '0.15rem',
                            padding: '0.5rem 0.75rem',
                            background: 'rgba(0,0,0,0.02)',
                            border: '1px solid transparent',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            textAlign: 'left',
                            width: '100%',
                            transition: 'all 0.15s ease'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.borderColor = 'var(--primary)';
                            e.currentTarget.style.background = 'white';
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.borderColor = 'transparent';
                            e.currentTarget.style.background = 'rgba(0,0,0,0.02)';
                          }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                            <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--text-dark)', maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.title}</span>
                            <span style={{ fontSize: '0.6rem', color: '#B98218', background: 'rgba(185, 130, 24, 0.1)', padding: '0.1rem 0.35rem', borderRadius: '4px', textTransform: 'uppercase', fontWeight: 'bold' }}>{r.status}</span>
                          </div>
                          <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Capability: {r.capability}</span>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Button 2: Logout (LogOut square arrow) */}
            <div style={{ position: 'relative' }}>
              <button 
                className="header-icon-btn" 
                type="button" 
                aria-label="Settings" 
                onClick={() => {
                  setShowLogoutConfirm(!showLogoutConfirm);
                  setShowNotifications(false);
                  setShowProfile(false);
                }} 
                title="Log Out Session" 
                style={{ color: 'var(--error)', borderColor: showLogoutConfirm ? 'var(--error)' : 'var(--border-color)', background: showLogoutConfirm ? 'rgba(182,66,59,0.05)' : 'rgba(255,255,255,0.72)' }}
              >
                <LogOut size={18} />
              </button>

              {/* Logout Confirm Popover */}
              {showLogoutConfirm && (
                <div style={{
                  position: 'absolute',
                  top: '110%',
                  right: 0,
                  width: '200px',
                  background: 'white',
                  border: '1px solid rgba(182, 66, 59, 0.2)',
                  borderRadius: '10px',
                  boxShadow: '0 8px 24px rgba(182, 66, 59, 0.12)',
                  padding: '0.85rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.65rem',
                  animation: 'viewFadeIn 0.15s ease-out',
                  zIndex: 200
                }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--text-dark)', textAlign: 'center', display: 'block' }}>Confirm Log Out?</span>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      type="button"
                      onClick={() => setShowLogoutConfirm(false)}
                      style={{
                        flex: 1,
                        background: '#FAFAFA',
                        border: '1px solid var(--border-color)',
                        borderRadius: '6px',
                        fontSize: '0.7rem',
                        fontWeight: '600',
                        padding: '0.35rem',
                        cursor: 'pointer'
                      }}
                    >
                      No
                    </button>
                    <button
                      type="button"
                      onClick={handleLogout}
                      style={{
                        flex: 1,
                        background: 'var(--error)',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '0.7rem',
                        fontWeight: 'bold',
                        padding: '0.35rem',
                        cursor: 'pointer'
                      }}
                    >
                      Yes, Exit
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Button 3: User Avatar (Profile summary card toggler) */}
            <div style={{ position: 'relative' }}>
              <div 
                className="header-avatar" 
                title="Logged in as Admin Operator"
                onClick={() => {
                  setShowProfile(!showProfile);
                  setShowNotifications(false);
                  setShowLogoutConfirm(false);
                }}
                style={{
                  cursor: 'pointer',
                  border: showProfile ? '2px solid var(--primary-light)' : 'none',
                  boxShadow: showProfile ? '0 0 12px rgba(224,169,40,0.3)' : 'none'
                }}
              >
                <User size={16} />
              </div>

              {/* Operator Profile Card Popover */}
              {showProfile && (
                <div style={{
                  position: 'absolute',
                  top: '120%',
                  right: 0,
                  width: '240px',
                  background: 'rgba(255, 255, 255, 0.95)',
                  backdropFilter: 'blur(20px)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '12px',
                  boxShadow: '0 12px 28px rgba(30, 41, 59, 0.15)',
                  padding: '1rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.75rem',
                  animation: 'viewFadeIn 0.2s ease-out',
                  zIndex: 200
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.6rem' }}>
                    <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'linear-gradient(135deg, #8B3A2B, #E0A928)', display: 'flex', alignItems: 'center', color: 'white', fontWeight: 'bold', fontSize: '0.8rem', justifyContent: 'center' }}>
                      A
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: 'var(--text-dark)' }}>Admin Operator</span>
                      <span style={{ fontSize: '0.62rem', color: 'var(--text-muted)' }}>Role: Search-Ops Lead</span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem', fontSize: '0.7rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Node Level:</span>
                      <strong style={{ color: 'var(--text-dark)' }}>Superuser (root)</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Subsystem:</span>
                      <strong style={{ color: 'var(--text-dark)' }}>Sandbox Dev Loop</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--text-muted)' }}>Security Token:</span>
                      <strong style={{ color: 'var(--info-light)', fontFamily: 'var(--mono)' }}>SSL ACTIVE</strong>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={handleLogout}
                    style={{
                      width: '100%',
                      background: 'rgba(182, 66, 59, 0.08)',
                      color: 'var(--error)',
                      border: '1px solid rgba(182, 66, 59, 0.15)',
                      borderRadius: '8px',
                      fontSize: '0.7rem',
                      fontWeight: 'bold',
                      padding: '0.45rem',
                      cursor: 'pointer',
                      textAlign: 'center',
                      transition: 'all 0.15s ease'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'var(--error)';
                      e.currentTarget.style.color = 'white';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'rgba(182, 66, 59, 0.08)';
                      e.currentTarget.style.color = 'var(--error)';
                    }}
                  >
                    Terminate Session
                  </button>
                </div>
              )}
            </div>

          </div>
        </div>

        {/* Active View */}
        {renderView()}
      </main>
    </div>
  );
};

export default App;
