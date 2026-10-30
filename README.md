<div align="center">

# 낯선 사람이 보는 내 아이 (가칭)

**부모가 올린 게시물 속 단서를 연결해, 낯선 사람이 알아낼 수 있는 아이 정보를 한 장의 카드로 보여주는 서비스**

코디세이 AI 해커톤 2026 · 주제 02 정보보호 · 팀 4K

</div>

## 프로젝트 개요
- 문제: 게시물 한 장씩은 안전해 보여도, 여러 게시물을 합치면 아이의 이름·나이·유치원·동네·등원 시간이 맞춰집니다.
- 해결: 부모 본인의 게시물을 분석해 단서를 연결하고, 최소한의 정리(몇 장만)로 프로필 완성을 끊습니다.
- 원칙: AI가 찾고 → 부모가 고르고 → 코드가 가립니다. 게시·삭제는 부모가 직접 합니다.

## 주요 기능
| 기능 | 설명 |
|---|---|
| UC1 과거 게시물 점검 | 내보낸 게시물 데이터를 한 번 점검해 프로필 카드와 최소 정리 목록을 보여줌 |
| UC2 게시 전 진단 | 새 게시물이 기존 단서와 합쳐질 때 새로 드러나는 정보를 경고 |
| 사진·글 교차 점검 | 사진 속 글자(이름표 등)와 캡션·해시태그 단서를 함께 연결 |
| 선택 가리기 | 부모가 고른 영역만 단색/모자이크 처리 (원본은 서버 밖으로 나가지 않음) |

## 개발환경
| 구분 | 사용 |
|---|---|
| Backend | Python 3.11, FastAPI |
| Frontend | Next.js (TypeScript) |
| 모델 서빙 | NCP L4 GPU, Ollama 또는 vLLM (확정 전) |
| 판독 | 로컬 VLM 또는 한국어 OCR + 로컬 LLM (비교 테스트 후 확정) |
| 협업 | GitHub Issue/PR, Discord |

## 배포 & 실행
```bash
cp .env.example .env          # 키 값은 팀 채널에서 공유, 절대 커밋 금지
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

## 프로젝트 구조
```
.github/        이슈·PR 템플릿, 룰셋 JSON
backend/app/    api(라우터) · services(판독·LLM·연결 엔진·가리기) · schemas(JSON 계약)
frontend/       Next.js 화면
ml/             model-test(모델 비교) · eval(정답·채점)
data/samples/   가상 캡션·소품 사진만 (실제 아이 사진 금지)
scripts/        GPU 서버 세팅·백업
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
