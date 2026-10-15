import logging
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["authentication"])

oauth = OAuth()
if settings.google_client_id_1 and settings.google_client_secret_1:
    oauth.register(
        name="google",
        client_id=settings.google_client_id_1,
        client_secret=settings.google_client_secret_1,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


def cookie_options() -> dict:
    return {
        "key": "access_token",
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": "lax",
        "max_age": settings.jwt_access_token_expire_minutes * 60,
        "path": "/",
    }


@router.get("/google/login")
async def google_login(request: Request):
    if not settings.google_client_id_1 or not settings.google_client_secret_1:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as exc:
        logger.exception("Google OAuth callback failed")
        raise HTTPException(status_code=400, detail="Google authentication failed") from exc

    user_info = token.get("userinfo")
    if not user_info or not user_info.get("sub") or not user_info.get("email") or not user_info.get("email_verified"):
        raise HTTPException(status_code=401, detail="Google account information is missing or unverified")

    email = user_info["email"].strip().lower()
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.google_sub == user_info["sub"]))
        user = result.scalar_one_or_none()
        if user is None:
            # Do not silently merge accounts based only on email; Google subject is the identity key.
            user = User(
                google_sub=user_info["sub"],
                email=email,
                name=user_info.get("name") or email.split("@")[0],
                picture=user_info.get("picture"),
            )
            db.add(user)
        else:
            user.email = email
            user.name = user_info.get("name") or user.name
            user.picture = user_info.get("picture") or user.picture
        await db.commit()
        await db.refresh(user)
        if not user.is_active:
            raise HTTPException(status_code=403, detail="This account is disabled")
        access_token = create_access_token(user_id=user.id, email=user.email)

    response = RedirectResponse(url=settings.frontend_url, status_code=302)
    options = cookie_options()
    response.set_cookie(value=access_token, **options)
    return response


@router.post("/google/logout")
async def google_logout(response: Response):
    response.delete_cookie(
        key="access_token", path="/", httponly=True,
        secure=settings.cookie_secure, samesite="lax",
    )
    return {"message": "Logged out successfully"}
