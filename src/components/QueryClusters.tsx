import React from 'react';
import { SearchCode, RefreshCcw, AlertTriangle } from 'lucide-react';
import type { QueryClusterRow } from '../types';

interface QueryClustersProps {
  clusters: QueryClusterRow[];
}

export const QueryClusters: React.FC<QueryClustersProps> = ({ clusters }) => {
  return (
    <div className="card">
      <div className="card-header">
        <h3>
          <SearchCode size={18} style={{ color: 'var(--primary)' }} />
          <span>AI Search Query Cluster Analytics</span>
        </h3>
        <button className="btn btn-secondary" style={{ width: 'auto', padding: '0.45rem 0.85rem', fontSize: '0.75rem' }} type="button">
          <RefreshCcw size={12} style={{ marginRight: '0.25rem' }} />
          Re-cluster logs
        </button>
      </div>
      <p className="policy-description" style={{ marginBottom: '1.25rem' }}>
        Magellan groups failed search logs into semantic query clusters, highlighting exit metrics and conversion loss to justify remediation workflows.
      </p>

      <div style={{ overflowX: 'auto' }}>
        <table className="cluster-table">
          <thead>
            <tr>
              <th>Semantic Query Cluster</th>
              <th>Monthly Volume</th>
              <th>Search Exits</th>
              <th>Estimated Revenue Loss</th>
              <th>Impact Rank</th>
              <th>Triaged Issue Type</th>
              <th>Triaged Status</th>
            </tr>
          </thead>
          <tbody>
            {clusters.length === 0 && (
              <tr>
                <td colSpan={7} style={{ color: 'var(--text-muted)', padding: '1.4rem', textAlign: 'center' }}>
                  No query cluster data returned. Configure <code>QUERY_CLUSTERS_API_URL</code> in <code>.env</code>.
                </td>
              </tr>
            )}
            {clusters.map((c, idx) => (
              <tr key={idx}>
                <td className="cluster-query">"{c.query}"</td>
                <td className="cluster-volume">{c.volume}</td>
                <td className="cluster-exits">{c.exits}</td>
                <td className="cluster-impact">{c.loss}</td>
                <td>
                  <span 
                    style={{
                      fontWeight: '700',
                      color: c.impact === 'High' ? 'var(--error)' : c.impact === 'Med' ? 'var(--warning)' : 'var(--success-light)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem'
                    }}
                  >
                    {c.impact === 'High' && <AlertTriangle size={12} />}
                    {c.impact}
                  </span>
                </td>
                <td>
                  <span className={`cluster-badge ${c.badgeClass}`}>
                    {c.tag}
                  </span>
                </td>
                <td style={{ fontStyle: 'italic', color: 'var(--text-muted)' }}>{c.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
