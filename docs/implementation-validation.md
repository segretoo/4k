# Implementation verification, 2026-11-01

| Check | Result | Scope |
|---|---|---|
| CPU API tests | 18 passed in 1.86s | Re-run in the CPU server's Linux environment; UC1 cleanup, UC2 fragments, sessions, fair queue, and API behavior |
| GPU service compilation | Passed | `python -m compileall -q ml/gpu_server` |
| Frontend production build | Passed | Local Node 20.14.0; Vite warns that Node 20.19+ or 22.12+ is preferred. CI uses Node 22. |
| Frontend lint | Exit 0, four warnings | Existing Fast Refresh export warnings in `components/wf.tsx` |
| Real browser flow | Passed | Edge against CPU API and the live NCP GPU; session → check → select → mask → local JPEG download. HTTP calls returned 200; OCR rescan passed; zero leaked characters in this smoke sample |
| Browser/Pillow compositing comparison | Mean channel error 0.0611 / 255 | Exported JPEG against the same patch+alpha composed in Pillow, 1080×1080 |
| Stored-detection mask regression | 34/34 at each VLM edge, 68 renders | Historical OCR-first polygons re-rendered with mean fill / 2px / sigma 8; patch+alpha reconstruction matched the single render within one channel value |
| Real NCP pipeline matrix | 34/34 per condition, 4 conditions | 1280/2200px VLM edge × OCR-first/VLM-first; full comparison below |

The 68 renders are **not fresh OCR or VLM calls**. They verify geometry, masking, and alpha composition with the complete stored 34-image set. The browser smoke exercised the real GPU through the CPU API; it used one synthetic image and verifies the product integration, not recognition quality. The separate real API matrix used 34 distinct photos per condition; two interrupted rows were retried and all four conditions completed.

The CPU frontend/API and GPU adapter are deployed on private NCP hosts. The CPU API reports `gpu_mock=false` and `gpu_ok=true`; the GPU health route reports ready. External internet access is intentionally deferred. The full-set OCR-first and VLM-first results are summarized here.

| Condition | Positive scenes | Valid VLM JSON | Mean check | Mean check + mask | Mean VLM input tokens | Peak reserved VRAM |
|---|---:|---:|---:|---:|---:|---:|
| OCR-first, 2200px | 30/32 | 33/34 | 26.06s | 33.16s | 4,613 | 11.94 GiB |
| OCR-first, 1280px | 28/32 | 32/34 | 26.89s | 33.85s | 2,619 | 10.93 GiB |
| VLM-first, 1280px | 24/32 | 28/34 | 40.72s | 47.62s | 4,255 | 10.34 GiB |
| VLM-first, 2200px | 19/32 | 25/34 | 41.19s | 48.65s | 8,272 | 12.17 GiB |

OCR used 2200px in all four conditions and returned identical text for all 34 images; character error rate cannot be calculated without exact transcriptions. The default is OCR-first at 2200px. OCR rescan still found residual text in 7–8 images per condition, so the product blocks downloads for those cases. The 2200px profile missed two small bench labels (`04.jpg`, `06.jpg`).

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

The opt-in `scripts/browser_smoke.py` needs Playwright and an existing Chromium/Edge executable, plus a running CPU API. `scripts/replay_masking.py` accepts the private 34-image manifest and refuses a partial set. Both write evidence outside the repository.

To reproduce the full matrix, start one CPU worker and one GPU worker, verify `GET /api/status` reports `gpu_mock=false` and `gpu_ok=true`, then run `scripts/evaluate_matrix.py` with the private 34-image manifest. It refuses mock mode or a partial set and records per-image check/mask times, OCR, fragments, tokens, and VRAM. Do not commit source photos or generated evidence.
