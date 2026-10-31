# 아키텍처 (v2.0 · 10/31)

```
[부모 브라우저(모바일 우선)] ──동의·업로드──▶ [FastAPI] ──SSH 터널──▶ [NCP L4 GPU: Qwen3-VL-8B]
      ▲                                        │
      │                                        ├─ 1. 판독 + 단서 추출 (로컬 VLM 한 번 호출)
      │                                        │     사진 글자·위치 박스 + 캡션·위치 태그 → 단서 5종 JSON
      │                                        │     (박스가 부정확하면 PaddleOCR로 박스만 보조)
      │                                        ├─ 2. 연결 엔진 (직접 개발)
      │                                        │     게시물 간 단서 연결 → 위험 단계(규칙) → 최소 정리 · 교차 점검
      │                                        └─ 3. 가리기 모듈 (직접 개발)
      │                                              단색 가림 → 새 파일 저장(메타데이터·GPS 제거) → 재검사
      └──── 위험 단계 카드 · 경고 카드(이유·권장 조치) · 가린 사진 ◀──┘
```

## 원칙
- **AI가 찾고 → 부모가 고르고 → 코드가 가린다.** 게시·삭제는 부모가 SNS에서 직접.
- **위험 단계는 AI가 매기지 않는다.** 아래 규칙을 코드로 계산해서 매번 같은 결과, 설명 가능한 근거를 낸다.
- **본인 데이터만.** URL·타인 계정 분석 기능은 만들지 않는다.

## 위험 단계 규칙
| 단계 | 코드 값 | 조건 |
|---|---|---|
| 안전 | `safe` | 단서 없음 |
| 주의 | `caution` | 단서는 있지만 장소 없음 |
| 위험 | `high` | 이름 + 장소(`school` 또는 `area`) |
| 매우 위험 | `very_high` | 이름 + 장소 + `time` |

경고 카드 심각도: 매우 위험 조합에 들어가는 단서 = `high`, 위험 조합 = `medium`, 판독 불확실 = `check`.

## 가리기와 안티마스킹 대응
| 위험 | 대응 |
|---|---|
| 모자이크·블러 복원 | 단색만 사용 (불투명 100%) |
| 반투명·투명 채널 | RGB로 변환해 저장 |
| EXIF 속 원본 썸네일·GPS | 메타데이터 없이 새 파일로 다시 인코딩 |
| 원본 위 덮어쓰기 잔여 데이터 | 항상 새 파일로 저장 |
| 덜 가려짐 | 박스 15~20% 확장 + 최소 크기 |
| 같은 단서가 다른 곳에 | 연결 엔진·교차 점검 + 재검사 |

## JSON 계약 (변경 시 팀 공유 필수 → `backend/app/schemas/contracts.py`)
### 판독 + 단서 추출 (게시물 1개)
```json
{"post_id": "p03",
 "caption": "#하늘이 #햇살유치원 첫 등원",
 "texts": [{"text": "하늘", "box": [159, 128, 207, 158], "conf": null, "source": "image"}],
 "entities": [
  {"type": "name", "value": "하늘", "evidence": "image", "box": [159, 128, 207, 158]},
  {"type": "school", "value": "햇살유치원", "evidence": "caption", "box": null},
  {"type": "area", "value": "망원동", "evidence": "location_tag", "box": null}]}
```
### 연결 엔진
```json
{"level": "very_high",
 "reason": ["name", "school", "time"],
 "card": {"name": "하늘", "school": "햇살유치원", "time": "08:40"},
 "sources": {"school": ["p03", "p11"]},
 "cleanup": ["p03", "p07", "p11"],
 "level_after_cleanup": "caution",
 "warnings": [{"type": "time", "severity": "high", "why": "이름·유치원과 합쳐져 매우 위험", "action": "시간 표현 빼기"}]}
```
### 가리기 결과
```json
{"file": "masked_p03.jpg", "rescan_passed": true, "leaked": [], "meta_clean": true}
```
