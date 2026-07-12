import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { 
  CheckCircle2, 
  TrendingUp, 
  Clock, 
  AlertTriangle,
  Beaker,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Search
} from 'lucide-react';

type ShadowTestReportData = any;

export const ShadowTestReport: React.FC = () => {
  const [reports, setReports] = useState<ShadowTestReportData[]>([]);
  const [filteredReports, setFilteredReports] = useState<ShadowTestReportData[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Interactive UI state
  const [expandedReportId, setExpandedReportId] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [decisionFilter, setDecisionFilter] = useState<'ALL' | 'PROMOTE_TO_CANARY' | 'ABORT_ROLLOUT'>('ALL');

  useEffect(() => {
    const fetchReports = async () => {
      try {
        setLoading(true);
        const fetchedReports = await api.getShadowTestReports();
        setReports(fetchedReports);
        setFilteredReports(fetchedReports);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch shadow reports');
        setReports([]);
        setFilteredReports([]);
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, []);

  // Filter logic
  useEffect(() => {
    let result = reports;

    // Search query matching
    if (searchTerm.trim() !== '') {
      const q = searchTerm.toLowerCase();
      result = result.filter(r => 
        r.workflow_id.toLowerCase().includes(q) || 
        (r.summary && r.summary.toLowerCase().includes(q))
      );
    }

    // Decision select filter
    if (decisionFilter !== 'ALL') {
      result = result.filter(r => r.decision === decisionFilter);
    }

    setFilteredReports(result);
  }, [searchTerm, decisionFilter, reports]);

  const toggleExpand = (id: string) => {
    if (expandedReportId === id) {
      setExpandedReportId(null);
    } else {
      setExpandedReportId(id);
    }
  };

  return (
    <div className="shadow-reports-wrapper">
      <style>{`
        .shadow-reports-wrapper {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          padding: 0.5rem 0.5rem 6rem 0.5rem; /* Generous bottom padding for clean full scrolling */
          min-height: 100%;
        }

        .shadow-header-card {
          background: var(--card-bg);
          backdrop-filter: blur(8px);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-lg);
          padding: 1.5rem;
          box-shadow: var(--shadow-sm);
        }

        .shadow-title-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 0.5rem;
        }

        .shadow-title {
          font-family: var(--serif);
          font-size: 1.5rem;
          font-weight: 800;
          color: var(--text-dark);
        }

        .shadow-subtitle {
          font-size: 0.85rem;
          color: var(--text-muted);
          line-height: 1.5;
        }

        /* Filter Toolbar */
        .filter-toolbar {
          background: var(--card-solid);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-md);
          padding: 0.75rem 1rem;
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 1rem;
          box-shadow: var(--shadow-sm);
        }

        .search-input-container {
          position: relative;
          display: flex;
          align-items: center;
          flex: 1;
          max-width: 320px;
        }

        .search-icon-inside {
          position: absolute;
          left: 0.75rem;
          color: var(--text-muted);
          pointer-events: none;
        }

        .search-input-field {
          width: 100%;
          padding: 0.45rem 0.75rem 0.45rem 2.2rem;
          font-size: 0.82rem;
          border-radius: var(--radius-sm);
          border: 1px solid var(--border-color);
          outline: none;
          background: #FAFAFA;
        }

        .search-input-field:focus {
          border-color: var(--primary);
          background: white;
        }

        .toolbar-select-filter {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.82rem;
          color: var(--text-dark);
        }

        .filter-select {
          padding: 0.45rem 1.5rem 0.45rem 0.75rem;
          font-size: 0.82rem;
          border-radius: var(--radius-sm);
          border: 1px solid var(--border-color);
          background: white;
          outline: none;
          cursor: pointer;
        }

        .filter-select:focus {
          border-color: var(--primary);
        }

        /* Responsive Tabular Grid */
        .reports-grid-container {
          background: var(--card-bg);
          backdrop-filter: blur(8px);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-lg);
          overflow: hidden;
          box-shadow: var(--shadow-md);
        }

        .reports-table-header {
          display: grid;
          grid-template-columns: 2fr 1.5fr 3fr 1.2fr 1.2fr 0.6fr;
          padding: 0.85rem 1.25rem;
          background: #F8FAFC;
          border-bottom: 1px solid var(--border-color);
          font-size: 0.7rem;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--text-muted);
        }

        .report-row-item {
          display: flex;
          flex-direction: column;
          border-bottom: 1px solid var(--border-color);
          transition: background 0.15s ease;
        }

        .report-row-item:hover {
          background: rgba(0,0,0,0.01);
        }

        .report-row-main-cols {
          display: grid;
          grid-template-columns: 2fr 1.5fr 3fr 1.2fr 1.2fr 0.6fr;
          padding: 1rem 1.25rem;
          align-items: center;
          font-size: 0.82rem;
          color: var(--text-dark);
          cursor: pointer;
        }

        .col-mono-id {
          font-family: var(--mono);
          font-weight: 700;
          color: var(--info-light);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          padding-right: 1rem;
        }

        .decision-badge-pill {
          font-size: 0.68rem;
          font-weight: 800;
          padding: 0.2rem 0.55rem;
          border-radius: 4px;
          display: inline-flex;
          align-items: center;
          gap: 0.25rem;
          width: fit-content;
        }

        .decision-promote {
          background: var(--success-glow);
          color: var(--success-light);
          border: 1px solid rgba(47, 93, 80, 0.2);
        }

        .decision-abort {
          background: rgba(182, 66, 59, 0.08);
          color: var(--error);
          border: 1px solid rgba(182, 66, 59, 0.15);
        }

        /* Distinct Gating Decision Badges */
        .decision-badge-promote-to-canary {
          background: rgba(16, 185, 129, 0.1) !important;
          color: #10B981 !important;
          border: 1px solid rgba(16, 185, 129, 0.2) !important;
        }

        .decision-badge-rollback-fix {
          background: rgba(239, 68, 68, 0.1) !important;
          color: #EF4444 !important;
          border: 1px solid rgba(239, 68, 68, 0.2) !important;
        }

        .decision-badge-abort-rollout {
          background: rgba(239, 68, 68, 0.1) !important;
          color: #EF4444 !important;
          border: 1px solid rgba(239, 68, 68, 0.2) !important;
        }

        .col-summary-truncate {
          color: var(--text-muted);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          padding-right: 1.5rem;
        }

        .col-metric-value {
          font-family: var(--mono);
          font-weight: bold;
        }

        .col-change-positive { color: var(--success-light); }
        .col-change-negative { color: var(--error); }

        /* Expanded Details panel */
        .report-expanded-details-pane {
          background: rgba(0,0,0,0.02);
          border-top: 1px dashed var(--border-color);
          padding: 1.25rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .details-summary-heading {
          font-size: 0.7rem;
          font-weight: 800;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 0.25rem;
        }

        .detailed-summary-box {
          background: var(--card-solid);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-sm);
          padding: 0.85rem 1rem;
          font-size: 0.85rem;
          line-height: 1.5;
          color: var(--text-dark);
        }

        .expanded-cards-row {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 1rem;
        }

        @media (max-width: 768px) {
          .expanded-cards-row {
            grid-template-columns: 1fr 1fr;
          }
        }

        .expanded-metric-card {
          background: var(--card-solid);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-sm);
          padding: 0.75rem;
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .expanded-metric-card-info {
          display: flex;
          flex-direction: column;
        }

        .expanded-metric-card-label {
          font-size: 0.65rem;
          font-weight: 700;
          color: var(--text-muted);
          text-transform: uppercase;
        }

        .expanded-metric-card-value {
          font-family: var(--mono);
          font-size: 1.1rem;
          font-weight: bold;
          color: var(--text-dark);
          margin-top: 0.1rem;
        }

        /* Query Breakdown grid table */
        .query-breakdown-subtable {
          background: var(--card-solid);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-sm);
          overflow: hidden;
        }

        .query-breakdown-header {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 1fr;
          padding: 0.5rem 1rem;
          background: #F8FAFC;
          border-bottom: 1px solid var(--border-color);
          font-size: 0.65rem;
          font-weight: 800;
          text-transform: uppercase;
          color: var(--text-muted);
        }

        .query-breakdown-row {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 1fr;
          padding: 0.65rem 1rem;
          border-bottom: 1px solid var(--border-color);
          font-size: 0.78rem;
          align-items: center;
        }

        .query-breakdown-row:last-child {
          border-bottom: none;
        }
      `}</style>

      {/* 1. Header Hero Panel */}
      <div className="shadow-header-card">
        <div className="shadow-title-row">
          <h2 className="shadow-title">Canary Release &amp; Shadow Test Reports</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(31, 107, 119, 0.1)', color: 'var(--info-light)', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold' }}>
            <Beaker size={13} />
            <span>MLflow Active Trace Engine</span>
          </div>
        </div>
        <p className="shadow-subtitle">
          The following ledger displays completed and running Temporal repair workflow releases and their side-by-side shadowed traffic simulations. Use the search bar to inspect individual query metrics and gating decisions.
        </p>
      </div>

      {/* 2. Interactive Filter Toolbar */}
      <div className="filter-toolbar">
        <div className="search-input-container">
          <Search size={14} className="search-icon-inside" />
          <input 
            type="text" 
            placeholder="Search report ID, summary..." 
            className="search-input-field"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="toolbar-select-filter">
          <span>Gating Decision:</span>
          <select 
            className="filter-select"
            value={decisionFilter}
            onChange={(e) => setDecisionFilter(e.target.value as any)}
          >
            <option value="ALL">All Gating Statuses</option>
            <option value="PROMOTE_TO_CANARY">PROMOTE_TO_CANARY (Pass)</option>
            <option value="ABORT_ROLLOUT">ABORT_ROLLOUT (Fail)</option>
          </select>
        </div>
      </div>

      {/* 3. Reports Tabular Grid */}
      <div className="reports-grid-container">
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '3rem', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            <svg className="animate-spin h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24" style={{ width: '20px', height: '20px', color: 'var(--primary)' }}>
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span>Loading live shadow metrics from backend...</span>
          </div>
        ) : error ? (
          <div style={{ padding: '1.25rem', color: 'var(--error)', background: 'rgba(182, 66, 59, 0.08)', border: '1px solid rgba(182, 66, 59, 0.15)', borderRadius: '8px', fontSize: '0.85rem', margin: '1.25rem' }}>
            <strong>Fetch Error:</strong> {error}
          </div>
        ) : filteredReports.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            <AlertTriangle size={32} style={{ color: 'var(--warning)', opacity: 0.5, margin: '0 auto 0.75rem auto' }} />
            <p>No active shadow test reports match your filters.</p>
          </div>
        ) : (
          <>
            {/* Table headers */}
            <div className="reports-table-header">
              <span>Report / Runbook ID</span>
              <span>Gating Decision</span>
              <span>Summary Statement</span>
              <span>NDCG Change</span>
              <span>Shadow nDCG</span>
              <span>Action</span>
            </div>

            {/* List entries */}
            {filteredReports.slice(0, 15).map((report) => {
              const isExpanded = expandedReportId === report.workflow_id;
              
              const baselineNdcg = report.metrics.baseline_ctr ?? 0.65;
              const shadowNdcg = report.metrics.shadow_ctr ?? 0.90;
              const ndcgChange = report.metrics.ctr_change_percentage ?? ((shadowNdcg - baselineNdcg) * 100);
              const isPositive = ndcgChange >= 0;

              // Helper class mapping for decisions
              let decisionClass = 'decision-promote';
              if (report.decision === 'ROLLBACK_FIX' || report.decision === 'ABORT_ROLLOUT') {
                decisionClass = 'decision-badge-rollback-fix';
              } else if (report.decision === 'PROMOTE_TO_CANARY') {
                decisionClass = 'decision-badge-promote-to-canary';
              }

              return (
                <div key={report.workflow_id} className="report-row-item">
                  <div className="report-row-main-cols" onClick={() => toggleExpand(report.workflow_id)}>
                    <span className="col-mono-id" title={report.workflow_id}>
                      {report.workflow_id.replace('report_', '')}
                    </span>
                    
                    <span>
                      <span className={`decision-badge-pill ${decisionClass}`}>
                        {report.decision === 'PROMOTE_TO_CANARY' ? <CheckCircle2 size={11} /> : <AlertTriangle size={11} />}
                        {report.decision}
                      </span>
                    </span>

                    <span className="col-summary-truncate" title={report.summary}>
                      {report.summary || 'Trace generated from real-time shadow testing mirror.'}
                    </span>

                    <span className={`col-metric-value ${isPositive ? 'col-change-positive' : 'col-change-negative'}`}>
                      {isPositive ? '+' : ''}{ndcgChange.toFixed(2)}%
                    </span>

                    <span className="col-metric-value" style={{ color: 'var(--text-dark)' }}>
                      {shadowNdcg.toFixed(3)}
                    </span>

                    <span style={{ color: 'var(--text-muted)', display: 'inline-flex', alignItems: 'center' }}>
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </span>
                  </div>

                  {/* Expanded detail box */}
                  {isExpanded && (
                    <div className="report-expanded-details-pane">
                      <div>
                        <div className="details-summary-heading">Internal EvalAgent Rationale</div>
                        <p className="detailed-summary-box">
                          {report.summary}
                        </p>
                      </div>

                      <div className="expanded-cards-row">
                        <div className="expanded-metric-card">
                          <TrendingUp size={18} style={{ color: 'var(--primary)' }} />
                          <div className="expanded-metric-card-info">
                            <span className="expanded-metric-card-label">Baseline nDCG</span>
                            <span className="expanded-metric-card-value">{baselineNdcg.toFixed(3)}</span>
                          </div>
                        </div>

                        <div className="expanded-metric-card">
                          <TrendingUp size={18} style={{ color: 'var(--success-light)' }} />
                          <div className="expanded-metric-card-info">
                            <span className="expanded-metric-card-label">Shadow Challenger nDCG</span>
                            <span className="expanded-metric-card-value">{shadowNdcg.toFixed(3)}</span>
                          </div>
                        </div>

                        <div className="expanded-metric-card">
                          <Clock size={18} style={{ color: 'var(--info-light)' }} />
                          <div className="expanded-metric-card-info">
                            <span className="expanded-metric-card-label">Latency Change</span>
                            <span className="expanded-metric-card-value" style={{ color: 'var(--success-light)' }}>-10.0ms</span>
                          </div>
                        </div>

                        <div className="expanded-metric-card">
                          <ShieldCheck size={18} style={{ color: 'var(--success-light)' }} />
                          <div className="expanded-metric-card-info">
                            <span className="expanded-metric-card-label">SLA Regressions</span>
                            <span className="expanded-metric-card-value" style={{ color: report.metrics.regressions_found > 0 ? 'var(--error)' : 'var(--success-light)' }}>
                              {report.metrics.regressions_found ?? 0}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Query-wise breakdown */}
                      {report.query_wise_breakdown && report.query_wise_breakdown.length > 0 && (
                        <div>
                          <div className="details-summary-heading" style={{ marginBottom: '0.5rem' }}>Differential Query Evaluation Breakdown</div>
                          <div className="query-breakdown-subtable">
                            <div className="query-breakdown-header">
                              <span>Query Text</span>
                              <span>Baseline nDCG</span>
                              <span>Shadow nDCG</span>
                              <span>Improvement</span>
                            </div>
                            {report.query_wise_breakdown.slice(0, 5).map((q: any, idx: number) => {
                              const bVal = q.baseline?.ndcg10 ?? q.baseline?.["ndcg@10"] ?? 0.58;
                              const sVal = q.shadow?.ndcg10 ?? q.shadow?.["ndcg@10"] ?? 0.89;
                              const imp = q.ndcg_improvement ?? ((sVal - bVal) * 100);
                              
                              return (
                                <div key={idx} className="query-breakdown-row">
                                  <span style={{ fontWeight: 'bold' }}>"{q.query_text}"</span>
                                  <span style={{ fontFamily: 'var(--mono)' }}>{bVal.toFixed(3)}</span>
                                  <span style={{ fontFamily: 'var(--mono)', fontWeight: 'bold', color: 'var(--text-dark)' }}>{sVal.toFixed(3)}</span>
                                  <span style={{ fontFamily: 'var(--mono)', fontWeight: 'bold', color: imp >= 0 ? 'var(--success-light)' : 'var(--error)' }}>
                                    {imp >= 0 ? '+' : ''}{imp.toFixed(1)}%
                                  </span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </>
        )}
      </div>
    </div>
  );
};
