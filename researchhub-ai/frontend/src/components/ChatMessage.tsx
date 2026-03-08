import React from 'react'
import ReactMarkdown from 'react-markdown'
import type { ChatMessage as ChatMsg } from '../types'

interface Props {
  message: ChatMsg
}

const ChatMessage: React.FC<Props> = ({ message }) => {
  const isUser = message.role === 'user'
  const time = new Date(message.created_at).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  })

  if (isUser) {
    return (
      <div className="flex justify-end animate-fade-in">
        <div className="max-w-[80%]">
          <div className="bg-blue-600 text-white rounded-2xl rounded-tr-none px-4 py-3 text-sm">
            {message.message_content}
          </div>
          <p className="text-xs text-gray-400 text-right mt-1">{time}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-3 animate-fade-in">
      {/* AI Avatar */}
      <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shrink-0 shadow-sm">
        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      </div>

      <div className="flex-1 min-w-0">
        <div className="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-3">
          <div className="prose prose-sm max-w-none text-gray-800 [&>p]:mb-2 [&>p:last-child]:mb-0 [&>ul]:mt-1 [&>ol]:mt-1 [&>h1,h2,h3]:font-semibold [&>h1,h2,h3]:text-gray-900">
            <ReactMarkdown>{message.message_content}</ReactMarkdown>
          </div>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-gray-400">{time}</span>
          <span className="badge bg-blue-50 text-blue-600 text-[10px]">Groq Llama 3.3</span>
        </div>
      </div>
    </div>
  )
}

export default ChatMessage
