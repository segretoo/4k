# Qwen3.5-4B BF16 + PP-OCRv5 GPU service

제품 계약은 [api-contract.md](../../docs/api-contract.md), 서버별 역할은 [architecture.md](../../docs/architecture.md), 이전 34장 실측은 [evaluation-2026-10-31.md](../../docs/evaluation-2026-10-31.md)를 참고하세요.

기본값은 PP-OCRv5 2200px → Qwen3.5-4B BF16 2200px 위험 단서 검토입니다. OCR ID를 원본 polygon으로 연결하고, OCR에서 놓친 글자는 좁은 VLM 상자로 검토합니다. 빈 결과·JSON 오류·VLM 위치만 있는 결과는 사용자 확인 대상으로 표시합니다. 프롬프트는 [prompts.py](prompts.py)에 있습니다.

## 기존 모델 환경에 설치

이미 검증한 CUDA/Torch 가상환경을 사용하고 Torch를 임의로 덮어쓰지 마세요. 이 폴더에서 API 의존성을 설치합니다.

```bash
python -m pip install -r requirements.txt
cp .env.example .env
```

`.env`에서 `API_KEY`를 비밀 임의값으로 바꾸고 `OCR_WORKER_CMD`를 실제 PaddleOCR 환경 경로로 지정하세요. 키가 비어 있거나 예시값이면 기동을 중단합니다. 모델은 기본적으로 로컬 캐시에서 로드합니다. Paddle 환경이 분리되어 있다면 그 환경에 `requirements-ocr.txt`를 설치합니다. `OCR_WORKER_CMD`를 비우면 현재 Python 환경의 PaddleOCR를 직접 사용합니다.

```dotenv
MODEL_ID=Qwen/Qwen3.5-4B
LOAD_4BIT=false
PIPELINE_ORDER=ocr_first
MODEL_EDGE=2200
OCR_EDGE=2200
OCR_WORKER_CMD=/실제/ocr-venv/bin/python /실제/4k/ml/gpu_server/ocr_worker.py
```

```bash
bash run_api.sh
```

`.env`는 앱이 읽습니다. 포트 변경은 실행 환경의 `API_PORT`로 지정합니다. Uvicorn worker는 한 개입니다. 이전 한 BF16 프로세스의 peak reserved가 13.12 GiB여서 L4 24 GiB에 두 프로세스가 들어간다고 가정할 수 없습니다. `MAX_WAITING=4`는 대기 상한이며 처리시간을 단축하는 설정은 아닙니다.

## CPU 서버 연결

CPU 서버 `.env`에 `GPU_MOCK=false`, `GPU_URL=http://10.1.2.30:8080`, 같은 비밀값의 `GPU_API_KEY`를 설정하세요. 8080 포트는 CPU 서버에서만 접근하도록 제한합니다.

| 제품 경로 | 역할 |
|---|---|
| `GET /gpu/v1/health` | 준비 여부. 모델 준비 전 503 |
| `POST /gpu/v1/screen-captions` | 빠른 캡션 후보 우선순위 |
| `POST /gpu/v1/analyze` | OCR·위험 단서·polygon·SVG path·검토 상태 |
| `POST /gpu/v1/mask` | 선택된 RGB patch와 grayscale alpha PNG, OCR 재검사 |

제품 경로는 원본·OCR JSON을 저장하지 않습니다. 업로드를 읽은 뒤 프레임워크의 임시 업로드 파일을 닫고 처리합니다. 처리 메모리는 요청 종료 후 회수 대상이 됩니다. 실제 평가 사진은 저장소에 넣지 마세요.

내부는 주변 평균 RGB로 완전히 덮고, 2px 확장·sigma 8로 경계만 부드럽게 연결합니다. patch는 아직 alpha를 적용하지 않은 RGB 레이어이고 alpha는 L 모드 PNG입니다. 브라우저가 grayscale을 투명도로 변환한 뒤 한 번만 합성합니다. 읽히지 않은 표지의 위치는 자동 OCR 검사 통과로 표시하지 않고 사용자 확인을 받습니다.

`/v1/analyze`와 `/v1/artifacts/*`는 벤치마크 경로이며 JSON·조각을 `ARTIFACT_DIR`에 TTL 동안 보관합니다. 제품 프록시에서는 이 경로를 허용하지 마세요. GPU의 전체 임시 합성은 OCR 재검사 동안 메모리에서만 만들고, 최종 저장 이미지는 클라이언트에서 만듭니다.

## 검증

```bash
python -m pytest ml/gpu_server/tests -q
python -m compileall -q ml/gpu_server
```

위 검사는 모델을 다운로드하지 않는 어댑터·합성 단위 테스트입니다. 이전 OCR-first 34장 결과는 2200px에서 30/32 양성 장면, JSON 34/34, 평균 26.65초입니다. VLM-first는 6장 표본만 측정했습니다. 새 HTTP 어댑터의 실제 GPU 검증과 VLM-first 전체 34장 재측정은 별도 작업입니다.
