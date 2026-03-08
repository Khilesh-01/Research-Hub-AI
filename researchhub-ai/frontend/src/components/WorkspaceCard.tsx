import React from 'react'
import type { Workspace } from '../types'

interface Props {
  workspace: Workspace
  onOpen: () => void
  onDelete: () => void
  onChat: () => void
}

const WorkspaceCard: React.FC<Props> = ({ workspace, onOpen, onDelete, onChat }) => {
  const created = new Date(workspace.created_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

  return (
    <div className="card hover:shadow-md transition-shadow cursor-pointer group">
      <div onClick={onOpen}>
        {/* Icon + title */}
        <div className="flex items-start gap-3 mb-3">
          <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center shrink-0">
            <svg
              className="w-5 h-5 text-blue-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
              />
            </svg>
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-gray-900 text-sm leading-tight group-hover:text-blue-700 transition-colors">
              {workspace.workspace_name}
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">{created}</p>
          </div>
        </div>

        {workspace.description && (
          <p className="text-xs text-gray-500 mb-3 line-clamp-2">
            {workspace.description}
          </p>
        )}

        {/* Stats */}
        <div className="flex items-center gap-3 mb-4">
          <span className="badge bg-blue-50 text-blue-700">
            📄 {workspace.paper_count} paper{workspace.paper_count !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-2 pt-3 border-t border-gray-100">
        <button
          onClick={onChat}
          className="flex-1 text-xs bg-blue-600 hover:bg-blue-700 text-white py-1.5 rounded-lg font-medium transition-colors"
        >
          💬 Chat
        </button>
        <button
          onClick={onOpen}
          className="flex-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 py-1.5 rounded-lg font-medium transition-colors"
        >
          Open
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete() }}
          className="text-xs bg-red-50 hover:bg-red-100 text-red-600 py-1.5 px-2.5 rounded-lg transition-colors"
          title="Delete workspace"
        >
          🗑
        </button>
      </div>
    </div>
  )
}

export default WorkspaceCard
