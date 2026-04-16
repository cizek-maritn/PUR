import { useRef, useState } from 'react'
import { createPostRequest } from '../utils/api'
import { getSessionToken } from '../utils/authStorage'

const FONT_SIZE_TO_COMMAND = {
  small: '2',
  normal: '3',
  large: '5',
}

function normalizeTagInput(rawTagInput) {
  if (!rawTagInput.trim()) {
    return []
  }

  const chunks = rawTagInput
    .split(',')
    .map((tag) => tag.trim().toLowerCase().replace(/\s+/g, '-'))
    .map((tag) => tag.replace(/[^a-z0-9-]/g, '').replace(/-{2,}/g, '-').replace(/^-|-$/g, ''))
    .filter(Boolean)

  return [...new Set(chunks)]
}

function CreatePostPanel({ onCreated }) {
  const editorRef = useRef(null)
  const [title, setTitle] = useState('')
  const [tagsInput, setTagsInput] = useState('')
  const [fontSize, setFontSize] = useState('normal')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  function runEditorCommand(command, value) {
    editorRef.current?.focus()
    document.execCommand(command, false, value)
  }

  function handleFontSizeChange(event) {
    const selectedSize = event.target.value
    setFontSize(selectedSize)
    runEditorCommand('fontSize', FONT_SIZE_TO_COMMAND[selectedSize])
  }

  async function handleSubmit(event) {
    event.preventDefault()

    const trimmedTitle = title.trim()
    const contentHtml = editorRef.current?.innerHTML ?? ''
    const contentText = editorRef.current?.innerText.trim() ?? ''
    const normalizedTags = normalizeTagInput(tagsInput)

    if (!trimmedTitle) {
      setError('A post title is required.')
      return
    }

    if (!contentText) {
      setError('Please add some text content to your post.')
      return
    }

    const token = getSessionToken()

    if (!token) {
      setError('Your session has expired. Please log in again.')
      return
    }

    setError('')
    setIsSubmitting(true)

    const result = await createPostRequest({
      title: trimmedTitle,
      content: contentHtml,
      tags: normalizedTags,
      token,
    })

    setIsSubmitting(false)

    if (!result.ok) {
      setError(result.message)
      return
    }

    setTitle('')
    setTagsInput('')
    if (editorRef.current) {
      editorRef.current.innerHTML = ''
    }

    onCreated(result.post)
  }

  return (
    <section className="create-post-page" aria-label="Create blog post">
      <div className="create-post-card">
        <header className="create-post-header">
          <h1>Create A New Post</h1>
          <p>Share your idea with formatting, clear tags, and a title.</p>
        </header>

        <form className="create-post-form" onSubmit={handleSubmit}>
          <label htmlFor="post-title">Title</label>
          <input
            id="post-title"
            type="text"
            maxLength={255}
            required
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="Example: 20-minute weeknight pasta"
          />

          <label htmlFor="post-tags">Tags</label>
          <input
            id="post-tags"
            type="text"
            value={tagsInput}
            onChange={(event) => setTagsInput(event.target.value)}
            placeholder="example: meal-prep, beginner-tips"
          />
          <p className="field-hint">Use lowercase tags with dashes, separated by commas.</p>

          <div className="editor-toolbar" role="toolbar" aria-label="Text formatting">
            <button type="button" onClick={() => runEditorCommand('bold')}>
              Bold
            </button>
            <button type="button" onClick={() => runEditorCommand('italic')}>
              Italic
            </button>
            <button type="button" onClick={() => runEditorCommand('underline')}>
              Underline
            </button>
            <label htmlFor="font-size-picker">Font size</label>
            <select id="font-size-picker" value={fontSize} onChange={handleFontSizeChange}>
              <option value="small">Small</option>
              <option value="normal">Normal</option>
              <option value="large">Large</option>
            </select>
          </div>

          <div
            ref={editorRef}
            className="rich-editor"
            contentEditable
            role="textbox"
            aria-multiline="true"
            suppressContentEditableWarning
            data-placeholder="Write your post content here..."
          />

          <button className="auth-submit-button" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Publishing...' : 'Publish Post'}
          </button>
        </form>

        {error ? <p className="auth-feedback is-error">{error}</p> : null}
      </div>
    </section>
  )
}

export default CreatePostPanel
