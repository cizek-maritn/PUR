from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

try:
    from ..content import extract_plain_text, normalize_tags, sanitize_post_html, serialize_post
    from ..deps import get_current_user, get_db
    from ..models import BlogPost, User
    from ..schemas import BlogPostCreateRequest
except ImportError:
    from content import extract_plain_text, normalize_tags, sanitize_post_html, serialize_post
    from deps import get_current_user, get_db
    from models import BlogPost, User
    from schemas import BlogPostCreateRequest


router = APIRouter(prefix='/api/posts')


@router.get('')
def list_posts(db: Session = Depends(get_db)) -> JSONResponse:
    posts = db.scalars(
        select(BlogPost)
        .options(
            selectinload(BlogPost.author),
            selectinload(BlogPost.comments),
            selectinload(BlogPost.ratings),
        )
        .order_by(BlogPost.created_at.desc())
    ).all()

    return JSONResponse({'ok': True, 'posts': [serialize_post(post) for post in posts]}, status_code=200)


@router.post('')
def create_post(
    payload: BlogPostCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    title = payload.title.strip()
    content = payload.content.strip()

    if not title:
        return JSONResponse({'ok': False, 'message': 'A post title is required.'}, status_code=400)

    if not content:
        return JSONResponse({'ok': False, 'message': 'Post content cannot be empty.'}, status_code=400)

    sanitized_content = sanitize_post_html(content)
    plain_text_content = extract_plain_text(sanitized_content)

    if not plain_text_content:
        return JSONResponse(
            {'ok': False, 'message': 'Post content must include visible text.'},
            status_code=400,
        )

    post = BlogPost(
        title=title,
        content=sanitized_content,
        author_username=current_user.username,
        tags=normalize_tags(payload.tags),
    )

    db.add(post)
    db.commit()

    created_post = db.scalar(
        select(BlogPost)
        .where(BlogPost.id == post.id)
        .options(
            selectinload(BlogPost.author),
            selectinload(BlogPost.comments),
            selectinload(BlogPost.ratings),
        )
    )

    if created_post is None:
        return JSONResponse({'ok': False, 'message': 'Unable to load created post.'}, status_code=500)

    return JSONResponse(
        {
            'ok': True,
            'message': 'Post created successfully.',
            'post': serialize_post(created_post),
        },
        status_code=201,
    )