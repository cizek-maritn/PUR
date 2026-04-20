import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { createCommentRequest, fetchPostById, fetchPostComments } from '../utils/api'
import { getSessionToken } from '../utils/authStorage'

function formatDateTime(dateValue) {
  const date = new Date(dateValue)

  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function PostDetailPage({ currentUser }) {
  const { postId } = useParams()
  const navigate = useNavigate()

  const [post, setPost] = useState(null)
  const [postError, setPostError] = useState('')
  const [isPostLoading, setIsPostLoading] = useState(true)

  const [comments, setComments] = useState([])
  const [commentsError, setCommentsError] = useState('')
  const [isCommentsLoading, setIsCommentsLoading] = useState(true)

  const [commentDraft, setCommentDraft] = useState('')
  const [replyDrafts, setReplyDrafts] = useState({})
  const [activeReplyId, setActiveReplyId] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')

  async function reloadComments() {
    setIsCommentsLoading(true)
    setCommentsError('')

    const result = await fetchPostComments(postId)

    if (!result.ok) {
      setComments([])
      setCommentsError(result.message)
      setIsCommentsLoading(false)
      return
    }

    setComments(result.comments)
    setIsCommentsLoading(false)
  }

  useEffect(() => {
    let isActive = true

    async function loadPostAndComments() {
      setIsPostLoading(true)
      setPostError('')
      setIsCommentsLoading(true)
      setCommentsError('')

      const [postResult, commentsResult] = await Promise.all([
        fetchPostById(postId),
        fetchPostComments(postId),
      ])

      if (!isActive) {
        return
      }

      if (!postResult.ok) {
        setPost(null)
        setPostError(postResult.message)
        setIsPostLoading(false)
      } else {
        setPost(postResult.post)
        setIsPostLoading(false)
      }

      if (!commentsResult.ok) {
        setComments([])
        setCommentsError(commentsResult.message)
        setIsCommentsLoading(false)
      } else {
        setComments(commentsResult.comments)
        setIsCommentsLoading(false)
      }
    }

    loadPostAndComments()

    return () => {
      isActive = false
    }
  }, [postId])

  function handleBackToMain() {
    if (window.history.length > 1) {
      navigate(-1)
      return
    }

    navigate('/')
  }

  async function submitComment(content, parentCommentId = null) {
    const trimmedContent = content.trim()
    if (!trimmedContent || isSubmitting) {
      return
    }

    if (!currentUser) {
      navigate('/auth')
      return
    }

    const token = getSessionToken()
    if (!token) {
      setSubmitError('You need to log in before posting comments.')
      return
    }

    setIsSubmitting(true)
    setSubmitError('')

    const result = await createCommentRequest({
      postId,
      content: trimmedContent,
      parentCommentId,
      token,
    })

    if (!result.ok) {
      setSubmitError(result.message)
      setIsSubmitting(false)
      return
    }

    if (parentCommentId) {
      setReplyDrafts((current) => ({ ...current, [parentCommentId]: '' }))
      setActiveReplyId(null)
    } else {
      setCommentDraft('')
    }

    await reloadComments()
    setIsSubmitting(false)
  }

  function renderComments(commentNodes, depth = 0) {
    return commentNodes.map((comment) => (
      <article
        key={comment.id}
        className="comment-card"
        style={{ '--comment-depth': Math.min(depth, 4) }}
      >
        <header className="comment-header">
          <p className="comment-author">@{comment.authorUsername}</p>
          <time className="comment-date" dateTime={comment.createdAt}>
            {formatDateTime(comment.createdAt)}
          </time>
        </header>

        <p className="comment-content">{comment.content}</p>

        <div className="comment-actions">
          {currentUser ? (
            <button
              type="button"
              className="reply-button"
              onClick={() =>
                setActiveReplyId((current) => (current === comment.id ? null : comment.id))
              }
            >
              {activeReplyId === comment.id ? 'Cancel reply' : 'Reply'}
            </button>
          ) : null}
        </div>

        {activeReplyId === comment.id ? (
          <form
            className="comment-form"
            onSubmit={(event) => {
              event.preventDefault()
              submitComment(replyDrafts[comment.id] ?? '', comment.id)
            }}
          >
            <label htmlFor={`reply-${comment.id}`}>Write a reply</label>
            <textarea
              id={`reply-${comment.id}`}
              value={replyDrafts[comment.id] ?? ''}
              onChange={(event) =>
                setReplyDrafts((current) => ({ ...current, [comment.id]: event.target.value }))
              }
              rows={3}
              placeholder="Share your thoughts"
            />
            <button type="submit" className="auth-submit-button" disabled={isSubmitting}>
              {isSubmitting ? 'Posting...' : 'Post Reply'}
            </button>
          </form>
        ) : null}

        {Array.isArray(comment.replies) && comment.replies.length ? (
          <div className="comment-replies">{renderComments(comment.replies, depth + 1)}</div>
        ) : null}
      </article>
    ))
  }

  return (
    <section className="post-detail-page" aria-label="Full post view">
      {isPostLoading ? <p className="empty-state">Loading post...</p> : null}
      {postError ? (
        <p className="empty-state" role="alert">
          {postError}
        </p>
      ) : null}

      {post ? (
        <article className="post-detail-card">
          <header className="post-header">
            <h1>{post.title}</h1>
            <p className="post-meta">
              <span>@{post.authorUsername}</span>
              <span aria-hidden="true">•</span>
              <time dateTime={post.createdAt}>{formatDateTime(post.createdAt)}</time>
            </p>
          </header>

          <div className="post-detail-content" dangerouslySetInnerHTML={{ __html: post.content }} />

          <footer className="post-detail-footer">
            <ul className="post-tags" aria-label="Post tags">
              {post.tags.map((tag) => (
                <li key={tag}>{tag}</li>
              ))}
            </ul>
          </footer>

          <section className="comments-section" aria-label="Comments">
            <h2>Comments</h2>

            {currentUser ? (
              <form
                className="comment-form"
                onSubmit={(event) => {
                  event.preventDefault()
                  submitComment(commentDraft)
                }}
              >
                <label htmlFor="new-comment">Add a comment</label>
                <textarea
                  id="new-comment"
                  value={commentDraft}
                  onChange={(event) => setCommentDraft(event.target.value)}
                  rows={4}
                  placeholder="Write your comment"
                />
                <button type="submit" className="auth-submit-button" disabled={isSubmitting}>
                  {isSubmitting ? 'Posting...' : 'Post Comment'}
                </button>
              </form>
            ) : (
              <p className="comment-login-hint">
                You can read all comments.{' '}
                <button type="button" onClick={() => navigate('/auth')}>
                  Log in
                </button>{' '}
                to add comments and replies.
              </p>
            )}

            {submitError ? (
              <p className="auth-feedback is-error" role="alert">
                {submitError}
              </p>
            ) : null}

            {isCommentsLoading ? <p className="empty-state">Loading comments...</p> : null}

            {commentsError ? (
              <p className="empty-state" role="alert">
                {commentsError}
              </p>
            ) : null}

            {!isCommentsLoading && !commentsError && !comments.length ? (
              <p className="empty-state">No comments yet. Start the conversation.</p>
            ) : null}

            {!isCommentsLoading && !commentsError && comments.length ? (
              <div className="comments-list">{renderComments(comments)}</div>
            ) : null}
          </section>
        </article>
      ) : null}

      <button type="button" className="back-to-main-button" onClick={handleBackToMain}>
        Back to Main Page
      </button>
    </section>
  )
}

export default PostDetailPage
