import React, { useState, useEffect } from 'react';
import { api } from '../api';

interface ShadowTestReportProps {
  workflowId: string | null;
}

interface ResultItem {
    id: string;
    name: string;
    score: number;
}

interface ReportData {
    status: string;
    summary?: string;
    production_results?: ResultItem[];
    candidate_results?: ResultItem[];
    diff?: string[];
    error?: string;
}

export const ShadowTestReport: React.FC<ShadowTestReportProps> = ({ workflowId }) => {
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!workflowId) {
      setData(null);
      return;
    }

    const fetchReport = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get<ReportData>(`/shadow-test/${workflowId}`);
        setData(response.data);
      } catch (err) {
        setError('Failed to fetch shadow test report.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [workflowId]);

  if (!workflowId) {
    return (
        <div className="p-6 text-center">
            <h2 className="text-xl font-semibold text-gray-500">Select a workflow run to view its shadow test report.</h2>
        </div>
    );
  }

  if (loading) {
    return <div className="p-6 text-center">Loading report...</div>;
  }

  if (error) {
    return <div className="p-6 text-center text-red-500">{error}</div>;
  }
  
  if (!data || data.status === 'RUNNING') {
    return <div className="p-6 text-center">The selected workflow is still running. Report is not yet available.</div>;
  }

  if (data.status === 'ERROR' || !data.summary) {
    return <div className="p-6 text-center text-red-500">An error occurred in the workflow: {data.error || 'Unknown error'}</div>;
  }


  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Shadow Test Report</h2>
      <p className="mb-6 text-gray-600">{data.summary}</p>
      
      <div className="grid grid-cols-2 gap-6">
        <div>
          <h3 className="text-lg font-bold mb-2">Production Results</h3>
          <ul className="border rounded p-4 bg-gray-50">
            {data.production_results?.map((item, index) => (
              <li key={index} className="mb-2 text-sm">
                <strong>{item.name}</strong> (Score: {item.score})
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="text-lg font-bold mb-2">Candidate Results</h3>
          <ul className="border rounded p-4 bg-gray-50">
            {data.candidate_results?.map((item, index) => (
              <li key={index} className="mb-2 text-sm">
                <strong>{item.name}</strong> (Score: {item.score})
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-6">
        <h3 className="text-lg font-bold mb-2">Summary of Differences</h3>
        <ul className="border rounded p-4 font-mono text-sm bg-gray-800 text-white">
          {data.diff?.map((item, index) => (
            <li key={index} className={item.startsWith('+') ? 'text-green-400' : item.startsWith('-') ? 'text-red-400' : 'text-gray-400'}>
              <span className="mr-2">{item.startsWith('+') ? '+' : item.startsWith('-') ? '-' : '~'}</span>
              <span>{item.substring(2)}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};