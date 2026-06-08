import type { AuditRow, QueryClusterRow, Runbook } from './types';

const getDefaultApiBaseUrl = () => {
  if (typeof window === 'undefined') return 'http://localhost:8000';

  const { protocol, hostname } = window.location;
  return `${protocol}//${hostname}:8000`;
};

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || getDefaultApiBaseUrl();

export type RunbookAction = 'evaluate' | 'release' | 'rollback';

export interface TemporalLink {
  namespace: string;
  workflows_url: string;
  redirect_endpoint: string;
}

export interface TemporalWorkflowSummary {
  runbook_id: string;
  title: string;
  workflow_id: string;
  status: string;
  cadence: string;
  retry_policy: string;
  sla: string;
  checkpoints: string[];
}

export interface TemporalDetails {
  namespace: string;
  status: string;
  workflows_url: string;
  redirect_endpoint: string;
  cors_origins: string[];
  backend_endpoints: Record<string, string>;
  workflow_count: number;
  workflows: TemporalWorkflowSummary[];
}

export interface RunbookActionResponse {
  runbook_id: string;
  action: RunbookAction;
  status: string;
  temporal_workflows_url: string;
  message: string;
}

export interface BackendRoot {
  service: string;
  status: string;
  docs: string;
  temporal_workflows_url: string;
  endpoints: Record<string, string>;
}

export interface HealthStatus {
  status: string;
  temporal_workflows_url: string;
}

const buildApiUrl = (path: string) => {
  if (path.startsWith('http')) return path;

  const base = API_BASE_URL.replace(/\/$/, '');
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${normalizedPath}`;
};

const request = async <T>(path: string, options?: RequestInit): Promise<T> => {
  const response = await fetch(buildApiUrl(path), {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`FastAPI request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
};

export const api = {
  url: buildApiUrl,
  getRoot: () => request<BackendRoot>('/'),
  getHealth: () => request<HealthStatus>('/health'),
  getRunbooks: () => request<Runbook[]>('/api/runbooks'),
  getAudit: () => request<AuditRow[]>('/api/audit'),
  getQueryClusters: () => request<QueryClusterRow[]>('/api/query-clusters'),
  getTemporalLink: () => request<TemporalLink>('/api/temporal'),
  getTemporalDetails: () => request<TemporalDetails>('/api/temporal/details'),
  runRunbookAction: (runbookId: string, action: RunbookAction) =>
    request<RunbookActionResponse>(`/api/runbooks/${runbookId}/actions/${action}`, {
      method: 'POST',
    }),
};
