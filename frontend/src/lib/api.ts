import axios from "axios";
import { useAuthStore } from "@/store/auth-store";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---------- Types ----------
export interface User {
  id: number;
  email: string;
  full_name?: string;
  is_admin: boolean;
  created_at: string;
}

export interface WorkflowStep {
  agent: string;
  action: string;
  params: Record<string, any>;
}

export interface Workflow {
  id: number;
  name: string;
  description?: string;
  definition: WorkflowStep[];
  original_prompt?: string;
  created_at: string;
}

export interface Job {
  id: number;
  status: "pending" | "running" | "succeeded" | "failed" | "cancelled";
  progress: number;
  prompt?: string;
  error_message?: string;
  architecture: "multi_agent" | "single_agent";
  processing_paradigm: "pandas" | "mapreduce" | "spark";
  node_id?: number;
  created_at: string;
  started_at?: string;
  finished_at?: string;
  workflow_id?: number;
}

export interface ResourceSample {
  elapsed_seconds: number;
  cpu_percent: number;
  gpu_percent: number;
  memory_percent: number;
  stage?: string;
}

export interface JobDetail extends Job {
  logs: { agent_name: string; message: string; created_at: string }[];
  result?: {
    metrics?: Record<string, any>;
    chart_data?: { type: string; data: any };
    report_markdown?: string;
    engine_metadata?: { engine: string; partitions?: number; stage_timings?: Record<string, any>; llm_calls?: number };
  };
  resource_samples: ResourceSample[];
  node_name?: string;
}

export interface ClusterNode {
  id: number;
  name: string;
  node_type: "cpu" | "gpu" | "hybrid";
  cpu_cores: number;
  gpu_count: number;
  memory_gb: number;
  status: "idle" | "busy";
}

export interface Dataset {
  id: number;
  name: string;
  file_path: string;
  columns?: { name: string; dtype: string }[];
  row_count: number;
  created_at: string;
}

// ---------- Auth ----------
export const authApi = {
  register: (email: string, password: string, full_name?: string) =>
    api.post<User>("/auth/register", { email, password, full_name }),
  login: (email: string, password: string) =>
    api.post<{ access_token: string; token_type: string }>("/auth/login", { email, password }),
};

// ---------- Prompts ----------
export const promptsApi = {
  parse: (prompt: string) => api.post("/prompts/parse", { prompt }),
  llmHealth: () => api.get("/prompts/llm-health"),
};

// ---------- Workflows ----------
export const workflowsApi = {
  list: () => api.get<Workflow[]>("/workflows"),
  create: (data: Partial<Workflow>) => api.post<Workflow>("/workflows", data),
  get: (id: number) => api.get<Workflow>(`/workflows/${id}`),
  remove: (id: number) => api.delete(`/workflows/${id}`),
};

// ---------- Jobs ----------
export const jobsApi = {
  list: () => api.get<Job[]>("/jobs"),
  create: (data: {
    workflow_id?: number;
    prompt?: string;
    architecture?: "multi_agent" | "single_agent";
    processing_paradigm?: "pandas" | "mapreduce" | "spark";
  }) => api.post<Job>("/jobs", data),
  get: (id: number) => api.get<JobDetail>(`/jobs/${id}`),
  restart: (id: number) => api.post<Job>(`/jobs/${id}/restart`),
};

// ---------- Cluster ----------
export const clusterApi = {
  nodes: () => api.get<ClusterNode[]>("/cluster/nodes"),
};

// ---------- Datasets ----------
export const datasetsApi = {
  list: () => api.get<Dataset[]>("/datasets"),
  rescan: () => api.post<Dataset[]>("/datasets/rescan"),
};

// ---------- Admin ----------
export const adminApi = {
  users: () => api.get<User[]>("/admin/users"),
  stats: () => api.get("/admin/stats"),
};
