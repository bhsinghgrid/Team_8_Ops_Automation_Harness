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

/* ── Runbook seed data (the 3 active incidents) ── */
// Explicitly typed to avoid TypeScript narrowing the status union from literal initial values
const initialRunbooks: Runbook[] = [
  {
    id: 'ops-4f72',
    title: 'Catalog Enrichment — "Waterproof" Attribute Gap',
    description:
      'AI Search fails to surface waterproof trail shoes because the catalog lacks a structured "waterproof" attribute. Embedding drift compounds missed synonym expansions.',
    visualCode: 'CE',
    capability: 'semantic search' as const,
    signalType: 'catalog gap' as const,
    risk: 'high' as const,
    confidence: 91,
    tags: ['catalog-enrichment-qa', 'semantic-search'],
    status: 'Eval Ready' as const,
    offlineEvalCoverage: 91,
    businessImpact: 78,
    approvalPolicy: 'Auto-approve if NDCG ≥ 0.84',
    evidenceNotes:
      'Magellan detects 18% search-exit rate on the query cluster "waterproof trail shoes." Root cause: missing structured attribute in product taxonomy. AI suggests adding a boolean waterproof facet and re-indexing the vector store.',
    agent: {
      name: 'Catalog Optimization Agent',
      role: 'Diagnoses missing catalog attributes and proposes index-safe enrichment patches.',
      autonomyLevel: 'Autonomous evaluation and canary release when all policy gates pass.',
      behaviors: [
        'Clusters failed queries against product taxonomy gaps.',
        'Generates facet and synonym patch candidates with bounded schema changes.',
        'Blocks release when NDCG, latency, or inventory coverage gates fail.',
      ],
      decisionRecord:
        'Stores structured rationale, evidence IDs, policy checks, and recommendation outcome. Private chain-of-thought is not stored.',
    },
    temporal: {
      workflowId: 'temporal/catalog-gap/ops-4f72',
      cadence: 'Triggered when exit-rate cluster exceeds 1,000 failed sessions/day.',
      retryPolicy: 'Retry enrichment, eval, and shadow tasks up to 3 times with exponential backoff.',
      sla: '30 minute eval SLA; page owner only if quality or latency gates fail.',
      checkpoints: [
        'Evidence capture',
        'Schema patch draft',
        'Offline relevance eval',
        'Shadow traffic replay',
        'Canary telemetry monitor',
      ],
    },
    humanApproval: {
      mode: 'auto',
      owner: 'Search relevance lead on exception',
      status: 'Not required',
      reason: 'Policy allows automation when NDCG >= floor and monitoring checks stay healthy.',
      expiry: 'Exception review within 4 business hours if triggered.',
      record: 'No human approval requested unless an eval or canary guardrail fails.',
    },
    monitoringSignals: [
      { label: 'NDCG delta', value: '+0.31', status: 'healthy', detail: 'Expected relevance lift clears policy floor.' },
      { label: 'P95 latency', value: '118ms', status: 'healthy', detail: 'Below global 150ms ceiling.' },
      { label: 'Zero-result exits', value: '-18%', status: 'watch', detail: 'Watched during canary for waterproof query cluster.' },
    ],
    feedbackLoop:
      'Post-release clicks, add-to-cart rate, and exit deltas are fed back into the taxonomy gap detector for 7-day drift review.',
    liveMetrics: {
      queryVolume: 12800,
      exitRate: 18,
      revenueLoss: 4200,
      baselineNdcg: 0.6,
      proposedNdcg: 0.91,
      p95Latency: 118,
    },
    accent: '#8B3A2B',
    accentGlow: 'rgba(139,58,43,0.12)',
    accentBorder: 'rgba(139,58,43,0.25)',
    beforeQuery: 'waterproof trail shoes',
    beforeResults: [
      { name: 'Trail Runner X1', price: 89, stock: 4, score: '0.41' },
      { name: 'Summer Sandal Pro', price: 32, stock: 18, score: '0.38' },
      { name: 'Office Loafer Classic', price: 65, stock: 11, score: '0.22' },
    ],
    afterResults: [
      { name: 'AquaShield GTX Boot', price: 149, stock: 22, score: '0.94' },
      { name: 'StormProof Trail Pro', price: 119, stock: 15, score: '0.91' },
      { name: 'RainGuard Hiker', price: 99, stock: 8, score: '0.88' },
    ],
  },
  {
    id: 'ops-1a88',
    title: 'Autocomplete Exits — "Hydration Pack" Typo Cluster',
    description:
      'Smart autocomplete fails on user typos like "hydra p" and "hydra pack". The synonym graph lacks phonetic fuzzy matches for hydration-related queries.',
    visualCode: 'AC',
    capability: 'smart autocomplete' as const,
    signalType: 'zero-result cluster' as const,
    risk: 'med' as const,
    confidence: 86,
    tags: ['autocomplete-tuning', 'synonym-gap'],
    status: 'Eval Ready' as const,
    offlineEvalCoverage: 86,
    businessImpact: 62,
    approvalPolicy: 'Auto-approve if NDCG ≥ 0.84',
    evidenceNotes:
      'Magellan clusters 5,400 monthly queries around "hydra p / hydra pack" with a 32% exit rate. No synonym mapping exists for these typos. Autocomplete Agent recommends phonetic fuzzy-match rules.',
    agent: {
      name: 'Smart Autocomplete Agent',
      role: 'Finds failed prefixes, typo clusters, and missing synonym expansions.',
      autonomyLevel: 'Autonomous rule proposal with conditional approval for high-volume prefix rewrites.',
      behaviors: [
        'Compares prefix failures with successful downstream product clicks.',
        'Builds phonetic and slang synonym candidates with rollback-safe rule IDs.',
        'Escalates if a rewrite affects protected brand or compliance terms.',
      ],
      decisionRecord:
        'Stores detected prefix cluster, generated rule IDs, confidence score, and release decision. Private chain-of-thought is not stored.',
    },
    temporal: {
      workflowId: 'temporal/autocomplete-tuning/ops-1a88',
      cadence: 'Runs hourly against failed-prefix logs and queued zero-result clusters.',
      retryPolicy: 'Retry prefix replay and latency tests twice; hold queue after repeated misses.',
      sla: '15 minute tuning SLA; route to owner if affected query volume crosses 10k/month.',
      checkpoints: [
        'Prefix cluster intake',
        'Synonym candidate generation',
        'Offline replay',
        'Shadow suggest API',
        'Canary conversion monitor',
      ],
    },
    humanApproval: {
      mode: 'conditional',
      owner: 'Search experience owner',
      status: 'Not required',
      reason: 'Automation allowed unless protected terms or excessive rewrite scope are detected.',
      expiry: 'Conditional review due within 2 business hours if triggered.',
      record: 'Approval-not-needed record is saved when protected-term checks pass.',
    },
    monitoringSignals: [
      { label: 'Prefix recall', value: '+42%', status: 'healthy', detail: 'Hydration pack variants now map to expected product family.' },
      { label: 'Suggest latency', value: '91ms', status: 'healthy', detail: 'Autocomplete stays under latency ceiling.' },
      { label: 'Rewrite scope', value: '3 rules', status: 'watch', detail: 'Limited rollout monitors accidental broad matches.' },
    ],
    feedbackLoop:
      'Accepted suggestions, abandoned prefixes, and downstream conversion deltas update the typo-cluster model after each canary window.',
    liveMetrics: {
      queryVolume: 5400,
      exitRate: 32,
      revenueLoss: 2100,
      baselineNdcg: 0.54,
      proposedNdcg: 0.86,
      p95Latency: 91,
    },
    accent: '#1F6B77',
    accentGlow: 'rgba(31,107,119,0.12)',
    accentBorder: 'rgba(31,107,119,0.25)',
    beforeQuery: 'hydra pack',
    beforeResults: [
      { name: 'Hydra Skin Cream', price: 12, stock: 40, score: '0.30' },
      { name: 'Dragon Action Figure', price: 19, stock: 7, score: '0.18' },
    ],
    afterResults: [
      { name: 'CamelBak Hydration Pack 3L', price: 79, stock: 34, score: '0.96' },
      { name: 'Osprey Hydration Reservoir', price: 45, stock: 18, score: '0.92' },
      { name: 'TrailSip Hydra-Pack 2L', price: 39, stock: 22, score: '0.89' },
    ],
  },
  {
    id: 'ops-7b19',
    title: 'MXP Merchandising Rule Conflict — Winter Clearance',
    description:
      'A manual merchandising boost for "winter jacket clearance" is pinning stale clearance inventory above higher-converting new arrivals. Conversion rate drops 14%.',
    visualCode: 'MX',
    capability: 'merchandising' as const,
    signalType: 'mxp rule conflict' as const,
    risk: 'high' as const,
    confidence: 88,
    tags: ['mxp-rule-governance', 'merchandising'],
    status: 'Owner Review' as const,
    offlineEvalCoverage: 88,
    businessImpact: 85,
    approvalPolicy: 'Requires search lead manual sign-off',
    evidenceNotes:
      'Magellan detects a manual boost rule pinning out-of-season clearance stock in position 1-3, overriding the ML relevance model. Exit rate is 14% while top competitor pages convert at 6%.',
    agent: {
      name: 'Merchandising Rules Agent',
      role: 'Detects conflicts between manual boosts, inventory health, and relevance models.',
      autonomyLevel: 'Recommend-only until a human search lead signs the override change.',
      behaviors: [
        'Compares pinned inventory against conversion, stock, seasonality, and relevance score.',
        'Suggests boost demotion or expiry changes with rollback snapshots.',
        'Requires owner approval before changing merchandising rules in production.',
      ],
      decisionRecord:
        'Stores the conflict evidence, proposed rule diff, approval signature, and monitoring outcome. Private chain-of-thought is not stored.',
    },
    temporal: {
      workflowId: 'temporal/mxp-governance/ops-7b19',
      cadence: 'Runs every 6 hours and immediately when exit-rate anomaly exceeds threshold.',
      retryPolicy: 'Retry rule snapshot and shadow replay twice; never retry production mutation without approval.',
      sla: 'Manual approval due within 1 business hour for high-risk merchandising conflicts.',
      checkpoints: [
        'Rule conflict capture',
        'Owner approval request',
        'Shadow relevance replay',
        'Canary traffic gate',
        'Rollback snapshot retention',
      ],
    },
    humanApproval: {
      mode: 'required',
      owner: 'Search lead: Priya Menon',
      status: 'Pending',
      reason: 'High-risk merchandising rule change touches promoted inventory and revenue ordering.',
      expiry: 'Approval expires 1 business hour after request.',
      record: 'A signed human approval must be recorded before canary deployment.',
    },
    monitoringSignals: [
      { label: 'Conversion risk', value: '14% drop', status: 'blocked', detail: 'Current rule pins stale inventory above better matches.' },
      { label: 'Inventory health', value: '3 units', status: 'watch', detail: 'Low stock on pinned clearance SKU creates poor landing experience.' },
      { label: 'Rollback snapshot', value: 'v1.0.4', status: 'healthy', detail: 'Baseline rule state is retained for emergency reset.' },
    ],
    feedbackLoop:
      'Post-approval canary feedback compares conversion, exit rate, and SKU availability before promotion beyond 25% traffic.',
    liveMetrics: {
      queryVolume: 9100,
      exitRate: 14,
      revenueLoss: 3500,
      baselineNdcg: 0.63,
      proposedNdcg: 0.88,
      p95Latency: 124,
    },
    accent: '#2F5D50',
    accentGlow: 'rgba(47,93,80,0.12)',
    accentBorder: 'rgba(47,93,80,0.25)',
    beforeQuery: 'winter jacket clearance',
    beforeResults: [
      { name: 'Last Season Parka (Clearance)', price: 45, stock: 3, detail: 'pinned #1 by MXP rule' },
      { name: 'Old Fleece Vest (Clearance)', price: 22, stock: 1, detail: 'pinned #2 by MXP rule' },
    ],
    afterResults: [
      { name: 'Alpine Down Jacket 2025', price: 189, stock: 42, score: '0.93' },
      { name: 'ThermoShell Pro Coat', price: 149, stock: 28, score: '0.90' },
      { name: 'Last Season Parka (Clearance)', price: 45, stock: 3, score: '0.72' },
    ],
  },
];

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
  const [backendStatus, setBackendStatus] = useState<'loading' | 'connected' | 'fallback'>('loading');
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

        if (backendRunbooks.length > 0) {
          setRunbooks(backendRunbooks);
          setSelectedRunbookId((currentId) => {
            const stillExists = backendRunbooks.some((runbook) => runbook.id === currentId);
            return stillExists ? currentId : backendRunbooks[0].id;
          });
        }

        setAuditHistory(backendAudit);
        setQueryClusters(backendClusters);
        setTemporalDetails(backendTemporal);
        setBackendStatus('connected');
      } catch (error) {
        if (!cancelled) setBackendStatus('fallback');
        console.warn('FastAPI data load failed; using local fallback data.', error);
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
