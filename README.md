<div align="center">

# 🫣 꼭꼭

### 꼭꼭 숨어라, 이름표 보일라 · 부모 본인의 게시물을 이어 보고 아이를 찾을 수 있는 단서를 경고하고 가려 주는 서비스

![Python](https://img.shields.io/badge/Python-3.11+-3776AB) ![Node](https://img.shields.io/badge/Node-20.19+%20%7C%2022.12+-339933) ![External AI API](https://img.shields.io/badge/외부%20AI%20API-사용%20안%20함-C7321F) ![GPU](https://img.shields.io/badge/GPU-NCP%20L4%2024GB%20내부망-2A1410)

코디세이 AI 해커톤 2026 · 주제 02 정보보호 · 팀 4K

</div>

> 아이 사진 한 장은 안전해 보여도, 여러 게시물을 이어 보면 이름·유치원·동네·등원 시간이 맞춰집니다. 꼭꼭은 **부모가 먼저** 그 연결을 보고, **필요한 곳만** 끊도록 돕습니다.

## 프로젝트 개요

부모가 SNS에 올린 아이 사진은 한 장씩 보면 평범합니다. 하지만 첫 등원 사진의 유치원 간판, 생일 케이크의 이름, 등원길 표지판과 "8시 40분"이라는 캡션을 이어 보면, 낯선 사람이 **언제 어디서 아이 이름을 부르며 다가갈 수 있는지**가 드러납니다.

꼭꼭은 부모 본인의 게시물만 분석해 사진 속 글자와 캡션에서 단서를 찾고, 게시물 사이의 단서를 이어서 **위험 단계**(안전 · 주의 · 위험 · 매우 위험)를 알려 줍니다. 모두 지우라고 하지 않고, 위험한 조합을 끊는 **최소 정리 개수**를 계산합니다. 새로 올릴 사진은 이름표처럼 고른 글자 영역만 주변 배경색으로 가리고, 다시 읽어서 정말 안 보이는지 확인합니다.

아이 정보를 다루는 서비스이므로 **외부 AI API를 쓰지 않습니다**. 모델은 대회 제공 GPU 서버 내부망에서만 실행되고, 원본 사진은 분석 후 삭제합니다. 원칙은 "AI가 찾고 → 부모가 고르고 → 코드가 가린다"입니다. 게시와 삭제는 부모가 직접 합니다.

## 주요 기능

| 기능 | 설명 |
|---|---|
| 게시물 건강검진 | 인스타그램 "내 정보 내보내기" zip을 올리면 게시물만 읽어 단서가 보이는 사진을 추천(최대 10장)하고, 게시물을 이어 본 위험 단계 카드와 최소 정리 목록을 보여 줍니다 |
| 올리기 전 체크 | 새 사진과 캡션이 지금 위험 단계를 얼마나 올리는지(예: 위험 → 매우 위험) 보여 주고, 단서마다 이유와 권장 조치를 알려 줍니다 |
| 단서 판단 | PP-OCRv5가 사진 속 글자를 먼저 읽고, Qwen3.5-4B가 OCR 후보·사진·캡션을 함께 보고 이름·나이·소속·장소·시간·연락처 단서를 고릅니다 |
| 위험 단계 계산 | 단계는 AI가 아니라 규칙으로 정합니다. 이름 + 장소 = 위험, 여기에 시간까지 = 매우 위험 |
| 골라서 가리기 + 재검사 | 고른 글자 영역만 주변 평균색으로 채우고(2px 확장, Gaussian sigma 8) OCR로 다시 읽습니다. 다시 읽히면 저장을 막습니다 |
| 캡션 정리 | 캡션 속 이름 해시태그·등원 시간 같은 표현을 골라 뺀 수정 캡션을 만들어 줍니다 |
| 개인정보 보호 | 보호자 동의 후 시작, 내보내기 파일은 게시물 폴더만 읽음, EXIF(GPS) 제거, 분석 후·이탈 시·재시작 시 임시 파일 삭제 |

## 개발 환경

- 언어/런타임: Python 3.11+ (CPU·GPU 서버), TypeScript + React 19 (Vite 8, Node 20.19+ 또는 22.12+)
- 주요 도구: FastAPI, React Router, Axios, Pillow, PyTorch, Transformers, PaddleOCR 3, OpenCV 5
- AI 모델: Qwen3.5-4B (BF16), PP-OCRv5 Korean — 모두 GPU 서버 내부망에서 실행, 외부 AI API 없음
- 실행/배포 방식: CPU 서버가 화면(React 빌드)과 API를 같은 주소로 제공하고, GPU 서버(NCP L4 24GB)는 CPU 서버만 호출
- 협업: GitHub Issue → 브랜치 → PR → 리뷰 → Squash 병합 ([docs/CONTRIBUTING.md](docs/CONTRIBUTING.md))
- 외부 자원 전체 목록: [docs/resources.md](docs/resources.md)

## 배포 & 실행 방법

- GitHub 저장소: 이 저장소
- GPU 서버 없이도 전체 화면 흐름을 돌려 볼 수 있습니다 (`GPU_MOCK=true`, 기본값). 이때 결과는 시연 데이터의 정답표로 만든 가짜 응답입니다.

```bash
cp .env.example .env                    # .env는 절대 커밋하지 않습니다
python scripts/make_demo_data.py        # 시연용 가상 계정 zip(합성 이미지) → data/demo/

# 백엔드 (터미널 1)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 프론트 (터미널 2) — /api 요청은 8000번 백엔드로 넘어갑니다
cd frontend
npm install
npm run dev                             # http://localhost:5173
```

- 시연: `data/demo/instagram-demo.zip`을 UC1에 올리고, `data/demo/uc2_demo.jpg`를 UC2에 올립니다.
- 배포: `cd frontend && npm run build` → 생긴 `frontend/dist/`를 백엔드가 같은 주소로 제공 (`uvicorn app.main:app --host 0.0.0.0 --port 8000`).
- 진짜 GPU 연결: CPU 서버 `.env`에 `GPU_MOCK=false`, `GPU_URL=http://10.1.2.30:8080`, GPU 서버와 같은 `GPU_API_KEY`를 지정합니다. GPU 서버는 `ml/gpu_server/.env.example`을 참고해 실행하며, 모델 프로세스는 한 개만 띄웁니다.
- 테스트 기준: 실제 NCP API에서 34장 × 4개 조합을 완료했습니다. 기본 OCR-first 2200px은 양성 장면 30/32, 유효 JSON 33/34, 평균 점검 26.06초·점검+마스킹 33.16초, VLM 입력 토큰 평균 4,613, 최대 예약 VRAM 11.94 GiB였습니다. 1280px OCR-first는 28/32, 점검+마스킹 평균 33.85초, 10.93 GiB였습니다. OCR 해상도는 모두 2200px였고 결과 문자열은 조합 간 같아, 정답 전사 없이 CER/오타율은 계산하지 않았습니다. VLM-first는 전체 세트에서 더 느리고 검출 수가 낮았습니다. 마스킹 후 잔류 문자가 나오면 문구와 위치를 추가 선택 항목으로 제공하며, 사용자가 추가로 가리거나 확인 후 현재 결과로 진행합니다. 이미지별 보고서와 원본 사진은 Git 밖에 보관합니다.
- 전체 API 데이터 흐름과 분리 배포는 [docs/architecture.md](docs/architecture.md), 정확한 요청·응답 형식은 [docs/api-contract.md](docs/api-contract.md)를 참고합니다.
- UC1 후보 선택 요청, 게시물별 결과 배열과 외부 직접 연결 설계는 [docs/api-contract.md](docs/api-contract.md), [docs/architecture.md](docs/architecture.md)를 참고합니다.
- NCP 외부 HTTPS 공개 준비와 필요한 콘솔 설정은 [docs/external-access-runbook.md](docs/external-access-runbook.md)를 참고합니다.

## 프로젝트 구조

```
.
├── backend/app/
│   ├── api/            uc1.py(게시물 건강검진) · uc2.py(올리기 전 체크)
│   ├── services/       zip 처리 · 추천 · 작업 큐 · 위험 단계 · GPU 클라이언트 · 세션
│   └── schemas/        contracts.py (API 요청·응답 형식)
├── frontend/src/
│   ├── pages/          화면 10개 (홈 · 동의 · 개인정보 안내 · 업로드 · 선택 · 분석 · 결과 · 정리 · 체크 · 가리기)
│   ├── components/     wf.tsx(공통 UI) · RegionPreview.tsx(가릴 영역 표시) · pixels.ts(픽셀 아이콘)
│   └── api/            types.ts · client.ts (contracts.py와 같은 이름)
├── ml/gpu_server/      GPU 내부 모델 API (OCR · Qwen 판단 · 가리기 · 재검사)
├── data/demo/          합성 이미지로 만든 시연 데이터
├── scripts/            시연 데이터 생성 · 평가 · 배포 보조
└── docs/               architecture · api-contract · data-policy · resources · CONTRIBUTING
```

- `services/engine.py`: 게시물 사이의 단서를 한 아이로 묶고, 위험 단계와 최소 정리 조합을 계산합니다.
- `services/gpu_queue.py`: GPU는 한 번에 한 요청만 처리하고, 대기열은 4개, 브라우저당 1개로 제한합니다.
- `ml/gpu_server/masking.py`: 고른 영역만 담은 작은 조각(patch + alpha)을 만듭니다. 원본 합성은 브라우저에서 합니다.
- `data/demo/mock_gpu.json`: `GPU_MOCK=true`일 때 쓰는 가짜 GPU 응답(시연 정답표)입니다.

## 시스템/서비스 아키텍처

```
부모 휴대폰(브라우저)
   │  HTTPS
   ▼
NCP Load Balancer ──▶ CPU 서버 :8000  (React 화면 + FastAPI)
                         │  zip 처리 · 게시물 연결 · 위험 단계 · 세션/대기열
                         │  내부망 + API 키
                         ▼
                      GPU 서버 :8080  (NVIDIA L4 24GB, 외부 차단)
                         PP-OCRv5 → Qwen3.5-4B → OpenCV 가리기 → OCR 재검사
```

- 브라우저는 CPU 서버하고만 통신합니다. GPU 서버 포트는 CPU 서버에서만 열려 있습니다.
- 올리기 전 체크의 사진은 요청 메모리에서만 처리하고, 게시물 건강검진의 zip은 세션별 임시 폴더에 두었다가 완료·취소·TTL·재시작 때 지웁니다.
- 가린 결과는 서버가 원본을 돌려주지 않고, 가린 조각만 보내 브라우저가 원본에 합성합니다. 새로 만든 JPEG에는 EXIF/GPS가 없습니다.
- 자세한 흐름: [docs/architecture.md](docs/architecture.md), API 형식: [docs/api-contract.md](docs/api-contract.md)

## 핵심 설계 결정

**Q. 위험 단계를 AI가 정하지 않는 이유는?**
**같은 조합이면 언제나 같은 단계가 나와야 부모가 결과를 믿고 행동할 수 있기 때문입니다.**

- AI(Qwen)는 "이 글자가 이름인가, 장소인가"처럼 단서를 고르는 일만 합니다.
- 단계는 `schemas/contracts.py`의 규칙으로 계산합니다: 이름 + 장소 = 위험, 이름 + 장소 + 시간 = 매우 위험.

**Q. 왜 OCR을 먼저 돌리고 Qwen을 나중에 쓰나요?**
**실측에서 OCR 먼저(OCR-first)가 더 많이 찾고 더 빨랐기 때문입니다.**

- 사진 34장 × 4개 조건 비교에서 OCR-first 2200px는 단서가 있는 장면 32개 중 30개를 찾았고, VLM-first는 19~24개였습니다.
- 평균 점검 시간도 OCR-first 26.06초, VLM-first 40.72~41.19초였습니다. ([docs/implementation-validation.md](docs/implementation-validation.md))

**Q. 왜 사진을 지우라고 하지 않고 "최소 정리"를 계산하나요?**
**부모가 실제로 할 수 있는 만큼만 권해야 행동으로 이어지기 때문입니다.**

- 위험 조합을 끊는 가장 적은 게시물만 고르고, 삭제보다 비공개 전환을 먼저 권합니다.
- 앱은 직접 지우거나 올리지 않습니다.

**Q. 가린 사진을 서버가 통째로 돌려주지 않는 이유는?**
**원본 사진이 서버와 네트워크에 머무는 시간을 줄이기 위해서입니다.**

- GPU 서버는 가린 영역의 작은 조각(patch + alpha)만 돌려주고, 합성은 브라우저 캔버스에서 합니다.
- 재검사에서 가린 글자가 다시 읽히면 저장 버튼을 막습니다.

## 배운 것 & 마무리

> 이 프로젝트를 통해 답할 수 있게 된 질문: **"보안 서비스에서 AI에게 무엇을 맡기고, 무엇을 코드와 사람에게 남겨야 하는가?"**

**AI 파이프라인** — OCR-first 판독, VLM 프롬프트 지침, JSON 재시도, 실측 기반 해상도·순서 선택
**보안·개인정보** — 동의 우선, 최소 수집(게시물 폴더만), EXIF 제거, TTL·3중 삭제, 내부망 GPU, 외부 API 미사용
**백엔드** — FastAPI, 작업(202) + 상태 조회, 공정 대기열, 서명 쿠키 세션, zip 폭탄·경로 공격 차단
**프론트** — React 19, 모바일 한 화면 레이아웃, 캔버스 조각 합성, 상태별 화면 전환

## 참고 / 트러블슈팅

- **GPU는 하나:** L4 24GB에서 BF16 모델 프로세스 하나가 최대 11.94 GiB(예약 기준)를 썼습니다. 프로세스를 두 개 띄우지 말고, 대기열이 가득 차면 429를 돌려줍니다.
- **재검사 실패:** 34장 측정에서 조건마다 7~8장은 가린 뒤에도 글자 일부가 다시 읽혔습니다. 이 경우 화면이 저장을 막고 영역을 바꿔 다시 가리도록 안내합니다.
- **CPU 서버 워커는 1개:** 작업 상태와 대기열을 메모리에 두기 때문에 워커가 여러 개면 상태가 어긋납니다.
- **TMP_DIR:** 재시작 때 폴더 전체를 지우므로 `/dev/shm` 같은 공용 폴더가 아니라 전용 하위 폴더(예: `/tmp/kkokkok`)를 지정합니다.
- **데이터 원칙:** 실제 아이 사진·실제 계정 데이터는 저장소에 올리지 않습니다 ([docs/data-policy.md](docs/data-policy.md)).

## 팀

| 이름 | 역할 |
|---|---|
| 김문정 | 기획 · 화면 · PM — 서비스 기획, API 계약, 와이어프레임, React 화면, 발표자료 |
| 김상원 | 팀장 · 백엔드 — FastAPI 로직 서버, 업로드·분석 작업 API, 보안 구조 검토 |
| 김기엽 | 판독 · 가리기 — PP-OCRv5 판독, OpenCV 가리기·재검사, 협업 컨벤션 |
| 김호재 | 서버 · 인프라 — GPU 모델 서버 구성, CPU 서버 배치·연결, 속도·메모리 측정 |
