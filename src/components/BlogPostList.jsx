import { useEffect, useMemo, useState } from 'react'
import { filterAndRankPosts, getAvailableTags } from '../utils/blogSearch'
import { buildApiUrl } from '../utils/api'
import BlogPostSnippet from './BlogPostSnippet'

function BlogPostList({ refreshKey = 0 }) {
  const [posts, setPosts] = useState([])
  const [query, setQuery] = useState('')
  const [selectedTags, setSelectedTags] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  useEffect(() => {
    const controller = new AbortController()

    async function loadPosts() {
      setIsLoading(true)
      setLoadError('')

      try {
        const response = await fetch(buildApiUrl('/api/posts'), {
          signal: controller.signal,
        })
        const parsed = await response.json().catch(() => ({}))

        if (!response.ok) {
          throw new Error(typeof parsed?.message === 'string' ? parsed.message : 'Unable to load posts.')
        }

        setPosts(Array.isArray(parsed?.posts) ? parsed.posts : [])
      } catch (error) {
        if (error?.name === 'AbortError') {
          return
        }

        setLoadError(error instanceof Error ? error.message : 'Unable to load posts.')
        setPosts([])
      } finally {
        setIsLoading(false)
      }
    }

    loadPosts()

    return () => controller.abort()
  }, [refreshKey])

  const filteredPosts = useMemo(
    () => filterAndRankPosts(posts, query, selectedTags),
    [posts, query, selectedTags],
  )

  const availableTags = useMemo(() => getAvailableTags(posts), [posts])

  function handleTagChange(event) {
    const { checked, value } = event.target

    setSelectedTags((currentTags) => {
      if (checked) {
        return currentTags.includes(value) ? currentTags : [...currentTags, value]
      }

      return currentTags.filter((tag) => tag !== value)
    })
  }

  return (
    <section className="post-feed" aria-label="Blog post snippets">
      <header className="feed-header">
        <h1>Fresh Blog Snippets</h1>
        <p>Discover quick reads from the community.</p>
      </header>

      <label className="search-label" htmlFor="post-search">
        Search by title, author, or content
      </label>
      <input
        id="post-search"
        className="search-input"
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Try: pasta, beginner, zoe"
      />

      <fieldset className="tag-filter-group">
        <legend className="search-label">Filter by tags</legend>
        <div className="tag-checkbox-grid" role="group" aria-label="Select one or more tags">
          {availableTags.map((tag) => (
            <label key={tag} className="tag-checkbox-option">
              <input
                type="checkbox"
                name="tag-filter"
                value={tag}
                checked={selectedTags.includes(tag)}
                onChange={handleTagChange}
              />
              <span>{tag}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="filter-actions">
        <p className="selected-tags-label">
          {selectedTags.length ? 'Selected tags' : 'No tags selected'}
        </p>
        {selectedTags.length ? (
          <button className="clear-tags-button" type="button" onClick={() => setSelectedTags([])}>
            Clear tags
          </button>
        ) : null}
      </div>

      {selectedTags.length ? (
        <ul className="selected-tags" aria-label="Selected tags">
          {selectedTags.map((tag) => (
            <li key={tag}>{tag}</li>
          ))}
        </ul>
      ) : null}

      <p className="results-count">
        {isLoading
          ? 'Loading posts from the database...'
          : `Showing ${filteredPosts.length} of ${posts.length} posts`}
      </p>

      {loadError ? (
        <p className="empty-state" role="alert">
          {loadError}
        </p>
      ) : null}

      {!isLoading && !loadError && filteredPosts.length ? (
        <div className="post-list">
          {filteredPosts.map((post) => (
            <BlogPostSnippet key={post.id} post={post} />
          ))}
        </div>
      ) : !isLoading && !loadError ? (
        <p className="empty-state">
          No posts match that search yet. Try a different title word or clear some tags.
        </p>
      ) : null}

      {isLoading && !loadError ? (
        <p className="empty-state">Loading demo posts from PostgreSQL...</p>
      ) : null}
    </section>
  )
}

export default BlogPostList
