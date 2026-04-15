from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

try:
    from .models import BlogPost, Comment, Like, Rating, User
except ImportError:
    from models import BlogPost, Comment, Like, Rating, User


DEMO_PASSWORD = 'demo-password'
DEMO_REACTOR_USERNAME = 'demo.reactor'
DEMO_COMMENTER_USERNAME = 'demo.commenter'
DEMO_LIKER_USERNAME = 'demo.liker'

DEMO_USERS = [
    'kitchen.kira',
    'urban.sprout',
    'papertrail.dev',
    'soil.sensei',
    'yeast.mode',
    'byte.by.zoe',
    'green.thumb.tom',
    'pantry.nora',
    DEMO_REACTOR_USERNAME,
    DEMO_COMMENTER_USERNAME,
    DEMO_LIKER_USERNAME,
]

DEMO_POSTS = [
    {
        'title': '7 Simple Dinners for Busy Weeknights',
        'author_username': 'kitchen.kira',
        'content': (
            'If your evenings are packed, these one-pan dinners can save you. I prep ingredients on '
            'Sunday, then rotate sauces so every night feels different. The lemon garlic chickpea '
            'skillet is still my favorite because it is cheap, fast, and very forgiving.'
        ),
        'created_at': '2026-03-27T17:40:00Z',
        'tags': ['cooking', 'meal-prep', 'quick-recipes'],
    },
    {
        'title': 'Balcony Gardening in Small Apartments',
        'author_username': 'urban.sprout',
        'content': (
            'You do not need a backyard to grow herbs and greens. A sunny railing plus vertical '
            'planters gives enough space for basil, mint, and lettuce. The key is watering deeply '
            'but less often, especially when spring winds dry out containers.'
        ),
        'created_at': '2026-04-05T08:22:00Z',
        'tags': ['gardening', 'small-spaces', 'urban-life'],
    },
    {
        'title': 'How I Organize My Reading Notes',
        'author_username': 'papertrail.dev',
        'content': (
            'I keep one digital notebook for highlights and one handwritten notebook for ideas. During '
            'review, I convert action points into tiny experiments I can run during the week. This '
            'rhythm helps me remember more and procrastinate less.'
        ),
        'created_at': '2026-03-11T21:10:00Z',
        'tags': ['learning', 'productivity', 'writing'],
    },
    {
        'title': 'Composting 101: Start With What You Already Have',
        'author_username': 'soil.sensei',
        'content': (
            'A successful compost pile starts with balance, not expensive gear. Mix dry browns like '
            'cardboard with wet greens like vegetable peels and coffee grounds. Turn the pile weekly, '
            'and in a few months your garden soil will noticeably improve.'
        ),
        'created_at': '2026-04-01T13:05:00Z',
        'tags': ['gardening', 'compost', 'sustainability'],
    },
    {
        'title': 'My Favorite Bread Recipe for Beginners',
        'author_username': 'yeast.mode',
        'content': (
            'Start with a no-knead dough so you can focus on timing and texture. Let fermentation do '
            'the heavy lifting overnight. In the morning, a hot Dutch oven gives you a crispy crust '
            'and a soft interior without complicated shaping techniques.'
        ),
        'created_at': '2026-02-18T10:50:00Z',
        'tags': ['cooking', 'baking', 'beginner-friendly'],
    },
    {
        'title': 'Rainy Day Coding Playlist and Focus Ritual',
        'author_username': 'byte.by.zoe',
        'content': (
            'When it rains, I lean into deep work blocks with ambient jazz and a strict timer. The first '
            'ten minutes are for outlining, then I code in quiet 45-minute rounds. A small ritual before '
            'each round makes it easier to begin.'
        ),
        'created_at': '2026-03-30T15:35:00Z',
        'tags': ['coding', 'focus', 'habits'],
    },
    {
        'title': 'Tomato Troubleshooting Guide for First-Time Growers',
        'author_username': 'green.thumb.tom',
        'content': (
            'Yellow leaves, curling stems, and blossom drop usually point to water stress or sudden '
            'temperature swings. Before adding fertilizer, check your watering pattern and mulching '
            'depth. Most tomato problems are solved by consistency, not additives.'
        ),
        'created_at': '2026-04-08T06:55:00Z',
        'tags': ['gardening', 'tomatoes', 'beginner-guide'],
    },
    {
        'title': 'One Pot Pasta That Actually Tastes Good',
        'author_username': 'pantry.nora',
        'content': (
            'Most one pot pasta recipes turn mushy because everything goes in too early. Hold back '
            'delicate herbs and cheese until the final minute. Toasted garlic and chili oil at the end '
            'add depth and make weeknight pasta feel intentional.'
        ),
        'created_at': '2026-04-09T19:12:00Z',
        'tags': ['cooking', 'pasta', 'weeknight'],
    },
]


def ensure_demo_users(session: Session) -> None:
    existing_usernames = {username for (username,) in session.execute(select(User.username)).all()}

    for username in DEMO_USERS:
        if username in existing_usernames:
            continue

        session.add(
            User(
                username=username,
                email=f'{username}@example.com',
                password_hash=generate_password_hash(DEMO_PASSWORD),
            )
        )

    session.flush()


def ensure_demo_posts(session: Session) -> list[BlogPost]:
    posts: list[BlogPost] = []

    for post_data in DEMO_POSTS:
        post = session.scalar(select(BlogPost).where(BlogPost.title == post_data['title']))

        if post is None:
            created_at = datetime.fromisoformat(post_data['created_at'].replace('Z', '+00:00'))
            post = BlogPost(
                title=post_data['title'],
                content=post_data['content'],
                author_username=post_data['author_username'],
                tags=list(post_data['tags']),
                created_at=created_at,
            )
            session.add(post)
            session.flush()

        if post not in posts:
            posts.append(post)

    return posts


def seed_demo_data(session: Session) -> None:
    ensure_demo_users(session)

    posts = ensure_demo_posts(session)
    if not posts:
        session.commit()
        return

    reactor = session.get(User, DEMO_REACTOR_USERNAME)
    commenter = session.get(User, DEMO_COMMENTER_USERNAME)
    liker = session.get(User, DEMO_LIKER_USERNAME)

    if reactor is None or commenter is None or liker is None:
        session.commit()
        return

    rating_keys = {
        (author_username, post_id)
        for author_username, post_id in session.execute(select(Rating.author_username, Rating.post_id)).all()
    }
    like_keys = {
        (user_username, comment_id)
        for user_username, comment_id in session.execute(select(Like.user_username, Like.comment_id)).all()
    }

    for post in posts:
        if (reactor.username, post.id) not in rating_keys:
            session.add(Rating(author_username=reactor.username, post_id=post.id, score=1))

        comment = session.scalar(
            select(Comment).where(
                Comment.post_id == post.id,
                Comment.author_username == commenter.username,
            )
        )

        if comment is None:
            comment = Comment(
                content='This is a demo discussion thread seeded from the database.',
                author_username=commenter.username,
                post_id=post.id,
            )
            session.add(comment)
            session.flush()

        if (liker.username, comment.id) not in like_keys:
            session.add(Like(user_username=liker.username, comment_id=comment.id))

    session.commit()