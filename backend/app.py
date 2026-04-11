from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
CORS(app)

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


def get_json_body() -> dict[str, Any]:
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else {}


@app.post('/api/auth/register')
def register() -> tuple[Any, int]:
    body = get_json_body()

    username = str(body.get('username', '')).strip()
    email = normalize_email(str(body.get('email', '')))
    password = str(body.get('password', ''))
    confirm_password = str(body.get('confirmPassword', ''))

    if not username or not email or not password or not confirm_password:
        return jsonify({'ok': False, 'message': 'Please fill in all required registration fields.'}), 400

    if password != confirm_password:
        return jsonify({'ok': False, 'message': 'Password and confirmation password do not match.'}), 400

    accounts = read_accounts()

    if any(str(account.get('username', '')).strip().lower() == username.lower() for account in accounts):
        return jsonify({'ok': False, 'message': 'That username is already registered.'}), 400

    if any(normalize_email(str(account.get('email', ''))) == email for account in accounts):
        return jsonify({'ok': False, 'message': 'That email is already registered.'}), 400

    account = {
        'username': username,
        'email': email,
        'passwordHash': generate_password_hash(password),
    }

    accounts.append(account)
    write_accounts(accounts)

    return (
        jsonify(
            {
                'ok': True,
                'message': 'Registration successful. You are now logged in.',
                'user': {'username': username, 'email': email},
            }
        ),
        201,
    )


@app.post('/api/auth/login')
def login() -> tuple[Any, int]:
    body = get_json_body()

    email = normalize_email(str(body.get('email', '')))
    password = str(body.get('password', ''))

    if not email or not password:
        return jsonify({'ok': False, 'message': 'Email and password are required.'}), 400

    account = next(
        (candidate for candidate in read_accounts() if normalize_email(str(candidate.get('email', ''))) == email),
        None,
    )

    if not account:
        return jsonify({'ok': False, 'message': 'Invalid email or password.'}), 401

    password_hash = str(account.get('passwordHash', ''))

    if not password_hash or not check_password_hash(password_hash, password):
        return jsonify({'ok': False, 'message': 'Invalid email or password.'}), 401

    return (
        jsonify(
            {
                'ok': True,
                'message': 'Login successful.',
                'user': {'username': str(account.get('username', '')), 'email': email},
            }
        ),
        200,
    )


@app.post('/api/auth/logout')
def logout() -> tuple[Any, int]:
    return jsonify({'ok': True, 'message': 'Logged out.'}), 200


if __name__ == '__main__':
    ensure_data_file()
    app.run(host='127.0.0.1', port=5000, debug=True)
