#!/usr/bin/env bash
# 로컬 → GPU 서버 모델 포트 터널. 접속 정보는 .env 또는 팀 채널(저장소에 쓰지 않기)
# 사용: GPU_HOST=user@ip ./scripts/gpu_tunnel.sh
set -euo pipefail
: "${GPU_HOST:?GPU_HOST=user@ip 형식으로 지정}"
ssh -N -L 11434:localhost:11434 "$GPU_HOST"
