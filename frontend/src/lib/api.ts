/** API client with Supabase JWT auth interceptor */

import axios from 'axios';
import { createClient } from './supabase';
import type {
  ApiResponse,
  Document,
  GenerationResponse,
  HealthStatus,
  MetricsData,
  QueryRequest,
} from '@/types';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 120000,
});

// Auth interceptor: attach Supabase JWT to every request
api.interceptors.request.use(async (config) => {
  try {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }
  } catch {
    // Silently fail — health endpoint doesn't need auth
  }
  return config;
});

// ─── Health ──────────────────────────────────────────────────

export async function checkHealth(): Promise<HealthStatus> {
  const { data } = await api.get<ApiResponse<HealthStatus>>('/health');
  return data.data;
}

// ─── Documents ───────────────────────────────────────────────

export async function uploadDocument(file: File): Promise<Document> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post<ApiResponse<Document>>('/upload-document', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data.data;
}

export async function getDocuments(): Promise<Document[]> {
  const { data } = await api.get<ApiResponse<Document[]>>('/documents');
  return data.data;
}

export async function deleteDocument(documentId: string): Promise<void> {
  await api.delete(`/document/${documentId}`);
}

// ─── Query ───────────────────────────────────────────────────

export async function sendQuery(req: QueryRequest): Promise<{
  response: GenerationResponse;
  queryId?: string;
}> {
  const { data } = await api.post<ApiResponse<GenerationResponse>>('/query', req);
  return {
    response: data.data,
    queryId: data.metadata?.query_id,
  };
}

// ─── Metrics ─────────────────────────────────────────────────

export async function getMetrics(limit = 50, offset = 0): Promise<MetricsData> {
  const { data } = await api.get<ApiResponse<MetricsData>>('/metrics', {
    params: { limit, offset },
  });
  return data.data;
}

// ─── Evaluation ──────────────────────────────────────────────

export async function runEvaluation(
  queryIds: string[],
  referenceAnswers: string[]
): Promise<unknown> {
  const { data } = await api.post('/evaluate', {
    query_ids: queryIds,
    reference_answers: referenceAnswers,
  });
  return data.data;
}

export async function exportReport(): Promise<Blob> {
  const { data } = await api.post('/evaluate/report', {}, {
    responseType: 'blob',
  });
  return data;
}

export default api;
