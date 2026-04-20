from __future__ import annotations

from typing import Generator

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

try:
    from .database import SessionLocal
    from .models import User
    from .security import JWT_ALGORITHM, get_jwt_secret
except ImportError:
    from database import SessionLocal
    from models import User
    from security import JWT_ALGORITHM, get_jwt_secret


security = HTTPBearer(auto_error=False)


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