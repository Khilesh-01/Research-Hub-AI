import React, { useState } from 'react'
import type { PaperSearchResult } from '../types'

interface Props {
  paper: PaperSearchResult
  imported: boolean
  importing: boolean
  onImport: () => void
}

const PaperCard: React.FC<Props> = ({ paper, imported, importing, onImport }) => {
  const [expanded, setExpanded] = useState(false)
  const abstract = paper.abstract ?? ''
  const shortAbstract = abstract.length > 280 ? abstract.slice(0, 280) + '…' : abstract

  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        <div className="flex-1 min-w-0">
          {/* Title */}
          <h3 className="font-semibold text-gray-900 text-sm leading-snug mb-1">
            {paper.title}
          </h3>

          {/* Authors */}
          {paper.authors && (
            <p className="text-xs text-gray-500 mb-2 truncate">{paper.authors}</p>
          )}

          {/* Badges */}
          <div className="flex flex-wrap items-center gap-2 mb-3">
            {paper.source && (
              <span
                className={`badge ${
                  paper.source === 'arxiv'
                    ? 'bg-orange-100 text-orange-700'
                    : 'bg-green-100 text-green-700'
                }`}
              >
                {paper.source.toUpperCase()}
              </span>
            )}
            {paper.published_date && (
              <span className="badge bg-gray-100 text-gray-600">
                {paper.published_date.slice(0, 10)}
              </span>
            )}
            {paper.doi && (
              <span className="badge bg-purple-100 text-purple-700 truncate max-w-[200px]">
                DOI: {paper.doi}
              </span>
            )}
          </div>

          {/* Abstract */}
          {abstract && (
            <div>
              <p className="text-xs text-gray-600 leading-relaxed">
                {expanded ? abstract : shortAbstract}
              </p>
              {abstract.length > 280 && (
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="text-xs text-blue-600 hover:underline mt-1"
                >
                  {expanded ? 'Show less' : 'Show more'}
                </button>
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-2 shrink-0">
          <button
            onClick={onImport}
            disabled={imported || importing}
            className={`text-sm px-3 py-1.5 rounded-lg font-medium transition-colors ${
              imported
                ? 'bg-green-100 text-green-700 cursor-default'
                : 'btn-primary'
            }`}
          >
            {importing ? (
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
                Importing
              </span>
            ) : imported ? (
              '✓ Imported'
            ) : (
              'Import'
            )}
          </button>

          {paper.pdf_url && (
            <a
              href={paper.pdf_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm px-3 py-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium text-center transition-colors"
            >
              PDF ↗
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

export default PaperCard
