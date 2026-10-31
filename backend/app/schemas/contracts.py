"""API 계약 (기획서 v2.2). 필드 이름을 바꿀 때는 팀 채널 공유 후 프론트 타입(frontend/src/api/types.ts)도 함께 바꾼다."""
from typing import Literal, Optional

from pydantic import BaseModel, Field

EntityType = Literal["name", "age", "school", "area", "time", "contact"]
Evidence = Literal["image", "caption"]
Level = Literal["safe", "caution", "high", "very_high"]
Severity = Literal["high", "medium", "check"]
Box = list[int]  # [x1, y1, x2, y2], 방향 보정한 원본 픽셀 기준
Point = list[int]  # [x, y], 방향 보정한 원본 픽셀 기준
Polygon = list[Point]

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
    polygon: Optional[Polygon] = None
    path: Optional[str] = None
    source: Literal["vlm", "ocr", "caption"] = "vlm"
    conf: Optional[float] = None


class Entity(BaseModel):
    type: EntityType
    value: str
    evidence: Evidence
    box: Optional[Box] = None
    polygon: Optional[Polygon] = None
    path: Optional[str] = None
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
    requires_review: bool = False
    review_reasons: list[str] = []
    pipeline_metrics: dict = Field(default_factory=dict)


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
    caption: str = Field(default="", max_length=2200)
    prior_clues: list[Clue] = []


class Region(BaseModel):
    id: str
    type: EntityType | Literal["unreadable"]
    text: str
    box: Box
    polygon: Optional[Polygon] = None
    path: Optional[str] = None


class Warning(BaseModel):
    type: EntityType | Literal["unreadable"]
    severity: Severity
    why: str
    action: str
    region_ids: list[str] = []
    in_caption: bool = False


class CaptionEdit(BaseModel):
    """캡션에서 뺄 수 있는 한 조각 (가리기 화면에서 하나씩 켜고 끔)"""
    id: str
    type: EntityType
    text: str  # 캡션 안에 그대로 있는 글자. 이 글자를 지우면 된다.


class CheckResponse(BaseModel):
    level_now: Optional[Level] = None
    level_if_posted: Level
    added: list[EntityType] = []
    warnings: list[Warning] = []
    regions: list[Region] = []
    caption_suggestion: str = ""
    caption_edits: list[CaptionEdit] = []
    image_size: list[int]
    requires_review: bool = False
    review_reasons: list[str] = []
    ocr_texts: list[TextItem] = Field(default_factory=list)
    pipeline_metrics: dict = Field(default_factory=dict)


class MaskRegion(BaseModel):
    id: str
    box: Box
    polygon: Optional[Polygon] = None
    text: str = ""
    type: Optional[EntityType | Literal["unreadable"]] = None


class MaskMeta(BaseModel):
    regions: list[MaskRegion] = Field(default_factory=list, max_length=256)
    boxes: list[Box] = Field(default_factory=list, max_length=256)
    polygons: list[Polygon] = Field(default_factory=list, max_length=256)
    region_ids: list[str] = []
    targets: list[str] = []

    def model_post_init(self, __context) -> None:
        if not self.regions and not self.boxes and not self.polygons:
            raise ValueError("regions, boxes, or polygons must contain at least one region")


class MaskFragment(BaseModel):
    region_id: str
    crop_box_original_pixels: Box
    patch_base64: str
    alpha_base64: str
    media_type: Literal["image/png"] = "image/png"


class MaskResponse(BaseModel):
    fragments: list[MaskFragment] = []
    rescan_passed: bool
    leaked: list[str] = []
    meta_clean: bool
    requires_review: bool = False
