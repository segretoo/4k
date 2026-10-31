# 꼭꼭 프론트 (React + TypeScript + Vite)

```bash
npm install
npm run dev      # http://localhost:5173, /api는 localhost:8000 백엔드로 프록시
npm run build    # dist/ 생성 → 백엔드가 같은 주소로 제공
```

| 폴더 | 내용 |
|---|---|
| `src/pages` | 화면 9개 (홈, 동의, 올리기, 사진 고르기, 분석 중, 위험 단계 카드, 최소 정리, 게시 전 진단, 가리기) |
| `src/api` | API 계약 타입(`types.ts`)과 호출(`client.ts`). 백엔드 `contracts.py`와 필드 이름을 맞춤 |
| `src/hooks` | `useJobProgress`: 2초마다 분석 진행률 확인 |
| `src/state` | 화면 사이 상태. 썸네일은 브라우저 메모리에만 보관 (서버 파일은 분석 후 삭제) |
| `src/lib` | 한국어 라벨, sessionStorage(동의 여부, UC2에 넘길 단서 요약) |
