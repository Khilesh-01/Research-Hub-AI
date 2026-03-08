import React, { useEffect, useState, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { chatAPI, workspacesAPI } from '../../services/api'
import type { ChatSession, ChatMessage as ChatMsg, Workspace } from '../../types'
import ChatMessage from '../../components/ChatMessage'

const Chatbot: React.FC = () => {
  const { workspaceId } = useParams<{ workspaceId: string }>()
  const navigate = useNavigate()

  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [activeSession, setActiveSession] = useState<ChatSession | null>(null)
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [initializing, setInitializing] = useState(true)
  const [error, setError] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () =>
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })

  // ── Load workspace + sessions ───────────────────────────────────────────
  const init = useCallback(async () => {
    if (!workspaceId) return
    setInitializing(true)
    try {
      const [wsRes, sessionsRes] = await Promise.all([
        workspacesAPI.getById(workspaceId),
        chatAPI.getSessions(workspaceId),
      ])
      setWorkspace(wsRes.data)
      const allSessions: ChatSession[] = sessionsRes.data
      setSessions(allSessions)

      if (allSessions.length > 0) {
        await selectSession(allSessions[0])
      }
    } catch {
      setError('Failed to initialise chat.')
    } finally {
      setInitializing(false)
    }
  }, [workspaceId])

  useEffect(() => { init() }, [init])
  useEffect(() => { scrollToBottom() }, [messages])

  const selectSession = async (session: ChatSession) => {
    setActiveSession(session)
    setMessages([])
    setError('')
    try {
      const res = await chatAPI.getMessages(session.session_id)
      setMessages(res.data)
    } catch {
      setError('Failed to load messages.')
    }
  }

  // ── New chat ────────────────────────────────────────────────────────────
  const newChat = async () => {
    if (!workspaceId) return
    setLoading(true)
    try {
      const res = await chatAPI.createSession(workspaceId)
      const newSession: ChatSession = res.data
      setSessions((prev) => [newSession, ...prev])
      setActiveSession(newSession)
      setMessages([])
      setError('')
    } catch {
      setError('Failed to create new chat.')
    } finally {
      setLoading(false)
    }
  }

  // ── Delete session ──────────────────────────────────────────────────────
  const deleteSession = async (sessionId: string) => {
    if (!window.confirm('Delete this chat session?')) return
    try {
      await chatAPI.deleteSession(sessionId)
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId))
      if (activeSession?.session_id === sessionId) {
        const remaining = sessions.filter((s) => s.session_id !== sessionId)
        if (remaining.length > 0) {
          await selectSession(remaining[0])
        } else {
          setActiveSession(null)
          setMessages([])
        }
      }
    } catch {
      setError('Failed to delete session.')
    }
  }

  // ── Rename session ──────────────────────────────────────────────────────
  const startRename = (session: ChatSession) => {
    setRenamingId(session.session_id)
    setRenameValue(session.title || 'New Chat')
  }

  const confirmRename = async (sessionId: string) => {
    if (!renameValue.trim()) return
    try {
      const res = await chatAPI.renameSession(sessionId, renameValue.trim())
      const updated: ChatSession = res.data
      setSessions((prev) =>
        prev.map((s) => (s.session_id === sessionId ? updated : s))
      )
      if (activeSession?.session_id === sessionId) {
        setActiveSession(updated)
      }
    } catch {
      setError('Failed to rename session.')
    } finally {
      setRenamingId(null)
    }
  }

  // ── Send message ────────────────────────────────────────────────────────
  const sendMessage = async () => {
    if (!input.trim() || !activeSession || loading) return
    const userText = input.trim()
    setInput('')
    setLoading(true)
    setError('')

    // Optimistically add user message
    const tempUser: ChatMsg = {
      message_id: `temp-user-${Date.now()}`,
      session_id: activeSession.session_id,
      role: 'user',
      message_content: userText,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, tempUser])

    try {
      const res = await chatAPI.query(activeSession.session_id, userText)
      const assistantMsg: ChatMsg = {
        message_id: `temp-ai-${Date.now()}`,
        session_id: activeSession.session_id,
        role: 'assistant',
        message_content: res.data.answer,
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistantMsg])

      // Refresh session list to get updated title + message count
      if (workspaceId) {
        const sessRes = await chatAPI.getSessions(workspaceId)
        setSessions(sessRes.data)
        const updated = sessRes.data.find(
          (s: ChatSession) => s.session_id === activeSession.session_id
        )
        if (updated) setActiveSession(updated)
      }
    } catch {
      setError('Failed to get a response. Please try again.')
      setMessages((prev) =>
        prev.filter((m) => m.message_id !== tempUser.message_id)
      )
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const formatDate = (iso: string) => {
    const d = new Date(iso)
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffDays = Math.floor(diffMs / 86400000)
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays}d ago`
    return d.toLocaleDateString()
  }

  // ── Render ──────────────────────────────────────────────────────────────
  if (initializing) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex h-[calc(100vh-64px)] overflow-hidden">
      {/* ── Session Sidebar ─────────────────────────────────────────── */}
      <aside
        className={`${
          sidebarOpen ? 'w-72' : 'w-0'
        } transition-all duration-200 bg-white border-r border-gray-200 flex flex-col overflow-hidden shrink-0`}
      >
        {/* Sidebar header */}
        <div className="p-3 border-b border-gray-100 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Chats
            </p>
            {workspace && (
              <p className="text-xs text-gray-400 truncate">{workspace.workspace_name}</p>
            )}
          </div>
          <button
            onClick={newChat}
            disabled={loading}
            className="flex items-center gap-1 text-xs bg-blue-600 hover:bg-blue-700 text-white px-2.5 py-1.5 rounded-lg font-medium transition-colors disabled:opacity-50"
          >
            + New
          </button>
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-y-auto py-2">
          {sessions.length === 0 ? (
            <div className="px-4 py-6 text-center text-xs text-gray-400">
              No chats yet.<br />Click "+ New" to start.
            </div>
          ) : (
            sessions.map((s) => (
              <div
                key={s.session_id}
                className={`group relative mx-2 mb-1 rounded-lg cursor-pointer ${
                  activeSession?.session_id === s.session_id
                    ? 'bg-blue-50 border border-blue-200'
                    : 'hover:bg-gray-50'
                }`}
              >
                {renamingId === s.session_id ? (
                  <div className="p-2">
                    <input
                      autoFocus
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onBlur={() => confirmRename(s.session_id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') confirmRename(s.session_id)
                        if (e.key === 'Escape') setRenamingId(null)
                      }}
                      className="w-full text-xs border border-blue-300 rounded px-2 py-1 outline-none"
                    />
                  </div>
                ) : (
                  <div
                    className="p-2.5 pr-16"
                    onClick={() => selectSession(s)}
                  >
                    <p className={`text-xs font-medium truncate ${
                      activeSession?.session_id === s.session_id
                        ? 'text-blue-700'
                        : 'text-gray-800'
                    }`}>
                      {s.title || 'New Chat'}
                    </p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-gray-400">{formatDate(s.started_at)}</span>
                      {s.message_count !== undefined && s.message_count > 0 && (
                        <span className="text-xs text-gray-400">
                          · {s.message_count} msg{s.message_count !== 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Actions shown on hover */}
                {renamingId !== s.session_id && (
                  <div className="absolute right-2 top-2.5 hidden group-hover:flex items-center gap-1">
                    <button
                      onClick={(e) => { e.stopPropagation(); startRename(s) }}
                      className="w-5 h-5 flex items-center justify-center rounded hover:bg-gray-200 text-gray-400 hover:text-gray-600"
                      title="Rename"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); deleteSession(s.session_id) }}
                      className="w-5 h-5 flex items-center justify-center rounded hover:bg-red-100 text-gray-400 hover:text-red-500"
                      title="Delete"
                    >
                      🗑
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Back to workspace */}
        <div className="p-3 border-t border-gray-100">
          <button
            onClick={() => navigate('/workspaces')}
            className="w-full text-xs text-gray-500 hover:text-gray-700 flex items-center gap-1"
          >
            ← Back to Workspaces
          </button>
        </div>
      </aside>

      {/* ── Main Chat Area ──────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-gray-400 hover:text-gray-600 p-1 rounded"
            title="Toggle sidebar"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <div className="flex-1 min-w-0">
            <h1 className="text-sm font-semibold text-gray-900 truncate">
              {activeSession?.title || 'AI Research Assistant'}
            </h1>
            {workspace && (
              <p className="text-xs text-gray-500 truncate">
                {workspace.workspace_name} · {workspace.paper_count} paper(s)
              </p>
            )}
          </div>

          <span className="badge bg-green-100 text-green-700 shrink-0">
            ● Groq Llama 3.3
          </span>
        </div>

        {error && (
          <div className="mx-4 mt-3 bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* No active session */}
        {!activeSession && (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
            <p className="text-sm mb-3">No chat selected.</p>
            <button onClick={newChat} className="btn-primary text-sm">
              + Start New Chat
            </button>
          </div>
        )}

        {/* Messages */}
        {activeSession && (
          <>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-center text-gray-400 py-12">
                  <div className="w-16 h-16 bg-blue-50 rounded-2xl flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <p className="font-medium text-gray-600 mb-1">Start a conversation</p>
                  <p className="text-sm max-w-sm">
                    Ask questions about the papers in this workspace. The AI will use
                    semantic search to find relevant context and provide research-focused answers.
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2 justify-center">
                    {['What are the key findings?', 'Summarise the methodology', 'What datasets were used?', 'What are the limitations?'].map((s) => (
                      <button
                        key={s}
                        onClick={() => setInput(s)}
                        className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-1.5 rounded-full transition-colors"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg) => (
                <ChatMessage key={msg.message_id} message={msg} />
              ))}

              {loading && (
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center shrink-0">
                    <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  <div className="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-3">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                      <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="bg-white border-t border-gray-200 p-4">
              <div className="flex gap-3 items-end max-w-4xl mx-auto">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask a research question… (Enter to send, Shift+Enter for new line)"
                  rows={2}
                  className="input-field flex-1 resize-none text-sm"
                  disabled={loading}
                />
                <button
                  onClick={sendMessage}
                  disabled={!input.trim() || loading}
                  className="btn-primary h-[56px] w-14 flex items-center justify-center"
                >
                  {loading ? (
                    <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                    </svg>
                  )}
                </button>
              </div>
              <p className="text-xs text-gray-400 text-center mt-2">
                Answers grounded in workspace papers via RAG · Powered by Groq
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default Chatbot
