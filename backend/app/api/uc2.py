"""UC2 올리기 전 점검 API. 서버는 사진을 저장하지 않고, 가리기 때 브라우저가 원본을 다시 보낸다."""
import io
import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import ValidationError

from app.config import settings
from app.schemas.contracts import CheckMeta, CheckResponse, MaskMeta, MaskResponse
from app.services import precheck
from app.services.gpu_client import GpuError, get_gpu

router = APIRouter(prefix="/api/uc2", tags=["UC2 올리기 전 점검"])


async def _read_image(file: UploadFile) -> tuple[bytes, tuple[int, int]]:
    """크기·형식 검사 후 방향 보정한 JPEG 바이트로 바꾼다 (EXIF 제거)."""
    raw = await file.read(settings.max_photo_mb * 1024 * 1024 + 1)
    if len(raw) > settings.max_photo_mb * 1024 * 1024:
        raise HTTPException(413, f"사진이 너무 커요. {settings.max_photo_mb}MB 이하로 올려 주세요.")
    try:
        with Image.open(io.BytesIO(raw)) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            if max(im.size) > settings.max_image_side:
                im.thumbnail((settings.max_image_side, settings.max_image_side))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=92)
            return buf.getvalue(), im.size
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as e:
        raise HTTPException(400, "사진 파일(JPEG·PNG)만 올릴 수 있어요.") from e


def _meta(raw: str, model):
    try:
        return model(**json.loads(raw or "{}"))
    except (json.JSONDecodeError, ValidationError, TypeError) as e:
        raise HTTPException(400, "요청 형식이 올바르지 않아요.") from e


@router.post("/check", response_model=CheckResponse)
async def check(file: UploadFile = File(...), meta: str = Form("{}")) -> CheckResponse:
    m: CheckMeta = _meta(meta, CheckMeta)
    image, size = await _read_image(file)
    try:
        result = await get_gpu().analyze(image, {"photo_id": "uc2", "post_id": "uc2", "caption": m.caption, "source": file.filename or ""})
    except GpuError as e:
        raise HTTPException(503, "분석 서버가 응답하지 않아요. 잠시 후 다시 시도해 주세요.") from e
    return precheck.build(result, m.caption, m.prior_clues, size)


@router.post("/mask", response_model=MaskResponse)
async def mask(file: UploadFile = File(...), meta: str = Form(...)) -> MaskResponse:
    m: MaskMeta = _meta(meta, MaskMeta)
    image, (w, h) = await _read_image(file)
    for b in m.boxes:
        if len(b) != 4 or not (0 <= b[0] < b[2] <= w and 0 <= b[1] < b[3] <= h):
            raise HTTPException(400, "가릴 영역 좌표가 올바르지 않아요.")
    try:
        return await get_gpu().mask(image, m.boxes, m.targets)
    except GpuError as e:
        raise HTTPException(503, "분석 서버가 응답하지 않아요. 잠시 후 다시 시도해 주세요.") from e
