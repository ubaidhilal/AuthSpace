import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.api.auth import router as auth_router
from app.api.routes import router as chat_router
from app.api.dependencies import get_current_user
from app.core.config import settings
from app.db.session import init_db
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.secret_key or len(settings.secret_key) < 32:
        raise RuntimeError("SECRET_KEY must be configured with a long random value (at least 32 characters)")
    if not settings.session_secret or len(settings.session_secret) < 32:
        raise RuntimeError("SESSION_SECRET must be configured with a long random value (at least 32 characters)")
    await init_db()
    logger.info("AuthSpace API started")
    yield


app = FastAPI(title="AuthSpace API", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret, same_site="lax", https_only=settings.cookie_secure)
app.include_router(auth_router)
app.include_router(chat_router)



@app.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"user": {"id": user.id, "email": user.email, "name": user.name, "picture": user.picture}}
