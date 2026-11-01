"""Privacy-preserving operational event logging and token-protected viewer API."""
import secrets

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field
from starlette.responses import Response

from app.config import settings
from app.services import audit

router = APIRouter(prefix="/api", tags=["운영 기록"])
AUDIT_VIEW_TOKEN = settings.audit_view_token


class DownloadEvent(BaseModel):
    photos: int = Field(default=1, ge=1, le=10)
    regions: int = Field(default=0, ge=0, le=500)


def _authorize(token: str | None) -> None:
    if not AUDIT_VIEW_TOKEN:
        raise HTTPException(503, "운영 로그 조회가 설정되지 않았어요.")
    if not token or not secrets.compare_digest(token, AUDIT_VIEW_TOKEN):
        raise HTTPException(401, "로그 조회 권한이 없어요.")


@router.get("/admin/audit")
def list_audit_events(
    x_audit_token: str | None = Header(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    _authorize(x_audit_token)
    return {"events": audit.recent(limit), "limit": limit}


@router.post("/audit/download", status_code=204)
def download_started(event: DownloadEvent) -> Response:
    audit.record("download_started", photos=event.photos, regions=event.regions)
    return Response(status_code=204)
