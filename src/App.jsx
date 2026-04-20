import { useState } from 'react'
import { Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import AuthPanel from './components/AuthPanel'
import BlogPostList from './components/BlogPostList'
import CreatePostPanel from './components/CreatePostPanel'
import PostDetailPage from './components/PostDetailPage'
import { buildApiUrl } from './utils/api'
import { clearSessionUser, getSessionUser } from './utils/authStorage'
import './App.css'

function App() {
  const navigate = useNavigate()
  const [currentUser, setCurrentUser] = useState(() => getSessionUser())
  const [postRefreshKey, setPostRefreshKey] = useState(0)

  function handleAuthOpen() {
    navigate('/auth')
  }

  function handleLogout() {
    fetch(buildApiUrl('/api/auth/logout'), { method: 'POST' }).catch(() => {
      // Keep local logout behavior even if backend is unavailable.
    })

    clearSessionUser()
    setCurrentUser(null)
    navigate('/')
  }

  function handleAuthenticated(user) {
    setCurrentUser(user)
    navigate('/')
  }

  function handleCreatePostOpen() {
    navigate(currentUser ? '/create-post' : '/auth')
  }

  function handlePostCreated() {
    setPostRefreshKey((current) => current + 1)
    navigate('/')
  }

  return (
    <>
      <header className="app-header">
        <div className="app-header-actions">
          {currentUser ? <p className="auth-user-pill">{currentUser.username}</p> : null}
          <button type="button" className="auth-entry-button" onClick={handleCreatePostOpen}>
            Create Post
          </button>
          <button
            type="button"
            className="auth-entry-button"
            onClick={currentUser ? handleLogout : handleAuthOpen}
          >
            {currentUser ? 'Log Out' : 'Login / Register'}
          </button>
        </div>
      </header>

      <main className="app-shell">
        <Routes>
          <Route path="/" element={<BlogPostList refreshKey={postRefreshKey} />} />
          <Route
            path="/auth"
            element={currentUser ? <Navigate to="/" replace /> : <AuthPanel onAuthenticated={handleAuthenticated} />}
          />
          <Route
            path="/create-post"
            element={
              currentUser ? (
                <CreatePostPanel onCreated={handlePostCreated} />
              ) : (
                <Navigate to="/auth" replace />
              )
            }
          />
          <Route path="/posts/:postId" element={<PostDetailPage currentUser={currentUser} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  )
}

export default App
