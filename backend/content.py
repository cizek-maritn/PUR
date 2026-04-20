from __future__ import annotations

import html
import re
from typing import Any

import bleach

try:
    from .models import BlogPost
except ImportError:
    from models import BlogPost


ALLOWED_HTML_TAGS = [
    'p',
    'br',
    'strong',
    'b',
    'em',
    'i',
    'u',
    'blockquote',
    'code',
    'pre',
    'ul',
    'ol',
    'li',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'span',
]
ALLOWED_HTML_ATTRIBUTES = {
    'span': ['style'],
}


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_tags(values: list[str] | None) -> list[str]:
    if not values:
        return []

    seen: set[str] = set()
    normalized: list[str] = []

    for value in values:
        candidate = re.sub(r'\s+', '-', value.strip().lower())
        candidate = re.sub(r'[^a-z0-9-]', '', candidate)
        candidate = re.sub(r'-{2,}', '-', candidate).strip('-')

        if not candidate or candidate in seen:
            continue

        seen.add(candidate)
        normalized.append(candidate)

    return normalized


def sanitize_post_html(content: str) -> str:
    cleaned = bleach.clean(
        content,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        strip=True,
    )

    return bleach.clean(cleaned, tags=ALLOWED_HTML_TAGS, attributes=ALLOWED_HTML_ATTRIBUTES, strip=True)


def extract_plain_text(content: str) -> str:
    plain_text = bleach.clean(content, tags=[], strip=True)
    decoded_text = html.unescape(plain_text)
    normalized_spaces = decoded_text.replace('\xa0', ' ')
    return re.sub(r'\s+', ' ', normalized_spaces).strip()


def normalize_post_created_at(created_at: Any) -> str:
    return created_at.isoformat().replace('+00:00', 'Z')


def serialize_post(post: BlogPost) -> dict[str, Any]:
    rating_scores = [r.score for r in post.ratings if r.score]
    average_rating = round(sum(rating_scores) / len(rating_scores), 1) if rating_scores else 0
    plain_text_content = extract_plain_text(post.content)
    excerpt = plain_text_content[:180].strip()

    return {
        'id': post.id,
        'title': post.title,
        'authorUsername': post.author.username,
        'createdAt': normalize_post_created_at(post.created_at),
        'content': post.content,
        'excerpt': excerpt,
        'averageRating': average_rating,
        'ratingCount': len(post.ratings),
        'commentsCount': len(post.comments),
        'tags': list(post.tags or []),
    }