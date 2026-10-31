"""API 계약 (기획서 v2.2). 필드 이름을 바꿀 때는 팀 채널 공유 후 프론트 타입(frontend/src/api/types.ts)도 함께 바꾼다."""
from typing import Literal, Optional

from pydantic import BaseModel, Field

EntityType = Literal["name", "age", "school", "area", "time"]
Evidence = Literal["image", "caption"]
Level = Literal["safe", "caution", "high", "very_high"]
Severity = Literal["high", "medium", "check"]
Box = list[int]  # [x1, y1, x2, y2], 방향 보정한 원본 픽셀 기준

LEVEL_ORDER: list[Level] = ["safe", "caution", "high", "very_high"]
PLACE: set[str] = {"school", "area"}


def risk_level(types: set[str]) -> Level:
    """위험 단계 표기 규칙. 단서 판단은 Qwen이 하고, 단계 표기는 이 표로만 정한다."""
    if not types:
        return "safe"
    has_place = bool(types & PLACE)
    if "name" in types and has_place and "time" in types:
        return "very_high"
    if "name" in types and has_place:
        return "high"
    return "caution"


# ---------- 공통 ----------
class TextItem(BaseModel):
    text: str
    box: Optional[Box] = None
    source: Literal["vlm", "ocr", "caption"] = "vlm"
    conf: Optional[float] = None


class Entity(BaseModel):
    type: EntityType
    value: str
    evidence: Evidence
    box: Optional[Box] = None
    why: str = ""


class Clue(BaseModel):
    """UC1 결과 요약. 브라우저 sessionStorage에만 두고 UC2 때 다시 보낸다."""
    type: EntityType
    value: str


# ---------- GPU 모델 앱 응답 ----------
class Risk(BaseModel):
    level: Level
    why: str = ""


class AnalyzeResult(BaseModel):
    photo_id: str
    texts: list[TextItem] = []
    entities: list[Entity] = []
    risk: Optional[Risk] = None
    elapsed_ms: int = 0


class ScreenResult(BaseModel):
    post_id: str
    score: float
    hints: list[str] = []


# ---------- UC1 ----------
class PhotoSummary(BaseModel):
    photo_id: str
    thumb_url: str


class PostSummary(BaseModel):
    post_id: str
    posted_at: Optional[str] = None
    caption: str = ""
    photos: list[PhotoSummary] = []
    recommended: bool = False
    hints: list[str] = []
    score: float = 0.0


class UploadResponse(BaseModel):
    upload_id: str
    total_posts: int
    total_photos: int
    max_select: int
    recommended_photo_ids: list[str] = []
    posts: list[PostSummary]


class JobCreate(BaseModel):
    upload_id: str
    photo_ids: list[str] = Field(min_length=1)


class JobCreated(BaseModel):
    job_id: str
    total: int


class CleanupItem(BaseModel):
    post_id: str
    posted_at: Optional[str] = None
    caption: str = ""
    photo_ids: list[str] = []
    clues: list[Clue] = []
    cuts: list[str] = []  # 끊기는 연결, 예: "이름 ↔ 유치원"


class EngineResult(BaseModel):
    level: Level
    reason: list[EntityType] = []
    card: dict[str, str] = {}
    sources: dict[str, list[str]] = {}
    explanation: str = ""
    cleanup: list[str] = []
    cleanup_items: list[CleanupItem] = []
    level_after_cleanup: Optional[Level] = None
    remaining_after_cleanup: list[EntityType] = []
    clues: list[Clue] = []
    analyzed_posts: int = 0
    failed_photo_ids: list[str] = []


class JobStatus(BaseModel):
    status: Literal["queued", "running", "done", "failed"]
    done: int
    total: int
    result: Optional[EngineResult] = None
    error: Optional[str] = None


# ---------- UC2 ----------
class CheckMeta(BaseModel):
    caption: str = ""
    prior_clues: list[Clue] = []


class Region(BaseModel):
    id: str
    type: EntityType | Literal["unreadable"]
    text: str
    box: Box


class Warning(BaseModel):
    type: EntityType | Literal["unreadable"]
    severity: Severity
    why: str
    action: str
    region_ids: list[str] = []
    in_caption: bool = False


class CheckResponse(BaseModel):
    level_now: Optional[Level] = None
    level_if_posted: Level
    added: list[EntityType] = []
    warnings: list[Warning] = []
    regions: list[Region] = []
    caption_suggestion: str = ""
    image_size: list[int]


class MaskMeta(BaseModel):
    boxes: list[Box] = Field(min_length=1)
    targets: list[str] = []


class MaskResponse(BaseModel):
    image_base64: str
    rescan_passed: bool
    leaked: list[str] = []
    meta_clean: bool
