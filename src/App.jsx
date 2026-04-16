import { useState } from 'react'
import AuthPanel from './components/AuthPanel'
import BlogPostList from './components/BlogPostList'
import CreatePostPanel from './components/CreatePostPanel'
import { buildApiUrl } from './utils/api'
import { clearSessionUser, getSessionUser } from './utils/authStorage'
import './App.css'

function App() {
  const [activeView, setActiveView] = useState('blog')
  const [currentUser, setCurrentUser] = useState(() => getSessionUser())
  const [postRefreshKey, setPostRefreshKey] = useState(0)

  function handleAuthOpen() {
    setActiveView('auth')
  }

  function handleLogout() {
    fetch(buildApiUrl('/api/auth/logout'), { method: 'POST' }).catch(() => {
      // Keep local logout behavior even if backend is unavailable.
    })

    clearSessionUser()
    setCurrentUser(null)
    setActiveView('blog')
  }

  function handleAuthenticated(user) {
    setCurrentUser(user)
    setActiveView('blog')
  }

  function handleCreatePostOpen() {
    setActiveView('create-post')
  }

  function handlePostCreated() {
    setPostRefreshKey((current) => current + 1)
    setActiveView('blog')
  }

  return (
    <>
      <header className="app-header">
        <div className="app-header-actions">
          {currentUser ? <p className="auth-user-pill">{currentUser.username}</p> : null}
          {currentUser ? (
            <button type="button" className="auth-entry-button" onClick={handleCreatePostOpen}>
              Create Post
            </button>
          ) : null}
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
        {activeView === 'auth' && !currentUser ? (
          <AuthPanel onAuthenticated={handleAuthenticated} />
        ) : activeView === 'create-post' && currentUser ? (
          <CreatePostPanel onCreated={handlePostCreated} />
        ) : (
          <BlogPostList refreshKey={postRefreshKey} />
        )}
      </main>
    </>
  )
}

export default App
