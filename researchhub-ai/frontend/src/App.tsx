import React from 'react'
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom'
import { AuthProvider, useAuth } from './hooks/useAuth'
import Navbar from './components/Navbar'
import Login from './pages/Login/Login'
import SearchPapers from './pages/SearchPapers/SearchPapers'
import Workspace from './pages/Workspace/Workspace'
import Chatbot from './pages/Chatbot/Chatbot'

// ── Protected route wrapper ───────────────────────────────────────────────
const Protected: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth()
  if (isLoading)
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

// ── Layout wrapper (navbar + content) ────────────────────────────────────
const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="min-h-screen bg-gray-50">
    <Navbar />
    <main>{children}</main>
  </div>
)

const App: React.FC = () => (
  <AuthProvider>
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <Protected>
              <Navigate to="/search" replace />
            </Protected>
          }
        />
        <Route
          path="/search"
          element={
            <Protected>
              <Layout>
                <SearchPapers />
              </Layout>
            </Protected>
          }
        />
        <Route
          path="/workspaces"
          element={
            <Protected>
              <Layout>
                <Workspace />
              </Layout>
            </Protected>
          }
        />
        <Route
          path="/workspaces/:workspaceId/chat"
          element={
            <Protected>
              <Layout>
                <Chatbot />
              </Layout>
            </Protected>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  </AuthProvider>
)

export default App
