import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("GPU_MOCK", "true")
os.environ.setdefault("MOCK_DELAY_S", "0")
os.environ.setdefault("TMP_DIR", str(Path("/tmp") / "kkokkok-test"))
os.environ.setdefault("MOCK_FIXTURE", str(ROOT / "data" / "demo" / "mock_gpu.json"))
os.environ.setdefault("FRONTEND_DIST", str(ROOT / "frontend" / "__no_dist__"))


@pytest.fixture(scope="session")
def demo_zip() -> Path:
    path = ROOT / "data" / "demo" / "instagram-demo.zip"
    if not path.exists():
        subprocess.run([sys.executable, str(ROOT / "scripts" / "make_demo_data.py")], check=True)
    return path
