import { useState } from 'react'
import { loginAccount, registerAccount } from '../utils/authStorage'

function AuthPanel({ defaultMode = 'login', onAuthenticated }) {
  const [mode, setMode] = useState(defaultMode)
  const [loginForm, setLoginForm] = useState({ email: '', password: '' })
  const [registerForm, setRegisterForm] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  })
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  function updateLoginField(event) {
    const { name, value } = event.target
    setLoginForm((current) => ({ ...current, [name]: value }))
  }

  function updateRegisterField(event) {
    const { name, value } = event.target
    setRegisterForm((current) => ({ ...current, [name]: value }))
  }

  function switchMode(nextMode) {
    setMode(nextMode)
    setError('')
  }

  async function handleLoginSubmit(event) {
    event.preventDefault()
    setIsSubmitting(true)

    const result = await loginAccount(loginForm)

    setIsSubmitting(false)

    if (!result.ok) {
      setError(result.message)
      return
    }

    setError('')
    onAuthenticated(result.user)
  }

  async function handleRegisterSubmit(event) {
    event.preventDefault()
    setIsSubmitting(true)

    const result = await registerAccount(registerForm)

    setIsSubmitting(false)

    if (!result.ok) {
      setError(result.message)
      return
    }

    setError('')
    onAuthenticated(result.user)
  }

  return (
    <section className="auth-page" aria-label="Authentication">
      <div className="auth-card">
        <header className="auth-header">
          <h1>{mode === 'login' ? 'Log In' : 'Register'}</h1>
          <p>Use your email and password only. No social login or 2FA is required.</p>
        </header>

        <div className="auth-mode-toggle" role="tablist" aria-label="Authentication mode">
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'login'}
            className={`auth-mode-button ${mode === 'login' ? 'is-active' : ''}`}
            onClick={() => switchMode('login')}
          >
            Login
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'register'}
            className={`auth-mode-button ${mode === 'register' ? 'is-active' : ''}`}
            onClick={() => switchMode('register')}
          >
            Register
          </button>
        </div>

        {mode === 'login' ? (
          <form className="auth-form" onSubmit={handleLoginSubmit}>
            <label htmlFor="login-email">Email</label>
            <input
              id="login-email"
              name="email"
              type="email"
              required
              value={loginForm.email}
              onChange={updateLoginField}
              autoComplete="email"
            />

            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              name="password"
              type="password"
              required
              value={loginForm.password}
              onChange={updateLoginField}
              autoComplete="current-password"
            />

            <button type="submit" className="auth-submit-button" disabled={isSubmitting}>
              {isSubmitting ? 'Logging In...' : 'Log In'}
            </button>
          </form>
        ) : (
          <form className="auth-form" onSubmit={handleRegisterSubmit}>
            <label htmlFor="register-username">Username</label>
            <input
              id="register-username"
              name="username"
              type="text"
              required
              value={registerForm.username}
              onChange={updateRegisterField}
              autoComplete="username"
            />

            <label htmlFor="register-email">Email</label>
            <input
              id="register-email"
              name="email"
              type="email"
              required
              value={registerForm.email}
              onChange={updateRegisterField}
              autoComplete="email"
            />

            <label htmlFor="register-password">Password</label>
            <input
              id="register-password"
              name="password"
              type="password"
              required
              value={registerForm.password}
              onChange={updateRegisterField}
              autoComplete="new-password"
            />

            <label htmlFor="register-confirm-password">Confirm password</label>
            <input
              id="register-confirm-password"
              name="confirmPassword"
              type="password"
              required
              value={registerForm.confirmPassword}
              onChange={updateRegisterField}
              autoComplete="new-password"
            />

            <button type="submit" className="auth-submit-button" disabled={isSubmitting}>
              {isSubmitting ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>
        )}

        {error ? <p className="auth-feedback is-error">{error}</p> : null}
      </div>
    </section>
  )
}

export default AuthPanel
