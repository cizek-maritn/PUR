function tokenizeQuery(query) {
  return query
    .toLowerCase()
    .trim()
    .split(/\s+/)
    .filter(Boolean)
}

function sortByNewest(posts) {
  return [...posts].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
  )
}

function getBestMatchBucket(post, token) {
  const title = post.title.toLowerCase()
  const author = post.authorUsername.toLowerCase()
  const content = post.content.toLowerCase()

  if (title.includes(token)) return 0
  if (author.includes(token)) return 1
  if (content.includes(token)) return 2

  return null
}

function matchesSelectedTags(post, selectedTags) {
  if (!selectedTags.length) {
    return true
  }

  return selectedTags.every((tag) => post.tags.includes(tag))
}

export function filterAndRankPosts(posts, query, selectedTags = []) {
  const tokens = tokenizeQuery(query)
  const filteredByTags = posts.filter((post) => matchesSelectedTags(post, selectedTags))

  if (!tokens.length) {
    return sortByNewest(filteredByTags)
  }

  return filteredByTags
    .map((post) => {
      let totalScore = 0
      let bestBucket = Number.POSITIVE_INFINITY
      let matchedTokens = 0

      for (const token of tokens) {
        const bucket = getBestMatchBucket(post, token)

        if (bucket === null) {
          continue
        }

        matchedTokens += 1
        bestBucket = Math.min(bestBucket, bucket)

        if (bucket === 0) totalScore += 40
        if (bucket === 1) totalScore += 30
        if (bucket === 2) totalScore += 20
        if (bucket === 3) totalScore += 10
      }

      if (!matchedTokens) {
        return null
      }

      return {
        post,
        bestBucket,
        totalScore,
        matchedTokens,
      }
    })
    .filter(Boolean)
    .sort((a, b) => {
      if (!tokens.length) {
        return new Date(b.post.createdAt).getTime() - new Date(a.post.createdAt).getTime()
      }

      if (a.bestBucket !== b.bestBucket) {
        return a.bestBucket - b.bestBucket
      }

      if (a.totalScore !== b.totalScore) {
        return b.totalScore - a.totalScore
      }

      if (a.matchedTokens !== b.matchedTokens) {
        return b.matchedTokens - a.matchedTokens
      }

      return new Date(b.post.createdAt).getTime() - new Date(a.post.createdAt).getTime()
    })
    .map((item) => item.post)
}

export function getAvailableTags(posts) {
  return [...new Set(posts.flatMap((post) => post.tags))].sort((a, b) => a.localeCompare(b))
}
