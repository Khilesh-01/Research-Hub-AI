// ── Shared TypeScript interfaces ──────────────────────────────────────────────

export interface User {
  user_id: string
  name: string
  email: string
  created_at: string
}

export interface Workspace {
  workspace_id: string
  user_id: string
  workspace_name: string
  description: string | null
  created_at: string
  paper_count: number
}

export interface Paper {
  paper_id: string
  title: string
  authors: string | null
  abstract: string | null
  source: string | null
  doi: string | null
  pdf_url: string | null
  published_date: string | null
  imported_at: string
  has_embeddings?: boolean
  chunk_count?: number
}

export interface PaperSearchResult {
  title: string
  authors: string | null
  abstract: string | null
  source: string
  doi: string | null
  pdf_url: string | null
  published_date: string | null
  abs_url?: string | null
}

export interface ChatSession {
  session_id: string
  user_id: string
  workspace_id: string
  title: string
  started_at: string
  message_count?: number
}

export interface ChatMessage {
  message_id: string
  session_id: string
  role: 'user' | 'assistant'
  message_content: string
  created_at: string
}

export interface Note {
  note_id: string
  workspace_id: string
  paper_id: string | null
  note_content: string
  created_at: string
}
