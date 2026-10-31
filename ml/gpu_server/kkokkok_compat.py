"""Adapter from the image pipeline to the current kkokkok CPU API contract."""
from __future__ import annotations

import base64
import io
import json
import time
from typing import Any

import numpy as np
from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

import app as gpu
from masking import render_mask

router = APIRouter(prefix="/gpu/v1", tags=["Kkokkok CPU API adapter"])
MAX_UPLOAD_BYTES = gpu.MAX_UPLOAD_MB * 1024 * 1024

TYPE_MAP = {
    "name_tag": "name", "person_name": "name",
    "school_or_org": "school",
    "schedule": "time",
    "contact_info": "contact",
    "business_name": "area", "address": "area", "road_name": "area",
    "building_name": "area", "neighborhood_sign": "area",
    "direction_sign": "area", "bus_route": "area", "bus_stop": "area",
    "banner": "area", "other_sign": "area",
}


def _bbox(points: list[list[int]]) -> list[int] | None:
    if len(points) < 3:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return [min(xs), min(ys), max(xs), max(ys)]


async def _image(file: UploadFile) -> Image.Image:
    try:
        raw = await file.read(MAX_UPLOAD_BYTES + 1)
    finally:
        await file.close()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"image exceeds {gpu.MAX_UPLOAD_MB} MiB")
    try:
        image = Image.open(io.BytesIO(raw))
        image.verify()
        image = Image.open(io.BytesIO(raw))
        if image.format not in {"JPEG", "PNG", "WEBP", "TIFF"}:
            raise ValueError("unsupported image format")
        if image.width * image.height > gpu.MAX_PIXELS:
            raise HTTPException(413, f"image exceeds {gpu.MAX_PIXELS} pixels")
        image = ImageOps.exif_transpose(image).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as exc:
        raise HTTPException(415, "invalid image") from exc
    if image.width * image.height > gpu.MAX_PIXELS:
        raise HTTPException(413, f"image exceeds {gpu.MAX_PIXELS} pixels")
    return image


async def _limited(fn, *args):
    if not gpu.state["ready"] or gpu.inference_gate is None:
        raise HTTPException(503, detail="GPU model is not ready")
    with gpu.queue_lock:
        if gpu.inference_gate.locked() and gpu.state["queue_waiting"] >= gpu.MAX_WAITING:
            raise HTTPException(429, detail="GPU inference queue is full")
        gpu.state["queue_waiting"] += 1
    acquired = False
    try:
        async with gpu.inference_gate:
            acquired = True
            with gpu.queue_lock:
                gpu.state["queue_waiting"] = max(0, gpu.state["queue_waiting"] - 1)
            return await run_in_threadpool(fn, *args)
    finally:
        if not acquired:
            with gpu.queue_lock:
                gpu.state["queue_waiting"] = max(0, gpu.state["queue_waiting"] - 1)


def _risk_level(types: set[str]) -> str:
    if not types:
        return "safe"
    has_place = bool(types & {"school", "area"})
    if "name" in types and has_place and "time" in types:
        return "very_high"
    if "name" in types and has_place:
        return "high"
    return "caution"


def _to_front_contract(result: dict[str, Any], photo_id: str) -> dict[str, Any]:
    texts = []
    for line in result.get("ocr_lines", []):
        polygon = line.get("polygon") or []
        box = _bbox(polygon)
        if not box:
            continue
        texts.append({
            "text": line.get("text", ""), "box": box, "polygon": polygon,
            "path": " ".join(f"{'M' if i == 0 else 'L'} {p[0]} {p[1]}" for i, p in enumerate(polygon)) + " Z",
            "source": "ocr", "conf": line.get("score"),
        })

    entities = []
    for item in result.get("risk_items", []):
        entity_type = TYPE_MAP.get(str(item.get("type", "")))
        if not entity_type:
            continue
        loc = item.get("location_in_image") or {}
        polygon = loc.get("polygon") or []
        box = loc.get("bbox") or _bbox(polygon)
        if not box:
            continue
        value = str(item.get("text") or "읽을 수 없는 글자")
        entities.append({
            "type": entity_type, "value": value, "evidence": "image", "box": box,
            "polygon": polygon or None, "path": loc.get("path"),
            "why": str(item.get("risk_evidence") or "사진 속 위치 단서"),
        })
    for clue in result.get("caption_clues", []):
        entities.append({"type": clue["type"], "value": clue["value"], "evidence": "caption",
                         "why": str(clue.get("why", "게시글 단서"))})
    kinds = {item["type"] for item in entities}
    review_reasons = list(result.get("review_reasons", []))
    if any(item.get("ocr_id") is None for item in result.get("risk_items", [])):
        review_reasons.append("A region uses a visual box rather than an OCR text polygon; inspect its location.")
    return {
        "photo_id": photo_id,
        "texts": texts,
        "entities": entities,
        "risk": {"level": _risk_level(kinds), "why": "단서 분류 결과로 규칙 계산"},
        "elapsed_ms": int(float(result.get("timing_seconds", 0)) * 1000),
        "requires_review": bool(result.get("requires_review", False) or review_reasons),
        "review_reasons": review_reasons,
        "pipeline_metrics": {key: result.get(key) for key in (
            "model", "pipeline_order", "input_edges", "vlm_input_token_count",
            "timing_seconds", "timing_breakdown_seconds", "gpu_peak_allocated_bytes",
            "gpu_peak_reserved_bytes", "json_valid")},
    }


@router.get("/health")
async def health(x_api_key: str | None = Header(default=None)):
    gpu.authorize(x_api_key)
    if not gpu.state["ready"]:
        raise HTTPException(503, detail={"status": "loading", **gpu.state})
    return {"status": "ok", **gpu.state}


@router.post("/screen-captions")
async def screen_captions(body: dict, x_api_key: str | None = Header(default=None)):
    gpu.authorize(x_api_key)
    vocabulary = {"유치원": ("유치원", "어린이집"), "반 이름": ("반",), "등·하원": ("등원", "하원", "등교", "하교"),
                  "시간": ("시", ":"), "나이": ("살", "세"), "동네": ("동", "로", "길"), "이름": ("#",)}
    results = []
    for post in body.get("posts", []):
        caption = str(post.get("caption", ""))
        hints = [label for label, tokens in vocabulary.items() if any(token in caption for token in tokens)]
        results.append({"post_id": post.get("post_id", ""), "score": min(1.0, .25 * len(hints)), "hints": hints})
    return {"results": results}


@router.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    meta: str = Form("{}"),
    x_api_key: str | None = Header(default=None),
):
    gpu.authorize(x_api_key)
    try:
        data = json.loads(meta or "{}")
        if not isinstance(data, dict):
            raise ValueError("meta must be an object")
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(400, "meta must be JSON") from exc
    image = await _image(file)
    started = time.perf_counter()
    caption = data.get("caption", "")
    if not isinstance(caption, str) or len(caption) > 2200:
        raise HTTPException(400, "caption must be a string of at most 2200 characters")
    result = await _limited(gpu.infer_sync, image, "mean_blur", 8, 5, None, None, False, False, caption)
    response = _to_front_contract(result, str(data.get("photo_id", "")))
    response["elapsed_ms"] = max(response["elapsed_ms"], int((time.perf_counter() - started) * 1000))
    return response


def _render_fragments(image: Image.Image, regions: list[dict], targets: list[str]) -> dict:
    source = ImageOps.exif_transpose(image).convert("RGB")
    targets = [str(value).strip() for value in targets
               if str(value).strip() not in {"", "읽을 수 없는 글자"}]
    width, height = source.size
    composite = source.copy()  # transient only: OCR rescan; never returned or written to disk
    fragments = []
    pad = max(24, int(np.ceil(8 * 3)) + 4)
    for index, item in enumerate(regions):
        polygon = item.get("polygon")
        if not isinstance(polygon, list) or len(polygon) < 3:
            x1, y1, x2, y2 = item["box"]
            polygon = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
        pts = [[int(p[0]), int(p[1])] for p in polygon]
        xs, ys = zip(*pts)
        left, top = max(0, min(xs) - pad), max(0, min(ys) - pad)
        right, bottom = min(width, max(xs) + pad + 1), min(height, max(ys) + pad + 1)
        crop = source.crop((left, top, right, bottom))
        local_points = [[x - left, y - top] for x, y in pts]
        local_item = {"type": item.get("type", "other_sign"), "text": item.get("text", ""),
                      "location_in_image": {"polygon": local_points}}
        patch, alpha = render_mask(crop, [local_item], mode="mean_blur", sigma=8, dilation_px=2,
                                   layer_only=True)
        composite.paste(patch, (left, top), alpha)
        patch_buf, alpha_buf = io.BytesIO(), io.BytesIO()
        patch.save(patch_buf, format="PNG", compress_level=1)
        alpha.save(alpha_buf, format="PNG", compress_level=1)
        fragments.append({
            "region_id": str(item.get("id") or f"r{index + 1}"),
            "crop_box_original_pixels": [left, top, right, bottom],
            "patch_base64": base64.b64encode(patch_buf.getvalue()).decode("ascii"),
            "alpha_base64": base64.b64encode(alpha_buf.getvalue()).decode("ascii"),
            "media_type": "image/png",
        })

    scale = min(1.0, gpu.OCR_EDGE / max(composite.size))
    ocr_image = composite.resize((max(1, round(width * scale)), max(1, round(height * scale))))
    lines = gpu.ocr.read(np.asarray(ocr_image), source.size)
    norm = lambda value: "".join(ch.lower() for ch in str(value) if ch.isalnum())
    leaked = []
    detected = [norm(line.get("text", "")) for line in lines]
    for target in targets:
        needle = norm(target)
        if needle and any(needle in text for text in detected):
            leaked.append(str(target))
    requires_review = len(targets) < len(regions)
    return {"fragments": fragments, "rescan_passed": bool(targets) and not leaked, "leaked": leaked,
            "meta_clean": True, "requires_review": requires_review}


@router.post("/mask")
async def mask(
    file: UploadFile = File(...),
    meta: str = Form(...),
    x_api_key: str | None = Header(default=None),
):
    gpu.authorize(x_api_key)
    try:
        data = json.loads(meta or "{}")
        if not isinstance(data, dict):
            raise ValueError("meta must be an object")
        regions = data.get("regions", [])
        if not regions:
            boxes = data.get("boxes", [])
            regions = [{"id": f"r{i + 1}", "box": b, "text": ""}
                       for i, b in enumerate(boxes)]
        if not isinstance(regions, list) or not 1 <= len(regions) <= 256 or any(not isinstance(r, dict) for r in regions):
            raise ValueError("1 to 256 regions are required")
        raw_targets = data.get("targets") or [region.get("text", "") for region in regions]
        targets = [str(value).strip() for value in raw_targets
                   if str(value).strip() not in {"", "읽을 수 없는 글자"}]
        if not isinstance(regions, list) or not regions:
            raise ValueError("regions are required")
        image = await _image(file)
        width, height = image.size
        for region in regions:
            box = region.get("box")
            poly = region.get("polygon")
            if box is not None and (len(box) != 4 or not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height)):
                raise ValueError("invalid box")
            if box is None and poly is None:
                raise ValueError("region needs box or polygon")
            if poly is not None and (len(poly) < 3 or any(len(p) != 2 or not (0 <= p[0] <= width and 0 <= p[1] <= height) for p in poly)):
                raise ValueError("invalid polygon")
            if poly and sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, poly[1:] + poly[:1])) == 0:
                raise ValueError("empty polygon")
    except (json.JSONDecodeError, TypeError, KeyError, ValueError) as exc:
        raise HTTPException(400, "invalid masking metadata") from exc
    return await _limited(_render_fragments, image, regions, targets)


gpu.app.include_router(router)
