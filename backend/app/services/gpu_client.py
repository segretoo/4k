"""GPU 모델 앱 호출은 이 파일에서만 한다.

GPU_MOCK=true(기본)면 GPU 없이 가짜 응답을 돌려준다. 진짜 모델 앱이 준비되면
.env에서 GPU_MOCK=false, GPU_URL=http://<GPU 내부 IP>:<포트> 로 바꾸기만 하면 된다.
"""
import asyncio
import base64
import io
import json
from functools import lru_cache

import httpx
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from app.config import settings
from app.schemas.contracts import AnalyzeResult, Entity, MaskResponse, ScreenResult, TextItem, risk_level
from app.services.text_rules import caption_entities, keyword_hints

# GPU는 한 번에 한 작업만 (L4 24GB 과부하 방지)
_gpu_lock = asyncio.Lock()


class GpuError(RuntimeError):
    pass


# ---------------- 진짜 GPU 모델 앱 ----------------
class HttpGpu:
    def __init__(self) -> None:
        self.base = settings.gpu_url.rstrip("/")

    async def _post(self, path: str, **kwargs) -> dict:
        async with _gpu_lock:
            try:
                async with httpx.AsyncClient(timeout=settings.gpu_timeout_s) as client:
                    r = await client.post(self.base + path, **kwargs)
                    r.raise_for_status()
                    return r.json()
            except httpx.HTTPError as e:
                raise GpuError(f"GPU 서버 호출 실패: {path}") from e

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                return (await client.get(self.base + "/gpu/v1/health")).status_code == 200
        except httpx.HTTPError:
            return False

    async def screen_captions(self, posts: list[dict]) -> list[ScreenResult]:
        data = await self._post("/gpu/v1/screen-captions", json={"posts": posts})
        return [ScreenResult(**r) for r in data.get("results", [])]

    async def analyze(self, image: bytes, meta: dict) -> AnalyzeResult:
        data = await self._post(
            "/gpu/v1/analyze",
            files={"file": ("photo.jpg", image, "image/jpeg")},
            data={"meta": json.dumps(meta, ensure_ascii=False)},
        )
        return AnalyzeResult(**data)

    async def mask(self, image: bytes, boxes: list[list[int]], targets: list[str]) -> MaskResponse:
        data = await self._post(
            "/gpu/v1/mask",
            files={"file": ("photo.jpg", image, "image/jpeg")},
            data={"meta": json.dumps({"boxes": boxes, "targets": targets}, ensure_ascii=False)},
        )
        return MaskResponse(**data)


# ---------------- 가짜 GPU (개발용) ----------------
@lru_cache
def _fixture() -> dict:
    """시연 데이터 정답표(data/demo/mock_gpu.json). 사진 파일 이름 → 판독 결과."""
    p = settings.mock_fixture
    if not p.is_absolute():
        from pathlib import Path
        p = Path(__file__).resolve().parents[2] / p
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


class MockGpu:
    async def health(self) -> bool:
        return True

    async def screen_captions(self, posts: list[dict]) -> list[ScreenResult]:
        await asyncio.sleep(min(settings.mock_delay_s, 0.3))
        out = []
        for p in posts:
            hints = keyword_hints(p.get("caption", ""))
            out.append(ScreenResult(post_id=p["post_id"], score=min(1.0, 0.25 * len(hints)), hints=hints))
        return out

    async def analyze(self, image: bytes, meta: dict) -> AnalyzeResult:
        async with _gpu_lock:
            await asyncio.sleep(settings.mock_delay_s)
        fx = _fixture().get(meta.get("source", ""), {})
        texts = [TextItem(**t) for t in fx.get("texts", [])]
        entities = [Entity(**e) for e in fx.get("entities", [])] + caption_entities(meta.get("caption", ""))
        level = risk_level({e.type for e in entities})
        return AnalyzeResult(
            photo_id=meta.get("photo_id", ""),
            texts=texts,
            entities=entities,
            risk={"level": level, "why": "가짜 GPU 응답 (GPU_MOCK=true)"},
            elapsed_ms=int(settings.mock_delay_s * 1000),
        )

    async def mask(self, image: bytes, boxes: list[list[int]], targets: list[str]) -> MaskResponse:
        """가짜 가리기: 상자 둘레의 평균색으로 채우고 흐리게. 진짜는 GPU의 OpenCV NS 인페인팅."""
        async with _gpu_lock:
            await asyncio.sleep(min(settings.mock_delay_s, 0.3))
        with Image.open(io.BytesIO(image)) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            draw = ImageDraw.Draw(im)
            w, h = im.size
            for x1, y1, x2, y2 in boxes:
                pad_x, pad_y = int((x2 - x1) * 0.15), int((y2 - y1) * 0.15)
                x1, y1, x2, y2 = max(0, x1 - pad_x), max(0, y1 - pad_y), min(w, x2 + pad_x), min(h, y2 + pad_y)
                ring = im.crop((max(0, x1 - 6), max(0, y1 - 6), min(w, x2 + 6), min(h, y2 + 6))).resize((1, 1))
                draw.rectangle((x1, y1, x2, y2), fill=ring.getpixel((0, 0)))
                region = im.crop((x1, y1, x2, y2)).filter(ImageFilter.GaussianBlur(4))
                im.paste(region, (x1, y1))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=92)  # EXIF를 넘기지 않아 메타데이터 없음
        return MaskResponse(
            image_base64=base64.b64encode(buf.getvalue()).decode(),
            rescan_passed=True,
            leaked=[],
            meta_clean=True,
        )


def get_gpu() -> HttpGpu | MockGpu:
    return MockGpu() if settings.gpu_mock else HttpGpu()
