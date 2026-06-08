import React, { useEffect, useState } from 'react';
import { Database, ExternalLink, RefreshCw, Server, ShieldCheck } from 'lucide-react';
import { api, API_BASE_URL, type BackendRoot, type HealthStatus, type TemporalDetails } from '../api';
import type { AuditRow, QueryClusterRow, Runbook } from '../types';

interface BackendSnapshot {
  root: BackendRoot;
  health: HealthStatus;
  temporal: TemporalDetails;
  runbooks: Runbook[];
  audit: AuditRow[];
  clusters: QueryClusterRow[];
}

export const BackendDetails: React.FC = () => {
  const [snapshot, setSnapshot] = useState<BackendSnapshot | null>(null);
  const [status, setStatus] = useState<'loading' | 'connected' | 'offline'>('loading');
  const [error, setError] = useState<string>('');

  const loadBackendSnapshot = async () => {
    setStatus('loading');
    setError('');

    try {
      const [root, health, temporal, runbooks, audit, clusters] = await Promise.all([
        api.getRoot(),
        api.getHealth(),
        api.getTemporalDetails(),
        api.getRunbooks(),
        api.getAudit(),
        api.getQueryClusters(),
      ]);

      setSnapshot({ root, health, temporal, runbooks, audit, clusters });
      setStatus('connected');
    } catch (err) {
      setSnapshot(null);
      setStatus('offline');
      setError(err instanceof Error ? err.message : 'Backend request failed.');
    }
  };

  useEffect(() => {
    loadBackendSnapshot();
  }, []);

  const temporalUrl = snapshot?.temporal.workflows_url ?? 'http://localhost:8233/namespaces/default/workflows';

  return (
    <div className="backend-page">
      <div className={`backend-hero ${status}`}>
        <div>
          <span className="backend-eyebrow">FastAPI integration</span>
          <h2>{snapshot?.root.service ?? 'Magellan AI Search Ops Backend'}</h2>
          <p>
            This page shows the backend data currently visible to the frontend: service status,
            CORS origins, Temporal workflow configuration, API routes, runbooks, audit rows, and query clusters.
            Frontend API base URL: <strong>{API_BASE_URL}</strong>.
          </p>
        </div>
        <button className="btn btn-secondary backend-refresh" type="button" onClick={loadBackendSnapshot}>
          <RefreshCw size={14} />
          Refresh backend data
        </button>
      </div>

      {status === 'offline' && (
        <div className="alert-banner error">
          <div className="alert-banner-text">
            <strong>Backend not reachable.</strong> Start FastAPI with `python3 run_fastapi.py`.
            {error && <span> Error: {error}</span>}
          </div>
        </div>
      )}

      <div className="backend-summary-grid">
        <div className="backend-summary-card">
          <Server size={18} />
          <span>Frontend API base</span>
          <strong style={{ fontSize: '0.9rem', overflowWrap: 'anywhere' }}>{API_BASE_URL}</strong>
        </div>
        <div className="backend-summary-card">
          <Server size={18} />
          <span>Backend status</span>
          <strong>{status === 'connected' ? snapshot?.health.status : status}</strong>
        </div>
        <div className="backend-summary-card">
          <ShieldCheck size={18} />
          <span>CORS origins</span>
          <strong>{snapshot?.temporal.cors_origins.length ?? 0}</strong>
        </div>
        <div className="backend-summary-card">
          <Database size={18} />
          <span>Runbooks</span>
          <strong>{snapshot?.runbooks.length ?? 0}</strong>
        </div>
        <div className="backend-summary-card">
          <Database size={18} />
          <span>Audit rows</span>
          <strong>{snapshot?.audit.length ?? 0}</strong>
        </div>
      </div>

      <div className="backend-grid">
        <section className="card backend-card">
          <div className="card-header">
            <h3>Backend Endpoints</h3>
          </div>
          <div className="backend-kv-list">
            {Object.entries(snapshot?.root.endpoints ?? {}).map(([label, path]) => (
              <div key={label} className="backend-kv-row">
                <span>{label.replace(/_/g, ' ')}</span>
                <strong>{api.url(path)}</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="card backend-card">
          <div className="card-header">
            <h3>Configured Data Sources</h3>
          </div>
          <div className="backend-kv-list">
            {Object.entries(snapshot?.root.data_sources ?? {}).map(([label, source]) => (
              <div key={label} className="backend-kv-row">
                <span>{label.replace(/_/g, ' ')}</span>
                <strong>{source.configured ? source.url : 'not configured'}</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="card backend-card">
          <div className="card-header">
            <h3>Temporal Details</h3>
            <a className="btn btn-secondary backend-open-link" href={api.url('/api/temporal/workflows')} target="_blank" rel="noreferrer">
              <ExternalLink size={13} />
              Open
            </a>
          </div>
          <div className="backend-kv-list">
            <div className="backend-kv-row">
              <span>Namespace</span>
              <strong>{snapshot?.temporal.namespace ?? 'default'}</strong>
            </div>
            <div className="backend-kv-row">
              <span>Temporal Web URL</span>
              <strong>{temporalUrl}</strong>
            </div>
            <div className="backend-kv-row">
              <span>Redirect Endpoint</span>
              <strong>{api.url(snapshot?.temporal.redirect_endpoint ?? '/api/temporal/workflows')}</strong>
            </div>
            <div className="backend-kv-row">
              <span>Workflow Count</span>
              <strong>{snapshot?.temporal.workflow_count ?? 0}</strong>
            </div>
            <div className="backend-kv-row">
              <span>CORS Origins</span>
              <strong>{snapshot?.temporal.cors_origins.join(', ') ?? 'not loaded'}</strong>
            </div>
          </div>
        </section>
      </div>

      <section className="card backend-card">
        <div className="card-header">
          <h3>Temporal Workflows Returned By Backend</h3>
        </div>
        <div className="backend-table-wrap">
          <table className="cluster-table">
            <thead>
              <tr>
                <th>Runbook</th>
                <th>Workflow ID</th>
                <th>Status</th>
                <th>SLA</th>
                <th>Cadence</th>
                <th>Checkpoints</th>
              </tr>
            </thead>
            <tbody>
              {(snapshot?.temporal.workflows ?? []).map((workflow) => (
                <tr key={workflow.workflow_id}>
                  <td className="cluster-query">{workflow.runbook_id}</td>
                  <td className="cluster-volume">{workflow.workflow_id}</td>
                  <td>{workflow.status}</td>
                  <td>{workflow.sla}</td>
                  <td>{workflow.cadence}</td>
                  <td>{workflow.checkpoints.join(' -> ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="backend-grid">
        <section className="card backend-card">
          <div className="card-header">
            <h3>Runbook Data From Backend</h3>
          </div>
          <div className="backend-record-list">
            {(snapshot?.runbooks ?? []).map((runbook) => (
              <div key={runbook.id} className="backend-record">
                <strong>{runbook.id} · {runbook.title}</strong>
                <span>{runbook.agent.name} · {runbook.status} · {runbook.temporal.workflowId}</span>
              </div>
            ))}
          </div>
        </section>

        <section className="card backend-card">
          <div className="card-header">
            <h3>Audit And Query Cluster Data</h3>
          </div>
          <div className="backend-record-list">
            <div className="backend-record">
              <strong>Audit rows</strong>
              <span>{snapshot?.audit.map((row) => `${row.runbookId}: ${row.action}`).join(' | ') || 'not loaded'}</span>
            </div>
            <div className="backend-record">
              <strong>Query clusters</strong>
              <span>{snapshot?.clusters.map((cluster) => `${cluster.query} (${cluster.exits})`).join(' | ') || 'not loaded'}</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};
