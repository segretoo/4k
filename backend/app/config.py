"""환경 변수 설정. 값은 .env에서 읽고, 저장소에는 .env.example만 둔다."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # GPU 모델 앱 주소 (내부 IP). GPU_MOCK=true면 호출하지 않고 가짜 응답을 쓴다.
    gpu_url: str = os.getenv("GPU_URL", "http://10.1.2.30:8080")
    gpu_api_key: str = os.getenv("GPU_API_KEY", "")
    gpu_mock: bool = _bool("GPU_MOCK", True)
    gpu_timeout_s: float = float(os.getenv("GPU_TIMEOUT_S", "120"))
    mock_delay_s: float = float(os.getenv("MOCK_DELAY_S", "0.6"))
    mock_fixture: Path = Path(os.getenv("MOCK_FIXTURE", "../data/demo/mock_gpu.json"))
    session_secret: str = os.getenv("SESSION_SECRET", "")
    session_cookie_secure: bool = _bool("SESSION_COOKIE_SECURE", False)

    # 분석 수량과 후보 범위
    max_photos: int = int(os.getenv("MAX_PHOTOS", "10"))
    max_candidate_posts: int = int(os.getenv("MAX_CANDIDATE_POSTS", "100"))
    max_screen_captions: int = int(os.getenv("MAX_SCREEN_CAPTIONS", "50"))

    # 임시 파일
    tmp_dir: Path = Path(os.getenv("TMP_DIR", "/tmp/kkokkok"))
    upload_ttl_min: int = int(os.getenv("UPLOAD_TTL_MIN", "30"))

    # 상한값 (기엽님 테스트 후 조정)
    max_zip_mb: int = int(os.getenv("MAX_ZIP_MB", "300"))
    max_unzipped_mb: int = int(os.getenv("MAX_UNZIPPED_MB", "1500"))
    max_zip_files: int = int(os.getenv("MAX_ZIP_FILES", "5000"))
    max_photo_mb: int = int(os.getenv("MAX_PHOTO_MB", "20"))
    max_image_side: int = int(os.getenv("MAX_IMAGE_SIDE", "2200"))
    max_image_pixels: int = int(os.getenv("MAX_IMAGE_PIXELS", "40000000"))
    thumb_side: int = int(os.getenv("THUMB_SIDE", "320"))

    # React 빌드 결과 위치 (있으면 같은 주소로 화면을 제공)
    frontend_dist: Path = Path(os.getenv("FRONTEND_DIST", "../frontend/dist"))


settings = Settings()
