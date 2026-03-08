import React, { useState, useCallback } from 'react'
import { papersAPI, workspacesAPI } from '../../services/api'
import type { PaperSearchResult, Workspace } from '../../types'
import PaperCard from '../../components/PaperCard'

type Source = 'all' | 'arxiv' | 'pubmed'

// ── Workspace picker modal ────────────────────────────────────────────────────
interface WorkspacePickerProps {
  workspaces: Workspace[]
  onSelect: (workspaceId: string | null) => void
  onCancel: () => void
}

const WorkspacePicker: React.FC<WorkspacePickerProps> = ({ workspaces, onSelect, onCancel }) => {
  const [selected, setSelected] = useState<string | 'none'>('none')

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">Add to Workspace</h2>
        <p className="text-sm text-gray-500 mb-4">Choose a workspace to add this paper to, or import without one.</p>

        <div className="space-y-2 mb-6 max-h-64 overflow-y-auto">
          <label className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${selected === 'none' ? 'border-blue-300 bg-blue-50' : 'border-gray-200 hover:border-gray-300'}`}>
            <input type="radio" name="ws" value="none" checked={selected === 'none'} onChange={() => setSelected('none')} className="text-blue-600" />
            <div>
              <p className="text-sm font-medium text-gray-700">No workspace</p>
              <p className="text-xs text-gray-400">Import to library only</p>
            </div>
          </label>

          {workspaces.map((ws) => (
            <label
              key={ws.workspace_id}
              className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${selected === ws.workspace_id ? 'border-blue-300 bg-blue-50' : 'border-gray-200 hover:border-gray-300'}`}
            >
              <input type="radio" name="ws" value={ws.workspace_id} checked={selected === ws.workspace_id} onChange={() => setSelected(ws.workspace_id)} className="text-blue-600" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">{ws.workspace_name}</p>
                {ws.description && <p className="text-xs text-gray-400 truncate">{ws.description}</p>}
                <p className="text-xs text-gray-400">{ws.paper_count} papers</p>
              </div>
            </label>
          ))}
        </div>

        <div className="flex gap-3 justify-end">
          <button onClick={onCancel} className="btn-secondary">Cancel</button>
          <button
            onClick={() => onSelect(selected === 'none' ? null : selected)}
            className="btn-primary"
          >
            Import
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Main SearchPapers Page ────────────────────────────────────────────────────
const SearchPapers: React.FC = () => {
  const [query, setQuery] = useState('')
  const [source, setSource] = useState<Source>('all')
  const [maxResults, setMaxResults] = useState(10)
  const [results, setResults] = useState<PaperSearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [importing, setImporting] = useState<number | null>(null)
  const [importedIndices, setImportedIndices] = useState<Set<number>>(new Set())
  const [successMsg, setSuccessMsg] = useState('')

  // Workspace picker modal state
  const [pickerPaper, setPickerPaper] = useState<{ paper: PaperSearchResult; index: number } | null>(null)
  const [loadingWorkspaces, setLoadingWorkspaces] = useState(false)

  const ensureWorkspaces = async (): Promise<Workspace[]> => {
    if (workspaces.length > 0) return workspaces
    setLoadingWorkspaces(true)
    try {
      const res = await workspacesAPI.getAll()
      setWorkspaces(res.data)
      return res.data as Workspace[]
    } finally {
      setLoadingWorkspaces(false)
    }
  }

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return
    setLoading(true)
    setError('')
    setResults([])
    setImportedIndices(new Set())
    try {
      const res = await papersAPI.search(query, source, maxResults)
      setResults(res.data.results ?? [])
    } catch {
      setError('Search failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [query, source, maxResults])

  const handleImport = async (paper: PaperSearchResult, index: number, workspaceId?: string | null) => {
    setImporting(index)
    setPickerPaper(null)
    try {
      await papersAPI.importPaper(paper, workspaceId ?? undefined)
      setImportedIndices((prev) => new Set(prev).add(index))
      setSuccessMsg(workspaceId ? 'Paper imported to workspace!' : 'Paper imported!')
      setTimeout(() => setSuccessMsg(''), 3000)
    } catch {
      setError('Import failed.')
    } finally {
      setImporting(null)
    }
  }

  const handleImportClick = async (paper: PaperSearchResult, index: number) => {
    const ws = await ensureWorkspaces()
    if (ws.length === 0) {
      // No workspaces — import directly
      await handleImport(paper, index)
    } else {
      // Show workspace picker
      setPickerPaper({ paper, index })
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Workspace picker modal */}
      {pickerPaper && (
        <WorkspacePicker
          workspaces={workspaces}
          onSelect={(wsId) => handleImport(pickerPaper.paper, pickerPaper.index, wsId)}
          onCancel={() => setPickerPaper(null)}
        />
      )}

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Discover Research Papers</h1>
        <p className="text-gray-500 mt-1">Search across arXiv and PubMed to find and import academic papers.</p>
      </div>

      {/* Search bar */}
      <div className="card mb-6">
        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Search papers — e.g. 'transformer attention mechanism'"
            className="input-field flex-1"
          />
          <select value={source} onChange={(e) => setSource(e.target.value as Source)} className="input-field sm:w-36">
            <option value="all">All Sources</option>
            <option value="arxiv">arXiv</option>
            <option value="pubmed">PubMed</option>
          </select>
          <select value={maxResults} onChange={(e) => setMaxResults(Number(e.target.value))} className="input-field sm:w-28">
            {[5, 10, 20, 30].map((n) => <option key={n} value={n}>{n} results</option>)}
          </select>
          <button onClick={handleSearch} disabled={loading || !query.trim()} className="btn-primary sm:w-32">
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Searching
              </span>
            ) : 'Search'}
          </button>
        </div>
      </div>

      {/* Status messages */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{error}</div>
      )}
      {successMsg && (
        <div className="mb-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-sm">✓ {successMsg}</div>
      )}
      {loadingWorkspaces && (
        <div className="mb-4 text-sm text-gray-500 flex items-center gap-2">
          <span className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
          Loading workspaces…
        </div>
      )}

      {results.length > 0 && (
        <p className="text-sm text-gray-500 mb-4">Found <strong>{results.length}</strong> papers</p>
      )}

      {!loading && results.length === 0 && query && (
        <div className="text-center py-16 text-gray-400">
          <svg className="w-12 h-12 mx-auto mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p>No results found. Try a different query.</p>
        </div>
      )}

      <div className="space-y-4">
        {results.map((paper, idx) => (
          <PaperCard
            key={idx}
            paper={paper}
            imported={importedIndices.has(idx)}
            importing={importing === idx}
            onImport={() => handleImportClick(paper, idx)}
          />
        ))}
      </div>
    </div>
  )
}

export default SearchPapers
