<div align="center">

# 꼭꼭

**꼭꼭 숨어라, 이름표 보일라 — 부모 본인의 게시물을 이어 보고, 낯선 사람이 아이를 찾을 수 있는 위험 단계를 경고하는 서비스**

코디세이 AI 해커톤 2026 · 주제 02 정보보호 · 팀 4K

</div>

## 프로젝트 개요
- 문제: 게시물 한 장씩은 안전해 보여도, 여러 게시물을 합치면 아이의 이름·나이·유치원·동네·등원 시간이 맞춰집니다.
- 해결: 부모 본인의 게시물을 분석해 단서를 연결하고, **조합 기반 위험 단계**(안전·주의·위험·매우 위험)로 경고합니다. 위험 요소마다 이유와 **권장 조치**를 보여 주고, 최소한의 정리(몇 장만)로 위험한 조합을 끊습니다.
- 원칙: AI가 찾고 → 부모가 고르고 → 코드가 가립니다. 게시·삭제는 부모가 직접 합니다. 본인 데이터만 분석합니다(URL·타인 계정 분석 없음).

## 주요 기능
| 기능 | 설명 |
|---|---|
| UC1 게시물 건강검진 | 인스타그램 내보내기 ZIP의 게시물 JSON·사진을 묶어 캡션/해시태그 단서를 먼저 추리고, 사용자가 단서와 사진을 조정한 뒤 선택분만 분석. 결과는 게시물·사진 배열로 반환 |
| UC2 올리기 전 체크 | 새 게시물을 올리면 단계가 어떻게 바뀌는지(예: 위험 → 매우 위험)와 경고 카드(이유·권장 조치) |
| 위험 판단 | 단서는 GPU 서버의 Qwen이 프롬프트 지침으로 판단하고, 단계 표기는 표로 통일 (이름 + 장소 = 위험, + 시간 = 매우 위험) |
| 사진·글 교차 점검 | 사진 속 글자(이름표 등)와 캡션·해시태그·위치 태그 단서를 함께 연결 |
| 가리기 + 재검사 | 고른 글자 polygon만 주변색으로 채우고 경계를 부드럽게 처리. 서버는 patch+alpha만 반환하고 브라우저가 원본에 합성 |

## 개발환경
| 구분 | 사용 |
|---|---|
| Backend | Python 3.11, FastAPI |
| Frontend | React + TypeScript (Vite 8, Node 20.19+ 또는 22.12+), React Router, axios · 모바일 우선 |
| 서버 | CPU 서버: 웹 앱(화면 + FastAPI) · GPU 서버(NCP L4 24GB): 모델 앱, 내부망 전용 |
| 판독 | PaddleOCR 3 / PP-OCRv5 2200px → Qwen3.5-4B BF16 위험 단서 검토 → OpenCV 5 평균색 채움 + sigma 8 블렌딩 |
| 요청 처리 | 포스트 후보 추림은 CPU 규칙으로 실행. 사용자가 선택한 사진만 EXIF 보정·긴 변 2200px로 정규화해 GPU로 보내며, L4 단일 모델 슬롯과 제한 대기열을 사용 |
| 협업 | GitHub Issue/PR, Discord |

## 배포 & 실행
GPU 서버 없이도 전체 화면 흐름을 돌려 볼 수 있습니다 (`GPU_MOCK=true`, 기본값).

```bash
cp .env.example .env                          # 절대 커밋 금지
python scripts/make_demo_data.py              # 시연용 가상 계정 zip (합성 이미지) 생성 → data/demo/

# 백엔드 (터미널 1)
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 프론트 (터미널 2) — /api 요청은 8000번 백엔드로 넘어감
cd frontend && npm install && npm run dev     # http://localhost:5173
```

- 시연: `data/demo/instagram-demo.zip`을 UC1에 올리고, `data/demo/uc2_demo.jpg`를 UC2에 올립니다.
- 배포: `cd frontend && npm run build` → 생긴 `frontend/dist/`를 백엔드가 같은 주소로 제공 (`uvicorn app.main:app --host 0.0.0.0 --port 8000`).
- 진짜 GPU 연결: CPU 서버 `.env`에 `GPU_MOCK=false`, `GPU_URL=http://10.1.2.30:8080`, GPU 서버와 같은 `GPU_API_KEY`를 지정합니다. GPU 서버는 `ml/gpu_server/.env.example`을 참고해 실행하며, 모델 프로세스는 한 개만 띄웁니다.
- 테스트 기준: 실제 NCP API에서 34장 × 4개 조합을 완료했습니다. 기본 OCR-first 2200px은 양성 장면 30/32, 유효 JSON 33/34, 평균 점검 26.06초·점검+마스킹 33.16초, VLM 입력 토큰 평균 4,613, 최대 예약 VRAM 11.94 GiB였습니다. 1280px OCR-first는 28/32, 점검+마스킹 평균 33.85초, 10.93 GiB였습니다. OCR 해상도는 모두 2200px였고 결과 문자열은 조합 간 같아, 정답 전사 없이 CER/오타율은 계산하지 않았습니다. VLM-first는 전체 세트에서 더 느리고 검출 수가 낮았습니다. 마스킹 후 잔류 문자가 나온 이미지는 UI가 다운로드를 막습니다. 이미지별 보고서와 원본 사진은 Git 밖에 보관합니다.
- 전체 API 데이터 흐름과 분리 배포는 [docs/architecture.md](docs/architecture.md), 정확한 요청·응답 형식은 [docs/api-contract.md](docs/api-contract.md)를 참고합니다.
- UC1 후보 선택 요청, 게시물별 결과 배열과 외부 직접 연결 설계는 [docs/api-contract.md](docs/api-contract.md), [docs/architecture.md](docs/architecture.md)를 참고합니다.

## 프로젝트 구조
```
.github/        이슈·PR 템플릿, 룰셋 JSON
backend/app/    api(uc1·uc2 라우터) · services(zip 처리·추천·작업·위험 단계·GPU 클라이언트) · schemas(API 계약)
frontend/src/    pages(화면 9개) · api(계약 타입·호출) · hooks · components
ml/             model-test(모델 비교) · eval(정답·채점)
data/demo/      합성 이미지로 만든 시연 데이터 (실제 아이 사진 금지)
scripts/        시연 데이터 생성 · GPU 서버 세팅·백업
docs/           CONTRIBUTING · architecture · data-policy · resources · github-setup
```

## 팀
| 이름 | 역할 |
|---|---|
| 김상원 | 팀장 · 로컬 모델/프롬프트 |
| 김기엽 | OCR/판독 |
| 김호재 | GPU 서버 |
| 김문정 | GitHub · 시나리오 |

## 외부 자원
사용한 외부 모델·데이터·라이브러리는 [docs/resources.md](docs/resources.md)에 기록합니다.
