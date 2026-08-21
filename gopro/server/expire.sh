#!/usr/bin/env bash
# Delete gopro-share token dirs whose .expires timestamp has passed.
# Run hourly from cron:  17 * * * * /opt/docker/gopro-share/expire.sh
set -euo pipefail
SHARE_DIR=/srv/media/gopro-share
now=$(date +%s)
shopt -s nullglob
for d in "$SHARE_DIR"/*/; do
  exp=$(cat "$d/.expires" 2>/dev/null || echo 0)
  case "$exp" in ''|*[!0-9]*) exp=0;; esac
  if [ "$exp" -gt 0 ] && [ "$now" -gt "$exp" ]; then rm -rf "$d"; fi
done
