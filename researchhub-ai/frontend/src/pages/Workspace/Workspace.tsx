import React, { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { workspacesAPI, papersAPI } from '../../services/api'
import type { Workspace, Paper, Note, PaperSearchResult } from '../../types'
import WorkspaceCard from '../../components/WorkspaceCard'

type View = 'list' | 'detail'

// ── PDF helpers ───────────────────────────────────────────────────────────────
const openPdf = async (paper: Paper, download = false) => {
  try {
    const res = await papersAPI.getPdfBlob(paper.paper_id, download)
    const url = window.URL.createObjectURL(res.data)
    if (download) {
      const a = document.createElement('a')
      a.href = url
      a.download = `${paper.title.slice(0, 60)}.pdf`
      a.click()
    } else {
      window.open(url, '_blank')
    }
    setTimeout(() => window.URL.revokeObjectURL(url), 10000)
  } catch {
    // Fallback: open original URL directly
    if (paper.pdf_url) window.open(paper.pdf_url, '_blank')
  }
}

// ── Import-from-search modal ──────────────────────────────────────────────────
interface ImportModalProps {
  workspaceId: string
  onClose: () => void
  onImported: () => void
}

const ImportModal: React.FC<ImportModalProps> = ({ workspaceId, onClose, onImported }) => {
  const [query, setQuery] = useState('')
  const [source, setSource] = useState('all')
  const [results, setResults] = useState<PaperSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [importing, setImporting] = useState<number | null>(null)
  const [imported, setImported] = useState<Set<number>>(new Set())
  const [error, setError] = useState('')

  const doSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await papersAPI.search(query, source, 15)
      setResults(res.data.results ?? [])
    } catch {
      setError('Search failed.')
    } finally {
      setLoading(false)
    }
  }

  const doImport = async (paper: PaperSearchResult, idx: number) => {
    setImporting(idx)
    try {
      await papersAPI.importPaper(paper, workspaceId)
      setImported((prev) => new Set(prev).add(idx))
      onImported()
    } catch {
      setError('Import failed.')
    } finally {
      setImporting(null)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl flex flex-col max-h-[85vh]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900">Import Papers to Workspace</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">×</button>
        </div>

        <div className="px-6 py-4 border-b border-gray-100">
          <div className="flex gap-2">
            <input
              autoFocus
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && doSearch()}
              placeholder="Search papers — e.g. 'attention mechanism'"
              className="input-field flex-1 text-sm"
            />
            <select value={source} onChange={(e) => setSource(e.target.value)} className="input-field w-28 text-sm">
              <option value="all">All</option>
              <option value="arxiv">arXiv</option>
              <option value="pubmed">PubMed</option>
            </select>
            <button onClick={doSearch} disabled={loading || !query.trim()} className="btn-primary text-sm px-4">
              {loading ? <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin inline-block" /> : 'Search'}
            </button>
          </div>
          {error && <p className="text-red-600 text-xs mt-2">{error}</p>}
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-3 space-y-3">
          {results.length === 0 && !loading && (
            <div className="text-center text-gray-400 py-8 text-sm">
              {query ? 'No results found.' : 'Enter a query above to search for papers.'}
            </div>
          )}
          {results.map((paper, idx) => (
            <div key={idx} className="flex items-start gap-3 p-3 rounded-xl border border-gray-100 hover:border-gray-200">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 line-clamp-2">{paper.title}</p>
                {paper.authors && <p className="text-xs text-gray-500 mt-0.5 truncate">{paper.authors}</p>}
                <div className="flex gap-2 mt-1">
                  {paper.source && (
                    <span className={`badge text-xs ${paper.source === 'arxiv' ? 'bg-orange-100 text-orange-700' : 'bg-green-100 text-green-700'}`}>{paper.source}</span>
                  )}
                  {paper.published_date && <span className="badge bg-gray-100 text-gray-600 text-xs">{paper.published_date.slice(0, 4)}</span>}
                </div>
              </div>
              <div className="flex gap-2 shrink-0">
                {paper.pdf_url && (
                  <a href={paper.pdf_url} target="_blank" rel="noopener noreferrer" className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-2 py-1.5 rounded-lg">📄 PDF</a>
                )}
                <button
                  onClick={() => doImport(paper, idx)}
                  disabled={importing === idx || imported.has(idx)}
                  className={`text-xs px-3 py-1.5 rounded-lg font-medium ${imported.has(idx) ? 'bg-green-100 text-green-700' : 'btn-primary'}`}
                >
                  {importing === idx ? <span className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin inline-block" /> : imported.has(idx) ? '✓ Added' : '+ Add'}
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="px-6 py-3 border-t border-gray-100 flex justify-end">
          <button onClick={onClose} className="btn-secondary text-sm">Done</button>
        </div>
      </div>
    </div>
  )
}

// ── Main Workspace Page ───────────────────────────────────────────────────────
const Workspace: React.FC = () => {
  const navigate = useNavigate()
  const [view, setView] = useState<View>('list')
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [selected, setSelected] = useState<Workspace | null>(null)
  const [papers, setPapers] = useState<Paper[]>([])
  const [notes, setNotes] = useState<Note[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showImportModal, setShowImportModal] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [newWs, setNewWs] = useState({ workspace_name: '', description: '' })
  const [creating, setCreating] = useState(false)
  const [noteContent, setNoteContent] = useState('')
  const [savingNote, setSavingNote] = useState(false)
  const [embeddingPaperId, setEmbeddingPaperId] = useState<string | null>(null)

  const loadWorkspaces = useCallback(async () => {
    setLoading(true)
    try {
      const res = await workspacesAPI.getAll()
      setWorkspaces(res.data)
    } catch {
      setError('Failed to load workspaces.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { loadWorkspaces() }, [loadWorkspaces])

  const loadWorkspacePapers = async (ws: Workspace) => {
    try {
      const [papersRes, notesRes] = await Promise.all([
        workspacesAPI.getPapers(ws.workspace_id),
        workspacesAPI.getNotes(ws.workspace_id),
      ])
      setPapers(papersRes.data)
      setNotes(notesRes.data)
    } catch {
      setError('Failed to load workspace content.')
    }
  }

  const openWorkspace = async (ws: Workspace) => {
    setSelected(ws)
    setView('detail')
    await loadWorkspacePapers(ws)
  }

  const createWorkspace = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newWs.workspace_name.trim()) return
    setCreating(true)
    try {
      await workspacesAPI.create(newWs)
      setNewWs({ workspace_name: '', description: '' })
      setShowCreate(false)
      loadWorkspaces()
    } catch {
      setError('Failed to create workspace.')
    } finally {
      setCreating(false)
    }
  }

  const deleteWorkspace = async (id: string) => {
    if (!window.confirm('Delete this workspace and all its data?')) return
    try {
      await workspacesAPI.delete(id)
      loadWorkspaces()
    } catch {
      setError('Failed to delete workspace.')
    }
  }

  const removePaper = async (paperId: string) => {
    if (!selected) return
    try {
      await workspacesAPI.removePaper(selected.workspace_id, paperId)
      setPapers((prev) => prev.filter((p) => p.paper_id !== paperId))
    } catch {
      setError('Failed to remove paper.')
    }
  }

  const buildEmbeddings = async (paperId: string) => {
    setEmbeddingPaperId(paperId)
    try {
      await papersAPI.processEmbeddings(paperId)
      if (selected) await loadWorkspacePapers(selected)
    } catch {
      setError('Failed to generate embeddings.')
    } finally {
      setEmbeddingPaperId(null)
    }
  }

  const saveNote = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selected || !noteContent.trim()) return
    setSavingNote(true)
    try {
      const res = await workspacesAPI.createNote(selected.workspace_id, {
        workspace_id: selected.workspace_id,
        note_content: noteContent,
      })
      setNotes((prev) => [res.data, ...prev])
      setNoteContent('')
    } catch {
      setError('Failed to save note.')
    } finally {
      setSavingNote(false)
    }
  }

  const deleteNote = async (noteId: string) => {
    if (!selected) return
    try {
      await workspacesAPI.deleteNote(selected.workspace_id, noteId)
      setNotes((prev) => prev.filter((n) => n.note_id !== noteId))
    } catch {
      setError('Failed to delete note.')
    }
  }

  // ── Workspace list ──────────────────────────────────────────────────────
  if (view === 'list') {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Workspaces</h1>
            <p className="text-gray-500 mt-1">Organise your research into focused collections.</p>
          </div>
          <button className="btn-primary" onClick={() => setShowCreate(true)}>+ New Workspace</button>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{error}</div>
        )}

        {showCreate && (
          <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
              <h2 className="text-lg font-semibold mb-4">Create Workspace</h2>
              <form onSubmit={createWorkspace} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                  <input type="text" required value={newWs.workspace_name} onChange={(e) => setNewWs({ ...newWs, workspace_name: e.target.value })} className="input-field" placeholder="e.g. Large Language Models" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea value={newWs.description} onChange={(e) => setNewWs({ ...newWs, description: e.target.value })} className="input-field h-24 resize-none" placeholder="Optional description…" />
                </div>
                <div className="flex gap-3 justify-end">
                  <button type="button" onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
                  <button type="submit" disabled={creating} className="btn-primary">{creating ? 'Creating…' : 'Create'}</button>
                </div>
              </form>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-16">
            <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : workspaces.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <svg className="w-12 h-12 mx-auto mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
            <p>No workspaces yet. Create one to get started!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {workspaces.map((ws) => (
              <WorkspaceCard key={ws.workspace_id} workspace={ws} onOpen={() => openWorkspace(ws)} onDelete={() => deleteWorkspace(ws.workspace_id)} onChat={() => navigate(`/workspaces/${ws.workspace_id}/chat`)} />
            ))}
          </div>
        )}
      </div>
    )
  }

  // ── Workspace detail ────────────────────────────────────────────────────
  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {showImportModal && selected && (
        <ImportModal
          workspaceId={selected.workspace_id}
          onClose={() => setShowImportModal(false)}
          onImported={() => loadWorkspacePapers(selected)}
        />
      )}

      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => { setView('list'); setSelected(null) }} className="text-gray-500 hover:text-gray-700 flex items-center gap-1 text-sm">
          ← Back
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{selected?.workspace_name}</h1>
          {selected?.description && <p className="text-gray-500 text-sm mt-0.5">{selected.description}</p>}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowImportModal(true)} className="btn-secondary text-sm">🔍 Import Papers</button>
          <button onClick={() => navigate(`/workspaces/${selected?.workspace_id}/chat`)} className="btn-primary text-sm">💬 Chat with AI</button>
        </div>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{error}</div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Papers list */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-gray-800">Papers ({papers.length})</h2>
            <div className="flex items-center gap-3 text-xs text-gray-400">
              <span className="flex items-center gap-1"><span className="w-2 h-2 bg-green-400 rounded-full" /> Embedded</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 bg-yellow-400 rounded-full" /> Abstract only</span>
            </div>
          </div>

          {papers.length === 0 ? (
            <div className="card text-center text-gray-400 py-8">
              <p className="mb-3">No papers yet.</p>
              <button onClick={() => setShowImportModal(true)} className="btn-primary text-sm">🔍 Import Papers</button>
            </div>
          ) : (
            <div className="space-y-3">
              {papers.map((p) => (
                <div key={p.paper_id} className="card">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start gap-2 mb-1">
                        <span className={`w-2 h-2 rounded-full shrink-0 mt-1.5 ${p.has_embeddings ? 'bg-green-400' : 'bg-yellow-400'}`} title={p.has_embeddings ? `${p.chunk_count} chunks embedded` : 'Not embedded'} />
                        <p className="font-medium text-gray-900 text-sm leading-snug line-clamp-2">{p.title}</p>
                      </div>
                      {p.authors && <p className="text-xs text-gray-500 mt-1 truncate pl-4">{p.authors}</p>}
                      <div className="flex items-center gap-2 mt-2 flex-wrap pl-4">
                        {p.source && (
                          <span className={`badge ${p.source === 'arxiv' ? 'bg-orange-100 text-orange-700' : 'bg-green-100 text-green-700'}`}>{p.source}</span>
                        )}
                        {p.published_date && <span className="badge bg-gray-100 text-gray-600">{p.published_date.slice(0, 4)}</span>}
                        {p.has_embeddings && <span className="badge bg-green-50 text-green-600">⚡ {p.chunk_count} chunks</span>}
                      </div>
                    </div>

                    <div className="flex flex-col gap-1.5 shrink-0">
                      <button
                        onClick={() => buildEmbeddings(p.paper_id)}
                        disabled={embeddingPaperId === p.paper_id}
                        className={`text-xs px-2 py-1 rounded flex items-center gap-1 ${p.has_embeddings ? 'bg-green-50 hover:bg-green-100 text-green-700' : 'bg-blue-50 hover:bg-blue-100 text-blue-700'}`}
                        title={p.has_embeddings ? 'Re-generate embeddings' : 'Build embeddings for AI chat'}
                      >
                        {embeddingPaperId === p.paper_id ? <span className="w-3 h-3 border border-current border-t-transparent rounded-full animate-spin" /> : '⚡'}
                        {p.has_embeddings ? 'Re-embed' : 'Embed'}
                      </button>

                      {p.pdf_url && (
                        <>
                          <button onClick={() => openPdf(p)} className="text-xs bg-gray-50 hover:bg-gray-100 text-gray-600 px-2 py-1 rounded" title="View PDF">
                            📄 View
                          </button>
                          <button onClick={() => openPdf(p, true)} className="text-xs bg-gray-50 hover:bg-gray-100 text-gray-600 px-2 py-1 rounded" title="Download PDF">
                            ⬇ Download
                          </button>
                        </>
                      )}

                      <button onClick={() => removePaper(p.paper_id)} className="text-xs bg-red-50 hover:bg-red-100 text-red-600 px-2 py-1 rounded">
                        Remove
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Notes panel */}
        <div>
          <h2 className="font-semibold text-gray-800 mb-3">Notes</h2>
          <form onSubmit={saveNote} className="card mb-4">
            <textarea value={noteContent} onChange={(e) => setNoteContent(e.target.value)} className="input-field h-24 resize-none text-sm" placeholder="Write a note about this workspace…" />
            <button type="submit" disabled={savingNote || !noteContent.trim()} className="btn-primary w-full mt-3 text-sm">
              {savingNote ? 'Saving…' : 'Save Note'}
            </button>
          </form>
          <div className="space-y-3">
            {notes.map((n) => (
              <div key={n.note_id} className="card text-sm">
                <p className="text-gray-700 whitespace-pre-wrap">{n.note_content}</p>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-xs text-gray-400">{new Date(n.created_at).toLocaleDateString()}</span>
                  <button onClick={() => deleteNote(n.note_id)} className="text-xs text-red-500 hover:text-red-700">Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Workspace
