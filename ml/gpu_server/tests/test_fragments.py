"""GPU contract/render tests use synthetic images and a stub model, never download weights."""
import base64
import importlib.util
import io
from pathlib import Path
import sys
import threading
from types import SimpleNamespace

from fastapi import FastAPI
import numpy as np
from PIL import Image, ImageDraw
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from masking import render_mask


@pytest.fixture
def adapter(monkeypatch):
    stub = SimpleNamespace(MAX_UPLOAD_MB=25, MAX_PIXELS=40_000_000, OCR_EDGE=2200,
                           app=FastAPI(), state={"ready": True, "queue_waiting": 0},
                           MAX_WAITING=1, queue_lock=threading.Lock(), inference_gate=None,
                           ocr=SimpleNamespace(read=lambda *_: []), authorize=lambda _: None)
    monkeypatch.setitem(sys.modules, "app", stub)
    spec = importlib.util.spec_from_file_location("gpu_adapter_test", ROOT / "kkokkok_compat.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample():
    image = Image.new("RGB", (180, 100), (90, 120, 150))
    ImageDraw.Draw(image).rectangle((60, 35, 100, 55), fill="black")
    item = {"type": "business_name", "location_in_image": {
        "polygon": [[58, 33], [102, 33], [102, 57], [58, 57]]}}
    return image, item


def test_fragment_alpha_composes_exactly_once():
    image, item = sample()
    expected, _ = render_mask(image, [item])
    patch, alpha = render_mask(image, [item], layer_only=True)
    composed = Image.composite(patch, image, alpha)
    assert np.max(np.abs(np.asarray(composed).astype(int) - np.asarray(expected).astype(int))) <= 1
    assert alpha.getpixel((80, 45)) == 255
    assert alpha.getpixel((0, 0)) == 0
    assert 0 < alpha.getpixel((55, 45)) < 255
    assert composed.getpixel((80, 45)) == (90, 120, 150)
    assert composed.getpixel((0, 0)) == image.getpixel((0, 0))


def test_fragment_response_and_rescan(adapter):
    image, item = sample()
    region = {"id": "r1", "text": "가게", "box": [58, 33, 102, 57],
              "polygon": item["location_in_image"]["polygon"]}
    result = adapter._render_fragments(image, [region], ["가게"])
    assert result["rescan_passed"] is True
    assert "image_base64" not in result
    fragment = result["fragments"][0]
    assert fragment["region_id"] == "r1"
    alpha = Image.open(io.BytesIO(base64.b64decode(fragment["alpha_base64"])))
    patch = Image.open(io.BytesIO(base64.b64decode(fragment["patch_base64"])))
    assert alpha.mode == "L" and patch.mode == "RGB"
    assert alpha.size == patch.size
    adapter.gpu.ocr = SimpleNamespace(read=lambda *_: [{"text": "가게"}])
    assert adapter._render_fragments(image, [region], ["가게"])["leaked"] == ["가게"]
    assert adapter._render_fragments(image, [region], ["가"])["leaked"] == ["가"]
    unknown = adapter._render_fragments(image, [region], ["읽을 수 없는 글자"])
    assert unknown["rescan_passed"] is False and unknown["requires_review"] is True


def test_visual_box_is_not_reported_as_ocr_text(adapter):
    response = adapter._to_front_contract({"risk_items": [{"type": "bus_stop", "text": None,
        "risk_evidence": "정류장처럼 보임", "location_in_image": {"bbox": [1, 2, 5, 8]}}]}, "p1")
    assert response["entities"][0]["value"] == "읽을 수 없는 글자"
    assert response["requires_review"] is True


def test_ocr_numpy_arrays_map_to_original_pixels():
    from ocr_backend import PaddleOCRBackend

    backend = PaddleOCRBackend.__new__(PaddleOCRBackend)
    backend.engine = SimpleNamespace(predict=lambda _: [{"rec_texts": ["학교"],
        "rec_scores": np.asarray([.99]),
        "rec_polys": np.asarray([[[10, 20], [40, 20], [40, 30], [10, 30]]])}])
    lines = backend.read(np.zeros((50, 100, 3), dtype=np.uint8), (200, 100))
    assert lines[0]["polygon"] == [[20, 40], [80, 40], [80, 60], [20, 60]]
    assert lines[0]["text"] == "학교"


def test_caption_clues_have_no_image_geometry(adapter):
    response = adapter._to_front_contract({"caption_clues": [
        {"type": "name", "value": "하늘", "why": "게시글 이름"}]}, "p1")
    assert response["entities"] == [{"type": "name", "value": "하늘", "evidence": "caption", "why": "게시글 이름"}]
    assert response["risk"]["level"] == "caution"


def test_mask_accepts_dense_signage_without_truncating_candidates(adapter, monkeypatch):
    import json
    from fastapi.testclient import TestClient

    async def limited(fn, *args):
        return fn(*args)

    monkeypatch.setattr(adapter, "_limited", limited)
    image, item = sample()
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    regions = [{"id": f"r{i}", "text": "가게", "box": [58, 33, 102, 57],
                "polygon": item["location_in_image"]["polygon"]} for i in range(72)]
    with TestClient(adapter.gpu.app) as client:
        response = client.post("/gpu/v1/mask", files={"file": ("dense.png", buffer.getvalue(), "image/png")},
                               data={"meta": json.dumps({"regions": regions})})
        assert response.status_code == 200, response.text
        assert len(response.json()["fragments"]) == 72
        assert response.json()["fragments"][-1]["region_id"] == "r71"
