# 외부 자원 기록 (발표 ⓕ 표에 그대로 사용)

> 새로 쓰면 PR에서 같이 추가합니다. 사전 보유 코드 없음.

| 구분 | 이름 | 버전 | 용도 | 라이선스 | 출처 | 추가한 사람 |
|---|---|---|---|---|---|---|
| 모델 | Qwen3-VL-8B-Instruct | bf16 | 사진 글자 판독 + 단서 추출 | Apache-2.0 (모델 카드 확인 필요) | Hugging Face | 김호재 |
| 모델 | Qwen/Qwen3.5-4B | BF16 | 현재 OCR 후보의 장소·인물 식별 단서 검토 | Apache-2.0 | [공식 모델 카드](https://huggingface.co/Qwen/Qwen3.5-4B) | 김기엽 |
| OCR | PaddleOCR + PP-OCRv5 | 3.x | 한국어 OCR와 문자 polygon | Apache-2.0 | [공식 라이선스](https://github.com/PaddlePaddle/PaddleOCR/blob/main/LICENSE) | 김기엽 |
| 라이브러리 | OpenCV headless | 5.0.0.93 | 주변 평균 RGB 채움·마스크 확장·Gaussian 경계 | Apache-2.0 | [공식 라이선스](https://github.com/opencv/opencv/blob/5.x/LICENSE) | 김기엽 |
| OCR | PaddleOCR (PP-OCRv5 Korean) | | 파일럿·박스 보조 후보 | Apache-2.0 | GitHub | 김상원 |
| 데이터 | HumynLabs/Korean-Signs-Image-Dataset | | OCR 파일럿 | CC BY 4.0 | Hugging Face | 김기엽 |
| 데이터 | Wikimedia Commons 이미지 12장 | | OCR 파일럿 | 이미지별 상이 | Commons | 김기엽 |
| 라이브러리 | FastAPI / Next.js / Pillow | | 서버·화면·가리기 | MIT / MIT / MIT-CMU | | |
| 폰트 | Jua, Gowun Dodum (@fontsource 패키지로 앱에 포함) | | 화면 글꼴 | SIL OFL 1.1 | Google Fonts · npm @fontsource | 김문정 |
| AI 개발 도구 | (예) Claude, ChatGPT, Gemini | | 기획·코드 보조 | - | - | |
