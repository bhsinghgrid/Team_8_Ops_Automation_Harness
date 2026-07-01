import React, { useEffect, useState } from 'react';
import { api } from '../api';

// A placeholder for a more specific type definition
type ShadowTestReportData = any;

export const ShadowTestReport: React.FC = () => {
  const [reports, setReports] = useState<ShadowTestReportData[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        setLoading(true);
        const fetchedReports = await api.getShadowTestReports();
        setReports(fetchedReports);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch shadow reports');
        setReports([]);
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, []);

  if (loading) {
    return <div className="p-8">Loading shadow test reports...</div>;
  }

  if (error) {
    return <div className="p-8 text-red-500">Error: {error}</div>;
  }

  if (reports.length === 0) {
    return <div className="p-8">No shadow test reports found.</div>;
  }

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-4">All Shadow Test Reports</h2>
      <div className="space-y-6">
        {reports.map((report) => (
          <div key={report.workflow_id} className="border rounded-lg p-4">
            <h3 className="text-xl font-semibold mb-2">Workflow ID: {report.workflow_id}</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <p><strong>Decision:</strong> <span className={`font-mono px-2 py-1 rounded ${report.decision === 'PROMOTE_TO_CANARY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{report.decision}</span></p>
              <p><strong>CTR Change:</strong> {(report.metrics.ctr_change_percentage ?? 0).toFixed(2)}%</p>
              <p><strong>Baseline CTR:</strong> {(report.metrics.baseline_ctr ?? 0).toFixed(3)}</p>
              <p><strong>Shadow CTR:</strong> {(report.metrics.shadow_ctr ?? 0).toFixed(3)}</p>
              <p><strong>Regressions Found:</strong> {report.metrics.regressions_found ?? 'N/A'}</p>
            </div>
            <p className="text-sm mt-2"><strong>Summary:</strong> {report.summary}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
