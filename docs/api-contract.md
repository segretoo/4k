# Frontend API contract (demo first)

This contract follows `frontend/src/api/client.ts` and `frontend/src/api/types.ts`. The CPU FastAPI app is the frontend's only API entry point; it calls the internal GPU service through `backend/app/services/gpu_client.py`.

## UC2: check a new post

`POST /api/uc2/check` (`multipart/form-data`)

| Part | Type | Example |
|---|---|---|
| `file` | JPEG or PNG file | `data/demo/uc2_demo.jpg` |
| `meta` | JSON string | `{"caption":"오늘도 8시 40분에 등원 완료 #하늘이","prior_clues":[{"type":"school","value":"햇살유치원"}]}` |

`prior_clues` is optional. `box`, `polygon`, and SVG `path` use pixels after EXIF orientation correction and server-side resize (default long edge: 2200px). The `polygon` is the exact text outline when OCR provides one; `box` remains a fallback.

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
    {"id": "r1", "type": "name", "text": "하늘", "box": [640, 581, 758, 642], "polygon": [[640,581],[758,581],[758,642],[640,642]], "path": "M 640 581 L 758 581 L 758 642 L 640 642 Z"}
  ],
  "caption_suggestion": "오늘도 등원 완료",
  "caption_edits": [
    {"id": "c1", "type": "time", "text": "8시 40분에"},
    {"id": "c2", "type": "name", "text": "#하늘이"}
  ],
  "image_size": [1080, 1080],
  "requires_review": false,
  "review_reasons": []
}
```

The same response is checked in at `data/demo/api/uc2-check-response.json`; its request metadata is `data/demo/api/uc2-check-meta.json`. The sample image is synthetic and safe to use for local integration checks.

## UC2: mask selected regions

`POST /api/uc2/mask` (`multipart/form-data`)

| Part | Type | Example |
|---|---|---|
| `file` | Original JPEG or PNG | `data/demo/uc2_demo.jpg` |
| `meta` | JSON string | `{"regions":[{"id":"r1","type":"name","text":"하늘","box":[640,581,758,642],"polygon":[[640,581],[758,581],[758,642],[640,642]]}]}` |

`box` and `polygon` use the same oriented, resized coordinate space returned by `/check`. Response contains one masked crop and one alpha mask per selected region; it never contains a full composited photo:

```json
{
  "fragments": [{
    "region_id": "r1",
    "crop_box_original_pixels": [612, 553, 786, 671],
    "patch_base64": "...PNG...",
    "alpha_base64": "...PNG...",
    "media_type": "image/png"
  }],
  "rescan_passed": true,
  "leaked": [],
  "retry_regions": [],
  "meta_clean": true,
  "requires_review": false
}
```

The browser scales each crop box from `CheckResponse.image_size` to the locally held original image, composites patch pixels through the alpha mask, and exports a new JPEG locally. Canvas export strips the original EXIF/GPS metadata. If OCR still reads a selected phrase, `leaked` contains the exact recognized OCR line and `retry_regions` contains its text geometry (`id`, `type`, `text`, `box`, `polygon`, `path`) when available. The user can add those suggested areas and rescan, or explicitly confirm proceeding with the current masked image. The same mask API is used for an individually uploaded photo and for a photo reselected after ZIP review.

## Operational audit log

The CPU API records count-only events for anonymous session connect/disconnect, completed ZIP uploads, analyses, photo checks, mask rescans, and download starts. It never records image bytes, OCR/caption text, filenames, IP addresses, session IDs, cookies, or request bodies. JSONL files are stored under `backend/logs` by default with owner-only file permissions and 5 MiB rotation (three backups). The read-only viewer is at `/admin/logs`; configure a random `AUDIT_VIEW_TOKEN` of at least 32 characters in the CPU server `.env` and enter it in the viewer. The token is held only in page memory and sent in a request header, never in a URL or audit record.

## UC1: past-post review

1. `POST /api/uc1/uploads` with an Instagram export ZIP. The CPU server reads Instagram `posts_*.json` when present, or modern `your_instagram_activity/media/posts_*.html` cards and their linked image members when JSON is absent. It returns `UploadResponse`, thumbnails, extracted hashtags, and CPU-only caption candidates. No GPU inference is used for this first review list.
2. The user may edit candidate toggles and photo selections. Candidate IDs are deterministic within a post and tied to a `type`, `value`, and source. Manually added caption clues must be exact text contained in that post's caption.
3. `POST /api/uc1/jobs` with selected photos and candidate decisions; returns `202 { "job_id": "...", "total": 1 }`.
4. Poll `GET /api/uc1/jobs/{job_id}` until `status` is `done` or `failed`. The existing aggregate risk fields remain in `result`; `result.post_results` adds the per-post JSON array with per-photo detections and risk levels.
5. `DELETE /api/uc1/uploads/{upload_id}` cancels and removes an upload.

Example job input:

```json
{
  "upload_id": "upload-token",
  "photo_ids": ["p001_1", "p001_2", "p002_1"],
  "candidate_selections": {
    "p001": ["p001:4cbb77b99014"],
    "p002": []
  },
  "manual_candidates": {
    "p002": [{"type": "school", "value": "한빛초등학교"}]
  }
}
```

`candidate_selections` can be omitted to keep all suggested clues; an explicitly empty list for a post excludes its caption candidates. Image findings are not discarded by caption toggles. `manual_candidates` adds a user-confirmed caption clue and the API rejects values absent from the original post text.

The completed response keeps the previous `EngineResult` fields and adds:

```json
{
  "post_results": [
    {
      "post_id": "p001",
      "posted_at": "2026-10-31T09:00:00+09:00",
      "caption": "#한빛초등학교 등교",
      "hashtags": ["한빛초등학교"],
      "selected_candidate_ids": ["p001:4cbb77b99014"],
      "manual_candidates": [],
      "risk_level": "high",
      "photos": [
        {
          "photo_id": "p001_1",
          "source": "IMG_001.jpg",
          "size": [2200, 1467],
          "entities": [],
          "risk_level": "caution",
          "analysis_failed": false
        }
      ]
    }
  ]
}
```

## Local demo mode

Set `GPU_MOCK=true` (default) and run the CPU API. UC2 uses the synthetic image fingerprint in `data/demo/mock_gpu.json`; it returns deterministic fake model data without loading a VLM or OCR model. The same `/api/uc2/check` and `/api/uc2/mask` routes exercise the fragment response contract. `GET /api/status` reports `gpu_mock: true` to distinguish demo output from real model results.

Interactive OpenAPI docs are served at `/docs` by FastAPI.

## Evaluation diagnostics

`/api/uc2/check` additionally returns `ocr_texts` (OCR text, confidence, pixel geometry) and `pipeline_metrics` (model, order, input edges, token count, step timings, peak GPU allocated/reserved bytes, JSON validity). These are measured by the real GPU service, not invented by the CPU API. Mock mode returns an empty diagnostics object. The browser does not need these fields to render the current UI.
