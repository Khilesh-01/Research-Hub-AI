import axios, { type InternalAxiosRequestConfig } from 'axios'

const BASE_URL = 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// ── Auth token injection ───────────────────────────────────────────────────
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ── Global 401 handler ────────────────────────────────────────────────────
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

// ── Auth ──────────────────────────────────────────────────────────────────
export const authAPI = {
  register: (data: { name: string; email: string; password: string }) =>
    api.post('/auth/register', data),

  login: (email: string, password: string) => {
    const form = new FormData()
    form.append('username', email)
    form.append('password', password)
    return api.post('/auth/login', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  getMe: () => api.get('/auth/me'),
}

// ── Papers ────────────────────────────────────────────────────────────────
export const papersAPI = {
  search: (query: string, source = 'all', maxResults = 10) =>
    api.get('/papers/search', {
      params: { query, source, max_results: maxResults },
    }),

  importPaper: (paperData: object, workspaceId?: string) =>
    api.post('/papers/import', paperData, {
      params: workspaceId ? { workspace_id: workspaceId } : {},
    }),

  addToWorkspace: (paperId: string, workspaceId: string) =>
    api.post(`/papers/${paperId}/workspace/${workspaceId}`),

  processEmbeddings: (paperId: string) =>
    api.post(`/papers/${paperId}/process-embeddings`),

  getEmbeddingStatus: (paperId: string) =>
    api.get(`/papers/${paperId}/embedding-status`),

  getPaper: (paperId: string) => api.get(`/papers/${paperId}`),

  /** Fetch PDF as blob (handles auth header properly) */
  getPdfBlob: (paperId: string, download = false) =>
    api.get(`/papers/${paperId}/pdf`, {
      params: { download },
      responseType: 'blob',
    }),
}

// ── Workspaces ────────────────────────────────────────────────────────────
export const workspacesAPI = {
  create: (data: { workspace_name: string; description?: string }) =>
    api.post('/workspaces/', data),

  getAll: () => api.get('/workspaces/'),

  getById: (id: string) => api.get(`/workspaces/${id}`),

  update: (id: string, data: { workspace_name: string; description?: string }) =>
    api.put(`/workspaces/${id}`, data),

  delete: (id: string) => api.delete(`/workspaces/${id}`),

  getPapers: (id: string) => api.get(`/workspaces/${id}/papers`),

  removePaper: (workspaceId: string, paperId: string) =>
    api.delete(`/workspaces/${workspaceId}/papers/${paperId}`),

  getNotes: (id: string) => api.get(`/workspaces/${id}/notes`),

  createNote: (workspaceId: string, data: object) =>
    api.post(`/workspaces/${workspaceId}/notes`, data),

  deleteNote: (workspaceId: string, noteId: string) =>
    api.delete(`/workspaces/${workspaceId}/notes/${noteId}`),
}

// ── Chat ──────────────────────────────────────────────────────────────────
export const chatAPI = {
  createSession: (workspaceId: string, title = 'New Chat') =>
    api.post('/chat/session', { workspace_id: workspaceId, title }),

  getSessions: (workspaceId: string) =>
    api.get(`/chat/session/${workspaceId}`),

  renameSession: (sessionId: string, title: string) =>
    api.patch(`/chat/session/${sessionId}`, { title }),

  deleteSession: (sessionId: string) =>
    api.delete(`/chat/session/${sessionId}`),

  query: (sessionId: string, query: string) =>
    api.post('/chat/query', { session_id: sessionId, query }),

  getMessages: (sessionId: string) =>
    api.get(`/chat/messages/${sessionId}`),
}

export default api
