from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

try:
    from ..content import normalize_email
    from ..deps import get_db
    from ..models import User
    from ..schemas import AuthLoginRequest, AuthRegisterRequest
    from ..security import generate_access_token
except ImportError:
    from content import normalize_email
    from deps import get_db
    from models import User
    from schemas import AuthLoginRequest, AuthRegisterRequest
    from security import generate_access_token


router = APIRouter(prefix='/api/auth')


@router.post('/register')
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


@router.post('/login')
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


@router.post('/logout')
def logout() -> JSONResponse:
    return JSONResponse({'ok': True, 'message': 'Logged out.'}, status_code=200)