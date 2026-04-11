import { useState } from 'react'
import AuthPanel from './components/AuthPanel'
import BlogPostList from './components/BlogPostList'
import { clearSessionUser, getSessionUser } from './utils/authStorage'
import './App.css'

function App() {
  const [activeView, setActiveView] = useState('blog')
  const [currentUser, setCurrentUser] = useState(() => getSessionUser())

  function handleAuthOpen() {
    setActiveView('auth')
  }

  function handleLogout() {
    fetch('/api/auth/logout', { method: 'POST' }).catch(() => {
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

  return (
    <>
      <header className="app-header">
        <div className="app-header-actions">
          {currentUser ? <p className="auth-user-pill">{currentUser.username}</p> : null}
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
        ) : (
          <BlogPostList />
        )}
      </main>
    </>
  )
}

export default App
