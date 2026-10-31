"""UC1 분석 작업: 고른 사진을 한 장씩 GPU로 보내고, 끝나면 업로드 폴더를 지운다."""
import asyncio
import time
import uuid
from dataclasses import dataclass, field

from app.schemas.contracts import EngineResult, Entity, JobStatus
from app.services import engine, storage
from app.services.gpu_client import GpuError, get_gpu
from app.services.gpu_queue import QueueBusy


@dataclass
class Job:
    upload_id: str
    total: int
    owner_id: str = ""
    status: str = "queued"
    done: int = 0
    result: EngineResult | None = None
    error: str | None = None
    created: float = field(default_factory=time.time)


JOBS: dict[str, Job] = {}


def create(upload_id: str, total: int, owner_id: str = "") -> str:
    job_id = uuid.uuid4().hex
    JOBS[job_id] = Job(upload_id=upload_id, total=total, owner_id=owner_id)
    return job_id


def status(job_id: str, owner_id: str | None = None) -> JobStatus | None:
    job = JOBS.get(job_id)
    if not job or (owner_id is not None and job.owner_id != owner_id):
        return None
    return JobStatus(status=job.status, done=job.done, total=job.total, result=job.result, error=job.error)


def sweep(ttl_s: int = 3600) -> None:
    """끝난 작업 결과도 메모리에 오래 두지 않는다."""
    limit = time.time() - ttl_s
    for jid in [k for k, j in JOBS.items() if j.created < limit]:
        JOBS.pop(jid, None)


async def run(job_id: str, posts: list[dict], selected: list[str]) -> None:
    job = JOBS[job_id]
    job.status = "running"
    gpu = get_gpu()
    folder = storage.upload_dir(job.upload_id)
    post_entities: dict[str, list[Entity]] = {}
    post_meta: dict[str, dict] = {}
    failed: list[str] = []
    try:
        by_photo = {ph["photo_id"]: (p, ph) for p in posts for ph in p["photos"]}
        for photo_id in selected:
            post, photo = by_photo[photo_id]
            pid = post["post_id"]
            post_meta.setdefault(pid, {"posted_at": post.get("posted_at"), "caption": post.get("caption", ""), "photo_ids": []})
            post_meta[pid]["photo_ids"].append(photo_id)
            post_entities.setdefault(pid, [])
            try:
                image = (folder / "photos" / f"{photo_id}.jpg").read_bytes()
                while True:
                    try:
                        res = await gpu.analyze(
                            image,
                            {
                                "photo_id": photo_id,
                                "post_id": pid,
                                "caption": post.get("caption", ""),
                                "posted_at": post.get("posted_at"),
                                "source": photo.get("source", ""),
                                "owner_id": job.owner_id,
                            },
                        )
                        break
                    except QueueBusy:
                        await asyncio.sleep(0.25)  # 대기 한도는 큐에서 보장하고, UC1 배치는 순서를 유지한다.
                post_entities[pid].extend(res.entities)
            except (GpuError, OSError, ValueError):
                failed.append(photo_id)  # 한 장 실패해도 나머지는 계속
            job.done += 1
        post_entities = {pid: engine.dedupe(ents) for pid, ents in post_entities.items()}
        job.result = engine.build_result(post_entities, post_meta, failed)
        job.status = "done"
    except Exception:  # noqa: BLE001 - 사용자에게는 짧은 메시지만
        job.status = "failed"
        job.error = "분석 중 문제가 생겼어요. 잠시 후 다시 시도해 주세요."
    finally:
        storage.remove(job.upload_id)  # 정상·실패 모두 업로드 폴더 삭제
