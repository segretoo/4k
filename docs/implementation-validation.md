# Implementation verification, 2026-10-31

| Check | Result | Scope |
|---|---|---|
| CPU API tests | 13 passed | UC1 cleanup, UC2 fragment contract, coordinate boundary/degenerate geometry, resize before inference, review state, captions |
| GPU adapter/render tests | 5 passed | Grayscale alpha + single compositing, no full-image response, OCR leaks, unreadable regions, original-pixel OCR geometry, separate caption evidence |
| Python compilation | Passed | GPU service and evaluation scripts |
| Frontend production build | Passed | TypeScript + Vite, Node 22.21.1 |
| Frontend lint | Exit 0, four warnings | Existing Fast Refresh export warnings in `components/wf.tsx` |
| Real browser flow | Passed | Edge headless; synthetic fixture; upload → check → select → mask → local JPEG download. Both HTTP calls returned 200; browser errors: 0 |
| Browser/Pillow compositing comparison | Mean channel error 0.0636 / 255 | Exported JPEG against the same patch+alpha composed in Pillow, 1080×1080 |
| Stored-detection mask regression | 34/34 at each VLM edge, 68 renders | Historical OCR-first polygons re-rendered with current mean fill / 2px / sigma 8. Every patch+alpha reconstruction matched the single render within one channel value |

The 68 renders are **not fresh OCR or VLM calls**. They verify geometry, masking, and alpha composition with the complete stored 34-image set. The real browser flow uses `GPU_MOCK=true`; it verifies the UI/API contract, not recognition quality. Historical NCP L4 recognition measurements are documented in [evaluation-2026-10-31.md](evaluation-2026-10-31.md).

New code includes a CPU-facing GPU adapter, a memory-oriented product path, separate model/bench endpoints, caption evidence, and a client compositor. The original GPU `/v1/analyze` route had previously been checked with a real model; the new `/gpu/v1/*` adapter has **not yet been deployed or tested with the actual GPU**. Direct SSH authentication is still pending. No production deployment is claimed by these local checks.

## Reproduce

```bash
cd backend
python -m pytest -q
cd ..
python -m pytest ml/gpu_server/tests -q
python -m compileall -q ml/gpu_server scripts
cd frontend
npm ci
npm run build
npm run lint
```

The opt-in `scripts/browser_smoke.py` needs Playwright and an existing Chromium/Edge executable, plus a running CPU API in mock mode. `scripts/replay_masking.py` accepts the private 34-image manifest and refuses a partial set. Both write evidence outside the repository.

When SSH access is available, start one CPU worker and one GPU worker, verify `GET /api/status` reports `gpu_mock=false` and `gpu_ok=true`, then use `scripts/evaluate_api.py --image-dir ... --expected 34 --out ...`. It refuses mock mode or fewer than 34 images and records per-image check/mask times and fragments. The two remaining bench-label misses and full-set VLM-first evaluation remain open.
