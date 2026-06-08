import React from 'react';
import { SearchCode, RefreshCcw, AlertTriangle } from 'lucide-react';
import type { QueryClusterRow } from '../types';

interface QueryClustersProps {
  clusters: QueryClusterRow[];
}

const fallbackClusters: QueryClusterRow[] = [
    {
      query: 'waterproof trail shoes',
      volume: '12,800',
      exits: '18%',
      loss: '-$4,200',
      impact: 'High',
      tag: 'Catalog attribute gap',
      badgeClass: 'waterproof',
      status: 'Active Runbook (ops-4f72)'
    },
    {
      query: 'hydra p / hydra pack',
      volume: '5,400',
      exits: '32%',
      loss: '-$2,100',
      impact: 'Med',
      tag: 'Typo synonym miss',
      badgeClass: 'typo',
      status: 'Active Runbook (ops-1a88)'
    },
    {
      query: 'winter jacket clearance',
      volume: '9,100',
      exits: '14%',
      loss: '-$3,500',
      impact: 'Med',
      tag: 'MXP Boost conflict',
      badgeClass: 'rules',
      status: 'Active Runbook (ops-7b19)'
    },
    {
      query: 'voice: hiking boots goretex',
      volume: '2,800',
      exits: '42%',
      loss: '-$1,800',
      impact: 'Med',
      tag: 'Multimodal image QA',
      badgeClass: 'waterproof',
      status: 'Shadow Test Queued'
    },
    {
      query: 'running jackets lightweight',
      volume: '15,200',
      exits: '4%',
      loss: '-$400',
      impact: 'Low',
      tag: 'Healthy relevance',
      badgeClass: 'rules',
      status: 'Auto-closed (Healthy)'
    }
  ];

export const QueryClusters: React.FC<QueryClustersProps> = ({ clusters }) => {
  const rows = clusters.length > 0 ? clusters : fallbackClusters;

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
            {rows.map((c, idx) => (
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
