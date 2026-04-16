import { buildApiUrl } from './api'

const SESSION_KEY = 'pc_session_user'
const TOKEN_KEY = 'pc_session_token'

function safeParseJSON(value, fallback) {
  if (!value) {
    return fallback
  }

  try {
    return JSON.parse(value)
  } catch {
    return fallback
  }
}

function normalizeEmail(email) {
  return email.trim().toLowerCase()
}

export function getSessionUser() {
  return safeParseJSON(localStorage.getItem(SESSION_KEY), null)
}

export function clearSessionUser() {
  localStorage.removeItem(SESSION_KEY)
  localStorage.removeItem(TOKEN_KEY)
}

function setSessionUser(user) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(user))
}

function setSessionToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function getSessionToken() {
  const token = localStorage.getItem(TOKEN_KEY)
  return typeof token === 'string' ? token : null
}

async function postAuth(path, payload) {
  try {
    const response = await fetch(buildApiUrl(path), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })

    const parsed = await response.json().catch(() => ({}))

    if (!response.ok) {
      return {
        ok: false,
        message: typeof parsed?.message === 'string' ? parsed.message : 'Request failed.',
      }
    }

    return {
      ok: true,
      message: typeof parsed?.message === 'string' ? parsed.message : 'Request successful.',
      user: parsed?.user,
      token: parsed?.token,
    }
  } catch {
    return { ok: false, message: 'Unable to reach the authentication server.' }
  }
}

export async function registerAccount({ username, email, password, confirmPassword }) {
  const trimmedUsername = username.trim()
  const normalizedEmail = normalizeEmail(email)

  if (!trimmedUsername || !normalizedEmail || !password || !confirmPassword) {
    return { ok: false, message: 'Please fill in all required registration fields.' }
  }

  if (password !== confirmPassword) {
    return { ok: false, message: 'Password and confirmation password do not match.' }
  }

  const result = await postAuth('/api/auth/register', {
    username: trimmedUsername,
    email: normalizedEmail,
    password,
    confirmPassword,
  })

  if (result.ok && result.user && result.token) {
    setSessionUser(result.user)
    setSessionToken(result.token)
  }

  return result
}

export async function loginAccount({ email, password }) {
  const normalizedEmail = normalizeEmail(email)

  if (!normalizedEmail || !password) {
    return { ok: false, message: 'Email and password are required.' }
  }

  const result = await postAuth('/api/auth/login', {
    email: normalizedEmail,
    password,
  })

  if (result.ok && result.user && result.token) {
    setSessionUser(result.user)
    setSessionToken(result.token)
  }

  return result
}
