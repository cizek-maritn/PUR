import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { filterAndRankPosts, getAvailableTags } from '../utils/blogSearch'
import { buildApiUrl } from '../utils/api'
import BlogPostSnippet from './BlogPostSnippet'

function BlogPostList({ refreshKey = 0 }) {
  const navigate = useNavigate()
  const [posts, setPosts] = useState([])
  const [query, setQuery] = useState('')
  const [selectedTags, setSelectedTags] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [isTagFilterExpanded, setIsTagFilterExpanded] = useState(false)
  const [tagSearchQuery, setTagSearchQuery] = useState('')
  const [searchMode, setSearchMode] = useState('title')

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
    () => filterAndRankPosts(posts, query, selectedTags, searchMode),
    [posts, query, selectedTags, searchMode],
  )

  const availableTags = useMemo(() => getAvailableTags(posts), [posts])

  const filteredAvailableTags = useMemo(() => {
    if (!tagSearchQuery.trim()) {
      return availableTags
    }
    const searchLower = tagSearchQuery.toLowerCase().trim()
    return availableTags.filter((tag) => tag.toLowerCase().includes(searchLower))
  }, [availableTags, tagSearchQuery])

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
        Search by {searchMode === 'title' ? 'title' : 'author'}
      </label>
      <div className="search-input-group">
        <input
          id="post-search"
          className="search-input"
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={searchMode === 'title' ? 'Try: pasta, beginner' : 'Try: zoe, john'}
        />
        <fieldset className="search-mode-toggle" aria-label="Search mode">
          <legend className="search-mode-legend">Search by:</legend>
          <label className="search-mode-option">
            <input
              type="radio"
              name="search-mode"
              value="title"
              checked={searchMode === 'title'}
              onChange={(e) => setSearchMode(e.target.value)}
            />
            Title
          </label>
          <label className="search-mode-option">
            <input
              type="radio"
              name="search-mode"
              value="author"
              checked={searchMode === 'author'}
              onChange={(e) => setSearchMode(e.target.value)}
            />
            Author
          </label>
        </fieldset>
      </div>

      <fieldset className="tag-filter-group">
        <legend className="search-label">Filter by tags</legend>
        <div className="tag-filter-header">
          <p className="tag-filter-summary">
            {availableTags.length
              ? `${availableTags.length} tags available for filtering.`
              : 'No tags are available yet.'}
          </p>
          <button
            type="button"
            className="tag-filter-toggle"
            onClick={() => setIsTagFilterExpanded((current) => !current)}
            aria-expanded={isTagFilterExpanded}
            aria-controls="tag-checkbox-panel"
            disabled={!availableTags.length}
          >
            {isTagFilterExpanded ? 'Hide tags' : 'Show tags'}
          </button>
        </div>
        {isTagFilterExpanded ? (
          <div id="tag-checkbox-panel" className="tag-checkbox-panel">
            <input
              type="search"
              className="tag-search-input"
              placeholder="Search tags..."
              value={tagSearchQuery}
              onChange={(event) => setTagSearchQuery(event.target.value)}
              aria-label="Search available tags"
            />
            <div className="tag-checkbox-grid" role="group" aria-label="Select one or more tags">
              {filteredAvailableTags.length ? (
                filteredAvailableTags.map((tag) => (
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
                ))
              ) : (
                <p className="no-tags-match">No tags match your search.</p>
              )}
            </div>
          </div>
        ) : null}
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
            <BlogPostSnippet
              key={post.id}
              post={post}
              onOpenPost={() => navigate(`/posts/${post.id}`)}
            />
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
