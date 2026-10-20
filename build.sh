#!/usr/bin/env bash
# Full pipeline: voice-over -> music/SFX mix -> frames -> MP4.
# Needs: python3, ffmpeg, pip install numpy scipy pycairo pillow soundfile pyloudnorm kokoro-onnx
# Kokoro model files (kokoro-v1.0.onnx, voices-v1.0.bin) from
# https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0 in $KOKORO_DIR.
set -euo pipefail
cd "$(dirname "$0")"
KOKORO_DIR=${KOKORO_DIR:-/tmp/claude-0/kokoro}
mkdir -p build out
python3 src/tts.py "$KOKORO_DIR"
(cd src && python3 audio.py ../build/mix.wav)
(cd src && python3 render.py video ../build/video.mp4 "$(nproc)")
ffmpeg -y -loglevel error -i build/video.mp4 -i build/mix.wav -map 0:v -map 1:a -c:v copy \
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart -t 30 out/sun_drop_intro_test.mp4
echo "done: out/sun_drop_intro_test.mp4"
