"""Signed anonymous browser sessions for temporary upload/job ownership."""
import hashlib
import hmac
import re
import secrets

from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

COOKIE = "kk.session"
_key = (settings.session_secret or secrets.token_hex(32)).encode()
_id = re.compile(r"^[a-f0-9]{32}$")


def sign(owner: str) -> str:
    return owner + "." + hmac.new(_key, owner.encode(), hashlib.sha256).hexdigest()


def verify(cookie: str) -> str | None:
    if not re.fullmatch(r"[a-f0-9]{32}\.[a-f0-9]{64}", cookie):
        return None
    owner, separator, _ = cookie.partition(".")
    if not separator or not _id.fullmatch(owner):
        return None
    return owner if hmac.compare_digest(cookie, sign(owner)) else None


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        owner = verify(request.cookies.get(COOKIE, ""))
        fresh = owner is None
        request.state.owner_id = owner or secrets.token_hex(16)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        if fresh:
            response.set_cookie(COOKIE, sign(request.state.owner_id), httponly=True,
                                secure=settings.session_cookie_secure, samesite="strict",
                                max_age=86400, path="/")
        return response
