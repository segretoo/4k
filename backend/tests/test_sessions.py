from fastapi.testclient import TestClient

from app.main import app
from app.services import storage
from app.services.sessions import COOKIE, sign, verify


def test_cookie_signature_and_flags():
    signed = sign("a" * 32)
    assert verify(signed) == "a" * 32
    assert verify(signed.replace("a", "b", 1)) is None
    assert verify("a" * 32 + ".손상된서명") is None
    with TestClient(app) as client:
        response = client.get("/api/session")
        cookie = response.headers["set-cookie"]
        assert "HttpOnly" in cookie and "SameSite=strict" in cookie
        assert response.headers["cache-control"] == "no-store"


def test_uploads_and_jobs_are_private_between_browsers(demo_zip):
    with TestClient(app) as alice:
        bob = TestClient(app)  # share the one running server lifespan, not Alice's cookies
        response = alice.post("/api/uc1/uploads", files={"file": ("export.zip", demo_zip.read_bytes(), "application/zip")})
        assert response.status_code == 200
        upload = response.json()
        upload_id = upload["upload_id"]
        thumbnail = upload["posts"][0]["photos"][0]["thumb_url"]
        assert bob.get(thumbnail).status_code == 404
        assert bob.delete(f"/api/uc1/uploads/{upload_id}").status_code == 404
        assert storage.upload_dir(upload_id) is not None
        request = {"upload_id": upload_id, "photo_ids": upload["recommended_photo_ids"][:1]}
        assert bob.post("/api/uc1/jobs", json=request).status_code == 404
        job = alice.post("/api/uc1/jobs", json=request)
        assert job.status_code == 202
        job_id = job.json()["job_id"]
        assert alice.get(f"/api/uc1/jobs/{job_id}").status_code == 200
        assert bob.get(f"/api/uc1/jobs/{job_id}").status_code == 404
        # Even a copied upload/job ID does not grant access after a forged cookie.
        bob.cookies.set(COOKIE, alice.cookies.get(COOKIE)[:-1] + "x")
        assert bob.get(f"/api/uc1/jobs/{job_id}").status_code == 404
        bob.close()


def test_restart_cleanup_preserves_unmanaged_files():
    managed, folder = storage.new_upload("owner")
    keep = storage.root() / "unmanaged.txt"
    keep.write_text("preserve", encoding="utf-8")
    storage.reset_all()
    assert storage.upload_dir(managed) is None
    assert keep.read_text(encoding="utf-8") == "preserve"
    keep.unlink()
