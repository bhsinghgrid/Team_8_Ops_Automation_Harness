import React, { useState, useEffect } from 'react';
import { api } from '../api';

interface PresetDefinition {
  title: string;
  badge: string;
  badgeBg: string;
  badgeText: string;
  description: string;
  icon: string;
  payload: object;
}

const PRESETS: Record<string, PresetDefinition> = {
  catalog: {
    title: 'Catalog Quality Ingestion',
    badge: 'Catalog',
    badgeBg: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    badgeText: 'text-blue-400',
    description: 'Diagnoses HTTP 404 SKU mapping and indexing failures for newly launched products.',
    icon: '🌐',
    payload: {
      type: "catalog",
      description: "ALERT: Search quality degradation batch of anomalous events.",
      events: [
        {
          context: { channel: "app", device_type: "mobile", locale: "de-DE" },
          error: "product_not_found",
          query: { text: "non-existent product sku SKU-2943" },
          response: { latency_ms: 63, result_count: 0, results: [], status_code: 404 },
          tenant: "sports_goods_tenant_002"
        }
      ],
      use_cache: true
    }
  },
  autocomplete: {
    title: 'Autocomplete Prefix Misses',
    badge: 'Autocomplete',
    badgeBg: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    badgeText: 'text-purple-400',
    description: 'Investigates stale autocomplete indices and prefix popularity weights.',
    icon: '⌨️',
    payload: {
      type: "autocomplete",
      description: "ALERT: Autocomplete quality degradation batch of anomalous events.",
      events: [
        {
          context: { channel: "app", device_type: "mobile", locale: "en-CA" },
          error: "autocomplete_miss",
          query: { text: "autocomplete not suggesting waterproof hiking boots" },
          response: { latency_ms: 189, result_count: 0, results: [], status_code: 200 },
          tenant: "sports_goods_tenant_002"
        }
      ],
      use_cache: true
    }
  },
  semantic: {
    title: 'Semantic Embedding Drift',
    badge: 'Semantic Vector',
    badgeBg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    badgeText: 'text-emerald-400',
    description: 'Analyzes cosine similarity drift inside LanceDB and vector index segment status.',
    icon: '🧠',
    payload: {
      type: "semantic",
      description: "ALERT: Semantic search quality degradation batch of anomalous events.",
      events: [
        {
          context: { channel: "web", device_type: "tablet", locale: "en-US" },
          error: "backend_server_error",
          query: { text: "search server error for outerwear" },
          response: { latency_ms: 158, result_count: 0, results: [], status_code: 500 },
          tenant: "sports_goods_tenant_002"
        }
      ],
      use_cache: true
    }
  },
  merchandising: {
    title: 'Merchandising Rules Conflict',
    badge: 'Merchandising',
    badgeBg: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    badgeText: 'text-amber-400',
    description: 'Resolves overlapping query-boost and category burial conditions in Grid Dynamics Merchandiser.',
    icon: '📊',
    payload: {
      type: "merchandising",
      query: "summer dresses",
      issue: "Two merchandising rules are conflicting — rule_boost_brandA_summer boosts Brand A, but rule_bury_brandA_clearance buries it on the same category",
      conflicting_rule_ids: ["rule_boost_brandA_summer", "rule_bury_brandA_clearance"],
      affected_category: "Dresses > Summer",
      events: [{ issue: "mxp_rules_conflict", severity: "high" }],
      use_cache: true
    }
  }
};

export const LiveTest: React.FC = () => {
  const [jsonInput, setJsonInput] = useState('');
  const [useCache, setUseCache] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [workflowId, setWorkflowId] = useState<string | null>(null);
  const [activeTab, setActivePreset] = useState<string | null>(null);
  const [terminalLogs, setTerminalLogs] = useState<string[]>([]);
  const [backendStatus, setBackendStatus] = useState<'ONLINE' | 'CONNECTING'>('ONLINE');

  // Load Catalog preset by default
  useEffect(() => {
    loadPreset('catalog');
    
    // Simulate backend polling
    const interval = setInterval(async () => {
      try {
        await api.getHealth();
        setBackendStatus('ONLINE');
      } catch {
        setBackendStatus('CONNECTING');
      }
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadPreset = (key: string) => {
    setActivePreset(key);
    const preset = PRESETS[key];
    const modifiedPayload = {
      ...preset.payload,
      use_cache: useCache
    };
    setJsonInput(JSON.stringify(modifiedPayload, null, 2));
  };

  const handleCacheToggle = () => {
    const nextCache = !useCache;
    setUseCache(nextCache);
    try {
      const parsed = JSON.parse(jsonInput);
      parsed.use_cache = nextCache;
      setJsonInput(JSON.stringify(parsed, null, 2));
    } catch {
      // Fallback if JSON is currently invalid/edited
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target?.result;
        setJsonInput(text as string);
        setActivePreset(null);
      };
      reader.readAsText(file);
    }
  };

  const addLog = (message: string, delayMs: number) => {
    return new Promise<void>((resolve) => {
      setTimeout(() => {
        setTerminalLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${message}`]);
        resolve();
      }, delayMs);
    });
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setResult(null);
    setWorkflowId(null);
    setTerminalLogs([]);

    try {
      await addLog('⚡ Initializing search-ops operator trigger context...', 0);
      const parsedJson = JSON.parse(jsonInput);
      
      await addLog(`🚀 Querying local Temporal Server cluster (localhost:7233)...`, 600);
      const response = await api.triggerWorkflow(parsedJson);
      
      setWorkflowId(response.workflow_id);
      await addLog(`✅ Temporal workflow started successfully! Instance: ${response.workflow_id}`, 600);
      
      if (parsedJson.use_cache) {
        await addLog(`🔒 Reading active anomalies caching layers...`, 500);
        await addLog(`🎯 CACHE HIT: Retrieved pre-verified root cause diagnostic and fix mapping instantly!`, 600);
      } else {
        await addLog(`🛠️ Caching Bypassed: spinning up WebAssembly Pyodide sandbox inside Deno...`, 800);
        await addLog(`🧠 Starting Fast-RLM subagent REPL reasoning loop...`, 1000);
        await addLog(`📊 Executing differential shadow evaluation: Baseline vs. Challenger query lists...`, 1200);
      }
      
      await addLog(`🏁 Release complete: Deployed canary and reported final telemetry back to Magellan DB.`, 1000);
      setResult(`Success! Workflow ${response.workflow_id} concluded successfully.`);
    } catch (error) {
      if (error instanceof SyntaxError) {
        await addLog(`❌ JSON Syntax Error: ${error.message}`, 200);
        setResult(`Error: Invalid JSON. Please verify syntax structure.`);
      } else if (error instanceof Error) {
        await addLog(`❌ Workflow Trigger Failed: ${error.message}`, 200);
        setResult(`Error: ${error.message}`);
      } else {
        await addLog(`❌ An unexpected error occurred.`, 200);
        setResult('An unknown error occurred.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Generate line numbers for the text editor
  const lineNumbers = jsonInput.split('\n').map((_, index) => index + 1);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fade-in">
      {/* Glow Top Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-8 shadow-2xl border border-indigo-500/20">
        <div className="absolute top-0 right-0 -mt-4 -mr-4 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 -mb-4 -ml-4 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl" />
        
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="px-3 py-1 text-[10px] font-bold tracking-widest text-indigo-400 bg-indigo-500/10 border border-indigo-400/20 rounded-full uppercase">
                Operator Playpen
              </span>
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-950/60 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
                <span className={`w-2 h-2 rounded-full ${backendStatus === 'ONLINE' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400 animate-ping'}`} />
                API: {backendStatus}
              </div>
            </div>
            <h2 className="text-3xl font-extrabold text-white tracking-tight">Autonomous Diagnostic Engine</h2>
            <p className="mt-2 text-slate-400 max-w-2xl text-sm leading-relaxed">
              Inject active search incidents directly into Temporal Orchestration to trigger recursive, sandboxed REPL diagnostic agents in real-time.
            </p>
          </div>
        </div>
      </div>

      {/* Preset cards grid */}
      <div className="space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 flex items-center gap-2">
          <span>🎯 Select Target Anomaly Template</span>
          <span className="h-px flex-1 bg-slate-200 dark:bg-slate-800" />
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Object.entries(PRESETS).map(([key, preset]) => (
            <button
              key={key}
              type="button"
              onClick={() => loadPreset(key)}
              className={`group relative p-5 text-left border rounded-2xl transition-all duration-300 hover:-translate-y-0.5 cursor-pointer overflow-hidden ${
                activeTab === key
                  ? 'border-indigo-500 bg-indigo-500/[0.03] ring-1 ring-indigo-500/20 shadow-md'
                  : 'border-slate-200 dark:border-slate-800/80 hover:border-slate-300 dark:hover:border-slate-700 hover:bg-slate-50/50 dark:hover:bg-slate-900/30 bg-white dark:bg-slate-900 shadow-sm'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl group-hover:scale-110 transition-transform duration-200">{preset.icon}</span>
                <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border tracking-wide uppercase ${preset.badgeBg}`}>
                  {preset.badge}
                </span>
              </div>
              <h4 className="font-bold text-slate-800 dark:text-slate-100 text-sm mb-1.5">{preset.title}</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed line-clamp-2">{preset.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Layout split */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left editor col */}
        <div className="lg:col-span-7 flex flex-col h-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
          {/* Header toolbar */}
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="w-2.5 h-2.5 bg-indigo-500 rounded-full animate-pulse" />
              <span className="text-sm font-bold text-slate-700 dark:text-slate-300 font-mono">REM_INCIDENT_CONTEXT.json</span>
            </div>

            <div className="flex items-center gap-6">
              {/* Cache Toggle switch */}
              <div className="flex items-center gap-2.5">
                <span className="text-xs font-semibold text-slate-600 dark:text-slate-400">Autonomous Caching</span>
                <button
                  type="button"
                  onClick={handleCacheToggle}
                  className={`relative inline-flex h-6.5 w-12 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none shadow-sm ${
                    useCache ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-700'
                  }`}
                >
                  <span
                    className={`pointer-events-none inline-block h-5.5 w-5.5 transform rounded-full bg-white shadow-md ring-0 transition duration-200 ease-in-out ${
                      useCache ? 'translate-x-5.5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {/* Upload file btn */}
              <div>
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer inline-flex items-center gap-1.5 px-3 py-1.5 border border-slate-200 dark:border-slate-700/80 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-semibold rounded-lg shadow-sm transition-colors duration-150"
                >
                  <svg className="w-3.5 h-3.5 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                  Upload File
                </label>
                <input
                  id="file-upload"
                  type="file"
                  className="hidden"
                  accept=".json,.csv"
                  onChange={handleFileChange}
                />
              </div>
            </div>
          </div>

          {/* Editor Container with simulated line numbers */}
          <form onSubmit={handleSubmit} className="flex-1 flex flex-col p-5">
            <div className="flex-1 flex border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden bg-slate-950 text-slate-300 shadow-inner">
              {/* Line numbers block */}
              <div className="w-12 bg-slate-900 py-4 text-right pr-3 select-none text-slate-600 font-mono text-xs leading-relaxed border-r border-slate-800/60">
                {lineNumbers.map((num) => (
                  <div key={num}>{num}</div>
                ))}
              </div>
              <textarea
                className="flex-1 p-4 font-mono text-sm leading-relaxed text-indigo-300 bg-slate-950 focus:outline-none resize-none h-[420px] overflow-y-auto"
                value={jsonInput}
                onChange={(e) => {
                  setJsonInput(e.target.value);
                  setActivePreset(null);
                }}
                placeholder={`{ "description": "Users are reporting low relevance for the query 'red running shoes'." }`}
              />
            </div>
            
            <button
              type="submit"
              className="mt-5 w-full flex items-center justify-center gap-2.5 px-6 py-3.5 bg-indigo-600 hover:bg-indigo-700 hover:shadow-lg hover:shadow-indigo-500/10 text-white font-bold rounded-xl shadow-md disabled:bg-slate-200 dark:disabled:bg-slate-800 disabled:text-slate-400 disabled:shadow-none transition-all duration-200 cursor-pointer text-sm tracking-wide"
              disabled={isLoading || !jsonInput}
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Processing Remediation Run...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5 text-indigo-100" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  </svg>
                  Fire Sandbox Signal
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right terminal / status col */}
        <div className="lg:col-span-5 flex flex-col h-full bg-slate-950 border border-slate-900 rounded-2xl shadow-xl overflow-hidden min-h-[500px]">
          {/* Terminal tab bar */}
          <div className="px-4 py-3 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-rose-500" />
              <span className="w-3 h-3 rounded-full bg-amber-500" />
              <span className="w-3 h-3 rounded-full bg-emerald-500" />
              <span className="ml-2.5 text-xs text-slate-400 font-mono font-bold tracking-tight">Live Operator Log Console</span>
            </div>
            {isLoading && (
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
            )}
          </div>

          {/* Terminal list or empty */}
          <div className="flex-1 p-5 font-mono text-xs leading-relaxed text-slate-300 overflow-y-auto space-y-2.5 h-[340px] bg-slate-950/80">
            {terminalLogs.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center text-slate-600">
                <svg className="w-10 h-10 mb-3 opacity-40 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <p className="font-sans font-semibold text-xs text-slate-500">Waiting for sandbox operator execution...</p>
                <p className="text-[10px] text-slate-700 mt-1 max-w-[200px] leading-normal">Select an anomaly template above and click "Fire Sandbox Signal"</p>
              </div>
            ) : (
              terminalLogs.map((log, index) => (
                <div key={index} className="border-l-2 border-indigo-500/20 pl-2 text-emerald-400 hover:text-emerald-300 transition-colors">
                  {log}
                </div>
              ))
            )}
          </div>

          {/* Status summary Card footer */}
          {result && (
            <div className="p-5 border-t border-slate-900 bg-slate-900/50 flex flex-col gap-4">
              <div className="bg-emerald-950/20 border border-emerald-500/20 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2 text-emerald-400">
                  <svg className="w-5 h-5 shrink-0 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <h4 className="font-bold text-sm">Execution Completed</h4>
                </div>
                <p className="text-slate-300 text-xs font-mono break-all leading-normal">{result}</p>
              </div>

              {workflowId && (
                <div className="flex items-center justify-between bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <div className="flex flex-col">
                    <span className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold font-sans">Temporal Workflow Instance</span>
                    <span className="font-mono text-xs text-slate-300 mt-0.5 truncate max-w-[180px]">{workflowId}</span>
                  </div>
                  <a
                    href="http://localhost:8233"
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] font-semibold font-sans text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 px-2.5 py-1 rounded-md transition-colors"
                  >
                    Temporal Web UI
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};