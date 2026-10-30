#!/usr/bin/env bash
# GPU 서버 삭제(11/1 13:00) 전 결과·로그 백업. 서버에서 실행.
set -euo pipefail
STAMP=$(date +%m%d_%H%M)
tar czf "backup_${STAMP}.tar.gz" ml/model-test ml/eval logs 2>/dev/null || true
echo "backup_${STAMP}.tar.gz 생성 → scp로 로컬에 받아두세요"
