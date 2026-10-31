import io
import json
import time
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services import instagram, storage

ROOT = Path(__file__).resolve().parents[2]


def client():
    return TestClient(app)


def test_uc1_full_flow(demo_zip):
    with client() as c:
        r = c.post("/api/uc1/uploads", files={"file": ("export.zip", demo_zip.read_bytes(), "application/zip")})
        assert r.status_code == 200, r.text
        up = r.json()
        assert up["total_posts"] == 12  # 동영상만 있는 게시물 없음, 12개 모두 사진 있음
        assert up["max_select"] == 10
        assert len(up["recommended_photo_ids"]) == 10
        captions = [p["caption"] for p in up["posts"]]
        assert any("햇살유치원" in cap for cap in captions)  # 깨진 한글 복원
        assert up["posts"][0]["posted_at"].startswith("2026-10-20")  # 최신순

        folder = storage.upload_dir(up["upload_id"])
        assert not (folder / "upload.zip").exists()  # zip은 바로 삭제
        assert not any("followers" in p.name for p in folder.rglob("*"))  # 다른 항목은 풀지 않음

        thumb = up["posts"][0]["photos"][0]["thumb_url"]
        assert c.get(thumb).headers["content-type"] == "image/jpeg"

        r = c.post("/api/uc1/jobs", json={"upload_id": up["upload_id"], "photo_ids": up["recommended_photo_ids"]})
        assert r.status_code == 202, r.text
        job = r.json()
        for _ in range(50):
            st = c.get(f"/api/uc1/jobs/{job['job_id']}").json()
            if st["status"] in {"done", "failed"}:
                break
            time.sleep(0.05)
        assert st["status"] == "done", st
        res = st["result"]
        assert res["level"] == "very_high"
        assert res["level_after_cleanup"] == "caution"
        assert 1 <= len(res["cleanup"]) <= 3
        assert storage.upload_dir(up["upload_id"]) is None  # 결과 후 폴더 삭제


def test_uc1_rejects_bad_inputs():
    with client() as c:
        assert c.post("/api/uc1/uploads", files={"file": ("a.txt", b"x", "text/plain")}).status_code == 400
        assert c.post("/api/uc1/uploads", files={"file": ("a.zip", b"not zip", "application/zip")}).status_code == 400
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("../evil.txt", "x")
        r = c.post("/api/uc1/uploads", files={"file": ("a.zip", buf.getvalue(), "application/zip")})
        assert r.status_code == 400 and "경로" in r.json()["detail"]
        assert c.get("/api/uc1/jobs/nope").status_code == 404
        assert c.get("/api/uc1/uploads/../../etc/thumbs/x").status_code == 404


def test_uc2_check_and_mask():
    img = (ROOT / "data" / "demo" / "uc2_demo.jpg").read_bytes()
    with client() as c:
        meta = {"caption": "오늘도 8시 40분에 등원 완료 #하늘이", "prior_clues": [{"type": "school", "value": "햇살유치원"}]}
        r = c.post("/api/uc2/check", files={"file": ("demo_05_bag.jpg", img, "image/jpeg")}, data={"meta": json.dumps(meta)})
        assert r.status_code == 200, r.text
        chk = r.json()
        assert chk["level_now"] == "caution"
        assert chk["level_if_posted"] == "very_high"
        assert "8시 40분" not in chk["caption_suggestion"] and "#하늘이" not in chk["caption_suggestion"]
        name_region = next(x for x in chk["regions"] if x["type"] == "name")

        r = c.post(
            "/api/uc2/mask",
            files={"file": ("demo_05_bag.jpg", img, "image/jpeg")},
            data={"meta": json.dumps({"regions": [{
                "id": name_region["id"], "type": name_region["type"],
                "box": name_region["box"], "polygon": name_region.get("polygon"),
                "text": name_region["text"],
            }]})},
        )
        assert r.status_code == 200, r.text
        masked = r.json()
        assert masked["meta_clean"] is True and masked["fragments"]
        fragment = masked["fragments"][0]
        assert fragment["region_id"] == name_region["id"]
        assert len(fragment["crop_box_original_pixels"]) == 4
        assert fragment["media_type"] == "image/png"
        assert fragment["patch_base64"] and fragment["alpha_base64"]
        assert "image_base64" not in masked  # server returns selected fragments, not a full composite

        bad = c.post("/api/uc2/mask", files={"file": ("a.jpg", img, "image/jpeg")}, data={"meta": json.dumps({"boxes": [[0, 0, 99999, 10]]})})
        assert bad.status_code == 400


def test_fix_mojibake():
    assert instagram.fix_mojibake("첫 등원".encode("utf-8").decode("latin-1")) == "첫 등원"
    assert instagram.fix_mojibake("이미 정상") == "이미 정상"


def test_mask_polygon_coordinates_and_invalid_paths():
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (100, 80), (100, 140, 180)).save(buf, "PNG")
    with client() as c:
        def mask(meta):
            return c.post("/api/uc2/mask", files={"file": ("photo.png", buf.getvalue(), "image/png")},
                          data={"meta": json.dumps(meta)})

        # OCR polygons can touch the exclusive right/bottom edge.
        polygon = [[70, 60], [100, 60], [100, 80], [70, 80]]
        result = mask({"polygons": [polygon]})
        assert result.status_code == 200, result.text
        assert len(result.json()["fragments"]) == 1
        assert mask({"polygons": [[[2, 2], [8, 8], [12, 12]]]}).status_code == 400
        assert mask({"regions": [{"id": "r1", "box": [10, 10, 20, 20],
                                   "polygon": [[-1, 10], [20, 10], [20, 20]]}]}).status_code == 400
        assert mask({}).status_code == 400


def test_check_resizes_before_gpu_and_propagates_review(monkeypatch):
    from PIL import Image
    from app.api import uc2
    from app.schemas.contracts import AnalyzeResult

    buf = io.BytesIO()
    Image.new("RGB", (4400, 200)).save(buf, "PNG")

    class Gpu:
        async def analyze(self, image, meta):
            with Image.open(io.BytesIO(image)) as im:
                assert im.size == (2200, 100)
                assert not im.getexif()
            return AnalyzeResult(photo_id="test", requires_review=True, review_reasons=["empty"])

    monkeypatch.setattr(uc2, "get_gpu", lambda: Gpu())
    with client() as c:
        result = c.post("/api/uc2/check", files={"file": ("wide.png", buf.getvalue(), "image/png")})
        assert result.status_code == 200
        assert result.json()["image_size"] == [2200, 100]
        assert result.json()["requires_review"] is True
