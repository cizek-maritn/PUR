from __future__ import annotations

import html
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Generator

import bleach
import jwt
from fastapi import Depends, FastAPI
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, selectinload
from werkzeug.security import check_password_hash, generate_password_hash

from database import Base, SessionLocal, engine
from models import BlogPost, User
from schemas import AuthLoginRequest, AuthRegisterRequest, BlogPostCreateRequest
from seed import seed_demo_data


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)

security = HTTPBearer(auto_error=False)
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24
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


def get_jwt_secret() -> str:
    return os.getenv('JWT_SECRET_KEY', 'dev-change-me')


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


def generate_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': user.username,
        'email': user.email,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(hours=JWT_EXPIRY_HOURS)).timestamp()),
    }

    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != 'bearer':
        raise HTTPException(status_code=401, detail='Authentication required.')

    try:
        payload = jwt.decode(credentials.credentials, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail='Invalid or expired token.') from exc

    username = payload.get('sub')
    if not isinstance(username, str) or not username.strip():
        raise HTTPException(status_code=401, detail='Invalid token payload.')

    account = db.scalar(select(User).where(User.username == username))
    if account is None:
        raise HTTPException(status_code=401, detail='User account not found.')

    return account


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
    db.refresh(account)
    token = generate_access_token(account)

    return JSONResponse(
        {
            'ok': True,
            'message': 'Registration successful. You are now logged in.',
            'user': {'username': username, 'email': email},
            'token': token,
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

    token = generate_access_token(account)

    return JSONResponse(
        {
            'ok': True,
            'message': 'Login successful.',
            'user': {'username': account.username, 'email': account.email},
            'token': token,
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


@app.post('/api/posts')
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


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv('HOST', '127.0.0.1'),
        port=int(os.getenv('PORT', '5000')),
    )
