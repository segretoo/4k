# 아키텍처 (초안 — 판독 방식은 비교 테스트 후 확정)

```
[부모 브라우저] ──업로드──▶ [FastAPI] ──SSH 터널──▶ [NCP L4 GPU: 로컬 모델]
      ▲                         │
      │                         ├─ 1. 판독: 로컬 VLM  또는  한국어 OCR(박스) + 로컬 LLM
      │                         ├─ 2. 단서 추출: name · age · school · area · time
      │                         ├─ 3. 연결 엔진(직접 개발): 게시물 간 단서 연결 → 프로필 카드
      │                         │     최소 정리(근사 최소 집합 덮개) · 사진↔글 교차 점검
      └──── 카드·정리 목록 ◀────┴─ 4. 가리기(OpenCV): 부모가 고른 박스만 단색/모자이크
```

## 역할 분담 원칙
**AI가 찾고 → 부모가 고르고 → 코드가 가린다.** 가리기 실행은 자동이지만, 무엇을 가릴지는 부모가 정하고 게시·삭제는 하지 않습니다.

## JSON 계약 (변경 시 팀 공유 필수 → `backend/app/schemas/contracts.py`)
### 판독 결과 (게시물 1개)
```json
{"post_id": "p01", "texts": [{"text": "김하늘", "box": [120, 80, 260, 130], "conf": 0.91, "source": "image"}],
 "caption": "#하늘이 #햇살유치원 등원길"}
```
### 단서 추출
```json
{"post_id": "p01", "entities": [{"type": "name", "value": "하늘", "evidence": "caption", "box": null}]}
```
### 엔진 결과
```json
{"card": {"name": "하늘", "age": "5세", "school": "햇살유치원", "area": "망원동", "time": "08:40"},
 "sources": {"name": ["p01", "p07"]},
 "cleanup": ["p07", "p12"],
 "new_items": []}
```
