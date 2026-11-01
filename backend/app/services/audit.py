"""Count-only operational audit log. Never accept or persist free-text fields."""
from collections import deque
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading

from app.config import settings

LOG_PATH = settings.audit_log_path
MAX_BYTES = 5 * 1024 * 1024
BACKUPS = 3
_lock = threading.Lock()

_FIELDS: dict[str, frozenset[str]] = {
    "connected": frozenset(),
    "disconnected": frozenset(),
    "zip_uploaded": frozenset({"posts", "photos"}),
    "analysis_completed": frozenset({"photos", "detections", "failed"}),
    "analysis_failed": frozenset({"photos"}),
    "photo_checked": frozenset({"photos", "detections", "warnings"}),
    "mask_checked": frozenset({"regions", "residuals", "fragments"}),
    "download_started": frozenset({"photos", "regions"}),
}


def _path() -> Path:
    path = Path(LOG_PATH)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / path
    return path


def record(event: str, **counts: int) -> None:
    """Append one allowlisted event. Unknown fields and any write error are ignored."""
    allowed = _FIELDS.get(event)
    if allowed is None:
        return
    row: dict[str, str | int] = {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "event": event,
    }
    for key in allowed:
        value = counts.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 1_000_000:
            row[key] = value
    try:
        path = _path()
        with _lock:
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            try:
                os.chmod(path.parent, 0o700)
            except OSError:
                pass
            if path.exists() and path.stat().st_size >= MAX_BYTES:
                for index in range(BACKUPS, 0, -1):
                    source = path.with_name(f"{path.name}.{index}")
                    target = path.with_name(f"{path.name}.{index + 1}")
                    if source.exists():
                        if index == BACKUPS:
                            source.unlink()
                        else:
                            source.replace(target)
                if path.exists():
                    path.replace(path.with_name(f"{path.name}.1"))
            descriptor = os.open(path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, "a", encoding="utf-8") as output:
                output.write(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n")
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass
    except OSError:
        # Auditing must not break image processing; callers never log the exception.
        return


def recent(limit: int = 100) -> list[dict[str, str | int]]:
    """Read recent allowlisted rows without exposing file paths to the API caller."""
    path = _path()
    rows: deque[dict[str, str | int]] = deque(maxlen=limit)
    with _lock:
        for index in range(BACKUPS, 0, -1):
            rotated = path.with_name(f"{path.name}.{index}")
            if rotated.is_file():
                _read_rows(rotated, rows)
        if path.is_file():
            _read_rows(path, rows)
    return list(rows)[-limit:]


def _read_rows(path: Path, rows: deque) -> None:
    try:
        with path.open("r", encoding="utf-8") as source:
            for line in source:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                event = row.get("event") if isinstance(row, dict) else None
                if (isinstance(row, dict) and isinstance(event, str) and event in _FIELDS
                        and isinstance(row.get("at"), str)
                        and all(key in {"at", "event"} | _FIELDS[event]
                                for key in row)):
                    rows.append(row)
    except OSError:
        return
