import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  RotateCcw, 
  AlertOctagon,
  UserCheck,
  ExternalLink
} from 'lucide-react';
import type { Runbook } from '../types';
import { api, type RunbookAction, type TemporalDetails } from '../api';


interface ConsoleProps {
  runbooks: Runbook[];
  setRunbooks: React.Dispatch<React.SetStateAction<Runbook[]>>;
  selectedRunbookId: string;
  setSelectedRunbookId: (id: string) => void;
  isSimulating: boolean;
  setIsSimulating: (sim: boolean) => void;
  logs: string[];
  setLogs: React.Dispatch<React.SetStateAction<string[]>>;
  ndcgFloor: string;
  canaryTraffic: string;
  onActionTriggered: (action: string) => void;
  skills: {
    catalogEnrichment: boolean;
    semanticIndex: boolean;
    autocompleteTuning: boolean;
    mxpGovernance: boolean;
    multimodalQa: boolean;
  };
  appBackendStatus: 'loading' | 'connected' | 'fallback';
  apiBaseUrl: string;
}

export const Console: React.FC<ConsoleProps> = ({
  runbooks,
  setRunbooks,
  selectedRunbookId,
  setSelectedRunbookId,
  isSimulating,
  setIsSimulating,
  logs,
  setLogs,
  ndcgFloor,
  canaryTraffic,
  onActionTriggered,
  skills,
  appBackendStatus,
  apiBaseUrl
}) => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [consoleTab, setConsoleTab] = useState<'evidence' | 'governance' | 'preview' | 'logs'>('evidence');
  const [selectedCapabilities, setSelectedCapabilities] = useState<string[]>(['semantic search', 'smart autocomplete', 'merchandising']);
  const [selectedSignalTypes, setSelectedSignalTypes] = useState<string[]>(['catalog gap', 'zero-result cluster', 'mxp rule conflict']);
  const [searchEvents, setSearchEvents] = useState<string[]>([]);
  const [backendStatus, setBackendStatus] = useState<'checking' | 'connected' | 'offline'>('checking');
  const [temporalWorkflowsUrl, setTemporalWorkflowsUrl] = useState(api.url('/api/temporal/workflows'));
  const [temporalDetails, setTemporalDetails] = useState<TemporalDetails | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  useEffect(() => {
    let cancelled = false;

    api.getTemporalDetails()
      .then((details) => {
        if (cancelled) return;
        setTemporalDetails(details);
        setTemporalWorkflowsUrl(api.url(details.redirect_endpoint));
        setBackendStatus('connected');
      })
      .catch(() => {
        if (cancelled) return;
        setTemporalWorkflowsUrl(api.url('/api/temporal/workflows'));
        setBackendStatus('offline');
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const selectedRunbook = runbooks.find(r => r.id === selectedRunbookId) || runbooks[0];

  if (!selectedRunbook) {
    return (
      <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
        <AlertOctagon size={36} style={{ color: 'var(--warning)', marginBottom: '0.75rem' }} />
        <h3 style={{ fontFamily: 'var(--serif)', marginBottom: '0.35rem' }}>No runbooks available</h3>
        <p className="policy-description">
          FastAPI returned no runbook records and no local fallback is available. Check `/api/runbooks`,
          then refresh the frontend.
        </p>
      </div>
    );
  }

  const needsHumanApproval = selectedRunbook.humanApproval.mode === 'required' && selectedRunbook.humanApproval.status !== 'Approved';
  const activeFiltersCount = selectedCapabilities.length + selectedSignalTypes.length;
  const healthySignalsCount = selectedRunbook.monitoringSignals.filter(signal => signal.status === 'healthy').length;
  const watchSignalsCount = selectedRunbook.monitoringSignals.filter(signal => signal.status === 'watch').length;
  const blockedSignalsCount = selectedRunbook.monitoringSignals.filter(signal => signal.status === 'blocked').length;
  const approvalTone = needsHumanApproval ? 'attention' : 'clear';
  const selectedTemporalWorkflow = temporalDetails?.workflows.find(
    (workflow) => workflow.runbook_id === selectedRunbook.id || workflow.workflow_id === selectedRunbook.temporal.workflowId
  );

  const writeSearchEvent = (message: string) => {
    const now = new Date().toLocaleTimeString();
    setSearchEvents(prev => [`[${now}] ${message}`, ...prev].slice(0, 5));
  };

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    if (value.trim().length === 0) {
      writeSearchEvent('Search cleared. Supervisor sees full queue.');
    } else {
      writeSearchEvent(`Operator searched "${value.trim()}".`);
    }
  };

  const handleToggleFilter = (item: string, list: string[], setter: React.Dispatch<React.SetStateAction<string[]>>) => {
    if (list.includes(item)) {
      setter(list.filter(x => x !== item));
    } else {
      setter([...list, item]);
    }
  };

  const filteredRunbooks = runbooks.filter(r => {
    const matchesSearch = r.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          r.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCapability = selectedCapabilities.includes(r.capability);
    const matchesSignalType = selectedSignalTypes.includes(r.signalType);

    // Registry skill toggles
    let isSkillEnabled = true;
    if (r.id === 'ops-4f72' && !skills.catalogEnrichment) isSkillEnabled = false;
    if (r.id === 'ops-1a88' && !skills.autocompleteTuning) isSkillEnabled = false;
    if (r.id === 'ops-7b19' && !skills.mxpGovernance) isSkillEnabled = false;

    return matchesSearch && matchesCapability && matchesSignalType && isSkillEnabled;
  });

  const disabledSkillMatches = runbooks.filter(r => {
    const matchesSearch = searchQuery.trim().length > 0 &&
      (
        r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        r.description.toLowerCase().includes(searchQuery.toLowerCase())
      );

    if (!matchesSearch) return false;
    if (r.id === 'ops-4f72' && !skills.catalogEnrichment) return true;
    if (r.id === 'ops-1a88' && !skills.autocompleteTuning) return true;
    if (r.id === 'ops-7b19' && !skills.mxpGovernance) return true;
    return false;
  });

  const searchError = (() => {
    if (searchQuery.trim().length === 0) return 'No error. Search is idle.';
    if (filteredRunbooks.length > 0) return 'No error. Query matched visible runbooks.';
    if (disabledSkillMatches.length > 0) return 'Matched runbooks are hidden because their automation skill is disabled.';
    if (selectedCapabilities.length === 0 || selectedSignalTypes.length === 0) return 'Filters exclude all runbooks. Restore at least one capability and signal type.';
    return 'No matching runbooks found for this query.';
  })();

  const recordHumanApproval = () => {
    if (selectedRunbook.humanApproval.mode !== 'required' || selectedRunbook.humanApproval.status === 'Approved') return;

    const now = new Date().toLocaleTimeString();
    setConsoleTab('logs');
    setLogs(prev => [
      ...prev,
      `[${now}] [APPROVAL] Human sign-off captured from ${selectedRunbook.humanApproval.owner}.`,
      `[${now}] [RECORD] Approval evidence retained for ${selectedRunbook.temporal.workflowId}.`,
    ]);
    setRunbooks(prev => prev.map(r => (
      r.id === selectedRunbookId
        ? {
            ...r,
            humanApproval: {
              ...r.humanApproval,
              status: 'Approved',
              record: `Signed approval captured from ${r.humanApproval.owner} at ${now}.`,
            },
          }
        : r
    )));
    onActionTriggered('human_approval_recorded');
  };

  const runSimulationFlow = async (type: RunbookAction) => {
    if (isSimulating) return;
    if (type === 'release' && needsHumanApproval) {
      const now = new Date().toLocaleTimeString();
      setConsoleTab('logs');
      setLogs([
        `[${now}] [APPROVAL] Canary deployment blocked. ${selectedRunbook.humanApproval.owner} must approve this high-risk runbook.`,
        `[${now}] [RECORD] Pending approval state retained for ${selectedRunbook.temporal.workflowId}.`,
      ]);
      return;
    }

    setIsSimulating(true);
    setLogs([]);
    setConsoleTab('logs');

    const timestamp = () => `[${new Date().toLocaleTimeString()}] `;

    const addLog = (line: string, delay: number) => {
      return new Promise<void>((resolve) => {
        setTimeout(() => {
          setLogs(prev => [...prev, timestamp() + line]);
          resolve();
        }, delay);
      });
    };

    try {
      const backendResponse = await api.runRunbookAction(selectedRunbook.id, type);
      setBackendStatus('connected');
      await addLog(`[BACKEND] FastAPI accepted ${backendResponse.action}; status=${backendResponse.status}.`, 200);
      await addLog(`[BACKEND] Temporal UI linked: ${backendResponse.temporal_workflows_url}`, 250);
    } catch (error) {
      setBackendStatus('offline');
      const message = error instanceof Error ? error.message : 'unknown backend error';
      await addLog(`[BACKEND] FastAPI unavailable (${message}). Continuing local UI simulation.`, 200);
    }

    if (type === 'evaluate') {
      await addLog(`[INFO] ${selectedRunbook.agent.name} started ${selectedRunbook.temporal.workflowId}.`, 100);
      await addLog(`[INFO] Behavior policy: ${selectedRunbook.agent.behaviors[0]}`, 450);
      await addLog(`[RECORD] ${selectedRunbook.agent.decisionRecord}`, 550);
      await addLog(`[INFO] Temporal checkpoint: ${selectedRunbook.temporal.checkpoints[0]} -> ${selectedRunbook.temporal.checkpoints[2]}.`, 700);
      await addLog(`[INFO] Executing offline relevance metrics simulation...`, 900);
      
      const currentNdcg = selectedRunbook.confidence / 100;
      const policyFloor = parseFloat(ndcgFloor) || 0.84;
      const passed = currentNdcg >= policyFloor;

      if (passed) {
        await addLog(`[SUCCESS] Relevance NDCG: ${currentNdcg.toFixed(2)} meets policy floor of ${policyFloor.toFixed(2)}.`, 1000);
        await addLog(`[INFO] Shadowing traffic to test vector latency and payload bounds...`, 600);
        await addLog(`[SUCCESS] Shadow testing completes cleanly. Ready for canary promotion.`, 800);
        await addLog(`[APPROVAL] ${selectedRunbook.humanApproval.mode === 'required' ? `Human approval pending with ${selectedRunbook.humanApproval.owner}.` : `No human approval requested. ${selectedRunbook.humanApproval.reason}`}`, 550);
        
        setRunbooks(prev => prev.map(r => r.id === selectedRunbookId ? { ...r, status: 'Shadow Test' } : r));
        onActionTriggered('evaluate_pass');
      } else {
        await addLog(`[WARNING] Relevance NDCG: ${currentNdcg.toFixed(2)} falls BELOW required policy floor of ${policyFloor.toFixed(2)}!`, 1000);
        await addLog(`[CAUTION] Runbook blocked from auto-approvals. Operator override signature required.`, 700);
        await addLog(`[RECORD] Manual approval need saved to evidence ledger.`, 400);
        onActionTriggered('evaluate_block');
      }
    } else if (type === 'release') {
      await addLog(`[INFO] Starting Temporal rollout workflow ${selectedRunbook.temporal.workflowId}.`, 100);
      await addLog(`[INFO] Agent owner: ${selectedRunbook.agent.name}. Autonomy: ${selectedRunbook.agent.autonomyLevel}`, 500);
      await addLog(`[INFO] Verifying approval gate and security token validity...`, 600);
      await addLog(`[SUCCESS] Approval gate satisfied: ${selectedRunbook.humanApproval.status}.`, 800);
      await addLog(`[INFO] Applying adaptors to traffic router. Initial Canary Traffic: ${canaryTraffic}...`, 800);
      
      setRunbooks(prev => prev.map(r => r.id === selectedRunbookId ? { ...r, status: 'Canary 5%' } : r));
      await addLog(`[MONITOR] ${selectedRunbook.monitoringSignals[0].label}: ${selectedRunbook.monitoringSignals[0].value} (${selectedRunbook.monitoringSignals[0].status}).`, 800);
      await addLog(`[MONITOR] ${selectedRunbook.monitoringSignals[1].label}: ${selectedRunbook.monitoringSignals[1].value} (${selectedRunbook.monitoringSignals[1].status}).`, 600);
      
      setRunbooks(prev => prev.map(r => r.id === selectedRunbookId ? { ...r, status: 'Canary 25%' } : r));
      await addLog(`[INFO] Healthy signals. Scaling traffic allocation to 25%...`, 1000);
      
      setRunbooks(prev => prev.map(r => r.id === selectedRunbookId ? { ...r, status: 'Canary 100%' } : r));
      await addLog(`[INFO] Telemetry stable. Scaling to 100% production traffic...`, 1000);

      setRunbooks(prev => prev.map(r => r.id === selectedRunbookId ? { ...r, status: 'Released' } : r));
      await addLog(`[RECORD] Feedback loop armed: ${selectedRunbook.feedbackLoop}`, 600);
      await addLog(`[SUCCESS] Change successfully promoted. Release audit evidence logged under hash: e4b2c918a...`, 800);
      onActionTriggered('release_success');
    } else if (type === 'rollback') {
      await addLog(`[CAUTION] Emergency manual rollback command received!`, 100);
      await addLog(`[INFO] ${selectedRunbook.agent.name} preserving evidence and operator override record.`, 550);
      await addLog(`[INFO] Initiating Temporal rollback sequence workflow: rollback_id: rb-${selectedRunbook.id}...`, 700);
      await addLog(`[INFO] Resetting live AI Search adaptors to snapshot version: v1.0.4-baseline...`, 900);
      
      setRunbooks(prev => prev.map(r => r.id === selectedRunbookId ? { ...r, status: 'Rolled Back' } : r));
      await addLog(`[SUCCESS] Adaptors reset successfully. Live endpoints restored to baseline.`, 800);
      onActionTriggered('rollback');
    }
    setIsSimulating(false);
  };

  return (
    <div className="workspace-layout">
      
      {/* Sidebar Filters */}
      <aside className="console-sidebar">
        <div className={`runbook-backend-source ${appBackendStatus}`}>
          <div className="supervisor-title">Backend source</div>
          <div className="supervisor-metric-row">
            <span>Status</span>
            <strong>{appBackendStatus}</strong>
          </div>
          <div className="supervisor-metric-row">
            <span>API base</span>
            <strong>{apiBaseUrl}</strong>
          </div>
          <div className="supervisor-metric-row">
            <span>Runbooks</span>
            <strong>{runbooks.length}</strong>
          </div>
          <div className="supervisor-error ok">
            {appBackendStatus === 'connected'
              ? 'Ops Runbooks are loaded from FastAPI.'
              : appBackendStatus === 'loading'
                ? 'Trying to load FastAPI data.'
                : 'FastAPI not reachable; showing local fallback data.'}
          </div>
        </div>

        <div>
          <div className="filter-group-title">Search logs</div>
          <div className="ui-search-bar" style={{ marginBottom: 0 }}>
            <input 
              type="text" 
              placeholder="Query query..." 
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              style={{ padding: '0.45rem 0.75rem', fontSize: '0.8rem', borderRadius: '6px 0 0 6px' }}
            />
            <button 
              type="button" 
              onClick={() => handleSearchChange('')}
              style={{ padding: '0.45rem 0.85rem', fontSize: '0.8rem', borderRadius: '0 6px 6px 0' }}
            >
              Clear
            </button>
          </div>
        </div>

        <div className="supervisor-search-card">
          <div className="supervisor-title">Supervisor search monitor</div>
          <div className="supervisor-metric-row">
            <span>Visible matches</span>
            <strong>{filteredRunbooks.length}/{runbooks.length}</strong>
          </div>
          <div className="supervisor-metric-row">
            <span>Active filters</span>
            <strong>{activeFiltersCount}</strong>
          </div>
          <div className={`supervisor-error ${filteredRunbooks.length === 0 && searchQuery.trim().length > 0 ? 'warn' : 'ok'}`}>
            {searchError}
          </div>
          <div className="supervisor-event-list">
            {searchEvents.length === 0 ? (
              <span>No search activity yet.</span>
            ) : (
              searchEvents.map((event) => <span key={event}>{event}</span>)
            )}
          </div>
        </div>

        <div>
          <div className="filter-group-title">Capability</div>
          <div 
            className={`filter-option ${selectedCapabilities.includes('semantic search') ? 'selected' : ''}`}
            onClick={() => handleToggleFilter('semantic search', selectedCapabilities, setSelectedCapabilities)}
          >
            <span className="checkbox-mock" />
            <span>Semantic search</span>
            <small>1</small>
          </div>
          <div 
            className={`filter-option ${selectedCapabilities.includes('smart autocomplete') ? 'selected' : ''}`}
            onClick={() => handleToggleFilter('smart autocomplete', selectedCapabilities, setSelectedCapabilities)}
          >
            <span className="checkbox-mock" />
            <span>Smart autocomplete</span>
            <small>1</small>
          </div>
          <div 
            className={`filter-option ${selectedCapabilities.includes('merchandising') ? 'selected' : ''}`}
            onClick={() => handleToggleFilter('merchandising', selectedCapabilities, setSelectedCapabilities)}
          >
            <span className="checkbox-mock" />
            <span>Merchandising</span>
            <small>1</small>
          </div>
        </div>

        <div>
          <div className="filter-group-title">Signal Type</div>
          <div 
            className={`filter-option ${selectedSignalTypes.includes('catalog gap') ? 'selected' : ''}`}
            onClick={() => handleToggleFilter('catalog gap', selectedSignalTypes, setSelectedSignalTypes)}
          >
            <span className="checkbox-mock" />
            <span>Catalog gap</span>
          </div>
          <div 
            className={`filter-option ${selectedSignalTypes.includes('zero-result cluster') ? 'selected' : ''}`}
            onClick={() => handleToggleFilter('zero-result cluster', selectedSignalTypes, setSelectedSignalTypes)}
          >
            <span className="checkbox-mock" />
            <span>Zero-result cluster</span>
          </div>
          <div 
            className={`filter-option ${selectedSignalTypes.includes('mxp rule conflict') ? 'selected' : ''}`}
            onClick={() => handleToggleFilter('mxp rule conflict', selectedSignalTypes, setSelectedSignalTypes)}
          >
            <span className="checkbox-mock" />
            <span>MXP rule conflict</span>
          </div>
        </div>
      </aside>

      {/* Main Incidents List Queue */}
      <div className="console-queue">
        {filteredRunbooks.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            <AlertOctagon size={36} style={{ color: 'var(--text-muted)', marginBottom: '0.75rem' }} />
            <p>No active incidents matched the selected filters.</p>
          </div>
        ) : (
          filteredRunbooks.map((r) => {
            const isSelected = r.id === selectedRunbookId;
            return (
              <article 
                key={r.id} 
                className={`incident-card ${isSelected ? 'active' : ''}`}
                onClick={() => setSelectedRunbookId(r.id)}
              >
                <div 
                  className="badge-code" 
                  style={{ 
                    '--accent': r.accent, 
                    '--accent-glow': r.accentGlow,
                    '--accent-border': r.accentBorder 
                  } as React.CSSProperties}
                >
                  {r.visualCode}
                </div>
                
                <div className="incident-info">
                  <h4>{r.title}</h4>
                  <p>{r.description}</p>
                  <div className="incident-meta-tags">
                    <span>{r.capability}</span>
                    <span>{r.signalType}</span>
                    <span>{r.risk} risk</span>
                    <span>{r.agent?.name ?? 'Unassigned agent'}</span>
                  </div>
                </div>

                <div className="incident-status-cell">
                  <strong>{r.confidence}</strong>
                  <span className="status-indicator">{r.status}</span>
                </div>
              </article>
            );
          })
        )}
      </div>

      {/* Inspector Workspace (Right) */}
      <aside className="console-inspector">
        <div className="inspector-section" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ fontFamily: 'var(--serif)', fontSize: '1.25rem' }}>{selectedRunbook.title}</h3>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>ID: {selectedRunbook.id}</span>
          </div>
          <span 
            className="incident-meta-tags"
            style={{ display: 'inline' }}
          >
            <span style={{ color: 'var(--primary)', border: '1px solid var(--primary-glow)', background: 'var(--primary-glow)' }}>
              {selectedRunbook.status}
            </span>
          </span>
        </div>

        <div className="runbook-glance-grid">
          <div className="glance-card">
            <span>Responsible agent</span>
            <strong>{selectedRunbook.agent.name}</strong>
            <small>{selectedRunbook.capability}</small>
          </div>
          <div className={`glance-card ${approvalTone}`}>
            <span>Approval state</span>
            <strong>{selectedRunbook.humanApproval.status}</strong>
            <small>{selectedRunbook.humanApproval.mode} gate</small>
          </div>
          <div className="glance-card">
            <span>Temporal status</span>
            <strong>{selectedRunbook.status}</strong>
            <small>{selectedRunbook.temporal.sla}</small>
          </div>
          <div className={`glance-card ${blockedSignalsCount > 0 ? 'blocked' : watchSignalsCount > 0 ? 'attention' : 'clear'}`}>
            <span>Monitoring</span>
            <strong>{healthySignalsCount} healthy · {watchSignalsCount} watch</strong>
            <small>{blockedSignalsCount} blocked guardrails</small>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="ui-segmented" style={{ width: '100%' }}>
          <button 
            type="button" 
            className={consoleTab === 'evidence' ? 'active' : ''} 
            onClick={() => setConsoleTab('evidence')}
            style={{ flex: 1 }}
          >
            Why this
          </button>
          <button 
            type="button" 
            className={consoleTab === 'governance' ? 'active' : ''} 
            onClick={() => setConsoleTab('governance')}
            style={{ flex: 1 }}
          >
            Controls
          </button>
          <button 
            type="button" 
            className={consoleTab === 'preview' ? 'active' : ''} 
            onClick={() => setConsoleTab('preview')}
            style={{ flex: 1 }}
          >
            Result Preview
          </button>
          <button 
            type="button" 
            className={consoleTab === 'logs' ? 'active' : ''} 
            onClick={() => setConsoleTab('logs')}
            style={{ flex: 1 }}
          >
            Run Log
          </button>
        </div>

        {/* Console Tab Content */}
        {consoleTab === 'evidence' && (
          <div className="inspector-section" style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div className="inspector-row">
              <strong>Capability classification</strong>
              <span>{selectedRunbook.capability}</span>
            </div>
            
            <div className="inspector-row">
              <strong>Offline eval confidence</strong>
              <div className="inspector-meter">
                <div 
                  className="inspector-meter-fill" 
                  style={{ width: `${selectedRunbook.offlineEvalCoverage}%` }}
                />
              </div>
              <span>{selectedRunbook.offlineEvalCoverage}% metrics match score</span>
            </div>

            <div className="inspector-row">
              <strong>Potential Business Impact</strong>
              <div className="inspector-meter">
                <div 
                  className="inspector-meter-fill" 
                  style={{ width: `${selectedRunbook.businessImpact}%` }}
                />
              </div>
              <span>{selectedRunbook.businessImpact}% exit rate reduction</span>
            </div>

            <div className="inspector-row">
              <strong>Approval Policy</strong>
              <span>{selectedRunbook.approvalPolicy}</span>
            </div>

            <div className="inspector-row">
              <strong>System Evidence Notes</strong>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: '1.45', background: 'var(--body-bg)', padding: '0.55rem', borderRadius: '6px', marginTop: '0.25rem' }}>
                {selectedRunbook.evidenceNotes}
              </p>
            </div>
          </div>
        )}

        {consoleTab === 'governance' && (
          <div className="inspector-section governance-panel">
            <div className="governance-card agent-card">
              <div className="governance-heading">
                <strong>{selectedRunbook.agent.name}</strong>
                <span>{selectedRunbook.agent.autonomyLevel}</span>
              </div>
              <p>{selectedRunbook.agent.role}</p>
              <ul className="behavior-list">
                {selectedRunbook.agent.behaviors.map((behavior) => (
                  <li key={behavior}>{behavior}</li>
                ))}
              </ul>
            </div>

            <div className="governance-card">
              <div className="governance-heading">
                <strong>Temporal workflow</strong>
                <span>{selectedRunbook.temporal.workflowId}</span>
              </div>
              <div className="metadata-grid">
                <div>
                  <span>Namespace</span>
                  <strong>{temporalDetails?.namespace ?? 'default'}</strong>
                </div>
                <div>
                  <span>Backend status</span>
                  <strong>{temporalDetails?.status ?? backendStatus}</strong>
                </div>
                <div>
                  <span>Workflow count</span>
                  <strong>{temporalDetails?.workflow_count ?? runbooks.length}</strong>
                </div>
                <div>
                  <span>Cadence</span>
                  <strong>{selectedTemporalWorkflow?.cadence ?? selectedRunbook.temporal.cadence}</strong>
                </div>
                <div>
                  <span>SLA</span>
                  <strong>{selectedTemporalWorkflow?.sla ?? selectedRunbook.temporal.sla}</strong>
                </div>
                <div>
                  <span>Retry policy</span>
                  <strong>{selectedTemporalWorkflow?.retry_policy ?? selectedRunbook.temporal.retryPolicy}</strong>
                </div>
              </div>
              <div className="temporal-detail-panel">
                <div>
                  <span>Temporal Web</span>
                  <strong>{temporalDetails?.workflows_url ?? 'http://localhost:8233/namespaces/default/workflows'}</strong>
                </div>
                <div>
                  <span>FastAPI redirect</span>
                  <strong>{api.url(temporalDetails?.redirect_endpoint ?? '/api/temporal/workflows')}</strong>
                </div>
                <div>
                  <span>CORS origins</span>
                  <strong>{temporalDetails?.cors_origins.join(', ') ?? 'http://localhost:5173'}</strong>
                </div>
              </div>
              <div className="backend-endpoint-map">
                <div className="endpoint-map-title">Backend API routes shown in this UI</div>
                {Object.entries(temporalDetails?.backend_endpoints ?? {
                  runbooks: '/api/runbooks',
                  audit: '/api/audit',
                  query_clusters: '/api/query-clusters',
                  actions: '/api/runbooks/{runbook_id}/actions/{action}',
                }).map(([name, path]) => (
                  <div key={name} className="endpoint-map-row">
                    <span>{name.replace('_', ' ')}</span>
                    <strong>{api.url(path)}</strong>
                  </div>
                ))}
              </div>
              <div className="checkpoint-list">
                {(selectedTemporalWorkflow?.checkpoints ?? selectedRunbook.temporal.checkpoints).map((checkpoint, index) => (
                  <span key={checkpoint}>{index + 1}. {checkpoint}</span>
                ))}
              </div>
              <a
                className="btn btn-secondary temporal-link"
                href={temporalWorkflowsUrl}
                target="_blank"
                rel="noreferrer"
              >
                <ExternalLink size={13} />
                <span>Open Temporal workflows</span>
              </a>
              <div className={`backend-status ${backendStatus}`}>
                Backend: {backendStatus === 'connected' ? 'FastAPI connected' : backendStatus === 'checking' ? 'checking...' : 'offline'}
              </div>
              {temporalDetails && (
                <div className="temporal-workflow-list">
                  {temporalDetails.workflows.map((workflow) => (
                    <div
                      key={workflow.workflow_id}
                      className={`temporal-workflow-item ${workflow.runbook_id === selectedRunbook.id ? 'active' : ''}`}
                    >
                      <span>{workflow.runbook_id}</span>
                      <strong>{workflow.workflow_id}</strong>
                      <small>{workflow.status}</small>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className={`governance-card approval-card ${selectedRunbook.humanApproval.mode}`}>
              <div className="governance-heading">
                <strong>Human approval gate</strong>
                <span className="approval-status">{selectedRunbook.humanApproval.status}</span>
              </div>
              <p>{selectedRunbook.humanApproval.reason}</p>
              <div className="metadata-grid two-col">
                <div>
                  <span>Owner</span>
                  <strong>{selectedRunbook.humanApproval.owner}</strong>
                </div>
                <div>
                  <span>Expiry</span>
                  <strong>{selectedRunbook.humanApproval.expiry}</strong>
                </div>
              </div>
              <div className="record-box">{selectedRunbook.humanApproval.record}</div>
            </div>

            <div className="governance-card">
              <div className="governance-heading">
                <strong>Monitoring and feedback</strong>
                <span>Canary guardrails</span>
              </div>
              <div className="monitoring-list">
                {selectedRunbook.monitoringSignals.map((signal) => (
                  <div key={signal.label} className={`monitoring-signal ${signal.status}`}>
                    <span>{signal.label}</span>
                    <strong>{signal.value}</strong>
                    <small>{signal.detail}</small>
                  </div>
                ))}
              </div>
              <div className="record-box">{selectedRunbook.feedbackLoop}</div>
            </div>

            <div className="governance-card">
              <div className="governance-heading">
                <strong>Agent rationale record</strong>
                <span>Saved evidence only</span>
              </div>
              <p>{selectedRunbook.agent.decisionRecord}</p>
            </div>
          </div>
        )}

        {consoleTab === 'preview' && (
          <div className="inspector-section" style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
            <div className="inspector-row">
              <strong>Trigger Query cluster:</strong>
              <span style={{ fontFamily: 'var(--mono)', fontSize: '0.78rem', background: 'var(--body-bg)', padding: '0.35rem', borderRadius: '4px' }}>
                "{selectedRunbook.beforeQuery}"
              </span>
            </div>
            
            <div className="two-panel" style={{ gridTemplateColumns: '1fr', gap: '0.75rem', marginTop: 0 }}>
              {/* Baseline */}
              <div style={{ background: '#FEF2F2', padding: '0.65rem', borderRadius: '8px', border: '1px solid #FEE2E2' }}>
                <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', fontFamily: 'var(--mono)', color: 'var(--error)', fontWeight: 700, marginBottom: '0.25rem' }}>
                  Baseline Search Results (NDCG ~0.60)
                </div>
                <ul style={{ listStyle: 'none', paddingLeft: 0, gap: '0.35rem', display: 'flex', flexDirection: 'column' }}>
                  {selectedRunbook.beforeResults.map((p, idx) => (
                    <li key={idx} style={{ fontSize: '0.72rem', display: 'flex', justifyContent: 'space-between', color: '#7f1d1d' }}>
                      <span>{p.name} (Qty: {p.stock})</span>
                      <strong>{p.price}$ {p.score ? `[${p.score}]` : ''}</strong>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Proposed */}
              <div style={{ background: '#ECFDF5', padding: '0.65rem', borderRadius: '8px', border: '1px solid #D1FAE5' }}>
                <div style={{ fontSize: '0.65rem', textTransform: 'uppercase', fontFamily: 'var(--mono)', color: 'var(--success-light)', fontWeight: 700, marginBottom: '0.25rem' }}>
                  Proposed Runbook results (NDCG ~0.90)
                </div>
                <ul style={{ listStyle: 'none', paddingLeft: 0, gap: '0.35rem', display: 'flex', flexDirection: 'column' }}>
                  {selectedRunbook.afterResults.map((p, idx) => (
                    <li key={idx} style={{ fontSize: '0.72rem', display: 'flex', justifyContent: 'space-between', color: '#065f46' }}>
                      <span>{p.name} (Qty: {p.stock})</span>
                      <strong>{p.price}$ {p.score ? `[${p.score}]` : ''}</strong>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {consoleTab === 'logs' && (
          <div className="inspector-section" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div className="sim-console">
              <div className="sim-console-header">Temporal execution logs</div>
              {logs.map((log, index) => {
                let cl = 'sim-line';
                if (log.includes('[SUCCESS]')) cl += ' success';
                if (log.includes('[WARNING]') || log.includes('[CAUTION]')) cl += ' warn';
                if (log.includes('[INFO]') || log.includes('[RECORD]') || log.includes('[MONITOR]') || log.includes('[APPROVAL]')) cl += ' info';
                return (
                  <div key={index} className={cl}>
                    {log}
                  </div>
                );
              })}
              {isSimulating && <div className="sim-line info">Executing Temporal workflow tasks...</div>}
              <div ref={logEndRef} />
            </div>
          </div>
        )}

        {/* Interactive action buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <button 
            className="btn btn-primary"
            disabled={isSimulating || selectedRunbook.status === 'Released'}
            onClick={() => runSimulationFlow('evaluate')}
          >
            <Play size={14} />
            <span>Run Offline Evals</span>
          </button>
          
          <button 
            className="btn btn-secondary"
            disabled={isSimulating || selectedRunbook.status === 'Released' || selectedRunbook.status === 'Eval Ready' || needsHumanApproval}
            onClick={() => runSimulationFlow('release')}
          >
            <span>Deploy Canary</span>
          </button>

          {selectedRunbook.humanApproval.mode === 'required' && (
            <button 
              className="btn btn-secondary"
              disabled={isSimulating || selectedRunbook.humanApproval.status === 'Approved' || selectedRunbook.status === 'Released' || selectedRunbook.status === 'Rolled Back'}
              onClick={recordHumanApproval}
            >
              <UserCheck size={14} />
              <span>{selectedRunbook.humanApproval.status === 'Approved' ? 'Human Approval Recorded' : 'Record Human Approval'}</span>
            </button>
          )}
          
          <button 
            className="btn btn-danger"
            disabled={isSimulating || selectedRunbook.status === 'Rolled Back' || selectedRunbook.status === 'Eval Ready'}
            onClick={() => runSimulationFlow('rollback')}
          >
            <RotateCcw size={14} />
            <span>Emergency Rollback</span>
          </button>
        </div>

      </aside>

    </div>
  );
};
