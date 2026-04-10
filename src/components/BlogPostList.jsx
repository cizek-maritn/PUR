import { useMemo, useState } from 'react'
import { blogPosts } from '../data/blogPosts'
import { filterAndRankPosts, getAvailableTags } from '../utils/blogSearch'
import BlogPostSnippet from './BlogPostSnippet'

function BlogPostList() {
  const [query, setQuery] = useState('')
  const [selectedTags, setSelectedTags] = useState([])

  const filteredPosts = useMemo(
    () => filterAndRankPosts(blogPosts, query, selectedTags),
    [query, selectedTags],
  )

  const availableTags = useMemo(() => getAvailableTags(blogPosts), [])

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
        Showing {filteredPosts.length} of {blogPosts.length} posts
      </p>

      {filteredPosts.length ? (
        <div className="post-list">
          {filteredPosts.map((post) => (
            <BlogPostSnippet key={post.id} post={post} />
          ))}
        </div>
      ) : (
        <p className="empty-state">
          No posts match that search yet. Try a different title word or clear some tags.
        </p>
      )}
    </section>
  )
}

export default BlogPostList
