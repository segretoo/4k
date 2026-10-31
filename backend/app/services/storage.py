"""업로드 임시 폴더 관리. 작업 번호는 사용자와 연결되지 않는 무작위 값이고, 폴더는 3중으로 지운다."""
import re
import shutil
import time
import uuid
from pathlib import Path

from app.config import settings

ID_RE = re.compile(r"^[a-f0-9]{32}$")
PHOTO_ID_RE = re.compile(r"^p\d{3,5}_\d{1,3}$")


def root() -> Path:
    settings.tmp_dir.mkdir(parents=True, exist_ok=True)
    return settings.tmp_dir


def new_upload(owner_id: str = "") -> tuple[str, Path]:
    upload_id = uuid.uuid4().hex
    path = root() / upload_id
    path.mkdir(mode=0o700)
    (path / "photos").mkdir(mode=0o700)
    (path / "thumbs").mkdir(mode=0o700)
    (path / ".owner").write_text(owner_id, encoding="ascii")
    return upload_id, path


def upload_dir(upload_id: str) -> Path | None:
    """형식이 맞고 실제로 있는 폴더만 돌려준다 (경로 조작 방지)."""
    if not ID_RE.match(upload_id):
        return None
    path = root() / upload_id
    return path if path.is_dir() else None


def owned_upload(upload_id: str, owner_id: str) -> Path | None:
    folder = upload_dir(upload_id)
    if folder is None or not owner_id:
        return None
    try:
        return folder if (folder / ".owner").read_text(encoding="ascii") == owner_id else None
    except OSError:
        return None


def remove(upload_id: str) -> None:
    if ID_RE.match(upload_id):
        shutil.rmtree(root() / upload_id, ignore_errors=True)


def sweep_expired() -> int:
    """중간 이탈: TTL이 지난 폴더 삭제."""
    limit = time.time() - settings.upload_ttl_min * 60
    removed = 0
    for p in root().iterdir():
        if p.is_dir() and ID_RE.match(p.name) and p.stat().st_mtime < limit:
            shutil.rmtree(p, ignore_errors=True)
            removed += 1
    return removed


def reset_all() -> None:
    """서버 재시작: 관리하는 무작위 업로드 폴더만 비운다."""
    for folder in root().iterdir():
        if folder.is_dir() and not folder.is_symlink() and ID_RE.fullmatch(folder.name):
            shutil.rmtree(folder, ignore_errors=True)
