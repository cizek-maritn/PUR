from __future__ import annotations

import os
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

try:
    from .database import Base, SessionLocal, engine
    from .routes.auth import router as auth_router
    from .routes.posts import router as posts_router
    from .seed import seed_demo_data
except ImportError:
    from database import Base, SessionLocal, engine
    from routes.auth import router as auth_router
    from routes.posts import router as posts_router
    from seed import seed_demo_data


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)


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


app.include_router(auth_router)
app.include_router(posts_router)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv('HOST', '127.0.0.1'),
        port=int(os.getenv('PORT', '5000')),
    )
