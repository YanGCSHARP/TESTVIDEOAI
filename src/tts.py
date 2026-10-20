"""Generate the voice-over with Kokoro (offline ONNX TTS), one clip per sentence."""
import json, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

MODEL_DIR = sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/kokoro"
OUT = "build"
VOICE, SPEED = "am_onyx", 0.93

LINES = [
    "On June thirteenth, two thousand eight, it was an ordinary morning at the Sun Drop bottling plant in Concord, North Carolina.",
    "Within minutes, two people were dead, and the killer had vanished with a box, and cash from the register.",
    "For seventeen years, the case went cold.",
    "Then, a DNA breakthrough pointed detectives three thousand miles away.",
]

def trim(x, sr, thr=0.01):
    idx = np.where(np.abs(x) > thr)[0]
    a, b = max(idx[0] - int(0.02 * sr), 0), min(idx[-1] + int(0.08 * sr), len(x))
    return x[a:b]

k = Kokoro(f"{MODEL_DIR}/kokoro-v1.0.onnx", f"{MODEL_DIR}/voices-v1.0.bin")
info = []
for i, line in enumerate(LINES):
    s, sr = k.create(line, voice=VOICE, speed=SPEED, lang="en-us")
    s = trim(s, sr)
    sf.write(f"{OUT}/vo_{i}.wav", s, sr)
    info.append({"i": i, "dur": len(s) / sr, "sr": sr})
    print(i, round(len(s) / sr, 2))
json.dump(info, open(f"{OUT}/vo.json", "w"), indent=1)
