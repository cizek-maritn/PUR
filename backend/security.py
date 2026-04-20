from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt

try:
    from .models import User
except ImportError:
    from models import User


JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24


def get_jwt_secret() -> str:
    return os.getenv('JWT_SECRET_KEY', 'dev-change-me')


def generate_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': user.username,
        'email': user.email,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(hours=JWT_EXPIRY_HOURS)).timestamp()),
    }

    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)