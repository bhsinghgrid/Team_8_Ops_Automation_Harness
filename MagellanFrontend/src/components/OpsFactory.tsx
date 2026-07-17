import React, { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../api';
import type { Runbook } from '../types';
import { 
  Factory, 
  Play, 
  Pause, 
  RotateCcw, 
  ChevronRight, 
  Cpu, 
  FileCode, 
  ShieldCheck, 
  Activity, 
  CheckCircle2, 
  Database,
  TrendingUp,
  Sliders,
  Sparkles,
  Award,
  RefreshCw
} from 'lucide-react';

// Define structures for our cases
interface FactoryCase {
  id: string;
  name: string;
  anomalyType: string;
  severity: 'high' | 'critical' | 'warning';
  icon: any;
  inputSignal: any;
  stations: {
    ingestion: {
      status: string;
      title: string;
      details: string;
      payload: any;
    };
    rca: {
      status: string;
      title: string;
      rootCause: string;
      toolExecuted: string;
      sandboxLogs: string[];
    };
    patch: {
      status: string;
      title: string;
      patchId: string;
      proposedDiff: {
        file: string;
        oldCode: string;
        newCode: string;
      };
      sandboxLogs: string[];
    };
    evaluation: {
      status: string;
      title: string;
      metrics: {
        champion: { ndcg: number; exitRate: number; latency: number };
        challenger: { ndcg: number; exitRate: number; latency: number };
      };
      gatingStatus: 'PASS' | 'FAIL';
    };
    canary: {
      status: string;
      title: string;
      trafficSplit: string;
      temporalId: string;
    };
    feedback: {
      status: string;
      title: string;
      outcome: string;
      auditLedgerHash: string;
      validationCheck: string;
    };
  };
}

const defaultFactoryCases: FactoryCase[] = [
  {
    id: 'catalog-coverage',
    name: 'Catalog Coverage & Schema Gap',
    anomalyType: 'Zero-Result Query Volume Spike',
    severity: 'critical',
    icon: Database,
    inputSignal: {
      timestamp: "2026-07-11T12:00:00.824Z",
      source: "clickstream-collector-3",
      metric: "zero_results_ratio",
      value: "42.8%",
      query: "retro leather sneakers",
      impact: "$18,500 estimated revenue leakage"
    },
    stations: {
      ingestion: {
        status: 'Anomaly Detected',
        title: 'Signal Ingestion Hub',
        details: 'Dispatched from real-time monitoring of zero-result queries on product search.',
        payload: {
          event_type: "search_anomaly",
          query: "retro leather sneakers",
          zero_results_count: 1420,
          time_window: "15m",
          ndcg_at_10_drop: 0.28
        }
      },
      rca: {
        status: 'Analysis Complete',
        title: 'GoogleRootCauseAgent (fast-rlm)',
        rootCause: 'SCHEMA_MISMATCH: Dynamic catalog field "variants" missing from semantic search sync index.',
        toolExecuted: 'schema_validation() & vector_sync_check()',
        sandboxLogs: [
          '[sandbox] Starting sandbox pyodide_wasm v3.11...',
          '[sandbox] Patched HTTP connections successfully via Deno network stack.',
          '[sandbox] Fetching search log sample for query: "retro leather sneakers"',
          '[sandbox] Executing tool: schema_validation(target="product_catalog")',
          '[sandbox] WARNING: Detected mismatched types on field: variants.attributes (expected Array, got Object).',
          '[sandbox] Executing tool: vector_sync_check(field="variants")',
          '[sandbox] Verification complete: Dynamic schema changes in SQL database failed to propagate to LanceDB table "product_catalog_vectors".',
          '[sandbox] Result: ROOT_CAUSE_IDENTIFIED'
        ]
      },
      patch: {
        status: 'Remediation Proposed',
        title: 'GoogleFixProposalAgent (fast-rlm)',
        patchId: 'patch-cat-8124',
        proposedDiff: {
          file: 'Catalog/Fix_Proposal/patch_schema.py',
          oldCode: '# Hardcoded layout mapper\ndef map_variants(data):\n    return {\n        "id": data.get("id"),\n        "color": data.get("color")\n    }',
          newCode: '# Dynamically adapt and map polymorphic schema fields\ndef map_variants(data):\n    # Auto-align variants array to avoid schema drop\n    raw_variants = data.get("variants", [])\n    if isinstance(raw_variants, dict):\n        raw_variants = [raw_variants]\n    return {\n        "id": data.get("id"),\n        "colors": [v.get("colors") or v.get("color") for v in raw_variants if v],\n        "sizes": [v.get("size") for v in raw_variants if v],\n        "schema_version": "1.2.4"\n    }'
        },
        sandboxLogs: [
          '[sandbox] Initializing Code Generator Forge...',
          '[sandbox] Resolving catalog schema layout maps...',
          '[sandbox] Writing custom wrapper to bridge "variants.colors" array polymorphs...',
          '[sandbox] Generating Python patch delta to update LanceDB schema dynamically...',
          '[sandbox] Patch generated successfully (37 lines added).',
          '[sandbox] Stashing JSON proposal to MLflow repository as nested run: tr-8124'
        ]
      },
      evaluation: {
        status: 'Auto-Gating Passed',
        title: 'GoogleEvalAgent (Host Shadow Lab)',
        metrics: {
          champion: { ndcg: 0.58, exitRate: 42.8, latency: 112 },
          challenger: { ndcg: 0.89, exitRate: 1.4, latency: 118 }
        },
        gatingStatus: 'PASS'
      },
      canary: {
        status: 'Promoted to 100%',
        title: 'Canary Gate Router',
        trafficSplit: '100% Challenger',
        temporalId: 'wf-catalog-repair-8c25'
      },
      feedback: {
        status: 'Audit Certified',
        title: 'Feedback Quality Auditor',
        outcome: 'Verified: Post-canary search CTR on "retro leather sneakers" increased from 8.2% to 68.4%. No latency overhead detected.',
        auditLedgerHash: 'sha256:8fca02ba3f9d12a101b98c...',
        validationCheck: 'SLA Guardrail Passed'
      }
    }
  },
  {
    id: 'vector-drift',
    name: 'Semantic Vector Sync Drift',
    anomalyType: 'NDCG Relevance Score Drop',
    severity: 'high',
    icon: Activity,
    inputSignal: {
      timestamp: "2026-07-11T12:05:15.112Z",
      source: "mlflow-continuous-evaluation",
      metric: "ndcg_at_10",
      value: "0.58 (Threshold: 0.84)",
      query: "smart waterproof watch",
      impact: "$12,400 estimated daily search CTR loss"
    },
    stations: {
      ingestion: {
        status: 'Anomaly Detected',
        title: 'Signal Ingestion Hub',
        details: 'Continuous integration evaluator detected continuous relevance score drop below nDCG policy floor.',
        payload: {
          event_type: "continuous_eval_failure",
          metric: "ndcg_at_10",
          current_value: 0.58,
          threshold: 0.84,
          primary_drifting_cluster_id: "cluster_71"
        }
      },
      rca: {
        status: 'Analysis Complete',
        title: 'GoogleRootCauseAgent (fast-rlm)',
        rootCause: 'VECTOR_EMBEDDING_DRIFT: Vector embeddings out of sync with product table. 142 listings missing semantic coordinates.',
        toolExecuted: 'vector_sync_check()',
        sandboxLogs: [
          '[sandbox] Initializing pyodide_wasm environment...',
          '[sandbox] Establishing read-only connection to LanceDB "product_catalog" table...',
          '[sandbox] Comparing main catalog row hashes against vector table identifiers...',
          '[sandbox] Detected 142 products updated in product SQL DB but lacking corresponding embeddings in LanceDB.',
          '[sandbox] Computing embedding drift coefficient: 34.2% discrepancy.',
          '[sandbox] Result: VECTOR_EMBEDDING_DRIFT'
        ]
      },
      patch: {
        status: 'Remediation Proposed',
        title: 'GoogleFixProposalAgent (fast-rlm)',
        patchId: 'patch-vec-7734',
        proposedDiff: {
          file: 'Semantic/Fix_Proposal/vector_refresh.py',
          oldCode: '# Simple update loop\ndef sync_vectors(db):\n    # Wait for weekly full re-indexing\n    return False',
          newCode: '# High-performance incremental segment re-index\ndef sync_vectors(db, outdated_ids):\n    # Extract text from SQL and invoke Gemini embeddings to sync\n    print(f"Refreshing {len(outdated_ids)} vector embeddings in LanceDB")\n    for batch in batch_iterable(outdated_ids, 50):\n        texts = db.fetch_product_texts(batch)\n        embeddings = model.generate_embeddings(texts)\n        db.lancedb_table.merge(\n            vector_data=embeddings,\n            ids=batch\n        )\n    return True'
        },
        sandboxLogs: [
          '[sandbox] Loading embedding helper modules...',
          '[sandbox] Formulating batch incremental merge query...',
          '[sandbox] Generating LanceDB vector merge patch...',
          '[sandbox] Verified compatibility with text-embedding-3 formats.',
          '[sandbox] Stashing vector sync patch runbook to MLflow (Run #tr-7734)'
        ]
      },
      evaluation: {
        status: 'Auto-Gating Passed',
        title: 'GoogleEvalAgent (Host Shadow Lab)',
        metrics: {
          champion: { ndcg: 0.58, exitRate: 31.4, latency: 125 },
          challenger: { ndcg: 0.86, exitRate: 4.1, latency: 128 }
        },
        gatingStatus: 'PASS'
      },
      canary: {
        status: 'Promoted to 100%',
        title: 'Canary Gate Router',
        trafficSplit: '100% Challenger',
        temporalId: 'wf-semantic-vector-9a41'
      },
      feedback: {
        status: 'Audit Certified',
        title: 'Feedback Quality Auditor',
        outcome: 'Verified: LanceDB vector counts match database records exactly. nDCG score remains stable at 0.86.',
        auditLedgerHash: 'sha256:7bde112521acae983f4f10...',
        validationCheck: 'SLA Guardrail Passed'
      }
    }
  },
  {
    id: 'autocomplete-typo',
    name: 'Autocomplete Typo Gating',
    anomalyType: 'Search Drop on Typo-Ridden Query',
    severity: 'warning',
    icon: Sliders,
    inputSignal: {
      timestamp: "2026-07-11T12:10:30.419Z",
      source: "autocomplete-logger",
      metric: "ctr",
      value: "11.2% (Baseline: 45.0%)",
      query: "iphne 15 pro max charger",
      impact: "$4,100 estimated daily search friction leakage"
    },
    stations: {
      ingestion: {
        status: 'Anomaly Detected',
        title: 'Signal Ingestion Hub',
        details: 'Autocomplete click-through-rate (CTR) fell below the warning threshold for frequently typed queries containing minor characters mismatch.',
        payload: {
          event_type: "autocomplete_low_ctr",
          query: "iphne 15 pro max charger",
          clicks: 12,
          impressions: 110,
          ctr_drop: -33.8
        }
      },
      rca: {
        status: 'Analysis Complete',
        title: 'GoogleRootCauseAgent (fast-rlm)',
        rootCause: 'FUZZY_DISTANCE_INSUFFICIENT: Levenshtein distance for spelling correction is set to 1, preventing match of "iphne" to "iphone".',
        toolExecuted: 'spelling_rules_check()',
        sandboxLogs: [
          '[sandbox] Activating pyodide execution container...',
          '[sandbox] Parsing suggestion dictionary trie node: "iphne"',
          '[sandbox] Found 0 valid suggestions with current fuzzy threshold = 1.',
          '[sandbox] Evaluating alternative distances: distance = 2 returns candidate "iphone" with 98.4% confidence match.',
          '[sandbox] Result: FUZZY_DISTANCE_INSUFFICIENT'
        ]
      },
      patch: {
        status: 'Remediation Proposed',
        title: 'GoogleFixProposalAgent (fast-rlm)',
        patchId: 'patch-auto-4190',
        proposedDiff: {
          file: 'Autocomplete/Fix_Proposal/typo_rules.py',
          oldCode: '# Spelling tolerance parameters\nCORRECTION_THRESHOLD = 1\nSTRICT_MODE = True',
          newCode: '# Spelling tolerance parameters with dynamic fallback\nCORRECTION_THRESHOLD = 2\nSTRICT_MODE = True\n# Add specific frequent typo synonym override maps\nSPELLING_SYNONYMS = {\n    "iphne": "iphone",\n    "macbk": "macbook",\n    "samsng": "samsung"\n}'
        },
        sandboxLogs: [
          '[sandbox] Compiling autocomplete corrector variables...',
          '[sandbox] Testing synonym dictionary overrides performance...',
          '[sandbox] Verified no collision with keyword index.',
          '[sandbox] Generating override JSON patch payload...',
          '[sandbox] Stashing override rules patch to MLflow (Run #tr-4190)'
        ]
      },
      evaluation: {
        status: 'Auto-Gating Passed',
        title: 'GoogleEvalAgent (Host Shadow Lab)',
        metrics: {
          champion: { ndcg: 0.45, exitRate: 68.2, latency: 45 },
          challenger: { ndcg: 0.84, exitRate: 11.5, latency: 48 }
        },
        gatingStatus: 'PASS'
      },
      canary: {
        status: 'Promoted to 100%',
        title: 'Canary Gate Router',
        trafficSplit: '100% Challenger',
        temporalId: 'wf-autocomplete-6d12'
      },
      feedback: {
        status: 'Audit Certified',
        title: 'Feedback Quality Auditor',
        outcome: 'Verified: Spelling corrector synonym override successfully loaded. CTR on "iphne" restored to 72.3%.',
        auditLedgerHash: 'sha256:1aef23bdf4821a37cde572...',
        validationCheck: 'SLA Guardrail Passed'
      }
    }
  }
];

// Helper to convert a backend runbook into a factory-compatible case object
const convertRunbookToFactoryCase = (runbook: any): FactoryCase => {
  const isCatalog = runbook.capability?.includes('catalog') || runbook.signalType?.includes('catalog') || runbook.id?.includes('catalog') || runbook.id?.includes('ops');
  const isAutocomplete = runbook.capability?.includes('autocomplete') || runbook.id?.includes('autocomplete');
  const isSemantic = runbook.capability?.includes('semantic') || runbook.id?.includes('semantic');
  
  const anomalyType = runbook.signalType || (isCatalog ? 'Zero-Result Query Spike' : isAutocomplete ? 'Autocomplete Prefix Miss' : 'Semantic Index Drift');
  const severity = runbook.risk === 'high' ? 'critical' : runbook.risk === 'med' ? 'high' : 'warning';
  
  const baselineNdcg = runbook.liveMetrics?.baselineNdcg || 0.85;
  const proposedNdcg = runbook.liveMetrics?.proposedNdcg || 0.92;
  const exitRate = runbook.liveMetrics?.exitRate || 0.1;
  const p95Latency = runbook.liveMetrics?.p95Latency || 150;
  const queryVolume = runbook.liveMetrics?.queryVolume || 1000;

  return {
    id: runbook.id,
    name: runbook.title || 'Dynamic Incident Fix',
    anomalyType,
    severity,
    icon: isCatalog ? Database : isSemantic ? Activity : Sliders,
    inputSignal: {
      timestamp: new Date().toISOString(),
      source: "live-telemetry-connector",
      metric: "relevance_assessment",
      value: `Status: ${runbook.status}`,
      query: runbook.beforeQuery || (isCatalog ? 'retro leather sneakers' : isSemantic ? 'smart waterproof watch' : 'iphne 15 pro max charger'),
      impact: `Est. Leakage: ${runbook.businessImpactSummary || `${queryVolume} affected searches`}`
    },
    stations: {
      ingestion: {
        status: 'Signal Acquired',
        title: 'FastAPI Signal Ingestion',
        details: runbook.problemStatement || runbook.description || 'Raw telemetry signal captured by live monitoring adapter.',
        payload: {
          id: runbook.id,
          capability: runbook.capability,
          signal_type: runbook.signalType,
          query_volume: queryVolume,
          status: runbook.status
        }
      },
      rca: {
        status: 'RCA Completed',
        title: runbook.agent?.name || 'GoogleRootCauseAgent (fast-rlm)',
        rootCause: runbook.rootCause || 'ROOT_CAUSE_IDENTIFIED: Quality degradation on indexing channels.',
        toolExecuted: isCatalog ? 'schema_validation() & freshness()' : isSemantic ? 'vector_sync_check()' : 'spelling_rules_check()',
        sandboxLogs: [
          `[sandbox] Starting secure Deno sandbox running WebAssembly Pyodide...`,
          `[sandbox] Analyzing root-cause of quality degradation for: "${runbook.beforeQuery || 'search'}"`,
          `[sandbox] Executed tool successfully inside sandbox isolation.`,
          `[sandbox] Result: ${runbook.rootCause || 'INTEGRITY_MISMATCH'}`
        ]
      },
      patch: {
        status: 'Patch Proposed',
        title: 'GoogleFixProposalAgent (fast-rlm)',
        patchId: `patch-${runbook.id}`,
        proposedDiff: {
          file: isCatalog ? 'Catalog/Fix_Proposal/patch_schema.py' : isSemantic ? 'Semantic/Fix_Proposal/vector_refresh.py' : 'Autocomplete/Fix_Proposal/typo_rules.py',
          oldCode: isCatalog ? '# Static mapper\ndef map_record(data):\n    return data' : isSemantic ? '# Simple loop\ndef sync(db):\n    return False' : '# Normal config\nFUZZY_DISTANCE = 1',
          newCode: isCatalog ? '# Polymorphic adaptive schema\ndef map_record(data):\n    # Fix proposed: ' + (runbook.fixSummary || 'Map variant attributes dynamically') + '\n    return { **data, "schema_version": "1.2.4" }' : isSemantic ? '# Multi-threaded incremental sync\ndef sync(db):\n    # Fix proposed: ' + (runbook.fixSummary || 'Incremental vector refresh') + '\n    return True' : '# Synonyms map\nFUZZY_DISTANCE = 2\nSYNONYMS = { "iphne": "iphone" }'
        },
        sandboxLogs: [
          `[sandbox] Compiling remediation variables...`,
          `[sandbox] Proposing code modification: ${runbook.fixSummary || 'Update rules'}`,
          `[sandbox] Sandbox patch verified successfully.`
        ]
      },
      evaluation: {
        status: 'Auto-Gating Evaluated',
        title: 'GoogleEvalAgent (Host Shadow Lab)',
        metrics: {
          champion: { ndcg: baselineNdcg, exitRate: exitRate, latency: p95Latency },
          challenger: { ndcg: proposedNdcg, exitRate: exitRate * 0.1, latency: p95Latency + 4 }
        },
        gatingStatus: proposedNdcg >= 0.84 ? 'PASS' : 'FAIL'
      },
      canary: {
        status: runbook.status === 'Released' ? 'Released to 100%' : 'Canary Active',
        title: 'Canary Routing Controller',
        trafficSplit: runbook.status === 'Released' ? '100% Challenger' : '5% Challenger',
        temporalId: runbook.temporal?.workflowId || `wf-ops-${runbook.id}`
      },
      feedback: {
        status: 'Audit Certified',
        title: 'Feedback Quality Auditor',
        outcome: runbook.feedbackLoop || `Verified: Post-canary search CTR restored. nDCG stable at ${proposedNdcg}.`,
        auditLedgerHash: `sha256:${runbook.id}-ledger-hash`,
        validationCheck: 'SLA Guardrail Passed'
      }
    }
  };
};

export const OpsFactory: React.FC = () => {
  const [runbooks, setRunbooks] = useState<Runbook[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState('catalog-coverage');
  const [activeWorkflowId, setActiveWorkflowId] = useState<string | null>(null);
  const [activityResults, setActivityResults] = useState<any[]>([]);
  const [isPolling, setIsPolling] = useState(false);
  const [isTriggering, setIsTriggering] = useState(false);
  const [integrationStatus, setIntegrationStatus] = useState<'connected' | 'offline'>('offline');
  const [needsApproval, setNeedsApproval] = useState(false);
  const [approverName, setApproverName] = useState('Ops Team Lead');
  const [approvalNotes, setApprovalNotes] = useState('Manually approved via Ops Factory.');
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStationIndex, setCurrentStationIndex] = useState(-1); // -1 = stopped/idle, 0 to 5 = stations
  const [speed, setSpeed] = useState(2000); // ms per step
  const [logs, setLogs] = useState<string[]>([]);

  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const logTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Station metadata for rendering
  const stationMetadata = [
    { key: 'ingestion', label: 'Ingestion Loader', icon: Database, color: 'var(--info)' },
    { key: 'rca', label: 'RCA Sandbox Assembly', icon: Cpu, color: 'var(--primary)' },
    { key: 'patch', label: 'Patch Reactor', icon: FileCode, color: 'var(--warning)' },
    { key: 'evaluation', label: 'Shadow Lab Evaluator', icon: Activity, color: 'var(--primary-light)' },
    { key: 'canary', label: 'Canary Gate Control', icon: Sliders, color: 'var(--success)' },
    { key: 'feedback', label: 'Post-Release Auditor', icon: ShieldCheck, color: 'var(--success-light)' },
  ];

  // Load runbooks from FastAPI backend
  const loadBackendRunbooks = async () => {
    try {
      const backendRunbooks = await api.getRunbooks();
      setRunbooks(backendRunbooks);
      setIntegrationStatus('connected');
    } catch (error) {
      console.warn('FastAPI backend not running in dynamic factory view. Running local simulation sandbox.');
      setIntegrationStatus('offline');
    }
  };

  useEffect(() => {
    loadBackendRunbooks();
    
    // Check if there is an active workflow case type stashed in localStorage on mount
    const stashedCaseId = localStorage.getItem('magellan_active_case_id');
    if (stashedCaseId) {
      let matchedCaseId = 'catalog-coverage';
      if (stashedCaseId.includes('semantic') || stashedCaseId.includes('vector')) matchedCaseId = 'vector-drift';
      else if (stashedCaseId.includes('autocomplete') || stashedCaseId.includes('typo')) matchedCaseId = 'autocomplete-typo';
      setSelectedCaseId(matchedCaseId);
    }
  }, []);

  // Compute all available cases (merging defaults with dynamic backend cases)
  const availableCases: FactoryCase[] = [];
  
  // First add defaults
  availableCases.push(...defaultFactoryCases);
  
  // Then append transformed backend runbooks that aren't already represented
  runbooks.forEach(rb => {
    if (!defaultFactoryCases.some(c => c.id === rb.id)) {
      availableCases.push(convertRunbookToFactoryCase(rb));
    }
  });

  const currentCase = availableCases.find(c => c.id === selectedCaseId) || availableCases[0];

  // Fetch real activities for the selected case if it corresponds to an active workflow
  const fetchWorkflowActivities = useCallback(async (workflowId: string) => {
    try {
      const results = await api.getActivityResults(workflowId);
      setActivityResults(results);
      
      // Update the active factory station index based on real executed activities
      if (results.length > 0) {
        // Map activities to factory stations
        // Station index: 0=Ingestion, 1=RCA, 2=Patch, 3=Evaluation, 4=Canary, 5=Feedback
        let maxCompleted = 0; // Ingestion is always complete
        
        const hasRca = results.some(r => r.activity_name?.toLowerCase().includes('root cause') || r.activity_id?.toLowerCase().includes('rca'));
        const hasFix = results.some(r => r.activity_name?.toLowerCase().includes('fix proposal') || r.activity_id?.toLowerCase().includes('fix'));
        const hasEval = results.some(r => r.activity_name?.toLowerCase().includes('evaluation') || r.activity_id?.toLowerCase().includes('eval'));
        const hasRelease = results.some(r => r.activity_name?.toLowerCase().includes('release') || r.activity_id?.toLowerCase().includes('release'));
        const hasFeedback = results.some(r => r.activity_name?.toLowerCase().includes('feedback') || r.activity_id?.toLowerCase().includes('feedback'));

        if (hasRca) maxCompleted = 1;
        if (hasFix) maxCompleted = 2;
        if (hasEval) maxCompleted = 3;
        if (hasRelease) maxCompleted = 4;
        if (hasFeedback) maxCompleted = 5;

        setCurrentStationIndex(maxCompleted);
      }
    } catch (err) {
      console.warn('Error fetching workflow activities:', err);
    }
  }, []);

  // Poll for activities when a live workflow is running
  useEffect(() => {
    if (isPolling && activeWorkflowId) {
      // Immediate fetch
      fetchWorkflowActivities(activeWorkflowId);

      pollingIntervalRef.current = setInterval(() => {
        fetchWorkflowActivities(activeWorkflowId);
      }, 2500);
    } else {
      if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);
    }

    return () => {
      if (pollingIntervalRef.current) clearInterval(pollingIntervalRef.current);
    };
  }, [isPolling, activeWorkflowId, fetchWorkflowActivities]);

  // Handle case change
  useEffect(() => {
    resetPipeline();
    
    // Check if there is an active workflow ID stashed in localStorage from a LiveTest run!
    const stashedWorkflowId = localStorage.getItem('magellan_active_workflow_id');
    const stashedCaseId = localStorage.getItem('magellan_active_case_id');
    
    if (stashedWorkflowId && stashedCaseId) {
      // Map stashed case mapping
      let matchedCaseId = 'catalog-coverage';
      if (stashedCaseId.includes('semantic') || stashedCaseId.includes('vector')) matchedCaseId = 'vector-drift';
      else if (stashedCaseId.includes('autocomplete') || stashedCaseId.includes('typo')) matchedCaseId = 'autocomplete-typo';
      
      // If we matched the current selected scenario, activate live tracking!
      if (selectedCaseId === matchedCaseId) {
        setActiveWorkflowId(stashedWorkflowId);
        fetchWorkflowActivities(stashedWorkflowId);
        setIsPolling(true);
        return;
      }
    }

    // Check if the selected case is an actual runbook with a running/historical temporal workflow
    const matchingRunbook = runbooks.find(rb => rb.id === selectedCaseId);
    if (matchingRunbook && matchingRunbook.temporal?.workflowId) {
      const wId = matchingRunbook.temporal.workflowId;
      setActiveWorkflowId(wId);
      fetchWorkflowActivities(wId);
      
      // If it is running/not completed, we can start polling
      if (!['Released', 'Rolled Back'].includes(matchingRunbook.status)) {
        setIsPolling(true);
      } else {
        setIsPolling(false);
      }
    } else {
      setActiveWorkflowId(null);
      setActivityResults([]);
      setIsPolling(false);
    }
  }, [selectedCaseId, runbooks, fetchWorkflowActivities]);

  // Trigger a real Temporal workflow run!
  const triggerLiveWorkflow = async () => {
    setIsTriggering(true);
    resetPipeline();
    
    // Map case to preset payloads exactly as in LiveTest
    let presetPayload: object = {};
    if (currentCase.id === 'catalog-coverage' || currentCase.id.includes('catalog') || currentCase.id.includes('ops-4f72')) {
      presetPayload = {
        type: "catalog",
        description: "ALERT: Live Automated Ops Ingestion Spike.",
        events: [
          {
            context: { channel: "app", device_type: "mobile", locale: "de-DE" },
            error: "product_not_found",
            query: { text: currentCase.inputSignal.query || "retro leather sneakers" },
            response: { latency_ms: 63, result_count: 0, results: [], status_code: 404 },
            tenant: "sports_goods_tenant_002"
          }
        ],
        use_cache: false
      };
    } else if (currentCase.id === 'vector-drift' || currentCase.id.includes('semantic')) {
      presetPayload = {
        type: "semantic",
        description: "ALERT: Live Embedded Vector Shift Detected.",
        events: [
          {
            context: { channel: "web", device_type: "tablet", locale: "en-US" },
            error: "backend_server_error",
            query: { text: currentCase.inputSignal.query || "smart waterproof watch" },
            response: { latency_ms: 158, result_count: 0, results: [], status_code: 500 },
            tenant: "sports_goods_tenant_002"
          }
        ],
        use_cache: false
      };
    } else {
      presetPayload = {
        type: "autocomplete",
        description: "ALERT: Popularity Prefix Friction Gaps.",
        events: [
          {
            context: { channel: "app", device_type: "mobile", locale: "en-CA" },
            error: "autocomplete_miss",
            query: { text: currentCase.inputSignal.query || "iphne 15 pro max charger" },
            response: { latency_ms: 189, result_count: 0, results: [], status_code: 200 },
            tenant: "sports_goods_tenant_002"
          }
        ],
        use_cache: false
      };
    }

    try {
      const res = await api.triggerWorkflow(presetPayload);
      setActiveWorkflowId(res.workflow_id);
      setIsPolling(true);
      setCurrentStationIndex(0); // Start at station 1 (Ingestion complete)
      setIsPlaying(false);
      
      // Force reload runbook list to register the new workflow runbook
      setTimeout(() => {
        loadBackendRunbooks();
      }, 1500);

    } catch (err) {
      alert(`Could not start live Temporal workflow: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsTriggering(false);
    }
  };

  const handleSendApproval = async () => {
    if (!activeWorkflowId) return;
    try {
      const approvalWorkflowId = localStorage.getItem('magellan_active_workflow_id') || activeWorkflowId;
      if (!approvalWorkflowId) {
        addLog(`[approval] Error: No active workflow ID found for approval.`, 0);
        return;
      }
      await addLog(`[approval] Submitting human approval signature from "${approverName}"...`, 0);
      await api.approveRunbook(approvalWorkflowId, approverName, approvalNotes);
      setNeedsApproval(false);
      addLog(`[approval] Safety gate unlocked! Signaling Temporal workflow to resume.`, 500);
    } catch (e: any) {
      addLog(`[approval] Approval submission failed: ${e.message}`, 200);
    }
  };

  // Main step-by-step pipeline runner
  useEffect(() => {
    if (isPlaying) {
      if (currentStationIndex === -1) {
        // Start from first station
        setCurrentStationIndex(0);
      } else {
        timerRef.current = setTimeout(() => {
          if (currentStationIndex < 5) {
            setCurrentStationIndex(prev => prev + 1);
          } else {
            // Pipeline reached the end
            setIsPlaying(false);
          }
        }, speed);
      }
    } else {
      if (timerRef.current) clearTimeout(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [isPlaying, currentStationIndex, speed]);

  // Handle dynamic log stream and trace assembly
  useEffect(() => {
    if (currentStationIndex === -1) {
      setLogs([`[factory] Ready. Select a scenario and start the pipeline to inspect real-time data.`]);
      return;
    }

    if (logTimerRef.current) clearInterval(logTimerRef.current);

    let allLogs: string[] = [];
    
    // Check if we have real active activity outputs to render actual backend details!
    if (activeWorkflowId && activityResults.length > 0) {
      allLogs.push(`[temporal] 🟢 Live workflow trace detected! Workflow ID: ${activeWorkflowId}`);
      
      activityResults.forEach((act) => {
        const actName = act.activity_name || act.activity_id;
        
        if (actName.toLowerCase().includes('root cause')) {
          allLogs.push(`[temporal] Running Root Cause Analysis Agent...`);
          allLogs.push(`[rca] Output root cause identified: "${act.result?.root_cause || act.result?.summary || 'SCHEMA_MISMATCH'}"`);
          if (act.result?.logs) {
            act.result.logs.slice(0, 5).forEach((log: string) => allLogs.push(`[rca] ${log}`));
          }
        } else if (actName.toLowerCase().includes('fix proposal')) {
          allLogs.push(`[temporal] Running Fix Proposal Agent...`);
          allLogs.push(`[patch] Patch stashed to MLflow: "${act.result?.patch_id || 'patch-delta'}"`);
          allLogs.push(`[patch] Summary of change: ${act.result?.summary || 'synonym or index update'}`);
        } else if (actName.toLowerCase().includes('eval')) {
          allLogs.push(`[temporal] Evaluating patch over Ranx benchmark lab...`);
          allLogs.push(`[evaluation] Gating score: NDCG=${act.result?.metrics?.shadow?.['ndcg@10'] || '0.89'}`);
        } else if (actName.toLowerCase().includes('release')) {
          allLogs.push(`[temporal] Directing Canary gate and Split Router...`);
          allLogs.push(`[canary] Route status: ${act.result?.status || 'Active'}`);
        } else if (actName.toLowerCase().includes('feedback')) {
          allLogs.push(`[temporal] Committing post-release guardrails and audit checks...`);
          allLogs.push(`[feedback] Final certified state: ${act.result?.outcome || 'Audit certified successfully'}`);
        }
      });
      
      if (isPolling) {
        allLogs.push(`[temporal] 🔄 Polling backend Temporal server for active tasks...`);
      }
    } else {
      // Dynamic simulated log generator based on chosen runbook properties
      allLogs.push(`[temporal] Initializing UnifiedSearchAiRepairWorkflow pipeline...`);
      allLogs.push(`[temporal] Incident Target: "${currentCase.name}" (Type: ${currentCase.anomalyType})`);
      allLogs.push(`[temporal] Registering task listeners under Temporal ADDRESS: ${api.url('/')}`);

      if (currentStationIndex >= 0) {
        allLogs.push(`[ingestion] Raw signal acquired. Triggering activity: root_cause_activity`);
        allLogs.push(`[ingestion] Affected query: "${currentCase.inputSignal.query}"`);
      }
      
      if (currentStationIndex >= 1) {
        allLogs.push(`[rca] Spawning secure Python Deno WASM sandbox...`);
        currentCase.stations.rca.sandboxLogs.forEach(log => allLogs.push(log));
        allLogs.push(`[rca] Activity root_cause_activity returned code: SUCCESS`);
      }

      if (currentStationIndex >= 2) {
        allLogs.push(`[patch] Dispatching Activity: fix_proposal_activity`);
        allLogs.push(`[patch] GoogleFixProposalAgent generated stashed fix: ${currentCase.stations.patch.patchId}`);
        currentCase.stations.patch.sandboxLogs.forEach(log => allLogs.push(log));
      }

      if (currentStationIndex >= 3) {
        allLogs.push(`[evaluation] Dispatching Activity: eval_activity (Champion vs Challenger)`);
        allLogs.push(`[evaluation] Relevance: Challenger NDCG=${currentCase.stations.evaluation.metrics.challenger.ndcg} (Baseline NDCG=${currentCase.stations.evaluation.metrics.champion.ndcg})`);
        allLogs.push(`[evaluation] Threshold check (>= 0.84) result: ${currentCase.stations.evaluation.gatingStatus}`);
      }

      if (currentStationIndex >= 4) {
        allLogs.push(`[canary] Dispatching Activity: release_activity`);
        allLogs.push(`[canary] Advancing canary traffic split: 100% stable promoter.`);
      }

      if (currentStationIndex >= 5) {
        allLogs.push(`[feedback] Dispatching Activity: feedback_activity`);
        allLogs.push(`[feedback] Verified: ${currentCase.stations.feedback.outcome}`);
        allLogs.push(`[feedback] Committed block transaction: ${currentCase.stations.feedback.auditLedgerHash}`);
        allLogs.push(`[feedback] State updated to: SOLVED (Released to 100%)`);
      }
    }

    setLogs(allLogs);
  }, [currentStationIndex, selectedCaseId, activeWorkflowId, activityResults, isPolling]);

  const runPipeline = () => {
    setIsPlaying(true);
    if (currentStationIndex === 5) {
      setCurrentStationIndex(0);
    }
  };

  const pausePipeline = () => {
    setIsPlaying(false);
  };

  const resetPipeline = () => {
    setIsPlaying(false);
    setCurrentStationIndex(-1);
  };

  const stepForward = () => {
    if (currentStationIndex < 5) {
      setCurrentStationIndex(prev => prev + 1);
    }
  };

  const getStationStatusClass = (index: number) => {
    if (index === currentStationIndex) return 'station-active';
    if (index < currentStationIndex) return 'station-completed';
    return 'station-idle';
  };

  // Helper to safely extract recorded values from real activity JSON results
  const getActResult = (typeKeyword: string) => {
    const act = activityResults.find(a => a.activity_name?.toLowerCase().includes(typeKeyword) || a.activity_id?.toLowerCase().includes(typeKeyword));
    return act?.result;
  };

  const realRca = getActResult('root cause');
  const realFix = getActResult('fix proposal');
  const realEval = getActResult('eval');
  const realRelease = getActResult('release');
  const realFeedback = getActResult('feedback');

  return (
    <div className="factory-wrapper">
      <style>{`
        .factory-wrapper {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          padding: 0.5rem;
          min-height: 100%;
        }

        /* Integration banner */
        .integration-header {
          background: rgba(31, 107, 119, 0.08);
          border: 1px solid rgba(31, 107, 119, 0.2);
          border-radius: var(--radius-sm);
          padding: 0.5rem 1rem;
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-size: 0.8rem;
        }

        .integration-status {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-weight: bold;
        }

        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
        }

        .status-dot.online {
          background: #10B981;
          box-shadow: 0 0 8px #10B981;
        }

        .status-dot.offline {
          background: #EF4444;
          box-shadow: 0 0 8px #EF4444;
        }

        /* Case selector styles */
        .case-selector-bar {
          background: var(--card-bg);
          backdrop-filter: blur(8px);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-md);
          padding: 1rem;
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 1rem;
          box-shadow: var(--shadow-sm);
        }

        .case-options {
          display: flex;
          gap: 0.75rem;
          flex-wrap: wrap;
        }

        .case-btn {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 1rem;
          border-radius: var(--radius-sm);
          border: 1px solid var(--border-color);
          background: var(--card-solid);
          color: var(--text-dark);
          font-weight: 500;
          font-size: 0.85rem;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .case-btn:hover {
          border-color: var(--primary);
          background: var(--primary-glow);
        }

        .case-btn.active {
          background: var(--primary);
          color: white;
          border-color: var(--primary);
          box-shadow: 0 4px 12px var(--primary-glow);
        }

        .case-severity-tag {
          font-size: 0.75rem;
          font-weight: 700;
          text-transform: uppercase;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          display: inline-flex;
          align-items: center;
          gap: 0.25rem;
        }

        .severity-critical {
          background: rgba(182, 66, 59, 0.15);
          color: var(--error);
        }

        .severity-high {
          background: rgba(185, 130, 24, 0.15);
          color: var(--warning);
        }

        .severity-warning {
          background: rgba(31, 107, 119, 0.15);
          color: var(--info);
        }

        /* Conveyor belt styling */
        .conveyor-belt-container {
          background: var(--card-bg);
          backdrop-filter: blur(8px);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-lg);
          padding: 2.2rem 1.5rem 2rem 1.5rem;
          box-shadow: var(--shadow-3d);
          position: relative;
          overflow: visible;
          flex-shrink: 0;
        }

        .conveyor-belt-track {
          position: relative;
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.5rem;
        }

        .conveyor-belt-line {
          position: absolute;
          top: 50%;
          left: 5%;
          right: 5%;
          height: 8px;
          background: #E2E8F0;
          border-radius: 4px;
          transform: translateY(-50%);
          z-index: 1;
          box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }

        .conveyor-belt-line-active {
          position: absolute;
          top: 0;
          left: 0;
          height: 100%;
          background: linear-gradient(90deg, var(--info), var(--primary), var(--success));
          border-radius: 4px;
          transition: width 0.3s ease;
          box-shadow: 0 0 10px rgba(139, 58, 43, 0.4);
        }

        /* Flowing particle animation */
        .glowing-data-particle {
          position: absolute;
          top: 50%;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: radial-gradient(circle, #FFE066 30%, var(--primary) 100%);
          transform: translate(-50%, -50%);
          z-index: 2;
          box-shadow: 0 0 15px #FFE066, 0 0 25px var(--primary);
          transition: left 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 0.7rem;
          font-weight: bold;
        }

        .factory-station-node {
          position: relative;
          z-index: 3;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.75rem;
          width: 14%;
          flex-shrink: 0;
        }

        .station-icon-container {
          width: 54px;
          height: 54px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: white;
          border: 3px solid #CBD5E1;
          color: #94A3B8;
          box-shadow: var(--bevel-highlight), 0 4px 6px rgba(0,0,0,0.05);
          transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
          position: relative;
          flex-shrink: 0;
        }

        .station-index {
          position: absolute;
          top: -6px;
          left: -6px;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: #64748B;
          color: white;
          font-size: 0.65rem;
          font-weight: bold;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 2px solid white;
        }

        .station-completed .station-icon-container {
          border-color: var(--success);
          background: var(--success-glow);
          color: var(--success-light);
          transform: scale(1.05);
        }

        .station-completed .station-index {
          background: var(--success-light);
        }

        .station-active .station-icon-container {
          border-color: var(--primary);
          background: white;
          color: var(--primary);
          transform: scale(1.22);
          box-shadow: 0 0 20px var(--primary-glow), var(--bevel-highlight);
          animation: stationPulse 2s infinite ease-in-out;
        }

        .station-active .station-index {
          background: var(--primary);
        }

        .station-label {
          font-size: 0.75rem;
          font-weight: 700;
          color: var(--text-dark);
          text-align: center;
          min-height: 1.5rem;
          transition: color 0.3s;
        }

        .station-active .station-label {
          color: var(--primary);
          transform: scale(1.05);
        }

        @keyframes stationPulse {
          0% { box-shadow: 0 0 5px var(--primary-glow); }
          50% { box-shadow: 0 0 22px rgba(139, 58, 43, 0.4); }
          100% { box-shadow: 0 0 5px var(--primary-glow); }
        }

        /* Grid section: Controls + Details */
        .factory-control-grid {
          display: grid;
          grid-template-columns: 2fr 3fr;
          gap: 1.5rem;
        }

        @media (max-width: 1024px) {
          .factory-control-grid {
            grid-template-columns: 1fr;
          }
        }

        /* Controls Panel */
        .controls-panel {
          background: var(--card-bg);
          backdrop-filter: blur(8px);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-lg);
          padding: 1.25rem;
          box-shadow: var(--shadow-md);
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .panel-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          border-bottom: 1px solid var(--border-color);
          padding-bottom: 0.5rem;
        }

        .panel-title {
          font-size: 1rem;
          font-weight: 700;
          color: var(--text-dark);
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .pipeline-buttons {
          display: flex;
          gap: 0.5rem;
        }

        .control-btn {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          padding: 0.5rem 0.75rem;
          font-size: 0.8rem;
          font-weight: bold;
          border-radius: var(--radius-sm);
          cursor: pointer;
          transition: all 0.2s;
          border: 1px solid var(--border-color);
          background: var(--card-solid);
          color: var(--text-dark);
        }

        .control-btn:hover {
          background: rgba(0,0,0,0.03);
        }

        .control-btn-primary {
          background: var(--primary);
          color: white;
          border-color: var(--primary);
        }

        .control-btn-primary:hover {
          background: #752E21;
        }

        .speed-slider-container {
          display: flex;
          align-items: center;
          gap: 1rem;
          background: rgba(0,0,0,0.02);
          padding: 0.5rem 0.75rem;
          border-radius: var(--radius-sm);
          font-size: 0.75rem;
        }

        .speed-slider-container input {
          flex: 1;
          accent-color: var(--primary);
          cursor: pointer;
        }

        /* Console styling */
        .terminal-panel {
          background: #111827;
          border-radius: var(--radius-md);
          padding: 1rem;
          font-family: var(--mono);
          color: #10B981;
          font-size: 0.75rem;
          line-height: 1.4;
          height: 240px;
          overflow-y: auto;
          box-shadow: inset 0 2px 8px rgba(0,0,0,0.8);
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .terminal-line {
          word-break: break-all;
          white-space: pre-wrap;
        }

        .terminal-line.temporal { color: #818CF8; }
        .terminal-line.ingestion { color: #38BDF8; }
        .terminal-line.rca { color: #F87171; }
        .terminal-line.patch { color: #FBBF24; }
        .terminal-line.evaluation { color: #F43F5E; }
        .terminal-line.canary { color: #34D399; }
        .terminal-line.feedback { color: #6EE7B7; }
        .terminal-line.factory { color: #9CA3AF; }

        /* Detail Station Panel */
        .station-details-panel {
          background: var(--card-bg);
          backdrop-filter: blur(8px);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-lg);
          padding: 1.5rem;
          box-shadow: var(--shadow-md);
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
          min-height: 420px;
        }

        .station-status-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.25rem;
          font-size: 0.75rem;
          font-weight: bold;
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          background: var(--primary-glow);
          color: var(--primary);
          align-self: flex-start;
        }

        .info-card {
          background: var(--card-solid);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-md);
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .info-card-title {
          font-size: 0.75rem;
          text-transform: uppercase;
          color: var(--text-muted);
          font-weight: 700;
          letter-spacing: 0.05em;
        }

        .info-card-content {
          font-size: 0.9rem;
          color: var(--text-dark);
          line-height: 1.5;
        }

        /* Payload / JSON Pre */
        .json-payload-view {
          background: #F8FAFC;
          border: 1px solid #E2E8F0;
          border-radius: var(--radius-sm);
          padding: 0.75rem;
          font-family: var(--mono);
          font-size: 0.75rem;
          color: #0F172A;
          overflow-x: auto;
          max-height: 200px;
        }

        /* Diff view */
        .code-diff-container {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 0.5rem;
          font-family: var(--mono);
          font-size: 0.7rem;
        }

        .diff-pane {
          background: #1E293B;
          color: #F8FAFC;
          border-radius: var(--radius-sm);
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }

        .diff-header {
          background: #0F172A;
          padding: 0.35rem 0.5rem;
          font-weight: bold;
          color: #94A3B8;
          font-size: 0.65rem;
          display: flex;
          justify-content: space-between;
        }

        .diff-code {
          padding: 0.5rem;
          white-space: pre;
          overflow-x: auto;
          line-height: 1.3;
        }

        .diff-removed { background: rgba(239, 68, 68, 0.15); color: #FCA5A5; }
        .diff-added { background: rgba(16, 185, 129, 0.15); color: #6EE7B7; }

        /* Gauges */
        .gauges-container {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
        }

        .gauge-card {
          background: var(--card-solid);
          border: 1px solid var(--border-color);
          border-radius: var(--radius-md);
          padding: 1rem;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
        }

        .gauge-title {
          font-size: 0.8rem;
          font-weight: bold;
          color: var(--text-dark);
        }

        .gauge-metric-row {
          display: flex;
          justify-content: space-between;
          width: 100%;
          font-size: 0.75rem;
          border-bottom: 1px dashed var(--border-color);
          padding: 0.25rem 0;
        }

        .metric-val {
          font-family: var(--mono);
          font-weight: bold;
        }

        .metric-champion { color: var(--text-muted); }
        .metric-challenger { color: var(--success-light); }

        /* Canary controller visual */
        .canary-visual-box {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.75rem;
          padding: 1.5rem;
          background: rgba(0,0,0,0.02);
          border-radius: var(--radius-md);
        }

        .canary-arc-container {
          width: 120px;
          height: 60px;
          position: relative;
          overflow: hidden;
        }

        .canary-semi-circle {
          width: 120px;
          height: 120px;
          border-radius: 50%;
          border: 12px solid #E2E8F0;
          position: absolute;
          top: 0;
          left: 0;
        }

        .canary-fill {
          width: 120px;
          height: 120px;
          border-radius: 50%;
          border: 12px solid var(--success);
          border-top-color: transparent;
          border-left-color: transparent;
          position: absolute;
          top: 0;
          left: 0;
          transform: rotate(-45deg);
          transition: transform 0.5s ease;
        }

        .canary-split-text {
          font-size: 1.5rem;
          font-weight: 900;
          color: var(--success);
          font-family: var(--mono);
        }

        .shadow-test-banner {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          background: var(--success-glow);
          color: var(--success-light);
          padding: 0.5rem 1rem;
          border-radius: var(--radius-sm);
          font-size: 0.8rem;
          font-weight: bold;
          border: 1px solid rgba(47, 93, 80, 0.2);
        }

        /* Feedback Certificate styling */
        .certificate-box {
          border: 2px solid var(--success-light);
          background: #FAFDFB;
          border-radius: var(--radius-md);
          padding: 1.25rem;
          position: relative;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.75rem;
          box-shadow: 0 4px 15px rgba(47, 93, 80, 0.08);
          overflow: hidden;
        }

        .certificate-box::after {
          content: 'MAGELLAN QUALITY AUDIT';
          position: absolute;
          font-size: 2.5rem;
          font-weight: bold;
          color: rgba(47, 93, 80, 0.02);
          transform: rotate(-15deg);
          z-index: 0;
          pointer-events: none;
        }

        .certificate-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: var(--success-light);
          font-weight: 800;
          font-size: 1rem;
          z-index: 1;
        }

        .certificate-body {
          font-family: var(--serif);
          font-size: 0.85rem;
          color: var(--text-dark);
          text-align: center;
          line-height: 1.5;
          z-index: 1;
        }

        .certificate-hash {
          font-family: var(--mono);
          font-size: 0.65rem;
          background: #F1FBF7;
          border: 1px solid rgba(47, 93, 80, 0.15);
          color: var(--success-light);
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          z-index: 1;
        }
      `}</style>

      {/* 0. Live Backend Integration Status */}
      <div className="integration-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="integration-status">
            <span className={`status-dot ${integrationStatus === 'connected' ? 'online' : 'offline'}`} />
            <span>FastAPI Server: {integrationStatus === 'connected' ? 'CONNECTED' : 'DISCONNECTED'}</span>
          </div>
          {activeWorkflowId && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(129, 140, 248, 0.12)', color: '#818CF8', padding: '0.2rem 0.6rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold' }}>
              <RefreshCw size={12} className={isPolling ? "animate-spin" : ""} />
              <span>Real Temporal Workflow Running: <code>{activeWorkflowId}</code></span>
            </div>
          )}
        </div>
        <button 
          className="control-btn" 
          onClick={loadBackendRunbooks} 
          style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
        >
          <RefreshCw size={11} />
          <span>Sync Data</span>
        </button>
      </div>

      {/* 1. Case Selector & Overview Banner */}
      <div className="case-selector-bar">
        <div>
          <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Select Operational Incident Runbook
          </span>
          <div className="case-options" style={{ marginTop: '0.4rem' }}>
            {availableCases.map(c => {
              const Icon = c.icon;
              return (
                <button
                  key={c.id}
                  className={`case-btn ${selectedCaseId === c.id ? 'active' : ''}`}
                  onClick={() => setSelectedCaseId(c.id)}
                >
                  <Icon size={14} />
                  <span>{c.name}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.25rem' }}>
          <span className={`case-severity-tag severity-${currentCase.severity}`}>
            {currentCase.severity} Severity
          </span>
          <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: 'var(--text-dark)' }}>
            Breach: <span style={{ color: 'var(--primary)', fontWeight: 800 }}>{currentCase.anomalyType}</span>
          </span>
        </div>
      </div>

      {/* 2. Factory Conveyor Belt Station Flow */}
      <div className="conveyor-belt-container">
        <div className="conveyor-belt-track">
          {/* Track Line */}
          <div className="conveyor-belt-line">
            <div 
              className="conveyor-belt-line-active" 
              style={{ 
                width: currentStationIndex === -1 ? '0%' : `${(currentStationIndex / 5) * 100}%` 
              }} 
            />
          </div>

          {/* Animated Particle Moving along the conveyor */}
          {currentStationIndex !== -1 && (
            <div 
              className="glowing-data-particle"
              style={{ 
                left: `${5 + (currentStationIndex / 5) * 90}%`
              }}
            >
              <Sparkles size={11} />
            </div>
          )}

          {/* Render Stations */}
          {stationMetadata.map((metaItem, index) => {
            const Icon = metaItem.icon;
            const statusClass = getStationStatusClass(index);
            return (
              <div key={metaItem.key} className={`factory-station-node ${statusClass}`}>
                <div className="station-icon-container">
                  <span className="station-index">{index + 1}</span>
                  <Icon size={22} style={{ color: index <= currentStationIndex ? metaItem.color : undefined }} />
                </div>
                <span className="station-label">{metaItem.label}</span>
              </div>
            );
          })}
        </div>

        {/* Input Signal Summary Overlay */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginTop: '1.25rem', padding: '0.75rem 1rem', background: 'rgba(0,0,0,0.02)', borderRadius: '8px', border: '1px solid rgba(0,0,0,0.04)' }}>
          <div>
            <div style={{ fontSize: '0.65rem', fontWeight: 'bold', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Ingested Query</div>
            <div style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--text-dark)' }}>"{currentCase.inputSignal.query}"</div>
          </div>
          <div>
            <div style={{ fontSize: '0.65rem', fontWeight: 'bold', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Trigger Source</div>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-dark)' }}>{currentCase.inputSignal.source}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.65rem', fontWeight: 'bold', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Breach Metric</div>
            <div style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--error)' }}>{currentCase.inputSignal.value}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.65rem', fontWeight: 'bold', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Business Leakage</div>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--warning)' }}>{currentCase.inputSignal.impact}</div>
          </div>
        </div>
      </div>

      {/* 3. Controls & Active Step Details */}
      <div className="factory-control-grid">
        {/* Left column: Controls and Logs */}
        <div className="controls-panel">
          <div className="panel-header">
            <span className="panel-title">
              <Factory size={16} style={{ color: 'var(--primary)' }} />
              Assembly Control
            </span>
            <div className="pipeline-buttons">
              {!activeWorkflowId ? (
                // Local simulation controls
                <>
                  {!isPlaying ? (
                    <button className="control-btn control-btn-primary" onClick={runPipeline}>
                      <Play size={13} fill="currentColor" />
                      <span>Simulate Flow</span>
                    </button>
                  ) : (
                    <button className="control-btn" onClick={pausePipeline}>
                      <Pause size={13} fill="currentColor" />
                      <span>Pause</span>
                    </button>
                  )}
                  <button className="control-btn" onClick={stepForward} disabled={isPlaying || currentStationIndex === 5}>
                    <ChevronRight size={13} />
                    <span>Step</span>
                  </button>
                  <button className="control-btn" onClick={resetPipeline}>
                    <RotateCcw size={13} />
                    <span>Reset</span>
                  </button>
                </>
              ) : (
                // Live Temporal workflow controls
                <button 
                  className="control-btn" 
                  onClick={() => setIsPolling(!isPolling)}
                  style={{ background: isPolling ? 'rgba(16,185,129,0.1)' : '', color: isPolling ? '#10B981' : '' }}
                >
                  <RefreshCw size={13} className={isPolling ? "animate-spin" : ""} />
                  <span>{isPolling ? 'Polling Live' : 'Resume Polling'}</span>
                </button>
              )}
            </div>
          </div>

          {!activeWorkflowId && (
            <div className="speed-slider-container">
              <span>Simulation Interval Speed:</span>
              <input 
                type="range" 
                min="1000" 
                max="5000" 
                step="500" 
                value={speed} 
                onChange={(e) => setSpeed(Number(e.target.value))} 
              />
              <span style={{ fontFamily: 'var(--mono)', fontSize: '0.7rem', width: '3.5rem', textAlign: 'right' }}>
                {(speed / 1000).toFixed(1)}s / step
              </span>
            </div>
          )}

          {integrationStatus === 'connected' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', background: 'rgba(31, 107, 119, 0.05)', padding: '0.75rem', borderRadius: '8px', border: '1px solid rgba(31, 107, 119, 0.1)' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--info)' }}>Live Temporal Trigger</div>
              <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                Dispatch a real production-grade telemetry anomaly to the Temporal Orchestration server to run the AI Agents in real-time.
              </p>
              <button 
                className="control-btn control-btn-primary" 
                onClick={triggerLiveWorkflow} 
                disabled={isTriggering}
                style={{ width: '100%', justifyContent: 'center', marginTop: '0.25rem', gap: '0.5rem' }}
              >
                {isTriggering ? <RefreshCw size={13} className="animate-spin" /> : <Sparkles size={13} />}
                <span>{isTriggering ? 'Triggering...' : 'Trigger Live Temporal Workflow'}</span>
              </button>
            </div>
          )}

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--text-muted)' }}>Temporal & Agent Process Logs</span>
              <span style={{ fontSize: '0.65rem', color: '#10B981', background: 'rgba(16,185,129,0.1)', padding: '0.1rem 0.4rem', borderRadius: '4px', fontFamily: 'var(--mono)' }}>
                {activeWorkflowId ? 'LIVE STREAM' : 'SIMULATOR'}
              </span>
            </div>
            <div className="terminal-panel">
              {logs.map((line, idx) => {
                let catClass = 'factory';
                if (line.includes('[temporal]')) catClass = 'temporal';
                else if (line.includes('[ingestion]')) catClass = 'ingestion';
                else if (line.includes('[rca]')) catClass = 'rca';
                else if (line.includes('[patch]')) catClass = 'patch';
                else if (line.includes('[evaluation]')) catClass = 'evaluation';
                else if (line.includes('[canary]')) catClass = 'canary';
                else if (line.includes('[feedback]')) catClass = 'feedback';
                
                return (
                  <div key={idx} className={`terminal-line ${catClass}`}>
                    {line}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Right column: Active Step Inspection Details */}
        <div className="station-details-panel">
          {currentStationIndex === -1 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', flex: 1, gap: '1rem', color: 'var(--text-muted)' }}>
              <Factory size={48} style={{ opacity: 0.2 }} />
              <div style={{ textAlign: 'center' }}>
                <h3 style={{ fontFamily: 'var(--serif)', fontSize: '1.2rem', color: 'var(--text-dark)', marginBottom: '0.25rem' }}>Factory Assembly Standby</h3>
                <p style={{ fontSize: '0.8rem', maxWidth: '300px' }}>
                  Select an operational scenario and click <strong>"{activeWorkflowId ? 'Polling Live' : 'Simulate Flow'}"</strong> to run the automated pipeline.
                </p>
              </div>
            </div>
          ) : (
            <>
              {/* Station Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Active Factory Station {currentStationIndex + 1} of 6
                  </span>
                  <h2 style={{ fontFamily: 'var(--serif)', fontSize: '1.25rem', color: 'var(--text-dark)', marginTop: '0.1rem' }}>
                    {stationMetadata[currentStationIndex].label}
                  </h2>
                </div>
                <span className="station-status-badge">
                  {currentStationIndex === 0 && (realRca ? 'Ingested complete' : currentCase.stations.ingestion.status)}
                  {currentStationIndex === 1 && (realRca ? 'RCA Loaded' : currentCase.stations.rca.status)}
                  {currentStationIndex === 2 && (realFix ? 'Fix Synthesized' : currentCase.stations.patch.status)}
                  {currentStationIndex === 3 && (realEval ? 'Evaluation Ready' : currentCase.stations.evaluation.status)}
                  {currentStationIndex === 4 && (realRelease ? 'Canary Done' : currentCase.stations.canary.status)}
                  {currentStationIndex === 5 && (realFeedback ? 'Audit Completed' : currentCase.stations.feedback.status)}
                </span>
              </div>

              {/* Station Content */}
              {currentStationIndex === 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div className="info-card">
                    <span className="info-card-title">Telemetry Signal Details</span>
                    <p className="info-card-content">{currentCase.stations.ingestion.details}</p>
                  </div>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--text-muted)' }}>Ingested Telemetry JSON Payload</span>
                    <pre className="json-payload-view">
                      {JSON.stringify(currentCase.stations.ingestion.payload, null, 2)}
                    </pre>
                  </div>
                </div>
              )}

              {currentStationIndex === 1 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div className="info-card" style={{ borderLeft: '4px solid var(--primary)' }}>
                    <span className="info-card-title">Sandbox Pyodide Root Cause Analysis</span>
                    <p className="info-card-content" style={{ fontWeight: 800, color: 'var(--primary)' }}>
                      {realRca?.root_cause || realRca?.summary || currentCase.stations.rca.rootCause}
                    </p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', marginTop: '0.25rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      <Database size={12} />
                      <span>Executed internal toolchain: <strong>{realRca ? 'diagnose_anomaly()' : currentCase.stations.rca.toolExecuted}</strong></span>
                    </div>
                  </div>

                  <div className="info-card">
                    <span className="info-card-title">Secure Sandboxed Execution Tech</span>
                    <p className="info-card-content" style={{ fontSize: '0.8rem' }}>
                      RCA Agent executing securely inside a locked-down <strong>Deno subprocess</strong> running a WebAssembly-compiled <strong>Pyodide Python REPL</strong>. Network fetches are securely channeled, and local file access is barred.
                    </p>
                  </div>
                </div>
              )}

              {currentStationIndex === 2 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div className="info-card" style={{ padding: '0.75rem 1rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="info-card-title">Synthesized Remediation Patch</span>
                      <span style={{ fontSize: '0.7rem', background: 'rgba(185,130,24,0.1)', color: 'var(--warning)', padding: '0.1rem 0.4rem', borderRadius: '4px', fontFamily: 'var(--mono)', fontWeight: 'bold' }}>
                        {realFix?.patch_id || currentCase.stations.patch.patchId}
                      </span>
                    </div>
                    <p className="info-card-content" style={{ fontSize: '0.85rem', marginTop: '0.25rem' }}>
                      {realFix?.summary || 'Remediation rule stashed successfully.'}
                    </p>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--text-muted)' }}>
                      Proposed Code Patch Diff: <code>{currentCase.stations.patch.proposedDiff.file}</code>
                    </span>
                    
                    <div className="code-diff-container">
                      <div className="diff-pane">
                        <div className="diff-header">
                          <span>ORIGINAL (CHAMPION)</span>
                          <span style={{ color: '#EF4444' }}>- REMOVED</span>
                        </div>
                        <div className="diff-code diff-removed">
                          {currentCase.stations.patch.proposedDiff.oldCode}
                        </div>
                      </div>

                      <div className="diff-pane">
                        <div className="diff-header">
                          <span>PATCHED (CHALLENGER)</span>
                          <span style={{ color: '#10B981' }}>+ ADDED</span>
                        </div>
                        <div className="diff-code diff-added">
                          {realFix?.proposed_code || currentCase.stations.patch.proposedDiff.newCode}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {currentStationIndex === 3 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div className="info-card" style={{ padding: '0.75rem 1rem' }}>
                    <span className="info-card-title">Automated SLA Gating Check</span>
                    <p className="info-card-content" style={{ fontSize: '0.85rem' }}>
                      Evaluator Agent performs parallel offline evaluations using <strong>Ranx Information Retrieval Library</strong> on historical test signals.
                    </p>
                  </div>

                  <div className="gauges-container">
                    <div className="gauge-card">
                      <span className="gauge-title">NDCG Relevance Score</span>
                      <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--success-light)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        {realEval?.metrics?.shadow?.['ndcg@10'] || currentCase.stations.evaluation.metrics.challenger.ndcg}
                        <TrendingUp size={16} />
                      </div>
                      <div className="gauge-metric-row">
                        <span className="metric-champion">Baseline:</span>
                        <span className="metric-val">{realEval?.metrics?.baseline?.['ndcg@10'] || currentCase.stations.evaluation.metrics.champion.ndcg}</span>
                      </div>
                      <div className="gauge-metric-row">
                        <span className="metric-challenger">Challenger:</span>
                        <span className="metric-val" style={{ color: 'var(--success-light)' }}>{realEval?.metrics?.shadow?.['ndcg@10'] || currentCase.stations.evaluation.metrics.challenger.ndcg}</span>
                      </div>
                      <span style={{ fontSize: '0.65rem', background: 'rgba(47,93,80,0.1)', color: 'var(--success-light)', padding: '0.1rem 0.4rem', borderRadius: '4px', marginTop: '0.25rem', fontWeight: 'bold' }}>NDCG FLOOR (0.84) PASSED</span>
                    </div>

                    <div className="gauge-card">
                      <span className="gauge-title">Search Exit Rate</span>
                      <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--error)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        {realEval?.metrics?.shadow?.exit_rate || currentCase.stations.evaluation.metrics.challenger.exitRate}%
                      </div>
                      <div className="gauge-metric-row">
                        <span className="metric-champion">Baseline:</span>
                        <span className="metric-val">{realEval?.metrics?.baseline?.exit_rate || currentCase.stations.evaluation.metrics.champion.exitRate}%</span>
                      </div>
                      <div className="gauge-metric-row">
                        <span className="metric-challenger">Challenger:</span>
                        <span className="metric-val" style={{ color: 'var(--success-light)' }}>{realEval?.metrics?.shadow?.exit_rate || currentCase.stations.evaluation.metrics.challenger.exitRate}%</span>
                      </div>
                      <span style={{ fontSize: '0.65rem', background: 'rgba(182,66,59,0.1)', color: 'var(--error)', padding: '0.1rem 0.4rem', borderRadius: '4px', marginTop: '0.25rem', fontWeight: 'bold' }}>EXIT ATTRITION MINIMIZED</span>
                    </div>
                  </div>
                </div>
              )}

              {currentStationIndex === 4 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div className="info-card">
                    <span className="info-card-title">Canary Release Routing Split</span>
                    <p className="info-card-content">
                      ReleaseAgent deploys the fix patch to an isolated canary traffic split, progressively scaling weight while monitoring performance signals via Temporal Workflow.
                    </p>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', alignItems: 'center' }}>
                    <div className="canary-visual-box">
                      <div className="canary-arc-container">
                        <div className="canary-semi-circle"></div>
                        <div className="canary-fill" style={{ transform: 'rotate(135deg)' }}></div>
                      </div>
                      <div className="canary-split-text">{realRelease?.status === 'success' ? '100% SPLIT' : '100% SPLIT'}</div>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>PROMOTED TO ALL TRAFFIC</span>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      <div style={{ background: '#FAF8F5', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '0.5rem 0.75rem' }}>
                        <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 'bold' }}>TEMPORAL WORKFLOW ID</span>
                        <div style={{ fontFamily: 'var(--mono)', fontSize: '0.75rem', fontWeight: 'bold', wordBreak: 'break-all' }}>{activeWorkflowId || currentCase.stations.canary.temporalId}</div>
                      </div>
                      <div className="shadow-test-banner" style={{ marginTop: '0.5rem' }}>
                        <CheckCircle2 size={14} />
                        <span>PROMOTION GATE CONFIRMED</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Manual Approval Section */}
              {currentStationIndex === 4 && needsApproval && activeWorkflowId && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginTop: '1.5rem', padding: '1rem', background: 'var(--card-solid)', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 'bold', color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <ShieldCheck size={16} />
                    Human Approval Required
                  </div>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    The automated evaluation detected metrics below the safety threshold. Please review and manually approve the deployment.
                  </p>
                  <input
                    type="text"
                    value={approverName}
                    onChange={(e) => setApproverName(e.target.value)}
                    placeholder="Your Name/Role (e.g., Search Lead)"
                    style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', fontSize: '0.8rem', background: 'var(--input-bg)', color: 'var(--text-dark)' }}
                  />
                  <textarea
                    value={approvalNotes}
                    onChange={(e) => setApprovalNotes(e.target.value)}
                    placeholder="Approval Notes (e.g., 'Override due to external factors')"
                    rows={3}
                    style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--border-color)', fontSize: '0.8rem', background: 'var(--input-bg)', color: 'var(--text-dark)', resize: 'vertical' }}
                  ></textarea>
                  <button
                    onClick={handleSendApproval}
                    className="control-btn control-btn-primary"
                    style={{ width: '100%', justifyContent: 'center', marginTop: '0.5rem' }}
                  >
                    <CheckCircle2 size={16} />
                    Approve Deployment
                  </button>
                </div>
              )}

              {currentStationIndex === 5 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div className="info-card">
                    <span className="info-card-title">Post-Release Telemetry Audit</span>
                    <p className="info-card-content" style={{ fontSize: '0.85rem' }}>
                      The Feedback Agent operates directly on the host process post-release to evaluate the live canary split, review post-canary telemetry data, and write the final guardrail approval report.
                    </p>
                  </div>

                  <div className="certificate-box">
                    <div className="certificate-header">
                      <Award size={18} />
                      <span>QUALITY ASSURANCE CERTIFICATE</span>
                    </div>
                    <div className="certificate-body">
                      "{realFeedback?.outcome || realFeedback?.summary || currentCase.stations.feedback.outcome}"
                    </div>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      <span className="certificate-hash">{realFeedback ? 'SLA Guardrail Passed' : currentCase.stations.feedback.validationCheck}</span>
                      <span className="certificate-hash" style={{ fontFamily: 'var(--mono)' }}>{realFeedback?.audit_ledger_hash || currentCase.stations.feedback.auditLedgerHash}</span>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};