import json
import os
import stat

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api import audit as audit_api
from app.main import session_end
from app.services import audit


def test_audit_is_count_only_and_private(tmp_path, monkeypatch):
    path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(audit, "LOG_PATH", path)

    audit.record("zip_uploaded", posts=3, photos=5, caption="private caption", filename="private.zip")
    audit.record("photo_checked", photos=1, detections=2, warnings=1, text="private OCR")
    audit.record("unknown_event", photos=99)

    rows = audit.recent(10)
    assert len(rows) == 2
    assert rows[0]["event"] == "zip_uploaded"
    assert rows[0]["posts"] == 3 and rows[0]["photos"] == 5
    assert "caption" not in rows[0] and "filename" not in rows[0]
    serialized = path.read_text(encoding="utf-8")
    assert "private caption" not in serialized
    assert "private.zip" not in serialized
    assert "private OCR" not in serialized
    if os.name != "nt":
        assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_audit_view_requires_token_and_session_can_end(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "LOG_PATH", tmp_path / "audit.jsonl")
    monkeypatch.setattr(audit_api, "AUDIT_VIEW_TOKEN", "test-only-token-value-long-enough")

    with pytest.raises(HTTPException) as error:
        audit_api.list_audit_events(None, 100)
    assert error.value.status_code == 401

    request = Request({
        "type": "http", "method": "POST", "path": "/api/session/end",
        "headers": [], "state": {"session_valid": True},
    })
    ended = session_end(request)
    assert ended.status_code == 200
    audit.record("connected")
    rows = audit_api.list_audit_events("test-only-token-value-long-enough", 100)
    events = [row["event"] for row in rows["events"]]
    assert "connected" in events and "disconnected" in events
    assert "test-only-token-value-long-enough" not in json.dumps(rows)
