export interface AgentProfile {
  name: string;
  role: string;
  autonomyLevel: string;
  behaviors: string[];
  decisionRecord: string;
}

export interface TemporalMetadata {
  workflowId: string;
  cadence: string;
  retryPolicy: string;
  sla: string;
  checkpoints: string[];
}

export interface HumanApprovalGate {
  mode: 'auto' | 'required' | 'conditional';
  owner: string;
  status: string;
  reason: string;
  expiry: string;
  record: string;
}

export interface MonitoringSignal {
  label: string;
  value: string;
  status: 'healthy' | 'watch' | 'blocked';
  detail: string;
}

export interface LiveRunbookMetrics {
  queryVolume: number;
  exitRate: number;
  revenueLoss: number;
  baselineNdcg: number;
  proposedNdcg: number;
  p95Latency: number;
}

export interface Runbook {
  id: string;
  title: string;
  description: string;
  visualCode: string;
  capability: 'semantic search' | 'smart autocomplete' | 'merchandising';
  signalType: 'catalog gap' | 'zero-result cluster' | 'mxp rule conflict';
  risk: 'med' | 'high' | 'low';
  confidence: number;
  tags: string[];
  status: 'Eval Ready' | 'Shadow Test' | 'Canary 5%' | 'Canary 25%' | 'Canary 100%' | 'Owner Review' | 'Rollback Candidate' | 'Released' | 'Rolled Back';
  offlineEvalCoverage: number;
  businessImpact: number;
  rootCause: string;
  businessImpactSummary: string;
  problemStatement: string;
  fixSummary: string;
  fixPlanSteps: string[];
  approvalPolicy: string;
  evidenceNotes: string;
  agent: AgentProfile;
  temporal: TemporalMetadata;
  humanApproval: HumanApprovalGate;
  monitoringSignals: MonitoringSignal[];
  feedbackLoop: string;
  liveMetrics: LiveRunbookMetrics;
  accent: string;
  accentGlow: string;
  accentBorder: string;
  beforeQuery: string;
  beforeResults: Array<{ name: string; price: number; stock: number; score?: string; detail?: string }>;
  afterResults: Array<{ name: string; price: number; stock: number; score?: string; detail?: string }>;
}

export interface Skills {
  catalogEnrichment: boolean;
  semanticIndex: boolean;
  autocompleteTuning: boolean;
  mxpGovernance: boolean;
  multimodalQa: boolean;
}

export interface AuditRow {
  time: string;
  runbookId: string;
  title: string;
  action: string;
  approver: string;
  agentName: string;
  agentBehavior: string;
  temporalWorkflowId: string;
  approvalGate: string;
  monitoringSummary: string;
  feedbackRecord: string;
  recordType: 'evaluation' | 'approval' | 'release' | 'rollback' | 'monitoring';
  hash: string;
  isRollback?: boolean;
}

export interface TriggerWorkflowResponse {
  workflow_id: string;
}


export interface QueryClusterRow {
  query: string;
  volume: string;
  exits: string;
  loss: string;
  impact: 'High' | 'Med' | 'Low';
  tag: string;
  badgeClass: 'waterproof' | 'typo' | 'rules';
  status: string;
}
