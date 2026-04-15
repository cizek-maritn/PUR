function formatPostDate(dateValue) {
  const date = new Date(dateValue)

  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function BlogPostSnippet({ post }) {
  return (
    <article className="post-snippet" aria-label={`Post: ${post.title}`}>
      <header className="post-header">
        <h2>{post.title}</h2>
        <p className="post-meta">
          <span>@{post.authorUsername}</span>
          <span aria-hidden="true">•</span>
          <time dateTime={post.createdAt}>{formatPostDate(post.createdAt)}</time>
        </p>
      </header>

      <p className="post-excerpt">{post.content}</p>

      <footer className="post-footer">
        <p className="post-engagement">
          <span>⭐ {post.averageRating}/5 ({post.ratingCount})</span>
          <span>{post.commentsCount} comments</span>
        </p>
        <ul className="post-tags" aria-label="Post tags">
          {post.tags.map((tag) => (
            <li key={tag}>{tag}</li>
          ))}
        </ul>
      </footer>
    </article>
  )
}

export default BlogPostSnippet
