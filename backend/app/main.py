"""꼭꼭 웹 앱 (CPU 서버). API와 React 빌드 결과를 같은 주소로 제공한다."""
import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import uc1, uc2
from app.config import settings
from app.services import jobs, storage
from app.services.gpu_client import get_gpu

# 캡션·판독 글자·파일명은 로그에 남기지 않는다 (접근 로그도 경로만)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


async def _sweeper() -> None:
    while True:
        await asyncio.sleep(300)
        storage.sweep_expired()
        jobs.sweep()


@asynccontextmanager
async def lifespan(app: FastAPI):
    storage.reset_all()  # 서버 재시작 시 임시 폴더 비우기
    task = asyncio.create_task(_sweeper())
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


app = FastAPI(title="꼭꼭 API", version="0.1.0", lifespan=lifespan)
app.include_router(uc1.router)
app.include_router(uc2.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/status")
async def status() -> dict:
    return {
        "gpu_mock": settings.gpu_mock,
        "gpu_ok": await get_gpu().health(),
        "max_photos": settings.max_photos,
        "max_zip_mb": settings.max_zip_mb,
    }


# ---- React 빌드 제공 (frontend/dist가 있을 때만) ----
dist = settings.frontend_dist
if not dist.is_absolute():
    from pathlib import Path

    dist = (Path(__file__).resolve().parents[1] / dist).resolve()

if (dist / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.exception_handler(404)
    async def spa_fallback(request: Request, exc):
        """화면 주소(/upload 등)는 index.html로, API는 그대로 404."""
        if request.url.path.startswith("/api") or request.method != "GET":
            return JSONResponse({"detail": getattr(exc, "detail", "Not Found")}, status_code=404)
        file = dist / request.url.path.lstrip("/")
        if file.is_file() and dist in file.resolve().parents:
            return FileResponse(file)
        return FileResponse(dist / "index.html")
