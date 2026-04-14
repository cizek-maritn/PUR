from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from werkzeug.security import check_password_hash, generate_password_hash

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)

DATA_FILE = Path(__file__).resolve().parents[1] / 'data' / 'accounts.json'
FILE_LOCK = Lock()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def ensure_data_file() -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps({'accounts': []}, indent=2), encoding='utf-8')


def read_accounts() -> list[dict[str, Any]]:
    ensure_data_file()

    with FILE_LOCK:
        try:
            payload = json.loads(DATA_FILE.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            payload = {'accounts': []}

        accounts = payload.get('accounts', [])
        return accounts if isinstance(accounts, list) else []


def write_accounts(accounts: list[dict[str, Any]]) -> None:
    ensure_data_file()

    with FILE_LOCK:
        DATA_FILE.write_text(
            json.dumps({'accounts': accounts}, indent=2),
            encoding='utf-8',
        )


async def get_json_body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        return {}

    return body if isinstance(body, dict) else {}


@app.post('/api/auth/register')
async def register(request: Request) -> JSONResponse:
    body = await get_json_body(request)

    username = str(body.get('username', '')).strip()
    email = normalize_email(str(body.get('email', '')))
    password = str(body.get('password', ''))
    confirm_password = str(body.get('confirmPassword', ''))

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

    accounts = read_accounts()

    if any(str(account.get('username', '')).strip().lower() == username.lower() for account in accounts):
        return JSONResponse({'ok': False, 'message': 'That username is already registered.'}, status_code=400)

    if any(normalize_email(str(account.get('email', ''))) == email for account in accounts):
        return JSONResponse({'ok': False, 'message': 'That email is already registered.'}, status_code=400)

    account = {
        'username': username,
        'email': email,
        'passwordHash': generate_password_hash(password),
    }

    accounts.append(account)
    write_accounts(accounts)

    return JSONResponse(
        {
            'ok': True,
            'message': 'Registration successful. You are now logged in.',
            'user': {'username': username, 'email': email},
        },
        status_code=201,
    )


@app.post('/api/auth/login')
async def login(request: Request) -> JSONResponse:
    body = await get_json_body(request)

    email = normalize_email(str(body.get('email', '')))
    password = str(body.get('password', ''))

    if not email or not password:
        return JSONResponse({'ok': False, 'message': 'Email and password are required.'}, status_code=400)

    account = next(
        (candidate for candidate in read_accounts() if normalize_email(str(candidate.get('email', ''))) == email),
        None,
    )

    if not account:
        return JSONResponse({'ok': False, 'message': 'Invalid email or password.'}, status_code=401)

    password_hash = str(account.get('passwordHash', ''))

    if not password_hash or not check_password_hash(password_hash, password):
        return JSONResponse({'ok': False, 'message': 'Invalid email or password.'}, status_code=401)

    return JSONResponse(
        {
            'ok': True,
            'message': 'Login successful.',
            'user': {'username': str(account.get('username', '')), 'email': email},
        },
        status_code=200,
    )


@app.post('/api/auth/logout')
async def logout() -> JSONResponse:
    return JSONResponse({'ok': True, 'message': 'Logged out.'}, status_code=200)


if __name__ == '__main__':
    ensure_data_file()
    import uvicorn

    uvicorn.run(app, host='127.0.0.1', port=5000)
