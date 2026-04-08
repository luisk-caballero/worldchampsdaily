#!/bin/zsh
set -euo pipefail

REPO_DIR="/Users/lcaballer1/Documents/venezuelan-mlb-report"
LOCK_DIR="/tmp/woldchampsdaily.lock"
LOG_DIR="$REPO_DIR/var"
LOG_FILE="$LOG_DIR/scheduler.log"

mkdir -p "$LOG_DIR"

# Prevent overlapping runs if one attempt is delayed by network retries.
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "$(date '+%Y-%m-%d %H:%M:%S %Z') [skip] lock exists, another run is active" >> "$LOG_FILE"
  exit 0
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

{
  echo "$(date '+%Y-%m-%d %H:%M:%S %Z') [start] scheduled run"
  cd "$REPO_DIR"
  PYTHONPATH=src python3 -m venezuelan_mlb_report run-daily \
    --history-mode if-missing \
    --publish-site-dir site \
    --git-push \
    --max-attempts 4 \
    --retry-delay-seconds 90
  echo "$(date '+%Y-%m-%d %H:%M:%S %Z') [done] scheduled run"
} >> "$LOG_FILE" 2>&1
