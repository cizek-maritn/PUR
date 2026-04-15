from __future__ import annotations

import os
import time
from typing import Any, Generator

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, selectinload
from werkzeug.security import check_password_hash, generate_password_hash

from database import Base, SessionLocal, engine
from models import BlogPost, User
from schemas import AuthLoginRequest, AuthRegisterRequest
from seed import seed_demo_data


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def normalize_post_created_at(created_at: Any) -> str:
    return created_at.isoformat().replace('+00:00', 'Z')


def serialize_post(post: BlogPost) -> dict[str, Any]:
    rating_scores = [r.score for r in post.ratings if r.score]
    average_rating = round(sum(rating_scores) / len(rating_scores), 1) if rating_scores else 0

    return {
        'id': post.id,
        'title': post.title,
        'authorUsername': post.author.username,
        'createdAt': normalize_post_created_at(post.created_at),
        'content': post.content,
        'averageRating': average_rating,
        'ratingCount': len(post.ratings),
        'commentsCount': len(post.comments),
        'tags': list(post.tags or []),
    }


def ensure_database_ready() -> None:
    retries = int(os.getenv('DATABASE_STARTUP_RETRIES', '12'))
    delay_seconds = float(os.getenv('DATABASE_STARTUP_DELAY_SECONDS', '1.5'))

    for attempt in range(1, retries + 1):
        try:
            with engine.begin() as connection:
                Base.metadata.create_all(bind=connection)
            break
        except OperationalError:
            if attempt >= retries:
                raise

            time.sleep(delay_seconds)

    if os.getenv('SEED_DEMO_DATA', 'true').lower() not in {'0', 'false', 'no'}:
        with SessionLocal() as session:
            seed_demo_data(session)


@app.on_event('startup')
def startup_event() -> None:
    ensure_database_ready()


@app.get('/api/health')
def health_check() -> JSONResponse:
    return JSONResponse({'ok': True, 'message': 'Healthy.'}, status_code=200)


@app.post('/api/auth/register')
def register(payload: AuthRegisterRequest, db: Session = Depends(get_db)) -> JSONResponse:
    username = payload.username.strip()
    email = normalize_email(payload.email)
    password = payload.password
    confirm_password = payload.confirm_password

    if not username or not email or not password or not confirm_password:
        return JSONResponse(
            {'ok': False, 'message': 'Please fill in all required registration fields.'},
            status_code=400,
        )

    if password != confirm_password:
        return JSONResponse(
            {'ok': False, 'message': 'Password and confirmation password do not match.'},
            status_code=400,
        )

    existing_username = db.scalar(select(User).where(User.username == username))
    if existing_username is not None:
        return JSONResponse({'ok': False, 'message': 'That username is already registered.'}, status_code=400)

    existing_email = db.scalar(select(User).where(User.email == email))
    if existing_email is not None:
        return JSONResponse({'ok': False, 'message': 'That email is already registered.'}, status_code=400)

    account = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
    )

    db.add(account)
    db.commit()

    return JSONResponse(
        {
            'ok': True,
            'message': 'Registration successful. You are now logged in.',
            'user': {'username': username, 'email': email},
        },
        status_code=201,
    )


@app.post('/api/auth/login')
def login(payload: AuthLoginRequest, db: Session = Depends(get_db)) -> JSONResponse:
    email = normalize_email(payload.email)
    password = payload.password

    if not email or not password:
        return JSONResponse({'ok': False, 'message': 'Email and password are required.'}, status_code=400)

    account = db.scalar(select(User).where(User.email == email))

    if not account:
        return JSONResponse({'ok': False, 'message': 'Invalid email or password.'}, status_code=401)

    if not account.password_hash or not check_password_hash(account.password_hash, password):
        return JSONResponse({'ok': False, 'message': 'Invalid email or password.'}, status_code=401)

    return JSONResponse(
        {
            'ok': True,
            'message': 'Login successful.',
            'user': {'username': account.username, 'email': account.email},
        },
        status_code=200,
    )


@app.post('/api/auth/logout')
def logout() -> JSONResponse:
    return JSONResponse({'ok': True, 'message': 'Logged out.'}, status_code=200)


@app.get('/api/posts')
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


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv('HOST', '127.0.0.1'),
        port=int(os.getenv('PORT', '5000')),
    )
