const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export function buildApiUrl(path) {
  return `${API_BASE_URL}${path}`
}

export async function createPostRequest({ title, content, tags, token }) {
  try {
    const response = await fetch(buildApiUrl('/api/posts'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ title, content, tags }),
    })

    const parsed = await response.json().catch(() => ({}))

    if (!response.ok) {
      return {
        ok: false,
        message: typeof parsed?.message === 'string' ? parsed.message : 'Unable to create post.',
      }
    }

    return {
      ok: true,
      message: typeof parsed?.message === 'string' ? parsed.message : 'Post created.',
      post: parsed?.post,
    }
  } catch {
    return { ok: false, message: 'Unable to reach the posts service.' }
  }
}