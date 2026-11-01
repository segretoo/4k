# 외부 자원 활용 내역

> 발표자료 ⓕ와 같은 내용입니다. 사전 보유 코드는 없고, 아래 외부 자원만 사용했습니다.
> 라이선스는 각 프로젝트의 공식 저장소·패키지 페이지 기준이며, 새 자원을 쓰면 PR에서 이 표에 함께 추가합니다.

## 1. AI 모델

| 이름 | 버전·설정 | 어디에 썼나 | 라이선스 | 출처 |
|---|---|---|---|---|
| Qwen3.5-4B | BF16, 긴 변 2200px 입력 | GPU 서버. OCR 후보와 사진·캡션을 보고 이름·장소·시간 등 단서를 판단 | Apache-2.0 | [Hugging Face 모델 카드](https://huggingface.co/Qwen/Qwen3.5-4B) |
| PaddleOCR / PP-OCRv5 (Korean) | PaddleOCR 3.x, 긴 변 2200px | GPU 서버의 CPU 보조 프로세스. 사진 속 글자 인식과 글자 영역(polygon), 가린 뒤 재검사 | Apache-2.0 | [GitHub](https://github.com/PaddlePaddle/PaddleOCR) |
| Qwen3-VL-8B-Instruct | BF16 | 모델 비교 테스트에만 사용 (최종 서비스에는 미사용) | Apache-2.0 | [Hugging Face](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct) |

## 2. 라이브러리

### 프론트 (`frontend/package.json`)
| 이름 | 용도 | 라이선스 |
|---|---|---|
| React 19 · React DOM | 화면 | MIT |
| React Router 7 | 화면 이동 | MIT |
| Axios | API 호출 | MIT |
| TypeScript 7 | 타입 | Apache-2.0 |
| Vite 8 · @vitejs/plugin-react | 개발 서버·빌드 | MIT |
| oxlint | 코드 검사 | MIT |
| @fontsource/jua · @fontsource/gowun-dodum | 화면 글꼴 파일 포함 | 글꼴 OFL-1.1 · 패키지 MIT |

### CPU 서버 (`backend/requirements.txt`, Python 3.11+)
| 이름 | 용도 | 라이선스 |
|---|---|---|
| FastAPI | API 서버 | MIT |
| Uvicorn | 서버 실행 | BSD-3-Clause |
| Pydantic | 요청·응답 형식 검증 | MIT |
| python-multipart | 파일 업로드 처리 | Apache-2.0 |
| python-dotenv | `.env` 설정 읽기 | BSD-3-Clause |
| HTTPX | GPU 서버 내부 호출 | BSD-3-Clause |
| Pillow | 이미지 회전 보정·크기 조정·썸네일·EXIF 제거 | MIT-CMU (HPND) |
| pytest | 테스트 | MIT |

### GPU 서버 (`ml/gpu_server/requirements*.txt`)
| 이름 | 용도 | 라이선스 |
|---|---|---|
| PyTorch | 모델 실행 (CUDA) | BSD-3-Clause |
| Transformers · Accelerate | Qwen 모델 불러오기·추론 | Apache-2.0 |
| PaddlePaddle | PaddleOCR 실행 | Apache-2.0 |
| OpenCV (opencv-python-headless 5.0.0.93) | 주변 평균색 채우기 · 2px 확장 · Gaussian(sigma 8) 경계 | Apache-2.0 |
| NumPy | 이미지 배열 처리 | BSD-3-Clause |
| FastAPI · Uvicorn · python-multipart · python-dotenv · HTTPX | 내부 모델 API | 위와 같음 |
| Requests | 평가 스크립트 HTTP 호출 | Apache-2.0 |

### 개발용 (선택)
| 이름 | 용도 | 라이선스 |
|---|---|---|
| Playwright | `scripts/browser_smoke.py` 브라우저 점검 (선택 실행) | Apache-2.0 |
| GitHub Actions (checkout, setup-python, setup-node) | CI 테스트·빌드 | MIT |

## 3. 데이터

| 이름 | 어디에 썼나 | 라이선스 | 출처 |
|---|---|---|---|
| 시연용 합성 이미지 · 가상 캡션 | `data/demo`, `data/samples` (팀 제작, 실제 아이 사진 없음) | 팀 제작 | `scripts/make_demo_data.py` |
| HumynLabs/Korean-Signs-Image-Dataset | OCR 파일럿 테스트 (저장소에 미포함) | CC BY 4.0 | [Hugging Face](https://huggingface.co/datasets/HumynLabs/Korean-Signs-Image-Dataset) |
| Wikimedia Commons 이미지 12장 | OCR 파일럿 테스트 (저장소에 미포함) | 이미지별 상이 (CC BY / CC BY-SA 등) | Wikimedia Commons |
| 평가용 사진 34장 | 파이프라인 비교 측정 (저장소에 미포함) | 팀 촬영·수집 | 비공개 보관 |

## 4. 인프라 · 글꼴 · 도구

| 이름 | 용도 | 비고 |
|---|---|---|
| NCP 서버 (CPU 서버, GPU 서버 NVIDIA L4 24GB) | 서비스 실행 | 대회 제공 |
| NCP Load Balancer · Certificate Manager | 외부 HTTPS 접속 | 대회 제공 NCP 서비스 |
| Jua · Gowun Dodum | 화면 글꼴 | SIL OFL 1.1 |
| Pretendard | 발표자료 글꼴 | SIL OFL 1.1 |
| AI 개발 도구 (Claude 등) | 기획·코드 작성 보조 | 생성 코드는 팀원이 검토 후 병합 |

## 외부 AI API

사용하지 않습니다. 모든 모델은 대회 제공 GPU 서버 내부망에서 실행됩니다.
