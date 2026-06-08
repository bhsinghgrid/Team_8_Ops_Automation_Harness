import React, { useState, useCallback, useEffect } from 'react';
import type { Runbook, AuditRow, QueryClusterRow } from './types';
import { api, API_BASE_URL, type TemporalDetails } from './api';
import { Sidebar } from './components/Sidebar';
import { Overview } from './components/Overview';
import { Console } from './components/Console';
import { Registry } from './components/Registry';
import { QueryClusters } from './components/QueryClusters';
import { AuditTrail } from './components/AuditTrail';
import { BackendDetails } from './components/BackendDetails';
import { Bell, Settings, User } from 'lucide-react';

/* ── Runbook data is loaded from FastAPI only. ── */
const initialRunbooks: Runbook[] = [];

/* ── Tab title / description mapping ── */
const tabMeta: Record<string, { title: string; subtitle: string }> = {
  overview: {
    title: 'Operations Overview',
    subtitle: 'Real-time health & performance across all AI Search surfaces.',
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
  backend: {
    title: 'Backend Details',
    subtitle: 'FastAPI, CORS, Temporal workflow URLs, endpoint map, and backend payload visibility.',
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
  /* ── Navigation ── */
  const [currentTab, setCurrentTab] = useState('overview');

  /* ── Runbook state ── */
  const [runbooks, setRunbooks] = useState(initialRunbooks);
  const [selectedRunbookId, setSelectedRunbookId] = useState('ops-4f72');

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

    loadBackendData();

    return () => {
      cancelled = true;
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
      case 'backend':
        return <BackendDetails />;
      case 'audit':
        return <AuditTrail history={auditHistory} />;
      default:
        return null;
    }
  };

  return (
    <div className="app-container">
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        openIncidentsCount={openIncidentsCount}
      />

      <main className="content-area">
        {/* Header bar */}
        <div className="content-header">
          <div className="header-title">
            <h1>{meta.title}</h1>
            <p>{meta.subtitle}</p>
          </div>
          <div className="header-actions">
            <button className="header-icon-btn" type="button" aria-label="Notifications">
              <Bell size={18} />
              {openIncidentsCount > 0 && (
                <span className="header-notification-dot" />
              )}
            </button>
            <button className="header-icon-btn" type="button" aria-label="Settings">
              <Settings size={18} />
            </button>
            <div className="header-avatar">
              <User size={16} />
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
