import React, { useState } from 'react';
import { api } from '../api';

export const LiveTest: React.FC = () => {
  const [jsonInput, setJsonInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target?.result;
        setJsonInput(text as string);
      };
      reader.readAsText(file);
    }
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setResult(null);

    try {
      const parsedJson = JSON.parse(jsonInput);
      const response = await api.triggerWorkflow(parsedJson);
      setResult(`Workflow started successfully! Workflow ID: ${response.workflow_id}`);
    } catch (error) {
      if (error instanceof SyntaxError) {
        setResult(`Error: Invalid JSON. ${error.message}`);
      } else if (error instanceof Error) {
        setResult(`Error: ${error.message}`);
      } else {
        setResult('An unknown error occurred.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Trigger Live Workflow</h2>
      <p className="mb-6 text-gray-600">
        Paste a JSON object below, or upload a JSON/CSV file, to be used as the input signal for a new workflow run.
      </p>
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="file-upload" className="cursor-pointer inline-block px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300">
            Upload JSON/CSV File
          </label>
          <input
            id="file-upload"
            type="file"
            className="hidden"
            accept=".json,.csv"
            onChange={handleFileChange}
          />
        </div>
        <textarea
          className="w-full h-64 p-2 border rounded font-mono text-sm"
          value={jsonInput}
          onChange={(e) => setJsonInput(e.target.value)}
          placeholder={`{ "description": "Users are reporting low relevance for the query 'red running shoes'." }`}
        />
        <button
          type="submit"
          className="mt-4 px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
          disabled={isLoading || !jsonInput}
        >
          {isLoading ? 'Starting Workflow...' : 'Run Test'}
        </button>
      </form>
      {result && (
        <div className="mt-6 p-4 border rounded bg-gray-50">
          <h3 className="font-bold mb-2">Result:</h3>
          <pre className="text-sm whitespace-pre-wrap">{result}</pre>
        </div>
      )}
    </div>
  );
};