import React from 'react';
import { History, ShieldCheck, Download } from 'lucide-react';
import type { AuditRow } from '../types';

interface AuditTrailProps {
  history: AuditRow[];
}

export const AuditTrail: React.FC<AuditTrailProps> = ({ history }) => {
  return (
    <div className="card">
      <div className="card-header">
        <h3>
          <History size={18} style={{ color: 'var(--primary)' }} />
          <span>Temporal Action Audit &amp; Evidence Ledger</span>
        </h3>
        <button className="btn btn-secondary" style={{ width: 'auto', padding: '0.45rem 0.85rem', fontSize: '0.75rem' }} type="button">
          <Download size={12} style={{ marginRight: '0.25rem' }} />
          Export signed evidence CSV
        </button>
      </div>
      <p className="policy-description" style={{ marginBottom: '1.25rem' }}>
        Magellan secures releases by writing signed execution evidence to an immutable history block. Every canary rollout, approval signature, and manual rollback is audited.
      </p>

      <div className="audit-timeline">
        {history.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No release history recorded in this session. Start a canary or rollback simulation.
          </div>
        ) : (
          history.map((row, idx) => (
            <div key={idx} className="audit-card">
              <div className="audit-stamp">
                <strong>{row.time}</strong>
                <span>runbook: {row.runbookId}</span>
                <em>{row.recordType}</em>
              </div>
              
              <div className="audit-details">
                <h4>{row.title}</h4>
                <p>
                  Action: <strong style={{ color: 'var(--text-dark)' }}>{row.action}</strong> · Route Signature: <em>{row.approver}</em>
                </p>
                <div className="audit-meta-grid">
                  <span>Agent: <strong>{row.agentName}</strong></span>
                  <span>Behavior: <strong>{row.agentBehavior}</strong></span>
                  <span>Temporal: <strong>{row.temporalWorkflowId}</strong></span>
                  <span>Approval: <strong>{row.approvalGate}</strong></span>
                  <span>Monitoring: <strong>{row.monitoringSummary}</strong></span>
                  <span>Feedback: <strong>{row.feedbackRecord}</strong></span>
                </div>
              </div>

              <div className={`audit-evidence ${row.isRollback ? 'warning' : ''}`} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <ShieldCheck size={14} />
                <span>{row.hash}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
