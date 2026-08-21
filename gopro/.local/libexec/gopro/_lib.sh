#!/usr/bin/env bash
# _lib.sh — shared helpers for the gopro-* workers. Sourced, never executed.
#
# The important idea in here is the *encode profile stamp*: every streamable copy
# carries the exact ladder it was made with, written into the mp4's `comment` tag
# (e.g. "gopro-enc:v2:1440p:h264:cq22"). The skip-check reads that tag instead of
# just testing "does the file exist", so bumping RES/CODEC/CQ/ENC_VERSION in
# gopro.conf makes every stale copy re-encodable — while everything already at the
# current profile is still skipped. That's what lets `gopro backfill` be both
# resumable and idempotent.

gopro_conf() {
  local conf="${XDG_CONFIG_HOME:-$HOME/.config}/gopro.conf"
  [[ -f "$conf" ]] || { echo "missing $conf (copy gopro.conf.example)" >&2; return 1; }
  # shellcheck disable=SC1090
  source "$conf"
  : "${RES:=1440}" "${CODEC:=h264}" "${CQ:=22}" \
    "${VBITRATE:=12M}" "${VMAXRATE:=18M}" "${ABITRATE:=128k}" "${ENC_VERSION:=2}"
  case "$CODEC" in
    h264) ENC=h264_nvenc;;
    hevc) ENC=hevc_nvenc;;
    *) echo "CODEC must be h264 or hevc (got '$CODEC')" >&2; return 1;;
  esac
}

# The profile string stamped into (and read back out of) every streamable copy.
gopro_profile() { printf 'gopro-enc:v%s:%sp:%s:cq%s' "$ENC_VERSION" "$RES" "$CODEC" "$CQ"; }

# Profile a given output was encoded with, or "" if unstamped/unreadable.
gopro_stamp_of() {
  ffprobe -v error -show_entries format_tags=comment -of default=nw=1:nk=1 "$1" 2>/dev/null | head -1
}

# 0 = this output needs (re-)encoding, 1 = it's already at the current profile.
gopro_needs_encode() {
  local out="$1"
  [[ -s "$out" ]] || return 0
  [[ "$(gopro_stamp_of "$out")" == "$(gopro_profile)" ]] && return 1
  return 0
}

# Encode one original into a streamable copy, stamped with the current profile.
#
# NOTE: decode on the GPU but hand frames back to the CPU (no -hwaccel_output_format
# cuda, CPU scale filter). This lets ffmpeg auto-apply the clip's rotation flag --
# GoPros mounted upside down record rotation=-180 metadata rather than flipping
# pixels, and keeping frames on the GPU (scale_cuda) silently skips that, baking the
# video in upside down. Still NVENC-encoded, ~4.5x realtime at 1440p on a 3060, so
# the CPU scale costs nothing that matters: the archive download is the bottleneck.
gopro_encode() {
  local in="$1" out="$2"
  ffmpeg -hide_banner -loglevel error -stats -y \
    -hwaccel cuda -i "$in" \
    -vf "scale=-2:${RES}" \
    -c:v "$ENC" -preset p5 -tune hq -rc vbr -cq "$CQ" \
    -b:v "$VBITRATE" -maxrate "$VMAXRATE" -bufsize 24M \
    -c:a aac -b:a "$ABITRATE" \
    -metadata comment="$(gopro_profile)" \
    -movflags +faststart "$out"
}

# Tuned rclone flags. MyCloud throttles per *connection*, not per account: one
# stream gets ~4 MB/s, eight get ~25 MB/s from the desktop and ~83 MB/s from the
# VPS. Every archive read should go through this.
gopro_rclone_fast() {
  rclone "$@" --transfers "${RCLONE_TRANSFERS:-8}" \
              --checkers "${RCLONE_CHECKERS:-16}" \
              --multi-thread-streams "${RCLONE_STREAMS:-4}"
}

gopro_ssh_host() { printf '%s' "${VPS_TARGET%%:*}"; }
gopro_gopro_dir() { printf '%s' "${VPS_TARGET#*:}"; }
