"""UC1 지난 게시물 점검 API (프론트 ↔ 백엔드)."""
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response

from app.config import settings
from app.schemas.contracts import JobCreate, JobCreated, JobStatus, UploadResponse
from app.services import instagram, jobs, recommend, storage

router = APIRouter(prefix="/api/uc1", tags=["UC1 게시물 건강검진"])
CHUNK = 1024 * 1024


@router.post("/uploads", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)) -> UploadResponse:
    if not (file.filename or "").lower().endswith(".zip"):
        raise HTTPException(400, "zip 파일만 올릴 수 있어요.")
    upload_id, folder = storage.new_upload()
    zip_path = folder / "upload.zip"
    size, limit = 0, settings.max_zip_mb * CHUNK
    try:
        with zip_path.open("wb") as out:  # 메모리가 아니라 디스크로 바로 저장 (CPU 서버 스왑 없음)
            while chunk := await file.read(CHUNK):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(413, f"파일이 너무 커요. {settings.max_zip_mb}MB 이하로 올려 주세요.")
                out.write(chunk)
        posts = instagram.extract(zip_path, folder)
    except instagram.ExportError as e:
        storage.remove(upload_id)
        raise HTTPException(400, str(e)) from e
    except HTTPException:
        storage.remove(upload_id)
        raise
    scores = await recommend.screen(posts)
    picked = recommend.pick(posts, scores)
    return UploadResponse(
        upload_id=upload_id,
        total_posts=len(posts),
        total_photos=sum(len(p["photos"]) for p in posts),
        max_select=settings.max_photos,
        recommended_photo_ids=picked,
        posts=recommend.summaries(upload_id, posts, scores, picked),
    )


@router.get("/uploads/{upload_id}/thumbs/{photo_id}")
def thumb(upload_id: str, photo_id: str) -> FileResponse:
    folder = storage.upload_dir(upload_id)
    if not folder or not storage.PHOTO_ID_RE.match(photo_id):
        raise HTTPException(404, "사진을 찾을 수 없어요.")
    path = folder / "thumbs" / f"{photo_id}.jpg"
    if not path.exists():
        raise HTTPException(404, "사진을 찾을 수 없어요.")
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=600"})


@router.delete("/uploads/{upload_id}", status_code=204)
def cancel(upload_id: str) -> Response:
    storage.remove(upload_id)
    return Response(status_code=204)


@router.post("/jobs", response_model=JobCreated, status_code=202)
def start_job(body: JobCreate, background: BackgroundTasks) -> JobCreated:
    folder = storage.upload_dir(body.upload_id)
    if not folder:
        raise HTTPException(404, "업로드가 만료됐어요. 파일을 다시 올려 주세요.")
    if len(body.photo_ids) > settings.max_photos:
        raise HTTPException(400, f"사진은 {settings.max_photos}장까지 고를 수 있어요.")
    posts = instagram.load_posts(folder)
    known = {ph["photo_id"] for p in posts for ph in p["photos"]}
    selected = list(dict.fromkeys(body.photo_ids))
    if any(pid not in known for pid in selected):
        raise HTTPException(400, "고른 사진 정보가 올바르지 않아요.")
    for pid in known - set(selected):  # 고르지 않은 사진은 바로 삭제
        (folder / "photos" / f"{pid}.jpg").unlink(missing_ok=True)
    job_id = jobs.create(body.upload_id, len(selected))
    background.add_task(jobs.run, job_id, posts, selected)
    return JobCreated(job_id=job_id, total=len(selected))


@router.get("/jobs/{job_id}", response_model=JobStatus)
def job_status(job_id: str) -> JobStatus:
    st = jobs.status(job_id)
    if not st:
        raise HTTPException(404, "작업을 찾을 수 없어요.")
    return st
