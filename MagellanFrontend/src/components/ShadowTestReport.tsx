import React, { useEffect, useState } from 'react';
import { api } from '../api';

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

  return (
    <div className="p-8 space-y-8">
      {/* 🚀 Dynamic Canary Releases & Shadow Test Table */}
      <div className="bg-white shadow rounded-lg p-6 border border-gray-200">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Canary Release & Shadow Test Runbook</h2>
        <p className="text-sm text-gray-600 mb-6">
          The following list displays completed Temporal repair workflow releases and their shadowed evaluations. 
          Relevance, performance latencies, and conversion gating are verified dynamically from backend runbook results.
        </p>

        {loading ? (
          <div className="flex items-center justify-center p-8 space-x-2 text-gray-500">
            <svg className="animate-spin h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span>Loading active shadow reports...</span>
          </div>
        ) : error ? (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            <strong>Fetch Error:</strong> {error}
          </div>
        ) : reports.length === 0 ? (
          <div className="text-gray-500 text-center py-8">
            No active shadow test reports found in MLflow. Trigger a workflow to generate shadow reports dynamically.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Runbook / Report ID</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Gating Decision</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Summary Statement</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">NDCG Change</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Baseline nDCG</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Shadow nDCG</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Regressions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200 text-sm text-gray-700">
                {reports.map((report) => (
                  <tr key={report.workflow_id} className="hover:bg-gray-50 transition">
                    <td className="px-6 py-4 whitespace-nowrap font-mono font-semibold text-blue-600">{report.workflow_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2.5 py-1 inline-flex text-xs leading-5 font-semibold rounded-full border ${report.decision === 'PROMOTE_TO_CANARY' ? 'bg-emerald-100 text-emerald-800 border-emerald-200' : 'bg-rose-100 text-rose-800 border-rose-200'}`}>
                        {report.decision}
                      </span>
                    </td>
                    <td className="px-6 py-4 max-w-md truncate text-gray-600" title={report.summary}>{report.summary}</td>
                    <td className="px-6 py-4 whitespace-nowrap font-semibold text-gray-900">
                      {report.metrics.ctr_change_percentage > 0 ? '+' : ''}{(report.metrics.ctr_change_percentage ?? 0).toFixed(2)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-500">{(report.metrics.baseline_ctr ?? 0).toFixed(3)}</td>
                    <td className="px-6 py-4 whitespace-nowrap font-semibold text-gray-900">{(report.metrics.shadow_ctr ?? 0).toFixed(3)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-center font-semibold text-rose-600">{report.metrics.regressions_found ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
