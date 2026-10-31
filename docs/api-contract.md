# Frontend API contract (demo first)

This contract follows `frontend/src/api/client.ts` and `frontend/src/api/types.ts`. The CPU FastAPI app is the frontend's only API entry point; it calls the internal GPU service through `backend/app/services/gpu_client.py`.

## UC2: check a new post

`POST /api/uc2/check` (`multipart/form-data`)

| Part | Type | Example |
|---|---|---|
| `file` | JPEG or PNG file | `data/demo/uc2_demo.jpg` |
| `meta` | JSON string | `{"caption":"오늘도 8시 40분에 등원 완료 #하늘이","prior_clues":[{"type":"school","value":"햇살유치원"}]}` |

`prior_clues` is optional. `box` is `[x1, y1, x2, y2]` in pixels after EXIF orientation correction and server-side resize. This is the existing frontend contract used by `RegionPreview` and `maskPhoto`.

Example response (the deterministic `GPU_MOCK=true` fixture):

```json
{
  "level_now": "caution",
  "level_if_posted": "very_high",
  "added": ["name", "time"],
  "warnings": [
    {
      "type": "name",
      "severity": "high",
      "why": "사진 · 캡션에 이름 \"하늘\" · 이전 게시물의 단서와 이어져요 · 사진을 가려도 캡션에 그대로 있어요",
      "action": "이름표 가리기, 이름 해시태그 빼기",
      "region_ids": ["r1"],
      "in_caption": true
    },
    {
      "type": "time",
      "severity": "high",
      "why": "캡션에 등원 시간 \"8:40\"",
      "action": "시간 표현 빼기",
      "region_ids": [],
      "in_caption": false
    }
  ],
  "regions": [
    {"id": "r1", "type": "name", "text": "하늘", "box": [640, 581, 758, 642]}
  ],
  "caption_suggestion": "오늘도 등원 완료",
  "caption_edits": [
    {"id": "c1", "type": "time", "text": "8시 40분에"},
    {"id": "c2", "type": "name", "text": "#하늘이"}
  ],
  "image_size": [1080, 1080]
}
```

The same response is checked in at `data/demo/api/uc2-check-response.json`; its request metadata is `data/demo/api/uc2-check-meta.json`. The sample image is synthetic and safe to use for local integration checks.

## UC2: mask selected regions

`POST /api/uc2/mask` (`multipart/form-data`)

| Part | Type | Example |
|---|---|---|
| `file` | Original JPEG or PNG | `data/demo/uc2_demo.jpg` |
| `meta` | JSON string | `{"boxes":[[640,581,758,642]],"targets":["하늘"]}` |

Response follows `MaskResponse`: `image_base64` (JPEG bytes, no data-URL prefix), `rescan_passed`, `leaked`, and `meta_clean`. The frontend adds the data-URL prefix and saves the result locally. Mask selection is sent as boxes because that is what the current frontend consumes.

## UC1: past-post review

1. `POST /api/uc1/uploads` with an Instagram export ZIP; returns `UploadResponse` and thumbnail URLs.
2. `POST /api/uc1/jobs` with `{ "upload_id": "...", "photo_ids": ["..."] }`; returns `202 { "job_id": "...", "total": 1 }`.
3. Poll `GET /api/uc1/jobs/{job_id}` until `status` is `done` or `failed`.
4. `DELETE /api/uc1/uploads/{upload_id}` cancels and removes an upload.

## Local demo mode

Set `GPU_MOCK=true` (default) and run the CPU API. UC2 uses the synthetic image fingerprint in `data/demo/mock_gpu.json`; it returns deterministic fake model data without loading a VLM or OCR model. The normal `/api/uc2/check` and `/api/uc2/mask` routes are used, so React can integrate against the real contract before GPU inference is connected. `GET /api/status` reports `gpu_mock: true` to distinguish demo output from real model results.

Interactive OpenAPI docs are served at `/docs` by FastAPI.
