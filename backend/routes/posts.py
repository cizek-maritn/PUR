from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

try:
    from ..content import (
        extract_plain_text,
        normalize_tags,
        sanitize_post_html,
        serialize_comment,
        serialize_comment_forest,
        serialize_post,
    )
    from ..deps import get_current_user, get_db
    from ..models import BlogPost, Comment, User
    from ..schemas import BlogPostCreateRequest, CommentCreateRequest
except ImportError:
    from content import (
        extract_plain_text,
        normalize_tags,
        sanitize_post_html,
        serialize_comment,
        serialize_comment_forest,
        serialize_post,
    )
    from deps import get_current_user, get_db
    from models import BlogPost, Comment, User
    from schemas import BlogPostCreateRequest, CommentCreateRequest


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


@router.get('/{post_id}')
def get_post(post_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    post = db.scalar(
        select(BlogPost)
        .where(BlogPost.id == post_id)
        .options(
            selectinload(BlogPost.author),
            selectinload(BlogPost.comments),
            selectinload(BlogPost.ratings),
        )
    )

    if post is None:
        return JSONResponse({'ok': False, 'message': 'Post not found.'}, status_code=404)

    return JSONResponse({'ok': True, 'post': serialize_post(post)}, status_code=200)


@router.get('/{post_id}/comments')
def list_post_comments(post_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    post_exists = db.scalar(select(BlogPost.id).where(BlogPost.id == post_id))

    if post_exists is None:
        return JSONResponse({'ok': False, 'message': 'Post not found.'}, status_code=404)

    comments = db.scalars(
        select(Comment)
        .where(Comment.post_id == post_id)
        .options(
            selectinload(Comment.author),
            selectinload(Comment.likes),
        )
        .order_by(Comment.created_at.asc())
    ).all()

    return JSONResponse({'ok': True, 'comments': serialize_comment_forest(comments)}, status_code=200)


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


@router.post('/{post_id}/comments')
def create_comment(
    post_id: str,
    payload: CommentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    post_exists = db.scalar(select(BlogPost.id).where(BlogPost.id == post_id))
    if post_exists is None:
        return JSONResponse({'ok': False, 'message': 'Post not found.'}, status_code=404)

    plain_text_content = extract_plain_text(payload.content)

    if not plain_text_content:
        return JSONResponse({'ok': False, 'message': 'Comment cannot be empty.'}, status_code=400)

    parent_comment_id = payload.parent_comment_id
    if parent_comment_id:
        parent_comment = db.scalar(
            select(Comment).where(Comment.id == parent_comment_id, Comment.post_id == post_id)
        )

        if parent_comment is None:
            return JSONResponse({'ok': False, 'message': 'Parent comment was not found.'}, status_code=400)

    comment = Comment(
        content=plain_text_content,
        author_username=current_user.username,
        post_id=post_id,
        parent_comment_id=parent_comment_id,
    )

    db.add(comment)
    db.commit()

    created_comment = db.scalar(
        select(Comment)
        .where(Comment.id == comment.id)
        .options(
            selectinload(Comment.author),
            selectinload(Comment.likes),
        )
    )

    if created_comment is None:
        return JSONResponse({'ok': False, 'message': 'Unable to load created comment.'}, status_code=500)

    return JSONResponse(
        {
            'ok': True,
            'message': 'Comment posted successfully.',
            'comment': serialize_comment(created_comment, replies=[]),
        },
        status_code=201,
    )