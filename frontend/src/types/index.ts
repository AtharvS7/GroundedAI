/** GroundedAI TypeScript type definitions */

export interface User {
  id: string;
  email: string;
}

export interface Document {
  id: string;
  user_id: string;
  filename: string;
  file_type: 'pdf' | 'docx' | 'txt';
  file_size_bytes: number;
  storage_path: string | null;
  total_pages: number;
  chunk_count: number;
  status: 'processing' | 'indexed' | 'failed';
  error_message: string | null;
  uploaded_at: string;
  updated_at: string;
}

export interface CitationObject {
  source_filename: string;
  page_number: number;
  chunk_preview: string;
  relevance_score: number;
}

export interface GenerationResponse {
  answer: string;
  citations: CitationObject[];
  confidence_score: number;
  model_used: string;
  retrieval_time_ms: number;
  generation_time_ms: number;
  chunks_used: number;
  refusal: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: CitationObject[];
  confidence_score?: number;
  retrieval_time_ms?: number;
  generation_time_ms?: number;
  chunks_used?: number;
  refusal?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  created_at: string;
  updated_at: string;
}

export interface QueryRequest {
  query: string;
  top_k?: number;
  use_reranking?: boolean;
  conversation_id?: string;
}

export interface MetricsSummary {
  total_queries: number;
  avg_confidence: number;
  avg_rouge_l: number;
  avg_bleu_4: number;
  avg_faithfulness: number;
  avg_hallucination_delta: number;
}

export interface QueryRecord {
  id: string;
  user_id: string;
  conversation_id: string | null;
  query_text: string;
  response_text: string | null;
  confidence_score: number | null;
  model_used: string;
  retrieval_ms: number | null;
  generation_ms: number | null;
  top_k: number;
  refusal: boolean;
  created_at: string;
}

export interface EvaluationRecord {
  id: string;
  query_id: string;
  rouge_l: number | null;
  bleu_4: number | null;
  faithfulness: number | null;
  precision_k: number | null;
  recall_k: number | null;
  mrr: number | null;
  baseline_rouge: number | null;
  baseline_bleu: number | null;
  baseline_faithfulness: number | null;
  hallucination_delta: number | null;
  evaluated_at: string;
}

export interface MetricsData {
  summary: MetricsSummary;
  queries: QueryRecord[];
  evaluations: EvaluationRecord[];
}

export interface ApiResponse<T> {
  data: T;
  error: string | null;
  metadata?: {
    request_id?: string;
    timestamp?: string;
    duration_ms?: number;
    query_id?: string;
  };
}

export interface HealthStatus {
  status: 'healthy' | 'degraded';
  ollama: boolean;
  faiss: {
    loaded: boolean;
    total_vectors: number;
  };
  supabase: boolean;
  version: string;
}
