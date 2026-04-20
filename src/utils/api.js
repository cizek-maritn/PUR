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

export async function fetchPostById(postId) {
  try {
    const response = await fetch(buildApiUrl(`/api/posts/${postId}`))
    const parsed = await response.json().catch(() => ({}))

    if (!response.ok) {
      return {
        ok: false,
        message: typeof parsed?.message === 'string' ? parsed.message : 'Unable to load the post.',
      }
    }

    return {
      ok: true,
      post: parsed?.post,
    }
  } catch {
    return { ok: false, message: 'Unable to reach the posts service.' }
  }
}

export async function fetchPostComments(postId) {
  try {
    const response = await fetch(buildApiUrl(`/api/posts/${postId}/comments`))
    const parsed = await response.json().catch(() => ({}))

    if (!response.ok) {
      return {
        ok: false,
        message: typeof parsed?.message === 'string' ? parsed.message : 'Unable to load comments.',
      }
    }

    return {
      ok: true,
      comments: Array.isArray(parsed?.comments) ? parsed.comments : [],
    }
  } catch {
    return { ok: false, message: 'Unable to reach the comments service.' }
  }
}

export async function createCommentRequest({ postId, content, token, parentCommentId = null }) {
  try {
    const response = await fetch(buildApiUrl(`/api/posts/${postId}/comments`), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        content,
        parentCommentId,
      }),
    })

    const parsed = await response.json().catch(() => ({}))

    if (!response.ok) {
      return {
        ok: false,
        message: typeof parsed?.message === 'string' ? parsed.message : 'Unable to post comment.',
      }
    }

    return {
      ok: true,
      message: typeof parsed?.message === 'string' ? parsed.message : 'Comment posted.',
      comment: parsed?.comment,
    }
  } catch {
    return { ok: false, message: 'Unable to reach the comments service.' }
  }
}