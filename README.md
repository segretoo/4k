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
| UC1 지난 게시물 점검 | 인스타그램 내보내기 zip을 올리면 점검할 사진을 추천(최대 10장)하고, 위험 단계 카드(근거 조합)와 최소 정리 목록을 보여줌 |
| UC2 게시 전 경고 | 새 게시물을 올리면 단계가 어떻게 바뀌는지(예: 위험 → 매우 위험)와 경고 카드(이유·권장 조치) |
| 위험 판단 | 단서는 GPU 서버의 Qwen이 프롬프트 지침으로 판단하고, 단계 표기는 표로 통일 (이름 + 장소 = 위험, + 시간 = 매우 위험) |
| 사진·글 교차 점검 | 사진 속 글자(이름표 등)와 캡션·해시태그·위치 태그 단서를 함께 연결 |
| 가리기 + 재검사 | 고른 영역을 OpenCV 인페인팅(NS)으로 채우고, 메타데이터(GPS) 제거 후 판독 모델로 다시 읽어 확인 |

## 개발환경
| 구분 | 사용 |
|---|---|
| Backend | Python 3.11, FastAPI |
| Frontend | React + TypeScript (Vite), React Router, axios · 모바일 우선 |
| 서버 | CPU 서버: 웹 앱(화면 + FastAPI) · GPU 서버(NCP L4 24GB): 모델 앱, 내부망 전용 |
| 판독 | VLM(Qwen-VL) 1차 → PaddleOCR 2차 → Qwen 위험 판단, 모두 GPU 서버 안에서 |
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
- 진짜 GPU 연결: `.env`에서 `GPU_MOCK=false`, `GPU_URL=http://<GPU 내부 IP>:<포트>`. GPU 호출은 `backend/app/services/gpu_client.py` 한 곳에서만 합니다.
- 테스트: `cd backend && python -m pytest -q`

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
