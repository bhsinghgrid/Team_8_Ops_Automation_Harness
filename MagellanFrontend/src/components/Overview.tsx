import React from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  CheckCircle,
  AlertTriangle,
  Database,
  Workflow
} from 'lucide-react';
import type { Runbook } from '../types';
import type { TemporalDetails } from '../api';

interface OverviewProps {
  metrics: {
    ndcg: number;
    zeroResultRate: number;
    latency: number;
    completedRunbooks: number;
  };
  runbooks: Runbook[];
  auditCount: number;
  queryClusterCount: number;
  backendStatus: 'loading' | 'connected' | 'offline';
  apiBaseUrl: string;
  temporalDetails: TemporalDetails | null;
  onNavigateToQueue: () => void;
}

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

const buildSvgPoints = (values: number[]) => {
  if (values.length === 0) return '';

  const paddingX = 18;
  const topY = 18;
  const height = 84;
  const width = 264;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const spread = max - min || 1;

  return values
    .map((value, index) => {
      const x = values.length === 1 ? 150 : paddingX + (index * width) / (values.length - 1);
      const y = topY + ((max - value) / spread) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');
};

const toPath = (points: string) => {
  const [first, ...rest] = points.split(' ');
  return `M ${first} ${rest.map((point) => `L ${point}`).join(' ')}`;
};

export const Overview: React.FC<OverviewProps> = ({
  metrics,
  runbooks,
  auditCount,
  queryClusterCount,
  backendStatus,
  apiBaseUrl,
  temporalDetails,
  onNavigateToQueue
}) => {
  const trendRows = runbooks.map((runbook) => {
    const progress = getRunbookProgress(runbook.status);
    const currentNdcg =
      runbook.liveMetrics.baselineNdcg +
      (runbook.liveMetrics.proposedNdcg - runbook.liveMetrics.baselineNdcg) * progress;
    const currentExitRate =
      runbook.liveMetrics.exitRate * (1 - (runbook.businessImpact / 100) * progress);

    return {
      id: runbook.id,
      code: runbook.visualCode,
      status: runbook.status,
      title: runbook.title,
      queryVolume: runbook.liveMetrics.queryVolume,
      currentNdcg,
      currentExitRate,
      p95Latency: runbook.liveMetrics.p95Latency,
      rootCause: runbook.rootCause,
      shadowTest: runbook.shadowTest,
    };
  });

  const [selectedShadowTest, setSelectedShadowTest] = React.useState<Runbook['shadowTest'] | null>(null);

  const relevancePoints = buildSvgPoints(trendRows.map((row) => row.currentNdcg * 100));
  const exitHealthPoints = buildSvgPoints(trendRows.map((row) => 100 - row.currentExitRate));
  const latencyHealthPoints = buildSvgPoints(trendRows.map((row) => Math.max(0, 180 - row.p95Latency)));
  const highestRiskRow = [...trendRows].sort((a, b) => b.currentExitRate - a.currentExitRate)[0];
  const hasTrendRows = trendRows.length > 0;
  const isTemporalBackendData = runbooks.some((runbook) => runbook.tags.includes('temporal-backend'));
  const healthLabel = isTemporalBackendData ? 'Workflow Health' : 'Average NDCG';
  const riskLabel = isTemporalBackendData ? 'Workflow Risk Rate' : 'Zero-Result Rate';
  const runtimeLabel = isTemporalBackendData ? 'Runtime Signal' : 'P95 Search Latency';
  const closedLabel = isTemporalBackendData ? 'Closed Workflows' : 'Closed Runbooks';
  const runtimeUnit = isTemporalBackendData ? 's' : 'ms';

  const recentEvents = [
    { type: 'success', time: '09:22:14', text: 'Scoped re-index refresh job complete for catalog-enrichment-qa.' },
    { type: 'warning', time: '08:14:02', text: 'Autocomplete exits trigger alert on query cluster "trail gear".' },
    { type: 'info', time: '07:45:11', text: 'Temporal workflow runbook_id: ops-4f72 approved by search lead.' },
    { type: 'success', time: '06:30:00', text: 'Emergency rollback drill executed successfully. Merchandising conflict resolved.' }
  ];

  return (
    <>
      {selectedShadowTest && (
        <ShadowTestReport
          report={selectedShadowTest}
          onClose={() => setSelectedShadowTest(null)}
        />
      )}
      {/* Alert Banner for pending tasks */}
      <div className="alert-banner">
        <div className="alert-banner-text" style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <AlertTriangle size={18} />
          <span>
            {hasTrendRows ? (
              <>
                <strong>Attention:</strong> {trendRows.length} AI Search anomalies are tracked from live runbook data. Highest current exit risk is <strong>{highestRiskRow?.code ?? 'n/a'}</strong> at <strong>{highestRiskRow?.currentExitRate.toFixed(1) ?? '0.0'}%</strong>.
              </>
            ) : (
              <>
                <strong>No live runbooks loaded.</strong> Configure <code>RUNBOOKS_API_URL</code> in <code>.env</code>, then restart FastAPI.
              </>
            )}
          </span>
        </div>
        <button className="alert-btn" type="button" onClick={onNavigateToQueue}>
          Resolve Now
        </button>
      </div>

      <div className="backend-inline-grid">
        <div className={`backend-inline-card ${backendStatus}`}>
          <Database size={18} />
          <span>Data source</span>
          <strong>{backendStatus === 'connected' ? 'FastAPI backend' : backendStatus === 'loading' ? 'Loading backend' : 'Backend offline'}</strong>
          <small>{apiBaseUrl}</small>
        </div>
        <div className="backend-inline-card">
          <Database size={18} />
          <span>Backend payloads</span>
          <strong>{runbooks.length} runbooks · {auditCount} audit · {queryClusterCount} clusters</strong>
          <small>Visible across Overview, Ops Runbooks, Query Clusters, and Audit Trail</small>
        </div>
        <div className="backend-inline-card">
          <Workflow size={18} />
          <span>Temporal namespace</span>
          <strong>{temporalDetails?.namespace ?? 'default'}</strong>
          <small>{temporalDetails?.backend_address ?? 'localhost:7233'} · {temporalDetails?.backend_connected ? 'connected' : 'not connected'}</small>
        </div>
        <div className="backend-inline-card">
          <Workflow size={18} />
          <span>Temporal Web URL</span>
          <strong>{temporalDetails?.workflows_url ?? 'http://localhost:8233/namespaces/default/workflows'}</strong>
          <small>{temporalDetails?.redirect_endpoint ?? '/api/temporal/workflows'}</small>
        </div>
      </div>

      {/* Metrics Widgets */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">
            <span>{healthLabel}</span>
            <TrendingUp size={16} style={{ color: '#2e7d32' }} />
          </div>
          <div>
            <div className="metric-value">{metrics.ndcg.toFixed(2)}</div>
            <div className="metric-change up">
              <span>{isTemporalBackendData ? 'Derived from workflow status' : '+3.2% vs baseline'}</span>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">
            <span>{riskLabel}</span>
            <TrendingDown size={16} style={{ color: '#2e7d32' }} />
          </div>
          <div>
            <div className="metric-value">{metrics.zeroResultRate.toFixed(1)}%</div>
            <div className="metric-change up">
              <span>{isTemporalBackendData ? 'Failed/running workflow risk' : '-12.4% today'}</span>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">
            <span>{runtimeLabel}</span>
            <Clock size={16} style={{ color: 'var(--text-muted)' }} />
          </div>
          <div>
            <div className="metric-value">{metrics.latency}{runtimeUnit}</div>
            <div className="metric-change down">
              <span>{isTemporalBackendData ? 'Runtime derived from Temporal timestamps' : '-4.5ms vs yesterday'}</span>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">
            <span>{closedLabel}</span>
            <CheckCircle size={16} style={{ color: '#2e7d32' }} />
          </div>
          <div>
            <div className="metric-value">{metrics.completedRunbooks}</div>
            <div className="metric-change neutral">
              <span>Last 24h timeline</span>
            </div>
          </div>
        </div>
      </div>

      {/* Charts and Live Activity */}
      <div className="dashboard-main-grid">
        {/* Latency and Relevance Trends */}
        <div className="card">
          <div className="card-header">
            <h3>System Relevance &amp; Latency Trends</h3>
          </div>
          <p className="policy-description" style={{ marginBottom: '1rem' }}>
            {isTemporalBackendData
              ? 'Data-backed diagram generated from live Temporal workflow status, runtime, task queue, and completion state.'
              : 'Data-backed diagram generated from active runbook query volume, NDCG, exit-rate, and P95 latency values.'}
          </p>
          <div className="chart-legend">
            <span><i className="legend-dot relevance" /> {isTemporalBackendData ? 'Workflow health' : 'Relevance NDCG'}</span>
            <span><i className="legend-dot exits" /> {isTemporalBackendData ? 'Risk health' : 'Exit health'}</span>
            <span><i className="legend-dot latency" /> {isTemporalBackendData ? 'Runtime health' : 'Latency health'}</span>
          </div>
          <div className="chart-wrapper">
            {hasTrendRows ? (
              <svg className="svg-chart" viewBox="0 0 300 120" preserveAspectRatio="none">
              <defs>
                <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--primary)" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="var(--primary)" stopOpacity="0.0" />
                </linearGradient>
                <linearGradient id="chartGradSecond" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--info)" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="var(--info)" stopOpacity="0.0" />
                </linearGradient>
              </defs>
              {/* Grid lines */}
              <line x1="0" y1="30" x2="300" y2="30" className="chart-grid-line" />
              <line x1="0" y1="60" x2="300" y2="60" className="chart-grid-line" />
              <line x1="0" y1="90" x2="300" y2="90" className="chart-grid-line" />

              {/* Relevance line */}
              <path d={toPath(relevancePoints)} className="chart-path" />
              <path d={`M 18,120 L ${relevancePoints.split(' ').join(' L ')} L 282,120 Z`} className="chart-area-fill" />

              {/* Exit health line */}
              <path d={toPath(exitHealthPoints)} className="chart-path-third" />

              {/* Latency line */}
              <path d={toPath(latencyHealthPoints)} className="chart-path-second" />
              <path d={`M 18,120 L ${latencyHealthPoints.split(' ').join(' L ')} L 282,120 Z`} className="chart-area-fill-second" />

              {/* Data points */}
              {relevancePoints.split(' ').map((p, idx) => {
                const [x, y] = p.split(',');
                return <circle key={`rel-${idx}`} cx={x} cy={y} r="4" className="chart-point" />;
              })}
              {exitHealthPoints.split(' ').map((p, idx) => {
                const [x, y] = p.split(',');
                return <circle key={`exit-${idx}`} cx={x} cy={y} r="3.5" className="chart-point" style={{ stroke: 'var(--success)' }} />;
              })}
              {latencyHealthPoints.split(' ').map((p, idx) => {
                const [x, y] = p.split(',');
                return <circle key={`lat-${idx}`} cx={x} cy={y} r="4" className="chart-point" style={{ stroke: 'var(--info)' }} />;
              })}
              </svg>
            ) : (
              <div className="empty-state">
                No runbook metrics returned from backend. The chart will render after your real runbook source returns data.
              </div>
            )}
          </div>
          <div className="trend-data-grid">
            {trendRows.map((row) => (
                <div key={row.id} className="trend-data-card">
                  <strong>{row.code}</strong>
                  <span>{row.status}</span>
                  <small>
                    {isTemporalBackendData
                      ? `Health ${row.currentNdcg.toFixed(2)} · Risk ${row.currentExitRate.toFixed(1)}% · Runtime ${row.p95Latency}${runtimeUnit}`
                      : `NDCG ${row.currentNdcg.toFixed(2)} · Exits ${row.currentExitRate.toFixed(1)}% · P95 ${row.p95Latency}${runtimeUnit}`}
                  </small>
                </div>
              ))}
          </div>
        </div>

        {/* Activity feed */}
        <div className="card">
          <div className="card-header">
            <h3>Recent Activity Feed</h3>
          </div>
          <div className="activity-feed">
            {recentEvents.map((evt, idx) => (
              <div key={idx} className={`activity-item ${evt.type}`}>
                <div>
                  <p>{evt.text}</p>
                  <span className="activity-time">{evt.time}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
};
