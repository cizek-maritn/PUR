from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from .database import Base
except ImportError:
    from database import Base


def new_uuid() -> str:
    return uuid4().hex


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = 'users'

    username: Mapped[str] = mapped_column(String(80), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    posts: Mapped[list['BlogPost']] = relationship(back_populates='author')
    comments: Mapped[list['Comment']] = relationship(back_populates='author')
    ratings: Mapped[list['Rating']] = relationship(back_populates='author')
    likes: Mapped[list['Like']] = relationship(back_populates='user')


class BlogPost(Base):
    __tablename__ = 'blog_posts'

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_username: Mapped[str] = mapped_column(ForeignKey('users.username'), nullable=False, index=True)
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    author: Mapped['User'] = relationship(back_populates='posts')
    comments: Mapped[list['Comment']] = relationship(back_populates='post', cascade='all, delete-orphan')
    ratings: Mapped[list['Rating']] = relationship(back_populates='post', cascade='all, delete-orphan')


class Comment(Base):
    __tablename__ = 'comments'

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_uuid)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    author_username: Mapped[str] = mapped_column(ForeignKey('users.username'), nullable=False, index=True)
    post_id: Mapped[str] = mapped_column(ForeignKey('blog_posts.id'), nullable=False, index=True)
    parent_comment_id: Mapped[str | None] = mapped_column(ForeignKey('comments.id'), nullable=True, index=True)

    author: Mapped['User'] = relationship(back_populates='comments')
    post: Mapped['BlogPost'] = relationship(back_populates='comments')
    parent_comment: Mapped['Comment | None'] = relationship(
        remote_side='Comment.id',
        back_populates='replies',
        foreign_keys=[parent_comment_id],
    )
    replies: Mapped[list['Comment']] = relationship(
        back_populates='parent_comment',
        cascade='all, delete-orphan',
        foreign_keys=[parent_comment_id],
    )
    likes: Mapped[list['Like']] = relationship(back_populates='comment', cascade='all, delete-orphan')


class Rating(Base):
    __tablename__ = 'ratings'

    author_username: Mapped[str] = mapped_column(ForeignKey('users.username'), primary_key=True)
    post_id: Mapped[str] = mapped_column(ForeignKey('blog_posts.id'), primary_key=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    author: Mapped['User'] = relationship(back_populates='ratings')
    post: Mapped['BlogPost'] = relationship(back_populates='ratings')


class Like(Base):
    __tablename__ = 'likes'

    user_username: Mapped[str] = mapped_column(ForeignKey('users.username'), primary_key=True)
    comment_id: Mapped[str] = mapped_column(ForeignKey('comments.id'), primary_key=True)

    user: Mapped['User'] = relationship(back_populates='likes')
    comment: Mapped['Comment'] = relationship(back_populates='likes')