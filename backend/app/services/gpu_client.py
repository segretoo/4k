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
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps, ImageStat

from app.config import settings
from app.schemas.contracts import AnalyzeResult, Entity, MaskResponse, ScreenResult, TextItem, risk_level
from app.services.text_rules import caption_entities, keyword_hints
from app.services.gpu_queue import gpu_queue


class GpuError(RuntimeError):
    pass


# ---------------- 진짜 GPU 모델 앱 ----------------
class HttpGpu:
    def __init__(self) -> None:
        self.base = settings.gpu_url.rstrip("/")
        self.headers = {"X-API-Key": settings.gpu_api_key} if settings.gpu_api_key else {}

    async def _post(self, path: str, *, owner_id: str = "", **kwargs) -> dict:
        async with gpu_queue.slot(owner_id):
            try:
                async with httpx.AsyncClient(timeout=settings.gpu_timeout_s) as client:
                    r = await client.post(self.base + path, headers=self.headers, **kwargs)
                    r.raise_for_status()
                    return r.json()
            except httpx.HTTPError as e:
                raise GpuError(f"GPU 서버 호출 실패: {path}") from e

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                return (await client.get(self.base + "/gpu/v1/health", headers=self.headers)).status_code == 200
        except httpx.HTTPError:
            return False

    async def screen_captions(self, posts: list[dict]) -> list[ScreenResult]:
        data = await self._post("/gpu/v1/screen-captions", owner_id=posts[0].get("owner_id", "") if posts else "",
                                json={"posts": [{k: v for k, v in post.items() if k != "owner_id"} for post in posts]})
        return [ScreenResult(**r) for r in data.get("results", [])]

    async def analyze(self, image: bytes, meta: dict) -> AnalyzeResult:
        data = await self._post(
            "/gpu/v1/analyze",
            owner_id=meta.get("owner_id", ""),
            files={"file": ("photo.jpg", image, "image/jpeg")},
            data={"meta": json.dumps(meta, ensure_ascii=False)},
        )
        entities = data.setdefault("entities", [])
        known = {(item.get("type"), item.get("value"), item.get("evidence")) for item in entities}
        for candidate in caption_entities(meta.get("caption", "")):
            key = (candidate.type, candidate.value, candidate.evidence)
            if key not in known:
                entities.append(candidate.model_dump())
                known.add(key)
        return AnalyzeResult(**data)

    async def mask(self, image: bytes, boxes: list[list[int]], targets: list[str],
                   polygons: list[list[list[int]]] | None = None,
                   region_ids: list[str] | None = None,
                   regions: list[dict] | None = None, owner_id: str = "") -> MaskResponse:
        meta = {"boxes": boxes, "targets": targets, "polygons": polygons or [],
                "region_ids": region_ids or [], "regions": regions or []}
        data = await self._post(
            "/gpu/v1/mask",
            owner_id=owner_id,
            files={"file": ("photo.jpg", image, "image/jpeg")},
            data={"meta": json.dumps(meta, ensure_ascii=False)},
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
    if not p.exists():
        return {}
    fx = json.loads(p.read_text(encoding="utf-8"))
    # 파일 이름이 바뀌거나(예: "uc2_demo (1).jpg") 서버가 다시 저장해도 같은 사진이면 알아보도록
    # 작은 흑백 지문(16x16)을 같이 만들어 둔다
    fx["__prints__"] = [(_print(img.read_bytes()), img.name) for img in p.parent.glob("*.jpg") if img.name in fx]
    return fx


def _print(image: bytes) -> list[int]:
    with Image.open(io.BytesIO(image)) as im:
        return list(ImageOps.exif_transpose(im).convert("L").resize((16, 16)).getdata())


def _lookup(image: bytes, source: str) -> dict:
    fx = _fixture()
    if source in fx:
        return fx[source]
    try:
        mine = _print(image)
    except Exception:
        return {}
    best = min(
        ((sum(abs(a - b) for a, b in zip(mine, fp)) / len(fp), name) for fp, name in fx.get("__prints__", [])),
        default=(999.0, ""),
    )
    return fx[best[1]] if best[0] < 4 else {}


class MockGpu:
    async def health(self) -> bool:
        return True

    async def screen_captions(self, posts: list[dict]) -> list[ScreenResult]:
        async with gpu_queue.slot(posts[0].get("owner_id", "") if posts else ""):
            await asyncio.sleep(min(settings.mock_delay_s, 0.3))
        out = []
        for p in posts:
            hints = keyword_hints(p.get("caption", ""))
            out.append(ScreenResult(post_id=p["post_id"], score=min(1.0, 0.25 * len(hints)), hints=hints))
        return out

    async def analyze(self, image: bytes, meta: dict) -> AnalyzeResult:
        async with gpu_queue.slot(meta.get("owner_id", "")):
            await asyncio.sleep(settings.mock_delay_s)
        fx = _lookup(image, meta.get("source", ""))
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

    async def mask(self, image: bytes, boxes: list[list[int]], targets: list[str],
                   polygons: list[list[list[int]]] | None = None,
                   region_ids: list[str] | None = None,
                   regions: list[dict] | None = None, owner_id: str = "") -> MaskResponse:
        """CPU demo returns alpha-composited fragments, never a completed full image."""
        async with gpu_queue.slot(owner_id):
            await asyncio.sleep(min(settings.mock_delay_s, 0.3))
        with Image.open(io.BytesIO(image)) as im:
            source = ImageOps.exif_transpose(im).convert("RGB")
        selected = regions or []
        if not selected:
            selected = []
            for i, box in enumerate(boxes):
                polygon = (polygons or [])[i] if i < len(polygons or []) else None
                selected.append({"id": (region_ids or [])[i] if i < len(region_ids or []) else f"r{i+1}",
                                 "box": box, "polygon": polygon, "text": targets[i] if i < len(targets) else ""})
        width, height = source.size
        fragments = []
        for index, region in enumerate(selected):
            points = region.get("polygon")
            if not points:
                x1, y1, x2, y2 = region["box"]
                points = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
            xs, ys = zip(*points)
            pad = 28
            left, top = max(0, min(xs) - pad), max(0, min(ys) - pad)
            right, bottom = min(width, max(xs) + pad + 1), min(height, max(ys) + pad + 1)
            crop = source.crop((left, top, right, bottom))
            core = Image.new("L", crop.size, 0)
            local_points = [(int(x-left), int(y-top)) for x, y in points]
            ImageDraw.Draw(core).polygon(local_points, fill=255)
            core = core.filter(ImageFilter.MaxFilter(5))
            outer = core.filter(ImageFilter.MaxFilter(27))
            ring = ImageChops.subtract(outer, core)
            stats = ImageStat.Stat(crop, mask=ring)
            fill = tuple(int(round(c)) for c in stats.mean[:3])
            feather = ImageChops.lighter(core, core.filter(ImageFilter.GaussianBlur(8)))
            patch = Image.new("RGB", crop.size, fill)
            patch_buf, alpha_buf = io.BytesIO(), io.BytesIO()
            patch.save(patch_buf, format="PNG", compress_level=1)
            feather.save(alpha_buf, format="PNG", compress_level=1)
            fragments.append({
                "region_id": str(region.get("id") or f"r{index+1}"),
                "crop_box_original_pixels": [left, top, right, bottom],
                "patch_base64": base64.b64encode(patch_buf.getvalue()).decode("ascii"),
                "alpha_base64": base64.b64encode(alpha_buf.getvalue()).decode("ascii"),
                "media_type": "image/png",
            })
        return MaskResponse(fragments=fragments, rescan_passed=True, leaked=[], meta_clean=True)


def get_gpu() -> HttpGpu | MockGpu:
    return MockGpu() if settings.gpu_mock else HttpGpu()
