import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles

from app.core.db import init_db
from app.routers.api import router as api_router
from app.routers.auth import router as auth_router
from app.routers.pages import router as pages_router
from app.routers.profile import router as profile_router

APP_DIR = Path(__file__).resolve().parent


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"{name} environment variable is required.")
    return value


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Sine Auth Demo", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=required_env("SESSION_SECRET"),
    same_site="lax",
    https_only=env_bool("SESSION_HTTPS_ONLY", False),
)
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
app.include_router(api_router)
app.include_router(pages_router)
app.include_router(auth_router)
app.include_router(profile_router)
