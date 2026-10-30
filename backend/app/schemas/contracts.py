"""단계 간 JSON 계약. 바꿀 때는 팀 채널 공유 후 PR (docs/architecture.md 함께 수정)."""
from typing import Literal, Optional
from pydantic import BaseModel

EntityType = Literal["name", "age", "school", "area", "time"]
Box = list[int]  # [x1, y1, x2, y2], 원본 픽셀 기준


class TextItem(BaseModel):
    text: str
    box: Optional[Box] = None
    conf: Optional[float] = None
    source: Literal["image", "caption"] = "image"


class ReadResult(BaseModel):          # 1. 판독 결과
    post_id: str
    texts: list[TextItem] = []
    caption: str = ""


class Entity(BaseModel):
    type: EntityType
    value: str
    evidence: Literal["image", "caption"]
    box: Optional[Box] = None


class PostEntities(BaseModel):        # 2. 단서 추출 결과
    post_id: str
    entities: list[Entity] = []


class EngineResult(BaseModel):        # 3. 연결 엔진 결과
    card: dict[EntityType, str] = {}
    sources: dict[EntityType, list[str]] = {}   # 단서별 근거 게시물
    cleanup: list[str] = []                      # 정리 추천 게시물(최소)
    new_items: list[EntityType] = []             # UC2: 새 게시물로 새로 드러나는 항목
