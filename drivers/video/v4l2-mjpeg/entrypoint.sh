#!/bin/sh
set -e

DEVICE="${DEVICE:-/dev/video0}"
VIDEO_SIZE="${VIDEO_SIZE:-1920x1080}"
FRAME_RATE="${FRAME_RATE:-30}"

# ffmpeg -listen 1 serves one client then exits; loop to accept the next one.
# `|| true` matters: without it, `set -e` kills this loop the first time a
# client disconnects mid-stream (ffmpeg exits non-zero on broken pipe).
while true; do
  ffmpeg -f v4l2 -input_format mjpeg -video_size "$VIDEO_SIZE" -framerate "$FRAME_RATE" -i "$DEVICE" \
    -c:v copy -content_type 'multipart/x-mixed-replace;boundary=ffmpeg' \
    -f mpjpeg -listen 1 http://0.0.0.0:8091 2>&1 || true
  sleep 1
done
